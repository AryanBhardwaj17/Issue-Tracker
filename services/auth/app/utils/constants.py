"""
Single source of truth for all magic values used across the auth service.

Every schema constraint, validation rule, cookie name, and user-facing error
message must be imported from here — never hard-coded inline. This makes
changes atomic and keeps the codebase easy to search.
"""

# ── Token types ───────────────────────────────────────────────────────────────
TOKEN_TYPE_BEARER = "bearer"
TOKEN_TYPE_ACCESS = "access"

# ── Pagination defaults ───────────────────────────────────────────────────────
DEFAULT_PAGE_SKIP = 0
DEFAULT_PAGE_LIMIT = 50

# ── User field validation ─────────────────────────────────────────────────────
NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 100

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d).{8,128}$"

ERR_WEAK_PASSWORD = (
    "Password must be at least 8 characters, include one uppercase letter and one number"
)

# ── Name generation ───────────────────────────────────────────────────────────
MAX_NAME_RETRIES = 5

# ── Cookie configuration ──────────────────────────────────────────────────────
REFRESH_TOKEN_COOKIE = "refresh_token"
AUTH_COOKIE_PATH = "/api/v1/auth"

# ── User-facing error messages ────────────────────────────────────────────────
ERR_INVALID_ACCESS_TOKEN = "Invalid or expired access token"
ERR_REFRESH_TOKEN_REQUIRED = "Refresh token required"
ERR_NAME_GENERATION_FAILED = "Could not generate a unique display name"
ERR_EMAIL_REGISTERED = "Email already registered"
ERR_INVALID_CREDENTIALS = "Invalid email or password"
ERR_USER_NOT_FOUND = "User not found"
ERR_USER_UNAVAILABLE = "User account unavailable"
ERR_INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"
ERR_WRONG_PASSWORD = "Current password is incorrect"
