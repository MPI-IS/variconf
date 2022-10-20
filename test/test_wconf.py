import pathlib

import pytest

from variconf import WConf


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
    assert wconf.cfg == wconf.get()


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


def test_load_file_json(wconf, test_data):
    wconf.load_file(test_data / "conf1.json")
    assert wconf.get() == {"foobar": _foobar, "type": "json"}


def test_load_file_yaml(wconf, test_data):
    wconf.load_file(test_data / "conf1.yml")
    assert wconf.get() == {"foobar": _foobar, "type": "yaml"}


def test_load_file_toml(wconf, test_data):
    wconf.load_file(test_data / "conf1.toml")
    assert wconf.get() == {"foobar": _foobar, "type": "toml"}


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


def test_add_loader():
    NotImplemented


def test_load_xdg():
    NotImplemented


def test_load_from_path():
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
