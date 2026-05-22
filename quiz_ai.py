import os
import json
from typing import Any
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY가 없습니다. 프로젝트 루트 폴더의 .env 파일에 OPENAI_API_KEY를 넣어주세요."
    )

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """
    모델이 혹시 ```json ... ``` 형태로 반환해도 JSON 배열만 뽑아서 파싱합니다.
    """
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise json.JSONDecodeError("JSON 배열을 찾지 못했습니다.", text, 0)

    return json.loads(text[start:end + 1])


async def generate_quizzes(content: str, count: int = 10) -> list[dict[str, Any]]:
    """
    발표자료 텍스트를 받아 복습 퀴즈를 생성합니다.

    반환 형식:
    [
      {
        "type": "multiple_choice",
        "question": "...",
        "choices": ["A", "B", "C", "D"],
        "answer": "...",
        "explanation": "...",
        "difficulty": "easy|medium|hard",
        "source_hint": "발표자료의 어떤 부분을 근거로 냈는지"
      }
    ]
    """
    if not content or not content.strip():
        raise ValueError("퀴즈를 생성할 발표자료 내용이 비어 있습니다.")

    prompt = f"""
너는 대학 동아리 세션 복습 퀴즈 출제자입니다.

아래 [발표자료]와 [참고자료] 내용을 바탕으로 복습 퀴즈 {count}문제를 생성하세요.

출제 원칙:
- 발표자료의 핵심 개념, 발표자가 강조했을 법한 내용, 헷갈리기 쉬운 개념을 우선 출제하세요.
- 단순 문장 암기보다 이해 여부를 확인하는 문제를 만드세요.
- 자료에 없는 내용을 억지로 만들지 마세요.
- 자료가 너무 부족하면, 일반적으로 알려진 배경지식을 최소한으로 보충할 수 있습니다.
- 단, 보충한 내용은 source_hint에 "일반 배경지식 보충"이라고 표시하세요.
- 한국어로 작성하세요.

문제 구성:
- 총 {count}문제
- 객관식 4문제
- 주관식/단답형 3문제
- 서술형 3문제
- 객관식은 choices를 반드시 4개 제공하세요.
- 각 문제마다 정답, 해설, 난이도, 출제 근거를 포함하세요.

반드시 아래 JSON 배열 형식만 반환하세요.
다른 설명 문장, markdown, 코드블록은 절대 쓰지 마세요.

[
  {{
    "type": "multiple_choice",
    "question": "질문 내용",
    "choices": ["보기1", "보기2", "보기3", "보기4"],
    "answer": "정답",
    "explanation": "해설",
    "difficulty": "easy",
    "source_hint": "출제 근거"
  }},
  {{
    "type": "short_answer",
    "question": "질문 내용",
    "choices": [],
    "answer": "정답",
    "explanation": "해설",
    "difficulty": "medium",
    "source_hint": "출제 근거"
  }},
  {{
    "type": "essay",
    "question": "질문 내용",
    "choices": [],
    "answer": "모범 답안",
    "explanation": "채점 포인트",
    "difficulty": "hard",
    "source_hint": "출제 근거"
  }}
]

[발표자료 및 참고자료]
{content[:15000]}
""".strip()

    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            max_output_tokens=4000,
        )

        text = response.output_text
        quizzes = _extract_json_array(text)

        return quizzes

    except json.JSONDecodeError:
        return [
            {
                "type": "error",
                "question": "퀴즈 JSON 파싱 오류가 발생했습니다.",
                "choices": [],
                "answer": "다시 시도해주세요.",
                "explanation": "AI 응답이 JSON 형식에 맞지 않았습니다.",
                "difficulty": "easy",
                "source_hint": "system",
            }
        ]

    except Exception as e:
        print(f"[quiz_ai] 오류: {e}")
        return [
            {
                "type": "error",
                "question": f"퀴즈 생성 실패: {e}",
                "choices": [],
                "answer": "-",
                "explanation": "API key, 모델명, 네트워크 상태를 확인해주세요.",
                "difficulty": "easy",
                "source_hint": "system",
            }
        ]