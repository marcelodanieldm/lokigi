-- Tabla de créditos de API por usuario/API Key
CREATE TABLE IF NOT EXISTS api_credits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id uuid REFERENCES api_keys(id),
    user_id uuid,
    credits_used int DEFAULT 0,
    credits_limit int DEFAULT 1000,
    period_start timestamptz DEFAULT date_trunc('month', now()),
    period_end timestamptz DEFAULT (date_trunc('month', now()) + interval '1 month'),
    last_billed_at timestamptz,
    created_at timestamptz DEFAULT now()
);

-- Tabla de eventos de facturación por exceso (overage)
CREATE TABLE IF NOT EXISTS api_billing_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id uuid REFERENCES api_keys(id),
    user_id uuid,
    credits_billed int,
    amount numeric,
    currency text DEFAULT 'USD',
    stripe_invoice_id text,
    created_at timestamptz DEFAULT now()
);
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


-- Tabla de API Keys para autenticación pública
CREATE TABLE IF NOT EXISTS api_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid,
    key_hash text NOT NULL,
    label text,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    last_used_at timestamptz,
    usage_count int DEFAULT 0,
    tier text DEFAULT 'tier1',
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Tabla de Webhooks para notificaciones externas
CREATE TABLE IF NOT EXISTS webhooks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid,
    url text NOT NULL,
    event text NOT NULL, -- p.ej. 'audit.completed'
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    last_triggered_at timestamptz,
    CONSTRAINT fk_user_webhook FOREIGN KEY(user_id) REFERENCES users(id)
);
