import os
import resend
from flask import render_template


class EmailNotConfiguredError(Exception):
    pass


def send_invitation_email(to_email, name, role, setup_link):
    """
    Sends the account-setup invitation email via Resend.
    Raises EmailNotConfiguredError if RESEND_API_KEY isn't set, so callers
    can fall back to showing the admin the link directly (e.g. in local dev).
    """
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        raise EmailNotConfiguredError('RESEND_API_KEY is not set.')

    resend.api_key = api_key
    from_address = os.environ.get('MAIL_FROM', 'Candidate Portal <onboarding@resend.dev>')

    html = render_template('emails/invite.html', name=name, role=role, setup_link=setup_link)

    resend.Emails.send({
        "from": from_address,
        "to": [to_email],
        "subject": "You're invited to the Uniting Church Candidate Portal",
        "html": html,
    })
