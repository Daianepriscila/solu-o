import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- USUÁRIOS ---
USUARIOS = {"michel_conferente": "italinea123", "matheus_conferente": "italinea456", "douglas_conferente": "italinea789", "admin": "adminamare"}

# --- FUNÇÃO DE AUDITORIA INTELIGENTE ---
def analisar_divergencias(venda_file, conf_file):
    def extrair(file):
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        pe_direito = 0
        parede_total = 0
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            larg = float(i.get('Width', 0))
            alt = float(i.get('Height', 0))
            itens[nome] = {'L': larg, 'A': alt}
            
            # Captura Pé-Direito e Medida Total de Parede
            if "DIREITO" in nome.upper(): pe_direito = alt
            if "PAREDE" in nome.upper(): parede_total += larg
            
        return itens, pe_direito, parede_total

    v_itens, v_pe, v_par = extrair(venda_file)
    c_itens, c_pe, c_par = extrair(conf_file)
    alertas = []

    # 1. Alerta de Parede (Tolerância 150mm / 15cm)
    dif_par = abs(v_par - c_par)
    if dif_par >= 150 and v_par > 0:
        alertas.append(f"🧱 PAREDE: Diferença CRÍTICA de {dif_par}mm na largura da parede (Venda: {v_par}mm | Real: {c_par}mm).")

    # 2. Alerta de Pé-Direito (Tolerância 20mm e Aviso de 15cm)
    dif_pe = abs(v_pe - c_pe)
    if dif_pe >= 150:
        alertas.append(f"🚨 PÉ-DIREITO CRÍTICO: Diferença maior que 15cm detectada ({dif_pe}mm). Verifique o gesso/laje!")
    elif dif_pe > 20 and v_pe > 0:
        alertas.append(f"🚨 PÉ-DIREITO: Variação de {dif_pe}mm detectada. Justifique o desnível:")

    # 3. Alerta de Módulos (Tolerância 20mm)
    for nome, info in v_itens.items():
        if nome in c_itens:
            dif_l = abs(info['L'] - c_itens[nome]['L'])
            if dif_l > 20:
                alertas.append(f"📏 MÓDULO: '{nome}' alterado em {dif_l}mm. O vão de eletros foi conferido?")
    
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
    st.title(f"🕵️ Auditoria Master: {st.session_state['nome_usuario']}")
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise XML", "🏠 Engenharia de Campo", "🔌 Eletros e Aparelhos", "🏁 Lacre Final"])

    with tab1:
        st.header("1. Comparação Automática (Tolerância: Parede 15cm / Móvel 2cm)")
        file_venda = st.file_uploader("XML Venda", type=['xml'])
        file_conf = st.file_uploader("XML Conferência", type=['xml'])

        xml_validado = True
        if file_venda and file_conf:
            questoes = analisar_divergencias(file_venda, file_conf)
            if questoes:
                st.error("🚨 DIVERGÊNCIAS DETECTADAS NO PROJETO:")
                respostas = []
                for i, q in enumerate(questoes):
                    st.warning(q)
                    res = st.text_area(f"Justificativa Técnica para: {q[:30]}...", key=f"ans_{i}")
                    respostas.append(res)
                xml_validado = all([len(r) > 10 for r in respostas])
            else:
                st.success("✅ Projeto em conformidade técnica.")

    with tab2:
        st.header("2. O Olhar do Especialista (Folha de Ofício)")
        c1, c2 = st.columns(2)
        with c1:
            h1 = st.checkbox("Caixa de Gordura, Registros e Filtro de água acessíveis?")
            h2 = st.checkbox("Altura da bancada permite abertura da janela/torneira?")
            h3 = st.checkbox("Ponto de Gás e Esgoto previstos nos nichos?")
            h4 = st.checkbox("LEDs: Perfil e furação de passagem de cabos previstos?")
        with c2:
            m1 = st.checkbox("GUARNIÇÃO: Gavetas e portas abrem sem bater no batente?")
            m2 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos p/ checar queda de laje?")
            m3 = st.checkbox("EMPENAMENTO: Reforço em prateleiras largas (>900mm)?")
            g1 = st.checkbox("ERGONOMIA: Bater cabeça, Eixo da TV e Filtro do Ar?")

    with tab3:
        st.header("3. Medidas de Eletros e Aparelhos")
        st.info("Caso o cliente não possua o aparelho, preencha com 0.")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            geladeira = st.number_input("Largura Geladeira (mm)", value=0)
            microondas = st.number_input("Largura Micro-ondas (mm)", value=0)
            forno = st.number_input("Largura Forno (mm)", value=0)
        with col_e2:
            adega = st.number_input("Largura Adega (mm)", value=0)
            cervejeira = st.number_input("Largura Cervejeira (mm)", value=0)
            aquecedor = st.number_input("Largura Aquecedor de Água (mm)", value=0)
        with col_e3:
            st.write("**Instruções:**")
            st.caption("Verifique se as medidas acima batem com os vãos deixados no projeto técnico.")

    with tab4:
        st.header("4. Registro e Geração de Laudo")
        cliente = st.text_input("Cliente / Contrato")
        foto = st.file_uploader("📷 Foto Obrigatória: Papel de Ofício (Medida Fina)", type=['jpg', 'png'])
        
        if st.button("🚀 FINALIZAR E GERAR PDF AMARE"):
            if not cliente or not foto or not xml_validado:
                st.error("❌ SISTEMA BLOQUEADO: Verifique se justificou as mudanças do XML e anexou a foto.")
            elif not (h1 and h2 and h3 and h4 and m1 and m2 and m3 and g1):
                st.error("❌ SISTEMA BLOQUEADO: Complete o checklist de engenharia.")
            else:
                st.balloons()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA", ln=True, align='C')
                pdf.set_font("Arial", size=10)
                pdf.ln(10)
                pdf.cell(0, 10, f"Cliente: {cliente} | Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
                
                pdf_name = f"Laudo_{cliente}.pdf"
                pdf.output(pdf_name)
                with open(pdf_name, "rb") as f:
                    st.download_button("📥 BAIXAR LAUDO", f, file_name=pdf_name)
