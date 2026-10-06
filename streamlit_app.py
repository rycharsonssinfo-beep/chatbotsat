import io
import re
import json
import base64
import sqlite3
import os
import hashlib
import html
from pathlib import Path
from datetime import datetime, date
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas

# ==========================================
# CONFIGURAÇÕES DE PERSISTÊNCIA
# ==========================================
DB_PATH = "relatorios_ss.db"
BACKUP_DIR = Path("backups")
PDF_DIR = Path("pdfs")
BACKUP_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL MODERNO
# ==========================================
st.set_page_config(
    page_title="Relatório de Atendimento Presencial",
    page_icon="📋",
    layout="wide"
)

st.markdown("""
<style>
/* ============================================================
   PACOTE VISUAL 2 — identidade corporativa
   ============================================================ */
:root {
    --ss-navy: #0F172A;
    --ss-navy-2: #111C33;
    --ss-blue: #2563EB;
    --ss-blue-dark: #1D4ED8;
    --ss-blue-soft: #EFF6FF;
    --ss-bg: #F6F8FC;
    --ss-card: #FFFFFF;
    --ss-border: #E2E8F0;
    --ss-border-strong: #CBD5E1;
    --ss-text: #1E293B;
    --ss-muted: #64748B;
    --ss-success: #047857;
    --ss-success-bg: #ECFDF5;
    --ss-warning: #B45309;
    --ss-warning-bg: #FFFBEB;
    --ss-danger: #B91C1C;
    --ss-danger-bg: #FEF2F2;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(37,99,235,.055), transparent 25rem),
        var(--ss-bg);
    color: var(--ss-text);
}

[data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1420px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1324 0%, #101B31 100%);
    border-right: 1px solid rgba(255,255,255,.06);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #E2E8F0;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF;
    letter-spacing: -.02em;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,.09);
}

[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,.07);
    border-color: rgba(255,255,255,.13);
    color: #FFFFFF;
}

[data-testid="stSidebar"] .stTextInput input::placeholder {
    color: #94A3B8;
}

[data-testid="stSidebar"] .stExpander {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
}

/* Cabeçalho */
.ss-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #FBFDFF 70%, #F3F7FF 100%);
    border: 1px solid var(--ss-border);
    border-radius: 20px;
    padding: 22px 26px;
    box-shadow: 0 10px 35px rgba(15, 23, 42, .055);
    margin-bottom: 1rem;
}

.ss-hero-title {
    font-size: clamp(1.65rem, 2vw, 2.15rem);
    font-weight: 750;
    color: var(--ss-navy);
    letter-spacing: -.035em;
    line-height: 1.1;
    margin: 0;
}

.ss-hero-subtitle {
    color: var(--ss-muted);
    font-size: .92rem;
    margin-top: .45rem;
}

.ss-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    margin-top: .9rem;
}

.ss-pill {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    border: 1px solid var(--ss-border);
    border-radius: 999px;
    padding: .34rem .7rem;
    color: #475569;
    background: #FFFFFF;
    font-size: .78rem;
    font-weight: 650;
}

.ss-pill-blue {
    color: #1D4ED8;
    background: #EFF6FF;
    border-color: #BFDBFE;
}

.ss-pill-green {
    color: #047857;
    background: #ECFDF5;
    border-color: #A7F3D0;
}

/* Progress */
.ss-progress-card {
    background: #FFFFFF;
    border: 1px solid var(--ss-border);
    border-radius: 14px;
    padding: 13px 16px;
    margin: .65rem 0 1rem 0;
}

.ss-progress-head {
    display:flex;
    justify-content:space-between;
    gap:1rem;
    align-items:center;
    font-size:.82rem;
    font-weight:650;
    color:#475569;
    margin-bottom:.55rem;
}

.ss-progress-track {
    width:100%;
    height:7px;
    background:#E8EEF7;
    border-radius:999px;
    overflow:hidden;
}

.ss-progress-fill {
    height:100%;
    background: linear-gradient(90deg, #2563EB, #3B82F6);
    border-radius:999px;
}

/* Containers/cartões */
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background: rgba(255,255,255,.98);
    border-radius: 16px !important;
    padding: 22px !important;
    border: 1px solid var(--ss-border) !important;
    box-shadow: 0 6px 24px rgba(15,23,42,.035);
}

h1, h2, h3 {
    letter-spacing: -.025em;
}

[data-testid="stMarkdownContainer"] h3 {
    color: var(--ss-navy);
}

.ss-section-kicker {
    color: var(--ss-blue);
    font-size: .74rem;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: .2rem;
}

.ss-section-help {
    color: var(--ss-muted);
    font-size: .84rem;
    margin-top: -.25rem;
    margin-bottom: .75rem;
}

/* Campos */
.stTextInput input,
.stDateInput input,
.stTextArea textarea,
div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border-color: var(--ss-border-strong) !important;
    background: #FFFFFF !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stDateInput input:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.10) !important;
}

.stTextArea textarea {
    min-height: 105px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #E9EEF6;
    border-radius: 13px;
    padding: 4px;
    margin-bottom: .85rem;
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 10px;
    border: 0 !important;
    background: transparent;
    color: #64748B;
    font-size: .88rem;
    font-weight: 650;
    padding: 0 16px;
}

.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: var(--ss-navy) !important;
    box-shadow: 0 2px 8px rgba(15,23,42,.08);
}

/* Botões */
.stButton > button,
.stDownloadButton > button {
    border-radius: 10px !important;
    min-height: 42px;
    font-weight: 650 !important;
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 14px rgba(15,23,42,.08);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    border: 0 !important;
    box-shadow: 0 8px 20px rgba(37,99,235,.20);
}

/* Histórico */
.history-card {
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.10);
    padding: 11px 12px;
    border-radius: 11px;
    margin: 8px 0 6px 0;
    font-size: .80rem;
    line-height: 1.45;
    color: #CBD5E1;
}

.history-card b {
    color: #FFFFFF;
    font-size: .86rem;
}

/* Assinaturas */
.signature-badge {
    background: var(--ss-success-bg);
    color: var(--ss-success);
    padding: 6px 10px;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 700;
    display: inline-block;
    margin: 6px 0 10px 0;
    border: 1px solid #A7F3D0;
}

/* Evidências */
.ss-evidence-title {
    color: var(--ss-navy);
    font-size: .9rem;
    font-weight: 700;
    margin-bottom: .15rem;
}

.ss-evidence-caption {
    color: var(--ss-muted);
    font-size: .78rem;
}

/* Finalização */
.ss-finish-card {
    background: linear-gradient(135deg, #F8FBFF, #FFFFFF);
    border: 1px solid #DCE6F5;
    border-radius: 18px;
    padding: 20px 22px;
    margin: 1.25rem 0 .85rem 0;
}

.ss-finish-title {
    color: var(--ss-navy);
    font-size: 1.08rem;
    font-weight: 750;
    margin-bottom: .25rem;
}

.ss-finish-sub {
    color: var(--ss-muted);
    font-size: .84rem;
}

/* Status/alerts */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Preview PDF */
iframe {
    border: 1px solid var(--ss-border) !important;
    border-radius: 14px;
    background: #FFFFFF;
    box-shadow: 0 8px 28px rgba(15,23,42,.06);
}

/* Mobile */
@media (max-width: 900px) {
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-left: .85rem;
        padding-right: .85rem;
    }
    .ss-hero {
        padding: 18px;
        border-radius: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0 10px;
        font-size: .80rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. LOGO OFICIAL DO GRUPO S&S
# ==========================================
# A logo é embutida no código em Base64 para que funcione
# tanto localmente quanto no Streamlit Cloud, sem depender
# de acesso externo à imagem.
LOGO_BASE64 = """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"""

@st.cache_data
def obter_logo_bytes() -> bytes:
    return base64.b64decode(LOGO_BASE64)

LOGO_BYTES = obter_logo_bytes()


# ==========================================
# 3. BANCO DE DADOS E PERSISTÊNCIA
# ==========================================
def garantir_coluna(cursor, tabela: str, coluna: str, definicao: str):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = {row[1] for row in cursor.fetchall()}
    if coluna not in colunas:
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    garantir_coluna(cursor, "historico", "report_id", "TEXT")
    garantir_coluna(cursor, "historico", "content_hash", "TEXT")
    garantir_coluna(cursor, "historico", "status", "TEXT DEFAULT 'Finalizado'")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_historico_report_id ON historico(report_id) WHERE report_id IS NOT NULL")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_entidade ON historico(entidade)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_usuario ON historico(nome_usuario)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historico_hash ON historico(content_hash)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rascunho (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data_atualizacao TEXT,
            report_id TEXT,
            dados_json TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM sistemas")
    if cursor.fetchone()[0] == 0:
        padroes = [
            "Contabilidade", "Gestor", "Fluxus", "Folha de Pagamento", "Nota Fiscal Eletrônica",
            "Portal da Transparência", "SAT Web", "SAT WEB SPU", "SIG - Almoxarifado",
            "SIG - Doações", "SIG - Licitação", "SIG - Merenda", "SIG - Patrimônio",
            "SIG - PPA", "SigWeb - Almoxarifado", "SigWeb - Geral", "SigWeb - Orçamento",
            "SigWeb - PPA", "SigWeb - Social", "Licitação", "Veículos Web"
        ]
        for s in padroes:
            cursor.execute("INSERT OR IGNORE INTO sistemas (nome) VALUES (?)", (s,))
        conn.commit()

    # Migração/correção de nomenclatura em bancos já existentes
    cursor.execute(
        "UPDATE sistemas SET nome = ? WHERE LOWER(TRIM(nome)) = LOWER(TRIM(?))",
        ("Gestor", "Jestor")
    )
    conn.commit()
    conn.close()


init_db()


def carregar_sistemas_db() -> list:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM sistemas ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return ["Selecione o sistema..."] + [r[0] for r in rows] + ["Outros"]


def adicionar_sistema_db(novo_sistema: str) -> bool:
    if novo_sistema and novo_sistema.strip():
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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


def gerar_id_relatorio() -> str:
    ano = datetime.now().year
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(CAST(SUBSTR(report_id, 10) AS INTEGER)) FROM historico WHERE report_id LIKE ?",
        (f"RAT-{ano}-%",)
    )
    ultimo = cursor.fetchone()[0] or 0
    conn.close()
    return f"RAT-{ano}-{ultimo + 1:05d}"


def calcular_hash_conteudo(dados: dict) -> str:
    payload = json.dumps(dados, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def salvar_rascunho_db(dados: dict, report_id: str | None = None):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rascunho (id, data_atualizacao, report_id, dados_json)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            data_atualizacao = excluded.data_atualizacao,
            report_id = excluded.report_id,
            dados_json = excluded.dados_json
    """, (agora, report_id, json.dumps(dados, ensure_ascii=False, default=str)))
    conn.commit()
    conn.close()
    return agora


