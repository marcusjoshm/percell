# Architecture Overview

PerCell follows a Ports & Adapters (Hexagonal) architecture.

## Layers

- Domain: business services and models
- Application: orchestration and coordination
- Ports: interfaces for driving/driven interactions
- Adapters: implementations (CLI, filesystem, ImageJ, Cellpose, etc.)

## Key components

- WorkflowCoordinator and StepExecutionCoordinator
- Centralized Paths
- Adapters: `CellposeSubprocessAdapter`, `ImageJMacroAdapter`, `LocalFileSystemAdapter`, `PILImageProcessingAdapter`

## Further reading (archived)

Detailed analysis and refactoring plans are preserved in `docs/archive/`:

- Ports & Adapters analysis (guide/report)
- Revised architecture plan
- Refactoring checklist and plan


