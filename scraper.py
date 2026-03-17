import requests
from bs4 import BeautifulSoup
import json
import time
import re
import csv
import os
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}


def buscar_en_google(empresa: str, puesto: str = "", pagina: int = 0) -> list:
    """
    Busca perfiles públicos de LinkedIn usando Google scraping (sin API key).
    Devuelve lista de dicts con url, titulo, snippet.
    """
    query = f'site:linkedin.com/in "{empresa}"'
    if puesto:
        query += f' "{puesto}"'

    params = {
        "q": query,
        "start": pagina * 10,
        "hl": "es",
    }

    url = "https://www.google.com/search"
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)

    if resp.status_code != 200:
        print(f"[!] Google devolvió {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    for div in soup.select("div.g"):
        a_tag = div.select_one("a[href]")
        titulo_tag = div.select_one("h3")
        snippet_tag = div.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")

        if not a_tag or not titulo_tag:
            continue

        href = a_tag["href"]
        if "linkedin.com/in/" not in href:
            continue

        resultados.append({
            "url": href,
            "titulo": titulo_tag.get_text(strip=True),
            "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
        })

    return resultados


def parsear_contacto(titulo: str, snippet: str, url: str) -> dict:
    """
    Extrae nombre, puesto, empresa y ubicación del título y snippet de Google.
    Formato típico: "Nombre Apellido - Cargo en Empresa | LinkedIn"
    """
    contacto = {
        "nombre": "",
        "puesto": "",
        "empresa": "",
        "ubicacion": "",
        "linkedin_url": url,
        "email": "",
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # Limpiar título
    titulo_limpio = re.sub(r"\s*\|\s*LinkedIn.*$", "", titulo).strip()
    titulo_limpio = re.sub(r"\s*-\s*LinkedIn.*$", "", titulo_limpio).strip()

    # Separar nombre del resto
    if " - " in titulo_limpio:
        partes = titulo_limpio.split(" - ", 1)
        contacto["nombre"] = partes[0].strip()
        resto = partes[1].strip()

        # Separar puesto de empresa
        for sep in [" en ", " at ", " @ ", " · ", " | "]:
            if sep in resto:
                sub = resto.split(sep, 1)
                contacto["puesto"] = sub[0].strip()
                contacto["empresa"] = sub[1].strip()
                break
        else:
            contacto["puesto"] = resto
    else:
        contacto["nombre"] = titulo_limpio

    # Ubicación desde snippet
    texto_completo = titulo + " " + snippet
    loc_match = re.search(
        r'\b([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?: [A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)*,\s*[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)\b',
        texto_completo
    )
    if loc_match:
        contacto["ubicacion"] = loc_match.group(1)

    # Email si aparece en snippet (raro pero posible)
    email_match = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', snippet)
    if email_match:
        contacto["email"] = email_match.group(0)

    return contacto


def scrape_linkedin(empresa: str, puestos: list = None, paginas: int = 1, delay: float = 3.0) -> list:
    """
    Pipeline principal. Busca contactos de una empresa y devuelve lista de dicts.

    Args:
        empresa:  Nombre de la empresa
        puestos:  Lista de puestos. None = búsqueda general
        paginas:  Cantidad de páginas de Google por búsqueda (10 resultados c/u)
        delay:    Segundos entre requests
    """
    if puestos is None:
        puestos = [""]

    todos = []
    urls_vistas = set()

    for puesto in puestos:
        label = puesto or "(todos los puestos)"
        print(f"\n[*] Buscando: {empresa} / {label}")

        for pagina in range(paginas):
            print(f"    Página {pagina + 1}...")
            resultados = buscar_en_google(empresa, puesto, pagina)

            for r in resultados:
                if r["url"] not in urls_vistas:
                    urls_vistas.add(r["url"])
                    contacto = parsear_contacto(r["titulo"], r["snippet"], r["url"])
                    todos.append(contacto)
                    print(f"    + {contacto['nombre']} — {contacto['puesto']}")

            time.sleep(delay)

    print(f"\n[✓] Total: {len(todos)} contactos únicos encontrados")
    return todos


def guardar_csv(contactos: list, archivo: str = "contactos.csv") -> None:
    if not contactos:
        print("[!] No hay contactos para guardar")
        return

    campos = ["nombre", "puesto", "empresa", "ubicacion", "linkedin_url", "email", "fecha_scraping"]
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(contactos)

    print(f"[✓] Guardado: {archivo} ({len(contactos)} filas)")


def guardar_json(contactos: list, archivo: str = "contactos.json") -> None:
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(contactos, f, ensure_ascii=False, indent=2)
    print(f"[✓] Guardado: {archivo}")


# ── Configuración ──────────────────────────────────────────
if __name__ == "__main__":
    EMPRESA = os.getenv("EMPRESA", "MercadoLibre")
    PUESTOS = os.getenv("PUESTOS", "Data Engineer,Product Manager,Software Engineer").split(",")
    PAGINAS = int(os.getenv("PAGINAS", "1"))
    DELAY   = float(os.getenv("DELAY", "3.0"))

    contactos = scrape_linkedin(
        empresa=EMPRESA,
        puestos=PUESTOS,
        paginas=PAGINAS,
        delay=DELAY,
    )

    guardar_csv(contactos, "contactos.csv")
    guardar_json(contactos, "contactos.json")
