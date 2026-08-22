# Backend — auditoría y fixes (2026-08-22)

Copia local (Engram bindea este repo como `cosillas`; ver frontend-ui.md).

## Bugs corregidos

**Edit parcial borraba campos (data loss).** `update_remito` hacía full-replace:
un POST JSON con solo `tonelaje_kg` dejaba fecha/patente/producto en NULL y el
remito desaparecía del total del día. Ahora `_read_fields` devuelve el set
`provided` (claves realmente enviadas) y `update_remito(provided=...)` mergea:
campo ausente → conserva; campo enviado vacío → borra (así vaciar "destino" en
el form sigue funcionando). `raw_ocr` nunca se pisa; `image_path`/`confidence`
solo se actualizan si vienen con valor. Sin `provided` → full-replace (llamadas
directas con RemitoIn completo).

**`extract_remito` no parseaba texto de ticket** (solo JSON). Ahora tiene parser
determinista por regex en `tools.py`: etiquetas de fixtures (`TONELAJE:`) y de
balanza real (`NETO`/`PESO NETO`), patente Mercosur y vieja, fechas ISO y
dd/mm/yyyy → ISO, `HUMEDAD`, `PRODUCTO/ORIGEN/DESTINO` con lookahead de labels,
y cultivos por keyword. Números localizados: separador + 3 dígitos = miles
(`28.740` → 28740), coma decimal (`13,4` → 13.4). Regla anti-corrupción: varios
`<n> kg` sin etiqueta NETO → devuelve None, no adivina entre bruto/tara/neto.

**Precedencia en `extract_handler` invertida**: el parser gana; los args del
LLM solo rellenan campos que el texto no dio. Consecuencia: el kg persistido
sale del regex cuando el ticket lo trae, y el guard de `run_document_agent`
ahora compara al modelo contra el ticket, no contra sí mismo. Esto refuerza el
argumento del 2° premio del track.

**Humedad basura → 422** (antes 200 con None silencioso). `_parse_humedad` en
`main.py` acepta coma decimal ("13,4") porque es lo que teclea el usuario.

**Logging**: `qcamp.web` y `qcamp.qvac`; `basicConfig` en lifespan
(no-op bajo uvicorn/pytest). Los 8 `except Exception` dejan rastro: connect y
load_model → `logger.exception`; el fallback de `post_remitos` a form manual →
`logger.exception` (antes demo muerta = debugging a ciegas); unload/close en
shutdown → debug.

## Pendiente (decisión de producto)

- Duplicados: mismo ticket cargado 2 veces duplica el total sin aviso.
  Opciones: bloquear / avisar y confirmar / permitir. **A debatir.**
- DELETE /remitos/{id} no existe (no se puede sacar un escaneo malo del total).
- Refactor de `post_remitos` (115 líneas) — sin cambio de comportamiento.
- Conexión SQLite compartida entre threads sin lock/busy_timeout.

## Estado

51 tests (9 nuevos), `ruff check` limpio. Drift de formato preexistente en
líneas no tocadas (get_remito, _invents_locked_fields, _page_ctx) — no churneado.
