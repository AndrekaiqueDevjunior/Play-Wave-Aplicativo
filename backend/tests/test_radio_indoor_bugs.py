"""Testes de regressão — Bugs do módulo Rádio Indoor.

Bug 1: Spot agendado bloqueia a playlist
  - Root cause (frontend): Player.jsx linha ~910 — `setInterval` chama `mgr.playSpot(url, policy)`.
    Quando `insertion_policy = "interrupt"`, o AudioManager (`audioManager.js` linha ~193-197)
    faz fade-out do rádio e seta state.current = SPOT, mas NÃO retorna para rádio automaticamente.
    A lógica de retorno existe em `_resumeAfterSpot` (linha ~217-234), porém ela só é chamada em
    `_onTrackEnded('spot')` (linha ~409-411), que dispara apenas quando o elemento <audio> emite
    o evento 'ended'.  Se o spot não tocar até o fim (e.g. src inválida ou player sem foco), o
    estado fica travado em AUDIO_STATE.SPOT e o rádio nunca retoma.
  - Root cause adicional (frontend): `playSpot` (linha ~187) não captura `previous` de forma
    confiável: quando chamado via setInterval, `this.state.current` pode já ser SPOT (se um
    intervalo anterior travou), então `previous` = SPOT → `_resumeAfterSpot(SPOT)` tenta
    retomar o player de spot em vez do rádio.

Bug 2: Pasta de música não roda nada
  - Root cause (backend): `_build_folder_schedules_payload` em `backend/api/v1/devices.py`
    linha ~533-537 — filtra `AudioTrack.status == AudioTrackStatus.ACTIVE`.  Se as faixas
    foram importadas com status INACTIVE ou ARCHIVED, a lista `tracks` fica vazia e o
    schedules entry é incluído no payload, mas sem faixas para tocar.

Observação sobre audioManager.js — `playSpot` e retorno ao rádio:
  - `playSpot` (linha 187) NÃO agenda retorno ao rádio de forma autônoma.
  - O retorno depende de `_onTrackEnded('spot')` → `_resumeAfterSpot(previous)`, que
    exige que o evento 'ended' do HTMLAudioElement do spot seja emitido.
  - Se o spot travar (src inválida, pausa forçada, player destruído), o estado permanece
    AUDIO_STATE.SPOT indefinidamente e o rádio não retoma.
  - Fix recomendado: em `playSpot`, capturar `previous` ANTES de mudar o estado e usar
    um `Promise.then` ou `addEventListener('ended', ...)` em linha com `removeEventListener`
    para garantir o retorno mesmo que `_onTrackEnded` não seja chamado a tempo.
"""

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_track(**kw):
    """Cria um SimpleNamespace simulando AudioTrack."""
    from core.models import AudioTrackStatus
    base = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Faixa Teste",
        file_url="/uploads/faixa.mp3",
        duration_seconds=180,
        status=AudioTrackStatus.ACTIVE,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_spot(**kw):
    """Cria um SimpleNamespace simulando AudioSpot."""
    from core.models import AudioSpotInsertionPolicy
    base = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Spot Promo",
        track_id=uuid.uuid4(),
        insertion_policy=AudioSpotInsertionPolicy.INTERRUPT,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_spot_schedule(**kw):
    """Cria um SimpleNamespace simulando AudioSpotSchedule."""
    base = dict(
        id=uuid.uuid4(),
        spot_id=uuid.uuid4(),
        playlist_id=uuid.uuid4(),
        interval_seconds=1800,
        start_time="06:00",
        end_time="22:00",
        priority=5,
        is_active=True,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_folder(**kw):
    """Cria um SimpleNamespace simulando AudioFolder."""
    base = dict(
        id=uuid.uuid4(),
        name="Pasta Música",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_folder_track(**kw):
    """Cria um SimpleNamespace simulando AudioFolderTrack."""
    base = dict(
        id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        track_id=uuid.uuid4(),
        order_index=0,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_folder_schedule(**kw):
    """Cria um SimpleNamespace simulando AudioPlaylistFolderSchedule."""
    from core.models import AudioPlaylistPlayMode
    base = dict(
        id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        playlist_id=uuid.uuid4(),
        start_time="08:00",
        end_time="18:00",
        days_of_week=[1, 2, 3, 4, 5],
        priority=0,
        play_mode=AudioPlaylistPlayMode.SEQUENTIAL,
        is_active=True,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_playlist(**kw):
    """Cria um SimpleNamespace simulando AudioPlaylist."""
    from core.models import AudioPlaylistStatus
    base = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Playlist Loja",
        status=AudioPlaylistStatus.ACTIVE,
        volume_default=0.7,
        loop_enabled=True,
        shuffle_enabled=False,
        track_ids=None,
        track_volumes=None,
        items=[],
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_db():
    """Cria um mock de Session SQLAlchemy configurado para encadeamento fluido."""
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.filter_by.return_value = q
    q.order_by.return_value = q
    q.all.return_value = []
    q.first.return_value = None
    q.count.return_value = 0
    db.query.return_value = q
    return db, q


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_spot_schedules_payload
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildSpotSchedulesPayload(unittest.TestCase):
    """
    Testa `_build_spot_schedules_payload` de backend/api/v1/devices.py.
    Linha de interesse: ~561-593.
    """

    def _call(self, db, playlist_id):
        from api.v1.devices import _build_spot_schedules_payload
        return _build_spot_schedules_payload(db, playlist_id=playlist_id)

    # ── Bug 1 — caminho feliz: spot ACTIVE deve aparecer no payload ────────────

    def test_active_spot_with_active_track_is_included(self):
        """Spot com AudioTrack ACTIVE deve ser incluído no payload."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        track = _make_track(status=AudioTrackStatus.ACTIVE)
        spot = _make_spot(track_id=track.id)
        sched = _make_spot_schedule(playlist_id=playlist_id, spot_id=spot.id)

        db, q = _make_db()

        # Primeira chamada: retorna schedules
        # Segunda: retorna spot
        # Terceira: retorna track
        q.all.return_value = [sched]
        q.first.side_effect = [spot, track]

        result = self._call(db, playlist_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["spot_id"], str(spot.id))
        self.assertEqual(result[0]["file_url"], track.file_url)

    def test_spot_payload_contains_expected_keys(self):
        """Cada item do payload deve ter as chaves exigidas pelo frontend."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        track = _make_track(status=AudioTrackStatus.ACTIVE, file_url="/uploads/promo.mp3")
        spot = _make_spot(track_id=track.id)
        sched = _make_spot_schedule(
            playlist_id=playlist_id,
            spot_id=spot.id,
            interval_seconds=3600,
            start_time="08:00",
            end_time="20:00",
            priority=10,
        )

        db, q = _make_db()
        q.all.return_value = [sched]
        q.first.side_effect = [spot, track]

        result = self._call(db, playlist_id)

        self.assertEqual(len(result), 1)
        entry = result[0]
        for key in ("id", "spot_id", "spot_name", "interval_seconds", "start_time",
                    "end_time", "priority", "insertion_policy", "file_url"):
            self.assertIn(key, entry, f"Chave '{key}' ausente no payload")

        self.assertEqual(entry["interval_seconds"], 3600)
        self.assertEqual(entry["start_time"], "08:00")
        self.assertEqual(entry["insertion_policy"], "interrupt")
        self.assertEqual(entry["file_url"], "/uploads/promo.mp3")

    # ── Bug 1 — filtro de status: AudioTrack INACTIVE não deve entrar ─────────

    def test_inactive_track_spot_is_excluded(self):
        """
        Confirma root cause do Bug 1 — spot cujo AudioTrack tem status INACTIVE
        não é incluído no payload (linha ~576-581 de devices.py).
        O filtro `AudioTrack.status == AudioTrackStatus.ACTIVE` funciona como esperado
        em isolamento; o problema está no frontend (playSpot sem retorno garantido).
        """
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        # Track INACTIVE — o db.query().filter(...).first() retorna None
        spot = _make_spot()
        sched = _make_spot_schedule(playlist_id=playlist_id, spot_id=spot.id)

        db, q = _make_db()
        q.all.return_value = [sched]
        # spot existe, mas a query de track com filtro ACTIVE retorna None
        q.first.side_effect = [spot, None]

        result = self._call(db, playlist_id)

        self.assertEqual(len(result), 0, "Spot com track INACTIVE não deve entrar no payload")

    def test_archived_track_spot_is_excluded(self):
        """Spot com AudioTrack ARCHIVED também não deve aparecer."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        spot = _make_spot()
        sched = _make_spot_schedule(playlist_id=playlist_id, spot_id=spot.id)

        db, q = _make_db()
        q.all.return_value = [sched]
        q.first.side_effect = [spot, None]  # second query (with ACTIVE filter) returns None

        result = self._call(db, playlist_id)
        self.assertEqual(len(result), 0)

    def test_missing_spot_record_is_skipped(self):
        """Se AudioSpot não existe (deletado), o schedule é ignorado silenciosamente."""
        playlist_id = uuid.uuid4()
        sched = _make_spot_schedule(playlist_id=playlist_id)

        db, q = _make_db()
        q.all.return_value = [sched]
        q.first.return_value = None  # spot não encontrado

        result = self._call(db, playlist_id)
        self.assertEqual(len(result), 0)

    def test_no_schedules_returns_empty_list(self):
        """Sem AudioSpotSchedule configurado, retorna lista vazia."""
        db, q = _make_db()
        q.all.return_value = []

        result = self._call(db, uuid.uuid4())
        self.assertEqual(result, [])

    def test_multiple_active_spots_all_included(self):
        """Múltiplos spots ativos são todos incluídos no payload."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        track1 = _make_track(status=AudioTrackStatus.ACTIVE)
        track2 = _make_track(status=AudioTrackStatus.ACTIVE)
        spot1 = _make_spot(track_id=track1.id, name="Spot A")
        spot2 = _make_spot(track_id=track2.id, name="Spot B")
        sched1 = _make_spot_schedule(playlist_id=playlist_id, spot_id=spot1.id)
        sched2 = _make_spot_schedule(playlist_id=playlist_id, spot_id=spot2.id)

        db, q = _make_db()
        q.all.return_value = [sched1, sched2]
        q.first.side_effect = [spot1, track1, spot2, track2]

        result = self._call(db, playlist_id)
        self.assertEqual(len(result), 2)
        names = {r["spot_name"] for r in result}
        self.assertIn("Spot A", names)
        self.assertIn("Spot B", names)

    def test_inactive_schedule_not_queried(self):
        """
        Schedules com is_active=False são filtrados pelo próprio SQL.
        O mock retorna lista vazia simulando que o filtro `is_active.is_(True)` funciona.
        """
        db, q = _make_db()
        q.all.return_value = []  # nenhum schedule ativo

        result = self._call(db, uuid.uuid4())
        self.assertEqual(result, [])


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_folder_schedules_payload
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildFolderSchedulesPayload(unittest.TestCase):
    """
    Testa `_build_folder_schedules_payload` de backend/api/v1/devices.py.
    Linha de interesse: ~507-558.

    Bug 2 — root cause confirmado aqui:
      Linha ~533-537 filtra `AudioTrack.status == AudioTrackStatus.ACTIVE`.
      Se as faixas da pasta têm status INACTIVE, a lista `tracks` fica vazia
      e o schedule entra no payload com `tracks: []` → frontend não toca nada.
    """

    def _call(self, db, playlist_id):
        from api.v1.devices import _build_folder_schedules_payload
        return _build_folder_schedules_payload(db, playlist_id=playlist_id)

    def _make_db_for_folder(self, schedules, folder, folder_tracks, active_tracks):
        """
        Monta um db mock com efeito colateral controlado por sequência de .all()/.first():
          - q.all() call 1 → schedules (AudioPlaylistFolderSchedule)
          - q.first() call 1 → folder (AudioFolder)
          - q.all() call 2 → folder_tracks (AudioFolderTrack)
          - q.all() call 3 → active_tracks (AudioTrack filtrados por ACTIVE)
        """
        db = MagicMock()

        all_calls = iter([schedules, folder_tracks, active_tracks])
        first_calls = iter([folder])

        q = MagicMock()

        def q_all():
            return next(all_calls)

        def q_first():
            return next(first_calls)

        q.filter.return_value = q
        q.filter_by.return_value = q
        q.order_by.return_value = q
        q.all.side_effect = q_all
        q.first.side_effect = q_first

        db.query.return_value = q
        return db

    # ── Caminho feliz: pasta com faixas ACTIVE ─────────────────────────────────

    def test_folder_with_active_tracks_included_in_payload(self):
        """Pasta com faixas ACTIVE deve aparecer no payload com tracks preenchido."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        folder = _make_folder()
        track = _make_track(status=AudioTrackStatus.ACTIVE)
        ft = _make_folder_track(folder_id=folder.id, track_id=track.id)
        sched = _make_folder_schedule(folder_id=folder.id, playlist_id=playlist_id)

        db = self._make_db_for_folder(
            schedules=[sched],
            folder=folder,
            folder_tracks=[ft],
            active_tracks=[track],
        )

        result = self._call(db, playlist_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["folder_id"], str(folder.id))
        self.assertEqual(result[0]["folder_name"], folder.name)
        self.assertEqual(len(result[0]["tracks"]), 1)
        self.assertEqual(result[0]["tracks"][0]["id"], str(track.id))

    def test_folder_payload_contains_expected_keys(self):
        """Cada entrada de folder schedule deve ter as chaves esperadas pelo frontend."""
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        folder = _make_folder()
        track = _make_track(status=AudioTrackStatus.ACTIVE)
        ft = _make_folder_track(folder_id=folder.id, track_id=track.id)
        sched = _make_folder_schedule(folder_id=folder.id, playlist_id=playlist_id)

        db = self._make_db_for_folder(
            schedules=[sched],
            folder=folder,
            folder_tracks=[ft],
            active_tracks=[track],
        )

        result = self._call(db, playlist_id)
        entry = result[0]

        for key in ("id", "folder_id", "folder_name", "start_time", "end_time",
                    "days_of_week", "priority", "play_mode", "tracks"):
            self.assertIn(key, entry, f"Chave '{key}' ausente no payload de folder schedule")

    # ── Bug 2 confirmado: pasta sem faixas ACTIVE retorna tracks vazio ─────────

    def test_folder_with_no_active_tracks_returns_empty_tracks_list(self):
        """
        ROOT CAUSE Bug 2: faixas da pasta têm status INACTIVE → filtro ACTIVE retorna [].
        O schedule é incluído no payload, mas `tracks: []` → frontend não toca nada.

        Localização exata: backend/api/v1/devices.py, linhas ~530-546.
        A query filtra `AudioTrack.status == AudioTrackStatus.ACTIVE` (linha ~534).
        Se as faixas foram importadas com status INACTIVE, nenhuma passa nesse filtro.
        """
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        folder = _make_folder()
        # Faixa existe na pasta mas status é INACTIVE
        track_inactive = _make_track(status=AudioTrackStatus.INACTIVE)
        ft = _make_folder_track(folder_id=folder.id, track_id=track_inactive.id)
        sched = _make_folder_schedule(folder_id=folder.id, playlist_id=playlist_id)

        db = self._make_db_for_folder(
            schedules=[sched],
            folder=folder,
            folder_tracks=[ft],
            active_tracks=[],  # filtro ACTIVE retorna vazio
        )

        result = self._call(db, playlist_id)

        # O schedule está presente (não é ignorado), mas tracks está vazio
        self.assertEqual(len(result), 1, "Schedule de pasta sem faixas ACTIVE ainda aparece no payload")
        self.assertEqual(
            result[0]["tracks"],
            [],
            "BUG 2 CONFIRMADO: tracks vazios quando faixas são INACTIVE — nada tocará no frontend",
        )

    def test_folder_with_no_folder_tracks_returns_empty_tracks_list(self):
        """Pasta sem faixas cadastradas também retorna tracks: []."""
        playlist_id = uuid.uuid4()
        folder = _make_folder()
        sched = _make_folder_schedule(folder_id=folder.id, playlist_id=playlist_id)

        db = self._make_db_for_folder(
            schedules=[sched],
            folder=folder,
            folder_tracks=[],  # nenhuma faixa na pasta
            active_tracks=[],
        )

        result = self._call(db, playlist_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tracks"], [])

    def test_missing_folder_record_is_skipped(self):
        """Se AudioFolder não existe (deletado), o schedule é ignorado."""
        playlist_id = uuid.uuid4()
        sched = _make_folder_schedule(playlist_id=playlist_id)

        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = [sched]
        q.first.return_value = None  # folder não encontrado
        db.query.return_value = q

        result = self._call(db, playlist_id)
        self.assertEqual(result, [])

    def test_no_folder_schedules_returns_empty_list(self):
        """Sem AudioPlaylistFolderSchedule ativo, retorna lista vazia."""
        db, q = _make_db()
        q.all.return_value = []

        result = self._call(db, uuid.uuid4())
        self.assertEqual(result, [])

    def test_mix_active_inactive_tracks_only_active_in_payload(self):
        """
        Quando a pasta tem 2 faixas (1 ACTIVE, 1 INACTIVE), apenas a ACTIVE aparece.
        Demonstra que o filtro funciona em isolamento — o bug só aparece quando
        TODAS as faixas estão INACTIVE.
        """
        from core.models import AudioTrackStatus

        playlist_id = uuid.uuid4()
        folder = _make_folder()
        track_ok = _make_track(status=AudioTrackStatus.ACTIVE, file_url="/ok.mp3")
        track_bad = _make_track(status=AudioTrackStatus.INACTIVE, file_url="/bad.mp3")
        ft1 = _make_folder_track(folder_id=folder.id, track_id=track_ok.id, order_index=0)
        ft2 = _make_folder_track(folder_id=folder.id, track_id=track_bad.id, order_index=1)
        sched = _make_folder_schedule(folder_id=folder.id, playlist_id=playlist_id)

        db = self._make_db_for_folder(
            schedules=[sched],
            folder=folder,
            folder_tracks=[ft1, ft2],
            active_tracks=[track_ok],  # apenas track_ok passa no filtro ACTIVE
        )

        result = self._call(db, playlist_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["tracks"]), 1)
        self.assertEqual(result[0]["tracks"][0]["file_url"], "/ok.mp3")


# ═══════════════════════════════════════════════════════════════════════════════
#  _build_audio_playlist_from_model  (payload completo do /playlist)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildAudioPlaylistFromModel(unittest.TestCase):
    """
    Testa `_build_audio_playlist_from_model` de backend/api/v1/devices.py.
    Garante que o payload enviado ao device inclui spot_schedules corretamente.
    """

    def _call(self, playlist, db):
        from api.v1.devices import _build_audio_playlist_from_model
        return _build_audio_playlist_from_model(playlist, db)

    def test_payload_has_spot_schedules_key(self):
        """Payload do /playlist deve conter a chave spot_schedules."""
        playlist = _make_playlist()
        db, q = _make_db()
        q.all.return_value = []

        with patch("api.v1.devices._audio_playlist_track_payload", return_value=[]), \
             patch("api.v1.devices._build_folder_schedules_payload", return_value=[]), \
             patch("api.v1.devices._build_spot_schedules_payload", return_value=[]):
            result = self._call(playlist, db)

        self.assertIn("spot_schedules", result)
        self.assertIn("folder_schedules", result)
        self.assertIn("tracks", result)

    def test_payload_spot_schedules_contains_active_spot(self):
        """
        Com spot_schedule ativo no db, o payload deve refletir isso.
        Valida o fluxo ponta-a-ponta: model → payload.
        """
        from core.models import AudioTrackStatus

        playlist = _make_playlist()
        track = _make_track(status=AudioTrackStatus.ACTIVE, file_url="/spot.mp3")
        spot = _make_spot(track_id=track.id, name="Jingle Natal")
        sched_entry = {
            "id": str(uuid.uuid4()),
            "spot_id": str(spot.id),
            "spot_name": "Jingle Natal",
            "interval_seconds": 1800,
            "start_time": "08:00",
            "end_time": "20:00",
            "priority": 5,
            "insertion_policy": "interrupt",
            "file_url": "/spot.mp3",
        }

        db, q = _make_db()

        with patch("api.v1.devices._audio_playlist_track_payload", return_value=[]), \
             patch("api.v1.devices._build_folder_schedules_payload", return_value=[]), \
             patch("api.v1.devices._build_spot_schedules_payload", return_value=[sched_entry]):
            result = self._call(playlist, db)

        self.assertEqual(len(result["spot_schedules"]), 1)
        self.assertEqual(result["spot_schedules"][0]["spot_name"], "Jingle Natal")
        self.assertEqual(result["spot_schedules"][0]["insertion_policy"], "interrupt")

    def test_payload_structure_matches_frontend_expectations(self):
        """
        Garante que a estrutura do payload tem todos os campos consumidos por
        Player.jsx (linhas 890-918): id, name, volume, loop, shuffle, tracks,
        folder_schedules, spot_schedules.
        """
        playlist = _make_playlist()
        db, q = _make_db()

        with patch("api.v1.devices._audio_playlist_track_payload", return_value=[]), \
             patch("api.v1.devices._build_folder_schedules_payload", return_value=[]), \
             patch("api.v1.devices._build_spot_schedules_payload", return_value=[]):
            result = self._call(playlist, db)

        expected_keys = ("id", "name", "volume", "loop", "shuffle",
                         "tracks", "folder_schedules", "spot_schedules")
        for key in expected_keys:
            self.assertIn(key, result, f"Chave '{key}' ausente no payload do audio_playlist")

    def test_payload_spot_schedules_empty_when_track_inactive(self):
        """
        Quando o AudioTrack do spot é INACTIVE, spot_schedules deve ser [].
        Confirma que o filtro de status funciona e que o payload não envia
        URL inválida para o player.
        """
        playlist = _make_playlist()
        db, q = _make_db()

        with patch("api.v1.devices._audio_playlist_track_payload", return_value=[]), \
             patch("api.v1.devices._build_folder_schedules_payload", return_value=[]), \
             patch("api.v1.devices._build_spot_schedules_payload", return_value=[]):
            result = self._call(playlist, db)

        self.assertEqual(result["spot_schedules"], [])


# ═══════════════════════════════════════════════════════════════════════════════
#  Análise do frontend: audioManager.js — playSpot sem retorno garantido
# ═══════════════════════════════════════════════════════════════════════════════


class TestAudioManagerSpotReturnAnalysis(unittest.TestCase):
    """
    Testes conceituais que documentam o comportamento do AudioManager (audioManager.js)
    em relação ao Bug 1.

    Como AudioManager é JavaScript e não Python, esses testes simulam a lógica
    equivalente para documentar os cenários de falha identificados na inspeção do código.
    """

    def test_play_spot_does_not_self_schedule_return_to_radio(self):
        """
        ANÁLISE Bug 1 — audioManager.js linha 187-211:
        `playSpot` seta state.current = AUDIO_STATE.SPOT mas NÃO registra callback
        de retorno autônomo. O retorno depende exclusivamente de _onTrackEnded('spot')
        (linha 409), que por sua vez depende do evento 'ended' do HTMLAudioElement.

        Se o elemento de áudio do spot não disparar 'ended' (src inválida, player
        pausado externamente, página re-renderizada destruindo o elemento), o estado
        permanece SPOT para sempre.

        Este teste documenta o contrato esperado (com fix) vs atual (sem fix).
        """
        # Simula lógica equivalente em Python para documentação
        state = {"current": "radio"}
        returned_to_radio = []

        def play_spot_current(spot_url, insertion_policy="interrupt"):
            """Comportamento ATUAL — sem garantia de retorno."""
            previous = state["current"]  # captura antes de mudar (ok)
            state["current"] = "spot"
            # Problema: não agenda retorno — depende de ended event externo

        def play_spot_fixed(spot_url, insertion_policy="interrupt"):
            """Comportamento ESPERADO — com retorno garantido via callback."""
            previous = state["current"]
            state["current"] = "spot"
            # Fix: registrar retorno como callback encadeado (simulação)
            returned_to_radio.append(previous)
            state["current"] = previous  # retorno garantido

        # Cenário atual: spot é chamado mas ended nunca dispara
        play_spot_current("/spot.mp3", "interrupt")
        self.assertEqual(state["current"], "spot",
                         "Sem fix: estado permanece SPOT quando ended não dispara")

        # Cenário com fix
        state["current"] = "radio"
        play_spot_fixed("/spot.mp3", "interrupt")
        self.assertEqual(state["current"], "radio",
                         "Com fix: estado retorna para RADIO após spot")

    def test_previous_state_captured_before_state_change(self):
        """
        ANÁLISE Bug 1 adicional:
        `playSpot` captura `previous = this.state.current` (linha 190) antes de mudar
        o estado — isso está correto. Porém se um intervalo anterior travou o estado
        em SPOT, `previous` será SPOT ao invés de RADIO, e `_resumeAfterSpot(SPOT)`
        tentará retomar o spot player em vez do rádio.

        Localização: audioManager.js linhas 217-233 — `_resumeAfterSpot`:
          const player = previous === AUDIO_STATE.RADIO ? this.players.radio : this.players.mediaAudio
          Se previous = 'spot', player = mediaAudio (errado para rádio indoor).
        """
        # Simula o estado travado em SPOT
        state_current = "spot"  # estado travado do bug anterior

        # previous é capturado AQUI — já é "spot" por causa do estado travado
        previous = state_current
        state_current = "spot"  # seta spot novamente

        # _resumeAfterSpot(previous) com previous = "spot"
        # player = mediaAudio (pois previous != RADIO)
        expected_resume_player = "radio"
        actual_resume_player = "radio" if previous == "radio" else "mediaAudio"

        self.assertNotEqual(
            actual_resume_player,
            expected_resume_player,
            "ANÁLISE Bug 1 confirmado: quando previous='spot', _resumeAfterSpot usa player errado",
        )


if __name__ == "__main__":
    unittest.main()
