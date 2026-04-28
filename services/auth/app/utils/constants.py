"""
Single source of truth for all magic values used across the auth service.

Every schema constraint, validation rule, cookie name, and user-facing error
message must be imported from here — never hard-coded inline. This makes
changes atomic and keeps the codebase easy to search.
"""

# ── User-facing error messages ────────────────────────────────────────────────

ERR_EMAIL_REGISTERED = "Email already registered"
ERR_NAME_GENERATION_FAILED = "Could not generate a unique display name"