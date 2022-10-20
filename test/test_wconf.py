import pathlib
import shutil

import pytest
import omegaconf.errors

from variconf import WConf, errors


_schema = {
    "foobar": {
        "foo": 1,
        "bar": 1,
        "nested": {
            "one": 0,
            "two": 0,
            "three": 0,
        },
    },
    "type": "???",
}


_foobar = {
    "foo": 42,
    "bar": 13,
    "nested": {
        "one": 1,
        "two": 2,
        "three": 3,
    },
}


@pytest.fixture
def test_data() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "data"


@pytest.fixture
def wconf() -> WConf:
    return WConf(_schema)


def test_defaults(wconf):
    assert wconf.cfg == _schema


def test_get(wconf):
    assert wconf.cfg == wconf.get(allow_missing=True)


def test_load_json(wconf, test_data):
    with open(test_data / "conf1.json") as f:
        wconf.load(f, "json")

    assert wconf.get() == {"foobar": _foobar, "type": "json"}


def test_load_yaml(wconf, test_data):
    with open(test_data / "conf1.yml") as f:
        wconf.load(f, "yaml")

    assert wconf.get() == {"foobar": _foobar, "type": "yaml"}


def test_load_toml(wconf, test_data):
    with open(test_data / "conf1.toml", "rb") as f:
        wconf.load(f, "toml")

    assert wconf.get() == {"foobar": _foobar, "type": "toml"}


def test_load_unknown(wconf, test_data):
    with pytest.raises(errors.UnknownFormatError) as e:
        with open(test_data / "conf1.toml") as f:
            wconf.load(f, "bad")

    assert str(e.value) == "bad"


def test_load_file_json(wconf, test_data):
    wconf.load_file(test_data / "conf1.json")
    assert wconf.get() == {"foobar": _foobar, "type": "json"}


def test_load_file_yaml(wconf, test_data):
    wconf.load_file(test_data / "conf1.yml")
    assert wconf.get() == {"foobar": _foobar, "type": "yaml"}


def test_load_file_toml(wconf, test_data):
    wconf.load_file(test_data / "conf1.toml")
    assert wconf.get() == {"foobar": _foobar, "type": "toml"}


def test_load_file_unknown(wconf, test_data):
    with pytest.raises(errors.UnknownExtensionError) as e:
        wconf.load_file(test_data / "conf.ini")

    assert str(e.value) == ".ini"


def test_load_file_fail_if_not_found(wconf, test_data):
    with pytest.raises(FileNotFoundError):
        wconf.load_file(test_data / "does_not_exist.yml")


def test_load_file_with_fail_if_not_found_false(wconf, test_data):
    wconf.load_file(test_data / "does_not_exist.yml", fail_if_not_found=False)
    assert wconf.get(allow_missing=True) == _schema


def test_load_file_with_search_path(
    wconf: WConf, test_data: pathlib.Path, tmp_path: pathlib.Path
):
    paths = [
        tmp_path / "foo",
        tmp_path / "bar",
        tmp_path / "baz",
    ]

    # create directory structure and add config files
    for p in paths:
        p.mkdir()
    shutil.copyfile(test_data / "conf1.json", tmp_path / "bar" / "conf.json")
    shutil.copyfile(test_data / "conf2.json", tmp_path / "baz" / "conf.json")

    # test loading it
    wconf.load_file("conf.json", search_paths=paths)
    # verify that conf1.json (from "bar/") was found
    assert wconf.get() == {"foobar": _foobar, "type": "json"}


def test_load_file_with_search_path_not_found(wconf: WConf, tmp_path: pathlib.Path):
    paths = [
        tmp_path / "foo",
        tmp_path / "bar",
        tmp_path / "baz",
    ]

    # create directory structure but don't add an actual config file
    for p in paths:
        p.mkdir()

    # loading will not be able to find the file, so the default config should remain
    wconf.load_file("conf.json", search_paths=paths, fail_if_not_found=False)
    assert wconf.get(allow_missing=True) == _schema

    # when running with fail_if_not_found=True, it should raise an error
    with pytest.raises(FileNotFoundError):
        wconf.load_file("conf.json", search_paths=paths, fail_if_not_found=True)


