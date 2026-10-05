import io
import re
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
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #1b5ef7;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #1446c2;
        color: white;
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
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. FUNÇÃO AUXILIAR DE VALIDAÇÃO DE TELEFONE
# ==========================================
def limpar_telefone(texto: str) -> str:
    """Remove caracteres indesejados, permitindo apenas números e símbolos comuns de telefone."""
    if not texto:
        return ""
    return re.sub(r'[^0-9\s\(\)\-\+]', '', texto)


# ==========================================
# 3. MODELO DE DADOS
# ==========================================
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

    def to_dict(self) -> dict:
        d = {
            "informacoes_gerais": self.informacoes_gerais.copy(),
            "servico_executado": self.servico_executado,
            "resultado_atendimento": self.resultado_atendimento,
            "area_cliente": self.area_cliente.copy()
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
# 4. COMPONENTE DE ASSINATURA SEGURO E PERSISTENTE
# ==========================================
def capturar_assinatura(titulo: str, key_prefix: str, modelo_ref, campo_modelo: str):
    st.markdown(f"**{titulo}**")
    
    metodo = st.radio(
        f"Método ({titulo})", 
        ["Desenhar na Tela", "Enviar Imagem"], 
        horizontal=True, 
        key=f"metodo_{key_prefix}"
    )
    
    if metodo == "Desenhar na Tela":
        st.markdown(f"<small style='color: #64748b;'>Desenhe a assinatura abaixo:</small>", unsafe_allow_html=True)
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=130,
            width=350,
            drawing_mode="freedraw",
            key=f"canvas_{key_prefix}"
        )
        
        if canvas_result is not None and canvas_result.image_data is not None:
            img_array = canvas_result.image_data
            if img_array.any():
                pil_img = Image.fromarray(img_array.astype("uint8"), mode="RGBA")
                background = Image.new("RGB", pil_img.size, (255, 255, 255))
                background.paste(pil_img, mask=pil_img.split()[3])
                
                buf = io.BytesIO()
                background.save(buf, format="PNG")
                modelo_ref.area_cliente[campo_modelo] = buf.getvalue()
    else:
        uploaded_file = st.file_uploader(f"Enviar arquivo da assinatura ({titulo})", type=["png", "jpg", "jpeg"], key=f"upload_{key_prefix}")
        if uploaded_file is not None:
            modelo_ref.area_cliente[campo_modelo] = uploaded_file.getvalue()

    # Exibe a prévia imediatamente se já estiver gravado no modelo
    if modelo_ref.area_cliente[campo_modelo]:
        st.success(f"Assinatura de {titulo.lower()} registrada!")
        st.image(modelo_ref.area_cliente[campo_modelo], width=180, caption=f"Prévia - {titulo}")


# ==========================================
# 5. APLICAÇÃO PRINCIPAL
# ==========================================
st.title("📋 Relatório de Atendimento Presencial")
st.markdown("Preencha as abas abaixo para registrar o atendimento técnico e gerar o documento oficial.")

if "relatorio_model" not in st.session_state:
    st.session_state["relatorio_model"] = RelatorioModel()

modelo = st.session_state["relatorio_model"]

with st.sidebar:
    st.header("Navegação")
    st.markdown("---")
    if st.button("🔄 Novo Relatório (Limpar)", use_container_width=True):
        st.session_state["relatorio_model"] = RelatorioModel()
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Informações Gerais", 
    "⚙️ Serviços Executados", 
    "📊 Resultado", 
    "✍️ Área do Cliente"
])

