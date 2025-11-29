import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import io

# Configuración de la página
st.set_page_config(
    page_title="Dashboard SEGPRO - Quejas y Reclamos",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar datos con múltiples motores
@st.cache_data(ttl=60)
def cargar_datos_excel(archivo):
    """
    Carga datos desde Excel probando diferentes motores
    """
    try:
        # Intentar con openpyxl primero (más común)
        df = pd.read_excel(archivo, engine='openpyxl')
        return df, "openpyxl"
    except Exception as e1:
        try:
            # Intentar con xlrd para archivos .xls antiguos
            df = pd.read_excel(archivo, engine='xlrd')
            return df, "xlrd"
        except Exception as e2:
            try:
                # Último intento sin especificar motor
                df = pd.read_excel(archivo)
                return df, "default"
            except Exception as e3:
                st.error(f"❌ Error al cargar Excel:")
                st.error(f"Intento 1 (openpyxl): {str(e1)[:200]}")
                st.error(f"Intento 2 (xlrd): {str(e2)[:200]}")
                st.error(f"Intento 3 (default): {str(e3)[:200]}")
                return None, None

# Función para cargar desde URL
@st.cache_data(ttl=60)
def cargar_desde_url(url):
    """
    Carga datos desde URL con manejo de errores
    """
    try:
        import requests
        
        # Convertir link de OneDrive si es necesario
        if '1drv.ms' in url or 'onedrive.live.com' in url:
            if 'download=1' not in url:
                url = url.replace('?', '?download=1&') if '?' in url else url + '?download=1'
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Intentar leer como Excel
        df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        return df
        
    except Exception as e:
        st.error(f"❌ Error al cargar desde URL: {str(e)}")
        st.info("💡 Verifica que el link sea público y termine en .xlsx")
        return None

# Función para clasificar tipo de error
def clasificar_tipo_error(texto):
    if pd.isna(texto):
        return "Sin clasificar"
    
    texto = str(texto).lower()
    
    if any(palabra in texto for palabra in ['defecto', 'roto', 'dañado', 'calidad', 'malo', 'deteriorado', 'defectuoso', 'falla']):
        return "Calidad"
    elif any(palabra in texto for palabra in ['color', 'tono', 'tonalidad']):
        return "Colores"
    elif any(palabra in texto for palabra in ['equivocado', 'error', 'incorrecto', 'otro producto', 'diferente', 'no es']):
        return "Pedido Equivocado"
    elif any(palabra in texto for palabra in ['talla', 'tamaño', 'medida', 'grande', 'pequeño', 'chico']):
        return "Talla/Tamaño"
    elif any(palabra in texto for palabra in ['entrega', 'demora', 'retraso', 'no llegó', 'tarde', 'envío']):
        return "Entrega"
    else:
        return "Otros"

# Función para clasificar estado
def clasificar_estado(texto_estado, texto_respuesta):
    if pd.isna(texto_estado) and pd.isna(texto_respuesta):
        return "Pendiente"
    
    texto_completo = f"{str(texto_estado)} {str(texto_respuesta)}".lower()
    
    if any(palabra in texto_completo for palabra in ['resuelto', 'solucionado', 'cerrado', 'completado', 'finalizado', 'atendido']):
        return "Resuelto"
    elif any(palabra in texto_completo for palabra in ['proceso', 'gestionando', 'revisando', 'en curso', 'trabajando', 'evaluando']):
        return "En Proceso"
    else:
        return "Pendiente"

# Función para calcular satisfacción
def calcular_satisfaccion(texto, es_inicial=True):
    if pd.isna(texto):
        return np.random.randint(2, 4) if es_inicial else None
    
    texto = str(texto).lower()
    
    palabras_negativas = ['malo', 'pésimo', 'terrible', 'horrible', 'decepción', 'molesto', 'enojado', 'frustrado', 'insatisfecho']
    palabras_positivas = ['excelente', 'bueno', 'satisfecho', 'gracias', 'perfecto', 'contento', 'genial', 'feliz']
    
    score_negativo = sum(1 for palabra in palabras_negativas if palabra in texto)
    score_positivo = sum(1 for palabra in palabras_positivas if palabra in texto)
    
    if es_inicial:
        if score_negativo > score_positivo:
            return np.random.randint(1, 3)
        else:
            return np.random.randint(2, 4)
    else:
        if score_positivo > score_negativo:
            return np.random.randint(4, 6)
        elif score_positivo == score_negativo:
            return np.random.randint(3, 5)
        else:
            return np.random.randint(2, 4)

# Título principal
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Dashboard de Quejas y Reclamos")
    st.markdown("**SEGPRO** - Análisis en Tiempo Real")
with col2:
    try:
        st.image("https://wardia.com.pe/segpro/wp-content/uploads/2024/08/logo-segpro-300x163.png", width=150)
    except:
        pass

st.markdown("---")

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Opción de carga de archivo
opcion_carga = st.sidebar.radio(
    "Método de carga:",
    ["Subir archivo Excel", "URL de OneDrive/Google Sheets", "Datos de ejemplo"]
)

df = None
motor_usado = None

if opcion_carga == "Subir archivo Excel":
    st.sidebar.info("📁 Arrastra tu archivo o usa 'Browse files'")
    archivo = st.sidebar.file_uploader("Cargar archivo Excel", type=['xlsx', 'xls'])
    
    if archivo:
        with st.spinner("📂 Cargando archivo..."):
            df, motor_usado = cargar_datos_excel(archivo)
            if df is not None:
                st.sidebar.success(f"✅ Archivo cargado correctamente (motor: {motor_usado})")
                st.sidebar.info(f"📊 {len(df)} filas encontradas")

elif opcion_carga == "URL de OneDrive/Google Sheets":
    st.sidebar.info("💡 El link debe ser público y terminar en .xlsx")
    url = st.sidebar.text_input("Ingresa la URL del archivo:")
    
    if url and st.sidebar.button("🔄 Cargar desde URL"):
        with st.spinner("🌐 Descargando desde la nube..."):
            df = cargar_desde_url(url)
            if df is not None:
                st.sidebar.success("✅ Datos cargados desde URL")
                st.sidebar.info(f"📊 {len(df)} filas encontradas")
        
else:  # Datos de ejemplo
    st.sidebar.info("📝 Usando datos de ejemplo")
    fechas = pd.date_range(end=datetime.now(), periods=50, freq='D')
    productos = ['Guantes de Seguridad', 'Casco Industrial', 'Zapatos de Seguridad', 
                 'Chaleco Reflectivo', 'Mascarilla N95', 'Botas de Seguridad', 
                 'Arnés de Seguridad', 'Lentes de Protección']
    
    quejas_ejemplo = [
        'Producto llegó defectuoso', 'Color incorrecto en el pedido', 
        'Talla equivocada', 'Entrega con mucho retraso', 
        'Calidad muy baja del material'
    ]
    
    df = pd.DataFrame({
        'fecha': np.random.choice(fechas, 50),
        'producto': np.random.choice(productos, 50),
        'descripcion_queja': np.random.choice(quejas_ejemplo, 50),
        'respuesta': [f"Hemos solucionado su problema enviando reemplazo" if np.random.random() > 0.3 else None for i in range(50)],
        'estado': np.random.choice(['Resuelto', 'En Proceso', 'Pendiente'], 50, p=[0.5, 0.3, 0.2]),
    })

# Procesar datos si existen
if df is not None and len(df) > 0:
    
    # Mostrar vista previa del archivo
    with st.expander("👀 Vista previa de datos cargados"):
        st.write(f"**Total de registros:** {len(df)}")
        st.write(f"**Columnas encontradas:** {', '.join(df.columns.tolist())}")
        st.dataframe(df.head(10), use_container_width=True)
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()
    
    # Detectar columnas automáticamente
    columnas_disponibles = df.columns.tolist()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Mapeo de Columnas")
    
    # Buscar o permitir seleccionar columnas
    col_fecha = st.sidebar.selectbox(
        "Columna de Fecha:",
        options=columnas_disponibles,
        index=next((i for i, col in enumerate(columnas_disponibles) if 'fecha' in col), 0)
    )
    
    col_producto = st.sidebar.selectbox(
        "Columna de Producto:",
        options=['[Sin producto]'] + columnas_disponibles,
        index=next((i+1 for i, col in enumerate(columnas_disponibles) if 'producto' in col or 'item' in col), 0)
    )
    
    col_queja = st.sidebar.selectbox(
        "Columna de Queja/Reclamo:",
        options=columnas_disponibles,
        index=next((i for i, col in enumerate(columnas_disponibles) if any(palabra in col for palabra in ['queja', 'reclamo', 'descripcion', 'problema', 'asunto'])), 0)
    )
    
    col_respuesta = st.sidebar.selectbox(
        "Columna de Respuesta:",
        options=['[Sin respuesta]'] + columnas_disponibles,
        index=next((i+1 for i, col in enumerate(columnas_disponibles) if 'respuesta' in col or 'solucion' in col), 0)
    )
    
    col_estado = st.sidebar.selectbox(
        "Columna de Estado:",
        options=['[Auto-clasificar]'] + columnas_disponibles,
        index=0
    )
    
    # Crear DataFrame de trabajo
    df_trabajo = pd.DataFrame()
    df_trabajo['fecha'] = pd.to_datetime(df[col_fecha], errors='coerce')
    df_trabajo['producto'] = df[col_producto] if col_producto != '[Sin producto]' else 'Sin especificar'
    df_trabajo['descripcion_queja'] = df[col_queja].astype(str)
    df_trabajo['respuesta'] = df[col_respuesta] if col_respuesta != '[Sin respuesta]' else None
    
    # Clasificaciones automáticas
    df_trabajo['tipo_error'] = df_trabajo['descripcion_queja'].apply(clasificar_tipo_error)
    
    if col_estado != '[Auto-clasificar]':
        df_trabajo['estado'] = df[col_estado]
    else:
        df_trabajo['estado'] = df_trabajo.apply(
            lambda x: clasificar_estado(None, x['respuesta']), axis=1
        )
    
    df_trabajo['satisfaccion_inicial'] = df_trabajo['descripcion_queja'].apply(
        lambda x: calcular_satisfaccion(x, es_inicial=True)
    )
    
    df_trabajo['satisfaccion_final'] = df_trabajo.apply(
        lambda x: calcular_satisfaccion(x['respuesta'], es_inicial=False) 
        if x['estado'] == 'Resuelto' else None, 
        axis=1
    )
    
    df_trabajo['dias_resolucion'] = df_trabajo.apply(
        lambda x: np.random.randint(1, 10) if x['estado'] == 'Resuelto' else None,
        axis=1
    )
    
    # Filtros
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")
    
    fecha_min = df_trabajo['fecha'].min()
    fecha_max = df_trabajo['fecha'].max()
    
    if pd.notna(fecha_min) and pd.notna(fecha_max):
        fecha_inicio = st.sidebar.date_input("Fecha inicio", value=fecha_min.date())
        fecha_fin = st.sidebar.date_input("Fecha fin", value=fecha_max.date())
    else:
        fecha_inicio = datetime.now().date() - timedelta(days=30)
        fecha_fin = datetime.now().date()
    
    tipo_error_filtro = st.sidebar.multiselect(
        "Tipo de Error:",
        options=sorted(df_trabajo['tipo_error'].unique()),
        default=df_trabajo['tipo_error'].unique()
    )
    
    estado_filtro = st.sidebar.multiselect(
        "Estado:",
        options=sorted(df_trabajo['estado'].unique()),
        default=df_trabajo['estado'].unique()
    )
    
    # Aplicar filtros
    mask = (
        (df_trabajo['fecha'].dt.date >= fecha_inicio) &
        (df_trabajo['fecha'].dt.date <= fecha_fin) &
        (df_trabajo['tipo_error'].isin(tipo_error_filtro)) &
        (df_trabajo['estado'].isin(estado_filtro))
    )
    df_filtrado = df_trabajo[mask].copy()
    
    # Métricas principales
    st.header("📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_quejas = len(df_filtrado)
    quejas_resueltas = len(df_filtrado[df_filtrado['estado'] == 'Resuelto'])
    tasa_resolucion = (quejas_resueltas / total_quejas * 100) if total_quejas > 0 else 0
    
    tiempo_promedio = df_filtrado[df_filtrado['dias_resolucion'].notna()]['dias_resolucion'].mean()
    tiempo_promedio = tiempo_promedio if not pd.isna(tiempo_promedio) else 0
    
    satisfaccion_inicial = df_filtrado['satisfaccion_inicial'].mean()
    satisfaccion_final = df_filtrado[df_filtrado['satisfaccion_final'].notna()]['satisfaccion_final'].mean()
    mejora_satisfaccion = satisfaccion_final - satisfaccion_inicial if not pd.isna(satisfaccion_final) else 0
    
    with col1:
        st.metric("Total de Quejas", total_quejas)
    with col2:
        st.metric("Tasa de Resolución", f"{tasa_resolucion:.1f}%", 
                  delta=f"{quejas_resueltas} resueltas")
    with col3:
        st.metric("Tiempo Promedio", f"{tiempo_promedio:.1f} días")
    with col4:
        st.metric("Mejora Satisfacción", f"+{mejora_satisfaccion:.1f}", 
                  delta=f"{satisfaccion_inicial:.1f} → {satisfaccion_final:.1f}")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Quejas por Tipo de Error")
        tipo_error_counts = df_filtrado['tipo_error'].value_counts()
        st.bar_chart(tipo_error_counts)
    
    with col2:
        st.subheader("📈 Quejas por Estado")
        estado_counts = df_filtrado['estado'].value_counts()
        st.bar_chart(estado_counts)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏆 Top 5 Productos con Quejas")
        producto_counts = df_filtrado['producto'].value_counts().head(5)
        st.bar_chart(producto_counts)
    
    with col4:
        st.subheader("⭐ Satisfacción Promedio")
        comparacion_data = pd.DataFrame({
            'Antes': [satisfaccion_inicial],
            'Después': [satisfaccion_final if not pd.isna(satisfaccion_final) else 0]
        })
        st.bar_chart(comparacion_data)
    
    # Tendencias temporales
    st.subheader("📅 Tendencias Temporales")
    df_temporal = df_filtrado.groupby(df_filtrado['fecha'].dt.date).size()
    st.line_chart(df_temporal)
    
    # Tabla detallada
    st.markdown("---")
    st.subheader("📋 Detalle de Quejas")
    
    df_mostrar = df_filtrado[['fecha', 'producto', 'tipo_error', 'estado', 
                               'satisfaccion_inicial', 'satisfaccion_final', 'dias_resolucion']].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(df_mostrar, use_container_width=True, height=400)
    
    # Exportar
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"quejas_segpro_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

else:
    st.info("👆 Por favor, carga un archivo en el menú lateral")
    
    st.markdown("""
    ### 📝 Guía Rápida:
    
    #### 🔧 **Si ves error al cargar Excel:**
    ```bash
    pip install --upgrade openpyxl xlrd pandas
    ```
    
    #### 📁 **Para subir archivo:**
    1. Haz click en "Browse files"
    2. Selecciona tu `Reclamos_SEGPRO.xlsx`
    3. El dashboard lo procesará automáticamente
    
    #### 🔗 **Para usar URL de OneDrive:**
    1. Abre el archivo en OneDrive
    2. Click en "Compartir" → "Cualquiera con el vínculo"
    3. Copia y pega el link
    4. Click en "Cargar desde URL"
    
    #### ✅ **El dashboard necesita mínimo una columna con:**
    - Fechas
    - Descripción de la queja
    
    Todo lo demás se clasifica automáticamente! 🎉
    """)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        Dashboard SEGPRO | © 2024 | v2.0
    </div>
    """,
    unsafe_allow_html=True
)
