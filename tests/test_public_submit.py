import unittest
from app import create_app, db
from app.models import User, GlobalSettings, PanelDocument, Profile
import io

class PublicSubmitTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config={'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False})
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a candidate
        self.candidate = User(username='candidate', email='candidate@example.com', name='Test Candidate')
        self.candidate.set_password('password')
        self.profile = Profile(user=self.candidate)
        db.session.add(self.candidate)

        # Create global settings
        self.settings = GlobalSettings(formation_panel_dates="First: 13 Feb 2026")
        db.session.add(self.settings)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_submit_page_loads(self):
        response = self.client.get('/submit-document')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Document', response.data)
        self.assertIn(b'Test Candidate', response.data)

    def test_submit_supervision_report(self):
        data = {
            'user_id': self.candidate.id,
            'document_type': 'supervision_report',
            'file': (io.BytesIO(b"test file content"), 'report.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.day_label, 'Supervision Report')
        self.assertIn('report.pdf', doc.original_filename)

    def test_submit_formation_paper(self):
        data = {
            'user_id': self.candidate.id,
            'document_type': 'formation_paper',
            'day_label': 'First',
            'file': (io.BytesIO(b"test file content"), 'paper.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.day_label, 'First')

    def test_submit_formation_paper_missing_day(self):
        data = {
            'user_id': self.candidate.id,
            'document_type': 'formation_paper',
            'file': (io.BytesIO(b"test file content"), 'paper.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please select a formation day.', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNone(doc)

if __name__ == '__main__':
    unittest.main()
