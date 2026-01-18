import argparse
from ersilia_apptainer.runner import ErsiliaApptainer, logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ersilia-apptainer",
        description="Run Ersilia models on HPC systems using Apptainer.",
    )

    parser.add_argument(
        "--sif",
        required=True,
        type=str,
        help="Path to the Apptainer (.sif) image.",
    )

    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="Path to the input file (e.g. SMILES list).",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Path to the output file.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    logger.set_verbosity(args.verbose)

    try:
       runner = ErsiliaApptainer(
          container=args.sif,
          input = args.input,
          output = args.output
       )
       runner.run()
       return 0
    except Exception as e:
       logger.error(str(e))
       return 1

if __name__ == "__main__":
  raise SystemExit(main())