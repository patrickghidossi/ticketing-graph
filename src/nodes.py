"""Node functions for the Slack to JIRA ticketing graph."""

import time
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState, TicketInfo
from .models import ExtractedTicketInfo, CompletenessCheck, InferredFields
from .tools import get_slack_client, get_jira_client


# Initialize LLM with temperature=0 for deterministic outputs
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def validate_source(state: GraphState) -> Dict:
    """
    Validate that the message is from Datadog in the correct channel.

    Args:
        state: The current graph state

    Returns:
        Dict with updated state keys
    """
    print("---VALIDATE_SOURCE---")

    raw_message = state["raw_message"]
    channel = state["channel"]

    slack_client = get_slack_client()
    validation = slack_client.validate_message(raw_message, channel)

    print(f"  Source valid: {validation['source_valid']}")
    print(f"  Channel valid: {validation['channel_valid']}")
    print(f"  Overall valid: {validation['is_valid']}")

    return {
        "is_valid_source": validation["is_valid"],
        "source": validation["source"]
    }


def extract_ticket_info(state: GraphState) -> Dict:
    """
    Extract ticket information from the Datadog message using LLM.

    Args:
        state: The current graph state

    Returns:
        Dict with extracted ticket info
    """
    print("---EXTRACT_TICKET_INFO---")

    raw_message = state["raw_message"]

    # First, parse the message structure
    slack_client = get_slack_client()
    parsed = slack_client.parse_datadog_message(raw_message)

    # Use LLM to extract structured ticket info
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a ticket extraction assistant. Extract JIRA ticket information from Datadog error alerts.

Rules:
- Title should be concise (max 100 chars) and describe the error
- Description should include the full error message, relevant stack trace, and trigger condition
- Labels should always include 'bug' and 'mobile' as defaults, plus any other relevant labels

Format the description with clear sections:
## Error
[error message]

## Stack Trace
[relevant stack trace lines]

## Trigger Condition
[what triggered the alert]"""),
        ("human", """Extract ticket information from this Datadog alert:

Issue ID: {issue_id}
Error: {error_message}
Stack Trace:
{stack_trace}

Condition: {condition}

Raw Message:
{raw}""")
    ])

    structured_llm = llm.with_structured_output(ExtractedTicketInfo)
    chain = extraction_prompt | structured_llm

    result = chain.invoke({
        "issue_id": parsed["issue_id"],
        "error_message": parsed["error_message"],
        "stack_trace": parsed["stack_trace"],
        "condition": parsed["condition"],
        "raw": raw_message
    })

    ticket_info: TicketInfo = {
        "title": result.title,
        "description": result.description,
        "labels": result.labels
    }

    print(f"  Extracted title: {ticket_info['title'][:50]}...")
    print(f"  Labels: {ticket_info['labels']}")

    return {
        "ticket_info": ticket_info
    }


def check_completeness(state: GraphState) -> Dict:
    """
    Check if all required ticket fields are present and valid.

    Args:
        state: The current graph state

    Returns:
        Dict with completeness status
    """
    print("---CHECK_COMPLETENESS---")

    ticket_info = state["ticket_info"]

    if ticket_info is None:
        print("  No ticket info found")
        return {"is_complete": False}

    # Use LLM to validate completeness
    check_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a ticket validation assistant. Check if the ticket information is complete and valid.

Required fields:
- title: Must be non-empty and descriptive (not just "Error" or "Bug")
- description: Must contain meaningful error information
- labels: Must include at least 'bug' and 'mobile'

A ticket is complete if all required fields are present and meaningful."""),
        ("human", """Check if this ticket information is complete:

Title: {title}
Description: {description}
Labels: {labels}""")
    ])

    structured_llm = llm.with_structured_output(CompletenessCheck)
    chain = check_prompt | structured_llm

    result = chain.invoke({
        "title": ticket_info["title"],
        "description": ticket_info["description"],
        "labels": ticket_info["labels"]
    })

    print(f"  Is complete: {result.is_complete}")
    if not result.is_complete:
        print(f"  Missing fields: {result.missing_fields}")
        print(f"  Reasoning: {result.reasoning}")

    return {
        "is_complete": result.is_complete
    }


def infer_missing_info(state: GraphState) -> Dict:
    """
    Attempt to infer or fill in missing ticket information.

    Args:
        state: The current graph state

    Returns:
        Dict with updated ticket info and inference attempts
    """
    print("---INFER_MISSING_INFO---")

    ticket_info = state["ticket_info"]
    raw_message = state["raw_message"]
    inference_attempts = state.get("inference_attempts", 0) + 1

    print(f"  Inference attempt: {inference_attempts}")

    # Use LLM to infer missing fields
    infer_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a ticket completion assistant. Fill in or improve missing/weak ticket fields.

