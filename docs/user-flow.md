# User Flow

This document describes the planned MVP user workflow for the Secure File Drop System.

## MVP Workflow

1. User opens the web app.
2. Frontend sends login request to FastAPI.
3. FastAPI validates the username/password.
4. FastAPI creates a session or JWT token.
5. User enters the dashboard.
6. Dashboard requests allowed files from FastAPI.
7. FastAPI validates the token/session.
8. FastAPI queries PostgreSQL for file permissions.
9. Allowed files are displayed.
10. User uploads a file.
11. FastAPI validates the token/session again.
12. FastAPI validates upload rules.
13. File is stored in local storage for the MVP.
14. File metadata is saved in PostgreSQL.
15. File permissions are saved.
16. Audit log records the upload.
17. User downloads a file.
18. FastAPI validates permissions again.
19. File is served or a download is generated.
20. Audit log records the download.

## Login Flow

1. User opens the login page.
2. User submits credentials.
3. FastAPI validates credentials.
4. If valid, the user enters the dashboard.
5. If invalid, the system shows a login error.

## Upload Flow

1. User selects a file.
2. User submits the upload form.
3. FastAPI validates the current user.
4. FastAPI validates the uploaded file.
5. File service prepares and saves file metadata.
6. Storage service saves the physical file.
7. Audit service logs the upload event.
8. Dashboard updates the file list.

## Download Flow

1. User clicks download.
2. FastAPI validates the current user.
3. FastAPI checks file permissions.
4. FastAPI retrieves the file from storage.
5. Audit service logs the download event.
6. User receives the file.

## Admin Log Flow

1. Admin logs in.
2. Admin opens the audit logs page.
3. FastAPI validates the admin role.
4. Audit service retrieves logs.
5. Admin reviews system activity.

## User Flow Rule

The frontend should never be trusted as the security boundary.

Even if a button is hidden, FastAPI must still validate authentication and permissions on every protected action.
