# Arquivo: app/Extractor.py (VERSÃO 8.2 - CORREÇÃO HEADER PRODUTOS UNIVERSAL)

import re
import fitz  # PyMuPDF
import spacy
import json
from io import BytesIO
from docx import Document
from docx.text.paragraph import Paragraph  # Import para leitura ordenada
from docx.table import Table               # Import para leitura ordenada
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

def extrair_dados_do_contrato_por_tipo(file_bytes: bytes, tipo_analise: str, file_extension: str) -> Optional[Dict[str, Any]]:
    """
    Função principal que o 'contratos/routes.py' chama.
    Agora lida com .pdf e .docx.
    """
    
    texto = _extrair_texto(file_bytes, file_extension)
    
    if not texto:
        return None

    # O print do texto puro agora acontece SEMPRE
    print("\n" + "*"*30 + f" INÍCIO DO TEXTO EXTRAÍDO ({file_extension}) " + "*"*30)
    print(texto.encode('utf-8', errors='ignore').decode('utf-8'))
    print("*"*30 + f" FIM DO TEXTO EXTRAÍDO ({file_extension}) " + "*"*30 + "\n")
    
    if tipo_analise == 'sistema':
        return _extrair_com_regex(texto)
    else:
        return _extrair_com_nlp(texto) 

def _extrair_texto(file_bytes: bytes, file_extension: str) -> Optional[str]:
    """
    (VERSÃO 7.1 - CORRIGIDA DOCX)
    Decide qual biblioteca usar (PyMuPDF ou python-docx)
    baseado na extensão do arquivo.
    """
    
    # Lógica para PDF (Inalterada)
    if file_extension == '.pdf':
        print("[INFO] Detectado .pdf, usando PyMuPDF (fitz) para extrair texto.")
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                return "".join(pagina.get_text("text") for pagina in doc)
        except Exception as e:
            print(f"[ERRO] Falha ao extrair texto do PDF: {e}")
            return None
    
    # Lógica para DOCX (Totalmente Corrigida)
    elif file_extension == '.docx':
        print("[INFO] Detectado .docx, usando python-docx para extrair texto.")
        try:
            texto_completo = ""
            doc_stream = BytesIO(file_bytes)
            document = Document(doc_stream)
            
            # --- INÍCIO DA CORREÇÃO ---

            # 1. Iterar sobre CABEÇALHOS primeiro
            print("[INFO-DOCX] Lendo cabeçalhos...")
            for section in document.sections:
                if section.header:
                    for p in section.header.paragraphs:
                        texto_completo += p.text + "\n"
                    for table in section.header.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                texto_completo += cell.text + "\n"
            
            # 2. Iterar sobre o CORPO do documento (parágrafos e tabelas)
            # Esta é a forma correta de ler o corpo MANTENDO A ORDEM
            print("[INFO-DOCX] Lendo corpo do documento (parágrafos e tabelas) em ordem...")
            
            for block in document.element.body:
                if block.tag.endswith('p'):
                    p = Paragraph(block, document)
                    texto_completo += p.text + "\n"
                
                elif block.tag.endswith('tbl'):
                    table = Table(block, document)
                    for row in table.rows:
                        for cell in row.cells:
                            texto_completo += cell.text + "\n"
            
            # 3. Iterar sobre RODAPÉS
            print("[INFO-DOCX] Lendo rodapés...")
            for section in document.sections:
                if section.footer:
                    for p in section.footer.paragraphs:
                        texto_completo += p.text + "\n"
                    for table in section.footer.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                texto_completo += cell.text + "\n"
            
            # --- FIM DA CORREÇÃO ---
            
            return texto_completo
        
        except Exception as e:
            print(f"[ERRO] Falha ao extrair texto do DOCX: {e}")
            return None
    
    else:
        print(f"[ERRO] Formato de arquivo não suportado: {file_extension}")
        return None


# ==============================================================================
# SEÇÃO 2: NOSSAS DUAS ESTRATÉGIA DE EXTRAÇÃO
# ==============================================================================

# --- ESTRATÉGIA 1: REGEX PERFEITAS (Botão Verde - "Modo Sistema") ---

