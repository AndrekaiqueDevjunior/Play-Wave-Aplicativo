"""Testes de regressão — Bugs nos comandos remotos de dispositivos.

============================================================
BUGS DOCUMENTADOS
============================================================

BUG 1 — onCommandNew no SSE não chama pollCommands completo
-----------------------------------------------------------
Arquivo: frontend/src/pages/Player.jsx
Linhas: 726-744

O handler SSE `onCommandNew` (linha 726) é disparado quando o backend publica
o evento `command:new` via Redis/SSE logo após criar um comando
(devices.py linha 1714-1728). Porém, em vez de chamar `pollCommands()` —
que é a função do useCallback (linha 604) com toda a lógica de ACK (receber,
iniciar, executar e enviar ACK) — o handler apenas faz:

    buscarComandosPendentes(deviceId, deviceToken).then((commands) => {
        if (commands && commands.length > 0) {
            console.log("[player] SSE triggered immediate fetch:", commands.length);
        }
    })

Isso busca os comandos e os imprime, mas NÃO os executa nem envia ACK.
O comando é de fato executado apenas no próximo tick do setInterval (linha 692),
que ocorre até 10 segundos depois (POLL_COMMANDS_INTERVAL = 10_000, linha 37).

Consequência: o operador envia um comando e o player pode demorar até 10s para
executá-lo, mesmo com SSE configurado para entrega imediata.

Correção sugerida: substituir o conteúdo de onCommandNew por:
    pollCommands();
Mas pollCommands é definido dentro de um useCallback diferente (effect 6) e não
está acessível diretamente no closure do effect 6b (SSE). A solução limpa é
usar uma ref estável:
    pollCommandsRef.current?.(); // se pollCommandsRef guardar a função, não o timer


BUG 2 — restart_device / shutdown_device lançam BROWSER_ENVIRONMENT no web
---------------------------------------------------------------------------
Arquivo: frontend/src/player-core/commands.js
Linhas: 45-55 (callNativePowerCommand) e 113-121 (restart_device, shutdown_device)

As handlers `restart_device` (linha 113) e `shutdown_device` (linha 118) chamam
`callNativePowerCommand`, que verifica se existe uma das bridges nativas:
    window.PlayWaveNative || window.AndroidPlayer || window.__ELECTRON__?.player

No browser web puro, nenhuma dessas bridges existe. O código então verifica
Platform.name (linha 51):
  - Se "web" → errorCode = "BROWSER_ENVIRONMENT"
  - Caso contrário → errorCode = "COMMAND_NOT_IMPLEMENTED"

E lança `CommandUnsupportedError`, resultando em ACK com:
    { success: false, error_code: "BROWSER_ENVIRONMENT" }

O backend recebe esse ACK no endpoint POST /commands/{id}/ack (devices.py linha
1976) e marca o comando como `failed` via crud_device_command.ack() (linha 1997).
O gerenciador não exibe feedback claro ao operador sobre o motivo da falha.

Consequência: operador envia "Reiniciar dispositivo" e vê status "failed" sem
mensagem explicativa de que o player está rodando no browser, não em Android/Electron.

O que seria necessário para suportar no Android (Capacitor):
  - Implementar window.PlayWaveNative = { restartDevice: () => Capacitor.Plugins.App.exitApp() }
    ou via plugin nativo Capacitor que chame PowerManager.reboot() com permissão REBOOT.
  - Registrar o plugin no AndroidManifest.xml com permissão android.permission.REBOOT.

O que seria necessário para suportar no Electron:
  - Implementar window.__ELECTRON__ = { player: { restartDevice: () => { app.relaunch(); app.exit(0); } } }
    no preload.js, exposto via contextBridge.exposeInMainWorld.
  - Para shutdown: shell.shutdown() não é padrão — precisaria de um módulo nativo ou
    invocar o processo via child_process.exec('shutdown -h now') no main process.

============================================================
COBERTURA DOS TESTES
============================================================

TestSendCommandCreatesStatusPending
  - POST /devices/{id}/command com restart_device → status pending

TestGetPendingCommandsMarksAsSent
  - GET /devices/{id}/commands/pending → retorna pendentes e marca como sent

TestFullCommandFlowBrowserEnvironment
  - Fluxo completo: criar → pending → sent → received → started → ACK(success=False,
    error_code=BROWSER_ENVIRONMENT) → status final = failed

TestInvalidCommandReturns400
  - POST /devices/{id}/command com tipo inválido → 400

TestCommandHistoryList
  - GET /devices/{id}/commands → lista histórico de comandos
"""

