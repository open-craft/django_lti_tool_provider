from django.core.exceptions import ImproperlyConfigured
from django.views.generic import View
import oauth2
import logging

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from ims_lti_py.tool_provider import DjangoToolProvider

from django_lti_tool_provider.models import LtiUserData
from django_lti_tool_provider.signals import Signals


_logger = logging.getLogger(__name__)


class LTIView(View):
    """ View handling LTI requests """
    authentication_manager = None

    PASS_TO_AUTHENTICATION_HOOK = {
        'lis_person_sourcedid': 'username',
        'lis_person_contact_email_primary': 'email',
        'user_id': 'user_id'
    }

    SESSION_KEY = 'lti_parameters'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        if self.authentication_manager is None:
            raise ImproperlyConfigured(u"AuthenticationManager is not set")

        return super(LTIView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.process_request(request)

    def post(self, request, *args, **kwargs):
        return self.process_request(request)

    def process_request(self, request):
        if not request.user.is_authenticated():
            try:
                lti_parameters = self._get_lti_parameters_from_request(request)
            except oauth2.Error, e:
                _logger.exception(u"Invalid LTI Request")
                return HttpResponseBadRequest(u"Invalid LTI Request: " + e.message)

            lti_data = {
                hook_name: lti_parameters.get(lti_name, None)
                for lti_name, hook_name in self.PASS_TO_AUTHENTICATION_HOOK.items()
            }

            self.authentication_manager.authentication_hook(request, **lti_data)

        if request.user.is_authenticated():
            return self.process_authenticated_lti(request)
        else:
            return self.process_anonymous_lti(request)

    @classmethod
    def _get_lti_parameters_from_request(cls, request):
        provider = DjangoToolProvider(settings.LTI_CLIENT_KEY, settings.LTI_CLIENT_SECRET, request.POST)
        provider.valid_request(request)
        return provider.to_params()

    @classmethod
    def _store_lti_parameters(cls, user, parameters):
        """
        Filters out OAuth parameters than stores LTI parameters into the DB, creating or updating record as needed
        """
        lti_params = {
            key: value
            for key, value in parameters.iteritems()
            if 'oauth' not in key
        }
        custom_key = cls.authentication_manager.vary_by_key(lti_params)

        # implicitly tested by test_views
        if custom_key is None:
            custom_key = ''

        lti_user_data, created = LtiUserData.objects.get_or_create(user=user, custom_key=custom_key)
        if not created:
            _logger.debug(u"Replaced LTI parameters for user %s", user.username)
        lti_user_data.edx_lti_parameters = lti_params
        lti_user_data.save()
        return lti_user_data

    @classmethod
    def register_authentication_manager(cls, manager):
        """ Registers authentication manager """
        cls.authentication_manager = manager

    @classmethod
    def process_anonymous_lti(cls, request):
        """
        This method handles LTI request if it was sent prior to tool authorization. In such a case, we need user
        authenticated first. Unfortunately, it looses POST data in the process, so when it gets back original LTI
        request is gone. So we save important parts of it into session to retrieve when authentication happens
        """
        try:
            lti_parameters = cls._get_lti_parameters_from_request(request)
        except oauth2.Error, e:
            _logger.exception(u"Invalid LTI Request")
            return HttpResponseBadRequest(u"Invalid LTI Request: " + e.message)

        request.session[cls.SESSION_KEY] = lti_parameters
        request.session.save()
        return HttpResponseRedirect(cls.authentication_manager.anonymous_redirect_to(request, lti_parameters))

    @classmethod
    def process_authenticated_lti(cls, request):
        """
        There are two options:
        1. This is actual LTI request made with cookies already set - need parsing and validating LTI parameters
        2. This is OpenID redirect from edx if actual LTI request was send anonymously - already validated
           LTI parameters and stored them in session - take them from session

        When lti parameters are ready (either taken from session or parsed and validated from request) store them
        in DB for later
        """
        if cls.SESSION_KEY in request.session and not cls._is_new_lti_request(request):
            lti_parameters = request.session[cls.SESSION_KEY]
            del request.session[cls.SESSION_KEY]
        else:
            try:
                lti_parameters = cls._get_lti_parameters_from_request(request)
            except oauth2.Error, e:
                _logger.exception(u"Invalid LTI Request")
                return HttpResponseBadRequest(u"Invalid LTI Request: " + e.message)

        lti_data = cls._store_lti_parameters(request.user, lti_parameters)
        Signals.LTI.received.send(cls, user=request.user, lti_data=lti_data)

        return HttpResponseRedirect(cls.authentication_manager.authenticated_redirect_to(request, lti_parameters))

    @classmethod
    def _is_new_lti_request(cls, request):
        return 'lis_result_sourcedid' in request.POST
