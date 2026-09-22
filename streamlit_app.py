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

# Inicialização segura do cliente Gemini compatível com o token AQ.
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("A chave GEMINI_API_KEY não foi configurada nos Secrets do Streamlit.")
        st.stop()
    
    # Define a chave no ambiente para captação automática
    os.environ["GEMINI_API_KEY"] = api_key
    
    # Para chaves com o padrão AQ. (Enterprise / Google Cloud Project), 
    # inicializamos o cliente utilizando o modo enterprise com o projeto correspondente
    try:
        # Tenta inicializar no modo padrão corporativo suportado por esse tipo de token
        return genai.Client(enterprise=True, project="gen-lang-client-0357902878", location="us-central1")
    except Exception:
        # Fallback para o cliente padrão caso o ambiente ajuste automaticamente
        return genai.Client(api_key=api_key)

client = get_gemini_client()

# Configuração do ChromaDB local para RAG
@st.cache_resource
def init_vector_store():
    chroma_client = chromadb.Client()
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = chroma_client.get_or_create_collection(
        name="manual_tributario",
        embedding_function=ef
    )
    return collection

collection = init_vector_store()

# System Prompt Rigoroso contra Alucinações
SYSTEM_PROMPT = """
Você é o Assistente Oficial de Suporte do Sistema Tributário Municipal (SAT).
Sua função é auxiliar os usuários exclusivamente na utilização do sistema tributário descrito na base de conhecimento fornecida pelo manual oficial.

REGRAS OBRIGATÓRIAS:
1. Utilize SOMENTE informações presentes no contexto recuperado da base de conhecimento.
2. NUNCA invente informações, menus, caminhos de tela, campos, botões, códigos ou regras.
3. Se a informação não estiver disponível na base recuperada, diga claramente: "Não encontrei essa informação no manual disponível. Para evitar fornecer uma orientação incorreta, não consigo confirmar o procedimento para essa situação."
4. Ao responder sobre procedimentos, utilize estritamente a seguinte estrutura prática:
   - **Como fazer:** [Passo a passo extraído do manual]
   - **Observação:** [Informações adicionais se houver]
5. Ao responder sobre erros, utilize:
   - **Erro:** [Mensagem]
   - **Causa:** [Se documentada]
   - **Solução:** [Procedimento documentado]
   - **Caminho no sistema:** [Se documentado]
6. Sempre informe a fonte com base nos metadados (Manual, Capítulo, Página).
"""

# Interface Lateral (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/administrative-tools.png", width=64)
    st.title("Chatbot SAT")
    st.markdown("**Sistema de Atendimento e Tributação**")
    st.markdown("---")
    
    pagina_selecionada = st.radio("Ir para:", ["💬 Chat de Suporte", "📚 Base de Conhecimento / Manual"])
    
    st.markdown("---")
    st.markdown("**Manual de Orientações 2026**")
    st.caption("Status da Base: Conectado e Indexado")

# -------------------------------------------------------------
# PÁGINA 1: CHAT DE SUPORTE TÉCNICO
# -------------------------------------------------------------
if pagina_selecionada == "💬 Chat de Suporte":
    st.subheader("Assistente Virtual SAT")
    st.caption("Tire dúvidas sobre apuração, cadastros, lançamentos e declarações com base no manual oficial.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Sugestões de perguntas:")
        col1, col2 = st.columns(2)
        sugestoes = [
            "Como cadastrar um contribuinte?",
            "Como emitir um DAM?",
            "Como realizar um parcelamento?",
            "Como consultar débitos?"
        ]
        for i, sug in enumerate(sugestoes):
            if (i % 2 == 0 and col1.button(sug, key=f"sug_{i}")) or (i % 2 != 0 and col2.button(sug, key=f"sug_{i}")):
                st.session_state.messages.append({"role": "user", "content": sug})
                st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "source" in message and message["source"]:
                st.info(f"📌 **Fonte:** {message['source']}")

    if prompt := st.chat_input("Digite sua dúvida ou cole uma mensagem de erro relacionada ao SAT..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando o manual oficial..."):
                try:
                    # 1. Recuperação Semântica (RAG)
                    results = collection.query(query_texts=[prompt], n_results=2)
                    
                    contexto_recuperado = ""
                    fonte_info = "Manual Oficial do Sistema Tributário"
                    
                    if results and results['documents'] and len(results['documents'][0]) > 0:
                        docs = results['documents'][0]
                        metas = results['metadatas'][0]
                        contexto_recuperado = "\n\n".join(docs)
                        if metas and "source" in metas[0]:
                            fonte_info = f"{metas[0].get('source', 'Manual')} (Página {metas[0].get('page', 'N/A')})"
                    
                    # 2. Montagem do Contexto Restrito
                    prompt_completo = f"""
                    Contexto recuperado do manual oficial:
                    {contexto_recuperado}
                    
                    Pergunta do usuário: {prompt}
                    """

                    # 3. Chamada ao Modelo Gemini via client moderno
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_completo,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.1
                        )
                    )
                    
                    resposta_final = response.text
                    
                except Exception as e:
                    resposta_final = f"Desculpe, ocorreu um erro técnico ao processar a sua consulta: {str(e)}"
                    fonte_info = None

                st.markdown(resposta_final)
                if fonte_info:
                    st.info(f"📌 **Fonte:** {fonte_info}")

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": resposta_final,
                    "source": fonte_info
                })

# -------------------------------------------------------------
# PÁGINA 2: BASE DE CONHECIMENTO / UPLOAD DE MANUAL (PDF)
# -------------------------------------------------------------
elif pagina_selecionada == "📚 Base de Conhecimento / Manual":
    st.subheader("Gerenciamento da Base de Conhecimento")
    st.write("Faça o upload do Manual Oficial em PDF para indexação automática na base vetorial.")

    uploaded_file = st.file_uploader("Selecione o arquivo PDF do Manual Tributário", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Processar e Indexar Manual"):
            with st.spinner("Extraindo texto e gerando embeddings inteligentes..."):
                try:
                    reader = pypdf.PdfReader(uploaded_file)
                    total_paginas = len(reader.pages)
                    
                    textos_chunks = []
                    metadados_chunks = []
                    ids_chunks = []
                    
                    chunk_counter = 0
                    for idx, page in enumerate(reader.pages):
                        texto_pagina = page.extract_text()
                        if texto_pagina:
                            paragrafos = texto_pagina.split("\n\n")
                            for p in paragrafos:
                                if len(p.strip()) > 30:
                                    textos_chunks.append(p.strip())
                                    metadados_chunks.append({
                                        "source": uploaded_file.name,
                                        "page": idx + 1,
                                        "version": "2026.1"
                                    })
                                    ids_chunks.append(f"chunk_{chunk_counter}")
                                    chunk_counter += 1

                    if textos_chunks:
                        collection.add(
                            documents=textos_chunks,
                            metadatas=metadados_chunks,
                            ids=ids_chunks
                        )
                        st.success(f"Manual processado com sucesso! {total_paginas} páginas lidas e {len(textos_chunks)} trechos indexados.")
                    else:
                        st.warning("O PDF não continha texto legível extraível.")
                        
                except Exception as e:
                    st.error(f"Erro ao processar o PDF: {str(e)}")

    st.markdown("---")
    st.markdown("### Status Atual do Repositório")
    st.metric(label="Total de Chunks Indexados", value=collection.count())
    st.metric(label="Versão Vigente do Manual", value="Manual Tributário v2026.1")
