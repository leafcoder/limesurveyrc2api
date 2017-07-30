from tests.test_limesurvey import TestBase
from limesurveyrc2api.limesurvey import LimeSurveyError


class TestSurveys(TestBase):

    def test_list_surveys_success(self):
        """A valid request for list of surveys should not return empty."""
        result = self.api.survey.list_surveys()
        for survey in result:
            self.assertIsNotNone(survey.get('sid'))

    def test_list_surveys_failure(self):
        """An invalid request for list of surveys should raise an error."""
        with self.assertRaises(LimeSurveyError) as ctx:
            self.api.survey.list_surveys(username="not_a_user")
        self.assertIn("Invalid user", ctx.exception.message)

    def test_list_questions_success(self):
        """Listing questions for a survey should return a question list."""
        surveys = self.api.survey.list_surveys()
        survey_id = surveys[0].get('sid')

        result = self.api.survey.list_questions(survey_id)
        for question in result:
            self.assertEqual(survey_id, question["sid"])
            self.assertIsNotNone(question["gid"])
            self.assertIsNotNone(question["qid"])

    def test_list_questions_failure(self):
        """Listing questions for an invalid survey should returns an error."""
        surveys = self.api.survey.list_surveys()
        survey_id = TestBase.get_invalid_survey_id(surveys)

        with self.assertRaises(LimeSurveyError) as ctx:
            self.api.survey.list_questions(survey_id)
        self.assertIn("Error: Invalid survey ID", ctx.exception.message)
