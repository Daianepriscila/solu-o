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
if "mapa_img_buffer" not in st.session_state:
    st.session_state["mapa_img_buffer"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# --- LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}

def realizar_login():
    if not st.session_state["logado"]:
        st.title("🛡️ Amare Italinea - Login")
        u = st.sidebar.text_input("Usuário")
        p = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.sidebar.error("Credenciais inválidas.")
        return False
    return True

# --- MOTOR DE DESENHO E COMPARAÇÃO XML ---
def processar_xmls(xml_venda, xml_conf):
    def extrair_geometria(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            itens = {}
            for item in root.findall(".//ITEM"):
                desc = item.get('DESCRIPTION', item.get('Description', 'MODULO')).upper()
                try:
                    w = float(item.get('WIDTH', 0))
                    h = float(item.get('HEIGHT', 0))
                    d = float(item.get('DEPTH', 0))
                    x = float(item.get('X', item.get('ABSCISSA', 0)))
                    z = float(item.get('Z', item.get('COTA', 0)))
                    
                    if w < 50 or h < 50: continue # Filtro de peças técnicas pequenas
                    
                    id_peca = f"{desc}_{int(x)}_{int(z)}"
                    itens[id_peca] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Z': z, 'V': w*h*d}
                except: continue
            return itens
        except: return {}

    venda = extrair_geometria(xml_venda)
    conf = extrair_geometria(xml_conf)

    fig, ax = plt.subplots(figsize=(14, 7))
    alertas = []

    # Desenha sombra do projeto original
    for p in venda.values():
        ax.add_patch(plt.Rectangle((p['X'], p['Z']), p['W'], p['H'], color='gray', alpha=0.1))

    todas_chaves = set(venda.keys()) | set(conf.keys())
    for k in todas_chaves:
        v, c = venda.get(k), conf.get(k)
        if v and (not c or c['V'] < v['V']):
            ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.6, edgecolor='darkred'))
            alertas.append(f"🔴 RETIRADO/REDUZIDO: {v['nome']}")
        elif c and (not v or c['V'] > v['V']):
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.6, edgecolor='darkgreen'))
            alertas.append(f"🟢 ADIADO/AUMENTADO: {c['nome']}")
        elif c:
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], fill=False, edgecolor='blue', alpha=0.2))

    ax.autoscale()
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_img_buffer"] = buf
    return buf, list(set(alertas))

# --- INTERFACE ---
if realizar_login():
    st.title("👷 Portal de Auditoria Técnica Amare")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Mapa de Mudanças XML", "🏠 Checklist Engenharia", "🔌 Memorial Eletros", "💰 Custos Extras", "🏁 Finalizar Laudo"])

    with tab1:
        st.header("1. Confronto de Projetos (Venda vs Técnico)")
        c1, c2 = st.columns(2)
        f_v = c1.file_uploader("XML Projeto Venda", type=['xml'], key="venda_xml")
        f_c = c2.file_uploader("XML Conferência Técnica", type=['xml'], key="conf_xml")
        
        if f_v and f_c:
            img, erros = processar_xmls(f_v, f_c)
            st.image(img, use_container_width=True)
            st.subheader("Diferenças Detectadas")
            for e in erros:
                if "🔴" in e: st.error(e)
                else: st.success(e)

    with tab2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica e Gás")
            h1 = st.checkbox("Caixa de gordura permite abertura do balcão?")
            h2 = st.checkbox("Registros e Sifão estão recuados para tubulação?")
            h3 = st.checkbox("Ponto de gás está acessível e seguro?")
            st.subheader("🧱 Civil e Alvenaria")
            a1 = st.checkbox("Paredes possuem prumo e esquadro?")
            a2 = st.checkbox("Drywall possui reforço de madeira?")
        with colB:
            st.subheader("⚡ Elétrica")
            e1 = st.checkbox("Ponto de energia para coifa/depurador no local?")
            e2 = st.checkbox("Tomadas bancada respeitam altura de 110cm?")
            st.subheader("📐 Medições")
            m1 = st.checkbox("Pé-direito medido em 3 pontos?")
            m2 = st.checkbox("Desconto de granitos aplicado no projeto?")

    with tab3:
        st.header("3. Memorial de Eletros (Medidas em mm)")
        def input_eletro(nome, key_ref):
            st.write(f"**{nome}**")
            cl1, cl2, cl3 = st.columns(3)
            alt = cl1.number_input(f"Altura", 0, key=f"a_{key_ref}")
            lar = cl2.number_input(f"Largura", 0, key=f"l_{key_ref}")
            pro = cl3.number_input(f"Profundidade", 0, key=f"p_{key_ref}")
            return f"{nome}: {alt}x{lar}x{pro} mm"
        
        el_gel = input_eletro("Geladeira", "gel")
        el_for = input_eletro("Forno", "for")
        el_mic = input_eletro("Micro-ondas", "mic")

    with tab4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Extra {i+1}")
            ce1, ce2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce1.text_input(f"Onde comprou?", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce2.number_input(f"Valor R$", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"Descrição", value="0", key=f"des_{i}")

    with tab5:
        st.header("5. Fechamento")
        cliente = st.text_input("Nome do Cliente")
        foto_ref = st.file_uploader("Anexar Foto da Medida Final", type=['jpg', 'jpeg', 'png'])
        
        if st.button("🏁 GERAR LAUDO PDF FINAL"):
            hora_fim = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            
            # Título
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"LAUDO DE AUDITORIA - {cliente}", ln=True, align='C')
            
            # Cronômetro
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Final: {hora_fim.strftime('%d/%m/%Y %H:%M')}", ln=True)

            # Mapa XML
            if st.session_state["mapa_img_buffer"]:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "MAPA DE DIVERGÊNCIAS (XML):", ln=True)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_img_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=180)
                os.remove("mapa_tmp.png")

            # Foto Medida
            if foto_ref:
                pdf.ln(5)
                with open("foto_tmp.png", "wb") as f: f.write(foto_ref.getbuffer())
                pdf.image("foto_tmp.png", x=10, w=100)
                os.remove("foto_tmp.png")

            # Extras
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE EXTRAS:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ex in st.session_state["lista_extras"]:
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)

            # Eletros
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "ELETROS:", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, el_gel, ln=True)
            pdf.cell(0, 8, el_for, ln=True)
            pdf.cell(0, 8, el_mic, ln=True)

            res_pdf = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR LAUDO", data=res_pdf, file_name=f"Laudo_{cliente}.pdf")

