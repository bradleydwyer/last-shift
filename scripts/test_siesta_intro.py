"""Exercise startup completion and early/late skips in an isolated SCI runtime.

Run inside the builder: python3 /work/scripts/test_siesta_intro.py.
Copies the packaged resources before launching; never changes a running game.
"""
from pathlib import Path
import os
import shutil
import subprocess
import time
import json
import struct
from array import array
import sys
from PIL import Image

ROOT=Path('/work')
TEMP=Path('/tmp/last-shift-siesta-check')
TEMP.mkdir(exist_ok=True)
shutil.copytree(ROOT/'dist/Last Shift',TEMP/'game',dirs_exist_ok=True)
(TEMP/'saves').mkdir(exist_ok=True)
config=TEMP/'player.ini'
config.write_text('''[scummvm]
updates_check=0
fullscreen=false
aspect_ratio=false
gfx_mode=2x
filtering=false
confirm_exit=false
output_rate=22050
[last-shift]
engineid=sci
gameid=sq5
path=/tmp/last-shift-siesta-check/game
savepath=/tmp/last-shift-siesta-check/saves
''')
env=os.environ.copy();env.update(DISPLAY=':101',SDL_AUDIODRIVER='disk')
xv=subprocess.Popen(['Xvfb',':101','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(.3)
results=[]

def screenshot(name):
    path=ROOT/'verification'/('siesta-'+name+'.png')
    subprocess.run(['import','-window','root',str(path)],env=env,check=True)
    return Image.open(path).convert('RGB')

def room_pixels(image):
    return image.crop((80,120,720,500)).resize((320,190),Image.Resampling.NEAREST)

def assert_reception(image):
    assert_room(image,110)

def assert_room(image,number):
    actual=room_pixels(image)
    expected=Image.open(ROOT/f'assets/converted/room-{number}.png').convert('RGB')
    for point in [(20,20),(70,30),(220,30),(280,60),(310,130)]:
        assert max(abs(a-b) for a,b in zip(actual.getpixel(point),expected.getpixel(point)))<=8,point

def assert_logo(image,frame):
    actual=room_pixels(image)
    expected=Image.open(ROOT/('assets/converted/siesta-%d.png'%frame)).convert('RGB')
    # The identical readable wordmark must never be mirrored by DrawPic.
    region=(88,120,234,151)
    a=actual.crop(region);b=expected.crop(region)
    assert sum(abs(x-y) for x,y in zip(a.tobytes(),b.tobytes()))/len(a.tobytes())<3

def key(k):subprocess.run(['xdotool','key','--clearmodifiers',k],env=env,check=True)
def click(x,y):
    subprocess.run(['xdotool','mousemove',str(x),str(y)],env=env,check=True)
    time.sleep(.2)
    subprocess.run(['xdotool','click','1'],env=env,check=True)

def has_response(image):
    return any(sum(145<=min(image.getpixel((x,y)))<=max(image.getpixel((x,y)))<=165
                   for x in range(140,660))>480 for y in range(150,400,4))

def wait_response(name):
    for attempt in range(40):
        image=screenshot(name)
        if has_response(image):
            # Standard SCI text dialogs discard clicks for their first 30 ticks.
            time.sleep(.8)
            return image
        time.sleep(.25)
    raise AssertionError('No response: '+name)

def wait_room(number,name):
    for attempt in range(80):
        image=screenshot(name)
        try:assert_room(image,number)
        except AssertionError:time.sleep(.25)
        else:return image
    raise AssertionError('Wrong room: '+str(number))

def assert_score(image,value):
    index=(TEMP/'game/resource.map').read_bytes()
    volume=(TEMP/'game/resource.000').read_bytes()
    font=None
    for p in range(0,len(index),3):
        kind,start=struct.unpack_from('<BH',index,p)
        if kind==255:break
        if kind!=135:continue
        end=struct.unpack_from('<H',index,p+4)[0]
        for pos in range(start,end,5):
            if struct.unpack_from('<H',index,pos)[0]==1605:
                offset=int.from_bytes(index[pos+2:pos+5],'little')*2
                _,_,_,size,method=struct.unpack_from('<BHHHH',volume,offset)
                assert method==0
                font=volume[offset+9:offset+9+size]
    assert font is not None
    expected=Image.new('1',(320,10),0);x=5
    for ch in f'LAST SHIFT   {value} / 60':
        offset=struct.unpack_from('<H',font,6+ord(ch)*2)[0]
        w,h=font[offset:offset+2];stride=(w+7)//8
        for y in range(h):
            for xx in range(w):
                if font[offset+2+y*stride+xx//8]&(128>>(xx%8)):
                    expected.putpixel((x+xx,1+y),1)
        x+=w
    actual=image.crop((80,100,720,120)).resize((320,10),Image.Resampling.NEAREST)
    assert all(bool(expected.getpixel((xx,y)))==(actual.getpixel((xx,y))==(0,0,0))
               for y in range(1,9) for xx in range(5,x)),f'Expected score {value}'

try:
    modes=sys.argv[1:] or ('complete','keyboard-skip','mouse-skip')
    for mode in modes:
        log=ROOT/'verification'/('siesta-'+mode+'.log')
        audio=ROOT/'verification'/('siesta-'+mode+'.raw')
        runenv=env.copy();runenv['SDL_DISKAUDIOFILE']=str(audio)
        with log.open('w') as output:
            game=subprocess.Popen(['/usr/games/scummvm','--config='+str(config),'last-shift'],cwd=TEMP,env=runenv,stdout=output,stderr=output)
            try:
                time.sleep(2)
                assert_logo(screenshot(mode+'-upright'),0)
                # With no window manager, a replacement SDL window does not
                # always receive keyboard focus after the prior process exits.
                window=subprocess.check_output(['xdotool','search','--onlyvisible','--pid',str(game.pid)],env=env,text=True).splitlines()[-1]
                subprocess.run(['xdotool','windowfocus','--sync',window],env=env,check=True)
                if mode=='complete':
                    time.sleep(4)
                    assert_logo(screenshot('sleeping'),5)
                    time.sleep(4)
                elif mode=='keyboard-skip':
                    key('space');time.sleep(1)
                else:
                    time.sleep(4)
                    assert_logo(screenshot('mouse-skip-sleeping'),5)
                    click(400,300);time.sleep(1)
                assert_reception(wait_response(mode+'-reception'))
                # Dismiss the story response, collect the wrench, and verify
                # the restored input handlers can actually perform an action.
                click(400,310);time.sleep(1.3)
                key('u');time.sleep(.4)
                key('u');time.sleep(.4)
                click(406,345);time.sleep(4)
                image=wait_response(mode+'-wrench')
                assert_reception(image)
                assert_score(image,10)
                results.append(mode+': logo, reception palette and actionable controls passed')
                if mode=='mouse-skip':
                    click(400,310);time.sleep(.8)
                    key('w');time.sleep(.4);click(684,446)
                    wait_room(111,'restart-workshop');time.sleep(4)
                    key('Tab');time.sleep(1.3)
                    click(263,280);time.sleep(1.3);click(544,216);time.sleep(1.3)
                    click(638,374)
                    wait_response('restart-death')
                    click(234,254)
                    # Restart must reach reception before an eight-second logo
                    # could finish, and return a fresh 0/60 status line.
                    time.sleep(2)
                    image=screenshot('restarted')
                    assert_reception(image);assert_score(image,0)
                    results.append('Death Restart bypassed logo and returned reception at 0/60')
            finally:
                key('ctrl+q')
                try:game.wait(timeout=4)
                except subprocess.TimeoutExpired:game.terminate();game.wait()
        text=log.read_text()
        assert 'ERROR:' not in text and 'sample already playing' not in text and 'not implemented' not in text,text[-3000:]
        assert audio.stat().st_size>0
        samples=array('h',audio.read_bytes()[:22050*4])
        assert max(samples)-min(samples)>500,'Startup mixer output is silent'
        print(results[-1],flush=True)
finally:
    xv.terminate();xv.wait()
report=ROOT/'verification/siesta-results.json'
if sys.argv[1:] and report.exists():
    results=list(dict.fromkeys(json.loads(report.read_text())['checks']+results))
report.write_text(json.dumps({'passed':True,'checks':results},indent=2)+'\n')
print('SIESTA startup integration checks passed.',flush=True)
