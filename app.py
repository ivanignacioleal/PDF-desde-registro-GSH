# === LIBRERÍAS ===
import sqlite3                            # Manejo de bases de datos SQLite
import pandas as pd                       # Análisis y manipulación de datos en estructuras tipo DataFrame
import numpy as np                        # Operaciones numéricas (aunque no se usa directamente)
import os                                 # Operaciones del sistema, como verificar si existe un archivo
import matplotlib.pyplot as plt           # Visualización de gráficos básicos
import seaborn as sns                     # Visualización estadística basada en Matplotlib
from scipy import stats                   # Herramientas estadísticas como correlación de Pearson
from sklearn.linear_model import LinearRegression      # Modelo de regresión lineal
from sklearn.model_selection import train_test_split   # División de datos en entrenamiento y prueba
import plotly.express as px               # Visualizaciones interactivas en HTML
from bokeh.plotting import figure, show, output_file   # Gráficos interactivos con Bokeh
from bokeh.layouts import column          # Organización de layouts en Bokeh
import dash                               # Framework web para dashboards interactivos
from dash import dcc, html, dash_table    # Componentes visuales para Dash
from dash.dependencies import Input, Output   # Conexiones interactivas entre componentes de Dash
import threading                          # Para ejecutar la app de Dash sin bloquear el script

# === PASO 1: CARGA Y LIMPIEZA DE DATOS ===
csv_file = 'winemag-data-130k-v2.csv'     # Nombre del archivo CSV a cargar

# Verifica si el archivo CSV existe; si no, lanza un error
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"No se encontró el archivo: {csv_file}")

# Columnas que se van a usar del CSV
cols = ['country', 'description', 'designation', 'points', 'price',
        'province', 'region_1', 'region_2', 'taster_name', 'taster_twitter_handle',
        'title', 'variety', 'winery']

# Carga el CSV solo con las columnas seleccionadas
df = pd.read_csv(csv_file, usecols=cols)

# Normaliza nombres de columnas (minúsculas, sin espacios)
df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]

# Elimina registros con valores críticos nulos
df.dropna(subset=['country', 'points', 'price', 'variety', 'winery'], inplace=True)

# Rellena los valores nulos de columnas no críticas con 'Desconocido'
df['taster_name'] = df['taster_name'].fillna('Desconocido')
df['taster_twitter_handle'] = df['taster_twitter_handle'].fillna('Desconocido')

# Guarda el dataset limpio en un nuevo archivo CSV
clean_csv = "wine_clean.csv"
df.to_csv(clean_csv, index=False)

# === RESUMEN ANALÍTICO EN CONSOLA ===
print("\n--- RESUMEN GENERAL ---")
print("Total de registros analizados:", len(df))   # Muestra cantidad de filas
print("Variedad más frecuente:", df['variety'].mode()[0])   # Muestra la variedad más común
print("País con mayor puntuación promedio:", df.groupby('country')['points'].mean().idxmax())  # País con mejor puntaje promedio
print("Promedio general de puntos:", round(df['points'].mean(), 2))   # Puntaje promedio general
print("Promedio general de precio:", round(df['price'].mean(), 2))   # Precio promedio general

# === CONEXIÓN A SQLITE ===
conn = sqlite3.connect("wine_reviews.db")      # Conecta (o crea) una base de datos SQLite
cursor = conn.cursor()                         # Crea un cursor para ejecutar comandos SQL

# Crea una tabla si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vinos (
        titulo TEXT, descripcion TEXT, puntos INTEGER, precio REAL,
        variedad TEXT, bodega TEXT, pais TEXT
    )
''')

# Limpia la tabla antes de insertar nuevos datos
cursor.execute("DELETE FROM vinos")

# Inserta todos los registros del DataFrame en la base de datos
for _, row in df.iterrows():
    cursor.execute('''INSERT INTO vinos VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (row['title'], row['description'], row['points'], row['price'],
                    row['variety'], row['winery'], row['country']))
conn.commit()   # Confirma los cambios en la base de datos

# === LECTURA DESDE SQLITE PARA VISUALIZACIONES ===
query = """
SELECT puntos, precio, titulo, bodega, variedad, pais FROM vinos
WHERE precio IS NOT NULL AND puntos IS NOT NULL
"""
df_vinos = pd.read_sql_query(query, conn)   # Carga los datos desde SQLite a un DataFrame

# === VISUALIZACIÓN 1: Matplotlib/Seaborn ===
plt.figure(figsize=(10, 6))    # Define el tamaño del gráfico
sns.scatterplot(data=df_vinos, x="precio", y="puntos", hue="pais", alpha=0.5)  # Muestra dispersión de precio vs puntos por país
plt.title("Precio vs Puntos por País")
plt.xlim(0, 200)               # Limita el eje X para mejor visualización
plt.tight_layout()            # Ajusta los márgenes
plt.savefig("scatter_precio_puntos.png")   # Guarda la imagen
plt.close()
os.startfile("scatter_precio_puntos.png")  # Abre automáticamente la imagen generada

# === VISUALIZACIÓN 2: Scipy Pearson ===
r, p = stats.pearsonr(df_vinos["precio"], df_vinos["puntos"])   # Calcula correlación entre precio y puntos
print(f"Coef. Pearson: {r:.2f}, p-valor: {p:.4f}")              # Muestra coeficiente y nivel de significancia

