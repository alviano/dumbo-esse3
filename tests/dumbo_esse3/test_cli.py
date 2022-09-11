from typer.testing import CliRunner

from dumbo_esse3.cli import app

runner = CliRunner()


def test_courses():
    result = runner.invoke(app, ["courses"])
    assert result.exit_code == 0
    assert "Courses" in result.stdout


def test_exams():
    result = runner.invoke(app, ["exams"])
    assert result.exit_code == 0
    assert "Exams" in result.stdout


def test_theses():
    result = runner.invoke(app, ["theses"])
    assert result.exit_code == 0
    assert "Theses" in result.stdout
