import requests
import json
import os
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ===== CONFIG =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SPREADSHEET_ID = "1xOMz2loJFBUel9ewTh1LUmPqSYgXw3JzDVgGAjD0R2Y"

# ===== GOOGLE SHEETS =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ===== HELPERS =====

def clean_text(text):
    if not text:
        return ""
    return str(text).strip()

def clean_email(email):
    if not email:
        return ""
    if "@" in email:
        return email.strip()
    return ""

def clean_phone(phone):
    if not phone:
        return ""
    phone = re.sub(r"[^\d+]", "", phone)
    return phone

def safe_json_parse(text):
    try:
        if "```" in text:
            text = text.split("```")[1]
        return json.loads(text)
    except:
        return None

# ===== GEMINI =====

def get_company_data():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt ="""
Give 100 REAL company in Malaysia related to:

- Geospatial
- GIS (Geographic Information System)
- Land Survey
- Mapping
- Drone Survey
- Remote Sensing

Avoid duplicates.

Include:
- Company Name
- City
- State
- Website (if available)
- Email (if available)
- Phone (if available)
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        res = requests.post(url, json=payload)
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except:
        print("❌ Gemini failed")
        return None

# ===== VALIDATION =====

def validate_data(data):
    if not data:
        return False

    if not data.get("company_name"):
        return False

    return True

# ===== CLEANING =====

def clean_data(data):
    return {
        "company_name": clean_text(data.get("company_name")),
        "industry": clean_text(data.get("industry")) or "construction",
        "state": clean_text(data.get("state")),
        "city": clean_text(data.get("city")),
        "country": clean_text(data.get("country")) or "Malaysia",
        "latitude": clean_text(data.get("latitude")),
        "longitude": clean_text(data.get("longitude")),
        "website": clean_text(data.get("website")),
        "email": clean_email(data.get("email")),
        "phone": clean_phone(data.get("phone")),
        "description": clean_text(data.get("description")),
    }

# ===== DUPLICATE CHECK =====

def is_duplicate(company_name):
    records = sheet.col_values(1)  # column A
    return company_name in records

# ===== INSERT =====

def insert_to_sheet(data):
    row = [
        data["company_name"],
        data["industry"],
        data["state"],
        data["city"],
        data["country"],
        data["latitude"],
        data["longitude"],
        data["website"],
        data["email"],
        data["phone"],
        data["description"]
    ]

    print("📤 INSERT:", row)
    sheet.append_row(row)

# ===== MAIN =====

def main():
    print("🚀 START PIPELINE")

    success = 0

    for i in range(20):
        print(f"\n🔄 {i+1}/20")

        raw = get_company_data()
        print("RAW:", raw)

        if not raw:
            raw = "Unknown Company Malaysia"

        # 🔥 FORCE INSERT (NO MORE EMPTY)
        data = {
            "company_name": raw[:50],
            "industry": "construction",
            "state": "Malaysia",
            "city": "",
            "country": "Malaysia",
            "latitude": "",
            "longitude": "",
            "website": "",
            "email": "",
            "phone": "",
            "description": raw
        }

        if is_duplicate(data["company_name"]):
            print("⚠️ Duplicate skip")
            continue

        insert_to_sheet(data)
        success += 1

        time.sleep(2)

    print(f"\n✅ DONE: {success} inserted")

if __name__ == "__main__":
    main()
