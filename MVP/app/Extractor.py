# Arquivo: app/Extractor.py (VERSÃO DE DEBUG V6 - PARA DIAGNÓSTICO)

import re
import fitz  # PyMuPDF
import spacy
import json
from io import BytesIO
from docx import Document
import datetime
import openpyxl
from typing import Dict, Any, Optional
from flask import render_template
from weasyprint import HTML

# (Carregamento do spaCy)
try:
    nlp = spacy.load("pt_core_news_md")
    print("[INFO] Modelo de NLP (pt_core_news_md) carregado com sucesso.")
except OSError:
    print("[AVISO] Modelo 'pt_core_news_md' não foi encontrado. Execute: python -m spacy download pt_core_news_md")
    nlp = None

# ==============================================================================
# SEÇÃO 1: FUNÇÃO PRINCIPAL DE ORQUESTRAÇÃO
# ==============================================================================

def extrair_dados_do_contrato_por_tipo(pdf_bytes: bytes, tipo_analise: str = 'padrao') -> Optional[Dict[str, Any]]:
    texto = _extrair_texto_de_pdf_bytes(pdf_bytes)
    if not texto:
        return None

    if tipo_analise == 'sistema':
        print("\n" + "*"*30 + " INÍCIO DO TEXTO EXTRAÍDO DO PDF (MODO SISTEMA) " + "*"*30)
        print(texto.encode('utf-8', errors='ignore').decode('utf-8'))
        print("*"*30 + " FIM DO TEXTO EXTRAÍDO DO PDF (MODO SISTEMA) " + "*"*30 + "\n")
    
    if tipo_analise == 'sistema':
        return _extrair_com_regex(texto)
    else:
        return _extrair_com_nlp(texto)

def _extrair_texto_de_pdf_bytes(pdf_bytes: bytes) -> Optional[str]:
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            return "".join(pagina.get_text("text") for pagina in doc)
    except Exception as e:
        print(f"[ERRO] Falha ao extrair texto do PDF a partir dos bytes: {e}")
        return None

# ==============================================================================
# SEÇÃO 2: NOSSAS DUAS ESTRATÉGIAS DE EXTRAÇÃO
# ==============================================================================

# --- ESTRATÉGIA 1: REGEX (MODO DEBUG V6) ---

