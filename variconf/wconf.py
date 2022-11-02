from __future__ import annotations

import typing
import pathlib
import platform
import os

import omegaconf as oc

from . import errors


_PathLike = typing.Union[os.PathLike, str]

LoaderFunction = typing.Union[
    typing.Callable[[typing.IO], dict],
    typing.Callable[[typing.TextIO], dict],
    typing.Callable[[typing.BinaryIO], dict],
]


def find_file(
    filename: pathlib.Path, search_paths: typing.Sequence[_PathLike]
) -> pathlib.Path:
    """Search for a file in a list of directories.

    Args:
        filename: Name of the file (can also be a relative path).
        search_paths:  List of directories in which the file is searched.

    Returns:
        The path to the first matching file that is found.

    Raises:
        FileNotFoundError: If the file is not found in any of the directories in
            search_paths.
    """
    for directory in map(pathlib.Path, search_paths):
        _file = directory / filename
        if _file.is_file():
            return _file

    raise FileNotFoundError(f"No file {filename} found in {search_paths}")


class WConf:
    """Load configuration from files.

    A thin wrapper around OmegaConf to easily load configurations from various types of
    files.

    When creating an instance of ``WConf``, a configuration "schema" needs to be given,
    i.e. a structure (e.g. dictionary) that defines what sections and parameters the
    configuration has and that provides default values.

    A number of "load"-methods is provided to load configurations from different sources
    (e.g. JSON files, YAML files, dictionaries from other sources, ...).  When called,
    the corresponding parameters are merged into the existing configuration, overwriting
    existing values.  This means that an input does not need to provide all parameters,
    in this case the default values are kept.  Further, if calling multiple
    "load"-methods after another, the later calls will overwrite values set by previous
    ones.

    All "load"-methods return ``self``, so they can be chained:

    .. code-block:: python

        schema = {"sec1": {"foo": 42, "bar": 13}, "sec2": {"bla": ""}}
        wconf = WConf(schema)
        config = (
            wconf.load_file("~/global_config.toml")
            .load_file("./local_config.yml")
            .load_dotlist(sys.argv[1:])
            .get()  # return the final config object
        )

    """

    def __init__(self, schema, strict: bool = True) -> None:
        """
        Args:
            schema: Configuration structure including all parameters with their default
                vaules.  This can be a dictionary, a dataclass (in which case type
                checking is enabled) or any other object that is supported by
                ``OmegaConf.create``.
            strict: If true, loading a configuration with parameters that are not listed
                in schema results in an error.  If false, they will be merged into the
                configuration.
        """
        self.cfg = oc.OmegaConf.create(schema)

        if strict:
            oc.OmegaConf.set_struct(self.cfg, True)

        self._loaders: typing.Dict[str, typing.Tuple[LoaderFunction, bool]] = {
            "json": (self._load_json, False),
            "toml": (self._load_toml, True),
            "yaml": (self._load_yaml, False),
        }
        # map extension (including dot) to format type
        self._file_extensions = {
            ".json": "json",
            ".toml": "toml",
            ".yml": "yaml",
            ".yaml": "yaml",
        }

    def _merge(self, cfg) -> None:
        self.cfg = oc.OmegaConf.merge(self.cfg, cfg)

    def _load_json(self, fp: typing.IO) -> dict:
        import json

        return json.load(fp)

    def _load_yaml(self, fp: typing.IO) -> dict:
        import yaml

        return yaml.safe_load(fp)

    def _load_toml(self, fp: typing.BinaryIO) -> dict:
        import tomli

        return tomli.load(fp)

    def get_supported_formats(self) -> typing.List[str]:
        """Get list of supported file formats."""
        return list(self._loaders.keys())

    def get(self, allow_missing=False) -> oc.OmegaConf:
        """Get the configuration object.

        Args:
            allow_missing: If enabled, the config can still contain required parameters
                which have not been set (accessing them will result in an error).  If
                disabled (default), get() will check the configuration for missing
                required values and raise an error instead of returning the config.

        Raises:
            omegaconfig.errors.MissingMandatoryValue: If ``allow_missing=False`` and the
                config has one or more required values (marked as missing in the
                schema), which have not been filled yet.
        """
        if not allow_missing:
            # the easiest way to check the whole config is to convert to a container
            # with throw_on_missing=True (even though, we're not interested in the
            # resulting container...).
            oc.OmegaConf.to_container(self.cfg, throw_on_missing=True)

        return self.cfg

    def load(self, fp, format: str) -> WConf:
        """Load configuration from the given stream.

        See :meth:`get_supported_formats` for a list of supported file formats.  Custom
        loaders for other formats can be added with :meth:`add_file_loader`.

        Args:
            fp: Input stream containing a document in the specified format.
            format: Name of the format (e.g. "yaml").

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        try:
            loader, _ = self._loaders[format]
        except KeyError:
            raise errors.UnknownFormatError(format)

        cfg = loader(fp)
        self._merge(cfg)

        return self

    def load_file(
        self,
        file: _PathLike,
        fail_if_not_found: bool = True,
        search_paths: typing.Optional[typing.Sequence[_PathLike]] = None,
    ) -> WConf:
        """Load configuration from the specified file.

        The format of the file is derived from the filename extension.
        See :meth:`get_supported_formats` for a list of supported file formats.  Custom
        loaders for other formats can be added with :meth:`add_file_loader`.

        Args:
            file:  A file in one of the supported formats.
            fail_if_not_found:  If true, raise an error if the file is not found.
                Otherwise simply return without loading anything (i.e. keep the current
                values).
            search_paths:  List of directories.  If set, search these directories for a
                file with the name specified in ``file`` and loads the first file that
                is found.

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        file = pathlib.Path(file)

        # If search_path is set, search for the file in these paths.  Otherwise directly
        # use `file`.
        try:
            if search_paths:
                file = find_file(file, search_paths)
            else:
                if not file.is_file():
                    raise FileNotFoundError(file)
        except Exception as e:
            if fail_if_not_found:
                raise e
            else:
                return self

        try:
            fmt = self._file_extensions[file.suffix]
        except KeyError:
            raise errors.UnknownExtensionError(file.suffix)

        _, binary = self._loaders[fmt]
        if binary:
            mode = "rb"
        else:
            mode = "rt"

        with open(file, mode) as f:
            self.load(f, fmt)

        return self

    def add_file_loader(
        self,
        name: str,
        file_extensions: typing.Sequence[str],
        loader: LoaderFunction,
        binary: bool = False,
    ) -> None:
        """Add a custom file loader.

        Add a custom loader to add support for other file formats.  It is also possible
        to overwrite the default loaders for existing formats.

        Args:
            name:  Name of the format.
            file_extensions:  List of file extensions by which files of this format can
                be detected.  The extensions must include the leading dot!
            loader:  Function that takes an file-like object as input and returns a
                dictionary.
            binary:  Set to True if the loader function expects a binary stream.
        """
        self._loaders[name] = (loader, binary)
        self._file_extensions.update({ext: name for ext in file_extensions})

    def load_object(self, config) -> WConf:
        """Load configuration from a dictionary, dataclass or OmegaConf instance.

        Args:
            config: Object containing the configuration.  See OmegaConf.merge for
                supported types.

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        self._merge(config)
        return self

    def load_dict(self, config: typing.Mapping) -> WConf:
        """Alias for :meth:`load_object`."""
        return self.load_object(config)

    def load_dotlist(self, dotlist: typing.List[str]) -> WConf:
        """Load configuration from a "dotlist"

        A dotlist looks like this: ``["foo.bar=42", "baz=13", ...]``
        This can, for example, be used to allow overwriting parameters from the file via
        a command-line argument.

        Args:
            dotlist: List of parameters in dot-notation.

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        cfg = oc.OmegaConf.from_dotlist(dotlist)
        self._merge(cfg)
        return self

    @staticmethod
    def _get_xdg_config_paths() -> typing.List[pathlib.Path]:
        if platform.system() == "Windows":
            raise NotImplementedError("XDG support is not implemented for Windows.")

        # get config_home
        config_home_default = pathlib.Path(os.environ["HOME"], ".config")

        config_home = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", ""))
        if not config_home.is_absolute():
            config_home = config_home_default

        # get config dirs
        config_dirs_str = os.environ.get("XDG_CONFIG_DIRS", "")
        _config_dirs = config_dirs_str.split(":")
        config_dirs = list(
            filter(lambda p: p.is_absolute(), map(pathlib.Path, _config_dirs))
        )
        if not config_dirs:
            config_dirs = [pathlib.Path("/etc/xdg")]

        return [config_home] + config_dirs

    def load_xdg_config(self, filename: _PathLike, fail_if_not_found=False) -> WConf:
        """Load file from XDG config directory.

        Searches for the specified file in the directories given in the
        ``XDG_CONFIG_HOME`` and ``XDG_CONFIG_DIRS`` environment variables.  If they are
        not set, they default to ``${HOME}/.config`` and ``/etc/xdg``.

        For more information on the XDG base directory specification see
        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html

        Args:
            filename: Name of the file, relative to the config directory.
            fail_if_not_found:  If true, raise an error if the file is not found.
                Otherwise simply return without loading anything (i.e. keep the current
                values).
        """
        paths = self._get_xdg_config_paths()
        return self.load_file(
            filename, fail_if_not_found=fail_if_not_found, search_paths=paths
        )
