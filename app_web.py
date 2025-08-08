import streamlit as st
import pandas as pd
import io

# --- Título y Descripción de la App Web ---
st.set_page_config(page_title="Procesador de Fechas Islero", layout="centered")
st.title("📄 Procesador de Archivos Excel")
st.write("""
    Esta aplicación extrae columnas específicas de un archivo Excel (`.xlsx` o `.xls`) 
    y crea una nueva columna llamada **'Fecha Islero'**.
""")
st.write("""
    La 'Fecha Islero' corresponde al día anterior si la hora en la columna 'Fecha' 
    original está entre las 12:00 a.m. y las 6:00 a.m.
""")

# --- LÓGICA CENTRAL DEL PROCESAMIENTO ---
# (La misma lógica, pero ahora devuelve el DataFrame procesado o un error)
def procesar_logica_excel(archivo):
    try:
        df = pd.read_excel(archivo)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

    columnas_requeridas = ["Fecha", "Franquicia", "Aprobación", "Valor Bruto"]
    if not all(col in df.columns for col in columnas_requeridas):
        st.error(f"Error: El archivo no contiene todas las columnas requeridas: {columnas_requeridas}")
        return None
    
    df_seleccion = df[columnas_requeridas].copy()
    df_seleccion['Fecha'] = pd.to_datetime(df_seleccion['Fecha'], errors='coerce')

    def calcular_fecha_islero(fecha):
        if pd.isna(fecha):
            return pd.NaT
        if 0 <= fecha.hour < 6:
            return fecha.date() - pd.Timedelta(days=1)
        else:
            return fecha.date()

    df_seleccion['Fecha Islero'] = df_seleccion['Fecha'].apply(calcular_fecha_islero)
    
    columnas_finales = ["Fecha", "Fecha Islero", "Franquicia", "Aprobación", "Valor Bruto"]
    return df_seleccion[columnas_finales]

# --- Interfaz de la Aplicación ---

# 1. Widget para cargar el archivo
uploaded_file = st.file_uploader(
    "👇 Carga tu archivo de Excel aquí",
    type=['xlsx', 'xls']
)

st.info("Tu archivo no se guarda en ningún servidor. Todo el procesamiento ocurre de forma segura.", icon="ℹ️")


if uploaded_file is not None:
    st.success(f"Archivo cargado: **{uploaded_file.name}**")
    
    # 2. Botón para iniciar el procesamiento
    if st.button("🚀 Procesar Archivo", type="primary"):
        with st.spinner('Procesando, por favor espera...'):
            df_procesado = procesar_logica_excel(uploaded_file)

        if df_procesado is not None:
            st.success("¡Proceso completado con éxito!")
            
            # Muestra una vista previa del resultado
            st.write("### Vista previa de los datos procesados:")
            st.dataframe(df_procesado.head())

            # 3. Prepara el archivo para la descarga
            # Convierte el DataFrame a un archivo Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_procesado.to_excel(writer, index=False, sheet_name='Datos Procesados')
            
            # El método getvalue() obtiene los bytes del archivo en memoria
            datos_excel = output.getvalue()

            # 4. Widget para descargar el archivo
            st.download_button(
                label="📥 Descargar Archivo Procesado (.xlsx)",
                data=datos_excel,
                file_name='datos_procesados.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
