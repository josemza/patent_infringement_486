# 🧠 Análisis de Infracción a la Decisión Andina 486 usando Modelos de Lenguaje

Este proyecto busca entrenar un modelo de lenguaje (LLM) que **reciba una reivindicación de patente y genere una justificación argumentativa indicando si infringe o no** los artículos **14, 15, 20 o 21** de la **Decisión Andina 486**, con base en resoluciones emitidas por la oficina de patentes de Perú simulando el estilo técnico-jurídico de dichos informes.

---

## 🔍 Motivación

La interpretación legal y técnica de las reivindicaciones en patentes suele requerir análisis experto y experiencia multidisciplinaria. Automatizar parte de este proceso puede ayudar a:

- Agilizar la revisión y análisis en etapas tempranas de redacción o validación de patentes.
- Proporcionar apoyo a examinadores de patentes con borradores preliminares de evaluación.
- Detectar patrones comunes de infracción normativa.
- Permitir a los redactores de patentes obtener una opinión temprana y preliminar sobre sus reivindicaciones.
- Crear un asistente legal-tecnológico que emule el razonamiento de la autoridad administrativa.

---

## 🧱 Estructura del Proyecto

```
patent_infringement_486/
├── data/                      # Datos crudos y procesados
│   ├── indecopi/              # PDFs de resoluciones y metadatos
│   ├── epo/                   # Patentes descargadas por OPS API
│   ├── ocr/                   # Resultados de OCR
│   └── final_dataset/         # Dataset para entrenamiento de modelos
│
├── scripts/                   # Scripts de scraping, descarga y OCR
│   └── utils/                 # Funciones auxiliares
│
├── sql/                       # Query para Patstat
│
├── models/                    # Modelos entrenados
│   └── fine_tuned/            # Modelos ajustados al dominio
│
├── notebooks/                 # Exploración, preprocesamiento y experimentos
├── requirements.txt           # Dependencias del proyecto
├── config.ini (ignorado)      # Credenciales de acceso (no subir)
└── README.md                  # Este archivo
```

---

## ⚙️ Requisitos

Instalar dependencias:

```bash
pip install -r requirements.txt
```

> Dependencias externas:
>
> - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
> - Chrome + Chromedriver (para Selenium)
> - Ghostscript y Poppler (para manejo de PDFs en Windows)

---

## 🧲 Etapas del Proyecto

```mermaid
graph LR
A(Scraping Indecopi) --> B(Consultar Patstat)
B --> C(Descargar Patentes)
C --> D(Extraer texto claims - OCR)
D --> E(Construir dataset)
E --> F(Fine-tunning)
```

### 1. Scraping de resoluciones INDECOPI

- Script: `scripts/automatizar_descarga_paginado.py`
- Filtra por área "Invenciones y Nuevas Tecnologías"
- En palabras clave usar "articulo 15" y "articulo 20"
- Descarga PDFs y genera CSV con metadatos

### 2. Recuperar la familia de patentes en Patstat

- Query: `sql/query_sql.sql`
- Notebook #1: `notebooks/generar_numsol_patstat`
- Notebook #2: `notebooks/asignar_prioridad`
- Utiliza el número de las solictudes de patentes obtenidas en las resoluciones del Indecopi y formateadas en el Notebook #1.
- Se extrae solo la información de las publicaciones de las oficinas de España y México debido a que suelen publicar textos completos en español.

### 3. Descarga de patentes desde OPS (EPO)

- Script: `scripts/ops_download.py`
- Usa el número de la publicación para obtener las páginas de **reivindicaciones**
- Controla el uso de la API para evitar bloqueo por throttling

### 4. OCR sobre páginas de reivindicaciones

- Script: `scripts/ocr_pdf_2.py`
- Convierte TIFF a texto utilizando `pytesseract` y OpenCV
- Recorta automáticamente regiones de texto
- Construye un pdf con las reivindicaciones por cada solicitud

### 5. Construcción del dataset para *fine-tuning*

- Unión de resoluciones (como fuente de razonamiento experto) y texto de reivindicaciones extraídas
- Anotación de la infracción por artículo con su justificación, replicando el estilo de las resoluciones de INDECOPI

### 6. *Fine-tunning* del modelo generativo

- Se utilizarán modelos tipo LLM (ej: mistralai/Mistral-7B-Instruct, llama3, phi, patent-specific LLMs)
- El objetivo es que el modelo genere una decisión fundamentada en texto, indicando:
  - si hay o no infracción
  - qué artículo se infringe
  - el razonamiento detallado basado en el contenido de la reivindicación

---

## 🔐 Credenciales para OPS (config.ini)

Crear tu propio archivo `config.ini` basado en este template para poder utilizar la interfaz de Open Patent Services RESTful Web Services:

```ini
[ops_api]
client_id = TU_CLIENT_ID
client_secret = TU_SECRET
auth_url = https://ops.epo.org/3.2/auth/accesstoken
base_url = http://ops.epo.org/rest-services/published-data
```

Este archivo debe estar en la raíz del proyecto.

---

## 📌 Autor

**Jose Zúñiga**\
Ingeniero Industrial y Msc en Computer Science\
Proyecto personal

---

## 📜 Licencia

Este proyecto incluye un archivo de licencia explícito en el repositorio. Por defecto, se utiliza la licencia MIT, que permite uso, copia, modificación, fusión, publicación, distribución y sublicencia del software con muy pocas restricciones. Para más detalles, consulta el archivo `LICENSE` en la raíz del proyecto.

