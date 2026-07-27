"""Initialize repository use case.

Creates a new Git repository with optional scaffold files.
"""

from __future__ import annotations

from pathlib import Path

from gitory.infrastructure.git_executor import GitExecutor


class InitRepository:
    """Initializes a new Git repository with optional files.

    Supports creating README.md, .gitignore, and MIT LICENSE.
    """

    def __init__(self, executor: GitExecutor) -> None:
        self._executor = executor

    def execute(
        self,
        path: Path,
        name: str = "",
        create_readme: bool = True,
        create_gitignore: bool = True,
        create_license: bool = False,
    ) -> tuple[bool, str]:
        """Initialize a new repository.

        Args:
            path: Directory to initialize.
            name: Repository name (used in README).
            create_readme: Create a README.md file.
            create_gitignore: Create a .gitignore file.
            create_license: Create a MIT LICENSE file.

        Returns:
            Tuple of (success, error_message).
        """
        path = path.resolve()
        name = name or path.name

        # Create directory if needed.
        path.mkdir(parents=True, exist_ok=True)

        # Run git init.
        self._executor.repo_path = path
        result = self._executor.run("init", str(path), use_repo_path=False)
        if not result.success:
            return False, f"git init failed: {result.error_message}"

        # Update executor path now that repo exists.
        self._executor.repo_path = path

        # Create scaffold files.
        if create_readme:
            readme = path / "README.md"
            readme.write_text(f"# {name}\n", encoding="utf-8")

        if create_gitignore:
            gitignore = path / ".gitignore"
            gitignore.write_text(
                "# Python\n__pycache__/\n*.py[cod]\n*.egg-info/\ndist/\nbuild/\n"
                ".venv/\nvenv/\n\n# IDE\n.vscode/\n.idea/\n*.swp\n\n"
                "# OS\n.DS_Store\nThumbs.db\n",
                encoding="utf-8",
            )

        if create_license:
            license_file = path / "LICENSE"
            license_file.write_text(
                "MIT License\n\n"
                "Copyright (c) 2025\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
                "of this software and associated documentation files (the \"Software\"), to deal\n"
                "in the Software without restriction, including without limitation the rights\n"
                "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
                "copies of the Software, and to permit persons to whom the Software is\n"
                "furnished to do so, subject to the following conditions:\n\n"
                "The above copyright notice and this permission notice shall be included in all\n"
                "copies or substantial portions of the Software.\n\n"
                'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
                "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
                "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
                "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
                "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
                "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
                "SOFTWARE.\n",
                encoding="utf-8",
            )

        # Stage and commit initial files.
        files_created = []
        if create_readme:
            files_created.append("README.md")
        if create_gitignore:
            files_created.append(".gitignore")
        if create_license:
            files_created.append("LICENSE")

        if files_created:
            self._executor.run("add", *files_created)
            commit_res = self._executor.run("commit", "-m", "Initial commit")
            if not commit_res.success and ("author identity unknown" in commit_res.error_message.lower() or "tell me who you are" in commit_res.error_message.lower()):
                self._executor.run("config", "user.name", "Gitory User")
                self._executor.run("config", "user.email", "user@gitory.app")
                self._executor.run("commit", "-m", "Initial commit")

        return True, ""
