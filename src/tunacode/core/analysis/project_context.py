"""Fast project context detection for intelligent task generation."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from ..code_index import CodeIndex


class ProjectType(Enum):
    """Supported project types."""

    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    DOTNET = "dotnet"
    RUBY = "ruby"
    PHP = "php"
    UNKNOWN = "unknown"


@dataclass
class ProjectInfo:
    """Project context information."""

    project_type: ProjectType
    name: Optional[str] = None
    description: Optional[str] = None
    main_language: Optional[str] = None
    framework: Optional[str] = None
    source_dirs: List[str] = None
    test_dirs: List[str] = None
    entry_points: List[str] = None
    config_files: List[str] = None
    dependencies: Dict[str, str] = None
    has_tests: bool = False
    has_docs: bool = False
    has_ci: bool = False

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.source_dirs is None:
            self.source_dirs = []
        if self.test_dirs is None:
            self.test_dirs = []
        if self.entry_points is None:
            self.entry_points = []
        if self.config_files is None:
            self.config_files = []
        if self.dependencies is None:
            self.dependencies = {}


class ProjectContext:
    """Fast project context detection using cached file index."""

    # Project detection patterns
    PROJECT_MARKERS = {
        ProjectType.PYTHON: {
            "files": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"],
            "dirs": ["src", "lib", "app", "tests", "test"],
            "frameworks": {
                "django": ["manage.py", "settings.py", "urls.py"],
                "flask": ["app.py", "application.py", "wsgi.py"],
                "fastapi": ["main.py", "api.py"],
                "pytest": ["conftest.py", "pytest.ini"],
            },
        },
        ProjectType.NODEJS: {
            "files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
            "dirs": ["src", "lib", "app", "dist", "build", "test", "tests"],
            "frameworks": {
                "react": ["App.js", "App.jsx", "App.tsx", "index.js"],
                "vue": ["App.vue", "main.js", "vue.config.js"],
                "express": ["app.js", "server.js", "index.js"],
                "next": ["next.config.js", "pages", "_app.js"],
            },
        },
        ProjectType.RUST: {
            "files": ["Cargo.toml", "Cargo.lock"],
            "dirs": ["src", "tests", "benches", "examples"],
            "frameworks": {
                "actix": ["main.rs"],
                "rocket": ["main.rs"],
                "tokio": ["main.rs"],
            },
        },
        ProjectType.GO: {
            "files": ["go.mod", "go.sum"],
            "dirs": ["cmd", "internal", "pkg", "test"],
            "frameworks": {
                "gin": ["main.go"],
                "echo": ["main.go"],
                "fiber": ["main.go"],
            },
        },
        ProjectType.JAVA: {
            "files": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
            "dirs": ["src/main/java", "src/test/java", "src/main/resources"],
            "frameworks": {
                "spring": ["Application.java", "application.properties"],
                "maven": ["pom.xml"],
                "gradle": ["build.gradle"],
            },
        },
    }

    def __init__(self, code_index: CodeIndex):
        """Initialize with a code index."""
        self.code_index = code_index
        self._context_cache: Optional[ProjectInfo] = None

    def detect_context(self, force_refresh: bool = False) -> ProjectInfo:
        """Detect project type and structure with caching.

        Args:
            force_refresh: Force re-detection even if cached

        Returns:
            ProjectInfo with detected project context
        """
        if self._context_cache and not force_refresh:
            return self._context_cache

        # Ensure index is built
        if not self.code_index._indexed:
            self.code_index.build_index()

        # Detect project type
        project_type = self._detect_project_type()

        # Create base project info
        info = ProjectInfo(project_type=project_type)

        # Extract detailed information based on type
        if project_type != ProjectType.UNKNOWN:
            self._extract_project_details(info)

        # Detect common patterns
        self._detect_common_patterns(info)

        # Cache the result
        self._context_cache = info
        return info

    def _detect_project_type(self) -> ProjectType:
        """Quickly detect the primary project type."""
        # Count markers for each project type
        scores = {}

        for proj_type, markers in self.PROJECT_MARKERS.items():
            score = 0

            # Check for marker files (higher weight)
            for marker_file in markers["files"]:
                if self.code_index.lookup(marker_file):
                    score += 3

            # Check for marker directories (lower weight)
            for marker_dir in markers["dirs"]:
                # Quick check if directory exists
                dir_path = Path(self.code_index.root_dir) / marker_dir
                if dir_path.exists() and dir_path.is_dir():
                    score += 1

            if score > 0:
                scores[proj_type] = score

        # Return type with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return ProjectType.UNKNOWN

    def _extract_project_details(self, info: ProjectInfo) -> None:
        """Extract detailed project information based on type."""
        extractors = {
            ProjectType.PYTHON: self._extract_python_details,
            ProjectType.NODEJS: self._extract_nodejs_details,
            ProjectType.RUST: self._extract_rust_details,
            ProjectType.GO: self._extract_go_details,
            ProjectType.JAVA: self._extract_java_details,
        }

        extractor = extractors.get(info.project_type)
        if extractor:
            extractor(info)

    def _extract_python_details(self, info: ProjectInfo) -> None:
        """Extract Python project details."""
        info.main_language = "Python"

        # Check for pyproject.toml first (modern Python)
        pyproject_files = self.code_index.lookup("pyproject.toml")
        if pyproject_files:
            info.config_files.append(str(pyproject_files[0]))
            # Could parse TOML here for name/description, but keeping it fast

        # Check for setup.py (legacy)
        setup_files = self.code_index.lookup("setup.py")
        if setup_files:
            info.config_files.append(str(setup_files[0]))

        # Detect framework
        markers = self.PROJECT_MARKERS[ProjectType.PYTHON]["frameworks"]
        for framework, files in markers.items():
            for marker_file in files:
                if self.code_index.lookup(marker_file):
                    info.framework = framework
                    break

        # Find source directories
        for src_dir in ["src", "lib", "app", info.name if info.name else ""]:
            if src_dir and Path(self.code_index.root_dir, src_dir).exists():
                info.source_dirs.append(src_dir)

        # Find test directories
        for test_dir in ["tests", "test"]:
            if Path(self.code_index.root_dir, test_dir).exists():
                info.test_dirs.append(test_dir)
                info.has_tests = True

        # Find entry points
        common_entries = ["main.py", "app.py", "__main__.py", "cli.py"]
        for entry in common_entries:
            entries = self.code_index.lookup(entry)
            if entries:
                info.entry_points.extend([str(e) for e in entries[:2]])  # Limit to 2

    def _extract_nodejs_details(self, info: ProjectInfo) -> None:
        """Extract Node.js project details."""
        info.main_language = "JavaScript/TypeScript"

        # Check for package.json
        package_files = self.code_index.lookup("package.json")
        if package_files:
            info.config_files.append(str(package_files[0]))
            # Could parse JSON here for name/description, but keeping it fast

        # Check for TypeScript
        tsconfig_files = self.code_index.lookup("tsconfig.json")
        if tsconfig_files:
            info.config_files.append(str(tsconfig_files[0]))
            info.main_language = "TypeScript"

        # Detect framework
        markers = self.PROJECT_MARKERS[ProjectType.NODEJS]["frameworks"]
        for framework, files in markers.items():
            for marker_file in files:
                if self.code_index.lookup(marker_file):
                    info.framework = framework
                    break

        # Find source directories
        for src_dir in ["src", "lib", "app"]:
            if Path(self.code_index.root_dir, src_dir).exists():
                info.source_dirs.append(src_dir)

        # Find test directories
        for test_dir in ["test", "tests", "__tests__", "spec"]:
            if Path(self.code_index.root_dir, test_dir).exists():
                info.test_dirs.append(test_dir)
                info.has_tests = True

        # Find entry points
        common_entries = ["index.js", "index.ts", "main.js", "main.ts", "app.js", "app.ts"]
        for entry in common_entries:
            entries = self.code_index.lookup(entry)
            if entries:
                info.entry_points.extend([str(e) for e in entries[:2]])

    def _extract_rust_details(self, info: ProjectInfo) -> None:
        """Extract Rust project details."""
        info.main_language = "Rust"

        # Check for Cargo.toml
        cargo_files = self.code_index.lookup("Cargo.toml")
        if cargo_files:
            info.config_files.append(str(cargo_files[0]))

        # Source is always src/ in Rust
        if Path(self.code_index.root_dir, "src").exists():
            info.source_dirs.append("src")

        # Check for tests
        if Path(self.code_index.root_dir, "tests").exists():
            info.test_dirs.append("tests")
            info.has_tests = True

        # Find entry points
        main_rs = self.code_index.lookup("main.rs")
        lib_rs = self.code_index.lookup("lib.rs")
        if main_rs:
            info.entry_points.append(str(main_rs[0]))
        if lib_rs:
            info.entry_points.append(str(lib_rs[0]))

    def _extract_go_details(self, info: ProjectInfo) -> None:
        """Extract Go project details."""
        info.main_language = "Go"

        # Check for go.mod
        gomod_files = self.code_index.lookup("go.mod")
        if gomod_files:
            info.config_files.append(str(gomod_files[0]))

        # Find source directories (Go convention)
        for src_dir in ["cmd", "internal", "pkg"]:
            if Path(self.code_index.root_dir, src_dir).exists():
                info.source_dirs.append(src_dir)

        # Find test files (Go tests are alongside source)
        info.has_tests = bool(self.code_index.lookup("_test.go"))

        # Find entry points
        main_go = self.code_index.lookup("main.go")
        if main_go:
            info.entry_points.extend([str(e) for e in main_go[:2]])

    def _extract_java_details(self, info: ProjectInfo) -> None:
        """Extract Java project details."""
        info.main_language = "Java"

        # Check build system
        if self.code_index.lookup("pom.xml"):
            info.config_files.append("pom.xml")
            info.framework = "maven"
        elif self.code_index.lookup("build.gradle"):
            info.config_files.append("build.gradle")
            info.framework = "gradle"

        # Standard Maven/Gradle structure
        for src_dir in ["src/main/java", "src/main/kotlin"]:
            if Path(self.code_index.root_dir, src_dir).exists():
                info.source_dirs.append(src_dir)

        for test_dir in ["src/test/java", "src/test/kotlin"]:
            if Path(self.code_index.root_dir, test_dir).exists():
                info.test_dirs.append(test_dir)
                info.has_tests = True

    def _detect_common_patterns(self, info: ProjectInfo) -> None:
        """Detect common patterns across all project types."""
        # Check for documentation
        doc_markers = ["README.md", "README.rst", "README.txt", "docs", "documentation"]
        for marker in doc_markers:
            if marker.startswith("README"):
                if self.code_index.lookup(marker):
                    info.has_docs = True
                    break
            else:
                if Path(self.code_index.root_dir, marker).exists():
                    info.has_docs = True
                    break

        # Check for CI/CD
        ci_markers = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci/config.yml",
        ]
        for marker in ci_markers:
            if marker.endswith(".yml") or marker == "Jenkinsfile":
                if self.code_index.lookup(marker):
                    info.has_ci = True
                    break
            else:
                if Path(self.code_index.root_dir, marker).exists():
                    info.has_ci = True
                    break

    def get_relevant_files(self, max_files: int = 10) -> List[str]:
        """Get the most relevant files to read for understanding the project.

        Args:
            max_files: Maximum number of files to return

        Returns:
            List of file paths to read
        """
        if not self._context_cache:
            self.detect_context()

        info = self._context_cache
        relevant = []

        # Always include config files
        relevant.extend(info.config_files[:3])

        # Include entry points
        relevant.extend(info.entry_points[:2])

        # Include README
        readme_files = ["README.md", "README.rst", "README.txt"]
        for readme in readme_files:
            matches = self.code_index.lookup(readme)
            if matches:
                relevant.append(str(matches[0]))
                break

        # Include framework-specific files
        if info.framework == "django":
            settings = self.code_index.lookup("settings.py")
            if settings:
                relevant.append(str(settings[0]))
        elif info.framework == "flask":
            app_py = self.code_index.lookup("app.py")
            if app_py:
                relevant.append(str(app_py[0]))

        # Remove duplicates and limit
        seen = set()
        unique = []
        for f in relevant:
            if f not in seen:
                seen.add(f)
                unique.append(f)

        return unique[:max_files]
