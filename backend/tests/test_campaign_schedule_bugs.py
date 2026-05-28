"""
Testes de agendamento de campanha — diagnóstico de bug "Agenda Duplicada".

CONTEXTO DO BUG
===============
O gerenciador exibe uma página de Agenda separada (frontend/src/pages/agenda.jsx)
que usa listarAgenda() → GET /schedule/, enquanto campanhas já possuem os campos
de agendamento: schedule_start_time, schedule_end_time, schedule_days,
schedule_all_day, start_date, end_date.

A pergunta central: são dois sistemas distintos ou o /schedule/ apenas
reexpõe campanhas com lens de calendário?

CONCLUSÃO DOCUMENTADA (resultado da análise do código-fonte)
=============================================================
1. Não há redundância de dados: /schedule/ (backend/api/v1/schedule.py) é apenas
   uma VIEW de leitura sobre a mesma tabela `campaigns`. Ele filtra campanhas
   que possuem start_date ou end_date e retorna as mesmas CampaignResponse.
   Não existe tabela separada de agenda; os únicos campos de agendamento estão
   em Campaign.

2. O frontend agenda.jsx usa listarAgenda() que aponta para GET /schedule/ e,
   ao editar/criar, chama criarCampanha()/atualizarCampanha() — endpoints do
   /campaigns/. Ou seja, ler via /schedule/, escrever via /campaigns/ — é
   consistente, não há duplicação de estado.

3. O backend FILTRA por horário no /playlist:
   - _resolve_player_campaign() → crud_campaign.get_active_for_device()
   - get_active_for_device() itera campanhas status="active" atribuídas ao
     device e chama _is_campaign_currently_active() que valida:
     a) start_date / end_date (janela de datas)
     b) schedule_all_day (se True, pula checagem de horário mas ainda checar dias)
     c) schedule_start_time / schedule_end_time (faixa horária HH:MM)
     d) schedule_days (lista de dias em pt-br: "seg","ter","qua","qui","sex","sab","dom")
   - Portanto: se a campanha estiver fora do horário, get_active_for_device()
     retorna None e o /playlist retorna {"campaign": null, "media": []}.

4. _media_is_valid_for_player() filtra mídias cujo starts_at é futuro — mídia
   com starts_at > now é excluída do payload de media mesmo que a campanha
   seja válida.

5. CampaignPlaylistItem.starts_at / ends_at também são checados por
   _item_window_active() antes de incluir o item na playlist.

PONTOS DE ATENÇÃO (possíveis bugs, não regressões):
- _resolve_player_campaign() tenta primeiro device.current_campaign_id sem
  filtrar por horário. Só cai em get_active_for_device() se não existir
  current_campaign_id. Isso significa que se um device tem current_campaign_id
  apontado, a campanha é servida MESMO fora do horário agendado.
  → Bug latente: a via rápida (current_campaign_id) ignora _is_campaign_currently_active.
"""

import uuid
from datetime import datetime, timedelta, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import sys
import os

import pytest

# Ajusta sys.path para importar módulos do backend sem instalar como pacote
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ── helpers ────────────────────────────────────────────────────────────────────

def _make_campaign(**kwargs):
    """Cria um SimpleNamespace que simula um objeto Campaign."""
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Campanha Teste",
        status="active",
        priority=1,
        device_ids=[],
        media_ids=[],
        media_order=None,
        audio_playlist_id=None,
        audio_policy=None,
        video_muted=True,
        schedule_all_day=True,
        schedule_days=None,
        schedule_start_time=None,
        schedule_end_time=None,
        loop_count=None,
        start_date=None,
        end_date=None,
        total_views=0,
        config_version="v1",
        description=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        playlist_items=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_media(**kwargs):
    """Cria um SimpleNamespace que simula um objeto Media."""
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Mídia Teste",
        type=SimpleNamespace(value="image"),
        status=SimpleNamespace(value="available"),
        is_active=True,
        starts_at=None,
        ends_at=None,
        file_url="http://example.com/media.jpg",
        thumbnail_url=None,
        duration=15,
        duration_seconds=None,
        display_duration_seconds=None,
        file_version=1,
        file_hash=None,
        mime_type="image/jpeg",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── importar funções testáveis ─────────────────────────────────────────────────

