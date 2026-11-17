#!/usr/bin/env bash
# Build a complete autoload bundle, without copying Autodesk reference assemblies.
set -euo pipefail
cd "$(dirname "$0")/.."
version="$(python3 experiments/release_package.py --print-version)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
bundle="$scratch/ACadHotKey.bundle"
mkdir -p "$bundle/Contents/2020" "$bundle/Contents/2021-2024" experiments/logs artifacts
cp bundle/ACadHotKey.bundle/PackageContents.xml "$bundle/PackageContents.xml"
for target in 2020 2021-2024; do
  api_version=23.1.0
  if [[ "$target" == 2021-2024 ]]; then api_version=24.0.0; fi
  output="$scratch/output-$target"
  # Build sequentially and turn off the persistent compiler server to bound memory usage.
  if ! dotnet build src/ACadHotKey.Plugin/ACadHotKey.Plugin.csproj -c Release -m:1 \
      -p:UseSharedCompilation=false -p:AutoCADNetVersion="$api_version" -p:Version="$version" -o "$output" \
      > "experiments/logs/package-$target.log" 2>&1; then
    echo "Build failed: experiments/logs/package-$target.log" >&2
    exit 1
  fi
  for filename in ACadHotKey.dll ACadHotKey.Core.dll ACadHotKey.config.xml; do
    cp "$output/$filename" "$bundle/Contents/$target/$filename"
  done
done
python3 experiments/verify-package.py "$bundle"
# Replace the previous output only after both builds and verification succeed.
rm -rf artifacts/ACadHotKey.bundle
mv "$bundle" artifacts/ACadHotKey.bundle
echo "Bundle: artifacts/ACadHotKey.bundle (copy it to %APPDATA%/Autodesk/ApplicationPlugins/)"
