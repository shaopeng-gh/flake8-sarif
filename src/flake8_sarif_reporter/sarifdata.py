"""Module containing the SARIF reporter for Flake8."""
import os
from pathlib import Path


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
