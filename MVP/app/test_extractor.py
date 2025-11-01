# Arquivo: test_extractor.py

import pytest
# Importamos a função específica que queremos testar do seu arquivo Extractor.py
# Certifique-se de que o pytest possa encontrar seu módulo 'app'.
from app.Extractor import _extrair_com_regex

# ==============================================================================
# SEÇÃO 1: TEXTOS DE EXEMPLO PARA OS TESTES
# ==============================================================================

# CASO 1: Um contrato "perfeito", sem quebras de linha inesperadas.
CONTRATO_NORMAL = """
Divinos Doces Finos
CONTRATO
CONTRATANTE: Sr(a) Cliente Teste Normal, brasileiro(a), portador(a) da cédula de RG:
11.222.333-4 e CPF: 123.456.789-00, residente e domiciliado(a) na Rua dos Testes, 123 - Tel.
(11) 98765-4321. E-mail: cliente.normal@teste.com.
CONTRATADO: Divinos Doces Finos...
CLÁUSULA 1 - PRODUTOS CONTRATADOS
Quantidade  Produto          Valor Unitário  Valor Total
10          Brigadeiro       R$ 3.00         R$ 30.00
TOTAL: R$ 30.00
CLÁUSULA 2 - VALOR E FORMA DE PAGAMENTO
O valor total de R$ 30.00 referente aos produtos acima citados, foram pagos no dia 25/12/2025 PIX.
CLÁUSULA 11 - DATA E LOCAL DO EVENTO
O evento acontecerá no dia: 31/12/2025 - Local do evento: Salão de Festas Principal
Como nos conheceu: Google
RESPONSÁVEL PELO CONTRATO: Admin
"""

# CASO 2: Contrato com o problema da quebra de linha entre "foram" e "pagos".
CONTRATO_QUEBRA_FORAM_PAGOS = """
Divinos Doces Finos
CONTRATO
CONTRATANTE: Sr(a) Cliente Quebra Pagamento, brasileiro(a), portador(a) da cédula de RG:
11.222.333-4 e CPF: 123.456.789-00, residente e domiciliado(a) na Rua dos Testes, 123 - Tel.
(11) 98765-4321. E-mail: cliente.quebra1@teste.com.
CONTRATADO: Divinos Doces Finos...
CLÁUSULA 1 - PRODUTOS CONTRATADOS
TOTAL: R$ 30.00
CLÁUSULA 2 - VALOR E FORMA DE PAGAMENTO
O valor total de R$ 30.00 referente aos produtos acima citados, foram
pagos no dia 15/10/2026 Boleto Bancário.
CLÁUSULA 11 - DATA E LOCAL DO EVENTO
...
"""

# CASO 3: Contrato com o problema da quebra de linha no meio de "E-mail".
CONTRATO_QUEBRA_EMAIL = """
Divinos Doces Finos
CONTRATO
CONTRATANTE: Sr(a) Cliente Quebra Email, brasileiro(a), portador(a) da cédula de RG:
11.222.333-4 e CPF: 123.456.789-00, residente e domiciliado(a) na Rua dos Testes, 123 - Tel.
(11) 98765-4321. E-
mail: cliente.quebra2@teste.com.
CONTRATADO: Divinos Doces Finos...
CLÁUSULA 1 - PRODUTOS CONTRATADOS
TOTAL: R$ 30.00
CLÁUSULA 2 - VALOR E FORMA DE PAGAMENTO
O valor total de R$ 30.00 referente aos produtos acima citados, foram pagos no dia 25/12/2025 PIX.
CLÁUSULA 11 - DATA E LOCAL DO EVENTO
...
"""

# CASO 4: Contrato com texto inválido ou vazio para testar a robustez.
CONTRATO_INVALIDO = "Este texto não é um contrato e não contém nenhuma informação relevante."


# ==============================================================================
# SEÇÃO 2: FUNÇÕES DE TESTE (PYTEST)
# ==============================================================================

def test_extracao_contrato_normal():
    """
    Testa o "caminho feliz": um contrato perfeitamente formatado.
    Verifica se todos os campos principais são extraídos corretamente.
    """
    dados = _extrair_com_regex(CONTRATO_NORMAL)
    
    assert dados["Contratante"]["Nome"] == "Cliente Teste Normal"
    assert dados["Contratante"]["Email"] == "cliente.normal@teste.com"
    assert dados["Data_de_Pagamento"] == "25/12/2025"
    assert dados["FormaDePagamento"] == "PIX"
    assert dados["Data_do_Evento"] == "31/12/2025"
    assert dados["Valor_Total_do_Pedido"] == "R$ 30.00"

def test_extracao_com_quebra_linha_em_pagamento():
    """
    Testa especificamente o bug da quebra de linha entre "foram" e "pagos".
    Garante que a nossa correção funciona como esperado.
    """
    dados = _extrair_com_regex(CONTRATO_QUEBRA_FORAM_PAGOS)

    assert dados["Contratante"]["Nome"] == "Cliente Quebra Pagamento"
    assert dados["Data_de_Pagamento"] == "15/10/2026"
    assert dados["FormaDePagamento"] == "Boleto Bancário"

def test_extracao_com_quebra_linha_em_email():
    """
    Testa especificamente o bug da quebra de linha na palavra "E-mail".
    Garante que a nossa correção para este caso também funciona.
    """
    dados = _extrair_com_regex(CONTRATO_QUEBRA_EMAIL)

    assert dados["Contratante"]["Nome"] == "Cliente Quebra Email"
    assert dados["Contratante"]["Email"] == "cliente.quebra2@teste.com"

def test_extracao_contrato_invalido():
    """
    Testa como a função se comporta com um texto que não é um contrato.
    Ela não deve quebrar e deve retornar os valores padrão "N/A".
    """
    dados = _extrair_com_regex(CONTRATO_INVALIDO)

    assert dados["Contratante"]["Nome"] == "N/A"
    assert dados["Data_de_Pagamento"] == "N/A"
    assert dados["Valor_Total_do_Pedido"] == "N/A"