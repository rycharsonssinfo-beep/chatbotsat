import io
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. MODELO DE DADOS
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
            "data_visita": "",
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
            "data_termino": "",
            "nome_coordenador": "",
            "whatsapp_coordenador": "",
            "assinatura_coordenador": None
        }

    def to_dict(self) -> dict:
        return {
            "informacoes_gerais": self.informacoes_gerais,
            "servico_executado": self.servico_executado,
            "resultado_atendimento": self.resultado_atendimento,
            "area_cliente": self.area_cliente
        }


# ==========================================
# 2. COMPONENTE DE ASSINATURA DIGITAL
# ==========================================
def capturar_assinatura(titulo: str, key_prefix: str):
    st.markdown(f"**{titulo}**")
    modo = st.radio("Método de Assinatura", ["Desenhar na Tela", "Enviar Imagem"], key=f"modo_{key_prefix}", horizontal=True)
    
    assinatura_bytes = None
    
    if modo == "Desenhar na Tela":
        st.info("Desenhe a assinatura no quadro abaixo:")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=150,
            width=400,
            drawing_mode="freedraw",
            update_streamlit=True,  # Obrigatório para evitar o RuntimeError
            key=f"canvas_{key_prefix}"
        )
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            assinatura_bytes = buf.getvalue()
    else:
        uploaded_file = st.file_uploader(f"Enviar imagem da assinatura ({titulo})", type=["png", "jpg", "jpeg"], key=f"upload_{key_prefix}")
        if uploaded_file is not None:
            assinatura_bytes = uploaded_file.getvalue()
            st.image(assinatura_bytes, width=200, caption="Assinatura Carregada")
            
    return assinatura_bytes


# ==========================================
# 3. COMPONENTE DO FORMULÁRIO
# ==========================================
def renderizar_formulario(modelo: RelatorioModel):
    st.markdown("### 1. Informações Gerais")
    col1, col2 = st.columns(2)
    with col1:
        modelo.informacoes_gerais["entidade"] = st.text_input("Entidade (Prefeitura / Câmara / Consórcio...)", value=modelo.informacoes_gerais["entidade"])
        modelo.informacoes_gerais["sistema"] = st.text_input("Sistema", value=modelo.informacoes_gerais["sistema"])
        modelo.informacoes_gerais["setor"] = st.text_input("Setor", value=modelo.informacoes_gerais["setor"])
        modelo.informacoes_gerais["nome_usuario"] = st.text_input("Nome do Usuário", value=modelo.informacoes_gerais["nome_usuario"])
        modelo.informacoes_gerais["email"] = st.text_input("E-mail", value=modelo.informacoes_gerais["email"])
    with col2:
        modelo.informacoes_gerais["whatsapp"] = st.text_input("WhatsApp", value=modelo.informacoes_gerais["whatsapp"])
        modelo.informacoes_gerais["data_visita"] = st.text_input("Data da Visita (DD/MM/AAAA)", value=modelo.informacoes_gerais["data_visita"])
        modelo.informacoes_gerais["responsavel_atendimento"] = st.text_input("Responsável pelo Atendimento", value=modelo.informacoes_gerais["responsavel_atendimento"])
        modelo.informacoes_gerais["periodo_atendimento"] = st.text_input("Período de Atendimento", value=modelo.informacoes_gerais["periodo_atendimento"])
        
        turno_map = {"M": 0, "T": 1, "N": 2}
        turno_atual = modelo.informacoes_gerais.get("turno", "M")
        turno_escolhido = st.radio("Turno", ["M — Manhã", "T — Tarde", "N — Noite"], index=turno_map.get(turno_atual, 0), horizontal=True)
        modelo.informacoes_gerais["turno"] = turno_escolhido[0]

    modelo.informacoes_gerais["descricao"] = st.text_area("Descrição", value=modelo.informacoes_gerais["descricao"])

    st.markdown("---")
    st.markdown("### 2. Registro do Serviço Executado")
    
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

    modelo.servico_executado["observacoes"] = st.text_area("Observações (Serviço Executado)", value=modelo.servico_executado["observacoes"])

    st.markdown("---")
    st.markdown("### 3. Resultado do Atendimento")
    modelo.resultado_atendimento["perfeito_funcionamento"] = st.checkbox("O Sistema ficou em perfeito funcionamento, sem nenhuma pendência", value=modelo.resultado_atendimento["perfeito_funcionamento"])
    modelo.resultado_atendimento["pendencias_posterior"] = st.checkbox("Existem pendências para solução posterior (listar em observações)", value=modelo.resultado_atendimento["pendencias_posterior"])
    modelo.resultado_atendimento["treinamento_sucesso"] = st.checkbox("Treinamento efetuado com sucesso", value=modelo.resultado_atendimento["treinamento_sucesso"])
    modelo.resultado_atendimento["pendencias_operador"] = st.checkbox("Existem pendências para que o operador/chefe do setor solucione depois", value=modelo.resultado_atendimento["pendencias_operador"])
    modelo.resultado_atendimento["cartoes"] = st.checkbox("Existem cartões (listar em observações)", value=modelo.resultado_atendimento["cartoes"])
    modelo.resultado_atendimento["outros"] = st.checkbox("Outros (inserir abaixo)", value=modelo.resultado_atendimento["outros"])
    
    modelo.resultado_atendimento["observacoes"] = st.text_area("Observações (Resultado do Atendimento)", value=modelo.resultado_atendimento["observacoes"])

    st.markdown("---")
    st.markdown("### 4. Área do Cliente")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### Informações do Usuário")
        modelo.area_cliente["local"] = st.text_input("Local", value=modelo.area_cliente["local"])
        modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário (Área do Cliente)", value=modelo.area_cliente["nome_usuario"])
        modelo.area_cliente["whatsapp_usuario"] = st.text_input("WhatsApp do Usuário", value=modelo.area_cliente["whatsapp_usuario"])
        sig_u = capturar_assinatura("Assinatura do Usuário", "usuario")
        if sig_u:
            modelo.area_cliente["assinatura_usuario"] = sig_u
            
    with col_c2:
        st.markdown("#### Informações do Setor / Coordenador")
        modelo.area_cliente["data_termino"] = st.text_input("Data do término do serviço (DD/MM/AAAA)", value=modelo.area_cliente["data_termino"])
        modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador do setor", value=modelo.area_cliente["nome_coordenador"])
        modelo.area_cliente["whatsapp_coordenador"] = st.text_input("WhatsApp do Coordenador do setor", value=modelo.area_cliente["whatsapp_coordenador"])
        sig_c = capturar_assinatura("Assinatura do Coordenador do setor", "coordenador")
        if sig_c:
            modelo.area_cliente["assinatura_coordenador"] = sig_c


