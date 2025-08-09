import streamlit as st
import pandas as pd
import io
import unicodedata # Biblioteca estándar de Python para manejar caracteres Unicode (acentos)

# --- Título y Descripción de la App Web ---
st.set_page_config(page_title="Procesador de Archivos", layout="centered")
st.title("📄 Procesador de Archivos")
st.write("""
    Esta aplicación procesa archivos **Excel** (`.xlsx`, `.xls`) y de texto **CSV** (`.csv`). 
    Acepta variaciones en los nombres de las columnas (ej. 'Fecha', 'FECHA', 'Aprobacion', 'Aprobación').
""")

# --- LÓGICA DE PROCESAMIENTO MEJORADA ---
def procesar_archivo(archivo_cargado):
    try:
        nombre_archivo = archivo_cargado.name
        if nombre_archivo.endswith('.csv'):
            df = pd.read_csv(archivo_cargado, sep=',')
        elif nombre_archivo.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo_cargado)
        else:
            st.error("Formato de archivo no soportado.")
            return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

    # --- CAMBIO CLAVE: Normalizar y renombrar columnas ---
    # 1. Función para normalizar: convierte a minúsculas y quita acentos.
    def normalizar_nombre(nombre_col):
        nombre_col = str(nombre_col) # Asegurarse de que el nombre es un string
        # unicodedata.normalize descompone los caracteres con acentos (ej. 'á' -> 'a' + '´')
        # El resto del código filtra y se queda solo con los caracteres base, sin los acentos.
        s = ''.join(c for c in unicodedata.normalize('NFD', nombre_col) if unicodedata.category(c) != 'Mn')
        return s.lower().strip() # Convierte a minúsculas y quita espacios extra

    # 2. Define un mapa de los nombres normalizados que buscamos al nombre estándar que queremos.
    mapa_nombres = {
        "fecha": "Fecha",
        "franquicia": "Franquicia",
        "aprobacion": "Aprobación", # El nombre normalizado no tiene tilde
        "valor bruto": "Valor Bruto"
    }

    # 3. Crea el diccionario para renombrar, usando los nombres de columna originales.
    columnas_a_renombrar = {}
    for col in df.columns:
        nombre_norm = normalizar_nombre(col)
        if nombre_norm in mapa_nombres:
            # Mapea el nombre original (ej. "FECHA") al nombre estándar (ej. "Fecha")
            columnas_a_renombrar[col] = mapa_nombres[nombre_norm]
    
    # 4. Aplica el renombrado al DataFrame
    df.rename(columns=columnas_a_renombrar, inplace=True)
    # --- FIN DEL CAMBIO ---

    # El resto de la lógica ya puede asumir los nombres de columna estándar
    columnas_requeridas = ["Fecha", "Franquicia", "Aprobación", "Valor Bruto"]
    if not all(col in df.columns for col in columnas_requeridas):
        st.error(f"Error: No se encontraron todas las columnas requeridas en el archivo.")
        st.info(f"Asegúrate de que tu archivo contenga columnas equivalentes a: {columnas_requeridas}")
        return None
    
    df_seleccion = df[columnas_requeridas].copy()
    
    df_seleccion['Fecha'] = pd.to_datetime(df_seleccion['Fecha'], dayfirst=True, errors='coerce')

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

# --- Interfaz de la Aplicación (sin cambios) ---

uploaded_file = st.file_uploader(
    "👇 Carga tu archivo Excel o CSV aquí",
    type=['xlsx', 'xls', 'csv']
)

st.info("Tu archivo no se guarda en ningún servidor. Todo el procesamiento ocurre de forma segura.", icon="ℹ️")


if uploaded_file is not None:
    st.success(f"Archivo cargado: **{uploaded_file.name}**")
    
    if st.button("🚀 Procesar Archivo", type="primary"):
        with st.spinner('Procesando, por favor espera...'):
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

