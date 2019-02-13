import json
import warnings
from base64 import b64encode, encodestring, decodestring
from collections import OrderedDict
from enum import Enum
from limesurveyrc2api.exceptions import LimeSurveyError
from posixpath import splitext, abspath, dirname, join

from limesurveyrc2api._utils import IDGenerator

id_generator = IDGenerator(19)

question_template = '''\
<?xml version="1.0" encoding="UTF-8"?>
<document>
 <LimeSurveyDocType>Question</LimeSurveyDocType>
 <DBVersion>355</DBVersion>
 <languages>
  <language>en</language>
 </languages>
 <questions>
  %(fieldnames)s
  %(rows)s
 </questions>
</document>
'''

question_fieldnames = (
    'qid', 'parent_qid', 'sid', 'gid', 'type', 'title', 'question', 'preg',
    'help', 'other', 'mandatory', 'question_order', 'language', 'scale_id',
    'same_default', 'relevance', 'modulename'
)

class QUESTION_TYPE(Enum):

    # Single choice questions
    LIST_5_POINT_CHOICE = '5'
    LIST_DROPDOWN = '!'
    LIST_WITH_COMMENT = 'O'
    LIST_RADIO = 'L'
    # Arrays
    ARRAY = 'F'
    ARRAY_10_POINT_CHOICE = 'B'
    ARRAY_5_POINT_CHOICE = 'A'
    ARRAY_INCREASE_SAME_DECREASE = 'E'
    ARRAY_NUMBERS = ':'
    ARRAY_TEXTS = ';'
    ARRAY_YES_NO_UNCERTAIN = 'C'
    ARRAY_COLUMN = 'H'
    ARRAY_DUAL_SCALE = '1'
    # Mask questions
    MASK_DATE_TIME = 'D'
    MASK_EQUATION = '*'
    MASK_FILE_UPLOAD = '|'
    MASK_GENDER = 'G'
    MASK_LANGUAGE_SWITCH = 'I'
    MASK_MULTIPLE_NUMERICAL_INPUT = 'K'
    MASK_NUMERICAL_INPUT = 'N'
    MASK_RANKING = 'R'
    MASK_TEXT_DISPLAY = 'X'
    MASK_YES_NO = 'Y'
    # Text questions
    TEXT_HUGE_FREE_TEXT = 'U'
    TEXT_LONG_FREE_TEXT = 'T'
    TEXT_MULTIPLE_SHORT_TEXT = 'Q'
    TEXT_SHORT_FREE_TEXT = 'S'
    # Multiple choice questions
    MULTIPLE_CHOICE = 'M'
    MULTIPLE_CHOICE_WITH_COMMENT = 'P'

def render_lsq(fields):
    fieldnames_str = render_lsq_fieldnames(fields.keys())
    rows_str = render_lsq_rows(fields)
    lsq_str = question_template % {
        'fieldnames': fieldnames_str,
        'rows': rows_str
    }
    return encodestring(lsq_str.encode('utf-8')).decode('utf-8')

def render_lsq_fieldnames(fieldnames):
    l = ['<fields>']
    for fieldname in fieldnames:
        l.append('<fieldname>%s</fieldname>' % fieldname)
    l.append('</fields>')
    return ''.join(l)

def render_lsq_rows(fieldvalues):
    l = ['<rows><row>']
    for fieldname, value in fieldvalues.items():
        if value is None:
            l.append('<%s/>' % fieldname)
        else:
            l.append('<%(fieldname)s><![CDATA[%(value)s]]></%(fieldname)s>' % {
                'fieldname': fieldname,
                'value': value
            })
    l.append('</row></rows>')
    return ''.join(l)

