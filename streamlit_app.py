import os
import re
import json
import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(
    page_title="Chatbot SAT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-app: #F8FAFC;
        --sidebar-bg: #FFFFFF;
        --surface-card: #FFFFFF;
        --surface-hover: #F1F5F9;
        --border-subtle: #E2E8F0;
        --border-strong: #CBD5E1;
        --text-main: #0F172A;
        --text-muted: #475569;
        --text-dim: #94A3B8;
        --accent: #2563EB;
        --accent-hover: #1D4ED8;
    }

    .stApp {
        background-color: var(--bg-app);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-main);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-main);
    }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 7rem;
        max-width: 900px;
        margin: 0 auto;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-subtle);
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
        max-width: 100%;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: transparent;
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        color: var(--text-muted);
        font-weight: 500;
        font-size: 0.88rem;
        text-align: left;
        padding: 0.55rem 0.85rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: var(--surface-hover);
        color: var(--text-main);
        border-color: var(--border-strong);
    }

    section[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: var(--accent);
        font-weight: 600;
    }
    section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
        background-color: #DBEAFE;
        color: var(--accent-hover);
    }

    [data-testid="stChatInput"] {
        background-color: var(--bg-app);
        border-top: 1px solid var(--border-subtle);
        padding: 1rem 0;
    }

    [data-testid="stChatInput"] textarea {
        background-color: #FFFFFF;
        color: var(--text-main);
        border: 1px solid var(--border-strong);
        border-radius: 12px;
        font-size: 0.95rem;
        padding: 0.85rem 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    [data-testid="stChatInput"] button {
        background-color: var(--accent);
        color: #ffffff;
        border-radius: 8px;
        margin: 4px;
        transition: background-color 0.2s ease;
    }
    [data-testid="stChatInput"] button:hover {
        background-color: var(--accent-hover);
    }

    [data-testid="stChatMessage"] {
        background-color: transparent;
        padding: 1.25rem 0;
        border-bottom: 1px solid var(--border-subtle);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--surface-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        color: var(--text-muted);
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--surface-hover);
        color: var(--accent);
        border-color: var(--border-strong);
    }

    input {
        background-color: #FFFFFF;
        color: var(--text-main);
        border: 1px solid var(--border-strong);
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE CONHECIMENTO DO CHATBOT SAT
# ==========================================
BASE_CONHECIMENTO_SAT = {
    "metadata": {
        "documento": "Manual de Orientação e Procedimentos do SAT",
        "versao": "2026",
        "orgao": "Sistema de Atendimento e Tributação (SAT)"
    },
    "tabelas": [
        {"tabela": "101", "nome": "Cadastro de Contribuintes", "modulo": "Cadastral", "finalidade": "Identificar dados cadastrais e fiscais dos contribuintes.", "fonte": "Manual SAT — p. 12"},
        {"tabela": "201", "nome": "Declarações Fiscais", "modulo": "Apuração", "finalidade": "Registrar as apurações e declarações mensais enviadas.", "fonte": "Manual SAT — p. 25"},
        {"tabela": "301", "nome": "Emissão de Guias de Recolhimento", "modulo": "Financeiro", "finalidade": "Gerenciar documentos de arrecadação e taxas.", "fonte": "Manual SAT — p. 40"}
    ],
    "regras": [
        {
            "id_interno": "SAT-RULE-001",
            "modulo": "Apuração",
            "tabela": "201",
            "regra": "O envio da declaração sem movimento deve ser informado explicitamente no sistema.",
            "mensagem_original": "Declaração não localizada para o período de apuração informado.",
            "causa": "Ausência de transmissão do arquivo de apuração no prazo regulamentar.",
            "correcao": "Transmitir a declaração correspondente ao período através do canal oficial do SAT.",
            "fonte": "Manual SAT — p. 28"
        },
        {
            "id_interno": "SAT-RULE-002",
            "modulo": "Cadastral",
            "tabela": "101",
            "regra": "Os dados cadastrais do contribuinte devem estar atualizados antes da emissão de certidões.",
            "mensagem_original": "Divergência cadastral detectada na validação do documento.",
            "causa": "Alteração de endereço ou atividade econômica não atualizada no sistema.",
            "correcao": "Realizar a atualização cadastral via requerimento online no SAT.",
            "fonte": "Manual SAT — p. 15"
        }
    ],
    "validacoes_matematicas": [
        {"id": "MAT-SAT-01", "descricao": "Conferência de saldo a recolher", "formula": "Total de Débitos - Total de Créditos = Imposto a Recolher", "fonte": "Manual SAT — p. 55"}
    ]
}

# ==========================================
# 3. MOTOR DE RAG / BUSCA INTELIGENTE NA BASE
# ==========================================
def buscar_conhecimento_relevante(query):
    query_lower = query.lower()
    trechos_relevantes = []
    
    for r in BASE_CONHECIMENTO_SAT["regras"]:
        termos = [r["modulo"].lower(), r["tabela"], r["mensagem_original"].lower(), r["regra"].lower()]
        if any(termo in query_lower for termo in termos if len(termo) > 2):
            trechos_relevantes.append(r)
            
    for t in BASE_CONHECIMENTO_SAT["tabelas"]:
        if t["tabela"] in query_lower or t["nome"].lower() in query_lower or t["modulo"].lower() in query_lower:
            trechos_relevantes.append(t)
            
    for m in BASE_CONHECIMENTO_SAT["validacoes_matematicas"]:
        if m["id"].lower() in query_lower or m["descricao"].lower() in query_lower:
            trechos_relevantes.append(m)
            
    if not trechos_relevantes:
        return BASE_CONHECIMENTO_SAT["regras"][:3]
        
    return trechos_relevantes

# ==========================================
# 4. CONFIGURAÇÃO DA API GEMINI
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def consultar_assistente_gemini(historico_conversas, ultima_mensagem):
    if not api_key:
        return "### ⚠️ Configuração Pendente\nA chave da API Gemini não foi configurada nos segredos da aplicação."
        
    contexto_filtrado = buscar_conhecimento_relevante(ultima_mensagem)
    
    prompt_sistema = f"""Você é um assistente técnico sênior especializado no **Chatbot do SAT** (Sistema de Atendimento e Tributação).
Seu objetivo é ajudar contribuintes e operadores a tirar dúvidas, diagnosticar erros de apuração, regularização de cadastros e envio de declarações.

Contexto técnico recuperado do Manual do SAT:
{json.dumps(contexto_filtrado, ensure_ascii=False, indent=2)}

Diretrizes para a resposta:
- Seja objetivo, técnico e direto ao ponto.
- Se o usuário enviou uma mensagem genérica, conduza a investigação pedindo detalhes do erro ou processo.
- Se o usuário enviou uma ocorrência clara, estruture o diagnóstico nos tópicos:
  1. **Contexto do problema**
  2. **Causa provável**
  3. **Passos para correção**
  4. **Fundamentação (Manual do SAT)**
- Inclua ao final em linha discreta: ● Alta confiança."""

    contents = []
    for msg in historico_conversas:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [msg["content"]]})
        
    contents.append({"role": "user", "parts": [ultima_mensagem]})
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=prompt_sistema)
        response = model.generate_content(contents)
        if response and response.text:
            return response.text
    except Exception as e:
        return f"""### ⚠️ Diagnóstico por Regra Normativa (SAT)
* **Contexto e Causa Raiz:** O erro reportado indica uma divergência nos registros fiscais ou cadastrais do SAT.
* **Plano de Correção:** Verifique os parâmetros informados no sistema e tente novamente.
*(Detalhe técnico: `{e}`)*\n\n● Média confiança"""

    return "Não foi possível gerar uma resposta no momento."

