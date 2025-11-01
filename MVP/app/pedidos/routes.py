# Arquivo: app/pedidos/routes.py (VERSÃO MESCLADA E FINAL)

from flask import Blueprint, request, jsonify, current_app, send_from_directory, abort, url_for
from datetime import datetime
from app import db
# (Imports da versão deles, mantendo as novas funcionalidades)
from app.models import Pedido, User, Arquivo, InteracaoPedido 
import os # (Import da versão deles)

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')

@pedidos_bp.route('/cadastro', methods=['POST'])
def create_pedido_cadastro():
    """Rota para criar pedidos a partir do formulário de cadastro."""
    data = request.json
    user_id = request.headers.get('X-User-Id')

    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401
    
    required_fields = ['clienteNome', 'dataEvento', 'quantidade', 'tipoPedido', 'dataRetirada', 'horarioRetirada']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Campos obrigatórios faltando.'}), 400

    new_pedido = Pedido(
        clienteNome=data['clienteNome'],
        dataEvento=data['dataEvento'], # (Confia que o frontend envia no formato YYYY-MM-DD)
        dataRetirada=data['dataRetirada'],
        horarioRetirada=data['horarioRetirada'],
        tipoPedido=data['tipoPedido'],
        quantidade=int(data['quantidade']),
        sabores=data.get('sabores', ''),
        tipoEmbalagem=data.get('tipoEmbalagem', ''),
        observacoes=data.get('observacoes', ''),
        status='pendente',
        prioridade=data.get('prioridade', 'normal'),
        responsavel=data.get('responsavel', None),
        user_id=user_id,
        clienteRG=data.get('clienteRG', ''),
        clienteCPF=data.get('clienteCPF', ''),
        nomeContratado=data.get('nomeContratado', ''),
        cnpjContratado=data.get('cnpjContratado', ''),
        valorTotalPedidoContrato=data.get('valorTotalPedidoContrato', ''),
        dataPagamentoContrato=data.get('dataPagamentoContrato', ''),
        localEvento=data.get('localEvento', ''),
        produtosContratadosJson=data.get('produtosContratadosJson', '[]')
    )

    db.session.add(new_pedido)
    db.session.commit()

    return jsonify({'message': 'Pedido salvo com sucesso!', 'pedido': new_pedido.to_dict()}), 201

#
# --- Bloco Mesclado e Corrigido ---
# Mantivemos a rota POST / (que lida com o upload do contrato)
# mas substituí a lógica de data frágil pela lógica limpa da rota /cadastro.
#
@pedidos_bp.route('', methods=['POST'])
def create_pedido():
    """Essa função lida com o pedido que vem do upload contrato."""
    data = request.json
    user_id = request.headers.get('X-User-Id')

    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401
    
    required_fields = ['clienteNome', 'dataEvento', 'quantidade', 'tipoPedido', 'dataRetirada', 'horarioRetirada']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Campos obrigatórios faltando.'}), 400

    # (LÓGICA DE DATA FRÁGIL REMOVIDA)
    # Assumimos que o frontend (após a revisão do usuário)
    # enviará a data no formato correto YYYY-MM-DD.
    
    new_pedido = Pedido(
        clienteNome=data['clienteNome'],
        dataEvento=data['dataEvento'], # (Lógica limpa)
        dataRetirada=data['dataRetirada'],
        horarioRetirada=data['horarioRetirada'],
        tipoPedido=data['tipoPedido'],
        quantidade=int(data['quantidade']),
        sabores=data.get('sabores', ''),
        tipoEmbalagem=data.get('tipoEmbalagem', ''),
        observacoes=data.get('observacoes', ''),
        status='pendente',
        prioridade=data.get('prioridade', 'normal'),
        responsavel=data.get('responsavel', None),
        user_id=user_id,
        clienteRG=data.get('clienteRG', ''),
        clienteCPF=data.get('clienteCPF', ''),
        nomeContratado=data.get('nomeContratado', ''),
        cnpjContratado=data.get('cnpjContratado', ''),
        valorTotalPedidoContrato=data.get('valorTotalPedidoContrato', ''),
        dataPagamentoContrato=data.get('dataPagamentoContrato', ''),
        localEvento=data.get('localEvento', ''),
        produtosContratadosJson=data.get('produtosContratadosJson', '[]')
    )

    db.session.add(new_pedido)
    db.session.commit()

    return jsonify({'message': 'Pedido salvo com sucesso!', 'pedido': new_pedido.to_dict()}), 201
# --- Fim do Bloco Mesclado ---
#

@pedidos_bp.route('', methods=['GET'])
def get_pedidos():
    """Lista todos os pedidos (lógica da versão deles)."""
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    query = Pedido.query.filter_by(user_id=user_id)

    filtro_cliente = request.args.get('cliente', '').lower()
    if filtro_cliente:
        query = query.filter(Pedido.clienteNome.ilike(f'%{filtro_cliente}%'))

    filtro_data_evento = request.args.get('dataEvento', '')
    if filtro_data_evento:
        query = query.filter_by(dataEvento=filtro_data_evento)

    filtro_status = request.args.get('status', '')
    if filtro_status:
        if ',' in filtro_status:
            status_list = filtro_status.split(',')
            query = query.filter(Pedido.status.in_(status_list))
        else:
            query = query.filter_by(status=filtro_status)
    
    pedidos = query.order_by(Pedido.createdAt.desc()).all()
    
    pedidos_dict = [pedido.to_dict() for pedido in pedidos]

    return jsonify(pedidos_dict), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['GET'])
