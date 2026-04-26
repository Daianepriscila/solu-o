import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", page_icon="🏢", layout="wide")

# --- BANCO DE DADOS DE USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO DE AUDITORIA XML ---
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

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Auditoria Técnica")
    st.info("Sistema de Blindagem Pós-Venda. Faça o login para acessar.")
    login()
else:
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logado"] = False
        st.rerun()

    st.title("🕵️ Auditoria Master: Risco Zero Amare Italinea")
    st.write(f"Conferente Responsável: **{st.session_state['nome_usuario']}**")
    st.markdown("---")

    # --- ABAS DE TRABALHO ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Auditoria XML", 
        "💧 Hidráulica/Gás/Pedra", 
        "⚡ Elétrica/Eletros/LED", 
        "🏗️ Engenharia/Ergonomia", 
        "🏁 Lacre Final"
    ])

    # --- TAB 1: CONFRONTO XML ---
    with tab1:
        st.header("1. Validação Projeto vs. Técnico")
        c1, c2 = st.columns(2)
        f_venda = c1.file_uploader("XML do Projeto de Venda", type=['xml'])
        f_conf = c2.file_uploader("XML do Detalhamento Final (Medida Fina)", type=['xml'])
        
        xml_ok = True
        if f_venda and f_conf:
            venda = extrair_dados_xml(f_venda)
            conf = extrair_dados_xml(f_conf)
            st.subheader("🔍 Alertas de Auditoria:")
            for id_v, info in venda.items():
                if id_v not in conf:
                    st.error(f"❌ **ITEM REMOVIDO:** O módulo '{info['nome']}' sumiu no técnico!")
                    xml_ok = False
                elif conf[id_v]['cor'] != info['cor']:
                    st.warning(f"🎨 **TROCA DE COR:** '{info['nome']}' mudou de {info['cor']} para {conf[id_v]['cor']}.")
            
            st.checkbox("Confirmo que as mudanças de módulos/cores são intencionais.", key="check_xml")

    # --- TAB 2: HIDRÁULICA, GÁS E PEDRAS ---
    with tab2:
        st.header("2. Infraestrutura de Base")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💧 Água e Gás")
            h1 = st.checkbox("CAIXA DE GORDURA: Balcão permite abertura total da tampa para limpeza?")
            h2 = st.checkbox("REGISTROS: Estão acessíveis? Previu fundo falso ou furação para manutenção?")
            h3 = st.checkbox("FILTRO DE ÁGUA: Existe ponto de entrada e espaço para o aparelho/elemento?")
            h4 = st.checkbox("PONTO DE GÁS: O nicho permite a mangueira e o registro sem esmagar?")
            h5 = st.checkbox("RALO: O móvel impede o escoamento ou acesso ao ralo de limpeza?")
        with col2:
            st.subheader("🪨 Marmoraria e Aberturas")
            h6 = st.checkbox("PEDRA: A bancada já está instalada ou o móvel servirá de gabarito?")
            h7 = st.checkbox("JANELA/PEITORIL: A altura da bancada e da torneira permitem a abertura da janela?")
            h8 = st.checkbox("CUBA: A profundidade do balcão (XML) permite os grampos de fixação da cuba?")

    # --- TAB 3: ELÉTRICA, ELETROS E ILUMINAÇÃO ---
    with tab3:
        st.header("3. Energia, Equipamentos e Luz")
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("⚡ Pontos Elétricos")
            e1 = st.checkbox("TOMADAS: Estão centralizadas nos vãos de Forno/Micro/Geladeira?")
            e2 = st.checkbox("CAIXAS DE LUZ: O armário ou painel vai obstruir algum interruptor?")
            e3 = st.checkbox("PONTO DE COIFA: A altura do ponto elétrico está dentro do duto/móvel?")
        with col4:
            st.subheader("💡 Iluminação LED e Eletros")
            e4 = st.checkbox("LED PIA: Previu o canal do perfil e o furo de passagem do cabo no aéreo?")
            e5 = st.checkbox("DRIVER LED: Onde ficará o transformador? Previu local ventilado e acessível?")
            e6 = st.checkbox("RESPIRO ELETROS: Forno e Geladeira possuem ventilação traseira/lateral?")
            n_forno = st.text_input("Nicho Forno/Micro (LxA em mm)")
            n_cook = st.text_input("Nicho Cooktop (LxP em mm)")

    # --- TAB 4: ENGENHARIA, ERGONOMIA E PORTAS ---
    with tab4:
        st.header("4. Engenharia de Marcenaria e Conforto")
        col5, col6 = st.columns(2)
        with col5:
            st.subheader("🔩 Detalhamento de Montagem")
            m1 = st.checkbox("GUARNIÇÃO: Descontou o batente da porta para as gavetas abrirem?")
            m2 = st.checkbox("CORTINEIRO: Deixou 15cm de espaço para o trilho/varão da cortina?")
            m3 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos. O móvel não vai travar no teto torto?")
            m4 = st.checkbox("DIVISÓRIA DE AMBIENTE: Ferragem confirmada (Oculta ou Aparente / Italinea ou Externa)?")
            m5 = st.checkbox("EMPENAMENTO: Prateleiras largas (>900mm) possuem reforço central ou engrosso?")
            m6 = st.checkbox("DRYWALL: Confirmou se a parede tem reforço de madeira para suspensos?")
        with col6:
            st.subheader("🛌 Ergonomia e UX")
            g1 = st.checkbox("ALTURA AÉREOS: O cliente não corre risco de bater a cabeça ao levantar/circular?")
            g2 = st.checkbox("TV: Está no eixo central da cama e na altura correta para o quarto?")
            g3 = st.checkbox("AR CONDICIONADO: O móvel permite manutenção e abertura da tampa do filtro?")
            g4 = st.checkbox("CIRCULAÇÃO: Existe o mínimo de 60cm de passagem livre em corredores?")

    # --- TAB 5: FINALIZAÇÃO ---
    with tab5:
        st.header("5. Lacre de Produção Amare Italinea")
        cliente = st.text_input("Nome do Cliente / Contrato")
        foto = st.file_uploader("📷 FOTO OBRIGATÓRIA: Trena na parede ou Papel de Ofício (Medida Fina)", type=['jpg', 'png', 'jpeg'])
        obs = st.text_area("INSTRUÇÕES CRÍTICAS PARA O MONTADOR (Ex: Cuidado com registro escondido)")
        
        if st.button("🚀 GERAR LAUDO FINAL DE ENGENHARIA"):
            # Verificação de todos os campos obrigatórios para travar o erro
            checks = [h1, h2, h3, h4, h5, h6, h7, h8, e1, e2, e3, e4, e5, e6, m1, m2, m3, m4, m5, m6, g1, g2, g3, g4, foto, cliente]
            
            if not all(checks):
                st.error("❌ SISTEMA BLOQUEADO: Existem itens técnicos ou de segurança não validados. Revise todas as abas!")
            else:
                st.balloons()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA 360", ln=True, align='C')
                
                pdf.set_font("Arial", size=11)
                pdf.ln(10)
                pdf.cell(0, 10, f"Cliente: {cliente} | Conferente: {st.session_state['nome_usuario']}", ln=True)
                pdf.cell(0, 10, f"Data da Auditoria: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
                
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "RESUMO DE ENGENHARIA:", ln=True)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 7, f"Eletros - Forno: {n_forno} | Cooktop: {n_cook}\nObs: {obs}")
                
                pdf_file = f"Laudo_{cliente}.pdf"
                pdf.output(pdf_file)
                with open(pdf_file, "rb") as f:
                    st.download_button("📥 BAIXAR LAUDO PARA FÁBRICA", f, file_name=pdf_file)
