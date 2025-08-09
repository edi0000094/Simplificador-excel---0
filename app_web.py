import streamlit as st
import pandas as pd
import io
import os

# --- Título y Descripción de la App Web ---
st.set_page_config(page_title="Procesador de Archivos", layout="centered")
st.title("📄 Procesador de Archivos")
st.write("""
    Esta aplicación procesa archivos **Excel** (`.xlsx`, `.xls`) y de texto **CSV** (`.csv`). 
    Extrae columnas específicas y crea la columna **'Fecha Islero'**.
""")

# --- LÓGICA DE PROCESAMIENTO MEJORADA ---
# La función ahora se llama "procesar_archivo" para reflejar que maneja múltiples tipos.
def procesar_archivo(archivo_cargado):
    try:
        # Extrae el nombre del archivo para verificar su extensión
        nombre_archivo = archivo_cargado.name
        
        # --- CAMBIO CLAVE: Lógica para leer según el tipo de archivo ---
        if nombre_archivo.endswith('.csv'):
            # Usa pd.read_csv para archivos de texto, especificando el separador
            # y pidiendo que convierta la columna "Fecha" directamente a formato de fecha.
            df = pd.read_csv(archivo_cargado, sep=',', parse_dates=['Fecha'])
        elif nombre_archivo.endswith(('.xls', '.xlsx')):
            # Usa pd.read_excel para archivos de Excel
            df = pd.read_excel(archivo_cargado)
        else:
            st.error("Formato de archivo no soportado. Por favor, usa .csv, .xls, o .xlsx.")
            return None

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.info("Sugerencia: Si es un archivo CSV, asegúrate de que el separador sea una coma (,) y que las columnas requeridas existan.")
        return None

    # El resto de la lógica funciona igual porque ya tenemos un DataFrame de pandas
    columnas_requeridas = ["Fecha", "Franquicia", "Aprobación", "Valor Bruto"]
    if not all(col in df.columns for col in columnas_requeridas):
        st.error(f"Error: El archivo no contiene todas las columnas requeridas: {columnas_requeridas}")
        return None
    
    df_seleccion = df[columnas_requeridas].copy()
    
    # La columna "Fecha" ya fue convertida al leer el archivo, pero lo aseguramos
    df_seleccion['Fecha'] = pd.to_datetime(df_seleccion['Fecha'], errors='coerce')

    def calcular_fecha_islero(fecha):
        if pd.isna(fecha):
            return pd.NaT
        if 0 <= fecha.hour < 6:
            return fecha.date() - pd.Timedelta(days=1)
        else:
            return fecha.date()

    df_seleccion['Fecha Islero'] = df_seleccion['Fecha'].apply(calcular_fecha_islero)
    
    columnas_finales = ["Fecha Islero", "Fecha", "Franquicia", "Aprobación", "Valor Bruto"]
    return df_seleccion[columnas_finales]

# --- Interfaz de la Aplicación ---

# --- CAMBIO CLAVE: Se añade '.csv' a la lista de tipos de archivo permitidos ---
uploaded_file = st.file_uploader(
    "👇 Carga tu archivo Excel o CSV aquí",
    type=['xlsx', 'xls', 'csv']
)

st.info("Tu archivo no se guarda en ningún servidor. Todo el procesamiento ocurre de forma segura.", icon="ℹ️")


if uploaded_file is not None:
    st.success(f"Archivo cargado: **{uploaded_file.name}**")
    
    if st.button("🚀 Procesar Archivo", type="primary"):
        with st.spinner('Procesando, por favor espera...'):
            # Se llama a la nueva función de lógica
            df_procesado = procesar_archivo(uploaded_file)

        if df_procesado is not None:
            st.success("¡Proceso completado con éxito!")
            
            st.write("### Vista previa de los datos procesados:")
            st.dataframe(df_procesado.head())

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_procesado.to_excel(writer, index=False, sheet_name='Datos Procesados')
            
            datos_excel = output.getvalue()

            st.download_button(
                label="📥 Descargar Resultado (.xlsx)",
                data=datos_excel,
                file_name='datos_procesados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
