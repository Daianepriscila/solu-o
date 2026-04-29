import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- INICIALIZAÇÃO DE SESSÃO ---
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []
if "mapa_dxf_buffer" not in st.session_state:
    st.session_state["mapa_dxf_buffer"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- MOTOR DE DESENHO TÉCNICO (DXF) ---
def renderizar_confronto_dxf(venda_dxf, conf_dxf):
    fig, ax = plt.subplots(figsize=(14, 8))
    def extrair_linhas(file, cor):
        try:
            with open("temp_file.dxf", "wb") as f:
                f.write(file.getbuffer())
            doc = ezdxf.readfile("temp_file.dxf")
            msp = doc.modelspace()
            for entity in msp.query('LINE LWPOLYLINE'):
                if entity.dxftype() == 'LINE':
                    start, end = entity.dxf.start, entity.dxf.end
                    ax.plot([start.x, end.x], [start.y, end.y], color=cor, alpha=0.6, lw=0.7)
            os.remove("temp_file.dxf")
        except: pass
    extrair_linhas(venda_dxf, 'red')   # Vermelho = Original
    extrair_linhas(conf_dxf, 'green') # Verde = Técnico
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- MOTOR DE COMPARAÇÃO DE LISTAS (XML) ---
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

# --- INTERFACE ---
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
    st.title("👷 Portal de Auditoria Técnica Amare")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Confronto XML/DXF", "🏠 Checklist", "🔌 Memorial Eletros", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Importação de Arquivos Técnicos")
        col1, col2 = st.columns(2)
        v_xml = col1.file_uploader("XML Venda (Original)", type=['xml'], key="vx_up")
        v_dxf = col1.file_uploader("DXF Venda (Original)", type=['dxf'], key="vd_up")
        c_xml = col2.file_uploader("XML Técnico (Conferência)", type=['xml'], key="cx_up")
        c_dxf = col2.file_uploader("DXF Técnico (Conferência)", type=['dxf'], key="cd_up")

        if v_xml and c_xml:
            saiu, entrou = comparar_xmls(v_xml, c_xml)
            cs, ce = st.columns(2)
            with cs:
                st.error("🔴 ITENS RETIRADOS")
                for s in saiu: st.write(f"- {s}")
            with ce:
                st.success("🟢 ITENS ADICIONADOS")
                for e in entrou: st.write(f"- {e}")

        if v_dxf and c_dxf:
            img_res = renderizar_confronto_dxf(v_dxf, c_dxf)
            st.image(img_res, caption="Sobreposição: Vermelho (Venda) | Verde (Conferência Técnico)", use_container_width=True)

    with tab2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica e Gás")
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Gás está acessível?"); st.checkbox("Paredes com prumo/esquadro?")
        with colB:
            st.subheader("⚡ Elétrica e Medição")
            st.checkbox("Ponto energia coifa no local?"); st.checkbox("Tomadas bancada 110cm?")
            st.checkbox("Pé-direito (3 pontos)?"); st.checkbox("Desconto granitos aplicado?")

    with tab3:
        st.header("3. Memorial de Eletros (mm)")
        
        st.subheader("❄️ Refrigeração")
        c1a, c1b, c1c = st.columns(3)
        gel_a = c1a.number_input("Altura Geladeira", 0, key="alt_gel_f")
        gel_l = c1b.number_input("Largura Geladeira", 0, key="lar_gel_f")
        gel_p = c1c.number_input("Profundidade Geladeira", 0, key="pro_gel_f")
        
        st.subheader("🔥 Cocção")
        c2a, c2b, c2c = st.columns(3)
        for_a = c2a.number_input("Altura Forno", 0, key="alt_for_f")
        for_l = c2b.number_input("Largura Forno", 0, key="lar_for_f")
        for_p = c2c.number_input("Profundidade Forno", 0, key="pro_for_f")
        
        st.subheader("⏲️ Outros")
        c3a, c3b, c3c = st.columns(3)
        mic_a = c3a.number_input("Altura Micro", 0, key="alt_mic_f")
        mic_l = c3b.number_input("Largura Micro", 0, key="lar_mic_f")
        mic_p = c3c.number_input("Profundidade Micro", 0, key="pro_mic_f")

    with tab4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce.text_input(f"Local {i}", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce.number_input(f"Valor R$ {i}", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"Descrição {i}", value="0", key=f"des_{i}")

    with tab5:
        st.header("5. Fechamento")
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
                with open("m_tmp.png", "wb") as f: f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("m_tmp.png", x=10, w=180); os.remove("m_tmp.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "MEMORIAL DE ELETROS:", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"- Geladeira: {gel_a}x{gel_l}x{gel_p} mm", ln=True)
            pdf.cell(0, 8, f"- Forno: {for_a}x{for_l}x{for_p} mm", ln=True)
            pdf.cell(0, 8, f"- Micro-ondas: {mic_a}x{mic_l}x{mic_p} mm", ln=True)

            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            
            st.download_button("📥 BAIXAR LAUDO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
