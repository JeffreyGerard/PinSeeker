import sys
from playwright.sync_api import sync_playwright
import time
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    page = context.new_page()
    page.goto('https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')
    page.wait_for_load_state('networkidle')
    time.sleep(3)
    
    # Login
    page.get_by_role("button", name="Sign In").click()
    time.sleep(2)
    email_field = page.get_by_role("textbox", name="Email")
    email_field.type('jeff.gerard05@gmail.com', delay=50)
    page.keyboard.press("Tab")
    page.get_by_role("button", name="NEXT").click()
    time.sleep(2)
    password_field = page.get_by_role("textbox", name="Password")
    password_field.type('Password101', delay=50)
    page.keyboard.press("Tab")
    page.get_by_role("button", name="SIGN IN", exact=True).evaluate("el => el.click()")
    time.sleep(5)
    
    # Click tomorrow's day
    day_str = str(20) # April 20
    page.get_by_text(day_str, exact=True).first.click(force=True)
    time.sleep(5)
    
    # Expand
    for btn_name in ["Show more Morning tee times", "Show more Mid Day tee times"]:
        try:
            page.get_by_role("button", name=btn_name).click(timeout=3000)
            time.sleep(1)
        except: pass

    print('--- Dumping All Button Text ---')
    btns = page.locator('button').all()
    for b in btns:
        txt = b.inner_text().strip().replace('\n', ' ')
        if txt:
            print(f"Button: [{txt}]")
            
    browser.close()