# === VISUALIZACIÓN 3: Scikit-learn ===
X = df_vinos[["precio"]]              # Variable independiente
y = df_vinos["puntos"]                # Variable dependiente
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)  # Divide los datos
model = LinearRegression().fit(X_train, y_train)   # Entrena el modelo
print(f"Regresión: y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}")   # Muestra la ecuación de la regresión

# === VISUALIZACIÓN 4: Plotly ===
df_top = df_vinos.groupby("variedad")["puntos"].mean().sort_values(ascending=False).head(10).reset_index()  # Top 10 variedades
fig = px.bar(df_top, x="variedad", y="puntos", title="Top 10 Variedades por Puntuación Promedio")  # Gráfico de barras
fig.write_html("plotly_top10_variedades.html")    # Guarda como HTML
os.startfile("plotly_top10_variedades.html")      # Abre el gráfico en el navegador

# === VISUALIZACIÓN 5: Bokeh ===
output_file("bokeh_precio_vs_puntos.html")   # Archivo de salida en HTML
p = figure(title="Precio vs Puntos (Bokeh)", x_axis_label="Precio", y_axis_label="Puntos")   # Define el gráfico
p.scatter(df_vinos["precio"], df_vinos["puntos"], size=5, color="navy", alpha=0.5)           # Añade los puntos
show(p)   # Abre el gráfico en el navegador

# === VISUALIZACIÓN 6: Dash App ===
app = dash.Dash(__name__)  # Se crea una instancia de la aplicación Dash.

variedades = sorted(df_vinos["variedad"].dropna().unique())  # Se obtiene la lista de variedades únicas (sin nulos), ordenadas alfabéticamente.

app.layout = html.Div([  # Se define el layout de la aplicación con estructura HTML simulada.
    html.H1("Análisis Interactivo de Vinos"),  # Título principal de la app.
    html.Label("Seleccione una variedad:"),  # Etiqueta que acompaña al menú desplegable.
    dcc.Dropdown(  # Componente de selección desplegable.
        id="dropdown-variedad",  # ID del componente (se usa en la función callback).
        options=[{"label": v, "value": v} for v in variedades],  # Se generan las opciones del dropdown usando las variedades.
        value=variedades[0]  # Se establece una variedad por defecto (la primera en orden alfabético).
    ),
    html.Div([  # Contenedor HTML que agrupa los gráficos y la tabla.
        dcc.Graph(id="grafico-1"),  # Primer gráfico, se actualizará dinámicamente por el callback.
        dcc.Graph(id="grafico-2"),  # Segundo gráfico, también controlado dinámicamente.
        dash_table.DataTable(id="tabla-vinos",  # Tabla de datos con información detallada de vinos.
                             columns=[  # Definición de columnas visibles.
                                 {"name": i, "id": i} for i in ["titulo", "precio", "puntos", "pais", "bodega"]
                             ],
                             style_table={'overflowX': 'auto'},  # Permite scroll horizontal si es necesario.
                             style_cell={"textAlign": "left"},  # Alineación del contenido de las celdas a la izquierda.
                             page_size=10)  # Se muestran 10 filas por página en la tabla.
    ])
])

@app.callback(  # Decorador que define el callback que actualiza los componentes según la interacción del usuario.
    [Output("grafico-1", "figure"),  # Primer gráfico que será actualizado.
     Output("grafico-2", "figure"),  # Segundo gráfico que será actualizado.
     Output("tabla-vinos", "data")],  # Datos que alimentan la tabla.
    [Input("dropdown-variedad", "value")]  # El valor seleccionado del dropdown será la entrada del callback.
)
def actualizar_visuales(variedad):  # Función que se ejecuta al cambiar la variedad seleccionada.
    dff = df_vinos[df_vinos["variedad"] == variedad]  # Filtra el dataframe para la variedad seleccionada.
    
    fig1 = px.bar(dff.groupby("pais")["puntos"].mean().reset_index(),  # Crea gráfico de barras: puntos promedio por país.
                  x="pais", y="puntos", title=f"Puntos promedio de {variedad} por País")
    
    fig2 = px.scatter(dff, x="precio", y="puntos", color="pais",  # Crea gráfico de dispersión: precio vs puntos por país.
                      title=f"Precio vs Puntos para {variedad}")
    
    tabla = dff.sort_values(by="puntos", ascending=False).head(10)[  # Selecciona top 10 vinos por puntuación.
        ["titulo", "precio", "puntos", "pais", "bodega"]].to_dict("records")  # Convierte los datos a formato de tabla compatible.
    
    return fig1, fig2, tabla  # Devuelve los gráficos y tabla actualizados.

def run_dash():  # Función para ejecutar la app Dash en un hilo separado.
    app.run(debug=False, use_reloader=False)  # Inicia el servidor de la app sin recarga automática.

thread = threading.Thread(target=run_dash)  # Crea un hilo independiente para ejecutar la app sin bloquear el flujo principal.
thread.start()  # Inicia el hilo (y por ende la app).

conn.close()  # Cierra la conexión a la base de datos SQLite.
