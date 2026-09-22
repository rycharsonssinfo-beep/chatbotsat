import os
import streamlit as st
from google import genai
from google.genai import types
import pypdf
import chromadb
from chromadb.utils import embedding_functions

# Configuração da Página
st.set_page_config(
    page_title="Assistente do Sistema Tributário",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização correta forçando o modo Vertex AI para chaves AQ.
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("A chave GEMINI_API_KEY não foi configurada nos Secrets do Streamlit.")
        st.stop()
    
    # Se a chave for do tipo AQ., definimos as variáveis de ambiente do Google Cloud
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    
    # Inicializa o cliente direcionando para o projeto e região padrão do Vertex AI
    try:
        return genai.Client(
            vertexai=True, 
            project="gen-lang-client-0357902878", # Substitua pelo ID do seu projeto GCP se necessário
            location="us-central1"
        )
    except Exception:
        return genai.Client(api_key=api_key)

client = get_gemini_client()
