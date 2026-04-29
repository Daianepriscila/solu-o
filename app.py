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
if "mapa_buffer" not in st.session_state:
    st.session_state["mapa_buffer"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- MOTOR XML (LISTA DE PREJUÍZO) ---
def comparar_listas_xml(xml_venda, xml_conf):
    def extrair(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            return [item.get('DESCRIPTION', 'MODULO').upper() for item in root.findall(".//ITEM") if float(item.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(xml_venda), extrair(xml_conf)
    saiu = [i for i in v if i not in c]
    entrou = [i for i in c if i not in v]
    return saiu, entrou

# --- MOTOR DXF (IMAGEM DE COMPARAÇÃO) ---
def renderizar_dxf(v_dxf, c_dxf):
    fig, ax = plt.subplots(figsize=(14, 8))
    def desenhar(file, cor):
        try:
            with open("t.dxf", "wb") as f: f.write(file.getbuffer())
            doc = ezdxf.readfile("t.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE LWPOLYLINE'):
                if e.dxftype() == 'LINE':
                    ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color=cor, alpha=0.6, lw=0.8)
            os.remove("t.dxf")
        except: pass
    desenhar(v_dxf, 'red')   # Vermelho = Original
    desenhar(c_dxf, 'green') # Verde = Conferência
    ax.set_aspect('equal'); plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_buffer"] = buf
    return buf

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
    t1, t2, t3, t4, t5 = st.tabs(["📊 Comparação XML/DXF", "🏠 Checklist", "🔌 Eletros 3D", "💰 Extras", "🏁 Finalizar"])

    with t1:
        st.header("1. Confronto de Arquivos Técnicos")
        c1, c2 = st.columns(2)
        f_v_x = c1.file_uploader("XML Venda", type=['xml'], key="vx")
        f_v_d = c1.file_uploader("DXF Venda", type=['dxf'], key="vd")
        f_c_x = c2.file_uploader("XML Conferência", type=['xml'], key="cx")
        f_c_d = c2.file_uploader("DXF Conferência", type=['dxf'], key="cd")

        if f_v_x and f_c_x:
            saiu, entrou = comparar_listas_xml(f_v_x, f_c_x)
            col_s, col_e = st.columns(2)
            with col_s: 
                st.error("🔴 ITENS RETIRADOS")
                for s in saiu: st.write(f"- {s}")
            with col_e: 
                st.success("🟢 ITENS ADICIONADOS")
                for e in entrou: st.write(f"- {e}")
        
        if f_v_d and f_c_d:
            st.image(renderizar_dxf(f_v_d, f_c_d), caption="Sobreposição: Vermelho (Original) vs Verde (Técnico)")

    with t2:
        st.header("2. Checklist Engenharia")
        ca, cb = st.columns(2)
        with ca:
            st.checkbox("Caixa de gordura ok?"); st.checkbox("Registros/Sifão recuados?")
            st.checkbox("Gás seguro?"); st.checkbox("Paredes prumo/esquadro?")
        with cb:
            st.checkbox("Ponto coifa ok?"); st.checkbox("Tomadas 110cm?")
            st.checkbox("Pé-direito (3 pontos)?"); st.checkbox("Desconto granitos ok?")

    with tab3: # Memorial Eletros corrigido
        st.header("3. Memorial de Eletros (mm)")
        st.write("**Geladeira**")
        c1, c2, c3 = st.columns(3)
        g_a = c1.number_input("Alt gel", 0, key="ag"); g_l = c2.number_input("Larg gel", 0, key="lg"); g_p = c3.number_input("Prof gel", 0, key="pg")
        st.write("**Forno**")
        c4, c5, c6 = st.columns(3)
        f_a = c4.number_input("Alt for", 0, key="af"); f_l = c5.number_input("Larg for", 0, key="lf"); f_p = c6.number_input("Prof for", 0, key="pf")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce.text_input(f"Onde?", key=f"l_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce.number_input(f"Valor R$", 0.0, key=f"v_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que?", value="0", key=f"d_{i}")

    with t5:
        st.header("5. Fechamento")
        cli = st.text_input("Nome do Cliente")
        if st.button("🏁 GERAR PDF FINAL"):
            fim = datetime.now()
            tempo = fim - st.session_state["inicio_conferencia"]
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cli}", ln=True, align='C')
            pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}", ln=True)
            if st.session_state["mapa_buffer"]:
                with open("m.png", "wb") as f: f.write(st.session_state["mapa_buffer"].getbuffer())
                pdf.image("m.png", x=10, w=190); os.remove("m.png")
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            st.download_button("📥 BAIXAR LAUDO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cli}.pdf")
