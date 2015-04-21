import ddt
from django.contrib.auth.models import User

from django.test import TestCase
from mock import patch, Mock, PropertyMock

from django_lti_tool_provider.models import LtiUserData
from django_lti_tool_provider.signals import grade_updated_handler, _send_grade


@ddt.ddt
@patch('django_lti_tool_provider.signals._send_grade')
class SignalHandlersTests(TestCase):
    @ddt.data(
        (Mock(spec=User),  0.5),
        (Mock(spec=User), 0.2),
        (u"something to indicate that grade_updated_handler is dumb and don't do any type checking", 0.2),
    )
    @ddt.unpack
    def test_handle_grade_updated(self, user, grade, send_grade_mock):
        grade_updated_handler(Mock(), user=user, grade=grade)
        send_grade_mock.assert_called_once_with(user, grade, None)

    @ddt.data(
        (Mock(spec=User), None, 0.5),
        (Mock(spec=User), "custom_key", 0.2),
        (u"something to indicate that grade_updated_handler is dumb and don't do any type checking", 12, 0.2),
    )
    @ddt.unpack
    def test_handle_grade_with_custom_key_updated(self, user, custom_key, grade, send_grade_mock):
        grade_updated_handler(Mock(), user=user, grade=grade, custom_key=custom_key)
        send_grade_mock.assert_called_once_with(user, grade, custom_key)


@ddt.ddt
@patch('django_lti_tool_provider.signals.LtiUserData.objects.get')
class SendGradeTests(TestCase):
    def test_send_grade_given_none_instance_raises_assertion_error(self, _):
        with self.assertRaises(ValueError):
            _send_grade(None, 0, None)

    def test_send_grade_no_lti_user_data_raises_does_not_exist(self, get_user_data):
        get_user_data.side_effect = LtiUserData.DoesNotExist()
        with self.assertRaises(LtiUserData.DoesNotExist):
            _send_grade(Mock(), 0, None)

    @ddt.data(
        (Mock(spec=User), None),
        (Mock(spec=User), "123"),
        (Mock(spec=User), u"assignment12"),
    )
    @ddt.unpack
    def test_send_grade_requests_correct_lti_user_data(self, user, custom_key, get_user_data):
        get_user_data.assert_not_called()
        _send_grade(user, 0, custom_key)
        get_user_data.assert_called_with(user=user, custom_key=custom_key)

    @ddt.data(0.1, 0.0, 0.87, 0.15, 1.0, 0.33)
    def test_send_grade_sends_grade_request(self, grade, get_user_data):
        user_data = Mock()
        get_user_data.return_value = user_data
        _send_grade(Mock(), grade, None)
        user_data.send_lti_grade.assert_called_with(grade)

    @ddt.data(
        AssertionError, ValueError, AttributeError, ZeroDivisionError,
        TypeError, RuntimeError
    )
    def test_send_grade_loose_suppresses_and_logs_exceptions(self, exception_type, get_user_data):
        get_user_data.side_effect = exception_type()
        with self.assertRaises(exception_type), \
                patch("django_lti_tool_provider.signals._logger.exception") as patched_log_exception:
            _send_grade(Mock(), 0, None)
            patched_log_exception.assert_called_once()
            call_args = patched_log_exception.call_args[0]
            self.assertIn("Exception occurred in lti module", call_args[0])

    def test_send_grade_loose_suppresses_and_logs_does_not_exist(self, get_user_data):
        get_user_data.side_effect = LtiUserData.DoesNotExist()
        with self.assertRaises(LtiUserData.DoesNotExist), \
                patch("django_lti_tool_provider.signals._logger.info") as patched_log_info:
            _send_grade(Mock(), 0, None)
            patched_log_info.assert_called_once()
            call_args = patched_log_info.call_args[0]
            self.assertIn("No LTI parameters", call_args[0])
