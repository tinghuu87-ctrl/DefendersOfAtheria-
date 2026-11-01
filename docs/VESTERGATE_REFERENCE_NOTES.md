# Vestergate — exterior map reference notes

## Blockout follow-through

Revision 02 follows the user's marked layout: all three roads and the gate-side approach are dirt, terrain/vegetation breakthrough has been addressed, lamps face the roads, ramps and centre discs are removed, and six low grass vantages remain. D1/D2/D3/D5/D6 move to the five marked areas; unmarked D4 retains its horizontal location; the two crystal-side positions D7/D8 are removed. The observations below describe the original reference, including its cobbles, and remain reference context rather than the current material specification.

The subsequent Blender blockout is authored in `blender/vestergate/`, with review renders in `renders/vestergate/`. It develops the planning proposals below into editable terrain, three trails, accessible defence shelves, foliage masses, the crystal courtyard, and kingdom gates. The original observations and undecided gameplay questions remain useful design context.

## Scope and confirmed layout

The original reference-analysis step recorded the design notes below before any map geometry was built. The subsequent blockout is described above; gameplay systems remain unimplemented.

- Use the user's current spelling, **Vestergate**, for these notes. Earlier atlas assets used Vespergate; this document does not rename existing assets.
- A three-lane defence map located outside the kingdom gates.
- The kingdom wall and gate are visible from the battlefield and establish the place being defended.
- Players spawn immediately outside the gate. The defended crystal also stands outside, directly in front of the gates.
- Farther into the landscape, three separate enemy trails approach the shared gate/crystal objective.
- The supplied image establishes the outdoor environment's visual direction. It does not show the proposed kingdom gate or prove a complete three-lane route layout.

## Foliage observed in the reference

- Broad, layered tree crowns form rounded masses, with oversized trunks and visibly branching silhouettes. Leaf clusters are stylized and readable rather than individually realistic.
- Deep teal forest behind the scene contrasts with brighter green foreground canopies and a few slender trees bearing yellow/golden leaves.
- Dense turquoise grass runs along cliff rims and path edges. Hanging blades soften the transition between grass and exposed rock.
- Broad-leaf plants, fern-like fronds, low bushes, flowers, and trailing vines provide several different scales of vegetation.
- Vines and rounded leaves descend over cliff faces and timber structures; small pink/red flowers punctuate the green.
- Blue/purple flowers and occasional luminous accents reinforce the enchanted woodland setting.
- Vegetation clusters around edges, rock bases, structures, and trees. The main paved paths remain comparatively exposed and readable.

### Application

Use a hierarchy of large tree silhouettes, medium shrubs, and small grass/flower clusters. Reserve dense foliage for boundaries and scenery. Keep enemy silhouettes, lane surfaces, buildable ground, and the crystal approach readable. Use selective golden-leaf trees as landmarks rather than covering every route in the same vegetation.

## Terrain levels observed in the reference

- The scene is a terraced woodland, with low paths, grassy shelves, taller rock escarpments, and distant ridges.
- Brown/gray rock faces are broad and irregular; grass caps and overhangs make each shelf read as a solid landform.
- Upper-left shelves step back in multiple layers. Vegetation and scattered rocks interrupt the exposed faces.
- A raised grassy strip occupies the middle foreground, separating visible path sections at different depths.
- Timber bridges connect land across lower gaps. Fences and railings mark some exposed edges and settlement boundaries.
- The main path surfaces combine warm cobbles and earth, contrasting with cool grass and rock shadows.
- Large foreground trunks, mid-distance terraces, and blue atmospheric recession create depth without requiring an extremely large visible footprint.
- The image shows some lower gaps and shaded ground, but does not establish that every gap contains water or is traversable.

### Application

Block out three useful terrain bands: the main approach floor, accessible defence terraces above it, and taller scenic cliffs beyond the playable boundary. Keep height changes broad and deliberate rather than building many small jagged steps. Provide clear ramps or steps to playable terraces and sufficient room for Roblox characters, camera movement, and actual defence footprints. Do not rely on grass or decorative meshes to define collision.

## Potential defensive vantage points

The reference suggests locations suitable for adaptation; it does not establish tower placement rules, unit ranges, line-of-sight behaviour, or elevation bonuses.

