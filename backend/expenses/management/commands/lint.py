import subprocess

from django.core.management.base import BaseCommand

LINTER_TYPES = ["all", "black", "isort", "pylint", "mypy"]


class Command(BaseCommand):
    help = "Runs linters"

    def add_arguments(self, parser):
        parser.add_argument(
            "linter_type",
            default="all",
            const="all",
            nargs="?",
            choices=LINTER_TYPES,
            help="Choose a linter type (default: %(default)s)",
        )

    def handle(self, *args, **kwarks):
        filenames = subprocess.run(["git", "ls-files", "*.py"], capture_output=True).stdout.decode().splitlines()

        linter_type = kwarks["linter_type"]
        if linter_type in ["black", "all"]:
            subprocess.run(["black", *filenames], check=True)
        if linter_type in ["isort", "all"]:
            subprocess.run(["isort", *filenames], check=True)
        if linter_type in ["pylint", "all"]:
            subprocess.run(["pylint", *filenames], check=True)
        if linter_type in ["mypy", "all"]:
            subprocess.run(["mypy", *filenames], check=True)

        self.stdout.write(self.style.SUCCESS(f"Successfully ran 'lint {linter_type}'."))
