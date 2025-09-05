# Implementation Guidelines (Ports & Adapters)

Source analyzed: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

## Coding Standards
- Core code may not import `subprocess`, `pathlib`, `cv2`, `pandas`, or OS I/O libs.
- All side-effects routed through ports. Use dependency injection at boundaries.
- Keep functions small, explicit types, early returns, and clear naming.

## Naming Conventions
- Ports: `SomethingPort` in `percell/ports/`.
- Adapters: `SomethingAdapter` in `percell/adapters/`.
- Use cases: verb-oriented modules in `percell/application/use_cases/`.

## Testing Patterns
- Unit-test core with mocks of ports.
- Contract tests for adapters against real tools (golden files for FS, sample images).
- End-to-end tests for representative pipelines.

## Code Review Checklist
- Core dependencies only on ports and domain types.
- No business logic inside adapters.
- Clear separation of driving vs driven adapters.
- Adequate tests at core and adapter levels.
