
__author__ = "tplick"

from django.conf.urls import url
from django.views.generic import TemplateView

from django.contrib.admin.views.decorators import staff_member_required

from . import views

urlpatterns = [
    url(
        regex=r'^profiles/?$',
        view=staff_member_required(views.ProfileStatsGetView.as_view()),
        name='profiles'
    ),

    # url(
    #     regex=r'^profiles_post/?$',
    #     view=views.ProfileStatsPostView.as_view(),
    #     name='profiles_post'
    # ),

    url(
        regex=r'^new_users/?$',
        view=staff_member_required(views.NewUsersStatsGetView.as_view()),
        name='new_users'
    ),

    # url(
    #     regex=r'^new_users_post/?$',
    #     view=views.NewUsersStatsPostView.as_view(),
    #     name='new_users_post'
    # ),
]
