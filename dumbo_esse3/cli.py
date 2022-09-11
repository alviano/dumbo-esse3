import dataclasses
from typing import Optional, List

import typer
from rich.progress import track
from rich.table import Table

from dumbo_esse3.esse3_wrapper import Esse3Wrapper
from dumbo_esse3.primitives import StudentThesisState, ExamDescription, ExamNotes, ExamType, ExamDateTime
from dumbo_esse3.utils.console import console


@dataclasses.dataclass(frozen=True)
class AppOptions:
    username: str = dataclasses.field(default='')
    password: str = dataclasses.field(default='')
    debug: bool = dataclasses.field(default=False)


app_options = AppOptions()
app = typer.Typer()


def is_debug_on():
    return app_options.debug


def run_app():
    try:
        app()
    except Exception as e:
        if is_debug_on():
            raise e
        else:
            console.print(f"[red bold]Error:[/red bold] {e}")

def new_esse3_wrapper(detached: bool = False, with_live_status: bool = True):
    def res():
        return Esse3Wrapper.create(
            username=app_options.username,
            password=app_options.password,
            debug=app_options.debug,
            detached=detached,
            headless=not app_options.debug and not detached,
        )
    if with_live_status:
        with console.status("Login..."):
            return res()
    return res()


@app.callback()
def main(
        username: str = typer.Option(..., prompt=True, envvar="DUMBO_ESSE3_USERNAME"),
        password: str = typer.Option(..., prompt=True, hide_input=True, envvar="DUMBO_ESSE3_PASSWORD"),
        debug: bool = typer.Option(False, "--debug", help="Don't minimize browser"),
):
    """
    Esse3 command line utility, to save my future time!
    """
    global app_options
    app_options = AppOptions(
        username=username,
        password=password,
        debug=debug,
    )


@app.command(name="courses")
def command_courses() -> None:
    """
    Prints the list of courses.
    The number associated with each course is used an ID.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching courses..."):
        courses_list = esse3_wrapper.fetch_courses()

    table = Table(title="Courses")
    table.add_column("#")
    table.add_column("Course")
    for index, course in enumerate(courses_list, start=1):
        table.add_row(
            str(index),
            course.value,
        )
    console.print(table)


@app.command(name="exams")
def command_exams(
        of: List[int] = typer.Option([], help="Index of the course"),
        all_dates: Optional[bool] = typer.Option(False, "--all", "-a", help="Show all exams, not only the next"),
        with_students: Optional[bool] = typer.Option(False, "--with-students", "-s", help="Also fetch students"),
) -> None:
    """
    Prints exams and registered students.
    Filtering options are available.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching courses..."):
        courses = esse3_wrapper.fetch_courses()
    console.rule("Exams")
    for index, course in enumerate(track(courses, console=console, transient=True), start=1):
        if of and index not in of:
            continue
        console.print(f"{index:2d}. {course}")
        exams = esse3_wrapper.fetch_exams(course)
        if not all_dates:
            next_exam = next(filter(lambda x: x.today_or_future, exams), None)
            exams = [next_exam] if next_exam else []
        for exam in exams:
            console.print(f"  - {exam.date_and_time}, {exam.number_of_students:3d} students")
            if with_students and exam.number_of_students.positive:
                console.print()
                students = esse3_wrapper.fetch_students(course, exam.date_and_time)
                console.print("\n".join(f"{student.id}\t{student.name}" for student in students))
                console.print()


