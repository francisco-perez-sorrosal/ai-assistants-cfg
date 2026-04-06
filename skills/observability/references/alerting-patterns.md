# Alerting Patterns

Alerting strategy, SLO-based burn rate alerting, error budgets, runbook design, and on-call practices. Reference material for the [Observability](../SKILL.md) skill.

## Symptom vs Cause Alerting

| Approach | What It Detects | Pros | Cons |
|----------|-----------------|------|------|
| **Symptom-based** | User-visible impact (error rate up, latency high) | Low noise, actionable, catches novel failures | Slower to detect (users already affected) |
| **Cause-based** | Underlying issue (disk full, CPU saturated) | Can be predictive, catches before user impact | High noise, many false positives, misses novel causes |

**Expert consensus**: Alert on symptoms, investigate causes. Monitor everything but page only on user-facing symptoms or imminent failures.

Symptom-based alerting catches failures you did not anticipate because it measures what users experience, not what you predicted could go wrong. A novel database contention issue you never predicted still shows up as elevated latency or error rate -- symptoms catch it without a dedicated cause-based rule.

Cause-based alerts are valuable on dashboards for investigation but should rarely trigger pages. The exception is imminent resource exhaustion (disk > 95% full, certificate expiring in < 7 days) where waiting for user-visible symptoms means data loss or outage.

**Practical layering**: Use symptom alerts for paging, cause alerts for dashboard monitoring, and predictive alerts (resource exhaustion trends) for ticket-level early warnings.

## SLO-Based Alerting (Burn Rate)

Google SRE's multi-window, multi-burn-rate approach replaces static threshold alerting with budget-aware detection. The core idea: alert when the error budget is being consumed faster than it should be.

Static thresholds suffer from a fundamental problem: they either fire too late (threshold too high) or too often (threshold too low). Burn rate alerting solves this by measuring the *rate of budget consumption* relative to the SLO window, automatically adapting to the service's reliability target.

### Burn Rate Windows

| Severity | Long Window | Short Window | Burn Rate | Budget Impact | Response |
|----------|-------------|--------------|-----------|---------------|----------|
| **Page (critical)** | 1 hour | 5 min | 14.4x | 2% consumed | Immediate |
| **Page (high)** | 6 hours | 30 min | 6x | 5% consumed | Within hours |
| **Ticket** | 3 days | 6 hours | 1x | 10% consumed | Next business day |

### How Burn Rate Works

**Formula**: `burn_rate x alerting_window / period = budget_consumed`

For a 30-day error budget window with a 99.9% SLO (0.1% budget):
- A burn rate of **14.4x** over 1 hour consumes **2%** of the monthly budget -- enough to warrant immediate response
- A burn rate of **6x** over 6 hours consumes **5%** -- serious but not emergent
- A burn rate of **1x** over 3 days consumes **10%** -- steady degradation, ticket-level

### Dual-Window Rationale

Both windows must fire before the alert triggers:

- **Long window** detects meaningful budget consumption over time -- filters out momentary spikes
- **Short window** confirms the burn is actively happening now -- prevents false positives from past incidents that already resolved

Without the short window, a resolved 2-hour outage from yesterday could still trigger alerts for hours afterward as the long window slides over the incident period.

**Implementation note**: Most monitoring systems (Prometheus, Datadog, Grafana Cloud) support multi-window burn rate alerting natively or via recording rules. Start with the three severity levels above, then tune windows based on operational experience.

## Error Budget Policies

The error budget is not just a monitoring concept -- it is a negotiation tool between reliability and velocity.

**Budget = 1 - SLO target**. For a 99.9% SLO over 30 days, the budget is 43.2 minutes of downtime (or equivalent error volume).

### When Error Budget Is Exhausted

- **Freeze feature deployments**: No non-critical changes until budget recovers
- **Redirect engineering effort**: Development time shifts to reliability work
- **Require SRE approval**: All changes need sign-off from the reliability team
- **Post-mortem required**: Any further budget consumption triggers a mandatory post-mortem

### Budget Window Practices

- Use **monthly** windows for operational decisions (deployment freezes, resource allocation)
- Use **quarterly** windows for strategic planning (headcount, infrastructure investment)
- Reset at the start of each window -- do not carry deficits or surpluses
- Track burn rate trends over multiple windows to detect systemic reliability issues

Error budget is a negotiation tool: when budget is healthy, product teams can ship faster with higher risk tolerance. When budget is low, reliability takes priority. This creates a self-regulating feedback loop -- the team that ships a buggy release feels the consequence through reduced deployment velocity, not through blame.

## Alert Design Principles

Every alert in production should satisfy five criteria:

1. **Actionable**: The alert has a clear next step. If no one can do anything about it, it should not page anyone.
2. **Owned**: A specific team or person is responsible for responding. Unowned alerts are worse than no alerts -- they train everyone to ignore pages.
3. **Linked**: Every alert links to a runbook with diagnostic and remediation steps. The alert message includes the runbook URL.
4. **Severitized**: Severity determines routing and response time:
   - **Critical**: Pages on-call immediately -- user-facing outage or imminent data loss
   - **High**: Response within hours -- degraded service, partial impact
   - **Medium**: Next business day -- non-urgent degradation, informational
5. **Deduplicated**: Related alerts are grouped to avoid noise. A single incident should not generate dozens of separate pages.

### The 30-Second Rule

An on-call engineer should understand **what is wrong** and **how to start responding** within 30 seconds of reading the alert. This means:

