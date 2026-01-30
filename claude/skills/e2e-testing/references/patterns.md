# Advanced Playwright Patterns

## Network Mocking and Interception

### Mock API Responses

```typescript
test("displays error when API fails", async ({ page }) => {
  await page.route("**/api/users", (route) => {
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: "Internal Server Error" }),
    });
  });

  await page.goto("/users");
  await expect(page.getByText("Failed to load users")).toBeVisible();
});
```

### Intercept and Modify Requests

```typescript
test("can modify API request", async ({ page }) => {
  await page.route("**/api/users", async (route) => {
    const request = route.request();
    const postData = JSON.parse(request.postData() || "{}");

    // Modify request
    postData.role = "admin";

    await route.continue({
      postData: JSON.stringify(postData),
    });
  });

  // Test continues...
});
```

### Mock Third-Party Services

```typescript
test("payment flow with mocked Stripe", async ({ page }) => {
  await page.route("**/api/stripe/**", (route) => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        id: "mock_payment_id",
        status: "succeeded",
      }),
    });
  });

  // Test payment flow with mocked response
});
```

## Fixtures for Test Data

```typescript
// fixtures/test-data.ts
import { test as base } from "@playwright/test";

type TestData = {
  testUser: { email: string; password: string; name: string };
  adminUser: { email: string; password: string };
};

export const test = base.extend<TestData>({
  testUser: async ({}, use) => {
    const user = {
      email: `test-${Date.now()}@example.com`,
      password: "Test123!@#",
      name: "Test User",
    };
    // Setup: Create user in database
    await createTestUser(user);
    await use(user);
    // Teardown: Clean up user
    await deleteTestUser(user.email);
  },

  adminUser: async ({}, use) => {
    await use({
      email: "admin@example.com",
      password: process.env.ADMIN_PASSWORD!,
    });
  },
});

// Usage in tests
import { test } from "./fixtures/test-data";

test("user can update profile", async ({ page, testUser }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(testUser.email);
  await page.getByLabel("Password").fill(testUser.password);
  await page.getByRole("button", { name: "Login" }).click();

  await page.goto("/profile");
  await page.getByLabel("Name").fill("Updated Name");
  await page.getByRole("button", { name: "Save" }).click();

  await expect(page.getByText("Profile updated")).toBeVisible();
});
```

## Visual Regression Testing

```typescript
import { test, expect } from "@playwright/test";

test("homepage looks correct", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveScreenshot("homepage.png", {
    fullPage: true,
    maxDiffPixels: 100,
  });
});

test("button in all states", async ({ page }) => {
  await page.goto("/components");

  const button = page.getByRole("button", { name: "Submit" });

  // Default state
  await expect(button).toHaveScreenshot("button-default.png");

  // Hover state
  await button.hover();
  await expect(button).toHaveScreenshot("button-hover.png");

  // Disabled state
  await button.evaluate((el) => el.setAttribute("disabled", "true"));
  await expect(button).toHaveScreenshot("button-disabled.png");
});
```

## Parallel Testing with Sharding

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: "shard-1",
      use: { ...devices["Desktop Chrome"] },
      grepInvert: /@slow/,
      shard: { current: 1, total: 4 },
    },
    {
      name: "shard-2",
      use: { ...devices["Desktop Chrome"] },
      shard: { current: 2, total: 4 },
    },
    // ... more shards
  ],
});

// Run in CI
// npx playwright test --shard=1/4
// npx playwright test --shard=2/4
```

## Accessibility Testing

```typescript
// Install: npm install @axe-core/playwright
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("page should not have accessibility violations", async ({ page }) => {
  await page.goto("/");

  const accessibilityScanResults = await new AxeBuilder({ page })
    .exclude("#third-party-widget")
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
});

test("form is accessible", async ({ page }) => {
  await page.goto("/signup");

  const results = await new AxeBuilder({ page }).include("form").analyze();

  expect(results.violations).toEqual([]);
});
```

## Element Discovery Script

For reconnaissance on dynamic pages:

```python
#!/usr/bin/env python3
"""Discover interactive elements on a page."""

