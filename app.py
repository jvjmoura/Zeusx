import tempfile

import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from document_processor import DocumentProcessor
from loaders import carrega_pdf
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
CONFIG_MODELOS = {'Groq': 
                        {'modelos': ['llama-3.1-70b-versatile', 'gemma2-9b-it', 'mixtral-8x7b-32768'],
                         'chat': ChatGroq},
                'OpenAI': 
                        {'modelos': ['gpt-4o-mini', 'gpt-4o', 'o1-preview', 'o1-mini'],
                         'chat': ChatOpenAI}}

# Inicializa memória global
MEMORIA = ConversationBufferMemory()

def carrega_arquivo(arquivo):
    """Carrega arquivo PDF."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
        temp.write(arquivo.read())
        nome_temp = temp.name
    return carrega_pdf(nome_temp)

def carrega_modelo(provedor, modelo, api_key, arquivo):
    """Carrega o modelo de linguagem e processa o documento."""
    if not arquivo:
        st.error('Por favor, faça upload de um arquivo')
        return
    
    # Container para progresso
    progress_container = st.sidebar.empty()
    with progress_container.container():
        st.markdown("#### Processando documento...")
        progress = st.progress(0)
        
        # Carrega arquivo
        progress.progress(25, "Carregando PDF...")
        documento = carrega_arquivo(arquivo)
        
        # Processa documento
        progress.progress(50, "Processando texto...")
        chat = CONFIG_MODELOS[provedor]['chat'](model=modelo, api_key=api_key)
        processor = DocumentProcessor(chat)
        chunks = processor.process_document(documento)
        
        # Configura modelo
        progress.progress(75, "Configurando modelo...")
        st.session_state['chunks'] = chunks
        st.session_state['processor'] = processor
        st.session_state['memoria'] = MEMORIA
        
        # Define template
        template = ChatPromptTemplate.from_messages([
            ('system', '''Você é um assistente amigável chamado Oráculo.
            
            {context}
            
            Utilize as informações fornecidas para basear as suas respostas.
            Se a informação não estiver nas seções fornecidas, indique que precisa 
            consultar outras partes do documento.
            
            HISTÓRICO DA CONVERSA:
            {chat_history}'''),
            ('user', '{input}')
        ])
        
        chain = template | chat
        st.session_state['chain'] = chain
        
        # Finaliza
        progress.progress(100, "Pronto!")
        st.success("Documento processado com sucesso!")
    
    # Remove container de progresso após 2 segundos
    import time
    time.sleep(2)
    progress_container.empty()

def pagina_chat():
    st.header('🤖Bem-vindo ao Oráculo', divider=True)

    chain = st.session_state.get('chain')
    if chain is None:
        st.error('Carrege o Oráculo')
        st.stop()

    # Recupera memória da sessão
    memoria = st.session_state.get('memoria', MEMORIA)
    
    # Mostra histórico
    for mensagem in memoria.buffer_as_messages:
        chat = st.chat_message(mensagem.type)
        chat.markdown(mensagem.content)

    input_usuario = st.chat_input('Fale com o oráculo')
    if input_usuario:
        chat = st.chat_message('human')
        chat.markdown(input_usuario)

        chat = st.chat_message('ai')
        processor = st.session_state.get('processor')
        chunks = st.session_state.get('chunks')
        
        # Pega contexto relevante baseado na pergunta
        context = processor.get_context(input_usuario, chunks)
        
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario,
            'context': context,
            'chat_history': memoria.buffer_as_messages
        }))
        
        # Atualiza memória
        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria

def sidebar():
    with st.sidebar:
        # Informações do autor
        st.markdown("### ⚡ Zeus - Assistente Jurídico")
        st.markdown("""
        *Desenvolvido por:*  
        **João Valério**  
        Juiz do Tribunal de Justiça do Pará  
        joao.moura@tjpa.jus.br
        """)
        
        st.divider()
        
        # Upload e configurações
        arquivo = st.file_uploader('Faça upload do arquivo PDF', type=['.pdf'])
        provedor = st.selectbox('Selecione o provedor dos modelo', CONFIG_MODELOS.keys())
        modelo = st.selectbox('Selecione o modelo', CONFIG_MODELOS[provedor]['modelos'])
        api_key = st.text_input(
            f'Adicione a api key para o provedor {provedor}',
            value=st.session_state.get(f'api_key_{provedor}'))
        st.session_state[f'api_key_{provedor}'] = api_key
    
        if st.button('Inicializar Zeus', use_container_width=True):
            carrega_modelo(provedor, modelo, api_key, arquivo)
            
        if st.button('Apagar Histórico', use_container_width=True):
            st.session_state['memoria'] = MEMORIA

def main():
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == '__main__':
    main()
