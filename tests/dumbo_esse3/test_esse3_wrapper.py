import pytest

from dumbo_esse3.esse3_wrapper import Esse3Wrapper
from dumbo_esse3.primitives import DateTime
from tests.test_environment import USERNAME, PASSWORD


@pytest.fixture
def esse3_wrapper():
    return Esse3Wrapper.create(
        username=USERNAME,
        password=PASSWORD,
        debug=False,
        detached=False,
    )


def test_fetch_courses(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert len(courses) >= 0  # just to avoid a warning


def test_fetch_exams(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    if not courses:
        return
    exams = esse3_wrapper.fetch_exams(courses[0])
    assert len(exams) >= 0  # just to avoid a warning


def test_fetch_students(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    if not courses:
        return
    exams = esse3_wrapper.fetch_exams(courses[0])
    if exams:
        students = esse3_wrapper.fetch_students(courses[0], exams[0].date_and_time)
        assert len(students) == exams[0].number_of_students.value


def test_is_exam_present(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    if not courses:
        return
    exams = esse3_wrapper.fetch_exams(courses[0])
    if exams:
        assert esse3_wrapper.is_exam_present(courses[0], exams[0].date_and_time)
    else:
        today = DateTime.now()
        assert not esse3_wrapper.is_exam_present(courses[0], today)


def test_fetch_thesis_list(esse3_wrapper):
    theses = esse3_wrapper.fetch_thesis_list()
    assert len(theses) >= 0  # just to avoid a warning


def test_fetch_registers(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    assert len(registers) >= 0  # just to avoid a warning


def test_fetch_register_activities(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    if not registers:
        return
    activities = esse3_wrapper.fetch_register_activities(registers[0])
    assert len(activities) >= 0  # just to avoid a warning
