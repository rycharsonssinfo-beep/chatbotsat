import io
from datetime import datetime, date
import streamlit as st
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Relatório de Atendimento Presencial — Portal",
    page_icon="📋",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #0d1527;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. MODELO DE DADOS
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
        if isinstance(d["informacoes_gerais"].get("data_visita"), date):
            d["informacoes_gerais"]["data_visita"] = d["informacoes_gerais"]["data_visita"].strftime("%d/%m/%Y")
        if isinstance(d["area_cliente"].get("data_termino"), date):
            d["area_cliente"]["data_termino"] = d["area_cliente"]["data_termino"].strftime("%d/%m/%Y")
        return d


# ==========================================
# 3. APLICAÇÃO PRINCIPAL
# ==========================================
st.title("📋 Relatório de Atendimento Presencial")
st.markdown("Preencha os dados abaixo para registrar o atendimento técnico e gerar o PDF formatado.")

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
            modelo.informacoes_gerais["entidade"] = st.text_input("Entidade (Prefeitura / Câmara...)*", value=modelo.informacoes_gerais["entidade"])
            modelo.informacoes_gerais["sistema"] = st.text_input("Sistema", value=modelo.informacoes_gerais["sistema"])
            modelo.informacoes_gerais["setor"] = st.text_input("Setor", value=modelo.informacoes_gerais["setor"])
            modelo.informacoes_gerais["nome_usuario"] = st.text_input("Nome do Usuário*", value=modelo.informacoes_gerais["nome_usuario"])
            modelo.informacoes_gerais["email"] = st.text_input("E-mail", value=modelo.informacoes_gerais["email"])
        with col2:
            modelo.informacoes_gerais["whatsapp"] = st.text_input("WhatsApp", value=modelo.informacoes_gerais["whatsapp"])
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
            modelo.servico_executado["outros"] = st.checkbox("Outros", value=modelo.servico_executado["outros"])
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
        modelo.resultado_atendimento["pendencias_posterior"] = st.checkbox("Existem pendências para solução posterior", value=modelo.resultado_atendimento["pendencias_posterior"])
        modelo.resultado_atendimento["treinamento_sucesso"] = st.checkbox("Treinamento efetuado com sucesso", value=modelo.resultado_atendimento["treinamento_sucesso"])
        modelo.resultado_atendimento["pendencias_operador"] = st.checkbox("Existem pendências para o operador/chefe do setor", value=modelo.resultado_atendimento["pendencias_operador"])
        modelo.resultado_atendimento["cartoes"] = st.checkbox("Existem cartões", value=modelo.resultado_atendimento["cartoes"])
        modelo.resultado_atendimento["outros"] = st.checkbox("Outros", value=modelo.resultado_atendimento["outros"])
        
        modelo.resultado_atendimento["observacoes"] = st.text_area("Observações do Resultado", value=modelo.resultado_atendimento["observacoes"])

with tab4:
    with st.container(border=True):
        st.subheader("Área do Cliente e Assinaturas")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("### 👤 Usuário")
            modelo.area_cliente["local"] = st.text_input("Local", value=modelo.area_cliente["local"])
            modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário", value=modelo.area_cliente["nome_usuario"])
            modelo.area_cliente["whatsapp_usuario"] = st.text_input("WhatsApp do Usuário", value=modelo.area_cliente["whatsapp_usuario"])
            
            up_u = st.file_uploader("Enviar imagem da Assinatura do Usuário", type=["png", "jpg", "jpeg"], key="up_u")
            if up_u:
                modelo.area_cliente["assinatura_usuario"] = up_u.getvalue()
                st.image(up_u, width=150)
                
        with col_c2:
            st.markdown("### 👔 Coordenador")
            modelo.area_cliente["data_termino"] = st.date_input("Data do término do serviço", value=modelo.area_cliente["data_termino"])
            modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador do setor", value=modelo.area_cliente["nome_coordenador"])
            modelo.area_cliente["whatsapp_coordenador"] = st.text_input("WhatsApp do Coordenador", value=modelo.area_cliente["whatsapp_coordenador"])
            
            up_c = st.file_uploader("Enviar imagem da Assinatura do Coordenador", type=["png", "jpg", "jpeg"], key="up_c")
            if up_c:
                modelo.area_cliente["assinatura_coordenador"] = up_c.getvalue()
                st.image(up_c, width=150)


