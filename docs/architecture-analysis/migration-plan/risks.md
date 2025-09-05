# Risk Assessment & Mitigation

Source analyzed: main branch at commit 925cee92e220a947ff10ce15415e2957f4812430

## Potential Breaking Changes
- CLI argument changes when routing through `CommandPort`.
- Module call-sites updated to DI-friendly entrypoints.

## Testing Requirements
- Unit tests for use cases and ports.
- Integration tests for pipelines, covering FS and subprocess.

## Rollback Procedures
- Keep compatibility CLI wrapper calling old code paths until stable.
- Feature-flag the new core entrypoints.

## Effort/Cost Estimate (relative)
- Phase A: S (1-2 days)
- Phase B: M (3-5 days)
- Phase C: L (5-8 days)
- Phase D: M (3-5 days)
