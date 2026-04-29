import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- INICIALIZAÇÃO ---
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []
if "mapa_img_final" not in st.session_state:
    st.session_state["mapa_img_final"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123", "douglas_conferente": "italinea456"}

if not st.session_state["logado"]:
    st.title("🛡️ Login Amare Italinea")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title("👷 Portal de Auditoria Técnica Amare")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Mapa XML", "🏠 Checklist", "🔌 Eletros 3D", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Confronto de Projetos (Venda vs Técnico)")
        c1, c2 = st.columns(2)
        f_v = c1.file_uploader("XML Projeto Venda", type=['xml'], key="v_xml")
        f_c = c2.file_uploader("XML Conferência Técnica", type=['xml'], key="c_xml")
        
        if f_v and f_c:
            def extrair(file):
                try:
                    tree = ET.parse(file)
                    root = tree.getroot()
                    itens = {}
                    for item in root.findall(".//ITEM"):
                        try:
                            w = float(item.get('WIDTH', 0))
                            h = float(item.get('HEIGHT', 0))
                            d = float(item.get('DEPTH', 0))
                            x = float(item.get('X', item.get('ABSCISSA', 0)))
                            z = float(item.get('Z', item.get('COTA', 0)))
                            if w < 50 or h < 50: continue # Filtra ferragens
                            desc = item.get('DESCRIPTION', 'MODULO').upper()
                            id_p = f"{int(x)}_{int(z)}"
                            itens[id_p] = {'nome': desc, 'W': w, 'H': h, 'X': x, 'Z': z, 'V': w*h*d}
                        except: continue
                    return itens
                except: return {}

            venda, conf = extrair(f_v), extrair(f_c)
            fig, ax = plt.subplots(figsize=(14, 7))
            alertas = []

            for p in venda.values():
                ax.add_patch(plt.Rectangle((p['X'], p['Z']), p['W'], p['H'], color='gray', alpha=0.1))

            todas = set(venda.keys()) | set(conf.keys())
            for k in todas:
                v, c = venda.get(k), conf.get(k)
                if v and (not c or c['V'] < v['V']):
                    ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.7))
                    alertas.append(f"🔴 RETIRADO/REDUZIDO: {v['nome']}")
                elif c and (not v or c['V'] > v['V']):
                    ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.7))
                    alertas.append(f"🟢 ADIÇÃO/AUMENTO: {c['nome']}")

            ax.autoscale(); ax.set_aspect('equal'); plt.axis('off')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            st.session_state["mapa_img_final"] = buf
            st.image(buf, use_container_width=True)
            for a in list(set(alertas)): st.write(a)

    with tab2:
        st.header("2. Checklist de Engenharia")
        clA, clB = st.columns(2)
        with clA:
            st.subheader("💧 Hidráulica e Civil")
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Paredes possuem prumo/esquadro?"); st.checkbox("Gás está acessível?")
        with clB:
            st.subheader("⚡ Elétrica e Medição")
            st.checkbox("Ponto de energia coifa no local?"); st.checkbox("Tomadas bancada respeitam 110cm?")
            st.checkbox("Pé-direito medido em 3 pontos?"); st.checkbox("Desconto de granitos aplicado?")

    with tab3:
        st.header("3. Memorial de Eletros (mm)")
        def in_e(n, r):
            st.write(f"**{n}**")
            c = st.columns(3)
            a = c.number_input(f"Alt", 0, key=f"a_{r}")
            l = c.number_input(f"Larg", 0, key=f"l_{r}")
            p = c.number_input(f"Prof", 0, key=f"p_{r}")
            return f"{n}: {a}x{l}x{p}mm"
        e1, e2, e3 = in_e("Geladeira", "g"), in_e("Forno", "f"), in_e("Micro-ondas", "m")

    with tab4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Extra {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce[0].text_input(f"Local {i}", key=f"lo_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce[1].number_input(f"Valor {i}", 0.0, key=f"va_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"Descrição {i}", value="0", key=f"de_{i}")

    with tab5:
        st.header("5. Fechamento")
        cliente = st.text_input("Nome do Cliente")
        foto_ref = st.file_uploader("Anexar Foto da Medida Final", type=['jpg', 'jpeg', 'png'])
        if st.button("🏁 GERAR PDF FINAL"):
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            if st.session_state["mapa_img_final"]:
                with open("m.png", "wb") as f: f.write(st.session_state["mapa_img_final"].getbuffer())
                pdf.image("m.png", x=10, w=190); os.remove("m.png")
            if foto_ref:
                with open("f.png", "wb") as f: f.write(foto_ref.getbuffer())
                pdf.image("f.png", x=10, w=100); os.remove("f.png")
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            st.download_button("📥 BAIXAR PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
