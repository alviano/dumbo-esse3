import pytest

from dumbo_esse3.esse3_wrapper import Esse3Wrapper
from dumbo_esse3.primitives import DateTime, Course, ActivityTitle, ExamType, ExamDescription, ExamNotes, \
    RegisterActivity, NumberOfHours, ActivityType, StudentThesisState, GraduationDay
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


def test_add_exam(esse3_wrapper):
    courses = esse3_wrapper.fetch_courses()
    assert courses
    old_exams = esse3_wrapper.fetch_exams(courses[0])
    esse3_wrapper.add_exam(
        course=courses[0],
        exam=DateTime.parse("18/02/2023 09:00"),
        exam_type=ExamType.WRITTEN_AND_ORAL,
        description=ExamDescription("Scritto, discussione ed eventuale orale"),
        notes=ExamNotes("Aula indicata sul sito del corso. L'orale è facoltativo. (Room is reported on the website of the course. Oral examination is optional.)")
    )
    new_exams = esse3_wrapper.fetch_exams(courses[0])
    assert len(new_exams) == len(old_exams) + 1


def test_fetch_registers(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    assert len(registers) == 3
    assert registers[0].course == Course("CYBER OFFENSE AND DEFENSE - [27008777]")


def test_fetch_register_activities(esse3_wrapper):
    registers = esse3_wrapper.fetch_registers()
    activities = esse3_wrapper.fetch_register_activities(registers[0])
    assert len(activities) == 15
    assert activities[0].title == ActivityTitle("Introduction")


def test_add_and_remove_register_activity(esse3_wrapper):
    register = esse3_wrapper.fetch_registers()[2]
    activities = esse3_wrapper.fetch_register_activities(register)
    assert len(activities) == 0

    assert esse3_wrapper.add_register_activity(register, RegisterActivity.of(
        DateTime.parse("24/11/2022 09:30"),
        NumberOfHours(2),
        ActivityType.LECTURE,
        ActivityTitle("Example"),
    ))
    activities = esse3_wrapper.fetch_register_activities(register)
    assert len(activities) == 1

    assert activities[0].title == ActivityTitle("Example")
    assert esse3_wrapper.delete_register_activity(register, 1)
    activities = esse3_wrapper.fetch_register_activities(register)
    assert len(activities) == 0

    assert not esse3_wrapper.delete_register_activity(register, 1)


def test_fetch_theses_list(esse3_wrapper):
    theses = esse3_wrapper.fetch_thesis_list()
    assert len(theses) == 2
    assert theses[0].state == StudentThesisState.State.UNSIGNED
    assert theses[1].state == StudentThesisState.State.MISSING


def test_fetch_theses_sign(esse3_wrapper):
    theses = esse3_wrapper.fetch_thesis_list()
    esse3_wrapper.sign_thesis(theses[0].student)
    theses = esse3_wrapper.fetch_thesis_list()
    assert theses[0].state == StudentThesisState.State.SIGNED


def test_fetch_graduation_days(esse3_wrapper):
    days = esse3_wrapper.fetch_graduation_days()
    assert len(days) == 2
    assert days[0] == GraduationDay("Commissione Master del 19 dicembre 2022")
