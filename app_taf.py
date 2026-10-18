import streamlit as st
from fpdf import FPDF
from datetime import datetime, timezone

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Generador de TAF", layout="wide")
st.title("Generador Estructurado de TAF")
st.markdown("Herramienta de ensamblado para pronósticos de aeródromo.")

# --- MEMORIA DE LA APP (SESSION STATE) ---
if 'num_grupos' not in st.session_state:
    st.session_state.num_grupos = 0
if 'tafs_guardados' not in st.session_state:
    st.session_state.tafs_guardados = []

def agregar_grupo():
    st.session_state.num_grupos += 1

def quitar_grupo():
    if st.session_state.num_grupos > 0:
        st.session_state.num_grupos -= 1

def limpiar_documento():
    st.session_state.tafs_guardados = []

# --- VARIABLES DE TIEMPO ACTUAL ---
ahora_utc = datetime.now(timezone.utc)
dia_actual = ahora_utc.strftime("%d")
hora_actual = ahora_utc.strftime("%H%M")

# --- 0. ENCABEZADO DEL BOLETÍN ---
st.header(" Encabezado de mensaje segun Nac&Int (Opcional)")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    tipo_encabezado = st.selectbox("Tipo de Mensaje", ["Internacional (FTAG)", "Nacional (FTAG60)", "Sin Encabezado"])
    
with col_b2:
    if tipo_encabezado == "Internacional (FTAG)":
        cabecera_default = "FTAG SAVC"
    elif tipo_encabezado == "Nacional (FTAG60)":
        cabecera_default = "FTAG60 SAVC"
    else:
        cabecera_default = ""
    
    cabecera_wmo = st.text_input("Línea de Cabecera", value=cabecera_default, disabled=(tipo_encabezado == "Sin Encabezado"))

with col_b3:
    dia_hora_imp = st.text_input("Día y Hora de Imposición (DDHHMM)", value=f"{dia_actual}{hora_actual}", disabled=(tipo_encabezado == "Sin Encabezado"))


# --- 1. IDENTIFICACIÓN Y VALIDEZ ---
st.header("1. Identificación y Validez")
col1, col2, col3, col4 = st.columns(4)

with col1:
    estacion = st.selectbox("Aeródromo", [
        "SAVC - Comodoro Rivadavia", 
        "SAVV - Viedma", 
        "SAVE - Esquel", 
        "SAWH - Ushuaia",
        "SAVT - Trelew",
        "SAWC - Calafate",
        "SAWG - Gallegos",
        "SAWE - Rio Grande",
    ])
    oaci = estacion.split(" ")[0]

with col2:
    dia_origen = st.text_input("Día (DD)", value=dia_actual)
    hora_origen = st.text_input("Hora Z (HHMM)", value="1200")

with col3:
    validez_inicio = st.text_input("Inicio Validez (DDHH)", value=f"{dia_origen}12")

with col4:
    dia_fin = str(int(dia_origen) + 1).zfill(2)
    validez_fin = st.text_input("Fin Validez (DDHH)", value=f"{dia_fin}12")

# --- 2. CONDICIONES METEOROLÓGICAS INICIALES ---
st.header("2. Condiciones Iniciales")
col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)

with col_v1:
    dir_viento = st.text_input("Dir. Viento (Grados/VRB)", value="270")
with col_v2:
    vel_viento = st.text_input("Vel. Viento (KT)", value="20")
with col_v3:
    raf_viento = st.text_input("Ráfagas (KT) [Opcional]", value="")
with col_v4:
    visibilidad = st.text_input("Visibilidad (Metros)", value="9999")
with col_v5:
    tiempo_sig = st.text_input("Tiempo (ej. -RA, FG)", value="")

# --- 3. NUBOSIDAD INICIAL ---
st.header("3. Nubosidad Inicial")
col_n1, col_n2, col_n3 = st.columns(3)

with col_n1:
    nubes_cant = st.selectbox("Cobertura", ["CAVOK", "FEW", "SCT", "BKN", "OVC", "NSC"])
with col_n2:
    alt_default = "030" if nubes_cant not in ["CAVOK", "NSC"] else ""
    nubes_alt = st.text_input("Altura (FL, ej. 030)", value=alt_default)
with col_n3:
    nubes_tipo = st.selectbox("Tipo [Opcional]", ["", "CB", "TCU"])

# --- 4. GRUPOS DE CAMBIO (DINÁMICOS) ---
st.header("4. Grupos de Cambio (Evolución)")
col_btn1, col_btn2 = st.columns([1, 8])
col_btn1.button("➕ Agregar Grupo", on_click=agregar_grupo)
col_btn2.button("➖ Eliminar Último", on_click=quitar_grupo)

grupos_ensamblados = []

for i in range(st.session_state.num_grupos):
    with st.expander(f"Grupo de Cambio {i+1}", expanded=True):
        cg1, cg2, cg3, cg4 = st.columns(4)
        tipo_cambio = cg1.selectbox("Indicador", ["BECMG", "TEMPO", "FM", "PROB30", "PROB40", "PROB30 TEMPO", "PROB40 TEMPO"], key=f"tipo_{i}")
        
        val_placeholder = "ej. 181500" if tipo_cambio == "FM" else "ej. 1815/1818"
        validez_cambio = cg2.text_input("Validez", placeholder=val_placeholder, key=f"val_{i}")
        
        viento_cambio = cg3.text_input("Viento", key=f"viento_{i}")
        vis_cambio = cg4.text_input("Visibilidad", key=f"vis_{i}")
        
        cg5, cg6 = st.columns(2)
        tiempo_cambio = cg5.text_input("Tiempo Sig.", key=f"tiempo_{i}")
        nubes_cambio = cg6.text_input("Nubosidad", key=f"nubes_{i}")
        
        partes = [tipo_cambio, validez_cambio, viento_cambio, vis_cambio, tiempo_cambio, nubes_cambio]
        grupo_str = " ".join([p for p in partes if p.strip()])
        if grupo_str:
            grupos_ensamblados.append(grupo_str)

