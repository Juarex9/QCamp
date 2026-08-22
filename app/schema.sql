CREATE TABLE IF NOT EXISTS remitos (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL,
  fecha TEXT,
  patente TEXT,
  tonelaje_kg REAL,
  origen TEXT,
  destino TEXT,
  producto TEXT,
  humedad REAL,
  raw_ocr TEXT,
  image_path TEXT,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_remitos_fecha ON remitos(fecha);
CREATE INDEX IF NOT EXISTS idx_remitos_producto ON remitos(producto);
