---
name: e2e-testing
description: Use when implementing E2E tests, debugging flaky tests, testing web applications with Playwright, or establishing E2E testing standards. Triggers on "e2e test", "end-to-end", "Playwright", "flaky test", "browser test".
---

# E2E Testing with Playwright

Build reliable, fast E2E test suites that catch regressions and enable confident deployments.

## Quick Start

**Test a local web application:**

```bash
# If server not running, use the helper script
python scripts/with_server.py --server "npm run dev" --port 3000 -- python your_test.py

# If server already running, write Playwright directly
```

**Basic Playwright test:**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle')  # CRITICAL: Wait for JS

    # Reconnaissance first
    page.screenshot(path='/tmp/inspect.png', full_page=True)

    # Then actions
    page.get_by_role('button', name='Login').click()
    browser.close()
```

## When to Use E2E Tests

**Good for:**
- Critical user journeys (login, checkout, signup)
- Complex interactions (drag-and-drop, multi-step forms)
- Cross-browser compatibility
- Real API integration
- Authentication flows

**Not for:**
- Unit-level logic (use unit tests)
- API contracts (use integration tests)
- Every edge case (too slow)
- Internal implementation details

## Decision Tree

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly for selectors
    │         └─ Write Playwright script using selectors
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Use scripts/with_server.py
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["html"], ["github"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile", use: { ...devices["iPhone 13"] } },
  ],
});
```

## Page Object Model

Encapsulate page logic in classes:

```typescript
// pages/LoginPage.ts
import { Page, Locator } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel("Email");
    this.passwordInput = page.getByLabel("Password");
    this.loginButton = page.getByRole("button", { name: "Login" });
  }

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

// Usage in tests
test("successful login", async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login("user@example.com", "password123");
  await expect(page).toHaveURL("/dashboard");
});
```

## Selectors (Priority Order)

1. **Role-based (best):** `page.getByRole('button', { name: 'Submit' })`
2. **Label (for forms):** `page.getByLabel('Email')`
3. **Placeholder:** `page.getByPlaceholder('Search...')`
4. **Test ID:** `page.getByTestId('submit-button')`
5. **Text:** `page.getByText('Welcome')`
6. **CSS (avoid):** `page.locator('.btn-primary')` - brittle!

**Multi-candidate strategy for Auth0/iframes:**

```typescript
// Frame-aware selectors
const frame = page.frameLocator('[data-testid="auth0-frame"]');
await frame.getByRole('textbox', { name: 'Email' }).fill(email);
```

## Waiting Strategies

```typescript
// BAD: Fixed timeouts
await page.waitForTimeout(3000); // Flaky!

// GOOD: Wait for specific conditions
await page.waitForLoadState("networkidle");
await page.waitForURL("/dashboard");

// BETTER: Auto-waiting with assertions
await expect(page.getByText("Welcome")).toBeVisible();
await expect(page.getByRole("button")).toBeEnabled();

// Wait for API response
const responsePromise = page.waitForResponse(
  (res) => res.url().includes("/api/users") && res.status() === 200
);
await page.getByRole("button", { name: "Load" }).click();
await responsePromise;
```

## Authentication

**Storage state for pre-auth (recommended):**

```typescript
// global-setup.ts
async function globalSetup() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto("/login");
  await page.getByLabel("Email").fill(process.env.TEST_USER!);
  await page.getByLabel("Password").fill(process.env.TEST_PASSWORD!);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL("/dashboard");

  await page.context().storageState({ path: "auth.json" });
  await browser.close();
}

// playwright.config.ts
use: {
  storageState: "auth.json",
}
```

## Debugging

```bash
# Headed mode
npx playwright test --headed

# Debug mode (step through)
npx playwright test --debug

# Pause in test
await page.pause();  # Opens inspector

# Trace viewer
npx playwright show-trace trace.zip
```

**Add test steps for reporting:**

```typescript
test('checkout flow', async ({ page }) => {
  await test.step('Add item to cart', async () => {
    await page.goto('/products');
    await page.getByRole('button', { name: 'Add to Cart' }).click();
  });

  await test.step('Proceed to checkout', async () => {
    await page.goto('/cart');
    await page.getByRole('button', { name: 'Checkout' }).click();
  });
});
```

## Flaky Test Prevention

| Cause | Fix |
|-------|-----|
| Fixed timeouts | Use proper waits (networkidle, assertions) |
| Race conditions | Wait for specific state before acting |
| Test interdependence | Make tests independent, clean up data |
| Stale selectors | Use role-based selectors, avoid CSS classes |
| Animation interference | Wait for animations, disable in test mode |

**Root cause checklist:**
- [ ] Using `waitForTimeout()` anywhere? Replace with proper waits
- [ ] Tests share state? Add proper setup/teardown
- [ ] Selectors rely on CSS classes? Use role/label/testid
- [ ] Network timing issues? Wait for specific responses

## Scripts Reference

**`scripts/with_server.py`** - Server lifecycle management

```bash
# Single server
python scripts/with_server.py --server "npm run dev" --port 3000 -- python test.py

# Multiple servers (backend + frontend)
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python test.py
```

Run `python scripts/with_server.py --help` first.

## Common Pitfalls

- **Inspecting DOM before networkidle:** Always wait for JS to execute on dynamic apps
- **Brittle CSS selectors:** Avoid `.btn.btn-primary`, use roles
- **Tests depend on order:** Each test must be independent
- **No cleanup:** Create and destroy test data per test
- **Over-testing with E2E:** Use unit tests for edge cases

## Reference Files

For advanced Playwright patterns, see:
- **[references/patterns.md](references/patterns.md)** - Network mocking, visual regression, fixtures