def _extrair_com_regex(texto: str) -> Dict[str, Any]:
    """
    (VERSÃO 8.2 - CORREÇÃO HEADER PRODUTOS UNIVERSAL)
    Usa Regex de alta precisão + "Máquina de Estados" para a tabela.
    Agora funciona com PDF (lista e tabela) e DOCX (tabela).
    """
    print("[INFO] Executando extração com REGEX DE PRECISÃO (Modo Sistema)...")
    
    flags = re.DOTALL | re.IGNORECASE
    dados = {
        "Contratante": {"Nome": "N/A", "CPF": "N/A", "Telefone": "N/A", "Email": "N/A", "RG": "N/A", "Endereco": "N/A"},
        "Data_do_Evento": "N/A", "Local_do_Evento": "N/A", "produtosContratadosJson": "[]",
        "Data_de_Pagamento": "N/A", "Valor_Total_do_Pedido": "N/A", "FormaDePagamento": "N/A",
        "Responsavel": "N/A", "Como nos conheceu": "N/A"
    }

    # CONTRATANTE (V8.1)
    bloco_contratante_sistema = re.search(r"CONTRATANTE:\s*Sr\(a\)([\s\S]*?)CONTRATADO:?\s", texto, flags)
    if bloco_contratante_sistema:
        print("[INFO-Regex] Bloco 'Contratante' encontrado.")
        texto_contratante = bloco_contratante_sistema.group(1)
        
        dados["Contratante"]["Nome"] = (m.group(1).strip() if (m := re.search(r"^\s*(.*?)\s*,", texto_contratante, flags)) else "N/A")
        dados["Contratante"]["RG"] = (m.group(1).strip() if (m := re.search(r"RG:\s*([\d.\s—-]+?)\s*e\s*CPF:", texto_contratante, flags)) else "N/A")
        dados["Contratante"]["CPF"] = (m.group(1).strip() if (m := re.search(r"CPF:\s*([\d.\s-]+?),", texto_contratante, flags)) else "N/A")
        dados["Contratante"]["Endereco"] = (m.group(1).strip() if (m := re.search(r"domiciliado\(a\) na\s*(.*?)\s*[–-]\s*Tel\.", texto_contratante, flags)) else "N/A")
        dados["Contratante"]["Telefone"] = (m.group(1).strip() if (m := re.search(r"Tel\.\s*([\d\(\)\s.ou/-]+)\.", texto_contratante, flags)) else "N/A") 
        dados["Contratante"]["Email"] = (m.group(1).strip() if (m := re.search(r"E-\s*mail:\s*([\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,})", texto_contratante, flags)) else "N/A")
    else:
        print("[AVISO-Regex] Bloco 'Contratante' não encontrado.")

    
    # VALOR TOTAL (V8.1)
    print("[INFO-Regex] Procurando Valor Total...")
    valor_total_match = re.search(r"O valor total de (?:R\$\s*)?([\d.,]+)", texto, flags)
    if not valor_total_match:
        print("[INFO-Regex] Valor Total (Padrão 1) falhou. Tentando Padrão 2 (Tabela: Total 500,00)...")
        valor_total_match = re.search(r"\nTOTAL\s+(?:R\$\s*)?([\d.,]+)", texto, flags) 
    if not valor_total_match:
        print("[INFO-Regex] Valor Total (Padrão 2) falhou. Tentando Padrão 3 (TOTAL: R$ 76.00)...")
        valor_total_match = re.search(r"TOTAL:\s+R\$\s+([\d.,]+)", texto, flags)
    
    if valor_total_match:
        dados["Valor_Total_do_Pedido"] = valor_total_match.group(1).strip()
        print(f"[INFO-Regex] Valor Total encontrado: {dados['Valor_Total_do_Pedido']}")
    else:
        print("[AVISO-Regex] Valor Total não encontrado.")


    # PRODUTOS (V8.2 - CORREÇÃO DA LÓGICA DO HEADER)
    print("[INFO-Regex] Tentando Padrão 1 (CLÁUSULA 1 -> CLÁUSULA 2)...")
    bloco_produtos_sistema = re.search(r'CLÁUSULA 1 [–-] PRODUTOS CONTRATADOS([\s\S]*?)CLÁUSULA 2', texto, flags)
    
    produtos_lista = []
    texto_produtos_sem_header = ""

    if bloco_produtos_sistema:
        print("[INFO-Regex] Bloco 'Produtos' encontrado.")
        texto_produtos = bloco_produtos_sistema.group(1) 
        
        # --- INÍCIO DA CORREÇÃO V8.2 ---
        try:
            # Procurar pela string "Valor Total", case-insensitive, para achar o header
            header_find_str = 'Valor Total'
            # .lower() em ambos para garantir que a busca seja case-insensitive
            data_start_index = texto_produtos.lower().index(header_find_str.lower())
            
            # Pega o texto DEPOIS do header
            texto_produtos_sem_header = texto_produtos[data_start_index + len(header_find_str):]
            print("[INFO-Regex] Header 'Valor Total' (Tabela) removido com sucesso.")
        except ValueError:
            texto_produtos_sem_header = texto_produtos.strip() # Remove espaço em branco
            print("[INFO-Regex] Header 'Valor Total' (Tabela) não encontrado. Usando texto puro (provavelmente formato Lista).")
        # --- FIM DA CORREÇÃO V8.2 ---

        # --- TENTATIVA 1: MÁQUINA DE ESTADOS (V8.1 - Para Tabelas PDF/DOCX) ---
        print("[INFO-Regex] Tentativa 1: Processando como TABELA (Máquina de Estados V8.1)...")
        linhas = texto_produtos_sem_header.split('\n')
        linhas_limpas = [linha.strip() for linha in linhas if linha.strip()]
        
        # V8.1: Regex de Preço corrigida. Aceita "R$ 3" e "R$ 18.00" e "62,25"
        is_just_price_regex = r'^(?:R\$\s*)?[\d.,]+(?:[.,]\d{2})?$' 
        
        produto_atual = {}
        ignore_keywords = ['quanti', 'dade', 'produto', 'valor', 'unitário', 'total', 'desconto']

        for linha in linhas_limpas:
            
            if linha.lower() in ignore_keywords:
                print(f"[INFO-Regex-Tabela] Ignorando linha de header/lixo: '{linha}'")
                continue
            
            if linha.startswith("TOTAL:"):
                print(f"[INFO-Regex-Tabela] Ignorando linha de Total: '{linha}'")
                continue

            if linha.isdigit():
                # É uma Quantidade (ex: '34', '2000', '5', '6', '130')
                if 'Quantidade' in produto_atual:
                    produto_atual.setdefault('Valor Unitário', 'N/A')
                    produto_atual.setdefault('Valor Total Item', 'N/A')
                    produtos_lista.append(produto_atual)
                
                produto_atual = {'Quantidade': linha}
                print(f"[INFO-Regex-Tabela] Estado 1 (Qtd): {linha}")
            
            elif re.match(is_just_price_regex, linha, flags):
                # É um Preço (ex: 'R$ 3', 'R$ 18.00', '62,25', '3,99')
                if 'Quantidade' not in produto_atual:
                    print(f"[INFO-Regex-Tabela] Ignorando preço órfão: '{linha}'")
                    continue 
                
                if 'Valor Unitário' not in produto_atual:
                    produto_atual['Valor Unitário'] = linha
                    print(f"[INFO-Regex-Tabela] Estado 3 (V. Uni): {linha}")
                elif 'Valor Total Item' not in produto_atual:
                    produto_atual['Valor Total Item'] = linha
                    print(f"[INFO-Regex-Tabela] Estado 4 (V. Tot): {linha}")
                    produtos_lista.append(produto_atual)
                    produto_atual = {} 
            
            else:
                # É um Nome de Produto (ex: 'Hóstias...', 'cANECAS', 'brigadeiro', 'Bem Casado...')
                if 'Quantidade' not in produto_atual:
                    print(f"[INFO-Regex-Tabela] Ignorando nome órfão: '{linha}'")
                    continue 
                
                if 'Produto' not in produto_atual:
                    produto_atual['Produto'] = linha
                    print(f"[INFO-Regex-Tabela] Estado 2 (Prod): {linha}")
                else:
                    produto_atual['Produto'] += " " + linha
                    print(f"[INFO-Regex-Tabela] Estado 2 (Prod+): {linha}")

        # Salvar o último produto que pode estar incompleto
        if produto_atual and 'Produto' in produto_atual:
            print(f"[INFO-Regex-Tabela] Salvando último item incompleto: {produto_atual['Produto']}")
            produto_atual.setdefault('Valor Unitário', 'N/A')
            produto_atual.setdefault('Valor Total Item', 'N/A')
            produtos_lista.append(produto_atual)
        
        # --- TENTATIVA 2: PARSER DE LISTA (Para Listas PDF) ---
        if not produtos_lista: 
            print("[AVISO-Regex] Máquina de Estados V8.1 falhou. Tentativa 2: Processando como LISTA (Formato PDF)...")
            texto_lista_corrida = re.sub(r'\s*\n\s*', ' ', texto_produtos_sem_header) 
            
            try:
                matches = re.findall(r"(\d+)\s*x\s(.*?)(?:,|$)", texto_lista_corrida, flags)
                if matches:
                    for match in matches:
                        produto = {
                            'Quantidade': match[0],
                            'Produto': match[1].strip(),
                            'Valor Unitário': 'N/A',
                            'Valor Total Item': 'N/A'
                        }
                        produtos_lista.append(produto)
                else:
                    print("[AVISO-Regex] Parser de Lista não encontrou o padrão 'Nx Produto'.")
            except Exception as e:
                print(f"[ERRO-Regex] Falha no Parser de Lista: {e}")

        # --- Conclusão dos Produtos ---
        if produtos_lista:
            print(f"[INFO-Regex] Produtos encontrados: {len(produtos_lista)}")
            dados["produtosContratadosJson"] = json.dumps(produtos_lista, ensure_ascii=False)
        else:
            print("[AVISO-Regex] Bloco de produtos encontrado, mas nenhum item foi parseado (nem Tabela, nem Lista).")
            if texto_produtos_sem_header:
                 print("[INFO-Regex] Salvando texto bruto dos produtos como fallback final.")
                 dados["produtosContratadosJson"] = json.dumps([{"Quantidade": "N/A", "Produto": texto_produtos_sem_header.strip(), "Valor Unitário": "N/A", "Valor Total Item": "N/A"}], ensure_ascii=False)

    else:
        print("[AVISO-Regex] Nenhum Padrão (PDF ou DOCX) para a tabela de produtos foi encontrado.")

    # --- FIM DA CORREÇÃO ---


    # PAGAMENTO (Corrigido V7.4)
    bloco_pagamento_sistema = re.search(r"(?:foram|serão)\s+pagos\s+no\s+dia\s+([\d/]+)\s+(.*?)\.", texto, flags)
    if not bloco_pagamento_sistema:
        bloco_pagamento_sistema = re.search(r"pagamento no dia\s+([\d/]+)\s+(.*?)\.", texto, flags)
        
    if bloco_pagamento_sistema:
        dados["Data_de_Pagamento"] = bloco_pagamento_sistema.group(1).strip()
        dados["FormaDePagamento"] = bloco_pagamento_sistema.group(2).strip()

    # ==============================================================================
    # --- EVENTO (Corrigido V8.1 - REGEX UNIVERSAL FINAL) ---
    # ==============================================================================
    
    print("[INFO-Regex] Procurando Evento (Padrão Universal V8.1)...")
    
    # Padrão Universal V8.1:
    # 1. Procura a Data
    # 2. Aceita espaços, pontos, travessões ou hífens [–\s.-]*
    # 3. Procura o Local
    # 4. Captura TUDO ([\s\S]*?)
    # 5. Para (lookahead) quando achar um dos 3 delimitadores universais
    
    bloco_evento_sistema = re.search(
        r"O evento acontecerá no dia:\s*([\d/]+)[\s.–-]*Local do evento\s*[:\s]*([\s\S]*?)"
        r"(?=CLÁUSULA 12|RESPONSÁVEL PELO CONTRATO|Como nos conheceu:)",
        texto,
        flags
    )
    
    if bloco_evento_sistema:
        print("[INFO-Regex] Padrão 1 (Evento Universal V8.1) funcionou.")
        dados["Data_do_Evento"] = bloco_evento_sistema.group(1).strip()
        dados["Local_do_Evento"] = bloco_evento_sistema.group(2).strip().strip(" \n.–-") # Limpa lixo
    else:
        print("[AVISO-Regex] Padrão 1 (Evento Universal) falhou. Tentando Padrão 2 (Fallback DO1EVENTO)...")
        # Padrão 2: O fallback original para o erro de digitação
        bloco_evento_sistema = re.search(r"CLÁUSULA 11 [–-] DATA E LOCAL DO1?EVENTO([\s\S]*?)CLÁUSULA 12", texto, flags)
        
        if bloco_evento_sistema:
            print("[INFO-Regex] Padrão 2 (Evento - DO1EVENTO) funcionou.")
            dados["Data_do_Evento"] = (m.group(1).strip() if (m := re.search(r"O evento acontecerá no dia:\s*([\d/]+)", bloco_evento_sistema.group(0), flags)) else "N/A")
            dados["Local_do_Evento"] = (m.group(1).strip() if (m := re.search(r"Local do evento\s*[:\s]*([\s\S]*?)(?:CLÁUSULA 12|RESPONSÁVEL PELO CONTRATO|Como nos conheceu:)", bloco_evento_sistema.group(0), flags)) else "N/A")
        else:
            print("[AVISO-Regex] Nenhum padrão de Evento foi encontrado.")

    # ==============================================================================
    # --- FIM DA SEÇÃO DE EVENTO ---
    # ==============================================================================

    # OUTROS (Funciona)
    dados["Como nos conheceu"] = (m.group(1).strip() if (m := re.search(r"Como nos conheceu:\s*(.*?)\n", texto, flags)) else "N/A")
    dados["Responsavel"] = (m.group(1).strip() if (m := re.search(r"RESPONSÁVEL PELO CONTRATO:\s*(.*?)\s*(\n|$)", texto, flags)) else "N/A")
    
    print("="*20 + " FIM DA EXTRAÇÃO (V8.2) " + "="*20 + "\n")
    return dados


