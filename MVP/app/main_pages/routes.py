from flask import Blueprint, render_template
from app.models import Pedido

# Este Blueprint servirá todas as suas páginas HTML.
# Não terá um prefixo de URL para que as rotas sejam simples, ex: /login, /pedidos.
main_pages_bp = Blueprint('main_pages', __name__)

@main_pages_bp.route('/')
@main_pages_bp.route('/login')
def login_page():
    """Rota para a página de login."""
    return render_template('login.html')

@main_pages_bp.route('/pedidos')
def list_pedidos_page():
    """Rota para a página de listagem de pedidos."""
    return render_template('pedidos.html')

@main_pages_bp.route('/pedidos/novo')
def new_pedido_page():
    """Rota para a página de criação de um novo pedido."""
    return render_template('novo_pedido.html')

@main_pages_bp.route('/pedidos/<pedido_id>')
def details_pedido_page(pedido_id):
    """Rota para a página de detalhes de um pedido específico."""
    pedido = Pedido.query.filter_by(id=pedido_id).first()

    # O 'pedido_id' pode ser usado pelo JavaScript na página para buscar os dados.
    return render_template( "pedido_detalhes.html", pedido = pedido)

@main_pages_bp.route('/contratos')
def upload_contratos_page():
    """Rota para a página de upload de contratos."""
    return render_template('contratos.html')

@main_pages_bp.route('/exportar')
def exportar_planilha_page():
    """Rota para a página de exportação de planilhas."""
    return render_template('exportar.html')






# @main_pages_bp.route('/relatorios')
# def relatorios_page():
#     """Rota para a página de relatórios e indicadores."""
#     return render_template('relatorios.html')
from datetime import datetime
from app.models import Pedido
from sqlalchemy import func
from app import db
@main_pages_bp.route('/relatorios')
def dashboard():

    # total_pedidos = db.session.query(func.count(Pedido.id)).scalar()
    total_pedidos = 33
    produto_mais_pedido = "Doces Finos"
    produto_mais_pedido_qntd = 44
    receita_total = {"valor": 20000}
    pedidos_urgentes = 8

    pedidos_mensais = [12, 19, 15, 25, 32, 28]
    
    categorias = {
        "Doces Finos": 40,
        "Bem-casados": 25,
        "Bolos": 20
    }
    top_clientes = {
        "Maria S.": 8,
        "João P.": 6,
        "Ana C.": 5,
        "Pedro L.": 4,
        "Carla M.": 3
    }
    comparativo = {
        "2025": [12, 19, 15, 25, 32, 28],
        "2024": [8, 14, 12, 18, 24, 22],
        "2023" : [4,16,10,22,20,34],
        "2022" : [7,16,30,28,19,36]

    }

    return render_template(
        'relatorios.html',
        total_pedidos=total_pedidos,
        produto_mais_pedido=produto_mais_pedido,
        produto_mais_pedido_qntd=produto_mais_pedido_qntd,
        receita_total=receita_total,
        pedidos_uregentes=pedidos_urgentes,
        pedidos_mensais=pedidos_mensais,
        categorias=categorias,
        top_clientes=top_clientes,
        comparativo=comparativo
    )





@main_pages_bp.route('/contratos/novo')
def novo_contrato_page():
    """Rota para a página de criação de um novo contrato."""
    return render_template('novo_contrato.html')


@main_pages_bp.route('/calculadora')
def calculadora_custos_page():
    """Rota para a página da calculadora de custos."""
    return render_template('calculadora.html')

@main_pages_bp.route('/equipe')
def pagina_equipe():
    """ Rota para página da equipe. """
    return render_template("equipe.html")