# ==========================================
# 4. GERADOR DE PDF REFINADO
# ==========================================
def gerar_pdf_relatorio(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    
    styles = getSampleStyleSheet()
    
    cor_primaria = colors.HexColor('#0d1527')
    cor_accent = colors.HexColor('#1b5ef7')
    cor_texto = colors.HexColor('#1e293b')
    cor_muted = colors.HexColor('#64748b')
    cor_borda = colors.HexColor('#cbd5e1')
    cor_fundo_bloco = colors.HexColor('#f8fafc')
    
    header_org_style = ParagraphStyle('HeaderOrg', parent=styles['Normal'], fontSize=8, textColor=cor_muted, spaceAfter=1)
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=cor_primaria, fontName='Helvetica-Bold', spaceAfter=2)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=8.5, textColor=cor_muted, spaceAfter=10)
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=9.5,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        backColor=cor_primaria,
        spaceBefore=10,
        spaceAfter=4,
        leftIndent=6,
        rightIndent=6,
        topPadding=4,
        bottomPadding=4
    )
    
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=cor_texto, fontName='Helvetica')
    bold_style = ParagraphStyle('BoldCustom', parent=normal_style, fontName='Helvetica-Bold')
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=7.5, textColor=cor_muted, spaceBefore=10)

    def checkbox_html(checked: bool, label: str) -> str:
        box = f'<font color="{cor_accent.hexval()}"><b>[X]</b></font>' if checked else f'<font color="{cor_muted.hexval()}">[  ]</font>'
        return f'{box} {label}'

    # Cabeçalho
    story.append(Paragraph("Portal de Treinamentos", header_org_style))
    story.append(Paragraph("Relatório de Atendimento Presencial", title_style))
    story.append(Paragraph("Registro oficial de compromissos e atividades executadas em campo.", subtitle_style))
    
    # Informações Gerais
    ig = dados.get("informacoes_gerais", {})
    story.append(Paragraph("<b>Informações Gerais</b>", section_style))
    
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
         Paragraph(f"<b>Turno:</b> &nbsp; [ {'<b>X</b>' if ig.get('turno')=='M' else '&nbsp;'} ] M &nbsp;&nbsp;&nbsp; [ {'<b>X</b>' if ig.get('turno')=='T' else '&nbsp;'} ] T &nbsp;&nbsp;&nbsp; [ {'<b>X</b>' if ig.get('turno')=='N' else '&nbsp;'} ] N", normal_style)],
    ]
    t_info = Table(info_data, colWidths=[280, 280])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_info)
    
    desc_text = ig.get('descricao', '').strip()
    if desc_text:
        story.append(Spacer(1, 4))
        desc_table = Table([[Paragraph(f"<b>Descrição Detalhada:</b><br/>{desc_text}", normal_style)]], colWidths=[560])
        desc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_fundo_bloco),
            ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(desc_table)
    
    # Serviços Executados
    se = dados.get("servico_executado", {})
    story.append(Paragraph("<b>Registro do Serviço Executado</b>", section_style))
    
    serv_data = [
        [Paragraph(checkbox_html(se.get('implantacao'), "Implantação"), normal_style),
         Paragraph(checkbox_html(se.get('treinamento'), "Treinamento"), normal_style),
         Paragraph(checkbox_html(se.get('demonstracao_sistema'), "Demonstração de Sistema"), normal_style)],
        [Paragraph(checkbox_html(se.get('visita'), "Visita"), normal_style),
         Paragraph(checkbox_html(se.get('outros'), "Outros"), normal_style),
         Paragraph("", normal_style)]
    ]
    t_serv = Table(serv_data, colWidths=[186, 186, 188])
    t_serv.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_serv)
    
    if se.get('visita'):
        tv = se.get('tipo_visita', [])
        rt_c = checkbox_html("Relacionamento Técnica" in tv, "Relacionamento Técnica")
        tp_c = checkbox_html("Técnica Preventiva" in tv, "Técnica Preventiva")
        t_visita_box = Table([[Paragraph(f"<b>Tipo de Visita:</b> &nbsp;&nbsp; {rt_c} &nbsp;&nbsp;&nbsp;&nbsp; {tp_c}", normal_style)]], colWidths=[560])
        t_visita_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_fundo_bloco),
            ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(Spacer(1, 3))
        story.append(t_visita_box)
        
    obs_serv = se.get('observacoes', '').strip()
    if obs_serv:
        story.append(Spacer(1, 3))
        t_obs_s = Table([[Paragraph(f"<b>Observações (Serviço):</b><br/>{obs_serv}", normal_style)]], colWidths=[560])
        t_obs_s.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_fundo_bloco),
            ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(t_obs_s)
    
    # Resultado
    ra = dados.get("resultado_atendimento", {})
    story.append(Paragraph("<b>Resultado do Atendimento</b>", section_style))
    
    res_data = [
        [Paragraph(checkbox_html(ra.get('perfeito_funcionamento'), "O Sistema ficou em perfeito funcionamento, sem nenhuma pendência"), normal_style)],
        [Paragraph(checkbox_html(ra.get('pendencias_posterior'), "Existem pendências para solução posterior (listar em observações)"), normal_style)],
        [Paragraph(checkbox_html(ra.get('treinamento_sucesso'), "Treinamento efetuado com sucesso"), normal_style)],
        [Paragraph(checkbox_html(ra.get('pendencias_operador'), "Existem pendências para que o operador/chefe do setor solucione depois"), normal_style)],
        [Paragraph(checkbox_html(ra.get('cartoes'), "Existem cartões (listar em observações)"), normal_style)],
        [Paragraph(checkbox_html(ra.get('outros'), "Outros"), normal_style)]
    ]
    t_res = Table(res_data, colWidths=[560])
    t_res.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_res)
    
    obs_res = ra.get('observacoes', '').strip()
    if obs_res:
        story.append(Spacer(1, 3))
        t_obs_r = Table([[Paragraph(f"<b>Observações (Resultado):</b><br/>{obs_res}", normal_style)]], colWidths=[560])
        t_obs_r.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_fundo_bloco),
            ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(t_obs_r)
    
    # Área do Cliente
    ac = dados.get("area_cliente", {})
    story.append(Paragraph("<b>Área do Cliente</b>", section_style))
    
    sig_u_img = Paragraph("<i>(Sem assinatura)</i>", normal_style)
    if ac.get("assinatura_usuario"):
        sig_u_img = RLImage(io.BytesIO(ac.get("assinatura_usuario")), width=140, height=45)
        
    sig_c_img = Paragraph("<i>(Sem assinatura)</i>", normal_style)
    if ac.get("assinatura_coordenador"):
        sig_c_img = RLImage(io.BytesIO(ac.get("assinatura_coordenador")), width=140, height=45)
        
    cliente_data = [
        [Paragraph(f"<b>Local:</b> {ac.get('local', '')}", normal_style),
         Paragraph(f"<b>Data do término:</b> {ac.get('data_termino', '')}", normal_style)],
        [Paragraph(f"<b>Nome do Usuário:</b> {ac.get('nome_usuario', '')}", normal_style),
         Paragraph(f"<b>Nome do Coordenador:</b> {ac.get('nome_coordenador', '')}", normal_style)],
        [Paragraph(f"<b>WhatsApp Usuário:</b> {ac.get('whatsapp_usuario', '')}", normal_style),
         Paragraph(f"<b>WhatsApp Coordenador:</b> {ac.get('whatsapp_coordenador', '')}", normal_style)],
        [Paragraph("<b>Assinatura do Usuário:</b>", bold_style),
         Paragraph("<b>Assinatura do Coordenador:</b>", bold_style)],
        [sig_u_img, sig_c_img]
    ]
    
    t_cli = Table(cliente_data, colWidths=[280, 280])
    t_cli.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, cor_borda),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_cli)
    
    # Rodapé
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Portal de Treinamentos &nbsp;&bull;&nbsp; Emitido em {agora_str}", footer_style))
    story.append(Paragraph("Relatório de uso administrativo", ParagraphStyle('SubFooter', parent=footer_style, fontSize=6.5, textColor=colors.HexColor('#94a3b8'))))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 5. BOTÃO DE GERAÇÃO
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
                label="📥 Baixar PDF Oficial Formatado",
                data=pdf_bytes,
                file_name="relatorio_atendimento_presencial.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao gerar o PDF: {e}")
