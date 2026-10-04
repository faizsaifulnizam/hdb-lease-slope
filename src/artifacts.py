"""Series batch replacement: validate first, roll back ordinary swap failures.
Not crash-atomic or safe for concurrent writers; copied from card-book-quality.
"""
import csv
import os
import shutil
import tempfile
from pathlib import Path


def publish_paths(pairs):
    pairs=[(Path(src),Path(dst)) for src,dst in pairs]
    pairs[0][1].parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix='.publish-backup-',dir=pairs[0][1].parent))
    saved,installed=[],[]
    try:
        for i,(src,dst) in enumerate(pairs):
            dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():
                previous=backup/str(i); os.replace(dst,previous); saved.append((previous,dst))
            os.replace(src,dst); installed.append(dst)
    except BaseException:
        try:
            for dst in reversed(installed):
                if dst.is_dir(): shutil.rmtree(dst)
                else: dst.unlink()
            for previous,dst in reversed(saved): os.replace(previous,dst)
        except BaseException as recovery:
            raise RuntimeError(f'rollback failed; recovery backup: {backup}') from recovery
        shutil.rmtree(backup)
        raise
    shutil.rmtree(backup)


def write_csv(path,rows,fields=None):
    rows=list(rows)
    fields=fields or list(rows[0])
    with Path(path).open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=fields,lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