| Position | Visual basis | Proposed role | Limitation to preserve |
| --- | --- | --- | --- |
| Grassy shelf beside a bend | Broad grass-capped terraces overlooking paths | Track enemies through a longer section of a winding lane | Clear sightline and enough flat surface for a real defence footprint |
| Middle terrace between approaches | Raised foreground strip separating visible paths | Let a position influence two nearby approaches, depending on defence range | Partial coverage; avoid one position covering all three lanes end to end |
| Bridge approach or abutment | Timber crossings over lower gaps | Defend a narrow crossing and its immediate approaches | Keep the walking/enemy crossing clear; do not assume the bridge deck is buildable |
| Raised outer-lane shoulder | Right-side elevated grassy areas and fenced edges | Give one route its own overlooking position | Trees, cliffs, and route curvature can limit visibility farther away |
| Gate-side ground terrace | Required by the proposed Vestergate layout, not visible in the reference | A final defensive position near the crystal | Keep the crystal, spawn, and all three final approaches unobstructed |

Buildable areas should read as broad, relatively flat, lightly dressed grass or stone, contrasted with dense scenic vegetation. Tall cliffs and narrow decorative ledges should not accidentally resemble usable platforms. A higher position should not automatically grant a mechanical damage or range bonus; that remains undecided.

## Proposed identities for the three lanes

These are planning labels and adaptations of the reference, not confirmed routes visible from end to end in the image. Left/right are defined while standing at the kingdom gate and looking outward toward incoming enemies.

### Left — shaded woodland trail

- Lower ground framed by large trunks, teal canopy, vines, and rock faces.
- More winding than the other routes, with distinct open stretches between wooded bends.
- Proposed visual landmark: a substantial old tree beside a broad path turn.
- Defence opportunities: flat shelves beside bends and a small terrace above the lower approach.
- Tactical character to explore later: stronger local opportunities around turns, with interrupted long-distance visibility. Do not add blind enemy spawns immediately around a corner.

### Centre — old gate road

- The clearest and most direct visual connection between the landscape and the kingdom gate.
- Broad worn cobbles broken by earthen edges, intermittent lantern posts, timber details, and low vegetation.
- A modest dip or raised crossing can add terrain interest without obscuring the route's purpose.
- Defence opportunities: open shoulders on both sides and controlled overlap with the adjacent lanes near the gate.
- Tactical character to explore later: strong visibility and straightforward approach geometry, contrasted with fewer winding sections. Any shorter travel time must be balanced when lane lengths and enemy speeds are set.

### Right — sunlit ridge trail

- An elevated outer approach, brighter foliage, scattered golden-leaf trees, and a descent toward the gate-side ground.
- A timber bridge across a shallow cut can supply a memorable crossing; a small roadside camp or pavilion is optional scenery, inspired by the reference's blue-roofed structure.
- Defence opportunities: a flat overlooking shoulder and clear ground at the bridge approaches.
- Tactical character to explore later: a recognizable crossing and height transition, with limited visibility around the ridge. Preserve a visible section of trail before enemies enter the contested area.

### Shared approach

Keep the lanes distinguishable through most of their length, then let them enter the crystal's shared defence area near the gate. Avoid merging them halfway across the battlefield, which would weaken the three-lane identity. The exact convergence geometry, lane widths and lengths, bridge locations, and enemy spawn positions remain undecided.

## Composition, landmarks, and lighting

- The gate and wall should be the dominant architectural landmark. Their masonry provides a clear contrast with the organic forest beyond.
- Use the crystal as the immediate defended focal point, with enough clear ground around it for player movement and readable enemy arrival.
- From the spawn area, show the beginnings of all three outgoing approaches and a landmark identifying each one. The entire length of every route need not be visible at once.
- The reference uses cool turquoise daylight, blue atmospheric depth, and small warm amber lanterns. Golden foliage provides additional warm accents.
- Preserve chunky, readable shapes and selective detail. Concentrate small props near landmarks and path junctions; allow quieter areas of grass and rock between them.
- Use cliffs, tree groups, fences, and terrain changes to explain boundaries. Avoid densely decorating every defence terrace or filling the sightline to the crystal with tree crowns.

## Decisions for a later blockout

Exact footprint and Roblox scale; wall/gate proportions; crystal and spawn separation; lane widths and travel times; accessible terrace heights; defence footprint sizes; ramps and player circulation; route overlap and line-of-sight rules; and the number of buildable positions. None are fixed by the reference image alone.
