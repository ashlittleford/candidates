import unittest
from app import create_app, db
from app.models import User, Profile, FormationPanel

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False # Disable CSRF for testing forms easily if using WTForms (not used here but good practice)
        }
        self.app = create_app(test_config)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create Admin
            admin = User(username='admin', name='Admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)

            # Create Candidate
            candidate = User(username='candidate', name='Candidate', is_admin=False)
            candidate.set_password('candidate')
            profile = Profile(user=candidate)
            db.session.add(candidate)
            db.session.add(profile)

            # Create a Panel
            panel = FormationPanel(chair_name='Rev. Test', members='Member 1, Member 2')
            db.session.add(panel)

            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        response = self.login('candidate', 'candidate')
        self.assertIn(b'Formation Details', response.data)
        self.assertIn(b'Welcome, Candidate', response.data)

        response = self.logout()
        self.assertIn(b'Login', response.data)

    def test_admin_access(self):
        # Login as candidate
        self.login('candidate', 'candidate')
        response = self.client.get('/admin', follow_redirects=True)
        # Should be denied and redirected to profile or shown error (my logic redirects)
        self.assertIn(b'Access denied', response.data)
        self.assertIn(b'Formation Details', response.data)

        self.logout()

        # Login as admin
        response = self.login('admin', 'admin')
        self.assertIn(b'Admin Dashboard', response.data)

        response = self.client.get('/admin')
        self.assertIn(b'Admin Dashboard', response.data)

    def test_profile_access(self):
        self.login('candidate', 'candidate')
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Formation Details', response.data)

    def test_admin_edit_profile(self):
        self.login('admin', 'admin')

        # Get candidate id and panel id
        with self.app.app_context():
            candidate = User.query.filter_by(username='candidate').first()
            candidate_id = candidate.id
            panel = FormationPanel.query.first()
            panel_id = panel.id

        response = self.client.post(f'/admin/edit/{candidate_id}', data=dict(
            name='Updated Name',
            formation_panel_id=panel_id,
            formation_days_completed='Day 1',
            walking_on_country='on', # Checkbox sends 'on' if checked
            upcoming_formation_dates='Tomorrow',
            formation_panel_dates='Jan, Feb, Mar'
        ), follow_redirects=True)

        self.assertIn(b'User updated successfully', response.data)

        # Verify changes in DB
        with self.app.app_context():
            updated_candidate = User.query.get(candidate_id)
            self.assertEqual(updated_candidate.name, 'Updated Name')
            self.assertEqual(updated_candidate.profile.formation_panel.chair_name, 'Rev. Test')
            self.assertTrue(updated_candidate.profile.walking_on_country)

if __name__ == '__main__':
    unittest.main()
