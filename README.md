VariConf - Load Configurations from Various Types of Files
==========================================================

VariConf provides a wrapper around [OmegaConf](https://omegaconf.readthedocs.io) for
loading configuration from various types of files.

Supported file types are JSON, YAML and TOML.  Support for more file types can easily be
added by registering a custom loader function.

Thanks to the power of OmegaConf, you can provide a configuration schema which the
defines expected parameters, default values and optionally expected types.

**Note: This project is currently in alpha phase.  Changes to the API may happen.**


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
- Keep it simple.  Prefer less features over too complicated API.


Why Another Configuration Loader?
---------------------------------

As loading configuration from a file in a controlled manner is a rather common task when
implementing applications, I expected that there should already be a well adopted
solution for it.  However, I could not find something that satisfies all my requirements
listed above.

There is, however, [OmegaConf](https://omegaconf.readthedocs.io), which already does
most of it.  It mostly is only missing the flexibility regarding file types.
Hence, I started to develop VariConf, which is basically just a thin wrapper around
OmegaConf, adding the things that I was missing.


Usage
-----

When creating an instance of `WConf`, a configuration "schema" needs to be given,
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

```python
import variconf

schema = {"sec1": {"foo": 42, "bar": 13}, "sec2": {"bla": ""}}
wconf = variconf.WConf(schema)
config = (
    wconf.load_file("~/global_config.toml")
    .load_file("./local_config.yml")
    .load_dotlist(sys.argv[1:])  # easily allow overwriting parameters via
                                 # command-line arguments
    .get()  # return the final config object
)
```

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
    foo: int
    bar: str

wconf = variconf.WConf(ConfigSchema)
```

### Required Values

OmegaConf supports required values by adding the corresponding parameter to the config
but setting its value to "???" to indicate that it is missinge.  See documentation of
OmegaConf for more on this.


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


Missing Features
----------------

- Option to raise error if config input contains unexpected parameters (using
  `OmegaConf.set_struct`).
- Option to load the config schema from a file.
- Use custom errors, e.g. in case of unsupported file formats.
- Find config file in a list of possible locations.
- Find config file based on [XDG specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).
