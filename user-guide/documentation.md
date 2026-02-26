# Documentation & Knowledge Base

Create, organize, and share technical documentation, runbooks, and network diagrams — with WYSIWYG or Markdown editors and an AI writing assistant.

---

## Overview

| Feature | URL |
|---------|-----|
| Documents | `/docs/` |
| Templates | `/docs/templates/` |
| Knowledge Base | `/docs/kb/` |
| Diagrams | `/docs/diagrams/` |
| AI Assistant | `/docs/ai/assistant/` |

---

## Documents

Documents are rich-content pages scoped to your organization:

| Field | Description |
|-------|-------------|
| **Title** | Document name |
| **Content** | Written in WYSIWYG (Quill) or Markdown |
| **Category** | Organize into folders/categories |
| **Tags** | Free-form labels for search and filtering |
| **Visibility** | Organization-scoped or private |

### Editors

| Editor | Best For |
|--------|----------|
| **WYSIWYG (Quill)** | Formatted docs with images, tables, callouts |
| **Markdown** | Technical docs, runbooks, code snippets |

Switch between editors with the **Editor** selector at the top of the form. Content is preserved when switching.

### Uploading Documents

Upload existing files (PDF, DOCX, etc.) directly at `/docs/upload/`. Uploaded files are stored securely and linked to your organization.

---

## Templates

**Templates** are reusable document skeletons — create a template once, then generate new documents from it instantly.

| Use Case | Example Template |
|----------|-----------------|
| **Runbooks** | "Network Outage Runbook" starter |
| **Client reports** | "Monthly IT Summary" |
| **Onboarding docs** | "New Employee IT Setup" |
| **Change requests** | "Change Request Form" |

Templates support the same WYSIWYG and Markdown editors as documents, and can include default tags and categories.

---

## Knowledge Base

The **Knowledge Base** is a public-within-org article library for reference material:

| Feature | Details |
|---------|---------|
| **URL slugs** | Human-readable URLs (`/docs/kb/my-article/`) |
| **Categories** | Organize articles by topic |
| **Search** | Full-text search across all KB articles |
| **Versioning** | Edit history for all articles |
| **Global KB** | Superusers can publish articles visible across all organizations |

### Global Knowledge Base

Global KB articles appear in every organization's knowledge base. Useful for:
- Company-wide IT policies
- Standard operating procedures
- Product documentation

---

## Network Diagrams

Create interactive network topology diagrams using a drag-and-drop canvas:

| Feature | Details |
|---------|---------|
| **Nodes** | Servers, switches, routers, firewalls, workstations, etc. |
| **Connections** | Labeled links with cable type and speed |
| **Layers** | Physical and logical topology views |
| **Templates** | Start from predefined diagram templates |
| **Export** | PNG, SVG, or JSON |

Diagrams are saved per-organization and can be embedded in documents.

---

## AI Documentation Assistant

The built-in AI assistant helps you write and improve documentation:

| Feature | What It Does |
|---------|-------------|
| **Generate** | Create a document draft from a prompt |
| **Enhance** | Improve clarity, grammar, and completeness of existing content |
| **Validate** | Check a runbook for missing steps or gaps |

> AI features require an API key configured in *Settings → AI Integration*.

---

## Categories

Organize both documents and KB articles into hierarchical categories:

- Create at *Docs → Categories → New Category*
- Nest categories up to 3 levels deep
- Filter and browse documents by category
- Categories are organization-scoped

---

*Back to [User Guide](README.md)*
