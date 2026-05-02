import sys
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    page.goto('https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23')
    page.wait_for_load_state('networkidle')
    time.sleep(3)
    
    # Login
    page.locator('button:has-text("Sign In"), mat-toolbar button:has(mat-icon)').first.click()
    time.sleep(2)
    email_field = page.get_by_placeholder("Email").or_(page.locator("input[type='email']")).first
    email_field.click()
    email_field.type('jeff.gerard05@gmail.com', delay=50)
    page.keyboard.press("Tab")
    time.sleep(1)
    page.locator('button:has-text("Next"), button[type="submit"]').first.click()
    
    password_field = page.get_by_placeholder("Password", exact=True).or_(page.locator("input[type='password']")).first
    password_field.wait_for(state="visible", timeout=10000)
    password_field.click()
    password_field.type('Password101', delay=50)
    page.keyboard.press("Tab")
    time.sleep(1)
    
    btn = page.locator('button[type="submit"], button:has-text("Sign In")').filter(has_text='Sign In').first
    btn.evaluate('el => el.click()')
    time.sleep(5)
    
    # Click 22nd day
    try:
        for _ in range(12):
            day_el = page.locator(".day-background-upper, .btn-day-unit").filter(has_text='22').first
            if day_el.is_visible(timeout=2000):
                day_el.click(force=True)
                time.sleep(5)
                break
            page.locator("button:has(mat-icon:has-text('chevron_right'))").first.click(force=True)
            time.sleep(2)
    except Exception as e:
        print(f"Calendar navigation failed: {e}")
        
    print('--- Checking Player Elements ---')
    toggles = page.locator('mat-button-toggle, .mat-button-toggle-label-content, button').all()
    print(f'Found {len(toggles)} possible buttons/toggles')
    for t in toggles[:50]:
        print(f"Element: {t.inner_text().strip()} | Classes: {t.get_attribute('class')}")
    browser.close()