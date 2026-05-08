---
name: welcome-dm-template
type: template
description: Welcome DM sent to new Skool group members on their join day. Engagement agent personalizes with member name and today's intake call time before sending via skool-dm skill.
---

## Template

```
Hey [FIRST_NAME] 👋

Welcome to [GROUP_NAME] — glad you're here.

We run a live Intake Call every day to get you oriented fast and make sure
you know exactly how to use everything inside the group.

Today's session: [INTAKE_CALL_TIME] — drop in, ask anything, get plugged in.

The group moves fast. The people who show up early get the most out of it.

See you in there.

— [BRAND_NAME]
```

## Personalization variables
| Variable | Source |
|----------|--------|
| `[FIRST_NAME]` | Member display name (first word) from member-activity.md |
| `[GROUP_NAME]` | `config.<group>.yaml → group.name` |
| `[INTAKE_CALL_TIME]` | `config.<group>.yaml → calls.intake_call.schedule_label` |
| `[BRAND_NAME]` | `config.<group>.yaml → operator.brand_name` |

## Usage instructions
1. Engagement agent reads this file
2. Replaces all `[VARIABLE]` placeholders with live values
3. Passes completed DM text to `skool-dm` skill as `job.prompt`
4. `skool-dm` sends and verifies

## Tone guidelines
- Short. This is a DM, not an email.
- No marketing language ("amazing opportunity", "life-changing").
- Direct invitation, not a pitch.
- The CTA is specific (today's call, not "check us out").

## Variations
For members who joined but haven't attended the intake call after 48 hours,
engagement agent sends a follow-up using this modified opening:

```
Hey [FIRST_NAME] — you joined [GROUP_NAME] a couple days ago and haven't made
it to an Intake Call yet. No pressure, but those calls are the fastest way to
get real value from the group.

Next one: [INTAKE_CALL_TIME] today.
```

## See also
- vault/skills/active/skool-group-manager/skool-dm.md
- examples/skool-group-manager/agent-briefs/engagement-agent.md
