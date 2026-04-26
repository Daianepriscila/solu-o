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

# --- FUNÇÃO DE AUDITORIA INTELIGENTE (TOLERÂNCIA 20mm) ---
def analisar_divergencias(venda_file, conf_file):
    def extrair(file):
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        pe_direito = 0
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            larg = float(i.get('Width', 0))
            alt = float(i.get('Height', 0))
            itens[nome] = {'L': larg, 'A': alt}
            if "PAREDE" in nome.upper() or "DIREITO" in nome.upper():
                pe_direito = alt
        return itens, pe_direito

    v_itens, v_pe = extrair(venda_file)
    c_itens, c_pe = extrair(conf_file)
    alertas = []

    # 1. Comparar Pé-Direito (Tolerância Estrita de 20mm)
    dif_pe = abs(v_pe - c_pe)
    if dif_pe > 20 and v_pe > 0:
        alertas.append(f"🚨 PÉ-DIREITO: Variação de {dif_pe}mm detectada (Venda: {v_pe}mm | Técnico: {c_pe}mm). Justifique a mudança:")

    # 2. Comparar Módulos (Tolerância Estrita de 20mm)
    for nome, info in v_itens.items():
        if nome in c_itens:
            dif_l = abs(info['L'] - c_itens[nome]['L'])
            if dif_l > 20:
                alertas.append(f"📏 MEDIDA: Módulo '{nome}' alterado em {dif_l}mm. Isso afeta o vão de eletros ou cubas?")
        elif "PAREDE" not in nome.upper():
            alertas.append(f"❓ REMOÇÃO: O item '{nome}' sumiu no projeto técnico. Foi acordado com o cliente?")

    return alertas

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Portal de Auditoria")
    st.info("Acesso Restrito. Faça o login para continuar.")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"], st.session_state["nome_usuario"] = True, u
            st.rerun()
        else: st.sidebar.error("Usuário ou senha incorretos")
else:
    # Interface Principal após Login
    st.title(f"🕵️ Auditoria Master Amare: {st.session_state['nome_usuario']}")
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 Auditoria XML (Inteligência)", "🏠 Engenharia de Campo", "🏁 Lacre de Produção"])

    # --- TAB 1: A INTELIGÊNCIA ---
    with tab1:
        st.header("1. Comparação Venda vs. Técnico (Tolerância 20mm)")
        f_venda = st.file_uploader("Suba o XML da Venda", type=['xml'])
        f_conf = st.file_uploader("Suba o XML da Conferência (Técnico)", type=['xml'])

        xml_validado = True
        if f_venda and f_conf:
            questoes = analisar_divergencias(f_venda, f_conf)
            if questoes:
                st.error("🚨 O SISTEMA DETECTOU DIVERGÊNCIAS ACIMA DE 20mm:")
                respostas = []
                for i, q in enumerate(questoes):
                    st.warning(q)
                    res = st.text_area(f"Justificativa para item {i+1}:", key=f"ans_{i}")
                    respostas.append(res)
                
                # Só valida se todas as justificativas tiverem texto
                xml_validado = all([len(r) > 10 for r in respostas])
                if not xml_validado:
                    st.info("👉 Descreva o motivo técnico das mudanças acima para liberar o laudo.")
            else:
                st.success("✅ Projeto técnico em total conformidade (Variação < 20mm).")

    # --- TAB 2: CHECKLIST DE ENGENHARIA COMPLETO ---
    with tab2:
        st.header("2. Detalhes Técnicos (O que o XML não vê)")
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("💧 Hidráulica, Gás e Pedras")
            h1 = st.checkbox("Caixa de gordura, Registros e Filtro de água acessíveis?")
            h2 = st.checkbox("Altura da bancada e Torneira permitem abertura da janela?")
            h3 = st.checkbox("Ponto de Gás e Esgoto previstos dentro dos nichos?")
            h4 = st.checkbox("LEDs: Perfil de LED e furação de passagem do cabo previstos?")
        with col_b:
            st.subheader("🛠️ Marcenaria e Sustentação")
            m1 = st.checkbox("GUARNIÇÃO: Descontou batente da porta para abertura de gavetas?")
            m2 = st.checkbox("PÉ-DIREITO (3 pontos): Verificou a queda de laje/gesso?")
            m3 = st.checkbox("EMPENAMENTO: Prateleiras largas (>900mm) têm reforço/engrosso?")
            m4 = st.checkbox("DIVISÓRIA: Ferragem da porta (oculta/aparente) confirmada?")
            g1 = st.checkbox("ERGONOMIA: Bater cabeça, Eixo da TV e Manutenção do Ar?")

    # --- TAB 3: FINALIZAÇÃO ---
    with tab3:
        st.header("3. Registro Final")
        cliente = st.text_input("Nome do Cliente / Contrato")
        foto = st.file_uploader("📷 FOTO OBRIGATÓRIA: Papel de Ofício (Medida Fina)", type=['jpg', 'png'])
        
        if st.button("🚀 FINALIZAR E GERAR PDF"):
            checks = [h1, h2, h3, h4, m1, m2, m3, m4, g1, foto, cliente]
            if not all(checks):
                st.error("❌ SISTEMA BLOQUEADO: Complete o checklist de engenharia e anexe a foto.")
            elif not xml_validado:
                st.error("❌ SISTEMA BLOQUEADO: Você precisa justificar as mudanças de medida no Passo 1.")
            else:
                st.balloons()
                st.success("Auditoria Amare Concluída com Sucesso!")
                # Geração de PDF (Estrutura Básica)
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE CONFERÊNCIA TÉCNICA", ln=True, align='C')
                pdf_name = f"Laudo_{cliente}.pdf"
                pdf.output(pdf_name)
                with open(pdf_name, "rb") as f:
                    st.download_button("📥 BAIXAR LAUDO PARA FÁBRICA", f, file_name=pdf_name)