with tab1:
    with st.container(border=True):
        st.subheader("Dados Principais e Contato")
        col1, col2 = st.columns(2)
        with col1:
            modelo.informacoes_gerais["entidade"] = st.text_input("Entidade (Prefeitura / Câmara / Consórcio...)*", value=modelo.informacoes_gerais["entidade"])
            modelo.informacoes_gerais["sistema"] = st.text_input("Sistema", value=modelo.informacoes_gerais["sistema"])
            modelo.informacoes_gerais["setor"] = st.text_input("Setor", value=modelo.informacoes_gerais["setor"])
            modelo.informacoes_gerais["nome_usuario"] = st.text_input("Nome do Usuário*", value=modelo.informacoes_gerais["nome_usuario"])
            modelo.informacoes_gerais["email"] = st.text_input("E-mail", value=modelo.informacoes_gerais["email"])
        with col2:
            raw_wpp = st.text_input("WhatsApp (Ex: (XX) 9XXXX-XXXX)", value=modelo.informacoes_gerais["whatsapp"])
            modelo.informacoes_gerais["whatsapp"] = limpar_telefone(raw_wpp)

            modelo.informacoes_gerais["data_visita"] = st.date_input("Data da Visita", value=modelo.informacoes_gerais["data_visita"])
            modelo.informacoes_gerais["responsavel_atendimento"] = st.text_input("Responsável pelo Atendimento", value=modelo.informacoes_gerais["responsavel_atendimento"])
            modelo.informacoes_gerais["periodo_atendimento"] = st.text_input("Período de Atendimento", value=modelo.informacoes_gerais["periodo_atendimento"])
            
            turno_map = {"M": 0, "T": 1, "N": 2}
            turno_atual = modelo.informacoes_gerais.get("turno", "M")
            turno_escolhido = st.radio("Turno", ["M — Manhã", "T — Tarde", "N — Noite"], index=turno_map.get(turno_atual, 0), horizontal=True)
            modelo.informacoes_gerais["turno"] = turno_escolhido[0]

        modelo.informacoes_gerais["descricao"] = st.text_area("Descrição Detalhada do Atendimento", value=modelo.informacoes_gerais["descricao"])

with tab2:
    with st.container(border=True):
        st.subheader("Registro do Serviço Executado")
        col3, col4, col5 = st.columns(3)
        with col3:
            modelo.servico_executado["implantacao"] = st.checkbox("Implantação", value=modelo.servico_executado["implantacao"])
            modelo.servico_executado["treinamento"] = st.checkbox("Treinamento", value=modelo.servico_executado["treinamento"])
        with col4:
            modelo.servico_executado["demonstracao_sistema"] = st.checkbox("Demonstração de Sistema", value=modelo.servico_executado["demonstracao_sistema"])
            modelo.servico_executado["outros"] = st.checkbox("Outros (inserir nas observações)", value=modelo.servico_executado["outros"])
        with col5:
            modelo.servico_executado["visita"] = st.checkbox("Visita", value=modelo.servico_executado["visita"])

        if modelo.servico_executado["visita"]:
            st.markdown("##### Tipo de Visita:")
            tipo_atual = modelo.servico_executado.get("tipo_visita", [])
            rt = st.checkbox("Relacionamento Técnica", value="Relacionamento Técnica" in tipo_atual)
            tp = st.checkbox("Técnica Preventiva", value="Técnica Preventiva" in tipo_atual)
            
            tipos_selecionados = []
            if rt: tipos_selecionados.append("Relacionamento Técnica")
            if tp: tipos_selecionados.append("Técnica Preventiva")
            modelo.servico_executado["tipo_visita"] = tipos_selecionados

        modelo.servico_executado["observacoes"] = st.text_area("Observações sobre o Serviço Executado", value=modelo.servico_executado["observacoes"])

