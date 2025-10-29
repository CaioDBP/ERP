# Arquivo: app/contratos/routes.py (Versão Refatorada com SQLAlchemy)

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from app import db                  # Importamos a instância do banco de dados
from app.models import Pedido         # Importamos nosso modelo Pedido
from app.Extractor import extrair_texto_de_pdf, extrair_dados_do_contrato, gerar_contrato_docx

contratos_bp = Blueprint('contratos', __name__, url_prefix='/api/contracts')

# @contratos_bp.route('/upload', methods=['POST'])
# def upload_contract():
#     user_id = request.headers.get('X-User-Id')
#     if not user_id:
#         return jsonify({'message': 'Usuário não autenticado.'}), 401

#     if 'file' not in request.files:
#         return jsonify({'message': 'Nenhum arquivo enviado.'}), 400

#     file = request.files['file']
#     if file.filename == '' or not (file.filename.endswith('.pdf')):
#         return jsonify({'message': 'Nenhum arquivo PDF selecionado.'}), 400

#     upload_folder = current_app.config.get('UPLOAD_FOLDER')
#     if not upload_folder:
#         return jsonify({'message': 'Pasta de upload não configurada.'}), 500

#     filepath = os.path.join(upload_folder, file.filename)
#     file.save(filepath)

#     try:
#         texto_extraido = extrair_texto_de_pdf(filepath)
#         if not texto_extraido:
#             return jsonify({'message': 'Não foi possível extrair texto do contrato.'}), 500

#         dados_extraidos_raw = extrair_dados_do_contrato(texto_extraido)
        
#         # --- Mapeamento dos dados extraídos para o formato do pedido ---
#         # (Esta parte da lógica original continua a mesma)
#         produtos_contratados = dados_extraidos_raw.get('Produtos Contratados', [])
#         total_quantidade_produtos = sum(int(p.get('Quantidade', 0)) for p in produtos_contratados)
#         sabores_list = [p.get('Produto') for p in produtos_contratados if p.get('Produto')]

#         # Criamos uma instância do nosso modelo Pedido com os dados extraídos
#         new_pedido_from_contract = Pedido(
#             clienteNome=dados_extraidos_raw.get('Contratante', {}).get('Nome', 'Cliente Desconhecido'),
#             clienteRG=dados_extraidos_raw.get('Contratante', {}).get('RG', ''),
#             clienteCPF=dados_extraidos_raw.get('Contratante', {}).get('CPF', ''),
#             nomeContratado=dados_extraidos_raw.get('Contratado', {}).get('Nome Empresa', ''),
#             cnpjContratado=dados_extraidos_raw.get('Contratado', {}).get('CNPJ', ''),
#             valorTotalPedidoContrato=dados_extraidos_raw.get('Valor Total do Pedido', ''),
#             dataPagamentoContrato=dados_extraidos_raw.get('Data de Pagamento', ''),
#             dataEvento=dados_extraidos_raw.get('Data do Evento', '').replace('/', '-'),
#             localEvento=dados_extraidos_raw.get('Local do Evento', ''),
#             produtosContratadosJson=json.dumps(produtos_contratados),
#             tipoPedido='Contrato',
#             quantidade=total_quantidade_produtos,
#             sabores=', '.join(sabores_list),
#             observacoes=f"Extraído de contrato: {file.filename}.",
            
#             # Campos obrigatórios que podem não estar no contrato, com valores padrão
#             dataRetirada=dados_extraidos_raw.get('Data do Evento', '').replace('/', '-'), # Usando data do evento como padrão
#             horarioRetirada='12:00', # Usando um horário padrão
            
#             # Ligando ao usuário
#             user_id=user_id
#         )

#         # Adicionamos à sessão e salvamos no banco de dados
#         db.session.add(new_pedido_from_contract)
#         db.session.commit()

#         return jsonify({
#             'message': 'Contrato processado e pedido salvo com sucesso!',
#             'pedido': new_pedido_from_contract.to_dict() # Retornamos o novo pedido criado
#         }), 201

#     except Exception as e:
#         print(f"Erro ao processar o arquivo de contrato: {e}")
#         return jsonify({'message': f'Erro ao processar o contrato: {str(e)}'}), 500
#     finally:
#         # Garante que o arquivo temporário seja sempre removido
#         if os.path.exists(filepath):
#             os.remove(filepath)
# Em app/contratos/routes.py

