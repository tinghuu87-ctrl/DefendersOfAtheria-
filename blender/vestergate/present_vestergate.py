"""Make a labelled route plan and five-page review PDF from Blender renders.

Run with ordinary Python (Pillow required), passing the builder's output folder.
This adds presentation graphics to copies; it does not alter the native scene.
"""
import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out=Path(sys.argv[1])
layout=json.loads((out/'VESTERGATE_LAYOUT.json').read_text())
anchors=json.loads((out/'CAMERA_ANNOTATIONS.json').read_text())
fonts=Path('/usr/share/fonts/truetype/dejavu')
def font(size,bold=False):
    return ImageFont.truetype(str(fonts/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size)

INK='#e7e8d6';MUTED='#a8b9b3';GOLD='#d2b46b';BG='#111f23'
COLORS={'left':'#a5dfac','centre':'#f0d48a','right':'#91d3f2'}
PAGES=[
    ('overview','Battlefield overview','Three approaches through a terraced woodland to the defended kingdom gate.'),
    ('plan','Three dirt lanes / six grass vantages','Five positions relocated from the red marks; the unmarked upper position is retained.'),
    ('arrival','Standing outside the gates','Player-height view from the spawn paving, looking outward past the defended crystal.'),
    ('gate','The defended objective','Closed wooden gates, flanking bastions, kingdom walls and the crystal courtyard.'),
    ('ridge','Ridge crossing and elevated ground','Timber bridge over a recessed stream cut; clear ground on the nearby defence shelves.'),
]

def badge(draw,xy,text,color=GOLD,radius=18):
    x,y=xy
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=BG,outline=color,width=2)
    draw.text((x,y),text,font=font(15,True),fill=INK,anchor='mm')

def projected(view,name,size):
    p=anchors[view][name]
    return (p[0]*size[0],p[1]*size[1])

plan=Image.open(out/'vestergate_plan.png').convert('RGB')
draw=ImageDraw.Draw(plan)
# Dashed colour guides are review graphics, not additional roads or in-game UI.
for lane in layout['lanes']:
    points=[]
    for x,y,z in lane['centreline']:
        points.append(((.5+x/200)*plan.width,(.5-(y-6)/150)*plan.height))
    for i in range(len(points)-1):
        if i%8<4:draw.line([points[i],points[i+1]],fill=COLORS[lane['id']],width=3)
    for t in [.30,.60,.82]:
        i=int(t*(len(points)-3));p=points[i];q=points[i+2]
        a=math.atan2(q[1]-p[1],q[0]-p[0]);r=9
        arrow=[(p[0]+r*math.cos(a),p[1]+r*math.sin(a)),
            (p[0]+r*.8*math.cos(a+2.45),p[1]+r*.8*math.sin(a+2.45)),
            (p[0]+r*.8*math.cos(a-2.45),p[1]+r*.8*math.sin(a-2.45))]
        draw.polygon(arrow,fill=COLORS[lane['id']])
for p in layout['defence_terraces']:
    badge(draw,projected('plan',p['id'],plan.size),p['id'])
for name,label,offset in [('left','WOODLAND',(-60,-45)),('centre','GATE ROAD',(-60,-45)),
                          ('right','RIDGE TRAIL',(-15,-45))]:
    x,y=projected('plan',name,plan.size);x+=offset[0];y+=offset[1]
    bounds=draw.textbbox((0,0),label,font=font(17,True));w=bounds[2]+24
    draw.rounded_rectangle((x-12,y-9,x+w,y+29),radius=7,fill=BG,outline=COLORS[name],width=2)
    draw.text((x,y),label,font=font(17,True),fill=COLORS[name])

for name,label,at in [('crystal','DEFEND THE CRYSTAL',(1080,990)),
                     ('spawn','PLAYER SPAWN',(1080,1045)),
                     ('gate','KINGDOM GATES',(480,1100))]:
    x,y=projected('plan',name,plan.size);tx,ty=at
    w=draw.textbbox((0,0),label,font=font(18,True))[2]
    draw.line([(x,y),(tx-13,ty+11)],fill=GOLD,width=2)
    draw.ellipse((x-4,y-4,x+4,y+4),fill=GOLD)
    draw.rounded_rectangle((tx-10,ty-7,tx+w+11,ty+30),radius=5,fill=BG)
    draw.text((tx,ty),label,font=font(18,True),fill=INK)
plan.save(out/'vestergate_plan_annotated.png')
if '--plan-only' in sys.argv:
    print('VESTERGATE_PLAN',out/'vestergate_plan_annotated.png')
    raise SystemExit(0)

pages=[]
for index,(key,title,caption) in enumerate(PAGES,1):
    canvas=Image.new('RGB',(1800,1510),BG);d=ImageDraw.Draw(canvas)
    d.text((82,28),'VESTERGATE',font=font(35,True),fill=INK)
    d.text((1718,41),f'{index:02d} / WOODLAND BLOCKOUT',font=font(17,True),fill=GOLD,anchor='ra')
    d.text((83,80),title.upper(),font=font(19,True),fill=MUTED)
    source=plan if key=='plan' else Image.open(out/f'vestergate_{key}.png').convert('RGB')
    canvas.paste(source.resize((1600,1200),Image.Resampling.LANCZOS),(100,124))
    d.line((82,1351,1718,1351),fill='#385054',width=2)
    d.text((83,1370),caption,font=font(19),fill=INK)
    if key=='plan':
        d.text((83,1409),'D1–D6: clear grass ledges for jump access. Crystal-side positions D7 and D8 removed.',font=font(18),fill=MUTED)
        lengths=layout['lane_lengths_metres']
        d.text((83,1443),f'Authored route lengths: woodland {lengths["left"]:.0f} m / gate road {lengths["centre"]:.0f} m / ridge {lengths["right"]:.0f} m. Combat balance pending.',font=font(17),fill=MUTED)
    else:
        d.text((83,1410),'Editable terrain, lane surfaces, tree masses, defence shelves and architectural landmarks.',font=font(18),fill=MUTED)
        d.text((83,1443),'Layout study • metre-scale authoring • no enemy navigation or Roblox collision setup yet',font=font(17),fill=MUTED)
    canvas.save(out/f'vestergate_review_{key}.png')
    pages.append(canvas)
pages[0].save(out/'vestergate_blockout_views.pdf',save_all=True,append_images=pages[1:],resolution=150)
print('VESTERGATE_PRESENTATION',out/'vestergate_blockout_views.pdf')
