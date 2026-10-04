from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),
    path("history/", views.history, name="history"),
    path("new/", views.new_conversation, name="new"),
    path("<int:pk>/", views.conversation_detail, name="detail"),
    path("<int:pk>/delete/", views.delete_conversation, name="delete"),
    path("<int:pk>/send/", views.SendMessageView.as_view(), name="send"),
]
