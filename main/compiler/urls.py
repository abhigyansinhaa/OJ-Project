from django.urls import path,include
from . import views

app_name='compiler'

urlpatterns = [
    path('submit/',include('submit.urls'))
]