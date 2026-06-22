# SPEC 019 — Usuários com Senha/Convite

Status: implementada — backend validado por revisão manual + sintaxe (pytest indisponível no ambiente); frontend sem regressão (170/173 testes); deploy/migration e teste manual end-to-end pendentes.

## Problema original

Do documento mestre (`2026-06-correcoes-player-radio-windows.md`): "Criação de usuário não permite definir senha nem envia acesso por e-mail" — o admin não tinha como escolher entre definir uma senha manualmente ou convidar o usuário por e-mail; a tela gerava uma senha temporária no cliente e a exibia em um toast, sem qualquer envio real de e-mail.

## Decisão de escopo

Diagnóstico confirmou que o projeto não tinha nenhuma infraestrutura de e-mail (SMTP) nem de convite/reset de senha. Sem acesso ao `AskUserQuestion` nesta sessão (falha repetida de stream), a implementação seguiu com dois defaults de menor risco, sinalizados ao usuário em texto simples e sujeitos a correção posterior:

- E-mail: serviço SMTP genérico via variáveis de ambiente, com fallback de log quando não configurado (não bloqueia a criação de usuário em ambiente de desenvolvimento).
- `account_status`: mantido como `String` solto (não migrado para enum formal), apenas com `"pending_invite"` adicionado como novo valor aceito — consistente com o uso já existente do campo no restante do código.

## O que foi entregue

- Admin escolhe, ao criar um usuário, entre "Enviar convite por e-mail" ou "Definir senha agora".
- Usuário criado via convite fica em `account_status="pending_invite"`, sem `password_hash`, e não pode logar até aceitar o convite e definir senha.
- Convite expira (`INVITE_TOKEN_EXPIRE_HOURS`, padrão 72h); admin pode reenviar (gera novo token, invalida o anterior).
- Fluxo de "Esqueci minha senha" para usuários já ativos, com token de expiração curta (`PASSWORD_RESET_TOKEN_EXPIRE_HOURS`, padrão 2h).
- Auditoria via `UserLog`/`UserLogAction` reaproveitada, com dois novos valores (`resend_invite`, `accept_invite`).

## Pendências explícitas

- Configuração real de SMTP em produção (ver `design.md`).
- Validação manual end-to-end do fluxo de convite e de reset de senha (ver `tests.md`).
- Deploy da migration `20260619_0900_user_invite_password_reset` na VPS.
