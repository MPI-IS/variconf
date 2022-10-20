from __future__ import annotations

import typing
import pathlib
import os

import omegaconf as oc


_PathLike = typing.Union[os.PathLike, str]

LoaderFunction = typing.Union[
    typing.Callable[[typing.IO], dict],
    typing.Callable[[typing.TextIO], dict],
    typing.Callable[[typing.BinaryIO], dict],
]


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

    def __init__(self, schema) -> None:
        """
        Args:
            schema: Configuration structure including all parameters with their default
                vaules.  This can be a dictionary, a dataclass (in which case type
                checking is enabled) or any other object that is supported by
                ``OmegaConf.create``.
        """
        # TODO: add allow_unknown argument
        # TODO: support schema from file
        self.cfg = oc.OmegaConf.create(schema)

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

    def get(self) -> oc.OmegaConf:
        """Get the configuration object."""
        # TODO: Add allow_missing argument
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
        # TODO: handle fp type (text vs binary)
        # TODO: more specific error for unsupported format
        loader, _ = self._loaders[format]
        cfg = loader(fp)
        self._merge(cfg)

        return self

    def load_file(self, file: _PathLike) -> WConf:
        """Load configuration from the specified file.

        The format of the file is derived from the filename extension.
        See :meth:`get_supported_formats` for a list of supported file formats.  Custom
        loaders for other formats can be added with :meth:`add_file_loader`.

        Args:
            file: A file in one of the supported formats.

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        file = pathlib.Path(file)
        fmt = self._file_extensions[file.suffix]
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

    def load_dict(self, config: typing.Mapping) -> WConf:
        """Load configuration from a dictionary.

        Args:
            config: Dictionary containing the configuration.

        Returns:
            ``self``, so methods can be chained when loading from multiple sources.
        """
        # TODO: better name as could also accept dataclass objects, etc.
        self._merge(config)
        return self

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

    def load_xdg(self, filename: str) -> WConf:
        """TODO"""
        raise NotImplementedError()
        return self

    def load_from_path(self, filename: str, path: typing.Sequence[_PathLike]) -> WConf:
        """TODO"""
        # TODO: better name?
        raise NotImplementedError()
        return self