def test_load_dict(wconf):
    wconf.load_dict(
        {
            "foobar": {"foo": 123, "nested": {"three": 4}},
            "type": "dict",
        }
    )
    assert wconf.get() == {
        "foobar": {"foo": 123, "bar": 1, "nested": {"one": 0, "two": 0, "three": 4}},
        "type": "dict",
    }


def test_load_dotlist(wconf):
    wconf.load_dotlist(["foobar.foo=123", "foobar.nested.three=4", "type=dotlist"])
    assert wconf.get() == {
        "foobar": {"foo": 123, "bar": 1, "nested": {"one": 0, "two": 0, "three": 4}},
        "type": "dotlist",
    }


def test_add_file_loader(test_data):
    # write a load that wraps Python's ConfigParser
    def configparser_loader(fp):
        from configparser import ConfigParser

        cfg = ConfigParser()
        cfg.read_file(fp)
        cfg_dict = {s: dict(cfg.items(s)) for s in cfg.sections()}
        return cfg_dict

    # test with load()
    wconf = WConf({}, strict=False)
    wconf.add_file_loader("ini", [".ini"], configparser_loader)
    with open(test_data / "conf.ini") as f:
        wconf.load(f, "ini")
    assert wconf.get() == {"section1": {"foo": "42", "bar": "yes"}}

    # test with load_file()
    wconf = WConf({}, strict=False)
    wconf.add_file_loader("ini", [".ini"], configparser_loader)
    wconf.load_file(test_data / "conf.ini")
    assert wconf.get() == {"section1": {"foo": "42", "bar": "yes"}}


def test_load_xdg():
    NotImplemented


def test_load_chaining(wconf, test_data):
    cfg = (
        wconf.load_file(test_data / "conf1.yml")
        .load_dict({"type": "mixed"})
        .load_dotlist(["foobar.bar=23"])
        .get()
    )

    assert cfg == {
        "foobar": {"foo": 42, "bar": 23, "nested": {"one": 1, "two": 2, "three": 3}},
        "type": "mixed",
    }

    # make sure the original object contains all the changes
    assert wconf.get() == cfg


def test_strict_true(test_data):
    # with strict=True, loading a config that contains additional arguments should
    # result in an error.
    wconf = WConf(_schema, strict=True)
    with pytest.raises(omegaconf.errors.ConfigKeyError):
        wconf.load_file(test_data / "conf_additional_1.toml")

    wconf = WConf(_schema, strict=True)
    with pytest.raises(omegaconf.errors.ConfigKeyError):
        wconf.load_file(test_data / "conf_additional_2.toml")


def test_strict_true_default(test_data):
    # make sure strict is enabled by default
    wconf = WConf(_schema)
    with pytest.raises(omegaconf.errors.ConfigKeyError):
        wconf.load_file(test_data / "conf_additional_1.toml")


def test_strict_false(wconf, test_data):
    # with strict=False, loading a config file with additional arguments is allowed, the
    # additional parameters are merged into the config.
    wconf = WConf(_schema, strict=False)
    wconf.load_file(test_data / "conf_additional_1.toml")
    assert wconf.get().foobar.additional == "this is not in the schema"

    wconf = WConf(_schema, strict=False)
    wconf.load_file(test_data / "conf_additional_2.toml")
    assert wconf.get().additional == {"bla": 1, "blub": 2}


def test_required_parameter(wconf):
    # "type" is required in the schema ("???") but no config has been provided to set
    # the value.  Accessing it should result in an error.
    cfg = wconf.get(allow_missing=True)
    with pytest.raises(omegaconf.errors.MissingMandatoryValue):
        cfg.type

    # With allow_missing=False, we should already get an error when calling get()
    with pytest.raises(omegaconf.errors.MissingMandatoryValue):
        wconf.get(allow_missing=False)
