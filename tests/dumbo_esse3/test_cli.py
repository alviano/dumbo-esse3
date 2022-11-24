import pytest
from typer.testing import CliRunner

from dumbo_esse3.cli import app
from tests.dumbo_esse3.utils.mocks import test_server  # noqa: F401; pylint: disable=unused-variable


@pytest.fixture
def runner(test_server):
    return CliRunner()


def test_courses(runner):
    result = runner.invoke(app, ["courses"])
    assert result.exit_code == 0
    assert "Courses" in result.stdout
    assert "CYBER OFFENSE AND DEFENSE [27008777]" in result.stdout
    assert "SECURE SOFTWARE DESIGN [27006179]" in result.stdout


def test_exams(runner):
    result = runner.invoke(app, ["exams"])
    assert result.exit_code == 0
    assert "Exams" in result.stdout
    assert "1. CYBER OFFENSE AND DEFENSE [27008777]" in result.stdout
    assert "- 31/01/2023 09:00" in result.stdout


def test_theses(runner):
    result = runner.invoke(app, ["theses"])
    assert result.exit_code == 0
    assert "Theses" in result.stdout
    assert "ROSSI MARIO" in result.stdout
