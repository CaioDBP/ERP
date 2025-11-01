# Arquivo: app/contratos/routes.py (VERSÃO 7 - SUPORTE A .DOCX)

import re
import os # <-- IMPORTANTE: Nova importação
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from app import db
from app.models import Pedido
from typing import Dict, Any

# (As importações do Extractor permanecem as mesmas)
from app.Extractor import (
    extrair_dados_do_contrato_por_tipo,
    gerar_contrato_docx,
    gerar_contrato_pdf_direto
)

contratos_bp = Blueprint('contratos', __name__, url_prefix='/api/contracts')

# ==============================================================================
# ROTA DE UPLOAD E ANÁLISE (ATUALIZADA)
# ==============================================================================
@contratos_bp.route('/upload', methods=['POST'])
def upload_contract():
    """
    Recebe um arquivo (PDF ou DOCX), extrai os dados e os retorna ao frontend
    para que o usuário possa revisar.
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado.'}), 400

    # --- MUDANÇA (SUPORTE A .DOCX) ---
    # 1. Pega o nome do arquivo e extrai a extensão
    filename = file.filename
    _, file_extension = os.path.splitext(filename)
    file_extension = file_extension.lower() # Garante que seja .pdf e não .PDF

    # 2. Valida a extensão
    if file_extension not in ['.pdf', '.docx']:
        return jsonify({'message': 'Formato de arquivo inválido. Envie apenas .pdf ou .docx'}), 400
    # --- FIM DA MUDANÇA ---

    tipo_analise = request.form.get('tipo_analise', 'padrao')

    try:
        file_bytes = file.read()

        # --- MUDANÇA (SUPORTE A .DOCX) ---
        # 3. Passa a extensão do arquivo para a função de extração
        dados_extraidos = extrair_dados_do_contrato_por_tipo(
            file_bytes, 
            tipo_analise, 
            file_extension # O novo argumento
        )
        # --- FIM DA MUDANÇA ---

        if not dados_extraidos:
            return jsonify({'message': 'Não foi possível extrair dados do contrato.'}), 500

        return jsonify({
            'message': 'Dados extraídos com sucesso! Revise para salvar.',
            'extractedData': dados_extraidos,
        }), 200

    except Exception as e:
        print(f"[ERRO] Falha na rota /upload: {e}")
        return jsonify({'message': f'Erro ao processar o contrato: {str(e)}'}), 500

# ==============================================================================
# ROTA PARA GERAR NOVOS CONTRATOS (Inalterada)
# ==============================================================================
@contratos_bp.route('/gerar-contrato', methods=['POST'])
def gerar_contrato():
    """
    (Esta função permanece 100% igual à que já tínhamos)
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    formato_desejado = data.get('formato_desejado', 'docx')

    contratante_info = {
        'Nome': data.get('contratanteNome'), 'RG': data.get('contratanteRg'),
        'CPF': data.get('contratanteCpf'), 'Endereco': data.get('contratanteEndereco'),
        'Telefone': data.get('contratanteTelefone'), 'Email': data.get('contratanteEmail'),
    }
    dados_para_contrato = {
        'Contratante': contratante_info,
        'Data do Evento': data.get('dataEvento'),
        'Local do Evento': data.get('localEvento'),
        'Produtos Contratados': data.get('produtosContratados', []),
        'Valor Total do Pedido': data.get('valorTotalPedidoContrato'),
        'Data de Pagamento': data.get('dataPagamentoContrato'),
        'Forma de Pagamento': data.get('formaPagamento'),
        'Como nos conheceu': data.get('comoConheceu'),
        'Responsavel': data.get('responsavelContrato'),
    }

    try:
        response, error_message = _processar_e_enviar_contrato(dados_para_contrato, formato_desejado)
        if error_message:
            return jsonify({'message': error_message}), 500
        return response
        
    except Exception as e:
        print(f"[ERRO] Não foi possível gerar ou enviar o contrato: {e}")
        return jsonify({'message': f"Erro ao gerar o contrato: {str(e)}"}), 500

# --- FUNÇÃO AUXILIAR (Inalterada) ---
def _processar_e_enviar_contrato(dados: Dict[str, Any], formato: str):
    """
    (Esta função permanece 100% igual à que já tínhamos)
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    nome_cliente_safe = re.sub(r'[^\w-]', '_', dados['Contratante'].get('Nome', 'Contrato')).lower()
    nome_base = f"contrato_{nome_cliente_safe}_{timestamp}"

    if formato == 'pdf':
        print("[INFO] Gerando contrato em formato PDF via WeasyPrint...")
        pdf_stream = gerar_contrato_pdf_direto(dados)
        if not pdf_stream:
            return None, "Erro interno ao gerar o documento PDF."
        
        return send_file(
            pdf_stream,
            as_attachment=True,
            download_name=f"{nome_base}.pdf",
            mimetype='application/pdf'
        ), None
    
    else: # O padrão é 'docx'
        print("[INFO] Gerando contrato em formato DOCX...")
        doc_stream = gerar_contrato_docx(dados)
        if not doc_stream:
            return None, "Erro interno ao gerar o documento DOCX."

        return send_file(
            doc_stream,
            as_attachment=True,
            download_name=f"{nome_base}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ), None