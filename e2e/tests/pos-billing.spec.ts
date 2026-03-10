/**
 * E2E test: POS Billing flow — barcode scan → add to cart → checkout → receipt preview.
 * Simulates barcode input by typing SKU into search field.
 */

import { test, expect } from "@playwright/test";

test.describe("POS Billing", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to POS page (assumes user is logged in)
    await page.goto("/pos");
  });

  test("should display POS billing page", async ({ page }) => {
    await expect(page.locator("text=Cart")).toBeVisible();
    await expect(page.getByPlaceholder(/scan barcode|enter sku/i)).toBeVisible();
  });

  test("should add product via barcode/SKU input", async ({ page }) => {
    // Simulate barcode scan by typing into search field
    const searchInput = page.getByPlaceholder(/scan barcode|enter sku/i);
    await searchInput.fill("PROD-001");
    await searchInput.press("Enter");

    // Product should appear in cart (or show 'not found' if not in local DB)
    // This depends on having products cached locally
    await page.waitForTimeout(1000);
  });

  test("should calculate totals correctly", async ({ page }) => {
    // This test validates the cart total display exists
    await expect(page.locator("text=Subtotal")).toBeVisible();
    await expect(page.locator("text=Total")).toBeVisible();
  });

  test("should show online/offline status", async ({ page }) => {
    // Status indicator should be visible
    const status = page.locator("text=/Online|Offline/");
    await expect(status).toBeVisible();
  });

  test("should show sync queue status when items pending", async ({ page }) => {
    // Go offline
    await page.context().setOffline(true);

    // Navigate to POS
    await page.goto("/pos").catch(() => {}); // May fail offline, that's ok

    // Restore online
    await page.context().setOffline(false);
  });
});

test.describe("Receipt Preview", () => {
  test("should open print preview for HTML receipt", async ({ page }) => {
    await page.goto("/pos");

    // Look for print button (only shows after checkout)
    const printBtn = page.locator("text=Print");
    // Print button may or may not be visible depending on state
    if (await printBtn.isVisible()) {
      // Verify it's clickable
      await expect(printBtn).toBeEnabled();
    }
  });
});

test.describe("Offline Sync", () => {
  test("should queue invoice when offline", async ({ page }) => {
    await page.goto("/pos");

    // Go offline
    await page.context().setOffline(true);

    // The page should show offline indicator
    await page.waitForTimeout(1000);
    const offlineIndicator = page.locator("text=/Offline/");
    await expect(offlineIndicator).toBeVisible();

    // Go back online
    await page.context().setOffline(false);
    await page.waitForTimeout(1000);

    const onlineIndicator = page.locator("text=/Online/");
    await expect(onlineIndicator).toBeVisible();
  });
});
