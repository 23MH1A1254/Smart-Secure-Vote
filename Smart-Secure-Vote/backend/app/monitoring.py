EVENTS = []
def record(event: str, voter_id: str = ""):
    EVENTS.append({"event": event, "voter_id": voter_id})
    if len(EVENTS) > 500:
        del EVENTS[:-500]
