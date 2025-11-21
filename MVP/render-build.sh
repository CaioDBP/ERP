#!/usr/bin/env bash
set -o errexit

apt-get update

# ---------------------------
# Dependências do WeasyPrint
# ---------------------------
apt-get install -y \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libssl-dev \
    libglib2.0-0 \
    libxml2 \
    libxml2-dev \
    libxslt1-dev \
    shared-mime-info \
    fonts-dejavu-core

# ---------------------------
# Dependências do spacy e pacotes Python nativos
# ---------------------------
apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev
