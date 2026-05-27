
API Endpoints

This document defines the planned API endpoints for the Secure File Drop System.

Endpoint names should stay stable unless the team agrees to change them.

Authentication Endpoints
POST /login

Purpose:

Authenticate a user.

Expected behavior:

- Receive email/username and password.
- Validate credentials.
- Create a session or JWT token.
- Return the user to the dashboard or return an auth response.

Related files:

- backend/app/api/routes_auth.py
- backend/app/auth/security.py
- backend/app/auth/dependencies.py
- POST /logout

Purpose:

- Log out the current user.

Expected behavior:

- Clear session/token where applicable.
- Return user to login page.

Related files:

- backend/app/api/routes_auth.py
- Dashboard Endpoint
- GET /dashboard

Purpose:

- Show the authenticated user's dashboard.

Expected behavior:

- Validate the current user.
- Request allowed files from the backend.
- Display upload form and allowed file list.

Related files:

- backend/app/api/routes_files.py
- backend/app/templates/dashboard.html
- File Endpoints
- POST /files/upload

Purpose:

- Upload a file.

Expected behavior:

- Validate current session/token.
- Validate upload rules.
- Store file using the storage layer.
- Save file metadata in PostgreSQL.
- Save permissions.
- Record an audit log entry.

Related files:

- backend/app/api/routes_files.py
- backend/app/services/file_service.py
- backend/app/storage/local_storage.py
- backend/app/services/audit_service.py
- GET /files

Purpose:

- List files the current user is allowed to access.

Expected behavior:

- Validate current session/token.
- Query PostgreSQL for files owned by or shared with the user.
- Return file metadata.

Related files:

- backend/app/api/routes_files.py
- backend/app/services/file_service.py
- GET /files/{file_id}/download

Purpose:

- Download a file.

Expected behavior:

- Validate current session/token.
- Check file permissions.
- Retrieve file from local storage or future S3 storage.
- Record an audit log entry.
- Return the file download.

Related files:

- backend/app/api/routes_files.py
- backend/app/services/file_service.py
- backend/app/storage/local_storage.py
- backend/app/services/audit_service.py
- Admin Endpoints
- GET /admin/logs

Purpose:

- Show audit logs for admin users.

Expected behavior:

- Validate current session/token.
- Confirm user has admin role.
- Query audit logs.
- Display or return log entries.

Related files:

- backend/app/api/routes_admin.py
- backend/app/services/audit_service.py
- backend/app/templates/admin_logs.html
- API Design Rules
- Routes should call service functions instead of containing all logic directly.
- Permission checks must happen before downloads.
- Upload and download actions must create audit log entries.
- New endpoint names should be added to this document before implementation.
- Do not rename endpoints without team approval.
