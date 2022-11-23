from pathlib import Path

import pytest
from pytest_localserver.http import WSGIServer

from dumbo_esse3.esse3_wrapper import ESSE3_SERVER, LOGIN_URL, LOGOUT_URL, COURSE_LIST_URL, REGISTER_LIST_URL, \
    change_esse3_server


def read_html(filename):
    file = (Path(__file__).parent / "html/filename").with_name(filename)
    return open(file).read()


def endpoint(url):
    return url.replace(ESSE3_SERVER, '', 1)


MOCK_ESSE3_STATE = {
    "add exam cod completed": False,
}


def mock_esse3_app(environ, start_response):
    status = "200 OK"
    response_headers = [('Content-type', 'text/html')]
    method = environ["REQUEST_METHOD"]
    url = environ["REQUEST_URI"]
    # if url.startswith("/auth/"):
    #     print('***', method, url)
    server = f'{environ["wsgi.url_scheme"]}://{environ["HTTP_HOST"]}'
    start_response(status, response_headers)
    html = f'Change with the content of GET {endpoint}'
    if method == "GET":
        if url == endpoint(LOGIN_URL):
            html = read_html("login.html")
        elif url == endpoint(LOGOUT_URL):
            html = read_html("logout.html")
        elif url == endpoint(COURSE_LIST_URL):
            html = read_html("course_list.html")
        elif url == endpoint(REGISTER_LIST_URL):
            html = read_html("registers.html")
        elif url == "/auth/docente/RegistroDocente/EnterRegistro.do;jsessionid=3D6CE80D6DED107AFC9D39538FB4AAEF.esse3-unical-prod-02?AA_OFF_ID=2022&FAT_PART_COD=N0&DOM_PART_COD=N0&AD_LOG_ID=65422&PART_COD=S1":
            html = read_html("register_cod.html")
    elif method == "POST":
        if url == "/auth/docente/CalendarioEsami/ElencoAppelliCalEsa.do;jsessionid=86CA8F3D3A6885013058837D593E0551.esse3-unical-prod-04":
            if MOCK_ESSE3_STATE["add exam cod completed"]:
                html = read_html("exams_cod_2.html")
            else:
                html = read_html("exams_cod.html")
        elif url == "/auth/docente/CalendarioEsami/ElencoAppelliCalEsa.do;jsessionid=8B87CE242AC8D7FDA971FBFB3A004EA5.esse3-unical-prod-02":
            html = read_html("add_exam_cod.html")
        elif url == "/auth/docente/CalendarioEsami/InserisciAggiornaAppelloCalEsaSubmit.do;jsessionid=F2C9EEA7A724D6C5A148AD08E959A4D1.esse3-unical-prod-02":
            MOCK_ESSE3_STATE["add exam cod completed"] = True
            html = read_html("add_exam_cod.html")
    return [html.replace(
        '<base href="https://unical.esse3.cineca.it/">',
        f'<base href="{server}">',
    ).encode()]


@pytest.fixture
def test_server(request):
    server = WSGIServer(application=mock_esse3_app)
    server.start()
    request.addfinalizer(server.stop)
    change_esse3_server(server.url)
    return server
