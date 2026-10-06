# File: test_file_actions.py
#
# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.

"""Exercise connector file actions with real Git repositories and a stub SOAR API."""

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import git


class ActionResult:
    def __init__(self, param=None):
        self.status = 0
        self.message = ""
        self.data = []
        self.summary = {}

    def set_status(self, status, message="", status_message=None):
        self.status = status
        self.message = status_message or message
        return status

    def get_status(self):
        return self.status

    def add_data(self, data):
        self.data.append(data)

    def update_summary(self, data):
        self.summary.update(data)
        return self.summary


class FileActionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = types.ModuleType("phantom.app")
        app.APP_SUCCESS, app.APP_ERROR = 0, 1
        app.is_fail = lambda status: status != 0
        rules = types.ModuleType("phantom.rules")
        modules = {"phantom": types.ModuleType("phantom"), "phantom.app": app, "phantom.rules": rules}
        for name, symbol, value in (
            ("phantom.action_result", "ActionResult", ActionResult),
            ("phantom.base_connector", "BaseConnector", object),
            ("Cryptodome.PublicKey", "RSA", Mock()),
        ):
            module = types.ModuleType(name)
            setattr(module, symbol, value)
            modules[name] = module
        modules["Cryptodome"] = types.ModuleType("Cryptodome")
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location("connector_under_test", root / "git_connector.py")
        cls.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(cls.module)
        cls.rules = rules

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo_dir = self.root / "repo"
        self.repo = git.Repo.init(self.repo_dir)
        self.connector = self.module.GitConnector()
        self.connector.app_state_dir = self.root
        self.connector.repo_name = "repo"
        self.connector.save_progress = Mock()
        self.connector.debug_print = Mock()
        self.connector.get_action_identifier = Mock(return_value="test")
        self.connector.get_container_id = Mock(return_value=1)
        self.connector._set_repo_attributes = Mock()
        self.results = []
        self.connector.add_action_result = lambda result: self.results.append(result) or result

    def write(self, name, content):
        path = self.repo_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_list_filters_and_counts(self):
        self.write("sub/tracked.txt", b"text")
        self.write("sub/other.bin", b"\x00")
        self.repo.index.add(["sub/tracked.txt"])
        self.assertTrue(hasattr(self.connector, "_list_files"))
        status = self.connector._list_files({"recursive": True, "filter_type": "files", "name_regex": r"\.txt$"})
        self.assertEqual(status, 0)
        self.assertEqual(self.results[-1].data[0]["files"][0]["path"], "sub/tracked.txt")
        self.assertTrue(self.results[-1].data[0]["files"][0]["tracked"])
        self.assertEqual(self.results[-1].summary["total_files"], 1)

    def test_get_text_and_binary_vault(self):
        self.write("text.txt", b"\xef\xbb\xbfhello")
        binary = self.write("binary.bin", b"\x00\xff\x80")
        self.assertTrue(hasattr(self.connector, "_get_file"))
        self.assertEqual(self.connector._get_file({"file_path": "text.txt"}), 0)
        self.assertEqual(self.results[-1].data[0]["contents"], "hello")
        paths = []

        def vault_add(**kwargs):
            path = Path(kwargs["file_location"])
            self.assertEqual(path.read_bytes(), binary.read_bytes())
            paths.append(path)
            return True, "", "vault-id"

        self.rules.vault_add = Mock(side_effect=vault_add)
        self.assertEqual(self.connector._get_file({"file_path": "binary.bin"}), 0)
        self.assertTrue(self.results[-1].data[0]["is_binary"])
        self.assertEqual(self.results[-1].data[0]["vault_id"], "vault-id")
        self.assertFalse(paths[0].exists())

    def test_rename_stages_move(self):
        self.write("old.txt", b"hello")
        self.repo.index.add(["old.txt"])
        self.assertTrue(hasattr(self.connector, "_rename_file"))
        self.assertEqual(self.connector._rename_file({"old_file_path": "old.txt", "new_file_path": "sub/new.txt"}), 0)
        self.assertFalse((self.repo_dir / "old.txt").exists())
        self.assertEqual((self.repo_dir / "sub/new.txt").read_bytes(), b"hello")
        self.assertEqual(self.repo.git.ls_files(), "sub/new.txt")

    def test_retrieval_rejects_traversal_and_symlink(self):
        outside = self.root / "secret"
        outside.write_bytes(b"secret")
        (self.repo_dir / "link").symlink_to(outside)
        self.assertTrue(hasattr(self.connector, "_get_file"))
        for path in ("../secret", "link"):
            self.assertEqual(self.connector._get_file({"file_path": path}), 1)

    def test_vault_import_preserves_empty_and_binary_bytes(self):
        for content in (b"", b"\x00\xff\x80", b"\xef\xbb\xbfhello"):
            source = self.root / "vault"
            source.write_bytes(content)
            self.rules.vault_info = Mock(return_value=(True, "", [{"path": str(source)}]))
            result = ActionResult()
            self.assertEqual(self.connector._file_interaction(result, "add", "import.bin", "fallback", "id"), 0)
            self.assertEqual((self.repo_dir / "import.bin").read_bytes(), content)
            (self.repo_dir / "import.bin").unlink()

    def test_list_rejects_bad_filters_and_excludes_metadata(self):
        outside = self.root / "secret"
        outside.write_bytes(b"secret")
        (self.repo_dir / "link").symlink_to(outside)
        for param in ({"name_regex": "["}, {"filter_type": "invalid"}, {"file_path": ".."}, {"file_path": ".git"}):
            self.assertEqual(self.connector._list_files(param), 1)
        self.assertEqual(self.connector._list_files({"recursive": True}), 0)
        self.assertEqual(self.results[-1].data[0]["files"], [])

    def test_rename_rejects_existing_destination_and_escape(self):
        self.write("old.txt", b"hello")
        self.write("existing.txt", b"keep")
        self.repo.index.add(["old.txt"])
        for destination in ("existing.txt", "../escape", ".git/config"):
            self.assertEqual(self.connector._rename_file({"old_file_path": "old.txt", "new_file_path": destination}), 1)
        self.assertEqual((self.repo_dir / "old.txt").read_bytes(), b"hello")

    def test_vault_failure_cleans_temporary_file(self):
        self.write("text.txt", b"hello")
        paths = []

        def fail(**kwargs):
            paths.append(Path(kwargs["file_location"]))
            self.assertEqual(kwargs["file_name"], "renamed.txt")
            return False, "vault unavailable", None

        self.rules.vault_add = Mock(side_effect=fail)
        self.assertEqual(self.connector._get_file({"file_path": "text.txt", "save_to_vault": True, "vault_filename": "renamed.txt"}), 1)
        self.assertIn("vault unavailable", self.results[-1].message)
        self.assertFalse(paths[0].exists())

    def test_text_contents_encode_after_unescaping(self):
        result = ActionResult()
        self.assertEqual(self.connector._file_interaction(result, "add", "text.txt", r"hello\nworld"), 0)
        self.assertEqual((self.repo_dir / "text.txt").read_bytes(), b"hello\nworld")

    def test_new_action_dispatch_and_checkout_preserved(self):
        for action in ("list_files", "get_file", "rename_file", "git_checkout"):
            handler = Mock(return_value=0)
            with patch.object(self.connector, "_" + action, handler):
                self.connector.get_action_identifier.return_value = action
                self.assertEqual(self.connector.handle_action({}), 0)
                handler.assert_called_once_with({})

    def test_metadata_symlink_alias_is_rejected(self):
        (self.repo_dir / "alias").symlink_to(self.repo_dir / ".git", target_is_directory=True)
        self.assertEqual(self.connector._get_file({"file_path": "alias/config"}), 1)
        self.assertEqual(self.connector._list_files({"file_path": "alias"}), 1)
        self.assertEqual(self.connector._list_files({"recursive": True}), 0)
        self.assertEqual(self.results[-1].data[0]["files"], [])
        self.write("old.txt", b"hello")
        self.repo.index.add(["old.txt"])
        self.assertEqual(self.connector._rename_file({"old_file_path": "old.txt", "new_file_path": "alias/new"}), 1)

    def test_derive_repository_name_from_asset_uri(self):
        self.write("text.txt", b"hello")
        self.repo_dir.rename(self.root / "repo_main")
        self.connector._set_repo_attributes = types.MethodType(self.module.GitConnector._set_repo_attributes, self.connector)
        self.connector.repo_uri = "https://example.com/repo.git"
        self.connector.branch_name = "main"
        self.connector.username = self.connector.password = self.connector.access_token = None
        for action, param in ((self.connector._list_files, {}), (self.connector._get_file, {"file_path": "text.txt"})):
            self.connector.repo_name = None
            self.assertEqual(action(param), 0)
            self.assertEqual(self.results[-1].data[0]["repo_name"], "repo_main")


if __name__ == "__main__":
    unittest.main()