import unittest
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers compartilhados ────────────────────────────────────────────────────

def _make_device(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="TV Lobby",
        status="online",
        is_blocked=False,
        requires_repairing=False,
        pairing_code="TV-ABCD",
        device_token="tok-device-valid",
        token_version=1,
        pairing_version=1,
        location=None,
        current_campaign=None,
        current_campaign_id=None,
        audio_playlist_id=None,
        last_seen_at=None,
        last_connection=None,
        updated_at=None,
        created_at=None,
        osd_config=None,
        config=None,
        config_version=None,
        type="android_tv",
        group=None,
        device_commands=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_user(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        email="admin@test.com",
        role="admin",
        tenant_id=uuid.uuid4(),
        is_active=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_command(device_id, **kwargs):
    """Cria um SimpleNamespace que imita um objeto DeviceCommand do SQLAlchemy."""
    defaults = dict(
        id=uuid.uuid4(),
        device_id=device_id,
        tenant_id=uuid.uuid4(),
        command_type="restart_device",
        payload=None,
        status="pending",
        requested_by="admin@test.com",
        requested_at=datetime.utcnow(),
        sent_at=None,
        received_at=None,
        started_at=None,
        executed_at=None,
        expires_at=datetime.utcnow() + timedelta(seconds=600),
        result=None,
        error_message=None,
        is_destructive=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_app_with_admin(device, user):
    """Monta um FastAPI com autenticação de admin mockada."""
    from api.v1.devices import router as devices_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(devices_router)

    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: user

    return app, fake_db


def _make_app_with_device_token(device):
    """Monta FastAPI com autenticação de device token mockada (endpoints do player)."""
    from api.v1.devices import router as devices_router, get_device_by_token
    from core.database import get_db

    app = FastAPI()
    app.include_router(devices_router)

    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_device_by_token] = lambda: device

    return app, fake_db


# ── TestSendCommandCreatesStatusPending ───────────────────────────────────────

class TestSendCommandCreatesStatusPending(unittest.TestCase):
    """POST /devices/{id}/command com restart_device deve criar o comando com status pending."""

    def setUp(self):
        self.device = _make_device()
        self.user = _make_user(role="admin", tenant_id=self.device.tenant_id)
        self.device_id = str(self.device.id)

    def _call_send(self, command_type, device_found=True, app=None, fake_db=None):
        if app is None:
            app, fake_db = _make_app_with_admin(self.device, self.user)

        cmd = _make_command(self.device.id, command_type=command_type)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
             patch("api.v1.devices.publish_device_event", create=True), \
             patch("services.event_bus.publish_device_event", create=True):

            mock_crud.get.return_value = self.device if device_found else None
            mock_cmd_crud.create.return_value = cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": command_type},
            )
        return resp, cmd

    def test_restart_device_creates_pending_command(self):
        """Bug 2 — restart_device deve ser criado com status pending no banco."""
        resp, cmd = self._call_send("restart_device")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        # O CRUD retorna o objeto criado; status deve ser pending
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["command_type"], "restart_device")

    def test_shutdown_device_creates_pending_command(self):
        """shutdown_device também é destrutivo — deve criar com status pending."""
        resp, cmd = self._call_send("shutdown_device")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["command_type"], "shutdown_device")

    def test_sync_creates_pending_command(self):
        """Comando não-destrutivo sync também deve criar com status pending."""
        cmd = _make_command(self.device.id, command_type="sync", is_destructive=False)
        app, fake_db = _make_app_with_admin(self.device, self.user)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
             patch("services.event_bus.publish_device_event", create=True):

            mock_crud.get.return_value = self.device
            mock_cmd_crud.create.return_value = cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "sync"},
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "pending")

    def test_send_command_device_not_found_returns_404(self):
        """Dispositivo inexistente deve retornar 404."""
        resp, _ = self._call_send("restart_device", device_found=False)
        self.assertEqual(resp.status_code, 404)

    def test_send_command_wrong_tenant_returns_403(self):
        """Operador de tenant diferente não pode enviar comandos."""
        operator = _make_user(role="operator", tenant_id=uuid.uuid4())
        # device.tenant_id diferente do operator.tenant_id
        app, _ = _make_app_with_admin(self.device, operator)
        cmd = _make_command(self.device.id)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud:

            mock_crud.get.return_value = self.device
            mock_cmd_crud.create.return_value = cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "restart_device"},
            )

        self.assertEqual(resp.status_code, 403)

    def test_send_command_is_destructive_flag_set(self):
        """Comandos destrutivos devem ter is_destructive=True na resposta."""
        resp, _ = self._call_send("restart_device")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_destructive"])