def _extrair_com_regex(texto: str) -> Dict[str, Any]:
    """
    [VERSÃO DE DEBUG V6] - Corrigindo a Regex principal para aceitar
    hífen (-) ou travessão (–).
    """
    print("\n" + "="*20 + " INÍCIO DO DEBUG DA REGEX (V6) " + "="*20)
    
    flags = re.DOTALL | re.IGNORECASE
    dados = {
        "Contratante": {"Nome": "N/A", "CPF": "N/A", "Telefone": "N/A", "Email": "N/A", "RG": "N/A", "Endereco": "N/A"},
        "Data_do_Evento": "N/A", "Local_do_Evento": "N/A", "produtosContratadosJson": "[]",
        "Data_de_Pagamento": "N/A", "Valor_Total_do_Pedido": "N/A", "FormaDePagamento": "N/A",
        "Responsavel": "N/A", "Como nos conheceu": "N/A"
    }

    # (Contratante - pulado para focar no bug)
    bloco_contratante_sistema = re.search(r"CONTRATANTE:\s*Sr\(a\)([\s\S]*?)CONTRATADO:", texto, flags)
    if bloco_contratante_sistema:
        texto_contratante = bloco_contratante_sistema.group(1)
        dados["Contratante"]["Nome"] = (m.group(1).strip() if (m := re.search(r"^\s*(.*?),\s*brasileiro", texto_contratante, flags)) else "N/A")
        # (Restante do Contratante omitido para focar no bug)

    # --- DEBUG DA EXTRAÇÃO DE PRODUTOS ---
    
    # --- A MUDANÇA (V6) ESTÁ AQUI ---
    # A Regex agora usa [–-] (um travessão OU um hífen) para ser mais robusta
    # e removemos o IGNORECASE do 'TOTAL' para que ele pegue o footer (maiúsculo)
    # e não o header (minúsculo).
    bloco_produtos_sistema = re.search(r'CLÁUSULA 1 [–-] PRODUTOS CONTRATADOS([\s\S]*?)TOTAL\s', texto, re.DOTALL) 
    
    if not bloco_produtos_sistema:
        print("[DEBUG-FALHA V6] A Regex principal falhou. Não encontrou o bloco entre 'CLÁUSULA 1' e 'TOTAL' (maiúsculo).")
        print("="*20 + " FIM DO DEBUG (V6) " + "="*20 + "\n")
        return dados
    
    print("[DEBUG-SUCESSO V6] Bloco 'Produtos' (Modo Sistema) encontrado.")
    texto_produtos = bloco_produtos_sistema.group(1)
    
    texto_produtos_sem_header = texto_produtos
    try:
        # Usamos rindex para achar o *último* 'Total' (o do header)
        data_start_index = texto_produtos.rindex('Total')
        texto_produtos_sem_header = texto_produtos[data_start_index + len('Total'):]
        print("[DEBUG-INFO V6] Header 'Total' removido com sucesso.")
    except ValueError:
        print("[DEBUG-AVISO V6] Header 'Total' não foi encontrado na tabela de produtos.")

    print(f"[DEBUG-TEXTO-BRUTO V6] O texto que será processado é: {repr(texto_produtos_sem_header)}")

    linhas = texto_produtos_sem_header.split('\n')
    linhas_limpas = [linha.strip() for linha in linhas if linha.strip()]
    
    print(f"[DEBUG-LINHAS V6] O texto foi dividido nestas linhas: {linhas_limpas}")

    produtos_lista = []
    
    # Regex para checar se uma linha é um PREÇO (deve conter vírgula ou ponto decimal)
    is_price_regex = r'[\d.,]+[.,]\d+' 
    
    produto_atual = {}
    print("\n--- INICIANDO LOOP DA MÁQUINA DE ESTADOS (V6) ---")

    for i, linha in enumerate(linhas_limpas):
        print(f"\n[DEBUG-LOOP V6] Processando Linha {i}: {repr(linha)}")
        print(f"[DEBUG-LOOP V6] Produto atual: {produto_atual}")

        # ESTADO 1: Procurando uma Quantidade (produto_atual está vazio)
        if not produto_atual:
            if linha.isdigit():
                produto_atual['Quantidade'] = linha
                print(f"[DEBUG-LOOP V6] ESTADO 1: 'Quantidade' encontrada -> {linha}")
            else:
                print(f"[DEBUG-LOOP V6] ESTADO 1: Ignorando lixo (não é Qtd): {repr(linha)}")
            continue 

        # ESTADO 2: Procurando um Nome de Produto
        if 'Produto' not in produto_atual:
            produto_atual['Produto'] = linha
            print(f"[DEBUG-LOOP V6] ESTADO 2: 'Produto' encontrado -> {linha}")
            continue

        # ESTADO 3: Procurando um Valor Unitário
        if 'Valor Unitário' not in produto_atual:
            eh_preco = re.match(is_price_regex, linha)
            if eh_preco:
                produto_atual['Valor Unitário'] = linha
                print(f"[DEBUG-LOOP V6] ESTADO 3: 'Valor Unitário' encontrado -> {linha}")
            else:
                produto_atual['Valor Unitário'] = 'N/A'
                produto_atual['Valor Total Item'] = 'N/A'
                print(f"[DEBUG-LOOP V6] ESTADO 3: (NÃO É PREÇO) Item de 2 colunas salvo: {produto_atual}")
                produtos_lista.append(produto_atual)
                
                if linha.isdigit():
                    produto_atual = {'Quantidade': linha}
                    print(f"[DEBUG-LOOP V6] ESTADO 3: Começando NOVO item com Qtd: {linha}")
                else:
                    produto_atual = {} 
                    print(f"[DEBUG-LOOP V6] ESTADO 3: Linha não é Qtd. Resetando.")
            continue

        # ESTADO 4: Procurando um Valor Total
        if 'Valor Total Item' not in produto_atual:
            produto_atual['Valor Total Item'] = linha
            print(f"[DEBUG-LOOP V6] ESTADO 4: 'Valor Total Item' encontrado -> {linha}")
            print(f"[DEBUG-LOOP V6] ESTADO 4: Item de 4 colunas salvo: {produto_atual}")
            produtos_lista.append(produto_atual)
            produto_atual = {} 
            continue
    
    print("\n--- FIM DO LOOP (V6) ---")

    if produto_atual and 'Produto' in produto_atual:
        produto_atual.setdefault('Valor Unitário', 'N/A')
        produto_atual.setdefault('Valor Total Item', 'N/A')
        print(f"[DEBUG-FINAL V6] Salvando último item (2 col): {produto_atual}")
        produtos_lista.append(produto_atual)

    if produtos_lista:
        print(f"[DEBUG-SUCESSO V6] Produtos encontrados: {len(produtos_lista)}")
        dados["produtosContratadosJson"] = json.dumps(produtos_lista, ensure_ascii=False)
    else:
        print("[DEBUG-FALHA V6] Loop terminou, mas 'produtos_lista' está VAZIA.")
    
    # (Restante da função)
    valor_total_sistema = re.search(r"TOTAL\s*([\d.,]+)", texto, flags)
    if valor_total_sistema:
        dados["Valor_Total_do_Pedido"] = valor_total_sistema.group(1).strip()
    
    bloco_pagamento_sistema = re.search(r"foram\s+pagos\s+no\s+dia\s+([\d/]+)\s+(.*?)\.", texto, flags)
    if bloco_pagamento_sistema:
        dados["Data_de_Pagamento"] = bloco_pagamento_sistema.group(1).strip()
        dados["FormaDePagamento"] = bloco_pagamento_sistema.group(2).strip()

    bloco_evento_sistema = re.search(r"O evento acontecerá no dia:\s*([\d/]+)\s*.\s*Local do evento:\s*(.*?)\n", texto, flags)
    if bloco_evento_sistema:
        dados["Data_do_Evento"] = bloco_evento_sistema.group(1).strip()
        dados["Local_do_Evento"] = bloco_evento_sistema.group(2).strip()

    dados["Como nos conheceu"] = (m.group(1).strip() if (m := re.search(r"Como nos conheceu:\s*(.*?)\n", texto, flags)) else "N/A")
    dados["Responsavel"] = (m.group(1).strip() if (m := re.search(r"RESPONSÁVEL PELO CONTRATO:\s*(.*?)\s*\n", texto, flags)) else "N/A")
    
    print("="*20 + " FIM DO DEBUG (V6) " + "="*20 + "\n")
    return dados


