import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Dashboard SEGPRO - Quejas y Reclamos",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Función para convertir link de SharePoint/OneDrive
def convertir_link_sharepoint(url):
    """Convierte links de SharePoint/OneDrive a formato descargable"""
    try:
        # Si ya tiene download=1, corregir formato
        if 'download=1' in url:
            url = url.replace('?download=1', '&download=1')
        
        # Si es SharePoint y no tiene download
        if 'sharepoint.com' in url and 'download=' not in url:
            if '?' in url:
                url = url.split('?')[0] + '?download=1'
            else:
                url = url + '?download=1'
        
        # Si es OneDrive
        if '1drv.ms' in url or 'onedrive.live.com' in url:
            if 'download=' not in url:
                url = url.replace('?', '?download=1&') if '?' in url else url + '?download=1'
        
        return url
    except:
        return url

# Función para cargar datos
@st.cache_data(ttl=60)
def cargar_datos_excel(archivo):
    try:
        df = pd.read_excel(archivo, engine='openpyxl')
        return df, None
    except Exception as e:
        return None, str(e)

# Función para cargar desde URL
@st.cache_data(ttl=60)
def cargar_desde_url(url):
    try:
        import requests
        
        # Convertir link
        url = convertir_link_sharepoint(url)
        
        st.info(f"🔗 Intentando descargar desde: {url[:100]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Verificar si es Excel
        content_type = response.headers.get('content-type', '')
        if 'html' in content_type:
            return None, "El link no apunta a un archivo Excel. Verifica que sea público y termine en .xlsx"
        
        # Intentar leer como Excel
        from io import BytesIO
        df = pd.read_excel(BytesIO(response.content), engine='openpyxl')
        return df, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Error de conexión: {str(e)}"
    except Exception as e:
        return None, f"Error al procesar Excel: {str(e)}"

# Función para clasificar tipo de error
def clasificar_tipo_error(texto):
    if pd.isna(texto):
        return "Sin clasificar"
    
    texto = str(texto).lower()
    
    if any(palabra in texto for palabra in ['defecto', 'roto', 'dañado', 'calidad', 'malo']):
        return "Calidad"
    elif any(palabra in texto for palabra in ['color', 'tono']):
        return "Colores"
    elif any(palabra in texto for palabra in ['equivocado', 'error', 'incorrecto']):
        return "Pedido Equivocado"
    elif any(palabra in texto for palabra in ['talla', 'tamaño']):
        return "Talla/Tamaño"
    elif any(palabra in texto for palabra in ['entrega', 'demora', 'retraso']):
        return "Entrega"
    else:
        return "Otros"

# Función para clasificar estado
def clasificar_estado(respuesta):
    if pd.isna(respuesta):
        return "Pendiente"
    
    texto = str(respuesta).lower()
    
    if any(palabra in texto for palabra in ['resuelto', 'solucionado', 'cerrado']):
        return "Resuelto"
    elif any(palabra in texto for palabra in ['proceso', 'gestionando', 'revisando']):
        return "En Proceso"
    else:
        return "Pendiente"

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

# Sidebar
st.sidebar.header("⚙️ Configuración")

# Opción de carga
opcion_carga = st.sidebar.radio(
    "Método de carga:",
    ["Subir archivo Excel", "URL de SharePoint/OneDrive", "Datos de ejemplo"]
)

df = None

if opcion_carga == "Subir archivo Excel":
    st.sidebar.info("📁 Arrastra tu archivo Excel aquí")
    archivo = st.sidebar.file_uploader("Cargar archivo", type=['xlsx', 'xls'])
    
    if archivo:
        with st.spinner("📂 Cargando archivo..."):
            df, error = cargar_datos_excel(archivo)
            if df is not None:
                st.sidebar.success(f"✅ {len(df)} registros cargados")
            else:
                st.sidebar.error(f"❌ Error: {error}")

elif opcion_carga == "URL de SharePoint/OneDrive":
    st.sidebar.info("💡 Pega el link compartido de SharePoint/OneDrive")
    url = st.sidebar.text_input("URL del archivo:")
    
    if url and st.sidebar.button("🔄 Cargar desde URL"):
        with st.spinner("🌐 Descargando desde la nube..."):
            df, error = cargar_desde_url(url)
            if df is not None:
                st.sidebar.success(f"✅ {len(df)} registros cargados")
            else:
                st.sidebar.error(f"❌ {error}")

else:  # Datos de ejemplo
    fechas = pd.date_range(end=datetime.now(), periods=30, freq='D')
    productos = ['Guantes', 'Casco', 'Zapatos', 'Chaleco', 'Mascarilla']
    
    df = pd.DataFrame({
        'fecha': pd.to_datetime([fechas[i % len(fechas)] for i in range(30)]),
        'producto': [productos[i % len(productos)] for i in range(30)],
        'queja': ['Producto defectuoso'] * 10 + ['Color incorrecto'] * 10 + ['Talla equivocada'] * 10,
        'respuesta': ['Solucionado'] * 15 + [None] * 15
    })
    st.sidebar.info("📝 Usando datos de ejemplo")

# Procesar datos
if df is not None and len(df) > 0:
    
    # Vista previa
    with st.expander("👀 Vista previa de datos"):
        st.write(f"**Registros:** {len(df)}")
        st.write(f"**Columnas:** {', '.join(df.columns)}")
        st.dataframe(df.head(5))
    
    # Limpiar columnas
    df.columns = df.columns.str.strip().str.lower()
    cols = df.columns.tolist()
    
    # Mapeo de columnas
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Columnas")
    
    col_fecha = st.sidebar.selectbox("Fecha:", cols, index=0)
    col_producto = st.sidebar.selectbox("Producto:", ['Sin especificar'] + cols)
    col_queja = st.sidebar.selectbox("Queja:", cols, index=min(1, len(cols)-1))
    col_respuesta = st.sidebar.selectbox("Respuesta:", ['Ninguna'] + cols)
    
    # Crear DataFrame procesado
    df_proc = pd.DataFrame()
    df_proc['fecha'] = pd.to_datetime(df[col_fecha], errors='coerce')
    df_proc['producto'] = df[col_producto] if col_producto != 'Sin especificar' else 'Sin especificar'
    df_proc['queja'] = df[col_queja].astype(str)
    df_proc['respuesta'] = df[col_respuesta] if col_respuesta != 'Ninguna' else None
    
    # Clasificaciones
    df_proc['tipo_error'] = df_proc['queja'].apply(clasificar_tipo_error)
    df_proc['estado'] = df_proc['respuesta'].apply(clasificar_estado)
    
    # Filtros
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Filtros de Fecha")
    
    # Filtrar filas con fechas válidas
    df_proc_con_fecha = df_proc[df_proc['fecha'].notna()].copy()
    
    if len(df_proc_con_fecha) > 0:
        fecha_min = df_proc_con_fecha['fecha'].min()
        fecha_max = df_proc_con_fecha['fecha'].max()
        
        try:
            fecha_inicio = st.sidebar.date_input("Desde:", fecha_min.date())
            fecha_fin = st.sidebar.date_input("Hasta:", fecha_max.date())
            
            # Aplicar filtro
            mask = (df_proc['fecha'].dt.date >= fecha_inicio) & (df_proc['fecha'].dt.date <= fecha_fin)
            df_filtrado = df_proc[mask]
        except:
            # Si hay error en las fechas, mostrar todos los datos
            df_filtrado = df_proc
            st.sidebar.warning("⚠️ Algunas fechas no son válidas")
    else:
        # Si no hay fechas válidas, mostrar todos los datos
        df_filtrado = df_proc
        st.sidebar.warning("⚠️ No se encontraron fechas válidas")
    
    # Métricas
    st.header("📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df_filtrado)
    resueltos = len(df_filtrado[df_filtrado['estado'] == 'Resuelto'])
    tasa = (resueltos / total * 100) if total > 0 else 0
    
    with col1:
        st.metric("Total Quejas", total)
    with col2:
        st.metric("Resueltas", resueltos)
    with col3:
        st.metric("Tasa Resolución", f"{tasa:.1f}%")
    with col4:
        pendientes = total - resueltos
        st.metric("Pendientes", pendientes)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Por Tipo de Error")
        tipo_counts = df_filtrado['tipo_error'].value_counts()
        st.bar_chart(tipo_counts)
    
    with col2:
        st.subheader("📈 Por Estado")
        estado_counts = df_filtrado['estado'].value_counts()
        st.bar_chart(estado_counts)
    
    # Tabla
    st.markdown("---")
    st.subheader("📋 Detalle de Quejas")
    
    # Preparar datos para mostrar
    df_mostrar = df_filtrado[['fecha', 'producto', 'tipo_error', 'estado']].copy()
    
    # Convertir fecha a string de forma segura
    df_mostrar['fecha'] = df_mostrar['fecha'].apply(
        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'Sin fecha'
    )
    
    st.dataframe(df_mostrar, use_container_width=True, height=400)
    
    # Exportar
    st.markdown("---")
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar CSV",
        data=csv,
        file_name=f"quejas_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("👈 Carga un archivo Excel en el menú lateral")

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Dashboard SEGPRO © 2024</div>", unsafe_allow_html=True)
