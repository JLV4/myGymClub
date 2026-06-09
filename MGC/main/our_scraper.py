from playwright.sync_api import sync_playwright
import time, db
from constants import TARGET_URL, DAYS_TO_SEARCH, SCRAPER_WAIT_TIME_SECONDS
from datetime import datetime, timedelta

def add_months_event():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./chrome_profile",
            channel="chrome",
            headless=False,
            viewport={"width": 1980, "height": 1200},
        )

        page = context.new_page()
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("networkidle")

        next_button = page.locator("#dailyContainer button.nav-button:has(i.fa-chevron-right)").first

        base_dt = datetime.now()

        for day in range(DAYS_TO_SEARCH):
            page.wait_for_load_state("networkidle")
            time.sleep(SCRAPER_WAIT_TIME_SECONDS)

            current_dt = base_dt + timedelta(days=day)

            sql_date = current_dt.strftime("%Y-%m-%d")

            even_rows = page.locator(".evenRows").all()
            odd_rows = page.locator(".oddRows").all()

            rows = even_rows + odd_rows
            row_count = len(rows)

            if row_count != 0:
                for i in range(row_count):
                    row = rows[i]
                    cells = row.locator("td")

                    try:
                        if cells.count() != 5:
                            continue

                        start_time = cells.nth(0).inner_text().strip()
                        end_time = cells.nth(1).inner_text().strip()
                        event_name = cells.nth(3).inner_text().strip()
                        location = cells.nth(4).inner_text().strip()

                        if not start_time or not end_time or not event_name or not location:
                            continue

                        db.add_rec_event(
                            event_name,
                            "UIC REC",
                            sql_date,
                            start_time,
                            end_time,
                            "An event pulled from the UIC REC landing page.",
                            location
                        )

                    except Exception:
                        continue

            if day < DAYS_TO_SEARCH - 1:
                next_button.wait_for(state="visible", timeout=10000)
                next_button.click()

        context.close()
