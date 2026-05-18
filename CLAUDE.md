# EconoDaily — AI Agent Instructions

## Principios

### Código limpio
- Una función hace una sola cosa. Si necesita comentario para explicar *qué* hace, renómbrala.
- Máximo 30 líneas por función, 200 LOC por archivo (`main.py` ≤ 80).
- Sin variables globales. Los datos viajan como argumentos y valores de retorno.
- Sin abstracciones prematuras. Tres líneas similares no justifican un helper.
- Sin código muerto: si se elimina algo, se elimina completo.
- Tipos explícitos en todas las firmas públicas (`def fetch_feed(url: str) -> list[NewsItem]`).

### Comandos cortos
- El comando principal del proyecto cabe en una línea: `python src/main.py`
- Los tests corren con: `python -m pytest tests/ -v`
- Instalar dependencias: `pip install -r requirements.txt`
- Sin scripts de build, sin Makefile, sin wrappers innecesarios.

### Mensajes claros
- Los logs usan `logging`, nunca `print`. Nivel correcto: `INFO` para flujo normal, `ERROR` para fallos.
- Formato de log: quién falló + por qué + qué se hará (fallback o exit).
  - Bien: `logger.error("Gemini API timeout for level %s — using raw RSS fallback", level.level)`
  - Mal: `logger.error("Error occurred")`
- Nunca loguear API keys, tokens ni contenido de variables de entorno.
- Los mensajes de commit describen el *por qué*, no el *qué* (el diff ya muestra el qué).

### Dependencias — solo si es necesario
Antes de agregar una dependencia pregunta: ¿la stdlib de Python no alcanza?

Si se necesita una librería externa debe cumplir **los tres criterios**:
1. **Madura** — versión ≥ 1.0, más de 2 años en producción activa.
2. **Mantenida** — commit en los últimos 12 meses, issues atendidos.
3. **Necesaria** — reemplaza al menos 50 líneas de código no trivial.

Dependencias aprobadas para este proyecto:

| Librería | Justificación |
|---|---|
| `feedparser` | Parser RSS/Atom con manejo de edge cases (encodings, fechas, malformed XML) que tomaría cientos de líneas replicar |
| `httpx` | Cliente HTTP async con timeouts configurables; `urllib` no tiene async nativo |
| `jinja2` | Templating HTML con autoescape; f-strings no escalan para plantillas de 200+ líneas |
| `premailer` | Inline CSS para compatibilidad Gmail/Outlook; regla del email HTML no negociable |
| `resend` | SDK oficial de Resend; alternativa sería reimplementar OAuth + retry logic |
| `python-dotenv` | Carga `.env` en desarrollo local; 1 línea de uso vs. parseo manual |
| `bleach` | Sanitización HTML de contenido RSS externo; no usar `html.escape` (pierde estructura legítima) |

---

## Proyecto

EconoDaily es un pipeline Python que corre lunes–viernes vía GitHub Actions:
1. Extrae noticias económicas de RSS (3 niveles: macro / meso / micro)
2. Enriquece resúmenes con Gemini 2.5 Flash (REST API)
3. Renderiza email HTML con Jinja2 + premailer
4. Envía por Resend API a `RECIPIENT_EMAIL`

## Archivos clave

```
src/__init__.py          — dataclasses: NewsItem, NewsLevel, Newsletter
src/main.py              — orquestador (≤80 LOC, sin lógica de negocio)
src/fetch_news.py        — extracción RSS
src/generate_content.py  — enriquecimiento con Gemini
src/render_email.py      — renderizado Jinja2 + CSS inline
src/send_email.py        — envío por Resend
templates/newsletter.html.j2  — plantilla HTML (tabla, no flex/grid)
tests/                   — pytest (32 tests)
.github/workflows/daily_newsletter.yml  — cron 11:00 UTC lun-vie
.ai-memory/              — memoria del agente (leer antes de modificar código)
```

## Variables de entorno

```bash
GEMINI_API_KEY    # Google AI Studio
RESEND_API_KEY    # Resend
RECIPIENT_EMAIL   # destinatario
FROM_EMAIL        # dominio verificado en Resend
FROM_NAME         # nombre del remitente (default: EconoDaily)
LOG_LEVEL         # opcional, default: INFO
```

## Comandos

```bash
cp .env.example .env && python src/main.py   # ejecutar pipeline
python -m pytest tests/ -v                   # correr tests
pip install -r requirements.txt              # instalar dependencias
```

## Protocolo de agente

1. Leer `.ai-memory/HANDOFF.md` antes de tocar código.
2. Revisar `.ai-memory/DECISIONS.md` antes de cambiar arquitectura.
3. Actualizar `HANDOFF.md` al cerrar la sesión.
4. Registrar la sesión en `AI_LOG.md`.
5. Errores que toman >10 min en resolver van a `ERRORS.md`.
