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

    def test_formation_days_tally_mixed_integer_and_text(self):
        # "5\nMonday 2nd March" -> 5 + 1 = 6
        u = User(username='test7', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "5\nMonday 2nd March"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 6)
        # Note: "5" is still part of the items list
        self.assertEqual(p.formation_days_list_items, ["5", "Monday 2nd March"])

    def test_formation_days_tally_multiple_integers(self):
        # "2\n3" -> 2 + 3 = 5
        u = User(username='test8', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "2\n3"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 5)
        self.assertEqual(p.formation_days_list_items, ["2", "3"])

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
        # Updated logic: Treat both newlines and commas as separators.
        # "Jan 1, Feb 2" becomes two items, "Mar 3" becomes another. Total 3.
        u = User(username='test4', password_hash='test')
        p = Profile(user=u)
        p.formation_days_completed = "Jan 1, Feb 2\nMar 3"
        db.session.add(u)
        db.session.add(p)
        db.session.commit()

        self.assertEqual(p.computed_formation_days_count, 3)
        self.assertEqual(p.formation_days_list_items, ["Jan 1", "Feb 2", "Mar 3"])

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
