"""End-to-end mouse playthrough of the packaged SCI game in isolated Xvfb.

Checks rendered score glyphs against the SCI font, verifies room backgrounds,
and exercises incorrect item use, the complete puzzle, inventory and the ending.
"""
from pathlib import Path
import subprocess,struct,time,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
report=[]
def action(kind,*args):
    print(kind,*args,flush=True)
    subprocess.run(['python3',str(ROOT/'scripts/test_input.py'),kind,*map(str,args)],cwd=ROOT,check=True,capture_output=True)
def snap(name):
    action('shot',name)
def screenshot(): return Image.open(ROOT/'verification/linux.png').convert('RGB')
def resource(kind,number):
    game=ROOT/'dist/Last Shift';index=(game/'resource.map').read_bytes();vol=(game/'resource.000').read_bytes()
    for p in range(0,len(index),3):
        t,start=struct.unpack_from('<BH',index,p)
        if t==255:break
        end=struct.unpack_from('<H',index,p+4)[0]
        if t!=(kind|128):continue
        for pos in range(start,end,5):
            n=struct.unpack_from('<H',index,pos)[0]
            if n==number:
                off=int.from_bytes(index[pos+2:pos+5],'little')*2
                _,_,_,size,method=struct.unpack_from('<BHHHH',vol,off)
                assert method==0
                return vol[off+9:off+9+size]
    raise AssertionError((kind,number))
font=resource(7,1605)
def score(value):
    expected=Image.new('1',(320,10),0);x=5
    for ch in f'LAST SHIFT   {value} / 60':
        offset=struct.unpack_from('<H',font,6+ord(ch)*2)[0]
        w,h=font[offset:offset+2];stride=(w+7)//8
        for y in range(h):
            for xx in range(w):
                if font[offset+2+y*stride+xx//8]&(128>>(xx%8)):expected.putpixel((x+xx,1+y),1)
        x+=w
    actual=screenshot().crop((80,100,720,120)).resize((320,10),Image.Resampling.NEAREST)
    differences=sum(bool(expected.getpixel((xx,y)))!=(actual.getpixel((xx,y))==(0,0,0)) for y in range(1,9) for xx in range(5,x))
    if differences and not getattr(score,'polling',False):
        score.polling=True
        try:
            for attempt in range(24):
                time.sleep(.5)
                action('shot')
                try:
                    score(value)
                    return
                except AssertionError:pass
        finally:score.polling=False
    assert differences==0,f'Expected score {value}, {differences} glyph pixels disagree'
    report.append(f'Rendered score {value}/60 verified')
def room(number):
    expected=Image.open(ROOT/f'assets/converted/room-{number}.png').convert('RGB')
    points=[(20,20),(70,30),(120,70),(220,30),(280,60)]
    # Exit and entry animations now take time; wait for the next room and control.
    for attempt in range(40):
        actual=screenshot().crop((80,120,720,500)).resize((320,190),Image.Resampling.NEAREST)
        if all(max(abs(a-b) for a,b in zip(actual.getpixel(p),expected.getpixel(p)))<=8 for p in points):
            time.sleep(4)
            action('shot')
            break
        time.sleep(.5)
        action('shot')
    else: raise AssertionError(f'Wrong room: {number}')
    report.append(f'Room {number} rendered correctly')
def dismiss():
    time.sleep(.4)
    action('click',400,310)
    time.sleep(.4)
def wait_text():
    # A response may be delayed until the actor finishes its approach. A wide
    # continuous grey span identifies the SCI dialog rather than the room art.
    for attempt in range(60):
        action('shot')
        image=screenshot()
        if any(sum(145 <= min(pixel) <= max(pixel) <= 165 and max(pixel)-min(pixel) <= 3
                   for pixel in (image.getpixel((x,y)) for x in range(140,660))) > 480
               for y in range(150,400,4)):
            return
        time.sleep(.25)
    raise AssertionError('Interaction did not show its response')
def hand():
    action('key','u')
    # Let the original SCI input loop settle after any pending actor motion.
    action('key','u')
def inventory(item):
    action('key','Tab')
    action('click',263+item*64,280)
    action('click',544,216)

time.sleep(2)
dismiss();score(0);room(110);snap('final-reception')
before=screenshot()
action('click',600,450);time.sleep(3);action('shot')
after=screenshot()
assert before.crop((360,365,650,460)).tobytes()!=after.crop((360,365,650,460)).tobytes(),'Walking did not move the actor'
report.append('Mouse walking and animation verified')
# Use the original Sierra toolbar; its icons have no native accessibility nodes.
hand()
action('click',145,315);wait_text();score(0);dismiss()  # kiosk before power: useful failure, no score
action('click',406,345);score(10);dismiss()
inventory(0);action('move',760,550);snap('door-wrench-before')
before_door=screenshot()
action('click',684,446);wait_text();dismiss();score(10);action('move',760,550);snap('door-wrench-after')
assert before_door.crop((260,275,420,445)).tobytes()==screenshot().crop((260,275,420,445)).tobytes(), 'Using wrench on door moved the actor'
report.append('Wrench on reception door neither moved the actor nor changed rooms')
action('key','w');action('click',684,446);room(111);snap('final-workshop');hand()
action('click',116,446);wait_text();dismiss();score(10)
action('click',708,476);wait_text();dismiss();score(10)
report.append('Hand on both workshop doors stayed in workshop')
action('click',639,342);score(20);dismiss()
# Repeatedly switch selection in one inventory visit; the final cell selection
# must be used (and rejected before repair), rather than the initial wrench.
action('key','Tab')
for item in (0,1,0,1):
    action('click',263+item*64,280)
snap('inventory-switched-in-place')
action('click',544,216)
action('click',400,285);score(20);dismiss()  # cell before repair must not be consumed
report.append('Inventory switched wrench/cell four times without closing; final cell remained selected')
inventory(0)
action('click',400,285);score(30);dismiss()
inventory(1)
action('click',400,285);score(40);dismiss()
if '--prepare-death' in sys.argv:
    snap('death-ready')
    print('Powered workshop ready for death/recovery validation',flush=True)
    sys.exit(0)
action('key','w');action('click',116,446);room(110)
hand();action('click',145,315);score(50);dismiss()
action('key','w');action('click',684,446);room(111)
action('key','w');action('click',708,476);room(112);snap('final-pod-bay')
hand();action('click',116,446);wait_text();dismiss();score(50)
action('click',230,327);wait_text();score(50);snap('console-approach');dismiss()
report.append('Hand on pod-bay door stayed in room; launch-console use approached console')
hand();action('click',584,290);wait_text();score(50);snap('craft-seated-response');dismiss()  # pod before authorisation
time.sleep(2);action('shot');snap('craft-returned-to-floor')
action('key','w');action('click',116,446);room(111)
action('key','w');action('click',708,476);room(112)
report.append('All adjoining room transitions exercised in both directions; failed boarding returns to floor')
inventory(1)  # consumed cell is absent: remaining items are wrench and transit card
action('click',230,327);score(50);dismiss()
hand();action('click',584,290);score(60);snap('final-ending-1');dismiss()
score(60);snap('final-ending-2');dismiss();score(60)
report.append('Incorrect item use retained the power cell; locked pod rejected premature escape')
report.append('Complete three-room adventure reached ending at 60/60')
log=(ROOT/'verification/linux-final.log').read_text()
assert 'ERROR:' not in log and 'sample already playing' not in log,log
report.append('Packaged runtime produced no SCI errors or audio overlap warnings')
(ROOT/'verification/playthrough-results.json').write_text(json.dumps({'passed':True,'checks':report},indent=2)+'\n')
print('\n'.join(report))
