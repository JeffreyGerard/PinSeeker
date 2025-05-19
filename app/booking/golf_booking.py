from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time

def book_via_foreup_software(url, public_btn_xpath, date, earliest_time, latest_time, players, email, password):
    # Specify the path to chromedriver.exe
    service = Service(r"C:\Users\jeffg\Projects\PinSeeker\chromedriver.exe")
    wb = wd.Chrome(service=service)
    wb.implicitly_wait(10)
    wb.maximize_window()
    wb.get(url)

    # Login
    wb.find_element(By.XPATH, '//*[@id="bs-example-navbar-collapse-1"]/ul[2]/li/a').click()
    wb.find_element(By.XPATH, '//*[@id="login_email"]').send_keys(email)
    wb.find_element(By.XPATH, '//*[@id="login_password"]').send_keys(password)
    wb.find_element(By.XPATH, '//*[@id="login"]/div/div[3]/div[1]/button[1]').click()

    # Click Public Button
    wb.find_element(By.XPATH, public_btn_xpath).click()

    # Select Day
    wb.find_element(By.XPATH, '//*[@id="date-field"]').send_keys(Keys.CONTROL + "a")
    wb.find_element(By.XPATH, '//*[@id="date-field"]').send_keys(Keys.DELETE)
    wb.find_element(By.XPATH, '//*[@id="date-field"]').send_keys(date)
    wb.find_element(By.XPATH, '//*[@id="date-field"]').send_keys(Keys.RETURN)

    # Select Player Count
    wb.find_element(By.XPATH, f'//*[@id="nav"]/div/div[3]/div/div/a[{players}]').click()

    # Select 18 Holes
    wb.find_element(By.XPATH, '//*[@id="nav"]/div/div[4]/div[2]/div/a[2]').click()

    # Get Available Tee Time
    earliest_date = datetime.strptime(f"{date} {earliest_time}", '%m-%d-%Y %I:%M%p')
    latest_date = datetime.strptime(f"{date} {latest_time}", '%m-%d-%Y %I:%M%p')
    available_tee_times = wb.find_elements(By.CLASS_NAME, "booking-start-time-label")
    for tee_time in available_tee_times:
        available_date = datetime.strptime(f"{date} {tee_time.text}", '%m-%d-%Y %I:%M%p')
        if earliest_date <= available_date <= latest_date:
            booking_time = available_date.strftime("%#I:%M%p").lower()
            break
    else:
        wb.quit()
        return "No available tee times in the specified range."

    # Select Tee Time
    wb.find_element(By.XPATH, f"//*[contains(text(),'{booking_time}')]").click()

    # Select Cart
    try:
        wb.find_element(By.XPATH, '//*[@id="book_time"]/div/div[2]/div[5]/div[2]/div/a[2]').click()
    except:
        pass

    # Book Time
    wb.find_element(By.XPATH, '//*[@id="book_time"]/div/div[3]/button[1]').click()

    # Re-login if required
    wb.find_element(By.XPATH, '//*[@id="login_email"]').send_keys(email)
    wb.find_element(By.XPATH, '//*[@id="login_password"]').send_keys(password)
    wb.find_element(By.XPATH, '/html/body/div[3]/div/div/div[3]/div[1]/button[1]').click()

    # Continue
    wb.find_element(By.XPATH, '//*[@id="player-name-entry"]/div/div[3]/div/button').click()
    wb.quit()
    return f"Success! Tee Time: {date} {booking_time} Players: {players}."


