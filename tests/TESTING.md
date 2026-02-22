# Testing Guide for Stocks Site

All tests in this project use the `pytest` framework for consistency and ease of use.

## How to Run Tests

- To run all tests:
  ```sh
  python -m pytest
  ```
- To run a specific test file:
  ```sh
  python -m pytest tests/test_search.py
  ```

## Writing New Tests
- Place all test files in the `tests/` directory.
- Name test files as `test_*.py`.
- Use plain functions prefixed with `test_` (no need for classes unless grouping is needed).
- Use `assert` statements for checks.
- For parameterized tests, use `@pytest.mark.parametrize`.
- See `test_search.py` and `test_historical.py` for examples.

## Example
```python
import pytest

def test_example():
    assert 1 + 1 == 2
```

## Notes
- Ensure your `.env` file contains a valid API key for tests that access the Financial Modeling Prep API.
- Tests should be fast and not depend on external state where possible.
