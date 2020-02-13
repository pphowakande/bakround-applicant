
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=staff_member_required(views.SkillIndexView.as_view()),
        name='index'
    ),

    url(
        regex=r'^add_object/$',
        view=staff_member_required(views.AddObjectView.as_view()),
        name='add_object'
    ),
]
