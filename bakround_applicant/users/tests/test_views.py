
from django.test import RequestFactory
from test_plus.test import TestCase
from django.test import Client

import pytest
import random
import string

from bakround_applicant.all_models.db import User


from ..views import (
    UserRedirectView,
    UserUpdateView
)


class BaseUserTestCase(TestCase):

    def setUp(self):
        self.user = self.make_user()
        self.factory = RequestFactory()


class TestUserUpdateView(BaseUserTestCase):

    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestUserUpdateView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = UserUpdateView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        self.view.request = request

    def test_get_success_url(self):
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            self.view.get_success_url(),
            '/users/testuser/'
        )

    def test_get_object(self):
        # Expect: self.user, as that is the request's user object
        self.assertEqual(
            self.view.get_object(),
            self.user
        )


@pytest.mark.django_db
def test_redirect_for_user():
    new_username = ''.join(random.choice(string.ascii_letters) for i in range(30))
    user = User.objects.create_user(username=new_username, email=new_username)
    client = Client()

    page = client.get("/")
    assert page.status_code == 302 and page.url == '/accounts/signup/employer'

    client.force_login(user)

    page = client.get("/")
    assert page.status_code == 302 and page.url == '/profile/'

    user.is_employer = True
    user.save()

    page = client.get("/")
    assert page.status_code == 302 and page.url == '/employer/'

    client.post("/accounts/logout/")
    page = client.get("/")
    assert page.status_code == 302 and page.url == '/accounts/login/'
