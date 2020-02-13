__author__ = 'ajaynayak'

import json
import logging
import uuid
from datetime import datetime

from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from .forms import SMEForm, RegionForm, make_region_list_for_sme_manager
from bakround_applicant.sme_feedback.models import SME, SMEPayRate, SMEFeedback
from bakround_applicant.all_models.db import LookupRegion, LookupPhysicalLocation

class SMEList(View):
    def get(self, request):
        ordering = ['last_name', 'job__job_name']
        if request.GET.get('ordering') == 'job':
            ordering = ['job__job_name', 'last_name']

        sme_list = (SME.objects
                       .filter(active=True)
                       .order_by(*ordering)
                       .select_related('job', 'region', 'employer_user', 'employer_user__employer', 'employer_user__user'))
        regions = make_region_list_for_sme_manager()

        return render(request, 'admin/sme_manager/index.html',
                        {'sme_list': sme_list.iterator(), 'regions': regions})


class SMEEdit(View):
    def get(self, request, sme_id):
        sme = SME.objects.get(pk=sme_id)
        pay_rate = None
        sme_pay_rate = SMEPayRate.objects.filter(sme_id=sme_id, effective_date__lte=timezone.now()).order_by('-effective_date')
        if sme_pay_rate and sme_pay_rate[0] is not None:
            pay_rate = sme_pay_rate[0].pay_rate

        data = {'first_name': sme.first_name,
                'last_name': sme.last_name,
                'email': sme.email,
                'review_limit': sme.review_limit,
                'pay_rate': pay_rate,
                'job': sme.job_id,
                'region': sme.region,
                'employer_user': sme.employer_user}

        form = SMEForm(initial=data)

        return render(request, 'admin/sme_manager/create_edit.html', {'mode': 'edit', 'form': form, 'sme_id': sme.id, 'sme': sme})

    def post(self, request, sme_id):
        form = SMEForm(request.POST)
        if form.is_valid():
            logging.info(form)

            sme = SME.objects.get(pk=sme_id)

            sme.first_name = form.cleaned_data['first_name']
            sme.last_name = form.cleaned_data['last_name']
            sme.email = form.cleaned_data['email']
            sme.review_limit = form.cleaned_data['review_limit']
            sme.job_id = form.cleaned_data['job']
            sme.region = form.cleaned_data['region']
            sme.employer_user = form.cleaned_data['employer_user']

            sme.save()

            if 'pay_rate' in form.cleaned_data and form.cleaned_data['pay_rate'] is not None:
                SMEPayRate(sme=sme,
                           pay_rate=form.cleaned_data['pay_rate']).save()

        return redirect("sme_manager:index")


class SMECreate(View):
    def get(self, request):
        form = SMEForm()

        return render(request, 'admin/sme_manager/create_edit.html', {'mode': 'create', 'form': form})

    def post(self, request):
        form = SMEForm(request.POST)

        if form.is_valid():
            sme = SME(first_name=form.cleaned_data['first_name'],
                      last_name=form.cleaned_data['last_name'],
                      email=form.cleaned_data['email'],
                      guid=str(uuid.uuid4()),
                      review_limit=form.cleaned_data['review_limit'],
                      job_id=form.cleaned_data['job'],
                      region=form.cleaned_data['region'],
                      employer_user=form.cleaned_data['employer_user'])
            sme.save()

            if 'pay_rate' in form.cleaned_data and form.cleaned_data['pay_rate'] is not None:
                SMEPayRate(sme=sme,
                           pay_rate=form.cleaned_data['pay_rate']).save()

        return redirect("sme_manager:index")


class SMEDelete(View):
    def post(self, request, sme_id):
        sme = SME.objects.get(pk=sme_id)

        sme.active = False

        sme.save()

        return redirect("sme_manager:index")


class RegionEdit(View):
    def get(self, request, region_id):
        region = LookupRegion.objects.get(id=region_id)

        data = {'name': region.name,
                'city': region.city,
                'state': region.state_id,
                'radius': region.radius or 50}

        form = RegionForm(initial=data)

        return render(request, 'admin/sme_manager/region_create_edit.html',
                        {'mode': 'edit', 'form': form, 'region_id': region.id})

    def post(self, request, region_id):
        form = RegionForm(request.POST)

        if form.is_valid():
            region = LookupRegion.objects.get(id=region_id)
            region.name = form.cleaned_data['name']
            region.city = form.cleaned_data['city']
            region.state_id = form.cleaned_data['state']
            region.radius = form.cleaned_data['radius']
            region.save()

        return redirect("sme_manager:index")


class RegionCreate(View):
    def get(self, request):
        form = RegionForm()

        return render(request, 'admin/sme_manager/region_create_edit.html',
                        {'mode': 'create', 'form': form})

    def post(self, request):
        form = RegionForm(request.POST)

        if form.is_valid():
            region = LookupRegion(name=form.cleaned_data['name'],
                                  city=form.cleaned_data['city'],
                                  state_id=form.cleaned_data['state'],
                                  radius=form.cleaned_data['radius'])
            region.save()

        return redirect("sme_manager:index")


class DoesCityExistView(View):
    def post(self, request):
        city = request.POST['city']
        state_id = request.POST['state_id']

        answer = {"does_city_exist":
                      LookupPhysicalLocation.objects.filter(city=city, state_id=state_id).exists()}

        return HttpResponse(json.dumps(answer),
                            content_type="application/json")
