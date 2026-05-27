# AI Usage Rules

This document defines how contributors may use AI tools while working on the Secure File Drop System.

AI tools are allowed and encouraged, but AI should support the project plan, not randomly redesign the project.

## Core Rule

AI may help write, explain, test, or refactor code, but it must follow the existing project documentation.

Before using AI for implementation, contributors should review:

```text
docs/architecture.md
docs/api-endpoints.md
docs/database-schema.md
docs/mvp-roadmap.md
docs/security-notes.md
docs/user-flow.md
What AI May Do

AI may be used to:

Explain project files
Generate starter code
Help debug errors
Suggest tests
Help write documentation
Refactor assigned code
Create small helper functions
Explain FastAPI, PostgreSQL, authentication, storage, and security concepts
What AI Must Not Do Without Approval

AI must not:

Rename existing routes
Rename database tables
Rename database fields
Move files to different folders
Change the approved folder structure
Add large new features outside the assigned task
Add new third-party dependencies without explanation
Replace the authentication approach without team discussion
Replace the storage design without team discussion
Change the MVP scope without team discussion
Assigned-Task Rule

Each AI-assisted task should have clear boundaries.

A task should define:

Assigned files:
Do-not-touch files:
Required routes:
Required functions:
Expected result:
Testing steps:

Contributors should give those boundaries to AI before asking it to generate code.

Example AI Prompt
I am working on the Secure File Drop System.

Follow these docs:
- docs/architecture.md
- docs/api-endpoints.md
- docs/database-schema.md

Task:
Implement POST /files/upload.

Assigned files:
- backend/app/api/routes_files.py
- backend/app/services/file_service.py
- backend/app/storage/local_storage.py

Do not modify:
- routes_auth.py
- database schema
- admin routes

Use the planned architecture:
Route -> Service -> Storage/Database -> Response

Do not rename existing tables, routes, or folders.
Function and Route Stability

Once a function, route, or table name is documented, contributors should treat it as stable.

Changing names can break other contributors' work.

If a rename is needed, open a discussion or GitHub issue first.

Review Rule

AI-generated code must be reviewed before merging.

Reviewers should check:

Did the code follow the assigned task?
Did it modify unrelated files?
Did it rename anything unexpectedly?
Did it introduce new dependencies?
Did it weaken security?
Did it match the documented architecture?
Did it include reasonable error handling?
Was it tested?
Security Rule

AI-generated security code must be treated carefully.

Authentication, password hashing, file upload validation, permissions, and audit logging should be reviewed closely.

Never accept AI-generated security code blindly.

MVP Scope Rule

The current MVP should stay focused on:

login -> dashboard -> upload -> database metadata -> local storage -> download -> audit log

Future features such as S3, team permissions, password-protected links, and expiring share links should not be added to the MVP unless the team agrees.
