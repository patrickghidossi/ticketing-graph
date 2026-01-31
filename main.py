"""Main entry point for the Slack to JIRA ticketing graph."""

import os
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables
load_dotenv()

# Set up environment (after loading .env)
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

from src.graph import app
from src.state import GraphState


# Sample Datadog message for testing
SAMPLE_DATADOG_MESSAGE = """Triggered: High number of errors in RUM on @issue.id:e1266418-913a-11ef-b48a-da7ad0900002
High number of errors on issue detected.

undefined is not an object (evaluating 'vm_r3.job.type') : TypeError: undefined is not an object (evaluating 'vm_r3.job.type')
  at executeTemplate @ capacitor://localhost/vendor.js:115793:15
  at refreshView @ capacitor://localhost/vendor.js:117360:22
  at detectChangesInView @ capacitor://localhost/vendor.js:117568:16
  at detectChangesInViewIfAttached @ capacitor://localhost/vendor.js:117530:22
  at detectChangesInEmbeddedViews @ capacitor://localhost/vendor.js:117490:36
  at refreshView @ capacitor://localhost/vendor.js:117387:33
  at detectChangesInView @ capacitor://localhost/vendor.js:117568:16
  at detectChangesInViewIfAttached @ capacitor://localhost/vendor.js:117530:22
  at detectChangesInComponent @ capacitor://localhost/vendor.js:117519:32
  at detectChangesInChildComponents @ capacitor://localhost/vendor.js:117580:29

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 20 during the last 5m."""


def run_graph(message: str, channel: str = "servicecore-mobile-errors") -> dict:
    """
    Run the ticketing graph with the given message.

    Args:
        message: The Slack message content
        channel: The Slack channel name

    Returns:
        Final state after graph execution
    """
    # Initial state
    initial_state: GraphState = {
        "raw_message": message,
        "channel": channel,
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

    print("=" * 60)
    print("STARTING TICKETING GRAPH")
    print("=" * 60)
    print(f"Channel: {channel}")
    print(f"Message preview: {message[:100]}...")
    print("=" * 60)

    # Run the graph
    final_state = None
    for output in app.stream(initial_state):
        for node_name, node_state in output.items():
            print(f"\nCompleted node: {node_name}")
        final_state = node_state

    print("\n" + "=" * 60)
    print("GRAPH EXECUTION COMPLETE")
    print("=" * 60)

    return final_state


def main():
    """Run the graph with the sample message."""
    result = run_graph(SAMPLE_DATADOG_MESSAGE)

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(result.get("final_response", "No response generated"))

    if result.get("jira_ticket_id"):
        print(f"\nTicket Details:")
        print(f"  ID: {result['jira_ticket_id']}")
        print(f"  URL: {result['jira_ticket_url']}")
        if result.get("ticket_info"):
            print(f"  Title: {result['ticket_info']['title']}")
            print(f"  Labels: {result['ticket_info']['labels']}")


if __name__ == "__main__":
    main()
