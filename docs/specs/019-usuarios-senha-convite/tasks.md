# SPEC 019 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 018 concluída — gate liberado.

## Diagnóstico

- [x] Auditar model `User` — confirmado: `password_hash` obrigatório, sem campos de convite/reset.
- [x] Auditar `POST /users/` — confirmado: `password` sempre obrigatório, sempre `account_status="active"`.
- [x] Auditar `POST /api/auth/login` — identificado bug real: crash (não 401 limpo) se `password_hash` fosse `None`.
- [x] Auditar infraestrutura de e-mail — confirmado: inexistente em todo o projeto (nenhum SMTP, nenhum serviço de envio).
- [x] Auditar `UserLog`/`UserLogAction` — confirmado: tabela e enum já existem e são reaproveitáveis sem mudança de schema (apenas 2 novos valores de enum).
- [x] Auditar `frontend/src/pages/ConfigUsuario.jsx` — confirmado: gera senha temporária no cliente, mostra em toast, sem envio de e-mail real; `handleResetPassword` é um stub que só loga.

## Decisão de escopo

- [!] `AskUserQuestion` falhou repetidamente nesta sessão (erro de stream) — seguido com defaults de menor risco, comunicados ao usuário em texto: SMTP genérico com fallback de log; `account_status` mantido como string solta com novo valor `"pending_invite"`.

## Backend

- [x] Tornar `User.password_hash` nullable; adicionar `invite_token`, `invite_expires_at`, `invite_sent_at`, `password_reset_token`, `password_reset_expires_at`.
- [x] Adicionar `RESEND_INVITE`/`ACCEPT_INVITE` a `UserLogAction` (model) e `UserLogActionEnum` (schema) — ambos precisavam ser sincronizados.
- [x] Criar migration `20260619_0900_user_invite_password_reset`.
- [x] Adicionar settings de SMTP/convite/reset em `core/config.py`.
- [x] Criar `backend/services/email_service.py` (SMTP real + fallback de log).
- [x] Adicionar `generate_secure_token`/`token_expiry` em `core/auth.py`.
- [x] Atualizar `UserCreate` (senha opcional + `send_invite`), `UserResponse` (expõe `invite_sent_at`/`invite_expires_at`), criar `UserResendInviteResponse`, `UserAcceptInviteRequest`, `PasswordForgotRequest`, `PasswordResetConfirmRequest`.
- [x] Atualizar `create_user` para branch convite vs. senha manual.
- [x] Criar `POST /users/{id}/resend-invite`.
- [x] Criar `POST /api/auth/accept-invite`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`.
- [x] Corrigir `login` para não crashar com `password_hash=None` e bloquear `pending_invite` com mensagem específica.
- [x] Adicionar `get_by_invite_token`/`get_by_password_reset_token` a `crud_user.py`.

## Frontend

- [x] `frontend/src/api/usuarios.js`: `reenviarConviteUsuario`, `aceitarConvite`, `solicitarResetSenha`, `confirmarResetSenha`.
- [x] `AuthContext.jsx`: novo método `setSession()` para autenticar a partir de uma resposta de auth já obtida (convite/reset), sem round-trip extra de login.
- [x] `ConfigUsuario.jsx`: dialog de criação com seletor "convite por e-mail" vs. "definir senha agora"; removida geração client-side de senha temporária; ação "Reenviar convite" no menu para usuários `pending_invite`.
- [x] `UserStatusBadge.jsx`: novo status `pending_invite`.
- [x] `UserLogDrawer.jsx`: labels/ícones para `resend_invite`/`accept_invite`.
- [x] Novas páginas públicas: `AceitarConvite.jsx`, `EsqueciSenha.jsx`, `RedefinirSenha.jsx`.
- [x] Rotas adicionadas em `app.jsx`: `/aceitar-convite`, `/esqueci-senha`, `/redefinir-senha`.
- [x] `Login.jsx`: link "Esqueci minha senha".

## Testes

- [x] Backend — `backend/tests/test_user_invite_password_reset.py` criado e **executado de fato** via `pytest` em venv dedicado (`backend/.venv`): 15/15 passando. Suite completa do backend: 439 passed / 22 failed (falhas restantes são pré-existentes, não relacionadas a esta SPEC — ver `tests.md` para detalhe arquivo por arquivo). Corrigidos no processo: 2 bugs no próprio teste novo, 3 falhas reais em `test_auth.py`, 2 em `test_media_endpoints.py`, 1 em `test_audio_track_archive_delete.py`.
- [x] Lint (`eslint`) de todos os arquivos frontend alterados — 0 erros (2 warnings pré-existentes de "no matching configuration" em arquivos fora do escopo de lint, não relacionados).
- [x] Suite completa do frontend: 170/173 — mesmas 3 falhas pré-existentes não relacionadas.

## Critérios de aceite

- [x] Admin escolhe entre convite por e-mail e senha manual ao criar usuário.
- [x] Usuário convidado não pode logar até aceitar o convite.
- [x] Convite expira e pode ser reenviado.
- [x] Aceitar convite ou redefinir senha autentica automaticamente.
- [x] "Esqueci senha" não revela quais e-mails existem.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
- [ ] SMTP real configurado em produção — pendente (atualmente em modo log/fallback).
- [ ] Validação manual end-to-end (criar com convite, receber e-mail real, aceitar, logar) — não executada nesta sessão.

## Riscos e pendências

- [ ] Deploy da migration `20260619_0900_user_invite_password_reset` na VPS.
- [ ] Configurar credenciais SMTP reais em produção.
- [x] `backend/tests/test_user_invite_password_reset.py` executado de fato (15/15) — venv criado em `backend/.venv`, não versionado.
- [ ] Reconfirmar com o usuário as duas decisões de escopo tomadas sem `AskUserQuestion` (SMTP genérico; `account_status` como string) na próxima interação.
