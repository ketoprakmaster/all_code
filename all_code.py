# Copyright 2024 Spencer Bentley

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import os
import argparse
import sys
import subprocess
import pathlib
import fnmatch


# Define the master file name
FULL_CODE_FILE_NAME = "full_code.txt"

FILES_TO_INCLUDE = {}  # if empty, include all files
EXCLUDE_EXTENSIONS = set()  # User-defined extensions to exclude

# FILES_TO_INCLUDE = {
#     'some_file.py',
#     'another_file.js',
# }

# Define programming-related file extensions (removed '.json' and '.md')
PROGRAMMING_EXTENSIONS = {
    # General Programming Languages
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".vb",
    ".r",
    ".rb",
    ".go",
    ".php",
    ".swift",
    ".kt",
    ".rs",
    ".scala",
    ".pl",
    ".lua",
    ".jl",
    # Web Development
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".less",
    ".sass",
    # Shell & Automation
    ".sh",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    # Database & Query Languages
    ".sql",
    ".psql",
    ".db",
    ".sqlite",
    # Markup & Config Files
    ".xml",
    ".json",
    ".toml",
    ".ini",
    ".yml",
    ".yaml",
    ".md",
    ".rst",
    # Build & Make Systems
    ".Makefile",
    ".gradle",
    ".cmake",
    ".ninja",
    # Other
    ".pqm",
    ".pq",
}

# Define directories to exclude during file aggregation and directory tree generation
DEFAULT_EXCLUDED_DIRS = {
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
    ".git",
    "dist",
    "build",
    "temp",
    "old_files",
    "flask_session",
}

# Define the name of this script to exclude it
SCRIPT_NAME = os.path.basename(__file__)

# Define files to exclude from both aggregation and directory tree
EXCLUDE_FILES = {"package-lock.json", "package.json", "temp.py"}


def generate_directory_tree(startpath, should_skip_dir, is_tree_excluded_file=None):
    """
    Generates an ASCII directory tree.
    - Excluded directories and their subdirectories are listed once and marked [EXCLUDED].
    - Files are listed once; if a file is user-excluded, it is shown as [EXCLUDED].
    """
    tree = ""
    for root, dirs, files in os.walk(startpath):
        # compute path pieces / indent
        rel_path = os.path.relpath(root, startpath)
        if rel_path == ".":
            rel_path = ""
        level = len(rel_path.split(os.sep)) if rel_path else 0
        indent = "│   " * level + "├── " if level > 0 else ""

        current_dir = (
            os.path.basename(root)
            if rel_path
            else os.path.basename(startpath.rstrip(os.sep)) or startpath
        )

        # directory-level exclusion
        if should_skip_dir(root):
            tree += f"{indent}{current_dir}/ [EXCLUDED]\n"
            dirs[:] = []  # don't descend
            continue

        tree += f"{indent}{current_dir}/\n"

        for f in files:
            if f in EXCLUDE_FILES:
                continue  # hide internal/always-excluded files from the tree

            path = os.path.join(root, f)
            # Decide if this file should be *marked* excluded in the tree.
            # IMPORTANT: do not mark non-programming files as excluded just because
            # they won't be aggregated; only mark files explicitly excluded by user controls.
            excluded_in_tree = False
            if is_tree_excluded_file is not None:
                excluded_in_tree = is_tree_excluded_file(path)

            suffix = " [EXCLUDED]" if excluded_in_tree else ""
            tree_line = f"{'│   ' * (level + 1)}├── {f}{suffix}\n"
            tree += tree_line

    return tree

# New helper: decide if a file should appear as [EXCLUDED] in the tree.
# Only explicit user controls should show "[EXCLUDED]" tags:
#  - --exclude-files matches (glob or exact)
#  - -X/--exclude-extensions matches
def make_is_tree_excluded_file(exclude_file_globs, excluded_exts, startpath):
    """
    Tree-exclusion predicate. Used by the directory-tree printer only.
    Non-programming files are *not* tagged excluded just because they won't be aggregated.
    """
    
    def _pred(filepath: str) -> bool:
        # extension-based denylist (user-provided -X)
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext and ext in excluded_exts:
            return True

        # --exclude-files globs or exact paths (abs or project-relative)
        if exclude_file_globs:
            abs_path = os.path.abspath(filepath)
            rel_path = os.path.relpath(filepath, startpath)
            for pat in exclude_file_globs:
                if (
                    fnmatch.fnmatch(abs_path, pat)
                    or fnmatch.fnmatch(rel_path, pat)
                    or abs_path == pat
                    or rel_path == pat
                ):
                    return True

        return False

    return _pred


