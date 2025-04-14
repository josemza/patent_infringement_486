import requests
import base64
import os
import csv
import time
import random
from PIL import Image
import xml.etree.ElementTree as ET
import configparser

# === CONFIGURA LA LECTURA DE LA CONFIGURACION ===
config = configparser.ConfigParser()
config.read("config.ini")

# === CONFIGURA CREDENCIALES ===
client_id = config['ops_api']['client_id']
client_secret = config['ops_api']['client_secret']
auth_url = config['ops_api']['auth_url']
base_url = config['ops_api']['base_url']

# === CONFIGURA CARPETAS ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
csv_file = os.path.join(BASE_DIR,"data","epo","patentes.csv")
output_folder = os.path.join(BASE_DIR,"data","epo","tiffs")
output_folder_pdf = os.path.join(BASE_DIR,"data","epo","claims_pdf")
output_log = os.path.join(BASE_DIR,"data","epo","resultado_descargas_ops.csv")

peticiones_realizadas = 0
inicio_minuto = time.time()
MAX_POR_MINUTO = 30

def clean_filename(doc_number):
    return doc_number.replace("/", "_").replace("(", "").replace(")", "").replace(" ", "_")

def dot_filename(doc_number):
    return doc_number.replace("/",".")

# === OBTENER TOKEN ===
def get_access_token(client_id, client_secret, auth_url):
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}

    response = requests.post(auth_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# === OBTENER PÁGINA DE INICIO DE LOS CLAIMS ===
def get_claims_start_page(doc_number, token, base_url):
    doc_number_dot = dot_filename(doc_number)
    url = f"{base_url}/publication/docdb/{doc_number_dot}/images"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    ns = {'ops': 'http://ops.epo.org'}

    sections = []
    for section in root.findall('.//ops:document-section', ns):
        name = section.attrib.get('name')
        start_page = int(section.attrib.get('start-page', 1))
        sections.append((name, start_page))

    sections.sort(key=lambda x: x[1])
    start = None
    end = None
    for i, (name, page) in enumerate(sections):
        if name == 'CLAIMS':
            start = page
            if i + 1 < len(sections):
                end = sections[i + 1][1] - 1
            break
    
    if start is None:
        return 1, None
    return start, end  # Por defecto, descargar desde la primera página si no se encuentra

# === DESCARGAR PÁGINAS INDIVIDUALES ===
def download_pages(doc_number, token, base_url, start_page=1, end_page=None):
    global peticiones_realizadas, inicio_minuto
    os.makedirs(output_folder, exist_ok=True)
    page = start_page
    pdf_files = []

    while True:
        if end_page is not None and page > end_page:
            print("✅ Se alcanzó la última página de claims.")
            break
        
        # Control de limite por minuto
        peticiones_realizadas += 1
        if peticiones_realizadas >= MAX_POR_MINUTO:
            elapsed = time.time() - inicio_minuto
            if elapsed < 60:
                espera = 60 - elapsed
                print(f"⏱ Esperando {espera:.1f}s para respetar límite por minuto...")
                time.sleep(espera)
            peticiones_realizadas = 0
            inicio_minuto = time.time()

        url = f"{base_url}/images/{doc_number}/fullimage.tiff?Range={page}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "image/tiff"
        }
        response = requests.get(url, headers=headers)
        # print(url)
        # print(response.status_code)

        # CONTROL DE THROTTLING
        throttle = response.headers.get("X-Throttling-Control","")
        if "black" in throttle.lower():
            print("⛔️ Límite alcanzado (black). Esperando 60 segundos...")
            time.sleep(60)
            continue
        elif "red" in throttle.lower():
            print("⚠️ Nivel 'red' alcanzado. Esperando 10 segundos...")
            time.sleep(10)

        if response.status_code == 200:
            filename = os.path.join(output_folder, f"{clean_filename(doc_number)}_p{page}.tiff")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Página {page} descargada: {filename}")
            pdf_files.append(filename)
            page += 1
        elif response.status_code == 404:
            print("✅ Todas las páginas descargadas.")
            break
        else:
            print(f"❌ Error al descargar página {page}: {response.status_code}")
            break

        time.sleep(random.uniform(2,5))

    return pdf_files

# === UNIR PÁGINAS EN UN SOLO PDF ===
def merge_tiffs_to_pdf(pdf_files, output_file):
    # images = [Image.open(f).convert('RGB') for f in pdf_files]
    os.makedirs(output_folder_pdf, exist_ok=True)
    images = []
    for f in pdf_files:
        if f.lower().endswith(('.tiff', '.tif')):
            try:
                img = Image.open(f).convert('RGB')
                images.append(img)
            except Exception as e:
                print(f"⚠️ No se pudo abrir {f}: {e}")
    if images:
        images[0].save(output_file, save_all=True, append_images=images[1:])
        print(f"📄 PDF final guardado como: {output_file}")
    else:
        print("⚠️ No hay imágenes TIFF para convertir a PDF.")

def load_patent_list():
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row["doc_number"].strip() for row in reader]

def append_to_log(entry):
    file_exists = os.path.isfile(output_log)
    with open(output_log, "a", newline='', encoding='utf-8') as csvfile:
        fieldnames = ["doc_number", "resultado"]
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)
    
# === MAIN ===
def main():
    try:
        token = get_access_token(client_id, client_secret, auth_url)
        token_time = time.time()
        print("🔐 Token obtenido.")

        patentes = load_patent_list()

        for doc_number in patentes:
            print(f"\n📘 Procesando: {doc_number}")

            # Verificar si el token ha vencido (18 min de margen)
            if time.time() - token_time > 1080:
                print("🔁 Token vencido. Renovando...")
                token = get_access_token(client_id, client_secret, auth_url)
                token_time = time.time()

            try:
                pdf_path = os.path.join(output_folder_pdf, f"{clean_filename(doc_number)}_claims.pdf")
                if os.path.exists(pdf_path):
                    print(f"⏩ Ya existe el PDF. Se omite: {pdf_path}")
                    append_to_log({"doc_number": doc_number, "resultado": "YA EXISTE"})
                    continue

                start_page, end_page = get_claims_start_page(doc_number, token, base_url)
                print(f"📌 Claims desde página {start_page} hasta {end_page if end_page else 'el final'}")

                pdf_pages = download_pages(doc_number, token,base_url, start_page=start_page, end_page=end_page)

                if pdf_pages:
                    merge_tiffs_to_pdf(pdf_pages, pdf_path)
                    append_to_log({"doc_number": doc_number, "resultado": "PDF OK"})
                else:
                    append_to_log({"doc_number": doc_number, "resultado": "SIN PAGINAS"})
                    
            except Exception as e:
                print(f"❌ Error con {doc_number}: {e}")
                append_to_log({"doc_number": doc_number, "resultado": f"ERROR: {e}"})
                time.sleep(5) # espera breve para evitar bloqueo

    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    main()
