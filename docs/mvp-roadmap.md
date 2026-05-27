
MVP Roadmap

This document defines the planned MVP phases for the Secure File Drop System.

The goal is to build a working secure local version first, then expand.

Phase 1: Local MVP

Core goal:

A logged-in user can upload and download files through the FastAPI web app.

Features:

- Basic FastAPI app
- Login page
- Dashboard page
- Single admin user or basic users table
- Local file upload
- Local file download
- File metadata saved in PostgreSQL
- Basic audit logging
- Simple admin logs page

Storage:

backend/uploaded_files/

Database:

PostgreSQL

Out of scope for Phase 1:

- Amazon S3
- Public share links
- Password-protected links
- Time/date-gated links
- Team access
- Email notifications
- Payment features
- Large enterprise permission system
- Phase 2: User and Permission Improvements

Features:

- Multiple users
- File ownership
- User-specific file permissions
- Permission checks before download
- Better admin audit view
- Soft delete support
- Phase 3: Team Access

Features:

- Teams
- Team members
- Team file permissions
- Team file dashboard

Tables involved:

- teams
- team_members
- file_permissions
- Phase 4: Secure Share Links

Features:

- Password-protected links
- Time/date-gated links
- Expiring links
- Download restrictions
- Share-link audit logs
- Phase 5: Amazon S3 Storage

Features:

- Store files in S3
- Keep file metadata in PostgreSQL
- Replace or extend local storage service with S3 storage service
- Preserve the same file service interface where possible
- Phase 6: Deployment

Possible deployment target:

- Ubuntu EC2 instance
- PostgreSQL
- FastAPI
- Nginx
- HTTPS
- S3
- MVP Rule

Do not add future-phase features to Phase 1 unless the team agrees.

The MVP should prove:

login -> dashboard -> upload -> database metadata -> local storage -> download -> audit log

