import sys
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    page.goto('https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')
    page.wait_for_load_state('networkidle')
    time.sleep(3)
    
    page.locator('button:has-text("Sign In"), mat-toolbar button:has(mat-icon)').first.click()
    time.sleep(2)
    page.get_by_placeholder('Email').or_(page.locator('input[type="email"]')).first.fill('jeff.gerard05@gmail.com')
    page.locator('button:has-text("Next"), button[type="submit"]').first.click()
    time.sleep(2)
    page.get_by_placeholder('Password', exact=True).or_(page.locator('input[type="password"]')).first.fill('Password101')
    btn = page.locator('button[type="submit"], button:has-text("Sign In")').filter(has_text='Sign In').first
    btn.evaluate('el => el.click()')
    time.sleep(5)
    
    print(f"Current URL: {page.url}")
    
    # Save a screenshot and the HTML content
    page.screenshot(path='C:/Users/jeffg/.gemini/tmp/jeffg/capital_hills_after_login.png')
    with open('C:/Users/jeffg/.gemini/tmp/jeffg/capital_hills_source.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    print("Saved screenshot and HTML to temp directory.")
    browser.close()