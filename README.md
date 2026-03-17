# LinkedIn Scraper — Deploy en Railway

Scraping de perfiles públicos de LinkedIn vía Google Search.
Sin API keys. Sin dependencias externas pagas.

## Archivos

```
linkedin-scraper/
├── scraper.py       # Lógica de scraping y parsing
├── main.py          # API con FastAPI
├── requirements.txt
├── Procfile
└── README.md
```

## Cómo deployar en Railway

### 1. Subir a GitHub
```bash
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/TU_USUARIO/linkedin-scraper.git
git push -u origin main
```

### 2. Conectar en Railway
1. Entrá a [railway.app](https://railway.app) y creá una cuenta
2. *New Project* → *Deploy from GitHub repo*
3. Seleccioná tu repositorio
4. Railway detecta el `Procfile` automáticamente y hace el deploy

### 3. Variables de entorno (opcional)
En Railway → tu proyecto → *Variables*, podés setear:
- `EMPRESA` — empresa por defecto (ej: `MercadoLibre`)
- `PUESTOS` — puestos separados por coma
- `PAGINAS` — páginas de Google (default: 1)
- `DELAY` — segundos entre requests (default: 3.0)

## Endpoints disponibles

| Endpoint | Descripción |
|---|---|
| `GET /` | Health check |
| `GET /buscar?empresa=X&puestos=Y,Z` | Ejecuta búsqueda |
| `GET /descargar/csv` | Descarga último resultado en CSV |
| `GET /descargar/json` | Descarga último resultado en JSON |
| `GET /ultimo` | Ver últimos resultados en memoria |

## Ejemplo de uso

```
https://tu-app.railway.app/buscar?empresa=MercadoLibre&puestos=Data%20Engineer,Product%20Manager&paginas=1
```

## Correr localmente

```bash
pip install -r requirements.txt
python main.py
# o directamente sin API:
python scraper.py
```

## Limitaciones

- Google puede bloquear requests si se hacen muy rápido (usá delay >= 3.0)
- LinkedIn requiere login para ver la mayoría de los perfiles completos
- Los datos disponibles sin login son: nombre, puesto, empresa, ubicación (desde snippets de Google)
- Emails aparecen raramente en perfiles públicos
