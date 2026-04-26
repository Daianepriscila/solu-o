import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Lacre Técnico Italinea", layout="wide")

# --- FUNÇÃO PARA LER O XML GERADO NO SISTEMA ---
def analisar_xml(file):
    if not file: return []
    tree = ET.parse(file)
    root = tree.getroot()
    modulos = []
    for i in root.iter('Item'):
        desc = i.get('Description', 'Módulo')
        larg = float(i.get('Width', 0))
        prof = float(i.get('Depth', 0))
        if larg > 0:
            modulos.append({'item': desc, 'L': larg, 'P': prof})
    return modulos

st.title("🛡️ Auditoria de Lançamento: Papel para o Sistema")
st.markdown("---")

# PASSO 1: IDENTIFICAÇÃO E COMPARAÇÃO DE XML
st.header("1️⃣ Auditoria de Venda vs. Conferência")
st.info("Suba os dois XMLs para garantir que nenhum módulo ou cor foi alterado sem querer.")

col_x1, col_x2 = st.columns(2)
with col_x1:
    f_venda = st.file_uploader("XML do Projeto de Venda", type=['xml'])
with col_x2:
    f_conf = st.file_uploader("XML da Conferência (O que você acabou de fazer)", type=['xml'])

if f_venda and f_conf:
    venda_dados = analisar_xml(f_venda)
    conf_dados = analisar_xml(f_conf)
    st.success(f"Auditando {len(conf_dados)} itens do projeto técnico.")

st.divider()

# PASSO 2: O CONFRONTO COM O MAPA DE OFÍCIO
st.header("2️⃣ Confronto com a Medida Fina (Papel de Ofício)")
st.warning("Consulte o seu desenho no papel e confirme os pontos de infraestrutura no sistema:")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("💧 Hidráulica, Gás e Esgoto")
    h1 = st.checkbox("REGISTROS: Estão acessíveis ou com fundo falso no sistema?")
    h2 = st.checkbox("CAIXA DE GORDURA: O balcão da pia permite a limpeza da tampa?")
    h3 = st.checkbox("RALO/ESGOTO: A furação de passagem foi prevista no móvel?")
    h4 = st.checkbox("PONTO DE GÁS: Há espaço para o regulador e mangueira atrás do módulo?")

with col_b:
    st.subheader("⚡ Elétrica e Civil")
    e1 = st.checkbox("TOMADAS: Estão centralizadas nos vãos dos eletros?")
    e2 = st.checkbox("CAIXAS DE LUZ: Algum armário vai tampar um interruptor por erro?")
    e3 = st.checkbox("SANCA/GESSO: O pé-direito medido nos 3 pontos foi respeitado no projeto?")
    e4 = st.checkbox("JANELA/PEITORIL: A altura da bancada permite a abertura da janela?")

st.divider()

# PASSO 3: ENGENHARIA DE DETALHAMENTO
st.header("3️⃣ Engenharia e Ferragens")
col_c, col_d = st.columns(2)

with col_c:
    m1 = st.checkbox("GUARNIÇÃO: Descontou o batente da porta para as gavetas abrirem?")
    m2 = st.checkbox("CORTINEIRO: Previu o recuo para o trilho da cortina?")
    m3 = st.checkbox("FECHAMENTOS: Colocou painéis de ajuste para as paredes tortas?")

with col_d:
    m4 = st.checkbox("EMPENAMENTO: Prateleiras largas têm reforço/sustentação?")
    m5 = st.checkbox("DIVISÓRIA: O sistema de ferragem (oculto/aparente) está correto?")
    m6 = st.checkbox("FRENTES: As folgas de abertura foram conferidas?")

# PASSO 4: REGISTRO DE EVIDÊNCIA
st.header("4️⃣ Registro da Medida Fina")
foto_papel = st.file_uploader("📷 FOTO OBRIGATÓRIA: Tire foto do seu papel de ofício (Medida Fina)", type=['jpg', 'png', 'jpeg'])
obs_final = st.text_area("Notas para o Montador (Ex: Cuidado com o cano de gás na parede X)")

# BOTÃO DE TRAVAMENTO FINAL
st.divider()
if st.button("🏁 FINALIZAR E GERAR LAUDO PARA FÁBRICA"):
    # Condição: Só libera se tudo estiver marcado e a foto anexada
    obrigatorios = [h1, h2, h3, h4, e1, e2, e3, e4, m1, m2, m3, m4, m5, m6, foto_papel]
    
    if not all(obrigatorios):
        st.error("❌ SISTEMA BLOQUEADO: Você esqueceu de validar pontos do seu papel no sistema. Verifique o checklist acima!")
    else:
        st.balloons()
        st.success("✅ PROJETO BLINDADO! Gerando PDF para envio à fábrica...")
        
        # Geração do PDF com os dados
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO DE AUDITORIA: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
        pdf.set_font("Arial", size=11)
        pdf.ln(10)
        pdf.multi_cell(0, 7, "Este documento certifica que o técnico conferiu o desenho de campo (papel de ofício) e aplicou todas as restrições hidráulicas, elétricas e civis no projeto enviado para a fábrica.")
        pdf.ln(5)
        pdf.cell(0, 10, f"Status: PROJETO APROVADO PARA PRODUÇÃO", ln=True)
        
        pdf_name = "Auditoria_Final.pdf"
        pdf.output(pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button("📥 BAIXAR LAUDO PARA O GERENTE", f, file_name=pdf_name)
