"""
Shared course configuration for PinSeeker.

Single source of truth for course → URL → scraper function mapping.
Used by worker.py, replicate_playwright.py, and scraper_job.py.
"""
import playwright_logic

COURSE_CONFIG = {
    "capital hills": {
        "url": "https://capitalhillsny.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_golf,
    },
    "eagle crest": {
        "url": "https://player.eagleclubsystems.online/#/tee-slot?dbname=eaglecrest20260101",
        "func": playwright_logic.book_via_eagleclub,
    },
    "fairways": {
        "url": "https://foreupsoftware.com/index.php/booking/22948/12410#/welcome",
        "func": playwright_logic.book_fairways_halfmoon,
    },
    "post road": {
        "url": "https://oldepostroad.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_cps_old_post,
    },
    "orchard creek": {
        "url": "https://foreupsoftware.com/index.php/booking/19530/1791?_gl=1*yg2s5f*_ga*OTc1NDk3MjU5LjE3Nzc3Mjc1NDE.*_ga_WQPLP348DP*czE3NzgzMjYwMTEkbzIkZzAkdDE3NzgzMjYwMTEkajYwJGwwJGgw#teetimes",
        "func": playwright_logic.book_orchard_creek,
    },
    "schenectady": {
        "url": "https://foreupsoftware.com/index.php/booking/20480/4739?_gl=1*is3gta*_ga*MzM4MjY1MTE4LjE3NzgzMjYxMzA.*_ga_WQPLP348DP*czE3NzgzMjYxMzAkbzEkZzAkdDE3NzgzMjYxMzMkajU3JGwwJGgw#/teetimes",
        "func": playwright_logic.book_schenectady_muni,
    },
    "stadium": {
        "url": "https://foreupsoftware.com/index.php/booking/index/3332#teetimes",
        "func": playwright_logic.book_stadium,
    },
    "colonie": {
        "url": "https://colonie.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23.999722222222225",
        "func": playwright_logic.book_town_of_colonie,
    },
    "van patten": {
        "url": "https://foreupsoftware.com/index.php/booking/19765/2544",
        "func": playwright_logic.book_van_patten,
    },
    "saratoga spa": {
        "url": "https://foreupsoftware.com/index.php/booking/21684/8618#/teetimes",
        "func": playwright_logic.book_saratoga_spa,
    }
}


def get_handler(course_name: str):
    """Look up a course handler by fuzzy matching the course name."""
    query = course_name.lower()
    for key, config in COURSE_CONFIG.items():
        if key in query:
            return config
    return None


def list_courses() -> list[str]:
    """Return all registered course keys."""
    return list(COURSE_CONFIG.keys())
