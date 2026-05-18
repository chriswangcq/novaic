# Retained ServiceConfig boundary classification

## Problem

Classify remaining `ServiceConfig` reads in runtime queue/task code after the saga decision config fix. Adapter-boundary defaults may be retained, but decision-path hidden inputs must be remediated or split.

## Success Criteria

- Produce a saved classification artifact for retained `ServiceConfig` hits.
- Each retained hit is classified as process startup, client adapter, tool adapter, retry policy adapter, or risky decision-path hidden input.
- Any risky hit not handled by P472 is turned into a new child/follow-up rather than ignored.
