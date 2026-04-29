import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E SESSÃO ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []
if "mapa_dxf_buffer" not in st.session_state:
    st.session_state["mapa_dxf_buffer"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- 2. MOTOR DE DESENHO (DXF) ---
def renderizar_confronto_dxf(v_dxf, c_dxf):
    fig, ax = plt.subplots(figsize=(14, 8))
    def desenhar(file, cor):
        try:
            with open("temp.dxf", "wb") as f:
                f.write(file.getbuffer())
            doc = ezdxf.readfile("temp.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE LWPOLYLINE'):
                if e.dxftype() == 'LINE':
                    ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color=cor, alpha=0.6, lw=0.7)
            os.remove("temp.dxf")
        except: pass
    
    desenhar(v_dxf, 'red')   # Projeto Venda
    desenhar(c_dxf, 'green') # Técnico/Conferência
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- 3. MOTOR DE LISTA (XML) ---
def comparar_xmls(f_v_x, f_c_x):
    def extrair(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            return [item.get('DESCRIPTION', 'MODULO').upper() for item in root.findall(".//ITEM") if float(item.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(f_v_x), extrair(f_c_x)
    saiu = [i for i in v if i not in c]
    entrou = [i for i in c if i not in v]
    return saiu, entrou

# --- 4. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Login Amare Italinea")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    # --- 5. INTERFACE ---
    st.title("👷 Portal de Auditoria Master Amare")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Confronto XML/DXF", "🏠 Checklist", "🔌 Memorial Eletros", "💰 Extras", "🏁 Finalizar"])

    with t1:
        st.header("1. Comparação Visual e Técnica")
        col1, col2 = st.columns(2)
        with col1:
            f_v_x = st.file_uploader("XML Venda", type=['xml'], key="vx")
            f_v_d = st.file_uploader("DXF Venda", type=['dxf'], key="vd")
        with col2:
            f_c_x = st.file_uploader("XML Técnico", type=['xml'], key="cx")
            f_c_d = st.file_uploader("DXF Técnico", type=['dxf'], key="cd")

        if f_v_x and f_c_x:
            saiu, entrou = comparar_xmls(f_v_x, f_c_x)
            cs, ce = st.columns(2)
            with cs:
                st.error("🔴 ITENS RETIRADOS")
                for s in saiu: st.write(f"- {s}")
            with ce:
                st.success("🟢 ITENS ADICIONADOS")
                for e in entrou: st.write(f"- {e}")
        
        if f_v_d and f_c_d:
            st.image(renderizar_confronto_dxf(f_v_d, f_c_d), caption="Vermelho: Original | Verde: Técnico", use_container_width=True)

    with t2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica, Gás e Civil")
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Gás está acessível?"); st.checkbox("Paredes com prumo/esquadro?")
        with colB:
            st.subheader("⚡ Elétrica e Medição")
            st.checkbox("Ponto energia coifa no local?"); st.checkbox("Tomadas bancada respeitam 110cm?")
            st.checkbox("Pé-direito (3 pontos)?"); st.checkbox("Desconto granitos aplicado?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        st.write("**Geladeira**")
        c1a, c1b, c1c = st.columns(3)
        gel_a = c1a.number_input("Altura Geladeira", 0, key="alt_gel")
        gel_l = c1b.number_input("Largura Geladeira", 0, key="lar_gel")
        gel_p = c1c.number_input("Profundidade Geladeira", 0, key="pro_gel")
        
        st.write("**Forno**")
        c2a, c2b, c2c = st.columns(3)
        for_a = c2a.number_input("Altura Forno", 0, key="alt_for")
        for_l = c2b.number_input("Largura Forno", 0, key="lar_for")
        for_p = c2c.number_input("Profundidade Forno", 0, key="pro_for")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
            st.rerun()
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce.text_input(f"Onde comprou? {i}", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce.number_input(f"Valor R$ {i}", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que foi comprado? {i}", value="0", key=f"des_{i}")

    with t5:
        st.header("5. Finalizar Auditoria")
        cliente = st.text_input("Nome do Cliente / Contrato")
        if st.button("🏁 GERAR PDF FINAL"):
            hora_fim = datetime.now()
            tempo = hora_fim - st.session_state["inicio_conferencia"]
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Final: {hora_fim.strftime('%d/%m %H:%M')} (Duração: {str(tempo).split('.')})", ln=True)

            if st.session_state["mapa_dxf_buffer"]:
                pdf.ln(5)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=180); os.remove("mapa_tmp.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            
            st.download_button("📥 BAIXAR LAUDO COMPLETO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