# --- 5. EXTREMOS TÉRMICOS ---
st.header("5. Extremos Térmicos")
col_t1, col_t2 = st.columns(2)
with col_t1:
    tx = st.text_input("Max Temp (ej. TX15/1818Z)", value="")
with col_t2:
    tn = st.text_input("Min Temp (ej. TN05/1909Z)", value="")


# --- LÓGICA DE ENSAMBLADO DEL TAF ACTUAL ---
viento_str = f"{dir_viento}{vel_viento}"
if raf_viento:
    viento_str += f"G{raf_viento}"
viento_str += "KT"

if nubes_cant in ["CAVOK", "NSC"]:
    nubes_str = nubes_cant
else:
    nubes_str = f"{nubes_cant}{nubes_alt}{nubes_tipo}"

partes_taf = [
    "TAF", oaci, f"{dia_origen}{hora_origen}Z", f"{validez_inicio}/{validez_fin}",
    viento_str, visibilidad, tiempo_sig, nubes_str
]
partes_taf.extend(grupos_ensamblados)
partes_taf.extend([tx, tn])

taf_final = " ".join([p for p in partes_taf if p.strip()]) + "="
taf_display = taf_final.replace(" BECMG", "\nBECMG").replace(" TEMPO", "\nTEMPO").replace(" FM", "\nFM").replace(" PROB", "\nPROB").replace(" TX", "\nTX")

# --- BANDEJA DE DOCUMENTO ---
st.divider()
st.header("6. Gestión del Documento")

col_d1, col_d2, col_d3 = st.columns([1, 1, 1])

# BOTÓN 1: AGREGAR AL DOCUMENTO
with col_d1:
    st.write("**TAF Actual en edición:**")
    st.code(taf_display, language="text")
    if st.button("📥 Agregar al Documento", use_container_width=True):
        st.session_state.tafs_guardados.append(taf_final)
        st.success(f"TAF de {oaci} agregado. Total en boletín: {len(st.session_state.tafs_guardados)}")

# BOTÓN 2: VISUALIZAR DOCUMENTO
with col_d2:
    st.write(f"**Documento actual:** {len(st.session_state.tafs_guardados)} TAF(s)")
    if st.session_state.tafs_guardados:
        with st.expander("👀 Visualizar Documento Completo"):
            # Mostrar encabezado si aplica
            if tipo_encabezado != "Sin Encabezado":
                st.markdown(f"**Encabezado:** `{cabecera_wmo} {dia_hora_imp}`")
                st.divider()
                
            for i, taf_guardado in enumerate(st.session_state.tafs_guardados):
                taf_guardado_disp = taf_guardado.replace(" BECMG", "\nBECMG").replace(" TEMPO", "\nTEMPO").replace(" FM", "\nFM").replace(" PROB", "\nPROB").replace(" TX", "\nTX")
                st.markdown(f"**TAF {i+1}**")
                st.code(taf_guardado_disp, language="text")
            
            st.button("🗑️ Vaciar Documento", on_click=limpiar_documento)
    else:
        st.info("El documento está vacío. Agregá un TAF para visualizarlo.")

# BOTÓN 3: DESCARGAR DOCUMENTO
with col_d3:
    st.write("**Exportación:**")
    def crear_pdf_boletin(lista_tafs, tipo_enc, cabecera, hora_imp):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "BOLETÍN DE PRONÓSTICOS DE AERÓDROMO (TAF)", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", "I", 10)
        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M")
        pdf.cell(0, 10, f"Fecha de emisión del documento: {fecha_emision} Local", align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # --- IMPRESIÓN DEL ENCABEZADO OMM ---
        if tipo_enc != "Sin Encabezado":
            pdf.set_font("courier", "B", 12)
            pdf.cell(0, 8, f"{cabecera} {hora_imp}", align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
        
        pdf.set_font("courier", "", 12)
        for t in lista_tafs:
            texto_pdf = t.replace(" BECMG", "\nBECMG").replace(" TEMPO", "\nTEMPO").replace(" FM", "\nFM").replace(" PROB", "\nPROB").replace(" TX", "\nTX")
            pdf.multi_cell(0, 8, texto_pdf)
            pdf.ln(5)
            # Línea separadora si hay más de un TAF
            if len(lista_tafs) > 1:
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
            
        return bytes(pdf.output())

    if st.session_state.tafs_guardados:
        pdf_bytes = crear_pdf_boletin(st.session_state.tafs_guardados, tipo_encabezado, cabecera_wmo, dia_hora_imp)
        st.download_button(
            label="📄 Descargar Boletín (PDF)",
            data=pdf_bytes,
            file_name=f"Boletin_TAF_{dia_actual}{hora_actual}Z.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    else:
        st.button("📄 Descargar Boletín (PDF)", disabled=True, use_container_width=True)
