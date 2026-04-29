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

st.set_page_config(page_title="Amare Italinea - Auditoria Master DXF", layout="wide")

# --- MOTOR DE DESENHO TÉCNICO (DXF) ---
def renderizar_confronto_dxf(venda_dxf, conf_dxf):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    def extrair_linhas(file, cor, label):
        try:
            with open("temp.dxf", "wb") as f:
                f.write(file.getbuffer())
            doc = ezdxf.readfile("temp.dxf")
            msp = doc.modelspace()
            # Filtra linhas e polilinhas do CAD
            for entity in msp.query('LINE LWPOLYLINE'):
                if entity.dxftype() == 'LINE':
                    start, end = entity.dxf.start, entity.dxf.end
                    ax.plot([start.x, end.x], [start.y, end.y], color=cor, alpha=0.6, lw=0.7, label=label)
            os.remove("temp.dxf")
        except: pass

    # Sobreposição: Vermelho (Venda) e Verde (Conferência)
    extrair_linhas(venda_dxf, 'red', 'Projeto Venda')
    extrair_linhas(conf_dxf, 'green', 'Projeto Conferência')
    
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Login Amare Italinea")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title("👷 Auditoria Master: Inteligência XML & Desenho DXF")
    
    t1, t2, t3, t4, t5 = st.tabs(["📊 Confronto XML/DXF", "🏠 Checklist Engenharia", "🔌 Memorial Eletros", "💰 Custos Extras", "🏁 Finalizar Laudo"])

    with t1:
        st.header("1. Importação de Arquivos Técnicos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Projeto Venda (Original)")
            v_xml = st.file_uploader("XML Venda", type=['xml'], key="v_xml")
            v_dxf = st.file_uploader("DXF Venda", type=['dxf'], key="v_dxf")
            
        with col2:
            st.subheader("Projeto Conferência (Técnico)")
            c_xml = st.file_uploader("XML Conferência", type=['xml'], key="c_xml")
            c_dxf = st.file_uploader("DXF Conferência", type=['dxf'], key="c_dxf")

        if v_dxf and c_dxf:
            with st.spinner("Sobrepondo desenhos técnicos..."):
                mapa_img = renderizar_confronto_dxf(v_dxf, c_dxf)
                st.image(mapa_img, caption="MAPA DE AUDITORIA: Vermelho (Original) vs Verde (Técnico)", use_container_width=True)

    with t2:
        st.header("2. Checklist de Engenharia")
        ca, cb = st.columns(2)
        with ca:
            st.subheader("💧 Hidráulica e Civil")
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Paredes possuem prumo/esquadro?"); st.checkbox("Gás está acessível?")
        with cb:
            st.subheader("⚡ Elétrica e Medição")
            st.checkbox("Ponto de energia coifa no local?"); st.checkbox("Tomadas bancada respeitam 110cm?")
            st.checkbox("Pé-direito medido em 3 pontos?"); st.checkbox("Desconto de granitos aplicado?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        def input_e(nome, r):
            st.write(f"**{nome}**")
            cl = st.columns(3)
            alt = cl.number_input(f"Altura", 0, key=f"a_{r}")
            lar = cl.number_input(f"Largura", 0, key=f"l_{r}")
            pro = cl.number_input(f"Profundidade", 0, key=f"p_{r}")
            return f"{nome}: {alt}x{lar}x{pro}mm"
        
        e_gel = input_e("Geladeira", "gel")
        e_for = input_e("Forno", "for")
        e_mic = input_e("Micro-ondas", "mic")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce1.text_input(f"Onde comprou?", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce2.number_input(f"Valor R$", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que foi comprado?", value="0", key=f"des_{i}")

    with t5:
        st.header("5. Fechamento do Laudo")
        cliente = st.text_input("Nome do Cliente / Número do Contrato")
        if st.button("🏁 GERAR PDF FINAL COM CRONÔMETRO"):
            hora_fim = datetime.now()
            tempo_total = hora_fim - st.session_state["inicio_conferencia"]
            
            pdf = FPDF()
            pdf.add_page()
            
            # Título
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "LAUDO DE AUDITORIA MASTER - AMARE ITALINEA", ln=True, align='C')
            
            # Cronômetro
            pdf.set_font("Arial", '', 10)
            pdf.ln(5)
            pdf.cell(0, 8, f"Cliente: {cliente}", ln=True)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Término: {hora_fim.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Tempo Total de Conferência: {str(tempo_total).split('.')[0]}", ln=True)

            # Mapa Visual DXF
            if st.session_state["mapa_dxf_buffer"]:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "CONFRONTO VISUAL DE DESENHOS (DXF):", ln=True)
                with open("mapa_temp.png", "wb") as f:
                    f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("mapa_temp.png", x=10, w=190)
                os.remove("mapa_temp.png")

            # Extras e Eletros
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE EXTRAS E ELETROS:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ex in st.session_state["lista_extras"]:
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            
            pdf.ln(2); pdf.cell(0, 8, e_gel, ln=True); pdf.cell(0, 8, e_for, ln=True); pdf.cell(0, 8, e_mic, ln=True)

            res_pdf = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR LAUDO COMPLETO", data=res_pdf, file_name=f"Laudo_{cliente}.pdf")
