
Collaboration Guide

This document defines how contributors should work together on the Secure File Drop System.

The goal is to keep the project organized while allowing contributors to use AI, GitHub, and their own development tools.

Project Collaboration Goal

The project should be built in small, controlled steps.

Each contributor should work on a clearly assigned task instead of randomly changing files.

Source of Truth

The documentation inside the docs/ folder is the source of truth for the project.

Important files:

docs/architecture.md
docs/api-endpoints.md
docs/database-schema.md
docs/mvp-roadmap.md
docs/security-notes.md
docs/user-flow.md
docs/ai-usage-rules.md
docs/collaboration-guide.md

If code and documentation disagree, the team should discuss and update the correct source.

Recommended Git Workflow

For baseline setup, direct commits to main may happen if needed.

For normal development, use branches and pull requests.

Recommended branch examples:

feature/auth-login
feature/file-upload
feature/file-download
feature/audit-logs
feature/dashboard-ui
docs/update-roadmap
fix/upload-validation
Normal Task Workflow
1. Discuss the feature or fix.
2. Create a GitHub issue.
3. Assign the issue to one contributor.
4. Create a branch for the work.
5. Make the change.
6. Test the change.
7. Commit and push the branch.
8. Open a pull request.
9. Review the pull request.
10. Merge after approval.
GitHub Issue Template

Each task should include:

Title:

Goal:

Assigned files:

Do-not-touch files:

Required routes:

Required functions:

Acceptance criteria:

Testing steps:

Notes:
Pull Request Checklist

Before merging, check:

What task does this complete?

What files changed?

Did this follow the current folder structure?

Did this change any route names?

Did this change any database fields?

Did this add dependencies?

How was it tested?

Does documentation need to be updated?
File Ownership by Area

Authentication work usually belongs in:

backend/app/api/routes_auth.py
backend/app/auth/security.py
backend/app/auth/dependencies.py
backend/app/templates/login.html

File upload/download work usually belongs in:

backend/app/api/routes_files.py
backend/app/services/file_service.py
backend/app/storage/local_storage.py
backend/uploaded_files/

Admin and audit work usually belongs in:

backend/app/api/routes_admin.py
backend/app/services/audit_service.py
backend/app/templates/admin_logs.html

Database work usually belongs in:

backend/app/database/
backend/app/models/
backend/app/schemas/
backend/app/database/migrations/

Frontend/template work usually belongs in:

backend/app/templates/
backend/app/static/
Avoiding Duplicate AI Work

When multiple people use AI, the project can drift if each AI assistant invents different names or patterns.

To avoid that:

Use the documented route names.
Use the documented table names.
Use the documented field names.
Keep business logic in services.
Keep route files focused on request/response handling.
Ask before changing architecture.
Keep pull requests small.
Good Task Example
Task:
Create local storage helper for uploaded files.

Assigned files:
- backend/app/storage/local_storage.py

Do not modify:
- routes_auth.py
- routes_admin.py
- database schema

Required functions:
- save_file_to_disk()
- get_file_path()
- delete_file_from_disk()

Acceptance criteria:
- Uploaded files are saved with safe unique names.
- Original filenames are not trusted as storage paths.
- The storage folder is created if missing.
Project Lead / Integrator Role

The project should have at least one person responsible for integration.

That person checks:

Does the change match the MVP?
Does the code fit the architecture?
Does it break other contributors' work?
Are docs updated when needed?
Are security rules followed?
Main Branch Rule

The main branch should represent stable project progress.

For normal collaboration, changes should go through pull requests.

Direct pushes to main should be limited to early setup, emergency fixes, or project-owner-approved changes.
