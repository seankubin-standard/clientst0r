"""
Integrated documentation and help system
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import markdown
import os
import re


# ── Searchable index ─────────────────────────────────────────────────────────
# Each entry: section title, url name, anchor id, heading, plain-text keywords
HELP_INDEX = [
    # Getting Started
    {'section': 'Getting Started', 'url_name': 'core:help_getting_started',
     'anchor': 'quick-start', 'heading': 'Quick Start',
     'text': 'setup organization users login first steps onboarding'},
    {'section': 'Getting Started', 'url_name': 'core:help_getting_started',
     'anchor': 'organizations', 'heading': 'Organizations',
     'text': 'organizations clients multi-tenant isolation scoping'},
    {'section': 'Getting Started', 'url_name': 'core:help_getting_started',
     'anchor': 'users-roles', 'heading': 'Users & Roles',
     'text': 'users roles permissions rbac owner admin editor read-only invite'},
    {'section': 'Getting Started', 'url_name': 'core:help_getting_started',
     'anchor': 'api-keys', 'heading': 'API Keys',
     'text': 'api keys authentication tokens bearer authorization profile'},

    # Assets
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'asset-tracking', 'heading': 'Asset Tracking',
     'text': 'asset tracking make model serial number purchase date warranty lifecycle custom fields attachments photos QR code'},
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'network-management', 'heading': 'Network Management',
     'text': 'network ip address subnet vlan mac address topology diagram port assignment switch patch panel'},
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'rack-management', 'heading': 'Rack Management',
     'text': 'rack data center location u-space drag drop power consumption temperature humidity'},
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'port-configuration', 'heading': 'Port Configuration',
     'text': 'port configuration switch patch panel access trunk hybrid vlan native tagged speed status'},
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'asset-categories', 'heading': 'Asset Categories',
     'text': 'server virtual machine network switch router firewall storage NAS SAN workstation laptop mobile printer UPS PDU'},
    {'section': 'Asset Management', 'url_name': 'core:help_assets',
     'anchor': 'reporting', 'heading': 'Reporting & Analytics',
     'text': 'report analytics export csv pdf depreciation warranty alert needs reorder'},

    # Vehicles
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'vehicle-tracking', 'heading': 'Vehicle Tracking',
     'text': 'vehicle fleet tracking make model year VIN license plate mileage odometer status condition GPS'},
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'insurance', 'heading': 'Insurance & Registration',
     'text': 'insurance registration policy provider expiration premium renewal alert 30 days'},
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'maintenance', 'heading': 'Maintenance Management',
     'text': 'maintenance service history oil change tire rotation inspection scheduled cost labor parts next due overdue'},
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'fuel', 'heading': 'Fuel Tracking',
     'text': 'fuel log fill-up gallons cost MPG miles per gallon efficiency trend analysis'},
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'damage', 'heading': 'Damage Reporting',
     'text': 'damage incident report photo severity minor moderate major repair tracking insurance claim'},
    {'section': 'Service Vehicles', 'url_name': 'core:help_vehicles',
     'anchor': 'vehicle-inventory', 'heading': 'Vehicle Inventory',
     'text': 'vehicle inventory equipment cables tools hardware quantity low stock value storage location'},

    # Vault
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'security-features', 'heading': 'Security Features',
     'text': 'AES-256 encryption zero knowledge master password access control audit log'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'breach-detection', 'heading': 'Breach Detection',
     'text': 'breach detection HIBP have i been pwned compromised password alert scan reuse'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'password-management', 'heading': 'Password Management',
     'text': 'password store organize search copy clipboard show hide notes URL tags labels'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'password-generator', 'heading': 'Password Generator',
     'text': 'password generator random strong cryptographic length character passphrase pronounceable'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'totp', 'heading': 'TOTP / Two-Factor Auth',
     'text': 'TOTP two factor 2FA authenticator QR code one-time password OTP'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'sharing', 'heading': 'Sharing & Collaboration',
     'text': 'share credential organization access control read-only temporary history'},
    {'section': 'Password Vault', 'url_name': 'core:help_vault',
     'anchor': 'import-export', 'heading': 'Import & Export',
     'text': 'import export CSV LastPass 1Password backup migrate'},

    # Monitoring
    {'section': 'Monitoring', 'url_name': 'core:help_monitoring',
     'anchor': 'system-monitoring', 'heading': 'System Monitoring',
     'text': 'monitor server CPU memory disk uptime network service HTTP HTTPS TCP ping SSL certificate port'},
    {'section': 'Monitoring', 'url_name': 'core:help_monitoring',
     'anchor': 'alerting', 'heading': 'Alerting',
     'text': 'alert notification email webhook Slack Teams threshold escalation maintenance window silence'},
    {'section': 'Monitoring', 'url_name': 'core:help_monitoring',
     'anchor': 'dashboards', 'heading': 'Dashboards & Visualization',
     'text': 'dashboard real-time graph historical custom heat map uptime SLA'},
    {'section': 'Monitoring', 'url_name': 'core:help_monitoring',
     'anchor': 'incident-management', 'heading': 'Incident Management',
     'text': 'incident timeline MTTR post-mortem root cause resolution'},

    # Security
    {'section': 'Security', 'url_name': 'core:help_security',
     'anchor': 'vulnerability-scanning', 'heading': 'Vulnerability Scanning',
     'text': 'vulnerability scan CVE python package OS severity critical high medium low scheduled fix'},
    {'section': 'Security', 'url_name': 'core:help_security',
     'anchor': 'authentication', 'heading': 'Authentication & Access Control',
     'text': '2FA two-factor TOTP Azure AD SSO password policy session timeout IP whitelist lockout'},
    {'section': 'Security', 'url_name': 'core:help_security',
     'anchor': 'rbac', 'heading': 'Role-Based Access Control',
     'text': 'RBAC role permissions owner admin editor read-only custom organization scoping'},
    {'section': 'Security', 'url_name': 'core:help_security',
     'anchor': 'audit-logging', 'heading': 'Audit Logging',
     'text': 'audit log action timestamp user change before after search filter export retention immutable'},
    {'section': 'Security', 'url_name': 'core:help_security',
     'anchor': 'data-protection', 'heading': 'Data Protection',
     'text': 'encryption rest transit TLS backup GDPR data privacy secure file'},

    # API
    {'section': 'API', 'url_name': 'core:help_api',
     'anchor': 'api-overview', 'heading': 'API Overview',
     'text': 'REST API GraphQL webhook API key authentication rate limit'},
    {'section': 'API', 'url_name': 'core:help_api',
     'anchor': 'authentication', 'heading': 'Authentication',
     'text': 'API key bearer token Authorization header profile settings generate'},
    {'section': 'API', 'url_name': 'core:help_api',
     'anchor': 'rest-api', 'heading': 'REST API',
     'text': 'REST endpoint assets passwords organizations vehicles monitors GET POST PUT DELETE'},
    {'section': 'API', 'url_name': 'core:help_api',
     'anchor': 'webhooks', 'heading': 'Webhooks',
     'text': 'webhook event payload asset created updated monitor down up vulnerability breach'},
    {'section': 'API', 'url_name': 'core:help_api',
     'anchor': 'filtering', 'heading': 'Filtering & Pagination',
     'text': 'filter search ordering pagination page size query parameter'},
]


def _highlight(text, query):
    """Wrap query matches in <mark> tags (case-insensitive)."""
    if not query:
        return text
    escaped = re.escape(query)
    return re.sub(f'({escaped})', r'<mark>\1</mark>', text, flags=re.IGNORECASE)


@login_required
def help_search(request):
    """Full-text search across all help sections."""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        q_lower = q.lower()
        seen = set()
        for entry in HELP_INDEX:
            key = (entry['url_name'], entry['anchor'])
            if key in seen:
                continue
            haystack = (
                entry['heading'] + ' ' +
                entry['text'] + ' ' +
                entry['section']
            ).lower()
            if q_lower in haystack:
                seen.add(key)
                results.append({
                    **entry,
                    'heading_hl': _highlight(entry['heading'], q),
                    'text_hl': _highlight(entry['text'], q),
                    'section_hl': _highlight(entry['section'], q),
                })
    return render(request, 'core/help/search_results.html', {
        'q': q,
        'results': results,
        'title': 'Help Search',
    })


@login_required
def help_index(request):
    """Main help documentation index"""
    sections = [
        {'icon': 'fa-rocket', 'title': 'Getting Started', 'url_name': 'core:help_getting_started',
         'desc': 'First steps, organizations, users, and API keys.'},
        {'icon': 'fa-server', 'title': 'Asset Management', 'url_name': 'core:help_assets',
         'desc': 'Track hardware, networks, racks, and ports.'},
        {'icon': 'fa-truck', 'title': 'Service Vehicles', 'url_name': 'core:help_vehicles',
         'desc': 'Fleet management, maintenance, fuel, and damage reports.'},
        {'icon': 'fa-lock', 'title': 'Password Vault', 'url_name': 'core:help_vault',
         'desc': 'Encrypted credential storage, breach detection, and TOTP.'},
        {'icon': 'fa-heartbeat', 'title': 'Monitoring', 'url_name': 'core:help_monitoring',
         'desc': 'Infrastructure checks, alerting, and dashboards.'},
        {'icon': 'fa-shield-alt', 'title': 'Security', 'url_name': 'core:help_security',
         'desc': 'Vulnerability scanning, RBAC, audit logging, and 2FA.'},
        {'icon': 'fa-plug', 'title': 'API & Integrations', 'url_name': 'core:help_api',
         'desc': 'REST API, webhooks, authentication, and client libraries.'},
    ]
    return render(request, 'core/help/index.html', {
        'title': 'Help & Documentation',
        'sections': sections,
    })


@login_required
def help_getting_started(request):
    """Getting started guide"""
    toc = [
        {'anchor': 'quick-start', 'heading': 'Quick Start'},
        {'anchor': 'organizations', 'heading': 'Organizations'},
        {'anchor': 'users-roles', 'heading': 'Users & Roles'},
        {'anchor': 'api-keys', 'heading': 'API Keys'},
    ]
    content = """
    <h4>Getting Started with ClientSt0r</h4>
    <p class="lead">Welcome! This guide walks you through setting up your instance and getting your team up and running.</p>

    <h5 class="mt-4" id="quick-start"><i class="fas fa-rocket"></i> Quick Start</h5>
    <ol>
        <li><strong>Log in</strong> — Use your credentials or Azure AD SSO if configured.</li>
        <li><strong>Create or select an Organization</strong> — All data is scoped to organizations.</li>
        <li><strong>Invite your team</strong> — Go to <em>Settings → Users</em> and invite members.</li>
        <li><strong>Assign roles</strong> — Grant appropriate permissions (Owner, Admin, Editor, Read-Only).</li>
        <li><strong>Add assets or passwords</strong> — Start populating your inventory or vault.</li>
        <li><strong>Set up monitoring</strong> — Create monitors for servers and services.</li>
    </ol>

    <h5 class="mt-4" id="organizations"><i class="fas fa-building"></i> Organizations</h5>
    <p>Organizations are the top-level containers for all data. ClientSt0r is multi-tenant — each client, department, or team has its own organization with full data isolation.</p>
    <ul>
        <li><strong>Create:</strong> <em>Admin → Organizations → New Organization</em></li>
        <li><strong>Switch:</strong> Use the organization selector in the top navigation</li>
        <li><strong>Scoping:</strong> Assets, passwords, vehicles, and monitors all belong to one organization</li>
        <li><strong>Global items:</strong> Some templates and reference data are shared across all organizations</li>
    </ul>

    <h5 class="mt-4" id="users-roles"><i class="fas fa-users"></i> Users &amp; Roles</h5>
    <p>Access control uses role-based permissions with four built-in roles:</p>
    <div class="table-responsive mt-3">
        <table class="table table-sm table-bordered">
            <thead><tr><th>Role</th><th>Capabilities</th></tr></thead>
            <tbody>
                <tr><td><span class="badge bg-danger">Owner</span></td><td>Full control including billing and organization deletion</td></tr>
                <tr><td><span class="badge bg-warning text-dark">Admin</span></td><td>Manage users, settings, all data — no billing</td></tr>
                <tr><td><span class="badge bg-primary">Editor</span></td><td>Create and edit data; cannot manage users or settings</td></tr>
                <tr><td><span class="badge bg-secondary">Read-Only</span></td><td>View data only; cannot create, edit, or delete</td></tr>
            </tbody>
        </table>
    </div>
    <p>Custom roles with 42 granular permissions are available for fine-grained control.</p>

    <h5 class="mt-4" id="api-keys"><i class="fas fa-key"></i> API Keys</h5>
    <p>API keys authenticate programmatic access to the REST API and the browser extension.</p>
    <ul>
        <li><strong>Generate:</strong> Click your username → <em>API Keys</em> → <em>Create New Key</em></li>
        <li><strong>Format:</strong> Keys are prefixed <code>itdocs_live_…</code></li>
        <li><strong>Usage:</strong> Pass as <code>Authorization: Bearer YOUR_KEY</code></li>
        <li><strong>Scope:</strong> Keys are tied to your user and inherit your organization access</li>
        <li><strong>Revoke:</strong> Delete a key instantly to invalidate all uses</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Getting Started',
        'section_id': 'getting-started',
        'prev_section': None,
        'next_section': {'title': 'Asset Management', 'url_name': 'core:help_assets'},
        'toc': toc,
        'content': content,
    })


