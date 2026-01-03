from playwright.sync_api import sync_playwright

def verify_resources():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login as Admin
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")

        # Navigate to Resources Management
        page.goto("http://127.0.0.1:5000/admin/resources")

        # Add a Link Resource
        page.fill("input[name='title']", "Google")
        page.select_option("select[name='type']", "link")
        page.fill("input[name='url']", "https://www.google.com")
        page.click("button:has-text('Add Resource')")

        # Verify Link added
        page.wait_for_selector("text=Google")
        page.screenshot(path="/home/jules/verification/admin_resources_link.png")

        # Add a File Resource (mock file)
        # Create a dummy file
        with open("testfile.txt", "w") as f:
            f.write("This is a test file.")

        page.fill("input[name='title']", "Test File")
        page.select_option("select[name='type']", "file")
        page.set_input_files("input[name='file']", "testfile.txt")
        page.click("button:has-text('Add Resource')")

        # Verify File added
        page.wait_for_selector("text=Test File")
        page.screenshot(path="/home/jules/verification/admin_resources_file.png")

        # Logout
        page.goto("http://127.0.0.1:5000/logout")

        # Login as Candidate
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "candidate")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")

        # Verify Resources on Profile
        page.goto("http://127.0.0.1:5000/profile")
        page.wait_for_selector("text=Google")
        page.wait_for_selector("text=Test File")
        page.screenshot(path="/home/jules/verification/profile_resources.png")

        browser.close()

if __name__ == "__main__":
    verify_resources()
