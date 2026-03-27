import requests
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== ENV =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM7_API_KEY = os.getenv("LLM7_API_KEY")

SPREADSHEET_ID = "1xOMz2loJFBUel9ewTh1LUmPqSYgXw3JzDVgGAjD0R2Y"

# ===== GOOGLE SHEETS =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ===== GEMINI =====
def get_raw_data():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

    prompt = """
    Give 1 real construction company in Malaysia with:
    - company_name
    - city
    - state
    - website
    - email
    - phone
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    res = requests.post(url, json=payload)

    try:
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        print("❌ Gemini Error:", res.text)
        return None

# ===== LLM7 =====
def clean_data(raw_text):
    url = "https://api.llm7.io/v1/process"

    prompt = f"""
    Convert this text into STRICT JSON format only.

    Format:
    {{
      "company_name": "",
      "industry": "construction",
      "state": "",
      "city": "",
      "country": "Malaysia",
      "latitude": "",
      "longitude": "",
      "website": "",
      "email": "",
      "phone": "",
      "description": ""
    }}

    TEXT:
    {raw_text}
    """

    headers = {
        "Authorization": f"Bearer {LLM7_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post(url, headers=headers, json={"prompt": prompt})

    try:
        text = res.text.strip()

        # 🔥 FIX: buang ```json kalau ada
        if "```" in text:
            text = text.split("```")[1]

        return json.loads(text)

    except Exception as e:
        print("❌ LLM7 Error:", res.text)
        return None

# ===== INSERT =====
def insert_to_sheet(data):
    row = [
        data.get("company_name"),
        data.get("industry"),
        data.get("state"),
        data.get("city"),
        data.get("country"),
        data.get("latitude"),
        data.get("longitude"),
        data.get("website"),
        data.get("email"),
        data.get("phone"),
        data.get("description")
    ]

    print("📤 INSERT ROW:", row)
    sheet.append_row(row)

# ===== MAIN =====
def main():
    print("🚀 TEST INSERT ONLY")

    test_data = {
        "company_name": "TEST COMPANY",
        "industry": "construction",
        "state": "Selangor",
        "city": "Shah Alam",
        "country": "Malaysia",
        "latitude": "",
        "longitude": "",
        "website": "test.com",
        "email": "test@email.com",
        "phone": "0123456789",
        "description": "THIS IS TEST DATA"
    }

    insert_to_sheet(test_data)

    print("✅ TEST DONE")

if __name__ == "__main__":
    main()
