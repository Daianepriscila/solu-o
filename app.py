import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- INÍCIO DA SESSÃO ---
st.set_page_config(page_title="Amare Italinea - Auditoria 3D", layout="wide")

if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "mapa_final_buffer" not in st.session_state:
    st.session_state["mapa_final_buffer"] = None

# --- MOTOR DE RENDERIZAÇÃO TÉCNICA ---
def renderizar_confronto_xml(xml_venda, xml_conf):
    def mapear_projeto(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            objetos = {}
            # O Promob armazena em ITEM ou DADOSITEM. Buscamos de forma profunda (.//)
            for item in root.findall(".//ITEM"):
                try:
                    desc = item.get('DESCRIPTION', item.get('Descricao', 'MODULO')).upper()
                    # Dimensões Reais
                    w = float(item.get('WIDTH', 0))
                    h = float(item.get('HEIGHT', 0))
                    d = float(item.get('DEPTH', 0))
                    # Posições no Ambiente (Sistema de Coordenadas Promob)
                    x = float(item.get('X', 0))
                    y = float(item.get('Y', 0))
                    z = float(item.get('Z', 0))

                    # Filtro: Ignora itens de sistema (ferragens/tapa-furos) para limpar a imagem
                    if w < 30 or h < 30: continue 

                    id_obj = f"{int(x)}_{int(y)}_{int(z)}"
                    objetos[id_obj] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Y': y, 'Z': z, 'V': w*h*d}
                except: continue
            return objetos
        except: return {}

    venda = mapear_projeto(xml_venda)
    conf = mapear_projeto(xml_conf)

    # Gerando a Vista Técnica (Elevação Frontal para facilitar leitura)
    fig, ax = plt.subplots(figsize=(16, 9))
    dif_texto = []

    # 1. Desenha o "Fantasma" do Projeto Venda (Cinza)
    for obj in venda.values():
        ax.add_patch(plt.Rectangle((obj['X'], obj['Z']), obj['W'], obj['H'], color='#CCCCCC', alpha=0.2))

    # 2. Lógica de Alerta Visual
    todas_chaves = set(venda.keys()) | set(conf.keys())
    for k in todas_chaves:
        v, c = venda.get(k), conf.get(k)

        # RETIRADO OU DIMINUÍDO (VERMELHO)
        if v and (not c or c['V'] < v['V']):
            ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.8, edgecolor='darkred'))
            dif_texto.append(f"🔴 MUDANÇA/RETIRADA: {v['nome']}")
        
        # ADICIONADO OU AUMENTADO (VERDE)
        elif c and (not v or c['V'] > v['V']):
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.8, edgecolor='darkgreen'))
            dif_texto.append(f"🟢 ADIÇÃO/EXTRA: {c['nome']}")
        
        # MANTIDO (CONTORNO TÉCNICO)
        elif c:
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], fill=False, edgecolor='blue', alpha=0.3, linestyle='--'))

    ax.set_aspect('equal')
    ax.autoscale()
    plt.axis('off')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    st.session_state["mapa_final_buffer"] = buf
    return buf, list(set(dif_texto))

# --- INTERFACE ---
st.title("🛡️ Amare Italinea - Auditoria Master")

tabs = st.tabs(["📊 Comparativo Visual", "🔌 Eletros Reais", "💰 Extras", "🏁 Finalizar Laudo"])

with tabs[0]:
    st.subheader("1. Importação de Dados do Promob")
    c1, c2 = st.columns(2)
    f_venda = c1.file_uploader("Subir XML Venda (Arquiteto)", type=['xml'])
    f_conf = c2.file_uploader("Subir XML Conferência (Técnico)", type=['xml'])
    
    if f_venda and f_conf:
        with st.spinner("Renderizando comparação técnica..."):
            img, alertas = renderizar_confronto_xml(f_venda, f_conf)
            st.image(img, caption="MAPA DE AUDITORIA: Vermelho (Removido/Menor) | Verde (Adicionado/Maior)", use_container_width=True)
            for a in alertas:
                if "🔴" in a: st.error(a)
                else: st.success(a)

with tabs[1]:
    st.header("2. Memorial de Eletros (Medidas Reais)")
    def input_e(label):
        st.write(f"**{label}**")
        col = st.columns(3)
        a = col[0].number_input(f"Altura (mm)", 0, key=f"a_{label}")
        l = col[1].number_input(f"Largura (mm)", 0, key=f"l_{label}")
        p = col[2].number_input(f"Profundidade (mm)", 0, key=f"p_{label}")
        return f"{label}: {a}x{l}x{p} mm"
    e1 = input_e("Geladeira")
    e2 = input_e("Forno")

with tabs[2]:
    st.header("3. Compras Extras")
    v_extra = st.number_input("Valor Extra (R$)", 0.0)
    d_extra = st.text_area("O que foi comprado?", value="0")

with tabs[3]:
    st.header("4. Conclusão")
    cliente = st.text_input("Nome do Cliente / Contrato")
    if st.button("🏁 GERAR PDF COMPLETO COM IMAGEM"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO TÉCNICO DE AUDITORIA - {cliente}", ln=True, align='C')
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Início da Auditoria: {st.session_state['inicio_conferencia'].strftime('%H:%M:%S')}", ln=True)
        pdf.cell(0, 8, f"Finalização: {datetime.now().strftime('%H:%M:%S')}", ln=True)

        if st.session_state["mapa_final_buffer"]:
            pdf.ln(5)
            # Salva temporariamente para o PDF
            with open("mapa_temp.png", "wb") as f:
                f.write(st.session_state["mapa_final_buffer"].getbuffer())
            pdf.image("mapa_temp.png", x=10, w=190)
            os.remove("mapa_temp.png")
        
        pdf.ln(5)
        pdf.cell(0, 8, f"EXTRAS: R$ {v_extra}", ln=True)
        pdf.multi_cell(0, 8, f"DESCRIÇÃO: {d_extra}")

        st.download_button("📥 BAIXAR LAUDO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