@login_required
def help_features(request):
    """Features documentation"""
    features_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FEATURES.md')
    try:
        with open(features_path, 'r') as f:
            content = f.read()
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code', 'toc'])
    except Exception:
        html_content = "<p>Features documentation not available.</p>"

    return render(request, 'core/help/section.html', {
        'title': 'Features',
        'section_id': 'features',
        'toc': [],
        'content': html_content,
        'prev_section': None,
        'next_section': None,
    })


@login_required
def help_assets(request):
    """Asset management help"""
    toc = [
        {'anchor': 'asset-tracking', 'heading': 'Asset Tracking'},
        {'anchor': 'network-management', 'heading': 'Network Management'},
        {'anchor': 'rack-management', 'heading': 'Rack Management'},
        {'anchor': 'port-configuration', 'heading': 'Port Configuration'},
        {'anchor': 'asset-categories', 'heading': 'Asset Categories'},
        {'anchor': 'reporting', 'heading': 'Reporting & Analytics'},
    ]
    content = """
    <h4>Asset Management</h4>
    <p class="lead">Track and manage all IT equipment, servers, network devices, and hardware assets.</p>

    <h5 class="mt-4" id="asset-tracking"><i class="fas fa-server"></i> Asset Tracking</h5>
    <ul>
        <li><strong>Comprehensive Information:</strong> Track make, model, serial numbers, purchase dates, warranties</li>
        <li><strong>Custom Fields:</strong> Add unlimited custom fields for organization-specific needs</li>
        <li><strong>Attachments:</strong> Upload photos, manuals, invoices, and documentation</li>
        <li><strong>Relationships:</strong> Link related assets, dependencies, and parent/child relationships</li>
        <li><strong>QR Codes:</strong> Generate QR codes for physical asset labels</li>
        <li><strong>Lifecycle Tracking:</strong> Monitor asset status from purchase to retirement</li>
        <li><strong>Needs Reorder:</strong> Flag assets for physical replacement — visible in the asset list with a yellow badge</li>
    </ul>

    <div class="help-screenshot mt-3 mb-4">
      <svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" class="help-svg-screenshot">
        <rect width="700" height="200" rx="6" fill="#1a1f2e" stroke="#30363d"/>
        <!-- Table header -->
        <rect x="0" y="0" width="700" height="36" rx="6" fill="#161b22" stroke="#30363d"/>
        <rect x="0" y="18" width="700" height="18" fill="#161b22"/>
        <text x="16" y="22" fill="#8b949e" font-size="11" font-family="monospace">Name</text>
        <text x="200" y="22" fill="#8b949e" font-size="11" font-family="monospace">Type</text>
        <text x="320" y="22" fill="#8b949e" font-size="11" font-family="monospace">IP / Host</text>
        <text x="460" y="22" fill="#8b949e" font-size="11" font-family="monospace">Status</text>
        <text x="580" y="22" fill="#8b949e" font-size="11" font-family="monospace">Actions</text>
        <!-- Row 1 -->
        <rect x="0" y="36" width="700" height="40" fill="#0d1117" stroke="#21262d" stroke-width="0.5"/>
        <text x="16" y="60" fill="#e6edf3" font-size="12" font-family="sans-serif">Core Switch</text>
        <text x="200" y="60" fill="#79c0ff" font-size="11" font-family="sans-serif">Switch</text>
        <text x="320" y="60" fill="#8b949e" font-size="11" font-family="monospace">192.168.1.1</text>
        <rect x="460" y="48" width="54" height="18" rx="9" fill="#1f6feb"/>
        <text x="487" y="61" fill="#fff" font-size="10" font-family="sans-serif" text-anchor="middle">Active</text>
        <!-- Reorder badge callout -->
        <rect x="535" y="48" width="68" height="18" rx="9" fill="#d29922"/>
        <text x="569" y="61" fill="#fff" font-size="10" font-family="sans-serif" text-anchor="middle">↩ Reorder</text>
        <!-- Row 2 -->
        <rect x="0" y="76" width="700" height="40" fill="#161b22" stroke="#21262d" stroke-width="0.5"/>
        <text x="16" y="100" fill="#e6edf3" font-size="12" font-family="sans-serif">Rack A Server 1</text>
        <text x="200" y="100" fill="#79c0ff" font-size="11" font-family="sans-serif">Server</text>
        <text x="320" y="100" fill="#8b949e" font-size="11" font-family="monospace">192.168.1.10</text>
        <rect x="460" y="88" width="54" height="18" rx="9" fill="#1f6feb"/>
        <text x="487" y="101" fill="#fff" font-size="10" font-family="sans-serif" text-anchor="middle">Active</text>
        <!-- Row 3 -->
        <rect x="0" y="116" width="700" height="40" fill="#0d1117" stroke="#21262d" stroke-width="0.5"/>
        <text x="16" y="140" fill="#e6edf3" font-size="12" font-family="sans-serif">Patch Panel A</text>
        <text x="200" y="140" fill="#79c0ff" font-size="11" font-family="sans-serif">Patch Panel</text>
        <text x="320" y="140" fill="#8b949e" font-size="11" font-family="sans-serif">–</text>
        <rect x="460" y="128" width="68" height="18" rx="9" fill="#21262d"/>
        <text x="494" y="141" fill="#8b949e" font-size="10" font-family="sans-serif" text-anchor="middle">Inactive</text>
        <!-- Annotation: Reorder badge -->
        <line x1="569" y1="48" x2="620" y2="20" stroke="#f0b429" stroke-width="1.5" stroke-dasharray="4,2"/>
        <rect x="600" y="4" width="96" height="20" rx="10" fill="#f0b42966"/>
        <text x="648" y="18" fill="#f0b429" font-size="10" font-family="sans-serif" text-anchor="middle">Reorder flag</text>
      </svg>
      <p class="help-screenshot-caption">Asset list showing the yellow <strong>↩ Reorder</strong> badge on flagged assets. Use the filter bar to show only assets needing reorder.</p>
    </div>

    <h5 class="mt-4" id="network-management"><i class="fas fa-network-wired"></i> Network Management</h5>
    <ul>
        <li><strong>IP Address Management:</strong> Track IPs, subnets, VLANs</li>
        <li><strong>MAC Addresses:</strong> Record network interface details</li>
        <li><strong>Network Diagrams:</strong> Create visual network topology maps</li>
        <li><strong>Port Assignments:</strong> Track switch ports and patch panel connections</li>
    </ul>

    <h5 class="mt-4" id="rack-management"><i class="fas fa-warehouse"></i> Rack Management</h5>
    <ul>
        <li><strong>Data Centers:</strong> Organize assets by locations and data centers</li>
        <li><strong>Racks:</strong> Visual rack layout with U-space allocation</li>
        <li><strong>Drag &amp; Drop:</strong> Easily move devices between rack positions</li>
        <li><strong>Power Management:</strong> Track power consumption and capacity</li>
        <li><strong>Environmental Monitoring:</strong> Record temperature, humidity, and conditions</li>
    </ul>

    <h5 class="mt-4" id="port-configuration"><i class="fas fa-ethernet"></i> Port Configuration</h5>
    <p>Switches and patch panels support per-port configuration with VLAN management.</p>
    <ul>
        <li><strong>Switch ports:</strong> Set mode (Access / Trunk / Hybrid), native VLAN, tagged VLANs, speed, and status</li>
        <li><strong>Patch panel ports:</strong> Set label, destination cable, cable type, VLAN, and status</li>
        <li><strong>Bulk edit:</strong> Configure all ports in one screen — changes saved in a single click</li>
    </ul>

    <div class="help-screenshot mt-3 mb-4">
      <svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" class="help-svg-screenshot">
        <rect width="700" height="160" rx="6" fill="#1a1f2e" stroke="#30363d"/>
        <!-- Header row -->
        <rect x="0" y="0" width="700" height="32" rx="6" fill="#161b22" stroke="#30363d"/>
        <rect x="0" y="18" width="700" height="14" fill="#161b22"/>
        <text x="16" y="21" fill="#8b949e" font-size="10" font-family="monospace">Port #</text>
        <text x="80" y="21" fill="#8b949e" font-size="10" font-family="monospace">Description</text>
        <text x="240" y="21" fill="#8b949e" font-size="10" font-family="monospace">Mode</text>
        <text x="330" y="21" fill="#8b949e" font-size="10" font-family="monospace">Native VLAN</text>
        <text x="460" y="21" fill="#8b949e" font-size="10" font-family="monospace">Tagged VLANs</text>
        <text x="590" y="21" fill="#8b949e" font-size="10" font-family="monospace">Status</text>
        <!-- Port row -->
        <rect x="0" y="32" width="700" height="38" fill="#0d1117" stroke="#21262d" stroke-width="0.5"/>
        <text x="22" y="55" fill="#e6edf3" font-size="12" font-weight="bold" font-family="sans-serif" text-anchor="middle">1</text>
        <rect x="80" y="38" width="150" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="88" y="53" fill="#8b949e" font-size="10" font-family="sans-serif">Uplink to Core</text>
        <!-- Mode select -->
        <rect x="240" y="38" width="80" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="250" y="53" fill="#e6edf3" font-size="10" font-family="sans-serif">Trunk ▾</text>
        <!-- Native VLAN -->
        <rect x="330" y="38" width="120" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="340" y="53" fill="#e6edf3" font-size="10" font-family="sans-serif">VLAN 1 - Default ▾</text>
        <!-- Tagged -->
        <rect x="460" y="38" width="120" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="470" y="53" fill="#e6edf3" font-size="10" font-family="sans-serif">10, 20, 30 ▾</text>
        <!-- Status -->
        <rect x="590" y="38" width="80" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="600" y="53" fill="#3fb950" font-size="10" font-family="sans-serif">Active ▾</text>
        <!-- Port row 2 -->
        <rect x="0" y="70" width="700" height="38" fill="#161b22" stroke="#21262d" stroke-width="0.5"/>
        <text x="22" y="93" fill="#e6edf3" font-size="12" font-weight="bold" font-family="sans-serif" text-anchor="middle">2</text>
        <rect x="80" y="76" width="150" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="88" y="91" fill="#8b949e" font-size="10" font-family="sans-serif">Workstation A</text>
        <rect x="240" y="76" width="80" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="250" y="91" fill="#e6edf3" font-size="10" font-family="sans-serif">Access ▾</text>
        <rect x="330" y="76" width="120" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="340" y="91" fill="#e6edf3" font-size="10" font-family="sans-serif">VLAN 10 - Staff ▾</text>
        <rect x="460" y="76" width="120" height="22" rx="3" fill="#21262d" stroke="#30363d" opacity="0.4"/>
        <text x="470" y="91" fill="#555" font-size="10" font-family="sans-serif">(disabled)</text>
        <rect x="590" y="76" width="80" height="22" rx="3" fill="#21262d" stroke="#30363d"/>
        <text x="600" y="91" fill="#3fb950" font-size="10" font-family="sans-serif">Active ▾</text>
        <!-- Annotations -->
        <line x1="280" y1="38" x2="280" y2="14" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,2"/>
        <rect x="220" y="2" width="120" height="16" rx="8" fill="#1f6feb44"/>
        <text x="280" y="13" fill="#79c0ff" font-size="10" font-family="sans-serif" text-anchor="middle">Mode controls VLANs</text>
        <line x1="500" y1="108" x2="500" y2="138" stroke="#f0b429" stroke-width="1.5" stroke-dasharray="3,2"/>
        <rect x="420" y="138" width="160" height="16" rx="8" fill="#f0b42944"/>
        <text x="500" y="149" fill="#f0b429" font-size="10" font-family="sans-serif" text-anchor="middle">Disabled in Access mode</text>
      </svg>
      <p class="help-screenshot-caption">Port configuration table. <strong>Mode</strong> controls which VLAN fields are active — Tagged VLANs are disabled in Access mode.</p>
    </div>

    <h5 class="mt-4" id="asset-categories"><i class="fas fa-list"></i> Asset Categories</h5>
    <p>Supported asset types include:</p>
    <div class="row">
        <div class="col-md-6">
            <ul>
                <li>Servers &amp; Virtual Machines</li>
                <li>Network Equipment (switches, routers, firewalls)</li>
                <li>Storage Devices (NAS, SAN)</li>
                <li>Workstations &amp; Laptops</li>
            </ul>
        </div>
        <div class="col-md-6">
            <ul>
                <li>Mobile Devices (phones, tablets)</li>
                <li>Printers &amp; Peripherals</li>
                <li>Security Equipment (cameras, access control)</li>
                <li>Power Distribution (UPS, PDU)</li>
            </ul>
        </div>
    </div>

    <h5 class="mt-4" id="reporting"><i class="fas fa-chart-line"></i> Reporting &amp; Analytics</h5>
    <ul>
        <li><strong>Asset Reports:</strong> Generate reports on inventory, warranties, and costs</li>
        <li><strong>Export Options:</strong> Export data to CSV, PDF, or Excel</li>
        <li><strong>Depreciation Tracking:</strong> Monitor asset value over time</li>
        <li><strong>Warranty Alerts:</strong> Get notified before warranties expire</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Asset Management',
        'section_id': 'assets',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Getting Started', 'url_name': 'core:help_getting_started'},
        'next_section': {'title': 'Service Vehicles', 'url_name': 'core:help_vehicles'},
    })


@login_required
def help_vehicles(request):
    """Service vehicles help"""
    toc = [
        {'anchor': 'vehicle-tracking', 'heading': 'Vehicle Tracking'},
        {'anchor': 'insurance', 'heading': 'Insurance & Registration'},
        {'anchor': 'maintenance', 'heading': 'Maintenance Management'},
        {'anchor': 'fuel', 'heading': 'Fuel Tracking'},
        {'anchor': 'damage', 'heading': 'Damage Reporting'},
        {'anchor': 'vehicle-inventory', 'heading': 'Vehicle Inventory'},
        {'anchor': 'assignments', 'heading': 'User Assignments'},
    ]
    content = """
    <h4>Service Vehicle Fleet Management</h4>
    <p class="lead">Comprehensive fleet management for service vehicles with mileage tracking, maintenance scheduling, and inventory management.</p>

    <h5 class="mt-4" id="vehicle-tracking"><i class="fas fa-truck"></i> Vehicle Tracking</h5>
    <ul>
        <li><strong>Vehicle Information:</strong> Track make, model, year, VIN, license plate</li>
        <li><strong>Mileage Tracking:</strong> Automatic odometer updates from fuel logs</li>
        <li><strong>Vehicle Status:</strong> Monitor active, maintenance, or retired status</li>
        <li><strong>Condition Tracking:</strong> Rate condition from excellent to needs repair</li>
        <li><strong>GPS Location:</strong> Store current vehicle coordinates (lat/long)</li>
        <li><strong>User Assignments:</strong> Track who's using each vehicle</li>
    </ul>

    <h5 class="mt-4" id="insurance"><i class="fas fa-shield-alt"></i> Insurance &amp; Registration</h5>
    <ul>
        <li><strong>Insurance Tracking:</strong> Policy number, provider, expiration dates</li>
        <li><strong>Premium Management:</strong> Track insurance costs</li>
        <li><strong>Registration Expiry:</strong> Monitor registration renewal dates</li>
        <li><strong>Expiration Alerts:</strong> Get notified 30 days before expiration</li>
    </ul>

    <h5 class="mt-4" id="maintenance"><i class="fas fa-wrench"></i> Maintenance Management</h5>
    <ul>
        <li><strong>Service History:</strong> Complete maintenance and repair logs</li>
        <li><strong>Scheduled Maintenance:</strong> Oil changes, tire rotations, inspections</li>
        <li><strong>Cost Tracking:</strong> Labor and parts costs for each service</li>
        <li><strong>Next Due:</strong> Track next service by mileage or date</li>
        <li><strong>Overdue Detection:</strong> Automatic alerts for overdue maintenance</li>
        <li><strong>Service Providers:</strong> Record mechanics and service centers</li>
    </ul>

    <h5 class="mt-4" id="fuel"><i class="fas fa-gas-pump"></i> Fuel Tracking</h5>
    <ul>
        <li><strong>Fuel Logs:</strong> Record every fill-up with gallons and cost</li>
        <li><strong>MPG Calculation:</strong> Automatic miles-per-gallon tracking</li>
        <li><strong>Cost Analysis:</strong> Track fuel expenses per vehicle</li>
        <li><strong>Station Locations:</strong> Record where fuel was purchased</li>
        <li><strong>Trend Analysis:</strong> Monitor fuel efficiency over time</li>
    </ul>

    <h5 class="mt-4" id="damage"><i class="fas fa-car-crash"></i> Damage Reporting</h5>
    <ul>
        <li><strong>Incident Reports:</strong> Document damage with photos and descriptions</li>
        <li><strong>Severity Levels:</strong> Minor, moderate, major, or total loss</li>
        <li><strong>Repair Tracking:</strong> Monitor repair status from reported to completed</li>
        <li><strong>Cost Estimates:</strong> Track estimated and actual repair costs</li>
        <li><strong>Insurance Claims:</strong> Claim numbers and payout tracking</li>
        <li><strong>Photo Attachments:</strong> Upload damage photos for documentation</li>
        <li><strong>Side Diagrams:</strong> Click damage areas on the interactive vehicle diagram (driver and passenger sides)</li>
    </ul>

    <h5 class="mt-4" id="vehicle-inventory"><i class="fas fa-boxes"></i> Vehicle Inventory</h5>
    <ul>
        <li><strong>Equipment Tracking:</strong> Cables, connectors, hardware, tools</li>
        <li><strong>Quantity Management:</strong> Track item quantities and units</li>
        <li><strong>Low Stock Alerts:</strong> Get notified when inventory runs low</li>
        <li><strong>Value Tracking:</strong> Monitor total inventory value per vehicle</li>
        <li><strong>Categories:</strong> Organize by cables, tools, hardware, supplies</li>
        <li><strong>Storage Locations:</strong> Note where items are stored in vehicle</li>
    </ul>

    <h5 class="mt-4" id="assignments"><i class="fas fa-user-check"></i> User Assignments</h5>
    <ul>
        <li><strong>Assignment History:</strong> Track who used each vehicle and when</li>
        <li><strong>Mileage Records:</strong> Starting and ending mileage per assignment</li>
        <li><strong>Duration Tracking:</strong> Calculate how long each assignment lasted</li>
        <li><strong>Active Assignments:</strong> See current vehicle assignments</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Service Vehicles',
        'section_id': 'vehicles',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Asset Management', 'url_name': 'core:help_assets'},
        'next_section': {'title': 'Password Vault', 'url_name': 'core:help_vault'},
    })


@login_required
def help_vault(request):
    """Password vault help"""
    toc = [
        {'anchor': 'security-features', 'heading': 'Security Features'},
        {'anchor': 'breach-detection', 'heading': 'Breach Detection'},
        {'anchor': 'password-management', 'heading': 'Password Management'},
        {'anchor': 'password-generator', 'heading': 'Password Generator'},
        {'anchor': 'totp', 'heading': 'TOTP / Two-Factor Auth'},
        {'anchor': 'sharing', 'heading': 'Sharing & Collaboration'},
        {'anchor': 'import-export', 'heading': 'Import & Export'},
    ]
    content = """
    <h4>Password Vault</h4>
    <p class="lead">Securely store and manage credentials with AES-256 encryption, breach detection, and TOTP support.</p>

    <h5 class="mt-4" id="security-features"><i class="fas fa-lock"></i> Security Features</h5>
    <ul>
        <li><strong>AES-256 Encryption:</strong> Military-grade encryption for all stored passwords</li>
        <li><strong>Zero-Knowledge Architecture:</strong> Passwords encrypted at rest and in transit</li>
        <li><strong>Master Password:</strong> Organization-level encryption keys</li>
        <li><strong>Access Control:</strong> Role-based permissions for vault access</li>
        <li><strong>Audit Logging:</strong> Track every password access and modification</li>
    </ul>

    <h5 class="mt-4" id="breach-detection"><i class="fas fa-shield-alt"></i> Breach Detection</h5>
    <ul>
        <li><strong>Have I Been Pwned Integration:</strong> Check passwords against known breaches</li>
        <li><strong>Automatic Scanning:</strong> Regular checks for compromised credentials</li>
        <li><strong>Breach Alerts:</strong> Immediate notification if password found in breach</li>
        <li><strong>Security Score:</strong> Rate password strength and security</li>
        <li><strong>Reuse Detection:</strong> Identify duplicate passwords across accounts</li>
    </ul>

    <div class="help-screenshot mt-3 mb-4">
      <svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" class="help-svg-screenshot">
        <rect width="700" height="170" rx="6" fill="#1a1f2e" stroke="#30363d"/>
        <!-- Card -->
        <rect x="12" y="12" width="676" height="146" rx="6" fill="#161b22" stroke="#30363d"/>
        <!-- Title row -->
        <text x="28" y="38" fill="#e6edf3" font-size="14" font-weight="bold" font-family="sans-serif">company-server-root</text>
        <text x="28" y="54" fill="#8b949e" font-size="11" font-family="sans-serif">username: root   |   server.company.com</text>
        <!-- Breach badge -->
        <rect x="500" y="22" width="80" height="20" rx="10" fill="#da363344"/>
        <text x="540" y="36" fill="#f85149" font-size="10" font-family="sans-serif" text-anchor="middle">⚠ Breached</text>
        <!-- Password row -->
        <rect x="28" y="66" width="320" height="28" rx="4" fill="#0d1117" stroke="#30363d"/>
        <text x="44" y="84" fill="#8b949e" font-size="13" font-family="monospace" letter-spacing="4">••••••••••••</text>
        <!-- Reveal button -->
        <rect x="360" y="66" width="80" height="28" rx="4" fill="#21262d" stroke="#30363d"/>
        <text x="400" y="84" fill="#79c0ff" font-size="11" font-family="sans-serif" text-anchor="middle">👁 Reveal</text>
        <!-- Copy button -->
        <rect x="452" y="66" width="80" height="28" rx="4" fill="#21262d" stroke="#30363d"/>
        <text x="492" y="84" fill="#8b949e" font-size="11" font-family="sans-serif" text-anchor="middle">⧉ Copy</text>
        <!-- TOTP -->
        <rect x="28" y="106" width="150" height="28" rx="4" fill="#1f6feb22" stroke="#1f6feb66"/>
        <text x="44" y="124" fill="#79c0ff" font-size="13" font-family="monospace">⏱ 483 291</text>
        <text x="190" y="124" fill="#8b949e" font-size="10" font-family="sans-serif">expires in 18s</text>
        <!-- Annotations -->
        <line x1="540" y1="42" x2="580" y2="10" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
        <rect x="560" y="1" width="130" height="14" rx="7" fill="#da363344"/>
        <text x="625" y="12" fill="#f85149" font-size="10" font-family="sans-serif" text-anchor="middle">HIBP breach alert</text>
        <line x1="400" y1="66" x2="400" y2="44" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="3,2"/>
        <rect x="340" y="34" width="120" height="14" rx="7" fill="#1f6feb44"/>
        <text x="400" y="44" fill="#79c0ff" font-size="10" font-family="sans-serif" text-anchor="middle">Reveal shows plaintext</text>
        <line x1="103" y1="134" x2="60" y2="156" stroke="#3fb950" stroke-width="1.5" stroke-dasharray="3,2"/>
        <rect x="10" y="152" width="120" height="14" rx="7" fill="#1a7f3744"/>
        <text x="70" y="163" fill="#3fb950" font-size="10" font-family="sans-serif" text-anchor="middle">Live TOTP counter</text>
      </svg>
      <p class="help-screenshot-caption">Password entry with breach detection badge, reveal-on-click password, copy button, and live TOTP counter.</p>
    </div>

    <h5 class="mt-4" id="password-management"><i class="fas fa-key"></i> Password Management</h5>
    <ul>
        <li><strong>Organized Storage:</strong> Group passwords by category, client, or service</li>
        <li><strong>Quick Search:</strong> Fast search across all credentials</li>
        <li><strong>Copy Protection:</strong> Secure clipboard with auto-clear</li>
        <li><strong>Show/Hide:</strong> Toggle password visibility</li>
        <li><strong>Notes &amp; URLs:</strong> Store additional context and login URLs</li>
        <li><strong>Tags &amp; Labels:</strong> Organize with custom tags</li>
    </ul>

    <h5 class="mt-4" id="password-generator"><i class="fas fa-random"></i> Password Generator</h5>
    <ul>
        <li><strong>Strong Passwords:</strong> Generate cryptographically secure passwords</li>
        <li><strong>Customizable:</strong> Set length, character types, and complexity</li>
        <li><strong>Pronounceable Options:</strong> Create memorable yet secure passwords</li>
        <li><strong>Passphrase Generator:</strong> Multi-word passphrases for better memorability</li>
    </ul>

    <h5 class="mt-4" id="totp"><i class="fas fa-mobile-alt"></i> TOTP / Two-Factor Auth</h5>
    <ul>
        <li><strong>TOTP Storage:</strong> Store TOTP secrets alongside credentials</li>
        <li><strong>Live Counter:</strong> View the current 6-digit code with countdown timer</li>
        <li><strong>QR Code Setup:</strong> Scan QR codes directly from authenticator apps</li>
        <li><strong>Browser Extension:</strong> TOTP codes auto-copied during autofill</li>
    </ul>

    <h5 class="mt-4" id="sharing"><i class="fas fa-users"></i> Sharing &amp; Collaboration</h5>
    <ul>
        <li><strong>Secure Sharing:</strong> Share credentials within organization</li>
        <li><strong>Access Control:</strong> Grant read-only or full access</li>
        <li><strong>Temporary Access:</strong> Time-limited credential sharing</li>
        <li><strong>Sharing History:</strong> Track who accessed shared passwords</li>
    </ul>

    <h5 class="mt-4" id="import-export"><i class="fas fa-download"></i> Import &amp; Export</h5>
    <ul>
        <li><strong>Import from CSV:</strong> Bulk import from other password managers</li>
        <li><strong>LastPass Import:</strong> Direct import from LastPass export</li>
        <li><strong>1Password Import:</strong> Import from 1Password exports</li>
        <li><strong>Secure Export:</strong> Export encrypted backups</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Password Vault',
        'section_id': 'vault',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Service Vehicles', 'url_name': 'core:help_vehicles'},
        'next_section': {'title': 'Monitoring', 'url_name': 'core:help_monitoring'},
    })


@login_required
def help_monitoring(request):
    """Monitoring help"""
    toc = [
        {'anchor': 'system-monitoring', 'heading': 'System Monitoring'},
        {'anchor': 'alerting', 'heading': 'Alerting'},
        {'anchor': 'dashboards', 'heading': 'Dashboards & Visualization'},
        {'anchor': 'network-monitoring', 'heading': 'Network Monitoring'},
        {'anchor': 'website-monitoring', 'heading': 'Website Monitoring'},
        {'anchor': 'incident-management', 'heading': 'Incident Management'},
    ]
    content = """
    <h4>Infrastructure Monitoring</h4>
    <p class="lead">Monitor servers, network devices, and services with real-time alerts and comprehensive dashboards.</p>

    <h5 class="mt-4" id="system-monitoring"><i class="fas fa-heartbeat"></i> System Monitoring</h5>
    <ul>
        <li><strong>Server Monitoring:</strong> Track CPU, memory, disk usage, and uptime</li>
        <li><strong>Network Devices:</strong> Monitor switches, routers, firewalls</li>
        <li><strong>Service Checks:</strong> HTTP, HTTPS, TCP, UDP, ICMP ping</li>
        <li><strong>SSL Certificate Monitoring:</strong> Track expiration dates</li>
        <li><strong>Port Monitoring:</strong> Check if specific ports are open/closed</li>
        <li><strong>Response Time:</strong> Measure latency and performance</li>
    </ul>

    <h5 class="mt-4" id="alerting"><i class="fas fa-bell"></i> Alerting</h5>
    <ul>
        <li><strong>Real-time Alerts:</strong> Instant notifications for issues</li>
        <li><strong>Multiple Channels:</strong> Email, webhook, Slack, Teams</li>
        <li><strong>Alert Rules:</strong> Customize thresholds and conditions</li>
        <li><strong>Escalation Policies:</strong> Multi-tier alert escalation</li>
        <li><strong>Alert Grouping:</strong> Reduce alert fatigue with smart grouping</li>
        <li><strong>Maintenance Windows:</strong> Silence alerts during maintenance</li>
    </ul>

    <h5 class="mt-4" id="dashboards"><i class="fas fa-chart-line"></i> Dashboards &amp; Visualization</h5>
    <ul>
        <li><strong>Real-time Dashboards:</strong> Live status of all monitored systems</li>
        <li><strong>Historical Graphs:</strong> Performance trends over time</li>
        <li><strong>Custom Views:</strong> Create dashboards for specific clients or locations</li>
        <li><strong>Heat Maps:</strong> Visual status overview of infrastructure</li>
        <li><strong>Uptime Reports:</strong> SLA compliance tracking</li>
    </ul>

    <h5 class="mt-4" id="network-monitoring"><i class="fas fa-network-wired"></i> Network Monitoring</h5>
    <ul>
        <li><strong>Bandwidth Monitoring:</strong> Track network utilization</li>
        <li><strong>Latency Checks:</strong> Measure network response times</li>
        <li><strong>Packet Loss:</strong> Detect network quality issues</li>
        <li><strong>Port Scanning:</strong> Identify open ports and services</li>
        <li><strong>IP Reputation:</strong> Check for blacklisted IPs</li>
    </ul>

    <h5 class="mt-4" id="website-monitoring"><i class="fas fa-globe"></i> Website Monitoring</h5>
    <ul>
        <li><strong>Uptime Monitoring:</strong> Check if websites are accessible</li>
        <li><strong>Response Time:</strong> Measure page load speed</li>
        <li><strong>Status Code Checks:</strong> Detect 404, 500, and other errors</li>
        <li><strong>Content Monitoring:</strong> Verify expected content is present</li>
        <li><strong>SSL/TLS Checks:</strong> Monitor certificate validity</li>
    </ul>

    <h5 class="mt-4" id="incident-management"><i class="fas fa-history"></i> Incident Management</h5>
    <ul>
        <li><strong>Incident Timeline:</strong> Track when issues started and resolved</li>
        <li><strong>Root Cause Analysis:</strong> Document problem resolution</li>
        <li><strong>MTTR Tracking:</strong> Measure mean time to resolution</li>
        <li><strong>Post-mortems:</strong> Create detailed incident reports</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Monitoring',
        'section_id': 'monitoring',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Password Vault', 'url_name': 'core:help_vault'},
        'next_section': {'title': 'Security', 'url_name': 'core:help_security'},
    })


@login_required
def help_security(request):
    """Security features help"""
    toc = [
        {'anchor': 'vulnerability-scanning', 'heading': 'Vulnerability Scanning'},
        {'anchor': 'authentication', 'heading': 'Authentication & Access Control'},
        {'anchor': 'rbac', 'heading': 'Role-Based Access Control'},
        {'anchor': 'audit-logging', 'heading': 'Audit Logging'},
        {'anchor': 'data-protection', 'heading': 'Data Protection'},
        {'anchor': 'security-alerts', 'heading': 'Security Alerts'},
    ]
    content = """
    <h4>Security Features</h4>
    <p class="lead">Comprehensive security tools including vulnerability scanning, breach detection, and audit logging.</p>

    <h5 class="mt-4" id="vulnerability-scanning"><i class="fas fa-shield-alt"></i> Vulnerability Scanning</h5>
    <ul>
        <li><strong>Python Package Scanner:</strong> Scan Python dependencies for known vulnerabilities</li>
        <li><strong>OS Package Scanner:</strong> Check system packages for security updates</li>
        <li><strong>CVE Database:</strong> Integration with Common Vulnerabilities and Exposures database</li>
        <li><strong>Severity Ratings:</strong> CRITICAL, HIGH, MEDIUM, LOW classifications</li>
        <li><strong>Automated Scans:</strong> Scheduled security checks (hourly, daily, weekly)</li>
        <li><strong>Fix Recommendations:</strong> Suggested remediation actions</li>
        <li><strong>Historical Tracking:</strong> Monitor vulnerability trends over time</li>
    </ul>

    <h5 class="mt-4" id="authentication"><i class="fas fa-user-shield"></i> Authentication &amp; Access Control</h5>
    <ul>
        <li><strong>Two-Factor Authentication (2FA):</strong> TOTP-based 2FA with QR code setup</li>
        <li><strong>Azure AD Integration:</strong> Single sign-on with Microsoft Azure AD</li>
        <li><strong>Password Policies:</strong> Enforce strong password requirements</li>
        <li><strong>Session Management:</strong> Automatic timeout and secure session handling</li>
        <li><strong>IP Whitelisting:</strong> Restrict access by IP address</li>
        <li><strong>Failed Login Detection:</strong> Account lockout after repeated failures</li>
    </ul>

    <h5 class="mt-4" id="rbac"><i class="fas fa-user-tag"></i> Role-Based Access Control (RBAC)</h5>
    <ul>
        <li><strong>42 Granular Permissions:</strong> Fine-grained control over features</li>
        <li><strong>Custom Roles:</strong> Create organization-specific roles</li>
        <li><strong>Role Templates:</strong> Owner, Admin, Editor, Read-Only presets</li>
        <li><strong>Permission Inheritance:</strong> Hierarchical role structures</li>
        <li><strong>Organization Scoping:</strong> Isolate data by organization</li>
    </ul>

    <h5 class="mt-4" id="audit-logging"><i class="fas fa-clipboard-list"></i> Audit Logging</h5>
    <ul>
        <li><strong>Comprehensive Logs:</strong> Every action logged with timestamp and user</li>
        <li><strong>Change Tracking:</strong> Before/after values for all modifications</li>
        <li><strong>Search &amp; Filter:</strong> Query logs by user, action, date, or resource</li>
        <li><strong>Export Logs:</strong> Download audit trails for compliance</li>
        <li><strong>Retention Policies:</strong> Configurable log retention periods</li>
        <li><strong>Immutable Records:</strong> Logs cannot be modified or deleted</li>
    </ul>

    <h5 class="mt-4" id="data-protection"><i class="fas fa-lock"></i> Data Protection</h5>
    <ul>
        <li><strong>Encryption at Rest:</strong> Database encryption for sensitive data</li>
        <li><strong>Encryption in Transit:</strong> TLS 1.2+ for all connections</li>
        <li><strong>Secure File Storage:</strong> Encrypted file attachments</li>
        <li><strong>Backup Encryption:</strong> Encrypted database backups</li>
        <li><strong>GDPR Compliance:</strong> Data privacy and right-to-delete support</li>
    </ul>

    <h5 class="mt-4" id="security-alerts"><i class="fas fa-bell"></i> Security Alerts</h5>
    <ul>
        <li><strong>Vulnerability Alerts:</strong> Notify when new CVEs discovered</li>
        <li><strong>Breach Notifications:</strong> Alert when passwords found in breaches</li>
        <li><strong>Failed Login Alerts:</strong> Suspicious authentication attempts</li>
        <li><strong>Permission Changes:</strong> Notify on role or access modifications</li>
        <li><strong>Certificate Expiration:</strong> Warn before SSL certificates expire</li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'Security',
        'section_id': 'security',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Monitoring', 'url_name': 'core:help_monitoring'},
        'next_section': {'title': 'API & Integrations', 'url_name': 'core:help_api'},
    })


@login_required
def help_api(request):
    """API documentation"""
    toc = [
        {'anchor': 'api-overview', 'heading': 'API Overview'},
        {'anchor': 'authentication', 'heading': 'Authentication'},
        {'anchor': 'rest-api', 'heading': 'REST API'},
        {'anchor': 'webhooks', 'heading': 'Webhooks'},
        {'anchor': 'filtering', 'heading': 'Filtering & Pagination'},
    ]
    content = """
    <h4>API Documentation</h4>
    <p class="lead">Programmatic access to ClientSt0r via REST API, webhooks, and the browser extension.</p>

    <h5 class="mt-4" id="api-overview"><i class="fas fa-plug"></i> API Overview</h5>
    <ul>
        <li><strong>REST API:</strong> Full-featured RESTful API for all resources</li>
        <li><strong>Webhooks:</strong> Real-time event notifications to external services</li>
        <li><strong>API Keys:</strong> Secure bearer token authentication</li>
        <li><strong>Rate Limiting:</strong> Fair usage policies (100 req/min standard)</li>
        <li><strong>Browser Extension:</strong> Uses the same API with your personal key</li>
    </ul>

    <h5 class="mt-4" id="authentication"><i class="fas fa-key"></i> Authentication</h5>
    <p>Include your API key in every request header:</p>
    <div class="card mt-2 mb-3">
        <div class="card-body bg-dark">
            <code class="text-info">Authorization: Bearer itdocs_live_YOUR_KEY_HERE</code>
        </div>
    </div>
    <p>Generate API keys: <strong>Profile menu → API Keys → Create New Key</strong></p>

    <h5 class="mt-4" id="rest-api"><i class="fas fa-exchange-alt"></i> REST API</h5>
    <p><strong>Base URL:</strong> <code>https://your-server/api/</code></p>

    <table class="table table-sm mt-3">
        <thead><tr><th>Resource</th><th>Endpoint</th><th>Methods</th></tr></thead>
        <tbody>
            <tr><td>Assets</td><td><code>/api/assets/</code></td><td>GET, POST, PATCH, DELETE</td></tr>
            <tr><td>Passwords</td><td><code>/api/passwords/</code></td><td>GET, POST, PATCH, DELETE</td></tr>
            <tr><td>Organizations</td><td><code>/api/organizations/</code></td><td>GET, POST, PATCH, DELETE</td></tr>
            <tr><td>Vehicles</td><td><code>/api/vehicles/</code></td><td>GET, POST, PATCH, DELETE</td></tr>
            <tr><td>VLANs</td><td><code>/api/vlans/</code></td><td>GET, POST, PATCH, DELETE</td></tr>
        </tbody>
    </table>

    <pre class="bg-dark p-3 rounded mt-3"><code class="text-light">curl -s https://your-server/api/assets/ \\
  -H "Authorization: Bearer itdocs_live_xxxxx" \\
  | python3 -m json.tool</code></pre>

    <h5 class="mt-4" id="webhooks"><i class="fas fa-bell"></i> Webhooks</h5>
    <p>Configure webhooks at <strong>Settings → Webhooks → Create Webhook</strong>.</p>
    <p>Supported events:</p>
    <ul>
        <li><code>asset.created</code> / <code>asset.updated</code> / <code>asset.deleted</code></li>
        <li><code>password.created</code> / <code>password.breached</code></li>
        <li><code>monitor.down</code> / <code>monitor.up</code></li>
        <li><code>vulnerability.found</code></li>
        <li><code>vehicle.maintenance_due</code></li>
    </ul>

    <h5 class="mt-4" id="filtering"><i class="fas fa-filter"></i> Filtering &amp; Pagination</h5>
    <ul>
        <li><strong>Filter:</strong> <code>?asset_type=server&amp;organization=1</code></li>
        <li><strong>Search:</strong> <code>?search=server</code></li>
        <li><strong>Ordering:</strong> <code>?ordering=-created_at</code></li>
        <li><strong>Pagination:</strong> <code>?page=2&amp;page_size=50</code></li>
        <li><strong>Needs Reorder:</strong> <code>?needs_reorder=true</code></li>
    </ul>
    """
    return render(request, 'core/help/section.html', {
        'title': 'API & Integrations',
        'section_id': 'api',
        'toc': toc,
        'content': content,
        'prev_section': {'title': 'Security', 'url_name': 'core:help_security'},
        'next_section': None,
    })
