# Copyright (c) 2022 Max Planck Gesellschaft
# SPDX-License-Identifier: BSD-3-Clause
from .wconf import WConf
from .errors import UnknownFormatError, UnknownExtensionError

__all__ = ("WConf", "UnknownFormatError", "UnknownExtensionError")

__version__ = "1.0.1"
