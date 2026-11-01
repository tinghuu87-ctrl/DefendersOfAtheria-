"""Create a review sheet, annotated plan and seven-page PDF from actual renders.
Usage: python present_complete_map.py /path/to/Vestergate_Full_Render
Requires Pillow. Review labels are separate from the raw map renders.
"""
import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
root = Path('/usr/share/fonts/truetype/dejavu')


def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    for candidate in [str(root / name), name,
            'C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),
            '/System/Library/Fonts/Supplemental/'+('Arial Bold.ttf' if bold else 'Arial.ttf')]:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


BG = '#10232e'
INK = '#f1f2df'
MUTED = '#acc5cd'
GOLD = '#ddbf7c'
VIEWS = [
    ('overview', 'Battlefield overview', 'Three dirt approaches converge on the crystal outside the closed kingdom gates.'),
    ('plan', 'Routes and defence ledges', 'D1–D6 are grass ledges with jump access; P1–P3 mark the enemy entrances.'),
    ('arrival', 'Outside the kingdom gates', 'The player arrives behind the crystal, facing out toward the three approaches.'),
    ('gate', 'Crystal courtyard', 'Closed wooden gates, flanking bastions and kingdom walls frame the defended objective.'),
    ('woodland', 'Woodland trail', 'Winding dirt bends, shaded planting and the lower woodland defence ledges.'),
    ('centre', 'Gate road', 'The central approach and grass overlooks, with the crystal courtyard farther down the road.'),
    ('ridge', 'Ridge trail and stream crossing', 'An elevated eastern approach crosses the timber bridge above the stream cut.'),
]
COLORS = {'left': '#a9e0ae', 'centre': '#f2d692', 'right': '#9ed7f5'}


def project(x, y, size):
    return ((.5+x/200)*size[0], (.5-(y-6)/150)*size[1])


def badge(draw, point, label, color=GOLD):
    x, y = point
    draw.ellipse((x-23, y-23, x+23, y+23), fill=BG, outline=color, width=3)
    draw.text((x, y), label, font=font(19, True), fill=INK, anchor='mm')


plan = Image.open(out / 'vestergate_plan.png').convert('RGB')
draw = ImageDraw.Draw(plan)
layout = json.loads((out / 'VESTERGATE_LAYOUT.json').read_text())
for lane in layout['lanes']:
    points = [project(p[0], p[1], plan.size) for p in lane['centreline']]
    for t in [.27, .52, .75]:
        i = int(t*(len(points)-3))
        x, y = points[i]
        q = points[i+2]
        a = math.atan2(q[1]-y, q[0]-x)
        draw.polygon([(x+12*math.cos(a), y+12*math.sin(a)),
            (x+10*math.cos(a+2.45), y+10*math.sin(a+2.45)),
            (x+10*math.cos(a-2.45), y+10*math.sin(a-2.45))], fill=COLORS[lane['id']])
    first = lane['centreline'][0]
    badge(draw, project(first[0], first[1]+3, plan.size),
          'P'+str(['left', 'centre', 'right'].index(lane['id'])+1), '#d6a4ff')
for pad in layout['defence_terraces']:
    badge(draw, project(pad['x'], pad['y'], plan.size), pad['id'])
for i,(lane,label) in enumerate([('left','P1  WOODLAND'),('centre','P2  GATE ROAD'),('right','P3  RIDGE TRAIL')]):
    y=140+i*65
    draw.rounded_rectangle((70,y,340,y+48),radius=7,fill=BG,outline=COLORS[lane],width=2)
    draw.text((86,y+13),label,font=font(20,True),fill=COLORS[lane])
for text, position, target in [
        ('CRYSTAL', (1535, 1100), (0, -35.2)),
        ('SPAWN', (1535, 1160), (0, -43.05)),
        ('CLOSED GATES', (110, 1190), (0, -47))]:
    p = project(*target, plan.size)
    x, y = position
    width = draw.textbbox((0,0), text, font=font(22, True))[2]
    edge = x-12 if x > p[0] else x+width+12
    draw.line([p, (edge, y+12)], fill=GOLD, width=3)
    draw.rounded_rectangle((x-12, y-9, x+width+12, y+37), radius=7, fill=BG)
    draw.text((x,y), text, font=font(22,True), fill=INK)
plan.save(out / 'vestergate_plan_annotated.png')
if '--plan-only' in sys.argv:
    print('MAP_PLAN_READY', out / 'vestergate_plan_annotated.png')
    raise SystemExit(0)

pages = []
for number, (key, title, caption) in enumerate(VIEWS, 1):
    canvas = Image.new('RGB', (2080, 1715), BG)
    d = ImageDraw.Draw(canvas)
    d.text((80,32), 'VESTERGATE', font=font(36,True), fill=INK)
    d.text((2000,46), f'{number:02d} / MAP RENDERS', font=font(18,True), fill=GOLD, anchor='ra')
    d.text((82,84), title.upper(), font=font(20,True), fill=MUTED)
    source = plan if key == 'plan' else Image.open(out / f'vestergate_{key}.png').convert('RGB')
    canvas.paste(source, (80,135))
    d.line((80,1601,2000,1601), fill='#3b5663', width=2)
    d.text((82,1621), caption, font=font(20), fill=INK)
    d.text((82,1665), 'Three lanes · six grass ledges · three reusable portal designs', font=font(17), fill=MUTED)
    canvas.save(out / f'vestergate_review_{key}.png')
    pages.append(canvas)
pages[0].save(out / 'vestergate_full_map_views.pdf', save_all=True,
              append_images=pages[1:], resolution=150)

sheet = Image.new('RGB', (1920, 2560), BG)
d = ImageDraw.Draw(sheet)
d.text((60,26), 'VESTERGATE', font=font(36,True), fill=INK)
d.text((60,80), 'THREE-LANE DEFENCE / COMPLETE MAP VIEWS', font=font(18,True), fill=GOLD)
hero = Image.open(out / 'vestergate_overview.png').convert('RGB')
hero.thumbnail((1800,1350), Image.Resampling.LANCZOS)
sheet.paste(hero, (60,125))
for i,(key,title,_) in enumerate(VIEWS[1:]):
    x = 60+(i%3)*610
    y = 1510+(i//3)*490
    image = plan.copy() if key=='plan' else Image.open(out / f'vestergate_{key}.png').convert('RGB')
    image.thumbnail((580,435), Image.Resampling.LANCZOS)
    sheet.paste(image, (x,y+32))
    d.text((x,y), title.upper(), font=font(17,True), fill=INK)
sheet.save(out / 'vestergate_render_sheet.png')
print('MAP_REVIEW_READY', out / 'vestergate_full_map_views.pdf')
