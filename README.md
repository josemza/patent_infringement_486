# 🧠 Análisis de Infracción a la Decisión Andina 486 en Reivindicaciones de Patentes

Este proyecto tiene como objetivo desarrollar un modelo de lenguaje que determine si una **reivindicación de patente infringe la Decisión Andina 486**, con base en resoluciones emitidas por la oficina de patentes de Perú (INDECOPI) y documentos oficiales de patente extraídos vía la API de la Oficina Europea de Patentes (EPO - OPS). Este proyecto se enfoca en los artículos 14,15, y 20 de la norma mencionada.

---

## 🔍 Motivación

La evaluación de infracciones a normas como la Decisión Andina 486 suele requerir análisis experto. Automatizar parte de este proceso puede ayudar a:

- Agilizar revisiones preliminares.
- Detectar patrones frecuentes de infracción.
- Proporcionar apoyo a examinadores y profesionales del área legal.
- Permitir a los redactores de patentes obtener una opinión temprana y preliminar sobre sus reivindicaciones.

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

> Asegúrate de tener instalado:
>
> - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
> - Chrome + Chromedriver (para Selenium)
> - Ghostscript y Poppler si usas Windows para manejo de PDFs

---

## 🧲 Etapas del Proyecto

### 1. Scraping de resoluciones INDECOPI

- Script: `scripts/automatizar_descarga_paginado.py`
- Filtra por área "Invenciones y Nuevas Tecnologías"
- Descarga PDFs y genera CSV con metadatos

### 2. Descarga de patentes desde OPS (EPO)

- Script: `scripts/ops_download.py`
- Usa el número de solicitud para obtener las páginas de **reivindicaciones**
- Controla el uso de la API para evitar bloqueo por throttling

### 3. OCR sobre páginas de reivindicaciones

- Script: `scripts/ocr_pdf_2.py`
- Convierte TIFF a texto utilizando `pytesseract` y OpenCV
- Recorta automáticamente regiones de texto

### 4. Preparación de dataset

- Combina los textos OCR con las resoluciones para construir un dataset supervisado

### 5. Entrenamiento y generación de decisiones con modelos

- El proyecto contempla tanto modelos de clasificación binaria como modelos generativos basados en LLMs.

- Modelos de clasificación: SVM, regresión logística y transformers como `anferico/bert-for-patents` son utilizados para predecir si una reivindicación infringe la norma.

- Modelos generativos: Se emplean LLMs ajustados al dominio legal para generar textos explicativos simulando el lenguaje técnico-jurídico empleado por INDECOPI.

- El objetivo es que, además de una clasificación (Sí/No), el sistema pueda **emitir una decisión fundamentada en texto**, similar a cómo lo haría un examinador en una resolución oficial.

- Fine-tuning y evaluación en tareas de clasificación binaria

---

## 🔐 Credenciales (config.ini)

Crear tu propio archivo `config.ini` basado en este template:

```ini
[ops_api]
client_id = TU_CLIENT_ID
client_secret = TU_SECRET
auth_url = https://ops.epo.org/3.2/auth/accesstoken
base_url = http://ops.epo.org/rest-services/published-data
```

Este archivo debe estar en la raíz del proyecto y está **excluido del repositorio** por seguridad (`.gitignore`).

---

## 📌 Autor

**Jose Zúñiga**\
Ingeniero Industrial y Msc en Computer Science\
Proyecto personal

---

## 📜 Licencia

Este proyecto incluye un archivo de licencia explícito en el repositorio. Por defecto, se utiliza la licencia MIT, que permite uso, copia, modificación, fusión, publicación, distribución y sublicencia del software con muy pocas restricciones. Para más detalles, consulta el archivo `LICENSE` en la raíz del proyecto.

