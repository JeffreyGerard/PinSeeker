from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
from datetime import datetime
import time
import re
import logging
import os

# --- Constants & Setup ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
SCREENSHOT_DIR = 'screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_time(date_obj, time_obj):
    """Combine a date object and a time object into a datetime object."""
    return datetime.combine(date_obj, time_obj)


def _new_stealth_context(p, headless=True):
    """Launch a Chromium context with anti-bot flags."""
    browser = p.chromium.launch(
        headless=headless,
        args=['--disable-blink-features=AutomationControlled'],
    )
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={'width': 1920, 'height': 1080},
        timezone_id='America/New_York'
    )
    return browser, context

# ---------------------------------------------------------------------------
# CPS Golf (Capital Hills / Old Post Road)
# ---------------------------------------------------------------------------

def book_cps_golf(url, booking, email, password, dry_run=False, headless=True):
    """Verified flow for CPS Golf sites."""
    with Stealth().use_sync(sync_playwright()) as p:
        browser, context = _new_stealth_context(p, headless=headless)
        page = context.new_page()
        try:
            logging.info("Navigating to CPS Golf URL: %s", url)
            page.goto(url, wait_until='networkidle')

            # --- Auth ---
            logging.info("Starting authentication.")
            page.get_by_role('button', name='Sign In').click()

            email_field = page.get_by_role('textbox', name='Email', exact=True)
            email_field.wait_for(state='visible', timeout=10000)
            email_field.type(email, delay=60)
            page.keyboard.press('Tab')

            page.get_by_role('button', name='NEXT').click()

            pass_field = page.get_by_role('textbox', name='Password', exact=True)
            pass_field.wait_for(state='visible', timeout=10000)
            pass_field.type(password, delay=60)
            page.keyboard.press('Tab')
            
            page.get_by_role('button', name='SIGN IN', exact=True).click()
            logging.info("Sign-in button clicked. Waiting for navigation.")
            page.wait_for_load_state('networkidle', timeout=30000)

            # --- Navigate date with arrow buttons ---
            logging.info("Navigating to target date: %s", booking.desired_date)
            today = datetime.today().date()
            delta = (booking.desired_date - today).days

            if delta != 0:
                arrow_selector = "button:has(mat-icon:text('navigate_next'))" if delta > 0 else "button:has(mat-icon:text('navigate_before'))"
                for i in range(abs(delta)):
                    logging.info(f"Clicking date arrow, attempt {i+1}/{abs(delta)}")
                    page.locator(arrow_selector).first.click()
                    page.wait_for_timeout(1500) # Wait for UI to update

            # --- Players ---
            logging.info("Selecting %d players.", booking.players)
            page.wait_for_timeout(1000)
            page.locator('.mat-button-toggle-label-content').filter(
                has_text=str(booking.players)
            ).first.click(force=True)
            page.wait_for_timeout(2000)

            # --- Expand all time sections ---
            logging.info("Expanding all tee time sections.")
            for label in [
                'Show more Morning tee times', 'Show more Mid Day tee times',
                'Show more Late Day tee times', 'Show more Evening tee times',
            ]:
                try:
                    page.get_by_role('button', name=label).click(timeout=1000)
                except PlaywrightTimeoutError:
                    pass

            # --- Find tee time in window ---
            logging.info("Searching for tee time between %s and %s.", booking.earliest_time, booking.latest_time)
            earliest = parse_time(booking.desired_date, booking.earliest_time)
            latest = parse_time(booking.desired_date, booking.latest_time)
            
            all_buttons = page.locator('button:has(.tee-time-value)').all()
            booking_element = None
            best_time_str = ''

            for btn in all_buttons:
                txt = btn.inner_text().strip()
                m = re.search(r'(\d{1,2}:\d{2})\s*(A|P)\s*M', txt, re.IGNORECASE)
                if m:
                    ts = f"{m.group(1)}{m.group(2)}M".upper()
                    try:
                        avail = datetime.strptime(f"{booking.desired_date.strftime('%Y-%m-%d')} {ts}", '%Y-%m-%d %I:%M%p')
                        if earliest <= avail <= latest:
                            booking_element = btn
                            best_time_str = ts
                            logging.info("Found matching tee time: %s", best_time_str)
                            break
                    except ValueError:
                        continue

            if not booking_element:
                raise Exception(f'No tee time found between {booking.earliest_time} and {booking.latest_time}')

            if dry_run:
                return f'Dry run success at {best_time_str}'

            # --- Book ---
            logging.info("Attempting to book tee time: %s", best_time_str)
            booking_element.click(force=True)
            page.wait_for_load_state('networkidle')

            for i in range(3):
                try:
                    confirm_btn = page.locator('button').filter(
                        has_text=re.compile(r'Continue|Confirm|Finalize|Reservation', re.I)
                    ).first
                    confirm_btn.wait_for(state='visible', timeout=5000)
                    logging.info("Clicking confirmation button: %s", (confirm_btn.inner_text()))
                    confirm_btn.click()
                    page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeoutError:
                    logging.info("No more confirmation buttons found or timed out.")
                    break
            
            logging.info("Booking process completed.")
            return f'Success! Booked {best_time_str}'

        except Exception as e:
            logging.error("An error occurred in book_cps_golf: %s", e, exc_info=True)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'cps_golf_error.png'))
            raise
        finally:
            browser.close()

