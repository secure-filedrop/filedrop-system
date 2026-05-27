
Project Handoff

This document summarizes the current working state of the Secure File Drop System.

Use this file when starting a new chat, onboarding a contributor, or resuming development after a break.

Current Project

Repository:

https://github.com/secure-filedrop/filedrop-system.git


Project Purpose

Secure File Drop System is a secure upload/download portal where authenticated users can upload, download, and manage files through controlled permissions and audit logging.

The system should start simple and expand over time.

Current Architecture Direction

Planned stack:

- Python FastAPI
- PostgreSQL
- Local file storage for MVP
- Amazon S3 later
- Server-rendered templates or simple frontend for MVP
- Ubuntu/EC2 deployment later

Preferred backend flow:

- Route -> Service -> Storage/Database -> Response

Example:

- routes_files.py
    - calls file_service.py
        - calls local_storage.py
        - calls database layer
        - calls audit_service.py
        
Current MVP Workflow:

- User opens web app
   |
   v
- Frontend sends login request to FastAPI
   |
   v
- FastAPI validates username/password
   |
   v
- FastAPI creates session/JWT token
   |
   v
- User enters dashboard
   |
   v
- Dashboard requests allowed files from FastAPI
   |
   v
- FastAPI validates token/session
   |
   v
- FastAPI queries PostgreSQL for permissions
   |
   v
- Allowed files displayed
   |
   v
- User uploads file
   |
   v
- FastAPI validates token/session again
   |
   v
- FastAPI validates upload rules
   |
   v
- File stored in local storage for MVP
   |
   v
- File metadata saved in PostgreSQL
   |
   v
- Permissions saved
   |
   v
- Audit log records upload
   |
   v
- User downloads file
   |
   v
- FastAPI validates permissions again
   |
   v
- File served/download generated
   |
   v
- Audit log records download

Suggested Database Tables
users
- id
- email
- password_hash
- role
- is_active
- created_at

teams
- id
- name
- created_at

team_members
- id
- user_id
- team_id

files
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

file_permissions
- id
- file_id
- user_id nullable
- team_id nullable
- permission_type
- created_at

audit_logs
- id
- user_id
- file_id nullable
- action
- ip_address
- details
- created_at
Existing Documentation

The following baseline docs exist or are planned in docs/:

- docs/architecture.md
- docs/api-endpoints.md
- docs/database-schema.md
- docs/mvp-roadmap.md
- docs/security-notes.md
- docs/user-flow.md
- docs/ai-usage-rules.md
- docs/collaboration-guide.md
- docs/handoff.md
- Collaboration Direction

This is intended to be a collaborative project.

Rules:

- Use documentation as the project source of truth.
- Keep tasks small.
- Use assigned files for each task.
- Avoid random architecture changes.
- Do not rename tables, fields, routes, or folders without discussion.
- Use branches and pull requests for normal development.
- AI-assisted development is allowed, but AI should follow the project docs.
- Current Git Workflow Preference

Baseline setup docs may be pushed directly to main.

After baseline setup, normal work should use branches.

Example:

- git checkout -b feature/file-upload

Then:

- git add .
- git commit -m "Implement local file upload"
- git push -u origin feature/file-upload

Then open a pull request.

Current Status

Baseline documentation is being created.

Already created/updated:

- docs/architecture.md
- docs/api-endpoints.md
- docs/database-schema.md
- docs/mvp-roadmap.md
- docs/security-notes.md
- docs/user-flow.md

Recently planned/added:

- docs/ai-usage-rules.md
- docs/collaboration-guide.md
- docs/handoff.md
- README.md
- Next Recommended Steps
- Finish baseline documentation.
- Commit and push baseline docs.
- Start using branches for implementation tasks.
- Create first implementation issue: FastAPI app foundation.
- Create second issue: authentication/login foundation.
- Create third issue: dashboard page.
- Create fourth issue: local upload/download flow.
- Create fifth issue: audit logging.
- Important Reminder

The MVP should stay focused on:

login -> dashboard -> upload -> database metadata -> local storage -> download -> audit log

Avoid adding future features too early.
