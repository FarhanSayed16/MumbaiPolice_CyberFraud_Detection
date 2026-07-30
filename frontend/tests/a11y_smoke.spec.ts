import { test, expect } from '@playwright/test';

const SEED_EMAIL = 'officer.mumbai@maharashtracyber.gov.in';
const SEED_PASSWORD = 'SecurePolice@2026';

test.describe('Accessibility smoke checks', () => {
  test('login form labels and app landmarks', async ({ page }) => {
    await page.goto('/login');

    // Login form accessible labels
    await expect(page.getByText('Official Email')).toBeVisible();
    await expect(page.getByText('Password')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /Log In/i })).toBeVisible();

    // Authenticate and check main app landmarks
    await page.fill('input[type="email"]', SEED_EMAIL);
    await page.fill('input[type="password"]', SEED_PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/cases/, { timeout: 15000 });

    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('aside')).toBeVisible();

    // Page should expose at least one heading landmark
    const headingCount = await page.locator('h1, h2').count();
    expect(headingCount).toBeGreaterThanOrEqual(1);

    // Cases search input should expose aria-label
    const searchInput = page.getByRole('textbox', { name: /Search cases/i });
    await expect(searchInput).toBeVisible();

    // Tab through focusable controls until search is focused
    let focused = false;
    for (let i = 0; i < 40; i++) {
      await page.keyboard.press('Tab');
      focused = await searchInput.evaluate((el) => el === document.activeElement);
      if (focused) break;
    }
    await expect(searchInput).toBeFocused();

    // Interactive control should show focus-visible styling when tabbed to
    const hasFocusIndicator = await searchInput.evaluate((el) => {
      if (!(el instanceof HTMLElement)) return false;
      if (el.matches(':focus-visible')) return true;
      const style = window.getComputedStyle(el);
      return style.outlineWidth !== '0px' || style.boxShadow !== 'none';
    });
    expect(hasFocusIndicator).toBeTruthy();

    // Pagination controls (if cases exist)
    const prevBtn = page.getByRole('button', { name: /Previous page/i });
    if (await prevBtn.count()) {
      await expect(prevBtn).toBeVisible();
      await expect(page.getByRole('button', { name: /Next page/i })).toBeVisible();
    }
  });
});
