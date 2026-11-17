Run experiments/package.sh from the repository root.
The complete bundle is created at artifacts/ACadHotKey.bundle:
  Contents/2020: SDK 23.1, .NET Framework 4.7
  Contents/2021-2024: SDK 24.0, .NET Framework 4.8
Each folder contains ACadHotKey.dll, ACadHotKey.Core.dll, ACadHotKey.config.xml.
Then run python3 experiments/release_package.py to create the manual-install ZIP.
End users can download this ZIP from GitHub Releases instead of building from source.
See bundle/INSTALL.md for installation under %APPDATA% without administrator rights.
