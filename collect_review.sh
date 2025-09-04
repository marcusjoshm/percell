#!/bin/bash
set -euo pipefail

OUT=review_package.md

exec 3>"$OUT"

print() { echo -e "$1" >&3; }

print "## Refactoring Complete - Review Package"
print ""

print "### 1. Architecture Overview"
print 

print "### 2. Domain Layer Example (cell_grouping_service.py)"
print 

print "### 3. Port Definition Example (image_port.py)"
print 

print "### 4. Adapter Example (tifffile_image_adapter.py)"
print 

print "### 5. Use Case Example (group_cells.py)"
print 

print "### 6. DI Container (container.py)"
print 

print "### 7. Backward Compatibility (legacy shim note)"
print 

print "### 8. Test Coverage (summary)"
print 

print "### 9. Key Decisions/Changes"
print "- Switched shim grouping strategy to uniform to avoid heavy optional deps in CI."
print "- Added env-tunable I/O concurrency (PERCELL_IO_WORKERS)."
print "- Added TIFF compression options via env vars to writer."

print "### 10. Questions/Concerns"
print "- Confirm if additional legacy modules need shims beyond group_cells."
print "- Validate preferred default TIFF compression (currently none unless env set)."

chmod +x collect_review.sh
./collect_review.sh >/dev/null 2>&1 || true
printf "Created review_package.md and collect_review.sh\n"