# --- ESTRATÉGIA 2: HÍBRIDA (Botão Azul - "Modo Padrão") ---
# (Esta seção permanece inalterada)

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
    dados = _extrair_com_regex(texto) # Chama a função V8.2 acima

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
        if locais and "Divinos Doces Finos" not in locais[0]: 
            dados["Local_do_Evento"] = locais[0]
    
    if dados["Contratante"]["CPF"] == "N/A":
        dados["Contratante"]["CPF"] = (m.group(1) if (m := re.search(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", texto)) else "N/Y")
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
# (Todas as funções de gerar_contrato_docx, gerar_contrato_pdf_direto,
# gerar_relatorio_entrega, e exportar_para_excel permanecem 100% iguais)

def gerar_contrato_docx(dados: Dict[str, Any]) -> Optional[BytesIO]:
    try:
        document = Document()
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
        document.add_paragraph('Caso haja locação de bolo cenográfico, o CONTRATANTE deverá deixar uma caução no valor de R$300,00 ou o valor em dinheiro, como forma de garantia. O bolo cenográfico sendo locado e deverá retornar nas mesmas condições, em até 4 dias após a data da retirada. Na devolução do bolo cenográfico, será devolvido o valor total. Em caso de avarias será cobrado R$ 100,00 por andar (dependendo do modelo) para refazer cada andar danificado. O CONTRATANTE deverá tomar todos os cuidados necessários como: não expor ao calor excessivo,  água  ou  qualquer  outro  líquido,  não  deverá  apertar,  amassar,  não  deixar convidados colocarem as mãos e deverá ser transportado com cuidado, pegando somente pela base de madeira.')
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
        dados_do_contrato = extrair_dados_do_contrato_por_tipo(pdf_bytes_content, tipo_analise='sistema', file_extension='.pdf') 

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

        nome_excel = f"dados_contrato_{datetime.datetime.now().strftime('%Ym%d_%H%M%S')}.xlsx"
        excel_stream = exportar_para_excel(dados_do_contrato)
        if excel_stream:
            with open(nome_excel, 'wb') as f:
                f.write(excel_stream.getvalue())
            print(f"\n[SUCESSO] Dados exportados para o arquivo '{nome_excel}'")
        else:
            print(f"\n[ERRO] Não foi possível gerar a planilha Excel.")

        nome_docx = f"relatorio_entrega_{datetime.datetime.now().strftime('%Y%H%S')}.docx"
        docx_stream = gerar_relatorio_entrega(dados_do_contrato)
        if docx_stream:
            with open(nome_docx, 'wb') as f:
                f.write(docx_stream.getvalue())
            print(f"[OK] Relatório de entrega salvo em: {nome_docx}")
        else:
            print(f"[ERRO] Falha ao salvar relatório de entrega.")

    else:
        print("\nNão foi possível processar o PDF.")