import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E ESTADO DA SESSÃO ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

if "inicio" not in st.session_state: st.session_state["inicio"] = datetime.now()
if "extras" not in st.session_state: st.session_state["extras"] = []
if "logado" not in st.session_state: st.session_state["logado"] = False
if "mapa_buffer" not in st.session_state: st.session_state["mapa_buffer"] = None

# --- 2. MOTOR DE AUDITORIA XML (LISTA DE PREJUÍZO) ---
def auditoria_xml(f1, f2):
    def extrair(file):
        try:
            tree = ET.parse(file)
            return [i.get('DESCRIPTION', 'ITEM').upper() for i in tree.getroot().findall(".//ITEM") if float(i.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(f1), extrair(f2)
    return [i for i in v if i not in c], [i for i in c if i not in v]

# --- 3. MOTOR DE DESENHO 3D (DXF) ---
def gerar_3d(v_file, c_file):
    try:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        def desenhar(file, cor, alpha):
            with open("temp.dxf", "wb") as f: f.write(file.getbuffer())
            doc = ezdxf.readfile("temp.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE'):
                if e.dxf.start.distance(e.dxf.end) > 50: # Filtro de ruído
                    ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], [e.dxf.start.z, e.dxf.end.z], color=cor, alpha=alpha, lw=1)
            os.remove("temp.dxf")

        desenhar(v_file, 'red', 0.3)   # Original (Venda)
        desenhar(c_file, 'green', 0.8) # Técnico (Conferência)
        ax.set_axis_off()
        ax.view_init(elev=20, azim=45)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120)
        st.session_state["mapa_buffer"] = buf
        return buf
    except: return None

# --- 4. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Portal Amare Italinea")
    u = st.text_input("Usuário").lower()
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.error("Acesso Negado")
else:
    # --- 5. INTERFACE ---
    st.title("👷 Auditoria de Projetos e Pós-Venda")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Confronto Técnico", "🏠 Checklist", "🔌 Eletros", "💰 Extras (+)", "🏁 Finalizar"])

    with t1:
        st.header("1. Importação e Comparação")
        c1, c2 = st.columns(2)
        v_xml = c1.file_uploader("XML Venda", type=['xml'], key="v1")
        v_dxf = c1.file_uploader("DXF Venda", type=['dxf'], key="v2")
        c_xml = c2.file_uploader("XML Técnico", type=['xml'], key="c1")
        c_dxf = c2.file_uploader("DXF Técnico", type=['dxf'], key="c2")

        if v_xml and c_xml:
            saiu, entrou = auditoria_xml(v_xml, c_xml)
            st.subheader("Diferenças lidas no XML")
            col_s, col_e = st.columns(2)
            with col_s:
                st.error(f"🔴 Retirados ({len(saiu)})")
                for s in saiu[:10]: st.write(f"- {s}")
            with col_e:
                st.success(f"🟢 Adicionados ({len(entrou)})")
                for e in entrou[:10]: st.write(f"- {e}")

        if v_dxf and c_dxf:
            st.subheader("Comparativo Visual 3D")
            st.image(gerar_3d(v_dxf, c_dxf), use_container_width=True)

    with t2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.checkbox("Pontos de água e esgoto no local?")
            st.checkbox("Caixa de gordura permite abertura?")
            st.checkbox("Paredes possuem prumo e esquadro?")
        with colB:
            st.checkbox("Tomadas bancada altura correta?")
            st.checkbox("Pé-direito medido em 3 pontos?")
            st.checkbox("Gás possui registro acessível?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        def input_e(nome, k):
            st.write(f"**{nome}**")
            cl = st.columns(3)
            a = cl.number_input("Alt", 0, key=f"a{k}")
            l = cl.number_input("Larg", 0, key=f"l{k}")
            p = cl.number_input("Prof", 0, key=f"p{k}")
            return f"{nome}: {a}x{l}x{p}mm"
        e1 = input_e("Geladeira", "gel")
        e2 = input_e("Forno", "forn")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Extra"):
            st.session_state["extras"].append({"loc": "", "val": 0.0, "des": "0"})
            st.rerun()
        
        for i, ex in enumerate(st.session_state["extras"]):
            st.markdown(f"**Registro Extra {i+1}**")
            ce1, ce2 = st.columns(2)
            st.session_state["extras"][i]["loc"] = ce1.text_input(f"Onde comprou?", key=f"l{i}")
            st.session_state["extras"][i]["val"] = ce2.number_input(f"Valor R$", 0.0, key=f"v{i}")
            st.session_state["extras"][i]["des"] = st.text_area(f"O que foi comprado?", key=f"d{i}", value="0")

    with t5:
        st.header("5. Fechamento de Laudo")
        cliente = st.text_input("Nome do Cliente")
        if st.button("🏁 GERAR LAUDO PDF FINAL"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio'].strftime('%d/%m %H:%M')} | Fim: {datetime.now().strftime('%H:%M')}", ln=True)
            
            if st.session_state["mapa_buffer"]:
                with open("map.png", "wb") as f: f.write(st.session_state["mapa_buffer"].getbuffer())
                pdf.image("map.png", x=10, w=180); os.remove("map.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for e in st.session_state["extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {e['loc']} | R$ {e['val']} | {e['des']}", ln=True)
            
            st.download_button("📥 Baixar PDF", data=pdf.output(dest='S').encode('latin-1'), file_name="Laudo_Final.pdf")
