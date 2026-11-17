#!/usr/bin/env python3
"""Create and validate the installer-free release using only the Python standard library."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[1]
BUNDLE_NAME = "ACadHotKey.bundle"
FILES = {"ACadHotKey.dll", "ACadHotKey.Core.dll", "ACadHotKey.config.xml"}
TARGETS = {"2020": ("R23.1", "R23.1"), "2021-2024": ("R24.0", "R24.3")}
BUNDLE_FILES = {"PackageContents.xml"} | {
    f"Contents/{target}/{name}" for target in TARGETS for name in FILES
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def release_version(tag=None):
    project = ET.parse(REPO / "src/ACadHotKey.Plugin/ACadHotKey.Plugin.csproj").getroot()
    version = project.findtext("PropertyGroup/Version", "")
    require(re.fullmatch(r"\d+\.\d+\.\d+", version), "Expected a numeric major.minor.patch project Version")
    manifest = ET.parse(REPO / "bundle" / BUNDLE_NAME / "PackageContents.xml").getroot()
    require(manifest.get("AppVersion") == version, "Project Version and bundle AppVersion must match")
    require(not tag or tag == f"v{version}", f"Tag {tag!r} does not match project version v{version}")
    return version


def verify_bundle(bundle, version=None):
    bundle = Path(bundle)
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file()}
    require(actual == BUNDLE_FILES, f"Unexpected/missing bundle files: {actual ^ BUNDLE_FILES}")
    root = ET.parse(bundle / "PackageContents.xml").getroot()
    require(root.tag == "ApplicationPackage" and root.get("Name") == "ACadHotKey", "Invalid package identity")
    if version:
        require(root.get("AppVersion") == version, "Bundle AppVersion differs from release version")
    components = root.findall("Components")
    require(len(components) == len(TARGETS), "Expected exactly two API generations")
    for target, (minimum, maximum) in TARGETS.items():
        matches = [c for c in components if c.find("RuntimeRequirements") is not None
                   and c.find("RuntimeRequirements").get("SeriesMin") == minimum
                   and c.find("RuntimeRequirements").get("SeriesMax") == maximum]
        require(len(matches) == 1, f"Expected one component for {target}")
        requirements = matches[0].find("RuntimeRequirements")
        require(requirements.get("OS") == "Win64" and requirements.get("Platform") == "AutoCAD*",
                f"Incorrect OS/platform for {target}")
        entries = matches[0].findall("ComponentEntry")
        require(len(entries) == 1, f"Expected one entry for {target}")
        entry = entries[0]
        require(entry.get("ModuleName") == f"./Contents/{target}/ACadHotKey.dll", f"Invalid module path for {target}")
        require(entry.get("LoadOnAutoCADStartup", "").lower() == "true", f"Startup loading disabled for {target}")
        for name in FILES:
            path = bundle / "Contents" / target / name
            require(path.stat().st_size > 0, f"Empty file: {path}")
            if path.suffix == ".dll":
                with path.open("rb") as stream:
                    require(stream.read(2) == b"MZ", f"Invalid DLL: {path}")
        ET.parse(bundle / "Contents" / target / "ACadHotKey.config.xml")


def archive_name(version):
    return f"ACadHotKey-manual-install-v{version}.zip"


def verify_release(output, version):
    output = Path(output)
    archive = output / archive_name(version)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    require((output / "release-manifest.txt").read_text(encoding="utf-8") == f"{checksum}  {archive.name}\n",
            "Release SHA256 mismatch")
    with ZipFile(archive) as zipped, tempfile.TemporaryDirectory() as scratch:
        expected = {f"{BUNDLE_NAME}/{name}" for name in BUNDLE_FILES} | {"INSTALL.md"}
        require(len(zipped.namelist()) == len(expected) and set(zipped.namelist()) == expected,
                "ZIP must contain only INSTALL.md and the complete ACadHotKey.bundle")
        require(zipped.testzip() is None, "ZIP CRC check failed")
        require(zipped.read("INSTALL.md") == (REPO / "bundle/INSTALL.md").read_bytes(), "Wrong installation instructions")
        # Simulate copying the extracted bundle to a user profile. No system directories are written.
        appdata = Path(scratch) / "User Profile" / "AppData" / "Roaming"
        plugins = appdata / "Autodesk" / "ApplicationPlugins"
        extracted = Path(scratch) / "extracted"
        zipped.extractall(extracted)
        shutil.copytree(extracted / BUNDLE_NAME, plugins / BUNDLE_NAME)
        verify_bundle(plugins / BUNDLE_NAME, version)


def create_release(bundle, output, version):
    verify_bundle(bundle, version)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / archive_name(version)
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zipped:
        zipped.write(REPO / "bundle/INSTALL.md", "INSTALL.md")
        for name in sorted(BUNDLE_FILES):
            zipped.write(Path(bundle) / name, f"{BUNDLE_NAME}/{name}")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "release-manifest.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    (output / "release-notes.md").write_text(
        f"# ACadHotKey {version}\n\n"
        f"`{archive.name}` — ручная установка для AutoCAD 2020–2024 (Windows x64) "
        "без инсталлятора и прав администратора. Инструкция `INSTALL.md` находится внутри архива.\n\n"
        "Скопируйте папку `ACadHotKey.bundle` целиком в "
        "`%APPDATA%\\Autodesk\\ApplicationPlugins` и перезапустите AutoCAD. "
        "Пакет настроен на автоматическую загрузку подходящей сборки.\n\n"
        "Контрольная сумма SHA256 — в `release-manifest.txt`.\n", encoding="utf-8")
    verify_release(output, version)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--tag", help="Reject tags that differ from v<project Version>")
    parser.add_argument("--bundle", type=Path, default=REPO / "artifacts" / BUNDLE_NAME)
    parser.add_argument("--output", type=Path, default=REPO / "artifacts/release")
    args = parser.parse_args()
    version = release_version(args.tag)
    if args.print_version:
        print(version)
    else:
        print(create_release(args.bundle, args.output, version))


if __name__ == "__main__":
    main()
