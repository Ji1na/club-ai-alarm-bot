import os
import json
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_quizzes(content: str, count: int = 3) -> list[dict]:
    """
    발표 내용을 받아 퀴즈를 생성합니다.
    반환 형식: [{"question": "...", "answer": "..."}, ...]
    """
    prompt = f"""다음 발표 내용을 바탕으로 퀴즈 {count}개를 만들어줘.
반드시 아래 JSON 형식만 반환해. 다른 텍스트 없이.

[
  {{"question": "질문1", "answer": "정답1"}},
  {{"question": "질문2", "answer": "정답2"}},
  {{"question": "질문3", "answer": "정답3"}}
]

발표 내용:
{content}"""

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        text = response.choices[0].message.content.strip()
        # ```json ... ``` 펜스 제거
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except json.JSONDecodeError:
        return [{"question": "퀴즈 파싱 오류가 발생했습니다.", "answer": "다시 시도해주세요."}]
    except Exception as e:
        print(f"[quiz_ai] 오류: {e}")
        return [{"question": f"퀴즈 생성 실패: {e}", "answer": "-"}]
