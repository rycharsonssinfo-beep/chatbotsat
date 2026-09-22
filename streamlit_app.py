import sys
# Patch obrigatório para o ChromaDB funcionar no Streamlit Cloud
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import streamlit as st

st.set_page_config(page_title="Assistente do Sistema Tributário", layout="wide")

os.makedirs("data/vectorstore", exist_ok=True)
os.makedirs("data/manuals", exist_ok=True)
os.makedirs("database", exist_ok=True)

import sqlite3
import pdfplumber
from openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AQ.Ab8RN6LDzgyz_W4yDpuHA4kAh-CJZqTW-_-zioR8LYMoaWVECg")
CHROMA_PATH = "data/vectorstore"
MANUALS_PATH = "data/manuals"
SQLITE_PATH = "database/sat_metadata.db"

def init_db():
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                helpful INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao inicializar o banco SQLite: {e}")

def log_feedback(question, answer, helpful):
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (question, answer, helpful) VALUES (?, ?, ?)",
            (question, answer, int(helpful))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def extract_text_from_pdf(pdf_path):
    documents = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                documents.append({
                    "page": i + 1,
                    "content": text
                })
    return documents

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Você é o Assistente Oficial de Suporte do Sistema Tributário.
Sua função é auxiliar usuários exclusivamente na utilização do sistema tributário descrito na base de conhecimento fornecida.
REGRAS OBRIGATÓRIAS:
1. Utilize somente informações presentes no contexto recuperado da base de conhecimento.
2. Nunca invente informações, menus, caminhos, campos, botões ou funcionalidades.
3. Se a informação não estiver disponível, diga claramente: "Não encontrei essa informação no manual disponível."
4. Quando possível, informe a página do manual utilizada na seção de referência.
"""

def generate_answer(query, context_docs):
    context_text = ""
    sources = []
    
    for doc in context_docs:
        context_text += f"\n---\n[Página {doc.metadata.get('page')}] {doc.page_content}\n"
        sources.append(f"Manual do Sistema Tributário, Página {doc.metadata.get('page')}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Contexto recuperado:\n{context_text}\n\nPergunta do usuário: {query}"}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.0
    )

    answer = response.choices[0].message.content
    unique_sources = list(set(sources))
    return answer, unique_sources

init_db()

st.markdown("""
    <h2 style='color: #1E3A8A;'>Assistente do Sistema Tributário</h2>
    <p style='color: #6B7280;'>Suporte inteligente baseado no Manual Oficial do Sistema</p>
    <hr>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Administração da Base")
    uploaded_file = st.file_uploader("Enviar Novo Manual (PDF)", type=["pdf"])
    
    if uploaded_file:
        file_path = os.path.join(MANUALS_PATH, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("PDF carregado com sucesso!")
        
        if st.button("Processar e Indexar Manual"):
            with st.spinner("Processando documento e gerando embeddings..."):
                raw_docs = extract_text_from_pdf(file_path)
                docs = [
                    Document(page_content=d["content"], metadata={"page": d["page"], "source": uploaded_file.name})
                    for d in raw_docs
                ]
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = splitter.split_documents(docs)
                
                embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
                vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
                vectorstore.persist()
                st.success(f"Base atualizada com {len(chunks)} chunks!")

    st.markdown("---")
    st.markdown("**Sugestões de Perguntas:**")
    if st.button("Como cadastrar um contribuinte?"):
        st.session_state["preset_query"] = "Como cadastrar um contribuinte?"
    if st.button("Como emitir um DAM?"):
        st.session_state["preset_query"] = "Como emitir um DAM?"

retriever = None
if os.path.exists(CHROMA_PATH) and os.listdir(CHROMA_PATH):
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    except Exception:
        pass

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            st.caption(f"**Fonte:** {', '.join(message['sources'])}")

query = st.chat_input("Digite sua dúvida sobre o sistema tributário...")

if "preset_query" in st.session_state and st.session_state["preset_query"]:
    query = st.session_state["preset_query"]
    st.session_state["preset_query"] = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if not retriever:
            response = "A base de conhecimento ainda não foi inicializada. Por favor, faça o upload do manual na barra lateral."
            sources = []
            st.markdown(response)
        else:
            with st.spinner("Consultando o manual oficial..."):
                relevant_docs = retriever.invoke(query)
                response, sources = generate_answer(query, relevant_docs)
                st.markdown(response)
                if sources:
                    st.caption(f"**Fonte:** {', '.join(sources)}")

        st.session_state.messages.append({
            "role": "assistant", 
            "content": response, 
            "sources": sources
        })
