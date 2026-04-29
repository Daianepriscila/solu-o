import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E SESSÃO ---
st.set_page_config(page_title="Amare Italinea Master", layout="wide")

if "inicio" not in st.session_state:
    st.session_state["inicio"] = datetime.now()
if "extras" not in st.session_state:
    st.session_state["extras"] = []
if "mapa_3d" not in st.session_state:
    st.session_state["mapa_3d"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- 2. MOTORES DE AUDITORIA (XML E DXF) ---
def comparar_xmls(f1, f2):
    def extrair(file):
        try:
            tree = ET.parse(file)
            return [i.get('DESCRIPTION', 'ITEM').upper() for i in tree.getroot().findall(".//ITEM") if float(i.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(f1), extrair(f2)
    return [i for i in v if i not in c], [i for i in c if i not in v]

def gerar_desenho_3d(v_file, c_file):
    try:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        def desenhar(file, cor, alpha):
            with open("temp.dxf", "wb") as f: f.write(file.getbuffer())
            doc = ezdxf.readfile("temp.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE'):
                if e.dxf.start.distance(e.dxf.end) > 50:
                    ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], [e.dxf.start.z, e.dxf.end.z], color=cor, alpha=alpha, lw=1)
            os.remove("temp.dxf")
        desenhar(v_file, 'red', 0.3)
        desenhar(c_file, 'green', 0.8)
        ax.set_axis_off()
        ax.view_init(elev=20, azim=45)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120)
        st.session_state["mapa_3d"] = buf
        return buf
    except: return None

# --- 3. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel": "italinea123", "michel_conferente": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Portal Amare Italinea")
    u = st.text_input("Usuário").lower()
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Sistema"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.error("Dados incorretos")
else:
    # --- 4. INTERFACE ---
    st.title("👷 Auditoria Master Amare")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Arquivos (XML/DXF)", "🏠 Checklist", "🔌 Eletros", "💰 Extras (+)", "🏁 Finalizar"])

    with t1:
        st.header("1. Importação e Comparação Técnica")
        c1, c2 = st.columns(2)
        v_xml = c1.file_uploader("XML Venda", type=['xml'], key="vx")
        v_dxf = c1.file_uploader("DXF Venda", type=['dxf'], key="vd")
        c_xml = c2.file_uploader("XML Técnico", type=['xml'], key="cx")
        c_dxf = c2.file_uploader("DXF Técnico", type=['dxf'], key="cd")

        if v_xml and c_xml:
            saiu, entrou = comparar_xmls(v_xml, c_xml)
            st.subheader("Diferenças Financeiras (Peças)")
            colS, colE = st.columns(2)
            with colS:
                st.error(f"🔴 Retirados: {len(saiu)}")
                for s in saiu[:15]: st.write(f"- {s}")
            with colE:
                st.success(f"🟢 Adicionados: {len(entrou)}")
                for e in entrou[:15]: st.write(f"- {e}")

        if v_dxf and c_dxf:
            st.subheader("Comparativo Visual 3D")
            st.image(gerar_desenho_3d(v_dxf, c_dxf), use_container_width=True)

    with t2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Ponto de Gás acessível?"); st.checkbox("Paredes com prumo/esquadro?")
        with colB:
            st.checkbox("Ponto energia coifa ok?"); st.checkbox("Tomadas bancada (110cm)?")
            st.checkbox("Pé-direito (3 pontos)?"); st.checkbox("Desconto granitos aplicado?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        def input_e(nome, k):
            st.write(f"**{nome}**")
            c1, c2, c3 = st.columns(3)
            alt = c1.number_input(f"Altura", 0, key=f"a{k}")
            lar = c2.number_input(f"Largura", 0, key=f"l{k}")
            pro = c3.number_input(f"Prof", 0, key=f"p{k}")
            return f"{nome}: {alt}x{lar}x{pro}mm"
        gel = input_e("Geladeira", "gel")
        forn = input_e("Forno", "forn")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["extras"].append({"loc": "", "val": 0.0, "des": "0"})
            st.rerun()
        for i, ex in enumerate(st.session_state["extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["extras"][i]["loc"] = ce1.text_input(f"Onde?", key=f"l{i}")
            st.session_state["extras"][i]["val"] = ce2.number_input(f"Valor R$", 0.0, key=f"v{i}")
            st.session_state["extras"][i]["des"] = st.text_area(f"O que?", key=f"d{i}", value="0")

    with t5:
        st.header("5. Gerar Laudo PDF")
        cliente = st.text_input("Nome do Cliente")
        if st.button("🏁 FINALIZAR E BAIXAR PDF"):
            fim = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio'].strftime('%d/%m %H:%M')} | Fim: {fim.strftime('%H:%M')}", ln=True)
            if st.session_state["mapa_3d"]:
                with open("m.png", "wb") as f: f.write(st.session_state["mapa_3d"].getbuffer())
                pdf.image("m.png", x=10, w=180); os.remove("m.png")
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for e in st.session_state["extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {e['loc']} | R$ {e['val']} | {e['des']}", ln=True)
            st.download_button("📥 Baixar Agora", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
