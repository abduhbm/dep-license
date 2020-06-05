import json
import os
import sys

import pytest

from dep_license import __version__
from dep_license import run

project = os.path.dirname(os.path.dirname(__file__))


def test_version(capsys):
    with pytest.raises(SystemExit):
        run(["-v"])
    out, _ = capsys.readouterr()
    assert out.strip() == __version__


def test_local_dir(capsys):
    ret = run([project])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert "Found" in out


def test_local_file(capsys):
    ret = run([os.path.join(project, "requirements.txt")])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert "Found" in out


def test_format(capsys):
    ret = run([project, "-f", "json"])
    out, _ = capsys.readouterr()
    assert ret == 0
    output = json.loads("".join(out.splitlines()[2:]))
    assert isinstance(output, list)
    assert isinstance(output[0], dict)


def test_output(tmpdir, capsys):
    x = tmpdir.join("output")
    ret = run([project, "-o", x.strpath, "-f", "json"])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert os.path.isfile(x.strpath)
    with open(x.strpath) as f:
        assert isinstance(json.load(f), list)


def test_name_dependency_file(capsys):
    ret = run([project, "-n", "requirements.txt"])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert "Found" in out


def test_check_banned(tmpdir, capsys):
    x = tmpdir.join("deplic.cfg")
    x.write(
        """
        [deplic]
        banned = MIT
        """
    )
    ret = run([project, "-c", x.strpath])
    out, _ = capsys.readouterr()
    assert ret == 1


def test_check_env(capsys):
    ret = run([sys.executable, "-e"])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert "Found" in out


def test_check_invalid_env(capsys):
    ret = run([os.path.dirname("/invalid/venv/path"), "-e"])
    out, _ = capsys.readouterr()
    assert ret == 1


def test_with_remote_git_repo(capsys):
    ret = run(["https://github.com/abduhbm/dep-license"])
    out, _ = capsys.readouterr()
    assert ret == 0
    assert "Found" in out


def test_invalid_project(capsys):
    ret = run(["SomethingDoesntExist"])
    out, _ = capsys.readouterr()
    assert ret == 1
    assert out == "no dependencies found\n"
