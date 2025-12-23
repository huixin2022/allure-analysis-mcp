# MCP-Allure

A Model Context Protocol (MCP) server for AI-powered test analysis. Transforms Allure test reports into LLM-friendly formats and integrates with Jira for automated issue management.

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io/)

---

## ✨ Key Features

### 📊 Dual Format Support
Parse both Allure report formats with **automatic detection**:

| Format | Directory | Description |
|--------|-----------|-------------|
| **HTML Report** | `allure-report/` | Generated HTML report (contains `data/suites.json`) |
| **Raw Results** | `allure-results/` | Raw test output (`*-result.json` files) |

No need to specify format — the tool automatically detects and parses correctly.

### 🎯 Smart Context Management
Avoid LLM context length limits with **4 output modes**:

| Mode | Size | Best For |
|------|------|----------|
| `summary` ⭐ | Smallest | Quick overview, initial analysis |
| `compact` | Small | Focus on failures only |
| `detailed` | Medium | Failed tests with step details |
| `full` | Largest | Complete data (auto-truncates if >50KB) |

### 🔗 Jira Integration
Full Jira Cloud support with API token authentication:

| Operation | Description |
|-----------|-------------|
| **Test Connection** | Verify API token authentication |
| **Search Issues** | Query with JQL (Jira Query Language) |
| **Create Issues** | Create bugs, tasks, stories, etc. |
| **Create Bug from Test** | Auto-formatted bug from test failure |
| **Add Comments** | Comment on existing issues |
| **List Projects** | Get accessible projects |
| **Get Issue Types** | Available types per project |

---

## 🚀 Installation

### Basic Setup (Allure Only)

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
      ]
    }
  }
}
```

### Full Setup (Allure + Jira)

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

### Jira API Token Setup

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Enter a label (e.g., "MCP Allure")
4. Copy the token immediately (shown only once)

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `JIRA_BASE_URL` | Jira instance URL | `https://company.atlassian.net` |
| `JIRA_EMAIL` | Your Atlassian email | `[email protected]` |
| `JIRA_API_TOKEN` | Generated API token | `ATATT3xFfGF0...` |

> **Note:** Allure tools work without Jira configuration. Jira tools return helpful error messages if not configured.

---

## 📖 Tools Reference

### Allure Report Tool

#### `get_allure_report`

Parse Allure reports with smart output sizing for LLM consumption.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `results_dir` | string | required | Path to `allure-report` or `allure-results` |
| `mode` | string | `"summary"` | Output mode: `summary`, `compact`, `detailed`, `full` |
| `status_filter` | string | `null` | Filter: `failed`, `passed`, `broken`, `skipped` |

**Output Modes Explained:**

#### 1. `summary` (Default) ⭐ Recommended First Call

Most compact. Returns statistics and failed test list only.

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

#### 2. `compact` — Failures Focus

Shows only failed tests with minimal details.

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

#### 3. `detailed` — With Steps

Includes step information (limited to 50 tests, 2-level step depth).

```json
{
  "note": "Showing 50 tests (max 50), step depth limited to 2",
  "test-suites": [
    {
      "name": "tests.test_login",
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

#### 4. `full` — Everything (Use with Caution)

Complete data. Auto-truncates if response exceeds 50KB.

**Usage Examples:**

```python
# Quick overview (recommended first call)
get_allure_report(results_dir="/path/to/allure-results")

# Focus on failures
get_allure_report(results_dir="/path/to/allure-results", mode="compact")

# Detailed failed tests only
get_allure_report(results_dir="/path/to/allure-results", mode="detailed", status_filter="failed")

# All passed tests (verification)
get_allure_report(results_dir="/path/to/allure-results", mode="compact", status_filter="passed")
```

---

### Jira Tools

#### `jira_test_connection`

Verify Jira API token authentication.

```python
jira_test_connection()
```

**Returns:** User info and connection status.

---

#### `jira_search`

Search issues using JQL (Jira Query Language).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `jql` | string | required | JQL query string |
| `max_results` | int | `20` | Maximum results (max 50) |

```python
# Find open bugs in project
jira_search(jql="project = PROJ AND type = Bug AND status = Open")

