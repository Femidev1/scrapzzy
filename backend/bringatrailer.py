import asyncio
import json
import smtplib
import os
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playwright.async_api import async_playwright

BAT_URL = "https://bringatrailer.com/motorcycles/"
EMAIL_ADDRESS = "thedesignerfemi@gmail.com"
EMAIL_PASSWORD = "cuwu dmni kqgs wlob"
TO_EMAIL = "femdavid09@gmail.com"
LISTING_HISTORY_FILE = "bat_seen.json"

# Load seen listings
if os.path.exists(LISTING_HISTORY_FILE):
    with open(LISTING_HISTORY_FILE, "r") as f:
        seen_links = set(json.load(f))
else:
    seen_links = set()

def send_email(title, link):
    print(f"🎯 New BaT Match: {title} — {link}")
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    msg["Subject"] = f"🚨 New BaT Motorcycle Listing: {title}"
    body = f"New motorcycle auction ending soon:\n\n{title}\n{link}"
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📬 Email sent!")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def is_under_2_hours(countdown_text):
    match = re.match(r"(\d{1,2}):(\d{2}):(\d{2})", countdown_text)
    if match:
        hours = int(match.group(1))
        return hours < 2
    return False

async def fetch_bat_motorcycles():
    global seen_links
    print("📡 Scanning Bring a Trailer...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(BAT_URL, timeout=60000)

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)

        await page.wait_for_selector("div.listing-card", timeout=10000)
        cards = await page.query_selector_all("div.listing-card")

        print(f"📦 Total cards found: {len(cards)}")
        found = 0

        for card in cards:
            try:
                await page.evaluate("(el) => el.style.border = '2px solid red'", card)

                anchor = await card.query_selector("h3 > a")
                if not anchor:
                    print("⚠️ No anchor in h3 — skipping")
                    continue

                href = await anchor.get_attribute("href")
                title = (await anchor.inner_text()).strip()
                link = href if href.startswith("http") else f"https://bringatrailer.com{href}"

                countdown = await card.query_selector("span.countdown-text")
                if not countdown:
                    print(f"⚠️ No countdown — {title}")
                    continue

                countdown_text = (await countdown.inner_text()).strip()
                print(f"⏱️ {title} — countdown: {countdown_text}")

                if re.match(r"\d+ days?", countdown_text, re.IGNORECASE):
                    continue

                if is_under_2_hours(countdown_text):
                    send_email(title, link)
                    seen_links.add(link)
                    found += 1
                    await asyncio.sleep(1.2)

            except Exception as e:
                print(f"⚠️ Error processing listing: {e}")
                continue

        print(f"✅ Listings emailed (under 2h left): {found}")
        await browser.close()

    with open(LISTING_HISTORY_FILE, "w") as f:
        json.dump(list(seen_links), f, indent=2)

async def main():
    while True:
        await fetch_bat_motorcycles()
        print("🕓 Waiting 10 minutes before next check...\n")
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())