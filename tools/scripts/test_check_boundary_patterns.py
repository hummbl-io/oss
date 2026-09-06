"""Focused boundary regressions using synthetic data and temporary repositories."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_boundary_patterns as checker


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))
        return name

    def scan(self, name, content):
        return checker.scan_paths(self.root, [self.write(name, content)])

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True)

    def test_package_documents_and_denied_directories(self):
        for name in ['packages/python/demo/docs/HANDOFF-private.md',
                     'packages/python/demo/receipts/example.json',
                     'docs/HANDOFF.md', 'docs/HANDOFF.txt']:
            with self.subTest(name=name):
                self.assertEqual(self.scan(name, '{}').exit_code, 1)

    def test_encoded_windows_home_paths(self):
        for separator in ('\\', '\\\\', '/', '//'):
            text = 'D:' + separator + 'Users' + separator + 'ExamplePerson' + separator + 'file.txt'
            with self.subTest(separator=separator):
                self.assertEqual(self.scan('fixture.py', text).exit_code, 1)

    def test_linked_root_never_invokes_git(self):
        target = self.root / 'target'
        target.mkdir()
        linked = self.root / 'linked'
        try:
            linked.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest(str(exc))
        with patch.object(checker.subprocess, 'run', side_effect=AssertionError('Git traversed linked root')):
            result = checker.scan(linked)
        self.assertEqual(result.incomplete, [('.', 'root-link-not-followed')])

    def test_public_domain_exceptions_are_exact_and_content_checked(self):
        for name in checker.PUBLIC_DOMAIN_PATHS:
            with self.subTest(name=name):
                self.assertEqual(self.scan(name, '{}').exit_code, 0)
                result = self.scan(name, '100.' + '96.22.31')
                self.assertEqual(result.exit_code, 1)
        self.assertEqual(self.scan('docs/receipt_engine.py', '{}').exit_code, 1)

    def test_private_declarations(self):
        for text in ['Status: private', '**Status:** private', '**Status: private**',
                     '**Status**: **PRIVATE**', '# Classification: confidential',
                     '- Visibility: internal-only', '**Status:** live v1.0 (private)',
                     '# Status: live v1.0 (private)', '__Status:__ live v1.0 (private)',
                     '_Status:_ live v1.0 (private)',
                     '**Status:** live v1.0 (private â€” pre-decision)',
                     '**Status:** live v1.0 internal (promoted; private â€” not for publication)']:
            with self.subTest(text=text):
                self.assertEqual(self.scan('docs/proposal.md', text).exit_code, 1)

    def test_quoted_and_fenced_declarations_are_examples(self):
        text = '> **Status:** private\n```markdown\nStatus: private\n```\n' \
               '~~~\nClassification: confidential\n~~~\n    Status: private\n' \
               '`Status: private`\nUse Status: private in an example.\n' \
               '**Status:** draft v0.1 (public|private)\n'
        self.assertEqual(self.scan('docs/examples.md', text).exit_code, 0)

    def test_url_only_and_mixed_url_local_path(self):
        url = 'https://example.org/users/example/docs'
        self.assertEqual(self.scan('README.md', url).exit_code, 0)
        for local_path in ['C:' + '/Users/' + 'synthetic/docs', '/' + 'home/synthetic/docs']:
            with self.subTest(local_path=local_path):
                result = self.scan('README.md', url + ' see ' + local_path)
                self.assertEqual(result.exit_code, 1)
                self.assertTrue(any('home-path' in rule for _, rule in result.findings))

    def test_adjacent_markdown_links_and_table_url_do_not_hide_paths(self):
        local = 'C:' + '/Users/' + 'synthetic/docs'
        for text in [f'[site](https://example.org),[local]({local})',
                     f'|https://example.org|{local}|']:
            self.assertEqual(self.scan('README.md', text).exit_code, 1)

    def test_content_in_unusual_extensions_and_dotfiles(self):
        for name in ['.settings', 'script.sh', 'settings.custom']:
            with self.subTest(name=name):
                self.assertEqual(self.scan(name, '100.' + '96.22.31').exit_code, 1)

    def test_example_ip_is_permitted(self):
        self.assertEqual(self.scan('README.md', '100.' + '64.0.1').exit_code, 0)

    def test_binary_and_unsupported_encoding_are_incomplete(self):
        for content in [b'\x89PNG\r\n\x1a\n', b'hello\x00world', b'\xffinvalid',
                        'text'.encode('utf-16')]:
            with self.subTest(content=content):
                self.assertEqual(self.scan('asset.unknown', content).exit_code, 2)

    def test_known_binary_types_need_review_even_with_printable_content(self):
        self.assertEqual(self.scan('asset.pdf', '%PDF-1.7 printable').exit_code, 2)

    def test_utf8_and_utf8_bom(self):
        for content in ['Mathematics: \u2200x \u2192 y', b'\xef\xbb\xbfpublic text']:
            self.assertEqual(self.scan('README.md', content).exit_code, 0)
        self.assertEqual(self.scan('README.md', b'\xef\xbb\xbfStatus: private').exit_code, 1)

    def test_missing_and_unreadable_are_incomplete(self):
        self.assertEqual(checker.scan_paths(self.root, ['missing.md']).exit_code, 2)
        name = self.write('README.md', 'public')
        with patch.object(Path, 'read_bytes', side_effect=PermissionError):
            self.assertEqual(checker.scan_paths(self.root, [name]).exit_code, 2)

    def test_outside_root_and_special_file(self):
        for name in ['.', '', '../outside.md', '/outside.md', 'C:/outside.md', 'dir\\outside.md']:
            self.assertEqual(checker.scan_paths(self.root, [name]).exit_code, 2)
        (self.root / 'directory').mkdir()
        self.assertEqual(checker.scan_paths(self.root, ['directory']).exit_code, 2)

    def test_symlink_and_linked_parent_are_not_followed(self):
        target = self.root / 'target'
        target.mkdir()
        (target / 'content.md').write_text('public')
        link = self.root / 'linked'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f'Symlink creation unavailable: {type(error).__name__}')
        for name in ['linked', 'linked/content.md']:
            result = checker.scan_paths(self.root, [name])
            self.assertEqual(result.exit_code, 2)
            self.assertIn((name, 'link-not-followed'), result.incomplete)

    def test_root_link_is_not_followed(self):
        target = self.root / 'target'
        target.mkdir()
        (target / 'README.md').write_text('public')
        link = self.root / 'linked'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as error:
            self.skipTest(f'Symlink creation unavailable: {type(error).__name__}')
        result = checker.scan_paths(link, ['README.md'])
        self.assertIn(('.', 'root-link-not-followed'), result.incomplete)
        (target / 'child').mkdir()
        (target / 'child' / 'README.md').write_text('public')
        result = checker.scan_paths(link / 'child', ['README.md'])
        self.assertIn(('.', 'root-link-not-followed'), result.incomplete)

    def test_git_timeout_is_incomplete(self):
        with patch.object(checker.subprocess, 'run', side_effect=subprocess.TimeoutExpired('git', 30)):
            self.assertEqual(checker.scan(self.root).exit_code, 2)

    def test_git_routing_environment_is_scrubbed(self):
        self.git('init', '-q')
        self.write('README.md', 'public')
        self.git('add', 'README.md')
        with patch.dict(checker.os.environ, {'GIT_DIR': 'missing', 'GIT_INDEX_FILE': 'missing'}):
            self.assertEqual(checker.scan(self.root).exit_code, 0)

    def test_reparse_attribute_is_not_followed(self):
        self.write('link.md', 'public')
        original = Path.lstat
        def fake_lstat(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path.name == 'link.md':
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            return info
        with patch.object(Path, 'lstat', fake_lstat):
            result = checker.scan_paths(self.root, ['link.md'])
        self.assertIn(('link.md', 'link-not-followed'), result.incomplete)

    def test_tracked_build_files_checked_untracked_scope_explicit(self):
        self.git('init', '-q')
        self.write('build/settings.custom', '100.' + '96.22.31')
        self.write('untracked.md', 'Status: private')
        self.git('add', 'build/settings.custom')
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.checked, 1)
        self.assertTrue(all(name != 'untracked.md' for name, _ in result.findings))

    def test_inventory_failure_empty_and_nonroot_are_incomplete(self):
        self.assertEqual(checker.scan(self.root).exit_code, 2)
        self.git('init', '-q')
        self.assertEqual(checker.scan(self.root).exit_code, 2)
        (self.root / 'child').mkdir()
        self.assertEqual(checker.scan(self.root / 'child').exit_code, 2)

    def test_tracked_link_even_if_materialized_is_incomplete(self):
        self.git('init', '-q')
        self.write('link.md', 'target.md')
        self.git('add', 'link.md')
        blob = self.git('rev-parse', ':link.md').stdout.decode().strip()
        self.git('update-index', '--cacheinfo', f'120000,{blob},link.md')
        result = checker.scan(self.root)
        self.assertEqual(result.exit_code, 2)
        self.assertIn(('link.md', 'tracked-link-not-followed'), result.incomplete)

    def test_manifest_scans_untracked_files_without_git(self):
        self.write('candidate.md', 'Status: private')
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(['candidate.md']))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(checker.main(['--root', str(self.root),
                                           '--files-from', str(manifest)]), 1)
        for content in ['{}', '[]', '[123]', '["../escape"]', 'not json']:
            manifest.write_text(content)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(checker.main(['--root', str(self.root),
                                               '--files-from', str(manifest)]), 2)

    def test_findings_and_incomplete_preserve_both_and_do_not_print_values(self):
        result = checker.Result(findings=[('README.md', 'internal-ip:line=1')],
                                incomplete=[('asset.png', 'binary-content-review-required')])
        output = io.StringIO()
        with patch.object(checker, 'scan', return_value=result), contextlib.redirect_stdout(output):
            self.assertEqual(checker.main([]), 2)
        self.assertIn('[DENY]', output.getvalue())
        self.assertIn('[INCOMPLETE]', output.getvalue())
        self.assertIn('History and untracked files not scanned', output.getvalue())
        ip = '100.' + '96.22.31'
        actual = self.scan('README.md', ip)
        self.assertNotIn(ip, repr(actual))


if __name__ == '__main__':
    unittest.main()
