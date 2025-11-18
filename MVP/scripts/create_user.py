#!/usr/bin/env python
"""
Script para criar um usuário manualmente no banco de dados da aplicação.
Uso:
  python scripts/create_user.py --email user@example.com --nome "Nome" [--senha S3nh@] [--tipo funcionario]
Se a senha não for passada via argumento, o script pedirá de forma invisível.

O script usa a factory `create_app()` definida em `app/__init__.py` e o modelo `User`.
"""

import argparse
import getpass
import os
import sys
from werkzeug.security import generate_password_hash

# Garante que o diretório do projeto (MVP) esteja no sys.path quando o script
# for executado diretamente. Isso evita ModuleNotFoundError: No module named 'app'.
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app import create_app, db
    from app.models import User
except ModuleNotFoundError as e:
    print('Erro ao importar o pacote `app`. Verifique se você está executando o script a partir do diretório correto e se o projeto está presente.')
    print('Projeto root esperado em:', PROJECT_ROOT)
    raise


def create_user(email: str, nome: str, senha: str, tipo_usuario: str = 'funcionario'):
    app = create_app()
    with app.app_context():
        # Verifica se já existe usuário com o email
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Erro: já existe usuário com o e-mail {email} (id={existing.id}).")
            return 1

        hashed = generate_password_hash(senha)
        user = User(email=email, nome_completo=nome, tipo_usuario=tipo_usuario, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        print(f"Usuário criado com sucesso. id={user.id}, email={user.email}")
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Criar usuário manualmente no banco (admin).')
    parser.add_argument('--email', '-e', required=True, help='E-mail do usuário')
    parser.add_argument('--nome', '-n', required=True, help='Nome completo do usuário')
    parser.add_argument('--senha', '-s', help='Senha do usuário (se ausente, será solicitada)')
    parser.add_argument('--tipo', '-t', default='funcionario', choices=['funcionario', 'administrador'], help='Tipo de usuário')

    args = parser.parse_args()

    # debug rápido para ajudar em casos onde o prompt não aparece
    print('DEBUG: iniciando create_user.py')
    print('DEBUG: caminho do projeto:', PROJECT_ROOT)
    print('DEBUG: stdin isatty =', sys.stdin.isatty())

    senha = args.senha
    if not senha:
        senha = getpass.getpass('Senha (não será mostrada): ')
        senha_confirm = getpass.getpass('Confirme a senha: ')
        if senha != senha_confirm:
            print('As senhas não coincidem. Abortando.')
            raise SystemExit(1)

    code = create_user(args.email.strip(), args.nome.strip(), senha, args.tipo)
    raise SystemExit(code)
