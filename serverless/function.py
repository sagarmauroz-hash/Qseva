"""Platform-neutral event-driven QueueLess analytics function."""
def handle(event: dict) -> dict:
    token = event.get("token", "unknown")
    duration = float(event.get("service_time_seconds", 0))
    return {"event":"queue.completed","token":token,"counter":event.get("counter","unknown"),"service_time_seconds":duration,"metric":"service_duration"}

if __name__ == "__main__":
    print(handle({"token":"A47","service_time_seconds":180,"counter":"C2"}))
