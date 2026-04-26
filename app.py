import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Checklist Italinea", page_icon="📐")

# --- ESTILIZAÇÃO CSS PARA PARECER UM APP ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #D32F2F; color: white; }
    .stCheckbox { background: white; padding: 10px; border-radius: 5px; margin-bottom: 5px; box-shadow: 1px 1px 3px #ccc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Sistema Anti-Erro Pós-Venda")
st.subheader("Conferência Técnica Obrigatória - Italinea")

# --- 1. IDENTIFICAÇÃO ---
col_a, col_b = st.columns(2)
with col_a:
    cliente = st.text_input("Nome do Cliente / Contrato")
with col_b:
    tecnico = st.text_input("Técnico Responsável")

st.divider()

# --- 2. ANÁLISE AUTOMÁTICA DO XML ---
st.header("1. Análise do Arquivo (XML)")
xml_file = st.file_uploader("Upload do XML do Projeto", type=['xml'])

alertas_xml = []
if xml_file:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Exemplo de lógica: Procura módulos com medidas suspeitas ou sem descrição
        for item in root.iter('Item'):
            desc = item.get('Description', 'Sem Nome')
            largura = float(item.get('Width', 0))
            prof = float(item.get('Depth', 0))
            
            # Alerta: Profundidade muito baixa para balcões de pia
            if "PIÁ" in desc.upper() and prof < 500:
                alertas_xml.append(f"⚠️ Alerta: {desc} com profundidade baixa ({prof}mm). Verifique a cuba!")
            
            # Alerta: Itens com medida ZERO (Erro comum de inserção)
            if largura <= 0:
                alertas_xml.append(f"❌ Erro Crítico: {desc} está com largura ZERO no XML!")

        if alertas_xml:
            for erro in alertas_xml:
                st.error(erro)
        else:
            st.success("✅ Nenhuma inconsistência técnica detectada no XML.")
    except Exception as e:
        st.error(f"Erro ao ler XML: {e}")

st.divider()

# --- 3. CHECKLIST HUMANO (TRAVAMENTO) ---
st.header("2. Conferência de Campo")
st.info("O técnico DEVE marcar todos os itens abaixo após conferência física no local.")

c1 = st.checkbox("Conferi as medidas de parede com trena laser e batem com o projeto?")
c2 = st.checkbox("Prumo e esquadro das paredes foram verificados?")
c3 = st.checkbox("Pontos de hidráulica, gás e esgoto estão na posição correta?")
c4 = st.checkbox("As tomadas de eletros (forno, micro, coifa) estão no local certo?")
c5 = st.checkbox("Verifiquei se há rodapés, molduras ou sancas que impedem a montagem?")
c6 = st.checkbox("O sentido do veio do MDF e as cores das frentes foram confirmados?")

st.divider()

# --- 4. GERAÇÃO DO RELATÓRIO PDF ---
st.header("3. Finalização")
obs = st.text_area("Observações Técnicas Extras")

# Botão para processar tudo
if st.button("GERAR RELATÓRIO PARA ENVIO"):
    if not cliente or not tecnico:
        st.error("Preencha o nome do cliente e do técnico!")
    elif not (c1 and c2 and c3 and c4 and c5 and c6):
        st.error("❌ BLOQUEADO: Você deve marcar todos os itens do checklist para prosseguir!")
    else:
        # Criando o PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="RELATÓRIO DE CONFERÊNCIA TÉCNICA", ln=True, align='C')
        
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
        pdf.cell(200, 10, txt=f"Técnico: {tecnico}", ln=True)
        pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Itens Verificados e Confirmados:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt="- Medidas de parede\n- Prumo e Esquadro\n- Pontos de Hidráulica/Gás\n- Posicionamento de Tomadas\n- Interferências (Sancas/Rodapés)\n- Sentido do Veio e Cores")
        
        if alertas_xml:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Alertas do XML (Atenção):", ln=True)
            pdf.set_font("Arial", size=10)
            for a in alertas_xml:
                pdf.multi_cell(0, 8, txt=f"- {a}")

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Observações do Técnico:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 8, txt=obs if obs else "Nenhuma observação.")

        # Salvar e disponibilizar download
        pdf_output = "Relatorio_Conferencia.pdf"
        pdf.output(pdf_output)
        
        with open(pdf_output, "rb") as file:
            st.download_button(
                label="📥 BAIXAR RELATÓRIO PDF",
                data=file,
                file_name=f"Conferencia_{cliente}.pdf",
                mime="application/pdf"
            )
        st.success("Relatório gerado com sucesso! Baixe o arquivo acima e envie para a gerência.")