def carregar_rascunho_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT data_atualizacao, report_id, dados_json FROM rascunho WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    try:
        return {"data_atualizacao": row[0], "report_id": row[1], "dados": json.loads(row[2])}
    except Exception:
        return None


def excluir_rascunho_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("DELETE FROM rascunho WHERE id = 1")
    conn.commit()
    conn.close()


def backup_database(max_backups: int = 30) -> Path:
    nome = BACKUP_DIR / f"relatorios_ss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    origem = sqlite3.connect(DB_PATH, check_same_thread=False)
    destino = sqlite3.connect(str(nome))
    try:
        origem.backup(destino)
    finally:
        destino.close()
        origem.close()

    backups = sorted(BACKUP_DIR.glob("relatorios_ss_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for antigo in backups[max_backups:]:
        try:
            antigo.unlink()
        except OSError:
            pass
    return nome


def salvar_pdf_local(pdf_bytes: bytes, report_id: str, entidade: str) -> Path:
    nome_entidade = re.sub(r"[^A-Za-z0-9_-]+", "_", entidade.strip()).strip("_") or "atendimento"
    caminho = PDF_DIR / f"{report_id}_{nome_entidade}.pdf"
    caminho.write_bytes(pdf_bytes)
    return caminho


# ==========================================
# 4. AUXILIARES E MODELO DE DADOS
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
        self.report_id = None

    def to_dict(self) -> dict:
        d = {
            "informacoes_gerais": self.informacoes_gerais.copy(),
            "servico_executado": self.servico_executado,
            "resultado_atendimento": self.resultado_atendimento,
            "area_cliente": self.area_cliente.copy(),
            "anexos": []
        }
        d["informacoes_gerais"]["whatsapp"] = limpar_telefone(d["informacoes_gerais"].get("whatsapp", ""))
        d["area_cliente"]["whatsapp_usuario"] = limpar_telefone(d["area_cliente"].get("whatsapp_usuario", ""))
        d["area_cliente"]["whatsapp_coordenador"] = limpar_telefone(d["area_cliente"].get("whatsapp_coordenador", ""))

        if isinstance(d["informacoes_gerais"].get("data_visita"), date):
            d["informacoes_gerais"]["data_visita"] = d["informacoes_gerais"]["data_visita"].strftime("%d/%m/%Y")
        if isinstance(d["area_cliente"].get("data_termino"), date):
            d["area_cliente"]["data_termino"] = d["area_cliente"]["data_termino"].strftime("%d/%m/%Y")

        sig_u = self.area_cliente.get("assinatura_usuario")
        if isinstance(sig_u, bytes):
            d["area_cliente"]["assinatura_usuario"] = base64.b64encode(sig_u).decode('utf-8')
        
        sig_c = self.area_cliente.get("assinatura_coordenador")
        if isinstance(sig_c, bytes):
            d["area_cliente"]["assinatura_coordenador"] = base64.b64encode(sig_c).decode('utf-8')

        for item in self.anexos:
            foto_b = item.get("foto")
            foto_enc = base64.b64encode(foto_b).decode('utf-8') if isinstance(foto_b, bytes) else foto_b
            d["anexos"].append({"foto": foto_enc, "legenda": item.get("legenda", "")})

        d["_meta"] = {"report_id": self.report_id}
        return d


# ==========================================
# OTIMIZAÇÃO DE EVIDÊNCIAS FOTOGRÁFICAS
# ==========================================
def otimizar_foto(uploaded_file, max_dim=1600, qualidade=82) -> bytes:
    """Reduz fotos de celular mantendo boa qualidade para o relatório/PDF."""
    img = Image.open(uploaded_file)
    img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
    return buffer.getvalue()


# ==========================================
# 5. CAPTURA DE ASSINATURA
# ==========================================
def capturar_assinatura(titulo: str, key_prefix: str, modelo_ref, campo_modelo: str):
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        st.caption("Assine diretamente no quadro ou envie uma imagem da assinatura.")

        metodo = st.radio(
            "Forma de assinatura",
            ["Desenhar na Tela", "Enviar Imagem"],
            horizontal=True,
            key=f"metodo_{key_prefix}",
            label_visibility="collapsed"
        )

        if metodo == "Desenhar na Tela":
            canvas_result = st_canvas(
                fill_color="rgba(255,255,255,0)",
                stroke_width=2,
                stroke_color="#0F172A",
                background_color="#FFFFFF",
                height=170,
                width=420,
                drawing_mode="freedraw",
                update_streamlit=True,
                return_image_data=True,
                key=f"canvas_{key_prefix}"
            )

            c_salvar, c_limpar = st.columns(2)
            with c_salvar:
                salvar = st.button(
                    "Salvar assinatura",
                    key=f"btn_salvar_{key_prefix}",
                    use_container_width=True,
                    type="primary"
                )
            with c_limpar:
                limpar = st.button(
                    "Limpar assinatura",
                    key=f"btn_limpar_canvas_{key_prefix}",
                    use_container_width=True
                )

            if limpar:
                modelo_ref.area_cliente[campo_modelo] = None
                st.rerun()

            if salvar:
                if canvas_result is not None and canvas_result.image_data is not None:
                    try:
                        img_array = canvas_result.image_data
                        if img_array.any():
                            pil_img = Image.fromarray(img_array.astype("uint8"), mode="RGBA")
                            background = Image.new("RGB", pil_img.size, (255, 255, 255))
                            background.paste(pil_img, mask=pil_img.split()[3])
                            buf = io.BytesIO()
                            background.save(buf, format="PNG", optimize=True)
                            modelo_ref.area_cliente[campo_modelo] = buf.getvalue()
                            st.success("Assinatura registrada.")
                            st.rerun()
                        else:
                            st.warning("O quadro de assinatura está vazio.")
                    except Exception as e:
                        st.error(f"Erro ao capturar assinatura: {e}")
        else:
            uploaded_file = st.file_uploader(
                "Enviar imagem da assinatura",
                type=["png", "jpg", "jpeg"],
                key=f"upload_{key_prefix}"
            )
            if uploaded_file is not None:
                modelo_ref.area_cliente[campo_modelo] = uploaded_file.getvalue()
                st.success("Assinatura carregada.")

        sig_val = modelo_ref.area_cliente.get(campo_modelo)
        if sig_val:
            st.markdown('<div class="signature-badge">✓ Assinatura registrada</div>', unsafe_allow_html=True)
            try:
                sig_bytes = base64.b64decode(sig_val) if isinstance(sig_val, str) else sig_val
                st.image(sig_bytes, width=220)
                if st.button(
                    "Remover assinatura",
                    key=f"btn_remover_{key_prefix}",
                    use_container_width=False
                ):
                    modelo_ref.area_cliente[campo_modelo] = None
                    st.rerun()
            except Exception as e:
                st.warning(f"A assinatura foi registrada, mas não pôde ser pré-visualizada: {e}")


# ==========================================
# 6. SIDEBAR E GERENCIAMENTO
# ==========================================
def modelo_from_dict(dados_carregados: dict, report_id: str | None = None) -> RelatorioModel:
    novo_mod = RelatorioModel()
    novo_mod.report_id = report_id or dados_carregados.get("_meta", {}).get("report_id")
    novo_mod.informacoes_gerais = dados_carregados.get("informacoes_gerais", novo_mod.informacoes_gerais)

    data_v_str = novo_mod.informacoes_gerais.get("data_visita")
    if isinstance(data_v_str, str):
        try:
            novo_mod.informacoes_gerais["data_visita"] = datetime.strptime(data_v_str, "%d/%m/%Y").date()
        except ValueError:
            novo_mod.informacoes_gerais["data_visita"] = date.today()

    novo_mod.servico_executado = dados_carregados.get("servico_executado", novo_mod.servico_executado)
    novo_mod.resultado_atendimento = dados_carregados.get("resultado_atendimento", novo_mod.resultado_atendimento)
    novo_mod.area_cliente = dados_carregados.get("area_cliente", novo_mod.area_cliente)

    for campo_assinatura in ("assinatura_usuario", "assinatura_coordenador"):
        valor = novo_mod.area_cliente.get(campo_assinatura)
        if isinstance(valor, str):
            try:
                novo_mod.area_cliente[campo_assinatura] = base64.b64decode(valor)
            except Exception:
                novo_mod.area_cliente[campo_assinatura] = None

    data_t_str = novo_mod.area_cliente.get("data_termino")
    if isinstance(data_t_str, str):
        try:
            novo_mod.area_cliente["data_termino"] = datetime.strptime(data_t_str, "%d/%m/%Y").date()
        except ValueError:
            novo_mod.area_cliente["data_termino"] = date.today()

    anexos_raw = dados_carregados.get("anexos", [])
    novo_mod.anexos = []
    for item in anexos_raw:
        try:
            f_b64 = item.get("foto")
            f_bytes = base64.b64decode(f_b64) if isinstance(f_b64, str) else f_b64
            if f_bytes:
                novo_mod.anexos.append({"foto": f_bytes, "legenda": item.get("legenda", "")})
        except Exception:
            continue
    return novo_mod


if "relatorio_model" not in st.session_state:
    rascunho = carregar_rascunho_db()
    if rascunho and rascunho.get("dados"):
        st.session_state["relatorio_model"] = modelo_from_dict(rascunho["dados"], rascunho.get("report_id"))
        st.session_state["rascunho_recuperado"] = rascunho.get("data_atualizacao")
    else:
        st.session_state["relatorio_model"] = RelatorioModel()
    st.session_state["draft_hash"] = None
    st.session_state["last_draft_save"] = None

modelo = st.session_state["relatorio_model"]

with st.sidebar:
    st.markdown("## Painel de controle")
    st.caption("Relatórios, histórico e configurações.")

    if st.button("Novo relatório", use_container_width=True):
        excluir_rascunho_db()
        st.session_state["relatorio_model"] = RelatorioModel()
        st.session_state["draft_hash"] = None
        st.session_state["last_draft_save"] = None
        st.session_state.pop("rascunho_recuperado", None)
        st.rerun()

    if st.session_state.get("rascunho_recuperado"):
        st.info(f"Rascunho recuperado em {st.session_state['rascunho_recuperado']}")

    st.markdown("---")
    with st.expander("Cadastrar novo sistema"):
        novo_sis_input = st.text_input("Nome do Sistema", placeholder="Ex.: Novo Sistema...")
        if st.button("Adicionar sistema", use_container_width=True):
            if adicionar_sistema_db(novo_sis_input):
                st.success("Sistema adicionado.")
                st.rerun()
            else:
                st.warning("O sistema já existe ou o nome está vazio.")

    st.markdown("---")
    st.subheader("Histórico")
    termo_busca = st.text_input("Pesquisar relatórios", placeholder="Entidade, usuário, sistema ou ID...")

    try:
        conn_h = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor_h = conn_h.cursor()
        if termo_busca:
            cursor_h.execute("""
                SELECT id, data_criacao, entidade, sistema, nome_usuario, report_id, status, dados_json
                FROM historico
                WHERE entidade LIKE ? OR nome_usuario LIKE ? OR sistema LIKE ? OR report_id LIKE ?
                ORDER BY id DESC LIMIT 15
            """, (f"%{termo_busca}%", f"%{termo_busca}%", f"%{termo_busca}%", f"%{termo_busca}%"))
        else:
            cursor_h.execute("""
                SELECT id, data_criacao, entidade, sistema, nome_usuario, report_id, status, dados_json
                FROM historico ORDER BY id DESC LIMIT 10
            """)
        historico_rows = cursor_h.fetchall()
        conn_h.close()

        if historico_rows:
            for h_id, h_data, h_ent, h_sis, h_user, h_report_id, h_status, h_json in historico_rows:
                with st.container():
                    st.markdown(f"""
                    <div class="history-card">
                        <b>{h_ent}</b><br>
                        <small>{h_report_id or 'ID legado'}</small><br>
                        🛠️ {h_sis or 'N/D'}<br>
                        👤 {h_user} | 📅 {h_data}<br>
                        <small>● {h_status or 'Finalizado'}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Carregar", key=f"carregar_{h_id}", use_container_width=True):
                        try:
                            dados_carregados = json.loads(h_json)
                            st.session_state["relatorio_model"] = modelo_from_dict(dados_carregados, h_report_id)
                            st.session_state["draft_hash"] = None
                            st.session_state.pop("rascunho_recuperado", None)
                            st.success(f"Relatório {h_report_id or ''} carregado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao carregar: {e}")
                st.markdown("")
        else:
            st.markdown("<small style='color: #94a3b8;'>Nenhum registro encontrado.</small>", unsafe_allow_html=True)
    except Exception as e:
        st.markdown("<small style='color: #94a3b8;'>Não foi possível consultar o histórico.</small>", unsafe_allow_html=True)



# Cabeçalho principal e progresso visual
def calcular_estado_visual(modelo_ref):
    ig = modelo_ref.informacoes_gerais
    se = modelo_ref.servico_executado
    ra = modelo_ref.resultado_atendimento
    ac = modelo_ref.area_cliente

    info_ok = all([
        bool(ig.get("entidade", "").strip()),
        bool(ig.get("nome_usuario", "").strip()),
        bool(ig.get("sistema", "").strip()),
        bool(ig.get("responsavel_atendimento", "").strip())
    ])

    serv_ok = any(se.get(k) for k in ["implantacao", "treinamento", "demonstracao_sistema", "visita", "outros"])
    if se.get("visita") and not se.get("tipo_visita"):
        serv_ok = False

    result_ok = any(ra.get(k) for k in [
        "perfeito_funcionamento", "pendencias_posterior", "treinamento_sucesso",
        "pendencias_operador", "cartoes", "outros"
    ])

    cliente_ok = bool(ac.get("nome_usuario", "").strip()) and bool(ac.get("assinatura_usuario")) and bool(ac.get("assinatura_coordenador"))
    evid_ok = bool(modelo_ref.anexos)

    estados = [info_ok, serv_ok, result_ok, cliente_ok, evid_ok]
    concluidas = sum(1 for item in estados if item)
    percentual = int((concluidas / len(estados)) * 100)

    return {
        "info": info_ok,
        "serv": serv_ok,
        "result": result_ok,
        "cliente": cliente_ok,
        "evid": evid_ok,
        "concluidas": concluidas,
        "percentual": percentual
    }


estado_visual = calcular_estado_visual(modelo)
status_relatorio = "Finalizado" if st.session_state.get("ultimo_report_id") == modelo.report_id and modelo.report_id else "Rascunho"
status_class = "ss-pill-green" if status_relatorio == "Finalizado" else "ss-pill-blue"
id_exibicao = modelo.report_id or "Será criado automaticamente"
salvamento_exibicao = st.session_state.get("last_draft_save") or "Aguardando alterações"

col_logo, col_hero = st.columns([1.35, 4.65], vertical_alignment="center")
with col_logo:
    if LOGO_BYTES:
        st.image(LOGO_BYTES, width=260)

with col_hero:
    st.markdown(
        f"""
        <div class="ss-hero">
            <div class="ss-section-kicker">Atendimento técnico em campo</div>
            <div class="ss-hero-title">Relatório de Atendimento Presencial</div>
            <div class="ss-hero-subtitle">
                Registro operacional de serviços, resultados, assinaturas e evidências do atendimento.
            </div>
            <div class="ss-meta-row">
                <span class="ss-pill {status_class}">{status_relatorio}</span>
                <span class="ss-pill">ID: {html.escape(id_exibicao)}</span>
                <span class="ss-pill">Autosave: {html.escape(str(salvamento_exibicao))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    f"""
    <div class="ss-progress-card">
        <div class="ss-progress-head">
            <span>Progresso do preenchimento</span>
            <span>{estado_visual['concluidas']} de 5 etapas · {estado_visual['percentual']}%</span>
        </div>
        <div class="ss-progress-track">
            <div class="ss-progress-fill" style="width:{estado_visual['percentual']}%"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

marca = lambda ok: " ✓" if ok else ""
qtd_evid = len(modelo.anexos)
rotulo_evid = f"Evidências {qtd_evid}" if qtd_evid else "Evidências"

# Abas do formulário
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"Informações Gerais{marca(estado_visual['info'])}",
    f"Serviços{marca(estado_visual['serv'])}",
    f"Resultados{marca(estado_visual['result'])}",
    f"Área do Cliente{marca(estado_visual['cliente'])}",
    rotulo_evid
])

with tab1:
    with st.container(border=True):
        st.markdown("### Informações Gerais")
        st.caption("Dados da entidade, usuário e contexto do atendimento.")
        col1, col2 = st.columns(2)
        with col1:
            modelo.informacoes_gerais["entidade"] = st.text_input("Entidade (Prefeitura / Câmara / Consórcio...)*", value=modelo.informacoes_gerais["entidade"])
            
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
            raw_wpp = st.text_input("WhatsApp", value=modelo.informacoes_gerais["whatsapp"])
            modelo.informacoes_gerais["whatsapp"] = limpar_telefone(raw_wpp)

            modelo.informacoes_gerais["data_visita"] = st.date_input("Data da Visita", value=modelo.informacoes_gerais["data_visita"], format="DD/MM/YYYY")
            modelo.informacoes_gerais["responsavel_atendimento"] = st.text_input("Responsável pelo Atendimento", value=modelo.informacoes_gerais["responsavel_atendimento"])
            modelo.informacoes_gerais["periodo_atendimento"] = st.text_input("Período de Atendimento", value=modelo.informacoes_gerais["periodo_atendimento"])
            
            turno_map = {"M": 0, "T": 1, "N": 2}
            turno_atual = modelo.informacoes_gerais.get("turno", "M")
            turno_escolhido = st.radio("Turno", ["M — Manhã", "T — Tarde", "N — Noite"], index=turno_map.get(turno_atual, 0), horizontal=True)
            modelo.informacoes_gerais["turno"] = turno_escolhido[0]

        modelo.informacoes_gerais["descricao"] = st.text_area("Descrição do Atendimento", value=modelo.informacoes_gerais["descricao"])

with tab2:
    with st.container(border=True):
        st.markdown("### Registro do Serviço Executado")
        st.caption("Selecione os serviços realizados e registre observações relevantes.")
        c1, c2, c3 = st.columns(3)
        with c1:
            modelo.servico_executado["implantacao"] = st.checkbox("Implantação", value=modelo.servico_executado["implantacao"])
            modelo.servico_executado["treinamento"] = st.checkbox("Treinamento", value=modelo.servico_executado["treinamento"])
        with c2:
            modelo.servico_executado["demonstracao_sistema"] = st.checkbox("Demonstração de Sistema", value=modelo.servico_executado["demonstracao_sistema"])
            modelo.servico_executado["outros"] = st.checkbox("Outros (inserir nas observações)", value=modelo.servico_executado["outros"])
        with c3:
            modelo.servico_executado["visita"] = st.checkbox("Visita", value=modelo.servico_executado["visita"])

        if modelo.servico_executado["visita"]:
            st.markdown("##### Marque o tipo de visita:")
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
        st.markdown("### Resultado do Atendimento")
        st.caption("Registre como o atendimento foi concluído e eventuais pendências.")
        modelo.resultado_atendimento["perfeito_funcionamento"] = st.checkbox("O Sistema ficou em perfeito funcionamento, sem nenhuma pendência", value=modelo.resultado_atendimento["perfeito_funcionamento"])
        modelo.resultado_atendimento["pendencias_posterior"] = st.checkbox("Existem pendências para solução posterior (listar em observações)", value=modelo.resultado_atendimento["pendencias_posterior"])
        modelo.resultado_atendimento["treinamento_sucesso"] = st.checkbox("Treinamento efetuado com sucesso", value=modelo.resultado_atendimento["treinamento_sucesso"])
        modelo.resultado_atendimento["pendencias_operador"] = st.checkbox("Existem pendências para que o operador/chefe do setor solucione depois", value=modelo.resultado_atendimento["pendencias_operador"])
        modelo.resultado_atendimento["cartoes"] = st.checkbox("Existem cartões (listar em observações)", value=modelo.resultado_atendimento["cartoes"])
        modelo.resultado_atendimento["outros"] = st.checkbox("Outros", value=modelo.resultado_atendimento["outros"])
        
        modelo.resultado_atendimento["observacoes"] = st.text_area("Observações do Resultado", value=modelo.resultado_atendimento["observacoes"])

with tab4:
    with st.container(border=True):
        st.markdown("### Área do Cliente")
        st.caption("Dados de validação do usuário e do coordenador do setor.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Usuário")
            modelo.area_cliente["local"] = st.text_input("Local (Ex: Jaguaribe-ce)", value=modelo.area_cliente["local"])
            modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário", value=modelo.area_cliente["nome_usuario"])
            raw_wpp_u = st.text_input("WhatsApp do Usuário", value=modelo.area_cliente["whatsapp_usuario"])
            modelo.area_cliente["whatsapp_usuario"] = limpar_telefone(raw_wpp_u)
            capturar_assinatura("Assinatura do Usuário", "usuario", modelo, "assinatura_usuario")
        with col_c2:
            st.markdown("#### Coordenador do Setor")
            modelo.area_cliente["data_termino"] = st.date_input("Data do término do serviço", value=modelo.area_cliente["data_termino"], format="DD/MM/YYYY")
            modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador do setor", value=modelo.area_cliente["nome_coordenador"])
            raw_wpp_c = st.text_input("WhatsApp do Coordenador do setor", value=modelo.area_cliente["whatsapp_coordenador"])
            modelo.area_cliente["whatsapp_coordenador"] = limpar_telefone(raw_wpp_c)
            capturar_assinatura("Assinatura Coordenador", "coordenador", modelo, "assinatura_coordenador")

with tab5:
    with st.container(border=True):
        st.markdown("### Evidências Fotográficas")
        st.caption("Adicione imagens que comprovem ou contextualizem o atendimento realizado.")

        uploaded_photos = st.file_uploader(
            "Enviar imagens de evidência",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="As imagens são otimizadas automaticamente para reduzir o tamanho do relatório."
        )

        if uploaded_photos:
            if len(uploaded_photos) > 12:
                st.error("Limite de 12 evidências por relatório. Remova algumas imagens para continuar.")
            else:
                novos_anexos = []
                for idx, p in enumerate(uploaded_photos):
                    try:
                        foto_otimizada = otimizar_foto(p)
                        legenda_atual = modelo.anexos[idx].get("legenda", "") if idx < len(modelo.anexos) else ""

                        if idx % 2 == 0:
                            grid_cols = st.columns(2, gap="medium")

                        with grid_cols[idx % 2]:
                            with st.container(border=True):
                                st.markdown(f'<div class="ss-evidence-title">Evidência {idx + 1}</div>', unsafe_allow_html=True)
                                st.caption(p.name)
                                st.image(foto_otimizada, width=300)
                                tamanho_kb = len(foto_otimizada) / 1024
                                st.markdown(
                                    f'<div class="ss-evidence-caption">Imagem otimizada · {tamanho_kb:.0f} KB</div>',
                                    unsafe_allow_html=True
                                )
                                legenda = st.text_input(
                                    "Legenda",
                                    key=f"legenda_foto_{idx}",
                                    value=legenda_atual,
                                    placeholder="Descreva o que a imagem registra..."
                                )
                        novos_anexos.append({"foto": foto_otimizada, "legenda": legenda})
                    except Exception as e:
                        st.error(f"Não foi possível processar a imagem {p.name}: {e}")
                modelo.anexos = novos_anexos

        elif modelo.anexos:
            st.markdown(f"**{len(modelo.anexos)} evidência(s) registrada(s)**")
            for idx, item in enumerate(modelo.anexos):
                if idx % 2 == 0:
                    saved_cols = st.columns(2, gap="medium")
                with saved_cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f'<div class="ss-evidence-title">Evidência {idx + 1}</div>', unsafe_allow_html=True)
                        st.image(item.get("foto"), width=300)
                        st.caption(item.get("legenda") or "Sem legenda")


# ==========================================
# 7. GERAÇÃO DO PDF PROFISSIONAL
# ==========================================
def gerar_pdf_relatorio(dados: dict) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=34,
        leftMargin=34,
        topMargin=28,
        bottomMargin=44,
        title="Relatório de Atendimento Presencial",
        author="Grupo S&S"
    )

    story = []
    meta = dados.get("_meta", {})
    report_id = meta.get("report_id") or "RAT-NÃO-IDENTIFICADO"
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    ig = dados.get("informacoes_gerais", {})
    se = dados.get("servico_executado", {})
    ra = dados.get("resultado_atendimento", {})
    ac = dados.get("area_cliente", {})
    anexos = dados.get("anexos", [])

    # Paleta institucional
    navy = colors.HexColor("#0F172A")
    blue = colors.HexColor("#2563EB")
    blue_soft = colors.HexColor("#EFF6FF")
    border = colors.HexColor("#E2E8F0")
    border_strong = colors.HexColor("#CBD5E1")
    bg = colors.HexColor("#F8FAFC")
    text = colors.HexColor("#1E293B")
    muted = colors.HexColor("#64748B")
    white = colors.white

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16.5,
        leading=19,
        textColor=navy,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "PDFSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=11,
        textColor=muted
    )
    section_title_style = ParagraphStyle(
        "PDFSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=navy,
        spaceBefore=10,
        spaceAfter=5
    )
    normal_style = ParagraphStyle(
        "PDFNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=text
    )
    label_style = ParagraphStyle(
        "PDFLabel",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9,
        textColor=muted,
        spaceAfter=2
    )
    value_style = ParagraphStyle(
        "PDFValue",
        parent=normal_style,
        fontName="Helvetica",
        fontSize=8.7,
        leading=11,
        textColor=text
    )
    caption_style = ParagraphStyle(
        "PDFCaption",
        parent=normal_style,
        fontSize=7.5,
        leading=9.5,
        textColor=muted,
        alignment=1
    )
    signature_name_style = ParagraphStyle(
        "PDFSignatureName",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10,
        alignment=1,
        textColor=navy
    )
    signature_role_style = ParagraphStyle(
        "PDFSignatureRole",
        parent=normal_style,
        fontSize=7.3,
        leading=9,
        alignment=1,
        textColor=muted
    )

    def esc(valor, vazio="—"):
        if valor is None or valor == "":
            valor = vazio
        return html.escape(str(valor)).replace("\n", "<br/>")

    def section_header(titulo):
        linha = Table(
            [[Paragraph(esc(titulo), section_title_style), ""]],
            colWidths=[220, 320]
        )
        linha.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.9, border_strong),
            ("LINEBELOW", (0, 0), (0, 0), 2.2, blue),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        return linha

    def campo(label, valor):
        return [
            Paragraph(esc(label).upper(), label_style),
            Paragraph(esc(valor), value_style)
        ]

    def tabela_campos(linhas):
        tabela = Table(linhas, colWidths=[270, 270])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), white),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ]))
        return tabela

    def box_texto(label, valor):
        conteudo = [
            Paragraph(esc(label).upper(), label_style),
            Spacer(1, 2),
            Paragraph(esc(valor, "Nenhuma informação registrada."), value_style)
        ]
        t = Table([[conteudo]], colWidths=[540])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ]))
        return t

    def checklist(itens):
        rows = []
        for marcado, texto_item in itens:
            mark = Paragraph("<b>X</b>" if marcado else "", normal_style)
            box = Table([[mark]], colWidths=[14], rowHeights=[14])
            box.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, blue if marcado else border_strong),
                ("BACKGROUND", (0, 0), (-1, -1), blue_soft if marcado else white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            rows.append([box, Paragraph(esc(texto_item), value_style)])

        t = Table(rows, colWidths=[24, 516])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    # Cabeçalho institucional
    if LOGO_BYTES:
        logo_pdf = RLImage(io.BytesIO(LOGO_BYTES), width=176, height=46, kind="proportional")
    else:
        logo_pdf = Paragraph("<b>GRUPO S&S</b>", title_style)

    header_text = [
        Paragraph("RELATÓRIO DE ATENDIMENTO PRESENCIAL", title_style),
        Paragraph("Registro técnico de atendimento em campo", subtitle_style),
        Spacer(1, 4),
        Paragraph(f"<b>{esc(report_id)}</b>", subtitle_style)
    ]

    header = Table([[logo_pdf, header_text]], colWidths=[190, 350])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), 1.1, navy),
    ]))
    story.append(header)
    story.append(Spacer(1, 9))

    # Metadados de leitura rápida
    meta_cells = [
        campo("Relatório", report_id),
        campo("Data da visita", ig.get("data_visita", "")),
        campo("Sistema", ig.get("sistema", "")),
        campo("Responsável", ig.get("responsavel_atendimento", "")),
    ]
    meta_table = Table([meta_cells], colWidths=[135, 135, 135, 135])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), blue_soft),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BFDBFE")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DBEAFE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)

    # Informações gerais
    story.append(section_header("Informações Gerais"))
    info_rows = [
        [campo("Entidade", ig.get("entidade", "")), campo("Sistema", ig.get("sistema", ""))],
        [campo("Setor", ig.get("setor", "")), campo("Data da visita", ig.get("data_visita", ""))],
        [campo("Nome do usuário", ig.get("nome_usuario", "")), campo("WhatsApp", ig.get("whatsapp", ""))],
        [campo("E-mail", ig.get("email", "")), campo("Responsável pelo atendimento", ig.get("responsavel_atendimento", ""))],
        [campo("Período", ig.get("periodo_atendimento", "")), campo("Turno", {"M": "Manhã", "T": "Tarde", "N": "Noite"}.get(ig.get("turno"), ig.get("turno", "")))]
    ]
    story.append(tabela_campos(info_rows))
    story.append(Spacer(1, 5))
    story.append(box_texto("Descrição do atendimento", ig.get("descricao", "")))

    # Serviço executado
    story.append(section_header("Registro do Serviço Executado"))
    story.append(checklist([
        (se.get("implantacao"), "Implantação"),
        (se.get("treinamento"), "Treinamento"),
        (se.get("demonstracao_sistema"), "Demonstração de Sistema"),
        (se.get("visita"), "Visita"),
        (se.get("outros"), "Outros")
    ]))

    if se.get("visita"):
        tipos = se.get("tipo_visita", [])
        story.append(Spacer(1, 3))
        story.append(checklist([
            ("Relacionamento Técnica" in tipos, "Relacionamento Técnica"),
            ("Técnica Preventiva" in tipos, "Técnica Preventiva")
        ]))

    story.append(Spacer(1, 4))
    story.append(box_texto("Observações sobre o serviço", se.get("observacoes", "")))

    # Resultado
    story.append(section_header("Resultado do Atendimento"))
    story.append(checklist([
        (ra.get("perfeito_funcionamento"), "O sistema ficou em perfeito funcionamento, sem nenhuma pendência"),
        (ra.get("pendencias_posterior"), "Existem pendências para solução posterior"),
        (ra.get("treinamento_sucesso"), "Treinamento efetuado com sucesso"),
        (ra.get("pendencias_operador"), "Existem pendências para que o operador/chefe do setor solucione depois"),
        (ra.get("cartoes"), "Existem cartões"),
        (ra.get("outros"), "Outros")
    ]))
    story.append(Spacer(1, 4))
    story.append(box_texto("Observações do resultado", ra.get("observacoes", "")))

    # Área do cliente
    story.append(section_header("Área do Cliente"))
    cliente_rows = [
        [campo("Local", ac.get("local", "")), campo("Data do término", ac.get("data_termino", ""))],
        [campo("Nome do usuário", ac.get("nome_usuario", "")), campo("Coordenador do setor", ac.get("nome_coordenador", ""))],
        [campo("WhatsApp do usuário", ac.get("whatsapp_usuario", "")), campo("WhatsApp do coordenador", ac.get("whatsapp_coordenador", ""))]
    ]
    story.append(tabela_campos(cliente_rows))
    story.append(Spacer(1, 10))

    def assinatura_flowable(valor, nome, funcao):
        elementos = [Spacer(1, 4)]
        if valor:
            try:
                sig_bytes = base64.b64decode(valor) if isinstance(valor, str) else valor
                elementos.append(RLImage(io.BytesIO(sig_bytes), width=140, height=48, kind="proportional"))
            except Exception:
                elementos.append(Paragraph("<i>Assinatura indisponível</i>", caption_style))
        else:
            elementos.append(Spacer(1, 48))

        elementos.extend([
            Spacer(1, 4),
            Table([[""]], colWidths=[210], rowHeights=[1], style=TableStyle([
                ("LINEABOVE", (0, 0), (-1, -1), 0.7, border_strong)
            ])),
            Paragraph(esc(nome, "Nome não informado"), signature_name_style),
            Paragraph(esc(funcao), signature_role_style)
        ])
        return elementos

    ass_table = Table(
        [[
            assinatura_flowable(ac.get("assinatura_usuario"), ac.get("nome_usuario"), "Usuário / responsável local"),
            assinatura_flowable(ac.get("assinatura_coordenador"), ac.get("nome_coordenador"), "Coordenador do setor")
        ]],
        colWidths=[270, 270]
    )
    ass_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether(ass_table))

    # Evidências em grade
    if anexos:
        story.append(section_header("Evidências Fotográficas"))

        cards = []
        for idx, item in enumerate(anexos):
            try:
                foto_val = item.get("foto")
                foto_bytes = base64.b64decode(foto_val) if isinstance(foto_val, str) else foto_val
                img_pil = Image.open(io.BytesIO(foto_bytes)).convert("RGB")

                max_w, max_h = 238, 155
                ratio = min(max_w / img_pil.width, max_h / img_pil.height, 1)
                img_w = img_pil.width * ratio
                img_h = img_pil.height * ratio

                img = RLImage(io.BytesIO(foto_bytes), width=img_w, height=img_h)
                legenda = item.get("legenda") or "Sem legenda"

                card = Table(
                    [[img], [Paragraph(f"<b>Evidência {idx + 1}</b><br/>{esc(legenda)}", caption_style)]],
                    colWidths=[252]
                )
                card.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.6, border),
                    ("BACKGROUND", (0, 0), (-1, -1), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (0, 0), 7),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 6),
                    ("TOPPADDING", (0, 1), (0, 1), 6),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]))
                cards.append(card)
            except Exception:
                cards.append(
                    Table([[Paragraph(f"Evidência {idx + 1}: imagem indisponível.", caption_style)]], colWidths=[252])
                )

        for i in range(0, len(cards), 2):
            linha = cards[i:i+2]
            if len(linha) == 1:
                linha.append("")
            grade = Table([linha], colWidths=[270, 270])
            grade.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(KeepTogether(grade))

    # Canvas customizado com "Página X de Y"
    class NumberedCanvas(pdfcanvas.Canvas):
        def __init__(self, *args, **kwargs):
            pdfcanvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_footer(total)
                pdfcanvas.Canvas.showPage(self)
            pdfcanvas.Canvas.save(self)

        def _draw_footer(self, total_pages):
            largura, _ = letter
            self.saveState()
            self.setStrokeColor(border)
            self.setLineWidth(0.45)
            self.line(34, 31, largura - 34, 31)

            self.setFont("Helvetica", 7)
            self.setFillColor(muted)
            self.drawString(34, 18, "Grupo S&S")
            self.drawCentredString(largura / 2, 18, report_id)
            self.drawRightString(largura - 34, 18, f"Página {self._pageNumber} de {total_pages}")

            self.setFont("Helvetica", 6.5)
            self.drawString(34, 9, f"Documento gerado eletronicamente em {agora_str}")
            self.restoreState()

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 8. AUTOSAVE, VALIDAÇÃO, GERAÇÃO E PRÉ-VISUALIZAÇÃO
# ==========================================
def tem_conteudo_para_rascunho(dados: dict) -> bool:
    ig = dados.get("informacoes_gerais", {})
    ac = dados.get("area_cliente", {})
    return any([
        ig.get("entidade", "").strip(),
        ig.get("nome_usuario", "").strip(),
        ig.get("descricao", "").strip(),
        ig.get("sistema", "").strip(),
        ig.get("responsavel_atendimento", "").strip(),
        dados.get("anexos"),
        ac.get("assinatura_usuario"),
        ac.get("assinatura_coordenador")
    ])


def validar_relatorio(dados: dict):
    ig = dados.get("informacoes_gerais", {})
    se = dados.get("servico_executado", {})
    ra = dados.get("resultado_atendimento", {})
    erros = []
    avisos = []

    if not ig.get("entidade", "").strip():
        erros.append("O campo **Entidade** é obrigatório.")
    if not ig.get("nome_usuario", "").strip():
        erros.append("O campo **Nome do Usuário** é obrigatório.")
    if not ig.get("sistema", "").strip():
        erros.append("Selecione o **Sistema** atendido.")
    if not ig.get("responsavel_atendimento", "").strip():
        erros.append("Informe o **Responsável pelo Atendimento**.")
    if ig.get("email") and not validar_email(ig.get("email")):
        erros.append("O formato do **E-mail** informado é inválido.")

    servicos_marcados = any(se.get(k) for k in ["implantacao", "treinamento", "demonstracao_sistema", "visita", "outros"])
    if not servicos_marcados:
        erros.append("Marque pelo menos um item em **Serviço Executado**.")
    if se.get("visita") and not se.get("tipo_visita"):
        erros.append("Ao marcar **Visita**, informe pelo menos um tipo de visita.")
    if se.get("outros") and not se.get("observacoes", "").strip():
        avisos.append("Foi marcado **Outros** em Serviço Executado, mas as observações estão vazias.")

    resultados_marcados = any(ra.get(k) for k in ["perfeito_funcionamento", "pendencias_posterior", "treinamento_sucesso", "pendencias_operador", "cartoes", "outros"])
    if not resultados_marcados:
        erros.append("Informe pelo menos um **Resultado do Atendimento**.")
    if any(ra.get(k) for k in ["pendencias_posterior", "pendencias_operador", "cartoes", "outros"]) and not ra.get("observacoes", "").strip():
        avisos.append("Há um resultado que pede detalhamento, mas as **Observações do Resultado** estão vazias.")

    if not dados.get("area_cliente", {}).get("nome_usuario", "").strip():
        avisos.append("O nome do usuário na **Área do Cliente** ainda não foi informado.")
    if not dados.get("area_cliente", {}).get("assinatura_usuario"):
        avisos.append("A **assinatura do usuário** ainda não foi registrada.")
    if not dados.get("area_cliente", {}).get("assinatura_coordenador"):
        avisos.append("A **assinatura do coordenador** ainda não foi registrada.")

    return erros, avisos


# Autosave: grava somente quando o conteúdo realmente mudou.
dados_atuais = modelo.to_dict()
if tem_conteudo_para_rascunho(dados_atuais):
    hash_atual = calcular_hash_conteudo(dados_atuais)
    if hash_atual != st.session_state.get("draft_hash"):
        try:
            if not modelo.report_id:
                modelo.report_id = gerar_id_relatorio()
                dados_atuais = modelo.to_dict()
                hash_atual = calcular_hash_conteudo(dados_atuais)
            salvo_em = salvar_rascunho_db(dados_atuais, modelo.report_id)
            st.session_state["draft_hash"] = hash_atual
            st.session_state["last_draft_save"] = salvo_em
        except Exception as e:
            st.session_state["last_draft_error"] = str(e)

if st.session_state.get("last_draft_save"):
    st.markdown(
        f"<div style='text-align:right; color:#64748b; font-size:.78rem; margin-top:.45rem;'>"
        f"✓ Alterações salvas automaticamente às {st.session_state['last_draft_save']}</div>",
        unsafe_allow_html=True
    )
if st.session_state.get("last_draft_error"):
    st.warning(f"O preenchimento continua normalmente, mas o rascunho não pôde ser salvo: {st.session_state['last_draft_error']}")

st.markdown(
    """
    <div class="ss-finish-card">
        <div class="ss-finish-title">Finalizar relatório</div>
        <div class="ss-finish-sub">
            O sistema validará os dados, salvará o histórico, criará o backup e emitirá o PDF oficial.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
if st.button("Validar, salvar e gerar PDF", type="primary", use_container_width=True):
    dados_val = modelo.to_dict()
    erros, avisos = validar_relatorio(dados_val)

    if erros:
        st.error("O relatório precisa de alguns ajustes antes da geração:")
        for err in erros:
            st.error(err)
    else:
        for aviso in avisos:
            st.warning(aviso)

        try:
            # Garante identificação única mesmo em relatórios antigos.
            if not modelo.report_id:
                modelo.report_id = gerar_id_relatorio()
            dados_val = modelo.to_dict()
            dados_val["_meta"] = {
                "report_id": modelo.report_id,
                "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            content_hash = calcular_hash_conteudo({k: v for k, v in dados_val.items() if k != "_meta"})

            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT report_id FROM historico WHERE content_hash = ? ORDER BY id DESC LIMIT 1", (content_hash,))
            duplicado = cursor.fetchone()

            if duplicado and duplicado[0] != modelo.report_id:
                conn.close()
                st.warning(f"Este conteúdo já foi registrado no relatório **{duplicado[0]}**. A geração duplicada foi evitada.")
            else:
                pdf_bytes = gerar_pdf_relatorio(dados_val)
                agora_db = datetime.now().strftime("%d/%m/%Y %H:%M")
                dados_json = json.dumps(dados_val, ensure_ascii=False, default=str)

                cursor.execute("SELECT id FROM historico WHERE report_id = ?", (modelo.report_id,))
                registro_existente = cursor.fetchone()
                if registro_existente:
                    cursor.execute("""
                        UPDATE historico
                        SET data_criacao = ?, entidade = ?, sistema = ?, nome_usuario = ?, dados_json = ?, content_hash = ?, status = 'Finalizado'
                        WHERE report_id = ?
                    """, (
                        agora_db,
                        dados_val["informacoes_gerais"].get("entidade"),
                        dados_val["informacoes_gerais"].get("sistema"),
                        dados_val["informacoes_gerais"].get("nome_usuario"),
                        dados_json,
                        content_hash,
                        modelo.report_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO historico (data_criacao, entidade, sistema, nome_usuario, dados_json, report_id, content_hash, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Finalizado')
                    """, (
                        agora_db,
                        dados_val["informacoes_gerais"].get("entidade"),
                        dados_val["informacoes_gerais"].get("sistema"),
                        dados_val["informacoes_gerais"].get("nome_usuario"),
                        dados_json,
                        modelo.report_id,
                        content_hash
                    ))
                conn.commit()
                conn.close()

                pdf_path = salvar_pdf_local(
                    pdf_bytes,
                    modelo.report_id,
                    dados_val["informacoes_gerais"].get("entidade", "atendimento")
                )
                excluir_rascunho_db()
                backup_path = backup_database()
                st.session_state["draft_hash"] = None
                st.session_state["last_draft_save"] = None
                st.session_state.pop("rascunho_recuperado", None)
                st.session_state["last_draft_error"] = None
                st.session_state["ultimo_pdf"] = pdf_bytes
                st.session_state["ultimo_report_id"] = modelo.report_id

                st.success(f"Relatório **{modelo.report_id}** gerado, salvo e protegido contra duplicidade.")
                st.caption(f"PDF local: `{pdf_path}` • Backup do banco: `{backup_path}`")

                col_dl, col_wpp = st.columns(2)
                with col_dl:
                    nome_entidade = re.sub(r"[^A-Za-z0-9_-]+", "_", dados_val["informacoes_gerais"].get("entidade", "atendimento").strip()).strip("_") or "atendimento"
                    st.download_button(
                        label="Baixar PDF oficial",
                        data=pdf_bytes,
                        file_name=f"{modelo.report_id}_{nome_entidade}_{datetime.now().strftime('%d-%m-%Y')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col_wpp:
                    wpp_num = re.sub(r'[^0-9]', '', dados_val["informacoes_gerais"].get('whatsapp', ''))
                    if wpp_num:
                        msg = f"Olá, {dados_val['informacoes_gerais'].get('nome_usuario')}. Segue o resumo do atendimento presencial realizado no Grupo S&S para a entidade {dados_val['informacoes_gerais'].get('entidade')}. Relatório {modelo.report_id}."
                        import urllib.parse
                        link_wpp = f"https://wa.me/55{wpp_num}?text={urllib.parse.quote(msg)}"
                        st.markdown(f'<a href="{link_wpp}" target="_blank"><button style="background-color:#25d366; color:white; border:none; border-radius:8px; padding:0.6rem 1.2rem; font-weight:600; width:100%; cursor:pointer;">Enviar resumo via WhatsApp</button></a>', unsafe_allow_html=True)

                st.markdown("### Pré-visualização do relatório")
                base64_pdf = io.BytesIO(pdf_bytes)
                base64_encoded = base64.b64encode(base64_pdf.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_encoded}" width="100%" height="600px" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao processar relatório: {e}")

