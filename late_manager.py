from datetime import datetime
import os


LATE_THRESHOLD_MIN = int(os.getenv("LATE_THRESHOLD_MIN", 10))


def is_late(session_time: str, arrived_at: str) -> bool:
    """
    세션 시작 시간과 도착 시간을 비교해 지각 여부 반환.
    session_time, arrived_at 모두 "HH:MM" 형식.
    """
    try:
        start = datetime.strptime(session_time, "%H:%M")
        arrived = datetime.strptime(arrived_at, "%H:%M")
        diff_minutes = (arrived - start).total_seconds() / 60
        return diff_minutes > LATE_THRESHOLD_MIN
    except ValueError as e:
        print(f"[late_manager] 시간 파싱 오류: {e}")
        return False


def get_early_notify_time(session_time: str, early_minutes: int = 30) -> str:
    """
    지각 상습자에게 공지할 시간 계산.
    예: 14:00 세션 → 13:30 반환
    """
    from datetime import timedelta
    start = datetime.strptime(session_time, "%H:%M")
    early = start - timedelta(minutes=early_minutes)
    return early.strftime("%H:%M")
