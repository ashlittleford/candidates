import os
import resend
from flask import render_template
from app.editable_content import render_content


class EmailNotConfiguredError(Exception):
    pass


def _send(to_email, subject, html):
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        raise EmailNotConfiguredError('RESEND_API_KEY is not set.')

    resend.api_key = api_key
    from_address = os.environ.get('MAIL_FROM', 'Candidate Portal <onboarding@resend.dev>')

    resend.Emails.send({
        "from": from_address,
        "to": [to_email],
        "subject": subject,
        "html": html,
    })


def send_invitation_email(to_email, name, role, setup_link):
    """
    Sends the account-setup invitation email via Resend.
    Raises EmailNotConfiguredError if RESEND_API_KEY isn't set, so callers
    can fall back to showing the admin the link directly (e.g. in local dev).
    """
    intro_key = 'invite_email_panel_member_intro' if role == 'Panel Member' else 'invite_email_candidate_intro'
    intro = render_content(intro_key, name=name, role=role, setup_link=setup_link)
    html = render_template('emails/invite.html', name=name, role=role, setup_link=setup_link, intro=intro)
    _send(to_email, "You're invited to the Uniting Church Candidate Portal", html)


def send_password_reset_email(to_email, name, reset_link, triggered_by_admin=False):
    """
    Sends a password reset email via Resend.
    Raises EmailNotConfiguredError if RESEND_API_KEY isn't set, so callers
    can fall back to showing the admin the link directly (e.g. in local dev).
    """
    intro = render_content('reset_password_email_intro', name=name, reset_link=reset_link)
    html = render_template(
        'emails/reset_password.html', name=name, reset_link=reset_link,
        triggered_by_admin=triggered_by_admin, intro=intro
    )
    _send(to_email, "Reset your Candidate Portal password", html)


def send_custom_email(recipients, subject, body_html):
    """
    Sends the same admin-composed message to each recipient individually
    (never a shared 'to' list, so recipients can't see each other's emails).
    `recipients` is a list of (name, email) tuples.
    Returns a list of (name, email, error) tuples for any that failed to send.
    Raises EmailNotConfiguredError immediately if RESEND_API_KEY isn't set,
    since that would fail identically for every recipient.
    """
    if not os.environ.get('RESEND_API_KEY'):
        raise EmailNotConfiguredError('RESEND_API_KEY is not set.')

    failures = []
    for name, email in recipients:
        html = render_template('emails/custom_message.html', name=name, subject=subject, body=body_html)
        try:
            _send(email, subject, html)
        except Exception as e:
            failures.append((name, email, str(e)))
    return failures
