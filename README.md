wConf - Easy Loading of Configurations from Files
==================================================

TODO: Intro


Design Goals
------------

- Load configuration from files with expected parameters and default values provided in
  an easy way.
- Provide config as a simple Namespace-like object (with option to convert to
  dictionary).
- Do not commit to a specific file format.  All formats that can easily be loaded into a
  dictionary should be supported (json, toml, yaml, ...).
- Optionally check types.
- Optionally check for unknown parameters in the file.
- Keep it simple.  Prefer less features over too complicated API.


Alternatives
------------

As loading configuration from a file in a controlled manner is a rather common task when
implementing applications, I expected that there should already be a well adopted
solution for it.  However, I could not find something that satisfies all my requirements
listed above.

There is, however, [OmegaConf](https://omegaconf.readthedocs.io), which already does
most of it.  It mostly is only missing the flexibility regarding file types.
Hence, wConf is basically just a thin wrapper around OmegaConf, adding the things that I
was missing.
