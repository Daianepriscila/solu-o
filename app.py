import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- INICIALIZAÇÃO DE SESSÃO ---
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []
if "mapa_img" not in st.session_state:
    st.session_state["mapa_img"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}

def login():
    if not st.session_state["logado"]:
        st.title("🛡️ Amare Italinea - Acesso Restrito")
        u = st.sidebar.text_input("Usuário")
        p = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.sidebar.error("Usuário ou senha incorretos.")
        return False
    return True

# --- MOTOR DE AUDITORIA XML (O QUE SAIU/ENTROU) ---
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
                    if w < 50 or h < 50: continue 
                    id_peca = f"{desc}_{int(x)}_{int(z)}"
                    pecas[id_peca] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Z': z, 'vol': w*h*d}
                except: continue
            return pecas
        except: return {}

    v_dados = extrair_dados(xml_venda)
    c_dados = extrair_dados(xml_conf)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    for p in v_dados.values():
        ax.add_patch(plt.Rectangle((p['X'], p['Z']), p['W'], p['H'], color='gray', alpha=0.1))

    alertas = []
    todas = set(v_dados.keys()) | set(c_dados.keys())
    for k in todas:
        v, c = v_dados.get(k), c_dados.get(k)
        if v and (not c or c['vol'] < v['vol']):
            ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.6))
            alertas.append(f"🔴 RETIRADO/REDUZIDO: {v['nome']}")
        elif c and (not v or c['vol'] > v['vol']):
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.6))
            alertas.append(f"🟢 ADIÇÃO/AUMENTO: {c['nome']}")
        elif c:
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], fill=False, edgecolor='blue', alpha=0.2))

    ax.autoscale()
    ax.set_aspect('equal')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_img"] = buf
    return buf, list(set(alertas))

# --- INTERFACE PRINCIPAL ---
if login():
    st.title("👷 Portal de Auditoria Técnica Amare")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Comparativo XML/3D", "🏠 Checklist Engenharia", "🔌 Eletros 3D", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Confronto de Projetos (Venda vs Técnico)")
        c1, c2 = st.columns(2)
        f_v_xml = c1.file_uploader("XML Venda", type=['xml'])
        f_c_xml = c2.file_uploader("XML Conferência", type=['xml'])
        
        if f_v_xml and f_c_xml:
            img, erros = analisar_xml_promob(f_v_xml, f_c_xml)
            st.image(img, use_container_width=True)
            for e in erros:
                if "🔴" in e: st.error(e)
                else: st.success(e)
        
        st.divider()
        st.subheader("Visualização 3D Real (.GLB)")
        c3, c4 = st.columns(2)
        f_v_3d = c3.file_uploader("Subir 3D Venda (.GLB)", type=['glb'])
        f_c_3d = c4.file_uploader("Subir 3D Conferência (.GLB)", type=['glb'])

    with tab2:
        st.header("2. Checklist de Engenharia (Original)")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica e Gás")
            h1 = st.checkbox("Caixa de gordura permite abertura do balcão?")
            h2 = st.checkbox("Registros e Sifão estão recuados?")
            h3 = st.checkbox("Ponto de gás está acessível?")
            st.subheader("🧱 Alvenaria e Civil")
            a1 = st.checkbox("Paredes possuem prumo e esquadro?")
            a2 = st.checkbox("Drywall possui reforço de madeira?")
        with colB:
            st.subheader("⚡ Elétrica")
            e1 = st.checkbox("Ponto de energia para coifa no local?")
            e2 = st.checkbox("Tomadas bancada respeitam 110cm?")
            st.subheader("📐 Medições")
            m1 = st.checkbox("Pé-direito medido em 3 pontos?")
            m2 = st.checkbox("Desconto de granitos aplicado?")

    with tab3:
        st.header("3. Memorial de Eletros (mm)")
        def input_e(nome, ref):
            st.write(f"**{nome}**")
            cl1, cl2, cl3 = st.columns(3)
            alt = cl1.number_input(f"Altura", 0, key=f"a_{ref}")
            lar = cl2.number_input(f"Largura", 0, key=f"l_{ref}")
            pro = cl3.number_input(f"Profundidade", 0, key=f"p_{ref}")
            return f"{nome}: {alt}x{lar}x{pro} mm"
        
        gel = input_e("Geladeira", "gel")
        forn = input_e("Forno", "for")
        micr = input_e("Micro-ondas", "mic")

    with tab4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Extra {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce1.text_input(f"Local {i}", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce2.number_input(f"Valor R$ {i}", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"Descrição {i}", value="0", key=f"desc_{i}")

    with tab5:
        st.header("5. Fechamento do Laudo")
        cliente = st.text_input("Nome do Cliente")
        foto_final = st.file_uploader("Anexar Foto da Medida Final", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🏁 GERAR PDF COMPLETO"):
            hora_fim = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"LAUDO AMARE ITALINEA - {cliente}", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Final: {hora_fim.strftime('%d/%m/%Y %H:%M')}", ln=True)

            if st.session_state["mapa_img"]:
                pdf.ln(5)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_img"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=190)
                os.remove("mapa_tmp.png")

            if foto_final:
                pdf.ln(5)
                with open("foto_tmp.png", "wb") as f: f.write(foto_final.getbuffer())
                pdf.image("foto_tmp.png", x=10, w=100)
                os.remove("foto_tmp.png")

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)

            pdf.ln(5)
            pdf.cell(0, 10, "ELETROS:", ln=True)
            pdf.cell(0, 8, gel, ln=True)
            pdf.cell(0, 8, forn, ln=True)
            pdf.cell(0, 8, micr, ln=True)

            output = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR LAUDO", data=output, file_name=f"Laudo_{cliente}.pdf")
