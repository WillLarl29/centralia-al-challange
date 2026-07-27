# CentralIA — Plan de Implementación

Agente de IA corporativo para **Mercado Central 24h**, capaz de responder preguntas de cualquier colaborador (RH, Compras, Finanzas, Legal, Operaciones, Atención al Cliente) usando como única fuente de verdad los documentos internos de la empresa.

> Nombre elegido: **CentralIA** — combina "Central" (de Mercado Central 24h, la marca omnipresente en todos los documentos) con "IA". Es corto, fácil de recordar y no choca con "CentralBot" (el bot de atención a clientes que ya existe *dentro* de la ficción de la empresa, mencionado en el FAQ) — CentralIA es la herramienta *interna* para colaboradores, un producto distinto.

---

## 1. Contexto: qué hay en `documents/`

| Archivo | Dominio | Contenido clave |
|---|---|---|
| `Manual de Proveedores y Política de Compras.pdf` | Compras / Finanzas | Alta de proveedores, clasificación A/B/C, condiciones de pago, KPIs, órdenes de compra, código de ética |
| `POLÍTICA DE ATENCIÓN AL CLIENTE, CAMBIOS Y DEVOLUCIONES.pdf` | Atención al cliente / Legal | Plazos de devolución, PROFECO, programa de lealtad, privacidad (LFPDPPP), accesibilidad |
| `PREGUNTAS FRECUENTES (FAQ).pdf` | Mixto (clientes + empleados) | Bloque A: pagos, delivery, promociones. Bloque B: **RH** (IMSS, Infonavit, aguinaldo, PTU, vacaciones, nómina, ética) |
| `REGLAMENTO INTERNO Y PROCEDIMIENTOS OPERATIVOS.pdf` | Operaciones / Legal / RH | Turnos, checklists de apertura/cierre, PEPS, seguridad alimentaria, prevención de pérdidas, protocolo de emergencias, régimen disciplinario |
| `inventario_de_supermercado_latam.xlsx` | Datos estructurados | SKU, código de barras, categoría, stock actual/mín/máx, lote, fechas de caducidad, costo, precio, proveedor — **~937 registros** |

Esto confirma el objetivo: **múltiples formatos** (PDF ya presentes; Word/PPT/MD/CSV/JSON/HTML deben soportarse aunque hoy no haya ejemplos) y **múltiples dominios organizacionales** en una sola base conversacional.

---

## 2. Arquitectura propuesta

```
                        ┌─────────────────────────┐
                        │   frontendIA (React)    │
                        │  Chat UI + histórico     │
                        └───────────┬─────────────┘
                                    │ HTTPS/REST (SSE streaming)
                        ┌───────────▼─────────────┐
                        │   backendIA (FastAPI)    │
                        │  - Ingesta multi-formato │
                        │  - Orquestación RAG      │
                        │  - Tool: SQL inventario  │
                        └───┬───────────────┬──────┘
                            │               │
            ┌───────────────▼───┐   ┌───────▼─────────────┐
            │ OCI Generative AI  │   │ Oracle Autonomous DB │
            │ (embeddings + LLM) │   │ 23ai — AI Vector      │
            │ Cohere / Llama 3   │   │ Search + tabla        │
            └────────────────────┘   │ estructurada inventario│
                                      └───────────────────────┘
                        ┌─────────────────────────┐
                        │  OCI Object Storage      │
                        │  (documentos originales) │
                        └─────────────────────────┘
              Todo corre en OCI Compute (Always Free) vía Docker Compose
```

**Patrón**: RAG "agéntico" con dos herramientas:
1. **Búsqueda semántica** (vector search) sobre los PDFs/Word/etc. troceados y embebidos.
2. **Consulta estructurada** (SQL/tool-calling) sobre la tabla de inventario, para preguntas cuantitativas exactas ("¿cuánto stock queda de Arroz Blanco?", "¿qué productos vencen esta semana?").

El LLM decide qué herramienta usar según la pregunta (function calling / ReAct).

### Servicios OCI utilizados (cumple "al menos uno", se documentan varios para robustecer el desafío)

| Servicio OCI | Uso | Capa gratuita |
|---|---|---|
| **Oracle Autonomous Database 23ai (AI Vector Search)** | Vector store + tabla relacional de inventario | Always Free |
| **OCI Generative AI Service** | Embeddings (Cohere multilingual) + Chat (Command R+ / Llama 3) | Trial $300 (30 días); fallback abajo |
| **OCI Compute (Ampere A1 / VM.Standard.E2.1.Micro)** | Hosting de backend + frontend vía Docker Compose | Always Free |
| **OCI Object Storage** | Repositorio de los documentos fuente (versión de respaldo) | Always Free (10 GB) |
| **OCI Vault** *(opcional)* | Guardar credenciales/API keys de forma segura | Always Free |

