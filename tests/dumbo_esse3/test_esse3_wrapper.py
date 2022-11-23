import pytest

from dumbo_esse3.esse3_wrapper import Esse3Wrapper
from dumbo_esse3.primitives import DateTime, Course, ActivityTitle
from tests.dumbo_esse3.utils.mocks import test_server  # noqa: F401; pylint: disable=unused-variable
from tests.test_environment import USERNAME, PASSWORD


@pytest.fixture
def esse3_wrapper(test_server):
    return Esse3Wrapper.create(
        username=USERNAME,
        password=PASSWORD,
        debug=False,
        detached=False,
    )


def test_fetch_courses(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert len(courses) == 6
    assert courses[0] == Course("CYBER OFFENSE AND DEFENSE [27008777]")


def test_fetch_exams(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert courses
    exams = esse3_wrapper.fetch_exams(courses[0])
    assert len(exams) == 2


def test_fetch_students(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert courses
    exams = esse3_wrapper.fetch_exams(courses[0])
    assert exams
    students = esse3_wrapper.fetch_students(courses[0], exams[0].date_and_time)
    assert len(students) == exams[0].number_of_students.value


def test_is_exam_present(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert courses
    exams = esse3_wrapper.fetch_exams(courses[0])
    assert exams
    assert esse3_wrapper.is_exam_present(courses[0], exams[0].date_and_time)


def test_not_is_exam_present(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert courses
    assert not esse3_wrapper.is_exam_present(courses[0], DateTime.parse("01/01/2022 09:00"))


def test_fetch_thesis_list(esse3_wrapper):
    theses = esse3_wrapper.fetch_thesis_list()
    assert len(theses) >= 0  # just to avoid a warning
    assert False


def test_fetch_registers(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    assert len(registers) == 3
    assert registers[1].course == Course("CYBER OFFENSE AND DEFENSE - [27008777]")


def test_fetch_register_activities(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    assert len(registers) > 1
    activities = esse3_wrapper.fetch_register_activities(registers[1])
    assert len(activities) == 15
    assert activities[0].title == ActivityTitle("Introduction")