# ==========================================
# 4. GERADOR DE PDF
# ==========================================
def gerar_pdf_relatorio(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#004D40'),
        spaceAfter=10,
        alignment=1
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        backColor=colors.HexColor('#004D40'),
        spaceBefore=8,
        spaceAfter=8,
        leftIndent=4,
        rightIndent=4
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.leading = 11

    # Cabeçalho
    story.append(Paragraph("<b>Grupo S&S</b>", normal_style))
    story.append(Paragraph("<b>RELATÓRIO DE ATENDIMENTO PRESENCIAL</b>", title_style))
    story.append(Spacer(1, 5))
    
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
         Paragraph(f"<b>Turno:</b> [ {'X' if ig.get('turno')=='M' else ' '} ] M  [ {'X' if ig.get('turno')=='T' else ' '} ] T  [ {'X' if ig.get('turno')=='N' else ' '} ] N", normal_style)],
    ]
    t_info = Table(info_data, colWidths=[270, 270])
    t_info.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_info)
    
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Descrição:</b> {ig.get('descricao', '')}", normal_style))
    
    # Serviço Executado
    se = dados.get("servico_executado", {})
    story.append(Paragraph("<b>Registro do Serviço Executado</b>", section_style))
    
    check_implantacao = "[X]" if se.get('implantacao') else "[  ]"
    check_treinamento = "[X]" if se.get('treinamento') else "[  ]"
    check_dem = "[X]" if se.get('demonstracao_sistema') else "[  ]"
    check_visita = "[X]" if se.get('visita') else "[  ]"
    check_outros = "[X]" if se.get('outros') else "[  ]"
    
    serv_text = f"{check_implantacao} Implantação   &nbsp;&nbsp;&nbsp;&nbsp; {check_treinamento} Treinamento   &nbsp;&nbsp;&nbsp;&nbsp; {check_dem} Demonstração de Sistema<br/>" \
                f"{check_visita} Visita   &nbsp;&nbsp;&nbsp;&nbsp; {check_outros} Outros"
    story.append(Paragraph(serv_text, normal_style))
    
    if se.get('visita'):
        tv = se.get('tipo_visita', [])
        rt_c = "[X]" if "Relacionamento Técnica" in tv else "[  ]"
        tp_c = "[X]" if "Técnica Preventiva" in tv else "[  ]"
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;Tipo de Visita: {rt_c} Relacionamento Técnica &nbsp;&nbsp; {tp_c} Técnica Preventiva", normal_style))
        
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Observações (Serviço):</b> {se.get('observacoes', '')}", normal_style))
    
    # Resultado
    ra = dados.get("resultado_atendimento", {})
    story.append(Paragraph("<b>Resultado do Atendimento</b>", section_style))
    
    r1 = "[X]" if ra.get('perfeito_funcionamento') else "[  ]"
    r2 = "[X]" if ra.get('pendencias_posterior') else "[  ]"
    r3 = "[X]" if ra.get('treinamento_sucesso') else "[  ]"
    r4 = "[X]" if ra.get('pendencias_operador') else "[  ]"
    r5 = "[X]" if ra.get('cartoes') else "[  ]"
    r6 = "[X]" if ra.get('outros') else "[  ]"
    
    res_text = f"{r1} O Sistema ficou em perfeito funcionamento, sem nenhuma pendência<br/>" \
               f"{r2} Existem pendências para solução posterior (listar em observações)<br/>" \
               f"{r3} Treinamento efetuado com sucesso<br/>" \
               f"{r4} Existem pendências para que o operador/chefe do setor solucione depois<br/>" \
               f"{r5} Existem cartões (listar em observações)<br/>" \
               f"{r6} Outros (inserir abaixo)"
    story.append(Paragraph(res_text, normal_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Observações (Resultado):</b> {ra.get('observacoes', '')}", normal_style))
    
    # Área do Cliente
    ac = dados.get("area_cliente", {})
    story.append(Paragraph("<b>Área do Cliente</b>", section_style))
    
    sig_u_img = ""
    if ac.get("assinatura_usuario"):
        sig_u_img = RLImage(io.BytesIO(ac.get("assinatura_usuario")), width=120, height=45)
    sig_c_img = ""
    if ac.get("assinatura_coordenador"):
        sig_c_img = RLImage(io.BytesIO(ac.get("assinatura_coordenador")), width=120, height=45)
        
    cliente_data = [
        [Paragraph(f"<b>Local:</b> {ac.get('local', '')}", normal_style),
         Paragraph(f"<b>Data do término do serviço:</b> {ac.get('data_termino', '')}", normal_style)],
        [Paragraph(f"<b>Nome do Usuário:</b> {ac.get('nome_usuario', '')}", normal_style),
         Paragraph(f"<b>Nome do Coordenador do setor:</b> {ac.get('nome_coordenador', '')}", normal_style)],
        [Paragraph(f"<b>WhatsApp do Usuário:</b> {ac.get('whatsapp_usuario', '')}", normal_style),
         Paragraph(f"<b>WhatsApp do Coordenador:</b> {ac.get('whatsapp_coordenador', '')}", normal_style)],
        [Paragraph("<b>Assinatura do Usuário:</b><br/>", normal_style),
         Paragraph("<b>Assinatura do Coordenador do Setor:</b><br/>", normal_style)],
        [sig_u_img if sig_u_img else Paragraph("<i>(Sem assinatura)</i>", normal_style),
         sig_c_img if sig_c_img else Paragraph("<i>(Sem assinatura)</i>", normal_style)]
    ]
    
    t_cli = Table(cliente_data, colWidths=[270, 270])
    t_cli.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_cli)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 5. APLICAÇÃO PRINCIPAL (STREAMLIT)
# ==========================================
st.set_page_config(
    page_title="Relatório de Atendimento Presencial",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Portal de Atendimento - Grupo S&S")
st.markdown("Preencha o formulário abaixo para gerar o **Relatório de Atendimento Presencial** oficial.")

# Inicializar estado da sessão
if "relatorio_model" not in st.session_state:
    st.session_state["relatorio_model"] = RelatorioModel()

modelo = st.session_state["relatorio_model"]

with st.sidebar:
    st.header("Navegação e Ações")
    if st.button("🔄 Novo Relatório (Limpar)", use_container_width=True):
        st.session_state["relatorio_model"] = RelatorioModel()
        st.rerun()

# Renderizar formulário unificado
renderizar_formulario(modelo)

st.markdown("---")
col_gen = st.columns(1)[0]

with col_gen:
    if st.button("🚀 Gerar e Baixar PDF", type="primary", use_container_width=True):
        try:
            pdf_bytes = gerar_pdf_relatorio(modelo.to_dict())
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
