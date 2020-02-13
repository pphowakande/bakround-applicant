
__author__ = "tplick"

import time
import html
from django.views import View
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .logic import get_stats
from .new_users import get_new_user_stats
#
#
class ProfileStatsGetView(View):
    def get(self, request):
        return HttpResponse(get_stats(), content_type="text/plain")


# @method_decorator(csrf_exempt, name='dispatch')
# class ProfileStatsPostView(View):
#     def post(self, request):
#         if request.POST.get('token') == '456c3e87-c443-4559-869e-fd3f1415ed8e':
#             stats_text = get_stats()
#             stats_html = "<pre>" + html.escape(stats_text) + "</pre>"
#             todays_date = time.strftime("%B %d, %Y")
#
#             send_mail(subject="Profile stats as of {}".format(todays_date),
#                       message=stats_text,
#                       html_message=stats_html,
#                       from_email="noreply@bakround.com",
#                       recipient_list=["stats@bakround.com"])
#             return HttpResponse("true")
#         else:
#             return HttpResponse("false")
#
#
class NewUsersStatsGetView(View):
    def get(self, request):
        return HttpResponse(get_new_user_stats(), content_type="text/plain")


# @method_decorator(csrf_exempt, name='dispatch')
# class NewUsersStatsPostView(View):
#     def post(self, request):
#         if request.POST.get('token') == '456c3e87-c443-4559-869e-fd3f1415ed8e':
#             stats_text = get_new_user_stats()
#             stats_html = "<pre>" + html.escape(stats_text) + "</pre>"
#             todays_date = time.strftime("%B %d, %Y")
#
#             send_mail(subject="New user stats for {}".format(todays_date),
#                       message=stats_text,
#                       html_message=stats_html,
#                       from_email="noreply@bakround.com",
#                       recipient_list=["stats@bakround.com"])
#             return HttpResponse("true")
#         else:
#             return HttpResponse("false")
