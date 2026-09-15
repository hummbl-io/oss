# Security policy

## Supported status

`@hummbl/mcp-base120` is a local technical canary. It has no supported public
release and must not be used as a hosted or production service.

## Boundary

The local package is designed to:

- read only its bundled Base120 catalog and provenance metadata;
- expose four read-only MCP tools over stdio;
- make no network requests;
- collect no telemetry;
- create no durable files.

Authentication, HTTP transport, multi-tenancy, billing, and hosted telemetry
are outside this package. They require separate product admission and threat
model review.

## Reporting

Report vulnerabilities privately through the repository security-reporting
process described in the root [`SECURITY.md`](../../../SECURITY.md). Do not put
sensitive vulnerability details in a public issue.
