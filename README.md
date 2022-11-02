VariConf - Load Configurations from Various Types of Files
==========================================================

VariConf provides a wrapper around [OmegaConf](https://omegaconf.readthedocs.io) for
loading configuration from various types of files.

Supported file types are JSON, YAML and TOML.  Support for more file types can easily be
added by registering a custom loader function.

Thanks to the power of OmegaConf, you can provide a configuration schema which the
defines expected parameters, default values and optionally expected types.


Design Goals
------------

This package is developed with the following goals in mind:

- Load configuration from files with expected parameters and default values provided in
  an easy way.
- Provide config as a simple Namespace-like object (with option to convert to
  dictionary).
- Do not commit to a specific file format.  All formats that can easily be loaded into a
  dictionary should be supported (json, toml, yaml, ...).
- Optionally check types.
- Optionally check for unknown parameters in the file (to raise an error).
- Keep it simple.  Prefer fewer features over too complicated API.


Installation
------------

Basic (does not include dependencies for YAML and TOML):
```
pip install variconf
```

With optional dependencies:
```bash
# with TOML support
pip install "variconf[toml]"

# with YAML support
pip install "variconf[yaml]"

# to include everything:
pip install "variconf[all]"
```


Usage
-----

The package provides a class `WConf` for loading and merging configurations from
different sources. When creating an instance of it, a configuration "schema" needs to be
given, i.e. a structure (dictionary or dataclass) that defines what sections and
parameters the configuration has and that provides default values.

A number of "load"-methods is provided to load configurations from different sources
(e.g. JSON files, YAML files, dictionaries from other sources, ...).  When called,
the corresponding parameters are merged into the existing configuration, overwriting
existing values.  This means that an input does not need to provide all parameters,
in this case the default values are kept.  Further, if calling multiple
"load"-methods after another, the later calls will overwrite values set by previous
ones.

All "load"-methods return ``self``, so they can be chained:

```python
import variconf

schema = {"sec1": {"foo": 42, "bar": 13}, "sec2": {"bla": ""}}
wconf = variconf.WConf(schema)
config = (
    wconf.load_file("~/global_config.toml")
    .load_file("./local_config.yml", fail_if_not_found=False)
    .load_dotlist(sys.argv[1:])  # easily allow overwriting parameters via
                                 # command-line arguments
    .get()  # return the final config object
)
```


### Allow Unknown Parameters

By default an error is raised if the loaded configuration contains parameters that are
not declared in the schema.  If you want to allow these unknown parameters, initialise
`WConf` with `strict=False`:

```python
wconf = variconf.WConf(schema, strict=False)
```

This will result in the unknown parameters being merged into the config object.

With this you can even omit the schema altogether by simply passing an empty dictionary:
```python
wconf = variconf.WConf({}, strict=False)
```


### Search File

Assuming an application where the config file can be located in one of several places
(e.g. `~`, `~/.config` or `/etc/myapp`).  This situation is supported by the optional
`search_paths` argument of `load_file()`:

```python
wconf.load_file(
    "config.yml",
    search_paths=[os.expanduser("~"), os.expanduser("~/.config"), "/etc/myapp"],
    fail_if_not_found=False,
)
```
This will search for a file "config.yml" in the listed directories (in the given order)
and use the first match.
By setting `fail_if_not_found=False`, we specify that it's okay if the file is not found
in any of these directories.  In this case, we simply keep the default values of all
parameters.


### Using XDG Base Directory Specification

If your application follows the [XDG Base Directory
Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
you can use ``load_xdg_config()`` (currently not supported on Windows!):

```python
wconf.load_xdg_config("myapp/config.toml")
```
Will search for the file in the directories specified in the environment variables
`XDG_CONFIG_HOME` and `XDG_CONFIG_DIRS` (defaulting to `~/.config`).

Like for `load_file()` there is an argument `fail_if_not_found` but here it defaults to
False as providing a config in `XDG_CONFIG_HOME` is typically optional.


### Supported File Types

Supported file types are JSON, YAML and TOML.  Support for custom file types can be
added by providing a loader function.  Example for adding XML support:

```python
import xml.etree.ElementTree as ET

def xml_loader(fp: typing.IO) -> dict:
    xml_str = fp.read()
    xml_tree = ET.fromstring(xml_str)
    # do some magic to convert XML tree to dictionary
    xml_dict = tree_to_dict(xml_tree)
    return xml_dict

wconf.add_file_loader("xml", [".xml"], xml_loader)

# now, XML files can be read by WConf.load and WConf.load_file
wconf.load_file("config.xml")
```


### Type Checking

OmegaConf supports type-checking by providing a schema as dataclass with type hints:

```python
@dataclasses.dataclass
class ConfigSchema:
    foo: int = 42
    bar: str = 13

wconf = variconf.WConf(ConfigSchema)

# raises ValidationError: Value 'hi' of type 'str' could not be converted to Integer
wconf.load_dict({"foo": "hi"})
```

### Required Values

Required parameters without default value are supported through OmegaConf's concept of
missing values.

When using a dictionary schema:

```python
schema = {
    "optional_param": "default value",
    "required_param": "???",
}
```

When using a dataclass schema:

```python
@dataclasses.dataclass
class Schema:
    required_param1: float  # not providing a default makes it required
    optional_param: str = "default value"
    required_param2: int = omegaconf.MISSING  # alternative for required parameters
```

If there is a required parameter for which no value has been provided by any of the
`load*`-methods, calling `get()` will raise an error.

You can avoid that error by using `get(allow_missing=True)`.  However, the error is
still raised when trying to access the actual value of the missing parameter.


### Variable Interpolation

OmegaConf has a feature called [variable interpolation](https://omegaconf.readthedocs.io/en/latest/usage.html#variable-interpolation)
that allows to refer to other fields within the config file:

```yaml
server:
  host: localhost
  port: 80

client:
  url: http://${server.host}:${server.port}/
  server_port: ${server.port}
  # relative interpolation
  description: Client of ${.url}
```
See the documentation of OmegaConf for more information.
