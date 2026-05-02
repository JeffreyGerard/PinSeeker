import sys
from playwright.sync_api import sync_playwright
import time
import re

# Credentials from user
EMAIL = 'jeff.gerard05@gmail.com'
PASS = 'Password101'

def check_cps():
    print("\n--- Checking Capital Hills Reservations ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page.goto('https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')
        page.wait_for_load_state("networkidle")
        
        # Login
        page.get_by_role("button", name="Sign In").click()
        page.get_by_role("textbox", name="Email").type(EMAIL, delay=50)
        page.keyboard.press("Tab")
        page.get_by_role("button", name="NEXT").click()
        page.get_by_role("textbox", name="Password").type(PASS, delay=50)
        page.keyboard.press("Tab")
        page.get_by_role("button", name="SIGN IN", exact=True).evaluate("el => el.click()")
        time.sleep(5)
        
        # Go to My Account / Reservations
        page.get_by_role("button", name="My Account").or_(page.get_by_text("My Account")).first.click()
        time.sleep(2)
        page.get_by_role("menuitem", name="My Reservations").or_(page.get_by_text("My Reservations")).first.click()
        time.sleep(5)
        
        print("Page Content Snippet (Reservations):")
        print(page.inner_text("body")[:1000])
        page.screenshot(path='C:/Users/jeffg/.gemini/tmp/jeffg/cps_reservations.png')
        browser.close()

def check_orchard():
    print("\n--- Checking Orchard Creek Reservations ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page.goto('https://foreupsoftware.com/index.php/booking/19530/1791#teetimes')
        page.wait_for_load_state("networkidle")
        
        # Login
        login_btn = page.locator("a:has-text('Login'), a:has-text('Log In'), .login").first
        login_btn.click()
        time.sleep(2)
        page.locator("#login_email").fill(EMAIL)
        page.locator("#login_password").fill(PASS)
        page.locator("button:has-text('Log In'), button:has-text('Login')").first.click()
        time.sleep(5)
        
        # Go to My Reservations
        # ForeUp usually has a sidebar or account menu
        page.locator("a:has-text('Reservations')").first.click()
        time.sleep(5)
        
        print("Page Content Snippet (Reservations):")
        print(page.inner_text("body")[:1000])
        page.screenshot(path='C:/Users/jeffg/.gemini/tmp/jeffg/orchard_reservations.png')
        browser.close()

if __name__ == "__main__":
    try:
        check_cps()
    except Exception as e: print(f"CPS Check Failed: {e}")
    try:
        check_orchard()
    except Exception as e: print(f"Orchard Check Failed: {e}")
