from pathlib import Path

import pytest
from pytest_localserver.http import WSGIServer

from dumbo_esse3.esse3_wrapper import URLs, change_esse3_server

TRACE = True

LOCAL_SERVER = None


def read_html(filename):
    file = (Path(__file__).parent / "html/filename").with_name(filename)
    if TRACE:
        if not file.exists():
            print("TRACE(read_html)", f"missing file {file}")
        else:
            print("TRACE(read_html)", f"serving file {file}")
    return open(file).read()


MOCK_ESSE3_STATE = {
    "add exam cod completed": False,
    "register ae empty": True,
    "theses signed": False,
}


def mock_esse3_app(environ, start_response):
    status = "200 OK"
    response_headers = [('Content-type', 'text/html')]
    method = environ["REQUEST_METHOD"]
    url = environ["REQUEST_URI"]
    if TRACE and url.startswith("/auth/"):
        print('TRACE(mock_esse3_app)', method, url)
    server = f'{environ["wsgi.url_scheme"]}://{environ["HTTP_HOST"]}'
    start_response(status, response_headers)
    html = None
    if method == "GET":
        if url == URLs["login"].replace(LOCAL_SERVER, ''):
            html = read_html("login.html")
        elif url == URLs["logout"].replace(LOCAL_SERVER, ''):
            html = read_html("logout.html")
        elif url == URLs["course_list"].replace(LOCAL_SERVER, ''):
            html = read_html("course_list.html")
        elif url == URLs["register_list"].replace(LOCAL_SERVER, ''):
            html = read_html("registers.html")
        elif url == "/auth/docente/RegistroDocente/EnterRegistro.do;jsessionid=3D6CE80D6DED107AFC9D39538FB4AAEF.esse3-unical-prod-02?AA_OFF_ID=2022&FAT_PART_COD=N0&DOM_PART_COD=N0&AD_LOG_ID=65422&PART_COD=S1":
            html = read_html("register_cod.html")
        elif url == "/auth/docente/RegistroDocente/EnterRegistro.do;jsessionid=3D6CE80D6DED107AFC9D39538FB4AAEF.esse3-unical-prod-02?AA_OFF_ID=2022&FAT_PART_COD=N0&DOM_PART_COD=N0&AD_LOG_ID=65351&PART_COD=S2":
            if MOCK_ESSE3_STATE["register ae empty"]:
                html = read_html("register_ae_empty.html")
            else:
                html = read_html("register_ae_nonempty.html")
        elif url == "/auth/docente/RegistroDocente/DettRigaReg.do;jsessionid=959E8793B1AEF05E5E4DFDB2445A6A9C.esse3-unical-prod-02?R_DOC_ID=6980&CAN_CHANGE=1&PROPR_FLG=1&TIT_FLG=1&VIS_DETT=0":
            html = read_html("register_ae_add_activity.html")
        elif url == "/auth/docente/RegistroDocente/DelRigaReg.do;jsessionid=959E8793B1AEF05E5E4DFDB2445A6A9C.esse3-unical-prod-02?DETT_REG_ID=116966&R_DOC_ID=6980&VIS_DETT=0":
            html = read_html("register_ae_delete_activity.html")
        elif url == "/auth/docente/Graduation/LaureandiAssegnati.do?menu_opened_cod=menu_link-navbox_docenti_Conseguimento_Titolo":
            html = read_html("theses.html")
        elif url == "/auth/docente/Graduation/AllegatiTesi.do?tesi_id=1234&pers_id=134":
            if MOCK_ESSE3_STATE["theses signed"]:
                html = read_html("theses_signed.html")
            else:
                html = read_html("theses_present.html")
        elif url == "/auth/docente/Graduation/ApprovaAllegatoTesi.do?tesi_id=1234&allegato_id=12344&stu_id=199451&pers_id=159952":
            html = read_html("theses_sign.html")
        elif url == URLs["graduation_day_list"].replace(LOCAL_SERVER, ''):
            html = read_html("graduation_day_list.html")
        elif url == "/auth/docente/Graduation/DettaglioSedutaLaurea.do?sed_ct_prg=1&app_ct_id=6603&sottoseduta=0":
            html = read_html("graduation_day_lm.html")
        elif url == "/auth/docente/Graduation/DettaglioLaureando.do?sed_ct_prg=1&app_ct_id=6111&stu_id=12344&pers_id=12344&mat_id=364442&cds_id=10646&pds_id=5&aa_ord_id=2018&dom_ct_id=126254&tesi_id=121&sottoseduta=0":
            html = read_html("graduation_day_lm_student_1.html")
        elif url == "/auth/docente/Graduation/DettaglioLaureando.do?sed_ct_prg=1&app_ct_id=12334&stu_id=12345&pers_id=12345&mat_id=342935&cds_id=10646&pds_id=1&aa_ord_id=2018&dom_ct_id=126474&tesi_id=132&sottoseduta=0":
            html = read_html("graduation_day_lm_student_1.html")
        elif url == URLs["committee_list"].replace(LOCAL_SERVER, ''):
            html = read_html("committee_list.html")
        elif url == "/auth/Admission/ValutazioneTitListaProve.do?comm_prove_conc_id=123":
            html = read_html("committee_parts.html")
        elif url == "/auth/Admission/ElencoIscrittiTurni.do?prove_conc_id=4028&comm_prove_conc_id=123":
            html = read_html("committee_part.html")
        elif url == "/auth/Admission/ValutazioneClassifica.do?classif_dett_id=321&prove_conc_id=4028&comm_prove_conc_id=123":
            html = read_html("committee_details.html")
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
        elif url == "/auth/docente/CalendarioEsami/ListaStudentiEsame.do;jsessionid=6B451A4C663DDAA5ABC8BE210A61964D.esse3-unical-prod-02?AA_ID=2022&CDS_ID=10711&AD_ID=14522&APP_ID=7&MIN_AA_CAL_ID=0&MAX_AA_CAL_ID=9999&FILTRO_AA_CAL=0&VIS_APP=0&DATA_ESA=21/01/2023":
            html = read_html("exam_cod_details.html")
        elif url == "/auth/docente/RegistroDocente/AggiornaRigaReg.do;jsessionid=959E8793B1AEF05E5E4DFDB2445A6A9C.esse3-unical-prod-02?R_DOC_ID=6980":
            MOCK_ESSE3_STATE["register ae empty"] = False
            html = read_html("register_ae_nonempty.html")
        elif url == "/auth/docente/RegistroDocente/DelRigaReg.do;jsessionid=959E8793B1AEF05E5E4DFDB2445A6A9C.esse3-unical-prod-02":
            MOCK_ESSE3_STATE["register ae empty"] = True
            html = read_html("register_ae_empty.html")
        elif url == "/auth/docente/Graduation/ApprovaAllegatoTesiSubmit.do":
            MOCK_ESSE3_STATE["theses signed"] = True
            html = read_html("theses_signed.html")
    if TRACE and url.startswith("/auth/") and html is None:
        print('TRACE(mock_esse3_app)', f'missing page {url}')
    return [html.replace(
        '<base href="https://unical.esse3.cineca.it/">',
        f'<base href="{server}">',
    ).encode()]


@pytest.fixture
def test_server(request):
    global LOCAL_SERVER

    server = WSGIServer(application=mock_esse3_app)
    server.start()
    request.addfinalizer(server.stop)
    LOCAL_SERVER = server.url
    change_esse3_server(LOCAL_SERVER)
    return server
