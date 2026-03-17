from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
from scraper import scrape_linkedin, guardar_csv, guardar_json

app = FastAPI(
    title="LinkedIn Scraper API",
    description="Scraping de perfiles públicos de LinkedIn vía Google",
    version="1.0.0",
)

# Almacenamiento en memoria de los últimos resultados
_ultimo_resultado = []


@app.get("/")
def root():
    return {"status": "ok", "mensaje": "LinkedIn Scraper corriendo en Railway"}


@app.get("/buscar")
def buscar(
    empresa: str = Query(..., description="Empresa a buscar, ej: MercadoLibre"),
    puestos: str = Query("", description="Puestos separados por coma, ej: 'Data Engineer,PM'"),
    paginas: int = Query(1, ge=1, le=3, description="Páginas de Google por búsqueda (máx 3)"),
    delay: float = Query(3.0, ge=2.0, description="Segundos entre requests"),
):
    """
    Busca contactos de una empresa y devuelve JSON con los resultados.
    Los resultados también se guardan en contactos.csv y contactos.json.
    """
    global _ultimo_resultado

    lista_puestos = [p.strip() for p in puestos.split(",") if p.strip()] or None

    contactos = scrape_linkedin(
        empresa=empresa,
        puestos=lista_puestos,
        paginas=paginas,
        delay=delay,
    )

    _ultimo_resultado = contactos
    guardar_csv(contactos)
    guardar_json(contactos)

    return {
        "empresa": empresa,
        "puestos_buscados": lista_puestos or ["(todos)"],
        "total": len(contactos),
        "contactos": contactos,
    }


@app.get("/descargar/csv")
def descargar_csv():
    """Descarga el último resultado como archivo CSV."""
    if not os.path.exists("contactos.csv"):
        return JSONResponse(status_code=404, content={"error": "Todavía no se hizo ninguna búsqueda"})
    return FileResponse("contactos.csv", media_type="text/csv", filename="contactos.csv")


@app.get("/descargar/json")
def descargar_json():
    """Descarga el último resultado como archivo JSON."""
    if not os.path.exists("contactos.json"):
        return JSONResponse(status_code=404, content={"error": "Todavía no se hizo ninguna búsqueda"})
    return FileResponse("contactos.json", media_type="application/json", filename="contactos.json")


@app.get("/ultimo")
def ultimo():
    """Devuelve los últimos resultados en memoria."""
    return {"total": len(_ultimo_resultado), "contactos": _ultimo_resultado}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