- The alert title names the symptom, not the metric (`High error rate on checkout` not `http_requests_total > threshold`)
- The body includes current value vs expected range
- A runbook link is immediately visible
- The affected service and environment are explicit

## Runbook Patterns

Every alert should link to a runbook. Runbooks transform incident response from improvisation to systematic diagnosis.

### Runbook Structure

A production runbook contains five sections:

1. **Description**: What this alert means in plain language. What condition triggered it and why it matters.
2. **Impact**: What users experience when this alert fires. Helps the responder gauge urgency.
3. **Diagnostic Steps**: Specific queries, dashboard links, and commands to run. Not vague ("check the logs") but concrete (`grep "payment_failed" /var/log/checkout.log | tail -20`).
4. **Remediation Steps**: A decision tree for common root causes:
   - If database connection errors -> restart connection pool / check DB health
   - If upstream timeout -> check upstream service status / activate circuit breaker
   - If traffic spike -> scale horizontally / enable rate limiting
   - If deployment-related -> rollback to previous version
5. **Escalation Criteria**: When to page someone else. Concrete triggers: "If not resolved within 15 minutes", "If more than 3 services affected", "If data loss is suspected".

### Runbook Template

```
## [Alert Name] Runbook

### Description
[What this alert means. What condition triggers it.]

### Impact
[What users experience. Severity estimation.]

### Diagnostic Steps
1. Check [dashboard link] for current error rate
2. Run: `kubectl logs -l app=<service> --since=10m | grep ERROR`
3. Check upstream dependency status: [status page link]
4. Query recent deployments: `git log --since="2 hours ago" --oneline`

### Remediation
- Database connection errors -> Restart connection pool: `kubectl rollout restart`
- Upstream timeout -> Check upstream / activate circuit breaker
- Traffic spike -> Scale horizontally / enable rate limiting
- Post-deployment regression -> Rollback: `kubectl rollout undo`

### Escalation
- Not resolved in 15 min -> Page secondary on-call
- Multiple services affected -> Page incident commander
- Data loss suspected -> Page database team lead
```

### Runbook Best Practices

- Store runbooks in a central, searchable location accessible during incidents (wiki, internal docs, incident management tool)
- Use **decision tree format** for multi-cause alerts -- responders follow branches rather than reading linearly
- Include **copy-pasteable commands** -- during an incident, nobody wants to construct queries from memory
- **Review quarterly**: Stale runbooks are worse than no runbooks because they give false confidence
- Link runbooks bidirectionally -- from the alert to the runbook and from the runbook to the alert definition
- **Test runbooks during drills**: A runbook that has never been followed under pressure is an untested hypothesis

## On-Call Best Practices

### Alert Routing

Route alerts to the team that owns the service, not a central operations team. Service ownership means alert ownership. Use service metadata (`service.name`, team tags) to automate routing.

### Escalation Chains

A clear escalation path prevents incidents from stalling:

1. **Primary on-call**: First responder, receives the initial page
2. **Secondary on-call**: Escalation after acknowledgment timeout (typically 5-10 minutes)
3. **Team lead**: Escalation for incidents lasting beyond 30 minutes or affecting multiple services
4. **Incident commander**: Activated for company-wide incidents requiring cross-team coordination

### Rotation Patterns

- **Weekly rotations**: Most common; long enough to build context, short enough to prevent burnout
- **Follow-the-sun**: For global teams -- each timezone covers business hours, eliminating overnight pages
- **Paired rotations**: Junior + senior on-call together for knowledge transfer

### Operational Hygiene

- **Handoff protocol**: Outgoing on-call briefs incoming on-call about active issues, recent deployments, and known risks
- **Post-incident review**: Conduct within 48 hours while memory is fresh. Blameless -- focus on systemic improvements, not individual errors
- **Track MTTA and MTTR**: Mean time to acknowledge and mean time to resolve. Trend these over time -- improving MTTA is often the highest-leverage investment
- **On-call load budgeting**: If on-call handles more than 2 pages per shift on average, the system needs reliability investment, not more on-call staff

## Alert Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|-------------|-------------|-----|
| **Threshold on every metric** | Noise flood -- dozens of alerts fire simultaneously during any incident | Alert on SLO burn rates; use dashboards for raw metrics |
| **Unowned alerts** | Nobody responds; trains the team to ignore pages | Every alert must have an explicit owner; delete unowned alerts |
| **Alerts without runbooks** | Responder paralysis -- engineer sees the alert but does not know what to do | Link every alert to a runbook before enabling it |
| **Paging on warnings** | Alert fatigue from non-critical notifications during off-hours | Reserve pages for critical/high severity; warnings go to dashboards or tickets |
| **Copy-paste alert rules** | Thresholds become stale after scaling, traffic changes, or architecture shifts | Derive thresholds from SLOs; review alert rules quarterly |
| **Alerting on internal metrics only** | Misses user-facing failures that do not map to a specific internal counter | Add symptom-based alerts (error rate, latency percentiles) alongside cause-based monitoring |

### Signs of Alert Fatigue

Alert fatigue is the single most dangerous failure mode in an alerting system. When it sets in, on-call engineers start ignoring pages -- including real incidents.

Warning signs:
- Alerts are routinely acknowledged without investigation
- On-call regularly snoozes or silences alerts during shifts
- Mean time to acknowledge (MTTA) is increasing over time
- Engineers joke about "the alert that always fires"

**Fix**: Conduct a quarterly alert review. For each alert, ask: "In the last 90 days, did this alert lead to a meaningful action?" If the answer is no, either fix the alert (better threshold, better scope) or delete it.