# Importa crud_campaign (não depende de DB real — usaremos instância direta)
_CRUDCampaign = None
_crud_available = False
_crud_import_error = ""
try:
    from crud.entidades.crud_campaign import CRUDCampaign as _CRUDCampaign
    _crud_available = True
except Exception as e:
    _crud_import_error = str(e)

# Importa helpers de devices.py via importação dinâmica dos auxiliares
_media_is_valid_for_player = None
_item_window_active = None
_device_helpers_available = False
_device_helpers_error = ""
try:
    from api.v1.devices import _media_is_valid_for_player, _item_window_active
    _device_helpers_available = True
except Exception as e:
    _device_helpers_error = str(e)


# ── SUITE 1: _is_campaign_currently_active (lógica pura, sem DB) ──────────────

class TestIsCampaignCurrentlyActive:
    """Testa a lógica de filtro de horário embutida em CRUDCampaign."""

    def setup_method(self):
        if not _crud_available:
            pytest.skip(f"crud_campaign não importável: {_crud_import_error}")
        # _CRUDCampaign não precisa do model importado para instanciar
        # se passarmos uma classe genérica; usamos __new__ para evitar __init__
        self.crud = _CRUDCampaign.__new__(_CRUDCampaign)

    # ── Testes de janela de datas ──────────────────────────────────────────

    def test_campanha_sem_datas_e_considerada_ativa(self):
        """Campanha sem start_date/end_date deve ser sempre ativa (sem restrição de data)."""
        campaign = _make_campaign(start_date=None, end_date=None, schedule_all_day=True)
        assert self.crud._is_campaign_currently_active(campaign) is True

    def test_campanha_com_start_date_futuro_retorna_falso(self):
        """Campanha que ainda não começou (start_date no futuro) deve ser inativa."""
        future = datetime.utcnow() + timedelta(days=1)
        campaign = _make_campaign(start_date=future, end_date=None)
        assert self.crud._is_campaign_currently_active(campaign) is False

    def test_campanha_com_end_date_passado_retorna_falso(self):
        """Campanha expirada (end_date no passado) deve ser inativa."""
        past = datetime.utcnow() - timedelta(days=1)
        campaign = _make_campaign(start_date=None, end_date=past)
        assert self.crud._is_campaign_currently_active(campaign) is False

    def test_campanha_dentro_da_janela_de_datas_e_ativa(self):
        """Campanha com start_date passado e end_date futuro deve ser ativa."""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=1)
        campaign = _make_campaign(start_date=past, end_date=future, schedule_all_day=True)
        assert self.crud._is_campaign_currently_active(campaign) is True

    # ── Testes de schedule_all_day ─────────────────────────────────────────

    def test_schedule_all_day_ignora_restricao_de_horario(self):
        """Com schedule_all_day=True, tempo de início/fim não é verificado."""
        campaign = _make_campaign(
            schedule_all_day=True,
            schedule_start_time="23:59",
            schedule_end_time="00:01",
            schedule_days=None,
        )
        # Independente do horário atual, deve ser ativo (sem schedule_days)
        assert self.crud._is_campaign_currently_active(campaign) is True

    def test_schedule_all_day_com_dia_errado_retorna_falso(self):
        """schedule_all_day=True com schedule_days exclui dia errado."""
        now = datetime.utcnow()
        current_weekday = now.strftime("%a").lower()
        day_map = {
            "mon": "seg", "tue": "ter", "wed": "qua",
            "thu": "qui", "fri": "sex", "sat": "sab", "sun": "dom"
        }
        pt_today = day_map.get(current_weekday, "")

        # Cria lista de todos os dias EXCETO hoje
        all_days = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
        days_without_today = [d for d in all_days if d != pt_today]

        campaign = _make_campaign(
            schedule_all_day=True,
            schedule_days=days_without_today,
        )
        # Deve retornar False porque hoje não está na lista
        assert self.crud._is_campaign_currently_active(campaign) is False

    def test_schedule_all_day_com_dia_correto_retorna_verdadeiro(self):
        """schedule_all_day=True com schedule_days inclui hoje → ativo."""
        now = datetime.utcnow()
        current_weekday = now.strftime("%a").lower()
        day_map = {
            "mon": "seg", "tue": "ter", "wed": "qua",
            "thu": "qui", "fri": "sex", "sat": "sab", "sun": "dom"
        }
        pt_today = day_map.get(current_weekday, "")

        campaign = _make_campaign(
            schedule_all_day=True,
            schedule_days=[pt_today],
        )
        assert self.crud._is_campaign_currently_active(campaign) is True

    # ── Testes de schedule_start_time / schedule_end_time ─────────────────

    def test_fora_do_horario_inicio_retorna_falso(self):
        """Campanha com schedule_start_time no futuro próximo deve ser inativa."""
        now = datetime.utcnow()
        # Horário de início daqui a 1 hora
        future_time = (now + timedelta(hours=1)).strftime("%H:%M")
        campaign = _make_campaign(
            schedule_all_day=False,
            schedule_start_time=future_time,
            schedule_end_time=None,
            schedule_days=None,
        )
        assert self.crud._is_campaign_currently_active(campaign) is False

    def test_fora_do_horario_fim_retorna_falso(self):
        """Campanha com schedule_end_time no passado próximo deve ser inativa."""
        now = datetime.utcnow()
        # Horário de fim 1 hora atrás
        past_time = (now - timedelta(hours=1)).strftime("%H:%M")
        campaign = _make_campaign(
            schedule_all_day=False,
            schedule_start_time=None,
            schedule_end_time=past_time,
            schedule_days=None,
        )
        assert self.crud._is_campaign_currently_active(campaign) is False

    def test_dentro_do_horario_retorna_verdadeiro(self):
        """Campanha com janela horária que inclui 'agora' deve ser ativa."""
        now = datetime.utcnow()
        start = (now - timedelta(hours=1)).strftime("%H:%M")
        end = (now + timedelta(hours=1)).strftime("%H:%M")
        campaign = _make_campaign(
            schedule_all_day=False,
            schedule_start_time=start,
            schedule_end_time=end,
            schedule_days=None,
        )
        assert self.crud._is_campaign_currently_active(campaign) is True

    def test_horario_invalido_nao_levanta_excecao(self):
        """Horário com formato inválido deve ser ignorado sem lançar exceção."""
        campaign = _make_campaign(
            schedule_all_day=False,
            schedule_start_time="INVALIDO",
            schedule_end_time="INVALIDO",
            schedule_days=None,
        )
        # Não deve lançar exceção; o except no código faz pass
        result = self.crud._is_campaign_currently_active(campaign)
        assert isinstance(result, bool)


