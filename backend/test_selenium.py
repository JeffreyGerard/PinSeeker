import os
import django
import sys
from datetime import date, time, datetime, timedelta
from selenium import webdriver as wd 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time as pytime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
django.setup()

from bookings.models import GolfCourse, UserCredential
from bookings.utils import decrypt_password

def book_Capital_Hills(desired_day, earliest_desired_time, latest_desired_time, players, email, password):
    wb = wd.Chrome()    
    wb.implicitly_wait(10)
    wb.maximize_window()
    wait = WebDriverWait(wb, 20)

    wb.get("https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23")
    pytime.sleep(3)

    # Login 
    try:
        login_btn = wb.find_elements(By.XPATH, "//button[contains(., 'Sign In') or .//mat-icon]")
        if login_btn:
            login_btn[0].click()
        else:
            wb.find_element(By.XPATH, "/html/body/app-root/app-full-layout/div/mat-toolbar/app-header/button").click()
    except Exception as e:
        print(f"Login icon click error: {e}")
        
    pytime.sleep(2)
    wb.find_element(By.CSS_SELECTOR, 'input[type="email"]').send_keys(email)
    wb.find_element(By.XPATH, "//button[contains(., 'Next') or @type='submit']").click()
    pytime.sleep(2)
    wb.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(password)
    wb.find_element(By.XPATH, "//button[contains(., 'Sign In') or @type='submit']").click()
    pytime.sleep(5)

    # Select Date
    available_days = wb.find_elements(By.CSS_SELECTOR, ".day-background-upper.is-visible:not(.is-disabled), .btn-day-unit")
    day_clicked = False
    
    target_day = desired_day.split("-")[1].lstrip('0') # Remove leading zero (e.g. '05' -> '5')
    
    for day in available_days:
        if day.text.strip() == target_day:
            day.click()        
            pytime.sleep(3)
            day_clicked = True
            break 
            
    if not day_clicked:
         wb.quit()
         return "Failed to find day on calendar."

    # Select Players
    player_buttons = wb.find_elements(By.CLASS_NAME, "mat-button-toggle-label-content")
    for player_button in player_buttons:
        if player_button.text.strip() == str(players):
            player_button.click()
            pytime.sleep(3)
            break    

    # Select 18 Holes
    try:
        wb.find_element(By.TAG_NAME, 'mat-select').click()
        pytime.sleep(2)
        wb.find_element(By.XPATH, "//mat-option[contains(., '18 Holes')]").click()
    except Exception as e: 
        print(f"Skipped 18 hole selection: {e}")

    # Get available tee times
    earliest_desired_date = datetime.strptime(desired_day + " " + earliest_desired_time, '%m-%d-%Y %I:%M%p')
    latest_desired_date = datetime.strptime(desired_day + " " + latest_desired_time, '%m-%d-%Y %I:%M%p')
    
    pytime.sleep(5)
    available_tee_times = wb.find_elements(By.CLASS_NAME, "teetimetableDateTime")
    
    booking_time = None
    for available_tee_time in available_tee_times: 
        text = available_tee_time.text.strip()
        if not text: continue
        available_date = datetime.strptime(desired_day + " " + text, '%m-%d-%Y %I:%M %p')
        if earliest_desired_date <= available_date and available_date <= latest_desired_date:            
            booking_time = available_date.strftime("%#I:%M %p")        
            break

    if not booking_time:
         wb.quit()
         return "No available tee times in range."

    # DRY RUN: Don't click the tee time to avoid actual booking
    # wb.find_element(By.XPATH, f"//*[contains(text(),'{booking_time}')]").click()
    
    wb.quit()
    return f"Dry Run Success! Found tee time for {booking_time}"

if __name__ == "__main__":
    try:
        course = GolfCourse.objects.get(name="Capital Hills")
        cred = UserCredential.objects.filter(course=course).first()
        email = cred.course_email
        password = decrypt_password(cred.encrypted_password)
        
        # Test for tomorrow to ensure the calendar day is visible
        tomorrow = datetime.now() + timedelta(days=1)
        test_date_str = tomorrow.strftime("%m-%d-%Y")
        
        print("Running Selenium fallback test for Capital Hills...")
        print(f"Date: {test_date_str}, Time: 8:00AM - 5:00PM (Broad range to ensure match)")
        result = book_Capital_Hills(test_date_str, "08:00AM", "05:00PM", 4, email, password)
        print(f"\nRESULT: {result}")
    except Exception as e:
        print(f"Error: {e}")