with tab3:
    with st.container(border=True):
        st.subheader("Resultado do Atendimento")
        modelo.resultado_atendimento["perfeito_funcionamento"] = st.checkbox("O Sistema ficou em perfeito funcionamento, sem nenhuma pendência", value=modelo.resultado_atendimento["perfeito_funcionamento"])
        modelo.resultado_atendimento["pendencias_posterior"] = st.checkbox("Existem pendências para solução posterior (listar em observações)", value=modelo.resultado_atendimento["pendencias_posterior"])
        modelo.resultado_atendimento["treinamento_sucesso"] = st.checkbox("Treinamento efetuado com sucesso", value=modelo.resultado_atendimento["treinamento_sucesso"])
        modelo.resultado_atendimento["pendencias_operador"] = st.checkbox("Existem pendências para que o operador/chefe do setor solucione depois", value=modelo.resultado_atendimento["pendencias_operador"])
        modelo.resultado_atendimento["cartoes"] = st.checkbox("Existem cartões (listar em observações)", value=modelo.resultado_atendimento["cartoes"])
        modelo.resultado_atendimento["outros"] = st.checkbox("Outros (inserir abaixo)", value=modelo.resultado_atendimento["outros"])
        
        modelo.resultado_atendimento["observacoes"] = st.text_area("Observações do Resultado do Atendimento", value=modelo.resultado_atendimento["observacoes"])

with tab4:
    with st.container(border=True):
        st.subheader("Área do Cliente e Assinaturas (Usuário e Coordenador)")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("### 👤 Usuário")
            modelo.area_cliente["local"] = st.text_input("Local", value=modelo.area_cliente["local"])
            modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário", value=modelo.area_cliente["nome_usuario"])
            
            raw_wpp_u = st.text_input("WhatsApp do Usuário", value=modelo.area_cliente["whatsapp_usuario"])
            modelo.area_cliente["whatsapp_usuario"] = limpar_telefone(raw_wpp_u)
            
            capturar_assinatura("Assinatura do Usuário", "usuario", modelo, "assinatura_usuario")
            
        with col_c2:
            st.markdown("### 👔 Coordenador")
            modelo.area_cliente["data_termino"] = st.date_input("Data do término do serviço", value=modelo.area_cliente["data_termino"])
            modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador do setor", value=modelo.area_cliente["nome_coordenador"])
            
            raw_wpp_c = st.text_input("WhatsApp do Coordenador", value=modelo.area_cliente["whatsapp_coordenador"])
            modelo.area_cliente["whatsapp_coordenador"] = limpar_telefone(raw_wpp_c)
            
            capturar_assinatura("Assinatura do Coordenador", "coordenador", modelo, "assinatura_coordenador")


