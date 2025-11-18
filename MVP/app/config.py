import os
from sqlalchemy.pool import NullPool


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma_chave_secreta_padrao_para_desenvolvimento'
    # Configurações do Banco de Dados (SQLite por padrão, substitua via env var DATABASE_URL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Habilita pre-ping para detectar conexões mortas antes de usá-las
    SQLALCHEMY_POOL_PRE_PING = True

    # Para provedores serverless (Neon, RDS proxy etc.) é mais estável usar NullPool
    # Isso evita reutilizar conexões que o servidor fechou. Mantemos também connect_args
    # para forçar sslmode quando o DATABASE_URL não incluir o parâmetro.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool,
        'pool_pre_ping': True,
        'connect_args': {
            'sslmode': os.environ.get('PGSSLMODE', 'require')
        }
    }

    # Outras configurações globais podem vir aqui, ex:
    # WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY')

    # 🟢 Diretório base do projeto
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # 🟢 Pasta onde os arquivos enviados serão salvos
    UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads')