import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL COMPACTA ---
st.set_page_config(page_title="Amare Italinea", layout="wide")
st.markdown("<style>div.block-container{padding-top:1rem;} .stTextArea textarea {height: 40px;}</style>", unsafe_allow_html=True)

USUARIOS = {"michel_conferente": "italinea123", "matheus_conferente": "italinea456", "douglas_conferente": "italinea789", "admin": "adminamare"}

def analisar_xmls(f_venda, f_conf):
    def extrair(f):
        root = ET.parse(f).getroot()
        itens, pe, par = {}, 0, 0
        for i in root.iter('Item'):
            n, l, a = i.get('Description', 'M'), float(i.get('Width', 0)), float(i.get('Height', 0))
            itens[n] = {'L': l, 'A': a}
            if "DIREITO" in n.upper(): pe = a
            if "PAREDE" in n.upper(): par += l
        return itens, pe, par

    v_it, v_pe, v_pa = extrair(f_venda)
    c_it, c_pe, c_pa = extrair(f_conf)
    err = []
    if abs(v_pe - c_pe) > 20: err.append(f"⚠️ Pé-Direito: Dif. {abs(v_pe-c_pe)}mm")
    if abs(v_pa - c_pa) > 150: err.append(f"🧱 Parede: Dif. {abs(v_pa-c_pa)}mm")
    for n, info in v_it.items():
        if n in c_it and abs(info['L'] - c_it[n]['L']) > 20:
            err.append(f"📏 {n}: Dif. {abs(info['L'] - c_it[n]['L'])}mm")
    return err

if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    with st.sidebar:
        u = st.text_input("Usuário").lower()
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logado"], st.session_state["user"] = True, u
                st.rerun()
else:
    # --- INTERFACE PRINCIPAL ---
    c1, c2 = st.columns([2, 1])
    c1.title(f"🕵️ Auditor: {st.session_state['user']}")
    if c2.button("Sair"): 
        st.session_state["logado"] = False
        st.rerun()

    # --- XML E ALERTAS (LADO A LADO) ---
    st.markdown("---")
    col_f1, col_f2, col_err = st.columns([1, 1, 2])
    f_v = col_f1.file_uploader("XML Venda", type=['xml'])
    f_c = col_f2.file_uploader("XML Técnico", type=['xml'])
    
    xml_val = True
    if f_v and f_c:
        erros = analisar_xmls(f_v, f_c)
        if erros:
            with col_err:
                st.error("🚨 Justifique os desvios:")
                for i, e in enumerate(erros):
                    st.text_area(e, key=f"e_{i}", placeholder="Motivo técnico...")
                xml_val = False
        else: col_err.success("✅ XMLs Batendo")

    # --- CHECKLIST COMPACTO EM 3 COLUNAS ---
    st.markdown("---")
    l1, l2, l3 = st.columns(3)
    with l1:
        h1 = st.checkbox("Caixa/Regis/Filtro")
        h2 = st.checkbox("Bancada/Janela")
        h3 = st.checkbox("Gás/Esgoto nicho")
    with l2:
        m1 = st.checkbox("Guarnição Porta")
        m2 = st.checkbox("Pé-Direito (3 pts)")
        m3 = st.checkbox("Empenamento/Reforço")
    with l3:
        g1 = st.checkbox("Altura Aéreos/TV")
        g2 = st.checkbox("Mautenção Ar Cond.")
        g3 = st.checkbox("Ferragem Divisória")

    # --- FINALIZAÇÃO ---
    st.markdown("---")
    f1, f2, f3 = st.columns([1.5, 1.5, 1])
    cli = f1.text_input("Cliente/Contrato")
    pic = f2.file_uploader("Foto Papel Ofício", type=['jpg', 'png'])
    
    if f3.button("🚀 LACRAR"):
        if all([h1, h2, h3, m1, m2, m3, g1, g2, g3, pic, cli, xml_val]):
            st.success("✅ LIBERADO")
            st.balloons()
        else: st.error("❌ ERRO/PENDÊNCIA")
