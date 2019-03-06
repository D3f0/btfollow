from loguru import logger
import time
from typing import MutableMapping, Any
from btfollow.device import Device


def run(config: MutableMapping[str, Any]) -> None:
    keep_running = True
    primary = Device.from_address(config["primary"])
    follower = Device.from_address(config["follower"])
    sleep_time = config["sleep_time"]
    logger.info(f"Launching {follower} -> {primary} " "(Check interval: {sleep_time})")

    while keep_running:
        if primary.is_connected():
            if not follower.is_connected():
                logger.info(
                    f"{primary} is connected but not "
                    f"{follower}, connecting follower"
                )
                follower.connect()
        elif follower.is_connected():
            logger.info(f"Releasing {follower}")
            follower.disconnect()

        time.sleep(sleep_time)
        logger.debug(
            f"Primary: {primary.is_connected()} " f"Follower: {follower.is_connected()}"
        )
