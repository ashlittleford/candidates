from playwright.sync_api import sync_playwright

def verify_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login as Admin
        print("Logging in as Admin...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")

        # Verify dashboard
        page.wait_for_selector("text=Admin Dashboard")
        print("Admin Dashboard loaded.")

        # 2. Go to Formation Panels
        print("Navigating to Formation Panels...")
        page.click("text=Manage Formation Panels")
        page.wait_for_selector("text=Formation Panels")
        page.screenshot(path="/home/jules/verification/admin_panels_list.png")

        # 3. Create a new Panel
        print("Creating new panel...")
        page.click("text=Add New Panel")
        page.fill("input[name='chair_name']", "Verification Chair")
        page.fill("textarea[name='members']", "Member A, Member B")
        page.click("button:text('Save')")

        # Verify it appears in list
        page.wait_for_selector("text=Verification Chair")
        print("New panel created.")

        # 4. Edit Candidate to assign this panel
        print("Editing candidate...")
        page.goto("http://127.0.0.1:5000/admin")
        # Find the row for 'candidate' or click Edit Profile for the first non-admin user
        page.click("text=Edit Profile") # Assuming only one candidate 'John Doe'

        # Select the new panel
        # Use page.select_option with the label or value. Since we don't know the ID easily,
        # let's assume it's the last one or search by text.
        # Actually, let's just select the one we created by label if possible, or index.
        # But select_option takes value or label.
        # Let's try selecting by label "Chair: Verification Chair"
        page.select_option("select[name='formation_panel_id']", label="Chair: Verification Chair")

        page.click("button:text('Save Changes')")
        print("Candidate updated.")

        # 5. Logout
        page.click("text=Logout")

        # 6. Login as Candidate
        print("Logging in as Candidate...")
        page.fill("input[name='username']", "candidate")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")

        # 7. Verify Panel Details on Profile
        print("Verifying profile...")
        page.wait_for_selector("text=Verification Chair")
        page.wait_for_selector("text=Member A")
        page.wait_for_selector("text=Member B")

        # Take final screenshot
        page.screenshot(path="/home/jules/verification/candidate_profile_panel.png")
        print("Verification complete. Screenshot saved.")

        browser.close()

if __name__ == "__main__":
    verify_app()
