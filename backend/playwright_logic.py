from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
from playwright_stealth import Stealth
from playwright_stealth import Stealth
from datetime import datetime, timezone
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


async def wait_for_release(release_time_str, lead_seconds=1.0, offset_seconds=0.250):
    """
    Precision wait loop to synchronize execution with the exact release time.
    Calculates time difference and coarse-sleeps, then fine-sleeps/busy-waits.
    """
    if not release_time_str:
        logging.info("Precision Sync: No release_time provided, executing immediately.")
        return
        
    try:
        # Normalize ISO 8601 'Z' suffix to '+00:00' for Python compatibility
        if release_time_str.endswith('Z'):
            release_time_str = release_time_str[:-1] + '+00:00'
            
        release_dt = datetime.fromisoformat(release_time_str)
        now_dt = datetime.now(timezone.utc)
        
        diff = (release_dt - now_dt).total_seconds()
        
        if diff <= 0:
            logging.info("Precision Sync: Release time %s is in the past (by %.2fs), executing immediately.", 
                         release_time_str, abs(diff))
            return
            
        logging.info("Precision Sync: Synchronizing for release at %s (Current: %s, Diff: %.2fs)", 
                     release_time_str, now_dt.isoformat(), diff)
                     
        # Stage 1: Coarse sleep until lead_seconds before target
        coarse_wait = diff - lead_seconds
        if coarse_wait > 0:
            logging.info("Precision Sync: Coarse sleeping for %.2fs...", coarse_wait)
            await asyncio.sleep(coarse_wait)
            
        # Stage 2: Fine-grained loop (busy-wait with tiny sleeps) to hit target precision
        # Target offset_seconds after release to ensure the server-side release is fully live and processed
        target_ts = release_dt.timestamp() + offset_seconds
        
        while True:
            current_ts = datetime.now(timezone.utc).timestamp()
            if current_ts >= target_ts:
                break
            # Use 5ms sleeps to keep accuracy high while preventing CPU pegging
            await asyncio.sleep(0.005)
            
        logging.info("Precision Sync: TARGET REACHED (Current: %s). Releasing trigger!", 
                     datetime.now(timezone.utc).isoformat())
                     
    except Exception as e:
        logging.error("Precision Sync: Error in wait_for_release: %s", e)


async def _new_stealth_context(p, headless=True):
    """Launch a Chromium context with anti-bot flags and optional proxy support."""
    proxy_server = os.getenv("PLAYWRIGHT_PROXY_SERVER")
    proxy_username = os.getenv("PLAYWRIGHT_PROXY_USERNAME")
    proxy_password = os.getenv("PLAYWRIGHT_PROXY_PASSWORD")

    proxy_dict = None
    if proxy_server:
        logging.info("Routing traffic through residential proxy: %s", proxy_server)
        proxy_dict = {"server": proxy_server}
        if proxy_username and proxy_password:
            proxy_dict["username"] = proxy_username
            proxy_dict["password"] = proxy_password

    browser = await p.chromium.launch(
        headless=headless,
        args=['--disable-blink-features=AutomationControlled', '--disable-gpu', '--no-sandbox'],
        proxy=proxy_dict
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={'width': 1920, 'height': 1080},
        timezone_id='America/New_York'
    )

    async def abort_heavy_requests(route):
        if route.request.resource_type in ["image", "media", "font"]:
            await route.abort()
        else:
            await route.continue_()
    await context.route("**/*", abort_heavy_requests)

    return browser, context

# ---------------------------------------------------------------------------
# CPS Golf (Capital Hills / Old Post Road)
# ---------------------------------------------------------------------------