# ==========================================
# 5. GERENCIAMENTO DE ESTADO DA SESSÃO (CHAT)
# ==========================================
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

if "nav_atual" not in st.session_state:
    st.session_state["nav_atual"] = "Assistente"

# ==========================================
# 6. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style='padding-top: 0.5rem; padding-bottom: 1.2rem;'>
            <div style='font-size: 0.95rem; font-weight: 700; color: #0F172A; display: flex; align-items: center; gap: 8px;'>
                <span>🤖</span> Chatbot SAT
            </div>
            <div style='font-size: 0.75rem; color: #64748B; margin-top: 2px;'>Sistema de Atendimento e Tributação</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("＋ Nova conversa", key="btn_nova_analise", use_container_width=True, type="primary"):
        st.session_state["mensagens"] = []
        st.session_state["nav_atual"] = "Assistente"
        st.rerun()
        
    st.markdown("<div style='margin: 1.2rem 0; border-top: 1px solid #E2E8F0;'></div>", unsafe_allow_html=True)
    
    nav_opcoes = {
        "Assistente": "💬 Chat",
        "Regras": "📖 Base de Conhecimento"
    }
    
    for chave, rotulo in nav_opcoes.items():
        ativo = st.session_state["nav_atual"] == chave
        btn_type = "primary" if ativo else "secondary"
        if st.button(rotulo, key=f"nav_{chave}", use_container_width=True, type=btn_type):
            st.session_state["nav_atual"] = chave
            st.rerun()

    st.markdown("<div style='margin: 2rem 0; border-top: 1px solid #E2E8F0;'></div>", unsafe_allow_html=True)
    
    st.markdown(
        "<div style='font-size: 0.73rem; color: #94A3B8; line-height: 1.5;'>"
        "<strong>Chatbot SAT</strong><br>"
        "Manual de Orientações 2026"
        "</div>", 
        unsafe_allow_html=True
    )

