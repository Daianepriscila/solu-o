import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DE USUÁRIOS (Login e Senha) ---
# Você pode adicionar quantos funcionários quiser aqui
USUARIOS = {
    "joao_conferente": "italinea123",
    "maria_tecnica": "conferente2024",
    "admin": "loja01"
}

def login():
    st.sidebar.title("🔑 Acesso ao Sistema")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    
    if st.sidebar.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = usuario
            st.rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos")

# --- INÍCIO DO APP ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Sistema de Auditoria Italinea")
    st.info("Por favor, faça o login na barra lateral para acessar o checklist.")
    login()
else:
    # BOTÃO DE SAIR
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logado"] = False
        st.rerun()

    st.title(f"🛋️ Auditor de Ergonomia e Conforto")
    st.write(f"Conferente logado: **{st.session_state['nome_usuario']}**")
    st.markdown("---")

    # --- O RESTANTE DO SEU CÓDIGO DO CHECKLIST VEM AQUI ABAIXO ---
    # (Mantenha toda aquela estrutura de abas, perguntas e PDF que já criamos)
    
    with st.expander("📝 Identificação", expanded=True):
        cliente = st.text_input("Nome do Cliente")
        # O nome do conferente já pode vir preenchido pelo login
        conferente = st.text_input("Técnico Conferente", value=st.session_state['nome_usuario'])

    st.header("1️⃣ Conforto e Uso Diário (Ergonomia)")
    # ... (cole aqui as perguntas do checklist anterior)
    
    # Ao gerar o PDF, você pode incluir quem foi o usuário logado que aprovou.
