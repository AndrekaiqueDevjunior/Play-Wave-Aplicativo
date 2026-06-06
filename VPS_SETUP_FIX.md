# VPS Setup - Database Fix

## Problema
Após rebuild do backend na VPS, o endpoint `/campaigns` retorna erro porque há incompatibilidades entre o schema do banco de dados e os modelos Python.

## Solução Rápida (Execute na VPS)

```bash
cd /opt/playwave

# 1. Executar script de correção
docker compose -f docker-compose.production.yml exec -T backend \
  python3 /app/scripts/fix_vps_database.py

# 2. Reiniciar backend
docker compose -f docker-compose.production.yml restart backend

# 3. Aguardar health check
sleep 5
docker compose -f docker-compose.production.yml ps backend

# 4. Testar (substituir <token> com token válido)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/campaigns/
```

## O que o script corrige

1. **Admin Password**: Reset do hash de senha do admin para `Playwave@123`
2. **Device Commands Status**: Remove valores inválidos (RECEIVED, EXECUTING)
3. **Enum Values**: Valida que enums estão no formato esperado (lowercase para audio, uppercase para device commands)

## Problemas conhecidos resolvidos

- ✅ Enum `audioplayliststatus` com valores inválidos → Corrigido
- ✅ Enum `audiotrackstatus` com valores minúsculos → Verificado
- ✅ Device commands com status inválido ('RECEIVED') → Corrigido
- ✅ Admin password hash corrompido → Corrigido

## Se ainda houver problema

Se após estas correções a API ainda não responder:

1. Verificar logs do backend:
```bash
docker compose -f docker-compose.production.yml logs backend --tail 50
```

2. Verificar diretamente no PostgreSQL:
```bash
docker compose -f docker-compose.production.yml exec -T postgres psql -U playwave -d playwave
# SELECT COUNT(*) FROM campaigns;
# SELECT DISTINCT status FROM audio_playlists;
```

3. Fazer rebuild completo:
```bash
docker compose -f docker-compose.production.yml build --no-cache backend
docker compose -f docker-compose.production.yml up -d backend
```
