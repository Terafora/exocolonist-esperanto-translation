"""Optional, version-checked Windows font patch. No game assets are distributed."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile

# Inspected Windows archive: Steam build 26332981 / game version 7030.
ORIGINAL_SHA256 = 'e227598bec2d991c79bae98edb60b30f73a1f42909678c19d5a24acd52702d81'
PATCHED_SHA256 = '7c71bd6263a219880f0ca2668a83f7b5dd917a53819f48e555ed9d03fcd0c136'
TARGET = ('sharedassets1.assets', 14)


class PatchError(Exception):
    """A failed safety check; do not overwrite the installation."""


def require(condition, message):
    if not condition:
        raise PatchError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_path(game_dir):
    return game_dir / 'Exocolonist_Data' / 'data.unity3d'


def backup_path(game_dir):
    return game_dir / '.esperanto-font-backup' / f'data.unity3d.{ORIGINAL_SHA256}.bak'


def status(game_dir):
    path = archive_path(game_dir)
    require(path.is_file(), f'Game archive not found: {path}')
    value = file_digest(path)
    if value == ORIGINAL_SHA256:
        return 'original'
    if value == PATCHED_SHA256:
        return 'patched'
    raise PatchError(
        f'Unsupported or modified game archive (SHA-256 {value}). '
        'No changes made. Only the inspected Windows build 26332981 / version 7030 '
        'is supported. A game update needs a newly reviewed patch.'
    )


def ensure_game_closed():
    require(sys.platform == 'win32', 'Applying/restoring is supported on Windows only.')
    result = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq Exocolonist.exe', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True, check=True,
    )
    running = any(row and row[0].lower() == 'exocolonist.exe'
                  for row in csv.reader(io.StringIO(result.stdout)))
    require(not running, 'Close Exocolonist before applying or restoring the font patch.')


def prepare_patch(source, game_dir):
    """Build in memory and verify every object before returning replacement bytes."""
    require(digest(source) == ORIGINAL_SHA256, 'Unexpected source archive.')
    try:
        import UnityPy
        from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
    except ImportError as exc:
        raise PatchError('Install tools/font-patch-requirements.txt first (see tools/README.md).') from exc

    def key(obj):
        return obj.assets_file.name, obj.path_id

    env = UnityPy.load(source)
    generator = TypeTreeGenerator(next(iter(env.objects)).assets_file.unity_version)
    generator.load_local_game(str(game_dir))
    env.typetree_generator = generator
    objects = {key(obj): obj for obj in env.objects}
    original_hashes = {k: digest(obj.get_raw_data()) for k, obj in objects.items()}
    obj = objects[TARGET]
    nodes = obj.generate_monobehaviour_node()
    before = obj.read_typetree(nodes=nodes)
    require(before['m_Name'] == 'TitilliumWeb-Bold SDF', 'Unexpected target font.')
    require(before['m_FallbackFontAssetTable'] == [], 'Unexpected existing fallback list.')
    require(obj.assets_file.externals[2].path == 'resources.assets', 'Unexpected external reference.')
    fallback = objects[('resources.assets', 323)]
    fallback_data = fallback.read_typetree(nodes=fallback.generate_monobehaviour_node())
    require(fallback_data['m_Name'] == 'TitilliumWeb-Bold SDF Dynamic Backup', 'Unexpected fallback font.')
    require(fallback_data['m_AtlasPopulationMode'] == 1, 'Fallback is not dynamic.')
    require(fallback_data['m_SourceFontFile'] == {'m_FileID': 0, 'm_PathID': 163},
            'Unexpected fallback source font.')
    original_bytes = obj.get_raw_data()
    obj.save_typetree(before, nodes=nodes)
    require(obj.get_raw_data() == original_bytes, 'Font serialization is not lossless.')
    after = copy.deepcopy(before)
    after['m_FallbackFontAssetTable'] = [{'m_FileID': 3, 'm_PathID': 323}]
    obj.save_typetree(after, nodes=nodes)
    bundle = obj.assets_file.parent
    patched = bundle.save(packer='original')

    check = UnityPy.load(patched)
    check.typetree_generator = generator
    checked = {key(o): o for o in check.objects}
    require(checked.keys() == objects.keys(), 'Archive object inventory changed.')
    changed = [k for k, o in checked.items() if digest(o.get_raw_data()) != original_hashes[k]]
    require(changed == [TARGET], f'Unexpected changed objects: {changed}')
    font = checked[TARGET]
    require(font.read_typetree(nodes=font.generate_monobehaviour_node()) == after,
            'Serialized font does not match the intended change.')
    rebuilt = font.assets_file.parent
    require(set(bundle.files) == set(rebuilt.files), 'Bundle entry inventory changed.')
    for name, entry in bundle.files.items():
        if name == TARGET[0]:
            continue
        other = rebuilt.files[name]
        def entry_bytes(value):
            return value.bytes if hasattr(value, 'bytes') else value.save()
        require(entry_bytes(entry) == entry_bytes(other), f'Unexpected bundle change: {name}')
    require(digest(patched) == PATCHED_SHA256,
            'Output differs from the verified patch. Refusing installation.')
    print(f'Verified {len(objects):,} objects; only the intended font fallback list changed.')
    return patched


def save_backup(path, source):
    """Never replace an existing backup, including one with unexpected contents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open('xb') as stream:
            stream.write(source)
            stream.flush()
            os.fsync(stream.fileno())
    require(file_digest(path) == ORIGINAL_SHA256,
            f'Backup is incomplete or differs from the original: {path}. Refusing to proceed.')


