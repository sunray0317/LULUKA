"""Build only explicitly reviewed public files. Run from any directory."""
from pathlib import Path
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.site'
ALLOWED_SUFFIXES = {'.html', '.css', '.js', '.png', '.jpg', '.gif', '.txt', '.xml', '.svg'}


def build():
    paths = json.loads((ROOT / 'scripts/public-files.json').read_text())
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        raise ValueError('Public manifest must be a nonempty list of unique paths')
    validated = []
    for entry in paths:
        relative = Path(entry)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Unsafe public path: {entry}')
        if any(part.startswith('.') or part.lower() in {'private', 'backups', 'docs', 'scripts', 'infra'} for part in relative.parts):
            raise ValueError(f'Nonpublic path: {entry}')
        if relative.suffix.lower() not in ALLOWED_SUFFIXES and entry != 'CNAME':
            raise ValueError(f'Unsupported public file type: {entry}')
        source = ROOT / relative
        if any(p.is_symlink() for p in [source, *source.parents] if p != ROOT.parent):
            raise ValueError(f'Symlinks cannot be published: {entry}')
        if not source.is_file() or not source.resolve().is_relative_to(ROOT):
            raise ValueError(f'Missing or escaped public file: {entry}')
        validated.append((entry, source))
    if DEST.is_symlink():
        raise ValueError('Output directory cannot be a symlink')
    with tempfile.TemporaryDirectory(prefix='.public-build-', dir=ROOT) as staging:
        output = Path(staging)
        for entry, source in validated:
            target = output / entry
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        if DEST.exists():
            shutil.rmtree(DEST)
        shutil.copytree(output, DEST)
    print(f'Built {len(validated)} reviewed public files into {DEST}')


if __name__ == '__main__':
    build()
