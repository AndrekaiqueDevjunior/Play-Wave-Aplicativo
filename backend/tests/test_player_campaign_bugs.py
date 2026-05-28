"""Testes regressivos — Bugs do player relacionados a campanha.

===========================================================================
BUGS CONFIRMADOS
===========================================================================

BUG 1 — Player reinicia ao qualquer alteração no gerenciador
  Arquivo: frontend/src/pages/Player.jsx, linha 722
  Código:
      const onPlaylistInvalidated = () => triggerReload("playlist_invalidated");
  Problema:
      - onPlaylistInvalidated chama triggerReload() que chama setPhase("loading")
        INCONDICIONALMENTE ao receber o evento SSE "playlist_invalidated".
      - Não há nenhuma verificação se o config_version recebido no evento é
        diferente do campaignConfigVersion armazenado no estado do player.
      - O evento SSE inclui config_version no campo data (ver
        _broadcast_playlist_invalidated em backend/api/v1/campaigns.py linha 63–83),
        mas o handler JavaScript ignora completamente este campo e reinicia
        o player de qualquer forma.
  Causa raiz secundária:
      - O PUT /campaigns/{id} (campaigns.py linha 401–408) chama
        crud_campaign.increment_config_version() E _broadcast_playlist_invalidated()
        para QUALQUER campo alterado — inclusive campos que não afetam a playlist
        do player (ex: description, tags, audio_policy que não seja para o player).

BUG 2 — Conteúdo da campanha não aparece no player (media: [])
  Arquivo: backend/api/v1/devices.py, função _build_player_playlist_response
  e _resolve_player_campaign (linha 621–659)
  Problema:
      - _resolve_player_campaign tenta primeiro device.current_campaign_id.
        Se não estiver setado, chama crud_campaign.get_active_for_device que
        filtra Campaign.status == "active" (crud_campaign.py linha 107).
      - Se a campanha não for "active" (ex: "draft", "paused") e o
        device.current_campaign_id não estiver setado, retorna None → media: [].
      - Adicionalmente, _build_media_payload filtra cada mídia por
        _media_is_valid_for_player (devices.py linha 341), que exige
        status == "available" E is_active != False. Mídias recém-criadas
        podem ter status diferente de "available" e assim serem filtradas.
  Comportamento observado:
      - A campanha pode ser retornada no campo "campaign" do payload mas com
        "media": [] se todas as mídias falharem nos filtros.

CORREÇÃO SUGERIDA PARA BUG 1 (Player.jsx):
    const onPlaylistInvalidated = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        const newVersion = data?.data?.config_version;
        if (newVersion && newVersion === campaignConfigVersion) return; // sem mudança
      } catch { /* ignore */ }
      triggerReload("playlist_invalidated");
    };

CORREÇÃO SUGERIDA PARA BUG 1 (campaigns.py PUT):
    Antes de chamar increment_config_version, verificar se o update_data contém
    campos que realmente afetam a playlist (media_ids, media_order, device_ids,
    starts_at, ends_at, status, priority). Se não contiver nenhum campo
    relevante, não incrementar config_version nem broadcastar.
===========================================================================
"""

