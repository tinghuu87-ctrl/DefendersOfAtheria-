-- Upload atheria_simple_atlas.png to Roblox as an IMAGE, then paste its asset ID below.
-- Run this entire script in Studio's Command Bar with Play stopped.
local ATLAS_IMAGE_ID = "PASTE_IMAGE_ASSET_ID_HERE"

assert(not game:GetService("RunService"):IsRunning(),"Stop Play first.")
local assetId=tostring(ATLAS_IMAGE_ID):match("%d+")
assert(assetId,"Upload the supplied atlas PNG as an image, then paste its image asset ID on the first settings line.")
local History=game:GetService("ChangeHistoryService")
local controller=game:GetService("StarterPlayer").StarterPlayerScripts:FindFirstChild("AtheriaCampaignUI")
assert(controller and controller:IsA("LocalScript"),"Install the Atheria campaign UI first.")
local source=controller.Source
local function replaceSection(code,startPattern,endPattern,replacement)
    local first=code:find(startPattern)
    local last=first and code:find(endPattern,first+1)
    assert(first and last,"Atlas structure not recognized. Nothing has been applied.")
    return code:sub(1,first-1)..replacement.."\n"..code:sub(last)
end
source=replaceSection(source,"local missions%s*=","local difficulties%s*=",[[
-- Reference-style atlas concept destinations; all remain previews.
local missions={
 {name="Vespergate",x=238,y=205,description="A fortified passage guarding Atheria's western approaches."},
 {name="Brassveil Ward",x=450,y=292,description="Copper roofs, foundry courts and merchant lanes beside the river."},
 {name="Crownshard Court",x=528,y=219,labelY=-57,description="The royal processional square beneath the kingdom's crystal insignia."},
 {name="Orison Bastion",x=759,y=120,description="Consecrated ramparts and watchtowers above the coastal cliffs."},
 {name="Auralith Sanctum",x=775,y=312,description="Terraced sacred ground surrounding one of Atheria's crystal seals."},
 {name="Thornwake Crossing",x=390,y=458,description="Old woodland roads meet at a narrow river crossing."},
 {name="Velmorrow Hollow",x=509,y=601,description="A deep forest refuge of ancient roots, moss and hidden pools."},
 {name="Gravemantle Roost",x=757,y=705,description="A ruined highland stronghold overlooking the restless sea."},
}
]])

-- Use a single updated corner/stroke rather than stacking competing modifiers.
source=replaceSection(source,"local function round%s*%(","local function outline%s*%(",[[
local function round(object,radius)
 local corner=object:FindFirstChildOfClass("UICorner") or Instance.new("UICorner")
 corner.CornerRadius=UDim.new(0,radius)
 corner.Parent=object
end
]])
source=replaceSection(source,"local function outline%s*%(","local function frame%s*%(",[[
local function outline(object,color,width,transparency)
 local stroke=object:FindFirstChildOfClass("UIStroke") or Instance.new("UIStroke")
 stroke.Color=color; stroke.Thickness=width; stroke.Transparency=transparency or 0
 stroke.Parent=object
 return stroke
end
]])
source=replaceSection(source,"local function resize%s*%(","local viewportConnection",[[
local function resize()
 local available=gui.AbsoluteSize
 if available.X<=0 or available.Y<=0 then
  local camera=workspace.CurrentCamera
  if not camera then return end
  available=camera.ViewportSize
 end
 local fit=math.min(available.X/1600,available.Y/900)
 canvas.AnchorPoint=Vector2.zero
 canvas.Position=UDim2.fromOffset((available.X-1600*fit)/2,(available.Y-900*fit)/2)
 uiScale.Scale=fit
end
gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(resize)
resize()
]])

local background=[[
-- ATHERIA_ILLUSTRATED_BACKGROUND
local atlasArt=create("ImageLabel",canvas,{
 Name="IllustratedAtlas",Position=UDim2.fromScale(0,0),Size=UDim2.fromScale(1,1),
 BackgroundTransparency=1,Image="rbxassetid://ASSET_ID",ScaleType=Enum.ScaleType.Stretch,
 ResampleMode=Enum.ResamplerMode.Default,ZIndex=3,
})
task.spawn(function()
 local ok,message=pcall(function()
  game:GetService("ContentProvider"):PreloadAsync({atlasArt})
 end)
 if not ok or not atlasArt.IsLoaded then
  warn("Atheria atlas art could not load. Check the image asset ID and its approval/access status. "..tostring(message))
 end
end)
]]
background=background:gsub("ASSET_ID",assetId)
local artStart=source:find("%-%- ATHERIA_ILLUSTRATED_BACKGROUND")
    or source:find('create%s*%(%s*"UIGradient"%s*,%s*canvas')
local artEnd=artStart and source:find('text%s*%(%s*canvas%s*,%s*"A T H E R I A"',artStart)
assert(artStart and artEnd,"Cannot locate the old map artwork. Nothing has been applied.")
source=source:sub(1,artStart-1)..background.."\n"..source:sub(artEnd)

source=replaceSection(source,"local routes%s*=","local function button%s*%(",[[
local routes={}
for index=1,#missions-1 do
 local a=Vector2.new(missions[index].x,missions[index].y)
 local b=Vector2.new(missions[index+1].x,missions[index+1].y)
 local delta=b-a
 local perpendicular=Vector2.new(-delta.Y,delta.X).Unit
 local control=(a+b)/2+perpendicular*((index%2==0 and -1 or 1)*48)
 local count=math.max(10,math.ceil(delta.Magnitude/13))
 local dots={}
 for step=0,count do
  local t=step/count
  local position=a*(1-t)^2+control*(2*(1-t)*t)+b*t*t
  local shadow=ellipse(canvas,position.X,position.Y,9,9,Color3.fromRGB(12,24,28),10)
  shadow.BackgroundTransparency=.4
  table.insert(dots,ellipse(canvas,position.X,position.Y,5,5,C.cream,11))
 end
 table.insert(routes,{from=index,to=index+1,dots=dots})
end
]])

-- Slightly larger circular mission markers, rendered independently of the art.
source=source:gsub("([%w_]+)%.ZIndex%s*=%s*15",function(variable)
 return variable..".ZIndex=15\n"..variable..".Size=UDim2.fromOffset(42,42)"
end)
source=source:gsub("THE ROYAL DISTRICTS","THE CROWNWARD")
source=source:gsub("THE ELDER WOODLANDS","THE VEILED WILDS")
-- Keep the central city label above its marker so it clears nearby nodes.
source=source:gsub("mission%.y%s*%+%s*27","mission.y+(mission.labelY or 27)")
History:SetWaypoint("Before simplified Atheria atlas")
controller.Source=source
controller:SetAttribute("AtlasArtworkId",assetId)
History:SetWaypoint("Simplified Atheria atlas")
print("Reference-style atlas installed; Atheria destination names retained. Save, then start a fresh Play session and enter Battle Gate.")
