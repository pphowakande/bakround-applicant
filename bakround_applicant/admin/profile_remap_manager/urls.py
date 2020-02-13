__author__ = "tplick"

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views


urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.IndexView.as_view()),
        name='index'
    ),
    url(
        regex=r'^add_job$',
        view=staff_member_required(views.AddJobView.as_view()),
        name='add_job'
    ),
    url(
        regex=r'^remove_job/(?P<job_id>\d+)$',
        view=staff_member_required(views.RemoveJobView.as_view()),
        name='remove_job'
    ),
    url(
        regex=r'^edit_job/(?P<job_id>\d+)$',
        view=staff_member_required(views.EditJobView.as_view()),
        name='edit_job'
    ),
    url(
        regex=r'^clean_up_order$',
        view=staff_member_required(views.CleanUpOrderView.as_view()),
        name='clean_up_order'
    ),
    url(
        regex=r'^change_order/(?P<job_id>\d+)$',
        view=staff_member_required(views.ChangeOrderView.as_view()),
        name='change_order'
    ),

    url(
        regex=r'^remap_job_now/(?P<job_id>\d+)$',
        view=staff_member_required(views.RemapJobNowView.as_view()),
        name='remap_job_now',
    ),
]
