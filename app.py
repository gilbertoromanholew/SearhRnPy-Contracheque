import requests
import pdfkit
import re
import os
import pandas as pd
import tabula
import fitz

def extrair_dados_pessoais(texto):
    """Extrai informações pessoais do texto usando expressões regulares."""
    padroes = {
        'NOME': r"NOME\s+([A-Z\s]+)\s+MATRÍCULA",
        'MATRÍCULA': r"MATRÍCULA\s+([\d\-]+)\s+VINC\.",
        'VINC.': r"VINC\.\s+(\d+)\s+PENSÃO",
        'PENSÃO': r"PENSÃO\s+([\w\-]+)\s+CARGO",
        'CARGO': r"CARGO\s+([\w\s\-]+)\s+REFERÊNCIA",
        'REFERÊNCIA': r"REFERÊNCIA\s+([\w\d]+)\s+PIS/PASEP",
        'PIS/PASEP': r"PIS/PASEP\s+([\d]+)\s+FUNÇÃO",
        'FUNÇÃO': r"FUNÇÃO\s+([\w\s\-]+)\s+BCO/AGÊNCIA",
        'BCO/AGÊNCIA': r"BCO/AGÊNCIA\s+([\d/]+)\s+CONTA",
        'CONTA': r"CONTA\s+([\d]+)\s+LOTAÇÃO",
        'LOTAÇÃO': r"LOTAÇÃO\s+([\d\s\w\-]+)\s+DEP IR",
        'DEP IR': r"DEP IR\s+([\w\-]+)\s+DEP SF",
        'DEP SF': r"DEP SF\s+([\w\-]+)\s+CPF",
        'CPF': r"CPF\s+([\d\-\.]+)\s+CÓDIGO"
    }
    return {chave: (re.search(padrao, texto, re.IGNORECASE).group(1).strip() if re.search(padrao, texto, re.IGNORECASE) else "")
            for chave, padrao in padroes.items()}

def processar_pdfs(pasta_pdfs):
    colunas = [
        'NOME', 'MATRÍCULA', 'VINC.', 'PENSÃO', 'CARGO', 'REFERÊNCIA', 'PIS/PASEP',
        'FUNÇÃO', 'BCO/AGÊNCIA', 'CONTA', 'LOTAÇÃO', 'DEP IR', 'DEP SF', 'CPF',
        'CÓDIGO', 'DISCRIMINAÇÃO', 'VANTAGENS', 'DESCONTOS', 'COMPET'
    ]
    dados_finais = []

    for arquivo in os.listdir(pasta_pdfs):
        if arquivo.endswith('.pdf'):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            
            with fitz.open(caminho_pdf) as doc:
                texto = ""
                for pagina in doc:
                    blocos = pagina.get_text("blocks")
                    for bloco in blocos:
                        texto += bloco[4]  # O texto está no índice 4 de cada bloco
                # leitor = PyPDF2.PdfReader(pdf)
                # texto = "".join(pagina.extract_text() for pagina in leitor.pages)    
            
            dados_pessoais = extrair_dados_pessoais(texto)
            print(texto)

            for dado in dados_pessoais:
                print(f"{dado}: {dados_pessoais[dado]}")

            break
            # texto = extrair_texto(caminho_pdf)
            # dados_pessoais = extrair_dados_pessoais(texto)
            # tabela = extrair_tabela(caminho_pdf)

            for _, linha in tabela.iterrows():
                dados_finais.append({**dados_pessoais, **linha.to_dict()})

    return pd.DataFrame(dados_finais, columns=colunas)














if __name__ == "__main__":
    pasta_pdfs = "folha/default"  # Ajuste para o seu diretório
    df = processar_pdfs(pasta_pdfs)
    print("Planilha 'contracheques_detalhados.xlsx' gerada com sucesso!")
