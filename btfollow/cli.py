# TODO: Run in background with pid structure
# TODO: Use some sort of event instead of polling
# import re  # TODO: Use in Device.__init__ description parsing
# TODO: Set log level
import os
import sys
import time
from pathlib import Path
from pprint import pformat
from typing import Any, List, MutableMapping

import click
import sh
import toml
from appdirs import user_data_dir
from voluptuous import Optional, Required, Schema
from loguru import logger

# TODO: Make cross os abstraction abstraction
BLUEUTIL_PATH = os.environ.get("BLUEUTIL_PATH", "/usr/local/bin/blueutil")

blueutil = sh.Command(BLUEUTIL_PATH)

paired = blueutil.bake("--paired")
is_connected = blueutil.bake("--is-connected")
connect = blueutil.bake("--connect")
disconnect = blueutil.bake("--disconnect")


class Device:
    __slots__ = "_data"

    class DeviceError(Exception):
        pass

    class NotSuchDevice(DeviceError):
        pass

    def __init__(self, description: str):
        """
        Consumes the output of blueutil --paried and stores the information
        """
        self._data: dict = {}
        for part in description.split(","):
            part = part.strip()
            if ":" in part:
                key, value = map(lambda s: s.strip(), part.split(":", 1))
                self._data[key] = value
            else:
                self._data[part] = part

    def __getitem__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(r"{self} has not attribute {name}")

    def get(self, name, default=None):
        return self._data.get(name, default)

    def __str__(self):
        return f"{self._data.get('name', 'No name')} {self._data.get('address', 'Invalid device')}"

    def is_connected(self):
        return str(is_connected(self["address"]).strip()) == "1"

    __repr__ = __str__

    def __eq__(self, other):
        return self["address"] == other["address"]

    def connect(self) -> bool:
        try:
            connect(self["address"])
            return True
        except sh.ErrorReturnCode as problem:
            logger.debug(f"Failed to connect {self}")
            return False

    def disconnect(self) -> None:
        disconnect(self["address"])

    @classmethod
    def list(cls) -> List["Device"]:
        """
        List existing devices
        """
        return [Device(desc) for desc in paired()]

    @classmethod
    def from_address(cls, address: str) -> "Device":
        for line in paired():
            if address in line:
                return Device(line)
        raise cls.NotSuchDevice(address)


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


@logger.catch
def run(config: MutableMapping[str, Any]) -> None:
    keep_running = True
    primary = Device.from_address(config["primary"])
    follower = Device.from_address(config["follower"])
    sleep_time = config["sleep_time"]
    logger.info(f"Launching {follower} -> {primary} (Check interval: {sleep_time})")

    while keep_running:
        if primary.is_connected():
            if not follower.is_connected():
                logger.info(
                    f"{primary} is connected but not {follower}, connecting follower"
                )
                follower.connect()
        elif follower.is_connected():
            logger.info(f"Releasing {follower}")
            follower.disconnect()

        time.sleep(sleep_time)
        logger.debug(
            f"Primary: {primary.is_connected()} Follower: {follower.is_connected()}"
        )


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
@click.option("-l", "--show", help="Shows current config", is_flag=True, default=False)
def main(create: bool, force: bool, show: bool, sleep_time: float):
    config_dir: Path = Path(user_data_dir(appname="btfollow", appauthor="D3f0"))
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    if force and not create:
        click.echo("You can't use force (-f) without create (-c)")
        sys.exit(1)

    if create:
        if config_file.exists() and not force:
            click.echo("Config file already exists. Overwrte with -f or list with -l")
            sys.exit(1)
        else:
            setup(config_file)
    elif show:
        if not config_file.exists():
            click.echo("Configuration file not created yet. Run with -c")
        else:

            click.echo(f"Configuration found in {config_file}")
            click.echo()
            click.echo(config_file.read_text())
            click.echo("Schema".center(50, "-"))
            click.echo(pformat(ConfigSchema.schema, indent=2))
    else:
        if not config_file.exists():
            click.echo("Run setup first (-c)")
            sys.exit(1)

        with config_file.open("r") as fp:
            cfg = toml.load(fp)
            if sleep_time:
                cfg["sleep_time"] = sleep_time
            else:
                cfg.setdefault("sleep_time", 1.0)
        ConfigSchema(cfg)
        run(cfg)


if __name__ == "__main__":
    main()
