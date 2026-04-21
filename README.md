# Dashboard de Tráfico Vehicular ANI

Aplicación web desarrollada en **Streamlit** para analizar datos abiertos de tráfico vehicular en peajes de la ANI. El proyecto consume datos dinámicamente desde una fuente pública, los transforma y los presenta mediante visualizaciones interactivas orientadas a preguntas reales.

## Objetivo

Construir un dashboard interactivo que permita responder preguntas como:

- ¿Cómo evoluciona el tráfico en el tiempo?
- ¿Qué peajes concentran más flujo?
- ¿Qué categorías tarifarias mueven más volumen?
- ¿Dónde hay más evasión?
- ¿Cuál es la relación entre la tarifa y el tráfico?
- ¿Cómo se comparan varios peajes entre sí?

## Tecnologías utilizadas

- **Python**
- **Streamlit**
- **Pandas**
- **Plotly**
- **Requests**
- **python-dotenv**
- **Render** para despliegue

## Estructura del proyecto

```text
proyecto_accidentes_envigado/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── data/
│   ├── trafico_ani.csv
│   └── sync_meta.json
└── src/
    ├── extract.py
    ├── transform.py
    ├── plots.py
    ├── insights.py
    └── catalogs.py
```

## Funcionalidades principales

- Consumo dinámico de datos abiertos desde una URL pública.
- Actualización automática del CSV local.
- Limpieza y transformación de datos.
- Filtros interactivos por año, peaje, categoría y fechas.
- KPIs ejecutivos.
- Gráficos interactivos con Plotly.
- Insights automáticos.
- Comparador de peajes.
- Descarga de datos filtrados en CSV.
- Despliegue en la nube con Render.

## Fuente de datos

Dataset público de **[datos.gov.co](https://www.datos.gov.co/Transporte/Tr-fico-Vehicular-ANI/8yi9-t44c/about_data)**:

```env
DATA_URL=https://datos.gov.co/resource/8yi9-t44c.csv?$limit=50000
DATA_FORMAT=csv
CHECK_INTERVAL_MINUTES=15
```

## Instalación local

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/dashboard-trafico-ani.git
cd dashboard-trafico-ani
```

### 2. Crear y activar entorno virtual

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear archivo `.env`

```env
DATA_URL=https://datos.gov.co/resource/8yi9-t44c.csv?$limit=50000
DATA_FORMAT=csv
CHECK_INTERVAL_MINUTES=15
```

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

## Variables de entorno

### Local

```env
DATA_URL=https://datos.gov.co/resource/8yi9-t44c.csv?$limit=50000
DATA_FORMAT=csv
CHECK_INTERVAL_MINUTES=15
```

### Producción en Render

```text
DATA_URL=https://datos.gov.co/resource/8yi9-t44c.csv?$limit=50000
DATA_FORMAT=csv
CHECK_INTERVAL_MINUTES=15
PYTHON_VERSION=3.13.5
```

## Despliegue en Render

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Módulos del proyecto

### `app.py`
Controla el flujo general de la aplicación, la interfaz y la navegación por pestañas.

### `src/extract.py`
Gestiona la descarga, sincronización y almacenamiento local de los datos.

### `src/transform.py`
Limpia, transforma y enriquece el dataset con variables derivadas.

### `src/plots.py`
Contiene todas las funciones de visualización con Plotly.

### `src/insights.py`
Genera hallazgos automáticos para enriquecer la interpretación del dashboard.

### `src/catalogs.py`
Contiene catálogos auxiliares, como el significado de categorías tarifarias.

## KPIs incluidos

- Tráfico total
- Evasores
- Exentos
- Tarifa promedio
- Peaje dominante
- Tasa global de evasión

## Secciones del dashboard

1. **Resumen ejecutivo**
2. **Evolución temporal**
3. **Concentración por peajes**
4. **Categorías y tarifas**
5. **Riesgo operativo**
6. **Comparador**
7. **Datos**

## Posibles mejoras futuras

- mapas de peajes
- comparación avanzada entre periodos
- exportación a Excel
- indicadores de tendencia
- visualizaciones geográficas
- conclusiones automáticas más detalladas

## Autor

Proyecto desarrollado por **Keith** como parte de una actividad académica de visualización de datos con Streamlit.

## Enlace de despliegue

```text
https://dashboard-trafico-ani.onrender.com
```
