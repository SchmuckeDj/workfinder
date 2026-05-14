import os
import sys
import django
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings

API_URL = "http://localhost:8000/api/incoming-job/"
TOKEN = settings.AUTOMATION_API_TOKEN
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def post_job(raw_text, source):
    resp = requests.post(
        API_URL,
        data={"raw_text": raw_text, "source": source},
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=10,
    )
    return resp.status_code, resp.json()


def scrape_trabajosdiarios():
    print("-> Scrapeando trabajosdiarios.com...")
    resp = requests.get("https://do.trabajosdiarios.com/", headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    count = 0
    for tag in soup.select('a[href*="/trabajo/"]'):
        href = tag.get("href", "")
        if href in seen:
            continue
        seen.add(href)
        text = tag.get_text(separator="\n", strip=True)
        if len(text) < 20:
            continue
        status, data = post_job(f"{text}\nURL: {href}", "trabajosdiarios")
        print(f"  [{status}] {text[:60]!r}")
        count += 1
    print(f"  Total: {count}")


def scrape_aldaba():
    print("-> Scrapeando aldaba.com...")
    resp = requests.get("https://www.aldaba.com/rd/empleos/", headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = soup.select('article, .oferta, [class*="oferta"]') or soup.select('a[href*="/empleo/"]')
    seen = set()
    count = 0
    for tag in jobs:
        href = tag.get("href", "") if tag.name == "a" else ""
        key = href or tag.get_text()[:50]
        if key in seen:
            continue
        seen.add(key)
        text = tag.get_text(separator="\n", strip=True)
        if len(text) < 20:
            continue
        status, data = post_job(f"{text}\nURL: {href}" if href else text, "aldaba")
        print(f"  [{status}] {text[:60]!r}")
        count += 1
    print(f"  Total: {count}")


if __name__ == "__main__":
    scrape_trabajosdiarios()
    scrape_aldaba()
    print("Completado.")
