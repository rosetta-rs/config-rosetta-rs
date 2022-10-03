#!/usr/bin/env python3

import copy
import datetime
import json
import multiprocessing
import pathlib
import platform
import subprocess
import tempfile


def main():
    repo_root = pathlib.Path(__name__).parent.resolve()
    fixture_root = repo_root / "fixture"at

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    hostname = platform.node()
    uname = platform.uname()
    cpus = multiprocessing.cpu_count()

    runs_root = repo_root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    raw_run_path = runs_root / "{}-{}.json".format(timestamp, hostname)
    if raw_run_path.exists():
        old_raw_run = json.loads(raw_run_path.read_text())
    else:
        old_raw_run = {}

    rustc_p = subprocess.run(["rustc", "-V"], capture_output=True, check=True, encoding="utf8")
    rustc_version = rustc_p.stdout.strip()

    raw_run = {
        "timestamp": timestamp,
        "hostname": hostname,
        "os": uname.system,
        "os_ver": uname.release,
        "arch": uname.machine,
        "cpus": cpus,
        "rustc": rustc_version,
        "libs": {},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        for example_path in sorted((repo_root / "examples").glob("*-app")):
            manifest_path = example_path / "Cargo.toml"
            metadata = harvest_metadata(manifest_path)

            full_build_report_path = pathlib.Path(tmpdir) / f"{example_path.name}-build.json"
            if True:
                hyperfine_cmd = [
                    "hyperfine",
                    "--warmup=1",
                    "--min-runs=5",
                    f"--export-json={full_build_report_path}",
                    "--prepare=cargo clean",
                    # Doing debug builds because that is more likely the
                    # time directly impacting people
                    f"cargo build -j {cpus} --manifest-path {example_path}/Cargo.toml"
                ]
                if False:
                    hyperfine_cmd.append("--show-output")
                subprocess.run(
                    hyperfine_cmd,
                    cwd=repo_root,
                    check=True,
                )
                full_build_report = json.loads(full_build_report_path.read_text())
            else:
                full_build_report = old_raw_run.get("libs", {}).get(str(manifest_path), {}).get("build_inc", None)

            inc_build_report_path = pathlib.Path(tmpdir) / f"{example_path.name}-build.json"
            if True:
                hyperfine_cmd = [
                    "hyperfine",
                    "--warmup=1",
                    "--min-runs=5",
                    f"--export-json={inc_build_report_path}",
                    f"--prepare=touch {example_path}/app.rs",
                    # Doing debug builds because that is more likely the
                    # time directly impacting people
                    f"cargo build -j {cpus} --manifest-path {example_path}/Cargo.toml"
                ]
                if False:
                    hyperfine_cmd.append("--show-output")
                subprocess.run(
                    hyperfine_cmd,
                    cwd=repo_root,
                    check=True,
                )
                inc_build_report = json.loads(inc_build_report_path.read_text())
            else:
                inc_build_report = old_raw_run.get("libs", {}).get(str(manifest_path), {}).get("build_inc", None)

            if True:
                # Doing release builds because that is where size probably matters most
                subprocess.run(["cargo", "build", "--release", "--package", example_path.name], cwd=repo_root, check=True)
                app_path = repo_root / f"target/release/{example_path.name}"
                file_size = app_path.stat().st_size
            else:
                app_path = None
                file_size = old_raw_run.get("libs", {}).get(str(manifest_path), {}).get("size", None)

            runtime_report_path = pathlib.Path(tmpdir) / f"{example_path.name}-runtime.json"
            if True and app_path is not None:
                hyperfine_cmd = [
                    "hyperfine",
                    "--warmup=1",
                    "--min-runs=5",
                    f"--export-json={runtime_report_path}",
                    # Doing debug builds because that is more likely the
                    # time directly impacting people
                    f"{app_path}"
                ]
                if False:
                    hyperfine_cmd.append("--show-output")
                subprocess.run(
                    hyperfine_cmd,
                    cwd=fixture_root,
                    check=True,
                )
                runtime_report = json.loads(runtime_report_path.read_text())
            else:
                runtime_report = old_raw_run.get("libs", {}).get(str(manifest_path), {}).get("runtime", None)

            p = subprocess.run(["cargo", "run", "--package", example_path.name], cwd=fixture_root, capture_output=True, encoding="utf-8")
            works = p.returncode == 0

            raw_run["libs"][str(manifest_path)] = {
                "name": example_path.name.rsplit("-", 1)[0],
                "manifest_path": str(manifest_path),
                "crate": metadata["name"],
                "version": metadata["version"],
                "build_inc": inc_build_report,
                "build_full": full_build_report,
                "runtime": runtime_report,
                "size": file_size,
                "works": works,
            }

    raw_run_path.write_text(json.dumps(raw_run, indent=2))
    print(raw_run_path)


def harvest_metadata(manifest_path):
    p = subprocess.run(["cargo", "tree"], check=True, cwd=manifest_path.parent, capture_output=True, encoding="utf-8")
    lines = p.stdout.strip().splitlines()
    app_line = lines.pop(0)
    if lines:
        self_line = lines.pop(0)
        name, version = _extract_line(self_line)
        unique = sorted(set(_extract_line(line) for line in lines if "(*)" not in line and "[build-dependencies]" not in line))
    else:
        name = None
        version = None

    return {
        "name": name,
        "version": version,
    }


def _extract_line(line):
    if line.endswith(" (proc-macro)"):
        line = line[0:-len(" (proc-macro)")]
    _, name, version = line.rsplit(" ", 2)
    return name, version



if __name__ == "__main__":
    main()
