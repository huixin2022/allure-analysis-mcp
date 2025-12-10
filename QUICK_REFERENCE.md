# Quick Reference: Using the Enhanced MCP-Allure Parser

## Installation

No additional dependencies required! The parser works with standard Python libraries.

## Basic Usage

### Option 1: Auto-Detection (Recommended)
```python
from allure_html import create_allure_parser

# Works with both allure-report and allure-results
parser = create_allure_parser('/path/to/directory')
result = parser.parse()
```

### Option 2: Explicit Parser Selection
```python
from allure_html import AllureSuiteParser, AllureResultsDirectParser

# For allure-report
report_parser = AllureSuiteParser('/path/to/allure-report')

# For allure-results
results_parser = AllureResultsDirectParser('/path/to/allure-results')
```

## Detection Function

```python
from allure_html import detect_allure_directory_type

# Returns "report" or "results"
dir_type = detect_allure_directory_type('/path/to/directory')
```

## Status Filtering

```python
# Only parse tests with specific status
parser = create_allure_parser('/path/to/directory', testcase_status='failed')
result = parser.parse()  # Only failed tests
```

Available statuses: `'passed'`, `'failed'`, `'broken'`, `'skipped'`

## Command-Line Testing

```bash
# Test the parser
python test_parser.py /path/to/allure-results

# Or with allure-report
python test_parser.py /path/to/allure-report
```

## MCP Tool Usage

The `get_allure_report` tool automatically detects the format:

```python
# Via MCP
result = await get_allure_report(results_dir="/path/to/directory")
```

Returns JSON with metadata:
```json
{
  "_metadata": {
    "source_type": "report|results",
    "source_path": "/path/to/directory"
  },
  "test-suites": [...]
}
```

## Output Structure

```python
{
    "_metadata": {
        "source_type": str,      # "report" or "results"
        "source_path": str       # Input path
    },
    "test-suites": [
        {
            "name": str,         # Suite name
            "description": str,  # Suite description
            "status": str,       # passed|failed|broken|skipped
            "start": str,        # Unix timestamp
            "stop": str,         # Unix timestamp
            "test-cases": [
                {
                    "name": str,        # Full test name
                    "title": str,       # Test title
                    "description": str, # Test description
                    "severity": str,    # critical|high|normal|low|trivial
                    "status": str,      # passed|failed|broken|skipped
                    "start": str,       # Unix timestamp
                    "stop": str,        # Unix timestamp
                    "labels": [],       # Allure labels
                    "parameters": [],   # Test parameters
                    "steps": [          # Test steps (recursive)
                        {
                            "name": str,
                            "title": str,
                            "status": str,
                            "start": str,
                            "stop": str,
                            "attachments": [],
                            "steps": []  # Nested steps
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Error Handling

```python
try:
    parser = create_allure_parser('/path/to/directory')
    result = parser.parse()
except FileNotFoundError:
    # Directory doesn't exist
    pass
except ValueError:
    # Not a valid allure directory
    pass
except Exception as e:
    # Other parsing errors
    pass
```

## Format Detection Logic

The parser detects format based on:

### allure-report
- ✅ Has `data/suites.json` file
- ✅ Has `data/test-cases/` directory
- ✅ May have HTML files

### allure-results
- ✅ Has `*-result.json` files
- ✅ May have `*-container.json` files
- ✅ May have attachment files

## Common Use Cases

### 1. CI/CD Pipeline (Real-time Analysis)
```python
# After test execution, parse results immediately
parser = create_allure_parser('allure-results')
result = parser.parse()

# Analyze failures
failed_suites = [s for s in result['test-suites'] if s['status'] == 'failed']
```

### 2. Historical Analysis
```python
# Parse generated HTML report
parser = create_allure_parser('allure-report')
result = parser.parse()

# Generate insights
total_tests = sum(len(s['test-cases']) for s in result['test-suites'])
```

### 3. Test Result Summary
```python
result = create_allure_parser('/path/to/directory').parse()

for suite in result['test-suites']:
    print(f"Suite: {suite['name']}")
    print(f"  Status: {suite['status']}")
    print(f"  Tests: {len(suite['test-cases'])}")
```

### 4. LLM Integration
```python
import json
from allure_html import create_allure_parser

# Parse and send to LLM
parser = create_allure_parser('/path/to/results')
result = parser.parse()

# Convert to LLM-friendly format
llm_input = json.dumps(result, indent=2, ensure_ascii=False)
# Send llm_input to your LLM for analysis
```

## Performance Tips

### For Large Result Sets
- Use status filtering to reduce data: `testcase_status='failed'`
- Parse specific suites if possible
- Consider streaming for very large datasets

### For Real-time Processing
- Use `allure-results` directly (no generation step)
- Parse incrementally as tests complete
- Cache parsed results if re-reading

## Troubleshooting

### "Directory not found"
- Check the path exists
- Use absolute paths to avoid confusion
- Verify file permissions

### "Invalid directory"
- Ensure directory contains either:
  - `data/suites.json` (for reports), or
  - `*-result.json` files (for results)
- Check you're pointing to the correct directory

### "No allure result files found"
- Verify tests actually ran
- Check test framework is configured for Allure output
- Look for `pytest --alluredir=...` or similar config

## Integration Examples

### Pytest
```bash
# Run tests and generate results
pytest --alluredir=allure-results tests/

# Parse immediately
python test_parser.py allure-results
```

### With MCP Server
```json
// In your MCP config
{
  "mcpServers": {
    "mcp-allure-server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "/path/to/mcp-allure/mcp-allure-server.py"
      ]
    }
  }
}
```

## API Reference

### Classes

- `AllureSuiteParser` - Parses allure-report directories
- `AllureResultsDirectParser` - Parses allure-results directories

### Functions

- `create_allure_parser(path, testcase_status=None)` - Factory function
- `detect_allure_directory_type(path)` - Format detection
- `parse_allure_suite(path, testcase_status=None)` - Convenience function

### MCP Tool

- `get_allure_report(results_dir: str)` - MCP tool for AI integration

## Further Reading

- `EXAMPLES.md` - Comprehensive usage examples
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `README.md` - Project overview



