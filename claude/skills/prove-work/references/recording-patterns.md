# Recording Patterns

Guidance for choosing what to record based on the type of change.

## Contents
- [Change type mapping](#change-type-mapping)
- [Interaction patterns](#interaction-patterns)
- [Timing guidelines](#timing-guidelines)
- [Script template](#script-template)

## Change Type Mapping

| Change Type | What to Record | Key Interactions |
|---|---|---|
| New page/route | Navigate to the page, scroll through it | `goto`, `wait`, slow scroll |
| Form changes | Fill the form, submit, show result | `fill`, `click` submit, wait for feedback |
| Component changes | Navigate to page with component, interact | `click`, `hover`, toggle states |
| Styling/layout | Navigate to affected pages, scroll | `goto`, slow scroll, pause on key areas |
| Modal/dialog | Trigger the modal, interact, close | `click` trigger, interact with modal, close |
| Table/list | Navigate to list, sort/filter/paginate | `click` headers, filter controls, pagination |
| Auth flow | Show login/signup/logout sequence | `fill` credentials, `click` submit, wait for redirect |
| API/backend only | Not visually demonstrable | Exit with message |
| Config/infra | Not visually demonstrable | Exit with message |
| Bug fix | Reproduce the fixed scenario | Navigate to the affected area, perform the action that was broken |

## Interaction Patterns

### Scrolling to show content

```python
# Slow scroll to show full page content
for _ in range(5):
    page.mouse.wheel(0, 300)
    time.sleep(0.4)
```

### Waiting for dynamic content

```python
page.wait_for_load_state("networkidle")
time.sleep(0.5)  # Let animations settle
```

### Highlighting an element before clicking

```python
# Hover before clicking to show intent
page.hover("button[name='Save']")
time.sleep(0.3)
page.click("button[name='Save']")
```

### Showing before/after states

```python
# Pause on initial state
time.sleep(1.5)

# Make the change
page.fill("#name", "New Value")
page.click("button:text('Save')")

# Pause on result
page.wait_for_selector("text=Saved successfully")
time.sleep(1.5)
```

## Timing Guidelines

| Phase | Duration | Purpose |
|---|---|---|
| Initial page load | 1-2 seconds | Show starting state |
| Between actions | 0.3-0.5 seconds | Natural pacing, visible intent |
| After key action | 1-1.5 seconds | Show result/feedback |
| Final state | 1.5-2 seconds | Hold on end result |
| Total recording | 5-15 seconds | Keep GIF under 10MB |

Avoid recordings longer than 15 seconds. If the flow is longer, focus on the most important interaction.

## Script Template

Standard structure for interaction scripts:

```python
"""Prove-work interaction script -- auto-generated"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        record_video_dir="/tmp/prove-work/",
        record_video_size={"width": 1280, "height": 720},
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # --- Navigate and wait ---
    page.goto("http://localhost:PORT/ROUTE")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # --- Demonstrate the feature ---
    # [Claude fills this section based on context]

    # --- Hold on final state ---
    time.sleep(1.5)

    # --- Finalize recording ---
    context.close()
    browser.close()
```

### Playwright install check

Before running interaction scripts, verify Playwright browsers are installed:

```bash
python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch(headless=True).close()" 2>/dev/null || python3 -m playwright install chromium
```
