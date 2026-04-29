import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E SESSÃO ---
st.set_page_config(page_title="Amare Auditoria", layout="wide")

# Inicialização segura do estado da sessão
if "inicio" not in st.session_state: st.session_state["inicio"] = datetime.now()
if "extras" not in st.session_state: st.session_state["extras"] = []
if "mapa_buffer" not in st.session_state: st.session_state["mapa_buffer"] = None
if "logado" not in st.session_state: st.session_state["logado"] = False

# --- 2. MOTOR DE DESENHO 3D (DXF) ---
def processar_dxf(v_dxf, c_dxf):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    def extrair_linhas(file, cor, alpha):
        try:
            # Salva o arquivo em disco temporariamente para o ezdxf ler
            with open("temp.dxf", "wb") as f:
                f.write(file.getbuffer())
            doc = ezdxf.readfile("temp.dxf")
            msp = doc.modelspace()
            for e in msp.query('LINE LWPOLYLINE'):
                if e.dxftype() == 'LINE':
                    # Filtro de ruído: ignora linhas minúsculas (detalhes irrelevantes)
                    if e.dxf.start.distance(e.dxf.end) > 40:
                        xs = [e.dxf.start.x, e.dxf.end.x]
                        ys = [e.dxf.start.y, e.dxf.end.y]
                        zs = [e.dxf.start.z, e.dxf.end.z]
                        ax.plot(xs, ys, zs, color=cor, alpha=alpha, lw=0.7)
            os.remove("temp.dxf")
        except:
            pass

    extrair_linhas(v_dxf, 'red', 0.4)   # Venda
    extrair_linhas(c_dxf, 'green', 0.8) # Técnico
    
    ax.view_init(elev=25, azim=45)
    ax.set_axis_off()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_buffer"] = buf
    return buf

# --- 3. MOTOR DE LISTA (XML) ---
def comparar_xmls(f1, f2):
    def extrair(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            return [i.get('DESCRIPTION', 'MODULO').upper() for i in root.findall(".//ITEM") if float(i.get('WIDTH', 0)) > 50]
        except: return []
    v, c = extrair(f1), extrair(f2)
    return [i for i in v if i not in c], [i for i in c if i not in v]

# --- 4. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Auditoria")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Dados incorretos")
else:
    # --- 5. INTERFACE ---
    st.title("👷 Portal de Auditoria Master Amare")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Arquivos", "🏠 Checklist", "🔌 Eletros", "💰 Extras (+)", "🏁 Finalizar"])

    with t1:
        st.header("1. Confronto de Projetos")
        c1, c2 = st.columns(2)
        v_xml = c1.file_uploader("XML Venda", type=['xml'], key="vx")
        v_dxf = c1.file_uploader("DXF Venda", type=['dxf'], key="vd")
        c_xml = c2.file_uploader("XML Técnico", type=['xml'], key="cx")
        c_dxf = c2.file_uploader("DXF Técnico", type=['dxf'], key="cd")

        if v_xml and c_xml:
            saiu, entrou = comparar_xmls(v_xml, c_xml)
            colS, colE = st.columns(2)
            with colS:
                st.error(f"🔴 Retirados: {len(saiu)}")
                for s in saiu: st.write(f"- {s}")
            with colE:
                st.success(f"🟢 Adicionados: {len(entrou)}")
                for e in entrou: st.write(f"- {e}")

        if v_dxf and c_dxf:
            st.image(processar_dxf(v_dxf, c_dxf), use_container_width=True)

    with t2:
        st.header("2. Checklist Engenharia")
        st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão ok?")
        st.checkbox("Ponto de Gás acessível?"); st.checkbox("Pé-direito (3 pontos) ok?")
        st.checkbox("Paredes com prumo/esquadro?"); st.checkbox("Desconto granitos aplicado?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        st.write("**Geladeira**")
        ca, cb, cc = st.columns(3)
        ga = ca.number_input("Altura", 0, key="ga"); gl = cb.number_input("Largura", 0, key="gl"); gp = cc.number_input("Prof", 0, key="gp")
        st.write("**Forno**")
        cd, ce, cf = st.columns(3)
        fa = cd.number_input("Altura ", 0, key="fa"); fl = ce.number_input("Larg ", 0, key="fl"); fp = cf.number_input("Prof ", 0, key="fp")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["extras"].append({"loc": "", "val": 0.0, "des": "0"})
            st.rerun()
        
        for i, ex in enumerate(st.session_state["extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["extras"][i]["loc"] = ce1.text_input(f"Onde?", key=f"l_{i}")
            st.session_state["extras"][i]["val"] = ce2.number_input(f"Valor R$", 0.0, key=f"v_{i}")
            st.session_state["extras"][i]["des"] = st.text_area(f"O que?", value="0", key=f"d_{i}")

    with t5:
        st.header("5. Fechamento do Laudo")
        cliente = st.text_input("Nome do Cliente")
        if st.button("🏁 GERAR PDF FINAL"):
            fim = datetime.now()
            tempo = fim - st.session_state["inicio"]
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio'].strftime('%d/%m %H:%M')} | Fim: {fim.strftime('%H:%M')}", ln=True)
            pdf.cell(0, 8, f"Tempo de Conferência: {str(tempo).split('.')}", ln=True)

            if st.session_state["mapa_buffer"]:
                pdf.ln(5)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=180); os.remove("mapa_tmp.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for e in st.session_state["extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {e['loc']} | R$ {e['val']} | {e['des']}", ln=True)
            
            st.download_button("📥 BAIXAR PDF COMPLETO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
