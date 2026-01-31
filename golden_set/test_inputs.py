"""Golden set test inputs for evaluation."""

# Each test case has:
# - id: unique identifier
# - message: the raw Slack message
# - channel: the Slack channel
# - expected: expected outcomes for evaluation

GOLDEN_SET = [
    # === VALID DATADOG MESSAGES ===
    {
        "id": "valid_001",
        "description": "Standard Datadog RUM error alert",
        "message": """Triggered: High number of errors in RUM on @issue.id:e1266418-913a-11ef-b48a-da7ad0900002
High number of errors on issue detected.

undefined is not an object (evaluating 'vm_r3.job.type') : TypeError: undefined is not an object (evaluating 'vm_r3.job.type')
  at executeTemplate @ capacitor://localhost/vendor.js:115793:15
  at refreshView @ capacitor://localhost/vendor.js:117360:22
  at detectChangesInView @ capacitor://localhost/vendor.js:117568:16

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 20 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
            "title_mentions_error": True,
        }
    },
    {
        "id": "valid_002",
        "description": "Datadog null reference error",
        "message": """Triggered: High number of errors in RUM on @issue.id:abc123-def456
High number of errors on issue detected.

Cannot read properties of null (reading 'map') : TypeError: Cannot read properties of null (reading 'map')
  at renderList @ capacitor://localhost/main.js:5423:12
  at updateView @ capacitor://localhost/main.js:5500:8

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 50 during the last 10m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "valid_003",
        "description": "Datadog network error",
        "message": """Triggered: High number of errors in RUM on @issue.id:net-error-789
Network request failed.

NetworkError: Failed to fetch : NetworkError: Failed to fetch
  at fetchData @ capacitor://localhost/api.js:234:10
  at loadUserProfile @ capacitor://localhost/profile.js:45:5

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 30 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "valid_004",
        "description": "Datadog async/promise error",
        "message": """Triggered: High number of errors in RUM on @issue.id:promise-rejection-001
Unhandled promise rejection detected.

Unhandled Promise Rejection: Request timeout after 30000ms : Error: Request timeout after 30000ms
  at createTimeout @ capacitor://localhost/utils.js:100:15
  at fetchWithTimeout @ capacitor://localhost/api.js:50:20

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 25 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "valid_005",
        "description": "Datadog memory error",
        "message": """Triggered: High number of errors in RUM on @issue.id:memory-001
Memory allocation failed.

RangeError: Maximum call stack size exceeded : RangeError: Maximum call stack size exceeded
  at recursiveFunction @ capacitor://localhost/utils.js:200:5
  at processData @ capacitor://localhost/data.js:150:10

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 15 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "valid_006",
        "description": "Datadog syntax error",
        "message": """Triggered: High number of errors in RUM on @issue.id:syntax-error-002
JavaScript syntax error detected.

SyntaxError: Unexpected token '<' : SyntaxError: Unexpected token '<'
  at parseJSON @ capacitor://localhost/utils.js:50:12
  at handleResponse @ capacitor://localhost/api.js:75:8

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 40 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "valid_007",
        "description": "Datadog authentication error",
        "message": """Triggered: High number of errors in RUM on @issue.id:auth-fail-003
Authentication failure detected.

Error: Token expired or invalid : Error: Token expired or invalid
  at validateToken @ capacitor://localhost/auth.js:120:10
  at checkAuth @ capacitor://localhost/middleware.js:30:5

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 100 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },

    # === INVALID SOURCE MESSAGES ===
    {
        "id": "invalid_001",
        "description": "Non-Datadog message in correct channel",
        "message": """Hey team, just a heads up that we're seeing some issues with the mobile app today.
Can someone take a look?

Thanks,
John""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": False,
            "ticket_created": False,
        }
    },
    {
        "id": "invalid_002",
        "description": "Datadog message in wrong channel",
        "message": """Triggered: High number of errors in RUM on @issue.id:wrong-channel-001
Error detected.

TypeError: Cannot read property 'id' of undefined
  at getUser @ capacitor://localhost/user.js:50:10

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 20 during the last 5m.""",
        "channel": "general",
        "expected": {
            "is_valid_source": False,
            "ticket_created": False,
        }
    },
    {
        "id": "invalid_003",
        "description": "Random bot message",
        "message": """Daily standup reminder!

Please post your updates in the thread below.
- What did you do yesterday?
- What are you doing today?
- Any blockers?""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": False,
            "ticket_created": False,
        }
    },

    # === EDGE CASES ===
    {
        "id": "edge_001",
        "description": "Datadog message with minimal stack trace",
        "message": """Triggered: High number of errors in RUM on @issue.id:minimal-001
Error occurred.

Error: Something went wrong

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 10 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "edge_002",
        "description": "Datadog message with very long stack trace",
        "message": """Triggered: High number of errors in RUM on @issue.id:long-stack-001
Deep error in component tree.

TypeError: Cannot access property of undefined : TypeError: Cannot access property of undefined
  at level1 @ capacitor://localhost/app.js:1:1
  at level2 @ capacitor://localhost/app.js:2:2
  at level3 @ capacitor://localhost/app.js:3:3
  at level4 @ capacitor://localhost/app.js:4:4
  at level5 @ capacitor://localhost/app.js:5:5
  at level6 @ capacitor://localhost/app.js:6:6
  at level7 @ capacitor://localhost/app.js:7:7
  at level8 @ capacitor://localhost/app.js:8:8
  at level9 @ capacitor://localhost/app.js:9:9
  at level10 @ capacitor://localhost/app.js:10:10
  at level11 @ capacitor://localhost/app.js:11:11
  at level12 @ capacitor://localhost/app.js:12:12
  at level13 @ capacitor://localhost/app.js:13:13
  at level14 @ capacitor://localhost/app.js:14:14
  at level15 @ capacitor://localhost/app.js:15:15
  at level16 @ capacitor://localhost/app.js:16:16
  at level17 @ capacitor://localhost/app.js:17:17
  at level18 @ capacitor://localhost/app.js:18:18
  at level19 @ capacitor://localhost/app.js:19:19
  at level20 @ capacitor://localhost/app.js:20:20
  at level21 @ capacitor://localhost/app.js:21:21
  at level22 @ capacitor://localhost/app.js:22:22
  at level23 @ capacitor://localhost/app.js:23:23
  at level24 @ capacitor://localhost/app.js:24:24
  at level25 @ capacitor://localhost/app.js:25:25

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 5 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "edge_003",
        "description": "Datadog message with special characters",
        "message": """Triggered: High number of errors in RUM on @issue.id:special-chars-001
Error with special characters.

Error: Invalid character '<script>alert("XSS")</script>' in input : Error: Invalid character
  at sanitize @ capacitor://localhost/utils.js:50:10
  at processInput @ capacitor://localhost/form.js:25:5

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile, grouped by @issue.id, was > 10 during the last 5m.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,
            "ticket_created": True,
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
    {
        "id": "edge_004",
        "description": "Recovered alert (not an error)",
        "message": """Recovered: High number of errors in RUM on @issue.id:recovered-001
The alert has recovered.

@slack-ServiceCore-servicecore-mobile-errors

The count of RUM errors matching service:mobile is now below the threshold.""",
        "channel": "servicecore-mobile-errors",
        "expected": {
            "is_valid_source": True,  # It's still from Datadog, but content differs
            "ticket_created": True,   # Should still create a ticket (or could be filtered)
            "has_title": True,
            "has_description": True,
            "has_labels": True,
            "labels_contain": ["bug", "mobile"],
        }
    },
]


def get_test_cases():
    """Return all test cases."""
    return GOLDEN_SET


def get_valid_cases():
    """Return only valid source test cases."""
    return [tc for tc in GOLDEN_SET if tc["expected"]["is_valid_source"]]


def get_invalid_cases():
    """Return only invalid source test cases."""
    return [tc for tc in GOLDEN_SET if not tc["expected"]["is_valid_source"]]
