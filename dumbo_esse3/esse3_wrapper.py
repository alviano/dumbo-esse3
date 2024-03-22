import dataclasses
from dataclasses import InitVar
from typing import List, Final, Optional

from dumbo_utils.primitives import PrivateKey
from lxml import html

import typeguard
from selenium import webdriver
from selenium.common import WebDriverException, NoSuchElementException, ElementNotSelectableException, \
    ElementNotVisibleException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from dumbo_esse3.primitives import Course, Username, Password, Exam, Student, StudentThesisState, CdL, \
    ExamDescription, ExamNotes, ExamType, DateTime, Register, NumberOfHours, Semester, RegisterActivity, \
    ActivityTitle, ActivityType, GraduationDay, StudentGraduation, Committee, CommitteeValuation, CommitteeName, \
    CommitteePart, FiscalCode
from dumbo_utils.validation import validate

ESSE3_SERVER = "https://unical.esse3.cineca.it"
URLs: Final = {
    "login": f'{ESSE3_SERVER}/auth/Logon.do?menu_opened_cod=',
    "logout": f'{ESSE3_SERVER}/Logout.do?menu_opened_cod=',
    "course_list": f'{ESSE3_SERVER}/auth/docente/CalendarioEsami/ListaAttivitaCalEsa.do?menu_opened_cod=menu_link-navbox_docenti_Didattica',
    "thesis_list": f'{ESSE3_SERVER}/auth/docente/Graduation/LaureandiAssegnati.do?menu_opened_cod=menu_link-navbox_docenti_Conseguimento_Titolo',
    "register_list": f'{ESSE3_SERVER}/auth/docente/RegistroDocente/Home.do?menu_opened_cod=menu_link-navbox_docenti_Registro',
    "graduation_day_list": f'{ESSE3_SERVER}/auth/docente/Graduation/ElencoSeduteLaurea.do',
    "committee_list": f'{ESSE3_SERVER}/auth/Admission/ElencoCommissioni.do?menu_opened_cod=menu_link-navbox_docenti_Commissioni',
}


