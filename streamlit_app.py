import io
import re
import json
import sqlite3
from datetime import datetime, date
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
# ==========================================
st.set_page_config(
    page_title="Relatório de Atendimento Presencial — Portal",
    page_icon="📋",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #0d1527;
        color: #ffffff;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #1b5ef7;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #1446c2;
        color: white;
    }
    /* Estilo compacto para os itens do histórico na barra lateral */
    .history-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #cbd5e1;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        color: #475569;
        font-weight: 600;
        border: 1px solid #e2e8f0;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b5ef7 !important;
        color: white !important;
        border-color: #1b5ef7 !important;
    }
    .stButton button[kind="primary"] {
        background-color: #1b5ef7;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #1446c2;
    }
    .signature-badge {
        background-color: #ecfdf5;
        color: #065f46;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 8px;
        border: 1px solid #a7f3d0;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. BANCO DE DADOS E PERSISTÊNCIA LOCAL
# ==========================================
def init_db():
    conn = sqlite3.connect("relatorios.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_criacao TEXT,
            entidade TEXT,
            sistema TEXT,
            nome_usuario TEXT,
            dados_json TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM sistemas")
    if cursor.fetchone()[0] == 0:
        padroes = [
            "Contabilidade", "Fluxus", "Folha de Pagamento", "Nota Fiscal Eletrônica",
            "Portal da Transparência", "SAT Web", "SAT WEB SPU", "SIG - Almoxarifado",
            "SIG - Doações", "SIG - Licitação", "SIG - Merenda", "SIG - Patrimônio",
            "SIG - PPA", "SigWeb - Almoxarifado", "SigWeb - Geral", "SigWeb - Orçamento",
            "SigWeb - PPA", "SigWeb - Social", "Licitação", "Veículos Web"
        ]
        for s in padroes:
            cursor.execute("INSERT OR IGNORE INTO sistemas (nome) VALUES (?)", (s,))
        conn.commit()
    conn.close()

init_db()

def carregar_sistemas_db() -> list:
    conn = sqlite3.connect("relatorios.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM sistemas ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return ["Selecione o sistema..."] + [r[0] for r in rows] + ["Outros"]

def adicionar_sistema_db(novo_sistema: str) -> bool:
    if novo_sistema and novo_sistema.strip():
        conn = sqlite3.connect("relatorios.db", check_same_thread=False)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM sistemas WHERE LOWER(nome) = LOWER(?)", (novo_sistema.strip(),))
            if cursor.fetchone():
                conn.close()
                return False
            cursor.execute("INSERT INTO sistemas (nome) VALUES (?)", (novo_sistema.strip(),))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    return False


# ==========================================
# 3. AUXILIARES E VALIDAÇÕES
# ==========================================
def limpar_telefone(texto: str) -> str:
    if not texto:
        return ""
    apenas_numeros = re.sub(r'[^0-9]', '', texto)
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2]} {apenas_numeros[3:7]}-{apenas_numeros[7:]}"
    elif len(apenas_numeros) == 10:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    return apenas_numeros

def validar_email(email: str) -> bool:
    if not email:
        return True
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(padrao, email))


class RelatorioModel:
    def __init__(self):
        self.informacoes_gerais = {
            "entidade": "",
            "sistema": "",
            "setor": "",
            "nome_usuario": "",
            "email": "",
            "whatsapp": "",
            "data_visita": date.today(),
            "responsavel_atendimento": "",
            "descricao": "",
            "periodo_atendimento": "",
            "turno": "M"
        }
        self.servico_executado = {
            "implantacao": False,
            "treinamento": False,
            "demonstracao_sistema": False,
            "visita": False,
            "tipo_visita": [],
            "outros": False,
            "observacoes": ""
        }
        self.resultado_atendimento = {
            "perfeito_funcionamento": False,
            "pendencias_posterior": False,
            "treinamento_sucesso": False,
            "pendencias_operador": False,
            "cartoes": False,
            "outros": False,
            "observacoes": ""
        }
        self.area_cliente = {
            "local": "",
            "nome_usuario": "",
            "whatsapp_usuario": "",
            "assinatura_usuario": None,
            "data_termino": date.today(),
            "nome_coordenador": "",
            "whatsapp_coordenador": "",
            "assinatura_coordenador": None
        }
        self.anexos = []

    def to_dict(self) -> dict:
        d = {
            "informacoes_gerais": self.informacoes_gerais.copy(),
            "servico_executado": self.servico_executado,
            "resultado_atendimento": self.resultado_atendimento,
            "area_cliente": self.area_cliente.copy(),
            "anexos": self.anexos
        }
        d["informacoes_gerais"]["whatsapp"] = limpar_telefone(d["informacoes_gerais"].get("whatsapp", ""))
        d["area_cliente"]["whatsapp_usuario"] = limpar_telefone(d["area_cliente"].get("whatsapp_usuario", ""))
        d["area_cliente"]["whatsapp_coordenador"] = limpar_telefone(d["area_cliente"].get("whatsapp_coordenador", ""))

        if isinstance(d["informacoes_gerais"].get("data_visita"), date):
            d["informacoes_gerais"]["data_visita"] = d["informacoes_gerais"]["data_visita"].strftime("%d/%m/%Y")
        if isinstance(d["area_cliente"].get("data_termino"), date):
            d["area_cliente"]["data_termino"] = d["area_cliente"]["data_termino"].strftime("%d/%m/%Y")
        return d


