import json
import os
from typing import Dict, List, Any
from collections import defaultdict

class AllureSuiteParser:
    def __init__(self, allure_report_dir: str,testcase_status=None):
        """Initialize parser with allure report directory path"""
        self.report_dir = allure_report_dir
        self.data_dir = os.path.join(allure_report_dir, 'data')
        self.suites_file = os.path.join(self.data_dir, 'suites.json')
        self.test_cases_dir = os.path.join(self.data_dir, 'test-cases')
        self.testcase_status=testcase_status
        
        if not os.path.exists(self.suites_file):
            raise FileNotFoundError(f"Suites file not found: {self.suites_file}")
    
    def parse(self) -> Dict[str, Any]:
        """Parse suites.json and test cases to return formatted data"""
        with open(self.suites_file, 'r', encoding='utf-8') as f:
            suites_data = json.load(f)
            
        result = {
            "test-suites": self._parse_suites(suites_data.get('children', []))
        }
        
        return result
    
    def _parse_suites(self, suites: List) -> List[Dict[str, Any]]:
        """Parse test suites information"""
        parsed_suites = []
        
        for suite in suites:
            # Extract suite information
            suite_info = {
                "name": suite.get('name', ''),
                # "title": suite.get('name', ''),  # Using name as title if not specified
                "description": "",  # No description in suites.json
                "status": "passed",  # Default status
                "start": "",  # Will be updated from test cases
                "stop": "",  # Will be updated from test cases
                "test-cases": []
            }
            
            # Process test cases in this suite
            if 'children' in suite:
                for child in suite['children']:
                    if 'children' in child:
                        # This is a sub-suite
                        sub_suites = self._parse_suites([child])
                        if sub_suites:
                            parsed_suites.extend(sub_suites)
                    else:
                        # This is a test case
                        test_case = self._parse_test_case(child)
                        if test_case:
                            suite_info['test-cases'].append(test_case)
                            
                            # Update suite timestamps
                            if test_case['start'] and (not suite_info['start'] or int(test_case['start']) < int(suite_info['start'])):
                                suite_info['start'] = test_case['start']
                            if test_case['stop'] and (not suite_info['stop'] or int(test_case['stop']) > int(suite_info['stop'])):
                                suite_info['stop'] = test_case['stop']
            
            if suite_info['test-cases']:
                parsed_suites.append(suite_info)
        
        return parsed_suites
    
    def _parse_test_case(self, case: Dict) -> Dict[str, Any]:
        """Parse test case information"""
        case_uid = case.get('uid', '')
        if not case_uid:
            return None
            
        case_file = os.path.join(self.test_cases_dir, f"{case_uid}.json")
        if not os.path.exists(case_file):
            return None
            
        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        # Check if testcase_status is None or matches the case status

        test_case = {
            "name": case_data.get('fullName', ''),
            "title": case_data.get('title', ''),
            "description": case_data.get('description', ''),
            "severity": self._get_severity(case_data.get('labels', [])),
            "status": case_data.get('status', ''),
            "start": str(case_data.get('time', {}).get('start', '')),
            "stop": str(case_data.get('time', {}).get('stop', '')),
            "labels": case_data.get('labels', []),
            "parameters": case_data.get('parameters', []),
            "steps": self._parse_steps(case_data.get('testStage', {}).get('steps', []))
        }
        
        return test_case
    
    def _get_severity(self, labels: List) -> str:
        """Extract severity from labels"""
        for label in labels:
            if label.get('name') == 'severity':
                return label.get('value', 'normal')
        return 'normal'
    
    def _parse_steps(self, steps: List) -> List[Dict[str, Any]]:
        """Parse test steps information"""
        parsed_steps = []
        
        for step in steps:
            step_info = {
                "name": step.get('name', ''),
                "title": step.get('title', ''),
                "status": step.get('status', ''),
                "start": str(step.get('time', {}).get('start', '')),
                "stop": str(step.get('time', {}).get('stop', '')),
                "attachments": step.get('attachments', []),
                "steps": self._parse_steps(step.get('steps', []))
            }
            parsed_steps.append(step_info)
            
        return parsed_steps

