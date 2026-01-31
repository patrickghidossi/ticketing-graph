"""Pydantic models for structured LLM outputs."""

from typing import List
from pydantic import BaseModel, Field


class ExtractedTicketInfo(BaseModel):
    """Structured output for ticket information extraction."""
    title: str = Field(
        description="A concise title for the JIRA ticket (max 100 chars)"
    )
    description: str = Field(
        description="Full description including error details and stack trace"
    )
    labels: List[str] = Field(
        description="Labels for the ticket (e.g., 'bug', 'mobile')"
    )


class CompletenessCheck(BaseModel):
    """Binary check for whether ticket info is complete."""
    is_complete: bool = Field(
        description="Whether all required fields (title, description, labels) are present and valid"
    )
    missing_fields: List[str] = Field(
        description="List of fields that are missing or invalid"
    )
    reasoning: str = Field(
        description="Explanation of the completeness assessment"
    )


class InferredFields(BaseModel):
    """Inferred values for missing ticket fields."""
    title: str = Field(
        description="Inferred or improved title for the ticket"
    )
    description: str = Field(
        description="Inferred or improved description"
    )
    labels: List[str] = Field(
        description="Inferred or default labels"
    )
    confidence: str = Field(
        description="Confidence level: 'high', 'medium', or 'low'"
    )
