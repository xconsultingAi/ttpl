# Security Policy

## Supported Versions

| Version      | Supported          |
| ------------ | ------------------ |
| `version-16` | :white_check_mark: |
| `develop`    | :x:                |

## Reporting a Vulnerability

We take the security of TTPL seriously. If you discover a security vulnerability, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email **masharfaroo@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within **48 hours**.
- **Assessment**: We will assess the severity and impact within **5 business days**.
- **Resolution**: We aim to release a fix within **30 days** of confirmation, depending on complexity.
- **Credit**: We will credit you in the release notes (unless you prefer to remain anonymous).

### Scope

The following are in scope:

- The TTPL application code (Python controllers, overrides, reports, print formats)
- Custom fields, permissions, and query conditions introduced by this app
- API endpoints exposed by this app

The following are out of scope:

- Vulnerabilities in Frappe Framework or ERPNext (report these to their respective projects)
- Issues in third-party dependencies (report upstream, but let us know so we can update)
- Social engineering attacks
- Denial of service attacks

## Security Best Practices for Deployers

- Always run the site behind HTTPS
- Keep Frappe, ERPNext, and TTPL updated to the latest patch releases
- Use strong passwords and enable two-factor authentication
- Review user roles and report permissions regularly
- Restrict access to financial reports (Banking Detail, Contribution Margin, Tax Withholding) to authorized users only
