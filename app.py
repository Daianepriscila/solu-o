import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "mapa_gerado" not in st.session_state:
    st.session_state["mapa_gerado"] = None

# --- FUNÇÃO DE LEITURA E DESENHO ---
def gerar_visualizacao_tecnica(xml_venda, xml_conf):
    def extrair_pecas(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            pecas = {}
            # Busca recursiva para achar ITENS dentro de qualquer sub-nível
            for item in root.findall(".//ITEM"):
                desc = item.get('DESCRIPTION', item.get('Descricao', 'MODULO')).upper()
                try:
                    w = float(item.get('WIDTH', 0))
                    d = float(item.get('DEPTH', 0))
                    h = float(item.get('HEIGHT', 0))
                    x = float(item.get('X', 0))
                    y = float(item.get('Y', 0))
                    
                    if w < 20 or d < 20: continue 

                    id_peca = f"{desc}_{int(x)}_{int(y)}"
                    pecas[id_peca] = {'nome': desc, 'W': w, 'D': d, 'H': h, 'X': x, 'Y': y}
                except (TypeError, ValueError):
                    continue
            return pecas
        except Exception as e:
            st.error(f"Erro ao ler XML: {e}")
            return {}

    v_pecas = extrair_pecas(xml_venda)
    c_pecas = extrair_pecas(xml_conf)

    if not v_pecas and not c_pecas:
        return None, ["Erro: Nenhuma peça detectada nos arquivos XML."]

    fig, ax = plt.subplots(figsize=(12, 8))
    mudancas_texto = []

    # 1. Paredes/Pisos (Contexto)
    for p in c_pecas.values():
        if any(x in p['nome'] for x in ['PAREDE', 'PISO', 'GEOMETRIA']):
            ax.add_patch(plt.Rectangle((p['X'], p['Y']), p['W'], p['D'], color='#EEEEEE', alpha=0.5))

    # 2. Comparação
    todas_chaves = set(v_pecas.keys()) | set(c_pecas.keys())
    for chave in todas_chaves:
        v, c = v_pecas.get(chave), c_pecas.get(chave)

        if v and (not c or (c['W'] * c['D']) < (v['W'] * v['D'])):
            ax.add_patch(plt.Rectangle((v['X'], v['Y']), v['W'], v['D'], color='red', alpha=0.6))
            mudancas_texto.append(f"🔴 RETIRADO/REDUZIDO: {v['nome']}")
        elif c and (not v or (c['W'] * c['D']) > (v['W'] * v['D'])):
            ax.add_patch(plt.Rectangle((c['X'], c['Y']), c['W'], c['D'], color='green', alpha=0.6))
            mudancas_texto.append(f"🟢 ADICIONADO/AUMENTADO: {c['nome']}")
        elif c and 'PAREDE' not in c['nome']:
            ax.add_patch(plt.Rectangle((c['X'], c['Y']), c['W'], c['D'], fill=False, edgecolor='blue', alpha=0.2))

    ax.autoscale()
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_gerado"] = buf
    return buf, mudancas_texto

# --- INTERFACE ---
st.title("🛡️ Amare Italinea - Auditoria Master")

t1, t2, t3, t4 = st.tabs(["📊 Comparativo XML", "🔌 Eletros", "💰 Extras", "🏁 Finalizar"])

with t1:
    st.header("1. Confronto de Projetos")
    c1, c2 = st.columns(2)
    f_venda = c1.file_uploader("XML Venda", type=['xml'])
    f_conf = c2.file_uploader("XML Conferência", type=['xml'])
    
    if f_venda and f_conf:
        img, lista = gerar_visualizacao_tecnica(f_venda, f_conf)
        if img:
            st.image(img, use_container_width=True)
            for item in lista: st.write(item)

with t2:
    st.header("2. Eletros (mm)")
    def input_e(nome):
        col1, col2, col3 = st.columns(3)
        a = col1.number_input(f"Alt {nome}", 0, key=f"a_{nome}")
        l = col2.number_input(f"Larg {nome}", 0, key=f"l_{nome}")
        p = col3.number_input(f"Prof {nome}", 0, key=f"p_{nome}")
        return f"{nome}: {a}x{l}x{p}mm"
    e_gel = input_e("Geladeira")
    e_for = input_e("Forno")

with t3:
    st.header("3. Extras")
    ex_local = st.text_input("Onde comprou?", "N/A")
    ex_valor = st.number_input("Valor R$", 0.0)
    ex_desc = st.text_area("O que é?", "0")

with t4:
    cliente = st.text_input("Nome do Cliente")
    if st.button("🏁 GERAR PDF FINAL"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%H:%M:%S')}", ln=True)
        pdf.cell(0, 8, f"Término: {datetime.now().strftime('%H:%M:%S')}", ln=True)
        
        pdf.ln(5)
        pdf.cell(0, 8, f"EXTRAS: R$ {ex_valor} ({ex_local})", ln=True)
        pdf.multi_cell(0, 8, f"Descrição: {ex_desc}")

        # ANEXANDO O GRÁFICO NO PDF
        if st.session_state["mapa_gerado"]:
            pdf.ln(5)
            with open("temp_mapa.png", "wb") as f:
                f.write(st.session_state["mapa_gerado"].getbuffer())
            pdf.image("temp_mapa.png", x=10, w=190)
            os.remove("temp_mapa.png")

        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 BAIXAR LAUDO", data=pdf_output, file_name=f"Laudo_{cliente}.pdf")
