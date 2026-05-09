from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from datetime import datetime
import time
import re

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_time(date_obj, time_obj):
    return datetime.combine(date_obj, time_obj)


def _new_stealth_context(p, headless=False):
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

def apply_stealth(page):
    stealth_sync(page)


def robust_click(page, selector, timeout=10000):
    try:
        el = page.locator(selector).first
        el.wait_for(state='visible', timeout=timeout)
        el.scroll_into_view_if_needed()
        el.click(force=True)
        return True
    except Exception:
        try:
            page.locator(selector).first.evaluate('el => el.click()')
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# CPS Golf (Capital Hills / Old Post Road)
# VERIFIED 2026-04-25: slow-type email → NEXT → slow-type password → SIGN IN
# Forward-arrow date navigation (not calendar picker).
# ---------------------------------------------------------------------------

def book_cps_golf(url, booking, email, password, dry_run=False):
    """
    Verified flow for CPS Golf sites (Capital Hills, Old Post Road).

    Key findings from live session (2026-04-25):
    - Email field requires .type(..., delay=50) to pass Angular validation.
    - Tab key after typing is required before NEXT becomes enabled.
    - Date navigation uses the '<' / '>' arrow buttons, NOT a date picker.
    - Players button group uses mat-button-toggle labels.
    - Must expand 'Show more Mid Day / Late Day tee times' sections.
    """
    with sync_playwright() as p:
        browser, context = _new_stealth_context(p, headless=False)
        page = context.new_page()
        apply_stealth(page)
        page.goto(url)
        page.wait_for_load_state('networkidle')
        time.sleep(3)

        # --- Auth ---
        page.get_by_role('button', name='Sign In').click()

        email_field = page.get_by_role('textbox', name='Email', exact=True)
        email_field.wait_for(state='visible', timeout=10000)
        email_field.type(email, delay=60)
        page.keyboard.press('Tab')
        time.sleep(1)
        page.get_by_role('button', name='NEXT').click()

        pass_field = page.get_by_role('textbox', name='Password', exact=True)
        pass_field.wait_for(state='visible', timeout=10000)
        pass_field.type(password, delay=60)
        page.keyboard.press('Tab')
        time.sleep(1)
        page.get_by_role('button', name='SIGN IN', exact=True).evaluate('el => el.click()')
        page.wait_for_load_state('networkidle')
        time.sleep(5)

        # --- Navigate date with arrow buttons ---
        target = booking.desired_date
        today = datetime.today().date()
        delta = (target - today).days

        # CPS uses Material icon buttons — accessible name varies between
        # headed and headless Chromium.  Try multiple selectors.
        def _click_date_arrow(forward=True):
            """Click the next/prev date arrow with cascading fallbacks."""
            selectors = (
                [
                    "button:has-text('navigate_next')",
                    "button:has-text('>')",
                    "button:has(mat-icon:text('navigate_next'))",
                    "button[aria-label*='next' i], button[aria-label*='forward' i]",
                    ".mat-calendar-next-button, .mat-icon-button >> nth=1",
                ] if forward else [
                    "button:has-text('navigate_before')",
                    "button:has-text('<')",
                    "button:has(mat-icon:text('navigate_before'))",
                    "button[aria-label*='prev' i], button[aria-label*='back' i]",
                    ".mat-calendar-previous-button, .mat-icon-button >> nth=0",
                ]
            )
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=2000):
                        loc.click(force=True)
                        return
                except Exception:
                    continue
            # Last resort: evaluate click on the DOM element directly
            icon_text = 'navigate_next' if forward else 'navigate_before'
            page.evaluate(f"""() => {{
                const icons = document.querySelectorAll('mat-icon, .material-icons');
                for (const el of icons) {{
                    if (el.textContent.trim() === '{icon_text}') {{
                        el.closest('button')?.click();
                        return;
                    }}
                }}
            }}""")

        for _ in range(abs(delta)):
            _click_date_arrow(forward=(delta >= 0))
            time.sleep(2)

        # --- Players ---
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.locator('.mat-button-toggle-label-content').filter(
            has_text=str(booking.players)
        ).first.click(force=True)
        time.sleep(3)

        # --- Expand all time sections ---
        for label in [
            'Show more Morning tee times',
            'Show more Mid Day tee times',
            'Show more Late Day tee times',
            'Show more Evening tee times',
        ]:
            try:
                btn = page.get_by_role('button', name=label)
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    time.sleep(1)
            except Exception:
                pass

        # --- Find tee time in window ---
        earliest = parse_time(target, booking.earliest_time)
        latest = parse_time(target, booking.latest_time)
        all_buttons = page.locator('button').all()
        booking_element = None
        best_time_str = ''

        for btn in all_buttons:
            txt = btn.inner_text().strip()
            m = re.search(r'(\d{1,2}:\d{2})\s*(A|P)\s*(M)', txt, re.IGNORECASE)
            if m:
                ts = f"{m.group(1)}{m.group(2)}{m.group(3)}".upper()
                try:
                    avail = datetime.strptime(
                        f"{target.strftime('%m-%d-%Y')} {ts}", '%m-%d-%Y %I:%M%p'
                    )
                    if earliest <= avail <= latest:
                        booking_element = btn
                        best_time_str = ts
                        break
                except ValueError:
                    continue

        if not booking_element:
            raise Exception(f'No tee time found between {booking.earliest_time} and {booking.latest_time}')

        if dry_run:
            browser.close()
            return f'Dry run success at {best_time_str}'

        # --- Book ---
        booking_element.click(force=True)
        page.wait_for_load_state('networkidle')
        time.sleep(3)

        for _ in range(3):
            try:
                btn = page.locator('button').filter(
                    has_text=re.compile(r'Continue|Confirm|Finalize|Reservation', re.I)
                ).first
                if btn.is_visible(timeout=5000):
                    btn.evaluate('el => el.click()')
                    time.sleep(3)
                    page.wait_for_load_state('networkidle')
            except Exception:
                break

        browser.close()
        return f'Success! Booked {best_time_str}'


