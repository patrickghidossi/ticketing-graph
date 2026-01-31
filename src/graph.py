"""Graph construction for the Slack to JIRA ticketing workflow."""

from langgraph.graph import StateGraph, END

from .state import GraphState
from .nodes import (
    validate_source,
    extract_ticket_info,
    check_completeness,
    infer_missing_info,
    create_jira_ticket,
    verify_ticket,
    format_response,
    handle_invalid_source,
)


# Configuration
MAX_INFERENCE_ATTEMPTS = 2
MAX_JIRA_RETRIES = 5


def route_after_validation(state: GraphState) -> str:
    """
    Route based on source validation result.

    Args:
        state: The current graph state

    Returns:
        str: Next node name
    """
    if state["is_valid_source"]:
        print("---ROUTING: Valid source -> extract_ticket_info---")
        return "extract_ticket_info"
    else:
        print("---ROUTING: Invalid source -> handle_invalid_source---")
        return "handle_invalid_source"


def route_after_completeness(state: GraphState) -> str:
    """
    Route based on completeness check.

    Args:
        state: The current graph state

    Returns:
        str: Next node name
    """
    is_complete = state.get("is_complete", False)
    inference_attempts = state.get("inference_attempts", 0)

    if is_complete:
        print("---ROUTING: Complete -> create_jira_ticket---")
        return "create_jira_ticket"
    elif inference_attempts < MAX_INFERENCE_ATTEMPTS:
        print(f"---ROUTING: Incomplete (attempt {inference_attempts + 1}/{MAX_INFERENCE_ATTEMPTS}) -> infer_missing_info---")
        return "infer_missing_info"
    else:
        print("---ROUTING: Max inference attempts reached -> create_jira_ticket---")
        return "create_jira_ticket"


def route_after_jira_create(state: GraphState) -> str:
    """
    Route based on JIRA ticket creation result.

    Args:
        state: The current graph state

    Returns:
        str: Next node name
    """
    error = state.get("error_message")
    retry_count = state.get("retry_count", 0)

    if error is None and state.get("jira_ticket_id"):
        print("---ROUTING: Ticket created -> verify_ticket---")
        return "verify_ticket"
    elif retry_count < MAX_JIRA_RETRIES:
        print(f"---ROUTING: Failed (retry {retry_count}/{MAX_JIRA_RETRIES}) -> create_jira_ticket---")
        return "create_jira_ticket"
    else:
        print("---ROUTING: Max retries reached -> format_response---")
        return "format_response"


def build_graph() -> StateGraph:
    """
    Build and compile the ticketing graph.

    Returns:
        Compiled graph application
    """
    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("validate_source", validate_source)
    workflow.add_node("extract_ticket_info", extract_ticket_info)
    workflow.add_node("check_completeness", check_completeness)
    workflow.add_node("infer_missing_info", infer_missing_info)
    workflow.add_node("create_jira_ticket", create_jira_ticket)
    workflow.add_node("verify_ticket", verify_ticket)
    workflow.add_node("format_response", format_response)
    workflow.add_node("handle_invalid_source", handle_invalid_source)

    # Set entry point
    workflow.set_entry_point("validate_source")

    # Add conditional edge after validation (branching)
    workflow.add_conditional_edges(
        "validate_source",
        route_after_validation,
        {
            "extract_ticket_info": "extract_ticket_info",
            "handle_invalid_source": "handle_invalid_source",
        },
    )

    # Extract -> Check completeness
    workflow.add_edge("extract_ticket_info", "check_completeness")

    # Conditional edge after completeness check (branching + loop)
    workflow.add_conditional_edges(
        "check_completeness",
        route_after_completeness,
        {
            "create_jira_ticket": "create_jira_ticket",
            "infer_missing_info": "infer_missing_info",
        },
    )

    # Infer -> Check completeness (loop back)
    workflow.add_edge("infer_missing_info", "check_completeness")

    # Conditional edge after JIRA creation (retry loop)
    workflow.add_conditional_edges(
        "create_jira_ticket",
        route_after_jira_create,
        {
            "verify_ticket": "verify_ticket",
            "create_jira_ticket": "create_jira_ticket",  # Retry loop
            "format_response": "format_response",
        },
    )

    # Verify -> Format response
    workflow.add_edge("verify_ticket", "format_response")

    # Handle invalid source -> End
    workflow.add_edge("handle_invalid_source", END)

    # Format response -> End
    workflow.add_edge("format_response", END)

    # Compile and return
    return workflow.compile()


# Create the compiled graph
app = build_graph()
