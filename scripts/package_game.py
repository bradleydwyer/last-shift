"""Build a compact SCI 1.1 distribution from library resources and our patches."""
from pathlib import Path
import struct,shutil,json
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'game'
DEST=ROOT/'dist/Last Shift'
DEST.mkdir(parents=True,exist_ok=True)
index=(GAME/'resource.map').read_bytes()
volume=(GAME/'resource.000').read_bytes()
resources={}
for p in range(0,len(index),3):
    kind,start=struct.unpack_from('<BH',index,p)
    if kind==255:break
    end=struct.unpack_from('<H',index,p+4)[0]
    for pos in range(start,end,5):
        number=struct.unpack_from('<H',index,pos)[0]
        offset=int.from_bytes(index[pos+2:pos+5],'little')*2
        t,n,compressed,size,method=struct.unpack_from('<BHHHH',volume,offset)
        # Preserve the library's compressed resources without changing their codecs.
        resources[(t&0x7f,n)]=volume[offset:offset+9+compressed]

# Remove template sample rooms, pictures, actors and audio maps.
resources={key:value for key,value in resources.items()
           if not (key[0] in (13,14,16)
                   or (key[0] in (2,17) and key[1] in (16,20,100))
                   or (key[0]==1)
                   or (key[0]==0 and key[1] in (1,2,2000,2099)))}
suffixes={'scr':(2,2),'hep':(17,2),'v56':(0,26),'p56':(1,26),'pal':(11,4),'voc':(6,2)}
for suffix,(kind,header) in suffixes.items():
    for file in GAME.glob('*.'+suffix):
        if file.stem.isdigit():
            number=int(file.stem)
            payload=file.read_bytes()[header:]
            assert len(payload)<65536
            resources[(kind,number)]=struct.pack('<BHHHH',kind|0x80,number,len(payload),len(payload),0)+payload

blob=bytearray();entries={}
for (kind,number),chunk in sorted(resources.items()):
    entries.setdefault(kind,[]).append(struct.pack('<H',number)+(len(blob)//2).to_bytes(3,'little'))
    blob+=chunk
    if len(blob)%2:blob+=b'\0'
offset=(len(entries)+1)*3
headers=bytearray();tables=bytearray()
for kind,items in sorted(entries.items()):
    headers+=struct.pack('<BH',kind|0x80,offset)
    block=b''.join(items);tables+=block;offset+=len(block)
headers+=struct.pack('<BH',255,offset)
(DEST/'resource.map').write_bytes(headers+tables)
(DEST/'resource.000').write_bytes(blob)
for file in GAME.glob('*.aud'):
    if file.stem.isdigit():shutil.copy2(file,DEST/file.name)
shutil.copy2(GAME/'VERSION',DEST/'VERSION')
for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2(ROOT/name,DEST/name)
shutil.copytree(ROOT/'LICENSES',DEST/'LICENSES',dirs_exist_ok=True)
manifest={"name":"Last Shift","version":"1.4","engine":"SCI 1.1","rooms":[110,111,112],
          "startup":{"script":120,"duration_seconds":8,"skippable":True,"audio":306},
          "resolution":[320,200],"palette_colors":256,"resources":len(resources),
          "digital_audio":sorted(int(file.stem) for file in GAME.glob('*.aud') if file.stem.isdigit())}
(ROOT/'dist/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Packaged {len(resources)} native resources and {len(manifest["digital_audio"])} sounds in {DEST}')
