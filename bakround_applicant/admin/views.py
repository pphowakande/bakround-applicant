
from django.core.cache import cache
from django_redis import get_redis_connection

from django.views.generic import View
from django.shortcuts import render, redirect, reverse

import cachalot.api
from django.http import HttpResponse

from bakround_applicant.score.util import get_score_from_score_server
from ..all_models.db import Profile, ProfileJobMapping
from ..scheduler.tasks import set_task_array, create_tasks


class ClearCacheView(View):
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('home')

        redis = get_redis_connection("default")

        context = {}

        context["redis"] = redis
        context["entries_before"] = redis.dbsize()

        cache.clear()
        cachalot.api.invalidate()

        context["entries_after"] = redis.dbsize()

        return render(request, "admin/clear_cache.html", context)


class TestScoringView(View):
    def get(self, request):
        return render(request, "admin/test_scoring.html")

    def post(self, request):
        results = []

        for iteration in range(10):
            mapping = ProfileJobMapping.objects.order_by("?").first()

            try:
                score_json = get_score_from_score_server(profile_id=mapping.profile_id, job_id=mapping.job_id)
            except Exception as e:
                score_json = "EXCEPTION: {}".format(str(e))

            results.append({
                'profile_id': mapping.profile_id,
                'job_id': mapping.job_id,
                'score_json': score_json,
            })

        context = {"results": results}
        return render(request, "admin/test_scoring.html", context)


class SchedulerView(View):
    def get(self, request):
        tasks = []
        set_task_array(tasks)
        create_tasks()
        context = {"tasks": tasks}

        for task in tasks:
            task.class_name = task.__class__.__name__

        return render(request, "admin/scheduler_tool.html", context)

    def post(self, request):
        task_name = request.POST['task_name']

        tasks = []
        set_task_array(tasks)
        create_tasks()

        for task in tasks:
            if task.name == task_name:
                task.run()
                break

        return redirect('staff:scheduler_tool')
