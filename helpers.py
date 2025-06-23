from datetime import date, datetime, timezone


def timestamp_from_date(date: date) -> str:
    return (
        datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)  # type: ignore
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
