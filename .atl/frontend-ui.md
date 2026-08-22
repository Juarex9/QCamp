# Frontend UI — landing + app

Copia local. Engram auto-detecta este repo como `cosillas` (git_child), así que
la observación quedó mal bindeada; esta es la fuente confiable.

## Rutas

| Ruta | Template | Estado |
|------|----------|--------|
| `/` | `landing.html` | Sin estado (contexto `{}`), no toca la DB |
| `/app` | `app.html` | La herramienta: captura, tabla, totales |

`index.html` se renombró a `app.html`. Los fallbacks HTML de `_respond_form`,
`_respond_saved`, `get_remitos` y `get_resumen` apuntan a `app.html`.

## Sistema de diseño

Brutalismo agro-industrial: ticket de balanza y papel de romaneo.

- Tinta cálida `#0c0c0a`, papel hueso `#f1ebdc`, naranja de señalización `#ff4d17`,
  trigo `#dcc07d` como acento secundario.
- Monoespaciada llevada a escala display; serif solo para prosa editorial.
- **Sin webfonts ni CDN**: la app corre en modo avión. La identidad sale de
  composición, color, escala y textura con stacks locales (DejaVu / Liberation).
- Texturas 100% CSS: grilla dot-matrix, grano vía SVG inline data-URI,
  perforación de ticket con `radial-gradient`.

## Contrato que no se puede romper

Los tests y el JS de `htmx.js` dependen de:

- ids `form-slot`, `list-slot`, `resumen`, `remitos-table-body`, `remito-{id}`
- atributos `hx-post` / `hx-get` / `hx-target` / `hx-swap`
- el literal `ocr_ready=false` / `llm_ready=false` en el banner
- el texto de los botones `Guardar remito` y `Confirmar`
- los `name=` de todos los campos, incluido `photo`

## Decisiones con motivo

**Placeholder de tabla vacía** — `.remito-row ~ .empty-row { display: none }`.
Selector hermano, no `:has()`, porque HTMX prepende filas con `afterbegin` sin
re-renderizar: el placeholder va último y cualquier fila insertada lo oculta.

**Filtro Jinja `kg`** (`_fmt_kg` en `main.py`) — `28740.0` se muestra `28740`.
Un `.0` en un número de 4rem se lee como roto. Tolera `Undefined` de Jinja
además de `TypeError`/`ValueError`, porque el form vacío pasa `{}`.

**La animación de entrada no usa `opacity`** — solo `transform`. Al fadear desde
`opacity: 0` con `animation-delay`, el titular del pitch quedaba invisible hasta
~1.1s: se reproducía de forma intermitente en capturas headless y afectaría
crawlers, imprimir a PDF y cualquier primer paint lento. El contenido crítico no
puede depender de que una animación termine.

**`prefers-reduced-motion` también anula `animation-delay`** — sin eso, con fill
`backwards` los elementos se quedaban en el estado inicial durante el delay,
que es justo lo que el usuario pidió evitar.

**`.workspace` estira a `100vh`** en desktop para que el divisor y el panel de
captura lleguen al fold, y se anula (`min-height: 0`) abajo de 60rem, donde en
una sola columna solo generaría aire muerto.

## Verificación

42 tests pasan, `ruff check` limpio. Render verificado con Firefox headless en
1440px, 414px y varios altos; capturas byte-idénticas entre corridas (sin
carreras de animación).
