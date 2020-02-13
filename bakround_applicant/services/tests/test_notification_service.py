__author__ = "natesymer"

import pytest
from bakround_applicant.all_models.db import Profile, ProfileEmail, Notification, NotificationRecipient
from bakround_applicant.services.notificationservice.util import ensure_recipient_verified, get_sender_email, build_header_json, get_recipient_email_addresses
from bakround_applicant.services.notificationservice.exceptions import UnspecifiedRecipientException, EmailNotFoundException, UnverifiedNameException

@pytest.mark.django_db
def test_ensure_recipient_verified():
    name_verified = Profile(name_verification_completed=True)
    name_verified.save()

    not_name_verified = Profile(name_verification_completed=False)
    not_name_verified.save()

    noti_a = Notification(type="email", recipient_profile=name_verified)
    noti_a.save()

    noti_b = Notification(type="email", recipient_profile=not_name_verified)
    noti_b.save()

    ensure_recipient_verified(noti_a) # should not raise

    with pytest.raises(UnverifiedNameException):
        ensure_recipient_verified(noti_b)

@pytest.mark.django_db
def test_get_sender_email():
    p = Profile()
    p.save()

    p_invalid = Profile()
    p_invalid.save()

    valid = ProfileEmail(value="asdf@bar.com", profile=p)
    valid.save()
    invalid = ProfileEmail(value="doo@bar.com", profile=p_invalid, bounces=True)
    invalid.save()

    noti_a = Notification(type="email", sender_profile=p)
    noti_a.save()
    noti_b = Notification(type="email", sender_profile=p_invalid)
    noti_b.save()
    noti_c = Notification(type="email", sender_profile=p_invalid, sender_email="foo@bar.com")
    
    assert get_sender_email(noti_a) == valid.value
    assert get_sender_email(noti_b, "fallback") == "fallback"
    assert get_sender_email(noti_c, "fallback") == noti_c.sender_email

def _make_notification(set_recipient_email = False, set_recipient_profile = False):
    n = Notification(type="email")
    if set_recipient_email:
        # This profile won't be used. It's a means of appeasing
        # the DB schema.
        p = Profile()
        p.save()
        pe = ProfileEmail(value="recipient_email@example.com", profile=p)
        pe.save()
        n.recipient_email = pe.value
    if set_recipient_profile:
        p = Profile()
        p.save()
        n.recipient_profile = p
        for addr in ["one@example.com", "two@example.com", "three@example.com"]:
            pe = ProfileEmail(value=addr, profile=p)
            pe.save()
    n.save()

    return n

def _reset():
    ProfileEmail.objects.all().delete()
    Profile.objects.all().delete()
    Notification.objects.all().delete()

def _drive_email_insane(email_address):
    """Takes an email address string or ProfileEmail and marks the corresponding ProfileEmail as bounces.
       This will cause it to be deemed non-sane."""
    if type(email_address) is str:
        pe = ProfileEmail.objects.filter(value=email_address).first()
    else:
        pe = email_address
    pe.bounces = True
    pe.save()

@pytest.mark.django_db
def test_get_recipient_email_addresses():
    # Cases

    # 3. has recipient_profile, has recipient_email
    n_3 = _make_notification(set_recipient_email=True, set_recipient_profile=True)
    emls = get_recipient_email_addresses(n_3)
    assert emls
    assert len(emls) == 1 + ProfileEmail.objects.filter(profile_id=n_3.recipient_profile.id).count()
    assert n_3.recipient_email in emls

    _reset()

    # 4. has no recipient_profile, has recipient_email
    n_4 = _make_notification(set_recipient_email=True, set_recipient_profile=False)
    emls = get_recipient_email_addresses(n_4)
    assert emls
    assert len(emls) == 1
    assert emls[0] == n_4.recipient_email

    _reset()

    # 5. has recipient_profile, has no recipient_email
    n_5 = _make_notification(set_recipient_email=False, set_recipient_profile=True)
    emls = get_recipient_email_addresses(n_5)
    assert emls
    assert len(emls) == ProfileEmail.objects.filter(profile_id=n_5.recipient_profile.id).count()

    _reset()

    # 6.  has neither recipient_{profile,email}
    n_6 = _make_notification(set_recipient_email=False, set_recipient_profile=False)

    with pytest.raises(UnspecifiedRecipientException):
        get_recipient_email_addresses(n_6)

    _reset()

    # 7. recipient_email: non-sane email
    n_7 = _make_notification(set_recipient_email=True, set_recipient_profile=False)
    _drive_email_insane(n_7.recipient_email)

    _reset()

    # 8. recipient_profile: non-sane email
    n_8 = _make_notification(set_recipient_email=True, set_recipient_profile=True)
    for pe in ProfileEmail.objects.filter(profile=n_8.recipient_profile):
        _drive_email_insane(pe)

    emls = get_recipient_email_addresses(n_8)
    assert emls
    assert len(emls) == 1
    assert emls[0] == n_8.recipient_email

    _reset()

    # 9. both: non-sane email ***This is an important test case***
    n_9 = _make_notification(set_recipient_email=True, set_recipient_profile=True)

    reml = ProfileEmail.objects.filter(value=n_9.recipient_email).first()
    if reml:
        reml.bounces = True
        reml.save()

    for pe in ProfileEmail.objects.filter(profile=n_9.recipient_profile):
        pe.bounces = True
        pe.save()

    with pytest.raises(UnspecifiedRecipientException):
        print(get_recipient_email_addresses(n_9))

