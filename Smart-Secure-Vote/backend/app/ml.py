def score_activity(event_counts):
    """Small demo heuristic placeholder; not a production fraud model."""
    return {ip: (count >= 8) for ip, count in event_counts.items()}
