import unittest
from app import create_app, db
from app.models import User, Profile, FormationPanel

class TestAdminCreate(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create admin user
            admin = User(username='admin', name='Admin User', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)

            # Create a panel
            panel = FormationPanel(chair_name='Test Chair', members='Test Members')
            db.session.add(panel)

            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_admin(self):
        return self.client.post('/login', data=dict(
            username='admin',
            password='admin123'
        ), follow_redirects=True)

    def test_create_candidate(self):
        self.login_admin()

        # Test GET
        response = self.client.get('/admin/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Candidate', response.data)

        # Test POST
        # Get panel ID
        with self.app.app_context():
            panel = FormationPanel.query.first()
            panel_id = panel.id

        response = self.client.post('/admin/create', data=dict(
            name='New Candidate',
            username='newcandidate',
            password='password123',
            start_date='January 2026',
            presbytery='Generate Presbytery',
            formation_panel_id=panel_id
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user = User.query.filter_by(username='newcandidate').first()
            self.assertIsNotNone(user)
            self.assertFalse(user.is_admin)
            self.assertFalse(user.is_panel_member)
            self.assertIsNotNone(user.profile)
            self.assertEqual(user.name, 'New Candidate')

            # Check profile fields
            self.assertEqual(user.profile.start_date, 'January 2026')
            self.assertEqual(user.profile.presbytery, 'Generate Presbytery')
            self.assertEqual(user.profile.formation_panel_id, panel_id)

    def test_create_panel_member(self):
        self.login_admin()

        # Test GET
        response = self.client.get('/admin/create_panel_member')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Panel Member', response.data)

        with self.app.app_context():
            panel = FormationPanel.query.first()
            panel_id = panel.id

        # Test POST
        response = self.client.post('/admin/create_panel_member', data=dict(
            name='New Panel Member',
            username='newpm',
            password='password123',
            formation_panel_id=panel_id
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user = User.query.filter_by(username='newpm').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.is_panel_member)
            self.assertEqual(user.formation_panel_id, panel_id)

if __name__ == '__main__':
    unittest.main()
