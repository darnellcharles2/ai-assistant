"""Configuration defaults for the agent framework."""


# Step execution timeout in seconds
STEP_TIMEOUT_SECONDS = 300

# Maximum retry attempts for transient step failures
MAX_STEP_RETRIES = 3

# Initial backoff delay in seconds between retries
RETRY_BACKOFF_SECONDS = 1.0

# Planner reasoning depth
REASONING_DEPTH = 3

# Default estimated plan duration in seconds
DEFAULT_ESTIMATED_DURATION_SECONDS = 300

# Tools that require human approval before execution
RISKY_TOOLS = frozenset([
    'shell_execute',
    'file_delete',
    'email_send',
    'api_call_external',
])

# Tools automatically added to every plan
COMMON_TOOLS = frozenset([
    'memory',
    'logger',
])

# Exceptions treated as transient (eligible for retry)
TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)
