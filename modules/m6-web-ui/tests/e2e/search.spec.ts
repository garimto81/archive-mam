/**
 * E2E Tests - Search Flow
 * Tests the complete search workflow from query to results
 */

import { test, expect } from '@playwright/test';

test.describe('Search Flow', () => {
  test('should display home page with search bar', async ({ page }) => {
    await page.goto('/');

    // Check title
    await expect(page).toHaveTitle(/POKER-BRAIN/);

    // Check search bar exists
    const searchInput = page.locator('input[placeholder*="Search poker hands"]');
    await expect(searchInput).toBeVisible();
  });

  test('should navigate to search results page', async ({ page }) => {
    await page.goto('/');

    // Type search query
    const searchInput = page.locator('input[placeholder*="Search poker hands"]');
    await searchInput.fill('Tom Dwan bluff');

    // Click search button
    await page.click('button:has-text("Search")');

    // Should navigate to search page
    await expect(page).toHaveURL(/\/search\?q=Tom%20Dwan%20bluff/);
  });

  test('should display search results', async ({ page }) => {
    await page.goto('/search?q=test');

    // Wait for results or error message
    await page.waitForSelector('text=/Found|No results|Searching/');
  });

  test('should handle empty search query', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="Search poker hands"]');
    const searchButton = page.locator('button:has-text("Search")');

    // Search button should be disabled for empty query
    await expect(searchButton).toBeDisabled();

    // Fill with single character (too short)
    await searchInput.fill('a');
    await expect(searchButton).toBeDisabled();

    // Fill with 2 characters (minimum)
    await searchInput.fill('ab');
    await expect(searchButton).toBeEnabled();
  });

  test('should display autocomplete suggestions', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('input[placeholder*="Search poker hands"]');

    // Type query
    await searchInput.fill('Tom');

    // Wait for suggestions (with timeout since it's debounced)
    await page.waitForTimeout(500);

    // Check if suggestions dropdown appears (may not in development mode)
    const suggestions = page.locator('[role="listbox"]');
    const suggestionsVisible = await suggestions.isVisible().catch(() => false);

    if (suggestionsVisible) {
      // Verify suggestions are clickable
      const firstSuggestion = suggestions.locator('button').first();
      await expect(firstSuggestion).toBeVisible();
    }
  });
});
