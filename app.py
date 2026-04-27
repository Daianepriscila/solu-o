import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import io

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO DE AUDITORIA INTELIGENTE ---
def analisar_divergencias(venda_file, conf_file):
    def extrair(file):
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        pe_direito, parede_total = 0, 0
        for i in root.iter('Item'):
            nome = i.get('Description', i.get('Descricao', 'Modulo'))
            try:
                larg = float(i.get('Width', i.get('Largura', 0)))
                alt = float(i.get('Height', i.get('Altura', 0)))
                prof = float(i.get('Depth', i.get('Profundidade', 0)))
            except:
                larg, alt, prof = 0, 0, 0
            
            cor = i.get('Material', 'Padrao')
            lado = i.get('Opening', 'N/A')
            
            itens[nome] = {'L': larg, 'A': alt, 'P': prof, 'cor': cor, 'lado': lado}
            
            if "DIREITO" in nome.upper(): 
                pe_direito = alt
            if "PAREDE" in nome.upper(): 
                parede_total += larg
        return itens, pe_direito, parede_total

    v_itens, v_pe, v_par = extrair(venda_file)
    c_itens, c_pe, c_par = extrair(conf_file)
    alertas = []

    # PONTO 1: PAREDE E PÉ-DIREITO
    if abs(v_par - c_par) >= 150 and v_par > 0:
        alertas.append(f"PAREDE: Diferença de {abs(v_par - c_par)}mm encontrada.")
    if abs(v_pe - c_pe) > 20 and v_pe > 0:
        alertas.append(f"PÉ-DIREITO: Variação de {abs(v_pe - c_pe)}mm encontrada.")

    # PONTO 2: MUDANÇAS TÉCNICAS
    for nome, info in v_itens.items():
        if nome in c_itens:
            if abs(info['L'] - c_itens[nome]['L']) > 20:
                alertas.append(f"LARGURA: '{nome}' mudou {abs(info['L']-c_itens[nome]['L'])}mm.")
            if abs(info['P'] - c_itens[nome]['P']) > 20:
                alertas.append(f"PROFUNDIDADE: '{nome}' mudou {abs(info['P']-c_itens[nome]['P'])}mm.")
            if info['cor'] != c_itens[nome]['cor']:
                alertas.append(f"COR: '{nome}' mudou de {info['cor']} para {c_itens[nome]['cor']}.")
            if info['lado'] != c_itens[nome]['lado'] and info['lado'] != 'N/A':
                alertas.append(f"ABERTURA: Lado de abertura de '{nome}' foi alterado.")
        elif "PAREDE" not in nome.upper():
            alertas.append(f"REMOÇÃO: O item '{nome}' sumiu no projeto técnico.")

    # PONTO 3: ACABAMENTOS
    vistas_v = sum(1 for n in v_itens if "PAINEL" in n.upper() or "VISTA" in n.upper())
    vistas_c = sum(1 for n in c_itens if "PAINEL" in n.upper() or "VISTA" in n.upper())
    if vistas_c < vistas_v:
        alertas.append(f"ACABAMENTO: Menos painéis/vistas que a venda ({vistas_v} vs {vistas_c}).")

    return alertas

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Portal de Auditoria")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.session_state["nome_usuario"] = u
            st.rerun()
        else:
            st.sidebar.error("Acesso Negado")
