# Importaciones necesarias
from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import openai
import pandas as pd
from googlesearch import search
import tldextract
import logging  # Importación de logging para depuración

# Configuración de la API de OpenAI
openai.api_key = 'sk-proj-tCNfA8Wv0hDBiRKNhMNzT3BlbkFJvtU4PC3Sj8htQmMZniDt'

# Creación de la aplicación Flask
app = Flask(__name__)

# Configuración de logging para depuración
logging.basicConfig(level=logging.DEBUG)

# Variables globales para almacenar datos
activos_totales = []
categorias_totales = []
valoraciones_totales = []

# Función para buscar activos en una URL dada
def buscar_activos(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    activos = [link['href'] for link in soup.find_all('a', href=True)]
    return activos[:10]  # Limitar a 10 resultados

# Función para categorizar activos utilizando OpenAI
def categorizar_activos(activos):
    categorias = []
    tipos = ['Datos', 'Servicio', 'Sitios', 'Personal', 'Hardware', 'Software', 'Organización', 'Otros']
    for activo in activos:
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=f"Clasifica el siguiente activo digital en una de las siguientes categorías: {', '.join(tipos)}.\nActivo: {activo}\nCategoría:",
            max_tokens=50
        )
        categoria = response.choices[0].text.strip()
        categorias.append(categoria if categoria in tipos else 'Otros')
    return categorias

# Función para valorar activos utilizando OpenAI
def valorar_activos(activos):
    valoraciones = []
    for activo in activos:
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=f"Valora el siguiente activo digital basado en su impacto financiero, reputacional y operativo: {activo}\nValoración:",
            max_tokens=50
        )
        valoracion = response.choices[0].text.strip()
        valoraciones.append(valoracion)
    return valoraciones

# Función para buscar subdominios asociados a un dominio dado
def buscar_subdominios(dominio):
    subdominios = []
    query = f"site:{dominio}"
    for resultado in search(query, num_results=10):
        subdominio = tldextract.extract(resultado).fqdn
        if subdominio.endswith(dominio):
            subdominios.append(subdominio)
    return list(set(subdominios))

# Ruta de inicio de la aplicación
@app.route('/')
def home():
    return render_template('home.html')

# Ruta para la página de búsqueda de activos
@app.route('/buscar_activos')
def index():
    return render_template('index.html')

# Ruta para realizar la búsqueda de activos
@app.route('/buscar', methods=['POST'])
def buscar():
    global activos_totales
    data = request.get_json()
    dominio = data['dominio']
    logging.debug(f"Buscando subdominios para: {dominio}")
    subdominios = buscar_subdominios(dominio)
    logging.debug(f"Subdominios encontrados: {subdominios}")
    activos_totales = []
    for subdominio in subdominios:
        url = f"https://{subdominio}"
        logging.debug(f"Buscando activos en: {url}")
        activos = buscar_activos(url)
        activos_totales.extend(activos)
    logging.debug(f"Activos totales encontrados: {activos_totales}")
    return jsonify(activos_totales)

# Ruta para categorizar los activos encontrados
@app.route('/categorizar', methods=['POST'])
def categorizar():
    global categorias_totales
    categorias_totales = categorizar_activos(activos_totales)
    logging.debug(f"Categorías asignadas: {categorias_totales}")
    return jsonify(categorias_totales)

# Ruta para evaluar los activos encontrados
@app.route('/evaluar', methods=['POST'])
def evaluar():
    global valoraciones_totales
    valoraciones_totales = valorar_activos(activos_totales)
    logging.debug(f"Valoraciones asignadas: {valoraciones_totales}")
    return jsonify(valoraciones_totales)

# Ruta para descargar los resultados en Excel
@app.route('/descargar', methods=['POST'])
def descargar():
    data = {
        'Activo': activos_totales,
        'Categoría': categorias_totales,
        'Valoración': valoraciones_totales
    }
    df = pd.DataFrame(data)
    filename = 'resultados_activos.xlsx'
    df.to_excel(filename, index=False)
    return send_file(filename, as_attachment=True)

# Punto de entrada de la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
