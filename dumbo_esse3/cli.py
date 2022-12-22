import csv
import dataclasses
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional, List

import typer
from rich.progress import track
from rich.table import Table

from dumbo_esse3.esse3_wrapper import Esse3Wrapper
from dumbo_esse3.primitives import StudentThesisState, ExamDescription, ExamNotes, ExamType, DateTime, Register, \
    RegisterActivity, ActivityType, NumberOfHours, ActivityTitle, StudentGraduation, Student, FinalScore, GraduationNote
from dumbo_esse3.utils.console import console
from dumbo_esse3.utils.validators import validate


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


def version_callback(value: bool):
    if value:
        import importlib.metadata
        __version__ = importlib.metadata.version("dumbo-esse3")
        console.print("dumbo-esse3", __version__)
        raise typer.Exit()


@app.callback()
def main(
        username: str = typer.Option(..., prompt=True, envvar="DUMBO_ESSE3_USERNAME"),
        password: str = typer.Option(..., prompt=True, hide_input=True, envvar="DUMBO_ESSE3_PASSWORD"),
        debug: bool = typer.Option(False, "--debug", help="Don't minimize browser"),
        version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True,
                                     help="Print version and exit"),
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
            date = DateTime.smart_parse(exam[1])
        except ValueError:
            console.print(f"Invalid datetime. Use DD/MM HH:MM")
            raise typer.Exit()
        if date < DateTime.now():
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


@app.command(name="registers")
def command_registers() -> None:
    """
    Prints the list of registers.
    The number associated with each course is used an ID.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching registers..."):
        registers = esse3_wrapper.fetch_registers()

    table = Table(title="Registers")
    table.add_column("#")
    table.add_column("Course")
    table.add_column("Hours")
    table.add_column("Semester")
    table.add_column("State")
    for index, register in enumerate(registers, start=1):
        style = ""
        if register.state == Register.State.VERIFIED:
            style = "bold green"
        table.add_row(
            str(index),
            register.course.value,
            str(register.hours),
            register.semester.value,
            register.state.name if register.state == Register.State.SIGNED else
            f"[bold red]{register.state.name}[/bold red]",
            style=style,
        )
    console.print(table)


@app.command(name="register-activities")
def command_register_activities(
        of: List[int] = typer.Option([], help="Index of the register to fetch (omit to fetch all)"),
        with_time: Optional[bool] = typer.Option(False, help="Also fetch starting time of each activity"),
) -> None:
    """
    Prints register activities.
    Filtering options are available.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching registers..."):
        registers = esse3_wrapper.fetch_registers()

    for index, register in enumerate(track(registers, console=console, transient=True), start=1):
        if of and index not in of:
            continue
        activities = esse3_wrapper.fetch_register_activities(register, with_time)

        table = Table(title=f"{register.course}" + (
            "" if register.state == Register.State.SIGNED else f" - [red]NOT SIGNED[/red]"
        ))
        table.add_column("#")
        table.add_column("Date and time" if with_time else "Date")
        table.add_column("Hours", justify="right")
        table.add_column("Title")
        table.add_column("Type")
        for activity_index, activity in enumerate(activities, start=1):
            table.add_row(
                str(activity_index),
                str(activity.date) if with_time else activity.date.stringify_date(),
                str(activity.hours),
                str(activity.title),
                activity.type.name,
            )
        console.print(table)

        hours = defaultdict(lambda: 0)
        for activity in activities:
            hours[activity.type] += activity.hours.value
        table = Table()
        table.add_column(justify="right")
        table.add_column("Summary")
        table.add_row("State", register.state.name)
        table.add_row("Semester", str(register.semester))
        table.add_row("Hours", str(register.hours))
        table.add_row("Missing hours", str(register.hours.value - sum(activity.hours.value for activity in activities)))
        for activity_type, hours in hours.items():
            table.add_row(activity_type.name, str(hours))
        console.print(table)