> ⚠️ **Nota de costo**: OCI Generative AI Service no está en la capa Always Free — se usa durante el trial de $300. Para operación continua tras el trial, dejar preparado un *fallback* configurable (ej. modelo local vía Ollama en el mismo Compute, o un proveedor externo con capa gratuita) detrás de la misma interfaz de "LLM provider" en el backend, para no depender de gasto continuo.

---

## 3. Stack tecnológico

### backendIA/
- **Python 3.11 + FastAPI** (API REST + streaming SSE para el chat)
- **LangChain** o **LlamaIndex** para orquestar el pipeline RAG (splitter, retriever, agent/tool-calling)
- Parsers por formato:
  - PDF → `pypdf` / `pdfplumber`
  - Word → `python-docx`
  - Excel/CSV → `pandas` / `openpyxl`
  - PowerPoint → `python-pptx`
  - Markdown → `markdown-it-py` o lectura directa
  - JSON → nativo
  - HTML → `beautifulsoup4`
- `python-oracledb` (driver oficial, thin mode) para hablar con Oracle 23ai Vector Search
- `oci` (SDK Python) para Generative AI Service y Object Storage
- `pydantic` para esquemas de request/response
- `pytest` para pruebas

### frontendIA/
- **React + Vite + TypeScript**
- **TailwindCSS** para estilos rápidos
- Cliente de chat con streaming (fetch + ReadableStream o EventSource)
- Vista simple de "fuentes citadas" (qué documento/página respaldó la respuesta) — importante para confianza del colaborador

### Infraestructura
- `Dockerfile` en cada carpeta + `docker-compose.yml` en la raíz
- **Nginx** (o Caddy, que da HTTPS automático) como reverse proxy delante de frontend/backend
- GitHub Actions (opcional) para build & push de imágenes

---

## 4. Estructura de carpetas propuesta

```
backendIA/
├── app/
│   ├── main.py                 # entrypoint FastAPI
│   ├── api/routes/chat.py      # endpoint /chat
│   ├── api/routes/health.py
│   ├── ingestion/
│   │   ├── loaders/            # un loader por formato (pdf.py, docx.py, xlsx.py, pptx.py, md.py, csv.py, json.py, html.py)
│   │   ├── chunker.py
│   │   └── pipeline.py         # orquesta: cargar → trocear → embeber → guardar en 23ai
│   ├── rag/
│   │   ├── retriever.py        # vector search sobre Oracle 23ai
│   │   ├── sql_tool.py         # consultas estructuradas sobre inventario
│   │   └── agent.py            # decide retriever vs sql_tool, arma el prompt final
│   ├── llm/
│   │   ├── provider.py         # interfaz abstracta LLMProvider
│   │   ├── oci_genai.py        # implementación con OCI Generative AI
│   │   └── local_fallback.py   # implementación alterna (Ollama, etc.)
│   ├── db/
│   │   ├── connection.py
│   │   └── models.py
│   └── core/config.py          # variables de entorno, settings
├── scripts/
│   └── ingest_documents.py     # CLI: procesar todo lo que hay en /documents
├── tests/
├── Dockerfile
├── requirements.txt
└── .env.example

frontendIA/
├── src/
│   ├── components/ChatWindow.tsx
│   ├── components/MessageBubble.tsx
│   ├── components/SourceCitation.tsx
│   ├── hooks/useChatStream.ts
│   ├── App.tsx
│   └── main.tsx
├── Dockerfile
├── package.json
└── vite.config.ts

documents/                       # (ya existe) fuente de verdad
docker-compose.yml
README.md                        # instrucciones + imagen/video del deploy
PLAN_IMPLEMENTACION.md           # este archivo
```

---

## 5. Roadmap de implementación (fases)

### Fase 0 — Preparación (repo y cuenta OCI)
- [ ] Inicializar repositorio git (`git init`) y crear repo **público** en GitHub
- [ ] Crear cuenta OCI (Always Free) si no existe
- [ ] Provisionar Oracle Autonomous Database 23ai (Always Free) con AI Vector Search habilitado
- [ ] Solicitar/activar acceso a OCI Generative AI Service (revisar región disponible, ej. Chicago/Frankfurt)
- [ ] Crear Compute Instance Always Free (Ubuntu, Ampere A1)
- [ ] Crear bucket de Object Storage para respaldo de `documents/`

