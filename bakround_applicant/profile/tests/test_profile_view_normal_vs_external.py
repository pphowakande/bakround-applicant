
__author__ = "tplick"

# Make sure that the normal profile view and the external profile view
# have the elements that they are supposed to have.

from bakround_applicant.all_models.db import Job, Profile, User, \
        ProfileEducation, ProfileExperience, \
        LookupDegreeMajor, LookupDegreeName, LookupDegreeType, \
        ProfileViewer
import pytest
from django.test import Client


@pytest.mark.django_db
def test_profile_view_normal_vs_external():
    set_up_users_and_profile()

    # normal view
    client = make_client_for_user_id(1)
    page_contents = contents_of_page(client, "/profile/").lower()
    assert "profilecompletioninfo" in page_contents
    assert "where you stack up" in page_contents
    assert "collegiate university" in page_contents
    assert "bachelor's" in page_contents
    assert "accounting" in page_contents

    # external view
    client = make_client_for_user_id(2)
    ProfileViewer(profile_id=1,
                  token="1234",
                  active=True).save()
    page_contents = contents_of_page(client, "/profile/external_view?token=1234").lower()
    assert "profilecompletioninfo" not in page_contents
    assert "where you stack up" not in page_contents
    assert "collegiate university" in page_contents
    assert "bachelor's" in page_contents
    assert "accounting" in page_contents


def set_up_users_and_profile():
    User(id=1, username='first').save()
    User(id=2, username='second', is_staff=True).save()
    Job(id=1, job_name="skateboarder").save()

    Profile(id=1,
            job_id=1,
            user_id=1,
            first_name="Bob",
            last_name="Loblaw").save()

    ProfileExperience(profile_id=1,
                      company_name="Excellence Incorporated").save()

    # I am adding a test for education because we had the problem where
    #   the degree major/name/type fields were not being passed to the external view.
    LookupDegreeMajor(id=1, degree_major_name="Accounting").save()
    LookupDegreeType(id=1, degree_type_name="Bachelor's", degree_type_sovren="bachelors").save()
    LookupDegreeName(id=1, degree_type_id=1, degree_name="Bachelor's in Accounting").save()

    ProfileEducation(profile_id=1,
                     school_name="Collegiate University",
                     degree_major_id=1,
                     degree_name_id=1,
                     degree_type_id=1).save()


def make_client_for_user_id(user_id):
    user_obj = User.objects.get(id=user_id)
    client = Client()
    client.force_login(user_obj)
    return client


def contents_of_page(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return response.content.decode('utf8')


@pytest.mark.django_db
def test_pdf_profile_view():
    set_up_users_and_profile()
    client = Client()

    # test as not logged in

    response = client.get('/profile/pdf/1?bkgen=1')
    assert response.status_code == 302

    response = client.get('/profile/pdf/100?bkgen=1')
    assert response.status_code == 302

    # test as user 1 (not staff)

    user_obj = User.objects.get(id=1)
    client.force_login(user_obj)

    response = client.get('/profile/pdf/1?bkgen=1')
    assert response.status_code == 200

    response = client.get('/profile/pdf/100?bkgen=1')
    assert response.status_code == 302

    # test as user 2 (staff)

    user_obj = User.objects.get(id=2)
    client.force_login(user_obj)

    response = client.get('/profile/pdf/1?bkgen=1')
    assert response.status_code == 200

    with pytest.raises(Profile.DoesNotExist):
        client.get('/profile/pdf/100?bkgen=1')