async def book_cps_golf(url, booking, email, password, dry_run=False, headless=True):
    """Verified flow for CPS Golf sites."""
    async with Stealth().use_async(async_playwright()) as p:
        browser, context = await _new_stealth_context(p, headless=headless)
        page = await context.new_page()
        try:
            logging.info("Navigating to CPS Golf URL: %s", url)
            await page.goto(url, wait_until='networkidle')

            # --- Auth ---
            logging.info("Starting authentication.")
            await page.get_by_role('button', name='Sign In').click()

            email_field = page.get_by_role('textbox', name='Email', exact=True)
            await email_field.wait_for(state='visible', timeout=10000)
            await email_field.fill(email)
            await page.get_by_role('button', name='NEXT').click()

            pass_field = page.get_by_role('textbox', name='Password', exact=True)
            await pass_field.wait_for(state='visible', timeout=10000)
            await pass_field.fill(password)
            await page.get_by_role('button', name='SIGN IN', exact=True).click()
            
            logging.info("Sign-in button clicked. Waiting for dashboard to load.")
            # Wait for any of these to confirm the dashboard is live
            try:
                await page.locator('.ngx-dates-picker-container, app-ngx-dates-picker, .topbar-title, .advancefilter-container').first.wait_for(state='visible', timeout=25000)
                logging.info("Dashboard detected.")
            except PlaywrightTimeoutError:
                logging.warning("Dashboard container not detected via locator, falling back to networkidle.")
                await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Additional settling time for headless
            await page.wait_for_timeout(3000)

            # --- Navigate date ---
            logging.info("Navigating to target date: %s", booking.desired_date)
            
            today = datetime.today().date()
            months_ahead = (booking.desired_date.year - today.year) * 12 + booking.desired_date.month - today.month
            if months_ahead > 0:
                logging.info("Target date is in a future month. Navigating calendar ahead by %d month(s).", months_ahead)
                arrow_selector = ".topbar-container > div:last-child, .topbar-container div:has(svg polygon#Forward)"
                for i in range(months_ahead):
                    btn = page.locator(arrow_selector).first
                    await btn.wait_for(state='visible', timeout=8000)
                    # Remove 'disabled' class if present before clicking
                    await btn.evaluate("el => el.classList.remove('disabled')")
                    await btn.click(force=True)
                    await page.wait_for_timeout(1500)
            
            day_str = str(booking.desired_date.day)
            day_button = page.locator('.ngx-dates-picker-container .day-unit').filter(has_text=re.compile(rf'^{day_str}$')).first
            if not await day_button.is_visible():
                 day_button = page.locator('.ngx-dates-picker-container').get_by_text(day_str, exact=True).first
            if not await day_button.is_visible():
                 day_button = page.get_by_text(day_str, exact=True).first
            
            await day_button.wait_for(state='visible', timeout=10000)
            
            # Bypass disabled UI elements for early/midnight booking
            await day_button.evaluate("""el => {
                el.classList.remove('is-disabled', 'disabled', 'mat-calendar-body-disabled');
                el.removeAttribute('disabled');
                el.removeAttribute('aria-disabled');
                el.style.pointerEvents = 'auto';
                const cell = el.closest('.day-unit, .mat-calendar-body-cell');
                if (cell) {
                    cell.classList.remove('is-disabled', 'disabled', 'mat-calendar-body-disabled');
                    cell.removeAttribute('disabled');
                    cell.removeAttribute('aria-disabled');
                    cell.style.pointerEvents = 'auto';
                }
            }""")
            
            # Precision wait until release time
            await wait_for_release(getattr(booking, 'release_time', None))
            
            # Toggle month right after wait to refresh calendar states
            if getattr(booking, 'release_time', None):
                try:
                    logging.info("Precision Sync: Toggling month to refresh calendar states.")
                    prev_btn = page.locator('.topbar-container > div:first-child').first
                    next_btn = page.locator('.topbar-container > div:last-child').first
                    if await prev_btn.is_visible(timeout=2000) and await next_btn.is_visible(timeout=2000):
                        await prev_btn.evaluate("el => el.classList.remove('disabled')")
                        await prev_btn.click(force=True)
                        await page.wait_for_timeout(300)
                        await next_btn.click(force=True)
                        await page.wait_for_timeout(300)
                        # Re-locate the day element since DOM re-rendered
                        day_button = page.locator('.ngx-dates-picker-container .day-unit').filter(has_text=re.compile(rf'^{day_str}$')).first
                        if not await day_button.is_visible():
                             day_button = page.get_by_text(day_str, exact=True).first
                except Exception as e:
                    logging.warning("Failed to toggle month: %s", e)
            
            await day_button.click(force=True)
            logging.info(f"Clicked day {day_str} directly.")
            await page.wait_for_load_state('networkidle', timeout=10000)

            # --- Players & Holes ---
            logging.info("Selecting %d players and 18 holes.", booking.players)
            await page.wait_for_timeout(2000)
            try:
                await page.get_by_role("button", name=str(booking.players), exact=True).click(force=True, timeout=8000)
                await page.wait_for_timeout(1500)
                
                logging.info("Opening holes dropdown.")
                # The Holes dropdown is the second mat-select on the page (first is Course)
                holes_select = page.locator('mat-select#mat-select-8, mat-select').nth(1)
                await holes_select.wait_for(state='visible', timeout=8000)
                await holes_select.click(force=True)
                await page.wait_for_timeout(1000)

                logging.info("Selecting '18 Holes'.")
                overlay = page.locator('.cdk-overlay-container')
                try:
                    await overlay.get_by_text("18 Holes", exact=True).first.click(force=True, timeout=3000)
                except Exception:
                    try:
                        await overlay.get_by_text("18", exact=True).first.click(force=True, timeout=3000)
                    except Exception:
                        logging.warning("Could not find 18 Holes option in overlay, continuing with default.")
                await page.wait_for_timeout(2000)
            except Exception as e:
                logging.warning("Failed to set players/holes via codegen sequence: %s", e)

            # --- Expand all time sections ---
            logging.info("Expanding all tee time sections.")
            await page.wait_for_timeout(1500) 
            for label in [
                'Show more Morning tee times', 'Show more Mid Day tee times',
                'Show more Late Day tee times', 'Show more Evening tee times',
            ]:
                btn = page.get_by_role('button', name=label)
                if await btn.is_visible():
                    try:
                        await btn.click(force=True, timeout=2000)
                    except: pass

            # --- Find tee time in window ---
            logging.info("Searching for tee time between %s and %s.", booking.earliest_time, booking.latest_time)
            earliest = parse_time(booking.desired_date, booking.earliest_time)
            latest = parse_time(booking.desired_date, booking.latest_time)
            
            all_buttons = await page.locator('button').filter(has_text=re.compile(r'\d{1,2}:\d{2}', re.I)).all()
            booking_element = None
            best_time_str = ''

            for btn in all_buttons:
                txt = (await btn.inner_text()).strip()
                m = re.search(r'(\d{1,2}:\d{2})\s*([AP])\s*M?', txt, re.IGNORECASE)
                if m:
                    time_part = m.group(1)
                    ampm = m.group(2).upper() + "M"
                    ts = f"{time_part}{ampm}"
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

            # --- Book & Finalize ---
            logging.info("Attempting to book tee time: %s", best_time_str)

            # 1. Click tee time until the first Continue button appears
            try:
                for attempt in range(6):
                    logging.info(f"Clicking tee time slot (Attempt {attempt + 1})")
                    
                    try:
                        # Scroll to ensure it's in the viewport
                        await booking_element.scroll_into_view_if_needed()
                        
                        # Get bounding box and click in the absolute center
                        box = await booking_element.bounding_box()
                        if box:
                            await page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                            logging.info("Triggered coordinate-based mouse click.")
                        else:
                            await booking_element.click(force=True)
                            logging.info("Triggered standard force click (no bounding box).")
                    except Exception as e:
                        logging.warning(f"Click action threw an error: {e}")
                    
                    try:
                        # Wait for the modal/notice to appear (Next or Continue button)
                        next_or_continue = page.get_by_role("button", name=re.compile(r'^(Next|Continue)$', re.I)).first
                        await next_or_continue.wait_for(state='visible', timeout=5000)
                        logging.info("Checkout modal/notice opened.")
                        break
                    except PlaywrightTimeoutError:
                        if attempt == 5:
                            screenshot_path = os.path.join(SCREENSHOT_DIR, 'modal_fail_debug.png')
                            await page.screenshot(path=screenshot_path, timeout=5000, animations="disabled")
                            logging.warning(f"Modal failed to open after all attempts. Saved debug screenshot to {screenshot_path}")
                        await page.wait_for_timeout(2000)
                        continue
            except Exception as e:
                logging.warning(f"Initial tee time click failed: {e}")

            # 2. Sequence through the checkout steps (click Next/Continue through terms & notices)
            try:
                for step in range(3):
                    btn = page.get_by_role("button", name=re.compile(r'^(Next|Continue)$', re.I)).first
                    if await btn.is_visible(timeout=5000):
                        logging.info(f"Clicking modal step button: {await btn.inner_text()}")
                        await btn.click(force=True)
                        await page.wait_for_timeout(2000)
                    else:
                        break

                logging.info("Looking for button: Finalize Reservation")
                finalize_btn = page.get_by_role("button", name=re.compile(r'Finalize|Complete|Book', re.I)).first
                await finalize_btn.wait_for(state='visible', timeout=15000)
                
                clicked_successfully = False
                for attempt in range(6):
                    logging.info(f"Clicking Finalize Reservation (Attempt {attempt + 1})")
                    try:
                        await finalize_btn.scroll_into_view_if_needed()
                        if attempt % 2 == 0:
                            await finalize_btn.click(force=True)
                        else:
                            await finalize_btn.dispatch_event("click")
                    except Exception as e:
                        logging.warning(f"Click action threw an error: {e}")
                    
                    try:
                        await page.wait_for_url(lambda url: "checkout" not in url.lower(), timeout=5000)
                        logging.info("URL changed! Proceeding to success verification.")
                        clicked_successfully = True
                        break
                    except PlaywrightTimeoutError:
                        logging.warning("URL did not change. Retrying...")
                        await page.wait_for_timeout(2000)

                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=20000)
                except: pass
                
                # Verify success STRICTLY
                success_locator = page.locator('text=Success, text=Confirmed, text=Reservation #, .confirmation-number, .reservation-details, .booking-id')
                return_btn = page.get_by_role('button', name='Return to Tee Times')
                
                try:
                    if await return_btn.is_visible(timeout=15000):
                        logging.info("Booking confirmation detected. Clicking 'Return to Tee Times'.")
                        await return_btn.click(timeout=5000)
                    elif await success_locator.first.is_visible(timeout=10000):
                        logging.info("Booking confirmation text detected on page.")
                    else:
                        raise PlaywrightTimeoutError("No success indicators found.")
                except PlaywrightTimeoutError:
                    if "reservation" in page.url.lower() or "success" in page.url.lower():
                        logging.info(f"Confirmation text not found, but URL indicates success: {page.url}")
                    elif "checkout" in page.url.lower():
                        raise Exception(f"Still on checkout page after clicking Finalize. URL: {page.url}")
                    else:
                        raise Exception(f"Finalize button clicked, but reached an unknown state. URL: {page.url}")
            
            except PlaywrightTimeoutError as e:
                logging.error(f"Confirmation sequence timed out: {e}")
                raise Exception(f"Failed to complete booking steps: {e}")
            
            return f'Success! Booked {best_time_str}'

        except Exception as e:
            logging.error("An error occurred in book_cps_golf: %s", e, exc_info=True)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'cps_golf_error.png'), timeout=5000, animations="disabled")
            raise
        finally:
            await browser.close()

