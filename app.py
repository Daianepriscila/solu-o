import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# Inicialização de variáveis de sessão para persistência de dados
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "mapa_img" not in st.session_state:
    st.session_state["mapa_img"] = None
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []

# Usuários permitidos
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123", "douglas_conferente": "italinea456"}

# --- MOTOR DE COMPARAÇÃO XML (DESENHO TÉCNICO) ---
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
                    
                    if w < 50 or h < 50: continue # Ignora ferragens pequenas
                    
                    id_peca = f"{desc}_{int(x)}_{int(z)}"
                    pecas[id_peca] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Z': z, 'vol': w*h*d}
                except: continue
            return pecas
        except: return {}

    v_dados = extrair_dados(xml_venda)
    c_dados = extrair_dados(xml_conf)

    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Desenha o original como "sombra"
    for p in v_dados.values():
        ax.add_patch(plt.Rectangle((p['X'], p['Z']), p['W'], p['H'], color='gray', alpha=0.1))

    alertas = []
    todas = set(v_dados.keys()) | set(c_dados.keys())
    
    for k in todas:
        v, c = v_dados.get(k), c_dados.get(k)
        if v and (not c or c['vol'] < v['vol']):
            # VERMELHO: O que foi retirado ou diminuiu (prejuízo/erro)
            ax.add_patch(plt.Rectangle((v['X'], v['Z']), v['W'], v['H'], color='red', alpha=0.6))
            alertas.append(f"🔴 MUDANÇA/RETIRADA: {v['nome']}")
        elif c and (not v or c['vol'] > v['vol']):
            # VERDE: O que foi adicionado ou aumentou (custo extra)
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], color='green', alpha=0.6))
            alertas.append(f"🟢 ADIÇÃO/AUMENTO: {c['nome']}")
        elif c:
            # AZUL: Mantido conforme original
            ax.add_patch(plt.Rectangle((c['X'], c['Z']), c['W'], c['H'], fill=False, edgecolor='blue', alpha=0.2))

    ax.autoscale()
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_img"] = buf
    return buf, list(set(alertas))

# --- LÓGICA DE LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Amare Italinea - Login")
    u = st.sidebar.text_input("Usuário")
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    st.title("👷 Portal de Auditoria Técnica Amare")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Comparativo XML", "🏠 Checklist Engenharia", "🔌 Eletros 3D", "💰 Extras", "🏁 Finalizar"])

    with tab1:
        st.header("1. Confronto de Plantas (Venda vs Técnico)")
        c1, c2 = st.columns(2)
        f_v = c1.file_uploader("XML Venda (Original)", type=['xml'])
        f_c = c2.file_uploader("XML Conferência (Executivo)", type=['xml'])
        
        if f_v and f_c:
            img, erros = analisar_xml_promob(f_v, f_c)
            st.image(img, use_container_width=True)
            st.subheader("Diferenças Técnicas Detectadas")
            for e in erros:
                if "🔴" in e: st.error(e)
                else: st.success(e)

    with tab2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("💧 Hidráulica, Gás e Civil")
            ch1 = st.checkbox("Caixa de gordura permite abertura do balcão?")
            ch2 = st.checkbox("Registros e Sifão estão recuados para tubulação?")
            ch3 = st.checkbox("Gás está na posição segura e acessível?")
            ch4 = st.checkbox("Paredes possuem prumo e esquadro?")
        with colB:
            st.subheader("⚡ Elétrica e Medição")
            ce1 = st.checkbox("Ponto de energia para coifa/depurador no local?")
            ce2 = st.checkbox("Tomadas acima da bancada respeitam altura (110cm)?")
            ce3 = st.checkbox("Pé-direito medido em 3 pontos diferentes?")
            ce4 = st.checkbox("Desconto de granitos aplicado no projeto?")

    with tab3:
        st.header("3. Memorial de Eletros (Medidas Reais em mm)")
        def input_eletro(nome, prefixo):
            st.markdown(f"**{nome}**")
            cla, clb, clc = st.columns(3)
            alt = cla.number_input(f"Alt (mm)", 0, key=f"alt_{prefixo}")
            lar = clb.number_input(f"Larg (mm)", 0, key=f"lar_{prefixo}")
            pro = clc.number_input(f"Prof (mm)", 0, key=f"pro_{prefixo}")
            return f"{nome}: {alt}x{lar}x{pro} mm"

        d_gel = input_eletro("Geladeira", "gel")
        d_for = input_eletro("Forno", "for")
        d_mic = input_eletro("Micro-ondas", "mic")

    with tab4:
        st.header("4. Custos Extras e Adicionais")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})

        for i, extra in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"---")
            ce1, ce2 = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce1.text_input(f"Local da Compra (Item {i+1})", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce2.number_input(f"Valor R$ (Item {i+1})", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que é este extra? (Item {i+1})", value="0", key=f"des_{i}")

    with tab5:
        st.header("5. Conclusão e Laudo PDF")
        cliente_nome = st.text_input("Nome do Cliente / Contrato")
        if st.button("🏁 GERAR LAUDO COMPLETO"):
            hora_final = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            
            # Título e Cabeçalho
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "LAUDO DE AUDITORIA MASTER - AMARE ITALINEA", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Cliente: {cliente_nome}", ln=True)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
            pdf.cell(0, 8, f"Fim: {hora_final.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)

            # Inserir Imagem do Mapa
            if st.session_state["mapa_img"]:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "COMPARAÇÃO VISUAL DO PROJETO:", ln=True)
                with open("mapa_laudo.png", "wb") as f:
                    f.write(st.session_state["mapa_img"].getbuffer())
                pdf.image("mapa_laudo.png", x=10, w=190)
                os.remove("mapa_laudo.png")

            # Extras e Eletros
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "RESUMO DE CUSTOS EXTRAS:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ex in st.session_state["lista_extras"]:
                pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | Desc: {ex['desc']}", ln=True)

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "MEMORIAL DE ELETROS:", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, d_gel, ln=True)
            pdf.cell(0, 8, d_for, ln=True)
            pdf.cell(0, 8, d_mic, ln=True)

            res_pdf = pdf.output(dest='S').encode('latin-1')
            st.success("Laudo PDF gerado com sucesso!")
            st.download_button("📥 BAIXAR LAUDO", data=res_pdf, file_name=f"Laudo_{cliente_nome}.pdf")
