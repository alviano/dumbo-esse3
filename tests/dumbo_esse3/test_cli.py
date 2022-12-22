from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
from typer.testing import CliRunner

from dumbo_esse3.cli import app, read_graduation_day_list
from dumbo_esse3.primitives import StudentId
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


def test_graduation_days(runner):
    result = runner.invoke(app, ["graduation-days"])
    assert result.exit_code == 0
    assert "Commissione Master del 19 dicembre 2022" in result.stdout


def test_read_graduation_day_list():
    with patch("builtins.open", mock_open(read_data="""
MATRICOLA,STUDENTE,VOTO FINALE,LODE,MENZIONE,NOTE
12344,AIEIE BRAZORF,105,,,una bella nota
12345,MARIANO VANO,114,sì,,una nota ancora più bella
    """.strip())):
        graduations = read_graduation_day_list(Path("scores.csv"))
        assert len(graduations) == 2
        assert graduations[0].student.id == StudentId("12344")
