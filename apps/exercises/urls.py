from django.urls import path

from . import views

app_name = "exercises"

urlpatterns = [
    path("", views.index, name="index"),
    path("relief/", views.relief, name="relief"),
    path("grounding/", views.grounding_list, name="grounding_list"),
    path("grounding/<slug:slug>/", views.grounding_detail, name="grounding_detail"),
    path("breathing/", views.breathing, name="breathing"),
    path("cbt/", views.cbt_list, name="cbt_list"),
    path("cbt/new/", views.cbt_new, name="cbt_new"),
    path("cbt/<int:pk>/", views.cbt_detail, name="cbt_detail"),
    path("cbt/<int:pk>/delete/", views.cbt_delete, name="cbt_delete"),
]
