import streamlit as st
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import ezdxf
import io
import os

# --- 1. CONFIGURAÇÕES E SESSÃO ---
st.set_page_config(page_title="Amare Italinea - Auditoria Master", layout="wide")

if "inicio_conferencia" not in st.session_state:
    st.session_state["inicio_conferencia"] = datetime.now()
if "lista_extras" not in st.session_state:
    st.session_state["lista_extras"] = []
if "mapa_dxf_buffer" not in st.session_state:
    st.session_state["mapa_dxf_buffer"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- 2. MOTOR DE DESENHO (DXF) ---
def renderizar_confronto_dxf(v_dxf, c_dxf):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    def desenhar_linhas(file, cor):
        try:
            # Salva o arquivo temporariamente para leitura do ezdxf
            with open("temp_file.dxf", "wb") as f:
                f.write(file.getbuffer())
            
            doc = ezdxf.readfile("temp_file.dxf")
            msp = doc.modelspace()
            
            # Percorre linhas e polilinhas do CAD
            for e in msp.query('LINE LWPOLYLINE'):
                if e.dxftype() == 'LINE':
                    start, end = e.dxf.start, e.dxf.end
                    ax.plot([start.x, end.x], [start.y, end.y], color=cor, alpha=0.6, lw=0.8)
                elif e.dxftype() == 'LWPOLYLINE':
                    points = e.get_points()
                    x_pts = [p[0] for p in points]
                    y_pts = [p[1] for p in points]
                    ax.plot(x_pts, y_pts, color=cor, alpha=0.6, lw=0.8)
            
            os.remove("temp_file.dxf")
        except Exception as err:
            st.error(f"Erro ao processar DXF: {err}")

    # Desenha os dois arquivos sobrepostos
    desenhar_linhas(v_dxf, 'red')   # Projeto Venda
    desenhar_linhas(c_dxf, 'green') # Conferência Técnica
    
    ax.set_aspect('equal')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    st.session_state["mapa_dxf_buffer"] = buf
    return buf

# --- 3. LOGIN ---
USUARIOS = {"admin": "adminamare", "michel_conferente": "italinea123"}
if not st.session_state["logado"]:
    st.title("🛡️ Login Amare Italinea")
    u = st.sidebar.text_input("Usuário").lower()
    p = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == p:
            st.session_state["logado"] = True
            st.rerun()
        else: st.sidebar.error("Acesso Negado")
else:
    # --- 4. INTERFACE ---
    st.title("👷 Portal de Auditoria Técnica Amare")
    t1, t2, t3, t4, t5 = st.tabs(["📊 Confronto DXF", "🏠 Checklist", "🔌 Memorial Eletros", "💰 Extras", "🏁 Finalizar"])

    with t1:
        st.header("1. Comparação Visual de Desenhos")
        c1, c2 = st.columns(2)
        f_v_dxf = c1.file_uploader("Subir DXF Venda (Original)", type=['dxf'], key="vd")
        f_c_dxf = c2.file_uploader("Subir DXF Técnico (Executivo)", type=['dxf'], key="cd")

        if f_v_dxf and f_c_dxf:
            with st.spinner("Processando sobreposição de linhas..."):
                img_result = renderizar_confronto_dxf(f_v_dxf, f_c_dxf)
                st.image(img_result, caption="Vermelho: Original | Verde: Técnico", use_container_width=True)

    with t2:
        st.header("2. Checklist de Engenharia")
        colA, colB = st.columns(2)
        with colA:
            st.checkbox("Caixa de gordura permite abertura?"); st.checkbox("Registros e Sifão recuados?")
            st.checkbox("Paredes com prumo/esquadro?"); st.checkbox("Gás está acessível?")
        with colB:
            st.checkbox("Ponto energia coifa no local?"); st.checkbox("Tomadas bancada 110cm?")
            st.checkbox("Pé-direito (3 pontos)?"); st.checkbox("Desconto granitos aplicado?")

    with t3:
        st.header("3. Memorial de Eletros (mm)")
        def input_e(nome, ref):
            st.write(f"**{nome}**")
            cl = st.columns(3)
            alt = cl.number_input(f"Alt {nome}", 0, key=f"alt_{ref}")
            lar = cl.number_input(f"Larg {nome}", 0, key=f"lar_{ref}")
            pro = cl.number_input(f"Prof {nome}", 0, key=f"pro_{ref}")
            return f"{nome}: {alt}x{lar}x{pro} mm"
        
        e_gel = input_e("Geladeira", "gel")
        e_for = input_e("Forno", "for")
        e_mic = input_e("Micro-ondas", "mic")

    with t4:
        st.header("4. Custos Extras")
        if st.button("➕ Adicionar Novo Item Extra"):
            st.session_state["lista_extras"].append({"local": "", "valor": 0.0, "desc": ""})
            st.rerun()
        
        for i, item in enumerate(st.session_state["lista_extras"]):
            st.markdown(f"--- Registro {i+1}")
            ce = st.columns(2)
            st.session_state["lista_extras"][i]["local"] = ce.text_input(f"Onde comprou?", key=f"loc_{i}")
            st.session_state["lista_extras"][i]["valor"] = ce.number_input(f"Valor R$", 0.0, key=f"val_{i}")
            st.session_state["lista_extras"][i]["desc"] = st.text_area(f"O que foi comprado?", value="0", key=f"des_{i}")

    with t5:
        st.header("5. Fechamento e Laudo")
        cliente = st.text_input("Nome do Cliente / Contrato")
        if st.button("🏁 GERAR PDF FINAL"):
            hora_fim = datetime.now()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, f"LAUDO AMARE - {cliente}", ln=True, align='C')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Início: {st.session_state['inicio_conferencia'].strftime('%d/%m %H:%M')}", ln=True)
            pdf.cell(0, 8, f"Término: {hora_fim.strftime('%d/%m %H:%M')}", ln=True)

            if st.session_state["mapa_dxf_buffer"]:
                pdf.ln(5)
                with open("mapa_tmp.png", "wb") as f: f.write(st.session_state["mapa_dxf_buffer"].getbuffer())
                pdf.image("mapa_tmp.png", x=10, w=180); os.remove("mapa_tmp.png")
            
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "EXTRAS:", ln=True)
            for ex in st.session_state["lista_extras"]:
                pdf.set_font("Arial", '', 10); pdf.cell(0, 8, f"- {ex['local']} | R$ {ex['valor']} | {ex['desc']}", ln=True)
            
            st.download_button("📥 BAIXAR LAUDO", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laudo_{cliente}.pdf")
