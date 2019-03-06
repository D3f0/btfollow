# TODO: Run in background with pid structure
# TODO: Use some sort of event instead of polling
# import re  # TODO: Use in Device.__init__ description parsing
# TODO: Set log level
import sys
from pathlib import Path
import os
import click
from appdirs import user_data_dir
from loguru import logger

from btfollow.config import setup, show_config, load_config, ConfigError
from btfollow.core import run


@click.command()
@click.option(
    "-c",
    "--create-config",
    "create",
    help="Creates config file",
    is_flag=True,
    default=False,
)
@click.option(
    "-f",
    "--force",
    help="Overwrites configuration. Used with -c",
    is_flag=True,
    default=False,
)
@click.option(
    "-s", "--sleep-time", help="Sleep time (overrides configuration)", type=float
)
@click.option("-d", "--daemon", help="Run in background", is_flag=True, default=False)
@click.option("-l", "--show", help="Shows current config", is_flag=True, default=False)
def main(create: bool, force: bool, show: bool, sleep_time: float, daemon: bool):
    config_dir: Path = Path(user_data_dir(appname="btfollow", appauthor="D3f0"))
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    if force and not create:
        click.echo("You can't use force (-f) without create (-c)")
        sys.exit(1)

    if daemon:
        raise NotImplementedError("daemon")
    if create:
        if config_file.exists() and not force:
            click.echo("Config file already exists. Overwrte with -f or list with -l")
            sys.exit(1)
        else:
            setup(config_file)
    elif show:
        show_config(config_file)
    else:
        if not config_file.exists():
            click.echo("Run setup first (-c)")
            sys.exit(1)
        try:
            cfg = load_config(config_file)
        except ConfigError as problem:
            click.echo(problem)
            sys.exit(2)
        run(cfg)


if os.environ.get("BTFOLLOW_VERBOSE_TRACEBACK", "").strip() == "1":
    main = logger.catch(main)


if __name__ == "__main__":
    main()