async def book_cps_old_post(url, booking, email, password, dry_run=False, headless=True):
    return await book_cps_golf(url, booking, email, password, dry_run=dry_run, headless=headless)

async def book_town_of_colonie(url, booking, email, password, dry_run=False, headless=True):
    """Verified flow for Town of Colonie (direct CPS Golf site)."""
    return await book_cps_golf(url, booking, email, password, dry_run=dry_run, headless=headless)

# ---------------------------------------------------------------------------
# ForeUp
# ---------------------------------------------------------------------------

async def book_via_foreup_software(url, booking, email, password, dry_run=False, headless=False, pay_at_facility=False):
    """Verified flow for ForeUp sites."""
    async with Stealth().use_async(async_playwright()) as p:
        browser, context = await _new_stealth_context(p, headless=headless)
        page = await context.new_page()
        try:
            logging.info("Navigating to ForeUp URL: %s", url)
            await page.goto(url, wait_until='networkidle', timeout=60000)

            # --- Booking class: click Public as GUEST (before login) ---
            try:
                logging.info("Trying to select 'Public' booking class.")
                await page.locator('button, a, div').filter(
                    has_text=re.compile(r'^\s*Public.*$', re.IGNORECASE)
                ).first.click(timeout=8000)
                await page.wait_for_load_state('networkidle')
            except PlaywrightTimeoutError:
                logging.warning("Could not find or click 'Public' booking class, continuing anyway.")

            # --- Navigate to target date ---
            logging.info("Navigating to target date: %s", booking.desired_date)
            target = booking.desired_date
            today = datetime.today().date()
            months_ahead = (target.year - today.year) * 12 + target.month - today.month
            if months_ahead > 0:
                for _ in range(months_ahead):
                    await page.locator('th.next, button.next-arrow, .fc-next-button, button[aria-label="next"]').first.click()
                    await page.wait_for_timeout(1000)

            # Click the day
            day_str = str(target.day)
            day_selector = f'td[data-day="{day_str}"], .day:has-text("{day_str}")'
            day_element = page.locator(day_selector).first
            await day_element.wait_for(state='visible', timeout=10000)
            
            # Bypass disabled UI elements for early/midnight booking
            await day_element.evaluate("""el => {
                el.classList.remove('disabled');
                el.removeAttribute('disabled');
                el.removeAttribute('aria-disabled');
                const cell = el.closest('td, button, .day');
                if (cell) {
                    cell.classList.remove('disabled');
                    cell.removeAttribute('disabled');
                    cell.removeAttribute('aria-disabled');
                    cell.style.pointerEvents = 'auto';
                }
            }""")
            
            # Precision wait until release time
            await wait_for_release(getattr(booking, 'release_time', None))
            
            # Toggle month right after wait to refresh calendar states
            if getattr(booking, 'release_time', None):
                try:
                    logging.info("Precision Sync: Toggling month to refresh datepicker states.")
                    prev_btn = page.locator('th.prev, button.prev-arrow, .fc-prev-button, button[aria-label="prev"]').first
                    next_btn = page.locator('th.next, button.next-arrow, .fc-next-button, button[aria-label="next"]').first
                    if await prev_btn.is_visible(timeout=2000) and await next_btn.is_visible(timeout=2000):
                        await prev_btn.click(force=True)
                        await page.wait_for_timeout(200)
                        await next_btn.click(force=True)
                        await page.wait_for_timeout(200)
                        # Re-locate the day element since DOM re-rendered
                        day_element = page.locator(day_selector).first
                except Exception as e:
                    logging.warning("Failed to toggle month: %s", e)
            
            await day_element.click(force=True)
            await page.wait_for_timeout(2500)  # Explicitly wait for SPA to load new day's data

            # --- Players & Holes ---
            logging.info("Setting players to %d and holes to 18.", booking.players)
            try:
                await page.locator('a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(timeout=5000)
                await page.wait_for_timeout(1000)
                await page.locator('button, a').filter(has_text=re.compile(r'18 Holes|18-Hole', re.I)).first.click(timeout=5000)
                await page.wait_for_timeout(2000)
            except PlaywrightTimeoutError:
                logging.warning("Could not set players/holes. Assuming defaults are OK.")

            # --- Find tee time ---
            logging.info("Searching for tee time between %s and %s.", booking.earliest_time, booking.latest_time)
            earliest = parse_time(target, booking.earliest_time)
            latest = parse_time(target, booking.latest_time)
            
            slots_locator = page.locator('.booking-start-time-label, .time-summary-ob-left, .time-label')
            try:
                await slots_locator.first.wait_for(state='visible', timeout=10000)
            except PlaywrightTimeoutError:
                logging.warning("No tee times appeared to load, or none exist.")

            slots = await slots_locator.all()
            booking_element = None
            best_time_str = ''

            for slot in slots:
                txt = (await slot.inner_text()).strip().lower()
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
            await booking_element.click()

            # Wait for modal or panel to appear
            modal_locator = page.locator('div.modal-body, div.booking-details, #booking-modal, .modal-dialog, .booking-modal').first
            await modal_locator.wait_for(state='visible', timeout=15000)

            # --- Handle Login (if necessary) ---
            try:
                # Use global page selectors for login to be safe
                email_input = page.get_by_placeholder("Email").first
                pass_input = page.get_by_placeholder("Password").first
                
                is_visible = False
                try:
                    is_visible = await email_input.is_visible(timeout=5000)
                except Exception:
                    pass

                if is_visible:
                    logging.info("Login form detected. Logging in...")
                    await email_input.fill(email)
                    await pass_input.fill(password)
                    await pass_input.press("Enter")
                    
                    # Wait for login to complete
                    try:
                        await email_input.wait_for(state='hidden', timeout=15000)
                        logging.info("Login successful, waiting for booking options...")
                        await page.wait_for_timeout(4000) # Give UI time to load options
                    except PlaywrightTimeoutError as e:
                        screenshot_path = os.path.join(SCREENSHOT_DIR, 'foreup_login_error.png')
                        try:
                            await page.screenshot(path=screenshot_path, timeout=5000, animations="disabled")
                            logging.info(f"Saved login error screenshot to {screenshot_path}")
                        except Exception:
                            pass
                        raise Exception("Golf course login failed - credentials may be incorrect, or portal blocked login.")
            except Exception as e:
                if "login failed" in str(e):
                    raise
                logging.info(f"No login required or login transition handled: {e}")

            # --- Select Booking Options ---
            # Search globally on the page as the modal might have refreshed
            logging.info("Selecting booking options (Holes, Players, Cart).")
            try:
                # Use codegen-style label selectors globally
                await page.get_by_label(re.compile(r"18 Holes", re.I)).click(timeout=5000)
                await page.wait_for_timeout(500)
                await page.get_by_label(re.compile(rf"{booking.players} Players", re.I)).click(timeout=5000)
                await page.wait_for_timeout(500)
                
                # Optional cart selection
                cart_opt = page.get_by_label(re.compile(r"Yes.*cart", re.I))
                if await cart_opt.is_visible(timeout=2000):
                    await cart_opt.click()
            except Exception as e:
                logging.warning(f"Could not select some options (may have used defaults): {e}")

            # --- Final Booking Confirmation ---
            logging.info("Looking for final booking confirmation button.")
            # Search globally for the button
            book_btn = page.get_by_role("button", name=re.compile(r"Book Time", re.I))
            
            # If role check fails, try text-based locator
            if not await book_btn.is_visible(timeout=5000):
                book_btn = page.locator('button, a').filter(
                    has_text=re.compile(r'Book Time|Reserve|Continue|Confirm', re.I)
                ).first
            
            await book_btn.wait_for(state='visible', timeout=10000)
            logging.info("Clicking final booking button: %s", (await book_btn.inner_text()).strip())
            
            if not dry_run:
                await book_btn.click()
                
                if pay_at_facility:
                    logging.info("Handling 'Pay At Facility' modal.")
                    try:
                        await page.get_by_role("radio", name="Pay At Facility").check(timeout=10000)
                        await page.locator("#select-payment-type-modal").get_by_role("button", name=re.compile(r"Book Time", re.I)).click()
                    except Exception as e:
                        logging.warning(f"Could not handle 'Pay At Facility': {e}")
                
                # Wait briefly for the action to process
                await page.wait_for_timeout(3000)
            else:
                logging.info("DRY RUN: Skipping final click.")
            
            return f'Success! Attempted booking for {best_time_str}.'

            

        except Exception as e:
            logging.error("An error occurred in book_via_foreup_software: %s", e, exc_info=True)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'foreup_error.png'), animations="disabled")
            raise
        finally:
            await browser.close()