def change_esse3_server(url):
    global ESSE3_SERVER, URLs

    for key in URLs.keys():
        URLs[key] = URLs[key].replace(ESSE3_SERVER, url, 1)

    ESSE3_SERVER = url


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Esse3Wrapper:
    key: InitVar[PrivateKey]
    username: InitVar[Username]
    password: InitVar[Password]
    debug: bool = dataclasses.field(default=False)
    driver: webdriver.Chrome = dataclasses.field(default_factory=webdriver.Chrome)
    __key = PrivateKey()

    def __post_init__(self, key: PrivateKey, username: Username, password: Password):
        self.__key.validate(key)
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
        if headless:
            options.add_argument("--headless=new")
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
        self.driver.get(URLs["login"])
        self.driver.find_element(By.ID, 'u').send_keys(username.value)
        self.driver.find_element(By.ID, 'p').send_keys(password.value)
        self.driver.find_element(By.ID, 'btnLogin').send_keys(Keys.RETURN)

    def __logout(self) -> None:
        self.driver.get(URLs["logout"])

    def minimize(self) -> None:
        self.driver.minimize_window()

    def maximize(self) -> None:
        self.driver.maximize_window()

    def __check_expiring_token(self):
        if self.driver.find_elements(By.XPATH, "//strong[text() = 'Certificati in scadenza']"):
            self.driver.find_element(By.XPATH, "//a[text() = 'Prosegui']").send_keys(Keys.RETURN)

    def fetch_courses(self) -> List[Course]:
        self.driver.get(URLs["course_list"])
        self.__check_expiring_token()
        rows = self.driver.find_elements(By.XPATH, "//tr[@class='detail_table'][td//input[@src = 'images/sostenuta.gif']]")
        res = []
        for idx, row in enumerate(rows):
            td = row.find_element(By.XPATH, "td[1]")
            res.append(Course.of(td.text))
        return res

    def fetch_exams(self, course: Course) -> List[Exam]:
        self.driver.get(URLs["course_list"])
        self.__check_expiring_token()
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)
        exams = self.driver.find_elements(By.XPATH, '//tr[@class="detail_table"]')
        return list(sorted([Exam.of(
            DateTime.parse(exam.find_element(By.XPATH, "td[3]").text),
            int(exam.find_element(By.XPATH, "td[5]").text or 0),
        ) for exam in exams], key=lambda exam: exam.date_and_time))

    def fetch_students(self, course: Course, exam: DateTime) -> List[Student]:
        self.driver.get(URLs["course_list"])
        self.__check_expiring_token()
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)

        self.driver.find_element(By.XPATH, f"//tr[normalize-space(td/text()) = '{exam}']//input[@src='images/defAppStudent.gif']").send_keys(Keys.RETURN)

        rows = self.driver.find_elements(By.XPATH, f"//table[@class='detail_table']//tr[position() > 1][td[1] >= 1]")
        return [
            Student.of(
                row.find_element(By.XPATH, 'td[3]').text,
                row.find_element(By.XPATH, 'td[4]').text,
            ) for row in rows
        ]

    def is_exam_present(self, course: Course, date_and_time: DateTime) -> bool:
        exams = self.fetch_exams(course)
        return any(exam for exam in exams if exam.date_and_time == date_and_time)

    def add_exam(self, course: Course, exam: DateTime, exam_type: ExamType, description: ExamDescription,
                 notes: ExamNotes) -> None:
        self.driver.get(URLs["course_list"])
        self.__check_expiring_token()
        self.driver.find_element(By.XPATH, f"//tr[td = '{course}']/td//input[@src = 'images/sostenuta.gif']").send_keys(Keys.RETURN)

        self.driver.find_element(By.XPATH, '//input[@type = "submit"][@name = "new_pf"]').send_keys(Keys.RETURN)

        self.driver.find_element(By.ID, 'data_inizio_app').send_keys(exam.stringify_date() + Keys.ESCAPE)
        self.driver.find_element(By.NAME, 'hh_esa').send_keys(exam.stringify_hour())
        self.driver.find_element(By.NAME, 'mm_esa').send_keys(exam.stringify_minute())

        self.driver.find_element(By.XPATH, f'//input[@type = "radio"][@value = "{exam_type.value}"]').send_keys(Keys.SPACE)

        self.driver.find_element(By.XPATH, '//tr[starts-with(th, "*Descrizione:")]//input').send_keys(description.value)
        self.driver.find_element(By.XPATH, '//tr[starts-with(th, "Note:")]//textarea').send_keys(notes.value)

        self.driver.find_element(By.NAME, 'sbmDef').send_keys(Keys.RETURN)
        self.driver.find_element(By.XPATH, '//a[. = "Esci"]').send_keys(Keys.RETURN)

    def fetch_thesis_list(self) -> List[StudentThesisState]:
        self.driver.get(URLs["thesis_list"])

        all_students = []

        tables = self.driver.find_elements(By.XPATH, "//div[@id='containerPrincipale']/table")
        for table in tables:
            ignore_list = [ElementNotVisibleException, ElementNotSelectableException]
            wait = WebDriverWait(table, timeout=3, poll_frequency=1, ignored_exceptions=ignore_list)
            wait.until(expected_conditions.presence_of_element_located((By.XPATH, "tbody/tr")))

            cdl = table.find_element(By.XPATH, f"caption").text
            students = table.find_elements(By.XPATH, f"tbody/tr")
            for student in students:
                all_students.append((
                    Student.of(
                        student.find_element(By.XPATH, f"td[1]").text,
                        student.find_element(By.XPATH, f"td[2]").text,
                    ),
                    CdL.parse(cdl),
                    student.find_element(By.XPATH, f"td[5]//a[@id = 'btnAllegatiTesi']").get_attribute("href")
                    if student.find_elements(By.XPATH, f"td[5]//a[@id = 'btnAllegatiTesi']") else None,
                ))

        res = []
        for student in all_students:
            state = StudentThesisState.State.MISSING
            if student[2]:
                state = StudentThesisState.State.UNSIGNED
                self.driver.get(student[2])
                if self.driver.find_elements(By.XPATH, f"//td[text() = 'Approvato']"):
                    state = StudentThesisState.State.SIGNED
                self.driver.back()
            res.append(StudentThesisState.of(student[0], student[1], state))
        return res

    def __thesis_action(self, student: Student, action) -> None:
        self.driver.get(URLs["thesis_list"])

        selector = f"//tr[td/text() = '{student.id}'][td/text() = '{student.name}']//a[@id = 'btnAllegatiTesi']"

        ignore_list = [ElementNotVisibleException, ElementNotSelectableException]
        wait = WebDriverWait(self.driver, timeout=3, poll_frequency=1, ignored_exceptions=ignore_list)
        wait.until(expected_conditions.presence_of_element_located((By.XPATH, selector)))

        self.driver.find_element(By.XPATH, selector).send_keys(Keys.RETURN)
        self.driver.find_element(By.ID, action).send_keys(Keys.RETURN)

    def show_thesis(self, student: Student) -> None:
        self.__thesis_action(student, "btnDownload")

    def sign_thesis(self, student: Student) -> None:
        self.__thesis_action(student, "btnApprova")
        self.driver.find_element(By.ID, "selApprova1").send_keys(Keys.SPACE)
        self.driver.find_element(By.ID, "btnApprova").send_keys(Keys.RETURN)

    def fetch_registers(self) -> List[Register]:
        self.driver.get(URLs["register_list"])
        rows = self.driver.find_elements(By.XPATH, "//tr[td/a/img[@src = 'images/open_registro.gif']]")
        res = []
        for idx, row in enumerate(rows):
            course = Course.parse(row.find_element(By.XPATH, "td[2]").text)
            hours = NumberOfHours.parse(row.find_element(By.XPATH, "td[4]").text)
            semester = Semester.parse(row.find_element(By.XPATH, "td[5]").text)
            state = Register.State(row.find_element(By.XPATH, "td[6]/img").get_attribute('alt'))
            res.append(Register.of(course=course, hours=hours, semester=semester, state=state))
        return sorted(res, key=lambda register: (register.semester, register.course))

    def fetch_register_activities(self, register: Register, with_time: bool = False) -> List[RegisterActivity]:
        self.driver.get(URLs["register_list"])
        self.driver.find_element(
            By.XPATH,
            f"//tr[normalize-space(td/text()) = '{register.course}']/td//a[img/@src = 'images/open_registro.gif']"
        ).send_keys(Keys.RETURN)

        rows_xpath = "//tr[td/form/input/@src = 'images/open_registro.gif']"
        rows = self.driver.find_elements(By.XPATH, rows_xpath)
        number_of_rows = len(rows)
        res = []
        for index in range(number_of_rows):
            row = rows[index]
            date = DateTime.parse_date(row.find_element(By.XPATH, "td[2]").text)
            hours = NumberOfHours.parse(row.find_element(By.XPATH, "td[3]").text)
            title = ActivityTitle.parse(row.find_element(By.XPATH, "td[4]").text)
            activity_type = ActivityType(row.find_element(By.XPATH, "td[5]").text)

            if with_time:
                row.find_element(By.XPATH, "td/form/input[@src = 'images/open_registro.gif']").send_keys(Keys.RETURN)
                h = self.driver.find_element(By.ID, "hh_inizio").find_element(By.XPATH, "option[@selected]").text
                m = self.driver.find_element(By.ID, "mm_inizio").find_element(By.XPATH, "option[@selected]").text
                date = date.at_time(hour=int(h), minute=int(m))
                self.driver.find_element(By.XPATH, "//a[. = 'Esci']").send_keys(Keys.RETURN)
                rows = self.driver.find_elements(By.XPATH, rows_xpath)

            res.append(RegisterActivity.of(date=date, hours=hours, activity_type=activity_type, title=title))

        return res

    def add_register_activity(self, register: Register, activity: RegisterActivity) -> bool:
        self.driver.get(URLs["register_list"])
        self.driver.find_element(
            By.XPATH,
            f"//tr[normalize-space(td/text()) = '{register.course}']/td//a[img/@src = 'images/open_registro.gif']"
        ).send_keys(Keys.RETURN)
        self.driver.find_element(
            By.XPATH,
            f"//a[normalize-space(text()) = 'Inserisci nuova attività']"
        ).send_keys(Keys.RETURN)

        self.driver.find_element(
            By.XPATH,
            "//tr[normalize-space(th/text()) = '*Data:']/td/input"
        ).send_keys(activity.date.stringify_date() + Keys.ESCAPE)
        self.driver.find_element(By.ID, "hh_inizio").send_keys(activity.date.stringify_hour())
        self.driver.find_element(By.ID, "mm_inizio").send_keys(activity.date.stringify_minute())
        self.driver.find_element(By.ID, "hh_fine").send_keys(activity.end_date_time.stringify_hour())
        self.driver.find_element(By.ID, "mm_fine").send_keys(activity.end_date_time.stringify_minute())
        self.driver.find_element(By.ID, "ore_accademiche").send_keys(str(activity.hours))
        self.driver.find_element(
            By.XPATH,
            "//tr[normalize-space(th/text()) = 'Tipo attività:']/td/select"
        ).send_keys(activity.type.value)
        self.driver.find_element(
            By.XPATH,
            "//tr[normalize-space(th/text()) = '*Titolo:']/td/input"
        ).send_keys(str(activity.title))
        self.driver.find_element(
            By.XPATH,
            "//input[@value = 'Salva']"
        ).send_keys(Keys.RETURN)

        return len(self.driver.find_elements(
            By.XPATH,
            "//tr[starts-with(normalize-space(td/text()), 'ATTENZIONE')]"
        )) == 0

    def delete_register_activity(self, register: Register, activity_index: int) -> bool:
        self.driver.get(URLs["register_list"])
        self.driver.find_element(
            By.XPATH,
            f"//tr[normalize-space(td/text()) = '{register.course}']/td//a[img/@src = 'images/open_registro.gif']"
        ).send_keys(Keys.RETURN)
        try:
            self.driver.find_element(
                By.XPATH,
                f"//tr[td/form/input/@src = 'images/open_registro.gif'][{activity_index}]/td/a[img/@src = 'images/del.gif']"
            ).send_keys(Keys.RETURN)
        except NoSuchElementException:
            return False
        self.driver.find_element(By.XPATH, "//input[@value = 'Conferma']").send_keys(Keys.RETURN)
        return True

    def fetch_graduation_days(self) -> List[GraduationDay]:
        self.driver.get(URLs["graduation_day_list"])
        rows = self.driver.find_elements(By.XPATH, "//table[@id = 'seduteAperte']/tbody/tr/td[1]")
        return [GraduationDay(row.text) for row in rows]

    def upload_graduation_day(
            self,
            graduation_day: GraduationDay,
            student_graduation_list: List[StudentGraduation],
            date: Optional[DateTime] = None,
            exclude_from_committee: Optional[List[int]] = None,
            dry_run: bool = False,
    ) -> None:
        validate("at least one student", student_graduation_list, min_len=1, help_msg="No student was provided")
        self.driver.get(URLs["graduation_day_list"])
        self.driver.find_element(
            By.XPATH,
            f"//table[@id = 'seduteAperte']/tbody/tr/td[text() = '{graduation_day}']/../td/a"
        ).send_keys(Keys.RETURN)

        html_document = html.fromstring(self.driver.page_source)
        rows = html_document.xpath('//table[@id="elencoLaureandi"]/tbody/tr')
        student_to_url = {
            Student.of(
                student_id=row.xpath("td[2]")[0].text,
                student_name=row.xpath("td[1]")[0].text,
            ): ESSE3_SERVER + '/' + row.xpath("td/a/@href")[0]
            for row in rows
        }
        student_to_graduation = {graduation.student: graduation for graduation in student_graduation_list}
        validate("student_graduation_list", student_to_graduation.keys(), equals=student_to_url.keys(),
                 help_msg="Students don't match")

        self.driver.get(student_to_url[student_graduation_list[0].student])
        graduation_date = self.driver.find_element(By.ID, 'grad-dettLau-dataCt').text
        if not graduation_date:
            graduation_date = DateTime.now().stringify_date() if date is None else date.stringify_date()
        committee = [
            checkbox.is_selected()
            for checkbox in self.driver.find_elements(
                By.XPATH,
                '//table[starts-with(@id, "gradDettLauCommissione")]//input[@type = "checkbox"]'
            )
        ]
        if all(not x for x in committee):
            committee = [not x for x in committee]
        if exclude_from_committee:
            committee = [x and index not in exclude_from_committee for index, x in enumerate(committee, start=1)]

        for graduation in student_graduation_list:
            url = student_to_url[graduation.student]
            self.driver.get(url)

            starting_score = int(self.driver.find_element(
                By.XPATH,
                '//*[@id="grad-dettLau-boxVerbalizzazione"]/dl/dt[text() = "Voto di partenza"]/../dd'
            ).text)
            thesis_score = graduation.final_score.value - starting_score
            validate("thesis_score", thesis_score, min_value=1, max_value=15, help_msg="Wrong thesis score")

            self.__replace_content(
                self.driver.find_element(By.ID, 'grad-dettLau-annotazioni'),
                graduation.notes.value
            )
            self.driver.execute_script("arguments[0].setAttribute('onchange', () => {})", self.driver.find_element(By.ID, 'grad-dettLau-puntiTesi'))
            self.__replace_content(
                self.driver.find_element(By.ID, 'grad-dettLau-puntiTesi'),
                str(thesis_score)
            )
            self.__replace_content(
                self.driver.find_element(By.ID, 'grad-dettLau-dataCt'),
                graduation_date
            )
            if graduation.special_mention != self.driver.find_element(By.ID, 'grad-dettLau-menzione1').is_selected():
                self.driver.find_element(By.ID, 'grad-dettLau-menzione1').send_keys(Keys.SPACE)

            if committee:
                checkboxes = self.driver.find_elements(
                    By.XPATH,
                    '//table[starts-with(@id, "gradDettLauCommissione")]//input[@type = "checkbox"]'
                )
                for index, member in enumerate(committee):
                    if member != checkboxes[index].is_selected():
                        checkboxes[index].send_keys(Keys.SPACE)

            if not dry_run:
                self.driver.find_element(By.ID, 'grad-dettLau-btnSubmit').send_keys(Keys.RETURN)

            if graduation.laude != self.driver.find_element(By.ID, 'grad-dettLau-lode1').is_selected():
                self.driver.get(url)
                self.driver.find_element(By.ID, 'grad-dettLau-lode1').send_keys(Keys.SPACE)
                if not dry_run:
                    self.driver.find_element(By.ID, 'grad-dettLau-btnSubmit').send_keys(Keys.RETURN)

    def fetch_committees(self) -> List[Committee]:
        self.driver.get(URLs["committee_list"])
        rows = self.driver.find_elements(By.XPATH, "//table[@id = 'tableElencoCommissioni']/tbody/tr")
        committee = [(
            element.find_element(By.XPATH, "td[1]").text,
            element.find_element(By.XPATH, "td[3]/a").get_attribute("href"),
        ) for element in rows]
        res: Final = []
        for name, link in committee:
            committee_name = CommitteeName(name)
            self.driver.get(link)
            rows = self.driver.find_elements(By.XPATH, "//table[@id = 'tableElencoConcTurni']/tbody/tr/td[2]")
            res.extend(Committee(committee_name, CommitteePart(row.text)) for row in rows)
        return res

    def upload_committee_valuations(
            self,
            committee: Committee,
            valuations: List[CommitteeValuation],
            dry_run: bool = False,
    ) -> None:
        validate("at least one valuation", valuations, min_len=1, help_msg="No valuation was provided")

        self.driver.get(URLs["committee_list"])
        self.driver.find_element(
            By.XPATH,
            f"//table[@id = 'tableElencoCommissioni']/tbody/tr[td[1] = '{committee.name}']/td[3]/a"
        ).send_keys(Keys.RETURN)
        self.driver.find_element(
            By.XPATH,
            f"//table[@id = 'tableElencoConcTurni']/tbody/tr[td[2] = '{committee.part}']/td[4]/a"
        ).send_keys(Keys.RETURN)

        try:
            ignore_list = [ElementNotVisibleException, ElementNotSelectableException]
            wait = WebDriverWait(self.driver, timeout=3, poll_frequency=1, ignored_exceptions=ignore_list)
            wait.until(expected_conditions.presence_of_element_located(
                (By.XPATH, "//table[@id='tableElencoIscritti']/tfoot/tr"))
            )

            self.driver.execute_script("""
                Object.keys(localStorage).forEach(key => {
                    if (key.endsWith(":paging")) {
                        localStorage.setItem(key, '{"current": 1,"size": 999999}');
                    }
                });
                console.log(Object.keys(localStorage));
                console.log(Object.values(localStorage));
            """)
            self.driver.refresh()
        except TimeoutException:
            pass

        fiscal_code_to_valuation = {valuation.fiscal_code: valuation for valuation in valuations}

        html_document = html.fromstring(self.driver.page_source)
        fiscal_code_to_url = {
            FiscalCode(row.xpath("td[3]")[0].text): ESSE3_SERVER + '/' + row.xpath("td[5]/a/@href")[0]
            for row in html_document.xpath('//table[@id="tableElencoIscritti"]/tbody/tr')
        }

        validate("valuations", fiscal_code_to_valuation.keys(), equals=fiscal_code_to_url.keys(),
                 help_msg="Candidates don't match")

        self.driver.get(fiscal_code_to_url[valuations[0].fiscal_code])
        for valuation in valuations:
            url = fiscal_code_to_url[valuation.fiscal_code]
            self.driver.get(url)

            self.__replace_content(
                self.driver.find_element(By.ID, 'esito'),
                str(valuation.score)
            )
            self.driver.find_element(By.ID, 'valutazioneCompletata1').send_keys(Keys.SPACE)
            self.__replace_content(
                self.driver.find_element(By.XPATH, '//div[@id = "nota-div"]//textarea'),
                str(valuation.notes)
            )
            self.__replace_content(
                self.driver.find_element(By.ID, 'numBusta'),
                str(valuation.envelope_number) if valuation.envelope_number is not None else ""
            )

            if not dry_run:
                self.driver.find_element(By.ID, 'btnSubmit').send_keys(Keys.RETURN)

    @staticmethod
    def __replace_content(element, content):
        element.clear()
        element.send_keys(content + Keys.ESCAPE)
