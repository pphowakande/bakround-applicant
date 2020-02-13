__author__ = "natesymer"

import json
from bakround_applicant.all_models.db import Profile, ProfileEmail, ProfilePhoneNumber, \
                                             NotificationBouncedEmail, NotificationRecipientEvent
from bakround_applicant.webhooks.utils import update_email_status_from_sendgrid

def add_contact(cls, value, profile_id, is_correct_person = False):
    if not value:
        return None

    if not profile_id:
        return None

    e = cls.objects.filter(value=value, profile_id=profile_id).first()
    if not e:
        e = cls(value=value, profile_id=profile_id)
    e.is_correct_person = is_correct_person
    e.save()

    # TODO: synchronize with other ProfileEmail's or ProfilePhoneNumber's

    if cls is ProfileEmail:
        collect_email_data(e)

    return e

def verify_sane(cls, value, assume_sane = False):
    """Return if value is sane for cls. Returns True if value is not in the DB."""
    rec = cls.objects.filter(value=value).first()
    return (rec and rec.sane) or (assume_sane and not rec)

def collect_email_data(pe, delete_records = True):
    if type(pe) is str:
        v = ProfileEmail.objects.filter(value=pe).first() # TODO: collect for all email records with same value.
        if not v:
            p = Profile()
            p.save()
            collect_email_data(add_contact(ProfileEmail, pe, p.id))
        else:
            collect_email_data(v)
        return

    if NotificationBouncedEmail.objects.filter(email=pe.value).exists():
        pe.bounces = True
        pe.save(update_fields=['bounces'])

    # Replay email events for a given email address and update the ProfileEmail
    for recipient_event in NotificationRecipientEvent.objects.filter(email=pe.value).order_by('date_created'):
        event = recipient_event.action
        update_email_status_from_sendgrid(pe.value, event)

    if delete_records:
        NotificationRecipientEvent.objects.filter(email=pe.value).delete()
        NotificationBouncedEmail.objects.filter(email=pe.value).delete()

def collect_contact_info_for_profile(profile):
    # We deleted the Profile.email field.
    
    if profile and hasattr(profile, 'phone') and profile.phone:
        add_contact(ProfilePhoneNumber, profile.phone, profile.id, True)
        profile.phone = None
        profile.save(update_fields=['phone'])

