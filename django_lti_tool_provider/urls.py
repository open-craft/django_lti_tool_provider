from django.conf.urls import patterns, url

from django_lti_tool_provider import views as lti_views

urlpatterns = [
    url(r'', lti_views.LTIView.as_view(), name='lti')
]
