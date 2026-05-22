import json
from pathlib import Path
from statistics import mean
from datetime import datetime, timedelta


DATA_DIR = Path("data")
LATE_FILE = DATA_DIR / "lates.json"
OUTLIER_MINUTES = 30


def _ensure_file():
    DATA_DIR.mkdir(exist_ok=True)

    if not LATE_FILE.exists():
        LATE_FILE.write_text("[]", encoding="utf-8")


def load_late_records() -> list[dict]:
    _ensure_file()

    with open(LATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_late_records(records: list[dict]) -> None:
    _ensure_file()

    with open(LATE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_late_record(
    member_id: int | str,
    name: str,
    session_date: str,
    minutes: int,
) -> dict:
    """
    운영진이 입력한 지각 기록을 JSON 파일에 저장합니다.
    """
    records = load_late_records()

    record = {
        "member_id": str(member_id),
        "name": name,
        "session_date": session_date,
        "minutes": int(minutes),
    }

    records.append(record)
    save_late_records(records)

    return record


def get_member_late_minutes(member_id: int | str) -> list[int]:
    """
    특정 회원의 전체 지각 분 기록을 리스트로 반환합니다.
    """
    records = load_late_records()
    member_id = str(member_id)

    return [
        int(record["minutes"])
        for record in records
        if record["member_id"] == member_id
    ]


def predict_early_notice_minutes(late_minutes: list[int]) -> int:
    """
    다음 세션 공지에서 몇 분 일찍 오라고 할지 계산합니다.
    """
    normal_lates = [
        minute
        for minute in late_minutes
        if 0 < minute < OUTLIER_MINUTES
    ]

    if not normal_lates:
        return 0

    avg_late = mean(normal_lates)

    if avg_late < 5:
        return 0

    rounded = round(avg_late / 5) * 5

    return min(25, int(rounded))


def count_outliers(late_minutes: list[int]) -> int:
    return sum(1 for minute in late_minutes if minute >= OUTLIER_MINUTES)


def total_late_minutes(late_minutes: list[int]) -> int:
    return sum(minute for minute in late_minutes if minute > 0)


def make_late_record_dm(session_date: str, minutes: int) -> str:
    """
    지각 기록 입력 후 해당 회원에게 보내는 개인 DM.
    """
    if minutes <= 0:
        return (
            f"✅ {session_date} 세션 출석 기록이 저장되었습니다.\n"
            f"지각 기록은 없습니다."
        )

    return (
        f"📌 {session_date} 세션에 {minutes}분 지각으로 기록되었습니다."
    )


def make_late_rank_report() -> str:
    """
    전체 지각 순위 리포트.
    운영진 채널에 보낼 용도.
    """
    records = load_late_records()

    if not records:
        return "아직 지각 기록이 없습니다."

    grouped = {}

    for record in records:
        member_id = record["member_id"]
        name = record["name"]
        minutes = int(record["minutes"])

        if member_id not in grouped:
            grouped[member_id] = {
                "name": name,
                "late_minutes": [],
            }

        grouped[member_id]["late_minutes"].append(minutes)

    ranked = []

    for member_id, data in grouped.items():
        late_minutes = data["late_minutes"]

        ranked.append({
            "name": data["name"],
            "total": total_late_minutes(late_minutes),
            "count": sum(1 for m in late_minutes if m > 0),
            "outliers": count_outliers(late_minutes),
            "early_notice": predict_early_notice_minutes(late_minutes),
        })

    ranked.sort(key=lambda x: (x["total"], x["count"], x["outliers"]), reverse=True)

    lines = ["📊 **운영진용 지각 순위 리포트**\n"]

    for i, item in enumerate(ranked, start=1):
        lines.append(
            f"{i}. {item['name']} - "
            f"총 {item['total']}분 / "
            f"{item['count']}회 지각 / "
            f"30분 이상 {item['outliers']}회 / "
            f"다음 공지 {item['early_notice']}분 일찍 안내"
        )

    return "\n".join(lines)


def make_personal_session_notice(
    session_title: str,
    session_start: datetime,
    location: str,
    member_id: int | str,
) -> str:
    """
    다음 세션 공지 때 개인별 지각 기록을 반영해서 메시지 생성.
    """
    late_minutes = get_member_late_minutes(member_id)
    early_minutes = predict_early_notice_minutes(late_minutes)

    adjusted_time = session_start - timedelta(minutes=early_minutes)

    start_text = session_start.strftime("%H:%M")
    adjusted_text = adjusted_time.strftime("%H:%M")

    if early_minutes <= 0:
        return (
            f"📢 **세션 알림**\n"
            f"- 세션: {session_title}\n"
            f"- 시간: {start_text}\n"
            f"- 장소: {location}\n"
            f"{start_text}까지 참여해 주세요."
        )

    return (
        f"📢 **세션 알림**\n"
        f"- 세션: {session_title}\n"
        f"- 실제 시작 시간: {start_text}\n"
        f"- 장소: {location}\n"
        f"최근 지각 기록을 반영해 {adjusted_text}까지 와 주세요."
    )