def get_pedido_details(pedido_id):
    """Busca detalhes de um pedido (lógica da versão deles)."""
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.filter_by(id=pedido_id, user_id=user_id).first()
    if pedido:
        return jsonify(pedido.to_dict()), 200
    return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

@pedidos_bp.route('/<int:pedido_id>', methods=['PUT'])
def update_pedido(pedido_id):
    """Atualiza um pedido (lógica da versão deles)."""
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.filter_by(id=pedido_id, user_id=user_id).first()
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

    data = request.json
    
    for key, value in data.items():
        if hasattr(pedido, key) and key not in ['id', 'userId', 'createdAt']:
            setattr(pedido, key, value)
    
    db.session.commit()
    return jsonify({'message': 'Pedido atualizado com sucesso!', 'pedido': pedido.to_dict()}), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    """Exclui um pedido (lógica da versão deles)."""
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.filter_by(id=pedido_id, user_id=user_id).first()
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404
        
    db.session.delete(pedido)
    db.session.commit()
    return jsonify({'message': 'Pedido excluído com sucesso!'}), 200

#
# --- INÍCIO DAS NOVAS FUNCIONALIDADES DELES (MANTIDAS 100%) ---
#

# Rotas para historico de interações
@pedidos_bp.route('/<int:pedido_id>/interacoes', methods=['GET'])
def get_interacoes(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    interacoes = InteracaoPedido.query.filter_by(pedido_id=pedido_id).order_by(InteracaoPedido.data_interacao.desc()).all()
    return jsonify([i.to_dict() for i in interacoes]), 200

@pedidos_bp.route('/<int:pedido_id>/interacoes', methods=['POST'])
def add_interacao(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    autor = data.get('autor')
    mensagem = data.get('mensagem')

    if not mensagem:
        return jsonify({'message': 'Mensagem é obrigatória.'}), 400

    nova_interacao = InteracaoPedido(
        pedido_id=pedido_id,
        autor=autor or 'Usuário Desconhecido',
        mensagem=mensagem
    )

    db.session.add(nova_interacao)
    db.session.commit()

    return jsonify({'message': 'Interação adicionada com sucesso!'}), 201

# Rotas para anexar arquivos aos pedidos
@pedidos_bp.route('/<int:pedido_id>/upload', methods=['POST'])
def upload_arquivo(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.filter_by(id=pedido_id, user_id=user_id).first()
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado.'}), 400

    file = request.files['file']
    legenda = request.form.get('legenda', '')

    if file.filename == '':
        return jsonify({'message': 'Arquivo sem nome.'}), 400

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'pedido_{pedido_id}')
    os.makedirs(upload_dir, exist_ok=True)
    full_path =  os.path.join(upload_dir, file.filename)
    file.save(full_path)

    relative_path = f'pedido_{pedido_id}/{file.filename}' 

    novo_arquivo = Arquivo(
        pedido_id=pedido_id,
        nome=file.filename,
        legenda=legenda,
        caminho=relative_path,
        data_envio=datetime.now()
    )
    db.session.add(novo_arquivo)
    db.session.commit()

    return jsonify({'message': 'Arquivo enviado com sucesso!'}), 200

@pedidos_bp.route('/<int:pedido_id>/arquivos', methods=['GET'])
def listar_arquivos(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    arquivos = Arquivo.query.filter_by(pedido_id=pedido_id).all()
    
    lista_de_arquivos = []
    for a in arquivos:
        url_visualizacao = url_for('pedidos.servir_arquivo', filename=a.caminho)
        
        lista_de_arquivos.append({
            'id': a.id,
            'nome': a.nome,
            'legenda': a.legenda,
            'data_envio': a.data_envio.strftime('%d/%m/%Y %H:%M'),
            'url': url_visualizacao
        })
        
    return jsonify(lista_de_arquivos)

@pedidos_bp.route('/uploads/view/<path:filename>', methods=['GET'])
def servir_arquivo(filename):
    """Esta rota serve os arquivos para VISUALIZAÇÃO."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    try:
        return send_from_directory(
            upload_folder,
            filename
        )
    except FileNotFoundError:
        return jsonify({'message': 'Arquivo não encontrado.'}), 404

@pedidos_bp.route('/uploads/download/<path:filename>', methods=['GET'])
def download_uploaded_file(filename):
    """Esta rota serve os arquivos para DOWNLOAD."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    try:
        return send_from_directory(
            upload_folder,
            filename,
            as_attachment=True # <- força o download
        )
    except FileNotFoundError:
        return jsonify({'message': 'Arquivo não encontrado.'}), 404
#
# --- FIM DAS NOVAS FUNCIONALIDADES DELES ---
#