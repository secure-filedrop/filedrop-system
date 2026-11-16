"""Authentication values agreed in Issue #12; change them only through review."""

# Fixed absolute lifetime for the MVP; sessions are not extended on activity.
SESSION_LIFETIME_MINUTES = 30

# Cookie name read by the authenticated-user dependency. Cookie flags are set by
# the login flow (separate PR): HttpOnly, SameSite=Lax, host-only, Path=/, Secure.
SESSION_COOKIE_NAME = "filedrop_session"

# 32 random bytes (256 bits) encoded with URL-safe base64 and no padding.
SESSION_TOKEN_BYTES = 32

# Passwords are never truncated: out-of-range values are rejected explicitly.
# 15 follows NIST SP 800-63B-4 for passwords used as the only factor; the upper
# bound limits hashing input size.
PASSWORD_MIN_LENGTH = 15
PASSWORD_MAX_LENGTH = 1024

EMAIL_MAX_LENGTH = 320
