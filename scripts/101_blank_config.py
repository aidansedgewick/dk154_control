from argparse import ArgumentParser
from pathlib import Path

from dk154_control.obs_parser import ObservationParser


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument(
        "filename",
        type=Path,
        help="The filename to save the blank config. YAML format.",
    )
    parser.add_argument("-o", "--outdir", default=None, type=Path)
    args = parser.parse_args()

    filename = Path(args.filename)
    if filename.stem not in ("yaml", "yml"):
        filename = filename.with_suffix(".yaml")

    dir = args.outdir
    if dir is None:
        dir = Path.cwd()
    filepath = dir / filename

    ObservationParser.write_blank_observation_config(filepath)
