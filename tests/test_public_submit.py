import unittest
import shutil
import tempfile
from app import create_app, db
from app.models import User, GlobalSettings, PanelDocument, Profile
import io

class PublicSubmitTestCase(unittest.TestCase):
    def setUp(self):
        self.upload_folder = tempfile.mkdtemp()
        self.app = create_app(test_config={'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False, 'UPLOAD_FOLDER': self.upload_folder})
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
        shutil.rmtree(self.upload_folder, ignore_errors=True)

    def test_submit_page_loads(self):
        response = self.client.get('/submit-document')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Document', response.data)
        self.assertIn(b'Test Candidate', response.data)

    def test_submit_supervisors_report(self):
        data = {
            'user_id': self.candidate.id,
            'submission_type': 'formation_panel_paper',
            'category': 'Supervisors Report',
            'file': (io.BytesIO(b"test file content"), 'report.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.category, 'Supervisors Report')
        self.assertEqual(doc.source, 'panel_member')
        self.assertIn('report.pdf', doc.original_filename)

    def test_submit_report_with_formation_day(self):
        data = {
            'user_id': self.candidate.id,
            'submission_type': 'formation_panel_paper',
            'category': 'Report',
            'day_label': 'First',
            'file': (io.BytesIO(b"test file content"), 'paper.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.category, 'Report')
        self.assertEqual(doc.day_label, 'First')
        self.assertEqual(doc.source, 'panel_member')

    def test_submit_multiple_files(self):
        data = {
            'user_id': self.candidate.id,
            'submission_type': 'formation_panel_paper',
            'category': 'Study Plan',
            'file': [
                (io.BytesIO(b"first file content"), 'plan1.pdf'),
                (io.BytesIO(b"second file content"), 'plan2.pdf'),
            ]
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        docs = PanelDocument.query.filter_by(user_id=self.candidate.id).all()
        self.assertEqual(len(docs), 2)
        self.assertTrue(all(doc.category == 'Study Plan' for doc in docs))

    def test_submit_panel_report(self):
        data = {
            'user_id': self.candidate.id,
            'submission_type': 'panel_report',
            'category': 'Mid-Term',
            'day_label': 'First',
            'file': (io.BytesIO(b"test file content"), 'panel_report.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document submitted successfully!', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.category, 'Mid-Term')
        self.assertIsNone(doc.day_label)
        self.assertEqual(doc.source, 'panel_member')

    def test_submit_missing_category(self):
        data = {
            'user_id': self.candidate.id,
            'submission_type': 'formation_panel_paper',
            'file': (io.BytesIO(b"test file content"), 'paper.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please select a candidate, submission type, and document category.', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNone(doc)

    def test_submit_missing_submission_type(self):
        data = {
            'user_id': self.candidate.id,
            'category': 'Report',
            'file': (io.BytesIO(b"test file content"), 'paper.pdf')
        }
        response = self.client.post('/submit-document', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please select a candidate, submission type, and document category.', response.data)

        doc = PanelDocument.query.filter_by(user_id=self.candidate.id).first()
        self.assertIsNone(doc)

if __name__ == '__main__':
    unittest.main()
