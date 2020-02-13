__author__ = "natesymer"

import os
from django.conf import settings
from django.utils import timezone
import pytest
import json
from piplapis.search import SearchAPIResponse

from datetime import timedelta, datetime

# TODO: Test these three imports
from bakround_applicant.verifier.lookup_brokers import PiplLookupBroker, AmbiguousLookupException, \
                                                       UnexpectedOutputException, LookupFailedException, \
                                                       get_valid_search_pointer_from_pipl_response, GenericLookupBroker
from bakround_applicant.services.verifyingservice.util import add_contact, verify_sane, collect_email_data, collect_contact_info_for_profile
from bakround_applicant.services.verifyingservice.consumer import Consumer
from bakround_applicant.all_models.db import ProfileEmail, ProfilePhoneNumber, Profile, NotificationBouncedEmail, NotificationRecipientEvent, ProfileExternalData, ProfileReverseLookup

# Test the ProfileEmail and ProfilePhoneNumber models

# TODO: test ProfilePhoneNumber model

@pytest.mark.django_db
def test_profile_email_sanity():
    p = Profile()
    p.save()
    VALID_EMAIL = "foo@bar.com"
    INVALID_EMAIL = "invalid@failure.com"

    # Invalid emails
    a = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=False, reported_spam=False)
    b = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=True, reported_spam=False)
    c = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=False, reported_spam=True)
    d = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=True, reported_spam=False)
    e = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=True, reported_spam=True)
    f = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=True, reported_spam=True)
    g = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, is_correct_person=True)

    # Valid emails
    h = ProfileEmail(value=VALID_EMAIL, profile=p, bounces=False, unsubscribed=False, reported_spam=False)

    for email in [a,b,c,d,e,f,g,h]:
        email.save()

    assert not a.sane
    assert not b.sane
    assert not c.sane
    assert not d.sane
    assert not e.sane
    assert not f.sane
    assert not g.sane
    assert h.sane

    sane = ProfileEmail.all_sane()
    assert len(sane) == 1
    assert sane.first().value == VALID_EMAIL

@pytest.mark.django_db
def test_no_valid_emails():
    p = Profile()
    p.save()
    INVALID_EMAIL = "invalid@failure.com"

    # Invalid emails
    a = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=False, reported_spam=False)
    b = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=True, reported_spam=False)
    c = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=False, reported_spam=True)
    d = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=True, reported_spam=False)
    e = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=False, unsubscribed=True, reported_spam=True)
    f = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, unsubscribed=True, reported_spam=True)
    g = ProfileEmail(value=INVALID_EMAIL, profile=p, bounces=True, is_correct_person=True)

    for email in [a,b,c,d,e,f,g]:
        email.save()

    assert ProfileEmail.to_reach(p.id) is None

@pytest.mark.django_db
def test_email_to_reach_valid_before_invalid():
    """Test to make sure ProfileEmail.to_reach only returns sane emails."""
    p = Profile()
    p.save()

    a = ProfileEmail(value="invalid@foo.com", profile=p, bounces=True, unsubscribed=False, reported_spam=False)
    b = ProfileEmail(value="invalid2@foo.com", profile=p, bounces=True, is_correct_person=True)
    valid = ProfileEmail(value="valid@foo.com", profile=p)    

    for email in [a, b, valid]:
        email.save()

    dubious = ProfileEmail.to_reach(p.id)

    assert dubious is not None
    assert dubious.value == valid.value

    assert ProfileEmail.to_reach(p.id, strict=True) is None

@pytest.mark.django_db
def test_email_to_reach_with_valid_is_correct_person():
    """Test to make sure ProfileEmail.to_reach returns `is_correct_person = True` first."""
    p = Profile()
    p.save()

    invalid = ProfileEmail(value="invalid@foo.com", profile=p, bounces=True)
    valid = ProfileEmail(value="valid@foo.com", profile=p)
    correct_person = ProfileEmail(value="correct@foo.com", profile=p, is_correct_person=True)

    for email in [invalid, valid, correct_person]:
        email.save()

    test = ProfileEmail.to_reach(p.id)
    assert test.value == correct_person.value

    test_two = ProfileEmail.to_reach(p.id, strict=True)
    assert test_two.value == correct_person.value