# ==========================================
# 6. GERADOR DE PDF PROFISSIONAL (DESIGN MODERNO)
# ==========================================
def gerar_pdf_relatorio(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0d1527')
    accent_color = colors.HexColor('#1b5ef7')
    border_color = colors.HexColor('#cbd5e1')
    bg_light = colors.HexColor('#f8fafc')
    text_dark = colors.HexColor('#1e293b')
    text_muted = colors.HexColor('#64748b')
    
    header_org_style = ParagraphStyle(
        'HeaderOrg',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        textColor=accent_color,
        textTransform='uppercase',
        spaceAfter=2
    )
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=text_muted,
        spaceAfter=14
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        backColor=primary_color,
        spaceBefore=12,
        spaceAfter=8,
        leftIndent=6,
        rightIndent=6,
        topPadding=6,
        bottomPadding=6
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=text_dark,
        fontName='Helvetica'
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=text_muted,
        spaceBefore=20,
        alignment=1
    )

    story.append(Paragraph("Portal de Treinamentos &bull; Suporte Técnico", header_org_style))
    story.append(Paragraph("Relatório de Atendimento Presencial", title_style))
    story.append(Paragraph("Documento oficial de registro de compromissos, suporte e atividades executadas em campo.", subtitle_style))
    
    ig = dados.get("informacoes_gerais", {})
    story.append(Paragraph("Informações Gerais", section_style))
    
    info_data = [
        [Paragraph(f"<b>Entidade:</b> {ig.get('entidade', '')}", normal_style),
         Paragraph(f"<b>Sistema:</b> {ig.get('sistema', '')}", normal_style)],
        [Paragraph(f"<b>Setor:</b> {ig.get('setor', '')}", normal_style),
         Paragraph(f"<b>Data da Visita:</b> {ig.get('data_visita', '')}", normal_style)],
        [Paragraph(f"<b>Nome do Usuário:</b> {ig.get('nome_usuario', '')}", normal_style),
         Paragraph(f"<b>WhatsApp:</b> {ig.get('whatsapp', '')}", normal_style)],
        [Paragraph(f"<b>E-mail:</b> {ig.get('email', '')}", normal_style),
         Paragraph(f"<b>Resp. Atendimento:</b> {ig.get('responsavel_atendimento', '')}", normal_style)],
        [Paragraph(f"<b>Período:</b> {ig.get('periodo_atendimento', '')}", normal_style),
         Paragraph(f"<b>Turno:</b> [ {'X' if ig.get('turno')=='M' else ' '} ] M  &nbsp;&nbsp;[ {'X' if ig.get('turno')=='T' else ' '} ] T  &nbsp;&nbsp;[ {'X' if ig.get('turno')=='N' else ' '} ] N", normal_style)],
    ]
    t_info = Table(info_data, colWidths=[270, 270])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_info)
    
    story.append(Spacer(1, 6))
    desc_data = [[Paragraph(f"<b>Descrição Detalhada:</b><br/>{ig.get('descricao', 'Nenhuma descrição informada.')}", normal_style)]]
    t_desc = Table(desc_data, colWidths=[540])
    t_desc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_desc)
    
    se = dados.get("servico_executado", {})
    story.append(Paragraph("Registro do Serviço Executado", section_style))
    
    ci = "[X]" if se.get('implantacao') else "[  ]"
    ct = "[X]" if se.get('treinamento') else "[  ]"
    cd = "[X]" if se.get('demonstracao_sistema') else "[  ]"
    cv = "[X]" if se.get('visita') else "[  ]"
    co = "[X]" if se.get('outros') else "[  ]"
    
    serv_html = f"<b>{ci}</b> Implantação &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>{ct}</b> Treinamento &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>{cd}</b> Demonstração de Sistema<br/>" \
                f"<b>{cv}</b> Visita &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>{co}</b> Outros"
    
    serv_data = [[Paragraph(serv_html, normal_style)]]
    t_serv = Table(serv_data, colWidths=[540])
    t_serv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_serv)
    
    if se.get('visita'):
        tv = se.get('tipo_visita', [])
        rt_c = "[X]" if "Relacionamento Técnica" in tv else "[  ]"
        tp_c = "[X]" if "Técnica Preventiva" in tv else "[  ]"
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"&nbsp;&nbsp;<b>Tipo de Visita:</b> &nbsp; {rt_c} Relacionamento Técnica &nbsp;&nbsp;&nbsp;&nbsp; {tp_c} Técnica Preventiva", normal_style))
        
    story.append(Spacer(1, 6))
    obs_serv_data = [[Paragraph(f"<b>Observações do Serviço:</b><br/>{se.get('observacoes', 'Nenhuma observação.')}", normal_style)]]
    t_obs_serv = Table(obs_serv_data, colWidths=[540])
    t_obs_serv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_obs_serv)
    
    ra = dados.get("resultado_atendimento", {})
    story.append(Paragraph("Resultado do Atendimento", section_style))
    
    r1 = "[X]" if ra.get('perfeito_funcionamento') else "[  ]"
    r2 = "[X]" if ra.get('pendencias_posterior') else "[  ]"
    r3 = "[X]" if ra.get('treinamento_sucesso') else "[  ]"
    r4 = "[X]" if ra.get('pendencias_operador') else "[  ]"
    r5 = "[X]" if ra.get('cartoes') else "[  ]"
    r6 = "[X]" if ra.get('outros') else "[  ]"
    
    res_html = f"<b>{r1}</b> O Sistema ficou em perfeito funcionamento, sem nenhuma pendência<br/>" \
               f"<b>{r2}</b> Existem pendências para solução posterior (listar em observações)<br/>" \
               f"<b>{r3}</b> Treinamento efetuado com sucesso<br/>" \
               f"<b>{r4}</b> Existem pendências para que o operador/chefe do setor solucione depois<br/>" \
               f"<b>{r5}</b> Existem cartões (listar em observações)<br/>" \
               f"<b>{r6}</b> Outros (inserir nas observações abaixo)"
               
    res_data = [[Paragraph(res_html, normal_style)]]
    t_res = Table(res_data, colWidths=[540])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_res)
    
    story.append(Spacer(1, 6))
    obs_res_data = [[Paragraph(f"<b>Observações do Resultado:</b><br/>{ra.get('observacoes', 'Nenhuma observação.')}", normal_style)]]
    t_obs_res = Table(obs_res_data, colWidths=[540])
    t_obs_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_obs_res)
    
    ac = dados.get("area_cliente", {})
    story.append(Paragraph("Área do Cliente e Validação", section_style))
    
    sig_u_img = Paragraph("<i>(Sem assinatura registrada)</i>", normal_style)
    if ac.get("assinatura_usuario"):
        sig_u_img = RLImage(io.BytesIO(ac.get("assinatura_usuario")), width=140, height=50)
        
    sig_c_img = Paragraph("<i>(Sem assinatura registrada)</i>", normal_style)
    if ac.get("assinatura_coordenador"):
        sig_c_img = RLImage(io.BytesIO(ac.get("assinatura_coordenador")), width=140, height=50)
        
    cliente_data = [
        [Paragraph(f"<b>Local:</b> {ac.get('local', '')}", normal_style),
         Paragraph(f"<b>Data do Término:</b> {ac.get('data_termino', '')}", normal_style)],
        [Paragraph(f"<b>Nome do Usuário:</b> {ac.get('nome_usuario', '')}", normal_style),
         Paragraph(f"<b>Nome do Coordenador:</b> {ac.get('nome_coordenador', '')}", normal_style)],
        [Paragraph(f"<b>WhatsApp Usuário:</b> {ac.get('whatsapp_usuario', '')}", normal_style),
         Paragraph(f"<b>WhatsApp Coordenador:</b> {ac.get('whatsapp_coordenador', '')}", normal_style)],
        [Paragraph("<b>Assinatura do Usuário:</b>", normal_style),
         Paragraph("<b>Assinatura do Coordenador:</b>", normal_style)],
        [sig_u_img, sig_c_img]
    ]
    
    t_cli = Table(cliente_data, colWidths=[270, 270])
    t_cli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8)
    ]))
    story.append(t_cli)
    
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"Portal de Treinamentos &nbsp;&bull;&nbsp; Relatório gerado eletronicamente em {agora_str}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 7. BOTÃO DE GERAÇÃO COM VALIDAÇÃO
# ==========================================
st.markdown("---")

if st.button("🚀 Validar e Gerar PDF", type="primary", use_container_width=True):
    dados_val = modelo.to_dict()
    ig_val = dados_val["informacoes_gerais"]
    
    erros = []
    if not ig_val.get("entidade", "").strip():
        erros.append("O campo **Entidade** na aba 'Informações Gerais' é obrigatório.")
    if not ig_val.get("nome_usuario", "").strip():
        erros.append("O campo **Nome do Usuário** na aba 'Informações Gerais' é obrigatório.")
        
    if erros:
        for erro in erros:
            st.error(erro)
    else:
        try:
            pdf_bytes = gerar_pdf_relatorio(dados_val)
            st.success("Relatório gerado com sucesso!")
            st.download_button(
                label="📥 Baixar PDF Oficial",
                data=pdf_bytes,
                file_name="relatorio_atendimento_presencial.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao gerar o PDF: {e}")
