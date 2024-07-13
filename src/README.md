
# Tests
The `pytest` testing framework was used in this project.  The tests are located in the `tests` directory.

There are tests for each module in the `tests` directory. The command used to run the tests:

```bash
 python -m pytest -m "not slow" -vv -s -rA  --lf -W error::RuntimeWarning tests/test_power_code.py
```
The interactive nature of VS Code's test runner was also used and extremely useful.  Pass/Fails are easily recognizable. Clicking on a fail brings up the error information.  Individual tests can be stepped through using the debugger.

## LEARN: markers are useful
- -m "not slow" - skips the slow tests.
    - -m is a known to pytest as a marker. It is useful for letting Pytest know which tests to include/exclude.
### Example
- Define a marker in the pytest.ini file:
    ```ini
    [pytest]
    markers =
        slow: marks tests as slow (deselect with '-m "not slow"')
    ```
- Use the marker in the test file:
    ```python
    @pytest.mark.slow
    def test_slow():
        pass
    ```
- Let Pytest know about the marker by running the command with the -m flag:
    ```bash
    python -m pytest -m "not slow" -vv -s -rA  --lf -W error::RuntimeWarning tests/test_power_code.py
    ```
### Example
`skip` is a built-in marker in pytest. It is used to skip tests.  This became useful when working with Async mocking.  Async mocking would work and then it wouldn't. This got very frustrating.  In the case of the `skip` marker, the step to add it to pytest.ini is not necessary.

## LEARN: pytest-cov aids in understanding and evolving test coverage
- pytest-cov is a plugin for pytest that generates coverage reports.
```bash
pytest --cov=src --cov-report=html
```

# General Helpful Information

## LEARN: Converting between WSL and Windows paths

```bash
# From the VS Code terminal in WSL, find out the current WSL directory path
pwd
# Use that path to convert to a Windows path, e.g.:
wspath -w /root/project
# Returned
\\wsl.localhost\Ubuntu\root\projects
# Which can then be used in Windows filemanager to locate the directory.
```
