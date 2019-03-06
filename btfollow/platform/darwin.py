"""
This module wraps calls to operating system commands
"""
import os
import sh

BLUEUTIL_PATH = os.environ.get("BLUEUTIL_PATH", "/usr/local/bin/blueutil")

blueutil = sh.Command(BLUEUTIL_PATH)

paired = blueutil.bake("--paired")
is_connected = blueutil.bake("--is-connected")
connect = blueutil.bake("--connect")
disconnect = blueutil.bake("--disconnect")
