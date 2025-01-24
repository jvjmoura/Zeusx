import os
from time import sleep
import streamlit as st
from langchain_community.document_loaders import (WebBaseLoader,
                                                  YoutubeLoader, 
                                                  CSVLoader, 
                                                  PyPDFLoader, 
                                                  TextLoader)
from fake_useragent import UserAgent
from ocr_processor import OCRProcessor

ocr = OCRProcessor()

def carrega_site(url):
    documento = ''
    for i in range(5):
        try:
            os.environ['USER_AGENT'] = UserAgent().random
            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
            break
        except:
            print(f'Erro ao carregar o site {i+1}')
            sleep(3)
    if documento == '':
        st.error('Não foi possível carregar o site')
        st.stop()
    return documento

def carrega_youtube(video_id):
    loader = YoutubeLoader(video_id, add_video_info=False, language=['pt'])
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_csv(caminho):
    loader = CSVLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_pdf(caminho):
    try:
        print("\n=== Iniciando carregamento do PDF ===")
        print("Caminho:", caminho)
        
        # Tenta primeiro extrair texto normalmente
        loader = PyPDFLoader(caminho)
        print("Loader PDF criado")
        paginas = loader.load()
        print(f"Carregou {len(paginas)} páginas")
        texto = ' '.join([pagina.page_content for pagina in paginas])
        print(f"Texto extraído normalmente: {len(texto)} caracteres")
        
        # Verifica se o texto parece ser válido
        palavras = len(texto.split())
        caracteres_por_palavra = len(texto) / max(palavras, 1)
        print(f"Palavras encontradas: {palavras}")
        print(f"Média de caracteres por palavra: {caracteres_por_palavra:.2f}")
        
        # Se não houver texto, texto muito curto, ou texto parecer inválido
        if (len(texto.strip()) < 100 or  # muito curto
            palavras < 10 or  # poucas palavras
            caracteres_por_palavra > 20):  # palavras muito longas (provável ruído)
            print("Texto parece inválido ou muito curto, tentando OCR")
            texto = ocr.process_file(caminho)
            print(f"Texto extraído via OCR: {len(texto)} caracteres")
        
        if not texto.strip():
            print("Nenhum texto extraído!")
            return "Não foi possível extrair texto deste documento."
            
        return texto
    except Exception as e:
        print(f"Erro detalhado ao carregar PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "Erro ao processar o documento."

def carrega_txt(caminho):
    loader = TextLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento
