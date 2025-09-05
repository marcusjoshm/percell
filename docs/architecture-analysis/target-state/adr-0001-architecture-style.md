# ADR-0001: Adopt Ports & Adapters (Hexagonal) Architecture

Status: Proposed
Date: 2025-09-05
Source analyzed: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

## Context
The current code couples orchestration and infrastructure (subprocess, filesystem, image I/O). We need clearer boundaries to improve testability and flexibility.

## Decision
Adopt Ports & Adapters architecture. Define driving and driven ports, with adapters for current technologies, and isolate business/use-case logic in the core.

## Consequences
- Pros: testable core, easier to replace infrastructure, clearer layering.
- Cons: initial refactor cost, more abstractions.

## Alternatives Considered
- Keep layered architecture but reduce coupling: less explicit boundaries.
- Microservices split: overkill for current scope.
