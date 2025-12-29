-- Tabla de puntos de visibilidad para el heatmap del dashboard premium
CREATE TABLE IF NOT EXISTS visibility_points (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lat double precision NOT NULL,
    lon double precision NOT NULL,
    dominance text CHECK (dominance IN ('client', 'competitor')) NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Tabla para el ROI Tracker (dinero protegido este mes)
CREATE TABLE IF NOT EXISTS roi_tracker (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    amount numeric NOT NULL,
    currency text NOT NULL,
    month int NOT NULL,
    year int NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_visibility_points_dominance ON visibility_points(dominance);
CREATE INDEX IF NOT EXISTS idx_roi_tracker_month_year ON roi_tracker(month, year);

-- Tabla de órdenes para almacenar reportes PDF generados
CREATE TABLE IF NOT EXISTS orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email text NOT NULL,
    business_id uuid,
    report_url text,
    lang text DEFAULT 'es',
    created_at timestamptz DEFAULT now()
);

-- Bucket público para reportes PDF
-- (Crear desde Supabase Storage UI: bucket 'reports', público)
