# Defense playbook (Nov 21 deliverable, part 1)

This playbook is the defending side of the Darwinistic Cybersecurity simulator. It lists six prevention measures in three layers and states, for each one, which persuasion tactics it weakens and by how much. The simulator's new defender agent (`app/defenses.py`, `DefenderAgent` in `app/agents.py`) reads this playbook. The synthetic responder applies it whenever an attempt is evaluated.

Everything here runs on synthetic personas only. No message text is generated and no one is contacted.

## How a defense works in the model

Each attempt has a fit score: how well the tactic suits the persona, times how reachable they are on that channel. A defense does two things:

1. **Blunts the tactic.** The fit is multiplied by (1 minus the blunt value). A blunt of 0.25 makes that tactic a quarter less effective against a defended persona.
2. **Raises reporting.** It adds a chance that a poor fit attempt gets reported rather than ignored, because the person knows what to look for and has an easy way to flag it.

Defenses stack multiplicatively, so layering helps with diminishing returns. Technical controls only apply on the channels they actually filter (email, and SMS for link sandboxing). People and process defenses go with the person onto every channel.

The values are modelling assumptions that follow the direction of published guidance. For example, verifying through a second channel mainly counters authority and urgency, and link sandboxing mainly counters curiosity lures. They are not measured effect sizes. We calibrated them so that one layer alone cuts the learned attacker's success by roughly a sixth to a half, and all layers together by about 90%, which leaves realistic residual risk. The IRB-approved participant study is what would replace these assumptions with real data.

## The six defenses

**Role tailored awareness training** (people, effort 2). Short, recurring training built around the tactics each role is most exposed to, plus a one click report button.

**Verify through a second channel** (people, effort 2). Any unexpected request is confirmed by contacting the sender through a number or address you already trust.

**Two person approval and a cooling off delay** (process, effort 3). Payments, access grants, and data exports need a second approver and cannot be rushed through in one step.

**Published 'we will never ask' policy** (process, effort 1). The organization states plainly which things it will never request by message (passwords, gift cards, bank changes), so any such request is an instant red flag.

**Sender authentication and external sender banner** (technical, effort 3). Email authentication (SPF, DKIM, DMARC) blocks spoofed senders, and a banner marks anything from outside.

**Link and attachment sandboxing with lure detection** (technical, effort 4). Links and files are opened in a sandbox first, and messages that look machine generated or lure-like are flagged before the person sees them.

## Tactic by defense matrix

Blunt strength per tactic: strong is 0.20 or more, medium is 0.10 to 0.19, light is below 0.10.

| Defense | Layer | Urgency | Authority | Curiosity | Reciprocity | Social proof | Job relevance |
|---|---|---|---|---|---|---|---|
| Role tailored awareness training | people | medium (0.10) | light (0.07) | medium (0.17) | medium (0.12) | medium (0.15) | light (0.07) |
| Verify through a second channel | people | strong (0.20) | strong (0.25) | light (0.03) | light (0.07) | light (0.05) | medium (0.15) |
| Two person approval and a cooling off delay | process | strong (0.28) | strong (0.20) | light (0.03) | medium (0.10) | light (0.07) | medium (0.17) |
| Published 'we will never ask' policy | process | light (0.07) | medium (0.15) | light (0.05) | strong (0.20) | medium (0.15) | medium (0.10) |
| Sender authentication and external sender banner | technical | light (0.07) | strong (0.28) | none (0.00) | none (0.00) | light (0.05) | medium (0.12) |
| Link and attachment sandboxing with lure detection | technical | light (0.05) | none (0.00) | strong (0.28) | medium (0.12) | light (0.07) | medium (0.10) |

## Where the attacker is strongest

The trained RL attacker found each role's hidden weak spot. A good playbook has to cover these tactics:

| Role | Tactic the attacker learned to use |
|---|---|
| Accounts Payable Specialist | Authority |
| Finance Director | Urgency |
| Procurement Analyst | Social proof |
| HR Coordinator | Curiosity |
| Executive Assistant | Reciprocity |
| IT Help Desk Technician | Job relevance |
| Software Engineer | Authority |
| Research Assistant | Social proof |
| Marketing Manager | Urgency |

Authority, urgency, and social proof show up most often, so verification habits and two person approval matter most.

## First measurement: each defense against the trained attacker

These runs use the attacker trained with no defenses in place (the current `learned_policy.json`), against 2,000 synthetic personas. This attacker is **not** allowed to adapt yet. Letting it relearn against the defenses is the arms race experiment, which comes next.

| Defense | Layer | Channels covered | Effort (1 to 5) | Learned attacker success | Cut vs no defense |
|---|---|---|---|---|---|
| No defense | | | | 57.5% | |
| Role tailored awareness training | people | all | 2 | 45.5% | 21% |
| Verify through a second channel | people | all | 2 | 44.2% | 23% |
| Two person approval and a cooling off delay | process | all | 3 | 42.6% | 26% |
| Published 'we will never ask' policy | process | all | 1 | 44.8% | 22% |
| Sender authentication and external sender banner | technical | email | 3 | 53.8% | 7% |
| Link and attachment sandboxing with lure detection | technical | email, sms | 4 | 52.8% | 8% |

| Bundle | Learned attacker success | Cut vs no defense |
|---|---|---|
| people | 31.5% | 45% |
| process | 29.3% | 49% |
| technical | 49.2% | 14% |
| layered | 4.9% | 92% |

## Early observations (to confirm in the arms race runs)

1. People and process defenses each cut success by roughly a fifth to a quarter on their own. They work on every channel, and they hit the tactics the attacker relies on most.
2. Technical controls look weak here (under 10% each). That isn't because they're bad. They only cover email and SMS, and the attacker also reaches personas on LinkedIn, Instagram, and TikTok, where no filter applies. This coverage gap is a finding in its own right.
3. Layering everything cuts success by about 90%, but not to zero.
4. The open question for the next step is whether these cuts hold once the attacker evolves. A learning attacker should shift toward whichever tactic and channel each defense misses.