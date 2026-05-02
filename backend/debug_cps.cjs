const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();
  try {
    await page.goto('https://capitalhillsny.cps.golf/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Login
    await page.locator("button:has-text('Sign In'), mat-toolbar button:has(mat-icon)").first().click({ force: true });
    await page.waitForTimeout(2000);
    await page.getByPlaceholder('Email').or(page.locator("input[type='email']")).first().fill('jeff.gerard05@gmail.com');
    await page.locator("button:has-text('Next'), button[type='submit']").first().click({ force: true });
    await page.waitForTimeout(2000);
    await page.getByPlaceholder('Password', { exact: true }).or(page.locator("input[type='password']")).first().fill('Password101');
    const signInBtn = page.locator("button[type='submit'], button:has-text('Sign In'), .mat-raised-button.mat-accent").filter({ hasText: 'Sign In' }).first();
    await signInBtn.evaluate("el => el.click()");
    await page.waitForTimeout(5000);
    
    // Log Day Elements
    console.log('--- Checking Day Elements ---');
    const dayElements = await page.locator('.day-background-upper, .btn-day-unit').all();
    console.log('Found elements:', dayElements.length);
    for (let i = 0; i < Math.min(dayElements.length, 31); i++) {
        const text = await dayElements[i].innerText();
        const className = await dayElements[i].getAttribute('class');
        console.log("Day: " + text.trim() + " | Classes: " + className);
    }
  } catch (e) {
    console.error(e);
  } finally {
    await browser.close();
  }
})();