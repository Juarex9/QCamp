# Pitch — Qcamp

Usuario final: **el productor** (o capataz / contratista con *su* copia del ticket).  
No la balanza. No el acopio.

**Plataforma MVP:** notebook o PC en la camioneta (`127.0.0.1`). App móvil **fuera de alcance** por ahora — el modelo QVAC corre en el mismo equipo que el servidor, no en el celular.

## Quick path (30 segundos)

El acopio ya digitaliza al pesar. El productor se lleva un **papel** y no ve esos kg hasta que hay señal. Qcamp es la libreta del productor en el **notebook del camión**: foto del ticket → kg/patente/fecha en SQLite local, total del día, **sin nube**. Demo en airplane mode en el host.

Demo: airplane mode → upload → fila → `/resumen`.

## Quién es y quién no

| Sí | No |
|----|----|
| Productor del NOA | Software de la balanza urbana |
| Capataz / contratista con la copia | El sistema del ingenio o la cooperativa |
| Acumulado del día (viajes, kg, humedad) | Reemplazar AFIP / carta de porte |
| Notebook / tablet en la camioneta (MVP) | App nativa en el celular (futuro) |

El ticket **nace** en la balanza (a veces con internet). El cuello es la **copia que viaja al campo**: guantera, 15 tickets, recién se cargan a la noche en el pueblo.

## Qué decir / qué no

**Decí:** “para el productor”; “la copia del ticket”; “el total del día”; “on-device en el notebook, los kg no salen del equipo”; “agente 1B + OCR, no un modelo en la nube”; “corre en localhost, modo avión”.

**No digas:** “las balanzas no tienen internet”; “reemplazamos el software de la planta”; “después lo subimos a la nube”; “app en el celular” (todavía no es cierto técnicamente).

## Borrador (iterar)

> En cosecha el productor junta tickets de balanza en la camión. La planta ya tiene el dato; él no. Qcamp corre QVAC en el notebook: subís la foto del ticket, el agente 1B extrae kg y patente con tools (sin inventar: si cambia el kg, no guarda), SQLite local, total del día. Sin API keys, sin que la liquidación salga del equipo. Demo en airplane mode.

## Datos que importan al productor

Del ticket: fecha, patente, **neto kg**, producto, humedad, origen (lote), destino.  
No el remito AFIP (CUIT, Pto. Vta.): eso es oficina.

## Track (una línea cada premio)

- 1° back-office: deja de anotar tickets a mano para saber cuánto salió hoy.
- 2° tool use: extract → save; kg inventado no se persiste.

## Cómo lo ve el jurado

El brief es **async**: video local + repo. No hace falta URL cloud.

- **Video / notebook:** airplane mode → upload → fila → `/resumen`. Eso es el producto.
- **Repo:** permalinks en el [README](../README.md).
- **Render / Vercel:** opcional, maqueta sin QVAC. Ver [deploy.md](deploy.md).

Más contexto: [cobertura.md](cobertura.md) · [modelos.md](modelos.md) · brief: [qvac-track.md](qvac-track.md) · envío: [submit.md](submit.md).
