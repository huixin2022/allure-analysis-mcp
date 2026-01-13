import asyncio
from mcp.server import FastMCP
from allure_html import create_allure_parser, detect_allure_directory_type
import json
from typing import Optional, List, Dict, Any
from jira_client import (
    JiraClient, JiraConfig, JiraAPIError, 
    get_jira_client, is_jira_configured
)

MCP_SERVER_NAME = "mcp-allure-server"
mcp = FastMCP(MCP_SERVER_NAME)
# mcp.start()


def _create_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary view with statistics only (most compact)"""
    test_suites = result.get('test-suites', [])
    
    total_tests = 0
    status_counts = {'passed': 0, 'failed': 0, 'broken': 0, 'skipped': 0, 'unknown': 0}
    failed_tests = []
    
    for suite in test_suites:
        for tc in suite.get('test-cases', []):
            total_tests += 1
            status = tc.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts['unknown'] += 1
            
            # Collect failed/broken tests for quick reference
            if status in ('failed', 'broken'):
                failed_tests.append({
                    'suite': suite.get('name', ''),
                    'name': tc.get('title', tc.get('name', '')),
                    'status': status
                })
    
    pass_rate = (status_counts['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    return {
        'summary': {
            'total_suites': len(test_suites),
            'total_tests': total_tests,
            'passed': status_counts['passed'],
            'failed': status_counts['failed'],
            'broken': status_counts['broken'],
            'skipped': status_counts['skipped'],
            'pass_rate': f"{pass_rate:.1f}%"
        },
        'failed_tests': failed_tests[:20],  # Limit to 20 failed tests
        'suites': [{'name': s.get('name', ''), 'status': s.get('status', ''), 'test_count': len(s.get('test-cases', []))} for s in test_suites]
    }


def _create_compact(result: Dict[str, Any], include_passed: bool = False) -> Dict[str, Any]:
    """Create a compact view focusing on failures with minimal details"""
    test_suites = result.get('test-suites', [])
    
    compact_suites = []
    total_passed = 0
    total_failed = 0
    
    for suite in test_suites:
        compact_cases = []
        for tc in suite.get('test-cases', []):
            status = tc.get('status', '')
            
            if status == 'passed':
                total_passed += 1
                if not include_passed:
                    continue  # Skip passed tests in compact mode
            else:
                total_failed += 1
            
            # Minimal test case info
            compact_case = {
                'name': tc.get('title', tc.get('name', '')),
                'status': status,
            }
            
            # Only add steps summary for non-passed tests
            if status != 'passed':
                steps = tc.get('steps', [])
                if steps:
                    # Only include failed steps
                    failed_steps = [s.get('name', '') for s in steps if s.get('status') != 'passed']
                    if failed_steps:
                        compact_case['failed_steps'] = failed_steps[:5]  # Limit to 5
            
            compact_cases.append(compact_case)
        
        if compact_cases:
            compact_suites.append({
                'name': suite.get('name', ''),
                'status': suite.get('status', ''),
                'test-cases': compact_cases
            })
    
    return {
        'overview': {
            'total_passed': total_passed,
            'total_failed': total_failed,
            'showing': 'failed_only' if not include_passed else 'all'
        },
        'test-suites': compact_suites
    }


def _create_detailed(result: Dict[str, Any], max_tests: int = 50, max_step_depth: int = 2) -> Dict[str, Any]:
    """Create detailed view with truncation limits"""
    test_suites = result.get('test-suites', [])
    
    def truncate_steps(steps: List[Dict], depth: int = 0) -> List[Dict]:
        """Recursively truncate steps to max depth"""
        if depth >= max_step_depth or not steps:
            return []
        
        truncated = []
        for step in steps[:10]:  # Max 10 steps per level
            truncated_step = {
                'name': step.get('name', ''),
                'status': step.get('status', ''),
            }
            if depth < max_step_depth - 1 and step.get('steps'):
                truncated_step['steps'] = truncate_steps(step.get('steps', []), depth + 1)
            truncated.append(truncated_step)
        
        if len(steps) > 10:
            truncated.append({'name': f'... and {len(steps) - 10} more steps', 'status': 'truncated'})
        
        return truncated
    
    detailed_suites = []
    test_count = 0
    
    for suite in test_suites:
        if test_count >= max_tests:
            break
            
        detailed_cases = []
        for tc in suite.get('test-cases', []):
            if test_count >= max_tests:
                break
            
            detailed_case = {
                'name': tc.get('name', ''),
                'title': tc.get('title', ''),
                'status': tc.get('status', ''),
                'severity': tc.get('severity', 'normal'),
            }
            
            # Include steps with truncation
            if tc.get('steps'):
                detailed_case['steps'] = truncate_steps(tc.get('steps', []))
            
            detailed_cases.append(detailed_case)
            test_count += 1
        
        if detailed_cases:
            detailed_suites.append({
                'name': suite.get('name', ''),
                'status': suite.get('status', ''),
                'test-cases': detailed_cases
            })
    
    return {
        'note': f'Showing {test_count} tests (max {max_tests}), step depth limited to {max_step_depth}',
        'test-suites': detailed_suites
    }


@mcp.tool()
async def analyze_allure_report(results_dir: str, mode: str = "summary", status_filter: str = None) -> str:
    """
    Analyze allure report or results directory and return structured JSON data.
    Automatically detects whether the input is an allure-report or allure-results directory.
    
    Args:
        results_dir: Path to allure-report (generated HTML report) or allure-results (raw test output)
        mode: Output mode - "summary" (default, most compact), "compact" (failures only), "detailed" (with steps), "full" (everything)
        status_filter: Optional filter - "failed", "passed", "broken", "skipped" (only applies to compact/detailed/full modes)
    
    Returns:
        JSON string with structured test suite data
    """
    try:
        # Auto-detect and create appropriate parser
        parser = create_allure_parser(results_dir, testcase_status=status_filter if mode != 'summary' else None)
        result = parser.parse()
        
        # Add metadata about source type
        dir_type = detect_allure_directory_type(results_dir)
        
        # Process based on mode
        if mode == "summary":
            output = _create_summary(result)
        elif mode == "compact":
            output = _create_compact(result, include_passed=(status_filter == 'passed'))
        elif mode == "detailed":
            output = _create_detailed(result)
        elif mode == "full":
            # Full mode - but still apply some limits
            output = result
            if len(json.dumps(output)) > 50000:  # If too large, warn and truncate
                output = _create_detailed(result, max_tests=100, max_step_depth=3)
                output['warning'] = 'Response truncated due to size. Use mode="compact" or mode="summary" for large test suites.'
        else:
            output = _create_summary(result)  # Default to summary
        
        output['_metadata'] = {
            'source_type': dir_type,
            'source_path': results_dir,
            'mode': mode,
            'status_filter': status_filter
        }
        
        # Use compact JSON (no indent) to reduce size
        return json.dumps(output, ensure_ascii=False, separators=(',', ':'))
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "path": results_dir
        })


# ==================== Jira Integration Tools ====================

def _check_jira_configured() -> Optional[str]:
    """Check if Jira is configured, return error message if not."""
    if not is_jira_configured():
        return json.dumps({
            "error": "Jira not configured",
            "message": "Please set environment variables: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN"
        })
    return None


@mcp.tool()
async def jira_test_connection() -> str:
    """
    Test Jira connection and return current user info.
    Verifies that the API token authentication is working correctly.
    
    Returns:
        JSON with current user information or error message
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        user_info = client.test_connection()
        return json.dumps({
            "status": "connected",
            "user": {
                "displayName": user_info.get('displayName'),
                "emailAddress": user_info.get('emailAddress'),
                "accountId": user_info.get('accountId'),
                "active": user_info.get('active')
            },
            "jira_url": client.config.base_url
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_get_issue(issue_key: str) -> str:
    """
    Get Jira issue details by key.
    
    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
    
    Returns:
        JSON with issue details including summary, status, description, assignee, etc.
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        issue = client.get_issue(issue_key)
        
        fields = issue.get('fields', {})
        return json.dumps({
            "key": issue.get('key'),
            "summary": fields.get('summary'),
            "status": fields.get('status', {}).get('name'),
            "priority": fields.get('priority', {}).get('name'),
            "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
            "reporter": fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
            "created": fields.get('created'),
            "updated": fields.get('updated'),
            "labels": fields.get('labels', []),
            "issue_type": fields.get('issuetype', {}).get('name'),
            "project": fields.get('project', {}).get('key'),
            "url": f"{client.config.base_url}/browse/{issue.get('key')}"
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_search(jql: str, max_results: int = 20) -> str:
    """
    Search Jira issues using JQL (Jira Query Language).
    
    Args:
        jql: JQL query string (e.g., 'project = PROJ AND status = Open')
        max_results: Maximum number of results to return (default 20, max 50)
    
    Returns:
        JSON with list of matching issues
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        max_results = min(max_results, 50)  # Cap at 50
        
        result = client.search_issues(jql, max_results=max_results)
        
        issues = []
        for issue in result.get('issues', []):
            fields = issue.get('fields', {})
            issues.append({
                "key": issue.get('key'),
                "summary": fields.get('summary'),
                "status": fields.get('status', {}).get('name'),
                "priority": fields.get('priority', {}).get('name'),
                "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                "updated": fields.get('updated')
            })
        
        return json.dumps({
            "total": result.get('total'),
            "returned": len(issues),
            "issues": issues
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Bug",
    priority: str = None,
    labels: List[str] = None
) -> str:
    """
    Create a new Jira issue.
    
    Args:
        project_key: Project key (e.g., 'PROJ')
        summary: Issue summary/title
        description: Issue description text
        issue_type: Issue type name (default 'Bug'). Common types: Bug, Task, Story, Epic
        priority: Priority name (e.g., 'Highest', 'High', 'Medium', 'Low', 'Lowest')
        labels: List of labels to add (optional)
    
    Returns:
        JSON with created issue key and URL
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        result = client.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            labels=labels
        )
        
        issue_key = result.get('key')
        return json.dumps({
            "status": "created",
            "key": issue_key,
            "id": result.get('id'),
            "url": f"{client.config.base_url}/browse/{issue_key}"
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_add_comment(issue_key: str, comment: str) -> str:
    """
    Add a comment to a Jira issue.
    
    Args:
        issue_key: Issue key (e.g., 'PROJ-123')
        comment: Comment text to add
    
    Returns:
        JSON with status and comment ID
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        result = client.add_comment(issue_key, comment)
        
        return json.dumps({
            "status": "comment_added",
            "issue_key": issue_key,
            "comment_id": result.get('id'),
            "created": result.get('created')
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_create_bug_from_test_failure(
    project_key: str,
    test_name: str,
    test_suite: str,
    error_message: str,
    steps_to_reproduce: str = None,
    priority: str = "High",
    labels: List[str] = None
) -> str:
    """
    Create a Jira bug from a test failure. Formats the issue with test information.
    
    Args:
        project_key: Project key (e.g., 'PROJ')
        test_name: Name of the failed test
        test_suite: Name of the test suite
        error_message: Error message or failure reason
        steps_to_reproduce: Optional steps or context for reproduction
        priority: Bug priority (default 'High')
        labels: Additional labels (will add 'test-failure' automatically)
    
    Returns:
        JSON with created issue key and URL
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        
        # Build descriptive summary
        summary = f"[Test Failure] {test_suite}: {test_name}"
        if len(summary) > 255:
            summary = summary[:252] + "..."
        
        # Build detailed description
        description_parts = [
            f"**Test Suite:** {test_suite}",
            f"**Test Name:** {test_name}",
            "",
            "**Error Message:**",
            f"```\n{error_message}\n```"
        ]
        
        if steps_to_reproduce:
            description_parts.extend([
                "",
                "**Steps/Context:**",
                steps_to_reproduce
            ])
        
        description_parts.extend([
            "",
            "---",
            "_This bug was created from automated test failure._"
        ])
        
        description = "\n".join(description_parts)
        
        # Ensure 'test-failure' label is included
        all_labels = list(labels) if labels else []
        if 'test-failure' not in all_labels:
            all_labels.append('test-failure')
        
        result = client.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type="Bug",
            priority=priority,
            labels=all_labels
        )
        
        issue_key = result.get('key')
        return json.dumps({
            "status": "bug_created",
            "key": issue_key,
            "id": result.get('id'),
            "url": f"{client.config.base_url}/browse/{issue_key}",
            "summary": summary
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_get_projects() -> str:
    """
    Get list of accessible Jira projects.
    
    Returns:
        JSON with list of projects including key, name, and project type
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        projects = client.get_projects()
        
        project_list = [{
            "key": p.get('key'),
            "name": p.get('name'),
            "projectTypeKey": p.get('projectTypeKey')
        } for p in projects]
        
        return json.dumps({
            "total": len(project_list),
            "projects": project_list
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def jira_get_issue_types(project_key: str) -> str:
    """
    Get available issue types for a Jira project.
    
    Args:
        project_key: Project key (e.g., 'PROJ')
    
    Returns:
        JSON with list of available issue types
    """
    if error := _check_jira_configured():
        return error
    
    try:
        client = get_jira_client()
        issue_types = client.get_issue_types(project_key)
        
        types_list = [{
            "name": it.get('name'),
            "description": it.get('description'),
            "subtask": it.get('subtask', False)
        } for it in issue_types]
        
        return json.dumps({
            "project": project_key,
            "issue_types": types_list
        }, ensure_ascii=False)
    except JiraAPIError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == '__main__':
    mcp.run(transport='stdio')