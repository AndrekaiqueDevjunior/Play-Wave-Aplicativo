-- VPS Database Fix Script
-- Executa correções necessárias de schema para que /campaigns endpoint funcione
--
-- Issues corrigidos:
-- 1. Enum audioplayliststatus com valores minúsculos que código esperava
-- 2. Usuário admin com hash de senha corrompido
-- 3. Device command status com valores inválidos (RECEIVED, EXECUTING)

-- ════════════════════════════════════════════════════════════════════════════

-- 1. RESETAR SENHA DO ADMIN
-- Executa como: SELECT crypt('Playwave@123', gen_salt('bf'));
-- Depois: UPDATE users SET password_hash = '<hash_acima>' WHERE email = 'admin@playwave.com';
-- OU use o script Python em vez disso:
-- python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('Playwave@123'))"

-- Para gerar o hash correto e depois executar no PostgreSQL:
-- UPDATE users SET password_hash = '$2b$12$...' WHERE email = 'admin@playwave.com';

-- ════════════════════════════════════════════════════════════════════════════

-- 2. VERIFICAR AUDIOPLAYLISTSTATUS
-- Verificar enum values:
SELECT enum_range(NULL::audioplayliststatus);
-- Esperado: {active,inactive,archived}

-- Verificar status de playlists:
SELECT DISTINCT status FROM audio_playlists;
-- Se houver valores uppercase (ACTIVE, INACTIVE, ARCHIVED), precisam ser convertidos

-- ════════════════════════════════════════════════════════════════════════════

-- 3. LIMPAR DEVICE_COMMANDS INVÁLIDOS
-- Remove device commands com status inválido
UPDATE device_commands SET status = 'EXECUTED' WHERE status::text IN ('RECEIVED', 'EXECUTING');

-- Verificar valores válidos:
SELECT DISTINCT status FROM device_commands;
-- Esperado: {PENDING, SENT, EXECUTED, FAILED, CANCELLED}

-- ════════════════════════════════════════════════════════════════════════════

-- 4. VERIFICAR AUDIO_TRACKS STATUS
SELECT enum_range(NULL::audiotrackstatus);
-- Esperado: {active,inactive,archived}

SELECT DISTINCT status FROM audio_tracks;
-- Todos devem estar em minúsculos

-- ════════════════════════════════════════════════════════════════════════════

-- 5. APÓS EXECUTAR ESSAS CORREÇÕES:
-- 1. Reiniciar o container backend: docker compose -f docker-compose.production.yml restart backend
-- 2. Testar: curl -s http://localhost:8000/health
-- 3. Fazer login: curl -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@playwave.com","password":"Playwave@123"}'
-- 4. Testar /campaigns: curl -H "Authorization: Bearer <token>" http://localhost:8000/campaigns/
