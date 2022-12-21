import pytest
from freezegun import freeze_time
from dumbo_esse3.primitives import DateTime, NumberOfStudents, Student, StudentId, StudentName, StudentThesisState, CdL, \
    RegisterActivity, NumberOfHours, ActivityType, ActivityTitle, StudentGraduation, FinalScore


def test_exam_date_time_order():
    assert DateTime.now() <= DateTime.now()


@freeze_time("2022-10-15 08:12")
def test_date_time_smart_parse():
    assert DateTime.smart_parse("3112 0900") == DateTime.parse(f"31/12/2022 09:00")
    assert DateTime.smart_parse("0101 0900") == DateTime.parse(f"01/01/2023 09:00")


@freeze_time("2022-10-15 08:12")
def test_date_time_now():
    assert DateTime.now() == DateTime.parse("15/10/2022 08:15")


@freeze_time("2022-10-15 07:59")
def test_date_time_now_early():
    assert DateTime.now() == DateTime.parse("15/10/2022 08:00")


@freeze_time("2022-10-15 23:46")
def test_date_time_now_late():
    assert DateTime.now() == DateTime.parse("16/10/2022 08:00")


def test_date_time_add_days():
    assert DateTime.parse(f"31/12/2022 09:00").add_days(1) == DateTime.parse("01/01/2023 09:00")


def test_date_time_add_hours():
    assert DateTime.parse(f"31/12/2022 23:00").add_hours(9) == DateTime.parse("01/01/2023 08:00")


def test_date_time_add_hours_may_rise_error():
    with pytest.raises(ValueError):
        DateTime.parse("31/12/2022 23:00").add_hours(1)


def test_date_time_stringify_time():
    assert DateTime.parse("15/10/2022 09:15").stringify_time() == "09:15"


def test_number_of_student_positive():
    assert NumberOfStudents(10).positive
    assert not NumberOfStudents(0).positive


def test_student_of():
    assert Student.of("1234", "ROSSI MARIO").id == StudentId("1234")


def test_student_thesis_state_of():
    assert StudentThesisState.of(
        Student.of("1234", "ROSSI MARIO"),
        CdL("INFORMATICA [0733] - Corso di Laurea"),
        StudentThesisState.State.MISSING
    ).state == StudentThesisState.State.MISSING


def test_register_activity_end_date_time():
    assert RegisterActivity.of(
        DateTime.parse("15/10/2022 09:30"),
        NumberOfHours(3),
        ActivityType.LECTURE,
        ActivityTitle("Introduction"),
    ).end_date_time == DateTime.parse("15/10/2022 12:30")


def test_register_activity_cannot_span_multiple_days():
    with pytest.raises(ValueError):
        RegisterActivity.of(
            DateTime.parse("15/10/2022 22:30"),
            NumberOfHours(2),
            ActivityType.LECTURE,
            ActivityTitle("Night event"),
        )


def test_student_types_are_validated():
    with pytest.raises(TypeError):
        Student("1234", "ROSSI MARIO")


def test_student_graduation_with_laude_needs_110():
    with pytest.raises(ValueError):
        StudentGraduation.of("123", "ROSSI MARIO", 100).with_laude()
    with pytest.raises(ValueError):
        StudentGraduation(Student.of("123", "ROSSI MARIO"), FinalScore(100), laude=True)
    assert StudentGraduation.of("123", "ROSSI MARIO", 110).with_laude().laude
    assert StudentGraduation.of("123", "ROSSI MARIO", 113).with_laude().laude


def test_student_graduation_with_special_mention_needs_with_laude():
    with pytest.raises(ValueError):
        StudentGraduation.of("123", "ROSSI MARIO", 110).with_special_mention()
    with pytest.raises(ValueError):
        StudentGraduation(Student.of("123", "ROSSI MARIO"), FinalScore(110), special_mention=True)
    assert StudentGraduation.of("123", "ROSSI MARIO", 110).with_laude().with_special_mention().special_mention
    assert StudentGraduation.of("123", "ROSSI MARIO", 113).with_laude().with_special_mention().special_mention
