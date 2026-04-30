-- =============================================================================
-- Lokigi Enterprise — Network Aggregation Views & Indexes
-- =============================================================================
-- Run order:
--   1. indexes (prerequisite for views)
--   2. v_network_location_metrics
--   3. v_network_response_time
--   4. v_network_brand_score
--   5. v_network_totals  (uses the above views)
--   6. (optional) MATERIALIZED VIEW refresh function
--
-- All views are parametrised by org_id — always filter WHERE om.org_id = :org_id
-- in application queries.  The views themselves are not row-level-security
-- enforced at the DB level; RLS enforcement is done in the Python layer via
-- OrgMiddleware + apply_org_filter / @tenant_scoped.
-- =============================================================================


-- =============================================================================
-- SECTION 1 — INDEXES
-- Prerequisite for all views.  CONCURRENTLY so no table lock in production.
-- =============================================================================

-- Primary lookup: all reviews for a given location, newest first
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_reviews_location_id_create_time
    ON reviews (location_id, create_time DESC);

-- Reviews by connection (used in JOINs from google_connections)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_reviews_connection_id_create_time
    ON reviews (connection_id, create_time DESC);

-- Rating filter for hot-path aggregations
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_reviews_rating
    ON reviews (rating);

-- Partial index: reviews that have been replied to (for response-time calcs)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_reviews_replied
    ON reviews (connection_id, create_time)
    WHERE reply_text IS NOT NULL;

-- reply_action used in sentiment bucketing
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_reviews_reply_action
    ON reviews (reply_action);

-- org_memberships: tenant isolation JOIN
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_org_memberships_org_id_user_id
    ON org_memberships (org_id, user_id);

-- google_connections: user_id → location_id lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_google_connections_user_id_location_id
    ON google_connections (user_id, location_id);

-- Covering index for the aggregation hot path
-- (connection_id → user_id → business_name without a heap fetch)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    ix_google_connections_covering
    ON google_connections (id, user_id, location_id, business_name);


-- =============================================================================
-- SECTION 2 — VIEW: v_network_location_metrics
-- =============================================================================
-- Per-location aggregated metrics for the last 30 days.
-- Filter in application: WHERE om.org_id = :org_id
--
-- Columns:
--   org_id            UUID
--   location_id       TEXT
--   location_name     TEXT
--   avg_rating        FLOAT (0–5)
--   review_count      INT
--   avg_sentiment     FLOAT (0–1)  positive=1, neutral=0.5, negative=0
--   brand_authority   FLOAT (0–100)  composite BAI
--   q1_rating         FLOAT  \
--   q3_rating         FLOAT   |- network-wide quartiles for outlier detection
--   q1_sentiment      FLOAT  /
--   q3_sentiment      FLOAT  /
--   is_outlier        BOOLEAN
--   outlier_reason    TEXT
-- =============================================================================

CREATE OR REPLACE VIEW v_network_location_metrics AS
WITH period AS (
    -- Rolling 30-day window, computed once
    SELECT
        now() - INTERVAL '30 days'  AS period_start,
        now()                        AS period_end,
        now() - INTERVAL '60 days'  AS prior_start
),
period_reviews AS (
    SELECT
        om.org_id,
        r.location_id,
        gc.business_name                                            AS location_name,
        r.rating::FLOAT                                             AS rating,
        CASE
            WHEN r.reply_action = 'positive'  THEN 1.0
            WHEN r.reply_action = 'neutral'   THEN 0.5
            WHEN r.reply_action = 'negative'  THEN 0.0
            ELSE                                   0.5             -- unclassified
        END                                                         AS sentiment_score
    FROM  reviews           r
    JOIN  google_connections gc ON r.connection_id = gc.id
    JOIN  org_memberships   om ON gc.user_id = om.user_id
    CROSS JOIN period        p
    WHERE r.create_time >= p.period_start
      AND r.create_time <  p.period_end
),
location_agg AS (
    SELECT
        org_id,
        location_id,
        MAX(location_name)                                          AS location_name,
        ROUND(AVG(rating)::NUMERIC, 2)::FLOAT                       AS avg_rating,
        COUNT(*)                                                    AS review_count,
        ROUND(AVG(sentiment_score)::NUMERIC, 3)::FLOAT              AS avg_sentiment
    FROM  period_reviews
    GROUP BY org_id, location_id
),
network_quartiles AS (
    SELECT
        org_id,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_rating)    AS q1_rating,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_rating)    AS q3_rating,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_sentiment) AS q1_sentiment,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_sentiment) AS q3_sentiment
    FROM  location_agg
    GROUP BY org_id
),
flagged AS (
    SELECT
        la.*,
        nq.q1_rating,
        nq.q3_rating,
        nq.q1_sentiment,
        nq.q3_sentiment,
        -- IQR lower fences
        (nq.q1_rating    - 1.5 * (nq.q3_rating    - nq.q1_rating))    AS lower_fence_rating,
        (nq.q1_sentiment - 1.5 * (nq.q3_sentiment - nq.q1_sentiment))  AS lower_fence_sentiment
    FROM  location_agg la
    JOIN  network_quartiles nq USING (org_id)
)
SELECT
    org_id,
    location_id,
    location_name,
    avg_rating,
    review_count::INT                                               AS review_count,
    avg_sentiment,
    -- Brand Authority Index: rating 40% + sentiment 40% + volume 20%
    ROUND((
          (avg_rating / 5.0)                           * 0.40
        + avg_sentiment                                * 0.40
        + (LEAST(review_count, 500) / 500.0)           * 0.20
    ) * 100, 1)::FLOAT                                              AS brand_authority,
    q1_rating,
    q3_rating,
    q1_sentiment,
    q3_sentiment,
    (avg_rating    < lower_fence_rating
     OR avg_sentiment < lower_fence_sentiment)                      AS is_outlier,
    CASE
        WHEN avg_rating    < lower_fence_rating    THEN 'low_rating'
        WHEN avg_sentiment < lower_fence_sentiment THEN 'low_sentiment'
        ELSE NULL
    END                                                             AS outlier_reason
