from django.urls import path

from . import views

app_name = 'compliance'

urlpatterns = [
    path('organizations/<int:org_id>/evidence-pack/',
         views.evidence_pack, name='evidence_pack'),
]
