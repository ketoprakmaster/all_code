# All Code Aggregator

Snapshot your project into one readable text file: a compact directory tree followed by file-by-file sections. Perfect for review packets, sharing with AI tools, or quick audits.
This is a focused PR on exclusion controls and clarity.

---

# What’s new in this PR (exclusions + clarity)

## Excluding directories via -e

- Previously: -e replaced the entire default excluded set (could accidentally re-include node_modules/.venv if you weren’t careful).
- Now: -e is additive by default; use --replace-exclude-dirs to replace the set intentionally.

## What the directory tree shows

- Previously: Only default-excluded dirs (like node_modules, .venv) were tagged [EXCLUDED]; individual files excluded by flags weren’t called out in the tree.
- Now: Files excluded via --exclude-files or -X are marked [EXCLUDED] in the tree so readers see why they’re missing from aggregation.

## Which directories can be excluded

- Previously: Exclusion was based on directory names supplied via -e and a fixed default name set.
- Now: -e accepts names or paths; you can exclude by name or path-prefix, and you can replace the defaults via --replace-exclude-dirs.

## File-level excludes

- Previously: No --exclude-files flag; exclusion was directory-based (plus extension denylist via -X).
- Now: --exclude-files supports comma-separated globs or exact paths (absolute or project-relative).

## Extension rules

- Previously: -x (allowlist) replaced the entire default set of allowed extension. Denylist precedence was not made clear.
- Now: Documented precedence: -X (denylist) overrides -x (allowlist). Clearer mental model.

## Output path convenience

- Previously: -o could point to a subpath if it already existed (not documented clearly).
- Now: Documented: -o accepts a subpath; create the folder first (e.g., -o tests/output.txt).

## Test runner portability (developer experience)

Previously: Tests invoked “python” directly (could call the wrong interpreter).
Now: Tests invoke sys.executable so they use the active interpreter (virtualenv-friendly).

> None of these change defaults; they’re opt-in immediately after the changes block for emphasis.

## Additional details of changes

- Files excluded due to a user-specified extension exclusion are marked as [EXCLUDED] in the tree overview and not traversed.
- Default excluded dirs (e.g. `node_modules`, `.venv`) are also marked once with `[EXCLUDED]` and not traversed.
- `--self` — include `all_code.py` in output (hidden by default to avoid self-inclusion).

## Installation

**From GitHub (original project)**

```bash
git clone https://github.com/foxalabs/all_code.git
cd all_code
pip install -e .
```

Install this PR from my fork (for reviewers)

```bash
pip install git+https://github.com/hamzadev3/all_code@feature/exclusions
```

# Usage

## Help

```bash
all-code --help
```

## Specify directory

```bash
all-code -d /path/to/project -o output.txt
```

## Copy to clipboard (macOS / Windows 10+)

```bash
all-code -d /path/to/project -c
```

## Output to a subfolder of directory

```bash
mkdir -p tests
all-code -d /path/to/project -o tests/output.txt
```

## Exclude by glob or exact path

```bash
all-code -d /path/to/project -o output.txt --exclude-files "foo/*.json,**/secrets.*"
```

## Replace all default exclusions entirely, then add your own exclusion

```bash
all-code -d /path/to/project -o output.txt --replace-exclude-dirs -e "my_generated,build-cache"
```

## Allowlist extensions (denylist wins if both set)

```bash
all-code -d /path/to/project -o output.txt -x ".py,.ts"
all-code -d /path/to/project -o output.txt -X ".py"
```

- `-x` allows extensions that may have been left out of the hardcoded set of accepted extensions
- `-X` denies them. In this case, -X takes priority

## Add more excluded dirs (keeps defaults)

```bash
all-code -d /path/to/project -o output.txt -e "secret,bar"
```

## Replace default excluded dirs entirely

```bash
all-code -d /path/to/project -o output.txt --replace-exclude-dirs -e "my_generated,build-cache"
```

## Include the tool itself

```bash
all-code -o output.txt --self
```

# Output format

```
Directory Tree:
project/
│   ├── src/
│   │   ├── main.py
│   ├── node_modules/ [EXCLUDED]

# ======================
# File: src/main.py
# ======================

print("hello world")
```

# Defaults & Notes

- Default excluded directories (not traversed): node_modules, .venv, venv, pycache, .git, dist, build, temp, old_files, flask_session.

- By default, only “programming-like” extensions are aggregated. Use -x to override or -X to deny specific extensions.

- Clipboard support is implemented for macOS (pbcopy) and Windows (clip).

# Testing

- Run the following command

```bash
python test_all_code.py
```

# Changelog (this PR)

- Directory tree now marks user-excluded files with [EXCLUDED].

- Allow file path exclusion in addition to file name exclusion.

- Add --exclude-files, --replace-exclude-dirs, --self.

- Make -e additive by default (use --replace-exclude-dirs to replace the entire directory).

- Clarity: -X (denylist) beats -x (allowlist).
