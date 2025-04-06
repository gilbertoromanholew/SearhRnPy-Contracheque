import os
import fitz
import tabula
import pandas as pd
import re
from datetime import datetime
import pdfkit
import requests

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
    
def download_pdf(matricula=None, senha=None, vinculo=1, ano=None, mes=None):
    tipofolha = ""

    url = f"http://servicos.searh.rn.gov.br/searh/copag/contrachk.asp?matricula={matricula}&vinculo={vinculo}&cpf={senha}&ano={ano}&mes={mes}&tipofolha={tipofolha}"

    # SISTEMA DE PESQUISA
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        encoding = response.apparent_encoding or "utf-8"
        print(f"\nCodificação detectada: {encoding}\n")

        # Configurações para maximizar a qualidade (compatíveis com wkhtmltopdf 0.12.6)
        options = {
            "encoding": encoding,              # Mantém a codificação detectada
            "dpi": "300",                     # Alta resolução (300 DPI)
            "image-dpi": "300",               # Alta resolução para imagens
            "image-quality": "100",           # Qualidade máxima para imagens
            "quiet": "",                      # Evita mensagens de log
            "load-error-handling": "ignore",  # Ignora erros de carregamento
            "page-size": "A4",                # Tamanho da página A4
            "margin-top": "0mm",              # Remove margens
            "margin-bottom": "0mm",
            "margin-left": "0mm",
            "margin-right": "0mm",
        }

        from pathlib import Path
        
        mes_formatado = f"{mes:02d}"

        pasta = Path("folha") / ("default" if tipofolha == "" else tipofolha)
        pasta.mkdir(parents=True, exist_ok=True)

        pdf_path = pasta / f"{mes_formatado}{ano} - {vinculo}.pdf"
        pdfkit.from_url(url, str(pdf_path), options=options)

        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return False

    except Exception as e:
        print(f"Erro ao converter para PDF: {e}")
        return False
    
def extrair_texto(caminho_pdf):
    """Extrai o texto de um PDF usando PyMuPDF (fitz)."""
    with fitz.open(caminho_pdf) as doc:
        texto = ""
        for pagina in doc:
            blocos = pagina.get_text("blocks")
            texto += "".join(bloco[4] for bloco in blocos)
    return texto

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

def extrair_tabela(caminho_pdf):
    """Lê a tabela principal do PDF e remove linhas de totais."""
    try:
        tabelas = tabula.read_pdf(caminho_pdf, pages=1, multiple_tables=True)
        for tabela in tabelas:
            if 'CÓDIGO' in tabela.columns and 'DISCRIMINAÇÃO' in tabela.columns:
                return tabela[~tabela['DISCRIMINAÇÃO'].str.contains('TOTAL|LÍQUIDO', na=False)]
        return pd.DataFrame()  # Retorna DataFrame vazio se a tabela não for encontrada
    except Exception as e:
        print(f"Erro ao extrair tabela do arquivo {caminho_pdf}: {e}")
        return pd.DataFrame()

def processar_pdfs(pasta_pdfs):
    """Processa todos os PDFs em uma pasta e retorna um DataFrame consolidado."""
    colunas = [
        'NOME', 'MATRÍCULA', 'VINC.', 'PENSÃO', 'CARGO', 'REFERÊNCIA', 'PIS/PASEP',
        'FUNÇÃO', 'BCO/AGÊNCIA', 'CONTA', 'LOTAÇÃO', 'DEP IR', 'DEP SF', 'CPF',
        'CÓDIGO', 'DISCRIMINAÇÃO', 'VANTAGENS', 'DESCONTOS', 'COMPET'
    ]
    dados_finais = []

    # Arquivo de log para registrar PDFs desconsiderados
    log_file = "log_falhas.txt"
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Log de PDFs desconsiderados - {datetime.now()}\n")
        log.write("=" * 50 + "\n")

        # Lista todos os PDFs na pasta
        arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
        total_arquivos = len(arquivos)
        
        for idx, arquivo in enumerate(arquivos, 1):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            print(f"Processando arquivo {idx}/{total_arquivos}: {arquivo}")

            # Extrai texto
            texto = extrair_texto(caminho_pdf)

            # Verifica se o registro foi encontrado
            if "Registro n" in texto:  # Ajustado para capturar "Registro não encontrado"
                mensagem = f"Registro não encontrado no arquivo: {caminho_pdf}\n"
                print(mensagem.strip())
                log.write(mensagem)
                continue

            # Extrai dados pessoais e tabela
            dados_pessoais = extrair_dados_pessoais(texto)
            tabela = extrair_tabela(caminho_pdf)

            # Verifica se a tabela não está vazia
            if not tabela.empty:
                for _, linha in tabela.iterrows():
                    dados_finais.append({**dados_pessoais, **linha.to_dict()})
            else:
                mensagem = f"Tabela vazia ou não encontrada no arquivo: {caminho_pdf}\n"
                print(mensagem.strip())
                log.write(mensagem)

    return pd.DataFrame(dados_finais, columns=colunas)

if __name__ == "__main__":

    ano_inicio = int(input("Digite o ano de início: "))
    ano_fim = int(input("Digite o ano de fim: "))

    anos = list(range(ano_inicio, ano_fim + 1))
    meses = [1,2,3,4,5,6,7,8,9,10,11,12]
    vinculos = [1,2]

    for ano in anos:
        for mes in meses:
            for vinculo in vinculos:
                print(f"Baixando contracheque para {ano}-{mes} com vínculo {vinculo}")
                donwload = download_pdf(matricula="00706000", senha="cyovqytx", vinculo=vinculo, ano=ano, mes=mes)

    # "http://servicos.searh.rn.gov.br/searh/copag/contrachk.asp?matricula=00706000&vinculo=1&cpf=cyovqytx&ano=2003&mes=1&tipofolha="

if __name__ == "__main__":
    pasta_pdfs = "folha/default"  # Ajuste para o seu diretório
    df = processar_pdfs(pasta_pdfs)
    df.to_excel('contracheques_detalhados.xlsx', index=False)
    print("Planilha 'contracheques_detalhados.xlsx' gerada com sucesso!")

