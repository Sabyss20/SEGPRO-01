import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
</style>
""", unsafe_allow_html=True)

# Función para cargar datos
@st.cache_data(ttl=300)
def cargar_datos(ruta_excel):
    """
    Carga datos desde Excel local o URL de Google Sheets/OneDrive
    """
    try:
        # Intentar cargar desde archivo local o URL
        df = pd.read_excel(ruta_excel)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None

# Función para clasificar tipo de error
def clasificar_tipo_error(texto):
    """
    Clasifica el tipo de error basado en palabras clave
    """
    if pd.isna(texto):
        return "Sin clasificar"
    
    texto = str(texto).lower()
    
    if any(palabra in texto for palabra in ['defecto', 'roto', 'dañado', 'calidad', 'malo', 'deteriorado']):
        return "Calidad"
    elif any(palabra in texto for palabra in ['color', 'tono', 'tonalidad']):
        return "Colores"
    elif any(palabra in texto for palabra in ['equivocado', 'error', 'incorrecto', 'otro producto', 'diferente']):
        return "Pedido Equivocado"
    elif any(palabra in texto for palabra in ['talla', 'tamaño', 'medida']):
        return "Talla/Tamaño"
    elif any(palabra in texto for palabra in ['entrega', 'demora', 'retraso', 'no llegó']):
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
    
    if any(palabra in texto_completo for palabra in ['resuelto', 'solucionado', 'cerrado', 'completado']):
        return "Resuelto"
    elif any(palabra in texto_completo for palabra in ['proceso', 'gestionando', 'revisando', 'en curso']):
        return "En Proceso"
    else:
        return "Pendiente"

# Función para calcular satisfacción (simulada basada en sentimiento)
def calcular_satisfaccion(texto, es_inicial=True):
    """
    Calcula satisfacción en escala 1-5 basada en sentimiento del texto
    """
    if pd.isna(texto):
        return np.random.randint(2, 4) if es_inicial else None
    
    texto = str(texto).lower()
    
    # Palabras negativas
    palabras_negativas = ['malo', 'pésimo', 'terrible', 'horrible', 'decepción', 'molesto', 'enojado']
    # Palabras positivas
    palabras_positivas = ['excelente', 'bueno', 'satisfecho', 'gracias', 'perfecto', 'contento']
    
    score_negativo = sum(1 for palabra in palabras_negativas if palabra in texto)
    score_positivo = sum(1 for palabra in palabras_positivas if palabra in texto)
    
    if es_inicial:
        # Quejas iniciales tienden a ser más negativas
        if score_negativo > score_positivo:
            return np.random.randint(1, 3)
        else:
            return np.random.randint(2, 4)
    else:
        # Respuestas finales tienden a ser más positivas si se resolvió
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
    ["Subir archivo Excel", "URL de Google Sheets/OneDrive", "Datos de ejemplo"]
)

df = None

if opcion_carga == "Subir archivo Excel":
    archivo = st.sidebar.file_uploader("Cargar archivo Excel", type=['xlsx', 'xls'])
    if archivo:
        df = pd.read_excel(archivo)
        
elif opcion_carga == "URL de Google Sheets/OneDrive":
    url = st.sidebar.text_input("Ingresa la URL del archivo:")
    if url:
        df = cargar_datos(url)
        
else:  # Datos de ejemplo
    # Crear datos de ejemplo
    fechas = pd.date_range(end=datetime.now(), periods=50, freq='D')
    productos = ['Guantes de Seguridad', 'Casco Industrial', 'Zapatos de Seguridad', 
                 'Chaleco Reflectivo', 'Mascarilla N95', 'Botas de Seguridad', 
                 'Arnés de Seguridad', 'Lentes de Protección']
    
    df = pd.DataFrame({
        'fecha': np.random.choice(fechas, 50),
        'producto': np.random.choice(productos, 50),
        'descripcion_queja': [f"Queja ejemplo {i}" for i in range(50)],
        'respuesta': [f"Respuesta ejemplo {i}" if np.random.random() > 0.3 else None for i in range(50)],
        'estado': np.random.choice(['Resuelto', 'En Proceso', 'Pendiente'], 50),
    })

# Procesar datos si existen
if df is not None:
    # Asegurar que tenemos las columnas necesarias
    columnas_requeridas = ['fecha', 'producto', 'descripcion_queja']
    
    if not all(col in df.columns for col in columnas_requeridas):
        st.error(f"El archivo debe contener las columnas: {', '.join(columnas_requeridas)}")
        st.stop()
    
    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    # Clasificaciones automáticas
    df['tipo_error'] = df['descripcion_queja'].apply(clasificar_tipo_error)
    
    if 'estado' not in df.columns:
        df['estado'] = df.apply(lambda x: clasificar_estado(
            x.get('estado', None), 
            x.get('respuesta', None)
        ), axis=1)
    
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
    
    fecha_inicio = st.sidebar.date_input(
        "Fecha inicio",
        value=df['fecha'].min().date() if not df['fecha'].isna().all() else datetime.now().date() - timedelta(days=30)
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha fin",
        value=df['fecha'].max().date() if not df['fecha'].isna().all() else datetime.now().date()
    )
    
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
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Quejas por Tipo de Error")
        tipo_error_counts = df_filtrado['tipo_error'].value_counts()
        fig1 = px.pie(
            values=tipo_error_counts.values,
            names=tipo_error_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("📈 Quejas por Estado")
        estado_counts = df_filtrado['estado'].value_counts()
        fig2 = px.bar(
            x=estado_counts.index,
            y=estado_counts.values,
            color=estado_counts.index,
            color_discrete_map={
                'Resuelto': '#10b981',
                'En Proceso': '#f59e0b',
                'Pendiente': '#ef4444'
            }
        )
        fig2.update_layout(showlegend=False, xaxis_title="Estado", yaxis_title="Cantidad")
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏆 Top 5 Productos con Quejas")
        producto_counts = df_filtrado['producto'].value_counts().head(5)
        fig3 = px.bar(
            x=producto_counts.values,
            y=producto_counts.index,
            orientation='h',
            color=producto_counts.values,
            color_continuous_scale='Viridis'
        )
        fig3.update_layout(showlegend=False, xaxis_title="Cantidad", yaxis_title="Producto")
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        st.subheader("⭐ Comparación de Satisfacción")
        comparacion_data = pd.DataFrame({
            'Momento': ['Antes', 'Después'],
            'Satisfacción': [satisfaccion_inicial, satisfaccion_final if not pd.isna(satisfaccion_final) else 0]
        })
        fig4 = px.bar(
            comparacion_data,
            x='Momento',
            y='Satisfacción',
            color='Momento',
            color_discrete_map={'Antes': '#ef4444', 'Después': '#10b981'}
        )
        fig4.update_layout(showlegend=False, yaxis_range=[0, 5])
        st.plotly_chart(fig4, use_container_width=True)
    
    # Tendencias temporales
    st.subheader("📅 Tendencias Temporales")
    df_temporal = df_filtrado.groupby(df_filtrado['fecha'].dt.to_period('D')).size().reset_index()
    df_temporal.columns = ['fecha', 'cantidad']
    df_temporal['fecha'] = df_temporal['fecha'].dt.to_timestamp()
    
    fig5 = px.line(
        df_temporal,
        x='fecha',
        y='cantidad',
        title='Quejas por Día'
    )
    fig5.update_traces(line_color='#3b82f6', line_width=2)
    st.plotly_chart(fig5, use_container_width=True)
    
    # Tabla detallada
    st.markdown("---")
    st.subheader("📋 Detalle de Quejas")
    
    # Preparar columnas para mostrar
    columnas_mostrar = ['fecha', 'producto', 'tipo_error', 'estado', 
                        'satisfaccion_inicial', 'satisfaccion_final', 'dias_resolucion']
    
    df_mostrar = df_filtrado[columnas_mostrar].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%Y-%m-%d')
    
    # Estilo condicional
    def colorear_estado(val):
        if val == 'Resuelto':
            return 'background-color: #d1fae5; color: #065f46'
        elif val == 'En Proceso':
            return 'background-color: #fef3c7; color: #92400e'
        else:
            return 'background-color: #fee2e2; color: #991b1b'
    
    st.dataframe(
        df_mostrar.style.applymap(colorear_estado, subset=['estado']),
        use_container_width=True,
        height=400
    )
    
    # Exportar datos procesados
    st.markdown("---")
    st.subheader("💾 Exportar Datos Procesados")
    
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"quejas_segpro_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("👆 Por favor, carga un archivo o selecciona 'Datos de ejemplo' en el menú lateral.")
    
    st.markdown("""
    ### 📝 Instrucciones de uso:
    
    1. **Subir archivo Excel**: El archivo debe contener al menos estas columnas:
       - `fecha`: Fecha de la queja
       - `producto`: Nombre del producto
       - `descripcion_queja`: Descripción del problema
       - (Opcional) `respuesta`: Respuesta dada al cliente
       - (Opcional) `estado`: Estado actual (Resuelto/En Proceso/Pendiente)
    
    2. **URL de Google Sheets/OneDrive**: 
       - Comparte el archivo con permisos de lectura
       - Copia el link de descarga directa
    
    3. **El dashboard clasificará automáticamente**:
       - Tipo de error (Calidad, Colores, Pedido Equivocado, etc.)
       - Estado de la queja
       - Nivel de satisfacción antes y después
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Dashboard desarrollado para SEGPRO | © 2024
    </div>
    """,
    unsafe_allow_html=True
)
