import asyncio
from mcp.server import FastMCP
from allure_html import create_allure_parser, detect_allure_directory_type
import json
from typing import Optional, List, Dict, Any

MCP_SERVER_NAME = "mcp-allure-server"
mcp=FastMCP(MCP_SERVER_NAME)
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
async def get_allure_report(results_dir: str, mode: str = "summary", status_filter: str = None) -> str:
    """
    Read allure report or results directory and return json data.
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


if __name__ == '__main__':
    mcp.run(transport='stdio')