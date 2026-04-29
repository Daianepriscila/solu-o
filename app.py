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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123", "douglas_conferente": "italinea456"}

def realizar_login():
    if not st.session_state["logado"]:
        st.title("🛡️ Amare Italinea - Login")
        u = st.sidebar.text_input("Usuário")
        p = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.sidebar.error("Credenciais inválidas.")
        return False
    return True

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

    extrair_linhas(venda_dxf, 'red')   # Projeto Venda em Vermelho
    extrair_linhas(conf_dxf, 'green') # Projeto Técnico em Verde
    
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- INTERFACE PRINCIPAL ---
if realizar_login():
    st.title("👷 Portal de Auditoria Técnica Amare")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Confronto XML/DXF", "🏠 Checklist Engenharia", "🔌 Memorial Eletros", "💰 Custos Extras", "🏁 Finalizar Laudo"])

    with tab1:
        st.header("1. Importação de Arquivos Técnicos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Projeto Venda (Original)")
            v_xml = st.file_uploader("XML Venda", type=['xml'], key="v_xml_file")
            v_dxf = st.file_uploader("DXF Venda", type=['dxf'], key="v_dxf_file")
            
        with col2:
            st.subheader("Projeto Conferência (Técnico)")
            c_xml = st.file_uploader("XML Conferência", type=['xml'], key="c_xml_file")
            c_dxf = st.file_uploader("DXF Conferência", type=['dxf'], key="c_dxf_file")

        if v_dxf and c_dxf:
            with st.spinner("Sobrepondo desenhos técnicos..."):
                img_result = renderizar_confronto_dxf(v_dxf, c_dxf)
                st.image(img_result, caption="Sobreposição: Vermelho (Venda) | Verde (Conferência Técnico)", use_container_width=True)

    with tab2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica e Gás")
            st.checkbox("Caixa de gordura permite abertura do balcão?")
            st.checkbox("Registros e Sifão estão recuados para tubulação?")
            st.checkbox("Gás está acessível e seguro?")
            st.subheader("🧱 Civil e Alvenaria")
            st.checkbox("Paredes possuem prumo e esquadro?")
            st.checkbox("Drywall possui reforço de madeira?")
        with colB:
            st.subheader("⚡ Elétrica")
            st.checkbox("Ponto de energia para coifa/depurador no local?")
            st.checkbox("Tomadas bancada respeitam altura mínima (110cm)?")
            st.subheader("📐 Medições")
            st.checkbox("Pé-direito medido em 3 pontos?")
            st.checkbox("Desconto de granitos aplicado no projeto?")

    with tab3:
        st.header("3. Memorial de Eletros (Medidas em mm)")
        def input_eletro(nome, ref):
            st.write(f"**{nome}**")
            cl = st.columns(3)
            # Chaves únicas para evitar AttributeError
            alt = cl.number_input(f"Altura (mm)", 0, key=f"alt_{ref}")
            lar = cl.number_input(f"Largura (mm)", 0, key=f"lar_{ref}")
            pro = cl.number_input(f"Prof (mm)", 0, key=f"pro_{ref}")
            return f"{nome}: {alt}x{lar}x{pro} mm"
        
        e_gel = input_eletro("Geladeira", "gel")
        e_for = input_eletro("Forno", "for")
        e_mic = input_eletro("Micro-ondas", "mic")

    with tab4:
        st.header("4. Custos Extras e Adicionais")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro Extra {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce1.text_input(f"Onde comprou?", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce2.number_input(f"Valor R$", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que foi comprado?", value="0", key=f"des_{i}")

    with tab5:
        st.header("5. Fechamento e Laudo Final")
        nome_cliente = st.text_input("Nome do Cliente / Número do Contrato")
        if st.button("🏁 GERAR PDF FINAL COM CRONÔMETRO"):
            hora_fim = datetime.now()
            tempo_total = hora_fim - st.session_state["inicio_conferencia"]
            
            pdf = FPDF()
            pdf.add_page()
            
            # Título e Cronômetro
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "LAUDO DE AUDITORIA MASTER - AMARE ITALINEA", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.ln(5)
            pdf.cell(0, 8, f"Cliente: {nome_cliente}", ln=True)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Término: {hora_fim.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Duração Total da Conferência: {str(tempo_total).split('.')[0]}", ln=True)

            # Inserir Mapa DXF se gerado
            if st.session_state["mapa_dxf_buffer"]:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "CONFRONTO VISUAL DE DESENHOS (DXF):", ln=True)
                with open("mapa_tmp.png", "wb") as f:
                    f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=190)
                os.remove("mapa_tmp.png")

            # Extras e Memorial
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "DETALHAMENTO DE EXTRAS E ELETROS:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ex in st.session_state["lista_extras"]:
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | Desc: {ex['desc']}", ln=True)
            
            pdf.ln(2)
            pdf.cell(0, 8, e_gel, ln=True)
            pdf.cell(0, 8, e_for, ln=True)
            pdf.cell(0, 8, e_mic, ln=True)

            res_pdf = pdf.output(dest='S').encode('latin-1')
            st.success("Auditoria finalizada! O PDF contém as evidências visuais e financeiras.")
            st.download_button("📥 BAIXAR LAUDO COMPLETO", data=res_pdf, file_name=f"Laudo_{nome_cliente}.pdf")