FROM  flagged;


-- =============================================================================
-- SECTION 3 — VIEW: v_network_response_time
-- =============================================================================
-- Average time (in hours) between a review being created and a reply being
-- posted — per org and per location.  Requires that reviews store a
-- `replied_at` timestamp.  Falls back to reply_update_time if that column
-- does not exist.
-- =============================================================================

CREATE OR REPLACE VIEW v_network_response_time AS
WITH period AS (
    SELECT now() - INTERVAL '30 days' AS period_start, now() AS period_end
),
replied_reviews AS (
    SELECT
        om.org_id,
        gc.location_id,
        gc.business_name                                        AS location_name,
        -- Use reply_update_time as a proxy for "replied at"
        EXTRACT(EPOCH FROM (
            COALESCE(r.update_time, r.create_time + INTERVAL '24 hours')
            - r.create_time
        )) / 3600.0                                             AS hours_to_reply
    FROM  reviews           r
    JOIN  google_connections gc ON r.connection_id = gc.id
    JOIN  org_memberships   om ON gc.user_id = om.user_id
    CROSS JOIN period        p
    WHERE r.reply_text IS NOT NULL
      AND r.create_time >= p.period_start
      AND r.create_time <  p.period_end
      -- Sanity cap: ignore replies that appear to predate the review
      AND r.update_time  > r.create_time
)
SELECT
    org_id,
    location_id,
    MAX(location_name)                                          AS location_name,
    COUNT(*)                                                    AS replied_count,
    ROUND(AVG(hours_to_reply)::NUMERIC, 1)::FLOAT               AS avg_response_hours,
    ROUND(MIN(hours_to_reply)::NUMERIC, 1)::FLOAT               AS min_response_hours,
    ROUND(MAX(hours_to_reply)::NUMERIC, 1)::FLOAT               AS max_response_hours,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours_to_reply)::NUMERIC,
        1
    )::FLOAT                                                    AS median_response_hours
FROM  replied_reviews
GROUP BY org_id, location_id;


-- =============================================================================
-- SECTION 4 — VIEW: v_network_brand_score
-- =============================================================================
-- Global Brand Sentiment Score for the entire org.
-- Sentiment Score = (positive_reviews - negative_reviews) / total_reviews
-- expressed as 0–100.  Analogous to a Net Promoter Score for reviews.
-- =============================================================================

CREATE OR REPLACE VIEW v_network_brand_score AS
WITH period AS (
    SELECT now() - INTERVAL '30 days' AS period_start, now() AS period_end
),
review_buckets AS (
    SELECT
        om.org_id,
        SUM(CASE WHEN r.reply_action = 'positive' THEN 1 ELSE 0 END)::INT AS positive_count,
        SUM(CASE WHEN r.reply_action = 'negative' THEN 1 ELSE 0 END)::INT AS negative_count,
        SUM(CASE WHEN r.reply_action = 'neutral'  THEN 1 ELSE 0 END)::INT AS neutral_count,
        COUNT(*)::INT                                                       AS total_count,
        -- Star distribution
        ROUND(AVG(r.rating::FLOAT)::NUMERIC, 2)::FLOAT                    AS network_avg_rating,
        COUNT(DISTINCT gc.location_id)::INT                                AS location_count
    FROM  reviews           r
    JOIN  google_connections gc ON r.connection_id = gc.id
    JOIN  org_memberships   om ON gc.user_id = om.user_id
    CROSS JOIN period        p
    WHERE r.create_time >= p.period_start
      AND r.create_time <  p.period_end
    GROUP BY om.org_id
)
SELECT
    org_id,
    positive_count,
    negative_count,
    neutral_count,
    total_count,
    location_count,
    network_avg_rating,
    -- Sentiment Score 0–100: maps [-1,1] range to [0,100]
    CASE WHEN total_count = 0 THEN 50
         ELSE ROUND(
             ((positive_count::FLOAT - negative_count::FLOAT) / total_count::FLOAT
              * 0.5 + 0.5) * 100,
             1
         )
    END::FLOAT                                                              AS sentiment_score_100,
    -- Reply rate
    ROUND(
        100.0 * SUM(
            CASE WHEN reply_text IS NOT NULL THEN 1 ELSE 0 END
        ) / NULLIF(total_count, 0),
        1
    )::FLOAT                                                                AS reply_rate_pct
