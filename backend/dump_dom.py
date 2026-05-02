import os
from playwright.sync_api import sync_playwright

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={'width': 1920, 'height': 1080},
        timezone_id='America/New_York'
    )
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page = context.new_page()
    page.goto('https://foreupsoftware.com/index.php/booking/19530/1791#teetimes')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)
    
    html = page.content()
    with open('/app/screenshots/dom_stealth.html', 'w', encoding='utf-8') as f:
        f.write(html)
    browser.close()