# Test the utility functions used by the verifier

@pytest.mark.django_db
def test_add_contact():
    p = Profile()
    p.save()

    # Test input existentiality invariants

    assert add_contact(ProfileEmail, "", p.id) is None
    assert add_contact(ProfileEmail, "", p.id, is_correct_person = True) is None
    assert add_contact(ProfileEmail, "asdf@foo.com", None) is None
    assert add_contact(ProfileEmail, "asdf@foo.com", None, is_correct_person = True) is None

    # Test add_contact() when the email already exists.

    a = ProfileEmail(value="one@foo.com", profile=p)
    b = ProfileEmail(value="two@foo.com", profile=p)

    for email in [a,b]:
        email.save()
    
    ap = add_contact(ProfileEmail, a.value, p.id)
    bp = add_contact(ProfileEmail, b.value, p.id)

    assert ap and ap.id is a.id and ap.value == a.value and ap.is_correct_person == a.is_correct_person
    assert bp and bp.id is b.id and bp.value == b.value and bp.is_correct_person == b.is_correct_person

    # Test add_contact() for a new email.

    c = add_contact(ProfileEmail, "three@foo.com", p.id)
    assert c and c.id and c.value == "three@foo.com" and c.id not in [a.id, b.id]

    # Test add_contact() is_correct_person parameter

    d = ProfileEmail(value="four@foo.com", profile=p)
    e = ProfileEmail(value="five@foo.com", profile=p, is_correct_person = True)
    f = ProfileEmail(value="six@foo.com", profile=p, is_correct_person = True)

    for email in [d,e]:
        email.save()

    dp = add_contact(ProfileEmail, d.value, p.id, is_correct_person = True)
    ep = add_contact(ProfileEmail, e.value, p.id, is_correct_person = False)
    fp = add_contact(ProfileEmail, f.value, p.id, is_correct_person = True)

    assert dp.is_correct_person is not d.is_correct_person
    assert ep.is_correct_person is not e.is_correct_person
    assert fp.is_correct_person is f.is_correct_person

@pytest.mark.django_db
def test_verify_sane():
    p = Profile()
    p.save()

    SANE_EMAIL = "sane@foo.com"
    INSANE_EMAIL = "insane@foo.com"
    UNUSED_EMAIL = "unused@foo.com"

    a = ProfileEmail(value=SANE_EMAIL, profile=p)
    b = ProfileEmail(value=SANE_EMAIL, profile=p, is_correct_person=True)
    c = ProfileEmail(value=INSANE_EMAIL, profile=p, bounces=True)
    d = ProfileEmail(value=INSANE_EMAIL, profile=p, bounces=True, is_correct_person=True)

    for email in [a,b,c,d]:
        email.save()

    assert verify_sane(ProfileEmail, SANE_EMAIL)
    assert not verify_sane(ProfileEmail, INSANE_EMAIL)
    assert verify_sane(ProfileEmail, UNUSED_EMAIL, assume_sane=True)
    assert not verify_sane(ProfileEmail, UNUSED_EMAIL, assume_sane=False)

