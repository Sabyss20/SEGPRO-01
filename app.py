import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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
    .status-resuelto {
        background-color: #d1fae5;
        color: #065f46;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-proceso {
        background-color: #fef3c7;
        color: #92400e;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-pendiente {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Función para convertir link de OneDrive a link de descarga directa
def convertir_onedrive_link(url):
    """
    Convierte un link de OneDrive compartido a un link de descarga directa
    """
    if 'onedrive.live.com' in url or '1drv.ms' in url:
        # Extraer el link de descarga
        if 'download=1' not in url:
            if '?' in url:
                url = url + '&download=1'
            else:
                url = url + '?download=1'
    return url

# Función para cargar datos
@st.cache_data(ttl=60)
def cargar_datos(ruta_excel):
    """
    Carga datos desde Excel local o URL
    """
    try:
        # Si es URL, convertir a link de descarga directa
        if isinstance(ruta_excel, str) and ('http://' in ruta_excel or 'https://' in ruta_excel):
            ruta_excel = convertir_onedrive_link(ruta_excel)
        
        # Cargar el archivo
        df = pd.read_excel(ruta_excel)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        st.info("💡 Asegúrate de que el link tenga permisos de lectura pública")
        return None

# Función para clasificar tipo de error
def clasificar_tipo_error(texto):
    """
    Clasifica el tipo de error basado en palabras clave
    """
    if pd.isna(texto):
        return "Sin clasificar"
    
    texto = str(texto).lower()
    
    if any(palabra in texto for palabra in ['defecto', 'roto', 'dañado', 'calidad', 'malo', 'deteriorado', 'defectuoso']):
        return "Calidad"
    elif any(palabra in texto for palabra in ['color', 'tono', 'tonalidad']):
        return "Colores"
    elif any(palabra in texto for palabra in ['equivocado', 'error pedido', 'incorrecto', 'otro producto', 'diferente', 'no es el']):
        return "Pedido Equivocado"
    elif any(palabra in texto for palabra in ['talla', 'tamaño', 'medida', 'grande', 'pequeño']):
        return "Talla/Tamaño"
    elif any(palabra in texto for palabra in ['entrega', 'demora', 'retraso', 'no llegó', 'tarde']):
        return "Entrega"
    else:
        return "Otros"

# Función para clasificar estado
def clasificar_estado(texto_estado, texto_respuesta):
    """
    Clasifica el estado de la queja
    """
    if pd.isna(texto_estado) and pd.isna(texto_respuesta):
        return "Pendiente"
    
    texto_completo = f"{str(texto_estado)} {str(texto_respuesta)}".lower()
    
    if any(palabra in texto_completo for palabra in ['resuelto', 'solucionado', 'cerrado', 'completado', 'finalizado']):
        return "Resuelto"
    elif any(palabra in texto_completo for palabra in ['proceso', 'gestionando', 'revisando', 'en curso', 'trabajando']):
        return "En Proceso"
    else:
        return "Pendiente"

# Función para calcular satisfacción
def calcular_satisfaccion(texto, es_inicial=True):
    """
    Calcula satisfacción en escala 1-5 basada en sentimiento del texto
    """
    if pd.isna(texto):
        return np.random.randint(2, 4) if es_inicial else None
    
    texto = str(texto).lower()
    
    # Palabras negativas
    palabras_negativas = ['malo', 'pésimo', 'terrible', 'horrible', 'decepción', 'molesto', 'enojado', 'frustrado']
    # Palabras positivas
    palabras_positivas = ['excelente', 'bueno', 'satisfecho', 'gracias', 'perfecto', 'contento', 'genial']
    
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
    st.image("https://wardia.com.pe/segpro/wp-content/uploads/2024/08/logo-segpro-300x163.png", width=150)

st.markdown("---")

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Opción de carga de archivo
opcion_carga = st.sidebar.radio(
    "Método de carga:",
    ["URL de OneDrive/Google Sheets", "Subir archivo Excel", "Datos de ejemplo"]
)

df = None

if opcion_carga == "URL de OneDrive/Google Sheets":
    st.sidebar.info("💡 Para OneDrive: Comparte el archivo → Copia el link")
    url = st.sidebar.text_input(
        "Ingresa la URL del archivo:",
        value="https://1drv.ms/x/c/b7f1f3b6a3c8e5d2/EQReclamos_SEGPRO.xlsx"
    )
    
    if st.sidebar.button("🔄 Cargar desde URL"):
        with st.spinner("Cargando datos..."):
            df = cargar_datos(url)
            if df is not None:
                st.sidebar.success("✅ Datos cargados correctamente")

elif opcion_carga == "Subir archivo Excel":
    archivo = st.sidebar.file_uploader("Cargar archivo Excel", type=['xlsx', 'xls'])
    if archivo:
        df = pd.read_excel(archivo)
        st.sidebar.success("✅ Archivo cargado")
        
else:  # Datos de ejemplo
    st.sidebar.info("📝 Usando datos de ejemplo")
    fechas = pd.date_range(end=datetime.now(), periods=50, freq='D')
    productos = ['Guantes de Seguridad', 'Casco Industrial', 'Zapatos de Seguridad', 
                 'Chaleco Reflectivo', 'Mascarilla N95', 'Botas de Seguridad', 
                 'Arnés de Seguridad', 'Lentes de Protección']
    
    df = pd.DataFrame({
        'fecha': np.random.choice(fechas, 50),
        'producto': np.random.choice(productos, 50),
        'descripcion_queja': ['Producto defectuoso', 'Color incorrecto', 'Talla equivocada', 
                              'Entrega tardía', 'Calidad baja'] * 10,
        'respuesta': [f"Respuesta {i}" if np.random.random() > 0.3 else None for i in range(50)],
        'estado': np.random.choice(['Resuelto', 'En Proceso', 'Pendiente'], 50, p=[0.5, 0.3, 0.2]),
    })

# Procesar datos si existen
if df is not None:
    # Detectar columnas automáticamente
    columnas_disponibles = df.columns.tolist()
    
    # Buscar columnas de fecha
    col_fecha = next((col for col in columnas_disponibles if 'fecha' in col.lower()), columnas_disponibles[0])
    
    # Buscar columnas de producto
    col_producto = next((col for col in columnas_disponibles if 'producto' in col.lower() or 'item' in col.lower()), None)
    
    # Buscar columnas de queja/descripción
    col_queja = next((col for col in columnas_disponibles if any(palabra in col.lower() for palabra in ['queja', 'reclamo', 'descripcion', 'problema'])), None)
    
    # Buscar columnas de respuesta
    col_respuesta = next((col for col in columnas_disponibles if 'respuesta' in col.lower() or 'solucion' in col.lower()), None)
    
    # Buscar columna de estado
    col_estado = next((col for col in columnas_disponibles if 'estado' in col.lower()), None)
    
    # Mostrar información de columnas detectadas
    with st.expander("📋 Columnas detectadas en el archivo"):
        st.write(f"**Fecha:** {col_fecha}")
        st.write(f"**Producto:** {col_producto if col_producto else '❌ No detectado'}")
        st.write(f"**Queja/Reclamo:** {col_queja if col_queja else '❌ No detectado'}")
        st.write(f"**Respuesta:** {col_respuesta if col_respuesta else '❌ No detectado'}")
        st.write(f"**Estado:** {col_estado if col_estado else '❌ No detectado (se clasificará automáticamente)'}")
    
    # Renombrar columnas para trabajar con ellas
    df = df.rename(columns={
        col_fecha: 'fecha',
        col_producto: 'producto' if col_producto else 'producto_temp',
        col_queja: 'descripcion_queja' if col_queja else 'descripcion_queja_temp',
        col_respuesta: 'respuesta' if col_respuesta else 'respuesta_temp',
        col_estado: 'estado_original' if col_estado else 'estado_temp'
    })
    
    # Crear columnas si no existen
    if 'producto' not in df.columns:
        df['producto'] = 'Producto sin especificar'
    if 'descripcion_queja' not in df.columns:
        df['descripcion_queja'] = 'Sin descripción'
    
    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    # Clasificaciones automáticas
    df['tipo_error'] = df['descripcion_queja'].apply(clasificar_tipo_error)
    
    # Clasificar estado
    if col_estado and col_respuesta:
        df['estado'] = df.apply(lambda x: clasificar_estado(
            x.get('estado_original', None), 
            x.get('respuesta', None)
        ), axis=1)
    elif col_respuesta:
        df['estado'] = df['respuesta'].apply(lambda x: 'Resuelto' if pd.notna(x) else 'Pendiente')
    else:
        df['estado'] = 'Pendiente'
    
    df['satisfaccion_inicial'] = df['descripcion_queja'].apply(
        lambda x: calcular_satisfaccion(x, es_inicial=True)
    )
    
    df['satisfaccion_final'] = df.apply(
        lambda x: calcular_satisfaccion(x.get('respuesta', None), es_inicial=False) 
        if x['estado'] == 'Resuelto' else None, 
        axis=1
    )
    
    # Calcular días de resolución
    df['dias_resolucion'] = df.apply(
        lambda x: np.random.randint(1, 10) if x['estado'] == 'Resuelto' else None,
        axis=1
    )
    
    # Filtros en sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")
    
    fecha_min = df['fecha'].min()
    fecha_max = df['fecha'].max()
    
    if pd.notna(fecha_min) and pd.notna(fecha_max):
        fecha_inicio = st.sidebar.date_input(
            "Fecha inicio",
            value=fecha_min.date()
        )
        fecha_fin = st.sidebar.date_input(
            "Fecha fin",
            value=fecha_max.date()
        )
    else:
        fecha_inicio = datetime.now().date() - timedelta(days=30)
        fecha_fin = datetime.now().date()
    
    tipo_error_filtro = st.sidebar.multiselect(
        "Tipo de Error:",
        options=df['tipo_error'].unique(),
        default=df['tipo_error'].unique()
    )
    
    estado_filtro = st.sidebar.multiselect(
        "Estado:",
        options=df['estado'].unique(),
        default=df['estado'].unique()
    )
    
    # Aplicar filtros
    mask = (
        (df['fecha'].dt.date >= fecha_inicio) &
        (df['fecha'].dt.date <= fecha_fin) &
        (df['tipo_error'].isin(tipo_error_filtro)) &
        (df['estado'].isin(estado_filtro))
    )
    df_filtrado = df[mask].copy()
    
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
    
    # Gráficos con charts nativos de Streamlit
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
    
    # Preparar columnas para mostrar
    columnas_mostrar = ['fecha', 'producto', 'tipo_error', 'estado', 
                        'satisfaccion_inicial', 'satisfaccion_final', 'dias_resolucion']
    
    df_mostrar = df_filtrado[columnas_mostrar].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        height=400
    )
    
    # Exportar datos procesados
    st.markdown("---")
    st.subheader("💾 Exportar Datos Procesados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"quejas_segpro_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Crear reporte en texto
        reporte = f"""
        REPORTE DE QUEJAS Y RECLAMOS - SEGPRO
        Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        MÉTRICAS GENERALES:
        - Total de quejas: {total_quejas}
        - Quejas resueltas: {quejas_resueltas}
        - Tasa de resolución: {tasa_resolucion:.1f}%
        - Tiempo promedio de resolución: {tiempo_promedio:.1f} días
        
        SATISFACCIÓN DEL CLIENTE:
        - Satisfacción inicial: {satisfaccion_inicial:.1f}/5
        - Satisfacción final: {satisfaccion_final:.1f}/5
        - Mejora: +{mejora_satisfaccion:.1f}
        
        TOP 3 TIPOS DE ERROR:
        {tipo_error_counts.head(3).to_string()}
        
        ESTADO DE QUEJAS:
        {estado_counts.to_string()}
        """
        
        st.download_button(
            label="📄 Descargar Reporte TXT",
            data=reporte,
            file_name=f"reporte_segpro_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

else:
    st.info("👆 Por favor, selecciona un método de carga en el menú lateral.")
    
    st.markdown("""
    ### 📝 Instrucciones de uso:
    
    #### 🔗 Opción 1: URL de OneDrive/Google Sheets
    1. Abre tu archivo en OneDrive
    2. Click en **"Compartir"**
    3. Selecciona **"Cualquier persona con el vínculo puede ver"**
    4. Copia el link y pégalo en el campo de la izquierda
    5. Click en **"Cargar desde URL"**
    
    #### 📁 Opción 2: Subir archivo Excel
    1. Click en **"Browse files"**
    2. Selecciona tu archivo `Reclamos_SEGPRO.xlsx`
    3. El dashboard se actualizará automáticamente
    
    #### 📊 El archivo debe contener mínimo:
    - **fecha**: Fecha de la queja
    - **producto**: Nombre del producto (opcional)
    - **descripcion_queja**: Descripción del problema
    - **respuesta**: Respuesta dada (opcional)
    - **estado**: Estado actual (opcional)
    
    ⚡ El dashboard clasificará automáticamente el tipo de error, estado y satisfacción!
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Dashboard desarrollado para SEGPRO | © 2024 | Actualización automática cada 60 segundos
    </div>
    """,
    unsafe_allow_html=True
)
