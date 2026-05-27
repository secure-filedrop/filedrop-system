
User Flow

This document describes the planned MVP user workflow.

MVP Workflow
User opens web app
   |
   v
Frontend sends login request to FastAPI
   |
   v
FastAPI validates username/password
   |
   v
FastAPI creates session/JWT token
   |
   v
User enters dashboard
   |
   v
Dashboard requests allowed files from FastAPI
   |
   v
FastAPI validates token/session
   |
   v
FastAPI queries PostgreSQL for permissions
   |
   v
Allowed files displayed
   |
   v
User uploads file
   |
   v
FastAPI validates token/session again
   |
   v
FastAPI validates upload rules
   |
   v
File stored in local storage for MVP
   |
   v
File metadata saved in PostgreSQL
   |
   v
Permissions saved
   |
   v
Audit log records upload
   |
   v
User downloads file
   |
   v
FastAPI validates permissions again
   |
   v
File served/download generated
   |
   v
Audit log records download
Login Flow
Open login page
Submit credentials
FastAPI validates credentials
If valid: enter dashboard
If invalid: show login error
Upload Flow
User selects file
User submits upload form
FastAPI validates user
FastAPI validates file
File service saves file metadata
Storage service saves physical file
Audit service logs upload
Dashboard updates file list
Download Flow
User clicks download
FastAPI validates user
FastAPI checks file permission
FastAPI retrieves file from storage
Audit service logs download
User receives file
Admin Log Flow
Admin logs in
Admin opens audit logs page
FastAPI validates admin role
Audit service retrieves logs
Admin reviews system activity
User Flow Rule

The frontend should never be trusted as the security boundary.

Even if a button is hidden, FastAPI must still validate authentication and permissions on every protected action.
