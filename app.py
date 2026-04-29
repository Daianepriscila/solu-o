import streamlit as st
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io

# --- CONFIGURAÇÃO MASTER ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

# Registro do tempo de início da conferência
if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()

# --- FUNÇÃO DE LEITURA E DESENHO TÉCNICO (O CORAÇÃO DO SISTEMA) ---
def gerar_visualizacao_tecnica(xml_venda, xml_conf):
    def extrair_pecas(file):
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            pecas = {}
            # O XML do Promob lista os itens. Vamos pegar descrição, tamanho e posição.
            for item in root.iter('ITEM'):
                desc = item.get('DESCRIPTION', item.get('Descricao', 'MODULO')).upper()
                w = float(item.get('WIDTH', 0))
                h = float(item.get('HEIGHT', 0))
                d = float(item.get('DEPTH', 0))
                x = float(item.get('X', 0))
                y = float(item.get('Y', 0))
                z = float(item.get('Z', 0))

                # Filtro para ignorar lixo de sistema (peças menores que 2cm)
                if w < 20 and d < 20: continue 

                # Chave única baseada na posição X e Y (planta baixa)
                id_peca = f"{int(x)}_{int(y)}"
                pecas[id_peca] = {'nome': desc, 'W': w, 'H': h, 'D': d, 'X': x, 'Y': y, 'Z': z, 'vol': w*h*d}
            return pecas
        except: return {}

    v_pecas = extrair_pecas(xml_venda)
    c_pecas = extrair_pecas(xml_conf)

    # Criando o gráfico da Planta Baixa
    fig, ax = plt.subplots(figsize=(12, 8))
    mudancas_texto = []

    # 1. Desenhar as Paredes da Conferência como Contexto (Cinza)
    for p in c_pecas.values():
        if 'PAREDE' in p['nome'] or 'PISO' in p['nome']:
            rect = plt.Rectangle((p['X'], p['Y']), p['W'], p['D'], color='#EEEEEE', alpha=0.5)
            ax.add_patch(rect)

    # 2. Lógica de Comparação Colorida
    todas_chaves = set(v_pecas.keys()) | set(c_pecas.keys())
    for chave in todas_chaves:
        v = v_pecas.get(chave)
        c = c_pecas.get(chave)

        # CASO 1: FOI RETIRADO OU DIMINUIU (VERMELHO)
        if v and (not c or c['vol'] < v['vol']):
            # Se sumiu ou encolheu, mostramos o tamanho original em Vermelho
            rect = plt.Rectangle((v['X'], v['Y']), v['W'], v['D'], color='red', alpha=0.6, label='Retirada/Redução')
            ax.add_patch(rect)
            mudancas_texto.append(f"🔴 PERDA/REDUÇÃO: {v['nome']} na posição X:{v['X']}")

        # CASO 2: FOI ADICIONADO OU AUMENTOU (VERDE)
        elif c and (not v or c['vol'] > v['vol']):
            # Se é novo ou cresceu, mostramos o novo tamanho em Verde
            rect = plt.Rectangle((c['X'], c['Y']), c['W'], c['D'], color='green', alpha=0.6, label='Adição/Aumento')
            ax.add_patch(rect)
            mudancas_texto.append(f"🟢 ADIÇÃO/EXTRA: {c['nome']} na posição X:{c['X']}")

        # CASO 3: SEM ALTERAÇÃO (AZUL CLARO)
        elif c and 'PAREDE' not in c['nome']:
            rect = plt.Rectangle((c['X'], c['Y']), c['W'], c['D'], fill=False, edgecolor='blue', alpha=0.2)
            ax.add_patch(rect)

    ax.set_aspect('equal')
    ax.autoscale()
    plt.axis('off')
    plt.title("MAPA DE AUDITORIA: VERMELHO (Prejuízo/Retirada) | VERDE (Adição/Extra)")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    return buf, mudancas_texto

# --- INTERFACE ---
st.title("🚀 Amare Italinea - Auditoria de Projetos")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparativo XML", "🔌 Eletros", "💰 Extras", "🏁 Laudo Final"])

with tab1:
    st.header("1. Leitura e Confronto de Projetos")
    col1, col2 = st.columns(2)
    f_venda = col1.file_uploader("XML Venda (Original)", type=['xml'])
    f_conf = col2.file_uploader("XML Conferência (Técnico)", type=['xml'])
    
    mapa_resultado = None
    if f_venda and f_conf:
        mapa_resultado, lista_erros = gerar_visualizacao_tecnica(f_venda, f_conf)
        st.image(mapa_resultado, use_container_width=True)
        
        st.subheader("Diferenças lidas no XML:")
        for erro in lista_erros:
            if "🔴" in erro: st.error(erro)
            else: st.success(erro)

with tab2:
    st.header("2. Detalhamento de Eletros (mm)")
    def input_eletro(label):
        st.write(f"**{label}**")
        c1, c2, c3 = st.columns(3)
        alt = c1.number_input(f"Altura {label}", 0, key=f"a_{label}")
        larg = c2.number_input(f"Largura {label}", 0, key=f"l_{label}")
        prof = c3.number_input(f"Profundidade {label}", 0, key=f"p_{label}")
        return f"{label}: {alt}x{larg}x{prof} mm"
    
    e1 = input_eletro("Geladeira")
    e2 = input_eletro("Forno")
    e3 = input_eletro("Micro-ondas")

with tab3:
    st.header("3. Controle de Extras")
    ex_local = st.text_input("Onde comprou o extra?", "N/A")
    ex_valor = st.number_input("Valor total do extra (R$)", 0.0)
    ex_desc = st.text_area("Descrição detalhada do extra", value="0")

with tab4:
    st.header("4. Fechamento do Laudo")
    cliente = st.text_input("Nome do Cliente / Contrato")
    if st.button("🏁 GERAR PDF E FINALIZAR"):
        hora_fim = datetime.now()
        tempo_total = hora_fim - st.session_state["inicio_conferencia"]
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"LAUDO DE AUDITORIA - {cliente}", ln=True, align='C')
        
        pdf.set_font("Arial", '', 10)
        pdf.ln(5)
        pdf.cell(0, 8, f"Início da Conferência: {st.session_state['inicio_conferencia'].strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.cell(0, 8, f"Finalização do Laudo: {hora_fim.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "CONTROLE DE EXTRAS:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Local: {ex_local} | Valor: R$ {ex_valor}", ln=True)
        pdf.multi_cell(0, 8, f"Descrição: {ex_desc}")

        if mapa_resultado:
            img_path = "mapa_final.png"
            with open(img_path, "wb") as f:
                f.write(mapa_resultado.getvalue())
            pdf.image(img_path, x=10, w=190)
            
        st.success("Laudo concluído! O arquivo PDF agora contém o tempo total e a comparação visual.")
        st.download_button("📥 BAIXAR PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
