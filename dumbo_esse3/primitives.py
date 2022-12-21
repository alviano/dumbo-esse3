import dataclasses
import datetime
import enum

import typeguard

from dumbo_esse3.utils.primitives import bounded_string, bounded_integer
from dumbo_esse3.utils.validators import validate

from dateutil.relativedelta import relativedelta


class ExamType(enum.Enum):
    WRITTEN = 'S'
    ORAL = 'O'
    WRITTEN_AND_ORAL = 'SO'


class ActivityType(enum.Enum):
    LECTURE = 'Lezione'
    LAB = 'Laboratorio'
    EXERCISE = 'Esercitazione'
    SEMINAR = 'Seminario'


@bounded_integer(min_value=1, max_value=120)
class NumberOfHours:
    pass


@bounded_string(min_length=3, max_length=30, pattern=r'[A-Za-z0-9]*')
class Username:
    pass


@bounded_string(min_length=5, max_length=100, pattern=r'[^\n]*')
class Password:
    pass


@bounded_string(min_length=3, max_length=255, pattern=r'[A-Z ]+ (- )?\[M?\d+\]')
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


@bounded_string(min_length=1, max_length=80, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]_-]*")
class ExamDescription:
    pass


@bounded_string(min_length=1, max_length=255, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]\n_-]*")
class ExamNotes:
    pass


@bounded_string(min_length=1, max_length=40, pattern=r"[A-Za-z0-9 ]*")
class Semester:
    pass


@bounded_string(min_length=1, max_length=80, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]\+*_-]*")
class ActivityTitle:
    pass


@typeguard.typechecked
@dataclasses.dataclass(frozen=True, order=True)
class DateTime:
    value: datetime.datetime

    def __post_init__(self):
        validate("value", self.value.hour, min_value=8, max_value=23, help_msg="Hour must be between 8 and 23")
        validate("value", self.value.minute, is_in=[0, 15, 30, 45], help_msg="Minutes must be aligned to 15")

    @staticmethod
    def parse(s: str) -> 'DateTime':
        return DateTime(datetime.datetime.strptime(s, "%d/%m/%Y %H:%M"))

    @staticmethod
    def parse_date(s: str) -> 'DateTime':
        return DateTime.parse(f"{s} 08:00")

    @staticmethod
    def smart_parse(s: str) -> 'DateTime':
        s = s.replace('/', '').replace(':', '')
        s = s.split(' ', maxsplit=1)
        now = datetime.datetime.now()
        year = now.year
        res = datetime.datetime.strptime(f"{s[0]}{year} {s[1]}", "%d%m%Y %H%M")
        if res <= now:
            res = res + relativedelta(years=1)
        return DateTime(res)

    @staticmethod
    def now() -> 'DateTime':
        res = datetime.datetime.now()
        res = datetime.datetime(year=res.year, month=res.month, day=res.day, hour=res.hour, minute=res.minute)

        minutes_to_add = 15 - (res.minute % 15)
        if minutes_to_add != 15:
            res = res + datetime.timedelta(minutes=minutes_to_add)

        if res.hour < 8:
            res = datetime.datetime(year=res.year, month=res.month, day=res.day, hour=8, minute=0)

        return DateTime(res)

    def __str__(self) -> str:
        return self.value.strftime("%d/%m/%Y %H:%M")

    def at_time(self, hour, minute) -> 'DateTime':
        return DateTime(datetime.datetime(self.value.year, self.value.month, self.value.day, hour=hour, minute=minute))

    def at_begin_of_day(self) -> 'DateTime':
        return self.at_time(hour=8, minute=0)

    def add_days(self, days: int) -> 'DateTime':
        return DateTime(self.value + datetime.timedelta(days=days))

    def add_hours(self, hours: int) -> 'DateTime':
        return DateTime(self.value + datetime.timedelta(hours=hours))

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
    date_and_time: DateTime
    number_of_students: NumberOfStudents

    @staticmethod
    def of(date_and_time: DateTime, number_of_students: int) -> 'Exam':
        return Exam(date_and_time, NumberOfStudents.of(number_of_students))

    @property
    def today_or_future(self) -> bool:
        return self.date_and_time >= DateTime.now().at_begin_of_day()


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Student:
    id: StudentId
    name: StudentName

    @staticmethod
    def of(student_id: str, student_name: str) -> 'Student':
        return Student(StudentId.parse(student_id), StudentName.parse(student_name))


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class StudentThesisState:
    class State(enum.Enum):
        MISSING = 0
        UNSIGNED = 1
        SIGNED = 2

    student: Student
    cdl: CdL
    state: State

    @staticmethod
    def of(student: Student, cdl: CdL, state: State) -> 'StudentThesisState':
        return StudentThesisState(student, cdl, state)


@typeguard.typechecked
@dataclasses.dataclass(frozen=True, order=True)
class Register:
    class State(enum.Enum):
        DRAFT = "Bozza"
        VERIFIED = "Verificato"
        SIGNED = "Stampato"

    course: Course
    hours: NumberOfHours
    semester: Semester
    state: State

    @staticmethod
    def of(course: Course, hours: NumberOfHours, semester: Semester, state: State) -> 'Register':
        return Register(course, hours, semester, state)


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class RegisterActivity:
    date: DateTime
    hours: NumberOfHours
    type: ActivityType
    title: ActivityTitle

    def __post_init__(self):
        validate("end_date_time", self.end_date_time, help_msg="The activity spans multiple days.")

    @staticmethod
    def of(date: DateTime, hours: NumberOfHours, activity_type: ActivityType,
           title: ActivityTitle) -> 'RegisterActivity':
        return RegisterActivity(date, hours, activity_type, title)

    @property
    def end_date_time(self) -> DateTime:
        return self.date.add_hours(self.hours.value)


@bounded_string(min_length=5, max_length=255, pattern=r"[A-Za-z0-9 _-]*")
class GraduationDay:
    pass


@bounded_integer(min_value=66, max_value=121)
class FinalScore:
    pass


@bounded_string(min_length=0, max_length=4000, pattern=r"[A-Za-z0-9ÀÈÉÌÒÙàèéìòù '\":;.,()\[\]\n_-]*")
class GraduationNote:
    @staticmethod
    def empty() -> 'GraduationNote':
        return GraduationNote('')


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class StudentGraduation:
    student: Student
    final_score: FinalScore
    laude: bool = dataclasses.field(default=False)
    special_mention: bool = dataclasses.field(default=False)
    notes: GraduationNote = dataclasses.field(default=GraduationNote.empty())

    def __post_init__(self):
        validate("laude needs 110", not self.laude or self.final_score >= FinalScore(110), equals=True)
        validate("special_mention needs laude", not self.special_mention or self.laude, equals=True)

    @staticmethod
    def of(student_id: str, student_name: str, final_score: int) -> 'StudentGraduation':
        return StudentGraduation(Student.of(student_id, student_name), FinalScore(final_score))

    def with_laude(self) -> 'StudentGraduation':
        return StudentGraduation(
            student=self.student,
            final_score=self.final_score,
            laude=True,
            special_mention=self.special_mention,
            notes=self.notes,
        )

    def with_special_mention(self) -> 'StudentGraduation':
        return StudentGraduation(
            student=self.student,
            final_score=self.final_score,
            laude=self.laude,
            special_mention=True,
            notes=self.notes,
        )

    def with_notes(self, value: GraduationNote) -> 'StudentGraduation':
        return StudentGraduation(
            student=self.student,
            final_score=self.final_score,
            laude=self.laude,
            special_mention=self.special_mention,
            notes=value,
        )
