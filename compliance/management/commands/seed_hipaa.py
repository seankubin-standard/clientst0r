"""Seed HIPAA Security Rule framework, categories, and check items.

Idempotent — re-running updates by slug, doesn't duplicate.
Run via: `python manage.py seed_hipaa`.

Control numbers reference the HIPAA Security Rule (45 CFR Part 164,
Subpart C). Items below cover the major standards in each safeguard
category; an MSP filling out the full attestation would extend each
category with the rule's implementation specifications as needed.
"""
from django.core.management.base import BaseCommand

from compliance.models import (
    ComplianceCategory, ComplianceCheckItem, ComplianceFramework,
)

HIPAA_FRAMEWORK = {
    'slug': 'hipaa-security-rule',
    'name': 'HIPAA Security Rule',
    'version': '2013 Omnibus',
    'description': (
        'HIPAA Security Rule (45 CFR Part 164, Subpart C). '
        'Required for covered entities and business associates that '
        'create, receive, maintain, or transmit electronic protected '
        'health information (ePHI).'
    ),
    'recertification_default_days': 365,
}

# (cat_slug, name, order, [(item_slug, item_name, description, evidence_hint), ...])
HIPAA_CATEGORIES = [
    ('admin-safeguards', 'Administrative Safeguards (45 CFR 164.308)', 1, [
        ('164-308-a-1-i', 'Security Management Process (164.308(a)(1)(i))',
         'Implement policies and procedures to prevent, detect, contain, and correct security violations.',
         'Written InfoSec policy; roles + responsibilities matrix; periodic review record.'),
        ('164-308-a-1-ii-A', 'Risk Analysis (164.308(a)(1)(ii)(A))',
         'Conduct an accurate and thorough assessment of the potential risks and vulnerabilities to the confidentiality, integrity, and availability of ePHI.',
         'Most recent risk assessment report; threat model; risk register.'),
        ('164-308-a-1-ii-B', 'Risk Management (164.308(a)(1)(ii)(B))',
         'Implement security measures sufficient to reduce risks and vulnerabilities to a reasonable and appropriate level.',
         'Remediation plan + tracker; mitigation evidence per risk.'),
        ('164-308-a-1-ii-C', 'Sanction Policy (164.308(a)(1)(ii)(C))',
         'Apply appropriate sanctions against workforce members who fail to comply with the security policies and procedures.',
         'HR sanction policy doc; sample disciplinary records (redacted).'),
        ('164-308-a-1-ii-D', 'Information System Activity Review (164.308(a)(1)(ii)(D))',
         'Implement procedures to regularly review records of information system activity (audit logs, access reports, security incident reports).',
         'SIEM dashboard; weekly log review checklist + sign-off.'),
        ('164-308-a-2', 'Assigned Security Responsibility (164.308(a)(2))',
         'Identify the security official who is responsible for the development and implementation of the Security Rule policies and procedures.',
         'Security officer appointment letter; org chart highlighting role.'),
        ('164-308-a-3-i', 'Workforce Security (164.308(a)(3)(i))',
         'Implement policies and procedures to ensure that all workforce members have appropriate access to ePHI, and to prevent those who do not have access from obtaining it.',
         'Onboarding access-grant checklist; offboarding access-revoke procedure.'),
        ('164-308-a-4-i', 'Information Access Management (164.308(a)(4)(i))',
         'Implement policies and procedures for authorizing access to ePHI consistent with the applicable requirements of 164.308.',
         'Access-request workflow (ticket history); role-to-permission matrix.'),
        ('164-308-a-5-i', 'Security Awareness and Training (164.308(a)(5)(i))',
         'Implement a security awareness and training program for all members of its workforce (including management).',
         'Training curriculum; completion records; phishing-test results.'),
        ('164-308-a-6-i', 'Security Incident Procedures (164.308(a)(6)(i))',
         'Implement policies and procedures to address security incidents.',
         'Incident response plan; recent incident reports; tabletop exercise records.'),
        ('164-308-a-7-i', 'Contingency Plan (164.308(a)(7)(i))',
         'Establish (and implement as needed) policies and procedures for responding to an emergency or other occurrence (fire, vandalism, system failure, natural disaster) that damages systems containing ePHI.',
         'Disaster-recovery plan; business-continuity plan; last DR test report.'),
        ('164-308-a-8', 'Evaluation (164.308(a)(8))',
         'Perform a periodic technical and non-technical evaluation, based initially upon the standards implemented under this rule, and subsequently in response to environmental or operational changes affecting the security of ePHI.',
         'Annual security review; gap analysis; remediation tracker.'),
        ('164-308-b-1', 'Business Associate Contracts (164.308(b)(1))',
         'Permit a business associate to create, receive, maintain, or transmit ePHI on the covered entity\'s behalf only if it obtains satisfactory assurances that the business associate will appropriately safeguard the information.',
         'BAA inventory; copies of executed BAAs with all vendors handling ePHI.'),
    ]),
    ('physical-safeguards', 'Physical Safeguards (45 CFR 164.310)', 2, [
        ('164-310-a-1', 'Facility Access Controls (164.310(a)(1))',
         'Implement policies and procedures to limit physical access to electronic information systems and the facility(ies) in which they are housed, while ensuring that properly authorized access is allowed.',
         'Badge-access system logs; visitor sign-in book; data-center contract.'),
        ('164-310-a-2-i', 'Contingency Operations (164.310(a)(2)(i))',
         'Establish (and implement as needed) procedures that allow facility access in support of restoration of lost data under the disaster recovery plan and emergency mode operations plan.',
         'Emergency-access procedure doc; test drill records.'),
        ('164-310-a-2-ii', 'Facility Security Plan (164.310(a)(2)(ii))',
         'Implement policies and procedures to safeguard the facility and the equipment therein from unauthorized physical access, tampering, and theft.',
         'Facility security plan; CCTV coverage map; alarm system records.'),
        ('164-310-b', 'Workstation Use (164.310(b))',
         'Implement policies and procedures that specify the proper functions to be performed, the manner in which those functions are to be performed, and the physical attributes of the surroundings of a specific workstation or class of workstation that can access ePHI.',
         'Acceptable-use policy; workstation lockdown configs.'),
        ('164-310-c', 'Workstation Security (164.310(c))',
         'Implement physical safeguards for all workstations that access ePHI, to restrict access to authorized users.',
         'Cable lock / kensington inventory; locked-screen policy + idle timeout config.'),
        ('164-310-d-1', 'Device and Media Controls (164.310(d)(1))',
         'Implement policies and procedures that govern the receipt and removal of hardware and electronic media that contain ePHI, into and out of a facility, and the movement of these items within the facility.',
         'Asset register with disposition events; media-handling policy.'),
        ('164-310-d-2-i', 'Disposal (164.310(d)(2)(i))',
         'Implement policies and procedures to address the final disposition of ePHI, and/or the hardware or electronic media on which it is stored.',
         'Destruction certificates from disposal vendor; on-site shred logs.'),
        ('164-310-d-2-ii', 'Media Re-use (164.310(d)(2)(ii))',
         'Implement procedures for removal of ePHI from electronic media before the media are made available for re-use.',
         'Wipe procedure (NIST 800-88 reference); attestation log per device.'),
    ]),
    ('technical-safeguards', 'Technical Safeguards (45 CFR 164.312)', 3, [
        ('164-312-a-1', 'Access Control (164.312(a)(1))',
         'Implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to those persons or software programs that have been granted access rights as specified in 164.308(a)(4).',
         'IAM configuration; per-system access matrix.'),
        ('164-312-a-2-i', 'Unique User Identification (164.312(a)(2)(i))',
         'Assign a unique name and/or number for identifying and tracking user identity.',
         'IAM user inventory; no shared accounts attestation.'),
        ('164-312-a-2-ii', 'Emergency Access Procedure (164.312(a)(2)(ii))',
         'Establish (and implement as needed) procedures for obtaining necessary ePHI during an emergency.',
         'Break-glass access procedure; emergency-access ticket history.'),
        ('164-312-a-2-iii', 'Automatic Logoff (164.312(a)(2)(iii))',
         'Implement electronic procedures that terminate an electronic session after a predetermined time of inactivity.',
         'Idle-timeout settings (per system); workstation policy.'),
        ('164-312-a-2-iv', 'Encryption and Decryption (164.312(a)(2)(iv))',
         'Implement a mechanism to encrypt and decrypt ePHI.',
         'Disk-encryption coverage report; database column encryption configs.'),
        ('164-312-b', 'Audit Controls (164.312(b))',
         'Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI.',
         'Centralized audit log inventory; SIEM ingestion proof; log retention policy.'),
        ('164-312-c-1', 'Integrity (164.312(c)(1))',
         'Implement policies and procedures to protect ePHI from improper alteration or destruction.',
         'Database backup procedure; integrity-monitoring tool (e.g. file-integrity monitor) reports.'),
        ('164-312-c-2', 'Mechanism to Authenticate ePHI (164.312(c)(2))',
         'Implement electronic mechanisms to corroborate that ePHI has not been altered or destroyed in an unauthorized manner.',
         'Hash/checksum on backups; FIM alert configuration.'),
        ('164-312-d', 'Person or Entity Authentication (164.312(d))',
         'Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed.',
         'MFA enrollment report; SSO IdP audit log.'),
        ('164-312-e-1', 'Transmission Security (164.312(e)(1))',
         'Implement technical security measures to guard against unauthorized access to ePHI that is being transmitted over an electronic communications network.',
         'TLS configuration of all ePHI-handling endpoints; VPN / IPSec for site-to-site.'),
        ('164-312-e-2-i', 'Integrity Controls (164.312(e)(2)(i))',
         'Implement security measures to ensure that electronically transmitted ePHI is not improperly modified without detection until disposed of.',
         'TLS in transit; message signing where applicable.'),
        ('164-312-e-2-ii', 'Encryption (164.312(e)(2)(ii))',
         'Implement a mechanism to encrypt ePHI whenever deemed appropriate.',
         'TLS 1.2+ enforcement; SSL Labs report.'),
    ]),
]


class Command(BaseCommand):
    help = 'Seed HIPAA Security Rule framework, categories, and check items.'

    def handle(self, *args, **opts):
        fw, _ = ComplianceFramework.objects.update_or_create(
            slug=HIPAA_FRAMEWORK['slug'],
            defaults={k: v for k, v in HIPAA_FRAMEWORK.items() if k != 'slug'},
        )
        cat_count = 0
        item_count = 0
        for cat_slug, cat_name, cat_order, items in HIPAA_CATEGORIES:
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
            f'HIPAA Security Rule seeded: 1 framework, {cat_count} '
            f'categories, {item_count} check items.'
        ))