@app.command(name="add-register-activity")
def command_add_register_activity(
        of: int = typer.Option(..., help="Index of the register of interest"),
        date: Optional[str] = typer.Option(DateTime.now().stringify_date(),
                                           help="Date of the activity in the format DD/MM/YYYY (today if omitted)"),
        time: str = typer.Option(..., help="Starting time of the activity in the format HH:MM"),
        hours: int = typer.Option(..., help="Number of hours of the activity"),
        title: str = typer.Option(..., help="Title of the activity"),
        activity_type: ActivityType = typer.Option(ActivityType.LECTURE.value, "--type", help="Type of activity"),
) -> None:
    """
    Add one activity to the specified register.
    """
    try:
        date_and_time = DateTime.parse(f"{date} {time}")
    except ValueError:
        console.print("Invalid date or time")
        raise typer.Exit()

    try:
        number_of_hours = NumberOfHours.of(hours)
    except ValueError:
        console.print("Invalid number of hours")
        raise typer.Exit()

    try:
        activity_title = ActivityTitle.parse(title)
    except ValueError:
        console.print("Invalid activity title")
        raise typer.Exit()

    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching registers..."):
        registers = esse3_wrapper.fetch_registers()

    if of <= 0 or of > len(registers):
        console.print(f"Invalid register index. Must be between 1 and {len(registers)}")
        raise typer.Exit()

    register = registers[of - 1]
    activity = RegisterActivity.of(
        date=date_and_time,
        hours=number_of_hours,
        activity_type=activity_type,
        title=activity_title,
    )
    with console.status(f"Adding activity to {register.course}..."):
        added = esse3_wrapper.add_register_activity(register, activity)
        if added:
            console.log(f"Added activity to {register.course}")
        else:
            console.log(f"Cannot add activity to {register.course}. Check date and time, and try again!",
                        style="bold red")


@app.command(name="delete-register-activity")
def command_delete_register_activity(
        of: int = typer.Option(..., help="Index of the register of interest"),
        index: int = typer.Argument(..., help="Index of the activity to delete"),
) -> None:
    """
    Delete one activity of the specified register.
    """
    if index <= 0:
        console.print("Invalid index. Must be greater than 1")
        raise typer.Exit()

    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching registers..."):
        registers = esse3_wrapper.fetch_registers()

    if of <= 0 or of > len(registers):
        console.print(f"Invalid register index. Must be between 1 and {len(registers)}")
        raise typer.Exit()

    register = registers[of - 1]
    with console.status(f"Deleting activity #{index} of register {register.course}..."):
        deleted = esse3_wrapper.delete_register_activity(register, index)
        if deleted:
            console.log(f"Deleted activity #{index} of register {register.course}")
        else:
            console.log(f"Cannot delete activity #{index} of register {register.course}. Check the index, and try again!",
                        style="bold red")


@app.command(name="graduation-days")
def command_graduation_days() -> None:
    """
    Print the list of graduation days.
    The number associated with each graduation day is used an ID.
    """
    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching graduation days..."):
        days = esse3_wrapper.fetch_graduation_days()

    table = Table(title="Graduation days")
    table.add_column("#")
    table.add_column("Graduation day")
    for index, day in enumerate(days, start=1):
        table.add_row(
            str(index),
            day.value,
        )
    console.print(table)


def read_graduation_day_list(csv_file: Path) -> List[StudentGraduation]:
    validate("csv-file", csv_file.exists(), help_msg="The provided file doesn't exist")
    with open(csv_file) as f:
        reader = csv.reader(f)
        rows = [row for row in reader]
        student_id_index = rows[0].index("MATRICOLA")
        student_name_index = rows[0].index("STUDENTE")
        final_score_index = rows[0].index("VOTO FINALE")
        laude_index = rows[0].index("LODE")
        special_mention_index = rows[0].index("MENZIONE")
        notes_index = rows[0].index("NOTE")
        return [
            StudentGraduation(
                student=Student.of(row[student_id_index], row[student_name_index]),
                final_score=FinalScore.parse(row[final_score_index]),
                laude=bool(row[laude_index]),
                special_mention=bool(row[special_mention_index]),
                notes=GraduationNote(row[notes_index]),
            )
            for row in rows[1:]
        ]

@app.command(name="upload-graduation-day")
def command_upload_graduation_day(
        of: int = typer.Option(..., help="Index of the graduation day to upload"),
        csv_file: Path = typer.Option(..., help="Path to the CSV file containing the scores to upload"),
        date: Optional[str] = typer.Option(
            None,
            help="Date of the graduation day DD/MM/YYYY (today or from ESSE3 if omitted)"
        ),
        no_committee: bool = typer.Option(False, "--no-committee", help="Don't change selected committee"),
) -> None:
    """
    Upload scores for a graduation day.
    The ID of the graduation day can be obtained with the command graduation-days.
    Scores are provided via a CSV file.
    """
    student_graduation_list = read_graduation_day_list(csv_file)

    esse3_wrapper = new_esse3_wrapper()
    with console.status("Fetching graduation days..."):
        days = esse3_wrapper.fetch_graduation_days()
    validate("", of, min_value=1, max_value=len(days))

    with console.status("Fetching graduation days..."):
        esse3_wrapper.upload_graduation_day(
            graduation_day=days[of - 1],
            student_graduation_list=student_graduation_list,
            date=None if date is None else DateTime.parse_date(date),
            no_committee=no_committee,
        )
    console.print("All done!")