class AllureResultsDirectParser:
    """Parser for allure-results directory (raw test execution output)"""
    
    def __init__(self, allure_results_dir: str, testcase_status=None):
        """
        Initialize parser with allure-results directory path
        
        Args:
            allure_results_dir: Path to allure-results directory
            testcase_status: Optional filter for test case status (e.g., 'passed', 'failed')
        """
        self.results_dir = allure_results_dir
        self.testcase_status = testcase_status
        
        if not os.path.exists(allure_results_dir):
            raise FileNotFoundError(f"Results directory not found: {allure_results_dir}")
        
        # Verify it's actually a results directory
        result_files = [f for f in os.listdir(allure_results_dir) if f.endswith('-result.json')]
        if not result_files:
            raise ValueError(f"No allure result files found in: {allure_results_dir}")
    
    def parse(self) -> Dict[str, Any]:
        """Parse allure-results and return formatted data"""
        # Step 1: Read all result and container files
        results = self._read_result_files()
        containers = self._read_container_files()
        
        # Step 2: Build suite hierarchy
        suites = self._build_suite_hierarchy(results, containers)
        
        return {
            "test-suites": suites
        }
    
    def _read_result_files(self) -> List[Dict]:
        """Read all *-result.json files"""
        results = []
        for filename in os.listdir(self.results_dir):
            if filename.endswith('-result.json'):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results.append(data)
                except Exception as e:
                    print(f"Warning: Failed to read {filename}: {e}")
        return results
    
    def _read_container_files(self) -> Dict[str, Dict]:
        """Read all *-container.json files, indexed by uuid"""
        containers = {}
        for filename in os.listdir(self.results_dir):
            if filename.endswith('-container.json'):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        uuid = data.get('uuid')
                        if uuid:
                            containers[uuid] = data
                except Exception as e:
                    print(f"Warning: Failed to read {filename}: {e}")
        return containers
    
    def _build_suite_hierarchy(self, results: List[Dict], containers: Dict[str, Dict]) -> List[Dict]:
        """Build hierarchical suite structure from flat results"""
        # Group test cases by their suite name
        suite_map = defaultdict(list)
        
        for result in results:
            # Filter by status if specified
            status = result.get('status', '')
            if self.testcase_status and status != self.testcase_status:
                continue
            
            # Get suite name from labels
            suite_name = self._get_suite_name(result)
            
            # Parse test case
            test_case = self._parse_test_result(result)
            suite_map[suite_name].append(test_case)
        
        # Convert map to list of suites
        suites = []
        for suite_name, test_cases in suite_map.items():
            if not test_cases:
                continue
            
            # Calculate suite-level aggregations
            start_times = [int(tc['start']) for tc in test_cases if tc['start'] and str(tc['start']).isdigit()]
            stop_times = [int(tc['stop']) for tc in test_cases if tc['stop'] and str(tc['stop']).isdigit()]
            
            suite = {
                "name": suite_name,
                "description": "",
                "status": self._aggregate_status(test_cases),
                "start": str(min(start_times)) if start_times else "",
                "stop": str(max(stop_times)) if stop_times else "",
                "test-cases": test_cases
            }
            suites.append(suite)
        
        return suites
    
    def _get_suite_name(self, result: Dict) -> str:
        """Extract suite name from labels"""
        labels = result.get('labels', [])
        
        # Priority 1: Look for 'suite' label
        for label in labels:
            if label.get('name') == 'suite':
                return label.get('value', 'Default Suite')
        
        # Priority 2: Look for 'parentSuite' label
        for label in labels:
            if label.get('name') == 'parentSuite':
                return label.get('value', 'Default Suite')
        
        # Priority 3: Use package label
        for label in labels:
            if label.get('name') == 'package':
                return label.get('value', 'Default Suite')
        
        # Fallback: Extract from fullName (module path)
        full_name = result.get('fullName', '')
        if '.' in full_name:
            # Get the module/class part (everything except the last part)
            parts = full_name.split('.')
            return '.'.join(parts[:-1]) if len(parts) > 1 else 'Default Suite'
        
        return 'Default Suite'
    
    def _parse_test_result(self, result: Dict) -> Dict[str, Any]:
        """Convert result.json format to enriched test case format"""
        return {
            "name": result.get('fullName', ''),
            "title": result.get('name', ''),
            "description": result.get('description', ''),
            "severity": self._get_severity(result.get('labels', [])),
            "status": result.get('status', ''),
            "start": str(result.get('start', '')),
            "stop": str(result.get('stop', '')),
            "labels": result.get('labels', []),
            "parameters": result.get('parameters', []),
            "steps": self._parse_steps(result.get('steps', []))
        }
    
    def _get_severity(self, labels: List) -> str:
        """Extract severity from labels"""
        for label in labels:
            if label.get('name') == 'severity':
                return label.get('value', 'normal')
        return 'normal'
    
    def _parse_steps(self, steps: List) -> List[Dict[str, Any]]:
        """Parse test steps information recursively"""
        parsed_steps = []
        
        for step in steps:
            step_info = {
                "name": step.get('name', ''),
                "title": step.get('name', ''),  # allure-results don't have separate title field
                "status": step.get('status', ''),
                "start": str(step.get('start', '')),
                "stop": str(step.get('stop', '')),
                "attachments": step.get('attachments', []),
                "steps": self._parse_steps(step.get('steps', []))  # Recursive for nested steps
            }
            parsed_steps.append(step_info)
        
        return parsed_steps
    
    def _aggregate_status(self, test_cases: List[Dict]) -> str:
        """Determine suite status from test case statuses"""
        statuses = [tc.get('status', '') for tc in test_cases]
        
        if not statuses:
            return 'unknown'
        
        # Priority: failed > broken > skipped > passed
        if 'failed' in statuses:
            return 'failed'
        elif 'broken' in statuses:
            return 'broken'
        elif 'skipped' in statuses:
            return 'skipped'
        elif all(s == 'passed' for s in statuses):
            return 'passed'
        
        return 'unknown'


