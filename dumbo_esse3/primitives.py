import dataclasses
import datetime
import enum

import typeguard

from dumbo_esse3.utils.primitives import bounded_string, bounded_integer
from dumbo_esse3.utils.validators import validate_dataclass, validate

from dateutil.relativedelta import relativedelta


@bounded_string(min_length=3, max_length=30, pattern=r'[A-Za-z0-9]*')
class Username:
    pass


@bounded_string(min_length=5, max_length=100, pattern=r'[^\n]*')
class Password:
    pass


@bounded_string(min_length=3, max_length=255, pattern=r'[A-Z ]+ \[\d+\]')
class Course:
    pass


@bounded_string(min_length=3, max_length=255, pattern=Course.pattern() + r' - [A-Za-z ]+')
class CdL:
    pass


@bounded_string(min_length=3, max_length=8, pattern=r'[0-9]*')
class StudentId:
    pass


@bounded_string(min_length=3, max_length=80, pattern=r"[A-ZÀÈÉÌÒÙ' ]*")
class StudentName:
    pass


class ExamType(enum.Enum):
    WRITTEN = 'S'
    ORAL = 'O'
    WRITTEN_AND_ORAL = 'SO'


@bounded_string(min_length=1, max_length=80, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]_-]*")
class ExamDescription:
    pass


@bounded_string(min_length=1, max_length=255, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]\n_-]*")
class ExamNotes:
    pass


@typeguard.typechecked
@dataclasses.dataclass(frozen=True, order=True)
class ExamDateTime:
    value: datetime.datetime

    def __post_init__(self):
        validate_dataclass(self)
        validate("value", self.value.hour, min_value=8, max_value=23, help_msg="Hour must be between 8 and 23")
        validate("value", self.value.minute, is_in=[0, 15, 30, 45], help_msg="Minutes must be aligned to 15")

    @staticmethod
    def parse(s: str) -> 'ExamDateTime':
        return ExamDateTime(datetime.datetime.strptime(s, "%d/%m/%Y %H:%M"))

    @staticmethod
    def smart_parse(s: str) -> 'ExamDateTime':
        s = s.replace('/', '').replace(':', '')
        s = s.split(' ', maxsplit=1)
        now = datetime.datetime.now()
        year = now.year
        res = datetime.datetime.strptime(f"{s[0]}{year} {s[1]}", "%d%m%Y %H%M")
        if res <= now:
            res = res + relativedelta(years=1)
        return ExamDateTime(res)

    @staticmethod
    def now() -> 'ExamDateTime':
        res = datetime.datetime.now()
        res = datetime.datetime(year=res.year, month=res.month, day=res.day, hour=res.hour, minute=res.minute)

        minutes_to_add = 15 - (res.minute % 15)
        if minutes_to_add != 15:
            res = res + datetime.timedelta(minutes=minutes_to_add)

        if res.hour < 8:
            res = datetime.datetime(year=res.year, month=res.month, day=res.day, hour=8, minute=0)
        elif res.hour > 23:
            res = datetime.datetime(year=res.year, month=res.month, day=res.day, hour=8, minute=0) + \
                  datetime.timedelta(days=1)

        return ExamDateTime(res)

    def __str__(self) -> str:
        return self.value.strftime("%d/%m/%Y %H:%M")

    def at_begin_of_day(self) -> 'ExamDateTime':
        return ExamDateTime(datetime.datetime(self.value.year, self.value.month, self.value.day, hour=8, minute=0))

    def add_days(self, days: int) -> 'ExamDateTime':
        return ExamDateTime(self.value + datetime.timedelta(days=days))

    def stringify_date(self) -> str:
        return self.value.strftime("%d/%m/%Y")

    def stringify_time(self) -> str:
        return self.value.strftime("%H:%M")

    def stringify_hour(self) -> str:
        return self.value.strftime("%-H")

    def stringify_minute(self) -> str:
        return self.value.strftime("%M")


@bounded_integer(min_value=0, max_value=300)
class NumberOfStudents:
    @property
    def positive(self) -> bool:
        return self.value > 0


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Exam:
    date_and_time: ExamDateTime
    number_of_students: NumberOfStudents

    def __post_init__(self):
        validate_dataclass(self)

    @staticmethod
    def of(date_and_time: ExamDateTime, number_of_students: int) -> 'Exam':
        return Exam(date_and_time, NumberOfStudents.of(number_of_students))

    @property
    def today_or_future(self) -> bool:
        return self.date_and_time >= ExamDateTime.now().at_begin_of_day()


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Student:
    id: StudentId
    name: StudentName

    def __post_init__(self):
        validate_dataclass(self)

    @staticmethod
    def of(student_id: str, student_name: str) -> 'Student':
        return Student(StudentId.parse(student_id), StudentName.parse(student_name))


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class StudentThesisState:
    student: Student
    cdl: CdL
    state: 'State'

    class State(enum.Enum):
        MISSING = 0
        UNSIGNED = 1
        SIGNED = 2

    @staticmethod
    def of(student: Student, cdl: CdL, state: State) -> 'StudentThesisState':
        return StudentThesisState(student, cdl, state)