def is_programming_file(filename):
    """Checks if a file has a programming-related extension and is not in the exclude list."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    return ext in PROGRAMMING_EXTENSIONS and ext not in EXCLUDE_EXTENSIONS


def should_exclude(path):
    # Determines if a file should be excluded based on its path.
    # - Excludes files in EXCLUDE_DIRS and their subdirectories.
    # - Excludes files listed in EXCLUDE_FILES.
    # legacy function

    # Normalize path separators
    normalized_path = os.path.normpath(path)
    parts = normalized_path.split(os.sep)

    # Check if the file itself is in EXCLUDE_FILES
    if parts[-1] in EXCLUDE_FILES:
        return True

    return False


def should_include_file(file_path):

    # Determines if a file should be included based on FILES_TO_INCLUDE.
    # If FILES_TO_INCLUDE is empty, include all files.

    if not FILES_TO_INCLUDE:
        return True  # Include all files if the list is empty
    rel_file_path = os.path.relpath(file_path)
    return rel_file_path in FILES_TO_INCLUDE


def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate code files into a master file with a directory tree."
    )
    parser.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Copy the aggregated content to the clipboard instead of writing to a file.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=os.getcwd(),
        help="Specify the directory to start aggregation from. Defaults to the current working directory.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default=FULL_CODE_FILE_NAME,
        help="Name of the output file. Defaults to full_code.txt.",
    )
    parser.add_argument(
        "-i",
        "--include-files",
        type=str,
        default="",
        help="Comma-separated list of files to include. If not provided, all files are included.",
    )
    parser.add_argument(
        "-x",
        "--extensions",
        type=str,
        default="",
        help="Comma-separated list of programming extensions to use. Replaces the default set if provided.",
    )
    parser.add_argument(
        "-X",
        "--exclude-extensions",
        type=str,
        default="",
        help="Comma-separated list of file extensions to exclude.",
    )
    """
    Additional parser arguments:  
    """
    parser.add_argument(
        "-e",
        "--exclude-dirs",
        default="",
        help="Comma-separated directory names or paths to additionally exclude files.",
    )
    parser.add_argument(
        "--replace-exclude-dirs",
        action="store_true",
        help="Replace default excluded directories with the list from -e.",
    )
    parser.add_argument(
        "--exclude-files",
        default="",
        help="Comma-separated file paths or globs to exclude.",
    )
    parser.add_argument("--self", action="store_true", help="Include all_code.py in tree/aggregation. all_code.py is excluded by default to avoid inclusion of the working script behind this tool.")

    return parser.parse_args()


# Helper to remove whitespace
def _split_csv(s: str):
    """Split a comma-separated string, stripping *all* whitespace (incl. NBSP)."""
    if not s:
        return []
    parts = []
    for raw in s.split(","):
        # remove all whitespace characters inside each token (incl. NBSP)
        p = "".join(ch for ch in raw if not ch.isspace())
        if p:
            parts.append(p)
    return parts

# TODO: Works on MacOS and Windows 10+. Linux support can be added later
def copy_to_clipboard(content):
    """Copy text to the system clipboard on macOS and Windows."""
    try:
        if sys.platform == "darwin":
            process = subprocess.Popen(
                "pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE
            )
            process.communicate(content.encode("utf-8"))
            return process.returncode == 0
        elif sys.platform.startswith("win"):
            # Windows 10+ ships with the 'clip' utility
            process = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
            # clip expects UTF-16LE encoding
            process.communicate(content.encode("utf-16le"))
            return process.returncode == 0
        else:
            print("Clipboard copy is only supported on macOS and Windows 10+.")
            return False
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False


def main():
    args = parse_arguments()

    # Override the global options if command line arguments are provided.
    global FULL_CODE_FILE_NAME, FILES_TO_INCLUDE, PROGRAMMING_EXTENSIONS, EXCLUDE_EXTENSIONS

    if args.output_file:
        FULL_CODE_FILE_NAME = args.output_file

    if args.include_files:
        # Split the comma-separated string and remove any extra whitespace.
        FILES_TO_INCLUDE = {
            f.strip() for f in args.include_files.split(",") if f.strip()
        }

    if args.extensions:
        PROGRAMMING_EXTENSIONS = {
            ext.strip() for ext in args.extensions.split(",") if ext.strip()
        }

    if args.exclude_extensions:
        EXCLUDE_EXTENSIONS = {
            ext.strip() for ext in args.exclude_extensions.split(",") if ext.strip()
        }
        
    # Users may include this script in output via --self.
    # By default we hide it to prevent the tool from including itself.
    if not args.self:
        EXCLUDE_FILES.add(SCRIPT_NAME)

    # Debugging print statement to verify exclusions
    print(f"Excluding extensions: {EXCLUDE_EXTENSIONS}")
    startpath = args.directory

    if not os.path.isdir(startpath):
        print(
            f"Error: The specified directory '{startpath}' does not exist or is not a directory."
        )
        sys.exit(1)

    # Build the effective directory exclusion set.
    # Default is additive: defaults ∪ user list. Use --replace-exclude-dirs to replace.
    user_excluded = set(_split_csv(args.exclude_dirs))
    effective_excluded = (
        user_excluded
        if args.replace_exclude_dirs
        else (set(DEFAULT_EXCLUDED_DIRS) | user_excluded)
    )

    # 2) Build name & path-prefix lists for directories
    exclude_dir_names = set()
    exclude_dir_prefixes = []
    for item in effective_excluded:
        if not item:
            continue
        base = os.path.basename(item.rstrip(os.sep))
        if base:
            exclude_dir_names.add(base)
        # treat path-like values as prefixes too
        if os.sep in item or item.startswith("."):
            prefix = os.path.abspath(os.path.expanduser(item))
            try:
                prefix = str(pathlib.Path(prefix).resolve())
            except Exception:
                pass
            exclude_dir_prefixes.append(prefix)

    # 3) File-level excludes (exact and glob)
    exclude_file_globs = _split_csv(args.exclude_files)
    

    # 4) Extension sets (NBSP-safe)
    excluded_exts = set(_split_csv(args.exclude_extensions))
    allowed_exts = set(
        PROGRAMMING_EXTENSIONS
    )  # PROGRAMMING_EXTENSIONS may be overridden above

    # 5) Helpers used by tree and aggregation
    def should_skip_dir(dirpath: str) -> bool:
        """Return True if a directory should not be traversed (name match or path-prefix match)."""
        base = os.path.basename(dirpath.rstrip(os.sep))
        if base in exclude_dir_names:
            return True
        # Resolve to real path for prefix checks
        try:
            rp = str(pathlib.Path(dirpath).resolve())
        except Exception:
            rp = os.path.abspath(dirpath)
        return any(rp.startswith(pref) for pref in exclude_dir_prefixes)

    is_tree_excluded_file = make_is_tree_excluded_file(
        exclude_file_globs, excluded_exts, startpath
    )
    directory_tree = generate_directory_tree(
        startpath, should_skip_dir, is_tree_excluded_file
    )
    def should_skip_file(filepath: str) -> bool:
        """
        Return True if a file must be skipped by the aggregator:
        - extension denylist (-X)
        - not in allowed extension allowlist
        - matches --exclude-files (abs or project-relative)
        - legacy exclude set (EXCLUDE_FILES)
        """
        
        # extension-based exclusions
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext and ext in excluded_exts:
            return True
        if allowed_exts and ext and ext not in allowed_exts:
            return True
        # file globs and exact matches (abs + project-relative)
        if exclude_file_globs:
            abs_path = os.path.abspath(filepath)
            rel_path = os.path.relpath(filepath, startpath)
            for pat in exclude_file_globs:
                if (
                    fnmatch.fnmatch(abs_path, pat)
                    or fnmatch.fnmatch(rel_path, pat)
                    or abs_path == pat
                    or rel_path == pat
                ):
                    return True
        # legacy file set
        if os.path.basename(filepath) in EXCLUDE_FILES:
            return True
        return False

    # Two-pass approach:
    #  1) print the tree (with explicit [EXCLUDED] tags for user-excludes)
    #  2) walk again to aggregate file contents (pruning excluded dirs)
    aggregated_content = "Directory Tree:\n" + directory_tree + "\n\n"
    
    # Traverse the directory again to process files
    for root, dirs, files in os.walk(startpath):
        # NEW: prune directories in-place so os.walk does not descend into excluded dirs
        dirs[:] = [d for d in dirs if not should_skip_dir(os.path.join(root, d))]

        # Determine the relative path from the startpath
        rel_path = os.path.relpath(root, startpath)
        if rel_path == ".":
            rel_path = ""

        for file in files:
            file_path = os.path.join(root, file)

            # Skip by extensions / globs / legacy excluded files
            if should_skip_file(file_path):
                continue

            if not is_programming_file(file):
                continue

            if not should_include_file(file_path):
                continue 

            # Get relative path for headers
            rel_file_path = os.path.relpath(file_path, startpath)

            header = f"\n\n# ======================\n# File: {rel_file_path}\n# ======================\n\n"
            aggregated_content += header

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    aggregated_content += content
            except Exception as e:
                error_msg = f"\n# Error reading file {rel_file_path}: {e}\n"
                aggregated_content += error_msg


    if args.clipboard:
        # Copy the aggregated content to the clipboard
        success = copy_to_clipboard(aggregated_content)
        if success:
            print("Aggregated content has been copied to the clipboard successfully.")
        else:
            print("Failed to copy aggregated content to the clipboard.")
            sys.exit(1)
    else:
        # Write the aggregated content to the master file
        try:
            with open(FULL_CODE_FILE_NAME, "w", encoding="utf-8") as master_file:
                master_file.write(aggregated_content)
            print(
                f"Full code file '{FULL_CODE_FILE_NAME}' has been created successfully."
            )
        except Exception as e:
            print(f"Error writing to file '{FULL_CODE_FILE_NAME}': {e}")
            sys.exit(1)
    # after the big for-root,dirs,files loop that adds file contents:


if __name__ == "__main__":
    main()