async def book_via_foreup_index(url, booking_class_id, booking, email, password, dry_run=False, headless=True, pay_at_facility=False):
    # Inject bc param into hash
    if '#' in url:
        base, fragment = url.split('#', 1)
        sep = '&' if '?' in fragment else '?'
        url = f"{base}#{fragment}{sep}bc={booking_class_id}"
    else:
        url = f"{url}#/teetimes?bc={booking_class_id}"
    return await book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless, pay_at_facility=pay_at_facility)


# Convenience wrappers
async def book_orchard_creek(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

async def book_schenectady_muni(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless, pay_at_facility=True)

async def book_fairways_halfmoon(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

async def book_stadium(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_index(url, booking_class_id=14558, booking=booking, email=email, password=password, dry_run=dry_run, headless=headless)

async def book_van_patten(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_index(url, booking_class_id=None, booking=booking, email=email, password=password, dry_run=dry_run, headless=headless)

async def book_saratoga_spa(url, booking, email, password, dry_run=False, headless=True):
    return await book_via_foreup_software(url, booking, email, password, dry_run=dry_run, headless=headless)

# ---------------------------------------------------------------------------
# Eagle Crest (Eagle Club Systems)
# ---------------------------------------------------------------------------

async def book_via_eagleclub(url, booking, email, password, card_number=None, card_exp_month=None, card_exp_year=None, card_cvv=None, dry_run=False, headless=True):
    """Books a tee time through Eagle Club Systems."""
    async with Stealth().use_async(async_playwright()) as p:
        browser, context = await _new_stealth_context(p, headless=headless)
        page = await context.new_page()
        try:
            logging.info("Navigating to Eagle Club URL: %s", url)
            await page.goto(url, wait_until='networkidle')

            # --- Login ---
            try:
                logging.info("Attempting to log in.")
                await page.get_by_text('Login', exact=True).first.click(timeout=5000)
                await page.get_by_placeholder('Email').type(email, delay=50)
                await page.get_by_placeholder('Password').type(password, delay=50)
                await page.locator('button:has-text("Login")').first.click()
                await page.wait_for_load_state('networkidle', timeout=15000)
            except PlaywrightTimeoutError as e:
                logging.warning("Login failed or not required: %s", e)

            # --- Select date, players ---
            target = booking.desired_date
            logging.info("Selecting date: %s", target)
            day_element = page.locator('a, div, span').filter(has_text=re.compile(rf'{target.strftime("%a")}.*{target.day}', re.I)).first
            await day_element.wait_for(state='visible', timeout=10000)
            
            # Bypass disabled UI elements for early/midnight booking
            await day_element.evaluate("""el => {
                el.classList.remove('disabled', 'is-disabled');
                el.removeAttribute('disabled');
                el.removeAttribute('aria-disabled');
                el.style.pointerEvents = 'auto';
            }""")
            
            # Precision wait until release time
            await wait_for_release(getattr(booking, 'release_time', None))
            
            await day_element.click(force=True)
            await page.wait_for_timeout(2500)
            
            logging.info("Selecting players: %d", booking.players)
            await page.locator('a, button').filter(has_text=re.compile(rf'^{booking.players}$')).first.click()
            await page.wait_for_timeout(2000)

            # --- Find and click tee time tile ---
            logging.info("Searching for tee time tile.")
            earliest = parse_time(target, booking.earliest_time)
            latest = parse_time(target, booking.latest_time)
            
            tiles = await page.locator('.tee-time-tile, .card, [class*="time"]').all()
            booking_tile = None
            best_time_str = ''

            for tile in tiles:
                txt = (await tile.inner_text()).strip()
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

            await booking_tile.click()
            
            # --- Reservation modal ---
            logging.info("Handling reservation modal.")
            modal = page.locator('.modal-dialog').first
            await modal.wait_for(state='visible', timeout=10000)
            
            try:
                await modal.locator('button, label').filter(has_text=re.compile(r'^18$')).first.click(timeout=2000)
                await modal.locator('button, label').filter(has_text=re.compile(rf'^{booking.players}$')).first.click(timeout=2000)
                await modal.locator('button, label').filter(has_text=re.compile(r'^YES$', re.I)).first.click(timeout=2000)
                await modal.locator('input[type="checkbox"]').first.check()
            except PlaywrightTimeoutError:
                logging.info("Could not select all options in modal, continuing.")

            await modal.locator('button:has-text("Continue")').first.click()

            # --- Credit Card Payment ---
            if card_number and card_cvv:
                logging.info("Entering credit card information.")
                cc_frame = page.frame_locator('iframe[title="credit card form"]').first
                await cc_frame.get_by_placeholder('Card Number').type(card_number)
                await cc_frame.locator('input[name*="month"]').type(card_exp_month or '07')
                await cc_frame.locator('input[name*="year"]').type(card_exp_year or '26')
                await cc_frame.get_by_placeholder('CVV').type(card_cvv)
                await page.locator('button:has-text("Pre-Authorize Now")').first.click()
                await page.wait_for_timeout(10000)

            await page.locator('button:has-text("OK")').first.click()
            await page.wait_for_timeout(3000)

            return f'Success! Booked Eagle Crest {best_time_str}'

        except Exception as e:
            logging.error("An error occurred in book_via_eagleclub: %s", e, exc_info=True)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'eagleclub_error.png'))
            raise
        finally:
            await browser.close()
