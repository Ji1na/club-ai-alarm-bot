import httpx
from bs4 import BeautifulSoup


def read_material(url: str | None) -> str | None:
    """
    URL에서 텍스트 내용을 읽어옵니다.
    - 일반 웹페이지: HTML에서 텍스트 추출
    - 텍스트 파일: 그대로 반환
    - URL 없으면 None 반환
    """
    if not url:
        return None

    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "")

            # 일반 텍스트
            if "text/plain" in content_type:
                return r.text[:4000]

            # HTML 페이지 → BeautifulSoup으로 텍스트만 추출
            if "text/html" in content_type:
                soup = BeautifulSoup(r.text, "html.parser")
                # 불필요한 태그 제거
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                # 빈 줄 정리 후 4000자 제한
                lines = [l for l in text.splitlines() if l.strip()]
                return "\n".join(lines)[:4000]

            # 그 외 (PDF 등) — 텍스트 디코딩 시도
            return r.text[:4000]

    except Exception as e:
        print(f"[material_reader] URL 읽기 실패: {e}")
        return None
