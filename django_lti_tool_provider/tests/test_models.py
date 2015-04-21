import ddt
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError

from django.test import TestCase
from django.test.utils import override_settings
from mock import patch

from django_lti_tool_provider.models import LtiUserData


@ddt.ddt
@patch('django_lti_tool_provider.models.DjangoToolProvider')
class LtiUserDataTest(TestCase):
    minimal_valid_lti_parameters = {
        'lis_result_sourcedid': 'result-sourced-id',
        'lis_outcome_service_url': 'lis-outcome-service-url'
    }

    def setUp(self):
        self.model = LtiUserData(edx_lti_parameters=self.minimal_valid_lti_parameters)

    def test_send_lti_grade_empty_lti_parameters_raises_value_error(self, _):
        self.model.edx_lti_parameters = None
        with self.assertRaises(ValueError) as exc:
            self.model.send_lti_grade(0)
            self.assertEqual("LTI grade parameters is not set", exc.message)

    @ddt.data(
        {'lis_result_sourcedid': '111'},
        {'lis_outcome_service_url': '111'},
        {'lis_result_sourcedid': '', 'lis_outcome_service_url': '111'},
        {'lis_result_sourcedid': '111', 'lis_outcome_service_url': ''},
    )
    def test_send_lti_grade_missing_lti_parameters_raises_value_error(self, lti_parameters, _):
        self.model.edx_lti_parameters = lti_parameters
        with self.assertRaises(ValueError) as exc:
            self.model.send_lti_grade(0)
            self.assertIn("Following required LTI parameters are not set", exc.message)

    @ddt.data(
        -1, 2, 1 + 10 ** -10, -10 ** -10, 7, 5, 42, -14
    )
    def test_send_lti_grade_incorrect_grade_raises_value_error(self, incorrect_grade, _):
        with self.assertRaises(ValueError) as exc:
            self.model.send_lti_grade(incorrect_grade)
            self.assertIn("Grade should be in range [0..1]", exc.message)

    @override_settings(LTI_CLIENT_KEY='client_key', LTI_CLIENT_SECRET='lti_client_secret')
    def test_send_lti_grade_creates_tool_provider(self, tool_provider_constructor_mock):
        self.model.send_lti_grade(0)
        tool_provider_constructor_mock.assert_called_with('client_key', 'lti_client_secret', self.model.edx_lti_parameters)

    @ddt.data(*[1.0 - i * 0.1 for i in xrange(10, -1, -1)])
    def test_send_lti_grade_sends_replace_result_request(self, grade, tool_provider_constructor_mock):
        tool_provider_mock = tool_provider_constructor_mock.return_value
        self.model.send_lti_grade(grade)

        tool_provider_mock.post_replace_result.assert_called_with(grade)


class LtiUserDataDatabaseTest(TestCase):
    fixtures = ['test_lti_db.yaml']

    def setUp(self):
        self.user1 = User.objects.get(username='test1')
        self.user2 = User.objects.get(username='test2')

    def test_user_and_custom_key_uniqueness(self):
        LtiUserData.objects.create(user=self.user1)  # works
        LtiUserData.objects.create(user=self.user2)  # works

        LtiUserData.objects.create(user=self.user1, custom_key="123")  # works
        LtiUserData.objects.create(user=self.user1, custom_key="456")  # works

        with self.assertRaises(IntegrityError), transaction.atomic():
            LtiUserData.objects.create(user=self.user1)  # unique key exception

        with self.assertRaises(IntegrityError), transaction.atomic():
            LtiUserData.objects.create(user=self.user1, custom_key="456")  # unique key exception

        LtiUserData.objects.create(user=self.user2, custom_key="123")  # works again
        LtiUserData.objects.create(user=self.user2, custom_key="456")  # works again

        with self.assertRaises(IntegrityError), transaction.atomic():
            LtiUserData.objects.create(user=self.user2)  # unique key exception

        with self.assertRaises(IntegrityError), transaction.atomic():
            LtiUserData.objects.create(user=self.user2, custom_key="456")  # unique key exception