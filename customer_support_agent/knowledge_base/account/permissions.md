# Permissions and Roles

## Overview

CloudSync Pro uses role-based access control (RBAC) to manage what users can see and do within a workspace. Permissions are managed at both the workspace level and the project level.

## Workspace-Level Roles

### Owner
- Full control over the workspace, billing, and all settings
- Can transfer workspace ownership to another admin
- Can delete the workspace
- Only one owner per workspace

### Admin
- Manage workspace settings, integrations, and security policies
- Invite and remove members
- Create, archive, and delete projects
- Access all projects regardless of project-level permissions
- Cannot change billing or delete the workspace

### Member
- Create projects and tasks
- Access projects they are added to
- Edit tasks assigned to them or tasks in their projects
- Cannot manage workspace settings or invite users

### Viewer
- Read-only access to projects they are added to
- Can add comments on tasks
- Cannot create, edit, or delete tasks or projects
- Cannot access workspace settings

## Project-Level Roles

Within each project, users can have additional permissions:

- **Project Admin**: Full control over the project (settings, members, deletion)
- **Project Editor**: Create, edit, and delete tasks within the project
- **Project Viewer**: Read-only access with commenting ability

Project-level roles can further restrict but never expand workspace-level permissions. For example, a workspace Member assigned as a Project Viewer cannot edit tasks in that project.

## Managing Permissions

### Assigning Workspace Roles
1. Go to **Settings > Members**
2. Find the user and click their current role
3. Select the new role from the dropdown
4. Click **Save**

### Assigning Project Roles
1. Open the project and go to **Project Settings > Members**
2. Click **Add Member** or modify an existing member's role
3. Select the project role
4. Click **Save**

## Custom Roles (Enterprise Only)

Enterprise plans can create custom roles with granular permissions:

1. Go to **Settings > Roles > Create Custom Role**
2. Name the role and select specific permissions from categories: Projects, Tasks, Members, Integrations, Settings, Billing
3. Assign the custom role to users from the Members page

## Permission Error Troubleshooting

If a user receives a "Permission Denied" error (code `ERR_FORBIDDEN_403`):
1. Check their workspace role at Settings > Members
2. Check their project role at Project Settings > Members
3. Verify they have been added to the specific project
4. If using SSO with SCIM, verify role mappings in your identity provider
