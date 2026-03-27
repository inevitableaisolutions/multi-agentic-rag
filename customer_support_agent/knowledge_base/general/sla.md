# Service Level Agreement (SLA)

## Overview

CloudSync Pro is committed to providing reliable, high-performance service. This SLA outlines our uptime guarantees, incident response commitments, and remedies for service disruptions. The full SLA applies to Pro and Enterprise plans. Free plans receive best-effort availability.

## Uptime Guarantee

| Plan | Monthly Uptime Guarantee |
|---|---|
| Free | Best effort (no SLA) |
| Pro | 99.5% |
| Enterprise | 99.9% |

Uptime is measured as the percentage of total minutes in a calendar month during which CloudSync Pro's core services (task management, file storage, API) are available. Scheduled maintenance windows are excluded from the calculation.

## Scheduled Maintenance

- Maintenance is performed during low-traffic windows: **Sundays, 2:00 AM - 6:00 AM UTC**
- Enterprise customers are notified 72 hours in advance via email and in-app banner
- Pro customers are notified 48 hours in advance
- Maintenance windows typically last 30-60 minutes. Extended maintenance (over 2 hours) requires 7-day advance notice.

## Incident Severity Levels

| Severity | Definition | Response Time (Enterprise) | Response Time (Pro) |
|---|---|---|---|
| P1 - Critical | Service completely unavailable for all users | 15 minutes | 1 hour |
| P2 - High | Major feature unavailable or significant performance degradation | 1 hour | 4 hours |
| P3 - Medium | Minor feature issue affecting some users | 4 hours | 12 hours |
| P4 - Low | Cosmetic issue or feature request | 1 business day | 3 business days |

## Incident Communication

During incidents:
- **Status page**: Real-time updates at status.cloudsyncpro.com
- **Email notifications**: Automatic alerts to workspace admins for P1 and P2 incidents
- **Post-incident report**: Published within 5 business days for P1 incidents, including root cause analysis and preventive measures

## Service Credits

If we fail to meet the uptime guarantee, eligible customers receive service credits:

| Monthly Uptime | Credit (% of Monthly Fee) |
|---|---|
| 99.0% - 99.9% | 10% |
| 95.0% - 99.0% | 25% |
| Below 95.0% | 50% |

To request a service credit:
1. Email sla@cloudsyncpro.com within 30 days of the incident
2. Include your workspace URL and the dates/times of the outage
3. Credits are applied to your next billing cycle within 10 business days

Service credits are the sole and exclusive remedy for SLA breaches. Credits do not exceed 50% of the monthly fee and cannot be converted to cash.

## Exclusions

The SLA does not cover downtime caused by:
- Force majeure events (natural disasters, war, government actions)
- Customer's internet connectivity issues
- Third-party service outages (e.g., AWS regional failure)
- Abuse or excessive API usage exceeding plan limits
- Pre-release or beta features
