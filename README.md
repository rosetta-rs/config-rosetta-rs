# Rust Config Parsing Benchmarks

This repo tries to assess Rust layered-config behavior.

We currently compare:

Name                                                 | Notes
-----------------------------------------------------|------
No-op                                                | N/A
[cfg-rs](https://github.com/leptonyu/cfg-rs)  |
[config](https://github.com/mehcode/config-rs)  |
[configure_me](https://github.com/kixunil/configure_me)  |
[confy](https://github.com/rust-cli/confy)           |
[figment](https://github.com/SergioBenitez/Figment)  |

*Note: any non-performance comparison is meant to provide context for what you
gain/lose with each crate's overhead.  For a full comparison, see each crates
docs*

General expectations
- Layers
  - Arg parse layer (opt-in per field, support arguments unrelated to config)
  - Env layer (opt-in per field)
  - User config layer
  - Parent directory layer
  - Default layer
- Paths remain relative to the their source
- Schema migrations (correctly layering one field migrating to another, [example](https://github.com/crate-ci/cargo-release/commit/97170451d4a0d7b4b42032cee9507f6c67b898be#diff-cba64c21ab992eaad29fce147a08f4560a4769bc14682b8a96081a5fd02dbecd))
- Isolated made
- Layers can override or append
- Report error for the correct layer
- File format is domain-specific (toml, yaml, gitconfig, etc)
- Show defaults in `--help` and man page
- Document env variables in `--help` and man page
- Support `--dump-config` flag, showing merged config

For a wider discussion on approaches to layered config, see [the clap discussion](https://github.com/clap-rs/clap/discussions/2763)

# Results

Name | Overhead (release) | Build (debug) | Parse (release) | Downloads | Version
-----|--------------------|---------------|-----------------|-----------|--------
null | 0 KiB | 3s *(full)* <br/>211ms *(incremental)* | 0ms | - | v4.0.1

*System: Linux 5.10.102.1-microsoft-standard-WSL2 (x86_64) w/ `-j 20`*

*rustc: rustc 1.64.0 (a55dd71d5 2022-09-19)*

Notes:
- Overhead will be lower if your application shares dependencies with your config library.

# Running the Benchmarks

```bash
$ ./bench.py
$ ./format.py
```

To be included, the crate needs meet one of the following criteria:
- 1k+ recent downloads
- Unique API design

# Special Thanks

- djc for inspiration with [template-benchmarks-rs](https://github.com/djc/template-benchmarks-rs)
- sharkdp for [hyperfine](https://github.com/sharkdp/hyperfine)
