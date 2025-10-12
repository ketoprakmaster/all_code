"""
Test script for all_code.py command-line arguments.

This script creates temporary directories and files, then uses the built-in
subprocess module to run all_code.py with different options:

- Default behavior (creates 'full_code.txt')
- Overriding the output file name with -o/--output-file
- Including only specific files with -i/--include-files
- Overriding programming extensions with -x/--extensions
- Excluding directories with -e/--exclude-dirs

No external libraries are required.
"""

import os
import shutil
import subprocess
import tempfile
import sys

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "all_code.py")


def run_script(args, cwd):
    """
    Run all_code.py with the provided command-line arguments in directory cwd.
    """
    cmd = [sys.executable, SCRIPT_PATH] + args
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result


def test_default_arguments():
    # Create a temporary directory to serve as the source for aggregation.
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Copy all_code.py to tmp directory  and run it without any args
        TMP_SCRIPT_PATH = shutil.copy(SCRIPT_PATH, tmp_dir)
        cmd = [sys.executable, TMP_SCRIPT_PATH]
        subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True)

        assert os.path.exists(os.path.join(tmp_dir, "full_code.txt")), "full_code.txt not created by default"


def test_directory_argument():
    with tempfile.TemporaryDirectory() as source_dir:
        # Create a dummy Python file in the source directory.
        dummy_file = os.path.join(source_dir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("print('Aggregating from source directory')")
        # Use a separate temporary directory as the working directory for the script.
        with tempfile.TemporaryDirectory() as tmp_working:
            custom_output = "test_output.txt"
            # Run the script with -d pointing to the source directory.
            run_script(["-d", source_dir, "-o", custom_output], cwd=tmp_working)
            output_file = os.path.join(tmp_working, custom_output)
            assert os.path.exists(output_file), "Output file not created when using --directory"
            with open(output_file, "r") as f:
                content = f.read()
            assert "dummy.py" in content, "Aggregated content does not reflect the --directory argument"
            print("test_directory_argument passed.")


def test_default_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy Python file so that there is something to include.
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("print('Hello World')")

        # Run the script with default output (should create full_code.txt)
        run_script(["-d", tmpdir], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        assert os.path.exists(output_file), "Default output file not created"
        print("test_default_output passed.")


def test_override_output_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("print('Hello World')")

        custom_output = "custom_output.txt"
        run_script(["-d", tmpdir, "-o", custom_output], cwd=tmpdir)
        output_file = os.path.join(tmpdir, custom_output)
        assert os.path.exists(output_file), "Overridden output file not created"
        print("test_override_output_file passed.")


def test_include_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two Python files.
        file1 = os.path.join(tmpdir, "dummy.py")
        with open(file1, "w") as f:
            f.write("print('Hello from dummy')")

        file2 = os.path.join(tmpdir, "extra.py")
        with open(file2, "w") as f:
            f.write("print('Hello from extra')")

        # Specify only dummy.py to be included.
        run_script(["-d", tmpdir, "-i", "dummy.py"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r") as f:
            content = f.read()
        assert "dummy.py" in content, "dummy.py should be included"
        assert "print('Hello from extra')" not in content, "extra.py should not be included"
        print("test_include_files passed.")


def test_extensions():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create one .py file and one .txt file.
        py_file = os.path.join(tmpdir, "dummy.py")
        with open(py_file, "w") as f:
            f.write("print('Python file')")
        txt_file = os.path.join(tmpdir, "dummy.txt")
        with open(txt_file, "w") as f:
            f.write("This is a text file.")

        # Override extensions to only include .py files.
        run_script(["-d", tmpdir, "-x", ".py"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r") as f:
            content = f.read()
        assert "dummy.py" in content, "dummy.py should be included with .py extension"
        assert "This is a text file." not in content, "dummy.txt should be excluded when only .py is allowed"
        print("test_extensions passed.")


def test_exclude_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory that will be excluded.
        exclude_dir = os.path.join(tmpdir, "exclude_me")
        os.mkdir(exclude_dir)
        file_in_excluded = os.path.join(exclude_dir, "dummy.py")
        with open(file_in_excluded, "w") as f:
            f.write("print('This file is in an excluded directory')")

        # Run the script with exclude_dirs set to 'exclude_me'
        run_script(["-d", tmpdir, "-e", "exclude_me"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r") as f:
            content = f.read()
        # The directory tree should mark exclude_me as excluded.
        assert "exclude_me/ [EXCLUDED]" in content, "exclude_me directory should be marked as excluded"
        # The file inside should not be aggregated.
        assert "dummy.py" not in content, "File inside excluded directory should not be included"
        print("test_exclude_dirs passed.")

def test_extensions_allowlist():
    with tempfile.TemporaryDirectory() as tmpdir:
        py_file = os.path.join(tmpdir, "dummy.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("print('Python file')")
        txt_file = os.path.join(tmpdir, "dummy.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("This is a text file.")
        run_script(["-d", tmpdir, "-x", ".py"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "dummy.py" in content, "dummy.py should be included with .py extension"
        assert "This is a text file." not in content, "dummy.txt should be excluded when only .py is allowed"
        print("test_extensions_allowlist() passed.")

def test_exclude_dirs_additive():
    with tempfile.TemporaryDirectory() as tmpdir:
        exclude_dir = os.path.join(tmpdir, "exclude_me")
        os.mkdir(exclude_dir)
        file_in_excluded = os.path.join(exclude_dir, "dummy.py")
        with open(file_in_excluded, "w", encoding="utf-8") as f:
            f.write("print('This file is in an excluded directory')")
        run_script(["-d", tmpdir, "-e", "exclude_me"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "exclude_me/ [EXCLUDED]" in content, "exclude_me directory should be marked as excluded"
        assert "This file is in an excluded directory" not in content, "File inside excluded directory should not be included"
        print("test_exclude_dirs_additive() passed.")


def test_exclude_files_glob():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "foo"), exist_ok=True)

        # a JSON file to exclude via glob
        cfg = os.path.join(tmpdir, "foo", "config.json")
        with open(cfg, "w", encoding="utf-8") as f:
            f.write('{"ok": true}')

        # a file that must remain included
        keep = os.path.join(tmpdir, "foo", "keep.py")
        with open(keep, "w", encoding="utf-8") as f:
            f.write("print('KEEP_ME')")

        # exclude via glob
        run_script(["-d", tmpdir, "--exclude-files", "foo/*.json"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # tree should show the excluded file as [EXCLUDED]
        assert "config.json [EXCLUDED]" in content, "Excluded file should be marked in the tree"

        # aggregated content should NOT contain the file's contents
        assert '{"ok": true}' not in content, "Excluded file contents must not be aggregated"

        # keep.py stays in
        assert "KEEP_ME" in content, "Non-excluded file should be included"
        print("test_exclude_files_glob() passed.")

def test_replace_exclude_dirs_behavior():
    with tempfile.TemporaryDirectory() as tmpdir:
        node_modules_dir = os.path.join(tmpdir, "node_modules")
        os.makedirs(node_modules_dir, exist_ok=True)
        nm_file = os.path.join(node_modules_dir, "lib.js")
        with open(nm_file, "w", encoding="utf-8") as f:
            f.write("console.log('IN_NODE_MODULES');")
        custom_dir = os.path.join(tmpdir, "custom_dir")
        os.makedirs(custom_dir, exist_ok=True)
        custom_file = os.path.join(custom_dir, "x.py")
        with open(custom_file, "w", encoding="utf-8") as f:
            f.write("print('IN_CUSTOM_DIR')")
        root_py = os.path.join(tmpdir, "main.py")
        with open(root_py, "w", encoding="utf-8") as f:
            f.write("print('ROOT_OK')")
        run_script(["-d", tmpdir, "--replace-exclude-dirs", "-e", "custom_dir"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "custom_dir/ [EXCLUDED]" in content, "custom_dir should be marked [EXCLUDED] when replaced"
        assert "IN_CUSTOM_DIR" not in content, "Files in custom_dir must be excluded in replace mode"
        assert "IN_NODE_MODULES" in content, "node_modules should not be excluded in replace mode"
        assert "ROOT_OK" in content, "root file should be included"
        print("test_replace_exclude_dirs_behavior() passed.")

def test_extension_precedence_exclude_overrides_allowlist():
    with tempfile.TemporaryDirectory() as tmpdir:
        js_file = os.path.join(tmpdir, "a.js")
        with open(js_file, "w", encoding="utf-8") as f:
            f.write("console.log('JS_INCLUDED?');")
        py_file = os.path.join(tmpdir, "b.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("print('PY_INCLUDED')")
        run_script(["-d", tmpdir, "-x", ".py,.js", "-X", ".js"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "JS_INCLUDED?" not in content, ".js should be excluded by -X even if allowed by -x"
        assert "PY_INCLUDED" in content, ".py should remain included"
        print("test_extension_precedence_exclude_overrides_allowlist() passed.")


def test_tree_not_traversing_excluded():
    with tempfile.TemporaryDirectory() as tmpdir:
        deep = os.path.join(tmpdir, "secret")
        os.makedirs(os.path.join(deep, "nested"), exist_ok=True)
        secret_file = os.path.join(deep, "nested", "hidden.py")
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write("print('SHOULD_NOT_APPEAR')")
        run_script(["-d", tmpdir, "-e", "secret"], cwd=tmpdir)
        output_file = os.path.join(tmpdir, "full_code.txt")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "secret/ [EXCLUDED]" in content, "Top-level excluded dir should be marked once"
        assert "hidden.py" not in content, "Files inside excluded dir must not appear (no traversal)"
        print("test_tree_not_traversing_excluded() passed.")

if __name__ == "__main__":
    # Run everything if executed directly
    test_default_arguments()
    test_directory_argument()
    test_default_output()
    test_override_output_file()
    test_include_files()
    test_extensions_allowlist()
    test_exclude_dirs_additive()
    test_exclude_files_glob()
    test_replace_exclude_dirs_behavior()
    test_extension_precedence_exclude_overrides_allowlist()
    test_tree_not_traversing_excluded()
    print("All tests passed!")
