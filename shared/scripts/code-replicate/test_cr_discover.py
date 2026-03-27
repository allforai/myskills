#!/usr/bin/env python3
"""Tests for cr_discover.py — Phase 2a directory scanner."""

import json
import os
import tempfile
import unittest

from cr_discover import scan_project


class TestScanGoProject(unittest.TestCase):
    """Scan a temp Go project with go.mod + internal/auth + internal/user."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # go.mod
        with open(os.path.join(self.tmpdir, "go.mod"), "w", encoding="utf-8") as f:
            f.write('module example.com/myapp\n\ngo 1.21\n\n'
                    'require (\n'
                    '\tgithub.com/gin-gonic/gin v1.9.0\n'
                    '\tgithub.com/go-gorm/gorm v1.25.0\n'
                    ')\n')

        # internal/auth
        auth_dir = os.path.join(self.tmpdir, "internal", "auth")
        os.makedirs(auth_dir)
        with open(os.path.join(auth_dir, "handler.go"), "w", encoding="utf-8") as f:
            f.write('package auth\n\n'
                    'import (\n'
                    '\t"example.com/myapp/internal/user"\n'
                    ')\n\n'
                    'func Handler() {\n'
                    '\tuser.GetByID(1)\n'
                    '}\n')

        # internal/user
        user_dir = os.path.join(self.tmpdir, "internal", "user")
        os.makedirs(user_dir)
        with open(os.path.join(user_dir, "service.go"), "w", encoding="utf-8") as f:
            f.write('package user\n\n'
                    'func GetByID(id int) {\n'
                    '}\n')
        with open(os.path.join(user_dir, "model.go"), "w", encoding="utf-8") as f:
            f.write('package user\n\n'
                    'type User struct {\n'
                    '\tID   int\n'
                    '\tName string\n'
                    '}\n')

    def test_detect_go_stack(self):
        result = scan_project(self.tmpdir)
        stacks = result["project"]["detected_stacks"]
        self.assertIn("go", stacks)
        self.assertIn("gin", stacks)
        self.assertIn("gorm", stacks)

    def test_find_modules(self):
        result = scan_project(self.tmpdir)
        modules = result["modules"]
        self.assertGreaterEqual(len(modules), 2)
        paths = [m["path"] for m in modules]
        self.assertIn(os.path.join("internal", "auth"), paths)
        self.assertIn(os.path.join("internal", "user"), paths)

    def test_module_ids_sequential(self):
        result = scan_project(self.tmpdir)
        ids = [m["id"] for m in result["modules"]]
        self.assertEqual(ids[0], "M001")
        self.assertEqual(ids[1], "M002")

    def test_dependencies_detected(self):
        result = scan_project(self.tmpdir)
        modules = {m["path"]: m for m in result["modules"]}
        auth = modules[os.path.join("internal", "auth")]
        user = modules[os.path.join("internal", "user")]
        # auth should depend on user
        self.assertIn(user["id"], auth["dependencies"])
        # user should NOT depend on auth
        self.assertNotIn(auth["id"], user["dependencies"])

    def test_file_counts(self):
        result = scan_project(self.tmpdir)
        modules = {m["path"]: m for m in result["modules"]}
        auth = modules[os.path.join("internal", "auth")]
        user = modules[os.path.join("internal", "user")]
        self.assertEqual(auth["file_count"], 1)
        self.assertEqual(user["file_count"], 2)

    def test_total_counts(self):
        result = scan_project(self.tmpdir)
        self.assertEqual(result["project"]["total_files"], 3)
        self.assertGreater(result["project"]["total_lines"], 0)

    def test_project_name(self):
        result = scan_project(self.tmpdir)
        self.assertEqual(result["project"]["name"], os.path.basename(self.tmpdir))


class TestScanNodeProject(unittest.TestCase):
    """Scan a temp Node.js project with package.json + express."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # package.json
        pkg = {
            "name": "my-api",
            "dependencies": {
                "express": "^4.18.0",
                "mongoose": "^7.0.0"
            }
        }
        with open(os.path.join(self.tmpdir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg, f, ensure_ascii=False)

        # src/routes
        routes_dir = os.path.join(self.tmpdir, "src", "routes")
        os.makedirs(routes_dir)
        with open(os.path.join(routes_dir, "index.js"), "w", encoding="utf-8") as f:
            f.write('const express = require("express");\n'
                    'const users = require("../controllers/userController");\n'
                    'module.exports = router;\n')

        # src/controllers
        ctrl_dir = os.path.join(self.tmpdir, "src", "controllers")
        os.makedirs(ctrl_dir)
        with open(os.path.join(ctrl_dir, "userController.js"), "w", encoding="utf-8") as f:
            f.write('const UserService = require("../services/userService");\n'
                    'exports.getUser = (req, res) => {};\n')

        # src/services
        svc_dir = os.path.join(self.tmpdir, "src", "services")
        os.makedirs(svc_dir)
        with open(os.path.join(svc_dir, "userService.js"), "w", encoding="utf-8") as f:
            f.write('class UserService {}\n'
                    'module.exports = UserService;\n')

    def test_detect_node_stack(self):
        result = scan_project(self.tmpdir)
        stacks = result["project"]["detected_stacks"]
        self.assertIn("node", stacks)
        self.assertIn("express", stacks)

    def test_find_src_modules(self):
        result = scan_project(self.tmpdir)
        paths = [m["path"] for m in result["modules"]]
        self.assertIn(os.path.join("src", "routes"), paths)
        self.assertIn(os.path.join("src", "controllers"), paths)
        self.assertIn(os.path.join("src", "services"), paths)

    def test_key_files_detected(self):
        result = scan_project(self.tmpdir)
        modules = {m["path"]: m for m in result["modules"]}
        routes = modules[os.path.join("src", "routes")]
        self.assertIn("index.js", routes["key_files"])


class TestScanPythonProject(unittest.TestCase):
    """Scan a temp Python project with requirements.txt + django."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # requirements.txt
        with open(os.path.join(self.tmpdir, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("django==4.2\ncelery==5.3\nredis==5.0\n")

        # app/models
        models_dir = os.path.join(self.tmpdir, "app", "models")
        os.makedirs(models_dir)
        with open(os.path.join(models_dir, "user.py"), "w", encoding="utf-8") as f:
            f.write('from app.services import auth_service\n\n'
                    'class User:\n'
                    '    pass\n')

        # app/services
        svc_dir = os.path.join(self.tmpdir, "app", "services")
        os.makedirs(svc_dir)
        with open(os.path.join(svc_dir, "auth_service.py"), "w", encoding="utf-8") as f:
            f.write('def authenticate(user, password):\n'
                    '    pass\n')

    def test_detect_python_stack(self):
        result = scan_project(self.tmpdir)
        stacks = result["project"]["detected_stacks"]
        self.assertIn("python", stacks)
        self.assertIn("django", stacks)
        self.assertIn("celery", stacks)

    def test_find_app_modules(self):
        result = scan_project(self.tmpdir)
        paths = [m["path"] for m in result["modules"]]
        self.assertIn(os.path.join("app", "models"), paths)
        self.assertIn(os.path.join("app", "services"), paths)


class TestModuleFields(unittest.TestCase):
    """Verify module has all required fields."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        with open(os.path.join(self.tmpdir, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module example.com/test\n\ngo 1.21\n")
        src_dir = os.path.join(self.tmpdir, "internal", "core")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "main.go"), "w", encoding="utf-8") as f:
            f.write("package core\n\nfunc Main() {}\n")

    def test_required_fields(self):
        result = scan_project(self.tmpdir)
        self.assertGreater(len(result["modules"]), 0)
        mod = result["modules"][0]
        self.assertIn("id", mod)
        self.assertIn("path", mod)
        self.assertIn("responsibility", mod)
        self.assertIn("exposed_interfaces", mod)
        self.assertIn("dependencies", mod)
        self.assertIn("key_files", mod)
        self.assertIn("file_count", mod)
        self.assertIn("line_count", mod)
        self.assertIn("confidence", mod)
        self.assertEqual(mod["confidence"], "skeleton")
        self.assertEqual(mod["responsibility"], "")
        self.assertEqual(mod["exposed_interfaces"], [])

    def test_top_level_fields(self):
        result = scan_project(self.tmpdir)
        self.assertIn("project", result)
        self.assertIn("modules", result)
        self.assertIn("cross_cutting", result)
        self.assertIn("data_entities", result)
        self.assertIn("infrastructure", result)
        self.assertIn("api_call_map", result)
        self.assertEqual(result["cross_cutting"], [])
        self.assertEqual(result["data_entities"], [])
        self.assertEqual(result["infrastructure"], {})
        self.assertEqual(result["api_call_map"], {})