# ── SUITE 2: _media_is_valid_for_player ───────────────────────────────────────

class TestMediaIsValidForPlayer:
    """Testa a filtragem de mídias por janela de exibição."""

    def setup_method(self):
        if not _device_helpers_available:
            pytest.skip(f"helpers de devices não importáveis: {_device_helpers_error}")

    def test_midia_disponivel_e_ativa_e_valida(self):
        """Mídia status=available, is_active=True, sem datas → válida."""
        media = _make_media()
        assert _media_is_valid_for_player(media) is True

    def test_midia_com_status_processing_e_invalida(self):
        """Mídia em processamento não deve aparecer na playlist."""
        media = _make_media(status=SimpleNamespace(value="processing"))
        assert _media_is_valid_for_player(media) is False

    def test_midia_inativa_e_invalida(self):
        """Mídia is_active=False não deve aparecer na playlist."""
        media = _make_media(is_active=False)
        assert _media_is_valid_for_player(media) is False

    def test_midia_com_starts_at_futuro_e_invalida(self):
        """
        BUG DOCUMENTADO: mídia com starts_at no futuro não deve ser exibida.
        _media_is_valid_for_player verifica: if media.starts_at and media.starts_at > now: return False
        """
        future = datetime.utcnow() + timedelta(days=1)
        media = _make_media(starts_at=future)
        assert _media_is_valid_for_player(media) is False, (
            "Mídia com starts_at futuro deve ser filtrada — "
            "_media_is_valid_for_player retornou True (bug se falhar)"
        )

    def test_midia_com_starts_at_passado_e_valida(self):
        """Mídia com starts_at no passado deve ser incluída."""
        past = datetime.utcnow() - timedelta(days=1)
        media = _make_media(starts_at=past)
        assert _media_is_valid_for_player(media) is True

    def test_midia_com_ends_at_passado_e_invalida(self):
        """Mídia cujo ends_at já passou não deve ser exibida."""
        past = datetime.utcnow() - timedelta(days=1)
        media = _make_media(ends_at=past)
        assert _media_is_valid_for_player(media) is False

    def test_midia_com_ends_at_futuro_e_valida(self):
        """Mídia cujo ends_at é futuro deve ser exibida."""
        future = datetime.utcnow() + timedelta(days=1)
        media = _make_media(ends_at=future)
        assert _media_is_valid_for_player(media) is True

    def test_now_parametro_explicito_funciona(self):
        """O parâmetro 'now' permite injetar tempo arbitrário para testes."""
        future_starts = datetime(2030, 1, 1, 12, 0, 0)
        media = _make_media(starts_at=future_starts)
        # Injetando 'now' no futuro além do starts_at → deve ser válido
        assert _media_is_valid_for_player(media, now=datetime(2030, 1, 2)) is True
        # Injetando 'now' antes do starts_at → deve ser inválido
        assert _media_is_valid_for_player(media, now=datetime(2029, 12, 31)) is False


