from pathlib import Path
from pprint import pformat
from typing import MutableMapping, Any
import click
import toml
from voluptuous import Optional, Required, Schema, Invalid

from btfollow.device import Device


class ConfigError(Exception):
    """Base exception for this module"""

    pass


class ConfigFileDoesNotExist(ConfigError):
    """
    The configuration file is missing
    """

    pass


class ConfigFileProblem(ConfigError):
    """
    The contents of the config file have problems
    """


ConfigSchema = Schema(
    {
        Required("primary"): str,
        Required("follower"): str,
        Optional("sleep_time"): float,
        Optional("log_level"): str,
    }
)


def select_device(prompt="Select one device") -> Device:
    devices = Device.list()
    count = len(devices)
    while True:
        print(f"{prompt} [1-{count}]")
        for i, device in enumerate(devices, 1):
            print(f"{i}) {device}")
        selection = input(":")
        try:
            index = int(selection)
            assert 0 < index < count
        except (ValueError, AssertionError):
            click.echo("Invalid selection")
            continue
        retval = devices[index - 1]
        click.echo(f"You selected {retval}")
        return retval


def setup(path: Path):
    """
    Runs interactive setup
    """
    click.echo(f"Creating configuration file in {path}")
    configuration_complete = False
    while not configuration_complete:
        primary = select_device('Select master device (e.g. "Keyboard foo"')
        click.echo("\n")
        click.echo(f"Selected {primary} as primary device".center(50, " "))
        click.echo("\n")
        follower = select_device(f"Select device to connect when {primary} is present")
        if follower == primary:
            click.echo("\n")
            click.echo("You've selected the same device!".center(50, "*"))
            click.echo("\n")
            continue
        with path.open("w") as fp:
            cfg = {"primary": primary["address"], "follower": follower["address"]}
            ConfigSchema(cfg)
            toml.dump(cfg, fp)
        configuration_complete = True


def show_config(config_file: Path):
    if not config_file.exists():
        click.echo("Configuration file not created yet. Run with -c")
    else:
        click.echo(f"Configuration found in {config_file}")
        click.echo()
        click.echo(config_file.read_text())
        click.echo("Schema".center(50, "-"))
        click.echo(pformat(ConfigSchema.schema, indent=2))


def load_config(config_file: Path) -> MutableMapping[str, Any]:
    try:
        with config_file.open("r") as fp:
            cfg = toml.load(fp)
    except IOError as problem:
        raise ConfigFileDoesNotExist(str(problem))

    cfg.setdefault("sleep_time", 1.0)
    try:
        ConfigSchema(cfg)
    except Invalid as exception:
        raise ConfigFileProblem(str(exception))
    return cfg
