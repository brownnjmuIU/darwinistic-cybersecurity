# Recommended prevention strategies (Nov 21 deliverable)

**Darwinistic Cybersecurity simulator · Manasi Manoj Koppal · November 21, 2026**

## The short answer

Against an attacker that learns and adapts, the defenses that work are the **broad** ones: measures that weaken several persuasion tricks at once, on every channel a person uses. A defense aimed at one trick, or at one channel, gets routed around. So the recommendation is to start with cheap, broad people and process defenses, add a two person approval rule for high risk actions, and treat technical email filters as a supplement rather than the main line of defense. Layering all of them cut the learning attacker's success rate from 57% to under 5% in simulation, and that cut held when the attacker kept learning against them.

## How we got here

1. **Defense playbook** (`docs/defense_playbook.md`). Six prevention measures in three layers (people, process, technical), each scored for how much it weakens each persuasion trick, which channels it covers, and how hard it is to adopt.
2. **Defender agent.** A seventh agent in the simulator that applies the chosen defenses whenever an attack attempt is evaluated.
3. **Arms race experiment** (`arms_race.py`). For each defense we measured the trained attacker's success on 2,000 synthetic personas, then let it keep learning against that defense on 2,000 new personas and measured again. If its success came back up, the defense was being routed around.

## Results

Share of synthetic personas the learning attacker fooled (no defense: 57%).

| Defense | Layer | Effort (1 to 5) | Fooled after attacker adapts | Cut vs no defense | Held up? |
|---|---|---|---|---|---|
| All six together | all | | 4.5% | 92% | yes |
| Process layer (both) | process | | 27.6% | 52% | yes |
| People layer (both) | people | | 31.6% | 45% | yes |
| Two person approval and cooling off delay | process | 3 | 39.9% | 31% | yes |
| Role tailored awareness training | people | 2 | 43.5% | 24% | yes |
| Verify through a second channel | people | 2 | 44.2% | 23% | yes |
| Published "we will never ask" policy | process | 1 | 45.0% | 22% | yes |
| Technical layer (both) | technical | | 50.7% | 12% | yes |
| Link and attachment sandboxing | technical | 4 | 52.4% | 9% | yes |
| Sender authentication and external banner | technical | 3 | 54.5% | 5% | yes |
| *Control: block only one trick (authority)* | | | *50.3%* | *12%* | ***no, routed around*** |

"Held up" means any change after the attacker adapted was within statistical noise (two standard errors). The control was the only case where adaptation was real: the attacker stopped using authority entirely (from about 20% of its attempts to 0%) and shifted to urgency and social proof, winning back a third of the ground it had lost.

## Recommendations, in order

**1. Start now: the cheap, broad defenses.** Publish a "we will never ask" policy (effort 1), and build the habit of verifying unexpected requests through a second, known channel (effort 2), supported by short training tailored to each role's most exposed tricks (effort 2). Each one alone cuts attack success by about a fifth to a quarter, works on every channel, and did not get routed around. Together the two people defenses cut success by 45%.

**2. Next: two person approval for high risk actions.** Payments, bank detail changes, access grants and data exports should need a second approver and a short cooling off delay. This was the strongest single defense (31% cut) because it directly breaks the urgency and authority tricks that the attacker learned to use most on finance and administrative roles. It costs more to run, so it should apply only to those high risk actions.

**3. Keep technical filters, but do not rely on them.** Sender authentication and link sandboxing cut success by only 5% to 12% here. That is not because they are weak but because they only cover email and SMS, while personas were also reachable on LinkedIn, Instagram and TikTok, where no filter applies. The finding is a coverage gap: an attacker simply moves to the channel nobody is filtering. People and process defenses travel with the person to every channel.

**4. Layer everything for the roles that matter most.** All six together cut success by 92%, and the attacker could not adapt around them. Even so, about 1 in 20 personas, mostly the most susceptible ones, were still fooled. No defense is perfect, so reporting and response matter as much as prevention.

### Matching defenses to the tricks the attacker learned

The trained attacker discovered which trick works best on each role. The defenses that blunt those tricks most strongly are:

| Role | Trick the attacker learned | Strongest defenses against it |
|---|---|---|
| Finance Director, Marketing Manager | urgency | two person approval, verify habit |
| Accounts Payable Specialist, Software Engineer | authority | verify habit, sender authentication, two person approval |
| Procurement Analyst, Research Assistant | social proof | role tailored training, "never ask" policy |
| HR Coordinator | curiosity | link sandboxing, role tailored training |
| Executive Assistant | reciprocity | "never ask" policy, role tailored training |
| IT Help Desk Technician | job relevance | two person approval, verify habit |

## The principle behind it

The Darwinistic point of the project is that GenAI attackers evolve. The experiment shows what that means for defense: **a defense survives an evolving attacker only if it leaves the attacker nowhere better to go.** Narrow defenses, whether they cover one trick or one channel, shift the attack rather than stop it. Broad defenses that follow the person across channels and weaken many tricks at once hold their value even as the attacker learns.

## Limitations

These results come from a simulation, so they show the *direction* of what works rather than real effect sizes.

* The defense strengths are modelling assumptions based on published guidance, not measured effects. They were set so that no defense is perfect.
* All personas and their reactions are synthetic. The responder that decides how a persona reacts is a stand in for real behavior.
* The attacker chooses among six abstract persuasion tricks and never writes message text, so effects that depend on wording (for example highly polished AI written messages) are not modelled.

The planned IRB approved participant study is what would replace these assumptions with measured effects: how much training, verification habits and approval rules actually change real people's responses.

## How to reproduce

```
python train_rl.py      # trains the learning attacker (learned_policy.json)
python arms_race.py     # runs the defense experiment (about one minute)
```

The live dashboard has a **Defenses** setting to see each layer in action, plus a panel with these results and charts.