def book_cps_old_post(url, booking, email, password, dry_run=False):
    return book_cps_golf(url, booking, email, password, dry_run=dry_run)


# ---------------------------------------------------------------------------
# ForeUp — /booking/<id>/<class_id> URLs  (Orchard Creek, Schenectady, Fairways)
# VERIFIED 2026-04-25: guest-first booking-class click bypasses bot detection.
# ---------------------------------------------------------------------------

def book_via_foreup_software(url, booking, email, password, dry_run=False):
    """
    Verified flow for ForeUp /booking/<id>/<class_id>/ sites.
    """
    with sync_playwright() as p:
        browser, context = _new_stealth_context(p, headless=False)
        page = context.new_page()
        apply_stealth(page)
        try:
            # Navigate to course
            page.goto(url)
            page.wait_for_load_state('networkidle')
            time.sleep(5)

            # --- Booking class: click Public as GUEST (before login) ---
            try:
                b_class = "Public"
                booking_classes = page.locator('button, a, div').filter(has_text=re.compile(rf'^\s*{re.escape(b_class)}.*$', re.IGNORECASE))
                booking_classes.first.wait_for(state='visible', timeout=8000)
                booking_classes.first.click(timeout=8000)
                time.sleep(3) 
            except Exception as e:
                print(f'DEBUG: booking class click failed: {e}')

            # --- Navigate to target date ---
            target = booking.desired_date
            today = datetime.today().date()
            months_ahead = (target.year - today.year) * 12 + target.month - today.month
            for _ in range(months_ahead):
                try:
                    arrow = page.locator('button.next-arrow, .fc-next-button, button[aria-label="next"]').first
                    arrow.click(force=True)
                    time.sleep(1.5)
                except Exception:
                    break

            # Click the day
            day_str = str(target.day)
            try:
                elements = page.locator('td, .day, .fc-daygrid-day-number, .calendar-day, .dp__cell_inner').filter(has_text=re.compile(rf'^\s*{day_str}\s*$')).all()
                clicked = False
                for el in elements:
                    cls = el.get_attribute('class') or ""
                    if 'disabled' in cls.lower() or 'old' in cls.lower() or 'other-month' in cls.lower():
                        continue
                    if el.inner_text().strip() == day_str:
                        el.click(force=True)
                        clicked = True
                        time.sleep(3)
                        break
                
                if not clicked:
                    # Last ditch effort
                    el = page.get_by_text(day_str, exact=True).first
                    if el.is_visible(timeout=2000):
                        el.click(force=True)
                        clicked = True
                        time.sleep(3)
            except Exception as e:
                print(f"Failed to click day {day_str}: {e}")

            # --- Players & Holes ---
            try:
                page.locator(f'a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(force=True)
                time.sleep(2)
                page.locator('button, a').filter(has_text=re.compile(r'18 Holes|18-Hole', re.I)).first.click(force=True)
                time.sleep(3)
            except Exception:
                pass

            # --- Find tee time ---
            page.wait_for_load_state('networkidle')
            earliest = parse_time(target, booking.earliest_time)
            latest = parse_time(target, booking.latest_time)
            date_str = target.strftime('%m-%d-%Y')
            slots = page.locator('.booking-start-time-label, .time-summary-ob-left, .time-label').all()
            booking_element = None
            best_time_str = ''

            for slot in slots:
                txt = slot.inner_text().strip().lower()
                m = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', txt)
                if m:
                    avail = datetime.strptime(f"{date_str} {m.group(1)} {m.group(2)}", '%m-%d-%Y %I:%M %p')
                    if earliest <= avail <= latest:
                        booking_element = slot
                        best_time_str = f"{m.group(1)} {m.group(2)}"
                        break

            if not booking_element:
                raise Exception(f'No tee time found between {booking.earliest_time} and {booking.latest_time}')

            if dry_run:
                browser.close()
                return f'Dry run success at {best_time_str}'

            # --- Click time slot ---
            print(f"DEBUG: Clicking tee time slot for {best_time_str}")
            
            # Attempt to click the slot multiple ways
            for attempt in range(3):
                try:
                    if attempt == 0:
                        booking_element.click(force=True)
                    elif attempt == 1:
                        # Click the text directly
                        page.get_by_text(best_time_str, exact=False).first.click(force=True)
                    else:
                        # Click the parent button
                        booking_element.locator('xpath=./ancestor::button | ./ancestor::a').first.click(force=True)
                    
                    # Wait for modal or panel to appear
                    time.sleep(3)
                    # Check if login or booking button exists in any frame
                    found = False
                    for f in [page] + page.frames:
                        if f.locator('input[type="password"], button:has-text("Book Time"), button:has-text("Log In")').count() > 0:
                            found = True
                            break
                    if found:
                        print(f"DEBUG: Successfully opened booking modal/panel on attempt {attempt+1}")
                        break
                except Exception as e:
                    print(f"DEBUG: Click attempt {attempt+1} failed: {e}")
            
            # --- Handle Login & Booking Panel ---
            def interact_with_booking(f):
                try:
                    # Check for login fields
                    if f.locator('input[type="password"]').count() > 0:
                        f.locator('input[type="email"], input[name="email"]').first.fill(email)
                        f.locator('input[type="password"], input[name="password"]').first.fill(password)
                        print(f"DEBUG: Clicking Log In button in frame {f.url}")
                        f.locator('button').filter(has_text=re.compile(r'Log In|Login', re.I)).first.click(force=True)
                        time.sleep(5)
                        page.screenshot(path='screenshots/after_login_click.png', full_page=True)
                        # After login, the page might redirect or refresh. 
                        # We should return and let the main loop re-scan all frames.
                        return "RETRY"
                    
                    # Select options
                    options_clicked = False
                    for opt in ['18', '4', 'Yes']:
                        try:
                            # Use more specific selectors for ForeUp options
                            btn = f.locator('button, label, .btn').filter(has_text=re.compile(rf'^{opt}$|{opt} Holes|{opt} Players', re.I)).first
                            if btn.is_visible(timeout=1000):
                                btn.click(force=True)
                                options_clicked = True
                                time.sleep(0.5)
                        except: pass
                    
                    # Final book button
                    book_btn = f.locator('button, a, .btn-primary').filter(has_text=re.compile(r'Book Time|Reserve|Continue|Confirm', re.I)).first
                    if book_btn.is_visible(timeout=2000):
                        print(f"DEBUG: Found final booking button: {book_btn.inner_text().strip()}")
                        book_btn.click(force=True)
                        return "SUCCESS"
                except Exception as e:
                    print(f"DEBUG: Error in frame {f.url}: {e}")
                return "FAIL"

            # Main interaction loop
            for _ in range(3): # Up to 3 attempts (e.g. one for login, one for options)
                res = interact_with_booking(page)
                if res == "SUCCESS": break
                if res == "FAIL" or res == "RETRY":
                    found_in_frame = False
                    for f in page.frames:
                        if f == page: continue
                        res = interact_with_booking(f)
                        if res == "SUCCESS":
                            found_in_frame = True
                            break
                        if res == "RETRY":
                            found_in_frame = True
                            break
                    if res == "SUCCESS": break
                time.sleep(2)
            
            time.sleep(10)
            page.screenshot(path='screenshots/final_attempt.png', full_page=True)
            browser.close()
            return f'Success! Attempted booking for {best_time_str}'

        except Exception as e:
            print(f"DEBUG: Error in booking flow: {e}")
            page.screenshot(path='screenshots/error.png', full_page=True)
            browser.close()
            raise e


def book_via_foreup_index(url, booking_class_id, booking, email, password, dry_run=False):
    # Inject bc param into hash
    if '#' in url:
        base, fragment = url.split('#', 1)
        sep = '&' if '?' in fragment else '?'
        url = f"{base}#{fragment}{sep}bc={booking_class_id}"
    else:
        url = f"{url}#/teetimes?bc={booking_class_id}"
    return book_via_foreup_software(url, booking, email, password, dry_run=dry_run)


# Convenience wrappers
def book_orchard_creek(url, booking, email, password, dry_run=False):
    return book_via_foreup_software(url, booking, email, password, dry_run)

def book_schenectady_muni(url, booking, email, password, dry_run=False):
    return book_via_foreup_software(url, booking, email, password, dry_run)

def book_fairways_halfmoon(url, booking, email, password, dry_run=False):
    return book_via_foreup_software(url, booking, email, password, dry_run)

def book_stadium(url, booking, email, password, dry_run=False):
    return book_via_foreup_index(url, booking_class_id=14558, booking=booking, email=email, password=password, dry_run=dry_run)

def book_van_patten(url, booking, email, password, dry_run=False):
    return book_via_foreup_index(url, booking_class_id=None, booking=booking, email=email, password=password, dry_run=dry_run)


# ---------------------------------------------------------------------------
# Eagle Crest (Eagle Club Systems)
# ---------------------------------------------------------------------------

def book_via_eagleclub(url, booking, email, password, card_number=None, card_exp_month=None, card_exp_year=None, card_cvv=None, dry_run=False):
    with sync_playwright() as p:
        browser, context = _new_stealth_context(p, headless=False)
        page = context.new_page()
        apply_stealth(page)
        page.goto(url)
        page.wait_for_load_state('networkidle')
        time.sleep(5)

        # --- Login ---
        try:
            page.get_by_text('Login', exact=True).first.click(timeout=5000)
            time.sleep(2)
            page.get_by_placeholder('Email').type(email, delay=60)
            page.get_by_placeholder('Password').type(password, delay=60)
            page.locator('button').filter(has_text=re.compile(r'^Login$', re.I)).first.click(force=True)
            time.sleep(5)
        except Exception as e:
            print(f'DEBUG: Eagle Crest login: {e}')

        # --- Select date ---
        target = booking.desired_date
        day_abbr = target.strftime('%a')
        try:
            page.locator('a, div, span').filter(has_text=re.compile(rf'{day_abbr}.*{target.day}', re.I)).first.click(force=True)
            time.sleep(5)
        except Exception: pass

        # --- Set player count ---
        try:
            page.locator('a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(force=True)
            time.sleep(3)
        except Exception: pass

        if dry_run:
            browser.close()
            return f'Dry run success (Eagle Crest)'

        # --- Find and click tee time tile ---
        earliest = parse_time(target, booking.earliest_time)
        latest = parse_time(target, booking.latest_time)
        date_str = target.strftime('%m-%d-%Y')
        tiles = page.locator('.tee-time-tile, .card, [class*="time"]').all()
        booking_tile = None
        best_time_str = ''

        for tile in tiles:
            try:
                txt = tile.inner_text().strip()
                m = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', txt, re.IGNORECASE)
                if m:
                    avail = datetime.strptime(f"{date_str} {m.group(1)} {m.group(2)}", '%m-%d-%Y %I:%M %p')
                    if earliest <= avail <= latest:
                        booking_tile = tile
                        best_time_str = f"{m.group(1)} {m.group(2)}"
                        break
            except: continue

        if not booking_tile:
            raise Exception('No Eagle Crest tee time found')

        booking_tile.click(force=True)
        time.sleep(3)

        # --- Reservation modal ---
        try:
            page.locator('button, label').filter(has_text=re.compile(r'^18$')).first.click(force=True)
            page.locator('.modal button, .modal label').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(force=True)
            page.locator('button, label').filter(has_text=re.compile(r'^YES$', re.I)).first.click(force=True)
            page.locator('input[type="checkbox"]').first.check(force=True)
        except: pass

        time.sleep(1)
        page.locator('button').filter(has_text=re.compile(r'Continue', re.I)).first.click(force=True)
        time.sleep(5)

        # --- Credit Card Payment ---
        if card_number and card_cvv:
            try:
                page.get_by_placeholder('Card Number').type(card_number, delay=60)
                page.locator('input[name*="month"], input[placeholder*="MM"]').first.type(card_exp_month or '07', delay=60)
                page.locator('input[name*="year"], input[placeholder*="YY"]').first.type(card_exp_year or '26', delay=60)
                page.get_by_placeholder('CVV').type(card_cvv, delay=60)
                page.locator('button').filter(has_text=re.compile(r'Pre-Authorize Now|Pay|Submit', re.I)).first.click(force=True)
                time.sleep(10)
            except Exception as e:
                print(f'DEBUG: Eagle Crest payment: {e}')

        try:
            page.locator('button').filter(has_text=re.compile(r'^OK$', re.I)).first.click(force=True)
            time.sleep(3)
        except: pass

        browser.close()
        return f'Success! Booked Eagle Crest {best_time_str}'
