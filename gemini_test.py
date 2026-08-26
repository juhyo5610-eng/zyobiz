import google.generativeai as genai

import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key")
genai.configure(api_key=GOOGLE_API_KEY)

# 2. 사용할 모델 선택 (코드 분석이나 복잡한 작업엔 pro 모델이 좋아)
model = genai.GenerativeModel('gemini-1.5-pro')

# 3. 프롬프트 작성 및 AI 호출
prompt = "안녕! 나는 파이썬으로 너를 처음 호출해 보는 중이야. 짧고 유쾌하게 인사해 줘!"
response = model.generate_content(prompt)

# 4. 결과 출력
print("AI의 답변:")
print(response.text)
