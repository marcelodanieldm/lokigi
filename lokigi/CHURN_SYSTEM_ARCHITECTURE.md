# Arquitectura del Sistema de Churn - Diagrama Visual

## 📊 Flujo General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    USUARIO CANCELA SUSCRIPCIÓN                          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              🎨 FRONTEND: /starter/churn-survey                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Radio Buttons: 9 churn reasons                                  │   │
│  │ Slider: Satisfaction Score (1-5)                                │   │
│  │ TextArea: Free Feedback                                         │   │
│  │ Checkbox: Would return with discount?                           │   │
│  │ [Submit Feedback Button] ──────────────────────────────────────→│   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────────────┐
    │  POST /api/churn/survey                                    │
    │  (backend/app/main.py)                                     │
    └────────┬─────────────────────────────────────────┬─────────┘
             │                                         │
             ▼                                         ▼
    ┌──────────────────┐                   ┌──────────────────┐
    │ 1️⃣ SAVE SURVEY    │                   │ 2️⃣ CAPTURE METRICS│
    │ ChurnSurvey      │                   │ ChurnTelemetry   │
    │ ┌──────────────┐ │                   │ ┌──────────────┐ │
    │ │ reason       │ │                   │ │active_days   │ │
    │ │satisfaction  │ │                   │ │approval_rate │ │
    │ │feedback      │ │                   │ │tone_selector │ │
    │ │price_willing │ │                   │ │responses_appr│ │
    │ └──────────────┘ │                   │ └──────────────┘ │
    └────────┬─────────┘                   └────────┬─────────┘
             │                                      │
             └──────────────────┬───────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────────┐
    │  3️⃣ RUN ALL ALERT CHECKS                                   │
    │  (app/churn_alert_engine.py)                               │
    │                                                             │
    │  async def run_all_churn_checks()                           │
    │  ├─ check_ease_of_use_churn_spike() ────→ HIGH alert       │
    │  │  (if >20% of churners cite "ease of use")              │
    │  │                                                          │
    │  ├─ check_churn_rate_spike() ────→ CRITICAL alert         │
    │  │  (if recent rate >50% above baseline)                  │
    │  │                                                          │
    │  ├─ check_low_engagement_churn() ────→ MEDIUM alert       │
    │  │  (if >40% have <50% approval & <7 active days)        │
    │  │                                                          │
    │  └─ check_price_sensitivity_spike() ────→ MEDIUM alert    │
    │     (if >25% would return with discount)                   │
    └────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
    ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
    │   📊 DATABASE        │  │   📧 EMAIL ALERTS    │  │   🎯 RESPONSE        │
    │  churn_alerts        │  │                      │  │                      │
    │  ┌────────────────┐  │  │ product@lokigi.com   │  │ {                    │
    │  │alert_type      │  │  │ ┌────────────────┐   │  │  status: "success"   │
    │  │severity        │  │  │ │[HIGH] Ease Use│   │  │  survey_id: "..."    │
    │  │metric_value    │  │  │ │Alert Message  │   │  │  alerts: [...]       │
    │  │alert_message   │  │  │ │[View Dashboard│   │  │ }                    │
    │  │acknowledged_at │  │  │ └────────────────┘   │  │                      │
    │  └────────────────┘  │  │                      │  │                      │
    └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

---

## 🔄 Flujo de Análisis (Dashboard)

```
┌──────────────────────────────────────┐
│ GET /api/churn/analytics?days=30    │
│ (backend/app/main.py)               │
└─────────────┬────────────────────────┘
              │
              ▼
   ┌────────────────────────┐
   │ DATABASE QUERIES       │
   ├────────────────────────┤
   │ 1. SELECT churn_alerts │
   │    WHERE triggered_at  │
   │    >= 7 days ago       │
   │                        │
   │ 2. SELECT churn_surveys│
   │    WITH telemetry_data │
   │    GROUP BY reason     │
   └─────────┬──────────────┘
             │
             ▼
   ┌────────────────────────────────────────┐
   │ analyze_churn_correlation()            │
   │ (app/churn_correlation_analysis.py)   │
   │                                        │
   │ For each churn_reason:                 │
   │ ├─ Count churners                      │
   │ ├─ Avg active days                     │
   │ ├─ Avg approval_rate                   │
   │ ├─ Avg responses_approved              │
   │ ├─ % using tone_selector               │
   │ └─ % low_engagement (<7 days, <50%)   │
   │                                        │
   │ Generates: 5 key insights              │
   └──────────────┬───────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │ ChurnAnalyticsResponse               │
   │ ┌──────────────────────────────────┐ │
   │ │ total_churn: 42                  │ │
   │ │                                  │ │
   │ │ churn_by_reason:                 │ │
   │ │ ├─ ease_of_use: 12 (28.6%) 🔴 │ │
   │ │ ├─ price_too_high: 10 (23.8%)  │ │
   │ │ ├─ lack_of_features: 8 (19.0%) │ │
   │ │ ├─ switched_competitor: 7...   │ │
   │ │                                  │ │
   │ │ satisfaction_by_reason:          │ │
   │ │ ├─ ease_of_use: avg 1.9/5       │ │
   │ │ ├─ price_too_high: avg 2.4/5    │ │
   │ │                                  │ │
   │ │ price_sensitivity:               │ │
   │ │ ├─ would_return: 8 (19.0%)       │ │
   │ │                                  │ │
   │ │ recent_alerts: [...]             │ │
   │ └──────────────────────────────────┘ │
   └──────────────────────────────────────┘
             │
             ▼
   ┌─────────────────────────────────────────────────────────┐
   │ 🎨 FRONTEND DASHBOARD: /admin/churn/analytics          │
   │ ┌─────────────────────────────────────────────────────┐ │
   │ │ Churn Breakdown (Pie Chart)                         │ │
   │ │                                                     │ │
   │ │ 🔴 Ease of Use: 28.6% → [⚠️ HIGH ALERT!]          │ │
   │ │ 💰 Price Too High: 23.8%                            │ │
   │ │ ❌ Lack Features: 19.0%                             │ │
   │ │ 🔄 Switched: 16.7%                                 │ │
   │ │                                                     │ │
   │ │ ┌─────────────────────────────────────────────────┐ │
   │ │ │ Engagement Correlation                         │ │
   │ │ │                                                 │ │
   │ │ │ Reason          │ Avg Days │ Approval │ Low Eng│
   │ │ │ ───────────────┼──────────┼──────────┼─────── │
   │ │ │ ease_of_use    │ 3.2 days │ 28%      │ 75%   │
   │ │ │ price_too_high │ 12.1days │ 62%      │ 20%   │
   │ │ │ lack_of_feats  │ 8.7 days │ 45%      │ 55%   │
   │ │ └─────────────────────────────────────────────────┘ │
   │ │                                                     │ │
   │ │ Recent Alerts                                       │ │
   │ │ ┌─────────────────────────────────────────────────┐ │
   │ │ │ 🚨 [HIGH] ease_of_use churn spike detected     │ │
   │ │ │    28.6% of churners cite difficulty (>20%)    │ │
   │ │ │    → UX Audit Recommended                      │ │
   │ │ │    [Acknowledge Button]                        │ │
   │ │ └─────────────────────────────────────────────────┘ │
   │ └─────────────────────────────────────────────────────┘ │
   └─────────────────────────────────────────────────────────┘
```

---

## 📦 Database Schema (PostgreSQL)

```
┌─────────────────────────────────────────────────────────┐
│ users                                                   │
├─────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                           │
│ email (VARCHAR, UNIQUE)                                 │
│ created_at (TIMESTAMP)                                  │
│ [relationships to churn tables below]                   │
└──────────┬──────────────────────────────────────────────┘
           │ 1:N
           │
           ├─────────────────────────────────────────────────────┐
           │                                                     │
           ▼                                                     ▼
    ┌──────────────────────────┐                  ┌──────────────────────────┐
    │ lifecycle_events         │                  │ churn_surveys            │
    ├──────────────────────────┤                  ├──────────────────────────┤
    │ id (UUID, PK)            │                  │ id (UUID, PK)            │
    │ user_id (UUID, FK)       │                  │ user_id (UUID, FK)       │
    │ event_type (ENUM) ◄───┐  │                  │ cancellation_date (DATE) │
    │ │ signup           │  │                      │ primary_reason (ENUM) ◄─┤
    │ │ first_connection │  │                      │ │ price_too_high    │
    │ │ first_reply_gen  │  │                      │ │ lack_of_features  │
    │ │ churn_initiated  │  │                      │ │ ease_of_use ◄─────┼─┐
    │ metadata (JSON)    │  │                      │ │ switched_competitor
    │ created_at         │  │                      │ │ not_using_enough │
    │                    │  │                      │ │ poor_support     │
    └────────────────────┼──┘                      │ │ technical_issues │
                         │                          │ │ personal_reasons │
                         │                          │ │ other            │
                         │                          │ secondary_reasons│ (JSON)
                         │                          │ satisfaction_score│ (INT)
                         │                          │ free_text_feedback│
                         │                          │ would_return_if_price │
                         │                          │ reduction_amount_pct│
                         │                          └──────────────────────────┘
                         │
                         │  1:1
                         │
                         ▼
           ┌──────────────────────────────────────────┐
           │ churn_telemetry_snapshot                 │
           ├──────────────────────────────────────────┤
           │ id (UUID, PK)                            │
           │ user_id (UUID, FK, UNIQUE) ◄─────┐      │
           │ active_days_before_cancel         │      │
           │ last_activity_days_ago            │      │
           │ total_reviews_processed           │      │
           │ total_ai_responses_generated      │      │
           │ total_ai_responses_approved       │      │
           │ approval_rate (FLOAT)             │      │
           │ used_tone_selector (BOOLEAN) ◄────┼──┐  │
           │ used_sentiment_reports            │  │  │
           │ used_manual_approval              │  │  │
           │ locations_connected               │  │  │
           │ days_subscribed                   │  │  │
           │ subscription_plan                 │  │  │
           │ captured_at                       │  │  │
           └────────────┬─────────────────────┘  │  │
                        │ (snapshot at moment    │  │
                        │  of churn)             │  │
                        └─────────────────────────┘  │
                                                     │
                                                     ▼
                        ┌──────────────────────────────────────────┐
                        │ churn_alerts                             │
                        ├──────────────────────────────────────────┤
                        │ id (UUID, PK)                            │
                        │ alert_type (VARCHAR)                     │
                        │ severity (VARCHAR): LOW/MEDIUM/HIGH/CRIT│
                        │ triggered_at (TIMESTAMP)                 │
                        │ acknowledged_at (TIMESTAMP, NULLABLE)    │
                        │ acknowledged_by_user_id (UUID, FK)       │
                        │ time_window_days (INT)                   │
                        │ metric_name (VARCHAR)                    │
                        │ metric_value (FLOAT)                     │
                        │ threshold_value (FLOAT)                  │
                        │ alert_message (TEXT) ◄─┐  Recomendations│
                        │ details (JSON)          │  accionables  │
                        │ created_at (TIMESTAMP)  │                │
                        └──────────────────────────────────────────┘
```

---

## 🚨 Alert Types & Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ ALERT ENGINE: run_all_churn_checks()                            │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 1. check_ease_of_use_churn_spike()                              │
├─────────────────────────────────────────────────────────────────┤
│ Trigger: > 20% of churns attribute to "ease_of_use_difficulty" │
│ Severity: HIGH                                                  │
│ Action: UX Audit, better onboarding, docs                       │
│ Example:                                                        │
│   "23 of 91 churners cite difficulty (25.3%)"                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. check_churn_rate_spike()                                     │
├─────────────────────────────────────────────────────────────────┤
│ Trigger: Recent churn rate > 50% above baseline                 │
│ Severity: CRITICAL                                              │
│ Action: Investigate recent changes, logs, support outreach      │
│ Example:                                                        │
│   "Recent: 8.2% (baseline 3.1%) = +164% spike"                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. check_low_engagement_churn_pattern()                         │
├─────────────────────────────────────────────────────────────────┤
│ Trigger: > 40% low-engagement churners                          │
│ Condition: approval_rate < 50%, active_days < 7               │
│ Severity: MEDIUM                                                │
│ Action: Simplify onboarding, show quick wins, engagement nudges │
│ Example:                                                        │
│   "52% of churners had <50% approval & <7 days"               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 4. check_price_sensitivity_spike()                              │
├─────────────────────────────────────────────────────────────────┤
│ Trigger: > 25% would return with discount OR > 30% cite price   │
│ Severity: MEDIUM                                                │
│ Action: Tiered pricing, discounts, value communication          │
│ Example:                                                        │
│   "31% would stay with discount | 28% cite price"             │
└─────────────────────────────────────────────────────────────────┘

           ALL ALERTS
               │
               ▼
        ┌──────────────┐
        │ Filter HIGH  │
        │  or CRITICAL │
        └──────┬───────┘
               │
               ▼
        ┌──────────────────────────┐
        │ Email to product team    │
        │ product@lokigi.com       │
        │ (Daily at 08:00 UTC)     │
        └──────────────────────────┘
```

---

## 📂 File Structure

```
backend/
├── app/
│   ├── main.py ...................... FastAPI routes (ADD: /api/churn/*)
│   ├── models.py ..................... SQLAlchemy (ADD: 4 churn models)
│   ├── telemetry_models.py ........... Pydantic schemas ✅ NEW
│   ├── churn_alert_engine.py ......... Alert logic ✅ NEW
│   ├── churn_correlation_analysis.py. Analytics ✅ NEW
│   ├── monthly_report_worker.py ...... APScheduler (ADD: daily_churn_report)
│   └── database.py
│
├── alembic/
│   └── versions/
│       ├── 20260418_0006_add_tone_preference.py
│       └── 20260418_0007_add_churn_tracking.py ✅ NEW
│
└── tests/
    └── test_churn_system.py .......... Test suite ✅ NEW

frontend/
└── src/
    ├── pages/
    │   └── ChurnSurvey.tsx ........... Survey form (ADD)
    └── app/
        └── admin/
            └── churn/
                └── analytics/page.tsx  Dashboard (ADD)
```

---

## 🎯 Signal Flow Example

**Scenario:** User cancels → Ease of Use complaint → System detects trend

```
User Action Timeline:
─────────────────────

Day 1-30: User signs up, tries platform, low engagement (~3 active days)
Day 31: User decides to cancel
       ↓
User clicks "Cancel Subscription"
       ↓
Browser navigates to /starter/churn-survey
       ↓
User selects: "ease_of_use_difficulty" (reason)
              Satisfaction: 2/5
              Feedback: "Dashboard was too confusing"
       ↓
Form POST /api/churn/survey
       ↓
Backend:
  ✓ Save ChurnSurvey (reason, feedback, etc)
  ✓ Capture ChurnTelemetrySnapshot (3 active days, 20% approval, etc)
  ✓ Run check_ease_of_use_churn_spike()
       ├─ Query: "SELECT count(*) FROM churn_surveys 
       │          WHERE reason = 'ease_of_use'
       │          AND date >= TODAY - 30
       ├─ Count: 23 ease_of_use churns out of 91 total = 25.3%
       ├─ Compare: 25.3% > 20% threshold ✓
       └─ CREATE ChurnAlert (severity=HIGH, alert_message=...)
  ✓ Return response with alerts
       ↓
APScheduler Daily Job (08:00 UTC):
  ✓ Run run_all_churn_checks()
  ✓ Find alert: severity=HIGH
  ✓ Email to product@lokigi.com:
       ┌─────────────────────────────────────┐
       │ 🚨 CHURN ALERT: Ease of Use Spike   │
       │                                     │
       │ 25.3% of churners (23/91) cite:     │
       │ "Difficulty using platform"         │
       │                                     │
       │ RECOMMENDED ACTIONS:                │
       │ 1. UX Audit of dashboard            │
       │ 2. Improve onboarding               │
       │ 3. Review user feedback             │
       │ 4. Support outreach                 │
       │                                     │
       │ [View Full Dashboard] →             │
       └─────────────────────────────────────┘
       ↓
Product Team Reviews:
  ✓ Opens /admin/churn/analytics
  ✓ Sees correlation: ease_of_use churners avg 3.2 days active
  ✓ Sees: 75% are in "low engagement" segment
  ✓ Decides: Priority 1 = Improve first-time user experience
  ✓ Clicks [Acknowledge Alert]
```

---

## 💾 Data Lifecycle

```
COLLECTION (ChurnSurvey + ChurnTelemetrySnapshot)
├─ When: User cancels subscription
├─ What: Qualitative (reason, feedback) + Quantitative (metrics)
├─ TTL: Permanent (for historical analysis)
└─ Retention: Governed by data retention policy

ANALYSIS (ChurnAlert + Correlation)
├─ When: Immediately + Daily job (08:00 UTC)
├─ Frequency: Real-time on each churn + Daily aggregation
├─ Window: Configurable (default 30 days)
└─ Output: Alerts, Insights, Recommendations

REPORTING (/admin/churn/analytics)
├─ Audience: Product Team (admin only)
├─ Frequency: Real-time dashboard
├─ Metrics: Reason breakdown, correlations, satisfaction, price sensitivity
└─ Action: Acknowledge alerts, plan UX improvements

ARCHIVE
├─ When: >90 days old (configurable)
├─ Where: Data warehouse / cold storage
├─ Query: For annual trend analysis
└─ Compliance: GDPR deletion on user account removal
```
