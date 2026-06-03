#!/usr/bin/env bash
set -euo pipefail

[ -d "skills/environments" ] || { echo "FAIL: skills/environments/ missing"; exit 1; }
[ -f "skills/environments/SKILL.md" ] || { echo "FAIL: skills/environments/SKILL.md missing"; exit 1; }

echo "PASS: skill paths valid"