# ── TestGetPendingCommandsMarksAsSent ────────────────────────────────────────

class TestGetPendingCommandsMarksAsSent(unittest.TestCase):
    """GET /devices/{id}/commands/pending retorna comandos e os marca como sent."""

    def setUp(self):
        self.device = _make_device()
        self.device_id = str(self.device.id)

    def _call_pending(self, commands=None):
        app, fake_db = _make_app_with_device_token(self.device)
        if commands is None:
            commands = [_make_command(self.device.id)]

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get_pending.return_value = commands
            mock_cmd_crud.mark_many_sent.return_value = None

            client = TestClient(app)
            resp = client.get(
                f"/devices/{self.device_id}/commands/pending",
                headers={"X-Device-Token": "tok-device-valid"},
            )
        return resp, mock_cmd_crud

    def test_returns_pending_commands(self):
        """GET /pending deve retornar os comandos pendentes com campos esperados."""
        resp, _ = self._call_pending()
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        item = data[0]
        self.assertIn("id", item)
        self.assertIn("command_type", item)
        self.assertEqual(item["command_type"], "restart_device")

    def test_marks_commands_as_sent(self):
        """Após retornar os pendentes, deve marcar todos como sent (mark_many_sent)."""
        commands = [_make_command(self.device.id), _make_command(self.device.id, command_type="sync")]
        _, mock_cmd_crud = self._call_pending(commands=commands)
        # mark_many_sent deve ter sido chamado com a lista de comandos
        mock_cmd_crud.mark_many_sent.assert_called_once()
        call_kwargs = mock_cmd_crud.mark_many_sent.call_args
        # Verifica que passou commands
        self.assertIn("commands", call_kwargs.kwargs or {})

    def test_empty_pending_returns_empty_list(self):
        """Se não há comandos pendentes, retorna lista vazia."""
        resp, _ = self._call_pending(commands=[])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_pending_contains_payload_field(self):
        """Cada comando retornado deve ter o campo payload."""
        cmd = _make_command(self.device.id, payload={"volume": 0.5})
        resp, _ = self._call_pending(commands=[cmd])
        self.assertEqual(resp.status_code, 200)
        item = resp.json()[0]
        self.assertIn("payload", item)

    def test_wrong_device_id_returns_403(self):
        """Token de um device não pode buscar pendentes de outro device."""
        other_device_id = str(uuid.uuid4())
        app, fake_db = _make_app_with_device_token(self.device)

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get_pending.return_value = []

            client = TestClient(app)
            resp = client.get(
                f"/devices/{other_device_id}/commands/pending",
                headers={"X-Device-Token": "tok-device-valid"},
            )
        self.assertEqual(resp.status_code, 403)


# ── TestFullCommandFlowBrowserEnvironment ─────────────────────────────────────

