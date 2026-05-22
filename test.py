import asyncio
from quiz_ai import generate_quizzes


async def main():
    sample_text = """
    Transformer는 self-attention을 사용해 문맥 속 단어의 의미를 파악한다.
    Query, Key, Value를 통해 단어 간 관련도를 계산하고,
    attention score와 softmax를 이용해 각 단어가 다른 단어를 얼마나 참고할지 결정한다.
    Multi-head attention은 여러 관점에서 단어 간 관계를 파악하도록 돕는다.
    Transformer는 RNN과 달리 순차적으로 단어를 처리하지 않아 병렬 처리가 가능하다.
    """

    quizzes = await generate_quizzes(sample_text, count=10)

    for i, quiz in enumerate(quizzes, start=1):
        print(f"\n=== 문제 {i} ===")
        print(f"유형: {quiz.get('type')}")
        print(f"난이도: {quiz.get('difficulty')}")
        print(f"질문: {quiz.get('question')}")

        choices = quiz.get("choices", [])
        if choices:
            for idx, choice in enumerate(choices, start=1):
                print(f"  {idx}. {choice}")

        print(f"정답: {quiz.get('answer')}")
        print(f"해설: {quiz.get('explanation')}")
        print(f"출제 근거: {quiz.get('source_hint')}")


asyncio.run(main())