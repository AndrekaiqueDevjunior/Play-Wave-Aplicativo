# SPEC 019 — Design

## Modelo de dados

`User` (`backend/core/models.py`):

- `password_hash` passa de `nullable=False` para `nullable=True` — usuário em convite pendente não tem senha ainda.
- Novas colunas: `invite_token` (único, indexado), `invite_expires_at`, `invite_sent_at`, `password_reset_token` (único, indexado), `password_reset_expires_at`.
- `account_status` continua `String(20)` solto; novo valor aceito: `"pending_invite"`.

`UserLogAction` (enum Postgres `userlogaction`): dois novos valores, `resend_invite` e `accept_invite`, adicionados via `ALTER TYPE ... ADD VALUE` (mesma limitação de não poder remover valores em downgrade, documentada desde a SPEC 018).

Migration: `backend/alembic/versions/20260619_0900_user_invite_password_reset.py`, encadeada após `20260618_1400` (SPEC 018).

## Fluxo de criação de usuário

`POST /users/` (`backend/api/v1/users.py::create_user`):

- `UserCreate.password` passa a ser opcional; novo campo `send_invite: bool`.
- Validação (`model_validator`): se `send_invite=False`, `password` é obrigatório.
- Se `send_invite=True`: usuário criado com `password_hash=None`, `account_status="pending_invite"`, token e expiração gerados, e-mail de convite disparado, log `INVITE` registrado.
- Se `send_invite=False`: comportamento equivalente ao anterior (senha definida pelo admin, `account_status="active"`).

## Reenvio de convite

`POST /users/{id}/resend-invite` — só permitido para usuários em `pending_invite`; gera novo `invite_token`/`invite_expires_at` (invalidando o anterior, já que é o único token armazenado), reenvia e-mail, registra log `RESEND_INVITE`.

## Aceite de convite

`POST /api/auth/accept-invite` (`backend/api/v1/auth.py`) — recebe `{token, password}`, busca por `invite_token`. Se expirado ou inexistente, rejeita. Se válido: define `password_hash`, `account_status="active"`, limpa `invite_token`/`invite_expires_at`, registra log `ACCEPT_INVITE`, retorna `Token` (login automático).

## Login

`POST /api/auth/login` — corrigido um bug pré-existente que faria a verificação de senha lançar exceção (não um 401 limpo) quando `password_hash` é `None`. Nova ordem de checagens:

1. Usuário existe e tem `password_hash` (senão, 401 genérico — não revela se o e-mail existe).
2. `account_status == "pending_invite"` → 403 com mensagem específica orientando a aceitar o convite.
3. Senha verificada via `verify_password`.
4. `is_active` (comportamento já existente).

## Reset de senha (usuário já ativo)

`POST /api/auth/forgot-password` — recebe `{email}`; se existir e tiver senha, gera `password_reset_token`/`password_reset_expires_at`, envia e-mail. Sempre retorna a mesma mensagem genérica, exista ou não o e-mail (evita enumeração).

`POST /api/auth/reset-password` — recebe `{token, password}`; valida expiração, define nova senha, limpa o token, registra log `RESET_PASSWORD` (valor de enum já existente, reaproveitado), retorna `Token`.

## Serviço de e-mail

`backend/services/email_service.py` — usa `smtplib` puro com configuração via `Settings` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`). Quando `SMTP_HOST` não está configurado, `_send()` apenas loga o conteúdo (`logger.info`) e retorna `False`, sem lançar exceção — nenhuma operação do fluxo de usuários depende do envio ter sucesso.

Links de convite/reset apontam para `FRONTEND_BASE_URL` (`/aceitar-convite?token=...`, `/redefinir-senha?token=...`).

## Frontend

- `frontend/src/pages/ConfigUsuario.jsx`: dialog de criação de usuário agora tem um seletor "Como conceder acesso" (convite por e-mail vs. senha definida pelo admin); removida a geração client-side de senha temporária e o toast com senha em texto plano.
- `UserStatusBadge.jsx`: novo status visual `pending_invite` ("Convite pendente", âmbar).
- Novo item no menu de ações por usuário: "Reenviar convite" (visível só quando `pending_invite`), substituindo "Redefinir senha" nesse estado (que não faz sentido para quem nunca teve senha).
- Três páginas novas, públicas (fora do `ProtectedRoute`): `AceitarConvite.jsx`, `EsqueciSenha.jsx`, `RedefinirSenha.jsx` — leem o token da query string, chamam o respectivo endpoint, e autenticam a sessão localmente via `AuthContext.setSession()` (novo método, evita um segundo round-trip de login após o aceite/reset).
- `Login.jsx`: link "Esqueci minha senha" adicionado.

## Decisões registradas (não confirmadas via `AskUserQuestion` por falha da ferramenta nesta sessão)

- SMTP genérico com fallback de log — risco baixo: não há comportamento ativo que dependa de envio real até que credenciais sejam configuradas.
- `account_status` como string solta — risco baixo: já era assim antes desta SPEC; manter consistência evita uma migração maior sem necessidade imediata.
