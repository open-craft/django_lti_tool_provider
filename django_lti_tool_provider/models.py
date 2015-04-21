import logging

from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField

from ims_lti_py.tool_provider import DjangoToolProvider
from django.conf import settings


_logger = logging.getLogger(__name__)


class LtiUserData(models.Model):
    user = models.ForeignKey(User)
    edx_lti_parameters = JSONField(default={})
    custom_key = models.CharField(max_length=400, null=False, default='')

    class Meta:
        app_label = "django_lti_tool_provider"
        unique_together = (("user", "custom_key"),)

    @property
    def _required_params(self):
        return ["lis_result_sourcedid", "lis_outcome_service_url"]

    def _validate_lti_grade_request(self, grade):
        def _log_and_throw(message):
            _logger.error(message)
            raise ValueError(message)

        if not 0 <= grade <= 1:
            _log_and_throw("Grade should be in range [0..1], got {grade}".format(grade=grade))

        if not self.edx_lti_parameters:
            _log_and_throw("LTI grade parameters is not set".format(params=self._required_params))

        empty_parameters = [
            parameter for parameter in self._required_params
            if not self.edx_lti_parameters.get(parameter, '')
        ]

        if empty_parameters:
            parameters_repr = ", ".join(empty_parameters)
            _log_and_throw(
                "Following required LTI parameters are not set: {parameters}".format(parameters=parameters_repr)
            )

    def send_lti_grade(self, grade):
        """ Instantiates DjangoToolProvider using stored lti parameters and sends grade """
        self._validate_lti_grade_request(grade)
        provider = DjangoToolProvider(settings.LTI_CLIENT_KEY, settings.LTI_CLIENT_SECRET, self.edx_lti_parameters)
        outcome = provider.post_replace_result(grade)

        _logger.info(u"LTI grade request was {successful}. Description is {description}".format(
            successful="successful" if outcome.is_success() else "unsuccessful", description=outcome.description
        ))

        return outcome
