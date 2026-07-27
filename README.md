# CentralIA — Agente de IA Corporativo de Mercado Central 24h

CentralIA es un agente de inteligencia artificial corporativo, accesible para todos los colaboradores, capaz de responder preguntas con base en los documentos internos de **Mercado Central 24h** (RH, Compras/Finanzas, Legal, Atención al Cliente y Operaciones). Funciona como una base de conocimiento conversacional, centralizada y siempre disponible.

> 📄 Ver [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md) para el detalle completo de arquitectura y roadmap.

## Evidencia de despliegue en la nube (OCI)

> 🚧 **Pendiente**: aquí se insertará la imagen/video del agente corriendo en OCI, según el requisito del desafío. Ver la sección [Despliegue en OCI](#despliegue-en-oci) más abajo para los pasos pendientes de ejecutar en tu cuenta de OCI.

<!-- ![CentralIA corriendo en OCI](docs/evidencia-oci.png) -->

## ¿Qué hace?

- Ingresa documentos en **múltiples formatos** (PDF, Word, Excel, PowerPoint, Markdown, CSV, JSON, HTML) y los convierte en una base de conocimiento consultable.
- Combina **búsqueda semántica (RAG)** sobre el texto de las políticas con **consultas estructuradas exactas** sobre el inventario (stock, caducidad, proveedor).
- Cita siempre la fuente (documento y página/fila) de cada respuesta.
- Corre localmente sin ninguna credencial de nube (modo `local`), y se conecta a **Oracle Autonomous Database 23ai (AI Vector Search)** + **OCI Generative AI** en producción.

## Arquitectura

```
frontendIA (React + Vite + Tailwind)  →  backendIA (FastAPI)  →  OCI Generative AI (embeddings + chat)
                                                              →  Oracle Autonomous DB 23ai (AI Vector Search)
                                                              →  SQLite/inventario (consultas exactas de stock)
```

Detalle completo en [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md).

## Estructura del repositorio

```
backendIA/      API FastAPI: ingesta multi-formato, RAG, tool de inventario, endpoint /chat
frontendIA/     Chat UI en React + Vite + TailwindCSS
documents/      Documentos internos fuente (la base de conocimiento)
docker-compose.yml   Levanta backend + frontend juntos
PLAN_IMPLEMENTACION.md   Plan de arquitectura y roadmap detallado
```

---

## Cómo correr localmente (sin Docker)

### Backend

```bash
cd backendIA
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
cp .env.example .env

# Ingesta inicial: procesa todo lo que hay en documents/
python -m scripts.ingest_documents

# Levantar la API
uvicorn app.main:app --reload --port 8000
```

Por defecto corre en **modo local** (`EMBEDDINGS_PROVIDER=local`, `LLM_PROVIDER=local`, `VECTORSTORE_PROVIDER=local`): usa embeddings por hashing y un fallback extractivo (sin LLM real) para que todo el pipeline sea probable sin ninguna credencial de nube. Para respuestas conversacionales completas y con mejor calidad semántica, configura las variables `OCI_*` en `.env` y cambia los tres providers a `oci` / `oracle23ai` (ver `.env.example`).

Probar:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cuál es el plazo de devolución de productos perecederos?"}'
```

### Frontend

```bash
cd frontendIA
pnpm install
cp .env.example .env
pnpm dev
```

Abre `http://localhost:5173`.

---

## Cómo correr con Docker Compose (recomendado)

```bash
cp backendIA/.env.example backendIA/.env
docker compose build
docker compose up -d
docker compose exec backend python -m scripts.ingest_documents
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:80`

---

## Despliegue en OCI

Estos pasos requieren tu propia cuenta de Oracle Cloud Infrastructure (Always Free es suficiente para casi todo):

1. **Oracle Autonomous Database 23ai (Always Free)**: crear una instancia con AI Vector Search habilitado, descargar el wallet de conexión y completar `ORACLE_DB_*` en `backendIA/.env`. Cambiar `VECTORSTORE_PROVIDER=oracle23ai`.
2. **OCI Generative AI Service**: habilitar el servicio en una región soportada (p. ej. Chicago o Frankfurt), crear un compartment, y completar `OCI_*` en `.env`. Cambiar `EMBEDDINGS_PROVIDER=oci` y `LLM_PROVIDER=oci`.
3. **OCI Object Storage** *(opcional)*: subir `documents/` como respaldo de la fuente de verdad.
4. **OCI Compute (Always Free, Ampere A1)**: crear una instancia Ubuntu, instalar Docker + Docker Compose, clonar este repositorio, copiar `.env` con las credenciales anteriores, y ejecutar:
   ```bash
   docker compose up -d
   docker compose exec backend python -m scripts.ingest_documents
   ```
5. Abrir los puertos 80/443 (y 8000 si se expone la API directamente) en el Security List / NSG de la instancia.
6. *(Opcional)* Configurar un dominio + HTTPS (Caddy o Nginx + Let's Encrypt) delante de la instancia.
7. Tomar la captura/video de la app funcionando en la URL pública de OCI y reemplazar el placeholder de la sección "Evidencia de despliegue" arriba.

---

## Requisitos del desafío

- [x] Proyecto en repositorio público de GitHub
- [ ] Despliegue en Oracle Cloud Infrastructure (OCI), usando al menos un servicio de OCI
- [ ] Imagen o video del agente corriendo en la nube, insertado en este README
