import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E ESTADO DO APP ---
st.set_page_config(page_title="Amare - Auditoria Master", layout="wide")

if "inicio_atendimento" not in st.session_state:
    st.session_state["inicio_atendimento"] = datetime.now()
if "extras_lista" not in st.session_state:
    st.session_state["extras_lista"] = []
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- 2. MOTOR DE DESENHO (DXF 3D) ---
def gerar_mapa_confronto(v_dxf, c_dxf):
    try:
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')
        
        def desenhar(file, cor, alpha, label):
            if file is None: return
            with open("temp_audit.dxf", "wb") as f:
                f.write(file.getbuffer())
            doc = ezdxf.readfile("temp_audit.dxf")
            msp = doc.modelspace()
            # Filtro de escala para evitar travamentos
            for e in msp.query('LINE'):
                # Só desenha linhas que representam estrutura (maiores que 10cm)
                if e.dxf.start.distance(e.dxf.end) > 100:
                    ax.plot([e.dxf.start.x, e.dxf.end.x], 
                            [e.dxf.start.y, e.dxf.end.y], 
                            [e.dxf.start.z, e.dxf.end.z], color=cor, alpha=alpha, lw=1)
            os.remove("temp_audit.dxf")

        desenhar(v_dxf, 'red', 0.3, 'Venda')     # Vermelho: O que era original
        desenhar(c_dxf, 'green', 0.8, 'Técnico') # Verde: O que ficou final
        
        ax.set_axis_off()
        ax.view_init(elev=20, azim=45)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Erro ao processar desenho 3D: {e}")
        return None

# --- 3. MOTOR DE AUDITORIA FINANCEIRA (XML) ---
def auditoria_xml(f1, f2):
    def extrair(file):
        try:
            tree = ET.parse(file)
            return [i.get('DESCRIPTION', 'ITEM').upper() for i in tree.getroot().findall(".//ITEM") if float(i.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(f1), extrair(f2)
    return [i for i in v if i not in c], [i for i in c if i not in v]

# --- 4. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Sistema de Auditoria Amare")
    u = st.text_input("Usuário").lower()
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Painel"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
else:
    # --- 5. INTERFACE DO AUDITOR ---
    st.title("👷 Conferência Técnica e Financeira")
    abas = st.tabs(["📊 Arquivos", "🏠 Checklist", "🔌 Eletros", "💰 Extras", "🏁 Laudo Final"])

    with abas[0]:
        st.header("1. Upload de Projeto e Conferência")
        c1, c2 = st.columns(2)
        v_xml = c1.file_uploader("XML Venda", type=['xml'], key="vxml")
        v_dxf = c1.file_uploader("DXF Venda", type=['dxf'], key="vdxf")
        c_xml = c2.file_uploader("XML Conferência", type=['xml'], key="cxml")
        c_dxf = c2.file_uploader("DXF Conferência", type=['dxf'], key="cdxf")

        if v_xml and c_xml:
            saiu, entrou = auditoria_xml(v_xml, c_xml)
            st.subheader("Lista de Mudanças (XML)")
            col_s, col_e = st.columns(2)
            col_s.error(f"🔴 Retirados: {len(saiu)} itens")
            col_e.success(f"🟢 Adicionados: {len(entrou)} itens")
            
        if v_dxf and c_dxf:
            st.subheader("Comparativo 3D (DXF)")
            img = gerar_mapa_confronto(v_dxf, c_dxf)
            if img:
                st.image(img, use_container_width=True)
                st.session_state["img_laudo"] = img

    with abas[1]:
        st.header("2. Checklist Técnico")
        st.checkbox("Pontos de esgoto e água no local?"); st.checkbox("Gás com registro acessível?")
        st.checkbox("Paredes com prumo?"); st.checkbox("Pé-direito conferido?")

    with abas[2]:
        st.header("3. Memorial de Eletros (mm)")
        col_g1, col_g2, col_g3 = st.columns(3)
        gel_a = col_g1.number_input("Alt Geladeira", 0)
        gel_l = col_g2.number_input("Larg Geladeira", 0)
        gel_p = col_g3.number_input("Prof Geladeira", 0)

    with abas[3]:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Extra"):
            st.session_state["extras_lista"].append({"local": "", "valor": 0.0, "obs": ""})
        
        for i, item in enumerate(st.session_state["extras_lista"]):
            st.markdown(f"**Item {i+1}**")
            st.session_state["extras_lista"][i]["local"] = st.text_input(f"Onde comprou? {i}", key=f"loc{i}")
            st.session_state["extras_lista"][i]["valor"] = st.number_input(f"Valor R$ {i}", key=f"val{i}")
            st.session_state["extras_lista"][i]["obs"] = st.text_area(f"O que foi? {i}", key=f"obs{i}", value="0")

    with abas[4]:
        st.header("5. Fechamento do Laudo")
        cliente = st.text_input("Nome do Cliente")
        if st.button("🏁 GERAR PDF FINAL"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            
            # Cronômetro
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_atendimento'].strftime('%d/%m %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Finalização: {datetime.now().strftime('%d/%m %H:%M')}", ln=True)

            # Imagem do Desenho
            if "img_laudo" in st.session_state:
                with open("mapa_temp.png", "wb") as f: f.write(st.session_state["img_laudo"].getbuffer())
                pdf.image("mapa_temp.png", x=10, w=180); os.remove("mapa_temp.png")
            
            # Lista de Extras
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["extras_lista"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['obs']}", ln=True)
            
            st.download_button("📥 Baixar Laudo Completo", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
