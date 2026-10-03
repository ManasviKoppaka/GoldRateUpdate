from playwright.sync_api import sync_playwright

URL = "https://goldprice.org/gold-price-usa.html"



import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_email(subject, body):
    msg = EmailMessage()
    msg["From"] = os.getenv("GMAIL_ADDRESS")
    msg["To"] = os.getenv("GMAIL_ADDRESS")
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            os.getenv("GMAIL_ADDRESS"),
            os.getenv("GMAIL_APP_PASSWORD")
        )
        smtp.send_message(msg)


def get_gold_price():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Wait for the gold price to load
        page.wait_for_function("""
            () => {
                const text = document.body.innerText;
                const lines = text.split('\\n')
                    .map(x => x.trim())
                    .filter(Boolean);

                const index = lines.indexOf("HOLDINGS");

                if (index === -1 || !lines[index + 1]) {
                    return false;
                }

                return lines[index + 1] !== "Loading...";
            }
        """, timeout=30000)

        text = page.locator("body").inner_text()

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        index = lines.index("HOLDINGS")

        price_text = lines[index + 1]

        price = float(price_text.replace(",", ""))

        browser.close()

        return price


def check_gold_price():
    price = get_gold_price()

    print(f"Current gold price: ${price:,.2f}")

    if price < 4000:
        send_email(
            "🚨 Gold Price Alert",
            f"Gold has dropped below $4,000!\n\n"
            f"Current gold price: ${price:,.2f}"
        )

        print("🚨 ALERT EMAIL SENT!")

    else:
        print("Gold is still above $4,000.")


check_gold_price()