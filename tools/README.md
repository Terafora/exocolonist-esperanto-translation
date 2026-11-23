# Optional Windows font fix

The translation mod works through the game's normal Mods menu. This **separate companion patcher** fixes thin Esperanto letters in the standard bold font. Downloading or enabling the translation alone does not run it.

Status: experimental. Archive structure and apply/restore behavior are tested. On 23 November 2026 the maintainer reported that the installed fix appears to work in-game; this is not exhaustive verification of all screens or font styles. The only supported archive is the inspected Windows Steam build **26332981**, game version **7030**, identified by its full SHA-256 checksum. Other builds and previously modified archives are rejected, even if their displayed version looks similar. macOS and Linux installations are not supported.

## What changes

`TitilliumWeb-Bold SDF` omits Esperanto letters and has no local fallback. The patch gives it the existing `TitilliumWeb-Bold SDF Dynamic Backup` fallback. That font's source contains `ĉ ĝ ĥ ĵ ŝ ŭ Ĉ Ĝ Ĥ Ĵ Ŝ Ŭ`.

This affects every text element using that shared font asset. Three other bold assets already reference the matching fallback. Semibold and italic styles are separate and are not changed. The patch does not promise correct rendering for every font/style combination throughout the game.

Only patching code is distributed. It rebuilds the player's own `Exocolonist_Data/data.unity3d` and verifies that only the intended fallback list changes. No game archives, extracted fonts, story files or DLLs belong in a release of this tool. Package the tracked source files, not the entire local working folder: exclude `local/`, `upstream/`, virtual environments and backups from ZIPs and Workshop uploads too; `.gitignore` alone does not filter those uploads.

## Setup and use

Use **64-bit Python 3.12 on Windows**. Close Exocolonist and let Steam finish any updates. Open PowerShell in the downloaded repository folder. Replace the example game path with your own installation directory, obtainable through Steam's Browse local files command.

```powershell
py -3.12 -m venv .venv-font-patch
.\.venv-font-patch\Scripts\python.exe -m pip install -r tools/font-patch-requirements.txt
.\.venv-font-patch\Scripts\python.exe tools/font_patch.py check --game-dir "D:\Steam\steamapps\common\Exocolonist"
.\.venv-font-patch\Scripts\python.exe tools/font_patch.py apply --game-dir "D:\Steam\steamapps\common\Exocolonist"
```

Allow several minutes and several GB of available RAM/disk space while the archive is rebuilt and checked. You need write access to the installation folder. A successful run prints `Font fix installed` with the backup location. Repeating `apply` on the exact patched archive makes no changes.

The original archive is retained inside `.esperanto-font-backup` in the game installation folder. Keep that backup. Installation stages the replacement on the same drive, checks that the game is closed and the archive has not changed, then replaces it atomically.

Launch the game with the Esperanto mod enabled. Check that **Ŭ** in **DAŬRIGI** and **Ŝ** in **ŜARGI** match the other letters. Check other bold headings and normal text for regressions. Record screenshots and the game version before treating the patch as ready for release.

## Undo

Close the game, then run:

```powershell
.\.venv-font-patch\Scripts\python.exe tools/font_patch.py restore --game-dir "D:\Steam\steamapps\common\Exocolonist"
```

Restore verifies both the installed patch and the backup. It will not overwrite a newer game archive or another modification. The backup remains after restoration. Steam's Verify integrity option can also restore game files, but can remove other direct game-file modifications too.

Steam updates or verification can remove the fix. Do not restore an old backup over an updated game, edit the accepted checksums, or force the patch onto an unknown build. A new build must be inspected and supported separately.

If `apply` reports that this exact fix is already installed but no companion-patcher backup exists, it leaves the installation untouched. This can happen after a manually installed patch. Keep your earlier original backup; the tool does not manufacture or download a replacement.

## Developer checks

```powershell
py -3.12 -m unittest discover -s tests -p "test_font_patch.py"
```

The small tests use artificial archives and exercise install/restore safety without requiring the game or Unity libraries. Actual archive rebuilding also performs full object and bundle-entry comparison and checks the expected output hash. Dependencies are pinned at the top level; transitive dependency changes are possible, so unexpected output is rejected instead of installed.
