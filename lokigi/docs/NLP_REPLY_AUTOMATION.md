# NLP Reply Automation

## Entry point

- Function: `generate_review_reply_decision`
- File: `backend/app/review_reply_engine.py`

## Inputs

- `review_text`
- `stars`
- `business_name`
- `author_name`

## Outputs

Structured decision object:

- `action`: `AUTO_REPLY` or `ALERT`
- `detected_language`
- `reason`
- `public_reply`
- `internal_alert`:
  - `priority`
  - `category`
  - `summary`
  - `recommended_next_step`

## Rules implemented

1. Language is auto-detected from review text.
2. Tone is professional and warm.
3. If stars < 3:
   - action is always `ALERT`
   - no public auto-reply
4. If stars > 4:
   - action is `AUTO_REPLY`
   - gratitude message must include business and author names
5. If stars are 3 or 4:
   - `AUTO_REPLY` by default
   - escalate to `ALERT` if sensitive content is detected

## Persistence

Decision fields are stored in `reviews` table for traceability and analytics.

## Webhook integration

The decision runs automatically after each stored review from Google webhook flow.
The API response includes key decision fields to support downstream automation.

## Tests

Unit tests are in `backend/tests/unit/test_review_reply_engine.py` and cover:

- low rating alert rule
- high rating gratitude rule with names
- language detection behavior
- sensitive content escalation
- mid-rating standard auto-reply