def replace_checked(target, replacement, expected_current):
    """Stage on the same volume, recheck the live file, then replace atomically."""
    fd, name = tempfile.mkstemp(prefix='.esperanto-font-', suffix='.tmp', dir=target.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        require(file_digest(staged) == digest(replacement), 'Staged file verification failed.')
        ensure_game_closed()
        require(file_digest(target) == expected_current,
                'Game archive changed during preparation. Refusing overwrite.')
        os.replace(staged, target)
        require(file_digest(target) == digest(replacement), 'Installed file verification failed.')
    finally:
        staged.unlink(missing_ok=True)


def apply(game_dir):
    if status(game_dir) == 'patched':
        print('The exact font fix is already installed. No files changed.')
        backup = backup_path(game_dir)
        if not backup.is_file() or file_digest(backup) != ORIGINAL_SHA256:
            print('No verified companion-patcher backup found; restore requires the original archive.')
        return
    ensure_game_closed()
    source = archive_path(game_dir).read_bytes()
    patched = prepare_patch(source, game_dir)
    save_backup(backup_path(game_dir), source)
    replace_checked(archive_path(game_dir), patched, ORIGINAL_SHA256)
    print(f'Font fix installed. Original backup: {backup_path(game_dir)}')


def restore(game_dir):
    if status(game_dir) == 'original':
        print('Original archive is already installed. No files changed.')
        return
    ensure_game_closed()
    backup = backup_path(game_dir)
    require(backup.is_file(), f'Original backup not found: {backup}')
    original = backup.read_bytes()
    require(digest(original) == ORIGINAL_SHA256, 'Backup checksum failed. Refusing restore.')
    replace_checked(archive_path(game_dir), original, PATCHED_SHA256)
    print('Original game archive restored. Backup retained.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'apply', 'restore'])
    parser.add_argument('--game-dir', required=True, type=Path,
                        help='Installation folder containing Exocolonist_Data (not the Mods folder)')
    args = parser.parse_args()
    game_dir = args.game_dir.resolve()
    try:
        if args.command == 'check':
            print(f'Archive status: {status(game_dir)}. No files changed.')
        elif args.command == 'apply':
            apply(game_dir)
        else:
            restore(game_dir)
    except (PatchError, OSError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
