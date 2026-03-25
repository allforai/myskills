#!/usr/bin/env python3
"""Phase 2a: Directory scanning for code-replicate.

CLI: python3 cr_discover.py <source_path> <output_path> [--profile <profile_path>]

If --profile is provided, reads a LLM-generated discovery-profile.json that
describes the project's module structure. This eliminates hardcoded heuristics.

Without --profile, falls back to built-in heuristics (SOURCE_ROOTS, manifests, etc.).
"""

import os
import re
import sys

from _common import write_json, load_json, assign_ids

# ── Fallback Constants (used only when no discovery-profile.json) ─────────────

_DEFAULT_SKIP_DIRS = {
    ".", "node_modules", "vendor", ".git", "__pycache__",
    "dist", "build", ".next", ".nuxt", "target", "bin", "obj",
}

_DEFAULT_SOURCE_ROOTS = {
    "src", "internal", "app", "lib", "packages", "pkg", "cmd",
    "components", "pages", "views", "features", "modules",
}

_DEFAULT_CODE_EXTENSIONS = {
    ".go", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".rs", ".java", ".php", ".rb", ".dart", ".cs",
}

_DEFAULT_ENTRY_POINT_PATTERNS = re.compile(
    r"^(main|index|app|handler|controller|service|router|routes|server|manage)\.",
    re.IGNORECASE,
)

# Active config — initialized from profile or defaults
SKIP_DIRS = set(_DEFAULT_SKIP_DIRS)
SOURCE_ROOTS = set(_DEFAULT_SOURCE_ROOTS)
CODE_EXTENSIONS = set(_DEFAULT_CODE_EXTENSIONS)
ENTRY_POINT_PATTERNS = _DEFAULT_ENTRY_POINT_PATTERNS


def _load_profile(profile_path):
    """Load LLM-generated discovery-profile.json and override active config.

    Profile schema:
    {
      "source_roots": ["src", "packages"],           // override SOURCE_ROOTS
      "skip_dirs": ["node_modules", ".git", ...],    // override SKIP_DIRS
      "code_extensions": [".go", ".py", ...],        // override CODE_EXTENSIONS
      "entry_patterns": ["main", "index", ...],      // override ENTRY_POINT_PATTERNS
      "module_boundaries": [".csproj", "package.json", ...],  // project manifest files/extensions
      "module_paths": [                               // explicit module list (highest priority)
        {"path": "src/ERP.Modules.Sales", "atomic": true},
        {"path": "packages/api/src/modules/user", "atomic": true},
        ...
      ],
      "mega_threshold": 50                            // override _MEGA_MODULE_THRESHOLD
    }

    All fields are optional. Missing fields keep defaults.
    """
    global SKIP_DIRS, SOURCE_ROOTS, CODE_EXTENSIONS, ENTRY_POINT_PATTERNS
    global _MEGA_MODULE_THRESHOLD, _PROJECT_MANIFESTS

    data = load_json(profile_path)
    if not data:
        print(f"WARN: discovery-profile not found or invalid: {profile_path}", file=sys.stderr)
        return None

    if "source_roots" in data:
        SOURCE_ROOTS.clear()
        SOURCE_ROOTS.update(data["source_roots"])

    if "skip_dirs" in data:
        SKIP_DIRS.clear()
        SKIP_DIRS.update(data["skip_dirs"])

    if "code_extensions" in data:
        CODE_EXTENSIONS.clear()
        CODE_EXTENSIONS.update(data["code_extensions"])

    if "entry_patterns" in data:
        patterns = data["entry_patterns"]
        if patterns:
            ENTRY_POINT_PATTERNS = re.compile(
                r"^(" + "|".join(re.escape(p) for p in patterns) + r")\.",
                re.IGNORECASE,
            )

    if "module_boundaries" in data:
        _PROJECT_MANIFESTS.clear()
        for item in data["module_boundaries"]:
            if item.startswith("."):
                # Extension-based: stored separately, handled in _has_project_manifest
                pass  # extensions already handled by endswith check
            else:
                _PROJECT_MANIFESTS.add(item)

    if "mega_threshold" in data:
        _MEGA_MODULE_THRESHOLD = data["mega_threshold"]

    print(f"Loaded discovery profile: {profile_path}", file=sys.stderr)
    return data


