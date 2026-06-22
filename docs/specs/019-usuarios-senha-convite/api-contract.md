# SPEC 019 — API Contract

## `POST /users/`

Alterado. Body (`UserCreate`):

```json
{
  "name": "string",
  "email": "string",
  "role": "admin|operator|viewer",
  "job_title": "string|null",
  "tenant_id": "string|null",
  "send_invite": true,
  "password": "string (obrigatório apenas se send_invite=false, min 6 chars)"
}
```

Resposta (`UserResponse`): inclui `account_status`, `invite_sent_at`, `invite_expires_at` (estes dois `null` quando o usuário foi criado com senha manual).

Erros:
- `400` — e-mail já cadastrado.
- `422` — nem senha nem `send_invite=true` informados (validação Pydantic).
- `403` — usuário autenticado sem permissão (`role` fora de `admin`/`operator`).

## `POST /users/{user_id}/resend-invite` (novo)

Sem body. Requer `admin` ou `operator`. Resposta:

```json
{ "invite_sent_at": "2026-06-19T12:00:00", "invite_expires_at": "2026-06-22T12:00:00" }
```

Erros: `404` usuário não encontrado; `400` usuário não está em `pending_invite`; `403` sem permissão.

## `POST /api/auth/accept-invite` (novo)

Público (sem autenticação). Body:

```json
{ "token": "string", "password": "string (min 6 chars)" }
```

Resposta: `Token` (`{access_token, token_type, user}`) — login automático após aceite.

Erros: `400` token inválido ou expirado.

## `POST /api/auth/forgot-password` (novo)

Público. Body: `{ "email": "string" }`. Resposta sempre `200`:

```json
{ "message": "Se o e-mail existir, enviaremos instruções para redefinir a senha" }
```

Nunca retorna erro distinguindo e-mail existente de inexistente (proteção contra enumeração).

## `POST /api/auth/reset-password` (novo)

Público. Body: `{ "token": "string", "password": "string (min 6 chars)" }`. Resposta: `Token` (login automático).

Erros: `400` token inválido ou expirado.

## `POST /api/auth/login` (comportamento alterado)

Mesmo contrato de request/response (`UserLogin` → `Token`). Mudança: usuários em `account_status="pending_invite"` agora recebem `403` com `detail` específico em vez de `401` genérico; usuários sem `password_hash` (não deveria ocorrer fora do fluxo de convite) recebem `401` genérico em vez de erro 500.
