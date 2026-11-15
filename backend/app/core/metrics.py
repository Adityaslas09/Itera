from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Metrics definitions
AI_REQUESTS_TOTAL = Counter(
    "packvote_ai_requests_total",
    "Total number of AI requests made via the Model Gateway",
    ["provider", "model", "status", "task"]
)

AI_LATENCY_SECONDS = Histogram(
    "packvote_ai_latency_seconds",
    "Latency of AI requests through the Model Gateway in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

AI_TOKEN_USAGE_TOTAL = Counter(
    "packvote_ai_token_usage_total",
    "Total tokens consumed by the AI Model Gateway",
    ["provider", "model", "token_type"]  # token_type: prompt, completion
)

AI_ESTIMATED_COST_USD = Counter(
    "packvote_ai_estimated_cost_usd_total",
    "Cumulative estimated dollar cost of AI inference",
    ["provider", "model"]
)

TRIPS_CREATED_TOTAL = Counter(
    "packvote_trips_created_total",
    "Total trips created in PackVote"
)

SMS_MESSAGES_TOTAL = Counter(
    "packvote_sms_messages_total",
    "Total SMS messages sent and received",
    ["direction", "status"]  # direction: outbound, inbound; status: success, failed
)

VOTES_CAST_TOTAL = Counter(
    "packvote_votes_cast_total",
    "Total ranked-choice ballots submitted"
)

ACTIVE_TRIPS_GAUGE = Gauge(
    "packvote_active_trips",
    "Current number of trips actively collecting surveys or voting"
)

def get_metrics_payload() -> tuple[bytes, str]:
    """Return raw Prometheus metrics bytes and content type."""
    return generate_latest(), CONTENT_TYPE_LATEST