def book_cps_old_post(url, booking, email, password, dry_run=False, headless=True):
    return book_cps_golf(url, booking, email, password, dry_run=dry_run, headless=headless)

# ---------------------------------------------------------------------------
# ForeUp
# ---------------------------------------------------------------------------

def book_via_foreup_software(url, booking, email, password, dry_run=False, headless=True):
    """Verified flow for ForeUp sites."""
    with Stealth().use_sync(sync_playwright()) as p:
        browser, context = _new_stealth_context(p, headless=headless)
        page = context.new_page()
        try:
            logging.info("Navigating to ForeUp URL: %s", url)
            page.goto(url, wait_until='networkidle', timeout=60000)

            # --- Booking class: click Public as GUEST (before login) ---
            try:
                logging.info("Trying to select 'Public' booking class.")
                page.locator('button, a, div').filter(
                    has_text=re.compile(r'^\s*Public.*$', re.IGNORECASE)
                ).first.click(timeout=8000)
                page.wait_for_load_state('networkidle')
            except PlaywrightTimeoutError:
                logging.warning("Could not find or click 'Public' booking class, continuing anyway.")

            # --- Navigate to target date ---
            logging.info("Navigating to target date: %s", booking.desired_date)
            target = booking.desired_date
            today = datetime.today().date()
            months_ahead = (target.year - today.year) * 12 + target.month - today.month
            if months_ahead > 0:
                for _ in range(months_ahead):
                    page.locator('button.next-arrow, .fc-next-button, button[aria-label="next"]').first.click()
                    page.wait_for_timeout(1000)

            # Click the day
            day_str = str(target.day)
            day_selector = f'td[data-day="{day_str}"]:not(.disabled), .day:not(.disabled):has-text("{day_str}")'
            page.locator(day_selector).first.click()
            page.wait_for_timeout(2500)  # Explicitly wait for SPA to load new day's data

            # --- Players & Holes ---
            logging.info("Setting players to %d and holes to 18.", booking.players)
            try:
                page.locator('a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(timeout=5000)
                page.wait_for_timeout(1000)
                page.locator('button, a').filter(has_text=re.compile(r'18 Holes|18-Hole', re.I)).first.click(timeout=5000)
                page.wait_for_timeout(2000)
            except PlaywrightTimeoutError:
                logging.warning("Could not set players/holes. Assuming defaults are OK.")

            # --- Find tee time ---
            logging.info("Searching for tee time between %s and %s.", booking.earliest_time, booking.latest_time)
            earliest = parse_time(target, booking.earliest_time)
            latest = parse_time(target, booking.latest_time)
            
            slots_locator = page.locator('.booking-start-time-label, .time-summary-ob-left, .time-label')
            try:
                slots_locator.first.wait_for(state='visible', timeout=10000)
            except PlaywrightTimeoutError:
                logging.warning("No tee times appeared to load, or none exist.")

            slots = slots_locator.all()
            booking_element = None
            best_time_str = ''

            for slot in slots:
                txt = slot.inner_text().strip().lower()
                m = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', txt)
                if m:
                    ts_str = f"{m.group(1)} {m.group(2)}"
                    try:
                        avail = datetime.strptime(f"{target.strftime('%Y-%m-%d')} {ts_str}", '%Y-%m-%d %I:%M %p')
                        if earliest <= avail <= latest:
                            booking_element = slot
                            best_time_str = ts_str
                            logging.info("Found matching tee time: %s", best_time_str)
                            break
                    except ValueError:
                        continue
            
            if not booking_element:
                raise Exception(f'No tee time found between {booking.earliest_time} and {booking.latest_time}')

            if dry_run:
                return f'Dry run success at {best_time_str}'

            # --- Click time slot and handle modal ---
            logging.info("Clicking tee time slot for %s", best_time_str)
            booking_element.click()

            # Wait for modal or panel to appear
            modal_locator = page.locator('div.modal-body, div.booking-details, #booking-modal, .modal-dialog, .booking-modal').first
            modal_locator.wait_for(state='visible', timeout=15000)

            # --- Handle Login (if necessary) ---
            try:
                # Use global page selectors for login to be safe
                email_input = page.get_by_placeholder("Email").first
                pass_input = page.get_by_placeholder("Password").first
                
                if email_input.is_visible(timeout=5000):
                    logging.info("Login form detected. Logging in...")
                    email_input.fill(email)
                    pass_input.fill(password)
                    pass_input.press("Enter")
                    
                    # Wait for login to complete
                    email_input.wait_for(state='hidden', timeout=15000)
                    logging.info("Login successful, waiting for booking options...")
                    page.wait_for_timeout(4000) # Give UI time to load options
            except Exception as e:
                logging.info(f"No login required or login transition handled: {e}")

            # --- Select Booking Options ---
            # Search globally on the page as the modal might have refreshed
            logging.info("Selecting booking options (Holes, Players, Cart).")
            try:
                # Use codegen-style label selectors globally
                page.get_by_label(re.compile(r"18 Holes", re.I)).click(timeout=5000)
                page.wait_for_timeout(500)
                page.get_by_label(re.compile(rf"{booking.players} Players", re.I)).click(timeout=5000)
                page.wait_for_timeout(500)
                
                # Optional cart selection
                cart_opt = page.get_by_label(re.compile(r"Yes.*cart", re.I))
                if cart_opt.is_visible(timeout=2000):
                    cart_opt.click()
            except Exception as e:
                logging.warning(f"Could not select some options (may have used defaults): {e}")

            # --- Final Booking Confirmation ---
            logging.info("Looking for final booking confirmation button.")
            # Search globally for the button
            book_btn = page.get_by_role("button", name=re.compile(r"Book Time", re.I))
            
            # If role check fails, try text-based locator
            if not book_btn.is_visible(timeout=5000):
                book_btn = page.locator('button, a').filter(
                    has_text=re.compile(r'Book Time|Reserve|Continue|Confirm', re.I)
                ).first
            
            book_btn.wait_for(state='visible', timeout=10000)
            logging.info("Clicking final booking button: %s", book_btn.inner_text().strip())
            
            if not dry_run:
                book_btn.click()
                # Wait for final success message
                page.wait_for_timeout(5000) 
            else:
                logging.info("DRY RUN: Skipping final click.")
            
            return f'Success! Attempted booking for {best_time_str}'

            

        except Exception as e:
            logging.error("An error occurred in book_via_foreup_software: %s", e, exc_info=True)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'foreup_error.png'))
            raise
        finally:
            browser.close()


