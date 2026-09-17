from flask import render_template_string
from app.models import EditableContent

EDITABLE_CONTENT_DEFAULTS = {
    'invite_email_candidate_intro': {
        'label': 'Invite Email — Candidate',
        'description': "Shown in the invitation email sent to a new candidate. {{ name }} is available.",
        'default': (
            "You've been invited to join the Candidate Portal as a <strong>Candidate</strong>. The portal is "
            "where you'll track your formation progress, RSVP to upcoming formation days, upload documents "
            "and reports for your formation panel, and see key dates and resources relevant to your journey."
        ),
    },
    'invite_email_panel_member_intro': {
        'label': 'Invite Email — Panel Member',
        'description': "Shown in the invitation email sent to a new panel member. {{ name }} is available.",
        'default': (
            "You've been invited to join the Candidate Portal as a <strong>Formation Panel Member</strong>. "
            "From your dashboard you'll be able to see the candidates assigned to your panel, review their "
            "submitted documents and reports, and record RSVPs for upcoming formation panel dates."
        ),
    },
    'reset_password_email_intro': {
        'label': 'Password Reset Email',
        'description': "Shown in the password reset email, whether self-requested or sent by an admin. {{ name }} is available.",
        'default': "Click below to set a new password for your Candidate Portal account.",
    },
    'setup_account_intro': {
        'label': 'Account Setup Screen',
        'description': "Shown on the account setup page a new candidate lands on after clicking their invite link.",
        'default': (
            "<ul class=\"mb-0 small\">\n"
            "<li>Your <strong>Formation Progress</strong> tab tracks your standards, academic requirements, and formation days.</li>\n"
            "<li>RSVP to upcoming formation days and formation panel dates as they're announced.</li>\n"
            "<li>Upload documents and reports for your formation panel under <strong>My Documents</strong>.</li>\n"
            "<li>Your panel and presbytery have already been assigned by an admin &mdash; you'll see them on your profile once you're set up.</li>\n"
            "</ul>"
        ),
    },
}


def get_raw_content(key):
    """The saved override for `key`, or its hardcoded default if never customized."""
    row = EditableContent.query.filter_by(key=key).first()
    if row:
        return row.content
    return EDITABLE_CONTENT_DEFAULTS[key]['default']


def render_content(key, **context):
    """The content for `key`, rendered through Jinja so {{ variables }} still work."""
    return render_template_string(get_raw_content(key), **context)