# --- ESTRATÉGIA 2: HÍBRIDA (Botão Azul - "Modo Padrão") ---

def _extrair_com_nlp(texto: str) -> Dict[str, Any]:
    """
    FUNÇÃO HÍBRIDA: Tenta extrair com as Regex Perfeitas (acima) primeiro.
    Se falharem, usa NLP (IA) e Regex Genéricas como fallback (Plano B).
    """
    if not nlp: 
        print("[ERRO] Modelo de linguagem spaCy não foi carregado. Não é possível usar o modo Padrão.")
        raise Exception("Modelo de linguagem spaCy não foi carregado.")

    print("[INFO] Executando extração HÍBRIDA (Regex-first, NLP-fallback)...")
    
    # --- 1. TENTATIVA COM REGEX PERFEITAS ---
    dados = _extrair_com_regex(texto) # Chama a função de DEBUG acima

    # --- 2. FALLBACK PARA NLP (IA) E REGEX GENÉRICAS ---
    print("[INFO-Híbrido] Executando fallback de NLP/IA para campos não encontrados...")
    
    doc = nlp(texto)

    if dados["Contratante"]["Nome"] == "N/A":
        print("[INFO-Híbrido] Fallback: Usando NLP para 'Nome'.")
        pessoas = [ent.text for ent in doc.ents if ent.label_ == "PER"]
        if pessoas: dados["Contratante"]["Nome"] = pessoas[0]

    if dados["Local_do_Evento"] == "N/A":
        print("[INFO-Híbrido] Fallback: Usando NLP para 'Local'.")
        locais = [ent.text for ent in doc.ents if ent.label_ == "LOC"]
        if locais: dados["Local_do_Evento"] = locais[0]
    
    # (Restante das Regex de fallback)
    if dados["Contratante"]["CPF"] == "N/A":
        dados["Contratante"]["CPF"] = (m.group(1) if (m := re.search(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", texto)) else "N/A")
    if dados["Contratante"]["Telefone"] == "N/A":
        dados["Contratante"]["Telefone"] = (m.group(1) if (m := re.search(r"(\(?\d{2}\)?\s*\d{4,5}-?\d{4})", texto)) else "N/A")
    if dados["Contratante"]["Email"] == "N/A":
        dados["Contratante"]["Email"] = (m.group(1) if (m := re.search(r"([\w.\-]+@[\w.\-]+)", texto)) else "N/A")
    if dados["Valor_Total_do_Pedido"] == "N/A":
        dados["Valor_Total_do_Pedido"] = (m.group(1) if (m := re.search(r"(?:valor\s*total|preço\s*final)[\s\S]*?(R\$\s*[\d.,]+)", texto, re.IGNORECASE)) else "N/A")
    if dados["Data_do_Evento"] == "N/A":
        dados["Data_do_Evento"] = (m.group(1) if (m := re.search(r"data\s*do\s*evento[:\s]*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)) else "N/A")

    return dados


# ==============================================================================
# SEÇÃO 3: GERAÇÃO DE DOCUMENTOS (Inalterado)
# ==============================================================================

def gerar_contrato_docx(dados: Dict[str, Any]) -> Optional[BytesIO]:
    try:
        document = Document()
        # (Resto da função de gerar DOCX - inalterada)
        document.add_heading('Divinos Doces Finos', 0)
        document.add_paragraph('CONTRATO', style='Normal')
        document.add_paragraph()
        contratante = dados.get('Contratante', {})
        contratante_texto = document.add_paragraph()
        contratante_texto.add_run('CONTRATANTE: ').bold = True
        contratante_texto.add_run(f"Sr(a) {contratante.get('Nome', 'N/A')}, brasileiro(a), portador(a) da cédula de RG: {contratante.get('RG', 'N/A')} e CPF: {contratante.get('CPF', 'N/A')}, residente e domiciliado(a) na {contratante.get('Endereco', 'N/A')} - Tel. {contratante.get('Telefone', 'N/A')}.")
        contratado_texto = document.add_paragraph()
        contratado_texto.add_run('CONTRATADO: ').bold = True
        contratado_texto.add_run(f"Divinos Doces Finos, inscrito sob o CNPJ: 18.826.801/0001-76, com sede na Rua Curupacê, 392 Mooca, São Paulo SP representado pela sócia proprietária Damaris Talita Macedo, portador do RG: 30.315.655-7.")
        document.add_paragraph()
        document.add_heading('CLÁUSULA 1 - PRODUTOS CONTRATADOS', level=1)
        produtos = []
        produtos_json_str = dados.get('produtosContratadosJson', '[]')
        try:
            produtos = json.loads(produtos_json_str)
        except json.JSONDecodeError:
            print("[AVISO] JSON de produtos inválido ao gerar DOCX.")
            produtos = dados.get('Produtos Contratados', [])
        if produtos:
            tabela = document.add_table(rows=1, cols=4)
            tabela.style = 'Table Grid'
            hdr_cells = tabela.rows[0].cells
            hdr_cells[0].text, hdr_cells[1].text, hdr_cells[2].text, hdr_cells[3].text = 'Quantidade', 'Produto', 'Valor Unitário', 'Valor Total'
            for item in produtos:
                row_cells = tabela.add_row().cells
                row_cells[0].text, row_cells[1].text, row_cells[2].text, row_cells[3].text = str(item.get('Quantidade', '')), str(item.get('Produto', '')), str(item.get('Valor Unitário', '')), str(item.get('Valor Total Item', ''))
            document.add_paragraph(f"TOTAL: {dados.get('Valor Total do Pedido', dados.get('Valor_Total_do_Pedido', 'N/A'))}")
        else:
            document.add_paragraph("Nenhum produto adicionado.")
        document.add_heading('CLÁUSULA 2 - VALOR E FORMA DE PAGAMENTO', level=1)
        document.add_paragraph(f"O valor total de {dados.get('Valor Total do Pedido', dados.get('Valor_Total_do_Pedido', 'N/A'))} referente aos produtos acima citados, foram pagos no dia {dados.get('Data de Pagamento', dados.get('Data_de_Pagamento', 'N/A'))} {dados.get('Forma de Pagamento', dados.get('FormaDePagamento', 'N/A'))}.")
        document.add_heading('CLÁUSULA 3 - EMBALAGEM DOS DOCES - FORMINHAS', level=1)
        document.add_paragraph('Os doces finos são entregues em forminhas no formato caixeta, na cor branca, todos decorados e prontos para o consumo. Os brigadeiros serão entregues em forminhas na cor branca nº 5.')
        document.add_paragraph('Caso o CONTRATANTE opte por embalagens decorativas, o mesmo deverá enviar ao CONTRATADO com no máximo 15 dias de antecedência ao evento, que entregará os doces finos dentro das embalagens decoradas, prontos para o consumo. Após esse prazo não recebemos.')
        document.add_paragraph('Por haver um manejo especial nas forminhas no modelo de flor e um custo maior de compra de caixas para armazenamento dos doces, é cobrado uma taxa adicional de R$0,10 por unidade, como consta abaixo:')
        document.add_paragraph('ATÉ 100 DOCES + R$10,00 / ATÉ 200 DOCES + R$20,00 ATÉ 300 DOCES + R$30,00 / ATÉ 400 DOCES + R$40,00 ACIMA DE 500 DOCES + R$50,00 e assim sucessivamente')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 4 - EMBALAGENS DOS BEM-CASADOS', level=1)
        document.add_paragraph('Os bem-casados são entregues em papel crepom crepe plus, com celofane e fita de cetim de 7mm, nas cores enviadas na tabela completa. Os papéis perolados da linha especial serão cobrados R$ 0,40 a mais por unidade e os papéis dourado, prata, tiffany e marsala serão cobrados R$ 0,20 a mais por unidade, por se tratar de um papel especial e com maior custo. Tudo está discriminado na tabela de cores.')
        document.add_paragraph('Caso o CONTRATANTE opte por incluir, medalhinhas, tercinhos, renda, juta, tag ou outro item decorativo, deverá consultar antecipadamente a disponibilidade e todos os itens são colados com cola quente. A entrega dos itens deverá ocorrer com no máximo 15 dias antes do evento. Após esse prazo não recebemos. Por haver um manejo especial dos itens, será cobrado uma taxa adicional de R$0,10, como consta abaixo: ATÉ 100 BEM-CASADOS + R$10,00 / ATÉ 200 BEM-CASADOS + R$20,00 ATÉ 300 BEM-CASADOS + R$30,00 / ATÉ 400 BEM-CASADOS + R$40,00 ACIMA de 500 BEM-CASADOS + R$50,00 e assim sucessivamente')
        document.add_paragraph('Caso opte pela aplicação de dois ou mais itens, será cobrado o valor de cada item.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 5 - ALTERAÇÕES', level=1)
        document.add_paragraph('Não recebemos forminhas, modificações, alterações em contrato em hipótese alguma na semana do evento.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 6 - ADIÇÃO DE NOVOS ITENS', level=1)
        document.add_paragraph('Caso haja a necessidade do CONTRATANTE adicionar novos itens ao pedido fechado, o valor dos produtos será de acordo com o valor vigente no momento da adição, mesmo que o contrato tenha sido fechado com valores promocionais.')
        document.add_paragraph('A adição de produtos ocorre de acordo com a disponibilidade de agenda. Não havendo disponibilidade para novos produtos ou pedidos, não será possível a complementação.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 7 - RETIRada OU SERVIÇO DE ENTREGA', level=1)
        document.add_paragraph(f"A entrega ou retirada dos itens acima, deverá ser definida pela CONTRATANTE até 15 dias antes do evento. Em caso de entrega será cobrada taxa de deslocamento de R$ 6,00 por km ou a taxa mínima de R$50,00 (sujeito a disponibilidade na data e horário desejados). Não fazemos entregas aos domingos e feriados. A retirada dos produtos ocorre de segunda-feira à sábado, das 9h às 16h30, mediante agendamento com o setor responsável, não havendo expediente aos domingos e feriados.")
        document.add_paragraph()
        document.add_heading('CLÁUSULA 8 - ARMAZENAMENTO', level=1)
        document.add_paragraph('Todos os doces e/ou bem-casados deverão, obrigatoriamente, ser armazenados em geladeira até o momento da montagem da mesa para o evento. Validade 3 a 5 dias em geladeira.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 9 - LOCAÇÃO (SE HOUVER)', level=1)
        document.add_paragraph('Caso haja locação de bolo cenográfico, o CONTRATANTE deverá deixar uma caução no valor de R$300,00 ou o valor em dinheiro, como forma de garantia. O bolo cenográfico sendo locado e deverá retornar nas mesmas condições, em até 4 dias após a data da retirada. Na devolução do bolo cenográfico, será devolvido o valor total. Em caso de avarias será cobrado R$ 100,00 por andar (dependendo do modelo) para refazer cada andar danificado. O CONTRATANTE deverá tomar todos os cuidados necessários como: não expor ao calor excessivo, água ou qualquer outro líquido, não deverá apertar, amassar, não deixar convidados colocarem as mãos e deverá ser transportado com cuidado, pegando somente pela base de madeira.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 10 - REMARCAÇÃO', level=1)
        document.add_paragraph('Em caso de REMARCAÇÃO de data do evento superior a 6 meses, será cobrado um reequilíbrio econômico e financeiro de 10% sobre o valor do contrato, a cada 6 meses de diferença da data marcada inicialmente.')
        document.add_paragraph()
        document.add_heading('CLÁUSULA 11 - DATA E LOCAL DO EVENTO', level=1)
        document.add_paragraph(f"O evento acontecerá no dia: {dados.get('Data do Evento', dados.get('Data_do_Evento', 'N/A'))} - Local do evento: {dados.get('Local do Evento', dados.get('Local_do_Evento', 'N/A'))}")
        document.add_paragraph(f"Como nos conheceu: {dados.get('Como nos conheceu', 'N/A')}")
        document.add_paragraph()
        document.add_heading('CLÁUSULA 12 - CANCELAMENTO', level=1)
        document.add_paragraph('A CONTRATANTE pagará multa de 30% do valor do contrato em caso de cancelamento. O CONTRATADO pagará multa de 100% do valor do contrato em caso de cancelamento.')
        document.add_paragraph()
        document.add_paragraph(f"RESPONSÁVEL PELO CONTRATO: {dados.get('Responsavel', 'N/A')}")
        document.add_paragraph(f"São Paulo, {dados.get('Data de Pagamento', dados.get('Data_de_Pagamento', 'N/A'))}")
        document.add_paragraph()
        document.add_paragraph('CONTRATANTE', style='Normal').bold = True
        document.add_paragraph('______________________________', style='Normal')
        document.add_paragraph('CONTRATADO', style='Normal').bold = True
        document.add_paragraph('______________________________', style='Normal')
        
        doc_stream = BytesIO()
        document.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream
    except Exception as e:
        print(f"[ERRO] Falha ao gerar contrato DOCX: {e}")
        return None

def gerar_contrato_pdf_direto(dados: Dict[str, Any]) -> Optional[BytesIO]:
    try:
        html_string = render_template("contrato_template.html", dados=dados)
        pdf_bytes = HTML(string=html_string).write_pdf()
        pdf_stream = BytesIO(pdf_bytes)
        pdf_stream.seek(0)
        return pdf_stream
    except Exception as e:
        print(f"[ERRO] Falha ao gerar contrato PDF com WeasyPrint: {e}")
        return None

def gerar_relatorio_entrega(dados: Dict[str, Any]) -> Optional[BytesIO]:
    try:
        document = Document()
        # (Resto da função de gerar Relatório - inalterada)
        document.add_heading('RELATÓRIO DE ENTREGA', 0)
        contratante = dados.get('Contratante', {})
        data_evento = dados.get('Data do Evento', dados.get('Data_do_Evento', 'Não informada'))
        local_evento = dados.get('Local do Evento', dados.get('Local_do_Evento', 'Não informado'))
        document.add_paragraph(f"Nome do Cliente: {contratante.get('Nome', 'Não encontrado')}")
        document.add_paragraph(f"Data do Evento: {data_evento}")
        document.add_paragraph(f"Local do Evento: {local_evento}")
        document.add_paragraph(f"Data de Emissão: {datetime.datetime.now().strftime('%d/%m/%Y')}")
        document.add_paragraph("\nProdutos Contratados:")
        produtos = []
        produtos_json_str = dados.get('produtosContratadosJson', '[]')
        try:
            produtos = json.loads(produtos_json_str)
        except json.JSONDecodeError:
            print("[AVISO] JSON de produtos inválido ao gerar Relatório.")
            produtos = dados.get('Produtos Contratados', [])
        if produtos:
            tabela = document.add_table(rows=1, cols=4)
            tabela.style = 'Table Grid'
            hdr_cells = tabela.rows[0].cells
            hdr_cells[0].text, hdr_cells[1].text, hdr_cells[2].text, hdr_cells[3].text = 'Quantidade', 'Produto', 'Valor Unitário', 'Valor Total'
            for item in produtos:
                row_cells = tabela.add_row().cells
                row_cells[0].text, row_cells[1].text, row_cells[2].text, row_cells[3].text = str(item.get('Quantidade', '')), str(item.get('Produto', '')), str(item.get('Valor Unitário', '')), str(item.get('Valor Total Item', ''))
        else:
            document.add_paragraph("Nenhum produto encontrado.")
        document.add_paragraph(f"\nValor Total do Pedido: R$ {dados.get('Valor Total do Pedido', dados.get('Valor_Total_do_Pedido', 'N/A'))}")
        document.add_paragraph("\n\n\nAssinaturas:\n")
        document.add_paragraph("______________________________\nResponsável pela Entrega")
        document.add_paragraph("\n\n")
        document.add_paragraph("______________________________\nResponsável pela Retirada")
        doc_stream = BytesIO()
        document.save(doc_stream)
        doc_stream.seek(0)
        return doc_stream
    except Exception as e:
        print(f"[ERRO] Falha ao salvar relatório de entrega: {e}")
        return None

def exportar_para_excel(dados: Dict[str, Any]) -> Optional[BytesIO]:
    try:
        workbook = openpyxl.Workbook()
        # (Resto da função de gerar Excel - inalterada)
        sheet = workbook.active
        sheet.title = "Dados do Contrato"
        sheet['A1'] = "Campo"
        sheet['B1'] = "Informação Extraída"
        linha_atual = 2
        for chave, valor in dados.items():
            if chave == 'Produtos Contratados' or chave == 'produtosContratadosJson':
                continue
            if isinstance(valor, dict):
                for sub_chave, sub_valor in valor.items():
                    sheet[f'A{linha_atual}'] = f"{chave} - {sub_chave}"
                    sheet[f'B{linha_atual}'] = sub_valor
                    linha_atual += 1
            else:
                sheet[f'A{linha_atual}'] = chave
                sheet[f'B{linha_atual}'] = valor
                linha_atual += 1
        linha_atual += 2
        produtos_contratados_str = dados.get('produtosContratadosJson')
        if produtos_contratados_str:
            produtos_contratados = json.loads(produtos_contratados_str)
            if produtos_contratados and isinstance(produtos_contratados, list) and len(produtos_contratados) > 0:
                headers_produtos = list(produtos_contratados[0].keys())
                for col_idx, header in enumerate(headers_produtos, 1):
                    sheet.cell(row=linha_atual, column=col_idx, value=header)
                linha_atual += 1
                for produto in produtos_contratados:
                    for col_idx, header in enumerate(headers_produtos, 1):
                        sheet.cell(row=linha_atual, column=col_idx, value=produto.get(header, 'N/A'))
                    linha_atual += 1
        excel_stream = BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)
        return excel_stream
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar a planilha: {e}")
        return None

# ==============================================================================
# SEÇÃO 4: BLOCO DE TESTE (Inalterado)
# ==============================================================================
if __name__ == "__main__":
    caminho_do_pdf = "modelo_contrato.pdf" 
    print(f"Tentando extrair texto de: {caminho_do_pdf}")
    
    try:
        with open(caminho_do_pdf, 'rb') as f:
            pdf_bytes_content = f.read()
        
        print("\n--- TESTANDO MODO SISTEMA (REGEX) ---")
        dados_do_contrato = extrair_dados_do_contrato_por_tipo(pdf_bytes_content, tipo_analise='sistema')

    except FileNotFoundError:
        print(f"\n[ERRO] Arquivo de teste '{caminho_do_pdf}' não encontrado. Crie um para testar.")
        dados_do_contrato = None
    except Exception as e:
        print(f"\n[ERRO] Falha ao ler PDF de teste: {e}")
        dados_do_contrato = None

    if dados_do_contrato:
        print("\nDados extraídos com sucesso. Imprimindo e gerando arquivos...")
        
        print("\n--- DADOS EXTRAÍDOS DO CONTRATO ---")
        for chave, valor in dados_do_contrato.items():
            print(f"\n>> {chave}:")
            if chave == 'produtosContratadosJson':
                try:
                    produtos = json.loads(valor)
                    for item in produtos:
                        print(f"    - {item}")
                except json.JSONDecodeError:
                    print(f"    {valor}")
            elif isinstance(valor, dict):
                for sub_chave, sub_valor in valor.items():
                    print(f"     {sub_chave}: {sub_valor}")
            else:
                print(f"    {valor}")
        print("\n----------------------------------------------------")

        nome_excel = f"dados_contrato_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_stream = exportar_para_excel(dados_do_contrato)
        if excel_stream:
            with open(nome_excel, 'wb') as f:
                f.write(excel_stream.getvalue())
            print(f"\n[SUCESSO] Dados exportados para o arquivo '{nome_excel}'")
        else:
            print(f"\n[ERRO] Não foi possível gerar a planilha Excel.")

        nome_docx = f"relatorio_entrega_{datetime.datetime.now().strftime('%Y%m%d_%H%S')}.docx"
        docx_stream = gerar_relatorio_entrega(dados_do_contrato)
        if docx_stream:
            with open(nome_docx, 'wb') as f:
                f.write(docx_stream.getvalue())
            print(f"[OK] Relatório de entrega salvo em: {nome_docx}")
        else:
            print(f"[ERRO] Falha ao salvar relatório de entrega.")

    else:
        print("\nNão foi possível processar o PDF.")