class TestSkipDirs(unittest.TestCase):
    """Verify hidden dirs and node_modules are skipped."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        with open(os.path.join(self.tmpdir, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module test\n\ngo 1.21\n")
        # Create a real module
        real_dir = os.path.join(self.tmpdir, "internal", "real")
        os.makedirs(real_dir)
        with open(os.path.join(real_dir, "main.go"), "w", encoding="utf-8") as f:
            f.write("package real\n")
        # Create dirs that should be skipped
        for skip in [".git", "node_modules", "vendor", "__pycache__"]:
            skip_dir = os.path.join(self.tmpdir, skip)
            os.makedirs(skip_dir)
            with open(os.path.join(skip_dir, "file.go"), "w", encoding="utf-8") as f:
                f.write("package skip\n")

    def test_skip_dirs_excluded(self):
        result = scan_project(self.tmpdir)
        paths = [m["path"] for m in result["modules"]]
        for skip in [".git", "node_modules", "vendor", "__pycache__"]:
            self.assertNotIn(skip, paths)


class TestFallbackTopLevel(unittest.TestCase):
    """When no standard source root exists, use top-level dirs."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # No src/, internal/, etc — just top-level dirs
        for name in ["api", "web"]:
            d = os.path.join(self.tmpdir, name)
            os.makedirs(d)
            with open(os.path.join(d, "main.py"), "w", encoding="utf-8") as f:
                f.write("# module\n")

    def test_top_level_dirs_as_modules(self):
        result = scan_project(self.tmpdir)
        paths = [m["path"] for m in result["modules"]]
        self.assertIn("api", paths)
        self.assertIn("web", paths)


if __name__ == "__main__":
    unittest.main()
