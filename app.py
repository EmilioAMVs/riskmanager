from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import openai
import pandas as pd
import tldextract
from googlesearch import search
import os
import logging

# Configuración de la API de OpenAI
openai.api_key = ""

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

activos_totales = []
categorias_totales = []
valoraciones_totales = []

def buscar_activos(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    activos = [link['href'] for link in soup.find_all('a', href=True)]
    return activos[:10]  # Limitar a 10 resultados

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

def buscar_subdominios(dominio):
    subdominios = []
    query = f"site:{dominio}"
    for resultado in search(query, num_results=10):
        subdominio = tldextract.extract(resultado).fqdn
        if subdominio.endswith(dominio):
            subdominios.append(subdominio)
    return list(set(subdominios))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/buscar_activos')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    global activos_totales, categorias_totales, valoraciones_totales
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
    categorias_totales = [''] * len(activos_totales)
    valoraciones_totales = [''] * len(activos_totales)
    logging.debug(f"Activos totales encontrados: {activos_totales}")
    return jsonify(activos_totales)

@app.route('/categorizar', methods=['POST'])
def categorizar():
    global categorias_totales
    categorias_totales = categorizar_activos(activos_totales)
    logging.debug(f"Categorías asignadas: {categorias_totales}")
    return jsonify(categorias_totales)

@app.route('/evaluar', methods=['POST'])
def evaluar():
    global valoraciones_totales
    valoraciones_totales = valorar_activos(activos_totales)
    logging.debug(f"Valoraciones asignadas: {valoraciones_totales}")
    return jsonify(valoraciones_totales)

@app.route('/descargar', methods=['POST'])
def descargar():
    data = {
        'ID': list(range(1, len(activos_totales) + 1)),
        'Activo': activos_totales,
        'Categoría': categorias_totales,
        'Valoración': valoraciones_totales
    }
    df = pd.DataFrame(data)
    filename = f"resultados_activos_{request.json['dominio']}.xlsx"
    df.to_excel(filename, index=False)
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
