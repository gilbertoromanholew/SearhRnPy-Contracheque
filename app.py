import requests
import pdfkit
import re

def converter_numero(valor):
    if isinstance(valor, (int, float)):
        return float(valor)
    elif isinstance(valor, str):
        numero_str = ''.join(c for c in valor if c.isdigit() or c in '.,')
        if not numero_str:
            raise ValueError("Nenhum número encontrado na string")
        
        pos_ultimo_ponto = numero_str.rfind('.')
        pos_ultima_virgula = numero_str.rfind(',')
        
        if pos_ultimo_ponto == -1 and pos_ultima_virgula == -1:
            return float(numero_str)
        elif pos_ultimo_ponto > pos_ultima_virgula:
            numero_str = numero_str.replace(',', '')
        elif pos_ultima_virgula > pos_ultimo_ponto:
            numero_str = numero_str.replace('.', '').replace(',', '.')
        else:
            raise ValueError("Formato de número inválido")
        
        return float(numero_str)
    else:
        raise ValueError("Tipo de input não suportado")

# Supondo que texto_pdf seja o texto extraído após o encoding
texto_pdf = "Algum texto LÍQUIDO A RECEBER R$ 554,57 mais texto"
# Ou, por exemplo: texto_pdf = "Texto LÍQUIDO A RECEBER R$ 12.345.678,90 outro texto"

padrao = r"LÍQUIDO A RECEBER\s+R\$\s*([\d.,]+)"
match = re.search(padrao, texto_pdf)
if match:
    valor_str = match.group(1)  # Ex: "554,57" ou "12.345.678,90"
    liquido = converter_numero(valor_str)  # Converte para float
    print(f"Valor líquido extraído: {liquido}")
else:
    raise ValueError("Valor líquido não encontrado no texto")
