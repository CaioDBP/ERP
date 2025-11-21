#!/usr/bin/env bash
set -o errexit

# ==============================
# Atualiza pacotes do sistema
# ==============================
apt-get update

# ==============================
# Instala dependências nativas necessárias para o WeasyPrint
# ==============================
apt-get install -y \
    libcairo2 \
    pango1.0-tools \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libmagic1

# ==============================
# Instala dependências Python
# ==============================
pip install --upgrade pip
pip install -r requirements.txt

# ==============================
# Instala modelo spaCy (pt_core_news_md)
# ==============================
python -m spacy download pt_core_news_md || true
