import re
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
TOOL_RE = re.compile(r"^\s*tool:\s*(.+?)\s*$", re.M)


class WorkflowToolPinTests(unittest.TestCase):
    def test_every_install_action_tool_is_pinned(self):
        found = 0
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            for line in TOOL_RE.findall(workflow.read_text(encoding="utf-8")):
                for tool in line.split(","):
                    found += 1
                    self.assertIn("@", tool, f"{workflow.name}: tool '{tool}' is not pinned (name@version)")
        self.assertGreater(found, 0, "no install-action tool lines found")


if __name__ == "__main__":
    unittest.main()
