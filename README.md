# Secure File Drop System

Secure File Drop System is a collaborative portfolio project focused on secure file upload, download, access control, and audit logging.

The project is being built as a FastAPI-based web application with PostgreSQL for metadata and permissions. The MVP will use local file storage first, with future plans to support Amazon S3.

## Project Goal

Build a secure web portal where authenticated users can upload and download files through controlled permissions while system activity is recorded in audit logs.

Core focus areas:

- FastAPI backend services
- Secure file handling
- User authentication
- Access control
- File metadata tracking
- Audit logging
- PostgreSQL database design
- Local storage first, S3 later
- Collaboration-friendly project structure

## MVP Scope

The first MVP should prove this workflow:

```text
login -> dashboard -> upload -> database metadata -> local storage -> download -> audit log

Phase 1 is intentionally simple.

Included in Phase 1:

Basic FastAPI app
Login page
Dashboard page
Local file upload
Local file download
PostgreSQL metadata storage
Basic permissions foundation
Audit log records for uploads/downloads
Admin audit log view

Not included in Phase 1:

Amazon S3
Public share links
Password-protected links
Time/date-gated links
Team access
Email notifications
Payment features
Planned Tech Stack
Backend: Python FastAPI
Database: PostgreSQL
Storage: Local storage for MVP, Amazon S3 later
Frontend: Server-rendered templates / simple web UI for MVP
Deployment target: Ubuntu / possible EC2 later
Repository Documentation

Project planning and architecture documents are located in the docs/ folder.

Important documents:

docs/architecture.md
docs/api-endpoints.md
docs/database-schema.md
docs/mvp-roadmap.md
docs/security-notes.md
docs/user-flow.md
docs/ai-usage-rules.md
docs/collaboration-guide.md
docs/handoff.md
Collaboration Notes

This project may use AI-assisted development, but all contributors should follow the project documentation.

AI should not randomly rename routes, database fields, folders, or core functions. Contributors should work from assigned tasks and keep pull requests focused.

Normal development should use branches and pull requests.

Example branch names:

feature/auth-login
feature/file-upload
feature/file-download
feature/audit-logs
feature/dashboard-ui
docs/update-roadmap
fix/upload-validation
Security Notes

Do not commit:

.env files with real secrets
API keys
AWS access keys
Database passwords
Private certificates
Real customer files
Uploaded files containing private information

Uploaded files should not be served directly from public static folders. Downloads should go through FastAPI so authentication and permission checks happen first.

Current Status

The project is currently in baseline planning and documentation setup.

Next major step:

Start Phase 1 implementation with FastAPI app setup, authentication foundation, dashboard, local upload/download, PostgreSQL metadata, and audit logging.

