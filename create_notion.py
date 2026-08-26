import requests
import json

import os
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

# 2. 템플릿이 만들어질 '빈 노션 페이지'의 ID를 여기에 넣으세요!
# (노션에서 새 페이지를 만들고 브라우저 주소창을 보면 https://www.notion.so/어쩌구저쩌구... 이렇게 되어있는데, 맨 뒤의 32자리 문자열입니다)
PARENT_PAGE_ID = '3c527beb718b8067af04c490a92be1fb'

def update_planner_database():
    url = "https://api.notion.com/v1/databases"
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 세련된 무채색(gray, default) 톤으로 디자인된 속성들
    data = {
        "parent": {
            "type": "page_id",
            "page_id": PARENT_PAGE_ID
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "⬛ My Workspace : Schedule & Tasks"
                }
            }
        ],
        "properties": {
            "일정 및 할일": {
                "title": {}
            },
            "기한/일시": {
                "date": {} # 노션 캘린더 연동 핵심 속성
            },
            "진행 상태": {
                "status": {
                    "options": [
                        {"name": "대기중", "color": "default"},
                        {"name": "진행중", "color": "gray"},
                        {"name": "완료됨", "color": "default"}
                    ]
                }
            },
            "분류": {
                "select": {
                    "options": [
                        {"name": "Task", "color": "gray"},
                        {"name": "Event", "color": "default"},
                        {"name": "Meeting", "color": "gray"}
                    ]
                }
            }
        }
    }
    
    print("세련된 디자인의 템플릿을 생성 중입니다...")
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print("✅ 성공! 노션을 확인해보세요.")
    else:
        print(f"❌ 실패 (상태 코드: {response.status_code})")
        print("에러:", response.json())

if __name__ == "__main__":
    update_planner_database()