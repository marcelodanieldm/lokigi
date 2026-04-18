-- =============================================================================
-- Starter Plan – Monthly KPI Aggregation Query
-- =============================================================================
-- Purpose : Compute the four key metrics for a given user's active location,
--           grouped by calendar month.  Designed to feed the INSERT … ON
--           CONFLICT upsert that refreshes starter_monthly_metrics daily.
--
-- Parameters (bind variables)
--   :user_id   UUID  – the user whose active location is queried
--
-- Output columns
--   month_start          first day of the calendar month (UTC)
--   year                 INTEGER  e.g. 2026
--   month                INTEGER  1-12
--   location_id          active location at time of query
--   total_reviews        total reviews received in that month
--   avg_rating           average star rating (1-5), rounded to 2 decimals
--   response_rate_pct    % of reviews handled via AUTO_REPLY (0.00 – 100.00)
--   avg_response_time_min avg minutes from review creation → NLP decision
--
-- Notes
--   • Only the single active location linked to :user_id is included.
--     The INNER JOIN on google_connections + WHERE gc.user_id = :user_id
--     guarantees isolation between tenants.
--   • Response Rate counts only AUTO_REPLY actions.  Reviews routed to ALERT
--     (human escalation) are intentionally excluded from the numerator.
--   • avg_response_time_min uses reply_decided_at (NLP engine decision time)
--     as the proxy for "response time" because no column yet tracks the
--     moment the reply was actually posted to Google.  NULL when no decision
--     was recorded in that month.
--   • Reviews with NULL create_time are excluded from the time calculation
--     to avoid skewing the average with incomplete data.
-- =============================================================================

SELECT
    DATE_TRUNC('month', r.create_time)::date          AS month_start,
    EXTRACT(YEAR  FROM r.create_time)::int            AS year,
    EXTRACT(MONTH FROM r.create_time)::int            AS month,
    gc.location_id,

    -- KPI 1 · Total Reviews
    COUNT(*)                                          AS total_reviews,

    -- KPI 2 · Average Rating  (NULL when no reviews have a rating)
    ROUND(AVG(r.rating)::numeric, 2)                  AS avg_rating,

    -- KPI 3 · Response Rate %
    -- Numerator  : reviews where the NLP engine issued an AUTO_REPLY
    -- Denominator: all reviews in the period (regardless of decision)
    ROUND(
        100.0
        * COUNT(*) FILTER (WHERE r.reply_action = 'AUTO_REPLY')
        / NULLIF(COUNT(*), 0),
        2
    )                                                 AS response_rate_pct,

    -- KPI 4 · Average Response Time (minutes)
    -- Only considers rows where both timestamps are present.
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (r.reply_decided_at - r.create_time)) / 60.0
        ) FILTER (
            WHERE r.reply_decided_at IS NOT NULL
              AND r.create_time      IS NOT NULL
        )::numeric,
        2
    )                                                 AS avg_response_time_min

FROM  reviews          r
INNER JOIN google_connections gc
       ON  gc.id = r.connection_id

WHERE gc.user_id  = :user_id          -- tenant isolation: only the active user
  AND r.create_time IS NOT NULL        -- exclude reviews with no timestamp

GROUP BY
    DATE_TRUNC('month', r.create_time),
    gc.location_id

ORDER BY month_start;


-- =============================================================================
-- Upsert pattern – refresh starter_monthly_metrics for one user
-- =============================================================================
-- Run this daily (e.g. via pg_cron or a background job) to keep the
-- pre-aggregated table current.  EXCLUDED refers to the incoming row.
-- =============================================================================

INSERT INTO starter_monthly_metrics (
    id,
    user_id,
    location_id,
    year,
    month,
    total_reviews,
    avg_rating,
    response_rate_pct,
    avg_response_time_minutes,
    computed_at
)
SELECT
    gen_random_uuid()                                      AS id,
    gc.user_id,
    gc.location_id,
    EXTRACT(YEAR  FROM r.create_time)::int                AS year,
    EXTRACT(MONTH FROM r.create_time)::int                AS month,
    COUNT(*)                                              AS total_reviews,
    ROUND(AVG(r.rating)::numeric, 2)                      AS avg_rating,
    ROUND(
        100.0
        * COUNT(*) FILTER (WHERE r.reply_action = 'AUTO_REPLY')
        / NULLIF(COUNT(*), 0),
        2
    )                                                     AS response_rate_pct,
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (r.reply_decided_at - r.create_time)) / 60.0
        ) FILTER (
            WHERE r.reply_decided_at IS NOT NULL
              AND r.create_time      IS NOT NULL
        )::numeric,
        2
    )                                                     AS avg_response_time_minutes,
    NOW()                                                 AS computed_at

FROM  reviews          r
INNER JOIN google_connections gc
       ON  gc.id = r.connection_id

WHERE gc.user_id  = :user_id
  AND r.create_time IS NOT NULL

GROUP BY
    gc.user_id,
    gc.location_id,
    EXTRACT(YEAR  FROM r.create_time),
    EXTRACT(MONTH FROM r.create_time)

ON CONFLICT (user_id, year, month)
DO UPDATE SET
    location_id               = EXCLUDED.location_id,
    total_reviews             = EXCLUDED.total_reviews,
    avg_rating                = EXCLUDED.avg_rating,
    response_rate_pct         = EXCLUDED.response_rate_pct,
    avg_response_time_minutes = EXCLUDED.avg_response_time_minutes,
    computed_at               = EXCLUDED.computed_at;