class TestFullCommandFlowBrowserEnvironment(unittest.TestCase):
    """Fluxo completo: criar → pending → sent → received → started → ACK(failed, BROWSER_ENVIRONMENT).

    Simula o que acontece quando o player web tenta executar restart_device
    sem bridge nativa. O player envia ACK com success=False e
    error_code="BROWSER_ENVIRONMENT" (ver commands.js linha 51).
    Status final deve ser "failed".
    """

    def setUp(self):
        self.device = _make_device()
        self.device_id = str(self.device.id)
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)
        self.cmd = _make_command(self.device.id, command_type="restart_device")

    # ── Passo 1: criar o comando ──

    def test_step1_create_command_status_pending(self):
        """POST /command → status=pending (o crud retorna o objeto criado)."""
        app, _ = _make_app_with_admin(self.device, self.admin)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
             patch("services.event_bus.publish_device_event", create=True):

            mock_crud.get.return_value = self.device
            mock_cmd_crud.create.return_value = self.cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "restart_device"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "pending")

    # ── Passo 2: buscar pendentes (→ marca como sent) ──

    def test_step2_fetch_pending_and_mark_sent(self):
        """GET /commands/pending → retorna o comando e chama mark_many_sent."""
        app, _ = _make_app_with_device_token(self.device)

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get_pending.return_value = [self.cmd]
            mock_cmd_crud.mark_many_sent.return_value = None

            client = TestClient(app)
            resp = client.get(
                f"/devices/{self.device_id}/commands/pending",
                headers={"X-Device-Token": "tok-device-valid"},
            )

        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["command_type"], "restart_device")
        mock_cmd_crud.mark_many_sent.assert_called_once()

    # ── Passo 3: marcar como received ──

    def test_step3_mark_received(self):
        """POST /commands/{id}/received → status=received."""
        app, _ = _make_app_with_device_token(self.device)
        cmd_received = _make_command(
            self.device.id,
            id=self.cmd.id,
            command_type="restart_device",
            status="received",
        )

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get.return_value = self.cmd
            mock_cmd_crud.mark_received.return_value = cmd_received

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/commands/{self.cmd.id}/received",
                headers={"X-Device-Token": "tok-device-valid"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "received")

    # ── Passo 4: marcar como started ──

    def test_step4_mark_started(self):
        """POST /commands/{id}/started → status=executing."""
        app, _ = _make_app_with_device_token(self.device)
        cmd_started = _make_command(
            self.device.id,
            id=self.cmd.id,
            command_type="restart_device",
            status="executing",
        )

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get.return_value = self.cmd
            mock_cmd_crud.mark_executing.return_value = cmd_started

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/commands/{self.cmd.id}/started",
                headers={"X-Device-Token": "tok-device-valid"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "executing")

    # ── Passo 5: ACK com success=False, error_code=BROWSER_ENVIRONMENT ──

    def test_step5_ack_browser_environment_results_in_failed(self):
        """POST /commands/{id}/ack com success=False → status final = failed.

        Documenta o bug: o player web tenta executar restart_device, não encontra
        bridge nativa (window.PlayWaveNative / AndroidPlayer / __ELECTRON__),
        e retorna error_code="BROWSER_ENVIRONMENT" (commands.js linha 51).
        O backend deve marcar o comando como failed.
        """
        app, _ = _make_app_with_device_token(self.device)
        cmd_failed = _make_command(
            self.device.id,
            id=self.cmd.id,
            command_type="restart_device",
            status="failed",
            error_message="restart_device não suportado na plataforma web",
            result={
                "platform": "web",
                "command_type": "restart_device",
                "platform_unsupported": True,
                "error_code": "BROWSER_ENVIRONMENT",
                "failed_at": datetime.utcnow().isoformat(),
            },
        )

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get.return_value = self.cmd
            mock_cmd_crud.ack.return_value = cmd_failed

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/commands/{self.cmd.id}/ack",
                headers={"X-Device-Token": "tok-device-valid"},
                json={
                    "success": False,
                    "error_message": "restart_device não suportado na plataforma web",
                    "result": {
                        "platform": "web",
                        "command_type": "restart_device",
                        "platform_unsupported": True,
                        "error_code": "BROWSER_ENVIRONMENT",
                        "failed_at": datetime.utcnow().isoformat(),
                    },
                },
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["status"], "failed")
        # O ACK deve ter sido chamado com success=False
        mock_cmd_crud.ack.assert_called_once()
        ack_call_kwargs = mock_cmd_crud.ack.call_args.kwargs
        self.assertFalse(ack_call_kwargs["success"])

    def test_ack_with_browser_environment_error_code_persisted(self):
        """O result.error_code='BROWSER_ENVIRONMENT' deve ser persistido no banco.

        Documenta que o gerenciador poderia usar esse campo para exibir badge
        "Não suportado — web browser" em vez de apenas "failed".
        """
        app, _ = _make_app_with_device_token(self.device)
        result_payload = {
            "platform": "web",
            "command_type": "restart_device",
            "platform_unsupported": True,
            "error_code": "BROWSER_ENVIRONMENT",
            "failed_at": datetime.utcnow().isoformat(),
        }
        cmd_failed = _make_command(
            self.device.id,
            id=self.cmd.id,
            status="failed",
            result=result_payload,
        )

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get.return_value = self.cmd
            mock_cmd_crud.ack.return_value = cmd_failed

            client = TestClient(app)
            client.post(
                f"/devices/{self.device_id}/commands/{self.cmd.id}/ack",
                headers={"X-Device-Token": "tok-device-valid"},
                json={
                    "success": False,
                    "error_message": "browser",
                    "result": result_payload,
                },
            )

        # Verifica que o result foi passado para o crud
        ack_call_kwargs = mock_cmd_crud.ack.call_args.kwargs
        self.assertIsNotNone(ack_call_kwargs.get("result"))
        self.assertEqual(ack_call_kwargs["result"].get("error_code"), "BROWSER_ENVIRONMENT")

    def test_ack_success_true_results_in_completed(self):
        """ACK com success=True → status=completed (controle positivo)."""
        app, _ = _make_app_with_device_token(self.device)
        cmd_completed = _make_command(
            self.device.id,
            id=self.cmd.id,
            status="completed",
        )

        with patch("api.v1.devices.crud_device_command") as mock_cmd_crud:
            mock_cmd_crud.get.return_value = self.cmd
            mock_cmd_crud.ack.return_value = cmd_completed

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/commands/{self.cmd.id}/ack",
                headers={"X-Device-Token": "tok-device-valid"},
                json={
                    "success": True,
                    "result": {
                        "platform": "android",
                        "command_type": "restart_device",
                        "completed_at": datetime.utcnow().isoformat(),
                    },
                },
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "completed")