Rules:
- If title is weak, create a more descriptive one from the error message
- If description is incomplete, add structure and relevant details
- Labels must always include 'bug' and 'mobile' at minimum
- Be confident in your inferences based on the raw message"""),
        ("human", """Improve this ticket information:

Current Title: {title}
Current Description: {description}
Current Labels: {labels}

Raw Datadog Message:
{raw_message}

Provide improved values for all fields.""")
    ])

    structured_llm = llm.with_structured_output(InferredFields)
    chain = infer_prompt | structured_llm

    result = chain.invoke({
        "title": ticket_info["title"] if ticket_info else "",
        "description": ticket_info["description"] if ticket_info else "",
        "labels": ticket_info["labels"] if ticket_info else [],
        "raw_message": raw_message
    })

    updated_ticket_info: TicketInfo = {
        "title": result.title,
        "description": result.description,
        "labels": result.labels
    }

    print(f"  Inferred title: {updated_ticket_info['title'][:50]}...")
    print(f"  Confidence: {result.confidence}")

    return {
        "ticket_info": updated_ticket_info,
        "inference_attempts": inference_attempts
    }


def create_jira_ticket(state: GraphState) -> Dict:
    """
    Create a JIRA ticket with retry logic.

    Args:
        state: The current graph state

    Returns:
        Dict with JIRA ticket info or error
    """
    print("---CREATE_JIRA_TICKET---")

    ticket_info = state["ticket_info"]
    retry_count = state.get("retry_count", 0)

    jira_client = get_jira_client()

    # Exponential backoff delay if this is a retry
    if retry_count > 0:
        delay = 2 ** retry_count  # 2, 4, 8, 16, 32 seconds
        print(f"  Retry attempt {retry_count}, waiting {delay}s...")
        time.sleep(min(delay, 5))  # Cap at 5s for testing

    result = jira_client.create_ticket(
        project="MOBILE",
        title=ticket_info["title"],
        description=ticket_info["description"],
        labels=ticket_info["labels"],
        issue_type="Bug"
    )

    if result["success"]:
        print(f"  Created ticket: {result['ticket_key']}")
        return {
            "jira_ticket_id": result["ticket_key"],
            "jira_ticket_url": result["ticket_url"],
            "error_message": None,
            "retry_count": retry_count
        }
    else:
        print(f"  Failed: {result['error']}")
        return {
            "error_message": result["error"],
            "retry_count": retry_count + 1
        }


def verify_ticket(state: GraphState) -> Dict:
    """
    Verify that the JIRA ticket was created successfully.

    Args:
        state: The current graph state

    Returns:
        Dict with verification status
    """
    print("---VERIFY_TICKET---")

    ticket_key = state["jira_ticket_id"]

    jira_client = get_jira_client()
    result = jira_client.verify_ticket_exists(ticket_key)

    if result["exists"]:
        print(f"  Verified ticket exists: {ticket_key}")
        print(f"  Status: {result['ticket']['status']}")
        return {"error_message": None}
    else:
        print(f"  Verification failed: ticket not found")
        return {"error_message": "Ticket verification failed - ticket not found"}


def format_response(state: GraphState) -> Dict:
    """
    Format the final response message.

    Args:
        state: The current graph state

    Returns:
        Dict with formatted response
    """
    print("---FORMAT_RESPONSE---")

    ticket_key = state.get("jira_ticket_id")
    ticket_url = state.get("jira_ticket_url")
    ticket_info = state.get("ticket_info")
    error_message = state.get("error_message")

    if error_message:
        response = f"Failed to create ticket: {error_message}"
    elif ticket_key and ticket_url:
        response = f"""JIRA ticket created successfully!

Ticket: {ticket_key}
URL: {ticket_url}
Title: {ticket_info['title']}
Labels: {', '.join(ticket_info['labels'])}"""
    else:
        response = "Unknown error occurred during ticket creation."

    print(f"  Response generated")

    return {"final_response": response}


def handle_invalid_source(state: GraphState) -> Dict:
    """
    Handle messages from invalid sources.

    Args:
        state: The current graph state

    Returns:
        Dict with error response
    """
    print("---HANDLE_INVALID_SOURCE---")

    channel = state["channel"]
    source = state.get("source", "unknown")

    response = f"Message rejected: Source '{source}' from channel '{channel}' is not valid. Only Datadog messages from 'servicecore-mobile-errors' channel are processed."

    print(f"  Rejected message")

    return {
        "final_response": response,
        "error_message": "Invalid source"
    }
