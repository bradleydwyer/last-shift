"""Operate only the game's isolated Xvfb test display, never the host desktop."""
import subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd):
    return subprocess.run(['docker','exec','-e','DISPLAY=:99','three-room-sci-builder',*cmd],check=True,capture_output=True,text=True).stdout
def shot(name='linux'):
    run(['import','-window','root',f'/work/verification/{name}.png'])
    print(ROOT/f'verification/{name}.png')
if sys.argv[1]=='shot':
    shot(sys.argv[2] if len(sys.argv)>2 else 'linux')
else:
    action=sys.argv[1]
    if action in ('click','right'):
        run(['xdotool','mousemove',sys.argv[2],sys.argv[3]])
        time.sleep(.2)
        run(['xdotool','click','1' if action=='click' else '3'])
    elif action=='move': run(['xdotool','mousemove',sys.argv[2],sys.argv[3]])
    elif action=='key': run(['xdotool','key',sys.argv[2]])
    elif action=='type': run(['xdotool','type','--clearmodifiers',sys.argv[2]])
    else: raise ValueError(action)
    time.sleep(1.3)
    shot()
