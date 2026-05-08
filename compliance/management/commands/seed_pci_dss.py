"""Seed PCI-DSS v4.0 framework, categories, and check items.

Idempotent — re-running updates existing rows by slug, doesn't duplicate.
Run via: `python manage.py seed_pci_dss`.

Control numbers and titles reference PCI-DSS v4.0 (March 2022). Items
listed below are a representative subset; an MSP filling out the full
checklist would expand each category with its sub-requirements as
attestation needs grow.
"""
from django.core.management.base import BaseCommand

from compliance.models import (
    ComplianceCategory, ComplianceCheckItem, ComplianceFramework,
)

PCI_FRAMEWORK = {
    'slug': 'pci-dss-v4',
    'name': 'PCI-DSS',
    'version': 'v4.0',
    'description': (
        'Payment Card Industry Data Security Standard, version 4.0. '
        'Required for any merchant or service provider that stores, '
        'processes, or transmits cardholder data (CHD).'
    ),
    'recertification_default_days': 365,
}

# (category_slug, name, order, [(item_slug, item_name, description, evidence_hint), ...])
PCI_CATEGORIES = [
    ('req-1', 'Requirement 1: Install and maintain network security controls', 1, [
        ('1-2-1', 'Configuration standards for NSCs (1.2.1)',
         'Documented and implemented configuration standards for network security controls (firewalls, routers, switches, cloud security groups).',
         'Firewall config baselines, change-management tickets, periodic config reviews.'),
        ('1-2-5', 'Allowed services, protocols, and ports (1.2.5)',
         'All services, protocols, and ports allowed are identified, approved, and have a defined business need.',
         'Approved port/protocol matrix; rule-justification log on each firewall ACL.'),
        ('1-3-1', 'CDE network segmentation (1.3.1)',
         'Inbound traffic to the cardholder data environment (CDE) is restricted to only what is necessary.',
         'Network diagram showing CDE boundary; firewall ruleset export.'),
        ('1-4-1', 'NSCs between trusted/untrusted networks (1.4.1)',
         'Network security controls are implemented between trusted and untrusted networks (e.g., between corporate and DMZ; between DMZ and CDE).'
         '',
         'Topology diagram showing trust zones; firewall ACLs.'),
    ]),
    ('req-2', 'Requirement 2: Apply secure configurations to all system components', 2, [
        ('2-2-1', 'Configuration standards (2.2.1)',
         'Configuration standards for system components address all known security vulnerabilities and are consistent with industry-accepted definitions (CIS, NIST, etc.).',
         'CIS-benchmarked OS golden images; baseline scan reports.'),
        ('2-2-2', 'Vendor default accounts (2.2.2)',
         'Vendor default accounts are managed: removed, disabled, or have non-default credentials. Demonstrated via attestation per system class.',
         'Inventory of default accounts with disposition; change records.'),
        ('2-2-7', 'All non-console admin access encrypted (2.2.7)',
         'All non-console administrative access is encrypted using strong cryptography (SSH, TLS, VPN — not Telnet).',
         'Service inventory + protocol used; nessus / nmap scan results.'),
    ]),
    ('req-3', 'Requirement 3: Protect stored account data', 3, [
        ('3-3-1', 'Sensitive auth data not stored after auth (3.3.1)',
         'SAD (track data, CAV/CVV/CVC, PIN/PIN block) is not retained after authorization, even if encrypted.',
         'Data-flow diagram for SAD; data-retention policy; sample audit of card-data tables.'),
        ('3-4-1', 'PAN unreadable when stored (3.4.1)',
         'PAN is rendered unreadable wherever stored — encryption / truncation / tokenization / one-way hashes.',
         'Encryption-at-rest evidence (DB column encryption configs, key management policy).'),
        ('3-5-1', 'Cryptographic key protection (3.5.1)',
         'Keys used to render PAN unreadable are protected against disclosure and misuse.',
         'KMS / HSM config; key-rotation policy; access-control list for key custodians.'),
    ]),
    ('req-4', 'Requirement 4: Protect cardholder data with strong cryptography during transmission', 4, [
        ('4-2-1', 'Strong crypto in transit (4.2.1)',
         'PAN is protected with strong cryptography whenever it is sent over open, public networks (TLS 1.2+ / IPSec).',
         'TLS configuration of all card-handling endpoints; SSL Labs A+ rating.'),
        ('4-2-1-1', 'Trusted certificates only (4.2.1.1)',
         'Only trusted keys and certificates are accepted by card-handling endpoints.',
         'Cert pinning / CA allowlist policy; cert-management process.'),
    ]),
    ('req-5', 'Requirement 5: Protect all systems and networks from malicious software', 5, [
        ('5-2-1', 'Anti-malware deployed (5.2.1)',
         'An anti-malware solution is deployed on all system components, except those identified in 5.2.3 as not commonly affected by malware.',
         'EDR/AV deployment report; coverage by host inventory.'),
        ('5-3-2', 'Anti-malware kept current (5.3.2)',
         'The anti-malware solution\'s definitions/signatures are kept current.',
         'EDR console showing per-agent definition age; alert thresholds.'),
        ('5-3-4', 'Anti-malware logs preserved (5.3.4)',
         'Anti-malware mechanisms generate audit logs in accordance with 10.5.1 retention.',
         'EDR log retention configuration; SIEM ingestion proof.'),
    ]),
    ('req-6', 'Requirement 6: Develop and maintain secure systems and software', 6, [
        ('6-2-1', 'Bespoke software developed securely (6.2.1)',
         'Bespoke and custom software is developed in accordance with PCI-DSS, secure-coding guidelines, and industry standards.',
         'SDLC policy; secure-coding training records; SAST scan in CI.'),
        ('6-3-1', 'Vulnerabilities identified and ranked (6.3.1)',
         'Security vulnerabilities are identified through a defined process (CVE feeds, vendor advisories) and assigned a risk ranking.',
         'Vuln-management workflow; severity-ranking policy.'),
        ('6-3-3', 'Critical/high vulns patched in 30 days (6.3.3)',
         'All system components are protected from known vulnerabilities by installing applicable security patches/updates within one month for critical vulns.',
         'Patch-management report; SLA-compliance metrics.'),
    ]),
    ('req-7', 'Requirement 7: Restrict access to system components and cardholder data by business need to know', 7, [
        ('7-2-1', 'Access-control system in place (7.2.1)',
         'An access-control system is in place that restricts access based on a user\'s need to know and is set to "deny all" by default.',
         'IAM policy; role-to-permission matrix.'),
        ('7-2-4', 'User accounts reviewed at least every 6 months (7.2.4)',
         'All user accounts and related access privileges, including third-party/vendor accounts, are reviewed at least once every six months.',
         'Last access-review report (per-user, per-system).'),
        ('7-2-5', 'Application/system accounts least-privileged (7.2.5)',
         'All application and system accounts and their access are managed; least-privilege; reviewed periodically.',
         'Service-account inventory; per-account privilege scope.'),
    ]),
    ('req-8', 'Requirement 8: Identify users and authenticate access to system components', 8, [
        ('8-3-1', 'Strong cryptography on auth factors (8.3.1)',
         'All authentication factors are rendered unreadable using strong cryptography (in storage and transit).',
         'Password-storage hash function (bcrypt/argon2); TLS on auth endpoints.'),
        ('8-3-6', 'Min password length (8.3.6)',
         'If passwords are used as the only authentication factor, they meet a minimum length of 12 characters (or 8 with multi-factor).',
         'Password policy in IAM; sample-account password complexity.'),
        ('8-4-2', 'MFA for all non-console access (8.4.2)',
         'MFA is implemented for all non-console access into the CDE for personnel with administrative access.',
         'MFA enrollment report; SSO / IdP audit log.'),
        ('8-4-3', 'MFA for all remote access (8.4.3)',
         'MFA is implemented for all remote network access from outside the entity\'s network.',
         'VPN / Zero-trust MFA logs.'),
    ]),
    ('req-9', 'Requirement 9: Restrict physical access to cardholder data', 9, [
        ('9-1-1', 'Physical security policies (9.1.1)',
         'Physical security policies and operational procedures are documented, kept up to date, in use, and known to all personnel.',
         'Facility access policy; sign-in log review.'),
        ('9-2-1', 'Physical access controls enforced (9.2.1)',
         'Appropriate facility entry controls are in use to restrict and monitor physical access to systems in the CDE.',
         'Badge system access logs; visitor logbook.'),
        ('9-4-7', 'Media destruction (9.4.7)',
         'Electronic media containing CHD is rendered unrecoverable when no longer needed (per NIST 800-88 or equivalent).',
         'Destruction certificates from disposal vendor.'),
    ]),
    ('req-10', 'Requirement 10: Log and monitor all access to system components and cardholder data', 10, [
        ('10-2-1', 'Audit logs enabled for all (10.2.1)',
         'Audit logs are enabled and active for all system components and cardholder data.',
         'Centralized log inventory; SIEM coverage report.'),
        ('10-3-3', 'Logs centralized + protected (10.3.3)',
         'Audit log files are promptly backed up to a secure, central, internal log server / SIEM that is difficult to alter.',
         'SIEM ingestion; immutability config (e.g., S3 Object Lock).'),
        ('10-4-1', 'Daily log review (10.4.1)',
         'Audit logs are reviewed at least daily, including review of security events, alerts, and anomalies.',
         'Daily SIEM dashboard sign-off; on-call review log.'),
    ]),
    ('req-11', 'Requirement 11: Test security of systems and networks regularly', 11, [
        ('11-3-1', 'Internal vuln scans quarterly (11.3.1)',
         'Internal vulnerability scans are performed at least once every 3 months.',
         'Quarterly Nessus / OpenVAS scan reports.'),
        ('11-3-2', 'External ASV scans quarterly (11.3.2)',
         'External vulnerability scans are performed at least every three months by a PCI SSC-approved scanning vendor (ASV).',
         'ASV-issued scan reports for last 4 quarters.'),
        ('11-4-1', 'Penetration testing annually (11.4.1)',
         'External and internal penetration testing is performed at least annually.',
         'Annual pen-test report from qualified provider.'),
    ]),
    ('req-12', 'Requirement 12: Support information security with organizational policies and programs', 12, [
        ('12-1-1', 'Overall InfoSec policy (12.1.1)',
         'An overall information-security policy is established, published, maintained, and disseminated to all relevant personnel.',
         'Latest InfoSec policy doc; signed acknowledgement records.'),
        ('12-3-1', 'Risk-assessment process (12.3.1)',
         'Risks to the CDE are formally identified, evaluated, and managed at least annually.',
         'Last risk-assessment report; remediation tracking.'),
        ('12-6-1', 'Security awareness training (12.6.1)',
         'A formal security-awareness program is implemented to make all personnel aware of the entity\'s InfoSec policy and procedures.',
         'Training completion records; phishing-test results.'),
        ('12-10-1', 'Incident response plan (12.10.1)',
         'An incident-response plan exists and is ready to be activated in the event of a suspected or confirmed security incident.',
         'IR playbook; tabletop-exercise records.'),
    ]),
]


class Command(BaseCommand):
    help = 'Seed PCI-DSS v4.0 framework, categories, and check items.'

    def handle(self, *args, **opts):
        fw, _ = ComplianceFramework.objects.update_or_create(
            slug=PCI_FRAMEWORK['slug'],
            defaults={k: v for k, v in PCI_FRAMEWORK.items() if k != 'slug'},
        )
        cat_count = 0
        item_count = 0
        for cat_slug, cat_name, cat_order, items in PCI_CATEGORIES:
            cat, _ = ComplianceCategory.objects.update_or_create(
                framework=fw, slug=cat_slug,
                defaults={'name': cat_name, 'order': cat_order},
            )
            cat_count += 1
            for idx, (item_slug, item_name, desc, hint) in enumerate(items, start=1):
                ComplianceCheckItem.objects.update_or_create(
                    category=cat, slug=item_slug,
                    defaults={
                        'name': item_name,
                        'description': desc,
                        'evidence_hint': hint,
                        'order': idx,
                    },
                )
                item_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'PCI-DSS v4.0 seeded: 1 framework, {cat_count} categories, '
            f'{item_count} check items.'
        ))
