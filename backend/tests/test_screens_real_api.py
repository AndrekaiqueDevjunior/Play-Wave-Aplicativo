"""Smoke tests — Telas reais vs API real (servidor live na porta 8000).

Cada teste verifica que o endpoint correspondente à tela retorna 200 OK
quando chamado com um token de admin válido, provando que a integração
frontend→backend está 100% real (sem mock).

Telas cobertas:
  1.  Dispositivos       → GET /devices/
  2.  Mídias             → GET /media/
  3.  Campanhas          → GET /campaigns/
  4.  Agenda             → GET /schedule/  + GET /schedule/upcoming
  5.  Operação (Usuários)→ GET /users/
  6.  Monitoramento      → GET /devices/   (mesmo endpoint)
  7.  Relatórios         → GET /reports/summary
  8.  Localizações       → GET /locations/
  9.  Rádio Indoor       → GET /audio/playlists/
  10. Faixas de Áudio    → GET /audio/tracks/
  11. Playlists Sonoras  → GET /audio/playlists/   (mesmo endpoint, filtro diferente)

Também cobre:
  - Dashboard            → GET /dashboard/stats
  - Auth                 → POST /api/auth/login  (obtém token)
"""

import os
import sys
import unittest

import requests

# ── Configuração ──────────────────────────────────────────────────────────────

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Credenciais lidas do .env ou override por variável de ambiente
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@playwave.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "&2p0Kw45A&lLNX4bM%gpH*cy")

_TOKEN_CACHE: dict = {}


def _get_token() -> str:
    if "token" not in _TOKEN_CACHE:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Login falhou ({resp.status_code}): {resp.text[:200]}"
            )
        _TOKEN_CACHE["token"] = resp.json()["access_token"]
    return _TOKEN_CACHE["token"]


def _get(path: str, params: dict | None = None) -> requests.Response:
    return requests.get(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {_get_token()}"},
        params=params or {},
        timeout=15,
    )


def _skip_if_unreachable():
    try:
        requests.get(f"{BASE_URL}/health", timeout=3)
    except Exception:
        raise unittest.SkipTest(f"Backend em {BASE_URL} não está acessível")


# ── Base test class ────────────────────────────────────────────────────────────

class LiveApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _skip_if_unreachable()
        _get_token()  # falha rápido se login não funcionar


# ═══════════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthScreenReal(LiveApiTestCase):
    def test_login_returns_token(self):
        """POST /api/auth/login → 200 com access_token"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_me_returns_user(self):
        """GET /api/auth/me → 200 com dados do usuário autenticado"""
        resp = _get("/api/auth/me")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("email", data)

    def test_wrong_password_returns_401(self):
        """POST /api/auth/login com senha errada → 401"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "errada"},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 401)


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 1 — Dispositivos
# ═══════════════════════════════════════════════════════════════════════════════

