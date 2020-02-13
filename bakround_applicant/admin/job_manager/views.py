__author__ = 'ajaynayak'

import django
from django.views import View
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from django.db.models import Count, F
from bakround_applicant.all_models.db import Job, Skill, JobSkill, \
                                             Profile, Certification, \
                                             JobCertification, JobFamily, SMEFeedback, \
                                             BgPositionMaster, IndustryJobFamily
from ...services.queue import QueueNames, QueueConnection
import json

import random
import string

from django.urls import reverse
from django.http import HttpResponse

from collections import defaultdict

import jinja2
jinja2_env = jinja2.Environment(
    loader=jinja2.PackageLoader('bakround_applicant', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml']),
)
# https://stackoverflow.com/questions/44271949/using-jinja2-with-django-load-tag-does-not-work
jinja2_env.globals.update({
    'url': reverse,
    # 'csrf_token': django.template.defaulttags.csrf_token,
})
jinja2_env.filters.update({
    'escapejs': django.utils.html.escapejs,
})

class Index(View):
    def general_dispatch(self, request, job, params, after_change=False, after_no_change=False):
        context = {}
        context['jobs'] = Job.objects.all().select_related('job_family').order_by('job_name')

        # TODO: fix this for the smes
        reviewed_jobs = []#SMEFeedback.objects.values(job_id=F('profile_resume__profile__job_id')).annotate(count=Count('job_id'))
        uniquely_reviewed_jobs = []#SMEFeedback.objects.values('sme_id', profile_id=F('profile_resume__profile_id'), job_id=F('profile_resume__profile__job_id')).distinct().annotate(count=Count('job_id'))
        job_review_count = {}
        for reviewed_job in reviewed_jobs:
            job_review_count[reviewed_job['job_id']] = reviewed_job['count']

        unique_review_count = {}
        for reviewed_job in uniquely_reviewed_jobs:
            unique_review_count[reviewed_job['job_id']] = reviewed_job['count']

        context['job_review_count'] = job_review_count

        context['unique_job_review_count'] = unique_review_count

        context['job_families'] = job_families = list(JobFamily.objects.all().order_by('family_name'))

        industry_names_for_job_family = get_industry_names_for_job_families()
        for job_family in job_families:
            job_family.industries = ", ".join(industry_names_for_job_family[job_family.id])

        context['job'] = job
        job_id = job.id if job else 0

        if job_id:
            context['skills'] = Skill.objects.all().only(
                                                'id', 'skill_name').order_by('skill_name')
            context['certifications'] = Certification.objects.all().only(
                                                'id', 'certification_name').order_by('certification_name')

            context['job_skills'] = {job_skill.skill_id: job_skill
                                     for job_skill in JobSkill.objects.filter(job_id=job_id)}
            context['job_certs'] = {job_cert.certification_id: job_cert
                                     for job_cert in JobCertification.objects.filter(job_id=job_id)}

            # get all skills info for the job
            skills_data = {}
            for job_skill in JobSkill.objects.filter(job_id=job_id):
                skills_data[job_skill.skill_id] = {"weight": job_skill.default_weightage,
                                                   "experience_months": job_skill.experience_months}
            context['skills_data_old'] = json.dumps(skills_data)

            # get all certs info for the job
            certs_data = {}
            for job_cert in JobCertification.objects.filter(job_id=job_id):
                certs_data[job_cert.certification_id] = {"weight": job_cert.default_weightage}
            context['certs_data_old'] = json.dumps(certs_data)

            if after_change:
                context['after_change'] = True
            if after_no_change:
                context['after_no_change'] = True

        context['onet_positions'] = get_onet_positions()

        context['csrf_token'] = django.middleware.csrf.get_token(request)

        context['accuracy_values'] = range(4)

        random_string = context['random_string'] = "".join(random.choice(string.ascii_letters) for _ in range(50))

        try:
            contents = jinja2_env.get_template('admin/job_manager/index.html').render(context)
        except jinja2.TemplateSyntaxError as e:
            raise e
            # raise Exception("Jinja exception in line {}".format(e.lineno)) from e

        string_output = render_to_string('admin/job_manager/index_wrapper.html',
                                         context={"random_string": random_string},
                                         request=request)

        return HttpResponse(string_output.replace(random_string, contents))

    def get(self, request):
        try:
            job_id = int(request.GET.get('job_id'))
            job = Job.objects.get(id=job_id)
        except Exception:
            job = job_id = None

        return self.general_dispatch(request, job, request.GET)

    def post(self, request):
        job_id = int(request.POST['job_id'])
        skills_data_old = json.loads(request.POST['skills_data_old'])
        skills_data_new = json.loads(request.POST['skills_data_new'])
        certs_data_old = json.loads(request.POST['certs_data_old'])
        certs_data_new = json.loads(request.POST['certs_data_new'])

        job_skills = JobSkill.objects.filter(job_id=job_id)
        job_certs = JobCertification.objects.filter(job_id=job_id)
        was_anything_changed = False

        for skill_id in skills_data_old:
            if skill_id not in skills_data_new:
                # remove skill from job
                job_skills.filter(skill_id=skill_id).delete()
                was_anything_changed = True

        for skill_id in skills_data_new:
            if skill_id not in skills_data_old:
                # add skill to job
                weight = int(skills_data_new[skill_id]["weight"])
                experience_months = int(skills_data_new[skill_id]["experience_months"])
                JobSkill(job_id=job_id,
                         skill_id=skill_id,
                         default_weightage=weight,
                         experience_months=experience_months).save()
                was_anything_changed = True

        preserved_skills = set(skills_data_old.keys()) & set(skills_data_new.keys())
        for skill_id in preserved_skills:
            old_params = skills_data_old[skill_id]
            new_params = skills_data_new[skill_id]
            changes = {}

            # check for changes to this job_skill
            if str(old_params["weight"]) != str(new_params["weight"]):
                changes = {"default_weightage": int(new_params["weight"])}
            if str(old_params["experience_months"]) != str(new_params["experience_months"]):
                changes = {"experience_months": int(new_params["experience_months"])}

            # make the changes, if there are any
            if changes:
                job_skills.filter(skill_id=skill_id).update(**changes)
                was_anything_changed = True

        for cert_id in certs_data_old:
            if cert_id not in certs_data_new:
                # remove cert from job
                job_certs.filter(certification_id=cert_id).delete()
                was_anything_changed = True

        for cert_id in certs_data_new:
            if cert_id not in certs_data_old:
                # add cert to job
                JobCertification(job_id=job_id,
                                 certification_id=cert_id,
                                 default_weightage=certs_data_new[cert_id]["weight"]).save()
                was_anything_changed = True

        # added by tplick on 16 Feb 2018: handle certification weights
        # ------------------
        preserved_certs = set(certs_data_old.keys()) & set(certs_data_new.keys())
        for cert_id in preserved_certs:
            old_params = certs_data_old[cert_id]
            new_params = certs_data_new[cert_id]
            changes = {}

            # check for changes to this job_cert
            if str(old_params["weight"]) != str(new_params["weight"]):
                changes = {"default_weightage": int(new_params["weight"]) if new_params["weight"] else None}

            # make the changes, if there are any
            if changes:
                job_certs.filter(certification_id=cert_id).update(**changes)
                was_anything_changed = True
        # ------------------

        job = Job.objects.get(id=job_id)
        new_job_attributes = json.loads(request.POST['job_attributes'])
        has_changes = False

        if job.job_name != new_job_attributes['job_name']:
            job.job_name = new_job_attributes['job_name']
            has_changes = True

        if (job.job_description is None and new_job_attributes['job_description']) \
            or job.job_description is not None and job.job_description != new_job_attributes['job_description']:
            job.job_description = new_job_attributes['job_description']
            has_changes = True

        if 'job_visible' in new_job_attributes and job.visible != bool(new_job_attributes['job_visible']):
            job.visible = bool(new_job_attributes['job_visible'])
            has_changes = True

        new_onet_position_id = int(request.POST['onet_position']) or None
        if new_onet_position_id != job.onet_position_id:
            job.onet_position_id = new_onet_position_id
            has_changes = True

        new_job_family_id = int(request.POST['job_family'])
        if new_job_family_id != job.job_family_id:
            job.job_family_id = new_job_family_id
            has_changes = True

        new_accuracy_str = request.POST['accuracy']
        new_accuracy = int(new_accuracy_str) if new_accuracy_str else None
        if new_accuracy != job.accuracy:
            job.accuracy = new_accuracy
            has_changes = True

        if has_changes:
            job.save()

        was_anything_changed = was_anything_changed or has_changes

        return self.general_dispatch(request, job, request.POST,
                                     after_change=was_anything_changed,
                                     after_no_change=not was_anything_changed)


def get_onet_positions():
    return BgPositionMaster.objects.order_by('title')


class EditJob(View):
    def get(self, request, job_id):
        context = {}

        context['job'] = Job.objects.get(pk=job_id)
        context['skills'] = Skill.objects.all()

        context['skills_by_job'] = JobSkill.objects.filter(job_id=job_id)

        return render(request, 'admin/job_manager/edit_job.html', context)


class AddJobView(View):
    def post(self, request):
        if 'name_for_new_job' in request.POST and 'description_for_new_job' in request.POST:
            add_new_job(job_name=request.POST['name_for_new_job'].strip(),
                        job_description=request.POST['description_for_new_job'].strip(),
                        job_family_id=int(request.POST['job_family']),
                        onet_position_id=int(request.POST['onet_position']) or None,
                        visible=bool(request.POST['visibility_for_new_job']
                                     if 'visibility_for_new_job' in request.POST
                                     else False),
                        accuracy=request.POST['accuracy'] or None)
            return redirect("job_manager:index")


class DeleteJobView(View):
    def post(self, request):
        if 'job_id' in request.POST:
            job_id = int(request.POST['job_id'])
            job_skills = JobSkill.objects.filter(job_id=job_id).exists()
            profiles_with_job = ProfileJobMapping.objects.filter(job_id=job_id).exists()
            if not job_skills and not profiles_with_job:
                Job.objects.get(pk=job_id).delete()
        return redirect("job_manager:index")


class RescoreProfilesView(View):
    def post(self, request):
        show_delay_message = False
        if 'job_id' in request.POST:
            job_id = int(request.POST['job_id'])

            QueueConnection.quick_publish(queue_name=QueueNames.scoring_service,
                                          body=json.dumps({"mode": "system",
                                                           "job_id": job_id}))

        return redirect("/job_manager")


class RescoreJobFamilyView(View):
    def post(self, request):
        show_delay_message = False
        if 'job_family_id' in request.POST:
            job_family_id = int(request.POST['job_family_id'])

            # send a message to the queue to handle the score requests immediately
            QueueConnection.quick_publish(queue_name=QueueNames.scoring_service,
                                              body=json.dumps({"mode": "job_family",
                                                               "job_family_id": job_family_id}))

        return redirect("/job_manager")


def add_new_job(job_name, job_description, visible=True, job_family_id=None, onet_position_id=None,
                accuracy=None):
    Job(job_name=job_name,
        job_description=job_description,
        visible=visible,
        onet_position_id=onet_position_id,
        job_family_id=job_family_id,
        accuracy=accuracy).save()


def get_industry_names_for_job_families():
    Dict = defaultdict(list)

    for ijf in (IndustryJobFamily.objects
                                 .select_related('industry')
                                 .order_by('industry__industry_name')):
        Dict[ijf.job_family_id].append(ijf.industry.industry_name)

    return Dict
