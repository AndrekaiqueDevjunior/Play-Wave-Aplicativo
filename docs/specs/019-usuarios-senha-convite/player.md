# SPEC 019 — Player

Status: não aplicável — esta SPEC não afeta o player.

## Por que não se aplica

SPEC 019 trata exclusivamente do fluxo administrativo de autenticação (criação de usuário, convite por e-mail, reset de senha) no painel web (`frontend/src/pages/ConfigUsuario.jsx`, `frontend/src/pages/Login.jsx`) e nos endpoints correspondentes (`backend/api/v1/auth.py`, `backend/api/v1/users.py`).

O player (`frontend/src/pages/Player.jsx` e o app desktop Electron) se autentica via token de dispositivo (`device_token`), um mecanismo totalmente separado do login de usuários administrativos alterado nesta SPEC. Nenhum arquivo do player foi tocado.
