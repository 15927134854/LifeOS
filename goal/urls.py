from django.urls import path

from goal.views import Simulate

app_name = 'goal'

urlpatterns = [
    path('simulate/', Simulate.as_view()),
]