### Fase 1 — Ingesta multi-formato (backendIA)
- [ ] Implementar loaders por tipo de archivo (empezar por PDF y XLSX, que ya tenemos)
- [ ] Chunking con overlap (ej. 800–1000 tokens, 150 de overlap), conservando metadata (archivo, sección/página)
- [ ] Cargar el Excel de inventario en una **tabla relacional** aparte (no solo como texto) para permitir consultas exactas
- [ ] Generar embeddings (OCI GenAI Cohere multilingual) y guardarlos en columna `VECTOR` de 23ai
- [ ] Script `ingest_documents.py` idempotente (recalcula solo lo que cambió, vía hash del archivo)

### Fase 2 — RAG y orquestación
- [ ] Implementar `retriever.py` (búsqueda semántica top-k + filtro por metadata si aplica)
- [ ] Implementar `sql_tool.py` (consultas parametrizadas seguras sobre inventario — nunca SQL libre generado por el LLM sin sanitizar)
- [ ] Implementar `agent.py`: prompt de sistema que instruye al modelo a citar la fuente, decir "no lo sé" si no hay evidencia en los documentos, y elegir herramienta (RAG vs SQL) según la pregunta
- [ ] Definir prompt de sistema con tono corporativo, aclarando alcance (solo información de Mercado Central 24h)

### Fase 3 — API backend
- [ ] Endpoint `POST /chat` con streaming (SSE) y devolución de fuentes citadas
- [ ] Endpoint `GET /health`
- [ ] Manejo de sesiones/historial de conversación (en memoria o tabla simple en 23ai)
- [ ] Logging estructurado (sin loguear contenido sensible de RH en texto plano)
- [ ] Tests unitarios de loaders, chunker y retriever

### Fase 4 — Frontend
- [ ] UI de chat minimalista (input, historial, indicador de "escribiendo")
- [ ] Mostrar citas de fuente (documento + sección) debajo de cada respuesta
- [ ] Manejo de errores / estado de carga
- [ ] Responsive (uso desde celular en piso de tienda)

### Fase 5 — Empaquetado y despliegue en OCI
- [ ] Dockerfile backend (multi-stage, imagen slim)
- [ ] Dockerfile frontend (build Vite + servir con Nginx)
- [ ] `docker-compose.yml` con backend + frontend + reverse proxy (Caddy/Nginx) + variables de entorno vía `.env`
- [ ] Copiar `.env.example` → `.env` en el servidor con credenciales OCI (DB wallet, GenAI API keys) — considerar OCI Vault
- [ ] Abrir puertos 80/443 en el Security List / NSG de la instancia
- [ ] `docker compose up -d` en la VM, verificar accesible por IP pública (y opcionalmente dominio + HTTPS con Caddy/Let's Encrypt)
- [ ] Ejecutar `ingest_documents.py` contra la base ya en producción

### Fase 6 — Evidencia y entrega del desafío
- [ ] Grabar video corto (o capturar imagen) del agente respondiendo preguntas, corriendo en la URL pública de OCI
- [ ] Insertar esa imagen/video en el `README.md`
- [ ] Documentar en el README: arquitectura, cómo correr localmente, cómo desplegar, qué servicios OCI se usaron y por qué
- [ ] Revisar que el repo sea público y no contenga secretos (`.env` en `.gitignore`)

---

## 6. Consideraciones de seguridad y buenas prácticas
- Nunca commitear credenciales de Oracle DB / OCI GenAI — usar `.env` + `.gitignore`, y opcionalmente OCI Vault en producción.
- El "tool" de SQL sobre inventario debe usar **queries parametrizadas predefinidas** (no ejecutar SQL arbitrario generado por el modelo) para evitar inyección.
- Aunque el reglamento interno tiene contenido sensible (sanciones, ética, línea de denuncias), es contenido *de política*, no datos personales de individuos reales — igual, si en el futuro se cargan documentos con PII real de colaboradores, evaluar control de acceso por rol antes de indexarlos.
- Rate limiting básico en el endpoint `/chat` para evitar abuso de la cuota de OCI Generative AI.

---

## 7. Próximos pasos inmediatos
1. Confirmar (o ajustar) el nombre **CentralIA** y esta arquitectura.
2. Decidir gestor de dependencias/orquestación (LangChain vs LlamaIndex vs implementación manual liviana).
3. Empezar por **Fase 0 + Fase 1** (repo, cuenta OCI, loaders de PDF/XLSX) ya que son la base de todo lo demás.