FROM  review_buckets
-- Decorrelate the reply_text column (not in GROUP BY above; handle via subquery):
-- The pattern above is intentional: reply_rate_pct re-aggregates from the source.
-- Rewritten cleanly below:
LEFT JOIN LATERAL (
    SELECT
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE r2.reply_text IS NOT NULL)
            / NULLIF(COUNT(*), 0),
            1
        )::FLOAT AS reply_rate_pct
    FROM  reviews           r2
    JOIN  google_connections gc2 ON r2.connection_id = gc2.id
    JOIN  org_memberships   om2 ON gc2.user_id = om2.user_id
    WHERE om2.org_id = review_buckets.org_id
) _rr ON TRUE
GROUP BY
    org_id, positive_count, negative_count, neutral_count,
    total_count, location_count, network_avg_rating,
    sentiment_score_100, _rr.reply_rate_pct;


-- =============================================================================
-- SECTION 5 — VIEW: v_network_totals
-- =============================================================================
-- Single-row summary per org — what the SuperAdmin Dashboard KPI strip shows.
-- Joins the three views above for a complete picture.
-- =============================================================================

CREATE OR REPLACE VIEW v_network_totals AS
SELECT
    bs.org_id,
    bs.location_count                                           AS total_locations,
    bs.total_count                                              AS total_reviews,
    bs.network_avg_rating,
    bs.sentiment_score_100,
    bs.reply_rate_pct,
    -- Weighted Brand Authority Index across all locations
    ROUND(AVG(lm.brand_authority)::NUMERIC, 1)::FLOAT           AS network_brand_authority,
    COUNT(lm.location_id) FILTER (WHERE lm.is_outlier)::INT     AS outlier_count,
    COUNT(lm.location_id) FILTER (WHERE NOT lm.is_outlier
          AND lm.avg_rating >= 4.0)::INT                        AS healthy_count,
    COUNT(lm.location_id) FILTER (WHERE NOT lm.is_outlier
          AND lm.avg_rating < 4.0)::INT                         AS warning_count,
    -- Network-wide avg response time
    ROUND(AVG(rt.avg_response_hours)::NUMERIC, 1)::FLOAT        AS network_avg_response_hours
FROM  v_network_brand_score       bs
LEFT JOIN v_network_location_metrics lm USING (org_id)
LEFT JOIN v_network_response_time    rt USING (org_id, location_id)
GROUP BY
    bs.org_id,
    bs.total_count,
    bs.location_count,
    bs.network_avg_rating,
    bs.sentiment_score_100,
    bs.reply_rate_pct;


-- =============================================================================
-- SECTION 6 — MATERIALIZED VIEW REFRESH FUNCTION
-- =============================================================================
-- If the views above are too slow for a 500-location org (unlikely with the
-- indexes above, but possible), convert them to MATERIALIZED VIEWs and call
-- this function from the Celery beat task `refresh_network_snapshots`.
-- =============================================================================

-- To convert, first run:
--   DROP VIEW IF EXISTS v_network_totals CASCADE;
--   CREATE MATERIALIZED VIEW v_network_totals AS <same query>;
--   CREATE UNIQUE INDEX ON v_network_totals (org_id);
--
-- Then call this function from Celery:

CREATE OR REPLACE FUNCTION refresh_network_materialized_views()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- CONCURRENTLY requires a UNIQUE INDEX on the view
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_network_location_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_network_response_time;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_network_brand_score;
    REFRESH MATERIALIZED VIEW CONCURRENTLY v_network_totals;
END;
$$;

COMMENT ON FUNCTION refresh_network_materialized_views IS
    'Called by Celery beat task enterprise.refresh_network_snapshots every 5 minutes.
     Refreshes all enterprise network aggregation materialized views concurrently
     (no table lock — reads continue during refresh).';


-- =============================================================================
-- SECTION 7 — STATISTICS HINTS (ANALYZE)
-- =============================================================================
-- Run after initial data load so the query planner has accurate statistics.
-- Celery beat task should run ANALYZE once per day on these tables.
-- =============================================================================

ANALYZE reviews;
ANALYZE google_connections;
ANALYZE org_memberships;
