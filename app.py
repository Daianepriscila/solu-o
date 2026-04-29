import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# Inicializa o tempo de início se não existir
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()

# --- USUÁRIOS (Mantido) ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}

# --- FUNÇÃO DE EXTRAÇÃO MELHORADA (Captura Posição) ---
def extrair_detalhado(file):
    tree = ET.parse(file)
    root = tree.getroot()
    itens = {}
    for i in root.iter('Item'):
        nome = i.get('Description', i.get('Descricao', 'Modulo'))
        try:
            # Dimensões
            l = float(i.get('Width', 0))
            a = float(i.get('Height', 0))
            p = float(i.get('Depth', 0))
            # Posição (Essencial para a imagem)
            x = float(i.get('X', 0))
            y = float(i.get('Y', 0))
            z = float(i.get('Z', 0))
        except:
            continue
        
        # Chave única baseada na posição para saber se é o mesmo lugar
        chave = f"{x}_{y}_{z}"
        itens[chave] = {'nome': nome, 'L': l, 'A': a, 'P': p, 'X': x, 'Y': y, 'Z': z}
    return itens

# --- FUNÇÃO DO MAPA VISUAL ---
def gerar_mapa_mudancas(itens_venda, itens_conf):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    # Itens que sumiram ou mudaram (VERMELHO)
    for chave, info in itens_venda.items():
        if chave not in itens_conf:
            ax.bar3d(info['X'], info['Y'], info['Z'], info['L'], info['P'], info['A'], 
                     color='red', alpha=0.5, edgecolor='black')
            
    # Itens novos ou confirmados (VERDE)
    for chave, info in itens_conf.items():
        color = 'green' if chave in itens_venda else 'blue' # Azul se for algo totalmente novo
        ax.bar3d(info['X'], info['Y'], info['Z'], info['L'], info['P'], info['A'], 
                 color=color, alpha=0.3)

    ax.set_title("MAPA DE MUDANÇAS (Vermelho = Removido/Alterado | Verde = Técnico)")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# --- LÓGICA DE LOGIN (Sua original) ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if not st.session_state["logado"]:
    # ... (Seu código de login aqui)
    st.title("🛡️ Amare Italinea")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análise XML/3D", "🏠 Engenharia", "🔌 Eletros", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Confronto de Projetos (Venda vs Técnico)")
        f_venda = st.file_uploader("XML Venda (Original)", type=['xml'])
        f_conf = st.file_uploader("XML Conferência (Final)", type=['xml'])
        
        if f_venda and f_conf:
            v_itens = extrair_detalhado(f_venda)
            c_itens = extrair_detalhado(f_conf)
            img_mapa = gerar_mapa_mudancas(v_itens, c_itens)
            st.image(img_mapa, use_container_width=True)
            st.warning("Peças em VERMELHO indicam que o projeto original foi alterado naquela posição.")

    with tab3:
        st.header("3. Memorial de Eletros (Medidas Reais)")
        def campo_eletro(label):
            st.subheader(label)
            c1, c2, c3 = st.columns(3)
            alt = c1.number_input(f"Altura {label} (mm)", 0, key=f"a_{label}")
            larg = c2.number_input(f"Largura {label} (mm)", 0, key=f"l_{label}")
            prof = c3.number_input(f"Prof {label} (mm)", 0, key=f"p_{label}")
            return f"{label}: {alt}x{larg}x{prof}"

        eletros_resumo = []
        eletros_resumo.append(campo_eletro("Geladeira"))
        eletros_resumo.append(campo_eletro("Forno"))
        eletros_resumo.append(campo_eletro("Micro-ondas"))

    with tab4:
        st.header("4. Custos Extras")
        col_ex1, col_ex2 = st.columns(2)
        extra_local = col_ex1.text_input("Onde comprou?", placeholder="Ex: Loja de Ferragens")
        extra_valor = col_ex2.number_input("Valor do Extra (R$)", value=0.0)
        extra_desc = st.text_area("O que é esse extra?", value="0")

    with tab5:
        st.header("5. Lacre Final")
        cliente = st.text_input("Nome do Cliente / Contrato")
        if st.button("🏁 FINALIZAR E GERAR PDF"):
            # Lógica de geração de PDF com tempos
            hora_fim = datetime.now()
            tempo_total = hora_fim - st.session_state["inicio_conferencia"]
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "LAUDO DE AUDITORIA MASTER - AMARE", ln=True, align='C')
            
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Final: {hora_fim.strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Cliente: {cliente}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE EXTRAS:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"Local: {extra_local} | Valor: R$ {extra_valor}", ln=True)
            pdf.multi_cell(0, 8, f"Descrição: {extra_desc}")
            
            # Adicionando os eletros detalhados
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "MEDIDAS DE ELETROS:", ln=True)
            pdf.set_font("Arial", '', 11)
            for e in eletros_resumo:
                pdf.cell(0, 8, e, ln=True)

            # Aqui você anexaria a imagem do mapa (gerada no Tab1)
            
            st.balloons()
            st.download_button("📥 BAIXAR LAUDO FINAL", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
