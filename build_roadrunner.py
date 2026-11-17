#!/usr/bin/env python3
"""Scaffold the `roadrunner` CLI application.

Run this once to generate a ready-to-install Python CLI project:

    python build_roadrunner.py            # creates ./roadrunner
    python build_roadrunner.py --dest ~/code --force

Then:

    cd roadrunner
    pip install -e .
    roadrunner --help
"""

from __future__ import annotations

import argparse
import stat
import sys
import textwrap
from pathlib import Path

APP = "roadrunner"

# Map of relative path -> file contents. Created under <dest>/<APP>/.
FILES: dict[str, str] = {
    "pyproject.toml": textwrap.dedent(
        f"""\
        [build-system]
        requires = ["setuptools>=61.0"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{APP}"
        version = "0.1.0"
        description = "Roadrunner command-line tool"
        readme = "README.md"
        requires-python = ">=3.9"
        dependencies = []

        [project.scripts]
        {APP} = "{APP}.cli:main"

        [tool.setuptools.packages.find]
        where = ["src"]
        """
    ),
    "README.md": textwrap.dedent(
        f"""\
        # {APP}

        A command-line tool.

        ## Install (editable)

        ```bash
        pip install -e .
        ```

        ## Usage

        ```bash
        {APP} --help
        {APP} run --name world
        ```
        """
    ),
    ".gitignore": textwrap.dedent(
        """\
        __pycache__/
        *.py[cod]
        .venv/
        build/
        dist/
        *.egg-info/
        .pytest_cache/
        """
    ),
    f"src/{APP}/__init__.py": '__version__ = "0.1.0"\n',
    f"src/{APP}/cli.py": textwrap.dedent(
        f'''\
        """Command-line entry point for {APP}."""

        from __future__ import annotations

        import argparse
        import sys

        from . import __version__


        def build_parser() -> argparse.ArgumentParser:
            parser = argparse.ArgumentParser(
                prog="{APP}",
                description="Roadrunner command-line tool",
            )
            parser.add_argument(
                "--version",
                action="version",
                version=f"%(prog)s {{__version__}}",
            )

            sub = parser.add_subparsers(dest="command", required=True)

            run = sub.add_parser("run", help="Run the main task")
            run.add_argument("--name", default="world", help="Who to greet")
            run.set_defaults(func=cmd_run)

            return parser


        def cmd_run(args: argparse.Namespace) -> int:
            print(f"Beep beep, {{args.name}}!")
            return 0


        def main(argv: list[str] | None = None) -> int:
            parser = build_parser()
            args = parser.parse_args(argv)
            return args.func(args)


        if __name__ == "__main__":
            sys.exit(main())
        '''
    ),
    "tests/test_cli.py": textwrap.dedent(
        f'''\
        from {APP}.cli import main


        def test_run_default(capsys):
            assert main(["run"]) == 0
            assert "Beep beep, world!" in capsys.readouterr().out


        def test_run_named(capsys):
            assert main(["run", "--name", "coyote"]) == 0
            assert "coyote" in capsys.readouterr().out
        '''
    ),
}


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Scaffold the {APP} CLI app.")
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path.cwd(),
        help="Directory to create the project in (default: current dir)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    args = parser.parse_args(argv)

    root = args.dest / APP
    print(f"Scaffolding {APP} into {root}")

    for rel, content in FILES.items():
        target = root / rel
        write_file(target, content, args.force)
        print(f"  created {target.relative_to(args.dest)}")

    print(
        textwrap.dedent(
            f"""
            Done. Next steps:

                cd {root}
                python -m venv .venv && source .venv/bin/activate
                pip install -e .
                {APP} run --name coyote
            """
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
