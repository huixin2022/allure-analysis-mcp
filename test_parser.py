"""
Test script to demonstrate parsing both allure-report and allure-results
"""
import json
from allure_html import create_allure_parser, detect_allure_directory_type

def test_parser(directory_path: str):
    """
    Test the parser with a given directory
    
    Args:
        directory_path: Path to allure-report or allure-results directory
    """
    print(f"\n{'='*60}")
    print(f"Testing parser with: {directory_path}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Detect directory type
        dir_type = detect_allure_directory_type(directory_path)
        print(f"✓ Detected directory type: {dir_type}")
        
        # Step 2: Create appropriate parser
        parser = create_allure_parser(directory_path)
        print(f"✓ Created parser: {parser.__class__.__name__}")
        
        # Step 3: Parse the data
        result = parser.parse()
        print(f"✓ Parsing successful!")
        
        # Step 4: Display summary
        test_suites = result.get('test-suites', [])
        total_cases = sum(len(suite.get('test-cases', [])) for suite in test_suites)
        
        print(f"\nSummary:")
        print(f"  - Test Suites: {len(test_suites)}")
        print(f"  - Total Test Cases: {total_cases}")
        
        # Display suite details
        for i, suite in enumerate(test_suites, 1):
            suite_name = suite.get('name', 'Unknown')
            suite_status = suite.get('status', 'unknown')
            cases_count = len(suite.get('test-cases', []))
            print(f"\n  Suite {i}: {suite_name}")
            print(f"    Status: {suite_status}")
            print(f"    Test Cases: {cases_count}")
            
            # Show first few test cases
            for j, test_case in enumerate(suite.get('test-cases', [])[:3], 1):
                tc_name = test_case.get('title', test_case.get('name', 'Unknown'))
                tc_status = test_case.get('status', 'unknown')
                print(f"      {j}. {tc_name} - {tc_status}")
            
            if cases_count > 3:
                print(f"      ... and {cases_count - 3} more")
        
        # Optionally save to file
        output_file = f"parsed_{dir_type}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Full result saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_parser.py <path_to_allure_directory>")
        print("\nExamples:")
        print("  python test_parser.py /path/to/allure-results")
        print("  python test_parser.py /path/to/allure-report")
        sys.exit(1)
    
    directory = sys.argv[1]
    test_parser(directory)