# ── Stack Detection ───────────────────────────────────────────────────────────

def _detect_stacks(source_path):
    """Detect technology stacks from manifest files.

    Returns a list of detected stack strings (e.g. ["go", "gin", "gorm"]).
    """
    stacks = []

    # Go
    go_mod = os.path.join(source_path, "go.mod")
    if os.path.isfile(go_mod):
        stacks.append("go")
        try:
            with open(go_mod, encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Detect common Go frameworks from require block
            framework_map = {
                "gin-gonic/gin": "gin",
                "labstack/echo": "echo",
                "gorilla/mux": "gorilla",
                "go-chi/chi": "chi",
                "gofiber/fiber": "fiber",
                "jinzhu/gorm": "gorm",
                "go-gorm/gorm": "gorm",
                "ent/ent": "ent",
                "beego/beego": "beego",
            }
            for pattern, name in framework_map.items():
                if pattern in content and name not in stacks:
                    stacks.append(name)
        except OSError:
            pass

    # Node.js / JavaScript / TypeScript
    pkg_json = os.path.join(source_path, "package.json")
    if os.path.isfile(pkg_json):
        try:
            import json
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {}
            deps.update(pkg.get("dependencies", {}))
            deps.update(pkg.get("devDependencies", {}))

            # Base stack
            if any(f.endswith(".ts") for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))):
                if "typescript" not in stacks:
                    stacks.append("typescript")
            if "node" not in stacks and "javascript" not in stacks:
                stacks.append("node")

            # Framework detection
            framework_map = {
                "express": "express",
                "koa": "koa",
                "fastify": "fastify",
                "hapi": "hapi",
                "nest": "nestjs",
                "@nestjs/core": "nestjs",
                "react": "react",
                "react-dom": "react",
                "vue": "vue",
                "next": "next",
                "nuxt": "nuxt",
                "@angular/core": "angular",
                "svelte": "svelte",
                "@sveltejs/kit": "sveltekit",
                "gatsby": "gatsby",
                "remix": "remix",
                "@remix-run/react": "remix",
                "electron": "electron",
                "react-native": "react-native",
            }
            for dep_key, name in framework_map.items():
                if dep_key in deps and name not in stacks:
                    stacks.append(name)
        except (OSError, ValueError, KeyError):
            if "node" not in stacks:
                stacks.append("node")

    # Python
    py_manifests = ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"]
    for manifest in py_manifests:
        if os.path.isfile(os.path.join(source_path, manifest)):
            if "python" not in stacks:
                stacks.append("python")
            try:
                with open(os.path.join(source_path, manifest), encoding="utf-8", errors="replace") as f:
                    content = f.read().lower()
                py_frameworks = {
                    "django": "django",
                    "flask": "flask",
                    "fastapi": "fastapi",
                    "starlette": "starlette",
                    "tornado": "tornado",
                    "aiohttp": "aiohttp",
                    "celery": "celery",
                    "sqlalchemy": "sqlalchemy",
                }
                for pattern, name in py_frameworks.items():
                    if pattern in content and name not in stacks:
                        stacks.append(name)
            except OSError:
                pass
            break

    # Rust
    if os.path.isfile(os.path.join(source_path, "Cargo.toml")):
        stacks.append("rust")

    # Java
    if os.path.isfile(os.path.join(source_path, "pom.xml")) or \
       os.path.isfile(os.path.join(source_path, "build.gradle")) or \
       os.path.isfile(os.path.join(source_path, "build.gradle.kts")):
        stacks.append("java")

    # PHP
    composer = os.path.join(source_path, "composer.json")
    if os.path.isfile(composer):
        if "php" not in stacks:
            stacks.append("php")
        try:
            import json
            with open(composer, encoding="utf-8") as f:
                comp = json.load(f)
            deps = comp.get("require", {})
            if "laravel/framework" in deps:
                stacks.append("laravel")
            if "symfony/framework-bundle" in deps or "symfony/symfony" in deps:
                stacks.append("symfony")
        except (OSError, ValueError, KeyError):
            pass

    # Ruby
    gemfile = os.path.join(source_path, "Gemfile")
    if os.path.isfile(gemfile):
        if "ruby" not in stacks:
            stacks.append("ruby")
        try:
            with open(gemfile, encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "rails" in content.lower():
                stacks.append("rails")
        except OSError:
            pass

    # Dart / Flutter
    if os.path.isfile(os.path.join(source_path, "pubspec.yaml")):
        stacks.append("dart")
        try:
            with open(os.path.join(source_path, "pubspec.yaml"), encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "flutter" in content.lower():
                stacks.append("flutter")
        except OSError:
            pass

    # C# / .NET
    for fname in os.listdir(source_path):
        if fname.endswith(".csproj") or fname.endswith(".sln"):
            if "csharp" not in stacks:
                stacks.append("csharp")
            if "dotnet" not in stacks:
                stacks.append("dotnet")
            break

    return stacks


# ── Directory Walking ─────────────────────────────────────────────────────────

def _should_skip(dirname):
    """Check if a directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith(".")


def _is_code_file(filename):
    """Check if a file is a recognized code file."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in CODE_EXTENSIONS


def _count_lines(filepath):
    """Count lines in a file, returning 0 on error."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


# ── Module Discovery ──────────────────────────────────────────────────────────

# Maximum code files before a directory is considered a mega-module and split further
_MEGA_MODULE_THRESHOLD = 50

# Project manifest files — if a directory contains one, it's an atomic project unit.
# Size-based splitting is BLOCKED for directories with a manifest (but nested
# SOURCE_ROOT traversal still applies, because monorepo sub-projects like
# packages/api/ have package.json AND contain nested src/modules/).
_PROJECT_MANIFESTS = {
    "package.json", "go.mod", "Cargo.toml", "pubspec.yaml",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "pyproject.toml", "setup.py", "Pipfile",
}
# .csproj/.fsproj/.vbproj are matched by extension, not exact name


def _has_project_manifest(dirpath):
    """Check if directory contains a project manifest file.

    This signals the directory is an atomic project unit — its internal
    sub-directories are architectural layers, not independent modules.
    """
    try:
        for f in os.listdir(dirpath):
            if f in _PROJECT_MANIFESTS:
                return True
            # C#/.NET project files: *.csproj, *.fsproj, *.vbproj
            if f.endswith((".csproj", ".fsproj", ".vbproj", ".sln")):
                return True
    except OSError:
        pass
    return False


def _count_code_files_shallow(dirpath):
    """Count code files in a directory (non-recursive, direct children only)."""
    count = 0
    try:
        for f in os.listdir(dirpath):
            if os.path.isfile(os.path.join(dirpath, f)) and _is_code_file(f):
                count += 1
    except OSError:
        pass
    return count


def _has_sub_modules(dirpath):
    """Check if a directory has sub-directories that look like modules.

    Returns True if the directory has ≥2 sub-dirs each containing code files.
    """
    sub_count = 0
    try:
        for entry in os.listdir(dirpath):
            entry_path = os.path.join(dirpath, entry)
            if os.path.isdir(entry_path) and not _should_skip(entry):
                if _count_code_files_shallow(entry_path) > 0 or _has_nested_code(entry_path):
                    sub_count += 1
                    if sub_count >= 2:
                        return True
    except OSError:
        pass
    return False


def _has_nested_code(dirpath, max_depth=2):
    """Check if a directory has code files within max_depth levels."""
    if max_depth <= 0:
        return False
    try:
        for entry in os.listdir(dirpath):
            fp = os.path.join(dirpath, entry)
            if os.path.isfile(fp) and _is_code_file(entry):
                return True
            if os.path.isdir(fp) and not _should_skip(entry):
                if _has_nested_code(fp, max_depth - 1):
                    return True
    except OSError:
        pass
    return False


def _split_mega_module(rel_path, abs_path, source_path):
    """Recursively split a mega-module into finer-grained sub-modules.

    Pure data-driven strategy (NO hardcoded directory name lists):
    1. If the directory contains a nested SOURCE_ROOT (e.g., src/ or modules/),
       always recurse through it. This handles monorepo chains like
       packages/api/src/modules/user/.
    2. If the directory exceeds the file threshold AND has no project manifest
       (.csproj, package.json, etc.) AND has sub-dirs that look like modules,
       split into children.
    3. If the directory HAS a project manifest, it's an atomic project unit —
       never split by size (its sub-dirs are architectural layers, not modules).
    4. Otherwise keep as-is — it's a leaf module.

    Returns list of (relative_path, absolute_path) tuples.
    """
    # Strategy 1: nested SOURCE_ROOTS — always recurse.
    # This is the only place that uses the SOURCE_ROOTS name list, which is
    # acceptable because it's filesystem-structural (not semantic guessing).
    for root_name in SOURCE_ROOTS:
        nested_root = os.path.join(abs_path, root_name)
        if os.path.isdir(nested_root):
            results = []
            try:
                entries = sorted(os.listdir(nested_root))
            except OSError:
                continue
            for entry in entries:
                entry_path = os.path.join(nested_root, entry)
                if os.path.isdir(entry_path) and not _should_skip(entry):
                    child_rel = os.path.join(rel_path, root_name, entry)
                    results.extend(_split_mega_module(child_rel, entry_path, source_path))
            if results:
                return results

    # Strategy 2: size-based split — BLOCKED if project manifest exists.
    # A directory with .csproj / package.json / go.mod is an atomic project.
    # Its internal Views/ViewModels/Models are layers, not independent modules.
    if _has_project_manifest(abs_path):
        return [(rel_path, abs_path)]

    # No manifest: split if file count exceeds threshold and has sub-modules
    file_count = len(_collect_module_files(abs_path))
    if file_count > _MEGA_MODULE_THRESHOLD and _has_sub_modules(abs_path):
        results = []
        for entry in sorted(os.listdir(abs_path)):
            entry_path = os.path.join(abs_path, entry)
            if os.path.isdir(entry_path) and not _should_skip(entry):
                child_rel = os.path.join(rel_path, entry)
                results.extend(_split_mega_module(child_rel, entry_path, source_path))
        if results:
            return results

    # Leaf module
    return [(rel_path, abs_path)]


def _find_module_dirs(source_path, profile=None):
    """Find module directories.

    If profile contains explicit module_paths, use them directly (LLM-guided).
    Otherwise fall back to SOURCE_ROOT scanning + mega-module splitting.

    Returns list of (relative_path, absolute_path) tuples.
    """
    # ── Priority 1: LLM-generated explicit module list ────────────────────
    if profile and profile.get("module_paths"):
        modules = []
        for entry in profile["module_paths"]:
            rel = entry["path"] if isinstance(entry, dict) else entry
            abs_path = os.path.join(source_path, rel)
            if os.path.isdir(abs_path):
                modules.append((rel, abs_path))
            else:
                print(f"WARN: profile module_path not found: {rel}", file=sys.stderr)
        if modules:
            print(f"Using {len(modules)} modules from discovery profile", file=sys.stderr)
            return modules
        # Fall through if all paths invalid

    # ── Priority 2: SOURCE_ROOT scanning + splitting ──────────────────────
    modules = []

    found_roots = []
    for root_name in SOURCE_ROOTS:
        root_path = os.path.join(source_path, root_name)
        if os.path.isdir(root_path):
            found_roots.append((root_name, root_path))

    if found_roots:
        for root_name, root_path in found_roots:
            for entry in sorted(os.listdir(root_path)):
                entry_path = os.path.join(root_path, entry)
                if os.path.isdir(entry_path) and not _should_skip(entry):
                    rel = os.path.join(root_name, entry)
                    modules.extend(_split_mega_module(rel, entry_path, source_path))
    else:
        for entry in sorted(os.listdir(source_path)):
            entry_path = os.path.join(source_path, entry)
            if os.path.isdir(entry_path) and not _should_skip(entry):
                modules.extend(_split_mega_module(entry, entry_path, source_path))

    return modules


def _collect_module_files(module_abs_path):
    """Collect all code files in a module directory (recursive).

    Returns list of (relative_path, absolute_path) for code files.
    """
    files = []
    for dirpath, dirnames, filenames in os.walk(module_abs_path):
        # Filter out skip dirs in-place
        dirnames[:] = [d for d in dirnames if not _should_skip(d)]
        for fname in sorted(filenames):
            if _is_code_file(fname):
                abs_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(abs_path, module_abs_path)
                files.append((rel_path, abs_path))
    return files


def _is_key_file(filename):
    """Check if a filename matches entry point patterns."""
    return bool(ENTRY_POINT_PATTERNS.match(filename))


# ── Import Parsing ────────────────────────────────────────────────────────────

# Go: import "module/path/pkg"
_GO_IMPORT_RE = re.compile(r'^\s*(?:import\s+)?"([^"]+)"', re.MULTILINE)
# Also handle import blocks
_GO_IMPORT_BLOCK_RE = re.compile(r'import\s*\((.*?)\)', re.DOTALL)
_GO_IMPORT_LINE_RE = re.compile(r'"([^"]+)"')

# JS/TS: import ... from "path" or require("path")
_JS_IMPORT_RE = re.compile(
    r'''(?:import\s+.*?\s+from\s+|require\s*\(\s*)['"]([^'"]+)['"]''',
    re.MULTILINE,
)

# Python: from app.module import ... or import app.module
_PY_IMPORT_RE = re.compile(
    r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
    re.MULTILINE,
)


def _parse_imports(filepath, source_path):
    """Parse imports from a source file.

    Returns set of relative directory paths that this file imports from.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    imports = set()

    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return imports

    if ext == ".go":
        # Parse Go imports
        # Single imports
        for m in _GO_IMPORT_RE.finditer(content):
            imports.add(m.group(1))
        # Import blocks
        for block in _GO_IMPORT_BLOCK_RE.finditer(content):
            for m in _GO_IMPORT_LINE_RE.finditer(block.group(1)):
                imports.add(m.group(1))

    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        for m in _JS_IMPORT_RE.finditer(content):
            path = m.group(1)
            if path.startswith(".") or path.startswith("@/") or path.startswith("~/"):
                imports.add(path)

    elif ext == ".py":
        for m in _PY_IMPORT_RE.finditer(content):
            mod = m.group(1) or m.group(2)
            if mod:
                imports.add(mod)

    return imports


def _resolve_import_to_module(imp, module_map, source_path, stacks):
    """Try to resolve an import string to a module ID.

    Args:
        imp: Raw import string
        module_map: {relative_path: module_id}
        source_path: Root source directory
        stacks: Detected stacks list

    Returns module_id string or None.
    """
    # Go: import paths often end with the package dir
    if "go" in stacks:
        # Try matching the last path segments against module relative paths
        parts = imp.split("/")
        for n in range(1, len(parts) + 1):
            suffix = "/".join(parts[-n:])
            for mod_path, mod_id in module_map.items():
                if mod_path == suffix or mod_path.endswith("/" + suffix):
                    return mod_id

    # JS/TS: resolve relative and alias paths
    if any(s in stacks for s in ("node", "javascript", "typescript", "react", "vue", "next")):
        path = imp
        # @/ or ~/ alias → src/
        if path.startswith("@/") or path.startswith("~/"):
            path = "src/" + path[2:]
        # Strip leading ./
        if path.startswith("./"):
            path = path[2:]
        elif path.startswith("../"):
            # Can't resolve parent refs without knowing the importing file's location
            return None
        # Try matching against module paths
        for mod_path, mod_id in module_map.items():
            if path.startswith(mod_path + "/") or path == mod_path:
                return mod_id
            # Also try without src/ prefix
            if mod_path.startswith("src/") and path.startswith(mod_path[4:] + "/"):
                return mod_id

    # Python: dotted module paths
    if "python" in stacks:
        parts = imp.split(".")
        # Try matching first 1-3 segments as directory paths
        for n in range(min(3, len(parts)), 0, -1):
            candidate = "/".join(parts[:n])
            for mod_path, mod_id in module_map.items():
                if mod_path == candidate or mod_path.endswith("/" + candidate):
                    return mod_id

    return None


# ── Main Scanner ──────────────────────────────────────────────────────────────

def scan_project(source_path, profile_path=None):
    """Scan source project directory and return source-summary skeleton.

    Args:
        source_path: Root directory of source project.
        profile_path: Optional path to LLM-generated discovery-profile.json.
                      If provided, overrides hardcoded heuristics.

    Returns a dict with project info, modules, and empty fields for LLM phases.
    """
    source_path = os.path.abspath(source_path)

    # Load profile if provided
    profile = None
    if profile_path:
        profile = _load_profile(profile_path)

    # Detect project name from directory or manifest
    project_name = os.path.basename(source_path)

    # Detect stacks
    stacks = _detect_stacks(source_path)

    # Find modules (profile-guided or fallback heuristics)
    module_dirs = _find_module_dirs(source_path, profile=profile)

    # Build modules
    modules = []
    module_map = {}  # relative_path → module_id (filled after ID assignment)
    total_files = 0
    total_lines = 0

    for rel_path, abs_path in module_dirs:
        code_files = _collect_module_files(abs_path)
        if not code_files:
            continue  # Skip empty directories

        file_count = len(code_files)
        line_count = sum(_count_lines(fp) for _, fp in code_files)

        # Identify key files — scan ALL levels, not just top-level
        key_files = []
        for rel_file, _ in code_files:
            basename = os.path.basename(rel_file)
            if _is_key_file(basename):
                key_files.append(rel_file)

        # If no entry-point pattern match, use heuristics:
        if not key_files:
            # 1. Try top-level files first
            top_files = [rf for rf, _ in code_files if os.sep not in rf and "/" not in rf]
            if top_files:
                key_files = top_files[:5]
            else:
                # 2. Deepest-nested entry points (e.g., src/modules/user/user.controller.ts)
                key_files = [rf for rf, _ in code_files[:10]]

        # Cap key_files to avoid overwhelming LLM context
        if len(key_files) > 10:
            key_files = key_files[:10]

        module = {
            "id": "",  # assigned below
            "path": rel_path,
            "responsibility": "",
            "exposed_interfaces": [],
            "dependencies": [],
            "key_files": key_files,
            "file_count": file_count,
            "line_count": line_count,
            "confidence": "skeleton",
        }
        modules.append(module)
        total_files += file_count
        total_lines += line_count

    # Assign IDs
    assign_ids(modules, prefix="M", start=1)

    # Build module_map for dependency resolution
    for mod in modules:
        module_map[mod["path"]] = mod["id"]

    # Parse imports and resolve dependencies
    for mod in modules:
        abs_mod_path = os.path.join(source_path, mod["path"])
        code_files = _collect_module_files(abs_mod_path)
        all_imports = set()
        for _, abs_file in code_files:
            all_imports.update(_parse_imports(abs_file, source_path))

        dep_ids = set()
        for imp in all_imports:
            target_id = _resolve_import_to_module(imp, module_map, source_path, stacks)
            if target_id and target_id != mod["id"]:
                dep_ids.add(target_id)

        mod["dependencies"] = sorted(dep_ids)

    # Also count files not in modules
    for dirpath, dirnames, filenames in os.walk(source_path):
        dirnames[:] = [d for d in dirnames if not _should_skip(d)]
        for fname in filenames:
            if _is_code_file(fname):
                abs_file = os.path.join(dirpath, fname)
                rel_file = os.path.relpath(abs_file, source_path)
                # Check if this file is in any module
                in_module = any(rel_file.startswith(m["path"] + os.sep) or
                                rel_file.startswith(m["path"] + "/")
                                for m in modules)
                if not in_module:
                    total_files += 1
                    total_lines += _count_lines(abs_file)

    return {
        "project": {
            "name": project_name,
            "detected_stacks": stacks,
            "total_files": total_files,
            "total_lines": total_lines,
        },
        "modules": modules,
        "cross_cutting": [],
        "data_entities": [],
        "infrastructure": {},
        "api_call_map": {},
    }


# ── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 cr_discover.py <source_path> <output_path> [--profile <profile_path>]", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2]

    # Optional --profile flag
    profile_path = None
    if "--profile" in sys.argv:
        idx = sys.argv.index("--profile")
        if idx + 1 < len(sys.argv):
            profile_path = sys.argv[idx + 1]

    if not os.path.isdir(source):
        print(f"ERROR: source path does not exist: {source}", file=sys.stderr)
        sys.exit(1)

    result = scan_project(source, profile_path=profile_path)
    write_json(output, result)
    print(f"Source summary written to {output}")
    if profile_path:
        print(f"  Profile: {profile_path}")
    print(f"  Project: {result['project']['name']}")
    print(f"  Stacks: {result['project']['detected_stacks']}")
    print(f"  Modules: {len(result['modules'])}")
    print(f"  Files: {result['project']['total_files']}, Lines: {result['project']['total_lines']}")
