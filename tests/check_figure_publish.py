"""Dependency-backed local check of the figure producer's real copy/swap seam."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

class FigurePublicationTests(unittest.TestCase):
    def test_rendered_f3_names_raw_and_adjusted_panels(self):
        import shutil
        import figures
        source=figures.ROOT
        checked=[]
        original_qa=figures.qa
        def inspect_render(fig,name):
            original_qa(fig,name)
            if name in ('f3','f3-dark'):
                self.assertEqual([ax.get_title(loc=figures.plt.rcParams['axes.titlelocation']) for ax in fig.axes],
                                 ['Raw prices and band medians','Storey, area and month removed'])
                checked.append(name)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for directory in ('outputs','data/processed'):
                shutil.copytree(source/directory,root/directory)
            (root/'assets/fonts').mkdir(parents=True)
            for style in ('style.mplstyle','style-dark.mplstyle'):
                shutil.copy(source/'assets'/style,root/'assets'/style)
            # Windows keeps rendered font files open; register originals, not temporary copies.
            for font in (source/'assets/fonts').glob('*.ttf'):
                figures.font_manager.fontManager.addfont(str(font))
            with patch.object(figures,'ROOT',root),patch.object(figures,'qa',side_effect=inspect_render):
                figures.main()
            self.assertEqual(checked,['f3','f3-dark'])
            for name in ('f3_exemplar.png','f3_exemplar-dark.png'):
                self.assertEqual((root/'reports/figures'/name).read_bytes(),
                                 (root/'docs/img'/name).read_bytes())

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
