from app import create_app, db
from app.models import GlobalSettings

app = create_app()

with app.app_context():
    settings = GlobalSettings.query.first()
    if settings:
        settings.upcoming_formation_dates = "Monday 2 March 2026, Monday 13 April 2026, Monday 4 May 2026, Monday 1 June 2026, Monday 3 August 2026, Monday 7 September 2026, Monday 12 October 2026, Monday 2 November 2026"
        settings.formation_panel_dates = "First: Friday 13 February 2026, Second: Friday 19 June 2026, Third: Friday 20 November 2026"
        db.session.commit()
        print("Global settings updated with 2026 dates.")
    else:
        print("No global settings found to update.")
