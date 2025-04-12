import os
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# === Configuración ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF_DIR = os.path.join(BASE_DIR, "data", "indecopi", "pdfs")
CSV_FILE = os.path.join(BASE_DIR,"data","indecopi","resoluciones_indecopi.csv")
HTML_DEBUG_DIR = os.path.join(BASE_DIR,"data","indecopi","html_debug")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(HTML_DEBUG_DIR, exist_ok=True)

URL_BASE = "https://servicio.indecopi.gob.pe/buscadorResoluciones/propiedad-intelectual.seam"

# === Iniciar navegador ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 60)

# === Abrir página ===
driver.get(URL_BASE)
wait.until(EC.presence_of_element_located((By.ID, "busqueda-avanzada")))
driver.find_element(By.ID, "busqueda-avanzada").click()
wait.until(EC.presence_of_element_located((By.ID, "FormListado")))

# Palabra clave
palabra_clave = driver.find_element(By.ID, "FormListado:txtSumilla")
palabra_clave.clear()
palabra_clave.send_keys("articulo 20")

# Seleccionar área
boton_combo = driver.find_element(By.ID, "FormListado:cboAreaPrimeracomboboxButton")
boton_combo.click()
time.sleep(1.5)
opciones = driver.find_elements(By.XPATH, "//div[@id='FormListado:cboAreaPrimeralist']//span[contains(@class, 'rich-combobox-item')]")
print(f"🔍 Se encontraron {len(opciones)} opciones en el combo.")
seleccionado = False
for opcion in opciones:
    texto = opcion.text.strip()
    print(f"⏺ Opción encontrada: {texto}")
    if texto == "Invenciones y Nuevas Tecnologias":
        opcion.click()
        print("✅ Opción seleccionada correctamente.")
        seleccionado = True
        break

if not seleccionado:
    print("🚫 No se encontró la opción deseada en el combo.")
    driver.quit()
    exit()

# Clic en buscar
time.sleep(1.5)
boton_buscar = driver.find_element(By.ID, "FormListado:btnAceptar")
driver.execute_script("arguments[0].click();", boton_buscar)
print("🔎 Se hizo clic en el botón Buscar.")

# Esperar panel de búsqueda
WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.ID, "FormListado1:panBuscandoContent"))
)
print("⏳ Panel 'Buscando...' desapareció, continuando...")

# 💡 Agregar pausa para asegurar que los resultados se rendericen completamente
time.sleep(20)

# Esperar filas visibles
try:
    def esperar_filas_resultado(driver, max_intentos=30):
        for i in range(max_intentos):
            filas = driver.find_elements(By.XPATH, "//tbody[@id='FormListado3:testpList:tb']/tr")
            if len(filas) >= 2:
                print(f"✅ Se detectaron {len(filas)} filas en la tabla.")
                return filas
            time.sleep(5)
        raise TimeoutException("⏰ No se detectaron filas visibles tras esperar.")

    try:
        filas = esperar_filas_resultado(driver)
    except TimeoutException as e:
        print(f"⚠️ {e}")
        with open(os.path.join(HTML_DEBUG_DIR,"debug_filas_timeout.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        exit()

except TimeoutException:
    print("⚠️ No se encontraron filas tras esperar.")
    with open(os.path.join(HTML_DEBUG_DIR,"debug_no_filas_post_espera.html"), "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.quit()
    exit()

# === Función para descargar PDFs ===
def descargar_pdf(url, nombre_archivo):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and 'application/pdf' in r.headers.get('Content-Type', ''):
            with open(nombre_archivo, "wb") as f:
                f.write(r.content)
        else:
            print(f"⚠️ Respuesta inválida o no es PDF: {url}")
    except Exception as e:
        print(f"⚠️ Error al descargar {url}: {e}")


# === Recorrer todas las páginas ===
todos_los_datos = []
pagina = 1
while True:
    print(f"📄 Procesando página {pagina}...")

    try:
        filas = esperar_filas_resultado(driver)
        print(f"✅ Se detectaron {len(filas)} filas en la tabla.")
    except TimeoutException as e:
        print(f"⚠️ {e}")
        with open(os.path.join(HTML_DEBUG_DIR,f"debug_filas_timeout_pagina_{pagina}.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        break

    print(f"🔍 Total de filas encontradas (pares info + sumilla): {len(filas)}")

    i = 0
    while i + 1 < len(filas):  # Nos aseguramos de tener al menos dos filas para procesar el par
        try:
            fila_info = filas[i]
            fila_sumilla = filas[i + 1]
            i += 2

            celdas = fila_info.find_elements(By.TAG_NAME, "td")
            if len(celdas) < 5:
                print("⚠️ Fila con menos de 5 celdas. Se omite.")
                continue

            expediente = celdas[0].text.strip()
            fecha = celdas[1].text.strip()
            solicitud = celdas[2].text.strip()
            solicitante = celdas[3].text.strip()

            try:
                link_pdf_elem = celdas[4].find_element(By.TAG_NAME, "a")
                url_pdf = link_pdf_elem.get_attribute("href")
                nombre_pdf = f"{expediente.replace('/', '_')}.pdf"
                ruta_destino = os.path.join(PDF_DIR, nombre_pdf)
            except:
                print(f"⚠️ No se encontró enlace PDF en expediente {expediente}")
                url_pdf = ""
                nombre_pdf = ""
                ruta_destino = ""

            sumilla = fila_sumilla.text.strip()

            if url_pdf:
                descargar_pdf(url_pdf, ruta_destino)

            todos_los_datos.append({
                "expediente": expediente,
                "fecha": fecha,
                "solicitud": solicitud,
                "solicitante": solicitante,
                "sumilla": sumilla,
                "nombre_pdf": nombre_pdf,
                "url_pdf": url_pdf
            })

            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error al procesar fila: {e}")
            continue

    # Guardar HTML de depuración
    # with open(os.path.join(HTML_DEBUG_DIR,f"debug_post_pagina_{pagina}.html"), "w", encoding="utf-8") as f:
    #     f.write(driver.page_source)

    # Intentar avanzar a la siguiente página
    try:
        pagina += 1
        print(f"➡️ Intentando ir a la página {pagina}...")

        # Buscar el enlace que contiene el número de la siguiente página
        link_siguiente = driver.find_element(
            By.XPATH,
            f"//a[contains(@id, 'cmlPage') and normalize-space(text())='{pagina}']"
        )
        driver.execute_script("arguments[0].click();", link_siguiente)

        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.ID, "FormListado1:panBuscandoContent"))
        )
        print("⏳ Panel 'Buscando...' desapareció, continuando...")
        time.sleep(5)  # pequeña pausa
    except Exception as e:
        print(f"📌 No se pudo avanzar a la página {pagina}: {e}")
        break


# === Guardar a CSV ===
df = pd.DataFrame(todos_los_datos)
df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
driver.quit()
print(f"✅ Proceso completo. Se guardaron {len(df)} resoluciones.")
