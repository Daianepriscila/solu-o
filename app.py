import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria", page_icon="🏢", layout="wide")

# --- BANCO DE DADOS DE USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO PARA EXTRAIR DADOS DETALHADOS DO XML ---
def extrair_dados_xml(file):
    if not file: return {}
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        modulos = {}
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            id_item = i.get('UniqueId', nome)
            larg = float(i.get('Width', 0))
            prof = float(i.get('Depth', 0))
            cor = i.get('Material', 'Padrão')
            modulos[id_item] = {'nome': nome, 'L': larg, 'P': prof, 'cor': cor}
        return modulos
    except: return {}

# --- FUNÇÃO DE LOGIN ---
def login():
    st.sidebar.title("🔑 Portal Amare Italinea")
    usuario = st.sidebar.text_input("Usuário", key="user_input").lower()
    senha = st.sidebar.text_input("Senha", type="password", key="pass_input")
    if st.sidebar.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = usuario
            st.rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos")

# --- INICIALIZAÇÃO DO ESTADO DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Auditoria Técnica")
    st.info("Sistema de Blindagem Pós-Venda. Faça o login para acessar.")
    login()
else:
    # Barra Lateral
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logado"] = False
        st.rerun()

    st.title("🕵️ Auditoria Master: Risco Zero Amare Italinea")
    st.write(f"Conferente Responsável: **{st.session_state['nome_usuario']}**")
    st.markdown("---")

    # --- ABAS DE TRABALHO ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Projeto (XML)", 
        "💧 Hidráulica/Gás", 
        "⚡ Elétrica/Eletros", 
        "🛠️ Engenharia/Ergonomia", 
        "🏁 Finalização"
    ])

    # --- TAB 1: CONFRONTO XML ---
    with tab1:
        st.header("1. Comparativo Venda vs. Detalhamento Técnico")
        c1, c2 = st.columns(2)
        f_venda = c1.file_uploader("XML da VENDA (O que o cliente comprou)", type=['xml'])
        f_conf = c2.file_uploader("XML do DETALHAMENTO (O que vai para fábrica)", type=['xml'])
        
        xml_confirmado = True
        if f_venda and f_conf:
            venda = extrair_dados_xml(f_venda)
            conf = extrair_dados_xml(f_conf)
            st.subheader("🔍 Alertas de Alteração:")
            for id_v, info in venda.items():
                if id_v not in conf:
                    st.error(f"❌ **SUMIU:** O módulo '{info['nome']}' foi removido do projeto técnico!")
                    xml_confirmado = False
                elif conf[id_v]['L'] != info['L']:
                    st.warning(f"📏 **MEDIDA:** '{info['nome']}' mudou de {info['L']}mm para {conf[id_v]['L']}mm.")
            
            if not xml_confirmado:
                st.checkbox("Estou ciente das remoções/alterações e confirmo que o projeto técnico está correto.", key="check_xml")
            else:
                st.success("✅ Itens de venda e conferência batem perfeitamente.")

    # --- TAB 2: HIDRÁULICA E INFRA ---
    with tab2:
        st.header("2. Pontos de Água, Gás e Acessos")
        col1, col2 = st.columns(2)
        with col1:
            h1 = st.checkbox("CAIXA DE GORDURA: O balcão da pia permite acesso para limpeza da tampa?")
            h2 = st.checkbox("REGISTROS: Estão acessíveis ou previu fundo falso/recorte no móvel?")
            h3 = st.checkbox("RALO: O móvel impede o escoamento ou manutenção no local?")
        with col2:
            h4 = st.checkbox("GÁS: Previu espaço para mangueira e registro atrás do módulo?")
            h5 = st.checkbox("JANELA/PEITORIL: A altura da bancada permite a abertura total da janela?")

    # --- TAB 3: ELÉTRICA E ELETROS ---
    with tab3:
        st.header("3. Elétrica, Calor e Medidas de Aparelhos")
        col3, col4 = st.columns(2)
        with col3:
            e1 = st.checkbox("TOMADAS: Estão centralizadas nos vãos de Forno/Micro/Geladeira?")
            e2 = st.checkbox("CAIXAS DE LUZ: Verificou se o armário vai tampar algum interruptor?")
            e3 = st.checkbox("LEDs: Previu local para esconder e ventilar o driver/transformador?")
        with col4:
            st.markdown("**Medidas Reais dos Eletros (Fina):**")
            n_forno = st.text_input("Nicho Forno (LxA mm)")
            n_cook = st.text_input("Nicho Cooktop (LxP mm)")
            e4 = st.checkbox("RESPIRO: Forno e Geladeira possuem ventilação traseira/lateral no projeto?")

    # --- TAB 4: ENGENHARIA E ERGONOMIA ---
    with tab4:
        st.header("4. Engenharia de Montagem e Conforto")
        col5, col6 = st.columns(2)
        with col5:
            st.subheader("Montagem")
            m1 = st.checkbox("GUARNIÇÃO: Descontou o alisado da porta para as gavetas abrirem?")
            m2 = st.checkbox("CORTINEIRO: Deixou o espaço de 15cm para o trilho da cortina?")
            m3 = st.checkbox("EMPENAMENTO: Prateleiras > 900mm têm reforço ou divisão?")
            m4 = st.checkbox("DRYWALL: Confirmou se a parede tem reforço para móveis suspensos?")
        with col6:
            st.subheader("Ergonomia (UX)")
            g1 = st.checkbox("ALTURA AÉREOS: O cliente não corre risco de bater a cabeça?")
            g2 = st.checkbox("TV: Está no eixo da cama e na altura correta para o quarto?")
            g3 = st.checkbox("AR CONDICIONADO: O móvel permite manutenção e limpeza do filtro?")

    # --- TAB 5: FINALIZAÇÃO ---
    with tab5:
        st.header("5. Lacre de Produção")
        cliente = st.text_input("Nome do Cliente / Contrato")
        foto = st.file_uploader("📷 FOTO OBRIGATÓRIA: Trena na parede ou Papel de Ofício", type=['jpg', 'png', 'jpeg'])
        obs = st.text_area("Instruções Técnicas para o Montador")
        
        if st.button("🚀 GERAR LAUDO FINAL DE AUDITORIA"):
            # Consolidação de todos os checklists
            obrigatorios = [h1, h2, h3, h4, h5, e1, e2, e4, m1, m2, m3, g1, g2, g3, foto, cliente]
            
            if not all(obrigatorios):
                st.error("❌ SISTEMA BLOQUEADO: Existem itens técnicos ou de segurança não validados. Revise as abas anteriores.")
            else:
                st.balloons()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA TÉCNICA", ln=True, align='C')
                # (Lógica de PDF completa aqui...)
                pdf_name = f"Auditoria_{cliente}.pdf"
                pdf.output(pdf_name)
                with open(pdf_name, "rb") as f:
                    st.download_button("📥 BAIXAR PDF PARA FÁBRICA", f, file_name=pdf_name)