def detect_allure_directory_type(path: str) -> str:
    """
    Detect whether the path is an allure-report or allure-results directory
    
    Args:
        path: Directory path to check
    
    Returns:
        'report' for allure-report directory
        'results' for allure-results directory
        
    Raises:
        ValueError: If path is neither a valid report nor results directory
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not os.path.isdir(path):
        raise ValueError(f"Path is not a directory: {path}")
    
    # Check for allure-report structure (has data/suites.json)
    suites_file = os.path.join(path, 'data', 'suites.json')
    if os.path.exists(suites_file):
        return 'report'
    
    # Check for allure-results structure (has *-result.json files)
    files = os.listdir(path)
    has_result_files = any(f.endswith('-result.json') for f in files)
    if has_result_files:
        return 'results'
    
    raise ValueError(
        f"Invalid directory: {path}\n"
        "Expected either:\n"
        "  - allure-report (with data/suites.json)\n"
        "  - allure-results (with *-result.json files)"
    )


def create_allure_parser(path: str, testcase_status=None):
    """
    Factory function that auto-detects format and returns appropriate parser
    
    Args:
        path: Path to allure-results or allure-report directory
        testcase_status: Optional filter for test case status
    
    Returns:
        Parser instance (AllureSuiteParser or AllureResultsDirectParser)
    """
    dir_type = detect_allure_directory_type(path)
    
    if dir_type == 'report':
        return AllureSuiteParser(path, testcase_status)
    else:  # dir_type == 'results'
        return AllureResultsDirectParser(path, testcase_status)


def parse_allure_suite(report_dir: str, testcase_status=None) -> Dict[str, Any]:
    """
    Main function to parse allure suite results (auto-detects report or results)
    
    Args:
        report_dir: Path to allure-report or allure-results directory
        testcase_status: Optional filter for test case status
    
    Returns:
        Dictionary with test-suites data
    """
    parser = create_allure_parser(report_dir, testcase_status)
    return parser.parse()


# def save_to_json(result,output_path: str) -> None:
#     """
#     将解析结果保存为 JSON 文件
    
#     Args:
#         output_path: 输出 JSON 文件路径
#     """
   
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(result, f, ensure_ascii=False, indent=2)
#     print(f"结果已保存到: {output_path}")
# if __name__ == '__main__':
#     report_dir = '/Users/crisschan/workspace/pyspace/PyTestApiAuto/Report/html'
#     result = parse_allure_suite(report_dir)
#     save_to_json(result,'resulthtml.json')
#     print(json.dumps(result, indent=2, ensure_ascii=False))