@pytest.mark.django_db
def test_collect_email_data():
    p = Profile()
    p.save()

    email = "foo@bar.com"
    pe = ProfileEmail(value=email, profile=p)
    pe.save()

    # First, test a bounced email.
    NotificationBouncedEmail(email=email).save()
    collect_email_data(pe)
    assert pe.bounces

    # unbounce it
    NotificationRecipientEvent(email=email, action="delivered").save()
    collect_email_data(pe)
    assert not pe.bounces

    # re-bounce it
    NotificationBouncedEmail(email=email).save()
    collect_email_data(pe)
    assert pe.bounces

    # open it - opening sets opens to True and bounces to False
    NotificationRecipientEvent(email=email, action="open").save()
    collect_email_data(pe)
    assert not pe.bounces and pe.opens

    # open it again. Make sure we're idempotent.
    NotificationRecipientEvent(email=email, action="open").save()
    collect_email_data(pe)
    assert not pe.bounces and pe.opens

    # re-bounce it, but differently
    NotificationRecipientEvent(email=email, action="bounce").save()
    collect_email_data(pe)
    assert pe.bounces

    # test a click.
    NotificationRecipientEvent(email=email, action="click").save()
    collect_email_data(pe)
    assert not pe.bounces and pe.responds

    # try a couple unreleated events, make sure they work
    NotificationRecipientEvent(email=email, action="spamreport").save()
    NotificationRecipientEvent(email=email, action="unsubscribe").save()
    collect_email_data(pe)
    assert pe.reported_spam
    assert pe.unsubscribed

    # resubscribe
    NotificationRecipientEvent(email=email, action="group_resubscribe").save()
    collect_email_data(pe)
    assert not pe.unsubscribed

@pytest.mark.django_db
def test_collect_contact_info_for_profile():
    p = Profile(email="primary@bar.com", phone="phonenumber")
    p.save()

    ProfileExternalData(emails=["foo@bar.com"], phones=["ring"], output={"foo": "foo"}, provider="pipl", profile=p).save()
    ProfileExternalData(emails=["baz@quux.com"], phones=["rang"], output={"foo": "bar"}, provider="whitepages", profile=p).save()

    collect_contact_info_for_profile(p)

    p = Profile.objects.get(id=p.id)

    assert ProfileEmail.objects.filter(value="primary@bar.com", profile=p, is_correct_person=True).first()
    assert ProfilePhoneNumber.objects.filter(value="phonenumber", profile=p, is_correct_person=True).first()
    assert ProfileEmail.objects.filter(value="foo@bar.com", profile=p).first()
    assert ProfileEmail.objects.filter(value="baz@quux.com", profile=p).first()
    assert not p.email
    assert not p.phone

    rlookup_one = ProfileReverseLookup.objects.filter(provider="pipl").first()
    rlookup_two = ProfileReverseLookup.objects.filter(provider="whitepages").first()

    assert rlookup_one and rlookup_one.output["foo"] == "foo"
    assert rlookup_two and rlookup_two.output["foo"] == "bar"

def get_datafile(relative_path):
    with open(os.path.join(str(settings.APPS_DIR), "services/tests/{}".format(relative_path)), 'r') as f:
        return f.read()

# Test the brokers used by the verifying service

@pytest.mark.django_db
def test_generic_lookup_broker():
    # The only part of the generic class that merits testing is the _load_data function.
    p = Profile()
    p.save()

    # Test the case where we don't have a reverse lookup at all
    broker = GenericLookupBroker(profile=p)
    broker.preload()

    assert broker.reverse_lookup is not None
    assert broker._phones == broker.phones == []
    assert broker._emails == broker.emails == []
    assert broker._addresses == broker.addresses == []

    # Test the case where we have a new-ish reverse lookup

    d = ProfileReverseLookup(profile=p, output={}, provider=GenericLookupBroker.provider)
    d.save()

    broker = GenericLookupBroker(profile=p)
    broker.preload()

    assert broker.reverse_lookup.id == d.id

    # Test the case where we have a reverse lookup, but it's too old

    d = ProfileReverseLookup(profile=p, output={}, provider=GenericLookupBroker.provider)
    d.save()
    # Move the created date back a year
    d.date_created = timezone.now() - timedelta(weeks=52)
    d.save()

    print(timezone.now())
    print(d.date_created)

    broker = GenericLookupBroker(profile=p)
    broker.preload()

    assert broker.reverse_lookup.id != d.id
    

