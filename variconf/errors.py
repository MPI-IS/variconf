# Copyright (c) 2022 Max Planck Gesellschaft
# SPDX-License-Identifier: BSD-3-Clause
"""Exceptions specific to the variconf package."""


class UnknownFormatError(Exception):
    """Error indicating that the given file format is unknown."""

    pass


class UnknownExtensionError(Exception):
    """Error indicating that the given file extension is unknown."""

    pass