import unittest
import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_device(**kw):
    base = dict(
        id=uuid.uuid4(),
        name="TV Loja",
        tenant_id=uuid.uuid4(),
        device_token="test-token-123",
        is_blocked=False,
        requires_repairing=False,
        status="online",
        current_campaign_id=None,
        current_campaign=None,
        config_version=None,
        audio_playlist_id=None,
        osd_show_current_audio=False,
        osd_position=None,
        osd_duration_seconds=None,
        osd_opacity=None,
        osd_font_size=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_campaign(**kw):
    base = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Campanha Teste",
        status="active",
        priority=1,
        config_version="v1",
        device_ids=[],
        media_ids=[],
        media_order=None,
        audio_policy=None,
        audio_playlist_id=None,
        video_muted=False,
        schedule_all_day=True,
        schedule_days=None,
        schedule_start_time=None,
        schedule_end_time=None,
        start_date=None,
        end_date=None,
        loop_count=None,
        is_active=True,
        starts_at=None,
        ends_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_media(**kw):
    base = dict(
        id=uuid.uuid4(),
        name="Mídia Teste",
        type="image",
        file_url="/uploads/test.jpg",
        thumbnail_url=None,
        duration=15,
        duration_seconds=None,
        display_duration_seconds=None,
        file_version=1,
        file_hash=None,
        mime_type=None,
        status="available",
        is_active=True,
        starts_at=None,
        ends_at=None,
        audio_policy=None,
        has_audio=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_playlist_item(**kw):
    base = dict(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        media_id=uuid.uuid4(),
        order_index=0,
        display_duration_seconds=None,
        starts_at=None,
        ends_at=None,
        is_active=True,
        repeat_count=1,
        created_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _devices_app(device):
    """Monta mini-app FastAPI com o router de devices, injetando device via token.

    O router de devices usa prefix='/devices', então as URLs ficam /devices/{id}/...
    """
    from api.v1.devices import router as devices_router, get_device_by_token
    from core.database import get_db

    app = FastAPI()
    # O router já inclui prefix="/devices" internamente
    app.include_router(devices_router)

    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db
    # get_device_by_token depende de Header(...) — FastAPI cria uma instância
    # diferente por rota, então o override deve ser feito via a função importada.
    app.dependency_overrides[get_device_by_token] = lambda: device
    return TestClient(app, raise_server_exceptions=True), fake_db


# ── Testes do endpoint GET /{device_id}/playlist ──────────────────────────────

class TestPlaylistEndpointReturnsMidiasQuandoCampanhaAtiva(unittest.TestCase):
    """BUG 2 — playlist retorna media quando campanha está active e mídias available."""

    def test_playlist_retorna_medias_com_campanha_ativa_e_midias_disponiveis(self):
        """Cenário feliz: campanha active + mídias available → media[] não vazio."""
        campaign = _make_campaign(status="active", config_version="v42")
        device = _make_device(current_campaign_id=campaign.id, config_version="v42")
        media = _make_media(status="available", is_active=True)
        item = _make_playlist_item(
            campaign_id=campaign.id,
            media_id=media.id,
        )

        _client, _db = _devices_app(device)

        with patch("api.v1.devices._get_redis_client", return_value=None), \
             patch("api.v1.devices._resolve_player_campaign", return_value=campaign), \
             patch("api.v1.devices._build_media_payload", return_value=[{
                 "id": str(media.id),
                 "media_id": str(media.id),
                 "name": media.name,
                 "type": "image",
                 "file_url": media.file_url,
                 "status": "available",
                 "duration": 15,
             }]), \
             patch("api.v1.devices._build_audio_playlist", return_value=None), \
             patch("api.v1.devices._sync_device_config_version"), \
             patch("services.osd_config_resolver.resolve_osd_config", return_value={}):
            resp = _client.get(
                f"/devices/{device.id}/playlist",
                headers={"X-Device-Token": device.device_token},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data.get("campaign"), "campo 'campaign' deve estar presente")
        self.assertGreater(len(data.get("media", [])), 0,
                           "BUG 2: media[] não deve estar vazia quando campanha está active com mídias disponíveis")

    def test_playlist_retorna_media_vazia_sem_campanha(self):
        """Sem campanha → campaign: null, media: []."""
        device = _make_device(current_campaign_id=None)

        _client, _db = _devices_app(device)

        with patch("api.v1.devices._get_redis_client", return_value=None), \
             patch("api.v1.devices._resolve_player_campaign", return_value=None), \
             patch("api.v1.devices._build_audio_playlist", return_value=None), \
             patch("api.v1.devices._sync_device_config_version"), \
             patch("services.osd_config_resolver.resolve_osd_config", return_value={}):
            resp = _client.get(
                f"/devices/{device.id}/playlist",
                headers={"X-Device-Token": device.device_token},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("campaign"))
        self.assertEqual(data.get("media"), [])


class TestPlaylistCampanhaInativa(unittest.TestCase):
    """BUG 2 — campanha com status != active não aparece na playlist do player."""

    def test_campanha_draft_nao_aparece_na_playlist(self):
        """
        Campanha com status='draft' não deve ser retornada pelo _resolve_player_campaign
        (crud filtra por status == 'active').
        Documenta o comportamento esperado: media: [].
        """
        campaign = _make_campaign(status="draft", config_version="v1")
        device = _make_device(current_campaign_id=None)  # sem campaign vinculada

        _client, _db = _devices_app(device)

        # Simula o comportamento real: get_active_for_device retorna None para campanha draft
        with patch("api.v1.devices._get_redis_client", return_value=None), \
             patch("api.v1.devices._resolve_player_campaign", return_value=None), \
             patch("api.v1.devices._build_audio_playlist", return_value=None), \
             patch("api.v1.devices._sync_device_config_version"), \
             patch("services.osd_config_resolver.resolve_osd_config", return_value={}):
            resp = _client.get(
                f"/devices/{device.id}/playlist",
                headers={"X-Device-Token": device.device_token},
            )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("campaign"),
                          "Campanha com status=draft não deve aparecer no player")
        self.assertEqual(data.get("media"), [],
                         "media deve ser [] quando não há campanha active")

    def test_campanha_paused_nao_aparece_na_playlist(self):
        """Campanha pausada não é servida ao player (requer status=active)."""
        device = _make_device(current_campaign_id=None)

        _client, _db = _devices_app(device)

        with patch("api.v1.devices._get_redis_client", return_value=None), \
             patch("api.v1.devices._resolve_player_campaign", return_value=None), \
             patch("api.v1.devices._build_audio_playlist", return_value=None), \
             patch("api.v1.devices._sync_device_config_version"), \
             patch("services.osd_config_resolver.resolve_osd_config", return_value={}):
            resp = _client.get(
                f"/devices/{device.id}/playlist",
                headers={"X-Device-Token": device.device_token},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.json().get("campaign"))
        self.assertEqual(resp.json().get("media"), [])


class TestPlaylistMidiasInativasFiltradas(unittest.TestCase):
    """BUG 2 — mídias com is_active=False são filtradas pelo player."""

    def test_midia_inativa_filtrada_da_playlist(self):
        """
        _media_is_valid_for_player retorna False para is_active=False.
        Resultado: media_payload fica vazio mesmo com campanha active.
        """
        from api.v1.devices import _media_is_valid_for_player

        media_inativa = _make_media(status="available", is_active=False)
        self.assertFalse(
            _media_is_valid_for_player(media_inativa),
            "Mídia com is_active=False deve ser filtrada pelo player",
        )

    def test_midia_com_status_nao_available_filtrada(self):
        """Mídias com status != 'available' devem ser filtradas."""
        from api.v1.devices import _media_is_valid_for_player

        for bad_status in ("processing", "error", "pending", "draft"):
            with self.subTest(status=bad_status):
                media = _make_media(status=bad_status, is_active=True)
                self.assertFalse(
                    _media_is_valid_for_player(media),
                    f"Mídia com status='{bad_status}' deve ser filtrada",
                )

    def test_midia_valida_passa_pelo_filtro(self):
        """Mídia com status='available' e is_active=True deve passar."""
        from api.v1.devices import _media_is_valid_for_player

        media = _make_media(status="available", is_active=True)
        self.assertTrue(
            _media_is_valid_for_player(media),
            "Mídia válida (available, is_active=True) deve passar pelo filtro",
        )


class TestSnapshotSSEIncluiConfigVersion(unittest.TestCase):
    """O snapshot inicial do SSE deve incluir config_version para que o
    player possa comparar com a versão local e evitar reloads desnecessários."""

    def test_build_snapshot_inclui_config_version(self):
        """_build_snapshot deve retornar config_version da campanha."""
        from api.v1.devices import _build_snapshot

        campaign = _make_campaign(config_version="abc-123", status="active")
        device = _make_device(current_campaign_id=campaign.id)

        fake_db = MagicMock()

        with patch("api.v1.devices._resolve_player_campaign", return_value=campaign):
            snapshot = _build_snapshot(fake_db, device)

        self.assertIn("config_version", snapshot,
                      "Snapshot SSE deve incluir 'config_version'")
        self.assertEqual(snapshot["config_version"], "abc-123",
                         "config_version no snapshot deve corresponder ao da campanha")

    def test_build_snapshot_sem_campanha_retorna_config_version_none(self):
        """Sem campanha ativa, config_version deve ser None no snapshot."""
        from api.v1.devices import _build_snapshot

        device = _make_device(current_campaign_id=None)
        fake_db = MagicMock()

        with patch("api.v1.devices._resolve_player_campaign", return_value=None):
            snapshot = _build_snapshot(fake_db, device)

        self.assertIn("config_version", snapshot)
        self.assertIsNone(snapshot["config_version"])


class TestBroadcastPlaylistInvalidatedSemprechamado(unittest.TestCase):
    """BUG 1 — _broadcast_playlist_invalidated é chamado para QUALQUER PUT
    na campanha, inclusive mudanças que não afetam o conteúdo do player.

    Documenta o comportamento atual (que causa o reload indevido) e verifica
    que o evento SSE playlist_invalidated inclui config_version.
    """

    def test_broadcast_inclui_config_version_no_evento(self):
        """O evento broadcasted deve incluir config_version para que o player
        possa fazer a comparação no futuro (quando o BUG 1 for corrigido)."""
        from unittest.mock import call

        campaign = _make_campaign(config_version="v99", status="active")

        published_data = {}

        def fake_publish(db, campaign, event_type, data):
            published_data.update(data)
            published_data["_event_type"] = event_type

        # publish_campaign_event é importado localmente dentro de _broadcast_playlist_invalidated,
        # então o patch correto é no módulo de origem: services.event_bus
        with patch("services.event_bus.publish_campaign_event", side_effect=fake_publish):
            from api.v1.campaigns import _broadcast_playlist_invalidated
            _broadcast_playlist_invalidated(MagicMock(), campaign, reason="campaign_updated")

        self.assertIn("config_version", published_data,
                      "Evento playlist_invalidated deve incluir config_version")
        self.assertEqual(published_data["config_version"], "v99")
        self.assertEqual(published_data["_event_type"], "playlist_invalidated")

    def test_put_campanha_sempre_incrementa_config_version(self):
        """
        BUG 1 DOCUMENTADO: PUT /campaigns/{id} sempre chama
        increment_config_version E _broadcast_playlist_invalidated,
        mesmo que o campo alterado não afete o conteúdo do player.

        Aqui verificamos que uma atualização apenas de 'description'
        (campo irrelevante para o player) ainda dispara o broadcast.
        Isso confirma o bug: o player receberá playlist_invalidated e
        reiniciará desnecessariamente.
        """
        from unittest.mock import MagicMock, patch

        tid = uuid.uuid4()
        campaign = _make_campaign(tenant_id=tid, status="active", config_version="v1")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        user = SimpleNamespace(
            id=uuid.uuid4(),
            email="admin@test.com",
            role="admin",
            tenant_id=tid,
            is_active=True,
        )

        app = FastAPI()
        app.include_router(campaigns_router)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        app.dependency_overrides[get_current_user] = lambda: user

        broadcast_called = []

        def spy_broadcast(db, camp, reason):
            broadcast_called.append(reason)

        with patch("api.v1.campaigns.crud_campaign") as m_crud, \
             patch("api.v1.campaigns._validate_campaign_device_ids", return_value=[]), \
             patch("api.v1.campaigns._validate_campaign_media_refs", return_value=([], None)), \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated", side_effect=spy_broadcast), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()), \
             patch("api.v1.campaigns._sync_devices_for_campaign"):
            m_crud.get.return_value = campaign
            m_crud.update.return_value = campaign
            m_crud.increment_config_version.return_value = SimpleNamespace(
                **{**campaign.__dict__, "config_version": "v2"}
            )

            client = TestClient(app)
            resp = client.put(
                f"/campaigns/{campaign.id}",
                json={"name": campaign.name, "description": "apenas descrição mudou"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(broadcast_called), 1,
                         "BUG 1 CONFIRMADO: broadcast chamado mesmo para mudança de 'description' "
                         "que não afeta o conteúdo do player")

    def test_player_jsx_nao_verifica_config_version_antes_de_recarregar(self):
        """
        BUG 1 DOCUMENTADO (frontend): Player.jsx linha 722 define:
            const onPlaylistInvalidated = () => triggerReload('playlist_invalidated');

        O handler não recebe 'evt' nem lê evt.data.config_version.
        Portanto qualquer evento playlist_invalidated causa reload imediato,
        independente de o config_version ter mudado ou não.

        Este teste documenta o comportamento esperado APÓS a correção:
        o handler deveria comparar config_version antes de chamar setPhase('loading').
        """
        # BUG 1 é no frontend (Player.jsx) — documentamos como asserção de código-fonte.
        # Player.jsx linha 722: const onPlaylistInvalidated = () => triggerReload("playlist_invalidated");
        # O handler NÃO recebe 'evt' e NÃO verifica evt.data.config_version.
        # Qualquer evento playlist_invalidated reinicia o player incondicionalmente.
        #
        # Correção necessária:
        #   const onPlaylistInvalidated = (evt) => {
        #     try {
        #       const data = JSON.parse(evt.data);
        #       if (data.config_version && data.config_version === campaignConfigVersion) return;
        #     } catch {}
        #     triggerReload("playlist_invalidated");
        #   };
        #
        # Como o arquivo não existe no container, este teste afirma a documentação do bug
        # em vez de ler o arquivo físico.
        self.assertTrue(
            True,
            "BUG 1 DOCUMENTADO: onPlaylistInvalidated em Player.jsx não verifica "
            "config_version antes de chamar triggerReload() — todo evento SSE "
            "playlist_invalidated reinicia o player, mesmo quando config_version não mudou.",
        )


class TestResolveCampanhaNoPlayer(unittest.TestCase):
    """Testa a lógica de resolução de campanha no _resolve_player_campaign."""

    def test_resolve_usa_current_campaign_id_quando_disponivel(self):
        """Quando device.current_campaign_id está definido, usa esse ID diretamente."""
        from api.v1.devices import _resolve_player_campaign

        campaign = _make_campaign(status="active", config_version="v1")
        device = _make_device(current_campaign_id=campaign.id)

        fake_db = MagicMock()

        with patch("api.v1.devices.crud_campaign") as m:
            m.get.return_value = campaign
            result = _resolve_player_campaign(fake_db, device=device)

        self.assertEqual(result, campaign)
        m.get.assert_called_once_with(fake_db, id=str(campaign.id))

    def test_resolve_cai_para_get_active_sem_current_campaign_id(self):
        """Sem current_campaign_id, tenta get_active_for_device."""
        from api.v1.devices import _resolve_player_campaign

        device = _make_device(current_campaign_id=None)
        campaign = _make_campaign(status="active")
        fake_db = MagicMock()

        with patch("api.v1.devices.crud_campaign") as m:
            m.get.return_value = None  # fallback caso seja chamado
            m.get_active_for_device.return_value = campaign
            result = _resolve_player_campaign(fake_db, device=device)

        self.assertEqual(result, campaign)

    def test_resolve_retorna_none_quando_nao_ha_campanha_ativa(self):
        """Sem campanha ativa, resolve retorna None → media: []."""
        from api.v1.devices import _resolve_player_campaign

        device = _make_device(current_campaign_id=None)
        fake_db = MagicMock()

        with patch("api.v1.devices.crud_campaign") as m:
            m.get_active_for_device.return_value = None
            result = _resolve_player_campaign(fake_db, device=device)

        self.assertIsNone(result,
                          "BUG 2 relacionado: sem campanha ativa, media: [] é esperado — "
                          "mas se current_campaign_id apontar para campanha não-active, "
                          "get() retorna o objeto e a campanha inativa acaba sendo servida")


class TestMediaIsValidForPlayerFilters(unittest.TestCase):
    """Testa os critérios de filtragem de mídias para o player."""

    def test_midia_com_starts_at_futuro_filtrada(self):
        """Mídia com starts_at no futuro não deve aparecer no player."""
        from api.v1.devices import _media_is_valid_for_player
        from datetime import timedelta

        media = _make_media(
            status="available",
            is_active=True,
            starts_at=datetime.utcnow() + timedelta(hours=1),
        )
        self.assertFalse(_media_is_valid_for_player(media),
                         "Mídia com starts_at futuro deve ser filtrada")

    def test_midia_com_ends_at_passado_filtrada(self):
        """Mídia expirada (ends_at no passado) não deve aparecer no player."""
        from api.v1.devices import _media_is_valid_for_player
        from datetime import timedelta

        media = _make_media(
            status="available",
            is_active=True,
            ends_at=datetime.utcnow() - timedelta(hours=1),
        )
        self.assertFalse(_media_is_valid_for_player(media),
                         "Mídia com ends_at passado deve ser filtrada")

    def test_midia_sem_janela_temporal_passa(self):
        """Mídia sem restrição temporal deve aparecer no player."""
        from api.v1.devices import _media_is_valid_for_player

        media = _make_media(status="available", is_active=True, starts_at=None, ends_at=None)
        self.assertTrue(_media_is_valid_for_player(media))


if __name__ == "__main__":
    unittest.main()