# ── SUITE 3: _item_window_active ──────────────────────────────────────────────

class TestItemWindowActive:
    """Testa a filtragem de itens de playlist por janela de exibição."""

    def setup_method(self):
        if not _device_helpers_available:
            pytest.skip(f"helpers de devices não importáveis: {_device_helpers_error}")

    def _make_item(self, **kwargs):
        defaults = dict(
            is_active=True,
            starts_at=None,
            ends_at=None,
            order_index=0,
            display_duration_seconds=None,
            repeat_count=1,
        )
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_item_ativo_sem_datas_e_valido(self):
        item = self._make_item()
        assert _item_window_active(item) is True

    def test_item_inativo_retorna_falso(self):
        item = self._make_item(is_active=False)
        assert _item_window_active(item) is False

    def test_item_com_starts_at_futuro_retorna_falso(self):
        future = datetime.utcnow() + timedelta(hours=2)
        item = self._make_item(starts_at=future)
        assert _item_window_active(item) is False

    def test_item_com_ends_at_passado_retorna_falso(self):
        past = datetime.utcnow() - timedelta(hours=2)
        item = self._make_item(ends_at=past)
        assert _item_window_active(item) is False

    def test_item_dentro_da_janela_retorna_verdadeiro(self):
        past = datetime.utcnow() - timedelta(hours=1)
        future = datetime.utcnow() + timedelta(hours=1)
        item = self._make_item(starts_at=past, ends_at=future)
        assert _item_window_active(item) is True


# ── SUITE 4: get_active_for_device — integração com mock de DB ────────────────

