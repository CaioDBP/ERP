from flask import Blueprint, request, jsonify
from app import db                  # Importamos a instância do banco de dados
from app.models import User         # Importamos nosso modelo User
from werkzeug.security import generate_password_hash, check_password_hash # Ferramentas para hashing

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Em app/auth/routes.py

@auth_bp.route('/register', methods=['POST'])
def register_user():
    # Registro desabilitado: endpoint retorna 403 para impedir criação pública de contas.
    return jsonify({'message': 'Registro de novos usuários está desabilitado.'}), 403

@auth_bp.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'E-mail e senha são obrigatórios.'}), 400

    # Busca o usuário pelo e-mail no banco de dados
    user = User.query.filter_by(email=email).first()

    # Verifica se o usuário existe E se a senha fornecida corresponde ao hash guardado
    if user and check_password_hash(user.password_hash, password):
        # O login é bem-sucedido!
        # Agora retornamos o ID numérico do usuário, que é mais seguro e padrão.
        return jsonify({'message': 'Login bem-sucedido!', 'userId': user.id}), 200
    else:
        # Se o usuário não existe ou a senha está errada, a mensagem é a mesma por segurança.
        return jsonify({'message': 'E-mail ou senha incorretos.'}), 401