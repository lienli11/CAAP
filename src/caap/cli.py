"""Small, lazy command router for workspace tools and guarded legacy entries."""

import argparse
import importlib
import sys

from . import __version__

COMMANDS = {
    "doctor": ("caap.runtime.doctor", "inspect this machine; never allocate GPUs"),
    "plan-check": ("caap.runtime.plancheck", "validate the task graph; never run experiments"),
    "legacy-attack": ("caap.attack.main", "guarded legacy training, not a v2 experiment"),
    "legacy-pretrain": ("caap.tools.pretrain_ms_dife", "guarded legacy feature pretraining"),
    "legacy-physical-report": ("caap.tools.physical_report", "historical statistics, not final evidence"),
    "make-synthetic": ("caap.tools.make_synth_data", "create explicitly synthetic test fixtures"),
}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="caap",
        description="CAAP workspace tools. Formal experiment workers remain planned, not implemented.",
        epilog="\n".join(
            ["Commands:"]
            + ["  {:24s} {}".format(name, details[1]) for name, details in COMMANDS.items()]
            + ["", "Run 'caap COMMAND --help' for command-specific arguments."]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("command", nargs="?", choices=sorted(COMMANDS))
    if not args:
        parser.print_help()
        return 0
    if args[0] not in COMMANDS:
        parser.parse_args(args)
        return 0
    module_name, description = COMMANDS[args[0]]
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        dependency = (exc.name or "").split(".", 1)[0]
        if args[0] in {"doctor", "plan-check"} or dependency not in {"torch", "torchvision", "numpy", "PIL", "tqdm"}:
            raise
        help_only = args[1:] in (["--help"], ["-h"])
        message = (
            "{}: {}. Missing optional research dependency: {}. "
            "Install compatible research extras in your approved environment "
            "(python -m pip install '.[research]' from the repository), then rerun --help for detailed options. "
            "Legacy commands require --allow-legacy-protocol and are not v2 evidence. No work was executed."
        ).format(args[0], description, dependency)
        print(message, file=sys.stdout if help_only else sys.stderr)
        return 0 if help_only else 2
    result = module.main(args[1:])
    return 0 if result is None else result
