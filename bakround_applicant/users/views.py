# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import re
import json

from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

import allauth.account.views
from allauth.account.views import RedirectAuthenticatedUserMixin

from .models import User
from bakround_applicant.all_models.db import Profile, Job, EmployerCandidate, \
                                             EmployerCandidateResponse, EmployerUser, \
                                             LookupDeclineReason, ProfileEmail, ProfilePhoneNumber, \
                                             EmployerCandidateWebsiteVisited, ProfileExperience

from bakround_applicant.forms import IndeedTestForm
from bakround_applicant.event import record_event, EventActions
from bakround_applicant.notifications import emails
from bakround_applicant.employer.utils import handle_candidate_accept, handle_candidate_decline
from bakround_applicant.services.queue import QueueConnection, QueueNames
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact
from bakround_applicant.utilities.functions import get_job_families_for_industry, redirect_for_login, \
                                                   is_request_marked_as_having_ever_logged_in 

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'

    # TP 28 Dec 2016
    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)


class UserRedirectView(LoginRequiredMixin, View):
    permanent = False

    def get(self, request):
        return redirect_for_user(request)


def redirect_for_user(request):
    user = request.user

    if not user.is_authenticated:
        if is_request_marked_as_having_ever_logged_in(request):
            return redirect('account_login')
        else:
            return redirect('employer_signup')
    elif user.is_employer:
        return redirect_for_login('employer:index')
    else:
        return redirect_for_login('profile:index')