# ── TestInvalidCommandReturns400 ──────────────────────────────────────────────

class TestInvalidCommandReturns400(unittest.TestCase):
    """POST /devices/{id}/command com tipo inválido deve retornar 400."""

    def setUp(self):
        self.device = _make_device()
        self.device_id = str(self.device.id)
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)

    def _call_send(self, command_type):
        app, _ = _make_app_with_admin(self.device, self.admin)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command"):

            mock_crud.get.return_value = self.device

            client = TestClient(app)
            return client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": command_type},
            )

    def test_invalid_command_type_returns_400(self):
        """Comando inexistente deve retornar 400 com detalhe."""
        resp = self._call_send("fly_to_moon")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())

    def test_empty_command_type_returns_400(self):
        """Tipo de comando vazio deve retornar 400."""
        resp = self._call_send("")
        self.assertEqual(resp.status_code, 400)

    def test_arbitrary_string_returns_400(self):
        """String arbitrária não deve ser aceita como comando."""
        resp = self._call_send("'; DROP TABLE devices; --")
        self.assertEqual(resp.status_code, 400)

    def test_valid_commands_are_accepted(self):
        """Todos os comandos da VALID_COMMANDS list devem retornar 200."""
        from api.v1.devices import VALID_COMMANDS

        for cmd_type in sorted(VALID_COMMANDS):
            cmd = _make_command(self.device.id, command_type=cmd_type, is_destructive=False)
            app, _ = _make_app_with_admin(self.device, self.admin)

            with patch("api.v1.devices.crud_device") as mock_crud, \
                 patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
                 patch("services.event_bus.publish_device_event", create=True):

                mock_crud.get.return_value = self.device
                mock_cmd_crud.create.return_value = cmd

                client = TestClient(app)
                resp = client.post(
                    f"/devices/{self.device_id}/command",
                    json={"command_type": cmd_type},
                )

            self.assertEqual(resp.status_code, 200, f"Comando {cmd_type!r} deveria ser aceito")

    def test_400_detail_lists_valid_commands(self):
        """A mensagem de erro 400 deve listar os comandos válidos."""
        resp = self._call_send("invalid_command_xyz")
        self.assertEqual(resp.status_code, 400)
        detail = resp.json().get("detail", "")
        # O endpoint faz: f"Comando inválido. Válidos: {sorted(VALID_COMMANDS)}"
        self.assertIn("restart_device", detail)


# ── TestCommandHistoryList ────────────────────────────────────────────────────

