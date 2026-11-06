import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures import write_fixture
from unfself_ui import __main__ as cli


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "unfself_ui", "--convert", *map(str, arguments)],
        env=os.environ | {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True, text=True,
    )


@pytest.mark.parametrize("with_report", [False, True])
def test_cli_converts_and_reports_json(tmp_path, with_report):
    source, expected = write_fixture(tmp_path)
    report = tmp_path / "report.json"
    arguments = [source, "--output-dir", tmp_path]
    if with_report:
        arguments += ["--report", report]
    result = run_cli(*arguments)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    output = tmp_path / "sample.elf"
    assert output.read_bytes() == expected
    assert json.loads(report.read_text() if with_report else result.stdout) == [
        {"source": str(source), "status": "converted", "output": str(output)}
    ]
    if with_report:
        assert result.stdout == ""


@pytest.mark.parametrize("symlink", [False, True])
def test_existing_report_prevents_conversion(tmp_path, symlink):
    source, _ = write_fixture(tmp_path)
    report = tmp_path / "report.json"
    target = tmp_path / "missing.json"
    if symlink:
        report.symlink_to(target)
    else:
        report.write_bytes(b"keep me")
    result = run_cli(source, "--output-dir", tmp_path, "--report", report)
    assert result.returncode == 1
    assert "report access failed" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
    assert set(tmp_path.iterdir()) == {source, report}
    if symlink:
        assert report.is_symlink()
        assert not target.exists()
    else:
        assert report.read_bytes() == b"keep me"


@pytest.mark.parametrize("parent_is_file", [False, True])
def test_invalid_report_parent_prevents_conversion(tmp_path, parent_is_file):
    source, _ = write_fixture(tmp_path)
    parent = tmp_path / "parent"
    if parent_is_file:
        parent.write_bytes(b"keep me")
    result = run_cli(source, "--output-dir", tmp_path, "--report", parent / "report.json")
    assert result.returncode == 1
    assert "report access failed" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
    assert set(tmp_path.iterdir()) == ({source, parent} if parent_is_file else {source})


def test_report_path_is_reserved_before_output_publication(tmp_path):
    source, expected = write_fixture(tmp_path)
    report = tmp_path / "sample.elf"
    result = run_cli(source, "--output-dir", tmp_path, "--report", report)
    assert result.returncode == 0, result.stderr
    output = tmp_path / "sample (2).elf"
    assert output.read_bytes() == expected
    assert json.loads(report.read_text()) == [
        {"source": str(source), "status": "converted", "output": str(output)}
    ]


def test_report_write_failure_is_a_clean_cli_error(tmp_path, monkeypatch, capsys):
    source, expected = write_fixture(tmp_path)
    report = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", ["unfself_ui", "--convert", str(source),
                                     "--output-dir", str(tmp_path), "--report", str(report)])

    def fail_write(*args, **kwargs):
        raise OSError("report disk full")

    monkeypatch.setattr(cli.json, "dump", fail_write)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "report access failed: report disk full" in captured.err
    assert "Traceback" not in captured.err
    assert (tmp_path / "sample.elf").read_bytes() == expected