class TestDispositivosScreenReal(LiveApiTestCase):
    def test_listar_dispositivos_200(self):
        """GET /devices/ — tela Dispositivos lista dispositivos"""
        resp = _get("/devices/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_dispositivos_com_filtro_status(self):
        """GET /devices/?status=online — filtro de status funciona"""
        resp = _get("/devices/", params={"status": "online"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_dispositivos_com_search(self):
        """GET /devices/?search=tv — busca por nome funciona"""
        resp = _get("/devices/", params={"search": "tv"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_dispositivos_200(self):
        """GET /devices/statistics/overview — cards de contagem"""
        resp = _get("/devices/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 2 — Mídias
# ═══════════════════════════════════════════════════════════════════════════════

class TestMidiasScreenReal(LiveApiTestCase):
    def test_listar_midias_200(self):
        """GET /media/ — tela Mídias lista mídias"""
        resp = _get("/media/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_midias_com_filtro_tipo(self):
        """GET /media/?type=video — filtro por tipo"""
        resp = _get("/media/", params={"type": "video"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_midias_com_search(self):
        """GET /media/?search=logo — busca por nome/tag"""
        resp = _get("/media/", params={"search": "logo"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_midias_200(self):
        """GET /media/statistics/overview — contadores da biblioteca"""
        resp = _get("/media/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 3 — Campanhas
# ═══════════════════════════════════════════════════════════════════════════════

class TestCampanhasScreenReal(LiveApiTestCase):
    def test_listar_campanhas_200(self):
        """GET /campaigns/ — tela Campanhas lista campanhas"""
        resp = _get("/campaigns/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_campanhas_com_filtro_status(self):
        """GET /campaigns/?status=active — filtro por status"""
        resp = _get("/campaigns/", params={"status": "active"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_campanhas_com_search(self):
        """GET /campaigns/?search=promo — busca por nome"""
        resp = _get("/campaigns/", params={"search": "promo"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_campanhas_200(self):
        """GET /campaigns/statistics/overview — contadores"""
        resp = _get("/campaigns/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_campanhas_ativas_200(self):
        """GET /campaigns/active/list — campanhas ativas agora"""
        resp = _get("/campaigns/active/list")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 4 — Agenda
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgendaScreenReal(LiveApiTestCase):
    def test_listar_agenda_200(self):
        """GET /schedule/ — tela Agenda lista campannhas agendadas"""
        resp = _get("/schedule/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_agenda_upcoming_200(self):
        """GET /schedule/upcoming — próximas campanhas"""
        resp = _get("/schedule/upcoming", params={"days": 7})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_agenda_active_200(self):
        """GET /schedule/active — campanhas ativas agora"""
        resp = _get("/schedule/active")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 5 — Operação (Usuários)
# ═══════════════════════════════════════════════════════════════════════════════

class TestOperacaoScreenReal(LiveApiTestCase):
    def test_listar_usuarios_200(self):
        """GET /users/ — tela Operação lista usuários"""
        resp = _get("/users/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_usuarios_com_filtro_role(self):
        """GET /users/?role=admin — filtro por papel"""
        resp = _get("/users/", params={"role": "admin"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_usuarios_200(self):
        """GET /users/statistics/overview — contadores de usuários"""
        resp = _get("/users/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_logs_usuario_200(self):
        """GET /user-logs/ — histórico de ações"""
        resp = _get("/user-logs/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_logs_recentes_200(self):
        """GET /user-logs/recent — logs mais recentes"""
        resp = _get("/user-logs/recent")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 6 — Monitoramento
# ═══════════════════════════════════════════════════════════════════════════════

class TestMonitoramentoScreenReal(LiveApiTestCase):
    def test_listar_dispositivos_monitoramento_200(self):
        """GET /devices/ — tela Monitoramento usa o mesmo endpoint de dispositivos"""
        resp = _get("/devices/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_monitoring_stats_200(self):
        """GET /monitoring/stats — estatísticas de monitoramento"""
        resp = _get("/monitoring/stats")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_monitoring_devices_200(self):
        """GET /monitoring/devices — lista de dispositivos com status live"""
        resp = _get("/monitoring/devices")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_monitoring_events_200(self):
        """GET /monitoring/events — eventos recentes de dispositivos"""
        resp = _get("/monitoring/events")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 7 — Relatórios
# ═══════════════════════════════════════════════════════════════════════════════

class TestRelatoriosScreenReal(LiveApiTestCase):
    def test_resumo_relatorio_200(self):
        """GET /reports/summary — tela Relatórios, resumo geral"""
        resp = _get("/reports/summary")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        data = resp.json()
        self.assertIn("device_status", data)
        self.assertIn("total_views", data)

    def test_playback_logs_200(self):
        """GET /reports/playback — logs de reprodução"""
        resp = _get("/reports/playback", params={"days": 7})
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_export_csv_200(self):
        """GET /reports/export/csv — exportação CSV"""
        resp = _get("/reports/export/csv", params={"days": 7})
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIn("text/csv", resp.headers.get("content-type", ""))

    def test_views_stats_200(self):
        """GET /reports/views/stats — estatísticas de visualizações"""
        resp = _get("/reports/views/stats")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 8 — Localizações
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalizacoesScreenReal(LiveApiTestCase):
    def test_listar_localizacoes_200(self):
        """GET /locations/ — tela Localizações lista localizações"""
        resp = _get("/locations/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_localizacoes_com_search(self):
        """GET /locations/?search=recep — busca por nome"""
        resp = _get("/locations/", params={"search": "recep"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_localizacoes_200(self):
        """GET /locations/statistics/overview — contadores"""
        resp = _get("/locations/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 9 — Rádio Indoor (Playlists Sonoras)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRadioIndoorScreenReal(LiveApiTestCase):
    def test_listar_playlists_audio_200(self):
        """GET /audio/playlists/ — tela Rádio Indoor lista playlists"""
        resp = _get("/audio/playlists/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_playlists_com_search(self):
        """GET /audio/playlists/?search=jazz — busca por nome"""
        resp = _get("/audio/playlists/", params={"search": "jazz"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_playlists_audio_200(self):
        """GET /audio/playlists/statistics/overview — contadores"""
        resp = _get("/audio/playlists/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_playlists_ativas_200(self):
        """GET /audio/playlists/active/list — playlists ativas"""
        resp = _get("/audio/playlists/active/list")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_spots_200(self):
        """GET /audio/spots/ — spots de áudio da tela Rádio Indoor"""
        resp = _get("/audio/spots/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_pastas_audio_200(self):
        """GET /audio/folders/ — pastas de faixas"""
        resp = _get("/audio/folders/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 10 — Faixas de Áudio
# ═══════════════════════════════════════════════════════════════════════════════

class TestFaixasAudioScreenReal(LiveApiTestCase):
    def test_listar_faixas_200(self):
        """GET /audio/tracks/ — tela Faixas de Áudio lista faixas"""
        resp = _get("/audio/tracks/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_listar_faixas_com_search(self):
        """GET /audio/tracks/?search=pop — busca por nome"""
        resp = _get("/audio/tracks/", params={"search": "pop"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_listar_faixas_com_filtro_status(self):
        """GET /audio/tracks/?status=active — filtro por status"""
        resp = _get("/audio/tracks/", params={"status": "active"})
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_stats_faixas_200(self):
        """GET /audio/tracks/statistics/overview — contadores"""
        resp = _get("/audio/tracks/statistics/overview")
        self.assertEqual(resp.status_code, 200, resp.text[:300])

    def test_faixas_ativas_200(self):
        """GET /audio/tracks/active/list — faixas ativas"""
        resp = _get("/audio/tracks/active/list")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Tela 11 — Playlists Sonoras (PlaylistDetalhe)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlaylistsSonorasScreenReal(LiveApiTestCase):
    def test_listar_playlists_sonoras_200(self):
        """GET /audio/playlists/ — tela Playlists Sonoras lista playlists"""
        resp = _get("/audio/playlists/")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        self.assertIsInstance(resp.json(), list)

    def test_playlist_detail_not_found_returns_404(self):
        """GET /audio/playlists/{uuid-inexistente} → 404"""
        resp = _get("/audio/playlists/00000000-0000-0000-0000-000000000000")
        self.assertEqual(resp.status_code, 404, resp.text[:300])

    def test_playlist_detalhe_com_id_real(self):
        """Se existir uma playlist, GET /audio/playlists/{id} retorna 200"""
        lista = _get("/audio/playlists/").json()
        if not lista:
            self.skipTest("Nenhuma playlist cadastrada para testar detalhe")
        pid = lista[0]["id"]
        resp = _get(f"/audio/playlists/{pid}")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        data = resp.json()
        self.assertEqual(str(data["id"]), str(pid))

    def test_folder_schedules_de_playlist_real(self):
        """GET /audio/playlists/{id}/folder-schedules → 200"""
        lista = _get("/audio/playlists/").json()
        if not lista:
            self.skipTest("Nenhuma playlist cadastrada")
        pid = lista[0]["id"]
        resp = _get(f"/audio/playlists/{pid}/folder-schedules")
        self.assertEqual(resp.status_code, 200, resp.text[:300])


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboardScreenReal(LiveApiTestCase):
    def test_dashboard_stats_200(self):
        """GET /dashboard/stats — tela Dashboard carrega estatísticas"""
        resp = _get("/dashboard/stats")
        self.assertEqual(resp.status_code, 200, resp.text[:300])
        data = resp.json()
        for key in ("devices", "campaigns", "media", "audio", "users", "views_per_day"):
            self.assertIn(key, data, f"Chave '{key}' ausente no dashboard/stats")

    def test_dashboard_devices_breakdown(self):
        """dashboard/stats.devices tem total/online/offline"""
        data = _get("/dashboard/stats").json()
        self.assertIn("total",   data["devices"])
        self.assertIn("online",  data["devices"])
        self.assertIn("offline", data["devices"])


# ═══════════════════════════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthReal(unittest.TestCase):
    def test_health_endpoint_200(self):
        """GET /health — servidor está respondendo"""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        self.assertEqual(resp.status_code, 200)

    def test_root_200(self):
        """GET / — rota raiz responde"""
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
