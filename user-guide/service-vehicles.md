# Service Vehicles

Comprehensive fleet management for service vehicles — mileage tracking, maintenance scheduling, insurance, fuel logs, and damage reporting.

---

## Vehicle Tracking

| Field | Description |
|-------|-------------|
| **Make / Model / Year** | Vehicle identification |
| **VIN** | Vehicle Identification Number |
| **License Plate** | Registration plate |
| **Odometer** | Current mileage (auto-updated from fuel logs) |
| **Status** | Active / In Maintenance / Retired |
| **Condition** | Excellent / Good / Fair / Poor / Needs Repair |
| **GPS Coordinates** | Latitude/longitude for mapping |
| **Assigned User** | Who is currently using the vehicle |

---

## Insurance & Registration

| Feature | Details |
|---------|---------|
| **Insurance Policy** | Policy number, provider, premium, coverage amount |
| **Expiration Alerts** | Automatic warnings 30 days before insurance or registration expires |
| **Registration** | State/region, expiry date, renewal tracking |
| **Document Upload** | Attach insurance cards and registration documents |

> Vehicles with expiring insurance or registration are flagged in the fleet overview.

---

## Maintenance Management

Schedule and record all service events:

| Field | Description |
|-------|-------------|
| **Service Type** | Oil change, tire rotation, brake inspection, etc. |
| **Date Performed** | When the service occurred |
| **Mileage at Service** | Odometer reading at time of service |
| **Cost** | Labor and parts cost |
| **Next Due** | Date or mileage for next service |
| **Provider** | Shop or technician |
| **Notes** | Free-text details |

**Overdue alerts** — maintenance items past their due date or mileage threshold appear in the fleet dashboard with a red indicator.

### Maintenance Log Example

```
Service History — Ford Transit (2021)
─────────────────────────────────────────────────────
Date        Type              Miles      Cost    Next Due
2025-11-12  Oil Change        48,200    $89      52,200 mi
2025-09-03  Tire Rotation     46,100    $45      50,100 mi
2025-06-20  Brake Inspection  44,000    $320     —
2025-03-01  Oil Change        41,800    $89      45,800 mi ✓ Done
```

---

## Fuel Tracking

Log every fill-up to track cost and efficiency:

| Field | Description |
|-------|-------------|
| **Date** | Fill-up date |
| **Gallons / Litres** | Quantity of fuel |
| **Cost per Unit** | Fuel price |
| **Total Cost** | Auto-calculated |
| **Odometer** | Current reading at fill-up |
| **MPG / L/100km** | Auto-calculated from previous log |

**Efficiency Chart** — trend graph of MPG over time highlights declining efficiency (potential mechanical issues).

```
MPG over 12 months
  30 ┤                     ●
  28 ┤         ●     ●
  26 ┤   ●
  24 ┤
  22 ┤                           ●  ← investigate
     └──────────────────────────────
       Jan Feb Mar Apr May Jun Jul
```

---

## Damage Reporting

Track every vehicle incident with photos and repair status:

| Field | Description |
|-------|-------------|
| **Date** | Incident date |
| **Description** | What happened |
| **Severity** | Minor / Moderate / Major |
| **Location on Vehicle** | Front, rear, driver-side, etc. |
| **Photos** | Attach damage photos |
| **Repair Status** | Pending / In Progress / Repaired |
| **Repair Cost** | Final repair amount |
| **Insurance Claim** | Claim number if applicable |

---

## Vehicle Inventory

Each vehicle has its own inventory for equipment and tools:

| Field | Description |
|-------|-------------|
| **Item Name** | Equipment or tool |
| **Category** | Cables, tools, hardware, consumables |
| **Quantity** | Current count |
| **Low Stock Threshold** | Alert when below this quantity |
| **Value** | Per-unit cost |
| **Location** | Storage location in vehicle |

---

## User Assignments

Assign users to vehicles for accountability and tracking:

- Record who is currently assigned to each vehicle
- View assignment history
- See all vehicles assigned to a specific user
- Assignment history is logged in the audit trail

---

*Previous: [Asset Management](asset-management.md) · Next: [Password Vault](password-vault.md)*
