import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria", page_icon="🏢", layout="wide")

# Estilo para garantir que as caixas de alerta e texto não gerem rolagem interna desnecessária
st.markdown("""
    <style>
    .stTextArea textarea {height: 80px;}
    .stAlert {padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO DE AUDITORIA INTELIGENTE ---
def analisar_divergencias(venda_file, conf_file):
    def extrair(file):
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        pe_direito = 0
        parede_total = 0
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            larg = float(i.get('Width', 0))
            alt = float(i.get('Height', 0))
            itens[nome] = {'L': larg, 'A': alt}
            if "DIREITO" in nome.upper(): pe_direito = alt
            if "PAREDE" in nome.upper(): parede_total += larg
        return itens, pe_direito, parede_total

    v_itens, v_pe, v_par = extrair(venda_file)
    c_itens, c_pe, c_par = extrair(conf_file)
    alertas = []

    if abs(v_par - c_par) >= 150 and v_par > 0:
        alertas.append(f"🧱 PAREDE: Diferença de {abs(v_par - c_par)}mm (Venda: {v_par}mm | Real: {c_par}mm).")
    if abs(v_pe - c_pe) > 20 and v_pe > 0:
        alertas.append(f"🚨 PÉ-DIREITO: Variação de {abs(v_pe - c_pe)}mm detectada.")
    for nome, info in v_itens.items():
        if nome in c_itens and abs(info['L'] - c_itens[nome]['L']) > 20:
            alertas.append(f"📏 MÓDULO: '{nome}' alterado em {abs(info['L'] - c_itens[nome]['L'])}mm.")
    
    return alertas

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Portal de Auditoria")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"], st.session_state["user"] = True, u
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title(f"🕵️ Auditoria Master Amare: {st.session_state['user']}")
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise XML", "🏗️ Engenharia e Obra", "🛌 Ergonomia e Conforto", "🏁 Lacre Final"])

    with tab1:
        st.header("1. Comparação Automática (Tolerância: Parede 15cm / Móvel 2cm)")
        c1, c2 = st.columns(2)
        f_venda = c1.file_uploader("XML Venda", type=['xml'])
        f_conf = c2.file_uploader("XML Conferência", type=['xml'])

        xml_validado = True
        if f_venda and f_conf:
            questoes = analisar_divergencias(f_venda, f_conf)
            if questoes:
                st.error("🚨 DIVERGÊNCIAS IDENTIFICADAS (Justifique abaixo):")
                # Aqui o sistema expande conforme o número de erros, sem barra de rolagem interna
                for i, q in enumerate(questoes):
                    st.warning(q)
                    st.text_area("Descreva o motivo desta alteração:", key=f"ans_{i}", placeholder="Justificativa técnica...")
                xml_validado = False
            else: st.success("✅ XMLs em conformidade técnica.")

    with tab2:
        st.header("2. Infraestrutura e Obra (Papel de Ofício)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💧 Hidráulica e Gás")
            h1 = st.checkbox("Caixa de Gordura, Registros e Filtro de água acessíveis?")
            h2 = st.checkbox("Altura da bancada permite abertura da janela/torneira?")
            h3 = st.checkbox("Ponto de Gás e Esgoto previstos nos nichos?")
            h4 = st.checkbox("LEDs: Perfil e furação de passagem de cabos previstos?")
        with col2:
            st.subheader("🧱 Marcenaria")
            m1 = st.checkbox("GUARNIÇÃO: Gavetas e portas abrem sem bater no batente?")
            m2 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos p/ checar queda de laje?")
            m3 = st.checkbox("EMPENAMENTO: Reforço em prateleiras largas (>900mm)?")
            m4 = st.checkbox("DIVISÓRIA: Ferragem da porta (oculta/aparente) confirmada?")

    with tab3:
        st.header("3. Conforto e Uso Diário")
        col3, col4 = st.columns(2)
        with col3:
            g1 = st.checkbox("ALTURA AÉREOS: O cliente não corre risco de bater a cabeça?")
            g2 = st.checkbox("TV: Está no eixo da cama e na altura correta?")
        with col4:
            g3 = st.checkbox("AR CONDICIONADO: O móvel permite manutenção e limpeza do filtro?")
            g4 = st.checkbox("CIRCULAÇÃO: Mínimo de 60cm de passagem livre garantida?")

    with tab4:
        st.header("4. Finalização do Laudo")
        cliente = st.text_input("Cliente / Contrato")
        foto = st.file_uploader("📷 Foto Obrigatória: Papel de Ofício (Medida Fina)", type=['jpg', 'png'])
        obs = st.text_area("Instruções Extras para o Montador")
        
        if st.button("🚀 GERAR LAUDO FINAL AMARE"):
            checks = [h1, h2, h3, h4, m1, m2, m3, m4, g1, g2, g3, g4, foto, cliente]
            if not all(checks): st.error("❌ Complete o checklist e anexe a foto.")
            else:
                st.balloons()
                st.success("Auditoria Concluída!")
                # Geração de PDF simplificada para download
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"LAUDO AMARE ITALINEA: {cliente}", ln=True, align='C')
                pdf.output(f"Laudo_{cliente}.pdf")
                with open(f"Laudo_{cliente}.pdf", "rb") as f:
                    st.download_button("📥 BAIXAR LAUDO", f, file_name=f"Laudo_{cliente}.pdf")
