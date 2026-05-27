# Secure File Drop System Architecture

## Purpose

Secure File Drop System is a secure upload/download portal where authenticated users can upload, download, and manage files through controlled permissions and audit logging.

The system should start simple for the MVP, then expand later into teams, time/date-gated links, password-protected share links, and Amazon S3 storage.

## High-Level Architecture

```text
[ Browser / Frontend ]
          |
          v
      HTTPS API
          |
          v
[ FastAPI Backend ]
  |-- Authentication
  |-- File Upload Logic
  |-- Permission Checks
  |-- Audit Logging
  |-- API Endpoints
          |
          v
[ PostgreSQL Database ]
  |-- Users
  |-- Teams
  |-- Files
  |-- Permissions
  |-- Audit Logs
          |
          v
[ File Storage Layer ]
  |-- Local Storage (MVP)
  |-- Amazon S3 (Future)
Backend Responsibilities

The FastAPI backend is responsible for:

Authenticating users
Validating active sessions or tokens
Enforcing file permissions
Receiving uploads
Serving downloads
Writing file metadata to PostgreSQL
Writing audit events
Separating storage logic from API route logic
Database Responsibilities

PostgreSQL stores system metadata, not the physical file contents.

It stores:

Users
Teams
Team membership
File metadata
File permissions
Audit logs
File Storage Responsibilities

The file storage layer stores the actual file content.

For the MVP, files are stored locally in:

backend/uploaded_files/

Future versions may use Amazon S3 while keeping the same service interface.

Design Rule

API routes should not directly contain all business logic.

Preferred flow:

Route -> Service -> Storage/Database -> Response

Example:

routes_files.py
    calls file_service.py
        calls local_storage.py
        calls database layer
        calls audit_service.py

