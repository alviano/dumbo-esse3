import dataclasses
from dataclasses import InitVar
from typing import List

import typeguard
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from dumbo_esse3.utils import validators
from dumbo_esse3.primitives import Course, Username, Password, Exam, Student, StudentThesisState, CdL, ExamDescription, \
    ExamNotes, ExamType, ExamDateTime

LOGIN_URL = 'https://unical.esse3.cineca.it/auth/Logon.do?menu_opened_cod='
LOGOUT_URL = 'https://unical.esse3.cineca.it/Logout.do?menu_opened_cod='
COURSE_LIST_URL = 'https://unical.esse3.cineca.it/auth/docente/CalendarioEsami/ListaAttivitaCalEsa.do?menu_opened_cod=menu_link-navbox_docenti_Didattica'
THESIS_LIST_URL = 'https://unical.esse3.cineca.it/auth/docente/Graduation/LaureandiAssegnati.do?menu_opened_cod=menu_link-navbox_docenti_Conseguimento_Titolo'


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Esse3Wrapper:
    key: InitVar[object]
    username: InitVar[Username]
    password: InitVar[Password]
    debug: bool = dataclasses.field(default=False)
    driver: webdriver.Chrome = dataclasses.field(default_factory=webdriver.Chrome)
    __key = object()

    def __post_init__(self, key: object, username: Username, password: Password):
        validators.validate_dataclass(self)
        validators.validate('key', key, equals=self.__key, help_msg="Can only be instantiated using a factory method")
        self.maximize()
        self.__login(username, password)

    def __del__(self):
        if not self.debug:
            try:
                self.__logout()
                self.driver.close()
            except WebDriverException:
                pass
            except ValueError:
                pass

    @classmethod
    def create(cls, username: str, password: str, debug: bool = False, detached: bool = False,
               headless: bool = True) -> 'Esse3Wrapper':
        options = webdriver.ChromeOptions()
        options.headless = headless
        if debug or detached:
            options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=options)

        return Esse3Wrapper(
            key=cls.__key,
            username=Username.parse(username),
            password=Password.parse(password),
            debug=debug,
            driver=driver,
        )

    @property
    def is_headless(self) -> bool:
        return self.driver.execute_script("return navigator.webdriver")

    def __login(self, username: Username, password: Password) -> None:
        self.driver.get(LOGIN_URL)
        self.driver.find_element(By.ID, 'u').send_keys(username.value)
        self.driver.find_element(By.ID, 'p').send_keys(password.value)
        self.driver.find_element(By.ID, 'btnLogin').send_keys(Keys.RETURN)

    def __logout(self) -> None:
        self.driver.get(LOGOUT_URL)

    def minimize(self) -> None:
        self.driver.minimize_window()

    def maximize(self) -> None:
        self.driver.maximize_window()

    def fetch_courses(self) -> List[Course]:
        self.driver.get(COURSE_LIST_URL)
        rows = self.driver.find_elements(By.XPATH, "//tr[@class='detail_table'][td//input[@src = 'images/sostenuta.gif']]")
        res = []
        for idx, row in enumerate(rows):
            td = row.find_element(By.XPATH, "td[1]")
            res.append(Course.of(td.text))
        return res

    def fetch_exams(self, course: Course) -> List[Exam]:
        self.driver.get(COURSE_LIST_URL)
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)
        exams = self.driver.find_elements(By.XPATH, '//tr[@class="detail_table"]')
        return list(sorted([Exam.of(
            ExamDateTime.parse(exam.find_element(By.XPATH, "td[3]").text),
            int(exam.find_element(By.XPATH, "td[5]").text or 0),
        ) for exam in exams], key=lambda exam: exam.date_and_time))

    def fetch_students(self, course: Course, exam: ExamDateTime) -> List[Student]:
        self.driver.get(COURSE_LIST_URL)
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)

        self.driver.find_element(By.XPATH, f"//tr[normalize-space(td/text()) = '{exam}']//input[@src='images/defAppStudent.gif']").send_keys(Keys.RETURN)

        rows = self.driver.find_elements(By.XPATH, f"//table[@class='detail_table']//tr[position() > 1][td[1] >= 1]")
        return [
            Student.of(
                row.find_element(By.XPATH, 'td[3]').text,
                row.find_element(By.XPATH, 'td[4]').text,
            ) for row in rows
        ]

    def is_exam_present(self, course: Course, date_and_time: ExamDateTime) -> bool:
        exams = self.fetch_exams(course)
        return any(exam for exam in exams if exam.date_and_time == date_and_time)

    def add_exam(self, course: Course, exam: ExamDateTime, exam_type: ExamType, description: ExamDescription,
                 notes: ExamNotes) -> None:
        self.driver.get(COURSE_LIST_URL)
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)

        self.driver.find_element(By.XPATH, '//input[@type = "submit"][@name = "new_pf"]').send_keys(Keys.RETURN)

        self.driver.find_element(By.ID, 'data_inizio_app').send_keys(exam.stringify_date() + Keys.ESCAPE)
        self.driver.find_element(By.NAME, 'hh_esa').send_keys(exam.stringify_hour())
        self.driver.find_element(By.NAME, 'mm_esa').send_keys(exam.stringify_minute())

        self.driver.find_element(By.XPATH, f'//input[@type = "radio"][@value = "{exam_type.value}"]').send_keys(Keys.RETURN)

        self.driver.find_element(By.XPATH, '//tr[starts-with(th, "*Descrizione:")]//input').send_keys(description.value)
        self.driver.find_element(By.XPATH, '//tr[starts-with(th, "Note:")]//textarea').send_keys(notes.value)

        self.driver.find_element(By.NAME, 'sbmDef').send_keys(Keys.RETURN)
        self.driver.find_element(By.XPATH, '//a[. = "Esci"]').send_keys(Keys.RETURN)

    def fetch_thesis_list(self) -> List[StudentThesisState]:
        self.driver.get(THESIS_LIST_URL)

        all_students = []

        tables = self.driver.find_elements(By.XPATH, f"//div[@id='containerPrincipale']/table")
        for table in tables:
            cdl = table.find_element(By.XPATH, f"caption").text
            students = table.find_elements(By.XPATH, f"tbody/tr")
            for student in students:
                all_students.append((
                    Student.of(
                        student.find_element(By.XPATH, f"td[1]").text,
                        student.find_element(By.XPATH, f"td[2]").text,
                    ),
                    CdL.parse(cdl),
                    student.find_element(By.XPATH, f"td[5]//a").get_attribute("href")
                    if student.find_elements(By.XPATH, f"td[5]//a") else None,
                ))

        res = []
        for student in all_students:
            state = StudentThesisState.State.MISSING
            if student[2]:
                self.driver.get(student[2])
                if self.driver.find_elements(By.ID, f"btnApprova"):
                    state = StudentThesisState.State.UNSIGNED
                else:
                    state = StudentThesisState.State.SIGNED
                self.driver.back()
            res.append(StudentThesisState.of(student[0], student[1], state))
        return res

    def __thesis_action(self, student: Student, action) -> None:
        self.driver.get(THESIS_LIST_URL)
        self.driver.find_element(By.XPATH, f"//tr[td/text() = '{student.id}'][td/text() = '{student.name}']//a").send_keys(Keys.RETURN)
        self.driver.find_element(By.ID, action).send_keys(Keys.RETURN)

    def show_thesis(self, student: Student) -> None:
        self.__thesis_action(student, "btnDownload")

    def sign_thesis(self, student: Student) -> None:
        self.__thesis_action(student, "btnApprova")
        self.driver.find_element(By.ID, "selApprova1").send_keys(Keys.RETURN)
        self.driver.find_element(By.ID, "btnApprova").send_keys(Keys.RETURN)