@contratos_bp.route('/upload', methods=['POST'])
def upload_contract():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado.'}), 400
    file = request.files['file']
    if file.filename == '' or not (file.filename.endswith('.pdf')):
        return jsonify({'message': 'Nenhum arquivo PDF selecionado.'}), 400
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)

    try:
        texto_extraido = extrair_texto_de_pdf(filepath)
        if not texto_extraido:
            return jsonify({'message': 'Não foi possível extrair texto do contrato.'}), 500

        dados_extraidos_raw = extrair_dados_do_contrato(texto_extraido)

        # --- Mapeamento dos dados para um DICIONÁRIO SIMPLES ---
        produtos_contratados = dados_extraidos_raw.get('Produtos Contratados', [])
        total_quantidade = sum(int(p.get('Quantidade', 0)) for p in produtos_contratados)
        sabores = ', '.join([p.get('Produto') for p in produtos_contratados if p.get('Produto')])

        extracted_data_for_pedido = {
            'clienteNome': dados_extraidos_raw.get('Contratante', {}).get('Nome', ''),
            'clienteRG': dados_extraidos_raw.get('Contratante', {}).get('RG', ''),
            'clienteCPF': dados_extraidos_raw.get('Contratante', {}).get('CPF', ''),
            'dataEvento': dados_extraidos_raw.get('Data do Evento', '').replace('/', '-'),
            'localEvento': dados_extraidos_raw.get('Local do Evento', ''),
            'produtosContratadosJson': json.dumps(produtos_contratados),
            'quantidade': total_quantidade,
            'sabores': sabores,
            'valorTotalPedidoContrato': dados_extraidos_raw.get('Valor Total do Pedido', ''),
            'dataPagamentoContrato': dados_extraidos_raw.get('Data de Pagamento', ''),
            'nomeContratado': dados_extraidos_raw.get('Contratado', {}).get('Nome Empresa', ''),
            'cnpjContratado': dados_extraidos_raw.get('Contratado', {}).get('CNPJ', ''),
            'tipoPedido': 'Contrato',
            'observacoes': f"Extraído de contrato: {file.filename}."
        }
        
        # --- MUDANÇA  ---
        # AGORA, APENAS RETORNAMOS o dicionário com os dados extraídos.
        return jsonify({
            'message': 'Dados extraídos com sucesso! Revise para salvar.',
            'extractedData': extracted_data_for_pedido,
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao processar o contrato: {str(e)}'}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@contratos_bp.route('/gerar-contrato', methods=['POST'])
def gerar_contrato():
    """
    Recebe os dados de um formulário, mapeia para o formato correto e gera um contrato em DOCX.
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    
   
    # Aqui nós "traduzimos" os dados do formulário para o formato que a função geradora espera.
    
    contratante_info = {
        'Nome': data.get('contratanteNome', 'N/A'),
        'RG': data.get('contratanteRg', 'N/A'),
        'CPF': data.get('contratanteCpf', 'N/A'),
        'Endereco': data.get('contratanteEndereco', 'N/A'),
        'Telefone': data.get('contratanteTelefone', 'N/A'),
        'Email': data.get('contratanteEmail', 'N/A'),
    }

    produtos_contratados_list = data.get('produtosContratados', [])

    # Este é o dicionário final no formato correto
    dados_para_contrato = {
        'Contratante': contratante_info,
        'Data do Evento': data.get('dataEvento', 'N/A'),
        'Local do Evento': data.get('localEvento', 'Não Informado'),
        'Produtos Contratados': produtos_contratados_list,
        'Valor Total do Pedido': data.get('valorTotalPedidoContrato', 'N/A'),
        'Data de Pagamento': data.get('dataPagamentoContrato', 'N/A'),
        'Forma de Pagamento': data.get('formaPagamento', 'Não Informado'),
        'Como nos conheceu': data.get('comoConheceu', 'N/A'),
        'Responsavel': data.get('responsavelContrato', 'N/A'), # Verifique se este campo vem do seu form
    }
 

    try:
        # AGORA PASSAMOS O DICIONÁRIO MAPEADO, E NÃO O 'data' BRUTO
        doc_stream = gerar_contrato_docx(dados_para_contrato)

        if doc_stream is None:
            return jsonify({'message': 'Erro interno ao gerar o contrato.'}), 500

        contrato_filename = f"contrato_gerado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        return send_file(
            doc_stream,
            as_attachment=True,
            download_name=contrato_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        print(f"\n[ERRO] Não foi possível gerar ou enviar o contrato: {e}")
        return jsonify({'message': f"Erro ao gerar o contrato: {str(e)}"}), 500