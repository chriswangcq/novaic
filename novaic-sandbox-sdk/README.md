# NovaIC Sandbox SDK

Thin service-boundary SDK for sandboxd.

This package owns only cross-process API types and the HTTP client:

- sandbox execution spec/result DTOs
- sandboxd request/response JSON wire contracts
- sandboxd HTTP client

It must not execute processes, create mount namespaces, inspect local host
capabilities, or import Cortex / sandbox core / product logic.
