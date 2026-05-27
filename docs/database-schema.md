
Database Schema

This document defines the planned database tables for the Secure File Drop System.

The MVP should start with the minimum needed fields, but the schema should leave room for teams, permissions, expiration dates, and future S3 support.

users

Stores application users.

- id
- email
- password_hash
- role
- is_active
- created_at

Notes:

role may start with simple values such as admin and user.
is_active allows an account to be disabled without deleting it.
Passwords must never be stored as plain text.
teams

Stores team/group names for future team-based access.

id
name
created_at

MVP status:

Future feature.
Can be added early if it does not slow down the MVP.
team_members

Connects users to teams.

- id
- user_id
- team_id

MVP status:

- Future feature.
- Used later for team file permissions.
- files

Stores metadata about uploaded files.

- id
- owner_user_id
- original_filename
- stored_filename
- storage_key
- storage_type
- file_size
- content_type
- expires_at
- is_deleted
- created_at

Notes:

- original_filename is the user-facing file name.
- stored_filename is the safe unique filename used on disk.
- storage_key identifies where the file is stored.
- storage_type can be local for MVP and s3 later.
- expires_at supports future time/date-gated files.
- is_deleted allows soft deletion.
- file_permissions

Stores file access rules.

- id
- file_id
- user_id nullable
- team_id nullable
- permission_type
- created_at

Notes:

- user_id is used for direct user permissions.
- team_id is used for future team permissions.
- permission_type may include values such as owner, view, download, or admin.
- audit_logs

Stores important user and system activity.

- id
- user_id
- file_id nullable
- action
- ip_address
- details
- created_at

Examples of actions:

- login_success
- login_failed
- file_uploaded
- file_downloaded
- file_deleted
- permission_granted
- permission_denied
- Database Design Rules
- Do not rename tables or fields without team approval.
- Do not store raw file contents in PostgreSQL.
- Do not store plain-text passwords.
- Keep file metadata and physical file storage separate.
- Prefer soft deletion for files using is_deleted.