class UserUpdateView(LoginRequiredMixin, UpdateView):

    fields = ['name', ]

    # we already imported User in the view code above, remember?
    model = User

    # send the user back to their own page after a successful update
    def get_success_url(self):
        return reverse('users:detail',
                       kwargs={'username': self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)


# tplick: December 22, 2016
class HomePageView(View):
    redirect_field_name = "next"

    def get(self, request):
        referral_code = request.GET.get('ref', None)

        request.session.update({
            "appl_email": None,
            "appl_profile_exists": None,
            "appl_wants_to_claim": None,
            "appl_login_email": None,
            "appl_referral_code": referral_code,
            "email_already_registered": None
        })

        email = request.GET.get('email', None)

        if email is not None:
            return self.post(request, email=email)

        return redirect_for_user(request)

    def post(self, request, email=None):

        if email is None:
            email = request.POST['email']

        if not is_email_address_valid(email):
            return render(request, "pages/home.html", {"is_email_invalid": True})

        if User.objects.filter(email=email).exists():
            request.session['appl_login_email'] = email
            return redirect('account_login')

        request.session['appl_email'] = email
        request.session['appl_profile_exists'] = False
        return HttpResponseRedirect("/accounts/signup")

def is_email_address_valid(email):
    return email and '@' in email

class AccountSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        context = {}

        try:
            customer = Customer.objects.get(subscriber_id=request.user.id)
            context["customer"] = customer
        except Exception:
            pass

        try:
            context["subscription"] = CurrentSubscription.objects.get(customer=customer)
        except Exception:
            pass

        context["PLAN_LIST"] = []
        context["plans"] = []

        try:
            context['profile'] = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            pass

        context['space_separated_email'] = request.user.email.replace("@", "@\u200B")

        context['api_key'] = request.user.api_key

        context['referral_link'] = "{}?ref={}".format(settings.WEBSITE_ROOT_URL, request.user.referral_code)

        context['is_employer_owner'] = EmployerUser.objects.filter(user=request.user,
                                                                   is_owner=True).exists()

        return render(request, "pages/account_settings.html", context)

class TokenLoginView(View):
    def get(self, request, token):
        user = User.objects.filter(initial_login_token=token).first()
        if user is None:
            return render(request, "pages/initial_token_login.html", {"success": False})

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return render(request, "pages/initial_token_login.html", {"success": True})


class SetPasswordAfterTokenLoginView(View):
    def post(self, request):
        user = request.user
        password = request.POST['password']

        user.initial_login_token = None
        user.set_password(password)
        user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect_for_login('home')

# tplick, 1 February 2017
class SignInView(allauth.account.views.LoginView):
    def get(self, request, *args, **kwargs):
        request.appl_login_email = request.session.get('appl_login_email', None)
        request.session['appl_login_email'] = None
        return super().get(self, request, *args, **kwargs)


# tplick, 10 February 2017
class UpdateJobForProfileView(LoginRequiredMixin, View):
    def get(self, request):
        context = {}
        try:
            context['profile'] = profile = Profile.objects.get(user=request.user)
            context['jobs'] = (Job.objects
                              .filter(visible=True,
                                      employer_id__isnull = True,
                                      job_family = profile.job.job_family)
                              .order_by('job_name'))
        except:
            context['profile'] = profile = None
            context['jobs'] = Job.objects.order_by('job_name')
        
        return render(request, "users/change_job.html", context)

    def post(self, request):
        new_job_id = int(request.POST['new_job_id'])
        Profile.objects.filter(user=request.user).update(job_id=new_job_id)
        return redirect('account_settings')


##### These are candidates endpoints

# tplick, 3 April 2017
class CandidateAcceptView(View):
    def get(self, request, employer_candidate_guid):
        template_name = "notifications/page_after_candidate_accepts.html"

        try:
            candidate = EmployerCandidate.objects.get(guid=employer_candidate_guid)
        except EmployerCandidate.DoesNotExist:
            return render(request, template_name, {"success": False, "no_such_guid": True})

        collect_contact_info_for_profile(candidate.profile)
        candidate_email = ProfileEmail.to_reach(candidate.profile.id)
        if candidate_email: candidate_email = candidate_email.value
        candidate_phone = ProfilePhoneNumber.to_reach(candidate.profile.id)
        if candidate_phone: candidate_phone = candidate_phone.value

        suggest_claim = (candidate_email is not None and
                         candidate.profile.user_id is None and
                         (request.user is None or not request.user.is_authenticated))
        if suggest_claim:
            request.session['appl_accepted_email'] = candidate_email

        handle_candidate_accept(candidate)

        return render(request, template_name, {"success": True,
                                               "employer_candidate_guid": employer_candidate_guid,
                                               "candidate_email": candidate_email,
                                               "candidate_phone": candidate_phone,
                                               "suggest_claim": suggest_claim})

# tplick, 10 April 2017
class CandidateSendMessageView(View):
    def post(self, request):
        template_name = "notifications/page_after_candidate_accepts.html"
        employer_candidate_guid = request.POST['employer_candidate_guid']
        message = request.POST['message']

        candidate = EmployerCandidate.objects.get(guid=employer_candidate_guid)

        new_response = EmployerCandidateResponse(response=message)
        new_response.save()

        # TODO: delete the old response.

        candidate.response = new_response
        candidate.save(update_fields=['response'])

        new_email = request.POST.get('email')
        new_phone = request.POST.get('phone')

        collect_contact_info_for_profile(candidate.profile)

        if new_email:
            add_contact(ProfileEmail, new_email, candidate.profile.id, True)

        if new_phone:
            add_contact(ProfilePhoneNumber, new_phone, candidate.profile.id, True)

        # Send a notification to the employer if they asked this candidate to update their info
        if candidate.contact_info_requested:
            emails.CandidateUpdatedInfo().send(employer_candidate=candidate)
            message = "Thanks for updating your info! The recruiter will contact you shortly."
        else:
            emails.CandidateAccepted().send(employer_candidate=candidate)
            message = "Your message has been sent!"

        messages.success(request, message)
        return redirect('/candidate/accept/{}'.format(candidate.guid))

# tplick, 20 June 2017
class CandidateDeclineView(View):
    def get(self, request, employer_candidate_guid):
        if not employer_candidate_guid:
            raise Http404

        candidate = EmployerCandidate.objects.filter(guid=employer_candidate_guid).first()

        if not candidate:
            raise Http404

        handle_candidate_decline(candidate)

        return render(request, "notifications/page_after_candidate_declines.html", {
            "decline_reasons": LookupDeclineReason.objects.order_by('order'),
            "employer_candidate": candidate,
        })


class CandidateDeclineReasonView(View):
    def post(self, request, employer_candidate_guid):
        candidate = EmployerCandidate.objects.get(guid=employer_candidate_guid)

        if request.POST.get('decline_reason'):
            candidate.decline_reason_id = request.POST['decline_reason']
        candidate.decline_reason_comments = request.POST['decline_reason_comments']
        candidate.save()

        return render(request, "pages/generic_message.html", {
            "message": "Thank you for giving us your reason.",
        })

class UnsubscribeView(View):
    def get(self, request, employer_candidate_guid):
        if not employer_candidate_guid:
            raise Http404

        employer_candidate = EmployerCandidate.objects.filter(guid=employer_candidate_guid).first()
        if not employer_candidate:
            raise Http404

        handle_candidate_unsubscribe(employer_candidate)

        return render(request, "notifications/unsubscribe.html")

class CandidateRecordClickView(View):
    def get(self, request, employer_candidate_guid):
        employer_candidate = EmployerCandidate.objects.get(guid=employer_candidate_guid)
        EmployerCandidateWebsiteVisited(employer_candidate=employer_candidate).save()
        return HttpResponseRedirect(employer_candidate.employer_job.employer.website_url)

