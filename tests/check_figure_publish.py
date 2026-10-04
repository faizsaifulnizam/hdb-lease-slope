"""Dependency-backed local check of the figure producer's real copy/swap seam."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

class FigurePublicationTests(unittest.TestCase):
    def test_real_copy_and_later_mirror_failure_rollback(self):
        import figures
        self.assertTrue(hasattr(figures,'publish_figures'),'figure producer must synchronize its validated batch into docs/img')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); directory=root/'reports/figures'; directory.mkdir(parents=True)
            staged=directory/'figure.png.part'; destination=directory/'figure.png'
            with patch.object(figures,'ROOT',root):
                staged.write_bytes(b'first validated figure')
                figures.publish_figures([(staged,destination)])
                mirror=root/'docs/img/figure.png'
                self.assertEqual(destination.read_bytes(),b'first validated figure')
                self.assertEqual(mirror.read_bytes(),destination.read_bytes())
                staged.write_bytes(b'next validated figure')
                replace=os.replace
                def fail_mirror(src,dst):
                    if Path(dst)==mirror and str(src).endswith('.part'):
                        raise OSError('injected later mirror install failure')
                    return replace(src,dst)
                with patch('artifacts.os.replace',side_effect=fail_mirror):
                    with self.assertRaisesRegex(OSError,'later mirror'):
                        figures.publish_figures([(staged,destination)])
                self.assertEqual(destination.read_bytes(),b'first validated figure')
                self.assertEqual(mirror.read_bytes(),b'first validated figure')

if __name__=='__main__': unittest.main()
