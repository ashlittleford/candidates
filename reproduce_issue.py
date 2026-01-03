import unittest
from app import create_app, db
from app.models import User, Profile

class ReproduceIssueTestCase(unittest.TestCase):
    def setUp(self):
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False
        }
        self.app = create_app(test_config)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            user = User(username='testuser', name='Test User')
            user.set_password('password')
            profile = Profile(user=user, presbytery='Test Presbytery', current_church='My Test Church')
            db.session.add(user)
            db.session.add(profile)
            db.session.commit()

    def login(self):
        return self.client.post('/login', data=dict(
            username='testuser',
            password='password'
        ), follow_redirects=True)

    def test_current_church_display_and_form(self):
        self.login()
        response = self.client.get('/profile')
        html = response.data.decode('utf-8')

        # Check if 'My Test Church' is displayed
        if 'My Test Church' not in html:
            print("ISSUE: 'My Test Church' value not found in profile page.")
        else:
            print("SUCCESS: 'My Test Church' value found in profile page.")

        # Check for update form
        if 'action="/profile/update_church"' not in html:
            print("ISSUE: update_church form not found in profile page.")
        else:
            print("SUCCESS: update_church form found in profile page.")

if __name__ == '__main__':
    unittest.main()
