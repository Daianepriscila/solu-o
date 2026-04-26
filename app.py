import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# Configuração Master do App
st.set_page_config(page_title="Super Auditor Italinea", layout="centered")

def extrair_detalhes(file):
    if not file: return {}
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        itens = {}
        for i in root.iter('Item'):
            nome = i.get('Description', 'Módulo')
            larg = float(i.get('Width', 0))
            itens[nome] = {'largura': larg}
        return itens
    except: return {}

st.title("🚀 Super Auditor 360° Italinea")
st.write("Sistema de Blindagem Pós-Venda: Da Planta à Montagem.")

# --- ETAPA 0: QUEM É O CLIENTE ---
with st.expander("📄 Identificação do Projeto", expanded=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nome do Cliente")
    contrato = col2.text_input("Número do Contrato/Pedido")
    conferente = st.text_input("Técnico Conferente")

# --- ETAPA 1: AUDITORIA DE PROJETO (XML) ---
st.header("1️⃣ Auditoria de Itens (Venda vs Conferência)")
st.info("Suba os arquivos para comparar se algum módulo sumiu ou mudou de tamanho.")
c1, c2 = st.columns(2)
f_venda = c1.file_uploader("XML do Projeto de Venda", type=['xml'])
f_conf = c2.file_uploader("XML da Conferência Técnica", type=['xml'])

mudancas_ok = True
if f_venda and f_conf:
    venda = extrair_detalhes(f_venda)
    conf = extrair_detalhes(f_conf)
    alertas = []
    for item, dados in conf.items():
        if item in venda and venda[item]['largura'] != dados['largura']:
            alertas.append(f"📏 O módulo **{item}** mudou de {venda[item]['largura']}mm para {dados['largura']}mm.")
    
    if alertas:
        for a in alertas: st.warning(a)
        mudancas_ok = st.checkbox("Estou ciente das mudanças e confirmo que o eletro/vão ainda cabe.")

# --- ETAPA 2: ESPECIFICAÇÃO DE ELETROS E PONTOS ---
st.header("2️⃣ Eletros e Infraestrutura")
st.write("Evite que o móvel chegue e o eletro não encaixe ou a tomada esteja no local errado.")
col_e1, col_e2 = st.columns(2)
with col_e1:
    f_med = st.text_input("Medidas do Forno (LxA em mm)", placeholder="Ex: 595x590")
    c_med = st.text_input("Medidas do Cooktop (Nicho em mm)", placeholder="Ex: 560x480")
with col_e2:
    g_med = st.text_input("Largura da Geladeira (mm)", placeholder="Ex: 700")
    ponto = st.selectbox("Situação Elétrica/Hidráulica", ["Pontos Ok", "Técnico marcou p/ puxar", "Cliente vai ajustar"])

obs_ponto = st.text_area("Instrução de Ponto: (Ex: Puxar tomada 15cm para a direita)")

# --- ETAPA 3: O OLHAR TÉCNICO (CHECKLIST) ---
st.header("3️⃣ Checklist de Obra (Onde o XML não vê)")
col_a, col_b = st.columns(2)
with col_a:
    q1 = st.checkbox("GUARNIÇÃO: Porta/Gaveta abre sem bater no alisado da porta?")
    q2 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos (evita travar no gesso)?")
    q3 = st.checkbox("RALO/CANO: Altura do esgoto permite o fundo do móvel?")
with col_b:
    q4 = st.checkbox("SANCA: Os basculantes abrem sem bater no gesso?")
    q5 = st.checkbox("PRUMO: Paredes retas ou previu fechamento maior?")
    q6 = st.checkbox("CUBA: Profundidade do balcão permite grampos e torneira?")

# --- ETAPA 4: EVIDÊNCIA ---
st.header("4️⃣ Foto de Segurança")
foto = st.file_uploader("📷 Foto da Trena na parede ou marcação de pontos", type=['jpg', 'png'])

# --- BOTÃO FINAL ---
st.divider()
if st.button("🏁 FINALIZAR E GERAR LAUDO TÉCNICO"):
    checks = [q1, q2, q3, q4, q5, q6]
    if not (cliente and contrato and conferente and foto):
        st.error("❌ ERRO: Preencha a identificação e anexe a foto da trena.")
    elif not all(checks):
        st.error("❌ BLOQUEADO: Você precisa validar todos os pontos do Checklist de Obra.")
    elif not mudancas_ok:
        st.error("❌ BLOQUEADO: Confirme que está ciente das mudanças no Passo 1.")
    else:
        st.balloons()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO TÉCNICO: {cliente}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Contrato: {contrato} | Técnico: {conferente}", ln=True)
        pdf.cell(0, 10, f"Eletros - Forno/Micro: {f_med} | Cooktop: {c_med}", ln=True)
        pdf.cell(0, 10, f"Infraestrutura: {ponto}", ln=True)
        pdf.multi_cell(0, 10, f"Obs de Ponto: {obs_ponto}")
        
        pdf_name = f"Laudo_{contrato}.pdf"
        pdf.output(pdf_name)
        with open(pdf_name, "rb") as f:
            st.download_button("📥 BAIXAR PDF PARA O GERENTE", f, file_name=pdf_name)
