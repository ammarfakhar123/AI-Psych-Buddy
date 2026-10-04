from django.urls import path

from . import views

app_name = "mood"

urlpatterns = [
    path("", views.tracker, name="tracker"),
    path("chart-data/", views.chart_json, name="chart_data"),
    path("<int:pk>/delete/", views.delete_entry, name="delete"),
]
