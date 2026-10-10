"""Compose and render the original SIESTA sting using the builder's GM synth.

Run inside three-room-sci-builder: python3 /work/scripts/build_siesta_audio.py.
The MIDI and WAV are original source assets. No Sierra recording is used.
FluidSynth and its installed sound bank render the source; only the resulting
audio, rather than that sound bank, ships with the game.
"""
from pathlib import Path
import ctypes as C
import ctypes.util
import math
import random
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/source'
RATE = 22050
DURATION = 8.0
events = []

def event(t, *data):
    events.append((t,bytes(data)))

def note(channel, pitch, t, duration, velocity):
    event(t,0x90|channel,pitch,velocity)
    event(t+duration,0x80|channel,pitch,0)

for channel,program in [(0,56),(1,60),(2,48),(3,57),(4,71)]:
    event(0,0xc0|channel,program)
    event(0,0xb0|channel,7,100)
    event(0,0xb0|channel,10,64)

# A fresh, short C-major brass phrase, followed by a decidedly unheroic fall.
for pitch,t,duration in [(72,.12,.24),(76,.48,.24),(74,.84,.24),
                         (79,1.20,.65),(84,2.02,.78)]:
    note(0,pitch,t,duration,100)
for pitches,t,duration in [([48,55,64],.12,.88),([53,60,69],1.15,.7),
                          ([48,55,67],2.02,.8)]:
    for pitch in pitches:
        note(1,pitch,t,duration,72)
        note(2,pitch+12,t,duration,46)
note(9,49,2.02,.2,64)

# Configure a twelve-semitone bend on the trombone, then let it sag with the art.
for controller,value in [(101,0),(100,0),(6,12),(38,0),(101,127),(100,127)]:
    event(2.9,0xb3,controller,value)
note(3,55,3.0,1.45,90)
for i in range(45):
    v=round(8192*(1-i/44))
    event(3.0+i/44*1.35,0xe3,v&127,v>>7)
    event(3.0+i/44*1.35,0xb3,11,round(105*(1-i/44*.8)))
note(4,43,4.43,.58,43)
note(4,42,5.12,.32,25)
events.sort(key=lambda e:e[0])

def vlq(n):
    result=[n&127]
    while (n:=n>>7):result.insert(0,128|(n&127))
    return bytes(result)

track=bytearray(b'\x00\xff\x51\x03\x07\xa1\x20')
label=b'SIESTA - original fanfare and wheeze'
track+=b'\x00\xff\x03'+vlq(len(label))+label
previous=0
for t,data in events:
    tick=round(t*960)
    track+=vlq(tick-previous)+data
    previous=tick
track+=vlq(round(DURATION*960)-previous)+b'\xff\x2f\x00'
(OUT/'siesta-fanfare.mid').write_bytes(b'MThd'+struct.pack('>IHHH',6,0,1,480)+
                                     b'MTrk'+struct.pack('>I',len(track))+track)

lib=C.CDLL(ctypes.util.find_library('fluidsynth'))
def api(name,restype,*args):
    f=getattr(lib,name);f.restype=restype;f.argtypes=list(args);return f
ptr=C.c_void_p;integer=C.c_int
settings=api('new_fluid_settings',ptr)()
api('fluid_settings_setnum',integer,ptr,C.c_char_p,C.c_double)(settings,b'synth.sample-rate',RATE)
api('fluid_settings_setnum',integer,ptr,C.c_char_p,C.c_double)(settings,b'synth.gain',.4)
synth=api('new_fluid_synth',ptr,ptr)(settings)
sf=api('fluid_synth_sfload',integer,ptr,C.c_char_p,integer)(synth,b'/usr/share/sounds/sf2/TimGM6mb.sf2',1)
assert sf>=0,'Builder General MIDI sound bank unavailable'
write=api('fluid_synth_write_s16',integer,ptr,integer,ptr,integer,integer,ptr,integer,integer)
noteon=api('fluid_synth_noteon',integer,ptr,integer,integer,integer)
noteoff=api('fluid_synth_noteoff',integer,ptr,integer,integer)
program=api('fluid_synth_program_change',integer,ptr,integer,integer)
control=api('fluid_synth_cc',integer,ptr,integer,integer,integer)
bend=api('fluid_synth_pitch_bend',integer,ptr,integer,integer)
audio=[]
cursor=0
def render(until):
    global cursor
    stop=round(until*RATE)
    count=stop-cursor
    if count:
        buffer=(C.c_int16*(count*2))()
        assert write(synth,count,buffer,0,2,buffer,1,2)==0
        audio.extend((buffer[i*2]+buffer[i*2+1])/2 for i in range(count))
    cursor=stop
for t,data in events:
    render(t)
    channel=data[0]&15;kind=data[0]&240
    if kind==0x90:noteon(synth,channel,data[1],data[2])
    elif kind==0x80:noteoff(synth,channel,data[1])
    elif kind==0xc0:program(synth,channel,data[1])
    elif kind==0xb0:control(synth,channel,data[1],data[2])
    elif kind==0xe0:bend(synth,channel,data[1]|data[2]<<7)
render(DURATION)
# Deterministic breath noise completes the joke; the final tail fades to silence.
rng=random.Random(306)
noise=0.0
for i in range(len(audio)):
    t=i/RATE
    noise=.78*noise+.22*rng.uniform(-1,1)
    if 3.7<t<5.6:
        envelope=math.sin(math.pi*(t-3.7)/1.9)**2
        pulse=.7+.3*math.sin(t*2*math.pi*7)
        audio[i]+=noise*2300*envelope*pulse
    if t>7.0:audio[i]*=max(0,(8-t))
gain=min(1.0,28000/max(abs(x) for x in audio))
pcm=b''.join(struct.pack('<h',round(x*gain)) for x in audio)
with wave.open(str(OUT/'siesta-fanfare.wav'),'wb') as wav:
    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(pcm)
api('delete_fluid_synth',None,ptr)(synth)
api('delete_fluid_settings',None,ptr)(settings)
print('Composed original eight-second SIESTA MIDI and rendered source WAV.')
