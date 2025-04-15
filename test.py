import os
import fitz
import tabula
import pandas as pd
import re
from datetime import datetime
import pdfkit
import requests

def download_pdf(matricula=None, senha=None, vinculo=1, ano=None, mes=None):
    tipofolha = ""

    url = f"https://saogoncalo.rn.gov.br/wp-content/uploads/2025/04/JOM-065-04ABR2025_EDICAO-EXTRA_PROCESSO_SELETIVO_EDUCACAO.pdf"

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

        pasta = Path("folha") / ("default" if tipofolha == "" else tipofolha)
        pasta.mkdir(parents=True, exist_ok=True)

        pdf_path = pasta / f"{ano} - {vinculo}.pdf"
        pdfkit.from_url(url, str(pdf_path), options=options)

        return True

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return False

    except Exception as e:
        print(f"Erro ao converter para PDF: {e}")
        return False
    
download_pdf()