"""
Aquí buscamos analizar la carpeta con las imágenes .tiff y obtener el texto OCR

 ▸ Lee cada .tiff, recorta automáticamente la zona de texto
 ▸ Ejecuta Tesseract (eng + spa)
 ▸ Guarda el resultado como .txt
 ▸ Guarda imagen log como .png

Uso:
    python ocr_imagenes_tiff.py --input-dir data/epo/tiffs \
                                --output-dir data/ocr/txt \
                                --debug-dir data/ocr/visual_debug
"""
import argparse, os, glob
import pytesseract, cv2, numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import re
from collections import defaultdict

# ====== Parámetros CLI ======
parser = argparse.ArgumentParser()
parser.add_argument("--input-dir",  required=True,  help="Carpeta con los .tiff")
parser.add_argument("--output-dir", required=False, help="Dónde guardar los .txt")
parser.add_argument("--debug-dir",  required=False, help="Carpeta para PNG de depuración")
parser.add_argument("--dpi", type=int, default=300,   help="Solo para referencia / metadatos")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True) if args.output_dir else None
os.makedirs(args.debug_dir,  exist_ok=True) if args.debug_dir  else None

# ====== Funciones ======
def limpia_parrafos(raw_text: str) -> str:
    """
    • Quita líneas que solo tienen números (o están vacías)
    • Elimina cabeceras estilo 'ES 2 308 562 T3'
    • Reconstruye guiones de palabra partida al final de línea
    • Devuelve el texto ya como párrafos continuos
    """
    # 1. Filtrado línea a línea
    lineas_limpias = []
    for linea in raw_text.splitlines():
        # fuera líneas que son SOLO números
        if re.fullmatch(r"\s*\d+\s*", linea):
            continue
        # fuera cabeceras tipo 'ES 2 308 562 T3'
        if re.fullmatch(r"\s*[A-Z]{2}\s+\d+(\s+\d+)*\s+[A-Z]\d?\s*", linea):
            continue
        lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # 2. Reconstruye palabras cortadas con guión + salto de línea
    texto = re.sub(r"-\n\s*", "", texto)

    # 3. Normalizar saltos de párrafo (dos o más \n seguidos → exactamente dos)
    texto = re.sub(r"\n{2,}", "\n", texto)

    # 4. Salto simple sin punto anterior → espacio (se concatena)
    #    • (?<![.\n])  => el carácter antes del \n no es punto ni otro \n
    #    • (?!\n)      => el carácter después del \n no es otro \n
    texto = re.sub(r"(?<![.\n])\n(?!\n)", " ", texto)

    return texto

def get_patent_name(file_name:str) -> str:
    """Genera el nombre del archivo txt bajo el formato MX_XXXXXX_XX.txt"""
    pattern = re.compile(r"^(.*?)_p\d+")

    code_name = pattern.match(file_name).group(1) if pattern.match(file_name) else file_name

    return code_name

def load_tiff(path:str) -> np.ndarray:
    """Carga un TIFF con PIL y devuelve un ndarray BGR (OpenCV)."""
    img = Image.open(path)

    try:
        img.seek(0)
    except (EOFError, AttributeError):
        pass
    
    mode = img.mode

    # TIFF bitonal (“1” → bool)
    if mode == "1":
        # bool → uint8 {0,255}
        arr = np.array(img, dtype=np.uint8) * 255
        # OpenCV necesita 3 canales para el pipeline ⇒ GRAY→BGR
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

    # Escala de grises (“L”) o paleta (“P”)
    if mode in ("L", "P"):
        arr = np.array(img.convert("L"), dtype=np.uint8)
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

    # RGB o cualquier otra cosa
    if mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def auto_crop(img_bgr:np.ndarray) -> np.ndarray:
    """Recorta la zona de texto usando un umbral vertical."""
    gray   = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thr = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    vertical_sum = thr.sum(axis=0)
    umbral       = vertical_sum.max() * 0.4
    limite_izq   = next((i for i,v in enumerate(vertical_sum) if v>umbral), 0)

    thr = cv2.bitwise_not(thr)            # texto negro
    return thr[:, limite_izq:]            # recorte

# ====== Procesamiento por archivo ======
def main():
    tiff_paths = sorted(glob.glob(os.path.join(args.input_dir, "*.tif*")))
    if not tiff_paths:
        raise FileNotFoundError(f"No se encontraron TIFF en {args.input_dir}")

    textos_por_patente = defaultdict(list)

    for idx, path in enumerate(tiff_paths, 1):
        print(f"🖼️  Procesando {os.path.basename(path)} ({idx}/{len(tiff_paths)})")
        img   = load_tiff(path)
        rec   = auto_crop(img)
        texto = pytesseract.image_to_string(rec, lang="eng+spa")

        texto = limpia_parrafos(texto)

        base = os.path.splitext(os.path.basename(path))[0]
        file_name = get_patent_name(base)

        textos_por_patente[file_name].append(texto)

        # Guardar OCR
        if args.output_dir:
            for file_name, fragmentos in textos_por_patente.items():
                cuerpo = limpia_parrafos("\n".join(fragmentos))
                file = os.path.join(args.output_dir, f"{file_name}.txt")
                with open(file, "w", encoding="utf-8") as f:
                    f.write(cuerpo)
            print(f"\tL...📝  Guardado {file}  ({len(fragmentos)} pág.)")

        # Guardar visual debug
        if args.debug_dir:
            dbg = np.hstack([cv2.cvtColor(img, cv2.COLOR_BGR2RGB), cv2.cvtColor(rec, cv2.COLOR_GRAY2RGB)])
            Image.fromarray(dbg).save(os.path.join(args.debug_dir, f"dbg_{os.path.basename(path)}.png"))

if __name__ == "__main__":
    main()
