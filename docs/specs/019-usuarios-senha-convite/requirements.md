# SPEC 019 — Requirements

## Origem

Master doc `2026-06-correcoes-player-radio-windows.md`: "Criação de usuário não permite definir senha nem envia acesso por e-mail."

## Requisitos funcionais

- RF01 — Ao criar um usuário, o admin deve poder escolher entre definir uma senha manualmente ou enviar um convite por e-mail.
- RF02 — Um usuário criado sem senha (via convite) deve ficar em `account_status="pending_invite"`.
- RF03 — Login deve ser bloqueado para usuários em `pending_invite` ou sem `password_hash`, com mensagem clara orientando a aceitar o convite.
- RF04 — O convite deve expirar após um período configurável (`INVITE_TOKEN_EXPIRE_HOURS`, padrão 72h).
- RF05 — O admin deve poder reenviar o convite para um usuário com `pending_invite`, invalidando o token anterior.
- RF06 — O usuário deve poder aceitar o convite via link único (token) e definir sua própria senha, passando a `account_status="active"`.
- RF07 — Usuários já ativos devem poder solicitar redefinição de senha ("esqueci minha senha") por e-mail, com token de expiração curta (`PASSWORD_RESET_TOKEN_EXPIRE_HOURS`, padrão 2h).
- RF08 — Toda ação de convite/reenvio/aceite/reset deve ser registrada em log de auditoria (`UserLog`).
- RF09 — A resposta de "esqueci minha senha" deve ser genérica independente do e-mail existir, para não permitir enumeração de usuários cadastrados.

## Requisitos não funcionais

- RNF01 — Quando SMTP não está configurado, o sistema não deve falhar a operação (criação de usuário, reenvio, etc.) — apenas registrar em log o conteúdo que seria enviado.
- RNF02 — Tokens de convite/reset devem ser opacos (não JWT), únicos, e nunca expostos em respostas de API que não sejam o e-mail enviado ao usuário.
- RNF03 — Compatibilidade retroativa: usuários existentes (todos com senha já definida) não são afetados pela mudança de `password_hash` para nullable.

## Critérios de aceite

- [x] Criar usuário com convite por e-mail → `pending_invite`, sem senha, token gerado, e-mail (real ou logado) enviado.
- [x] Criar usuário com senha manual → `active`, login imediato funciona.
- [x] Login bloqueado para `pending_invite` com mensagem específica (não a mensagem genérica de credenciais incorretas).
- [x] Reenviar convite gera novo token e nova expiração, invalidando o anterior.
- [x] Aceitar convite com token válido define senha, ativa o usuário e retorna sessão autenticada.
- [x] Aceitar convite com token expirado ou inválido é rejeitado com mensagem clara.
- [x] Esqueci senha sempre responde com a mesma mensagem genérica, exista ou não o e-mail.
- [x] Reset de senha com token válido define nova senha e retorna sessão autenticada; token expirado/inválido é rejeitado.
- [ ] Validação manual end-to-end com SMTP real configurado — pendente (ver `tests.md`).