# ==========================================
# 7. CORPO DA APLICAÇÃO (TELAS)
# ==========================================
pagina = st.session_state["nav_atual"]

if pagina == "Assistente":
    st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.8rem;'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.4rem;'>🤖</span>
                <div>
                    <div style='font-size: 1.1rem; font-weight: 700; color: #0F172A; line-height: 1.2;'>Assistente Virtual SAT</div>
                    <div style='font-size: 0.78rem; color: #64748B;'>Tire dúvidas sobre apuração, cadastros e declarações</div>
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #059669;'>
                <span style='width: 7px; height: 7px; background-color: #10B981; border-radius: 50%; display: inline-block;'></span> Online
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state["mensagens"]:
        st.markdown("""
            <div style='text-align: center; margin-top: 4rem; margin-bottom: 3rem;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.8rem;'>🤖</div>
                <h1 style='font-size: 1.4rem; font-weight: 600; color: #0F172A; margin-bottom: 0.4rem;'>Olá! Como posso ajudar no SAT?</h1>
                <p style='font-size: 0.9rem; color: #64748B; max-width: 450px; margin: 0 auto; line-height: 1.5;'>
                    Digite sua dúvida ou cole uma mensagem de erro relacionada aos processos do SAT.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
    for msg in st.session_state["mensagens"]:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])
                
    if prompt_usuario := st.chat_input("Digite sua dúvida sobre o SAT..."):
        st.session_state["mensagens"].append({"role": "user", "content": prompt_usuario})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt_usuario)
            
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processando sua dúvida..."):
                resposta_ia = consultar_assistente_gemini(st.session_state["mensagens"][:-1], prompt_usuario)
                st.markdown(resposta_ia)
                
        st.session_state["mensagens"].append({"role": "assistant", "content": resposta_ia})

elif pagina == "Regras":
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h2 style='font-size: 1.35rem; font-weight: 600; margin-bottom: 0.3rem; color: #0F172A;'>Base de Conhecimento</h2>
            <p style='color: #64748B; font-size: 0.88rem; margin: 0;'>Regras, tabelas e orientações normativas do Chatbot SAT.</p>
        </div>
    """, unsafe_allow_html=True)
    
    termo_busca = st.text_input("🔍 Pesquisar na base...", placeholder="Digite um termo...")
    
    st.markdown("<div style='margin: 1.2rem 0;'></div>", unsafe_allow_html=True)
    
    tab_regras, tab_tabelas = st.tabs(["📌 Diretrizes e Regras", "📊 Tabelas do SAT"])
    
    with tab_regras:
        st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
        for regra in BASE_CONHECIMENTO_SAT["regras"]:
            if termo_busca.lower() in str(regra).lower() or not termo_busca:
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 14px;'>
                        <div style='font-size: 0.73rem; font-weight: 600; color: #2563EB; margin-bottom: 4px;'>{regra['id_interno']} • {regra['modulo']}</div>
                        <div style='font-size: 0.93rem; font-weight: 600; color: #0F172A; margin-bottom: 6px;'>{regra['regra']}</div>
                        <div style='font-size: 0.83rem; color: #475569; margin-bottom: 6px;'><strong>Correção:</strong> {regra['correcao']}</div>
                    </div>
                """, unsafe_allow_html=True)
                    
    with tab_tabelas:
        st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
        for tab in BASE_CONHECIMENTO_SAT["tabelas"]:
            if termo_busca.lower() in str(tab).lower() or not termo_busca:
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px; margin-bottom: 12px;'>
                        <div style='font-weight: 600; color: #2563EB;'>Tabela {tab['tabela']} - {tab['nome']}</div>
                        <p style='font-size: 0.83rem; color: #475569; margin: 4px 0 0 0;'>{tab['finalidade']}</p>
                    </div>
                """, unsafe_allow_html=True)
