"""Graph state definition for the Slack to JIRA ticketing workflow."""

from typing import List, Optional
from typing_extensions import TypedDict


class TicketInfo(TypedDict):
    """Extracted ticket information from Datadog message."""
    title: str
    description: str
    labels: List[str]


class GraphState(TypedDict):
    """
    State for the Slack to JIRA ticketing graph.

    Attributes:
        raw_message: The original Slack message content
        channel: The Slack channel the message came from
        source: The source of the message (e.g., "datadog")
        is_valid_source: Whether the message is from a valid source/channel
        ticket_info: Extracted ticket information (title, description, labels)
        is_complete: Whether all required ticket fields are present
        inference_attempts: Number of attempts to infer missing fields
        jira_ticket_id: The created JIRA ticket ID
        jira_ticket_url: The URL to the created JIRA ticket
        retry_count: Number of JIRA API retry attempts
        error_message: Any error message from failed operations
        final_response: The formatted final response message
    """
    raw_message: str
    channel: str
    source: str
    is_valid_source: bool
    ticket_info: Optional[TicketInfo]
    is_complete: bool
    inference_attempts: int
    jira_ticket_id: Optional[str]
    jira_ticket_url: Optional[str]
    retry_count: int
    error_message: Optional[str]
    final_response: str