class _Survey(object):

    def __init__(self, api):
        self.api = api

    def list_surveys(self, username=None):
        """
        List surveys accessible to the specified username.

        Parameters
        :param username: LimeSurvey username to list accessible surveys for.
        :type username: String
        """
        method = "list_surveys"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", username or self.api.username)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)
        if response_type is dict and "status" in response:
            status = response["status"]
            if status == "No surveys found":
                return []
            error_messages = [
                "Invalid user",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def list_questions(self, survey_id,
                       group_id=None, language=None):
        """
        Return a list of questions from the specified survey.

        Parameters
        :param survey_id: ID of survey to list questions from.
        :type survey_id: Integer
        :param group_id: ID of the question group to filter on.
        :type group_id: Integer
        :param language: Language of survey to return for.
        :type language: String
        """
        method = "list_questions"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("iGroupID", group_id),
            ("sLanguage", language)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            if status == "No questions found":
                return []
            error_messages = [
                "Error: Invalid survey ID",
                "Error: Invalid language",
                "Error: IMissmatch in surveyid and groupid",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def add_survey(self, title,
                   survey_id=None, language=None, format_=None):
        """Add an empty survey with minimum details.
        
        Parameters
        :param title: Title of the new Survey.
        :type: String
        :param survey_id: The desired ID of the Survey to add.
        :type: Integer
        :param language: Default language of the Survey.
        :type: String
        :param format_: (optional) Question appearance format (A, G or S)
                for "All on one page", "Group by Group", "Single questions",
                default to group by group (G).
        :type: String
        """
        method = "add_survey"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", int(survey_id) if survey_id else 1),
            ("sSurveyTitle", title),
            ("sSurveyLanguage", language or "en"),
            ("sForamt", format_ or "G")
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Creation Failed result"
                "Faulty parameters",
                "No permission",
                "Invalid session key",
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int, response_type
        return response

    def delete_survey(self, survey_id):
        """ Delete a survey.
        
        Parameters
        :param survey_id: The ID of the Survey to be deleted.
        :type: Integer
        """
        method = "delete_survey"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def export_responses(self, survey_id, document_type, language_code=None,
                         completion_status='all', heading_type='code',
                         response_type='short', from_response_id=None,
                         to_response_id=None, fields=None):
        """ Export responses in base64 encoded string.
        
        Parameters
        :param survey_id: Id of the Survey.
        :type survey_id: Integer
        :param document_type: Any format available by plugins 
                             (e.g. pdf, csv, xls, doc, json)
        :type document_type: String
        :param language_code: (optional) The language to be used.
        :type language_code: String
        :param completion_status: (optional) 'complete', 'incomplete' or 'all'
        :type completion_status: String
        :param heading_type: (optional) 'code', 'full' or 'abbreviated'
        :type heading_type: String
        :param response_type: (optional) 'short' or 'long'
        :type response_type: String
        :param from_response_id: (optional)
        :type from_response_id: Integer
        :param to_response_id: (optional)
        :type to_response_id: Integer
        :param fields: (optional) Selected fields.
        :type fields: Array
        """
        method = "export_responses"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("sDocumentType", document_type),
            ("sLanguageCode", language_code),
            ("sCompletionStatus", completion_status),
            ("sHeadingType", heading_type),
            ("sResponseType", response_type),
            ("iFromResponseID", from_response_id),
            ("iToResponseID", to_response_id),
            ("aFields", fields)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Language code not found for this survey.",
                "No Data, could not get max id.",
                "No Data, survey table does not exist",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is str
        return response

    def add_question(self, survey_id, group_id, question,
                     question_help=None, question_type=None, mandatory=None):
        method = "import_question"
        if not question_type:
            question_type = 'TEXT_SHORT_FREE_TEXT'
        question_type = question_type.upper()
        if question_type not in QUESTION_TYPE.__members__:
            raise ValueError('invalid question type')
        question_type = getattr(QUESTION_TYPE, question_type).value
        mandatory = mandatory if mandatory else 'N'
        fields = dict.fromkeys(question_fieldnames)
        fields.update({
            'parent_qid': 0,
            'sid': int(survey_id),
            'gid': int(group_id),
            'title': 'q' + id_generator.generate_id(),
            'question': question,
            'help': question_help,
            'type': question_type,
            'mandatory': mandatory,
            'language': 'en'
        })
        lsq_str = render_lsq(fields)
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("iGroupID", group_id),
            ("sImportData", lsq_str),
            ("sImportDataType", 'lsq'),
            # ('sMandatory', 'N'),
            # ("sNewQuestionTitle", 'First question'),
            # ("sNewqQuestion", 'Tell us your gender'),
            # ("sNewQuestionHelp", 'A simple question that asks for your gender'),
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Error: ...",  # TODO: Unclear what might be returned here
                "Invalid extension",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int  # the new survey id
        return response

    def delete_question(self, question_id):
        """Delete a question from a survey .
        
        Returns the id of the deleted question.
        
        Arguments:
            question_id Integer -- ID of the Question to delete.
        
        Returns:
            Integer -- ID of the deleted Question.
        
        Raises:
            LimeSurveyError -- Error status.
        """
        method = "delete_question"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iQuestionID", question_id)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int
        return response

    def import_survey(self, path_to_import_survey, new_name=None,
                      dest_survey_id=None):
        """ Import a survey. Allowed formats: lss, csv, txt or lsa

        Parameters
        :param path_to_import_survey: Path to survey as file to copy.
        :type path_to_import_survey: String
        :param new_name: (optional) The optional new name of the survey
                    Important! Seems only to work if lss file is given!
        :type new_name: String
        :param dest_survey_id: (optional) This is the new ID of the survey - 
                          if already used a random one will be taken instead
        :type dest_survey_id: Integer
        """
        import_datatype = splitext(path_to_import_survey)[1][1:]
        # TODO: Naming seems only to work with lss files - why?
        if import_datatype != 'lss' and new_name:
            warnings.warn("New naming seems only to work with lss files",
                          RuntimeWarning)
        # encode import data
        with open(path_to_import_survey, 'rb') as f:
            # import data must be a base 64 encoded string
            import_data = b64encode(f.read())
            # decoding needed because json.dumps() in method get of
            # class LimeSurvey can not encode bytes
            import_data = import_data.decode('ascii')

        method = "import_survey"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("sImportData", import_data),
            ("sImportDataType", import_datatype),
            ("sNewSurveyName", new_name),
            ("DestSurveyID", dest_survey_id)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Error: ...",  # TODO: Unclear what might be returned here
                "Invalid extension",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int  # the new survey id
        return response

    def activate_survey(self, survey_id):
        """ Activate an existing survey.

        Return the result of the activation
        
        Arguments:
            survey_id Integer -- Id of the Survey to be activated.
        
        Returns:
            list -- In case of success result of the activation.
        """
        method = "activate_survey"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Error: Invalid survey ID",
                "Error: Activation Error",
                "Error: ...",  # TODO: what could be output of ActivateResults?
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def activate_tokens(self, survey_id, attribute_fields=[]):
        """
        
        Parameters
        :param survey_id: ID of the Survey where a participants table will
            be created for.
        :type survey_id: Integer
        :param attribute_fields: An array of integer describing any additional 
            attribute fiields.
        :type attribute_fields: Array
        """
        method = "activate_tokens"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyId", survey_id),
            ("aAttributeFields", attribute_fields)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Error: Invalid survey ID",
                "Survey participants table could not be created",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def list_groups(self, survey_id):
        """ Return the ids and all attributes of groups belonging to survey.
        
        Parameters
        :param survey_id: ID of the survey containing the groups.
        :type survey_id: Integer
        """
        method = "list_groups"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            if status == "No groups found":
                return []
            error_messages = [
                "Error: Invalid survey ID",
                "No permission"
                "Invalid S ession key"  # typo in remotecontrol_handle.php
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is list
        return response

    def add_group(self, survey_id, group_title, group_description=None):
        """Add an empty group with minimum details to a chosen survey.
        
        Used as a placeholder for importing questions.
        Returns the groupid of the created group.

        Parameters
        :param survey_id: ID of the survey containing the groups.
        :type survey_id: Integer
        :param group_title: Name of the group.
        :type group_title: String
        :param group_description: Optional description of the group.
        :type group_description: String
        """
        method = "add_group"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("sGroupTitle", group_title),
            ("sGroupDescription", group_description or '')
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Creation Failed result"
                "Faulty parameters",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int
        return response

    def get_survey_properties(self, survey_id, settings=None):
        """RPC Routine to get survey properties.
        
        Get properties of a survey.
        All internal properties of a survey are available.
        
        Arguments:
            survey_id Integer -- The id of the Survey to be checked.
        
        Keyword Arguments:
            settings {List} -- (optional) The properties to get.
        """
        method = "get_survey_properties"
        survey_data = {}
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("aSurveySetting", settings)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)

        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "No valid Data",
                "Invalid survey ID",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is dict
        return response

    def set_survey_properties(self, survey_id, settings):
        """Set survey properties.
        
        for the list of available properties.
        Properties available are restricted.

        Always
            * sid
            * active
            * language
            * additional_languages

        If survey is active
            * anonymized
            * datestamp
            * savetimings
            * ipaddr
            * refurl

        In case of partial success : return an array with key as properties
                    and value as boolean , true if saved with success.
        
        Arguments:
            survey_id Integer -- ID of the Survey.
            settings dict -- An dict with the particular fieldnames as keys
                    and their values to set on that particular Survey
        
        Returns:
            dict -- Of succeeded and failed nodifications according to
                internal validation.
        
        Raises:
            LimeSurveyError -- Error status.
        """
        method = "set_survey_properties"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("aSurveyData", settings)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)
        print(response_type)
        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Invalid survey ID"
                "No valid Data",
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is dict
        return response

    def add_response(self, survey_id, response_data):
        method = "add_response"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("aResponseData", response_data)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)
        print(response_type)
        if response_type is dict and "status" in response:
            status = response["status"]
            error_messages = [
                "Invalid survey ID"
                "No permission",
                "Invalid session key"
            ]
            for message in error_messages:
                if status == message:
                    raise LimeSurveyError(method, status)
        else:
            assert response_type is int
        return response

    def export_responses(self, survey_id, document_type,
                         language_code=None, completion_status='all',
                         heading_type='code', response_type='short',
                         from_response_id=None, to_response_id=None,
                         fields=None):
        method = "export_responses"
        params = OrderedDict([
            ("sSessionKey", self.api.session_key),
            ("iSurveyID", survey_id),
            ("sDocumentType", document_type),
            ("sLanguageCode", language_code),
            ("sCompletionStatus", completion_status),
            ("sHeadingType", heading_type),
            ("sResponseType", response_type),
            ("sFromResponseID", from_response_id),
            ("sToResponseID", to_response_id),
            ("aFields", fields)
        ])
        response = self.api.query(method=method, params=params)
        response_type = type(response)
        if response_type is dict and "status" in response:
            status = response["status"]
            raise LimeSurveyError(method, status)
        assert response_type is str
        return json.loads(decodestring(response.encode('utf-8')))
