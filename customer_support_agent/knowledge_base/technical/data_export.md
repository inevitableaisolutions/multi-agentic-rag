# Data Export

## Overview

CloudSync Pro allows you to export your data at any time. Data export is available on all plans. You own your data and can take it with you whenever you need.

## Exporting Individual Projects

1. Open the project you want to export
2. Click the **three-dot menu** (top right) > **Export Project**
3. Choose your format:
   - **CSV**: Task data in spreadsheet format. Best for importing into Excel or Google Sheets.
   - **JSON**: Structured data including all metadata, comments, and activity history. Best for programmatic use.
   - **PDF**: Formatted project report with task details, timelines, and status summaries. Best for sharing with stakeholders.
4. Click **Export**. The file is generated and a download link is emailed to you within 5 minutes.

## What Data Is Included

Each export contains:
- All tasks with titles, descriptions, status, priority, assignees, and dates
- Custom field values
- Comments and activity log entries
- File attachment URLs (files are not embedded in CSV/JSON exports; use bulk export for files)
- Project settings and member list

## Bulk Export (Full Workspace)

Available on Pro and Enterprise plans:

1. Go to **Settings > Data Management > Export All Data**
2. Select what to include: Projects, Tasks, Users, Comments, Files, Audit Logs
3. Choose format (CSV or JSON)
4. Click **Request Export**
5. A background job generates the archive. You will receive an email with a download link when ready (typically 15-60 minutes depending on workspace size).

The download link expires after 7 days. The export is a ZIP archive containing one file per data type.

## File Attachment Export

To export file attachments:

1. Go to **Settings > Data Management > Export Files**
2. Select specific projects or the entire workspace
3. Click **Export Files**
4. Files are packaged into a ZIP archive. Maximum export size is 10 GB per request. For larger workspaces, export by project.

## API-Based Export

Use the CloudSync Pro API to programmatically export data:

```
GET /api/v2/projects/{project_id}/export?format=json
Authorization: Bearer sk_live_xxxxxxxxxxxx
```

Response includes a `download_url` field with a time-limited link to the export file. Rate limits apply (see API Errors guide).

## Data Portability

CloudSync Pro supports importing data from Asana, Trello, Monday.com, and Jira. Go to **Settings > Data Management > Import** to start a migration. Our import tool maps fields automatically and provides a preview before committing the import.
