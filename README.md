# MCP-Allure

A Model Context Protocol (MCP) server for AI-powered test analysis. Transforms Allure test reports into LLM-friendly formats.

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io/)

---

## Key Features

### Dual Format Support
Parse both Allure report formats with **automatic detection**:

| Format | Directory | Description |
|--------|-----------|-------------|
| **HTML Report** | `allure-report/` | Generated HTML report (contains `data/suites.json`) |
| **Raw Results** | `allure-results/` | Raw test output (`*-result.json` files) |

No need to specify format — the tool automatically detects and parses correctly.

### Smart Context Management
Avoid LLM context length limits with **4 output modes**:

| Mode | Size | Best For |
|------|------|----------|
| `summary` | Smallest | Quick overview, initial analysis |
| `compact` | Small | Focus on failures only |
| `detailed` | Medium | Failed tests with step details |
| `full` | Largest | Complete data (auto-truncates if >50KB) |

---

## Installation

Choose the method that best fits your needs:

| Method | Best For | Pros |
|--------|----------|------|
| **CLI (Recommended)** | Production use | Faster startup, simpler config, no runtime downloads |
| **uv run** | Quick testing | No installation needed, always latest |

### Method 1: CLI Installation (Recommended)

Install the package once, then use the simple `mcp-allure` command.

**Step 1: Install**

```bash
# Clone or download the repository
cd /path/to/mcp-allure

# Install with uv (recommended)
uv pip install .

# Or with pip
pip install .
```

**Step 2: Configure MCP**

Add to your MCP settings (e.g., `~/.cursor/mcp.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "mcp-allure-server": {
      "command": "mcp-allure"
    }
  }
}
```

That's it! The `mcp-allure` command is now available.

### Method 2: Using `uv run` (No Installation)

Run directly without installing. Useful for testing or one-time use.

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
        "/path/to/mcp-allure/mcp_allure_server.py"
      ]
    }
  }
}
```

> **Note:** If you're behind a corporate proxy, you may need to add `"env": { "UV_NATIVE_TLS": "true" }` to handle SSL certificates.

---

## Tools Reference

### `analyze_allure_report`

Parse Allure reports with smart output sizing for LLM consumption.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `results_dir` | string | required | Path to `allure-report` or `allure-results` |
| `mode` | string | `"summary"` | Output mode: `summary`, `compact`, `detailed`, `full` |
| `status_filter` | string | `null` | Filter: `failed`, `passed`, `broken`, `skipped` |

**Output Modes Explained:**

#### 1. `summary` (Default) - Recommended First Call

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
analyze_allure_report(results_dir="/path/to/allure-results")

# Focus on failures
analyze_allure_report(results_dir="/path/to/allure-results", mode="compact")

# Detailed failed tests only
analyze_allure_report(results_dir="/path/to/allure-results", mode="detailed", status_filter="failed")

# All passed tests (verification)
analyze_allure_report(results_dir="/path/to/allure-results", mode="compact", status_filter="passed")
```

---

## Workflow Example

A typical workflow for analyzing test results:

### Step 1: Analyze Test Results

```python
# Get quick overview
analyze_allure_report(results_dir="./allure-results", mode="summary")
```

### Step 2: Investigate Failures

```python
# Get details on failed tests
analyze_allure_report(results_dir="./allure-results", mode="detailed", status_filter="failed")
```

### Step 3: Deep Dive into Specific Tests

```python
# Get full details for comprehensive analysis
analyze_allure_report(results_dir="./allure-results", mode="full", status_filter="failed")
```

---

## Why MCP-Allure?

| Problem | Solution |
|---------|----------|
| Allure reports aren't LLM-optimized | Transforms to structured JSON with smart sizing |
| Context length limits | Multiple output modes from summary to full |
| Large test suites overwhelm LLMs | Automatic truncation and filtering |

---

## License

MIT License - See [LICENSE](LICENSE) for details.
