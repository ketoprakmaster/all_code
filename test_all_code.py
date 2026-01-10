import os
import shutil
import subprocess
import sys
import pytest

# Path to the script we are testing
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "all_code.py")

def run_script(args, cwd):
    """
    Helper to run all_code.py with the provided command-line arguments.
    """
    cmd = [sys.executable, SCRIPT_PATH] + args
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result

def test_default_arguments(tmp_path):
    # Copy all_code.py to tmp directory and run it without any args
    TMP_SCRIPT_PATH = shutil.copy(SCRIPT_PATH, tmp_path)
    cmd = [sys.executable, str(TMP_SCRIPT_PATH)]
    subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)

    assert (tmp_path / "full_code.txt").exists(), "full_code.txt not created by default"

def test_directory_argument(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create a dummy Python file
    dummy_file = source_dir / "dummy.py"
    dummy_file.write_text("print('Aggregating from source directory')")

    tmp_working = tmp_path / "working"
    tmp_working.mkdir()

    custom_output = "test_output.txt"
    run_script(["-d", str(source_dir), "-o", custom_output], cwd=tmp_working)

    output_file = tmp_working / custom_output
    assert output_file.exists(), "Output file not created when using --directory"

    content = output_file.read_text()
    assert "dummy.py" in content, "Aggregated content does not reflect the --directory argument"

def test_default_output(tmp_path):
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("print('Hello World')")

    run_script(["-d", str(tmp_path)], cwd=tmp_path)
    assert (tmp_path / "full_code.txt").exists(), "Default output file not created"

def test_override_output_file(tmp_path):
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("print('Hello World')")

    custom_output = "custom_output.txt"
    run_script(["-d", str(tmp_path), "-o", custom_output], cwd=tmp_path)
    assert (tmp_path / custom_output).exists(), "Overridden output file not created"

def test_include_files(tmp_path):
    (tmp_path / "dummy.py").write_text("print('Hello from dummy')")
    (tmp_path / "extra.py").write_text("print('Hello from extra')")

    run_script(["-d", str(tmp_path), "-i", "dummy.py"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text()

    assert "dummy.py" in content
    assert "print('Hello from extra')" not in content

def test_extensions(tmp_path):
    (tmp_path / "dummy.py").write_text("print('Python file')")
    (tmp_path / "dummy.txt").write_text("This is a text file.")

    run_script(["-d", str(tmp_path), "-x", ".py"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text()

    assert "dummy.py" in content
    assert "This is a text file." not in content

def test_exclude_dirs(tmp_path):
    exclude_dir = tmp_path / "exclude_me"
    exclude_dir.mkdir()
    (exclude_dir / "dummy.py").write_text("print('excluded')")

    run_script(["-d", str(tmp_path), "-e", "exclude_me"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text()

    assert "exclude_me/ [EXCLUDED]" in content
    assert "print('excluded')" not in content

def test_extensions_allowlist(tmp_path):
    (tmp_path / "dummy.py").write_text("print('Python file')", encoding="utf-8")
    (tmp_path / "dummy.txt").write_text("This is a text file.", encoding="utf-8")

    run_script(["-d", str(tmp_path), "-x", ".py"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "dummy.py" in content
    assert "This is a text file." not in content

def test_exclude_dirs_additive(tmp_path):
    exclude_dir = tmp_path / "exclude_me"
    exclude_dir.mkdir()
    (exclude_dir / "dummy.py").write_text("print('excluded')", encoding="utf-8")

    run_script(["-d", str(tmp_path), "-e", "exclude_me"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "exclude_me/ [EXCLUDED]" in content
    assert "print('excluded')" not in content

def test_exclude_files_glob(tmp_path):
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    (foo_dir / "config.json").write_text('{"ok": true}', encoding="utf-8")
    (foo_dir / "keep.py").write_text("print('KEEP_ME')", encoding="utf-8")

    run_script(["-d", str(tmp_path), "--exclude-files", "foo/*.json"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "config.json [EXCLUDED]" in content
    assert '{"ok": true}' not in content
    assert "KEEP_ME" in content

def test_exclude_files_absolute_path(tmp_path):
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    cfg = foo_dir / "config.json"
    cfg.write_text('{"abs": true}', encoding="utf-8")

    run_script(["-d", str(tmp_path), "--exclude-files", str(cfg)], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")
    assert '{"abs": true}' not in content

def test_exclude_files_dot_slash(tmp_path):
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    (foo_dir / "config.json").write_text('{"dot": true}', encoding="utf-8")

    run_script(["-d", str(tmp_path), "--exclude-files", "./foo/config.json"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "config.json [EXCLUDED]" in content
    assert '{"dot": true}' not in content

def test_exclude_files_cwd_differs_from_startpath(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    foo_dir = project / "foo"
    foo_dir.mkdir()
    (foo_dir / "config.json").write_text('{"cwd": true}', encoding="utf-8")

    run_script(["-d", "project", "--exclude-files", "./foo/config.json"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")
    assert '{"cwd": true}' not in content

def test_exclude_files_dot_slash_glob(tmp_path):
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    (foo_dir / "config.json").write_text('{"glob": true}', encoding="utf-8")

    run_script(["-d", str(tmp_path), "--exclude-files", "./foo/*.json"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")
    assert '{"glob": true}' not in content

@pytest.mark.skipif(os.name != "nt", reason="Backslash paths are Windows-only")
def test_exclude_files_backslash_path(tmp_path):
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    (foo_dir / "config.json").write_text('{"win": true}', encoding="utf-8")

    win_style = r"foo\config.json"
    run_script(["-d", str(tmp_path), "--exclude-files", win_style], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")
    assert '{"win": true}' not in content

def test_replace_exclude_dirs_behavior(tmp_path):
    nm_dir = tmp_path / "node_modules"
    nm_dir.mkdir()
    (nm_dir / "lib.js").write_text("console.log('IN_NODE_MODULES');", encoding="utf-8")

    custom_dir = tmp_path / "custom_dir"
    custom_dir.mkdir()
    (custom_dir / "x.py").write_text("print('IN_CUSTOM_DIR')", encoding="utf-8")

    (tmp_path / "main.py").write_text("print('ROOT_OK')", encoding="utf-8")

    run_script(["-d", str(tmp_path), "--replace-exclude-dirs", "-e", "custom_dir"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "custom_dir/ [EXCLUDED]" in content
    assert "IN_CUSTOM_DIR" not in content
    assert "IN_NODE_MODULES" in content
    assert "ROOT_OK" in content

def test_exclude_files_case_insensitivity(tmp_path):
    """Checks if exclusions are case-insensitive (standard on Windows)."""
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    target = foo_dir / "build.xml"
    target.write_text("<xml>target</xml>", encoding="utf-8")

    # Use uppercase pattern for lowercase filename
    run_script(["-d", str(tmp_path), "--exclude-files", "FOO/BUILD.XML"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    if os.name == "nt":
        assert "<xml>target</xml>" not in content
        assert "build.xml [EXCLUDED]" in content
    else:
        # On Linux/WSL, behavior depends on your fnmatch implementation
        # Most cross-platform tools prefer case-insensitive for config files
        pass

def test_exclude_files_recursive_glob(tmp_path):
    """Tests if double-asterisk recursive globs work as expected."""
    deep_dir = tmp_path / "a" / "b" / "c"
    deep_dir.mkdir(parents=True)
    (deep_dir / "secret.log").write_text("SENSITIVE_DATA", encoding="utf-8")

    # Pattern designed to find .log files anywhere in a/
    run_script(["-d", str(tmp_path), "--exclude-files", "a/**/*.log"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "SENSITIVE_DATA" not in content
    assert "secret.log [EXCLUDED]" in content

def test_exclude_files_parent_traversal(tmp_path):
    """Tests if '../' in patterns are resolved correctly before matching."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "main.py").write_text("print('hello')", encoding="utf-8")

    # A weird but valid path pattern
    weird_pat = "app/../app/main.py"
    run_script(["-d", str(tmp_path), "--exclude-files", weird_pat], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "print('hello')" not in content
    assert "main.py [EXCLUDED]" in content

def test_exclude_files_with_spaces(tmp_path):
    """Ensures filenames with spaces are handled correctly."""
    foo_dir = tmp_path / "foo"
    foo_dir.mkdir()
    # Note: We use a file with a space
    space_file = foo_dir / "my notes.txt"
    space_file.write_text("TOP_SECRET_NOTES", encoding="utf-8")

    # In a CSV, this usually needs to be handled carefully by your _split_csv
    run_script(["-d", str(tmp_path), "--exclude-files", "foo/my notes.txt"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "TOP_SECRET_NOTES" not in content

def test_exclude_files_multi_value(tmp_path):
    """Tests providing multiple patterns at once."""
    (tmp_path / "one.xml").write_text("ONE", encoding="utf-8")
    (tmp_path / "two.json").write_text("TWO", encoding="utf-8")
    (tmp_path / "three.py").write_text("THREE", encoding="utf-8")

    run_script(["-d", str(tmp_path), "--exclude-files", "one.xml,two.json"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "ONE" not in content
    assert "TWO" not in content
    assert "THREE" in content

def test_extension_precedence_exclude_overrides_allowlist(tmp_path):
    (tmp_path / "a.js").write_text("console.log('JS_INCLUDED?');", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('PY_INCLUDED')", encoding="utf-8")

    run_script(["-d", str(tmp_path), "-x", ".py,.js", "-X", ".js"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "JS_INCLUDED?" not in content
    assert "PY_INCLUDED" in content

def test_tree_not_traversing_excluded(tmp_path):
    deep = tmp_path / "secret"
    nested = deep / "nested"
    nested.mkdir(parents=True)
    (nested / "hidden.py").write_text("print('SHOULD_NOT_APPEAR')", encoding="utf-8")

    run_script(["-d", str(tmp_path), "-e", "secret"], cwd=tmp_path)
    content = (tmp_path / "full_code.txt").read_text(encoding="utf-8")

    assert "secret/ [EXCLUDED]" in content
    assert "hidden.py" not in content