class TestCommandHistoryList(unittest.TestCase):
    """GET /devices/{id}/commands deve retornar o histórico de comandos."""

    def setUp(self):
        self.device = _make_device()
        self.device_id = str(self.device.id)
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)

    def _call_list(self, commands=None, user=None, device_found=True):
        if user is None:
            user = self.admin
        app, _ = _make_app_with_admin(self.device, user)
        if commands is None:
            commands = []

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud:

            mock_crud.get.return_value = self.device if device_found else None
            mock_cmd_crud.get_by_device.return_value = commands

            client = TestClient(app)
            return client.get(f"/devices/{self.device_id}/commands")

    def test_empty_history_returns_empty_list(self):
        """Sem comandos, retorna lista vazia."""
        resp = self._call_list(commands=[])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_history_contains_all_statuses(self):
        """Histórico deve mostrar comandos em qualquer status (pending, failed, completed)."""
        commands = [
            _make_command(self.device.id, status="completed", command_type="sync"),
            _make_command(self.device.id, status="failed", command_type="restart_device"),
            _make_command(self.device.id, status="pending", command_type="shutdown_device"),
        ]
        resp = self._call_list(commands=commands)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 3)
        statuses = {item["status"] for item in data}
        self.assertIn("completed", statuses)
        self.assertIn("failed", statuses)
        self.assertIn("pending", statuses)

    def test_history_includes_result_field(self):
        """Campos result e error_message devem estar presentes."""
        result = {
            "platform": "web",
            "error_code": "BROWSER_ENVIRONMENT",
            "platform_unsupported": True,
        }
        cmd = _make_command(
            self.device.id,
            status="failed",
            command_type="restart_device",
            error_message="browser sem suporte",
            result=result,
        )
        resp = self._call_list(commands=[cmd])
        self.assertEqual(resp.status_code, 200)
        item = resp.json()[0]
        self.assertEqual(item["status"], "failed")
        self.assertEqual(item["error_message"], "browser sem suporte")
        self.assertIsNotNone(item.get("result"))
        self.assertEqual(item["result"]["error_code"], "BROWSER_ENVIRONMENT")

    def test_history_device_not_found_returns_404(self):
        """Histórico de dispositivo inexistente retorna 404."""
        resp = self._call_list(device_found=False)
        self.assertEqual(resp.status_code, 404)

    def test_history_wrong_tenant_returns_403(self):
        """Operador de tenant diferente não pode ver o histórico."""
        other_user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call_list(user=other_user)
        self.assertEqual(resp.status_code, 403)

    def test_history_ordered_by_most_recent_first(self):
        """O histórico deve vir ordenado por requested_at desc (mais recente primeiro)."""
        now = datetime.utcnow()
        cmd_old = _make_command(
            self.device.id,
            status="completed",
            command_type="sync",
            requested_at=now - timedelta(hours=2),
        )
        cmd_new = _make_command(
            self.device.id,
            status="failed",
            command_type="restart_device",
            requested_at=now - timedelta(minutes=5),
        )
        # Mock retorna na mesma ordem em que o crud retornaria (mais recente primeiro)
        resp = self._call_list(commands=[cmd_new, cmd_old])
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["command_type"], "restart_device")
        self.assertEqual(data[1]["command_type"], "sync")


# ── TestDestructiveCommandRequiresEmail ───────────────────────────────────────

class TestDestructiveCommandRequiresEmail(unittest.TestCase):
    """Comandos destrutivos exigem usuário com e-mail (SPEC 003, linha 1698 de devices.py)."""

    def setUp(self):
        self.device = _make_device()
        self.device_id = str(self.device.id)

    def test_destructive_command_without_email_returns_403(self):
        """Se current_user.email é None, comandos destrutivos retornam 403."""
        user_no_email = _make_user(role="admin", email=None)
        app, _ = _make_app_with_admin(self.device, user_no_email)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command"):

            mock_crud.get.return_value = self.device

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "restart_device"},
            )

        self.assertEqual(resp.status_code, 403)
        self.assertIn("e-mail", resp.json().get("detail", ""))

    def test_destructive_command_with_email_succeeds(self):
        """Com e-mail presente, comando destrutivo deve ser criado normalmente."""
        user_with_email = _make_user(role="admin", email="admin@test.com")
        app, _ = _make_app_with_admin(self.device, user_with_email)
        cmd = _make_command(self.device.id, command_type="restart_device")

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
             patch("services.event_bus.publish_device_event", create=True):

            mock_crud.get.return_value = self.device
            mock_cmd_crud.create.return_value = cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "restart_device"},
            )

        self.assertEqual(resp.status_code, 200)

    def test_non_destructive_command_without_email_succeeds(self):
        """Comandos não-destrutivos não exigem e-mail."""
        user_no_email = _make_user(role="admin", email=None)
        app, _ = _make_app_with_admin(self.device, user_no_email)
        cmd = _make_command(self.device.id, command_type="sync", is_destructive=False)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_command") as mock_cmd_crud, \
             patch("services.event_bus.publish_device_event", create=True):

            mock_crud.get.return_value = self.device
            mock_cmd_crud.create.return_value = cmd

            client = TestClient(app)
            resp = client.post(
                f"/devices/{self.device_id}/command",
                json={"command_type": "sync"},
            )

        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
