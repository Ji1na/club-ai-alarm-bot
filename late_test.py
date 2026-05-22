from late_manager import (
    predict_early_notice_minutes,
    make_late_report,
    make_late_rank_report,
)


def main():
    print("개인 예측 테스트")
    print(predict_early_notice_minutes([0, 5, 10, 15, 40]))
    print()

    print("개인 리포트 테스트")
    print(make_late_report("김철수", [0, 5, 10, 15, 40]))
    print()

    print("전체 순위 리포트 테스트")
    records = [
        {"name": "김철수", "late_minutes": [0, 5, 10, 15, 40]},
        {"name": "이영희", "late_minutes": [0, 0, 3]},
        {"name": "박민수", "late_minutes": [20, 25, 15, 35]},
    ]

    print(make_late_rank_report(records))


if __name__ == "__main__":
    main()