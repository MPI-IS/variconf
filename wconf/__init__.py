import importlib.metadata

from .wconf import WConf

__all__ = ("WConf",)

# get version from package metadata (only works if package is installed, otherwise fall
# back to "unknown".
try:
    __version__ = importlib.metadata.version(__package__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