# ==========================================
# 4. CAPTURA DE ASSINATURA
# ==========================================
def capturar_assinatura(titulo: str, key_prefix: str, modelo_ref, campo_modelo: str):
    st.markdown(f"**{titulo}**")
    metodo = st.radio(f"Método ({titulo})", ["Desenhar na Tela", "Enviar Imagem"], horizontal=True, key=f"metodo_{key_prefix}")
    
    if metodo == "Desenhar na Tela":
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=130,
            width=350,
            drawing_mode="freedraw",
            update_streamlit=True,
            return_image_data=True,
            key=f"canvas_{key_prefix}"
        )
        if st.button(f"Salvar {titulo}", key=f"btn_salvar_{key_prefix}"):
            if canvas_result is not None and canvas_result.image_data is not None:
                try:
                    img_array = canvas_result.image_data
                    if img_array.any():
                        pil_img = Image.fromarray(img_array.astype("uint8"), mode="RGBA")
                        background = Image.new("RGB", pil_img.size, (255, 255, 255))
                        background.paste(pil_img, mask=pil_img.split()[3])
                        buf = io.BytesIO()
                        background.save(buf, format="PNG")
                        modelo_ref.area_cliente[campo_modelo] = buf.getvalue()
                        st.success(f"{titulo} salva com sucesso!")
                    else:
                        st.warning("O painel de desenho está vazio.")
                except Exception as e:
                    st.error(f"Erro ao capturar desenho: {e}")
    else:
        uploaded_file = st.file_uploader(f"Enviar arquivo ({titulo})", type=["png", "jpg", "jpeg"], key=f"upload_{key_prefix}")
        if uploaded_file is not None:
            modelo_ref.area_cliente[campo_modelo] = uploaded_file.getvalue()
            st.success(f"{titulo} carregada com sucesso!")

    if modelo_ref.area_cliente[campo_modelo]:
        st.markdown('<div class="signature-badge">✅ Assinatura Registrada</div>', unsafe_allow_html=True)
        st.image(modelo_ref.area_cliente[campo_modelo], width=180)


# ==========================================
# 5. INTERFACE PRINCIPAL E BARRA LATERAL REORGANIZADA
# ==========================================
st.title("📋 Relatório de Atendimento Presencial")
st.markdown("Preencha os campos abaixo, adicione evidências com legendas e gere relatórios profissionais.")

if "relatorio_model" not in st.session_state:
    st.session_state["relatorio_model"] = RelatorioModel()

modelo = st.session_state["relatorio_model"]

