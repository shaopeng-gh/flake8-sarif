"""Module containing all of the SARIF reporters for Flake8."""
import json
import os
from pathlib import Path

from flake8.formatting import base


class DefaultSARIF(base.BaseFormatter):
    """Formatter for SARIF."""

    def after_init(self):
        """Force newline to be empty."""
        self.newline = ""
        self.sarif_data = []

    def _write(self, output):
        if self.output_fd is not None:
            self.output_fd.write(output + self.newline)
        if self.output_fd is None or self.options.tee:
            print(output, end=self.newline)

    def write_line(self, line):
        """Override write for convenience."""
        self.write(line, None)

    def stop(self):
        """Clean up after reporting is finished."""
        self.write_line(self.print_sarif_report())

    def format(self, violation):
        """Format a violation."""
        sarif = SarifData(
            rule_id=violation.code,
            rule_level="error"
            if violation.code.startswith("E")
            else "warning",
            rule_full_desc=violation.text,
            file_path=violation.filename,
            root_dir_path=None,
            result_message=violation.text,
            start_line=violation.line_number,
            start_column=violation.column_number,
            end_line=violation.line_number,
            end_column=violation.column_number,
            code_snippet=violation.physical_line,
        )
        self.sarif_data.append(sarif)

    def print_sarif_report(self):
        """Print all violations in SARIF format."""
        sarif = {
            "$schema": (
                "https://schemastore.azurewebsites.net/schemas/"
                "json/sarif-2.1.0-rtm.5.json"
            ),
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "flake8",
                            "informationUri": "https://flake8.pycqa.org/",
                            "version": "4.0.1",
                            "rules": [
                                {
                                    "id": "E101",
                                    "defaultConfiguration": {"level": "error"},
                                }
                            ],
                        }
                    },
                    "results": [
                        {
                            "ruleId": "E101",
                            "ruleIndex": 0,
                            "message": {
                                "text": "indentation contains mixed spaces..."
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "TestFileFolder/E10.py",
                                            "uriBaseId": "ROOTPATH",
                                        },
                                        "region": {
                                            "startLine": 2,
                                            "startColumn": 7,
                                            "endLine": 2,
                                            "endColumn": 7,
                                            "snippet": {
                                                "text": "\tprint b  # ind..."
                                            },
                                        },
                                    }
                                }
                            ],
                        }
                    ],
                    "columnKind": "utf16CodeUnits",
                    "originalUriBaseIds": {
                        "ROOTPATH": {"uri": "file:///C:/repos/repototest/"}
                    },
                }
            ],
        }

        rules = sarif["runs"][0]["tool"]["driver"]["rules"] = []
        results = sarif["runs"][0]["results"] = []
        roots = sarif["runs"][0]["originalUriBaseIds"] = {}

        for message in self.sarif_data:
            rule_index_exists = next(
                (
                    i
                    for i, tag in enumerate(rules)
                    if tag["id"] == message.rule_id
                ),
                "none",
            )
            if rule_index_exists == "none":
                new_rule = {"id": message.rule_id}
                if message.rule_level != "warning":
                    new_rule["defaultConfiguration"] = {
                        "level": message.rule_level
                    }
                rules.append(new_rule)
                rule_index = len(rules) - 1
            else:
                rule_index = rule_index_exists

            base_uri = message.get_base_dir_file_uri()
            root_path_index_exists = next(
                (i for i, tag in roots.items() if tag["uri"] == base_uri),
                "none",
            )
            if root_path_index_exists == "none":
                new_root_name = (
                    "ROOTPATH" + str(len(roots) + 1)
                    if len(roots) >= 1
                    else "ROOTPATH"
                )
                roots[new_root_name] = {"uri": base_uri}
                root_path = new_root_name
            else:
                root_path = root_path_index_exists

            result = {
                "ruleId": message.rule_id,
                "ruleIndex": rule_index,
                "message": {"text": message.result_message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": message.get_relative_path(),
                                "uriBaseId": root_path,
                            },
                            "region": {
                                "startLine": message.start_line,
                                "startColumn": message.start_column,
                                "endLine": message.end_line,
                                "endColumn": message.end_column,
                                "snippet": {"text": message.code_snippet},
                            },
                        }
                    }
                ],
            }
            results.append(result)
        return json.dumps(sarif, indent=4)


class SarifData:
    """Collect the results of the checks for SARIF format."""

    def __init__(
        self,
        rule_id,
        rule_level,
        rule_full_desc,
        file_path,
        root_dir_path,
        result_message,
        start_line,
        start_column,
        end_line,
        end_column,
        code_snippet,
    ):
        """Init a new SarifData object."""
        self.rule_id = rule_id
        self.rule_level = rule_level
        self.rule_full_desc = rule_full_desc
        self.file_path = file_path
        self.root_dir_path = root_dir_path
        self.result_message = result_message
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = end_line
        self.end_column = end_column
        self.code_snippet = code_snippet

    def get_relative_path(self):
        """Return path of the file relative to the root folder."""
        if self.root_dir_path is None:
            if os.path.isabs(self.file_path):
                path = os.path.basename(self.file_path)
            else:
                path = self.file_path
        else:
            abs_path = os.path.abspath(self.file_path)
            path = Path(abs_path).relative_to(self.root_dir_path)
        path = path.replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        return path

    def get_base_dir_file_uri(self):
        """Return file uri of the root folder."""
        if self.root_dir_path is None:
            if os.path.isabs(self.file_path):
                path = os.path.dirname(self.file_path)
            else:
                path = os.getcwd()
        else:
            path = self.root_dir_path
        return Path(path).as_uri() + "/"
