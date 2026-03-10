/**
 * E2E test: Device pairing flow.
 */

import { test, expect } from "@playwright/test";

test.describe("Device Pairing API", () => {
  const API_BASE = "http://localhost:8000";

  test("should create pairing token via API", async ({ request }) => {
    // This test requires a running backend with auth
    // Skip if backend not available
    try {
      const health = await request.get(`${API_BASE}/health`);
      if (!health.ok()) {
        test.skip();
        return;
      }
    } catch {
      test.skip();
      return;
    }

    // Login to get token
    const loginRes = await request.post(`${API_BASE}/auth/login`, {
      data: { username: "test@example.com", password: "testpassword" },
    });

    if (!loginRes.ok()) {
      test.skip(); // No test user
      return;
    }

    const { access_token } = await loginRes.json();

    // Create pairing request
    const pairRes = await request.post(`${API_BASE}/devices/pair`, {
      headers: { Authorization: `Bearer ${access_token}` },
      data: {
        device_name: "Test POS Terminal",
        device_type: "pos_terminal",
        platform: "playwright-test",
      },
    });

    expect(pairRes.ok()).toBeTruthy();
    const data = await pairRes.json();
    expect(data.pairing_token).toBeTruthy();
    expect(data.device_id).toBeTruthy();
    expect(data.expires_at).toBeTruthy();
  });
});
