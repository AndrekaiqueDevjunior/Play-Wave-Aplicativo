# SPEC 019 — Tests

## Backend

`backend/tests/test_user_invite_password_reset.py` — segue o padrão das SPECs 016–018: `unittest.TestCase`, importa as funções de endpoint diretamente (`api.v1.auth.login/accept_invite/forgot_password/reset_password`, `api.v1.users.create_user/resend_invite`), mocka `db: Session` via `MagicMock` e `current_user` via `SimpleNamespace`, constrói instâncias reais de `User` via `_make_user(**overrides)`.

Casos cobertos:

- `TestCreateUserInviteVsPassword`
  - criação com `send_invite=True` → `password_hash=None`, `account_status="pending_invite"`, `invite_token` gerado, e-mail de convite disparado.
  - criação com `send_invite=False` + `password` → `password_hash` definido, `account_status="active"`.
  - `UserCreate` sem senha e sem `send_invite=True` → erro de validação Pydantic.
- `TestLoginBlocksPendingInviteAndNullPassword`
  - usuário sem `password_hash` → `401` (não crasha tentando verificar hash `None`).
  - usuário com `account_status="pending_invite"` → `403` com mensagem específica.
  - usuário ativo com senha correta → token emitido.
- `TestResendInvite`
  - usuário fora de `pending_invite` → `400`.
  - usuário `pending_invite` → novo token gerado, e-mail reenviado, `invite_sent_at`/`invite_expires_at` atualizados.
- `TestAcceptInvite`
  - token inexistente → `400`.
  - token expirado → `400`.
  - token válido → usuário ativado, senha definida, token limpo, sessão (`Token`) retornada.
- `TestForgotAndResetPassword`
  - e-mail inexistente → mensagem genérica de sucesso (sem revelar não-existência).
  - e-mail existente com senha → token de reset gerado e e-mail enviado.
  - token de reset expirado → `400`.
  - token de reset válido → senha atualizada, token limpo, sessão retornada.

## Execução real (atualizado)

Criado virtualenv `backend/.venv` com `requirements.txt` + `pytest`/`httpx==0.24.1` (versão pinada por compatibilidade com `starlette` da versão de FastAPI travada no projeto) e executado de fato via `python3 -m pytest`.

`test_user_invite_password_reset.py`: **15/15 passando**. Dois bugs reais encontrados e corrigidos no próprio arquivo de teste (não no código de produção) durante a primeira execução:
- `_make_user()` não preenchia `created_at`/`updated_at`, causando `ValidationError` no schema `Token` (que exige esses campos) — corrigido adicionando os dois campos ao factory.
- Em `create_user`, `db.add()` é chamado duas vezes (uma para `User`, outra para `UserLog` quando `send_invite=True`); o `fake_add` dos dois testes de criação sobrescrevia `captured["user"]` na segunda chamada — corrigido filtrando por `isinstance(obj, User)`.

Suite completa do backend (`python3 -m pytest tests/`, excluindo testes de integração que exigem Postgres real): **439 passed / 22 failed**. Todas as 22 falhas restantes são em testes pré-existentes não tocados por nenhuma SPEC recente (confirmado via `git log` nos arquivos), desincronizados da implementação atual há mais tempo — não são regressões desta SPEC. Corrigidos nesta sessão (eram regressões reais, expostas pela mudança em `login()`/`get_in_use_references()`):
- `test_auth.py` (3 falhas) — `_make_user()` não tinha `account_status`, e `login()` agora acessa esse campo. Corrigido adicionando `account_status="active"` ao factory.
- `test_media_endpoints.py::TestMediaDelete` (2 falhas) — testes da era pré-SPEC-018 não mockavam `crud_media.get_in_use_references()` (novo na SPEC 018). Corrigido adicionando o mock.
- `test_audio_track_archive_delete.py` (1 falha) — asserção comparava a representação em string de uma `BinaryExpression` do SQLAlchemy, que nunca contém o valor literal (fica em bind params); teste estava errado desde a SPEC 016, nunca executado de verdade antes. Corrigido usando `.compile(compile_kwargs={"literal_binds": True})`.

Falhas restantes (pré-existentes, fora do escopo desta SPEC): `test_campaign_playlist_002.py`, `test_campaign_schedule_bugs.py`, `test_devices_commands.py::TestGetDeviceEndpoint`, `test_player_campaign_bugs.py`, `test_radio_indoor_bugs.py`, `test_schedule_clock_spots.py` — usam `SimpleNamespace`/`MagicMock` incompletos que não acompanharam mudanças de assinatura/campos em código não relacionado a esta SPEC. `test_audio_playlist_folder_schedules_007.py` (6 erros) e `test_campaign_playlist_spots_e2e.py` exigem um Postgres real local (fixture `db` de integração) — não executável neste ambiente sem banco de dados.

## Frontend

- `npx eslint` nos 10 arquivos alterados/criados: 0 erros (2 warnings pré-existentes de "no matching configuration", não relacionados a esta SPEC).
- `npx vitest run`: 170 passando / 3 falhando — as mesmas 3 falhas pré-existentes (`player_sse.test.js` erro de parse + 3 casos em `playbackQueueManager.test.js`), confirmadas como não relacionadas a esta SPEC.
- Nenhum teste novo de frontend foi escrito especificamente para as páginas `AceitarConvite.jsx`/`EsqueciSenha.jsx`/`RedefinirSenha.jsx` — registrado como dívida técnica (mesma decisão de escopo aplicada ao backend, por tempo).
