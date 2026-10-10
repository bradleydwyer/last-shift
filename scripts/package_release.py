"""Package source and playable resources without local diagnostics or saves."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'Last Shift.zip'
roots = ['README.md', 'LICENSE', 'LICENSES', 'THIRD_PARTY_NOTICES.md',
         'Play Last Shift.command', 'dist', 'game', 'assets', 'scripts', 'verification']

def include(path):
    parts = path.relative_to(ROOT).parts
    if '__pycache__' in parts or path.name.startswith('.') or path.suffix == '.pyc':
        return False
    if parts[0] == 'game' and (path.suffix.lower() in ('.exe', '.drv', '.com')
                              or path.name.lower() in ('interp.err', 'resource.cfg',
                                                       'dosbox.conf', 'resource.aud', 'resource.sfx')):
        return False
    if parts[0] == 'verification':
        if len(parts) > 2 or path.suffix in ('.log', '.raw', '.ini', '.wav', '.txt') or path.name.endswith('state.json'):
            return False
    return True

staging = ROOT / 'Last Shift.updated.zip'
with ZipFile(staging, 'w', ZIP_DEFLATED) as archive:
    archive.writestr('Last Shift/START HERE.txt',
        'Last Shift - double-click Play Last Shift.command on macOS. '
        'Other platforms: add dist/Last Shift to ScummVM. '
        'See README.md for controls and rebuilding.\n')
    for name in roots:
        base = ROOT / name
        for path in ([base] if base.is_file() else sorted(base.rglob('*'))):
            if path.is_file() and include(path):
                archive.write(path, 'Last Shift/' + path.relative_to(ROOT).as_posix())

with ZipFile(staging) as archive:
    assert archive.testzip() is None
    assert archive.read('Last Shift/LICENSE') == (ROOT/'LICENSE').read_bytes()
    assert 'Last Shift/THIRD_PARTY_NOTICES.md' in archive.namelist()
    assert not any(Path(name).suffix.lower() in ('.exe', '.drv', '.com')
                   for name in archive.namelist())
    assert archive.read('Last Shift/dist/Last Shift/resource.000') == (ROOT/'dist/Last Shift/resource.000').read_bytes()
    assert (archive.getinfo('Last Shift/Play Last Shift.command').external_attr >> 16) & 0o111
    for name in archive.namelist():
        data = archive.read(name)
        assert (b'/' + b'Users' + b'/') not in data and (b'/var' + b'/folders/') not in data, name
staging.replace(DEST)
print(f'Packaged and privacy-checked {DEST.name}: {DEST.stat().st_size:,} bytes')