else:
    st.title(f"👨‍💻 Auditoria Master Amare: {st.session_state['nome_usuario']}")
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise XML", "🏠 Engenharia de Campo", "🔌 Eletros e Aparelhos", "🏁 Lacre Final"])

    with tab1:
        st.header("1. Inteligência de Confronto (Venda vs Conferência)")
        f_venda = st.file_uploader("XML Venda", type=['xml'])
        f_conf = st.file_uploader("XML Conferência (Técnico)", type=['xml'])
        xml_validado = False
        if f_venda and f_conf:
            questoes = analisar_divergencias(f_venda, f_conf)
            if questoes:
                st.error("⚠️ DIVERGÊNCIAS DETECTADAS NO XML (PONTOS DE RISCO):")
                respostas = []
                for i, q in enumerate(questoes):
                    respostas.append(st.text_area(f"Justificativa para: {q}", key=f"ans_{i}"))
                xml_validado = all(len(r) > 10 for r in respostas)
            else:
                st.success("✅ XMLs em conformidade absoluta.")
                xml_validado = True

    with tab2:
        st.header("2. O Olhar do Especialista (Análise de Risco na Obra)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💧 Hidráulica, Gás e Pedras")
            h1 = st.checkbox("CAIXA DE GORDURA: Balcão permite abertura?")
            h2 = st.checkbox("REGISTROS/SIFÃO: Recuado p/ tubulação?")
            h3 = st.checkbox("FILTRO DE ÁGUA: Há ponto de energia?")
            h4 = st.checkbox("JANELA/PEITORIL: Permite abertura total?")
            h5 = st.checkbox("GÁS: Acesso fácil?")
            h6 = st.checkbox("RALO: Móvel não impede escoamento?")
        with col2:
            st.subheader("🏗️ Detalhes Civis e Estrutura")
            m1 = st.checkbox("GUARNIÇÃO: Puxador não bate no batente?")
            m2 = st.checkbox("DRYWALL: Possui reforço de madeira?")
            m3 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos?")
            m4 = st.checkbox("RODAPÉ CIVIL: Previu ajuste?")
            m5 = st.checkbox("EMPENAMENTO: Prateleiras têm reforço?")

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("🛋️ Conforto e Ergonomia")
            g1 = st.checkbox("ALTURA AÉREOS: Cliente não bate a cabeça?")
            g2 = st.checkbox("TV: Eixo e altura correta?")
            g3 = st.checkbox("AR CONDICIONADO: 15cm acima?")
            g4 = st.checkbox("LED/DRIVER: Local ventilado?")
        with col4:
            st.subheader("⚙️ Ferragens e Cantos")
            f1 = st.checkbox("DIVISÓRIA: Ferragem confirmada?")
            f2 = st.checkbox("CANTO L: Previu distanciador?")

    with tab3:
        st.header("3. Memorial Descritivo de Eletros")
        st.info("Caso o cliente não possua o aparelho, mantenha em 0.")
        e1, e2, e3 = st.columns(3)
        gel_1 = e1.number_input("Largura Geladeira (mm)", value=0)
        mic_1 = e1.number_input("Largura Micro-ondas (mm)", value=0)
        for_1 = e2.number_input("Largura Forno (mm)", value=0)
        ade_1 = e2.number_input("Largura Adega (mm)", value=0)
        cer_1 = e3.number_input("Largura Cervejeira (mm)", value=0)
        aqu_1 = e3.number_input("Largura Aquecedor Torneira (mm)", value=0)

    with tab4:
        st.header("4. Lacre de Produção Amare")
        cliente = st.text_input("Nome do Cliente / Contrato")
        foto = st.file_uploader("📸 FOTO OBRIGATÓRIA: Medida Fina", type=['jpg', 'png', 'jpeg'])
        obs = st.text_area("Instruções Técnicas (O que não está no desenho)")

        if st.button("🏁 FINALIZAR E GERAR PDF"):
            valid = [h1, h2, h3, h4, h5, h6, m1, m2, m3, m4, m5, g1, g2, g3, g4, f1, f2, foto, cliente, xml_validado]
            if not all(valid):
                st.error("❌ SISTEMA BLOQUEADO: Revise as abas e justificativas.")
            else:
                st.balloons()
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA MASTER", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
                pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
                pdf.cell(0, 10, f"Auditor: {st.session_state['nome_usuario']}", ln=True)
                pdf.ln(5)
                pdf.multi_cell(0, 10, f"Observações: {obs}")
                
                # Gera PDF na memória para evitar erros de permissão no servidor
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(
                    label="📥 BAIXAR LAUDO",
                    data=pdf_bytes,
                    file_name=f"Laudo_{cliente}.pdf",
                    mime="application/pdf"
                )
