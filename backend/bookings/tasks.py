
from celery import shared_task
from .models import BookingRequest, UserCredential
from .utils import decrypt_password
from .selenium_logic import book_via_foreup_software, book_via_foreup_new, book_cps_golf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback
import os

@shared_task
def execute_booking(request_id):
    # 1. Load Request
    try:
        booking = BookingRequest.objects.get(id=request_id)
    except BookingRequest.DoesNotExist:
        return "Request not found"

    # 2. Load Credentials
    try:
        creds = UserCredential.objects.get(user=booking.user, course=booking.course)
        password = decrypt_password(creds.encrypted_password)
        email = creds.course_email
    except UserCredential.DoesNotExist:
        booking.status = 'FAILED'
        booking.result_log = "Missing credentials"
        booking.save()
        return

    # 3. Setup Driver
    chrome_options = Options()
    # In Docker, we usually want these optimizations
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Check if we are running in Docker with a remote Selenium container
    selenium_host = os.getenv('SELENIUM_HOST')
    
    try:
        if selenium_host:
            # Connect to the standalone chrome container
            driver = webdriver.Remote(
                command_executor=f'{selenium_host}/wd/hub',
                options=chrome_options
            )
        else:
            # Run locally
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
        driver.implicitly_wait(10)
        driver.maximize_window()

        booking.status = 'RUNNING'
        booking.save()
        
        logic = booking.course.logic_type
        url = booking.course.url
        xpath = booking.course.public_btn_xpath
        
        result = ""
        
        if logic == 'foreup':
            result = book_via_foreup_software(driver, url, xpath, booking, email, password)
        elif logic == 'foreup_new':
            result = book_via_foreup_new(driver, url, xpath, booking, email, password)
        elif logic == 'cps':
            result = book_cps_golf(driver, url, booking, email, password)
        elif logic == 'frear':
            # Implement frear logic call
            pass
        else:
            raise Exception("Unknown logic type")

        booking.status = 'SUCCESS'
        booking.result_log = result
        
    except Exception as e:
        booking.status = 'FAILED'
        booking.result_log = f"{str(e)}\n{traceback.format_exc()}"
        
    finally:
        booking.save()
        if 'driver' in locals():
            driver.quit()
