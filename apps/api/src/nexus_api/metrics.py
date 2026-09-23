from prometheus_client import Counter, Histogram

SEARCH_REQUESTS = Counter(
    "nexus_search_requests_total", "Search requests", labelnames=("engine", "status")
)
SEARCH_LATENCY = Histogram(
    "nexus_search_latency_seconds", "Search latency", labelnames=("engine",)
)
ZERO_RESULTS = Counter(
    "nexus_search_zero_results_total", "Searches returning no hits", labelnames=("engine",)
)