def book_via_foreup_index(url, booking_class_id, booking, email, password, dry_run=False, headless=True):
    # Inject bc param into hash
    if '#' in url:
        base, fragment = url.split('#', 1)
        sep = '&' if '?' in fragment else '?'
        url = f"{base}#{fragment}{sep}bc={booking_class_id}"
    else:
        url = f"{url}#/teetimes?bc={booking_class_id}"
    return book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)


# Convenience wrappers
def book_orchard_creek(url, booking, email, password, dry_run=False, headless=True):
    return book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

def book_schenectady_muni(url, booking, email, password, dry_run=False, headless=True):
    return book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

def book_fairways_halfmoon(url, booking, email, password, dry_run=False, headless=True):
    return book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

def book_stadium(url, booking, email, password, dry_run=False, headless=True):
    return book_via_foreup_index(url, booking_class_id=14558, booking=booking, email=email, password=password, dry_run=dry_run, headless=headless)

def book_van_patten(url, booking, email, password, dry_run=False, headless=True):
    return book_via_foreup_index(url, booking_class_id=None, booking=booking, email=email, password=password, dry_run=dry_run, headless=headless)

# ---------------------------------------------------------------------------
# Eagle Crest (Eagle Club Systems)
# ---------------------------------------------------------------------------

def book_via_eagleclub(url, booking, email, password, card_number=None, card_exp_month=None, card_exp_year=None, card_cvv=None, dry_run=False, headless=True):
    """Books a tee time through Eagle Club Systems."""
    with Stealth().use_sync(sync_playwright()) as p:
        browser, context = _new_stealth_context(p, headless=headless)
        page = context.new_page()
        try:
            logging.info("Navigating to Eagle Club URL: %s", url)
            page.goto(url, wait_until='networkidle')

            # --- Login ---
            try:
                logging.info("Attempting to log in.")
                page.get_by_text('Login', exact=True).first.click(timeout=5000)
                page.get_by_placeholder('Email').type(email, delay=50)
                page.get_by_placeholder('Password').type(password, delay=50)
                page.locator('button:has-text("Login")').first.click()
                page.wait_for_load_state('networkidle', timeout=15000)
            except PlaywrightTimeoutError as e:
                logging.warning("Login failed or not required: %s", e)

            # --- Select date, players ---
            target = booking.desired_date
            logging.info("Selecting date: %s", target)
            page.locator('a, div, span').filter(has_text=re.compile(rf'{target.strftime("%a")}.*{target.day}', re.I)).first.click()
            page.wait_for_timeout(2500)
            
            logging.info("Selecting players: %d", booking.players)
            page.locator('a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click()
            page.wait_for_timeout(2000)

            # --- Find and click tee time tile ---
            logging.info("Searching for tee time tile.")
            earliest = parse_time(target, booking.earliest_time)
            latest = parse_time(target, booking.latest_time)
            
            tiles = page.locator('.tee-time-tile, .card, [class*="time"]').all()
            booking_tile = None
            best_time_str = ''

            for tile in tiles:
                txt = tile.inner_text().strip()
                m = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', txt, re.IGNORECASE)
                if m:
                    ts_str = f"{m.group(1)} {m.group(2)}"
                    avail = datetime.strptime(f"{target.strftime('%Y-%m-%d')} {ts_str}", '%Y-%m-%d %I:%M %p')
                    if earliest <= avail <= latest:
                        booking_tile = tile
                        best_time_str = ts_str
                        logging.info("Found matching tee time: %s", best_time_str)
                        break

            if not booking_tile:
                raise Exception('No Eagle Crest tee time found')
            
            if dry_run:
                return f'Dry run success at {best_time_str} (Eagle Crest)'

            booking_tile.click()
            
            # --- Reservation modal ---
            logging.info("Handling reservation modal.")
            modal = page.locator('.modal-dialog').first
            modal.wait_for(state='visible', timeout=10000)
            
            try:
                modal.locator('button, label').filter(has_text=re.compile(r'^18$')).first.click(timeout=2000)
                modal.locator('button, label').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(timeout=2000)
                modal.locator('button, label').filter(has_text=re.compile(r'^YES$', re.I)).first.click(timeout=2000)
                modal.locator('input[type="checkbox"]').first.check()
            except PlaywrightTimeoutError:
                logging.info("Could not select all options in modal, continuing.")

            modal.locator('button:has-text("Continue")').first.click()

            # --- Credit Card Payment ---
            if card_number and card_cvv:
                logging.info("Entering credit card information.")
                cc_frame = page.frame_locator('iframe[title="credit card form"]').first
                cc_frame.get_by_placeholder('Card Number').type(card_number)
                cc_frame.locator('input[name*="month"]').type(card_exp_month or '07')
                cc_frame.locator('input[name*="year"]').type(card_exp_year or '26')
                cc_frame.get_by_placeholder('CVV').type(card_cvv)
                page.locator('button:has-text("Pre-Authorize Now")').first.click()
                page.wait_for_timeout(10000)

            page.locator('button:has-text("OK")').first.click()
            page.wait_for_timeout(3000)

            return f'Success! Booked Eagle Crest {best_time_str}'

        except Exception as e:
            logging.error("An error occurred in book_via_eagleclub: %s", e, exc_info=True)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'eagleclub_error.png'))
            raise
        finally:
            browser.close()
