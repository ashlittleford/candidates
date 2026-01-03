import unittest
from app import create_app, db
from app.models import User, Profile

class FormationTallyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config={
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_formation_days_tally_integer(self):
        u = User(username='test', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "5"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 5)
        self.assertEqual(p.formation_days_list_items, [])

    def test_formation_days_tally_comma_list(self):
        u = User(username='test2', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "Jan 1, Feb 2, Mar 3"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 3)
        self.assertEqual(p.formation_days_list_items, ["Jan 1", "Feb 2", "Mar 3"])

    def test_formation_days_tally_newline_list(self):
        u = User(username='test3', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "Jan 1\nFeb 2\nMar 3"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 3)
        self.assertEqual(p.formation_days_list_items, ["Jan 1", "Feb 2", "Mar 3"])

    def test_formation_days_tally_mixed(self):
        # Mixed newlines and commas.
        # Since newlines are present, it should split by newline only.
        # "Jan 1, Feb 2" becomes one item, "Mar 3" becomes another.
        u = User(username='test4', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "Jan 1, Feb 2\nMar 3"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 2)
        self.assertEqual(p.formation_days_list_items, ["Jan 1, Feb 2", "Mar 3"])

    def test_formation_days_tally_empty(self):
        u = User(username='test5', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = ""
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 0)
        self.assertEqual(p.formation_days_list_items, [])

    def test_formation_days_tally_digits_with_spaces(self):
        # " 5 " should be treated as 5
        u = User(username='test6', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = " 5 "
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 5)
        self.assertEqual(p.formation_days_list_items, [])

if __name__ == '__main__':
    unittest.main()
