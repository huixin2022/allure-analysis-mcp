# MCP-Allure Usage Examples

This document provides practical examples of using MCP-Allure with both allure-report and allure-results directories.

## Architecture Overview

MCP-Allure now supports two input formats with automatic detection:

```
┌─────────────────────────────────────────┐
│         User Input Directory            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│    detect_allure_directory_type()       │
│    • Checks for data/suites.json        │
│    • Checks for *-result.json files     │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────┐   ┌──────────────────────┐
│ allure-report│   │  allure-results      │
│              │   │                      │
│ Uses:        │   │ Uses:                │
│ AllureSuite  │   │ AllureResultsDirect  │
│ Parser       │   │ Parser               │
└──────┬───────┘   └─────────┬────────────┘
       │                     │
       └─────────┬───────────┘
                 ▼
    ┌────────────────────────┐
    │  Unified JSON Output   │
    └────────────────────────┘
```

## Example 1: Parsing allure-report

### Directory Structure
```
allure-report/
├── data/
│   ├── suites.json           # ← Key file for report detection
│   ├── test-cases/
│   │   ├── {uuid1}.json
│   │   └── {uuid2}.json
│   └── ...
├── index.html
└── ...
```

### Python Code
```python
from allure_html import create_allure_parser

# Automatically detects it's a report
parser = create_allure_parser('allure-report')
result = parser.parse()

print(f"Found {len(result['test-suites'])} test suites")
```

### Output
```json
{
  "_metadata": {
    "source_type": "report",
    "source_path": "allure-report"
  },
  "test-suites": [
    {
      "name": "tests.test_login",
      "description": "",
      "status": "passed",
      "start": "1702123456789",
      "stop": "1702123459999",
      "test-cases": [...]
    }
  ]
}
```

## Example 2: Parsing allure-results

### Directory Structure
```
allure-results/
├── 12345678-result.json      # ← Key files for results detection
├── 23456789-result.json
├── 34567890-container.json
├── 45678901-container.json
├── screenshot-abc.png
└── ...
```

### Python Code
```python
from allure_html import create_allure_parser

# Automatically detects it's raw results
parser = create_allure_parser('allure-results')
result = parser.parse()

print(f"Found {len(result['test-suites'])} test suites")
```

### Output
```json
{
  "_metadata": {
    "source_type": "results",
    "source_path": "allure-results"
  },
  "test-suites": [
    {
      "name": "tests.test_api",
      "description": "",
      "status": "passed",
      "start": "1702123456789",
      "stop": "1702123459999",
      "test-cases": [...]
    }
  ]
}
```

## Example 3: Using the MCP Tool

When using through MCP (e.g., with Claude Desktop):

### With allure-report
```
User: "Analyze my test results in /path/to/allure-report"

AI calls: get_allure_report(results_dir="/path/to/allure-report")

Returns: { "_metadata": { "source_type": "report", ... }, ... }
```

### With allure-results
```
User: "Analyze my test results in /path/to/allure-results"

AI calls: get_allure_report(results_dir="/path/to/allure-results")

Returns: { "_metadata": { "source_type": "results", ... }, ... }
```

## Example 4: Filtering by Test Status

Both parsers support filtering by test status:

```python
from allure_html import create_allure_parser

# Only parse failed tests
parser = create_allure_parser('allure-results', testcase_status='failed')
result = parser.parse()

# Result will only contain test suites with failed test cases
for suite in result['test-suites']:
    for test_case in suite['test-cases']:
        assert test_case['status'] == 'failed'
```

## Example 5: Manual Parser Selection

If you want to explicitly choose the parser:

```python
from allure_html import AllureSuiteParser, AllureResultsDirectParser

# Explicitly use report parser
report_parser = AllureSuiteParser('allure-report')
report_result = report_parser.parse()

# Explicitly use results parser
results_parser = AllureResultsDirectParser('allure-results')
results_result = results_parser.parse()
```

## Example 6: Command-Line Testing

Use the included test script:

```bash
# Test with allure-report
python test_parser.py /path/to/allure-report

# Test with allure-results
python test_parser.py /path/to/allure-results
```

### Expected Output
```
============================================================
Testing parser with: /path/to/allure-results
============================================================

✓ Detected directory type: results
✓ Created parser: AllureResultsDirectParser
✓ Parsing successful!

Summary:
  - Test Suites: 3
  - Total Test Cases: 15

  Suite 1: tests.test_login
    Status: passed
    Test Cases: 5
      1. test_login_success - passed
      2. test_login_invalid_password - passed
      3. test_login_invalid_username - passed
      ... and 2 more

✓ Full result saved to: parsed_results.json
```

## Example 7: Error Handling

The parsers provide clear error messages:

```python
from allure_html import create_allure_parser

try:
    parser = create_allure_parser('/invalid/path')
except FileNotFoundError as e:
    print(f"Error: {e}")
    # Output: Error: Directory not found: /invalid/path

try:
    parser = create_allure_parser('/some/random/directory')
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Invalid directory: /some/random/directory
    #         Expected either:
    #           - allure-report (with data/suites.json)
    #           - allure-results (with *-result.json files)
```

## Key Differences: Report vs Results

### allure-report
- ✅ Pre-organized hierarchical structure
- ✅ Enriched with cross-references
- ✅ Human-readable HTML included
- ❌ Requires `allure generate` command
- ❌ Larger file size

### allure-results
- ✅ Immediate availability after test run
- ✅ Smaller file size
- ✅ Direct parsing without dependencies
- ❌ Flat structure (requires reconstruction)
- ❌ No HTML visualization

## Best Practices

1. **For CI/CD pipelines**: Use `allure-results` for immediate feedback
2. **For historical analysis**: Use `allure-report` for richer data
3. **For LLM analysis**: Both formats work equally well
4. **For debugging**: Use the test script to verify parsing before production use

## Integration with Testing Frameworks

### Pytest
```bash
# Generate allure-results
pytest --alluredir=allure-results

# Parse directly
python test_parser.py allure-results
```

### TestNG / JUnit
```bash
# Tests generate allure-results automatically
mvn test

# Parse directly
python test_parser.py target/allure-results
```

### Generating allure-report (optional)
```bash
# If you want the HTML report too
allure generate allure-results -o allure-report

# Can parse either format
python test_parser.py allure-report
# or
python test_parser.py allure-results
```

