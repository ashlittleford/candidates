from playwright.sync_api import sync_playwright

def verify_changes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login as candidate to view profile
        page.goto("http://localhost:5000/login")
        page.fill("input[name='username']", "candidate")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")

        # Check Profile Page
        page.wait_for_selector("h1")

        # Take screenshot of the top part (Header with Start Date)
        page.screenshot(path="verification_profile_header.png", clip={"x":0, "y":0, "width":1200, "height":400})

        # Take screenshot of the progress section (Mid-Term Panel)
        # We need to find the element containing "Mid-Term Panel"
        mid_term_element = page.locator("text=Mid-Term Panel")
        if mid_term_element.count() > 0:
            # Scroll to it
            mid_term_element.first.scroll_into_view_if_needed()
            page.screenshot(path="verification_profile_progress.png")

        browser.close()

if __name__ == "__main__":
    verify_changes()