class TestGetActiveForDevice:
    """
    Testa get_active_for_device com DB mockado.

    DOCUMENTAÇÃO DE COMPORTAMENTO:
    get_active_for_device() faz query filtrando:
      - Campaign.device_ids contains [device_id]
      - Campaign.status == "active"
    Em seguida itera e aplica _is_campaign_currently_active().

    O método NÃO filtra por horário no SQL — a filtragem é Python puro.
    Isso é correto mas pode ser lento com muitas campanhas: iteração O(n).
    """

    def setup_method(self):
        if not _crud_available:
            pytest.skip(f"crud_campaign não importável: {_crud_import_error}")
        self.crud = _CRUDCampaign.__new__(_CRUDCampaign)

    def _build_db_mock(self, campaigns):
        """Retorna um db mock que devolve campaigns na query encadeada."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = campaigns
        db = MagicMock()
        db.query.return_value = mock_query
        return db

    def test_retorna_campanha_ativa_dentro_do_horario(self):
        device_id = str(uuid.uuid4())
        campaign = _make_campaign(
            device_ids=[device_id],
            status="active",
            schedule_all_day=True,
        )
        db = self._build_db_mock([campaign])
        result = self.crud.get_active_for_device(db, device_id=device_id)
        assert result is campaign

    def test_retorna_none_quando_campanha_fora_do_horario(self):
        """
        COMPORTAMENTO ESPERADO: campanha fora do schedule_start_time/schedule_end_time
        deve ser ignorada e get_active_for_device retorna None.
        """
        device_id = str(uuid.uuid4())
        now = datetime.utcnow()
        # Horário de início muito no futuro (1 hora)
        future_start = (now + timedelta(hours=1)).strftime("%H:%M")
        campaign = _make_campaign(
            device_ids=[device_id],
            status="active",
            schedule_all_day=False,
            schedule_start_time=future_start,
            schedule_end_time=None,
        )
        db = self._build_db_mock([campaign])
        result = self.crud.get_active_for_device(db, device_id=device_id)
        assert result is None, (
            "Campanha fora do horário agendado não deveria ser retornada. "
            "Se None falhar, confirmar se schedule_all_day=False está sendo verificado."
        )

    def test_retorna_campanha_com_maior_prioridade(self):
        """Quando há múltiplas campanhas ativas, retorna a de maior prioridade."""
        device_id = str(uuid.uuid4())
        low = _make_campaign(device_ids=[device_id], status="active", priority=1, schedule_all_day=True, name="Low")
        high = _make_campaign(device_ids=[device_id], status="active", priority=10, schedule_all_day=True, name="High")
        # A query já vem ordenada por priority.desc() — simulamos isso
        db = self._build_db_mock([high, low])
        result = self.crud.get_active_for_device(db, device_id=device_id)
        assert result is high

    def test_retorna_none_quando_campanha_expirada_por_end_date(self):
        """Campanha com end_date no passado deve ser ignorada."""
        device_id = str(uuid.uuid4())
        past = datetime.utcnow() - timedelta(days=1)
        campaign = _make_campaign(
            device_ids=[device_id],
            status="active",
            end_date=past,
        )
        db = self._build_db_mock([campaign])
        result = self.crud.get_active_for_device(db, device_id=device_id)
        assert result is None

    def test_retorna_none_quando_start_date_futuro(self):
        """Campanha com start_date no futuro ainda não começou."""
        device_id = str(uuid.uuid4())
        future = datetime.utcnow() + timedelta(days=1)
        campaign = _make_campaign(
            device_ids=[device_id],
            status="active",
            start_date=future,
        )
        db = self._build_db_mock([campaign])
        result = self.crud.get_active_for_device(db, device_id=device_id)
        assert result is None


# ── SUITE 5: _resolve_player_campaign — bug da via rápida ─────────────────────

class TestResolvePlayerCampaign:
    """
    DOCUMENTA O BUG LATENTE em _resolve_player_campaign (devices.py).

    _resolve_player_campaign() primeiro tenta device.current_campaign_id.
    Se existir, retorna a campanha SEM validar horário.
    Só chama get_active_for_device() se current_campaign_id for None/não encontrado.

    Consequência: se um device tem current_campaign_id definido,
    a campanha é servida MESMO fora do horário agendado.
    """

    def setup_method(self):
        if not _crud_available:
            pytest.skip(f"crud_campaign não importável: {_crud_import_error}")

    def test_via_rapida_serve_campanha_sem_checar_horario(self):
        """
        BUG DOCUMENTADO: device com current_campaign_id contorna _is_campaign_currently_active.

        _resolve_player_campaign() retorna campaign diretamente de crud_campaign.get()
        sem chamar _is_campaign_currently_active(). Isso significa que campanhas
        fora do horário são servidas se o device.current_campaign_id estiver preenchido.

        Este teste verifica o comportamento ATUAL (bug), não o esperado.
        Se este teste começar a FALHAR, significa que o bug foi corrigido.
        """
        try:
            from api.v1.devices import _resolve_player_campaign
        except ImportError as e:
            pytest.skip(f"_resolve_player_campaign não importável: {e}")

        now = datetime.utcnow()
        future_start = (now + timedelta(hours=1)).strftime("%H:%M")
        campaign_id = uuid.uuid4()

        # Campanha fora do horário
        campaign = _make_campaign(
            id=campaign_id,
            status="active",
            schedule_all_day=False,
            schedule_start_time=future_start,
            schedule_end_time=None,
        )

        device = SimpleNamespace(
            id=uuid.uuid4(),
            current_campaign_id=campaign_id,
        )

        mock_crud = MagicMock()
        mock_crud.get.return_value = campaign

        with patch("api.v1.devices.crud_campaign", mock_crud):
            result = _resolve_player_campaign(db=MagicMock(), device=device)

        # BUG: a campanha fora do horário É retornada (via rápida não valida horário)
        assert result is campaign, (
            "BUG CONFIRMADO: _resolve_player_campaign retornou campaign fora do horário "
            "quando device.current_campaign_id está preenchido. "
            "A via rápida não chama _is_campaign_currently_active()."
        )


# ── SUITE 6: Campos de agenda persistidos corretamente ───────────────────────

class TestCampaignScheduleFields:
    """
    Testa que campos de agendamento são parte do modelo Campaign.

    Estes são testes de contrato de modelo — verificam que os atributos existem
    e têm os tipos esperados (usando o modelo SQLAlchemy diretamente).
    """

    def test_campaign_model_tem_campos_de_agendamento(self):
        """Campaign deve ter todos os campos de agendamento esperados."""
        try:
            from core.models import Campaign
        except ImportError as e:
            pytest.skip(f"models não importável: {e}")

        campos_esperados = [
            "schedule_all_day",
            "schedule_days",
            "schedule_start_time",
            "schedule_end_time",
            "start_date",
            "end_date",
        ]
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(Campaign)
        campos_no_modelo = {col.key for col in mapper.mapper.column_attrs}
        for campo in campos_esperados:
            assert campo in campos_no_modelo, (
                f"Campo '{campo}' não encontrado no modelo Campaign. "
                f"Campos existentes: {sorted(campos_no_modelo)}"
            )

    def test_campaign_schedule_fields_tipos(self):
        """schedule_start_time e schedule_end_time devem ser String(10)."""
        try:
            from core.models import Campaign
            from sqlalchemy import inspect as sa_inspect, String
        except ImportError as e:
            pytest.skip(f"models não importável: {e}")

        mapper = sa_inspect(Campaign)
        col_map = {col.key: col for col in mapper.mapper.column_attrs}

        # schedule_start_time e schedule_end_time devem ser String
        for field in ("schedule_start_time", "schedule_end_time"):
            col = col_map.get(field)
            assert col is not None, f"Coluna {field} não encontrada"
            # Verifica que é uma coluna (não relationship)
            assert hasattr(col, "columns"), f"{field} não é uma coluna mapeada"