def book_via_foreup_software_new(url, public_btn_xpath, date, earliest_time, latest_time, players, email, password):
   
   # Target date
    target_date = datetime.date(2025, 5, 22)
    target_day = str(target_date.day)
   
   # Specify the path to chromedriver.exe
    service = Service(r"C:\Users\jeffg\Projects\PinSeeker\chromedriver.exe")
    wb = wd.Chrome(service=service)
    wb.implicitly_wait(10)
    wb.maximize_window()    

    # Enter Website
    wb.get(url)

    # Login 
    wb.find_element(By.XPATH, '//*[@id="bs-example-navbar-collapse-1"]/ul[2]/li/a').click()
    wb.find_element(By.XPATH, '//*[@id="login_email"]').send_keys(email)
    wb.find_element(By.XPATH, '//*[@id="login_password"]').send_keys(password)
    wb.find_element(By.XPATH, '//*[@id="login"]/div/div[3]/div[1]/button[1]').click()

    # Click Public Button
    public_18holes_btn = wb.find_element(By.XPATH, public_btn_xpath).click()

    # Select Day on Calendar
    available_days = wb.find_elements(By.CLASS_NAME, "day")
    for available_day in available_days: 
        if available_day.text == desired_day.split("-")[1] and (available_day.get_attribute("class") == "active day"
                                            or available_day.get_attribute("class") == "day"
                                            or available_day.get_attribute("class") == "new day"):                                         
            available_day.click()                                
            break
    
    # Select Players
    time.sleep(5)            
    wb.find_element(By.XPATH, '//*[@id="nav"]/div/div[4]/div/div[1]/a[4]').click()
    
    # Select 18 Holes
    time.sleep(5)            
    wb.find_element(By.XPATH, '//*[@id="nav"]/div/div[4]/div/div[2]/a[2]').click()
    
    # Get Available Tee Time from Range
    earliest_desired_date = datetime.strptime(desired_day + " " + earliest_desired_time, '%m-%d-%Y %I:%M%p')
    latest_desired_date = datetime.strptime(desired_day + " " + latest_desired_time, '%m-%d-%Y %I:%M%p')
    available_tee_times = wb.find_elements(By.CLASS_NAME, "times-booking-start-time-label")
    for available_tee_time in available_tee_times: 
        available_date = datetime.strptime(desired_day + " " + available_tee_time.text, '%m-%d-%Y %I:%M%p')
        if earliest_desired_date <= available_date and available_date <= latest_desired_date:            
            booking_time = available_date.strftime("%#I:%M%p")
            booking_time = booking_time.lower()
            break

    # Select Tee Time
    wb.find_element(By.XPATH, f"//*[contains(text(),'{booking_time}')]").click()
    time.sleep(2)
    # Select Holes
    wb.find_element(By.XPATH, f'//label[@for="holes-eighteen"]').click()    
    time.sleep(2)
    # Select Players
    match players:
        case "1":
            players_string = "one"
        case "2":
            players_string = "two"
        case "3":
            players_string = "three"
        case "4":
            players_string = "four"        
            
    wb.find_element(By.XPATH, f'//label[@for="players-four"]').click()    

    # Select Cart
    wb.find_element(By.XPATH, f'//label[@for="cart-yes"]').click()    

    # Select Book Tee Time
    wb.find_element(By.XPATH, '//*[@id="content"]/div/section/div[2]/section/button').click()

def book_tee_time(date, earliest_time, latest_time, players, golf_course, email, password):
    courses = {
        "Capital Hills": {
            "func": lambda: "Not implemented",
            "url": "https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23"
        },
        "Eagle Crest": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/21756#/teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button[1]'
        },
        "Fairways of Halfmoon": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/21756#/teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button'
        },
        "Frear Park Municipal Golf Course": {
            "func": lambda: "Not implemented",
            "url": "https://secure.east.prophetservices.com/FrearParkV3/(S(13kebkre22enx3l3kh5xqh2p))/Home/nIndex?CourseId=1,2&Date=2024-6-28&Time=AnyTime&Player=4&Hole=18"
        },
        "Orchard Creek": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/19530/1791#teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button[5]'
        },
        "Schenectady Muni Golf Course": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/20480/4739#/teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button[1]'
        },
        "Stadium Golf Course": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/index/3332#/teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button[1]'
        },
        "Van Patten Golf Course": {
            "func": book_via_foreup_software,
            "url": "https://foreupsoftware.com/index.php/booking/index/19324#/teetimes",
            "public_btn_xpath": '//*[@id="content"]/div/button[1]'
        }
    }

    course = courses.get(golf_course)
    if not course:
        return "Invalid golf course selected."

    return course["func"](course["url"], course["public_btn_xpath"], date, earliest_time, latest_time, players, email, password)