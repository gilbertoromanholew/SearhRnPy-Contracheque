import requests
import pdfkit
import re
import os

import PyPDF2

def extrair_texto_pdf(caminho_pdf):
    with open(caminho_pdf, 'rb') as arquivo:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for pagina in leitor.pages:
            texto += pagina.extract_text()
    return texto

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
    
def download_pdf(matricula=None, senha=None, vinculo=1):

    ano = input("Digite o ano: ")
    mes = input("Digite o mês: ")
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

        if not len(mes) == 1:
            mes_formatado = mes 
        else:
            mes_formatado = "0" + mes 

        pasta = Path("folha") / ("default" if tipofolha == "" else tipofolha)
        pasta.mkdir(parents=True, exist_ok=True)

        pdf_path = pasta / f"{mes_formatado}{ano}.pdf"
        pdfkit.from_url(url, str(pdf_path), options=options)

        texto_pdf = extrair_texto_pdf(pdf_path)

        padrao = r"registro.*encontrado\."
        match = re.search(padrao, texto_pdf.lower())

        if match is not None:
            try:
                os.remove(pdf_path)
                print(f"Registro não encontado. Arquivo PDF excluído: {pdf_path}")
                return False
            
            except OSError as e:
                print(f"Erro ao excluir o arquivo PDF: {e}")
                return False
            
        else:
            padrao2 = r"líquido\s*a\s*receber\s*r\$\s*([\d.,]+)"
            match2 = re.search(padrao2, texto_pdf.lower())

            if match2 is not None:
                valor_str = match2.group(1)  # Ex: "554,57" ou "12.345.678,90"
                liquido = converter_numero(valor_str)  # Converte para float
                return mes, ano, liquido
            else:
                raise ValueError("Valor líquido não encontrado no texto")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return False

    except Exception as e:
        print(f"Erro ao converter para PDF: {e}")
        return False

if __name__ == "__main__":
    print(download_pdf(matricula="00706000", senha="cyovqytx"))

    # "http://servicos.searh.rn.gov.br/searh/copag/contrachk.asp?matricula=00706000&vinculo=1&cpf=cyovqytx&ano=2003&mes=1&tipofolha="