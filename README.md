# MCP-Allure

MCP-Allure is a MCP server that reads Allure reports and returns them in LLM-friendly formats.

# Motivation

As AI and Large Language Models (LLMs) become increasingly integral to software development, there is a growing need to bridge the gap between traditional test reporting and AI-assisted analysis. Traditional Allure test report formats, while human-readable, aren't optimized for LLM consumption and processing.

MCP-Allure addresses this challenge by transforming Allure test reports into LLM-friendly formats. This transformation enables AI models to better understand, analyze, and provide insights about test results, making it easier to:

- Generate meaningful test summaries and insights
- Identify patterns in test failures
- Suggest potential fixes for failing tests
- Enable more effective AI-assisted debugging
- Facilitate automated test documentation generation

By optimizing test reports for LLM consumption, MCP-Allure helps development teams leverage the full potential of AI tools in their testing workflow, leading to more efficient and intelligent test analysis and maintenance.

# Problems Solved
- **Efficiency**: Traditional test reporting formats are not optimized for AI consumption, leading to inefficiencies in test analysis and maintenance.
- **Accuracy**: AI models may struggle with interpreting and analyzing test reports that are not in a format optimized for AI consumption.
- **Cost**: Converting test reports to LLM-friendly formats can be time-consuming and expensive.

# Key Features
- **Dual Format Support**: Parses both allure-report (HTML report) and allure-results (raw test output) with automatic detection
- **Direct Parsing**: No external dependencies - parses allure-results directly without needing Allure CLI
- **Smart Response Sizing**: Multiple output modes (summary/compact/detailed/full) to fit LLM context limits
- **LLM-Optimized**: Compact JSON output with automatic truncation for large test suites
- **Flexible Filtering**: Filter by test status (passed/failed/broken/skipped)
- **Conversion**: Converts Allure test reports into LLM-friendly formats
- **Efficiency**: Converts test reports efficiently with minimal token usage

# Installation 

To install mcp-repo2llm using uv:
```
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
        "/Users/crisschan/workspace/pyspace/mcp-allure/mcp-allure-server.py"
      ]
    }
  }
}
```
# Tool
##  get_allure_report

- **Automatically detects and parses** both Allure HTML reports and raw Allure results
- **Smart response sizing** to avoid exceeding LLM context limits

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `results_dir` | string | required | Path to allure-report or allure-results directory |
| `mode` | string | "summary" | Output mode: "summary", "compact", "detailed", or "full" |
| `status_filter` | string | null | Filter by status: "failed", "passed", "broken", "skipped" |

### Output Modes

#### 1. `summary` (Default - Most Compact) ⭐ Recommended
Returns only statistics and failed test list. Best for initial analysis.

```json
{
  "summary": {
    "total_suites": 5,
    "total_tests": 150,
    "passed": 142,
    "failed": 6,
    "broken": 2,
    "skipped": 0,
    "pass_rate": "94.7%"
  },
  "failed_tests": [
    {"suite": "tests.test_login", "name": "test_invalid_password", "status": "failed"}
  ],
  "suites": [
    {"name": "tests.test_login", "status": "passed", "test_count": 10}
  ],
  "_metadata": {"source_type": "results", "mode": "summary"}
}
```

#### 2. `compact` (Failures Focus)
Returns test cases without verbose details. Shows only failed tests by default.

```json
{
  "overview": {"total_passed": 142, "total_failed": 8, "showing": "failed_only"},
  "test-suites": [
    {
      "name": "tests.test_api",
      "status": "failed",
      "test-cases": [
        {"name": "test_create_user", "status": "failed", "failed_steps": ["POST /api/users"]}
      ]
    }
  ]
}
```

#### 3. `detailed` (With Steps)
Returns test cases with truncated step information (limited to 50 tests, 2-level step depth).

```json
{
  "note": "Showing 50 tests (max 50), step depth limited to 2",
  "test-suites": [
    {
      "name": "tests.test_login",
      "status": "passed",
      "test-cases": [
        {
          "name": "test_success",
          "title": "Test successful login",
          "status": "passed",
          "severity": "critical",
          "steps": [
            {"name": "Open login page", "status": "passed"},
            {"name": "Enter credentials", "status": "passed"}
          ]
        }
      ]
    }
  ]
}
```

#### 4. `full` (Everything - Use with Caution)
Returns all data. Automatically truncates if response exceeds 50KB.

### Usage Examples

#### Quick Overview (Recommended for First Call)
```
get_allure_report(results_dir="/path/to/allure-results")
```

#### Focus on Failures
```
get_allure_report(results_dir="/path/to/allure-results", mode="compact")
```

#### Detailed Failed Tests Only
```
get_allure_report(results_dir="/path/to/allure-results", mode="detailed", status_filter="failed")
```

#### All Passed Tests
```
get_allure_report(results_dir="/path/to/allure-results", mode="compact", status_filter="passed")
```

### Directory Support

The tool automatically detects:
- `allure-report` directory (generated HTML report with `data/suites.json`)
- `allure-results` directory (raw test output with `*-result.json` files)

### Command-Line Testing

```bash
# Test with summary mode (default)
python test_parser.py /path/to/allure-results

# The test script shows detailed output locally
```

The tool automatically detects which format you're using and applies the appropriate parsing method.