@pytest.mark.django_db
def test_pipl_lookup_broker():
    #
    # Single user responses, test parsing
    #
    p = Profile()
    p.save()

    single_1 = ProfileReverseLookup(
        output=json.loads(get_datafile("pipl_output_files/pipl_response_single_1.json")),
        provider='pipl',
        profile=p
    )
    single_1.save()
    broker = PiplLookupBroker(reverse_lookup=single_1)
    assert len(broker.emails) == 0

    single_2 = ProfileReverseLookup(
        output=json.loads(get_datafile("pipl_output_files/pipl_response_single_2.json")),
        provider='pipl',
        profile=p
    )
    single_2.save()
    broker = PiplLookupBroker(reverse_lookup=single_2)
    assert len(broker.emails) == 3
    assert broker.emails[1] == 'wthelusma@hotmail.com'
    assert len(broker.phones) == 3
    assert str(broker.phones[1]) == '9736991858'

    single_3 = ProfileReverseLookup(
        output=json.loads(get_datafile("pipl_output_files/pipl_response_single_3.json")),
        provider='pipl',
        profile=p
    )
    single_3.save()
    broker = PiplLookupBroker(reverse_lookup=single_3)
    assert len(broker.phones) == 1
    assert str(broker.phones[0]) == '2157479158'

    #
    # Multiple user responses, test search pointer generation.
    #

    multiple_response_1 = json.loads(get_datafile("pipl_output_files/pipl_response_multiple_1.json"))
    response = SearchAPIResponse().from_json(json.dumps(multiple_response_1))
    search_pointer = get_valid_search_pointer_from_pipl_response(response, job_family_name='Nursing')
    assert search_pointer == 'eb08348e790c56fead3ce0fec0f9514d032efaf54b7a0489b90cb37e2ed6e2f071104c5d36bb48d6017e10ff9fe158f1c3e06aa2ca44fa1de1f5374b44b07f6118a5289e47565e51b330ebf68604e2e71c3e31f0042a1c41e2f40bf7a71272122b9c1dbb14176b191500b0dba9b06abe4af345da53ef99704702852a96c53bb411f53560805f28a62354020c37237a33c1e07f841f4f1cf04d7fee2d8235b04cd20c32e10e73d092ea4fdfe8b496996e5d699f427140073b4ed359e21b7cafd386af6713d7f9ac119d32e909483e792309de32658d3192afde7b751eafeafe2e6cab9dbaee21be5963e883ea478c574f2123c239b2552458dc6e39d0f07dbfc53eb843ca2586351fd934ed759f2402dd42716b0356f1d0258e16cec57b7392fb84e699f66d1e7cac08f717d6d56a9bc4d99e9b192c0199f01e8fe1ee2349411fb832cc89cfeaf4607f306ddce80a12252f74becbae4289c84a5e47d100a24fe305168b392c1ba1329969a52ef3234f5115a9bdfce6d2b6100fa7137766929ee4b2a5a25a91a0d92e5f1d66e7d54fab4e0d0950896b478d1d0cb82780ce51bbcb9118d30e01f51233437aa4d6382ea8e5b03e469658a3b4224da0387e5a829c5c6c23704948dddc465c25da33fda549195fc5725daed5180cb5e3bbdbdd7e7f306ef7972aa75fa96ed4835c61bd5da598ce3a0cabaae1cee4b7cd7eb596ebadfeb90a57efdee48c105e1137ce7477f59a019e05f06be20a213cd348b1df12124f66a5eadbf7d94af80fc2a11895d11059bac171669a123ad783c592f89025a0cca62dbac06827c0874fa6d56ebc06198820a9f78c5bcb50d537709e895c400463fbdc60c28b0a56c79f5baa9724c93c4037348612355a2116f9c3c2ee82db3cae5ba26dfd25264fd92301d9b29c7e5bb3ad15677a18474ee4018ed5e79cab4230e1c5adf6c42de4026043b0aa20c710a6e31bafb7dd631aa4ddb0c56282ecc24ea12ff1b512b381de953ce7223be28251459d7abe94c582708580b17245cf36d7d443fdcd4805baf491d8a3c26db89e91c4bde53e6d33b28db17c8ce45dbc8917d126823e567d9948cdafe6d0aa2ffaa2fb7418c73de07b96759d953e7680f434548fc601e05f4b9657a7f7bf546c828a89d59073741a66268650a033956c2a7dfb48a19e463ae379bf5ed1fdc7be8a1f467bca74a2f240adf1bcc11b5248e520dd9236d80947dff918274662ccd86179b5b845092bb9b59a85cf1353ed5cae50c8e287fadfc7ad18aefea934a5196d2a743d2cb2efb50532d6da259227427594077e3c998ab475e7d6094b3a63311eb4a4bf559b45abc95f12ac29596f16c7e1b9555628e8f6106121a49ef1c1d02da8'

    multiple_response_2 = json.loads(get_datafile("pipl_output_files/pipl_response_multiple_2.json"))
    response = SearchAPIResponse().from_json(json.dumps(multiple_response_2))
    search_pointer = get_valid_search_pointer_from_pipl_response(response, job_family_name='Nursing')
    assert search_pointer == '45a3b3eeabc6a6f9b61528f5e5c7aa4ccf3543bfaaf11a84ba4b3b13be136545404232aafea40d40a37574f99a32f5c02ea58a3afea5a2e4b89e1d9b8f9e4bfd0181071b045a1b9c92f792e88f0622be40ba407cb5f754f46d9288ae675ef9d5ef28c2200aa0e79212ff42180ff36ea0966bb1c1da481cd4c49a70984aeba5f87c07e2903f9a095bbd732952ec80de6e5383c605d8598725cc7956eb98e361f1c5f4e744ae086a6bc612528086165c136fe7b34d945c0a571d505cdc846b3c63d9ec7756b4b5614d89c7b36abe9a51183e09e4e0c430a4bfba69129bc1c3c777cdd95a5cb1521c203fc1876c061a7ad525879020fdb68a98e0379e9280cbc09b4438470f78f7594d00cd51cdccacd1e9bc82aad8aba32f69d10fb8cd376da56a1f7df17d6b2baec829dfd393a30181da8773a30a36d18e848f29a92ddf09beb5990920d1eda7812b86963e3048bf68d20632d937136c34a45b6f95e219a2699005c8706e5277f6c430fce3a99b8814f6ad90d79c7a375bb483a6ecb595982b94ad34c97e73b81cb5d8e1e66563c0f6281dbad57ddf629dfb7ccf51c9068bfcaa3e4929a924bb19df7c7a24ee7458e44ddf9dd0104d5e721392c85eaa41fa9135c3cb151c809edd4584e2b25c914af6e5b40c3c1670fc5c6dd955ae4a272186e7be060ba7deba4cfe8d12b7fc32cd2c91ab53676755aa39077d1db922133997d1a494387c7fb1b85a0332ba999ff2c4fcebb7a087aca39c669e19807accc03a886f75b863c064294334633990064ab99d66902d35060e54bafd397fe761fc518193d43241db4d9e5955640816cf1c585037be41b8960ea1b4319e4366a9665e07439384975fb9c338936f0721ca07da5d1a0bce409cf49bc23545a771a795ed833b44bf35c2e49bcde0522b4e04461966c89b1002a08e30873ee3160206d2ddf7bfcd5767cb572079e340c2a07a05e47adc24969ef309c8b1e84ca2e0e95848dfcdc79bcfa4bc4e738d9e2ceee0169f57c0452ceda6cd04e24b23ed623c9629b4be727b0bb23286a25fd0ddbe99067e00eee95bc89374a51b071573b9f1c8e1df53f49e09359bd6f1be78627f1a506a6a71459cae3b10a8add31a16f63ef9db68a60ee737df9649d53ac283c5612787ffcd9c7f962af983488687cb9771f05feed612c3103d455e73d85eec872d4cb5fe10fbded1338418e9d33174f3d6e22164bdd614da5016178a9f3f63dcc70997d47b6a891823ddd1aa5458a386581bd87bb27f6f5c0afe5234bbf66bedfb304d484775a61dbb64ae588947243e69a1875ac5d4e227edd0e564912c6f1250a7b82e85f99f5bd74ea2a9ee3cd5d01835db00cc2637986b2838d9c53507ccc7e2ae3aaca0116f1340411f61211f9d9c14c0a7297e5cb346c476b9241dd202c872a687b28b27e6257347b55c229b28fcf6a282984011cb21827f80ae1bbb9d794d96342b9102758e877049e408df6e18a2fc9d7bc79e8fcf7fa9cc8c99f8e55c19a15c6483c66dc57d36402c67ffc8e4d5495811804a2e7a4ddaa5c38538be54ea4b5b'

    multiple_response_3 = json.loads(get_datafile("pipl_output_files/pipl_response_multiple_3.json"))
    response = SearchAPIResponse().from_json(json.dumps(multiple_response_3))
    search_pointer = get_valid_search_pointer_from_pipl_response(response, job_family_name='Nursing')
    assert search_pointer is None

    multiple_response_4 = json.loads(get_datafile("pipl_output_files/pipl_response_multiple_4.json"))
    response = SearchAPIResponse().from_json(json.dumps(multiple_response_4))
    search_pointer = get_valid_search_pointer_from_pipl_response(response, job_family_name='Hospitality')
    assert search_pointer == '83829f0a3de9b785e1e0a6b20219b011accb9b798b1a8af688d6ddfd9e63880e68026fb718da3ecc89bd319856f9cf5b8b4c169ba70dbb10a4e62b6b891b9d317de2f17f4cb702fb1468a0bbb5aeb43d4714b76812dfc64958c6ab0562c5db01524362beadf1571b2dea0f60ff3c23d17caac1510b80854b3ad144b2f4dd5c12ee068db79d53f7b4b4b17f7e3f78c50c16f3b6947f376a1ce24f6b97acfae728d4d0274e21a83e60b0058af6e958482d871cd70a08f58cca6ab99e6b544a4795e4a00f9df9be3e3f6a31be3e6a8b455e7232bd933a86d93983c974f7b7b8f2e7d29f2634a2292ed3e85bcfd495c3dfbc1c9bc29a2188da3c9e3c14b8f914f7997524adb015a2ca80629186ded429c10b84f76aa27069f8d5843773dc57788646021f17e6c7f6e265dcdf233bc4e65da87ddf2f05a7c4faac895e01fdeec057c9e31bcada5f5ec76910813a47954904c5ce8543163a26f1a316529939c6e5ff8b6292da04064acc605e5eac9cf5379695f1645f0b8452d4cfe3f1cc4b962631594b634798207814313195a547c0dfeb86d7ff2e8c01bd73cd520b18da0d097abe4935260f3b6b7878f09836717c53ed3492b97b2484e6edc0aaf91ab34cf1802d68fe09299d7d6017bf90b93636a0744edd04146521b85eb331d5eae7d281d3350c345d96be86af28df3a416a79b2ae47c19dd02e5b9db5e46c2c14af3b810bcbb28dad9f402f3ae667d9fdd605d9091602eef9514424070ebaad7b01a376e49bbc9e3fe873f2f031470290c3b83a4c036a3ba2cb079a37247ae5d6c412143516683481d3ced69bb9da02b225ce5b5b6df47da6f70d29cce5cd715436cad43243f027d37e36f71a7d54e6a51299d2896c4fbc1db89fed853dd76a07f1f21bd739169eb192844f6d5e611eddaebdd3031c86d97a40244b6a18fe55e6d9441cd1b82629a3dae1a175ad3a457d0c6b3cdecad459a2d09fd13b18e1a5b2b0d8c3bbd1dc409d7f931a676af1b4b6bc6d3395ff31e5673fdfd41c97e4da8d88724a28adcc322bffeab25fcf528f6709dfb820ea04e63e12978aff776a68e48d101e758dd9e9b39ecfa2ea24ccab44023e240c9c1042ce3b36869e84e8e4753494c65a35744c2da9172822ebf41d7dc754213540'

