"""
Exceptions interface.
"""
import os
import fnmatch
import re
import yaml

class Exceptions(object):
    """
    Manages which plugins are run for each statick scan level and what flags
    are used for each plugin at those levels.
    """
    def __init__(self, filename):
        with open(filename) as fname:
            self.exceptions = yaml.safe_load(fname)

    def get_ignore_packages(self):
        """
        Get list of packages to skip when scanning a workspace.
        """
        ignore = []
        if "ignore_packages" in self.exceptions and self.exceptions["ignore_packages"] is not None:
            ignore = self.exceptions["ignore_packages"]
        return ignore

    def get_exceptions(self, package):
        """
        Get specific exceptions for given package.
        """
        exceptions = {"file": [], "message_regex": []}

        if "global" in self.exceptions and "exceptions" in self.exceptions["global"]:
            global_exceptions = self.exceptions["global"]["exceptions"]
            if "file" in global_exceptions:
                exceptions["file"] += global_exceptions["file"]
            if "message_regex" in global_exceptions:
                exceptions["message_regex"] += global_exceptions["message_regex"]

# pylint: disable=too-many-boolean-expressions
        if self.exceptions and "packages" in self.exceptions \
            and self.exceptions["packages"] and package.name in \
                self.exceptions["packages"] \
                and self.exceptions["packages"][package.name] \
                and "exceptions" in self.exceptions["packages"][package.name]:
            package_exceptions = self.exceptions["packages"][package.name]["exceptions"]
            if "file" in package_exceptions:
                exceptions["file"] += package_exceptions["file"]
            if "message_regex" in package_exceptions:
                exceptions["message_regex"] += package_exceptions["message_regex"]
# pylint: enable=too-many-boolean-expressions

        return exceptions

    @classmethod
    def filter_file_exceptions(cls, package, exceptions, issues):
        """
        Filter issues based on file pattern exceptions list.
        """
        for tool, tool_issues in issues.iteritems():
            to_remove = []
            for issue in tool_issues:
                rel_path = os.path.relpath(issue.filename, package.path)
                for exception in exceptions:
                    if exception["tools"] == 'all' or tool in exception["tools"]:
                        for pattern in exception["globs"]:
                            if fnmatch.fnmatch(issue.filename, pattern) or \
                               fnmatch.fnmatch(rel_path, pattern):
                                to_remove.append(issue)
            issues[tool] = [issue for issue in tool_issues if issue not in
                            to_remove]

        return issues

    @classmethod
    def filter_regex_exceptions(cls, exceptions, issues):
        """
        Filter issues based on message regex exceptions list.
        """
        for exception in exceptions:
            exception_re = exception["regex"]
            exception_tools = exception["tools"]
            compiled_re = re.compile(exception_re)
            for tool, tool_issues in issues.iteritems():
                to_remove = []
                if exception_tools == "all" or tool in exception_tools:
                    for issue in tool_issues:
                        match = compiled_re.match(issue.message)
                        if match:
                            to_remove.append(issue)
                issues[tool] = [issue for issue in tool_issues if issue not in
                                to_remove]
        return issues

    @classmethod
    def filter_nolint(cls, issues):
        """
        Filter out lines that have an explicit NOLINT on them.
        Sometimes the tools themselves don't properly filter these out if
        there is a complex macro or something.
        """
        for tool, tool_issues in issues.iteritems():
            to_remove = []
            for issue in tool_issues:
                lines = open(issue.filename, "r").readlines()
                line_number = int(issue.line_number)-1
                if line_number < len(lines) and "NOLINT" in lines[line_number]:
                    to_remove.append(issue)
            issues[tool] = [issue for issue in tool_issues if issue not in to_remove]
        return issues

    def filter_issues(self, package, issues):
        """
        Filter issues based on exceptions list.
        """
        exceptions = self.get_exceptions(package)

        if len(exceptions["file"]) > 0:
            issues = self.filter_file_exceptions(package,
                                                 exceptions["file"],
                                                 issues)

        if len(exceptions["message_regex"]) > 0:
            issues = self.filter_regex_exceptions(exceptions["message_regex"],
                                                  issues)

        issues = self.filter_nolint(issues)

        return issues
