"""Command line, author metadata, file errors and the Windows batch report."""

import pytest
from pptx import Presentation

import mermaid2pptx as m2p
from mermaid2pptx import cli
from samples import ALL_EXAMPLES


def test_author(tmp_path, monkeypatch):
    monkeypatch.delenv(m2p.AUTHOR_ENV, raising=False)
    prs, _, _ = m2p.convert("graph TD\nA-->B")
    out = tmp_path / "a.pptx"
    prs.save(out)
    cp = Presentation(out).core_properties
    assert cp.author == cp.last_modified_by == ""                    # not python-pptx's own
    assert cp.comments == "" and cp.revision == 1
    monkeypatch.setenv(m2p.AUTHOR_ENV, "From Env")
    prs, _, _ = m2p.convert("graph TD\nA-->B")
    assert prs.core_properties.author == "From Env"
    prs, _, _ = m2p.convert("graph TD\nA-->B", m2p.Options(author="Someone Else"))
    assert prs.core_properties.author == "Someone Else"


def test_cli(tmp_path, capsys):
    md = tmp_path / "doc.md"
    md.write_text("```mermaid\ngraph TD\nA-->B\n```\n```mermaid\ngraph LR\nX-->Y-->Z\n```\n")
    assert cli.main([str(md), "--block", "2"]) == 0
    assert (tmp_path / "doc.pptx").exists()
    assert "3 nodes, 2 edges" in capsys.readouterr().out            # the Mermaid drawing by default
    assert cli.main([str(md), "--block", "2", "--render", "bpmn", "--color", "slate"]) == 0
    assert "5 nodes, 4 edges" in capsys.readouterr().out            # + start and end events
    with pytest.raises(SystemExit):
        cli.main([str(md), "--color", "nope"])
    bad = tmp_path / "bad.mmd"
    bad.write_text("pie\n")
    assert cli.main([str(bad), "-o", str(tmp_path / "x.pptx")]) == 1
    with pytest.raises(SystemExit):
        cli.main([str(md), "--block", "3"])
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert m2p.__version__ in capsys.readouterr().out


def test_cli_file_errors(tmp_path, capsys, monkeypatch):
    """A one-line message, never a traceback: the .exe is run by people who don't read Python."""
    assert cli.main([str(tmp_path / "missing.mmd")]) == 1
    assert capsys.readouterr().err.startswith("error: cannot read")
    ansi = tmp_path / "ansi.mmd"
    ansi.write_bytes("graph TD\nA[Été] --> B\n".encode("cp1252"))
    assert cli.main([str(ansi)]) == 1
    assert "is not UTF-8" in capsys.readouterr().err
    good = tmp_path / "good.mmd"
    good.write_text("graph TD\nA --> B\n", encoding="utf-8")
    assert cli.main([str(good), "-o", str(tmp_path / "no" / "such" / "dir.pptx")]) == 1
    assert capsys.readouterr().err.startswith("error: cannot write")

    def locked(self, path):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(type(Presentation()), "save", locked)
    assert cli.main([str(good)]) == 1
    assert "open in PowerPoint" in capsys.readouterr().err


def test_convert_files_reports_for_a_message_box(tmp_path, capsys, monkeypatch):
    good, bad = tmp_path / "good.mmd", tmp_path / "bad.mmd"
    good.write_text("graph TD\nA --> B\n", encoding="utf-8")
    bad.write_text("pie\n", encoding="utf-8")
    assert cli.convert_files([str(good)]) == (True, f"{tmp_path / 'good.pptx'}: 2 nodes, 1 edge, 0 subgraphs")
    ok, report = cli.convert_files([str(good), str(bad), str(tmp_path / "missing.mmd")])
    assert not ok and report.count("\n") == 2 and "error: cannot read" in report
    monkeypatch.setattr(cli, "convert", lambda *a: 1 / 0)                  # a bug, not a user error
    ok, report = cli.convert_files([str(good)])
    assert not ok and "unexpected ZeroDivisionError" in report
    assert capsys.readouterr() == ("", "")                                  # nothing leaks to the console


@pytest.mark.parametrize("path", ALL_EXAMPLES, ids=lambda p: p.stem)
def test_every_example_converts(path, tmp_path, capsys):
    assert cli.main([str(path), "-o", str(tmp_path / "out.pptx")]) == 0
    assert "warning" not in capsys.readouterr().err
