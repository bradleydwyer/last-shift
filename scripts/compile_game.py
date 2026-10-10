"""Compile modified SCI scripts through the headless SCI Companion compiler."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
compiler='/work/tools/lucasartsifier/tools/scicompile/build/scicompile'
scripts=[('Cycle',992),('Main',0),('Inventory',15),('AboutCode',13),('StationActions',113),('SiestaIntro',120),('rm110',110),('rm111',111),('rm112',112)]
for name,number in scripts:
    output=ROOT/'game'/f'{number}.scr'
    cmd=['docker','exec','three-room-sci-builder',compiler,'--version','sci11','/work/game',f'/work/game/src/{name}.sc',f'/work/game/{number}.scr']
    subprocess.run(cmd,check=True)
    payload=output.read_bytes()
    output.write_bytes(b'\x82\x00'+payload)
    heap=Path(str(output)+'.hep')
    (ROOT/'game'/f'{number}.hep').write_bytes(b'\x91\x00'+heap.read_bytes())
    heap.unlink()
print('SCI bytecode and heap patches compiled successfully.')