# Barra Lateral Limpa e Funcional
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button("🔄 Novo Relatório (Limpar)", use_container_width=True):
        st.session_state["relatorio_model"] = RelatorioModel()
        st.rerun()
        
    st.markdown("---")
    st.subheader("➕ Novo Sistema")
    novo_sis_input = st.text_input("Nome do Sistema", placeholder="Ex: Novo Sistema...")
    if st.button("Cadastrar", use_container_width=True):
        if adicionar_sistema_db(novo_sis_input):
            st.success(f"Sistema adicionado!")
            st.rerun()
        else:
            st.warning("Já existe ou nome vazio.")

    st.markdown("---")
    st.subheader("📂 Histórico de Relatórios")
    termo_busca = st.text_input("🔍 Filtrar entidade/usuário", placeholder="Digite para buscar...")
    
    try:
        conn_h = sqlite3.connect("relatorios.db", check_same_thread=False)
        cursor_h = conn_h.cursor()
        if termo_busca:
            cursor_h.execute("SELECT id, data_criacao, entidade, sistema, nome_usuario, dados_json FROM historico WHERE entidade LIKE ? OR nome_usuario LIKE ? ORDER BY id DESC LIMIT 10", (f"%{termo_busca}%", f"%{termo_busca}%"))
        else:
            cursor_h.execute("SELECT id, data_criacao, entidade, sistema, nome_usuario, dados_json FROM historico ORDER BY id DESC LIMIT 5")
        historico_rows = cursor_h.fetchall()
        conn_h.close()
        
        if historico_rows:
            for h_id, h_data, h_ent, h_sis, h_user, h_json in historico_rows:
                with st.container():
                    st.markdown(f"""
                    <div class="history-card">
                        <b>{h_ent}</b><br>
                        🛠️ {h_sis or 'N/D'}<br>
                        👤 {h_user} | 📅 {h_data}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Carregar", key=f"carregar_{h_id}", use_container_width=True):
                        try:
                            dados_carregados = json.loads(h_json)
                            novo_mod = RelatorioModel()
                            novo_mod.informacoes_gerais = dados_carregados.get("informacoes_gerais", novo_mod.informacoes_gerais)
                            
                            # Correção: Converter string de data para objeto date do Python
                            data_v_str = novo_mod.informacoes_gerais.get("data_visita")
                            if isinstance(data_v_str, str):
                                try:
                                    novo_mod.informacoes_gerais["data_visita"] = datetime.strptime(data_v_str, "%d/%m/%Y").date()
                                except ValueError:
                                    try:
                                        novo_mod.informacoes_gerais["data_visita"] = datetime.strptime(data_v_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        novo_mod.informacoes_gerais["data_visita"] = date.today()

                            novo_mod.servico_executado = dados_carregados.get("servico_executado", novo_mod.servico_executado)
                            novo_mod.resultado_atendimento = dados_carregados.get("resultado_atendimento", novo_mod.resultado_atendimento)
                            
                            novo_mod.area_cliente = dados_carregados.get("area_cliente", novo_mod.area_cliente)
                            data_t_str = novo_mod.area_cliente.get("data_termino")
                            if isinstance(data_t_str, str):
                                try:
                                    novo_mod.area_cliente["data_termino"] = datetime.strptime(data_t_str, "%d/%m/%Y").date()
                                except ValueError:
                                    try:
                                        novo_mod.area_cliente["data_termino"] = datetime.strptime(data_t_str, "%Y-%m-%d").date()
                                    except ValueError:
                                        novo_mod.area_cliente["data_termino"] = date.today()

                            novo_mod.anexos = dados_carregados.get("anexos", [])
                            st.session_state["relatorio_model"] = novo_mod
                            st.success("Carregado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                st.markdown("")
        else:
            st.markdown("<small style='color: #94a3b8;'>Nenhum registro encontrado.</small>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<small style='color: #94a3b8;'>Banco de dados vazio.</small>", unsafe_allow_html=True)

# Abas do Formulário
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Informações Gerais", 
    "⚙️ Serviços", 
    "📊 Resultados", 
    "✍️ Assinaturas",
    "📷 Evidências (Fotos)"
])

with tab1:
    with st.container(border=True):
        st.subheader("📌 Dados Principais e Contato")
        col1, col2 = st.columns(2)
        with col1:
            modelo.informacoes_gerais["entidade"] = st.text_input("Entidade (Prefeitura / Câmara...)*", value=modelo.informacoes_gerais["entidade"])
            
            lista_sistemas_atual = carregar_sistemas_db()
            sistema_atual = modelo.informacoes_gerais.get("sistema", "Selecione o sistema...")
            try:
                idx_sis = lista_sistemas_atual.index(sistema_atual)
            except ValueError:
                idx_sis = 0
            sistema_esc = st.selectbox("Sistema", lista_sistemas_atual, index=idx_sis)
            modelo.informacoes_gerais["sistema"] = "" if sistema_esc == "Selecione o sistema..." else sistema_esc

            modelo.informacoes_gerais["setor"] = st.text_input("Setor", value=modelo.informacoes_gerais["setor"])
            modelo.informacoes_gerais["nome_usuario"] = st.text_input("Nome do Usuário*", value=modelo.informacoes_gerais["nome_usuario"])
            modelo.informacoes_gerais["email"] = st.text_input("E-mail", value=modelo.informacoes_gerais["email"])
        with col2:
            raw_wpp = st.text_input("WhatsApp (Apenas números)", value=modelo.informacoes_gerais["whatsapp"])
            modelo.informacoes_gerais["whatsapp"] = limpar_telefone(raw_wpp)

            modelo.informacoes_gerais["data_visita"] = st.date_input("Data da Visita", value=modelo.informacoes_gerais["data_visita"], format="DD/MM/YYYY")
            modelo.informacoes_gerais["responsavel_atendimento"] = st.text_input("Responsável pelo Atendimento", value=modelo.informacoes_gerais["responsavel_atendimento"])
            modelo.informacoes_gerais["periodo_atendimento"] = st.text_input("Período de Atendimento", value=modelo.informacoes_gerais["periodo_atendimento"])
            
            turno_map = {"M": 0, "T": 1, "N": 2}
            turno_atual = modelo.informacoes_gerais.get("turno", "M")
            turno_escolhido = st.radio("Turno", ["M — Manhã", "T — Tarde", "N — Noite"], index=turno_map.get(turno_atual, 0), horizontal=True)
            modelo.informacoes_gerais["turno"] = turno_escolhido[0]

        modelo.informacoes_gerais["descricao"] = st.text_area("Descrição Detalhada do Atendimento", value=modelo.informacoes_gerais["descricao"])

with tab2:
    with st.container(border=True):
        st.subheader("⚙️ Registro do Serviço Executado")
        c1, c2, c3 = st.columns(3)
        with c1:
            modelo.servico_executado["implantacao"] = st.checkbox("Implantação", value=modelo.servico_executado["implantacao"])
            modelo.servico_executado["treinamento"] = st.checkbox("Treinamento", value=modelo.servico_executado["treinamento"])
        with c2:
            modelo.servico_executado["demonstracao_sistema"] = st.checkbox("Demonstração de Sistema", value=modelo.servico_executado["demonstracao_sistema"])
            modelo.servico_executado["outros"] = st.checkbox("Outros", value=modelo.servico_executado["outros"])
        with c3:
            modelo.servico_executado["visita"] = st.checkbox("Visita", value=modelo.servico_executado["visita"])

        if modelo.servico_executado["visita"]:
            st.markdown("##### Tipo de Visita:")
            t_vis = modelo.servico_executado.get("tipo_visita", [])
            rt = st.checkbox("Relacionamento Técnica", value="Relacionamento Técnica" in t_vis)
            tp = st.checkbox("Técnica Preventiva", value="Técnica Preventiva" in t_vis)
            sel_t = []
            if rt: sel_t.append("Relacionamento Técnica")
            if tp: sel_t.append("Técnica Preventiva")
            modelo.servico_executado["tipo_visita"] = sel_t

        modelo.servico_executado["observacoes"] = st.text_area("Observações sobre o Serviço", value=modelo.servico_executado["observacoes"])

with tab3:
    with st.container(border=True):
        st.subheader("📊 Resultado do Atendimento")
        modelo.resultado_atendimento["perfeito_funcionamento"] = st.checkbox("O Sistema ficou em perfeito funcionamento, sem nenhuma pendência", value=modelo.resultado_atendimento["perfeito_funcionamento"])
        modelo.resultado_atendimento["pendencias_posterior"] = st.checkbox("Existem pendências para solução posterior", value=modelo.resultado_atendimento["pendencias_posterior"])
        modelo.resultado_atendimento["treinamento_sucesso"] = st.checkbox("Treinamento efetuado com sucesso", value=modelo.resultado_atendimento["treinamento_sucesso"])
        modelo.resultado_atendimento["pendencias_operador"] = st.checkbox("Existem pendências para o operador/chefe do setor", value=modelo.resultado_atendimento["pendencias_operador"])
        modelo.resultado_atendimento["cartoes"] = st.checkbox("Existem cartões", value=modelo.resultado_atendimento["cartoes"])
        modelo.resultado_atendimento["outros"] = st.checkbox("Outros resultados", value=modelo.resultado_atendimento["outros"])
        
        modelo.resultado_atendimento["observacoes"] = st.text_area("Observações do Resultado", value=modelo.resultado_atendimento["observacoes"])

with tab4:
    with st.container(border=True):
        st.subheader("✍️ Área do Cliente e Validação")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("### 👤 Usuário")
            modelo.area_cliente["local"] = st.text_input("Local", value=modelo.area_cliente["local"])
            modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário (Validação)", value=modelo.area_cliente["nome_usuario"])
            raw_wpp_u = st.text_input("WhatsApp do Usuário", value=modelo.area_cliente["whatsapp_usuario"])
            modelo.area_cliente["whatsapp_usuario"] = limpar_telefone(raw_wpp_u)
            capturar_assinatura("Assinatura do Usuário", "usuario", modelo, "assinatura_usuario")
        with col_c2:
            st.markdown("### 👔 Coordenador")
            modelo.area_cliente["data_termino"] = st.date_input("Data de Término", value=modelo.area_cliente["data_termino"], format="DD/MM/YYYY")
            modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador", value=modelo.area_cliente["nome_coordenador"])
            raw_wpp_c = st.text_input("WhatsApp do Coordenador", value=modelo.area_cliente["whatsapp_coordenador"])
            modelo.area_cliente["whatsapp_coordenador"] = limpar_telefone(raw_wpp_c)
            capturar_assinatura("Assinatura do Coordenador", "coordenador", modelo, "assinatura_coordenador")

with tab5:
    with st.container(border=True):
        st.subheader("📷 Evidências Fotográficas do Atendimento")
        uploaded_photos = st.file_uploader("Enviar imagens de evidência (Telas, comprovantes...)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if uploaded_photos:
            novos_anexos = []
            for idx, p in enumerate(uploaded_photos):
                st.markdown(f"**Foto {idx + 1}:** `{p.name}`")
                c_img, c_leg = st.columns([1, 2])
                with c_img:
                    st.image(p, width=150)
                with c_leg:
                    legenda = st.text_input(f"Legenda para a foto {idx + 1}", key=f"legenda_foto_{idx}")
                novos_anexos.append({"foto": p.getvalue(), "legenda": legenda})
                st.markdown("---")
            modelo.anexos = novos_anexos


# ==========================================
# 6. GERAÇÃO DO PDF PROFISSIONAL COM ANEXOS
# ==========================================
def gerar_pdf_relatorio(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#0d1527')
    accent_color = colors.HexColor('#1b5ef7')
    border_color = colors.HexColor('#cbd5e1')
    bg_light = colors.HexColor('#f8fafc')
    text_dark = colors.HexColor('#1e293b')
    text_muted = colors.HexColor('#64748b')
    
    header_org_style = ParagraphStyle('HeaderOrg', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=accent_color, textTransform='uppercase', spaceAfter=2)
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=primary_color, fontName='Helvetica-Bold', spaceAfter=4)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=9.5, textColor=text_muted, spaceAfter=14)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', backColor=primary_color, spaceBefore=12, spaceAfter=8, leftIndent=6, rightIndent=6, topPadding=6, bottomPadding=6)
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=9, leading=12, textColor=text_dark, fontName='Helvetica')
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=8, textColor=text_muted, spaceBefore=20, alignment=1)

    story.append(Paragraph("Portal de Treinamentos &bull; Suporte Técnico", header_org_style))
    story.append(Paragraph("Relatório de Atendimento Presencial", title_style))
    story.append(Paragraph("Documento oficial de registro de compromissos, suporte e atividades executadas em campo.", subtitle_style))
    
    # Informações Gerais
    ig = dados.get("informacoes_gerais", {})
    story.append(Paragraph("Informações Gerais", section_style))
    info_data = [
        [Paragraph(f"<b>Entidade:</b> {ig.get('entidade', '')}", normal_style), Paragraph(f"<b>Sistema:</b> {ig.get('sistema', '')}", normal_style)],
        [Paragraph(f"<b>Setor:</b> {ig.get('setor', '')}", normal_style), Paragraph(f"<b>Data da Visita:</b> {ig.get('data_visita', '')}", normal_style)],
        [Paragraph(f"<b>Nome do Usuário:</b> {ig.get('nome_usuario', '')}", normal_style), Paragraph(f"<b>WhatsApp:</b> {ig.get('whatsapp', '')}", normal_style)],
        [Paragraph(f"<b>E-mail:</b> {ig.get('email', '')}", normal_style), Paragraph(f"<b>Resp. Atendimento:</b> {ig.get('responsavel_atendimento', '')}", normal_style)],
        [Paragraph(f"<b>Período:</b> {ig.get('periodo_atendimento', '')}", normal_style), Paragraph(f"<b>Turno:</b> [ {'X' if ig.get('turno')=='M' else ' '} ] M &nbsp;&nbsp;[ {'X' if ig.get('turno')=='T' else ' '} ] T &nbsp;&nbsp;[ {'X' if ig.get('turno')=='N' else ' '} ] N", normal_style)],
    ]
    t_info = Table(info_data, colWidths=[270, 270])
    t_info.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_info)
    
    story.append(Spacer(1, 6))
    desc_data = [[Paragraph(f"<b>Descrição Detalhada:</b><br/>{ig.get('descricao', 'Nenhuma descrição informada.')}", normal_style)]]
    t_desc = Table(desc_data, colWidths=[540])
    t_desc.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_desc)
    
    # Serviço Executado
    se = dados.get("servico_executado", {})
    story.append(Paragraph("Registro do Serviço Executado", section_style))
    ci, ct, cd, cv, co = ("[X]" if se.get(k) else "[  ]" for k in ['implantacao', 'treinamento', 'demonstracao_sistema', 'visita', 'outros'])
    serv_html = f"<b>{ci}</b> Implantação &nbsp;&nbsp;&nbsp;&nbsp; <b>{ct}</b> Treinamento &nbsp;&nbsp;&nbsp;&nbsp; <b>{cd}</b> Demonstração de Sistema<br/><b>{cv}</b> Visita &nbsp;&nbsp;&nbsp;&nbsp; <b>{co}</b> Outros"
    t_serv = Table([[Paragraph(serv_html, normal_style)]], colWidths=[540])
    t_serv.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_serv)
    
    if se.get('visita'):
        tv = se.get('tipo_visita', [])
        rt_c = "[X]" if "Relacionamento Técnica" in tv else "[  ]"
        tp_c = "[X]" if "Técnica Preventiva" in tv else "[  ]"
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"&nbsp;&nbsp;<b>Tipo de Visita:</b> &nbsp; {rt_c} Relacionamento Técnica &nbsp;&nbsp;&nbsp;&nbsp; {tp_c} Técnica Preventiva", normal_style))
        
    story.append(Spacer(1, 6))
    t_obs_serv = Table([[Paragraph(f"<b>Observações do Serviço:</b><br/>{se.get('observacoes', 'Nenhuma observação.')}", normal_style)]], colWidths=[540])
    t_obs_serv.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_obs_serv)
    
    # Resultado
    ra = dados.get("resultado_atendimento", {})
    story.append(Paragraph("Resultado do Atendimento", section_style))
    r1, r2, r3, r4, r5, r6 = ("[X]" if ra.get(k) else "[  ]" for k in ['perfeito_funcionamento', 'pendencias_posterior', 'treinamento_sucesso', 'pendencias_operador', 'cartoes', 'outros'])
    res_html = f"<b>{r1}</b> O Sistema ficou em perfeito funcionamento<br/><b>{r2}</b> Existem pendências para solução posterior<br/><b>{r3}</b> Treinamento efetuado com sucesso<br/><b>{r4}</b> Existem pendências para o operador/chefe<br/><b>{r5}</b> Existem cartões<br/><b>{r6}</b> Outros resultados"
    t_res = Table([[Paragraph(res_html, normal_style)]], colWidths=[540])
    t_res.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_res)
    
    story.append(Spacer(1, 6))
    t_obs_res = Table([[Paragraph(f"<b>Observações do Resultado:</b><br/>{ra.get('observacoes', 'Nenhuma observação.')}", normal_style)]], colWidths=[540])
    t_obs_res.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_obs_res)
    
    # Área do Cliente
    ac = dados.get("area_cliente", {})
    story.append(Paragraph("Área do Cliente e Validação", section_style))
    sig_u = RLImage(io.BytesIO(ac.get("assinatura_usuario")), width=140, height=50) if ac.get("assinatura_usuario") else Paragraph("<i>(Sem assinatura)</i>", normal_style)
    sig_c = RLImage(io.BytesIO(ac.get("assinatura_coordenador")), width=140, height=50) if ac.get("assinatura_coordenador") else Paragraph("<i>(Sem assinatura)</i>", normal_style)
    
    cliente_data = [
        [Paragraph(f"<b>Local:</b> {ac.get('local', '')}", normal_style), Paragraph(f"<b>Data do Término:</b> {ac.get('data_termino', '')}", normal_style)],
        [Paragraph(f"<b>Usuário:</b> {ac.get('nome_usuario', '')}", normal_style), Paragraph(f"<b>Coordenador:</b> {ac.get('nome_coordenador', '')}", normal_style)],
        [Paragraph(f"<b>WhatsApp Usuário:</b> {ac.get('whatsapp_usuario', '')}", normal_style), Paragraph(f"<b>WhatsApp Coordenador:</b> {ac.get('whatsapp_coordenador', '')}", normal_style)],
        [Paragraph("<b>Assinatura Usuário:</b>", normal_style), Paragraph("<b>Assinatura Coordenador:</b>", normal_style)],
        [sig_u, sig_c]
    ]
    t_cli = Table(cliente_data, colWidths=[270, 270])
    t_cli.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_light), ('BOX', (0,0), (-1,-1), 0.8, border_color), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_cli)
    
    # Anexos Fotográficos com Legenda
    anexos = dados.get("anexos", [])
    if anexos:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Evidências Fotográficas", section_style))
        for idx, item in enumerate(anexos):
            try:
                foto_bytes = item.get("foto")
                legenda = item.get("legenda", f"Evidência {idx+1}")
                img_io = io.BytesIO(foto_bytes)
                rl_img = RLImage(img_io, width=400, height=250, kind='proportional')
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Evidência {idx+1}:</b> {legenda}", normal_style))
                story.append(Spacer(1, 4))
                story.append(rl_img)
            except Exception:
                pass

    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"Portal de Treinamentos &nbsp;&bull;&nbsp; Relatório gerado eletronicamente em {agora_str}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 7. GERAÇÃO, PRÉ-VISUALIZAÇÃO E WHATSAPP
# ==========================================
st.markdown("---")
if st.button("🚀 Validar, Salvar e Gerar PDF", type="primary", use_container_width=True):
    dados_val = modelo.to_dict()
    ig_val = dados_val["informacoes_gerais"]
    
    erros = []
    if not ig_val.get("entidade", "").strip():
        erros.append("O campo **Entidade** é obrigatório.")
    if not ig_val.get("nome_usuario", "").strip():
        erros.append("O campo **Nome do Usuário** é obrigatório.")
    if ig_val.get("email") and not validar_email(ig_val.get("email")):
        erros.append("O formato do **E-mail** informado é inválido.")
        
    if erros:
        for err in erros:
            st.error(err)
    else:
        try:
            conn = sqlite3.connect("relatorios.db", check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO historico (data_criacao, entidade, sistema, nome_usuario, dados_json) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    ig_val.get("entidade"),
                    ig_val.get("sistema"),
                    ig_val.get("nome_usuario"),
                    json.dumps(dados_val, default=str)
                )
            )
            conn.commit()
            conn.close()

            pdf_bytes = gerar_pdf_relatorio(dados_val)
            st.success("Relatório gerado e salvo com sucesso!")
            
            col_dl, col_wpp = st.columns(2)
            with col_dl:
                st.download_button(
                    label="📥 Baixar PDF Oficial",
                    data=pdf_bytes,
                    file_name=f"relatorio_{ig_val.get('entidade', 'atendimento').lower().replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col_wpp:
                wpp_num = re.sub(r'[^0-9]', '', ig_val.get('whatsapp', ''))
                if wpp_num:
                    msg = f"Olá, {ig_val.get('nome_usuario')}. Segue o resumo do atendimento presencial realizado na entidade {ig_val.get('entidade')} referente ao sistema {ig_val.get('sistema')}."
                    import urllib.parse
                    link_wpp = f"https://wa.me/55{wpp_num}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{link_wpp}" target="_blank"><button style="background-color:#25d366; color:white; border:none; border-radius:8px; padding:0.6rem 1.2rem; font-weight:600; width:100%; cursor:pointer;">💬 Enviar Resumo via WhatsApp</button></a>', unsafe_allow_html=True)

            st.markdown("### 👁️ Pré-visualização do Relatório Gerado")
            base64_pdf = io.BytesIO(pdf_bytes)
            import base64
            base64_encoded = base64.b64encode(base64_pdf.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_encoded}" width="100%" height="600px" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao processar relatório: {e}")
