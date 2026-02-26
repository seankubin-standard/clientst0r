# Workflows (Processes)

Define and execute step-by-step checklists and workflows for repeatable IT tasks — onboarding, offboarding, maintenance, incident response, and more.

---

## Overview

| Feature | URL |
|---------|-----|
| Process Library | `/processes/` |
| Executions (active runs) | `/processes/executions/` |
| Global Processes | `/processes/global/` |

**Process** = a reusable workflow template with ordered stages  
**Execution** = a running instance of a process for a specific task or client

---

## Processes

A **Process** is a template defining the steps to complete a task:

| Field | Description |
|-------|-------------|
| **Name** | e.g., "Employee Onboarding", "Network Device Replacement" |
| **Description** | What this process is for |
| **Category** | Onboarding / Offboarding / Maintenance / Incident / etc. |
| **Organization** | Scoped to one org, or Global (shared across all) |
| **Stages** | Ordered list of steps (see below) |

### Stages

Each process has multiple **stages** (steps):

| Field | Description |
|-------|-------------|
| **Order** | Drag-to-reorder step sequence |
| **Title** | Step name (e.g., "Create AD account") |
| **Description** | Detailed instructions for the step |
| **Required** | Whether this step must be completed before proceeding |
| **Assigned Role** | Which role is responsible for this step |
| **Notes** | Free-text notes field on execution |
| **Checklist Items** | Sub-tasks within a stage |

---

## Executing a Process

1. Open a process from the library
2. Click **Execute** (or **Start Execution**)
3. Fill in execution metadata (assigned user, target, due date)
4. Work through each stage — check off items as completed
5. Add notes per stage as needed
6. Process is marked complete when all required stages are done

### Execution Tracking

| Feature | Details |
|---------|---------|
| **Progress bar** | Shows % of stages completed |
| **Stage status** | Pending / In Progress / Complete / Skipped |
| **Audit trail** | Every stage completion is logged with timestamp and user |
| **Due dates** | Set overall and per-stage due dates |
| **Reassignment** | Assign stages to specific users |

---

## Global Processes

**Global Processes** are available across all organizations — useful for standardized IT procedures.

- Only **superusers/staff** can create global processes
- Global processes appear in every organization's process library
- Organizations can **copy** a global process and customize it

### Example Global Processes

- Employee Onboarding Checklist
- Employee Offboarding Checklist
- Network Device Deployment
- New Client Onboarding
- Security Incident Response
- Quarterly Maintenance Review

---

## Process Diagrams

Automatically generate a visual flowchart from a process definition:

- Click **Generate Diagram** on any process
- Exports as a network diagram showing stage order and dependencies
- Saved to the Diagrams section of Documentation

---

## Execution History

All completed and in-progress executions are listed at `/processes/executions/`:

| Column | Details |
|--------|---------|
| **Process** | Which workflow template was used |
| **Started By** | User who initiated |
| **Started At** | Timestamp |
| **Status** | In Progress / Complete / Cancelled |
| **Completion** | % of stages done |

Each execution has a full **audit log** showing who completed each stage and when.

---

*Back to [User Guide](README.md)*
