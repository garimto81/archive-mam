/**
 * E2E Tests - Navigation
 * Tests navigation between pages
 */

import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to all main pages', async ({ page }) => {
    await page.goto('/');

    // Navigate to Search
    await page.click('a:has-text("Search")');
    await expect(page).toHaveURL(/\/search/);

    // Navigate to Favorites
    await page.click('a:has-text("Favorites")');
    await expect(page).toHaveURL(/\/favorites/);

    // Navigate to Downloads
    await page.click('a:has-text("Downloads")');
    await expect(page).toHaveURL(/\/downloads/);

    // Navigate to Admin
    await page.click('a:has-text("Admin")');
    await expect(page).toHaveURL(/\/admin/);

    // Navigate back to Home
    await page.click('a:has-text("Home")');
    await expect(page).toHaveURL(/^http:\/\/localhost:3000\/$/);
  });

  test('should display responsive navigation', async ({ page }) => {
    await page.goto('/');

    // Check navigation bar exists
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Check all navigation links are present
    await expect(page.locator('a:has-text("Home")')).toBeVisible();
    await expect(page.locator('a:has-text("Search")')).toBeVisible();
    await expect(page.locator('a:has-text("Favorites")')).toBeVisible();
    await expect(page.locator('a:has-text("Downloads")')).toBeVisible();
  });
});
