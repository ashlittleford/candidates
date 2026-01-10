import unittest
from app import create_app, db

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False})
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def test_login_page_attributes(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Check for Username field with new attributes
        self.assertIn('name="username"', html)
        self.assertIn('autocomplete="username"', html)
        self.assertIn('placeholder="Enter your username"', html)

        # Check for Password field with new attributes
        self.assertIn('name="password"', html)
        self.assertIn('autocomplete="current-password"', html)

        print("Login page verified: Contains enhanced attributes.")

if __name__ == '__main__':
    unittest.main()
