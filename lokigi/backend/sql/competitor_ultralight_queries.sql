-- Ultra-light competitor benchmarking queries
-- Tables: competitor, scrape_run, competitor_snapshot, service_catalog, competitor_service_map

-- 1) Evolucion de precio promedio por zona (ultimo mes)
SELECT
  c.zone_code,
  cs.observed_on,
  AVG(
    CASE cs.price_bucket
      WHEN 'budget' THEN 1
      WHEN 'mid' THEN 2
      WHEN 'premium' THEN 3
      WHEN 'luxury' THEN 4
      ELSE NULL
    END
  ) AS avg_price_index
FROM competitor_snapshot cs
JOIN competitor c ON c.id = cs.competitor_id
WHERE cs.observed_on >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.zone_code, cs.observed_on
ORDER BY cs.observed_on DESC, c.zone_code;

-- 2) Relacion rating vs precio por competidor
SELECT
  c.id AS competitor_id,
  c.name_short,
  AVG(cs.rating_x100) / 100.0 AS avg_rating,
  AVG(
    CASE cs.price_bucket
      WHEN 'budget' THEN 1
      WHEN 'mid' THEN 2
      WHEN 'premium' THEN 3
      WHEN 'luxury' THEN 4
      ELSE NULL
    END
  ) AS avg_price_index
FROM competitor_snapshot cs
JOIN competitor c ON c.id = cs.competitor_id
GROUP BY c.id, c.name_short
ORDER BY avg_rating DESC NULLS LAST;

-- 3) Cobertura de servicios por competidor (ultimo snapshot por competidor)
WITH latest_snapshot AS (
  SELECT DISTINCT ON (cs.competitor_id)
    cs.id,
    cs.competitor_id,
    cs.observed_on
  FROM competitor_snapshot cs
  ORDER BY cs.competitor_id, cs.observed_on DESC, cs.created_at DESC
)
SELECT
  c.id AS competitor_id,
  c.name_short,
  COUNT(csm.service_id) AS total_services
FROM latest_snapshot ls
JOIN competitor c ON c.id = ls.competitor_id
LEFT JOIN competitor_service_map csm ON csm.snapshot_id = ls.id
GROUP BY c.id, c.name_short
ORDER BY total_services DESC;

-- 4) Competidor con mayor crecimiento de reseñas (7d)
WITH latest AS (
  SELECT
    cs.competitor_id,
    cs.observed_on,
    cs.total_reviews,
    ROW_NUMBER() OVER (PARTITION BY cs.competitor_id ORDER BY cs.observed_on DESC) AS rn
  FROM competitor_snapshot cs
),
joined AS (
  SELECT
    l1.competitor_id,
    l1.total_reviews AS latest_reviews,
    l2.total_reviews AS prev_reviews
  FROM latest l1
  LEFT JOIN latest l2 ON l2.competitor_id = l1.competitor_id AND l2.rn = l1.rn + 1
  WHERE l1.rn = 1
)
SELECT
  c.id AS competitor_id,
  c.name_short,
  COALESCE(j.latest_reviews, 0) - COALESCE(j.prev_reviews, 0) AS review_growth
FROM joined j
JOIN competitor c ON c.id = j.competitor_id
ORDER BY review_growth DESC;

-- 5) Gaps de servicios frente al lider de cobertura
WITH latest_snapshot AS (
  SELECT DISTINCT ON (cs.competitor_id)
    cs.id,
    cs.competitor_id,
    cs.observed_on
  FROM competitor_snapshot cs
  ORDER BY cs.competitor_id, cs.observed_on DESC, cs.created_at DESC
),
service_counts AS (
  SELECT
    ls.competitor_id,
    COUNT(csm.service_id) AS svc_count
  FROM latest_snapshot ls
  LEFT JOIN competitor_service_map csm ON csm.snapshot_id = ls.id
  GROUP BY ls.competitor_id
),
leader AS (
  SELECT competitor_id, svc_count
  FROM service_counts
  ORDER BY svc_count DESC
  LIMIT 1
)
SELECT
  c.id AS competitor_id,
  c.name_short,
  sc.svc_count,
  l.svc_count AS leader_services,
  (l.svc_count - sc.svc_count) AS service_gap
FROM service_counts sc
JOIN competitor c ON c.id = sc.competitor_id
CROSS JOIN leader l
ORDER BY service_gap ASC;
