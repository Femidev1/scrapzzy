import json
import asyncio
import re
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# === CONFIG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LISTING_HISTORY_FILE = os.path.join(BASE_DIR, "listing_history.json")
EXPORT_JSON_PATH = os.path.abspath(os.path.join(BASE_DIR, "../frontend/public/listings.json"))
REFRESH_INTERVAL = 180  # Check every 3 minutes
CUTOFF_MINUTES = 15

KIJIJI_URLS = [
    "https://www.kijiji.ca/b-motorcycles/canada/c30l0"
]

# === Load Seen Listings ===
if os.path.exists(LISTING_HISTORY_FILE):
    with open(LISTING_HISTORY_FILE, "r") as f:
        seen_listings = json.load(f)
else:
    seen_listings = {}

# === Time Parser ===
def parse_relative_time(text):
    now = datetime.utcnow()
    text = text.lower().strip()
    if "just now" in text or "less than" in text or text == "":
        return now
    match = re.search(r"(\d+)\s+(min|minute|hour)", text)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    return now - timedelta(minutes=amount) if "min" in unit else now - timedelta(hours=amount)

# === Process a Single Kijiji Page ===
async def process_page(context, url, cutoff):
    global seen_listings
    print(f"📄 Checking: {url}")
    page = await context.new_page()
    await page.goto(url, timeout=60000)

    container = await page.query_selector('ul[data-testid="srp-search-list"]')
    if not container:
        print("❌ Could not find listings container.")
        await page.close()
        return {}

    links = await container.query_selector_all('a[data-testid="listing-link"]')
    if not links:
        print("⚠️ No listings found.")
        await page.close()
        return {}

    new_listings = {}
    for link_tag in links:
        href = await link_tag.get_attribute("href")
        link = href if href.startswith("http") else "https://www.kijiji.ca" + href
        title = await link_tag.inner_text()

        if link in seen_listings:
            continue

        detail_page = await context.new_page()
        try:
            await detail_page.goto(link, timeout=15000)
            await detail_page.wait_for_selector('span[data-testid="listing-date"]', timeout=7000)
            date_element = await detail_page.query_selector('span[data-testid="listing-date"]')
            posted_text = await date_element.inner_text() if date_element else "unknown"
            posted_time = parse_relative_time(posted_text)

            if not posted_time or posted_time < cutoff:
                print(f"⏳ Old: {posted_text.strip()} — {title.strip()}")
                await detail_page.close()
                continue

            # Try to fetch image (fallback: "")
            image_element = await detail_page.query_selector('img[data-testid="gallery-image"]')
            image = await image_element.get_attribute("src") if image_element else ""

            listing_obj = {
                "title": title.strip(),
                "url": link,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "image": image
            }

            new_listings[link] = listing_obj
            seen_listings[link] = listing_obj  # ✅ just add it to memory

            print(f"✅ Fresh: {posted_text.strip()} — {title.strip()} — {link}")

        except Exception as e:
            print(f"⚠️ Error fetching {link}: {e}")
        finally:
            await detail_page.close()

    await page.close()
    return new_listings

# === Master Scraper ===
async def fetch_kijiji_listings():
    global seen_listings
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cutoff = datetime.utcnow() - timedelta(minutes=CUTOFF_MINUTES)
        all_new = {}

        for url in KIJIJI_URLS:
            listings = await process_page(context, url, cutoff)
            all_new.update(listings)

        # 🧼 Clean out expired listings
        seen_listings = {
            link: obj for link, obj in seen_listings.items()
            if isinstance(obj, dict) and "timestamp" in obj and datetime.strptime(obj["timestamp"], "%Y-%m-%dT%H:%M:%SZ") > cutoff
        }

        # 💾 Save full history to listing_history.json
        try:
            os.makedirs(os.path.dirname(LISTING_HISTORY_FILE), exist_ok=True)
            with open(LISTING_HISTORY_FILE, "w") as f:
                json.dump(seen_listings, f, indent=2)
            print(f"💾 Updated listing_history.json")
        except Exception as e:
            print(f"❌ Failed to write history file: {e}")

        # 🚀 Export to frontend listings.json
        try:
            listings_to_export = list(seen_listings.values())
            os.makedirs(os.path.dirname(EXPORT_JSON_PATH), exist_ok=True)
            with open(EXPORT_JSON_PATH, "w") as f:
                json.dump(listings_to_export, f, indent=2)
            print(f"📤 Synced {len(listings_to_export)} listings to frontend")
        except Exception as e:
            print(f"❌ Failed to export to frontend: {e}")

        await browser.close()
        print("✅ Scan complete.\n")

# === Run Loop ===
async def main():
    while True:
        await fetch_kijiji_listings()
        print(f"🕓 Waiting {REFRESH_INTERVAL} seconds before next scan...\n")
        await asyncio.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())