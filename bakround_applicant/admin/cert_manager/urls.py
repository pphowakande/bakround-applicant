
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from ..skill_manager import views

urlpatterns = (
    url(
        regex=r'^$',
        view=staff_member_required(views.CertIndexView.as_view()),
        name='index'
    ),
)
