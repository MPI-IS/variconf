from __future__ import annotations

import typing
import pathlib
import os

import omegaconf as oc


_PathLike = typing.Union[os.PathLike, str]


class WConf:
    def __init__(self, schema) -> None:
        # TODO: add allow_unknown argument

        self.cfg = oc.OmegaConf.create(schema)

        self._loaders = {
            "json": self._load_json,
            "toml": self._load_toml,
            "yaml": self._load_yaml,
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

    def load(self, fp: typing.IO, format: str) -> WConf:
        loader = self._loaders[format]
        cfg = loader(fp)
        self._merge(cfg)

        return self

    def load_file(self, file: _PathLike) -> WConf:
        file = pathlib.Path(file)
        fmt = self._file_extensions[file.suffix]
        with open(file) as f:
            self.load(f, fmt)

        return self

    def add_file_loader(
        self, name: str, file_extensions: typing.Sequence[str], loader
    ) -> None:
        self._loaders[name] = loader
        self._file_extensions.update({ext: name for ext in file_extensions})

    def load_dict(self, config: typing.Mapping) -> WConf:
        # TODO: better name as could also accept dataclass objects, etc.
        self._merge(config)
        return self

    def load_dotlist(self, dotlist: typing.Sequence[str]) -> WConf:
        cfg  = oc.OmegaConf.from_dotlist(dotlist)
        self._merge(cfg)
        return self

    def load_xdg(self, filename: str) -> WConf:
        raise NotImplementedError()
        return self

    def load_from_path(self, filename: str, path: typing.Sequence[_PathLike]) -> WConf:
        # TODO: better name?
        raise NotImplementedError()
        return self

    def get(self) -> oc.OmegaConf:
        return self.cfg
