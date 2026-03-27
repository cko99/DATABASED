import requests
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== ENV VARIABLES =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM7_API_KEY = os.getenv("LLM7_API_KEY")

SHEET_NAME = "company_data"

# ===== GOOGLE SHEETS SETUP =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1Yge8HlHEiQUTazaQ1yy0hYney22MFMYzlMBfjBoWHD8").sheet1

# ===== GEMINI =====
def get_raw_data():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

    prompt = "List 1 construction company in Malaysia with details: name, location, email, phone, website."

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    res = requests.post(url, json=payload)
    data = res.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        print("Gemini error:", data)
        return ""

# ===== LLM7 =====
def clean_data(raw_text):
    url = "https://api.llm7.io/v1/process"

    prompt = f"""
    Extract this into JSON:
    {{
      "company_name": "",
      "industry": "",
      "state": "",
      "city": "",
      "country": "",
      "latitude": "",
      "longitude": "",
      "website": "",
      "email": "",
      "phone": "",
      "description": ""
    }}

    Text:
    {raw_text}
    """

    headers = {
        "Authorization": f"Bearer {LLM7_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt
    }

    res = requests.post(url, headers=headers, json=payload)

    try:
        return res.json()
    except:
        print("LLM7 error:", res.text)
        return {}

# ===== INSERT TO SHEET =====
def insert_to_sheet(data):
    row = [
        data.get("company_name", ""),
        data.get("industry", ""),
        data.get("state", ""),
        data.get("city", ""),
        data.get("country", ""),
        data.get("latitude", ""),
        data.get("longitude", ""),
        data.get("website", ""),
        data.get("email", ""),
        data.get("phone", ""),
        data.get("description", "")
    ]

    sheet.append_row(row)

# ===== MAIN =====
def main():
    print("STEP 1: Gemini...")
    raw = get_raw_data()

    if not raw:
        print("No raw data. Stop.")
        return

    print("STEP 2: LLM7...")
    cleaned = clean_data(raw)

    if not cleaned:
        print("No cleaned data. Stop.")
        return

    print("STEP 3: Insert to Google Sheet...")
    insert_to_sheet(cleaned)

    print("DONE")

if __name__ == "__main__":
    main()
