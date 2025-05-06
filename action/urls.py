from django.urls import path

from action.views import Vialization


app_name = 'action'

urlpatterns = [
    path('vialization/', Vialization.as_view()),
]
