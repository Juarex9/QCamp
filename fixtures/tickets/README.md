# Tickets de demo (sintéticos)

Estas tres imágenes **no son remitos reales**. Son PNGs generados para
el happy path (upload → fila → `/resumen`) sin fotografiar papel de campo.

El brief QVAC pide inputs sucios, no un solo cherry-pick. En el video:
usar al menos **un fixture distinto** o, mejor, una foto real de ticket.

| Archivo | Producto | kg | Patente | Origen → destino |
|---------|----------|----|---------|------------------|
| `remito-soja-tucuman.png` | soja | 18500 | AB123CD | Tucumán → Rosario |
| `remito-maiz-salta.png` | maíz | 24200 | AC456DE | Salta → Timbúes |
| `remito-trigo-santiago.png` | trigo | 15800 | AD789FG | Santiago del Estero → San Lorenzo |

Regenerar: `python scripts/gen_synthetic_tickets.py`.
Seed opcional (lista + totales sin subir foto): `python scripts/seed_demo.py`.
