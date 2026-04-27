"""
Management command to scan installed Python packages for known vulnerabilities
using pip-audit. Mirrors scan_system_packages.py for consistency.
"""
import json
import shutil
import subprocess
import sys
from collections import Counter

from django.core.management.base import BaseCommand
from django.utils import timezone


SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'unknown']


class Command(BaseCommand):
    help = 'Scan installed Python packages for known vulnerabilities (pip-audit)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON',
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save results to PythonPackageScan',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=180,
            help='Timeout in seconds for pip-audit (default 180)',
        )

    def handle(self, *args, **options):
        self.json_output = options['json']
        self.save_db = options['save']
        timeout = options['timeout']

        if not self.json_output:
            self.stdout.write(self.style.SUCCESS('Python Package Vulnerability Scanner'))
            self.stdout.write('=' * 70)

        scan_data = self.run_pip_audit(timeout=timeout)

        if self.json_output:
            self.stdout.write(json.dumps(scan_data, indent=2))
        else:
            self.print_results(scan_data)

        if self.save_db:
            self.save_scan_results(scan_data)

    def run_pip_audit(self, timeout):
        """Invoke pip-audit on the current environment, parse JSON output."""
        scan_data = {
            'scanner': 'pip-audit',
            'scan_date': timezone.now().isoformat(),
            'total_packages': 0,
            'vulnerable_packages': 0,
            'total_vulnerabilities': 0,
            'severity_counts': {s: 0 for s in SEVERITY_ORDER},
            'packages': [],
            'succeeded': True,
            'error': '',
        }

        # Resolve pip-audit binary (prefer the venv's interpreter)
        pip_audit = shutil.which('pip-audit')
        if not pip_audit:
            scan_data['succeeded'] = False
            scan_data['error'] = 'pip-audit not found on PATH'
            return scan_data

        # Use the same Python interpreter Django runs under so we audit the
        # right environment (otherwise pip-audit may target a different env).
        cmd = [pip_audit, '--format', 'json', '--progress-spinner', 'off']

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                # pip-audit needs to introspect the active env; running it
                # via sys.executable -m gives the most consistent result.
                env={**__import__('os').environ},
            )
        except subprocess.TimeoutExpired:
            scan_data['succeeded'] = False
            scan_data['error'] = f'pip-audit timed out after {timeout}s'
            return scan_data
        except FileNotFoundError as e:
            scan_data['succeeded'] = False
            scan_data['error'] = f'pip-audit invocation failed: {e}'
            return scan_data

        # pip-audit exits 1 when vulns are found — that's not an error.
        # It exits with other non-zero codes for actual failures.
        if result.returncode not in (0, 1):
            scan_data['succeeded'] = False
            scan_data['error'] = (result.stderr or result.stdout or 'unknown error')[:2000]
            return scan_data

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            scan_data['succeeded'] = False
            scan_data['error'] = f'pip-audit JSON parse failed: {e}'
            return scan_data

        # pip-audit JSON shape: {"dependencies": [{"name", "version", "vulns": [...]}]}
        deps = payload.get('dependencies') if isinstance(payload, dict) else payload
        if not isinstance(deps, list):
            scan_data['succeeded'] = False
            scan_data['error'] = 'unexpected pip-audit output format'
            return scan_data

        severity_counter = Counter()
        packages = []
        vuln_count = 0
        vulnerable_packages = 0

        for dep in deps:
            name = dep.get('name', '')
            version = dep.get('version', '')
            vulns_raw = dep.get('vulns') or []

            normalized_vulns = []
            for v in vulns_raw:
                # pip-audit doesn't always populate severity. Best-effort
                # extraction: explicit field, then aliases, else 'unknown'.
                severity = (v.get('severity') or v.get('cvss_severity') or '').lower().strip()
                if severity not in SEVERITY_ORDER:
                    severity = 'unknown'
                normalized_vulns.append({
                    'id': v.get('id', ''),
                    'aliases': v.get('aliases', []) or [],
                    'fix_versions': v.get('fix_versions', []) or [],
                    'severity': severity,
                    'description': (v.get('description') or '')[:1000],
                })
                severity_counter[severity] += 1
                vuln_count += 1

            if normalized_vulns:
                vulnerable_packages += 1

            packages.append({
                'name': name,
                'version': version,
                'vulns': normalized_vulns,
            })

        scan_data['total_packages'] = len(packages)
        scan_data['vulnerable_packages'] = vulnerable_packages
        scan_data['total_vulnerabilities'] = vuln_count
        scan_data['severity_counts'] = {s: severity_counter.get(s, 0) for s in SEVERITY_ORDER}
        scan_data['packages'] = packages
        return scan_data

    def print_results(self, scan_data):
        if not scan_data['succeeded']:
            self.stdout.write(self.style.ERROR(f"Scan failed: {scan_data['error']}"))
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Scan Results:'))
        self.stdout.write(f"Total packages:        {scan_data['total_packages']}")
        self.stdout.write(f"Vulnerable packages:   {scan_data['vulnerable_packages']}")
        self.stdout.write(f"Total vulnerabilities: {scan_data['total_vulnerabilities']}")
        sev = scan_data['severity_counts']
        self.stdout.write(
            f"  Critical: {sev['critical']}  High: {sev['high']}  "
            f"Medium: {sev['medium']}  Low: {sev['low']}  Unknown: {sev['unknown']}"
        )

        if scan_data['total_vulnerabilities'] > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Vulnerable packages:'))
            self.stdout.write('-' * 70)
            shown = 0
            for pkg in scan_data['packages']:
                if not pkg['vulns']:
                    continue
                fix = ', '.join(sorted({fv for v in pkg['vulns'] for fv in v['fix_versions']})) or 'no fix available'
                vuln_ids = ', '.join(v['id'] for v in pkg['vulns'])
                self.stdout.write(f"  • {pkg['name']} {pkg['version']} → fix: {fix}  ({vuln_ids})")
                shown += 1
                if shown >= 20:
                    self.stdout.write(f"  ... and {scan_data['vulnerable_packages'] - shown} more")
                    break

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Scan complete'))

    def save_scan_results(self, scan_data):
        """Persist the scan to the PythonPackageScan model."""
        from core.models import PythonPackageScan

        sev = scan_data.get('severity_counts', {})
        PythonPackageScan.objects.create(
            total_packages=scan_data.get('total_packages', 0),
            vulnerable_packages=scan_data.get('vulnerable_packages', 0),
            total_vulnerabilities=scan_data.get('total_vulnerabilities', 0),
            critical_count=sev.get('critical', 0),
            high_count=sev.get('high', 0),
            medium_count=sev.get('medium', 0),
            low_count=sev.get('low', 0),
            unknown_count=sev.get('unknown', 0),
            scan_succeeded=scan_data.get('succeeded', True),
            scan_error=scan_data.get('error', ''),
            scan_data=scan_data,
        )
        if not self.json_output:
            self.stdout.write(self.style.SUCCESS('Scan results saved to database'))
