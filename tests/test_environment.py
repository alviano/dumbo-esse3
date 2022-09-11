import os

from dumbo_esse3.primitives import Username, Password, ExamDescription, ExamNotes, ExamType


USERNAME = os.environ.get("DUMBO_ESSE3_USERNAME")
PASSWORD = os.environ.get("DUMBO_ESSE3_PASSWORD")
EXAM_TYPE = os.environ.get("DUMBO_ESSE3_EXAM_TYPE")
EXAM_DESCRIPTION = os.environ.get("DUMBO_ESSE3_EXAM_DESCRIPTION")
EXAM_NOTES = os.environ.get("DUMBO_ESSE3_EXAM_NOTES")


def test_environment():
    assert USERNAME is not None
    assert PASSWORD is not None
    assert EXAM_TYPE is not None
    assert EXAM_DESCRIPTION is not None
    assert EXAM_NOTES is not None

    assert Username.parse(USERNAME).value == USERNAME
    assert Password.parse(PASSWORD).value == PASSWORD
    assert ExamType(EXAM_TYPE).value == EXAM_TYPE
    assert ExamDescription.parse(EXAM_DESCRIPTION).value == EXAM_DESCRIPTION
    assert ExamNotes.parse(EXAM_NOTES).value == EXAM_NOTES
