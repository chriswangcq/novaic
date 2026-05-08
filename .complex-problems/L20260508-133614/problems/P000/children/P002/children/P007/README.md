# P007: Roster-driven runtime launch generation

## Problem
Make runtime worker launch commands generated from or explicitly bound to runtime_roster.py so start.sh no longer owns a second process-role list.

## Success Criteria
- start.sh launch path consumes canonical runtime roster
- tests fail if launch roles drift from roster
