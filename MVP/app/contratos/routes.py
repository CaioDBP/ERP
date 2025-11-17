# Arquivo: app/contratos/routes.py (VERSÃO REVISADA, ESTÁVEL E SEGURO)

import re
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from app import db
from app.models import Pedido
from typing import Dict, Any
from io import BytesIO


# Importações do Extractor
try:
    from app.Extractor import (
        extrair_dados_do_contrato_por_tipo,
        gerar_contrato_docx,
        gerar_contrato_pdf_direto
    )
except ImportError:
    def extrair_dados_do_contrato_por_tipo(file_bytes, tipo_analise, file_extension):
        print("AVISO: Função extrair_dados_do_contrato_por_tipo não implementada.")
        return {}

    def gerar_contrato_docx(dados):
        print("AVISO: Função gerar_contrato_docx não implementada.")
        return BytesIO(b"Documento DOCX placeholder.")

    def gerar_contrato_pdf_direto(dados):
        print("AVISO: Função gerar_contrato_pdf_direto não implementada.")
        return BytesIO(b"%PDF-1.4\n%EOF")


contratos_bp = Blueprint('contratos', __name__, url_prefix='/api/contracts')

# ============================================================================
# SANITIZADOR DE DADOS – GARANTE JSON VÁLIDO
# ============================================================================
def _sanitize(value):
    """
    Converte qualquer estrutura Python em algo JSON-serializável.
    """
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    elif isinstance(value, list):
        return [_sanitize(v) for v in value]

    elif isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}

    return str(value)  # fallback para qualquer objeto estranho


# ============================================================================
# ROTA DE UPLOAD E EXTRAÇÃO
# ============================================================================
@contratos_bp.route('/upload', methods=['POST'])
def upload_contract():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado.'}), 400

    filename = file.filename
    _, file_extension = os.path.splitext(filename)
    file_extension = file_extension.lower()

    if file_extension not in ['.pdf', '.docx']:
        return jsonify({'message': 'Formato inválido. Envie PDF ou DOCX.'}), 400

    tipo_analise = request.form.get('tipo_analise', 'padrao')

    try:
        file_bytes = file.read()

        dados_extraidos = extrair_dados_do_contrato_por_tipo(
            file_bytes,
            tipo_analise,
            file_extension
        )

        if not dados_extraidos:
            return jsonify({'message': 'Falha ao extrair dados.'}), 500

        # 🔥 CORREÇÃO CRÍTICA — Sanitiza antes de enviar
        dados_extraidos = _sanitize(dados_extraidos)

        return jsonify({
            'message': 'Dados extraídos com sucesso! Revise para salvar.',
            'extractedData': dados_extraidos,
        }), 200

    except Exception as e:
        print(f"[ERRO] Falha na rota /upload: {e}")
        return jsonify({'message': f'Erro ao processar contrato: {str(e)}'}), 500



# ============================================================================
# ROTA PARA GERAR CONTRATO (DOCX OU PDF)
# ============================================================================
@contratos_bp.route('/gerar-contrato', methods=['POST'])
def gerar_contrato():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    formato_desejado = data.get('formato_desejado', 'docx')

    # --- Tratar JSON de produtos ---
    produtos_contratados = []
    produtos_data = data.get('produtosContratados')

    if isinstance(produtos_data, str):
        try:
            produtos_contratados = json.loads(produtos_data)
        except:
            produtos_contratados = []

    elif isinstance(produtos_data, list):
        produtos_contratados = produtos_data

    # Mapeamento dos dados para o contrato
    contratante_info = {
        'Nome': data.get('contratanteNome'),
        'RG': data.get('contratanteRg'),
        'CPF': data.get('contratanteCpf'),
        'Endereco': data.get('contratanteEndereco'),
        'Telefone': data.get('contratanteTelefone'),
        'Email': data.get('contratanteEmail'),
    }

    dados_para_contrato = {
        'Contratante': contratante_info,
        'Data do Evento': data.get('dataEvento'),
        'Horario do Evento': data.get('horarioEvento'),
        'Local do Evento': data.get('localEvento'),
        'Produtos Contratados': produtos_contratados,
        'Valor Total do Pedido': data.get('valorTotalPedidoContrato'),
        'Data de Pagamento': data.get('dataPagamentoContrato'),
        'Forma de Pagamento': data.get('formaPagamento'),
        'Como nos conheceu': data.get('comoConheceu'),
        'Responsavel': data.get('responsavelContrato'),
    }

    try:
        response, error = _processar_e_enviar_contrato(dados_para_contrato, formato_desejado)
        if error:
            return jsonify({'message': error}), 500
        return response

    except Exception as e:
        print(f"[ERRO] Gerar contrato: {e}")
        return jsonify({'message': f'Erro ao gerar contrato: {str(e)}'}), 500



# ============================================================================
# PROCESSADOR DE SAÍDA DE ARQUIVO
# ============================================================================
def _processar_e_enviar_contrato(dados: Dict[str, Any], formato: str):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nome_cliente_safe = re.sub(r'[^\w-]', '_', dados['Contratante'].get('Nome', 'Contrato')).lower()
    nome_base = f"contrato_{nome_cliente_safe}_{timestamp}"

    if formato == 'pdf':
        print("[INFO] Gerando contrato PDF...")
        pdf_stream = gerar_contrato_pdf_direto(dados)
        if not pdf_stream:
            return None, "Erro interno ao gerar PDF."

        return send_file(
            pdf_stream,
            as_attachment=True,
            download_name=f"{nome_base}.pdf",
            mimetype='application/pdf'
        ), None

    print("[INFO] Gerando contrato DOCX...")
    doc_stream = gerar_contrato_docx(dados)
    if not doc_stream:
        return None, "Erro interno ao gerar DOCX."

    return send_file(
        doc_stream,
        as_attachment=True,
        download_name=f"{nome_base}.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ), None
