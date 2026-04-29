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
            # Desenha linhas e polilinhas do CAD
            for entity in msp.query('LINE LWPOLYLINE'):
                if entity.dxftype() == 'LINE':
                    start, end = entity.dxf.start, entity.dxf.end
                    ax.plot([start.x, end.x], [start.y, end.y], color=cor, alpha=0.6, lw=0.7)
            os.remove("temp_file.dxf")
        except: pass

    extrair_linhas(venda_dxf, 'red')   # Projeto Venda (Original)
    extrair_linhas(conf_dxf, 'green') # Projeto Conferência (Final Técnico)
    
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123", "douglas_conferente": "italinea456"}
if not st.session_state["logado"]:
    st.title("🛡️ Login Amare Italinea")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u.lower() in USUARIOS and USUARIOS[u.lower()] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title("👷 Portal de Auditoria Técnica Amare")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Confronto XML/DXF", "🏠 Checklist", "🔌 Memorial Eletros", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Importação de Arquivos Técnicos")
        col1, col2 = st.columns(2)
        v_dxf = col1.file_uploader("DXF Venda (Original)", type=['dxf'], key="v_dxf_f")
        c_dxf = col2.file_uploader("DXF Conferência (Técnico)", type=['dxf'], key="c_dxf_f")

        if v_dxf and c_dxf:
            with st.spinner("Sobrepondo desenhos..."):
                img_result = renderizar_confronto_dxf(v_dxf, c_dxf)
                st.image(img_result, caption="Vermelho: Venda (Original) | Verde: Técnico (Conferência)", use_container_width=True)

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
        def input_e(nome, ref):
            st.write(f"**{nome}**")
            cl = st.columns(3)
            # Chaves únicas para evitar o erro AttributeError
            a = cl.number_input(f"Alt {nome}", 0, key=f"a_{ref}")
            l = cl.number_input(f"Larg {nome}", 0, key=f"l_{ref}")
            p = cl.number_input(f"Prof {nome}", 0, key=f"p_{ref}")
            return f"{nome}: {a}x{l}x{p} mm"
        
        e_gel = input_e("Geladeira", "gel")
        e_for = input_e("Forno", "for")
        e_mic = input_e("Micro-ondas", "mic")

    with tab4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce.text_input(f"Onde comprou? {i}", key=f"loc_{i}")
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
            pdf.cell(0, 8, f"Início da Conferência: {st.session_state['inicio_conferencia'].strftime('%d/%m %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Finalização do Laudo: {hora_fim.strftime('%d/%m %H:%M')} (Duração: {str(tempo).split('.')[0]})", ln=True)

            if st.session_state["mapa_dxf_buffer"]:
                pdf.ln(5)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=180); os.remove("mapa_tmp.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "RESUMO DE EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            
            pdf.ln(5); pdf.cell(0, 10, "ELETROS:", ln=True)
            pdf.cell(0, 8, e_gel, ln=True); pdf.cell(0, 8, e_for, ln=True); pdf.cell(0, 8, e_mic, ln=True)

            st.download_button("📥 BAIXAR LAUDO COMPLETO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
