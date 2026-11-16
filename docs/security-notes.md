
Security Notes

This document lists security rules and concerns for the Secure File Drop System.

Security is part of the main design, not an afterthought.

- Password Security
- Never store plain-text passwords.
- Store only password hashes.
- Use a trusted password hashing method.
- Do not log passwords.
- Do not commit real passwords or secrets to GitHub.
- Session / Token Security

The MVP may use either sessions or JWT tokens, but the team should choose one clear approach before implementation.

Decision (Issue #12, approved): email login with opaque, PostgreSQL-backed
server-side sessions rather than JWT.

- Session tokens are generated server-side with 256 bits of randomness. Only
  their SHA-256 digest is stored, in `auth_sessions`; the raw token exists only
  in the browser cookie.
- Sessions have a fixed 30-minute absolute lifetime and can be revoked
  individually (logout) or all at once for a user (administrator action,
  future password change/reset). Each protected request checks the session and
  `users.is_active` server-side.
- Passwords are hashed with Argon2id (`pwdlib[argon2]`; 64 MiB, 3 passes, 4
  lanes). New passwords must be 15 to 1024 characters and are never truncated.
  Stored hashes with outdated parameters are reported for rehash on the next
  successful verification.
- The first administrator is created only by the explicit, interactive
  `scripts/create_initial_admin.py` command. There are no default credentials,
  seeded accounts, or public registration.
- Authentication failures return a generic response with `Cache-Control:
  no-store`; database or configuration failures deny access with a generic
  response. Tokens, passwords, and hashes are kept out of responses and logs.
- Cookie flags (HttpOnly, SameSite=Lax, host-only, Path=/, Secure in
  production), CSRF validation, login throttling, and login/logout audit events
  are part of the separate login/logout web-flow PR.

Rules:

- Validate the session or token before showing protected pages.
- Validate again before upload.
- Validate again before download.
- Do not rely only on the frontend to hide buttons or links.
- File Upload Security

Uploads should be validated.

Important checks:

- File size limits
- Allowed or blocked file types
- Safe stored filenames
- Unique stored filenames
- Prevent path traversal
- Do not trust the original filename
- Do not allow users to choose server paths

Dangerous example to prevent:

../../some-system-file
File Download Security

Downloads must check permissions first.

Rules:

- User must be authenticated.
- User must own the file or have permission.
- Deleted files should not be downloadable.
- Expired files should not be downloadable once expiration is implemented.
- Downloads should be logged.
- Audit Logging

The system should log important events:

- login_success
- login_failed
- file_uploaded
- file_downloaded
- file_deleted
- permission_granted
- permission_denied

Audit logs should include:

- user_id
- file_id when available
- action
- ip_address
- details
- created_at
- GitHub Safety

Do not commit:

- .env files with real secrets
- API keys
- AWS access keys
- Database passwords
- Private certificates
- Production config files
- Real customer files
- Uploaded test files containing private information

Use .gitignore to block sensitive local files.

Storage Security

For MVP local storage:

- Store uploaded files outside public static folders.
- Do not serve uploaded files directly by public path.
- Serve downloads through FastAPI after permission checks.

For future S3 storage:

- Avoid public buckets.
- Use private buckets.
- Use controlled download logic or signed URLs only when appropriate.
