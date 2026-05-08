#!/bin/sh
set -e

echo "==> Aguardando banco de dados..."
until python3 -c "
import sys, os
import psycopg2
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    print('  Banco disponível.')
except Exception as e:
    print(f'  Aguardando: {e}')
    sys.exit(1)
" 2>&1; do
  sleep 2
done

echo "==> Inicializando banco..."
python3 init_db.py

echo "==> Iniciando API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
