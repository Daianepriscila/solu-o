import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# Registro do início da conferência para o laudo
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()

# --- USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- FUNÇÃO DE ANÁLISE E IMAGEM 3D ---
def analisar_e_gerar_mapa(xml_venda, xml_conf):
    def extrair_pecas(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            pecas = {}
            # Busca por itens no padrão Promob/Italínea
            for item in root.iter('ITEM'):
                desc = item.get('DESCRIPTION', item.get('Descricao', 'Modulo'))
                try:
                    w = float(item.get('WIDTH', item.get('Largura', 0)))
                    h = float(item.get('HEIGHT', item.get('Altura', 0)))
                    d = float(item.get('DEPTH', item.get('Profundidade', 0)))
                    x = float(item.get('X', 0))
                    y = float(item.get('Y', 0))
                    z = float(item.get('Z', 0))
                    # Chave única baseada na posição exata
                    pos_chave = f"{int(x)}_{int(y)}_{int(z)}"
                    pecas[pos_chave] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Y': y, 'Z': z}
                except: continue
            return pecas
        except: return {}

    v_pecas = extrair_pecas(xml_venda)
    c_pecas = extrair_pecas(xml_conf)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Desenha o que mudou ou saiu (VERMELHO)
    for chave, p in v_pecas.items():
        if chave not in c_pecas:
            ax.bar3d(p['X'], p['Y'], p['Z'], p['W'], p['D'], p['H'], color='red', alpha=0.5, edgecolor='black')

    # Desenha o que entrou ou ficou (VERDE)
    for chave, p in c_pecas.items():
        ax.bar3d(p['X'], p['Y'], p['Z'], p['W'], p['D'], p['H'], color='green', alpha=0.3, edgecolor='green')

    ax.set_title("Mapa de Mudanças (Vermelho: Saiu/Alterado | Verde: Conferido)")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf, v_pecas, c_pecas

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
        else: st.sidebar.error("Acesso Negado")
else:
    st.title(f"👷 Auditoria Master Amare: {st.session_state['nome_usuario']}")
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Comparação XML", "🏠 Engenharia", "🔌 Eletros", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Inteligência de Confronto (Venda vs Conferência)")
        col_v, col_c = st.columns(2)
        f_venda = col_v.file_uploader("XML Venda (Original)", type=['xml'])
        f_conf = col_c.file_uploader("XML Conferência (Técnico)", type=['xml'])
        
        mapa_img = None
        if f_venda and f_conf:
            mapa_img, v_dados, c_dados = analisar_e_gerar_mapa(f_venda, f_conf)
            st.image(mapa_img, caption="Analise Visual: Vermelho é o que foi perdido ou mudado de lugar.")
            
            # Lista de texto das diferenças
            st.subheader("📝 Diferenças Detectadas")
            for chave, p in v_dados.items():
                if chave not in c_dados:
                    st.error(f"ITEM REMOVIDO OU ALTERADO: {p['nome']} na posição X:{p['X']}")

    with tab2:
        st.header("2. Checklist de Engenharia")
        # Mantendo seus itens anteriores de hidráulica e civil...
        c1, c2 = st.columns(2)
        h1 = c1.checkbox("CAIXA DE GORDURA: Balcão permite abertura?")
        m1 = c2.checkbox("DRYWALL: Possui reforço de madeira?")
        # (Adicione os outros checkboxes aqui se desejar manter todos os 15)

    with tab3:
        st.header("3. Memorial de Eletros (Medidas Reais)")
        def input_eletro_3d(label):
            st.write(f"**{label}**")
            col1, col2, col3 = st.columns(3)
            alt = col1.number_input(f"Altura (mm)", 0, key=f"alt_{label}")
            larg = col2.number_input(f"Largura (mm)", 0, key=f"larg_{label}")
            prof = col3.number_input(f"Profundidade (mm)", 0, key=f"prof_{label}")
            return f"{label}: {alt}x{larg}x{prof} mm"

        e_gel = input_eletro_3d("Geladeira")
        e_forno = input_eletro_3d("Forno")
        e_micro = input_eletro_3d("Micro-ondas")

    with tab4:
        st.header("4. Compras Extras e Adicionais")
        extra_local = st.text_input("Onde foi comprado o extra?", placeholder="Ex: Leroy Merlin, Madeireira...")
        extra_valor = st.number_input("Valor do Extra (R$)", value=0.0, step=10.0)
        extra_desc = st.text_area("O que é esse extra?", value="0", help="Se não houver extra, deixe 0")

    with tab5:
        st.header("5. Lacre de Produção")
        cliente = st.text_input("Nome do Cliente / Contrato")
        obs = st.text_area("Instruções Técnicas Adicionais")
        
        if st.button("🏁 FINALIZAR E GERAR PDF"):
            hora_fim = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            
            # Cabeçalho
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "AMARE ITALINEA - LAUDO DE AUDITORIA MASTER", ln=True, align='C')
            pdf.ln(5)
            
            # Datas e Tempos
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"Cliente: {cliente}", ln=True)
            pdf.cell(0, 8, f"Início da Conferência: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Finalização (PDF): {hora_fim.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Auditor: {st.session_state['nome_usuario']}", ln=True)
            
            # Extras
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "CONTROLE FINANCEIRO (EXTRAS):", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"Local: {extra_local} | Valor: R$ {extra_valor}", ln=True)
            pdf.multi_cell(0, 8, f"Descrição: {extra_desc}")
            
            # Eletros
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "ESPECIFICAÇÕES DE ELETROS:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, e_gel, ln=True)
            pdf.cell(0, 8, e_forno, ln=True)
            pdf.cell(0, 8, e_micro, ln=True)

            # Imagem do Mapa 3D (Se gerada)
            if mapa_img:
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "MAPA DE DIVERGÊNCIAS (VISUAL):", ln=True)
                # Salva imagem temporária para o PDF
                img_path = "mapa_temp.png"
                with open(img_path, "wb") as f:
                    f.write(mapa_img.getvalue())
                pdf.image(img_path, x=10, w=180)

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.success("Laudo concluído com sucesso!")
            st.download_button(label="📥 BAIXAR LAUDO COMPLETO", data=pdf_bytes, file_name=f"Laudo_{cliente}.pdf")
