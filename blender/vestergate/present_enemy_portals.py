"""Create a portal comparison sheet and four-page PDF (ordinary Python/Pillow)."""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw, ImageFont

out=Path(sys.argv[1]);font_dir=Path('/usr/share/fonts/truetype/dejavu')
def font(n,bold=False):
    return ImageFont.truetype(str(font_dir/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),n)
background='#10101c';ink='#eeecf7';muted='#aaa4bf';accent='#ca99ff'
layout=json.loads((out/'PORTAL_LAYOUT.json').read_text())
plan=Image.open(out/'enemy_portals_plan.png').convert('RGB')
d=ImageDraw.Draw(plan)
for i,portal in enumerate(layout['portals'],1):
    x,y,z=portal['position'];px=(.5+x/200)*plan.width;py=(.5-(y-6)/150)*plan.height
    label=f'P{i}  '+portal['design'].upper();w=d.textbbox((0,0),label,font=font(17,True))[2]
    d.line((px,py,px,py-26),fill=accent,width=2)
    d.rounded_rectangle((px-w/2-10,py-62,px+w/2+10,py-27),radius=6,fill=background,outline=accent,width=2)
    d.text((px,py-44),label,anchor='mm',font=font(17,True),fill=ink)
plan.save(out/'enemy_portals_plan_annotated.png')
pages=[]
views=[('designs','Three violet vortex designs','Animated energy layers, broken obsidian rims, rune arcs and golden sparks.'),
    ('portal','Facing the incoming lane','The gate-road portal faces down its trail, with grounded spawn markers and a clear central opening.'),
    ('overview','Vestergate / enemy entrances','One portal is placed at the beginning of each of the three dirt approaches.'),
    ('plan','Three lane origins','P1: woodland / P2: gate road / P3: ridge. The revised six grass vantages remain in place.')]
for index,(key,title,caption) in enumerate(views,1):
    im=plan if key=='plan' else Image.open(out/f'enemy_portals_{key}.png').convert('RGB')
    canvas=Image.new('RGB',(1800,im.height+350),background);d=ImageDraw.Draw(canvas)
    d.text((82,28),'VESTERGATE / ENEMY PORTALS',font=font(30,True),fill=ink)
    d.text((1718,38),f'{index:02d} / DESIGN STUDY',anchor='ra',font=font(17,True),fill=accent)
    d.text((83,79),title.upper(),font=font(18,True),fill=muted)
    canvas.paste(im,(100,124));bottom=im.height+154
    d.line((82,bottom,1718,bottom),fill='#433451',width=2)
    if key=='designs':
        for x,name,description in [(365,'THORNRIFT','Woodland / asymmetric talons'),
            (900,'VOIDMAW','Gate road / reinforced rune rim'),(1435,'STORMSCAR','Ridge / fractured angular rim')]:
            d.text((x,bottom+23),name,anchor='ma',font=font(25,True),fill=accent)
            d.text((x,bottom+63),description,anchor='ma',font=font(17),fill=muted)
        d.text((83,bottom+115),caption,font=font(18),fill=ink)
    else:d.text((83,bottom+26),caption,font=font(18),fill=ink)
    d.text((83,canvas.height-47),'Blender model and 120-frame idle loop • Roblox enemy spawning and VFX integration remain game-side work.',font=font(16),fill=muted)
    name='enemy_portals_design_sheet.png' if key=='designs' else f'enemy_portals_review_{key}.png'
    canvas.save(out/name);pages.append(canvas)
pages[0].save(out/'enemy_portals_views.pdf',save_all=True,append_images=pages[1:],resolution=150)
print('PORTAL_PRESENTATION',out/'enemy_portals_views.pdf')
