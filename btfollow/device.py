from btfollow.platform import get_interface
from loguru import logger
import sh
from typing import List, Any


class Device:
    """
    An object oriented abstraction of a bluetooth device
    """

    __slots__ = "_data"

    class DeviceError(Exception):
        pass

    class NotSuchDevice(DeviceError):
        pass

    def __init__(self, description: str) -> None:
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

    def __getitem__(self, name: str) -> "Device":
        if name in self._data:
            return self._data[name]
        raise AttributeError(r"{self} has not attribute {name}")

    def get(self, name, default=None):
        return self._data.get(name, default)

    def __str__(self) -> str:
        return (
            f"{self._data.get('name', 'No name')} "
            f"{self._data.get('address', 'Invalid device')}"
        )

    def is_connected(self) -> bool:
        return str(self.get_interface().is_connected(self["address"]).strip()) == "1"

    __repr__ = __str__

    def __eq__(self, other) -> bool:
        return self["address"] == other["address"]

    def connect(self) -> bool:
        try:
            self.get_interface().connect(self["address"])
        except sh.ErrorReturnCode:
            logger.debug(f"Failed to connect {self}")
            return False
        return True

    def disconnect(self) -> None:
        self.get_interface().disconnect(self["address"])

    @classmethod
    def list(cls) -> List["Device"]:
        """
        List existing devices
        """
        return [Device(desc) for desc in Device.get_interface().paired()]

    @classmethod
    def from_address(cls, address: str) -> "Device":
        for line in Device.get_interface().paired():
            if address in line:
                return Device(line)
        raise cls.NotSuchDevice(address)

    __interface = None

    @classmethod
    def get_interface(cls) -> Any:
        """
        This method pulls at runtime the appropriate module
        that implements the operating system operations.
        For now is a module, although this could be improved as a class.
        """
        if not cls.__interface:
            cls.__interface = get_interface()
        return cls.__interface
