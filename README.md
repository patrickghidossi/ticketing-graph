# Slack to JIRA Ticketing Graph

An intelligent, LLM-powered workflow that automatically converts Datadog error alerts from Slack into JIRA bug tickets. Built with LangGraph for stateful, agentic workflow orchestration.

## Overview

This system monitors Slack channels for Datadog error alerts and automatically:

1. **Validates** that messages are from Datadog in the correct channel
2. **Extracts** structured ticket information (title, description, labels) using GPT-4o-mini
3. **Infers** missing or incomplete fields with intelligent LLM reasoning
4. **Creates** JIRA tickets in the MOBILE project with automatic retry logic
5. **Verifies** ticket creation and returns a formatted response

## Architecture

The workflow is implemented as a LangGraph state machine with 8 nodes and conditional routing:

```
validate_source
    │
    ├─ INVALID → handle_invalid_source → END
    │
    └─ VALID → extract_ticket_info → check_completeness
                                          │
                    ┌─────────────────────┤
                    │                     │
                    ▼                     ▼
             infer_missing_info      create_jira_ticket
             (max 2 attempts)        (exponential backoff, max 5 retries)
                    │                     │
                    └──► loop back        ▼
                                     verify_ticket → format_response → END
```

### Key Features

- **Intelligent Extraction**: Uses GPT-4o-mini to parse Datadog alert formats and extract structured ticket data
- **Self-Healing**: Automatically infers missing fields with up to 2 LLM reasoning attempts
- **Resilient**: Exponential backoff retry logic for JIRA API failures (2s, 4s, 8s, 16s, max 5s cap)
- **Validated**: Comprehensive golden set with 16 test cases covering valid, invalid, and edge cases

## Installation

```bash
# Clone the repository
git clone https://github.com/patrickghidossi/ticketing-graph.git
cd ticketing-graph

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.sample .env
   ```

2. Configure your environment variables in `.env`:
   ```
   # Required: OpenAI API key for GPT-4o-mini
   OPENAI_API_KEY=your-openai-api-key

   # Optional: LangChain tracing
   LANGCHAIN_API_KEY=your-langchain-key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=ticketing-graph
   ```

### Message Requirements

For messages to be processed, they must:
- Originate from Datadog (contain markers like "Triggered:", "@issue.id:", "RUM errors")
- Be posted in the `servicecore-mobile-errors` channel
- Contain error information with an issue ID

## Usage

### Run with Sample Message

```bash
python main.py
```

This processes a sample Datadog error message and outputs the workflow execution, including the created JIRA ticket details.

### Run Evaluation Suite

Test the system against the golden set of 16 test cases:

```bash
# Run evaluation
python eval.py

# Verbose output
python eval.py -v

# Save results to JSON
python eval.py -s
```

Results are saved to `golden_set/eval_results_YYYYMMDD_HHMMSS.json`.

## Project Structure

```
ticketing-graph/
├── main.py                 # Entry point - runs the graph with sample message
├── eval.py                 # Evaluation framework for golden set testing
├── requirements.txt        # Python dependencies
├── .env.sample             # Environment variable template
├── src/
│   ├── state.py            # Graph state definitions (TypedDict)
│   ├── graph.py            # LangGraph workflow construction
│   ├── nodes.py            # Node implementations (8 nodes)
│   ├── models.py           # Pydantic models for LLM structured output
│   └── tools.py            # Slack/JIRA client implementations (currently mocked)
└── golden_set/
    └── test_inputs.py      # 16 test cases (7 valid, 3 invalid, 4 edge cases)
```

## Graph State

The workflow maintains state through a `GraphState` TypedDict:

| Field | Type | Description |
|-------|------|-------------|
| `raw_message` | str | Original Slack message |
| `channel` | str | Source channel name |
| `source` | str | Detected source ("datadog" or "unknown") |
| `is_valid_source` | bool | Validation result |
| `ticket_info` | TicketInfo | Extracted title, description, labels |
| `is_complete` | bool | Completeness check result |
| `inference_attempts` | int | LLM inference retry count |
| `jira_ticket_id` | str | Created JIRA ticket key |
| `jira_ticket_url` | str | JIRA ticket URL |
| `retry_count` | int | JIRA creation retry counter |
| `error_message` | str | Error details if any |
| `final_response` | str | Formatted output message |

## Dependencies

- **langgraph** - State graph/workflow framework
- **langchain** / **langchain-openai** - LLM integration
- **pydantic** - Data validation and structured output
- **python-dotenv** - Environment variable loading

## Production Deployment

The current implementation uses mock Slack and JIRA clients for local testing. For production:

1. Replace `MockSlackClient` in `src/tools.py` with the actual Slack SDK
2. Replace `MockJiraClient` with the JIRA REST API client
3. Set up Slack event subscriptions to listen for Datadog messages
4. Deploy as a service (AWS Lambda, Cloud Run, containerized service, etc.)

## Testing

The golden set in `golden_set/test_inputs.py` includes:

- **7 Valid Messages**: Standard errors (TypeError, NetworkError, SyntaxError, etc.)
- **3 Invalid Sources**: Non-Datadog messages, wrong channels, random bots
- **4 Edge Cases**: Minimal/long stack traces, special characters, recovered alerts

Evaluation metrics track:
- Source validation accuracy
- Ticket creation success
- Required field completeness (title, description, labels)
- Label accuracy (bug, mobile)
- Title quality (mentions error type)

## License

MIT
