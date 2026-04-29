import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Amare Italinea - Auditoria", layout="wide")

if "inicio" not in st.session_state: st.session_state["inicio"] = datetime.now()
if "extras" not in st.session_state: st.session_state["extras"] = []
if "mapa" not in st.session_state: st.session_state["mapa"] = None
if "logado" not in st.session_state: st.session_state["logado"] = False

# --- 2. MOTOR VISUAL (Simplificado para Grandes Ambientes) ---
def gerar_mapa(v_dxf, c_dxf):
    fig, ax = plt.subplots(figsize=(16, 8))
    def desenhar(file, cor, peso):
        try:
            with open("t.dxf", "wb") as f: f.write(file.getbuffer())
            doc = ezdxf.readfile("t.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE LWPOLYLINE'):
                if e.dxftype() == 'LINE':
                    # Simplificação: ignora linhas muito curtas (detalhes irrelevantes)
                    if e.dxf.start.distance(e.dxf.end) > 50:
                        ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color=cor, alpha=0.5, lw=peso)
            os.remove("t.dxf")
        except: pass

    desenhar(v_dxf, 'red', 1.0)   # Projeto Venda
    desenhar(c_dxf, 'green', 0.8) # Conferência
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    st.session_state["mapa"] = buf
    return buf

# --- 3. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Login Amare")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
else:
    # --- 4. INTERFACE ---
    st.title("👷 Auditoria Master Amare")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Arquivos", "🏠 Checklist", "🔌 Eletros", "💰 Extras", "🏁 Finalizar"])

    with t1:
        st.header("1. Comparação XML/DXF")
        c1, c2 = st.columns(2)
        v_xml = c1.file_uploader("XML Venda", type=['xml'], key="vx")
        v_dxf = c1.file_uploader("DXF Venda", type=['dxf'], key="vd")
        c_xml = c2.file_uploader("XML Técnico", type=['xml'], key="cx")
        c_dxf = c2.file_uploader("DXF Técnico", type=['dxf'], key="cd")

        if v_dxf and c_dxf:
            st.image(gerar_mapa(v_dxf, c_dxf), use_container_width=True)

    with t2:
        st.header("2. Checklist")
        colA, colB = st.columns(2)
        with colA:
            h1 = st.checkbox("Caixa de gordura/Sifão ok?"); h2 = st.checkbox("Ponto de Gás ok?")
        with colB:
            e1 = st.checkbox("Elétrica bancada ok?"); m1 = st.checkbox("Pé-direito ok?")

    with t3:
        st.header("3. Memorial Eletros (mm)")
        st.write("**Geladeira**")
        ca, cb, cc = st.columns(3)
        ga = ca.number_input("Alt", 0, key="ga"); gl = cb.number_input("Larg", 0, key="gl"); gp = cc.number_input("Prof", 0, key="gp")
        st.write("**Forno**")
        cd, ce, cf = st.columns(3)
        fa = cd.number_input("Alt ", 0, key="fa"); fl = ce.number_input("Larg ", 0, key="fl"); fp = cf.number_input("Prof ", 0, key="fp")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Extra"):
            st.session_state["extras"].append({"loc": "", "val": 0.0, "des": "0"})
            st.rerun()
        
        for i, ex in enumerate(st.session_state["extras"]):
            st.markdown(f"--- Item {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["extras"][i]["loc"] = ce1.text_input(f"Onde?", key=f"l_{i}")
            st.session_state["extras"][i]["val"] = ce2.number_input(f"R$", 0.0, key=f"v_{i}")
            st.session_state["extras"][i]["des"] = st.text_area(f"O que?", key=f"d_{i}")

    with t5:
        st.header("5. Gerar Laudo")
        cliente = st.text_input("Nome do Cliente")
        if st.button("🏁 BAIXAR PDF FINAL"):
            fim = datetime.now()
            tempo = fim - st.session_state["inicio"]
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio'].strftime('%d/%m %H:%M')} | Fim: {fim.strftime('%H:%M')}", ln=True)
            pdf.cell(0, 8, f"Tempo total: {str(tempo).split('.')[0]}", ln=True)

            if st.session_state["mapa"]:
                with open("m.png", "wb") as f: f.write(st.session_state["mapa"].getbuffer())
                pdf.image("m.png", x=10, w=180); os.remove("m.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for e in st.session_state["extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {e['loc']} | R$ {e['val']} | {e['des']}", ln=True)
            
            st.download_button("📥 Clique aqui para baixar", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
