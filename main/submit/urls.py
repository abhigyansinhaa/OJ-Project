from django.urls import path
from submit.views import submit

app_name='submit'

urlpatterns=[   
    path('',submit,name='submit')
]