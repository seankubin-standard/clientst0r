# Asset Management

Track and manage all IT equipment, servers, network devices, and hardware assets across your organizations.

---

## Asset Tracking

Each asset record can store:

| Field | Description |
|-------|-------------|
| **Make / Model / Serial** | Hardware identification |
| **Purchase Date / Cost** | Financial tracking |
| **Warranty Expiry** | Auto-alerts before expiry |
| **Status** | Active, Inactive, Maintenance, Retired, Needs Reorder |
| **Location** | Data center, rack, room, or site |
| **Custom Fields** | Unlimited organization-specific fields |
| **Attachments** | Photos, manuals, invoices, documentation |
| **Relationships** | Link to parent assets, dependencies, or related equipment |

### QR Codes
Generate a QR code label for any asset — scan with a mobile device to open the asset record instantly.

### Needs Reorder Flag
Mark an asset for physical replacement with the **↩ Reorder** flag. Flagged assets appear with a yellow badge in the asset list and can be filtered separately.

---

## Network Management

| Feature | Details |
|---------|---------|
| **IP Addresses** | Track IPs and subnets per asset |
| **VLANs** | Assign assets to VLANs, manage VLAN definitions |
| **MAC Addresses** | Record all network interface MACs |
| **Network Diagrams** | Create visual topology maps |
| **Port Assignments** | See switch ports and patch panel connections per asset |

---

## Rack Management

Organize equipment in data center racks with a visual drag-and-drop layout.

```
┌─────────────────────────┐
│  Rack A — 42U           │
├─────────────────────────┤
│ 1U  Patch Panel A       │  ← grey
│ 2U  Core Switch         │  ← blue (network)
│ 3U  Server A (2U)  ●    │  ← green (active)
│ 5U  — empty —           │
│ 6U  NAS Storage (4U)    │  ← purple (storage)
│     ...                 │
│ 38U UPS (2U)            │  ← amber (power)
└─────────────────────────┘
  Power: 1.4 kW / 4.0 kW
  Temp:  22°C ✓
```

| Feature | Details |
|---------|---------|
| **U-space allocation** | Drag devices to any U position |
| **Power tracking** | Total draw vs. capacity with visual bar |
| **Environmental** | Log temperature and humidity readings |
| **Locations** | Organize racks by data center → room → row |

---

## Port Configuration

Switches and patch panels support full per-port configuration:

### Switch Ports

| Field | Options |
|-------|---------|
| **Description** | Free-text label (e.g., "Uplink to Core") |
| **Mode** | Access / Trunk / Hybrid |
| **Native VLAN** | Single VLAN for untagged traffic |
| **Tagged VLANs** | Multiple VLANs (Trunk/Hybrid mode only) |
| **Speed** | 100M / 1G / 10G / 25G / 40G / 100G |
| **Status** | Active / Inactive / Error |

> **Tip:** Tagged VLANs are automatically disabled in Access mode.

### Patch Panel Ports

| Field | Description |
|-------|-------------|
| **Label** | Port identifier |
| **Destination** | What the cable connects to |
| **Cable Type** | Cat5e, Cat6, Cat6a, fiber, etc. |
| **VLAN** | Associated VLAN |
| **Status** | Active / Inactive |

**Bulk edit** — configure all ports on one screen; save with a single click.

---

## Asset Categories

Supported asset types:

**Compute**
- Servers & Virtual Machines
- Workstations & Laptops
- Mobile Devices (phones, tablets)

**Network**
- Switches, Routers, Firewalls
- Wireless Access Points
- Patch Panels, Fiber Panels

**Storage**
- NAS, SAN
- External drives

**Other**
- Printers & Peripherals
- Security Equipment (cameras, access control)
- Power Distribution (UPS, PDU)

---

## Reporting & Analytics

| Report | Details |
|--------|---------|
| **Inventory** | Full asset list with all fields, filterable |
| **Warranty** | Assets with warranties expiring in 30/60/90 days |
| **Depreciation** | Asset value over time |
| **Needs Reorder** | All assets flagged for replacement |
| **Export** | CSV, PDF, or Excel download |

---

*Previous: [Getting Started](getting-started.md) · Next: [Service Vehicles](service-vehicles.md)*
