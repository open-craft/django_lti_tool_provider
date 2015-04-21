import logging

from django.dispatch import Signal, receiver

from django_lti_tool_provider.models import LtiUserData


_logger = logging.getLogger(__name__)


class Signals(object):
    class Grade(object):
        updated = Signal(providing_args=["user", "new_grade"])

    class LTI(object):
        received = Signal(providing_args=["user", "lti_data"])


@receiver(Signals.Grade.updated, dispatch_uid="django_lti_grade_updated")
def grade_updated_handler(sender, **kwargs):
    user = kwargs.get('user', None)
    grade = kwargs.get('grade', None)
    custom_key = kwargs.get('custom_key', None)
    _send_grade(user, grade, custom_key)


def _send_grade(user, grade, custom_key):
    try:
        if user is None:
            raise ValueError(u"User is not specified")
        lti_user_data = LtiUserData.objects.get(user=user, custom_key=custom_key)
        lti_user_data.send_lti_grade(grade)
    except LtiUserData.DoesNotExist:
        _logger.info(
            u"No LTI parameters for user {user} and key {key} stored - probably never sent an LTI request"
            .format(user=user.username, key=custom_key)
        )
        raise
    except Exception:  # pylint:disable=too-broad-exception
        _logger.exception(
            u"Exception occurred in lti module when sending grade for user {user} and key {key}.".format(
                user=user, key=custom_key
            )
        )
        raise
