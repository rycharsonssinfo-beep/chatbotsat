import os
import sqlite3
import streamlit as st
import pdfplumber
from openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# --- CONFIGURAÇÕES E CAMINHOS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AQ.Ab8RN6LDzgyz_W4yDpuHA4kAh-CJZqTW-_-zioR8LYMoaWVECg")
CHROMA_PATH = "data/vectorstore"
MANUALS_PATH = "data/manuals"
SQLITE_PATH = "database/sat_metadata.db"

# --- BANCO DE DADOS SQLITE (LOGS E FEEDBACK) ---
def init_db():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
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

def log_feedback(question, answer, helpful):
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (question, answer, helpful) VALUES (?, ?, ?)",
        (question, answer, int(helpful))
    )
    conn.commit()
    conn.close()

# --- INGESTÃO DE PDF ---
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

# --- GERAÇÃO DE RESPOSTA COM IA ---
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Você é o Assistente Oficial de Suporte do Sistema Tributário.
Sua função é auxiliar usuários exclusivamente na utilização do sistema tributário descrito na base de conhecimento fornecida.

REGRAS OBRIGATÓRIAS:
1. Utilize somente informações presentes no contexto recuperado da base de conhecimento.
2. Nunca invente informações, menus, caminhos, campos, botões ou funcionalidades.
3. Se a informação não estiver disponível, diga claramente: "Não encontrei essa informação no manual disponível. Para evitar fornecer uma orientação incorreta, não consigo confirmar o procedimento para essa situação."
4. Quando possível, informe a página do manual utilizada na seção de referência.
5. Priorize respostas práticas e objetivas baseadas no formato de suporte técnico (Como fazer, Erro, Causa, Solução).
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

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Assistente do Sistema Tributário", layout="wide")

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
        os.makedirs(MANUALS_PATH, exist_ok=True)
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

# Inicialização do VectorStore para consultas
if os.path.exists(CHROMA_PATH):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
else:
    retriever = None

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
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Útil", key=f"utl_{len(st.session_state.messages)}"):
                log_feedback(query, response, 1)
                st.toast("Obrigado pelo feedback!")
        with col2:
            if st.button("👎 Não resolveu", key=f"not_utl_{len(st.session_state.messages)}"):
                log_feedback(query, response, 0)
                st.toast("Feedback registrado.")
