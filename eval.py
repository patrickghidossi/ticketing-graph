"""
Evaluation script for the Slack to JIRA ticketing graph.

Runs the golden set through the graph and reports results.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

from src.graph import app
from src.state import GraphState
from golden_set.test_inputs import get_test_cases


class EvalResult:
    """Result of a single evaluation."""

    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.checks: Dict[str, Dict] = {}
        self.passed = True
        self.error: str = None

    def add_check(self, name: str, expected: Any, actual: Any, passed: bool):
        """Add a check result."""
        self.checks[name] = {
            "expected": expected,
            "actual": actual,
            "passed": passed
        }
        if not passed:
            self.passed = False

    def set_error(self, error: str):
        """Set an error message."""
        self.error = error
        self.passed = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "description": self.description,
            "passed": self.passed,
            "checks": self.checks,
            "error": self.error
        }


def run_single_eval(test_case: Dict) -> EvalResult:
    """
    Run evaluation for a single test case.

    Args:
        test_case: Test case dictionary with message, channel, expected

    Returns:
        EvalResult with check results
    """
    result = EvalResult(test_case["id"], test_case["description"])

    try:
        # Prepare initial state
        initial_state: GraphState = {
            "raw_message": test_case["message"],
            "channel": test_case["channel"],
            "source": "",
            "is_valid_source": False,
            "ticket_info": None,
            "is_complete": False,
            "inference_attempts": 0,
            "jira_ticket_id": None,
            "jira_ticket_url": None,
            "retry_count": 0,
            "error_message": None,
            "final_response": "",
        }

        # Run graph and accumulate state
        # Each node only returns the keys it updates, so we need to merge
        accumulated_state = dict(initial_state)
        for output in app.stream(initial_state):
            for node_name, node_state in output.items():
                # Merge node output into accumulated state
                accumulated_state.update(node_state)

        final_state = accumulated_state

        if not final_state:
            result.set_error("Graph did not produce output")
            return result

        expected = test_case["expected"]

        # Check: is_valid_source
        if "is_valid_source" in expected:
            actual = final_state.get("is_valid_source", False)
            result.add_check(
                "is_valid_source",
                expected["is_valid_source"],
                actual,
                actual == expected["is_valid_source"]
            )

        # Check: ticket_created
        if "ticket_created" in expected:
            actual = final_state.get("jira_ticket_id") is not None
            result.add_check(
                "ticket_created",
                expected["ticket_created"],
                actual,
                actual == expected["ticket_created"]
            )

        # Check: has_title
        if "has_title" in expected:
            ticket_info = final_state.get("ticket_info")
            actual = ticket_info is not None and bool(ticket_info.get("title"))
            result.add_check(
                "has_title",
                expected["has_title"],
                actual,
                actual == expected["has_title"]
            )

        # Check: has_description
        if "has_description" in expected:
            ticket_info = final_state.get("ticket_info")
            actual = ticket_info is not None and bool(ticket_info.get("description"))
            result.add_check(
                "has_description",
                expected["has_description"],
                actual,
                actual == expected["has_description"]
            )

        # Check: has_labels
        if "has_labels" in expected:
            ticket_info = final_state.get("ticket_info")
            actual = ticket_info is not None and len(ticket_info.get("labels", [])) > 0
            result.add_check(
                "has_labels",
                expected["has_labels"],
                actual,
                actual == expected["has_labels"]
            )

        # Check: labels_contain
        if "labels_contain" in expected:
            ticket_info = final_state.get("ticket_info")
            actual_labels = ticket_info.get("labels", []) if ticket_info else []
            # Normalize to lowercase for comparison
            actual_labels_lower = [l.lower() for l in actual_labels]
            expected_labels = expected["labels_contain"]
            all_present = all(l.lower() in actual_labels_lower for l in expected_labels)
            result.add_check(
                "labels_contain",
                expected_labels,
                actual_labels,
                all_present
            )

        # Check: title_mentions_error (if applicable)
        if "title_mentions_error" in expected and expected["title_mentions_error"]:
            ticket_info = final_state.get("ticket_info")
            if ticket_info:
                title = ticket_info.get("title", "").lower()
                # Check if title contains error-related terms
                error_terms = ["error", "type", "undefined", "null", "exception", "fail"]
                mentions_error = any(term in title for term in error_terms)
                result.add_check(
                    "title_mentions_error",
                    True,
                    mentions_error,
                    mentions_error
                )

    except Exception as e:
        result.set_error(str(e))

    return result


def run_evaluation(verbose: bool = False) -> Dict:
    """
    Run full evaluation on all test cases.

    Args:
        verbose: Whether to print detailed output

    Returns:
        Dictionary with evaluation summary and results
    """
    test_cases = get_test_cases()
    results: List[EvalResult] = []

    print("=" * 70)
    print("RUNNING GOLDEN SET EVALUATION")
    print(f"Total test cases: {len(test_cases)}")
    print("=" * 70)

    for i, test_case in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] Running: {test_case['id']} - {test_case['description']}")

        result = run_single_eval(test_case)
        results.append(result)

        if result.passed:
            print(f"  ✓ PASSED")
        else:
            print(f"  ✗ FAILED")
            if result.error:
                print(f"    Error: {result.error}")
            for check_name, check_result in result.checks.items():
                if not check_result["passed"]:
                    print(f"    - {check_name}: expected {check_result['expected']}, got {check_result['actual']}")

    # Calculate summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    pass_rate = (passed / len(results)) * 100 if results else 0

    # Group by check type
    check_stats = {}
    for result in results:
        for check_name, check_result in result.checks.items():
            if check_name not in check_stats:
                check_stats[check_name] = {"passed": 0, "failed": 0}
            if check_result["passed"]:
                check_stats[check_name]["passed"] += 1
            else:
                check_stats[check_name]["failed"] += 1

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{pass_rate:.1f}%",
        "check_stats": check_stats,
        "results": [r.to_dict() for r in results]
    }

    # Print summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Pass Rate: {pass_rate:.1f}%")
    print("\nCheck Statistics:")
    for check_name, stats in check_stats.items():
        total = stats["passed"] + stats["failed"]
        rate = (stats["passed"] / total) * 100 if total > 0 else 0
        print(f"  {check_name}: {stats['passed']}/{total} ({rate:.0f}%)")

    if failed > 0:
        print("\nFailed Tests:")
        for result in results:
            if not result.passed:
                print(f"  - {result.test_id}: {result.description}")

    return summary


def save_results(summary: Dict, filename: str = None):
    """Save evaluation results to a JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"golden_set/eval_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run golden set evaluation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save", "-s", action="store_true", help="Save results to file")
    args = parser.parse_args()

    summary = run_evaluation(verbose=args.verbose)

    if args.save:
        save_results(summary)
