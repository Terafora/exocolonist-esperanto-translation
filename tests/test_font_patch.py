"""Safety/lifecycle tests with tiny stand-in archives, not copyrighted game data."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import font_patch as fp


class FontPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='esperanto-font-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = b'original test archive'
        self.patched = b'patched test archive'
        self.target = fp.archive_path(self.root)
        self.target.parent.mkdir()
        self.target.write_bytes(self.original)
        for name, value in [('ORIGINAL_SHA256', fp.digest(self.original)),
                            ('PATCHED_SHA256', fp.digest(self.patched))]:
            context = patch.object(fp, name, value)
            context.start()
            self.addCleanup(context.stop)
        self.closed = patch.object(fp, 'ensure_game_closed')
        self.closed_mock = self.closed.start()
        self.addCleanup(self.closed.stop)
        builder = patch.object(fp, 'prepare_patch', return_value=self.patched)
        self.builder = builder.start()
        self.addCleanup(builder.stop)
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_apply_repeat_restore_repeat(self):
        self.assertEqual(fp.status(self.root), 'original')
        fp.apply(self.root)
        backup = fp.backup_path(self.root)
        self.assertEqual(backup.read_bytes(), self.original)
        self.assertEqual(self.target.read_bytes(), self.patched)
        backup_time = backup.stat().st_mtime_ns
        fp.apply(self.root)
        self.assertEqual(self.builder.call_count, 1)
        self.assertEqual(backup.stat().st_mtime_ns, backup_time)
        fp.restore(self.root)
        fp.restore(self.root)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(backup.read_bytes(), self.original)

    def test_unknown_update_rejected_by_apply_and_restore(self):
        self.target.write_bytes(b'newer game version')
        for operation in [fp.apply, fp.restore]:
            with self.assertRaisesRegex(fp.PatchError, 'Unsupported'):
                operation(self.root)
        self.assertEqual(self.target.read_bytes(), b'newer game version')
        self.builder.assert_not_called()
        self.assertFalse(fp.backup_path(self.root).exists())

    def test_corrupt_backup_never_overwritten(self):
        backup = fp.backup_path(self.root)
        backup.parent.mkdir()
        backup.write_bytes(b'damaged backup')
        with self.assertRaisesRegex(fp.PatchError, 'Backup'):
            fp.apply(self.root)
        self.assertEqual(backup.read_bytes(), b'damaged backup')
        self.assertEqual(self.target.read_bytes(), self.original)
        self.target.write_bytes(self.patched)
        with self.assertRaisesRegex(fp.PatchError, 'Backup checksum'):
            fp.restore(self.root)
        self.assertEqual(self.target.read_bytes(), self.patched)

    def test_missing_backup_restore_rejected(self):
        self.target.write_bytes(self.patched)
        with self.assertRaisesRegex(fp.PatchError, 'backup not found'):
            fp.restore(self.root)
        self.assertEqual(self.target.read_bytes(), self.patched)

    def test_already_patched_without_backup_is_noop(self):
        self.target.write_bytes(self.patched)
        fp.apply(self.root)
        self.builder.assert_not_called()
        self.assertFalse(fp.backup_path(self.root).exists())

    def test_preparation_failure_preserves_installation(self):
        self.builder.side_effect = fp.PatchError('serialization failed')
        with self.assertRaisesRegex(fp.PatchError, 'serialization'):
            fp.apply(self.root)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse(fp.backup_path(self.root).exists())

    def test_game_running_stops_before_preparation(self):
        self.closed_mock.side_effect = fp.PatchError('Close Exocolonist')
        with self.assertRaises(fp.PatchError):
            fp.apply(self.root)
        self.builder.assert_not_called()

    def test_update_during_preparation_is_not_overwritten(self):
        def update(*args):
            self.target.write_bytes(b'game updated concurrently')
            return self.patched
        self.builder.side_effect = update
        with self.assertRaisesRegex(fp.PatchError, 'changed during'):
            fp.apply(self.root)
        self.assertEqual(self.target.read_bytes(), b'game updated concurrently')
        self.assertEqual(fp.backup_path(self.root).read_bytes(), self.original)
        self.assertEqual(list(self.target.parent.glob('.esperanto-font-*.tmp')), [])

    def test_failed_replace_keeps_original_and_backup(self):
        with patch.object(fp.os, 'replace', side_effect=PermissionError('file locked')):
            with self.assertRaises(PermissionError):
                fp.apply(self.root)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(fp.backup_path(self.root).read_bytes(), self.original)
        self.assertEqual(list(self.target.parent.glob('.esperanto-font-*.tmp')), [])

    def test_game_starts_before_replace(self):
        self.closed_mock.side_effect = [None, fp.PatchError('Close Exocolonist')]
        with self.assertRaises(fp.PatchError):
            fp.apply(self.root)
        self.assertEqual(self.target.read_bytes(), self.original)


class ProcessCheckTests(unittest.TestCase):
    def test_tasklist_process_detection_and_failure(self):
        with patch.object(fp.sys, 'platform', 'win32'):
            with patch.object(fp.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, '"Exocolonist.exe","123","Console","1","1 K"\n')):
                with self.assertRaisesRegex(fp.PatchError, 'Close Exocolonist'):
                    fp.ensure_game_closed()
            with patch.object(fp.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 0, 'INFO: No tasks are running which match the specified criteria.')):
                fp.ensure_game_closed()
            with patch.object(fp.subprocess, 'run', side_effect=OSError('tasklist unavailable')):
                with self.assertRaises(OSError):
                    fp.ensure_game_closed()


if __name__ == '__main__':
    unittest.main()
