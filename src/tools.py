"""Mock tools for Slack and JIRA integration."""

import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SlackMessage:
    """Represents a Slack message."""
    content: str
    channel: str
    source: str  # e.g., "datadog", "user", "bot"
    timestamp: str = ""


@dataclass
class JiraTicket:
    """Represents a JIRA ticket."""
    id: str
    key: str
    url: str
    title: str
    description: str
    labels: List[str]
    project: str
    status: str = "Open"


class MockSlackClient:
    """Mock Slack client for testing."""

    def __init__(self):
        self.messages: List[SlackMessage] = []

    def validate_message(self, message: str, channel: str) -> Dict:
        """
        Validate if a message is from a valid source.

        Args:
            message: The message content
            channel: The channel name

        Returns:
            Dict with validation results
        """
        # Check if message contains Datadog indicators
        is_datadog = any([
            "Triggered:" in message,
            "@issue.id:" in message,
            "RUM errors" in message.lower(),
            "@slack-ServiceCore" in message
        ])

        # Check if channel matches
        is_valid_channel = channel == "servicecore-mobile-errors"

        return {
            "is_valid": is_datadog and is_valid_channel,
            "source": "datadog" if is_datadog else "unknown",
            "channel_valid": is_valid_channel,
            "source_valid": is_datadog
        }

    def parse_datadog_message(self, message: str) -> Dict:
        """
        Parse a Datadog message to extract key components.

        Args:
            message: The raw Datadog message

        Returns:
            Dict with parsed components
        """
        lines = message.strip().split('\n')

        # Extract issue ID from first line
        issue_id = ""
        if "@issue.id:" in lines[0]:
            issue_id = lines[0].split("@issue.id:")[-1].strip()

        # Find the error message (usually the main error description)
        error_message = ""
        stack_trace_lines = []
        condition_line = ""

        in_stack_trace = False
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith("at ") or line.startswith("  at "):
                in_stack_trace = True
                stack_trace_lines.append(line)
            elif "was >" in line or "during the last" in line:
                condition_line = line
            elif not in_stack_trace and not line.startswith("@slack-"):
                if not error_message:
                    error_message = line
                elif ":" in line and not stack_trace_lines:
                    # This might be the actual error (e.g., "TypeError: ...")
                    error_message = line

        return {
            "issue_id": issue_id,
            "error_message": error_message,
            "stack_trace": "\n".join(stack_trace_lines[:20]),  # Limit stack trace
            "condition": condition_line,
            "raw": message
        }


class MockJiraClient:
    """Mock JIRA client for testing."""

    def __init__(self, failure_rate: float = 0.0):
        """
        Initialize the mock JIRA client.

        Args:
            failure_rate: Probability of API failure (0.0 to 1.0) for testing retries
        """
        self.tickets: Dict[str, JiraTicket] = {}
        self.failure_rate = failure_rate
        self._ticket_counter = 1000

    def create_ticket(
        self,
        project: str,
        title: str,
        description: str,
        labels: List[str],
        issue_type: str = "Bug"
    ) -> Dict:
        """
        Create a JIRA ticket.

        Args:
            project: Project key (e.g., "MOBILE")
            title: Ticket title
            description: Ticket description
            labels: List of labels
            issue_type: Type of issue

        Returns:
            Dict with ticket info or error
        """
        # Simulate random failures for retry testing
        if random.random() < self.failure_rate:
            return {
                "success": False,
                "error": "JIRA API temporarily unavailable"
            }

        # Generate ticket ID and key
        self._ticket_counter += 1
        ticket_id = str(self._ticket_counter)
        ticket_key = f"{project}-{ticket_id}"
        ticket_url = f"https://jira.example.com/browse/{ticket_key}"

        # Create ticket object
        ticket = JiraTicket(
            id=ticket_id,
            key=ticket_key,
            url=ticket_url,
            title=title,
            description=description,
            labels=labels,
            project=project
        )

        self.tickets[ticket_key] = ticket

        return {
            "success": True,
            "ticket_id": ticket_id,
            "ticket_key": ticket_key,
            "ticket_url": ticket_url
        }

    def get_ticket(self, ticket_key: str) -> Optional[Dict]:
        """
        Get a ticket by its key.

        Args:
            ticket_key: The JIRA ticket key (e.g., "MOBILE-1001")

        Returns:
            Dict with ticket info or None if not found
        """
        ticket = self.tickets.get(ticket_key)
        if ticket:
            return {
                "id": ticket.id,
                "key": ticket.key,
                "url": ticket.url,
                "title": ticket.title,
                "description": ticket.description,
                "labels": ticket.labels,
                "project": ticket.project,
                "status": ticket.status
            }
        return None

    def verify_ticket_exists(self, ticket_key: str) -> Dict:
        """
        Verify that a ticket exists in JIRA.

        Args:
            ticket_key: The JIRA ticket key

        Returns:
            Dict with verification result
        """
        ticket = self.get_ticket(ticket_key)
        return {
            "exists": ticket is not None,
            "ticket": ticket
        }


# Global instances for use in nodes
slack_client = MockSlackClient()
jira_client = MockJiraClient()


def get_slack_client() -> MockSlackClient:
    """Get the mock Slack client instance."""
    return slack_client


def get_jira_client(failure_rate: float = 0.0) -> MockJiraClient:
    """Get the mock JIRA client instance."""
    global jira_client
    jira_client.failure_rate = failure_rate
    return jira_client