# Find test failures from last 7 days
jira_search(jql="labels = test-failure AND created >= -7d", max_results=50)

# Find high priority issues assigned to me
jira_search(jql="assignee = currentUser() AND priority = High")
```

---

#### `jira_get_issue`

Get details of a specific issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | Issue key (e.g., `PROJ-123`) |

```python
jira_get_issue(issue_key="PROJ-123")
```

---

#### `jira_create_issue`

Create a new Jira issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_key` | string | required | Project key (e.g., `PROJ`) |
| `summary` | string | required | Issue title |
| `description` | string | required | Issue description |
| `issue_type` | string | `"Bug"` | Type: Bug, Task, Story, Epic, etc. |
| `priority` | string | `null` | Highest, High, Medium, Low, Lowest |
| `labels` | list | `null` | List of labels |

```python
jira_create_issue(
    project_key="PROJ",
    summary="Login button not responding",
    description="The login button does not respond to clicks on mobile devices",
    issue_type="Bug",
    priority="High",
    labels=["ui", "mobile", "login"]
)
```

---

#### `jira_create_bug_from_test_failure` ⭐

Create a well-formatted bug from test failure. Auto-adds `test-failure` label.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_key` | string | required | Project key |
| `test_name` | string | required | Failed test name |
| `test_suite` | string | required | Test suite name |
| `error_message` | string | required | Error/failure message |
| `steps_to_reproduce` | string | `null` | Additional context |
| `priority` | string | `"High"` | Bug priority |
| `labels` | list | `null` | Additional labels |

```python
jira_create_bug_from_test_failure(
    project_key="PROJ",
    test_name="test_checkout_payment",
    test_suite="tests.test_e2e.TestCheckout",
    error_message="AssertionError: Expected status 200, got 500\nResponse: Internal Server Error",
    steps_to_reproduce="1. Add item to cart\n2. Proceed to checkout\n3. Submit payment",
    priority="High",
    labels=["e2e", "payments"]
)
```

**Created Issue Format:**
- **Summary:** `[Test Failure] tests.test_e2e.TestCheckout: test_checkout_payment`
- **Labels:** `test-failure` + any additional labels
- **Description:** Structured with test info, error message, and steps

---

#### `jira_add_comment`

Add a comment to an existing issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | Issue key |
| `comment` | string | Yes | Comment text |

```python
jira_add_comment(
    issue_key="PROJ-123",
    comment="Test passed after fix in commit abc123. Closing issue."
)
```

---

#### `jira_get_projects`

List all accessible Jira projects.

```python
jira_get_projects()
```

---

#### `jira_get_issue_types`

Get available issue types for a project.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_key` | string | Yes | Project key |

```python
jira_get_issue_types(project_key="PROJ")
```

---

## 🔄 Workflow Example

A typical workflow combining Allure analysis with Jira integration:

### Step 1: Analyze Test Results

```python
# Get quick overview
get_allure_report(results_dir="./allure-results", mode="summary")
```

### Step 2: Investigate Failures

```python
# Get details on failed tests
get_allure_report(results_dir="./allure-results", mode="detailed", status_filter="failed")
```

### Step 3: Check Existing Issues

```python
# Search for existing bugs related to failures
jira_search(jql="project = PROJ AND labels = test-failure AND status != Done")
```

### Step 4: Create Bug for New Failure

```python
# Create bug from test failure
jira_create_bug_from_test_failure(
    project_key="PROJ",
    test_name="test_user_registration",
    test_suite="tests.test_auth",
    error_message="ValidationError: Email field required",
    priority="High"
)
```

### Step 5: Update Existing Issue

```python
# Add comment when test passes after fix
jira_add_comment(
    issue_key="PROJ-456",
    comment="✅ Test now passing after fix in PR #789"
)
```

---

## 🎯 Why MCP-Allure?

| Problem | Solution |
|---------|----------|
| Allure reports aren't LLM-optimized | Transforms to structured JSON with smart sizing |
| Context length limits | Multiple output modes from summary to full |
| Manual bug creation from failures | Auto-formatted Jira bugs with test details |
| Switching between tools | Single MCP server for analysis + issue management |
| Large test suites overwhelm LLMs | Automatic truncation and filtering |

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.
