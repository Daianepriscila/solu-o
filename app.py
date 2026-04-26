import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea", page_icon="📐", layout="wide")

# --- BANCO DE DADOS DE USUÁRIOS (CORRIGIDO) ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO DE LOGIN ---
def login():
    st.sidebar.title("🔑 Acesso Amare Italinea")
    usuario = st.sidebar.text_input("Usuário", key="user_input").lower()
    senha = st.sidebar.text_input("Senha", type="password", key="pass_input")
    if st.sidebar.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = usuario
            st.rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos")

# --- INICIALIZAÇÃO DO ESTADO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- LÓGICA DE EXIBIÇÃO ---
if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Auditoria Técnica")
    st.info("Bem-vindo! Por favor, faça o login na barra lateral para continuar.")
    login()
else:
    # Barra Lateral
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logado"] = False
        st.rerun()

    st.title("🛋️ Amare Italinea: Auditor de Ergonomia e Conforto")
    st.write(f"Conferente logado: **{st.session_state['nome_usuario']}**")
    st.markdown("---")

    # --- PASSO 0: IDENTIFICAÇÃO ---
    with st.expander("📝 Identificação do Projeto", expanded=True):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nome do Cliente")
        contrato = col2.text_input("Número do Contrato")
        conferente = st.text_input("Técnico Conferente", value=st.session_state['nome_usuario'], disabled=True)

    # --- PASSO 1: ERGONOMIA E CONFORTO ---
    st.header("1️⃣ Conforto e Uso Diário (Ergonomia)")
    col_erg1, col_erg2 = st.columns(2)
    with col_erg1:
        st.subheader("🛌 Quarto e Circulação")
        erg1 = st.checkbox("A altura dos aéreos/prateleiras evita batida de cabeça?")
        erg2 = st.checkbox("A TV está no eixo da cama e na altura correta?")
        erg3 = st.checkbox("Existe passagem mínima de 60cm ao pé da cama?")
    with col_erg2:
        st.subheader("❄️ Climatização e Conectividade")
        erg4 = st.checkbox("O ar condicionado permite manutenção e saída de ar livre?")
        erg5 = st.checkbox("Os armários superiores não fazem sombra na bancada?")
        erg6 = st.checkbox("Tomadas e interruptores de cabeceira estão acessíveis?")

    # --- PASSO 2: ENGENHARIA DE CAMPO ---
    st.header("2️⃣ Engenharia de Campo e Obstáculos")
    st.warning("Consulte seu croqui (Folha de Ofício) para validar os itens abaixo:")
    
    col_tec1, col_tec2 = st.columns(2)
    with col_tec1:
        st.subheader("💧 Hidráulica e Gás")
        h1 = st.checkbox("Caixa de gordura e Registros estão com acesso fácil?")
        h2 = st.checkbox("A altura da bancada permite abertura total da janela?")
        h3 = st.checkbox("Ponto de gás e esgoto previstos dentro do módulo?")
    with col_tec2:
        st.subheader("🧱 Detalhes Civis e Montagem")
        m1 = st.checkbox("GUARNIÇÃO: Descontou o batente da porta para as gavetas?")
        m2 = st.checkbox("EMPENAMENTO: Prateleiras largas (>900mm) têm reforço?")
        m3 = st.checkbox("SUSTENTAÇÃO: Paredes de Drywall possuem reforço?")

    # --- PASSO 3: ELETROS ---
    st.header("3️⃣ Medidas de Eletros")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        n_forno = st.text_input("Medida Nicho Forno (LxA mm)")
        n_cook = st.text_input("Medida Nicho Cooktop (LxP mm)")
    with col_e2:
        f_conf = st.file_uploader("Upload do XML de Conferência (Técnico)", type=['xml'])

    # --- PASSO 4: EVIDÊNCIA ---
    st.header("4️⃣ Registro da Medida Fina")
    foto = st.file_uploader("📷 Foto Obrigatória: Papel de Ofício ou Marcação na Parede", type=['jpg', 'png', 'jpeg'])
    obs = st.text_area("Notas Técnicas para a Montagem (Instruções Extras)")

    # --- BOTÃO FINAL ---
    st.divider()
    if st.button("🏁 FINALIZAR CONFERÊNCIA E GERAR PDF"):
        # Requisitos obrigatórios
        checks = [erg1, erg2, erg3, erg4, erg5, erg6, h1, h2, h3, m1, m2, m3, foto, cliente]
        
        if not all(checks):
            st.error("❌ SISTEMA BLOQUEADO: Você deve preencher o nome do cliente, anexar a foto e marcar TODOS os itens do checklist.")
        else:
            st.balloons()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "AMARE ITALINEA - LAUDO TÉCNICO FINAL", ln=True, align='C')
            
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(0, 10, f"Cliente: {cliente} | Contrato: {contrato}", ln=True)
            pdf.cell(0, 10, f"Conferente: {st.session_state['nome_usuario']} | Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO TÉCNICO:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 7, f"- Nicho Forno: {n_forno}", ln=True)
            pdf.cell(0, 7, f"- Nicho Cooktop: {n_cook}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "OBSERVAÇÕES:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, txt=obs if obs else "Sem observações adicionais.")
            
            nome_pdf = f"Laudo_Amare_{cliente}.pdf"
            pdf.output(nome_pdf)
            
            with open(nome_pdf, "rb") as f:
                st.download_button("📥 BAIXAR LAUDO PARA O GERENTE", f, file_name=nome_pdf)