from playwright.sync_api import sync_playwright

def discover_elements(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')

        # Find all buttons
        buttons = page.locator('button').all()
        print(f"\nButtons ({len(buttons)}):")
        for btn in buttons:
            text = btn.inner_text().strip()[:50]
            print(f"  - {text or '[no text]'}")

        # Find all links
        links = page.locator('a').all()
        print(f"\nLinks ({len(links)}):")
        for link in links[:10]:
            text = link.inner_text().strip()[:30]
            href = link.get_attribute('href')
            print(f"  - {text or '[no text]'} -> {href}")

        # Find all inputs
        inputs = page.locator('input, textarea, select').all()
        print(f"\nInputs ({len(inputs)}):")
        for inp in inputs:
            name = inp.get_attribute('name') or inp.get_attribute('id')
            type_ = inp.get_attribute('type') or 'text'
            print(f"  - {name or '[unnamed]'} ({type_})")

        # Take screenshot
        page.screenshot(path='/tmp/page.png', full_page=True)
        print(f"\nScreenshot saved to /tmp/page.png")

        browser.close()

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    discover_elements(url)
```

## Handling Auth0 and iFrames

```typescript
test("Auth0 login", async ({ page }) => {
  await page.goto("/login");

  // Click login button that opens Auth0
  await page.getByRole("button", { name: "Login" }).click();

  // Auth0 opens in a frame or redirects
  // Wait for Auth0 domain
  await page.waitForURL(/auth0\.com/);

  // Fill Auth0 form
  await page.getByLabel("Email").fill(process.env.TEST_USER!);
  await page.getByLabel("Password").fill(process.env.TEST_PASSWORD!);
  await page.getByRole("button", { name: "Continue" }).click();

  // Wait for redirect back
  await page.waitForURL(/localhost/);

  await expect(page.getByText("Welcome")).toBeVisible();
});

// For Auth0 in iframe
test("Auth0 in iframe", async ({ page }) => {
  await page.goto("/login");

  // Get iframe
  const frame = page.frameLocator('iframe[src*="auth0"]');

  await frame.getByLabel("Email").fill(process.env.TEST_USER!);
  await frame.getByLabel("Password").fill(process.env.TEST_PASSWORD!);
  await frame.getByRole("button", { name: "Continue" }).click();
});
```

## Multi-Candidate Selector Strategy

For elements that might have different selectors across environments:

```typescript
async function clickByMultipleCandidates(page: Page, candidates: string[]) {
  for (const selector of candidates) {
    try {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        await element.click();
        return;
      }
    } catch {
      continue;
    }
  }
  throw new Error(`None of the candidate selectors found: ${candidates.join(", ")}`);
}

// Usage
await clickByMultipleCandidates(page, [
  '[data-testid="submit-btn"]',
  'button:has-text("Submit")',
  '.submit-button',
  '#submit',
]);
```

## Console Log Capture

```typescript
test("capture console logs", async ({ page }) => {
  const logs: string[] = [];

  page.on("console", (msg) => {
    logs.push(`${msg.type()}: ${msg.text()}`);
  });

  await page.goto("/");

  // Check for errors
  const errors = logs.filter((l) => l.startsWith("error"));
  expect(errors).toHaveLength(0);
});
```

## Waiting for Multiple Conditions

```typescript
// Wait for multiple conditions
await Promise.all([
  page.waitForURL("/success"),
  page.waitForLoadState("networkidle"),
  expect(page.getByText("Payment successful")).toBeVisible(),
]);

// Wait for network request AND response
const [request, response] = await Promise.all([
  page.waitForRequest((req) => req.url().includes("/api/checkout")),
  page.waitForResponse((res) => res.url().includes("/api/checkout")),
  page.getByRole("button", { name: "Pay" }).click(),
]);

expect(response.status()).toBe(200);
```
