# MCP-Allure

MCP-Allure is a MCP server that reads Allure reports and returns them in LLM-friendly formats, with **Jira integration** for creating and managing issues from test failures.

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
- **Jira Integration**: Create bugs, search issues, and link test failures directly to Jira

# Installation 

To install mcp-allure using uv:

```json
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
      ],
      "env": {
        "JIRA_BASE_URL": "https://yourcompany.atlassian.net",
        "JIRA_EMAIL": "[email protected]",
        "JIRA_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

## Jira Configuration (Optional)

To enable Jira integration, set the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `JIRA_BASE_URL` | Your Jira instance URL | `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Your Atlassian account email | `[email protected]` |
| `JIRA_API_TOKEN` | Your Jira API token | `ATATT3xFfGF0...` |

### Generating a Jira API Token

1. Go to [Atlassian Account API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Enter a label (e.g., "MCP Allure Integration")
4. Click **Create** and copy the token immediately

> **Note:** The Allure report tools work without Jira configuration. Jira tools will return an error message if not configured.
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

---

# Jira Integration Tools

The following tools are available when Jira is configured:

## jira_test_connection

Test Jira connection and verify API token authentication.

```
jira_test_connection()
```

**Returns:** Current user information and connection status.

## jira_get_issue

Get details of a specific Jira issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | Issue key (e.g., 'PROJ-123') |

```
jira_get_issue(issue_key="PROJ-123")
```

## jira_search

Search Jira issues using JQL (Jira Query Language).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `jql` | string | required | JQL query string |
| `max_results` | int | 20 | Maximum results (max 50) |

**Examples:**
```
jira_search(jql="project = PROJ AND status = Open")
jira_search(jql="labels = test-failure AND created >= -7d", max_results=50)
```

## jira_create_issue

Create a new Jira issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_key` | string | required | Project key (e.g., 'PROJ') |
| `summary` | string | required | Issue summary/title |
| `description` | string | required | Issue description |
| `issue_type` | string | "Bug" | Issue type (Bug, Task, Story, etc.) |
| `priority` | string | null | Priority (Highest, High, Medium, Low, Lowest) |
| `labels` | list | null | List of labels |

```
jira_create_issue(
    project_key="PROJ",
    summary="Login button not working",
    description="The login button does not respond on click",
    priority="High",
    labels=["ui", "login"]
)
```

## jira_create_bug_from_test_failure ⭐

Create a bug specifically formatted for test failures. Automatically adds the `test-failure` label.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_key` | string | required | Project key |
| `test_name` | string | required | Name of the failed test |
| `test_suite` | string | required | Name of the test suite |
| `error_message` | string | required | Error message or failure reason |
| `steps_to_reproduce` | string | null | Additional context |
| `priority` | string | "High" | Bug priority |
| `labels` | list | null | Additional labels |

```
jira_create_bug_from_test_failure(
    project_key="PROJ",
    test_name="test_login_invalid_password",
    test_suite="tests.test_authentication",
    error_message="AssertionError: Expected 401, got 500",
    priority="High"
)
```

## jira_add_comment

Add a comment to an existing issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | Issue key |
| `comment` | string | Yes | Comment text |

```
jira_add_comment(issue_key="PROJ-123", comment="Test passed after fix in commit abc123")
```

## jira_get_projects

Get list of accessible Jira projects.

```
jira_get_projects()
```

## jira_get_issue_types

Get available issue types for a project.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_key` | string | Yes | Project key |

```
jira_get_issue_types(project_key="PROJ")
```

---

# Workflow Example

Here's a typical workflow combining Allure reports with Jira:

1. **Analyze test results:**
   ```
   get_allure_report(results_dir="./allure-results", mode="summary")
   ```

2. **Get details on failed tests:**
   ```
   get_allure_report(results_dir="./allure-results", mode="detailed", status_filter="failed")
   ```

3. **Create bugs for failures:**
   ```
   jira_create_bug_from_test_failure(
       project_key="PROJ",
       test_name="test_checkout_flow",
       test_suite="tests.test_e2e",
       error_message="TimeoutError: Element not found after 30s",
       priority="High"
   )
   ```

4. **Search for existing related issues:**
   ```
   jira_search(jql="project = PROJ AND labels = test-failure AND status != Done")
   ```
