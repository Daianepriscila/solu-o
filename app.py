import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# Registro do início da conferência
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()

# --- USUÁRIOS ---
USUARIOS = {
    "michel_conferente": "italinea123",
    "matheus_conferente": "italinea456",
    "douglas_conferente": "italinea789",
    "admin": "adminamare"
}

# --- NOVA FUNÇÃO DE ANÁLISE VISUAL DIDÁTICA ---
def analisar_e_gerar_mapa(xml_venda, xml_conf):
    def extrair_pecas(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            pecas = {}
            for item in root.iter('ITEM'):
                desc = item.get('DESCRIPTION', item.get('Descricao', 'Modulo')).upper()
                
                # Captura Dimensões
                w = float(item.get('WIDTH', item.get('Largura', 0)))
                h = float(item.get('HEIGHT', item.get('Altura', 0)))
                d = float(item.get('DEPTH', item.get('Profundidade', 0)))
                
                # FILTRO DIDÁTICO: Ignora peças irrelevantes (parafusos, ferragens minúsculas)
                if w < 20 and h < 20: continue 

                try:
                    # Captura Posições
                    x = float(item.get('X', 0))
                    y = float(item.get('Y', 0))
                    z = float(item.get('Z', 0))
                    
                    # Chave baseada na posição e nome para detectar mudanças
                    pos_chave = f"{desc}_{int(x)}_{int(y)}"
                    pecas[pos_chave] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Y': y, 'Z': z}
                except: continue
            return pecas
        except: return {}

    v_pecas = extrair_pecas(xml_venda)
    c_pecas = extrair_pecas(xml_conf)

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 1. Desenha o que MUDOU ou SAIU (VERMELHO VIVO)
    for chave, p in v_pecas.items():
        if chave not in c_pecas:
            ax.bar3d(p['X'], p['Y'], p['Z'], p['W'], p['D'], p['H'], 
                     color='red', alpha=0.7, edgecolor='darkred', linewidth=0.5)

    # 2. Desenha o que está no técnico (VERDE / CINZA para paredes)
    for chave, p in c_pecas.items():
        if 'PAREDE' in p['nome'] or 'PISO' in p['nome']:
            cor = 'silver'
            opacidade = 0.1
        else:
            cor = 'green'
            opacidade = 0.3
        
        ax.bar3d(p['X'], p['Y'], p['Z'], p['W'], p['D'], p['H'], 
                 color=cor, alpha=opacidade, edgecolor=cor, linewidth=0.2)

    # Configuração de Visão Didática (Tipo Promob)
    ax.view_init(elev=25, azim=-45) 
    ax.set_axis_off() # Limpa os eixos para focar no projeto
    
    plt.title("MAPA TÉCNICO: Itens em VERMELHO indicam mudança/perda em relação à venda")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
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
        st.header("1. Confronto de Projetos (Venda vs Técnico)")
        col_v, col_c = st.columns(2)
        f_venda = col_v.file_uploader("XML Venda (Projeto)", type=['xml'])
        f_conf = col_c.file_uploader("XML Conferência (Executivo)", type=['xml'])
        
        mapa_img = None
        if f_venda and f_conf:
            mapa_img, v_dados, c_dados = analisar_e_gerar_mapa(f_venda, f_conf)
            st.image(mapa_img, use_container_width=True)
            
            st.subheader("📋 Lista de Alterações Detectadas")
            for chave, p in v_dados.items():
                if chave not in c_dados:
                    st.error(f"🔴 MUDANÇA DETECTADA: {p['nome']} (Original: L:{p['W']}mm | P:{p['D']}mm)")

    with tab2:
        st.header("2. O Olhar do Especialista")
        col1, col2 = st.columns(2)
        with col1:
            h1 = st.checkbox("CAIXA DE GORDURA: Balcão permite abertura?")
            h2 = st.checkbox("REGISTROS/SIFÃO: Recuado p/ tubulação?")
            h3 = st.checkbox("FILTRO DE ÁGUA: Há ponto de energia?")
        with col2:
            m1 = st.checkbox("GUARNIÇÃO: Puxador não bate no batente?")
            m2 = st.checkbox("DRYWALL: Possui reforço de madeira?")
            m3 = st.checkbox("PÉ-DIREITO: Medido em 3 pontos?")

    with tab3:
        st.header("3. Memorial Descritivo de Eletros")
        def input_eletro(label):
            st.markdown(f"**{label}**")
            c1, c2, c3 = st.columns(3)
            alt = c1.number_input(f"Altura (mm)", 0, key=f"a_{label}")
            larg = c2.number_input(f"Largura (mm)", 0, key=f"l_{label}")
            prof = c3.number_input(f"Profundidade (mm)", 0, key=f"p_{label}")
            return f"{label}: {alt}x{larg}x{prof} mm"

        e1 = input_eletro("Geladeira")
        e2 = input_eletro("Forno")
        e3 = input_eletro("Micro-ondas")

    with tab4:
        st.header("4. Compras Extras")
        ex_local = st.text_input("Onde comprou?", placeholder="N/A")
        ex_valor = st.number_input("Valor Pago (R$)", value=0.0)
        ex_desc = st.text_area("O que é o extra?", value="0")

    with tab5:
        st.header("5. Conclusão e Laudo")
        cliente = st.text_input("Nome do Cliente / Contrato")
        obs = st.text_area("Instruções de Montagem / Justificativas")
        
        if st.button("🏁 GERAR LAUDO PDF"):
            hora_fim = datetime.now()
            tempo_total = hora_fim - st.session_state["inicio_conferencia"]
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "LAUDO DE AUDITORIA MASTER - AMARE ITALINEA", ln=True, align='C')
            
            pdf.set_font("Arial", '', 11)
            pdf.ln(5)
            pdf.cell(0, 7, f"Cliente: {cliente}", ln=True)
            pdf.cell(0, 7, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 7, f"Término: {hora_fim.strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 7, f"Auditor Responsável: {st.session_state['nome_usuario']}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "EXTRAS E CUSTOS:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 7, f"Local: {ex_local} | Valor: R$ {ex_valor}", ln=True)
            pdf.multi_cell(0, 7, f"Descrição: {ex_desc}")

            if mapa_img:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "MAPA DE DIVERGÊNCIAS XML:", ln=True)
                img_path = "mapa_laudo.png"
                with open(img_path, "wb") as f:
                    f.write(mapa_img.getvalue())
                pdf.image(img_path, x=10, w=185)

            st.download_button("📥 BAIXAR PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