@app.command(name="add-exams")
def command_add_exams(
        exams: List[str] = typer.Argument(
            ...,
            metavar="exam",
            help="One or more strings of the form 'CourseIndex DD/MM HH:MM' "
                 "(separators can be omitted, and spaces can be replaced by dashes; year is inferred)",
        ),
        exam_type: str = typer.Option(..., prompt=True, envvar="DUMBO_ESSE3_EXAM_TYPE"),
        description: str = typer.Option(..., prompt=True, envvar="DUMBO_ESSE3_EXAM_DESCRIPTION"),
        notes: str = typer.Option(..., prompt=True, envvar="DUMBO_ESSE3_EXAM_NOTES"),
):
    """
    Adds exams provided as command-line arguments.
    """
    try:
        exam_type = ExamType(exam_type)
    except ValueError:
        console.print("Invalid type")
        raise typer.Exit()

    try:
        description = ExamDescription(description)
    except ValueError:
        console.print("Invalid description")
        raise typer.Exit()

    try:
        notes = ExamNotes(notes)
    except ValueError:
        console.print("Invalid notes")
        raise typer.Exit()

    def parse(exam):
        exam = exam.replace('-', ' ').split(' ', maxsplit=1)
        course_index = int(exam[0])
        if course_index <= 0:
            console.print(f"Course index must be positive, not {course_index}")
            raise typer.Exit()

        try:
            date = ExamDateTime.smart_parse(exam[1])
        except ValueError:
            console.print(f"Invalid datetime. Use DD/MM HH:MM")
            raise typer.Exit()
        if date < ExamDateTime.now():
            console.print(f"Cannot schedule an exam in the past!")
            raise typer.Exit()

        return course_index, date

    exam_list = [parse(exam) for exam in exams]

    esse3_wrapper = new_esse3_wrapper()
    courses = esse3_wrapper.fetch_courses()
    for exam in exam_list:
        if exam[0] > len(courses):
            console.print(f"Course index cannot be larger than {len(courses)}, it was given {exam[0]}")
            raise typer.Exit()

    for exam in track(exam_list, console=console, transient=True):
        index, date_and_time = exam
        course = courses[index - 1]
        if esse3_wrapper.is_exam_present(course, date_and_time):
            console.log(f"Skip already present exam {date_and_time} for {course} (#{index})")
        else:
            console.log(f"Add exam {date_and_time} to {course} (#{index})")
            esse3_wrapper.add_exam(course, date_and_time, exam_type, description, notes)


@app.command(name="theses")
def command_theses(
        list_option: bool = typer.Option(True, "--list", "--no-list", help="Print the list of theses"),
        show: List[int] = typer.Option([], help="Index of student thesis to show"),
        sign: List[int] = typer.Option([], help="Index of student thesis to sign"),
        show_all: bool = typer.Option(False, "--show-all", help="Show all theses"),
        sign_all: bool = typer.Option(False, "--sign-all", help="Sign all theses"),
):
    """
    Prints the list of theses.
    The number associated with each student is used as an ID.
    Theses can be shown in the browser and signed automatically.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching theses..."):
        student_thesis_states = esse3_wrapper.fetch_thesis_list()

    if list_option:
        table = Table(title="Theses")
        table.add_column("#")
        table.add_column("Student ID")
        table.add_column("Student Name")
        table.add_column("CdL")
        table.add_column("State")

        for index, student_thesis_state in enumerate(student_thesis_states, start=1):
            style = ""
            if student_thesis_state.state == StudentThesisState.State.SIGNED:
                style = "bold green"
            elif student_thesis_state.state == StudentThesisState.State.UNSIGNED:
                style = "bold red"
            table.add_row(
                str(index),
                student_thesis_state.student.id.value,
                student_thesis_state.student.name.value,
                student_thesis_state.cdl.value,
                student_thesis_state.state.name,
                style=style,
            )

        console.print(table)

    must_wait = False
    for index, student_thesis_state in enumerate(
            track(student_thesis_states, console=console, transient=True),
            start=1
    ):
        if show_all or index in show:
            if student_thesis_state.state == StudentThesisState.State.MISSING:
                console.print(f"Skip thesis of {student_thesis_state.student.name} (#{index})")
            else:
                console.print(f"Open thesis of {student_thesis_state.student.name} (#{index})")
                student_wrapper = new_esse3_wrapper(detached=True, with_live_status=False)
                student_wrapper.show_thesis(student_thesis_state.student)
                student_wrapper.maximize()
                must_wait = True
    if must_wait:
        console.input("Press ENTER to continue")

    for index, student_thesis_state in enumerate(
            track(student_thesis_states, console=console, transient=True),
            start=1
    ):
        if sign_all or index in sign:
            if student_thesis_state.state == StudentThesisState.State.UNSIGNED:
                console.log(f"Sign thesis of {student_thesis_state.student.name} (#{index})")
                esse3_wrapper.sign_thesis(student_thesis_state.student)
            else:
                console.log(f"Skip thesis of {student_thesis_state.student.name} (#{index})")
