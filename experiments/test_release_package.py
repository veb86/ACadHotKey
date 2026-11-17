#!/usr/bin/env python3
"""Focused release regressions using the real build output; run package.sh first."""
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import release_package as release


class ReleasePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = release.REPO / "artifacts" / release.BUNDLE_NAME
        cls.version = release.release_version()
        release.verify_bundle(cls.bundle, cls.version)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def copy_bundle(self):
        return Path(shutil.copytree(self.bundle, self.root / release.BUNDLE_NAME))

    def make_release(self):
        return release.create_release(self.bundle, self.root, self.version)

    def refresh_checksum(self, archive):
        checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
        (self.root / "release-manifest.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")

    def test_archive_round_trip_to_user_profile(self):
        archive = self.make_release()
        self.assertEqual(archive.name, f"ACadHotKey-manual-install-v{self.version}.zip")
        release.verify_release(self.root, self.version)
        with ZipFile(archive) as zipped:
            self.assertEqual(len(zipped.namelist()), 8)
            self.assertIn("ACadHotKey.bundle/PackageContents.xml", zipped.namelist())
        self.assertIn("%APPDATA%", (self.root / "release-notes.md").read_text(encoding="utf-8"))

    def test_every_dependency_is_required(self):
        bundle = self.copy_bundle()
        for target in release.TARGETS:
            for name in release.FILES:
                with self.subTest(target=target, name=name):
                    path = bundle / "Contents" / target / name
                    data = path.read_bytes()
                    path.unlink()
                    with self.assertRaisesRegex(ValueError, "missing bundle files"):
                        release.create_release(bundle, self.root / "out", self.version)
                    path.write_bytes(data)

    def test_autodesk_dll_installer_and_stale_files_are_rejected(self):
        bundle = self.copy_bundle()
        for name in ("Contents/2020/AcMgd.dll", "setup.exe", "Contents/old/ACadHotKey.dll"):
            with self.subTest(name=name):
                path = bundle / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"unexpected payload")
                with self.assertRaisesRegex(ValueError, "Unexpected/missing bundle files"):
                    release.verify_bundle(bundle)
                path.unlink()

    def test_empty_or_invalid_dll_is_rejected(self):
        bundle = self.copy_bundle()
        dll = bundle / "Contents/2020/ACadHotKey.dll"
        for content in (b"", b"not a DLL"):
            with self.subTest(content=content):
                dll.write_bytes(content)
                with self.assertRaises(ValueError):
                    release.verify_bundle(bundle)

    def test_broken_config_is_rejected(self):
        bundle = self.copy_bundle()
        (bundle / "Contents/2021-2024/ACadHotKey.config.xml").write_text("<broken>")
        with self.assertRaises(ET.ParseError):
            release.verify_bundle(bundle)

    def test_autoload_manifest_regressions_are_rejected(self):
        bundle = self.copy_bundle()
        manifest = bundle / "PackageContents.xml"
        original = manifest.read_bytes()
        for query, attribute, value in (
            ("Components/ComponentEntry", "LoadOnAutoCADStartup", "False"),
            ("Components/ComponentEntry", "ModuleName", "../outside.dll"),
            ("Components/RuntimeRequirements", "SeriesMax", "R24.0"),
            ("Components/RuntimeRequirements", "Platform", "AutoCAD"),
            ("Components/RuntimeRequirements", "OS", "Win32"),
            (".", "AppVersion", "0.0.0"),
        ):
            with self.subTest(attribute=attribute):
                tree = ET.ElementTree(ET.fromstring(original))
                tree.find(query).set(attribute, value)
                tree.write(manifest)
                with self.assertRaises(ValueError):
                    release.verify_bundle(bundle, self.version)

    def test_tag_must_match_project_version(self):
        self.assertEqual(release.release_version(f"v{self.version}"), self.version)
        for tag in ("v999.0.0", self.version, "v../bad"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "does not match"):
                release.release_version(tag)

    def test_project_and_manifest_versions_must_match(self):
        project = Path("src/ACadHotKey.Plugin/ACadHotKey.Plugin.csproj")
        manifest = Path("bundle/ACadHotKey.bundle/PackageContents.xml")
        for path in (project, manifest):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(release.REPO / path, self.root / path)
        tree = ET.parse(self.root / manifest)
        tree.getroot().set("AppVersion", "0.0.0")
        tree.write(self.root / manifest)
        with patch.object(release, "REPO", self.root):
            with self.assertRaisesRegex(ValueError, "must match"):
                release.release_version()

    def test_checksum_detects_corrupt_archive(self):
        archive = self.make_release()
        with archive.open("ab") as stream:
            stream.write(b"corruption")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            release.verify_release(self.root, self.version)

    def test_unsafe_or_incomplete_zip_is_rejected_even_with_valid_checksum(self):
        for name in ("../outside.dll", "setup.exe", "ACadHotKey.bundle/Contents/2020/AcMgd.dll"):
            with self.subTest(name=name):
                archive = self.make_release()
                with ZipFile(archive, "a") as zipped:
                    zipped.writestr(name, b"unexpected")
                self.refresh_checksum(archive)
                with self.assertRaisesRegex(ValueError, "ZIP must contain only"):
                    release.verify_release(self.root, self.version)
        archive = self.make_release()
        with ZipFile(archive) as zipped:
            entries = {n: zipped.read(n) for n in zipped.namelist() if not n.endswith("Core.dll")}
        with ZipFile(archive, "w") as zipped:
            for name, data in entries.items():
                zipped.writestr(name, data)
        self.refresh_checksum(archive)
        with self.assertRaisesRegex(ValueError, "ZIP must contain only"):
            release.verify_release(self.root, self.version)


if __name__ == "__main__":
    unittest.main(verbosity=2)
