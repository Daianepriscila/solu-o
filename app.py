import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- USUÁRIOS ---
USUARIOS = {"michel_conferente": "italinea123", "matheus_conferente": "italinea456", "douglas_conferente": "italinea789", "admin": "adminamare"}

# --- FUNÇÃO DE AUDITORIA INTELIGENTE ---
def analisar_divergencias(venda_file, conf_file):
    def extrair(file):
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        pe_direito, parede_total = 0, 0
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            larg, alt = float(i.get('Width', 0)), float(i.get('Height', 0))
            itens[nome] = {'L': larg, 'A': alt}
            if "DIREITO" in nome.upper(): pe_direito = alt
            if "PAREDE" in nome.upper(): parede_total += larg
        return itens, pe_direito, parede_total

    v_itens, v_pe, v_par = extrair(venda_file)
    c_itens, c_pe, c_par = extrair(conf_file)
    alertas = []

    if abs(v_par - c_par) >= 150 and v_par > 0:
        alertas.append(f"🧱 PAREDE: Diferença de {abs(v_par-c_par)}mm. Verifique se o ajuste de fechamento/vistas no XML é suficiente!")
    if abs(v_pe - c_pe) > 20 and v_pe > 0:
        alertas.append(f"🚨 PÉ-DIREITO: Variação de {abs(v_pe-c_pe)}mm. Cuidado com móveis até o teto!")
    for nome, info in v_itens.items():
        if nome in c_itens and abs(info['L'] - c_itens[nome]['L']) > 20:
            alertas.append(f"📏 MÓDULO: '{nome}' mudou {abs(info['L']-c_itens[nome]['L'])}mm. Isso altera o alinhamento de frentes ou eletros?")
    return alertas

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Portal de Auditoria")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"], st.session_state["nome_usuario"] = True, u
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title(f"🕵️ Auditoria Master Amare: {st.session_state['nome_usuario']}")
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise XML", "🏠 Engenharia de Campo", "🔌 Eletros e Aparelhos", "🏁 Lacre Final"])

    with tab1:
        st.header("1. Inteligência de Confronto (Venda vs Conferência)")
        f_venda = st.file_uploader("XML Venda", type=['xml'])
        f_conf = st.file_uploader("XML Conferência", type=['xml'])
        xml_validado = True
        if f_venda and f_conf:
            questoes = analisar_divergencias(f_venda, f_conf)
            if questoes:
                st.error("🚨 DIVERGÊNCIAS DETECTADAS NO XML:")
                respostas = [st.text_area(f"Justificativa para: {q}", key=f"ans_{i}") for i, q in enumerate(questoes)]
                xml_validado = all([len(r) > 10 for r in respostas])
            else: st.success("✅ XMLs em conformidade.")

    with tab2:
        st.header("2. O Olhar do Especialista (Análise de Risco na Obra)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💧 Hidráulica, Gás e Pedras")
            h1 = st.checkbox("CAIXA DE GORDURA: Balcão permite a abertura da tampa SEM remover o móvel?")
            h2 = st.checkbox("REGISTROS/SIFÃO: O fundo do móvel foi recuado p/ tubulação (fundo falso)?")
            h3 = st.checkbox("FILTRO DE ÁGUA: Há ponto de energia e espaço livre para o aparelho?")
            h4 = st.checkbox("JANELA/PEITORIL: A altura final da pedra permite a abertura total da janela?")
            h5 = st.checkbox("GÁS: A mangueira e o registro possuem acesso fácil (não estão esmagados)?")
            h6 = st.checkbox("RALO: O móvel impede o escoamento ou acesso ao ralo de limpeza?")

        with col2:
            st.subheader("🧱 Detalhes Civis e Estrutura")
            m1 = st.checkbox("GUARNIÇÃO: O puxador ou a porta batem no alisado da porta ao abrir?")
            m2 = st.checkbox("DRYWALL: Parede de gesso possui reforço de madeira p/ móveis suspensos?")
            m3 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos p/ garantir que móvel não trave na laje?")
            m4 = st.checkbox("RODAPÉ CIVIL: Previu o recorte ou ajuste para o rodapé da casa?")
            m5 = st.checkbox("EMPENAMENTO: Prateleiras/tampos > 900mm têm reforço central ou engrosso?")

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🛌 Ergonomia e UX (Conforto)")
            g1 = st.checkbox("ALTURA AÉREOS: O cliente não bate a cabeça ao circular na cozinha?")
            g2 = st.checkbox("TV: Está no eixo da cama e na altura correta (conforto cervical)?")
            g3 = st.checkbox("AR CONDICIONADO: Há 15cm acima do móvel p/ manutenção do filtro?")
            g4 = st.checkbox("LED/DRIVER: Previu local ventilado e acessível p/ transformador do LED?")
        with col4:
            st.subheader("⚙️ Ferragens e Cantos")
            f1 = st.checkbox("DIVISÓRIA: Ferragem confirmada (Oculta ou Aparente / Italinea ou Externa)?")
            f2 = st.checkbox("CANTO L: Previu distanciador (bate-fecha) p/ puxadores não colidirem?")

    with tab3:
        st.header("3. Memorial Descritivo de Eletros")
        st.info("Caso o cliente não possua o aparelho, mantenha em 0.")
        e1, e2, e3 = st.columns(3)
        gel_l = e1.number_input("Largura Geladeira (mm)", value=0)
        mic_l = e1.number_input("Largura Micro-ondas (mm)", value=0)
        for_l = e2.number_input("Largura Forno (mm)", value=0)
        ade_l = e2.number_input("Largura Adega (mm)", value=0)
        cer_l = e3.number_input("Largura Cervejeira (mm)", value=0)
        aqu_l = e3.number_input("Largura Aquecedor Torneira (mm)", value=0)

    with tab4:
        st.header("4. Lacre de Produção Amare")
        cliente = st.text_input("Nome do Cliente / Contrato")
        foto = st.file_uploader("📷 FOTO OBRIGATÓRIA: Papel de Ofício (Medida Fina)", type=['jpg', 'png', 'jpeg'])
        obs = st.text_area("Instruções Técnicas (O que não está no desenho)")
        
        if st.button("🚀 FINALIZAR E GERAR PDF"):
            v = [h1, h2, h3, h4, h5, h6, m1, m2, m3, m4, m5, g1, g2, g3, g4, f1, f2, foto, cliente, xml_validado]
            if not all(v):
                st.error("❌ SISTEMA BLOQUEADO: Revise todas as abas e justifique as mudanças do XML.")
            else:
                st.balloons()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA MASTER", ln=True, align='C')
                pdf.output(f"Laudo_{cliente}.pdf")
                with open(f"Laudo_{cliente}.pdf", "rb") as f:
                    st.download_button("📥 BAIXAR LAUDO", f, file_name=f"Laudo_{cliente}.pdf")
