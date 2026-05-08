# ===========================================
# IMAGEM BASE PYTHON
# ===========================================
FROM python:3.11-slim as base

# ===========================================
# CONFIGURAÇÕES DE AMBIENTE
# ===========================================
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ===========================================
# INSTALAÇÃO DE DEPENDÊNCIAS DO SISTEMA
# ===========================================
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ===========================================
# DIRETÓRIO DE TRABALHO
# ===========================================
WORKDIR /app

# ===========================================
# COPIA E INSTALAÇÃO DE DEPENDÊNCIAS PYTHON
# ===========================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===========================================
# COPIA DO CÓDIGO FONTE
# ===========================================
COPY . .

# ===========================================
# CRIAÇÃO DE DIRETÓRIOS NECESSÁRIOS
# ===========================================
RUN mkdir -p uploads/media uploads/audio/tracks logs alembic/versions

# ===========================================
# PERMISSÕES DOS DIRETÓRIOS
# ===========================================
RUN chmod -R 755 uploads logs alembic

# Script de inicialização (roda init_db.py antes do uvicorn)
RUN chmod +x start.sh

# ===========================================
# EXPOSIÇÃO DA PORTA
# ===========================================
EXPOSE 8000

# ===========================================
# COMANDO DE INICIALIZAÇÃO
# ===========================================
CMD ["/bin/sh", "start.sh"]
