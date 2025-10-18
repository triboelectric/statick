"""Do nothing to have a default reporting plugin with no side effects."""

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class DoNothingReportingPlugin(ReportingPlugin):
    """Do nothing."""

    def get_name(self) -> str:
        """Return the name of the plugin."""
        return "do_nothing"

    def report(
        self, package: Package, issues: dict[str, list[Issue]], level: str
    ) -> tuple[None, bool]:
        """Do nothing.

        Args:
            package: The Package object that was analyzed.
            issues: The issues found by the Statick analysis, keyed by the tool that found them.
            level: Name of the level used in the scan.

        Returns:
            None, True indicating the report was processed (even though nothing was done).
        """
        return None, True
