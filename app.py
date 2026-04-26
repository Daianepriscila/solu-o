import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Auditoria de Conforto Italinea", layout="wide")

st.title("🛋️ Auditor de Ergonomia e Conforto")
st.markdown("---")

# PASSO 1: IDENTIFICAÇÃO
with st.expander("📝 Identificação", expanded=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nome do Cliente")
    conferente = col2.text_input("Técnico Conferente")

# PASSO 2: CHECKLIST DE ERGONOMIA (O SEU PEDIDO)
st.header("1️⃣ Conforto e Uso Diário (Ergonomia)")
st.info("Responda pensando na circulação do cliente dentro do ambiente:")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🛌 Quarto e Circulação")
    erg1 = st.checkbox("PRATELEIRAS/AÉREOS: A altura de instalação evita que o cliente bata a cabeça ao levantar ou circular?")
    erg2 = st.checkbox("TV: Está centralizada com o eixo da cama e na altura correta para o tamanho do quarto?")
    erg3 = st.checkbox("CIRCULAÇÃO: A distância entre o pé da cama e o armário/painel permite a passagem (mín. 60cm)?")

with col_b:
    st.subheader("❄️ Climatização e Obstáculos")
    erg4 = st.checkbox("AR CONDICIONADO: O móvel/fechamento respeita a saída de ar e permite manutenção/limpeza do filtro?")
    erg5 = st.checkbox("ILUMINAÇÃO: Os armários superiores não fazem sombra na área de trabalho da bancada?")
    erg6 = st.checkbox("INTERRUPTORES: As cabeceiras ou painéis deixam as tomadas de cabeceira acessíveis?")

st.divider()

# PASSO 3: AUDITORIA TÉCNICA (HIDRÁULICA/CIVIL)
st.header("2️⃣ Segurança de Instalação (Papel de Ofício)")
c1, c2 = st.columns(2)

with c1:
    h1 = st.checkbox("Caixa de gordura e Registros estão com acesso garantido?")
    h2 = st.checkbox("A altura da bancada permite a abertura total da janela?")
    h3 = st.checkbox("O ponto de gás e esgoto foram previstos dentro do módulo?")

with c2:
    m1 = st.checkbox("Guarnição da porta: Descontou o batente para as gavetas abrirem?")
    m2 = st.checkbox("Empenamento: Prateleiras largas (>900mm) possuem reforço?")
    m3 = st.checkbox("Sustentação: Paredes de Drywall possuem reforço para suspensos?")

# PASSO 4: FINALIZAÇÃO
st.header("3️⃣ Fechamento e Laudo")
foto_papel = st.file_uploader("📷 Foto do Papel de Ofício / Croqui de Campo", type=['jpg', 'png', 'jpeg'])
obs = st.text_area("Observações Técnicas para o Montador")

if st.button("🏁 GERAR LAUDO DE CONFERÊNCIA"):
    # Requisitos: Tudo de ergonomia e segurança deve estar marcado
    erros_erg = [erg1, erg2, erg3, erg4, erg5, erg6]
    erros_tec = [h1, h2, h3, m1, m2, m3]
    
    if not (cliente and foto_papel):
        st.error("❌ Preencha o nome do cliente e anexe a foto do seu papel de medição.")
    elif not all(erros_erg) or not all(erros_tec):
        st.error("❌ SISTEMA BLOQUEADO: Você não validou todos os pontos de Ergonomia ou Segurança. Verifique os itens acima!")
    else:
        st.balloons()
        st.success("✅ Laudo aprovado! O projeto respeita as normas de conforto e engenharia.")
        
        # Geração de PDF (Estrutura Básica)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO DE AUDITORIA TÉCNICA: {cliente}", ln=True, align='C')
        pdf.output(f"Laudo_{cliente}.pdf")
        with open(f"Laudo_{cliente}.pdf", "rb") as f:
            st.download_button("📥 Baixar Relatório Final", f, file_name=f"Laudo_{cliente}.pdf")
