"""Encode original assets as real SCI 1.1 PIC, VIEW, PAL and SOL resources."""
from pathlib import Path
import struct, math, wave
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'game'
OUT = ROOT / 'assets/converted'
OUT.mkdir(parents=True, exist_ok=True)
pack = struct.pack

def template_resource(kind, number):
    index = (GAME / 'resource.map').read_bytes()
    volume = (GAME / 'resource.000').read_bytes()
    for p in range(0, len(index), 3):
        t, start = struct.unpack_from('<BH', index, p)
        if t == 255: break
        end = struct.unpack_from('<H', index, p+4)[0]
        if t != kind | 0x80: continue
        for pos in range(start, end, 5):
            n = struct.unpack_from('<H', index, pos)[0]
            offset = int.from_bytes(index[pos+2:pos+5], 'little') * 2
            if n == number:
                _, _, compressed, size, method = struct.unpack_from('<BHHHH', volume, offset)
                assert method == 0
                return volume[offset+9:offset+9+size]
    raise ValueError((kind, number))

original_palette = template_resource(11, 999)
base_colors = [tuple(original_palette[37+4*i+1:37+4*i+4]) for i in range(64)]
# Keep the template's UI colour range stable. The new art uses the remaining colours.
sheet = Image.open(ROOT / 'assets/source/rooms.png').convert('RGB')
rooms = [sheet.crop((i*sheet.width//3, 0, (i+1)*sheet.width//3, 530)).resize((320,190), Image.Resampling.LANCZOS) for i in range(3)]
combined = Image.new('RGB', (960,190))
for i, im in enumerate(rooms): combined.paste(im, (i*320,0))
quant = combined.quantize(colors=191, method=Image.Quantize.MEDIANCUT)
room_colors = [tuple(quant.getpalette()[i*3:i*3+3]) for i in range(191)]
colors = base_colors + room_colors + [(255,255,255)]

def palette(palette_colors=None):
    b = bytearray(37)
    b[0] = 14
    struct.pack_into('<H',b,10,1)
    struct.pack_into('<H',b,13,1046)
    struct.pack_into('<I',b,15,0x00393939)
    struct.pack_into('<H',b,29,256)
    b[31] = 3
    return bytes(b) + b''.join(bytes((1,*c)) for c in (palette_colors or colors))

def rle(image):
    pixels = image.tobytes()
    controls, literals = bytearray(), bytearray()
    i=0
    while i<len(pixels):
        run=1
        while i+run<len(pixels) and pixels[i+run]==pixels[i] and run<63:
            run+=1
        if pixels[i]==255 or run>=3:
            controls.append((0xc0 if pixels[i]==255 else 0x80)|run)
            if pixels[i]!=255: literals.append(pixels[i])
            i+=run
        else:
            start=i
            i+=run
            while i<len(pixels) and i-start<63:
                if pixels[i]==255 or (i+2<len(pixels) and pixels[i]==pixels[i+1]==pixels[i+2]):break
                i+=1
            count=min(63,i-start)
            i=start+count
            controls.append(count)
            literals.extend(pixels[start:i])
    return bytes(controls),bytes(literals)

def cel_header(im, control, literal, control_offset, literal_offset, palette_offset=0, displacement=(0,0)):
    return pack('<HHhhBBBBIIIIII', im.width,im.height,*displacement,255,10,0,0,
                len(control)+len(literal),len(control),palette_offset,control_offset,literal_offset,0)

def write_patch(kind, number, payload, name):
    suffix={0:'v56',1:'p56',11:'pal'}[kind]
    # SCI 1.1's loose graphics resources have an extra patch wrapper.
    header_size=26 if kind in (0,1) else 4
    (GAME / f'{number}.{suffix}').write_bytes(bytes((kind|0x80,))+bytes(header_size-1)+payload)

def picture(im, number, palette_colors=None):
    pal = palette(palette_colors)
    c,l = rle(im)
    cel_offset = 40+28+4
    rle_offset = cel_offset+42
    literal_offset = rle_offset+len(c)
    pal_offset = literal_offset+len(l)
    vector_offset = pal_offset+len(pal)
    vectors = b'\xff'
    header = pack('<HBBBBHHHIIIIIII',38,16,14,1,0,160,55536,70,
                  len(vectors),vector_offset,0,0,pal_offset,cel_offset,0)
    bands = pack('<14H',*range(42,182,10))
    cel = cel_header(im,c,l,rle_offset,literal_offset,pal_offset)+pack('<HI',0x401,len(c)+len(l))
    write_patch(1,number,header+bands+b'\0'*4+cel+c+l+pal+vectors,'pic')

for i in range(3):
    im = quant.crop((i*320,0,(i+1)*320,190))
    im.putdata(bytes(p+64 for p in im.tobytes()))
    im.putpalette([v for color in colors for v in color])
    im.save(OUT / f'room-{110+i}.png')
    picture(im,110+i)
write_patch(11,999,palette(),'pal')

# The startup gets its own gold palette; each room reinstates its usual palette.
# Use one crop and one scale for all generated poses to keep the seal stationary.
siesta_source = Image.open(ROOT/'assets/source/siesta-logo-poses.png').convert('RGB')
siesta_tiles = [siesta_source.crop((col*siesta_source.width//2,row*siesta_source.height//3,
                                  (col+1)*siesta_source.width//2,(row+1)*siesta_source.height//3))
                for row in range(3) for col in range(2)]
bounds = [im.convert('L').point(lambda v:255 if v>40 else 0).getbbox() for im in siesta_tiles]
crop = (min(b[0] for b in bounds),min(b[1] for b in bounds),
        max(b[2] for b in bounds),max(b[3] for b in bounds))
scale = 133/(crop[3]-crop[1])
size = (round((crop[2]-crop[0])*scale),133)
siesta_frames = []
for im in siesta_tiles:
    frame = Image.new('RGB',(320,190))
    frame.paste(im.crop(crop).resize(size,Image.Resampling.LANCZOS),((320-size[0])//2,16))
    siesta_frames.append(frame)
siesta_sheet = Image.new('RGB',(320*6,190))
for i,im in enumerate(siesta_frames):siesta_sheet.paste(im,(320*i,0))
siesta_quant = siesta_sheet.quantize(colors=191,method=Image.Quantize.MEDIANCUT)
siesta_colors = base_colors+[tuple(siesta_quant.getpalette()[i*3:i*3+3]) for i in range(191)]+[(255,255,255)]
for i in range(6):
    im = siesta_quant.crop((320*i,0,320*(i+1),190))
    im.putdata(bytes(p+64 for p in im.tobytes()))
    im.putpalette([v for color in siesta_colors for v in color])
    im.save(OUT/f'siesta-{i}.png')
    picture(im,120+i,siesta_colors)

def view(loops, number, mirror_loops=None, cursor_hotspot=None):
    images = [im for loop in loops for im in loop]
    count = len(images)
    size = 18+16*len(loops)+36*count
    # Directional loops often share identical poses. Keep independent cel
    # headers but share pixel packets so SCI's 16-bit resource size stays valid.
    packets, identities, unique = [], [], {}
    for im in images:
        key = (im.size, im.tobytes())
        if key not in unique:
            unique[key] = len(packets)
            packets.append(rle(im))
        identities.append(unique[key])
    rle_size = sum(len(c) for c,l in packets)
    header = pack('<HBBBBHIBBHH',16,len(loops),0x40 if number in (0,903,912) else 1,1,0,count,0,16,36,0,0)
    offset = 18+len(loops)*16
    loop_headers = b''
    for loop_number, loop in enumerate(loops):
        mirror_source=(mirror_loops or {}).get(loop_number,255)
        loop_headers += pack('<BBBBIII',mirror_source,int(mirror_source!=255),len(loop),255,0x03ffffff,0,offset)
        offset += 36*len(loop)
    c_offset,l_offset = size,size+rle_size
    pointers,cs,ls = [],b'',b''
    for c,l in packets:
        pointers.append((c_offset,l_offset))
        cs+=c;ls+=l;c_offset+=len(c);l_offset+=len(l)
    headers=b''
    for im,identity in zip(images,identities):
        c,l=packets[identity]
        displacement=(im.width//2-cursor_hotspot[0], im.height-1-cursor_hotspot[1]) if cursor_hotspot else (0,0)
        headers+=cel_header(im,c,l,*pointers[identity],displacement=displacement)
    payload=header+loop_headers+headers+cs+ls
    assert len(payload)<65536, (number,len(payload))
    write_patch(0,number,payload,'view')

# Only the camera-near jamb occludes a crossing actor. The opposite jamb,
# lintel, corridor and threshold stay behind the actor. Follow each painted
# front edge down to its real floor contact instead of cutting off at y146.
near_jambs = {
    110: [[(318,0),(319,0),(319,174),(313,169),(313,54),(318,51)]],
    111: [[(0,0),(5,0),(5,159),(0,164)],
          [(318,0),(319,0),(319,179),(318,178)]],
    112: [[(0,0),(5,0),(6,158),(0,165)]],
}
for room_number, polygons in near_jambs.items():
    background=Image.open(OUT/f'room-{room_number}.png')
    silhouette=Image.new('1',(320,190))
    brush=ImageDraw.Draw(silhouette)
    for polygon in polygons:
        brush.polygon(polygon,fill=1)
    mask=Image.new('P',(320,190),255)
    mask.putpalette([v for c in colors for v in c])
    mask.paste(background,(0,0),silhouette)
    mask.save(OUT/f'near-jamb-{room_number}.png')
    view([[mask]],904+room_number-110)

def closest(rgb):
    return min(range(64), key=lambda i: sum((a-b)**2 for a,b in zip(colors[i],rgb)))

# Use one physical scale for all six phases; never stretch individual poses.
source = Image.open(ROOT / 'assets/source/worker-walk-v5.png').convert('RGBA')
reference = Image.new('P', (1,1))
reference.putpalette([v for color in colors for v in color])
walk_tiles=[]
for row in range(3):
    band=source.crop((0,row*source.height//3,source.width,(row+1)*source.height//3))
    alpha=band.getchannel('A')
    # Generated poses exceed equal-cell boundaries. Split at transparent gutters
    # so contact-frame boots remain intact.
    occupied=[alpha.crop((x,0,x+1,alpha.height)).getextrema()[1]>=110 for x in range(alpha.width)]
    starts=[x for x in range(alpha.width) if occupied[x] and (x==0 or not occupied[x-1])]
    ends=[x+1 for x in range(alpha.width) if occupied[x] and (x==alpha.width-1 or not occupied[x+1])]
    assert len(starts)==len(ends)==8, (row,starts,ends)
    poses=[]
    for left,right in zip(starts,ends):
        tile=band.crop((left,0,right,band.height))
        bounds=tile.getchannel('A').point(lambda v:255 if v>=110 else 0).getbbox()
        poses.append(tile.crop(bounds))
    walk_tiles.append(poses)
body_heights=sorted(tile.height for row in walk_tiles for tile in row)
walk_scale=76/body_heights[len(body_heights)//2]
frames=[]
for row,tiles in enumerate(walk_tiles):
    # Frontal sheet repeats the leading leg. Mirroring the second half creates
    # an alternating gait while preserving the original painted poses.
    if row in (1,2):
        tiles=tiles[:4]+[tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for tile in tiles[:4]]
    poses=[]
    for tile in tiles:
        tile=tile.resize((round(tile.width*walk_scale),round(tile.height*walk_scale)),Image.Resampling.LANCZOS)
        # Anchor the head, avoiding lateral shifts from swinging arms or legs.
        torso=tile.getchannel('A').crop((0,round(tile.height*.06),tile.width,round(tile.height*.24)))
        points=[(x,a) for y in range(torso.height) for x in range(torso.width)
                if (a:=torso.getpixel((x,y)))>=110]
        anchor=round(sum(x*a for x,a in points)/sum(a for x,a in points))
        rgba=Image.new('RGBA',(68,80))
        rgba.paste(tile,(34-anchor,79-tile.height))
        indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
        indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
        poses.append(indexed)
    frames.append(poses)
east,south,north=frames
west=[im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for im in east]
# SCI headings: E,W,S,N,SE,SW,NE,NW.
worker_loops=[east,west,south,north,east,west,east,west]
view(worker_loops,0)
preview=Image.new('RGB',(68*8,80*8),(22,23,30))
for direction,loop in enumerate(worker_loops):
    for phase,im in enumerate(loop):
        preview.paste(im.convert('RGB'),(direction*68,phase*80))
preview.resize((1632,1920),Image.Resampling.NEAREST).save(OUT/'worker-sheet.png')

# Six painted electrical-accident frames, all using one physical scale.
death_source=Image.open(ROOT/'assets/source/worker-death-transparent.png').convert('RGBA')
death_tiles=[]
for row in range(2):
    for col in range(3):
        tile=death_source.crop((col*death_source.width//3,row*death_source.height//2,
                               (col+1)*death_source.width//3,(row+1)*death_source.height//2))
        bounds=tile.getchannel('A').point(lambda v:255 if v>=110 else 0).getbbox()
        death_tiles.append(tile.crop(bounds))
death_scale=76/death_tiles[0].height
death_frames=[]
for tile in death_tiles:
    tile=tile.resize((round(tile.width*death_scale),round(tile.height*death_scale)),Image.Resampling.LANCZOS)
    rgba=Image.new('RGBA',(104,84))
    rgba.paste(tile,((104-tile.width)//2,83-tile.height))
    indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
    indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
    death_frames.append(indexed)
view([death_frames],903)
preview=Image.new('RGB',(104*3,84*2),(22,23,30))
for i,im in enumerate(death_frames):preview.paste(im.convert('RGB'),((i%3)*104,(i//3)*84))
preview.resize((1248,672),Image.Resampling.NEAREST).save(OUT/'death-sheet.png')

# Consistent generated painted inventory art, including cursor and selected loops.
for i,name in enumerate(('wrench','cell','card')):
    rgba=Image.open(ROOT/f'assets/source/inventory-{name}.png').convert('RGBA')
    indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
    indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<128 else 0))
    view([[indexed] for _ in range(3)],900+i)
    # Separate cursor views preserve inventory drawing while their cel offsets
    # make the visible wrench head/item centre the actual click point. This
    # uses the normal three-argument cursor call across ScummVM versions.
    view([[indexed]],914+i,cursor_hotspot=(6,4) if i==0 else (15,12))

# Opening toolbox: fixed base position and scale across closed/half/open poses.
source=Image.open(ROOT/'assets/source/toolbox-opening.png').convert('RGBA')
chest_tiles=[]
for col in range(3):
    tile=source.crop((col*source.width//3,0,(col+1)*source.width//3,source.height))
    bounds=tile.getchannel('A').point(lambda v:255 if v>=110 else 0).getbbox()
    chest_tiles.append(tile.crop(bounds))
chest_scale=min(48/max(im.width for im in chest_tiles),28/max(im.height for im in chest_tiles))
chest_frames=[]
for tile in chest_tiles:
    tile=tile.resize((round(tile.width*chest_scale),round(tile.height*chest_scale)),Image.Resampling.LANCZOS)
    rgba=Image.new('RGBA',(52,30))
    rgba.paste(tile,((52-tile.width)//2,29-tile.height))
    indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
    indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
    chest_frames.append(indexed)
view([chest_frames],907)

# Only the cell's small footprint changes; all other room pixels stay intact.
empty_bench=Image.open(ROOT/'assets/source/workshop-empty-bench.png').convert('RGB').resize((320,190),Image.Resampling.LANCZOS)
bench_patch=empty_bench.crop((255,96,297,119)).quantize(palette=reference,dither=Image.Dither.NONE)
view([[bench_patch]],909)

empty_chest=Image.open(ROOT/'assets/source/reception-empty-bench.png').convert('RGB').resize((320,190),Image.Resampling.LANCZOS)
chest_patch=empty_chest.crop((137,94,189,123)).quantize(palette=reference,dither=Image.Dither.NONE)
view([[chest_patch]],910)

source=Image.open(ROOT/'assets/source/generator-glow.png').convert('RGBA')
reactor_frames=[]
for row in range(2):
    for col in range(2):
        tile=source.crop((col*source.width//2,row*source.height//2,(col+1)*source.width//2,(row+1)*source.height//2))
        bounds=tile.getchannel('A').point(lambda v:255 if v>=110 else 0).getbbox()
        tile=tile.crop(bounds)
        scale=min(24/tile.width,24/tile.height)
        tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.LANCZOS)
        rgba=Image.new('RGBA',(26,26))
        rgba.paste(tile,((26-tile.width)//2,(26-tile.height)//2))
        indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
        indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
        reactor_frames.append(indexed)
view([reactor_frames],911)

# The cabin occupant remains visible while the boarding response is shown.
source=Image.open(ROOT/'assets/source/worker-seated.png').convert('RGBA')
bounds=source.getchannel('A').point(lambda v:255 if v>=110 else 0).getbbox()
tile=source.crop(bounds)
scale=min(38/tile.width,48/tile.height)
tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.LANCZOS)
rgba=Image.new('RGBA',(40,50))
rgba.paste(tile,((40-tile.width)//2,49-tile.height))
indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
view([[indexed],[indexed]],912,{1:0})
indexed.save(OUT/'worker-seated.png')

# A blast changes only the workshop's right bench and wall; its camera and
# walkable floor match the clean room. All effects use the existing palette.
damage=Image.open(ROOT/'assets/source/workshop-damaged-native.png').convert('RGB')
assert damage.size==(320,190)
damaged_indexed=damage.quantize(palette=reference,dither=Image.Dither.NONE)
picture(damaged_indexed,113)
damaged_indexed.save(OUT/'room-113.png')
blast_loops=[]
for effect in ('burst','smoke'):
    frames=[]
    for phase in range(3):
        rgba=Image.open(ROOT/f'assets/source/cell-{effect}-{phase}.png').convert('RGBA')
        indexed=rgba.convert('RGB').quantize(palette=reference,dither=Image.Dither.NONE)
        indexed.paste(255,mask=rgba.getchannel('A').point(lambda v:255 if v<110 else 0))
        frames.append(indexed)
    blast_loops.append(frames)
view(blast_loops,913)

def sound(number,seconds,fn):
    rate=11025
    samples=bytes(max(0,min(255,int(128+fn(t/rate)*90))) for t in range(int(seconds*rate)))
    sol=pack('<BB4sHBI',0x8d,11,b'SOL\0',rate,0,len(samples))+samples
    (GAME / f'{number}.aud').write_bytes(sol)
    with wave.open(str(OUT/f'sound-{number}.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(1);wav.setframerate(rate);wav.writeframes(samples)

sound(300,5,lambda t: .12*math.sin(t*2*math.pi*55)+.05*math.sin(t*2*math.pi*82.4)+.025*math.sin(t*2*math.pi*165)*(1+math.sin(t*2)))
sound(301,.5,lambda t: .4*math.sin(t*2*math.pi*(440 if t<.16 else 660 if t<.32 else 880))*math.exp(-t*4))
sound(302,1.5,lambda t: .22*math.sin(t*2*math.pi*(90+40*t))*(1-t/1.5)+.05*math.sin(t*2*math.pi*330))
sound(303,2.5,lambda t: .35*math.sin(t*2*math.pi*[261.6,329.6,392,523.2][min(3,int(t*2))])*max(0,1-(t%.5)*2))
sound(304,1.8,lambda t: (.25*math.sin(t*2*math.pi*95)+.2*math.sin(t*2*math.pi*1400)*math.sin(t*2*math.pi*41))*max(0,1-t/1.8))
sound(305,1.4,lambda t: .38*math.sin(t*2*math.pi*(80-25*t))*math.exp(-t*5)+.38*math.sin(math.sin(t*12345)*54321)*math.exp(-t*7))
# Rendered from our original MIDI composition, not the SQ4 reference music.
with wave.open(str(ROOT/'assets/source/siesta-fanfare.wav'),'rb') as wav:
    assert wav.getnchannels()==1 and wav.getsampwidth()==2
    rate=wav.getframerate()
    pcm=wav.readframes(wav.getnframes())
samples=bytes(max(0,min(255,(v>>8)+128)) for (v,) in struct.iter_unpack('<h',pcm))
(GAME/'306.aud').write_bytes(pack('<BB4sHBI',0x8d,11,b'SOL\0',rate,0,len(samples))+samples)
with wave.open(str(OUT/'sound-306.wav'),'wb') as wav:
    wav.setnchannels(1);wav.setsampwidth(1);wav.setframerate(rate);wav.writeframes(samples)
print('Encoded 3 rooms, SIESTA intro, painted worker, death animations, inventory and 7 digital sounds.')
