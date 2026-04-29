import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- CONFIGURAÇÃO E LOGIN ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "mapa_img" not in st.session_state:
    st.session_state["mapa_img"] = None
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []

USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}

# --- MOTOR DE LEITURA XML (O "CÉREBRO" DO PROMOB) ---
def analisar_xml_promob(xml_venda, xml_conf):
    def extrair_dados(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            pecas = {}
            for item in root.findall(".//ITEM"):
                desc = item.get('DESCRIPTION', item.get('Description', 'MODULO')).upper()
                try:
                    w = float(item.get('WIDTH', 0))
                    h = float(item.get('HEIGHT', 0))
                    d = float(item.get('DEPTH', 0))
                    x = float(item.get('X', item.get('ABSCISSA', 0)))
                    z = float(item.get('Z', item.get('COTA', 0)))
                    if w < 30 or h < 30: continue # Limpeza de peças pequenas
                    id_peca = f"{desc}_{int(x)}_{int(z)}"
                    pecas[id_peca] = {'nome': desc, 'W': w, 'H': h, 'X': x, 'Z': z, 'vol': w*h*d}
                except: continue
            return pecas
        except: return {}

    v_dados = extrair_dados(xml_venda)
    c_dados = extrair_dados(xml_conf)

    fig, ax = plt.subplots(figsize=(14, 7))
    # Desenha o original (Cinza) e o técnico (Colorido)
    for p in v_dados.values():
        ax.add_patch(plt.Rectangle((p['X'], p['Z']), p['W'], p['H'], color='gray', alpha=0.1))

    alertas = []
    todas = set(v_dados.keys()) | set(c_dados.keys())
    for k in todas:
        v, c = v_dados.get(k), c_dados.get(k)
        if v and (not c or c['vol'] < v['vol']):
            ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.6))
            alertas.append(f"🔴 MUDANÇA/RETIRADA: {v['nome']}")
        elif c and (not v or c['vol'] > v['vol']):
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.6))
            alertas.append(f"🟢 ADIÇÃO/AUMENTO: {c['nome']}")
        elif c:
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], fill=False, edgecolor='blue', alpha=0.2))

    ax.autoscale()
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_img"] = buf
    return buf, list(set(alertas))

# --- INTERFACE ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea Login")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
else:
    st.title("👷 Portal de Auditoria Técnica Amare")
    
    tabs = st.tabs(["📊 Comparativo XML", "🏠 Checklist Engenharia", "🔌 Eletros 3D", "💰 Extras", "🏁 Finalizar"])

    with tabs[0]:
        st.header("1. Confronto de Plantas (Venda vs Técnico)")
        c1, c2 = st.columns(2)
        f_v = c1.file_uploader("XML Venda", type=['xml'])
        f_c = c2.file_uploader("XML Conferência", type=['xml'])
        if f_v and f_c:
            img, erros = analisar_xml_promob(f_v, f_c)
            st.image(img, use_container_width=True)
            for e in erros: st.write(e)

    with tabs[1]:
        st.header("2. Checklist Técnico (Original)")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Hidráulica/Civil")
            c1 = st.checkbox("Caixa de gordura permite abertura?")
            c2 = st.checkbox("Pontos de esgoto e água corretos?")
            c3 = st.checkbox("Gás está na posição segura?")
        with col2:
            st.subheader("Medição/Alvenaria")
            c4 = st.checkbox("Paredes possuem prumo e esquadro?")
            c5 = st.checkbox("Drywall possui reforço?")
            c6 = st.checkbox("Desconto de granitos aplicado?")

    with tabs[2]:
        st.header("3. Memorial de Eletros (Altura/Largura/Prof)")
        def input_e(nome):
            col = st.columns(3)
            a = col.number_input(f"Alt {nome}", 0, key=f"a_{nome}")
            l = col.number_input(f"Larg {nome}", 0, key=f"l_{nome}")
            p = col.number_input(f"Prof {nome}", 0, key=f"p_{nome}")
            return f"{nome}: {a}x{l}x{p} mm"
        e_gel = input_e("Geladeira")
        e_for = input_e("Forno")

    with tabs[3]:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"**Item Extra {i+1}**")
            col_ex1, col_ex2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = col_ex1.text_input(f"Local {i}", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = col_ex2.number_input(f"Valor {i}", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que é? {i}", value="0", key=f"desc_{i}")

    with tabs[4]:
        st.header("5. Fechamento")
        cliente = st.text_input("Nome do Cliente / Contrato")
        if st.button("🏁 GERAR PDF COMPLETO"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"LAUDO AMARE ITALINEA - {cliente}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Final: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)

            if st.session_state["mapa_img"]:
                pdf.ln(5)
                with open("mapa_temp.png", "wb") as f:
                    f.write(st.session_state["mapa_img"].getbuffer())
                pdf.image("mapa_temp.png", x=10, w=190)
                os.remove("mapa_temp.png")
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | Desc: {ex['desc']}", ln=True)

            output = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR LAUDO COMPLETO", data=output, file_name=f"Laudo_{cliente}.pdf")
