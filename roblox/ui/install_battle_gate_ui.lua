-- ATHERIA CAMPAIGN ATLAS / Run in Studio Command Bar with Play stopped.
local History=game:GetService("ChangeHistoryService")
assert(not game:GetService("RunService"):IsRunning(),"Stop Play before installing the UI.")
local circles=workspace:FindFirstChild("AtheriaServiceCircles")
local gate=circles and circles:FindFirstChild("BattleGate")
assert(gate and gate:FindFirstChild("Anchor"),"Install the Battle Gate circle first.")
History:SetWaypoint("Before Atheria Battle Gate UI")
local old=gate.Anchor:FindFirstChild("AtheriaCampaignPrompt")
if old then old:Destroy() end
local scripts=game:GetService("StarterPlayer").StarterPlayerScripts
local previous=scripts:FindFirstChild("AtheriaCampaignUI")
if previous then previous:Destroy() end
local controller=Instance.new("LocalScript"); controller.Name="AtheriaCampaignUI"
controller.Source=[==[
local Players=game:GetService("Players")
local TweenService=game:GetService("TweenService")
local Lighting=game:GetService("Lighting")
local Input=game:GetService("UserInputService")
local GuiService=game:GetService("GuiService")
local player=Players.LocalPlayer
local playerGui=player:WaitForChild("PlayerGui")
local old=playerGui:FindFirstChild("AtheriaCampaignAtlas")
if old then old:Destroy() end
local C={gold=Color3.fromRGB(255,213,95),ink=Color3.fromRGB(19,29,32),cream=Color3.fromRGB(245,238,209),white=Color3.fromRGB(248,248,232)}
-- These are concept destinations, not playable maps.
local missions={
 {name="The Gates of Atheria",x=250,y=250,description="The kingdom's outer approach and first line of defence."},
 {name="Lantern Quarter",x=480,y=310,description="A sheltered district of taverns, workshops and winding streets."},
 {name="Kingsroad Plaza",x=690,y=220,description="A broad royal square on the road to the inner city."},
 {name="The Royal Ramparts",x=910,y=150,description="High walls overlooking the approaches to Atheria."},
 {name="Crystal Sanctuary",x=920,y=360,description="Sacred ground protecting the ancient crystal seal."},
 {name="Whisperwood Crossroads",x=470,y=520,description="Forest paths converge beneath the old woodland canopy."},
 {name="Elderroot Grove",x=660,y=660,description="An ancient grove beyond the kingdom's stone walls."},
 {name="Hollowspire Den",x=970,y=740,description="A remote stronghold at the edge of the known kingdom."},
}
local difficulties={
 {name="Normal",color=Color3.fromRGB(104,216,162),description="A balanced defence."},
 {name="Intermediate",color=Color3.fromRGB(255,201,91),description="A tougher tactical challenge."},
 {name="Expert",color=Color3.fromRGB(239,117,115),description="For determined defenders."},
}
local gui=Instance.new("ScreenGui")
gui.Name="AtheriaCampaignAtlas"; gui.ResetOnSpawn=false; gui.IgnoreGuiInset=true
gui.DisplayOrder=30; gui.ZIndexBehavior=Enum.ZIndexBehavior.Global; gui.Enabled=false; gui.Parent=playerGui
local function create(class,parent,properties)
 local object=Instance.new(class)
 for key,value in pairs(properties or {}) do object[key]=value end
 object.Parent=parent; return object
end
local function round(object,radius) create("UICorner",object,{CornerRadius=UDim.new(0,radius)}) end
local function outline(object,color,width,transparency)
 return create("UIStroke",object,{Color=color,Thickness=width,Transparency=transparency or 0})
end
local function frame(parent,x,y,w,h,color,z)
 return create("Frame",parent,{Position=UDim2.fromOffset(x,y),Size=UDim2.fromOffset(w,h),BackgroundColor3=color,BorderSizePixel=0,ZIndex=z or 2})
end
local function text(parent,body,x,y,w,h,size,color,z)
 return create("TextLabel",parent,{Text=body,Position=UDim2.fromOffset(x,y),Size=UDim2.fromOffset(w,h),
 BackgroundTransparency=1,Font=Enum.Font.GothamBold,TextSize=size,TextColor3=color or C.cream,ZIndex=z or 12})
end
local function line(parent,a,b,width,color,z)
 local d=b-a
 local p=frame(parent,(a.X+b.X)/2,(a.Y+b.Y)/2,d.Magnitude,width,color,z)
 p.AnchorPoint=Vector2.new(.5,.5); p.Rotation=math.deg(math.atan2(d.Y,d.X)); round(p,width/2); return p
end
local function ellipse(parent,x,y,w,h,color,z)
 local p=frame(parent,x-w/2,y-h/2,w,h,color,z); round(p,math.max(w,h)); return p
end
local dim=frame(gui,0,0,0,0,Color3.new(0,0,0),1)
dim.Size=UDim2.fromScale(1,1); dim.BackgroundTransparency=.18
dim.Active=true
local canvas=frame(gui,0,0,1600,900,Color3.fromRGB(35,68,79),2)
canvas.AnchorPoint=Vector2.new(.5,.5); canvas.Position=UDim2.fromScale(.5,.5); canvas.ClipsDescendants=true
local uiScale=create("UIScale",canvas,{Scale=1})
local function resize()
 local camera=workspace.CurrentCamera
 if camera then uiScale.Scale=math.min(camera.ViewportSize.X/1600,camera.ViewportSize.Y/900) end
end
resize()
local viewportConnection
local function watchCamera()
 if viewportConnection then viewportConnection:Disconnect() end
 if workspace.CurrentCamera then viewportConnection=workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(resize) end
 resize()
end
workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(watchCamera); watchCamera()
create("UIGradient",canvas,{Color=ColorSequence.new(Color3.fromRGB(39,78,95),Color3.fromRGB(18,42,60)),Rotation=90})
local random=Random.new(87)
-- Water strokes around the painted land silhouette.
for i=1,130 do
 local x,y=random:NextNumber(0,1600),random:NextNumber(0,900)
 local p=line(canvas,Vector2.new(x,y),Vector2.new(x+random:NextNumber(7,23),y-3),2,Color3.fromRGB(100,160,176),3)
 p.BackgroundTransparency=.6
end
local lobes={{420,315,1000,830},{785,390,700,790},{980,620,440,390},{180,480,350,510}}
for _,v in ipairs(lobes) do ellipse(canvas,v[1],v[2],v[3]+35,v[4]+35,Color3.fromRGB(172,160,106),4) end
for _,v in ipairs(lobes) do ellipse(canvas,v[1],v[2],v[3],v[4],Color3.fromRGB(108,129,61),5) end
for i=1,100 do
 local x,y=random:NextNumber(80,1050),random:NextNumber(40,820)
 if ((x-560)/530)^2+((y-420)/405)^2<1 then
  local p=ellipse(canvas,x,y,random:NextNumber(40,160),random:NextNumber(30,100),Color3.fromRGB(random:NextInteger(110,140),random:NextInteger(130,150),random:NextInteger(65,82)),6)
  p.BackgroundTransparency=.5
 end
end
-- Layered riverbanks and a winding blue river.
local river={Vector2.new(120,0),Vector2.new(160,140),Vector2.new(330,190),Vector2.new(390,340),Vector2.new(570,350),Vector2.new(740,430),Vector2.new(890,480),Vector2.new(1120,550)}
for i=1,#river-1 do
 line(canvas,river[i],river[i+1],39,Color3.fromRGB(53,70,58),7)
 line(canvas,river[i],river[i+1],28,Color3.fromRGB(84,146,164),8)
 line(canvas,river[i]+Vector2.new(0,-5),river[i+1]+Vector2.new(0,-5),3,Color3.fromRGB(160,200,198),9)
end
-- Royal city: walls, warm roof blocks, and small courtyards.
local city=frame(canvas,520,60,510,290,Color3.fromRGB(153,149,83),7); round(city,65)
city.Rotation=-6; outline(city,Color3.fromRGB(89,102,63),7)
for row=0,4 do for column=0,8 do
 local roof=frame(canvas,545+column*51,85+row*49,random:NextInteger(26,40),random:NextInteger(23,35),Color3.fromRGB(random:NextInteger(147,177),random:NextInteger(103,129),65),8)
 roof.Rotation=-6; round(roof,3)
end end
-- Forest canopy symbols.
for i=1,75 do
 local x,y=random:NextNumber(365,970),random:NextNumber(475,785)
 if ((x-660)/330)^2+((y-620)/180)^2<1 then
  local leaf=ellipse(canvas,x,y,random:NextInteger(18,34),random:NextInteger(22,38),Color3.fromRGB(random:NextInteger(58,86),random:NextInteger(103,128),57),9)
  outline(leaf,Color3.fromRGB(56,87,48),2)
 end
end
text(canvas,"A T H E R I A",45,22,380,45,34,C.cream,12).TextXAlignment=Enum.TextXAlignment.Left
text(canvas,"KINGDOM CAMPAIGN  /  PREVIEW",48,70,420,25,14,C.gold,12).TextXAlignment=Enum.TextXAlignment.Left
text(canvas,"THE ROYAL DISTRICTS",570,36,450,28,16,Color3.fromRGB(219,210,154),10)
text(canvas,"THE ELDER WOODLANDS",470,810,460,28,18,Color3.fromRGB(218,216,155),10)
-- Curved dotted routes. No progression locks are implied by these previews.
local routes={}
for i=1,#missions-1 do
 local a=Vector2.new(missions[i].x,missions[i].y)
 local b=Vector2.new(missions[i+1].x,missions[i+1].y)
 local delta=b-a
 local perpendicular=Vector2.new(-delta.Y,delta.X).Unit
 local control=(a+b)/2+perpendicular*((i%2==0 and -1 or 1)*65)
 local count=math.max(10,math.ceil(delta.Magnitude/15))
 local dots={}
 for j=0,count do
  local t=j/count
  local p=a*(1-t)^2+control*(2*(1-t)*t)+b*t*t
  table.insert(dots,ellipse(canvas,p.X,p.Y,6,6,C.cream,11))
 end
 table.insert(routes,{from=i,to=i+1,dots=dots})
end
local function button(parent,body,x,y,w,h)
 local b=create("TextButton",parent,{Text=body,Position=UDim2.fromOffset(x,y),Size=UDim2.fromOffset(w,h),
  BackgroundColor3=Color3.fromRGB(48,62,66),BorderSizePixel=0,Font=Enum.Font.GothamBold,TextSize=20,TextColor3=C.cream,AutoButtonColor=true,ZIndex=24})
 round(b,9); outline(b,Color3.fromRGB(104,118,115),1)
 return b
end
local panel=frame(canvas,1120,24,450,530,Color3.fromRGB(18,29,34),20)
round(panel,17); outline(panel,C.gold,3)
text(panel,"CAMPAIGN SELECT",20,15,345,34,24,C.gold,22).TextXAlignment=Enum.TextXAlignment.Left
local close=button(panel,"X",393,12,42,40)
local status=text(panel,"MAPS COMING SOON",24,66,402,24,14,Color3.fromRGB(156,187,178),22)
local title=text(panel,"",55,105,340,88,30,C.cream,22); title.TextWrapped=true
local previousMap=button(panel,"‹",14,122,38,54)
local nextMap=button(panel,"›",398,122,38,54)
local description=text(panel,"",25,205,400,75,17,Color3.fromRGB(193,208,201),22); description.TextWrapped=true
text(panel,"DIFFICULTY",20,296,410,24,14,C.gold,22)
local previousDifficulty=button(panel,"‹",30,333,45,47)
local nextDifficulty=button(panel,"›",375,333,45,47)
local difficulty=text(panel,"Normal",80,330,290,50,27,C.cream,22)
local difficultyDescription=text(panel,"",25,386,400,28,15,C.cream,22)
local private=button(panel,"PLAY PRIVATE",24,442,193,54)
local play=button(panel,"PLAY MAP",230,442,196,54)
play.BackgroundColor3=Color3.fromRGB(140,111,44); outline(play,C.gold,1)
local toast=frame(canvas,395,831,810,48,Color3.fromRGB(22,36,41),25); round(toast,12); outline(toast,C.gold,1)
local toastText=text(toast,"Choose a destination to preview it. Battles are coming soon.",14,5,782,38,17,C.cream,26)
local footer=text(canvas,"Concept destinations • No playable maps yet     |     M closes the atlas",35,865,1050,24,14,C.cream,22)
footer.TextXAlignment=Enum.TextXAlignment.Left
local selected,difficultyIndex=1,1
local nodes={}
local pointer=text(canvas,"▼",0,0,54,52,45,C.gold,17)
pointer.TextStrokeColor3=C.ink; pointer.TextStrokeTransparency=0
local function refresh()
 local mission=missions[selected]
 gui:SetAttribute("SelectedMission",mission.name)
 gui:SetAttribute("SelectedDifficulty",difficulties[difficultyIndex].name)
 title.Text=mission.name:upper(); description.Text=mission.description
 difficulty.Text=difficulties[difficultyIndex].name
 difficulty.TextColor3=difficulties[difficultyIndex].color
 difficultyDescription.Text=difficulties[difficultyIndex].description
 pointer.Position=UDim2.fromOffset(mission.x-27,mission.y-74)
 for i,node in ipairs(nodes) do
  node.button.BackgroundColor3=i==selected and C.gold or C.white
  node.glow.Visible=i==selected; node.label.TextColor3=i==selected and C.gold or C.white
  node.scale.Scale=i==selected and 1.12 or 1
 end
 for _,route in ipairs(routes) do
  for _,dot in ipairs(route.dots) do dot.BackgroundColor3=(route.from==selected or route.to==selected) and C.gold or C.cream end
 end
end
for index,mission in ipairs(missions) do
 local shadow=ellipse(canvas,mission.x+4,mission.y+5,43,43,Color3.fromRGB(35,44,31),13)
 local glow=ellipse(canvas,mission.x,mission.y,67,67,C.gold,12); glow.BackgroundTransparency=.78
 local b=button(canvas,"",mission.x-19,mission.y-19,38,38)
 b.AnchorPoint=Vector2.new(.5,.5); b.Position=UDim2.fromOffset(mission.x,mission.y); b.ZIndex=15
 round(b,100); outline(b,C.ink,4)
 create("UIGradient",b,{Color=ColorSequence.new(Color3.new(1,1,1),Color3.fromRGB(169,176,162)),Rotation=90})
 local scaler=create("UIScale",b,{Scale=1})
 local label=text(canvas,mission.name,mission.x-160,mission.y+27,320,33,21,C.white,16)
 label.TextStrokeColor3=C.ink; label.TextStrokeTransparency=0
 nodes[index]={button=b,glow=glow,label=label,scale=scaler}
 b.Activated:Connect(function() selected=index; refresh(); toastText.Text=mission.name.." selected • Map in development" end)
 b.MouseEnter:Connect(function() TweenService:Create(scaler,TweenInfo.new(.12),{Scale=1.17}):Play() end)
 b.MouseLeave:Connect(function() TweenService:Create(scaler,TweenInfo.new(.12),{Scale=index==selected and 1.12 or 1}):Play() end)
end
previousMap.Activated:Connect(function() selected=(selected-2)%#missions+1; refresh() end)
nextMap.Activated:Connect(function() selected=selected%#missions+1; refresh() end)
previousDifficulty.Activated:Connect(function() difficultyIndex=(difficultyIndex-2)%#difficulties+1; refresh() end)
nextDifficulty.Activated:Connect(function() difficultyIndex=difficultyIndex%#difficulties+1; refresh() end)
local function comingSoon(isPrivate)
 toastText.Text=(isPrivate and "Private battle" or "Battle").." coming soon: "..missions[selected].name.." / "..difficulties[difficultyIndex].name
 TweenService:Create(toast,TweenInfo.new(.12),{BackgroundColor3=Color3.fromRGB(76,64,31)}):Play()
 task.delay(.4,function() if toast.Parent then TweenService:Create(toast,TweenInfo.new(.3),{BackgroundColor3=Color3.fromRGB(22,36,41)}):Play() end end)
end
play.Activated:Connect(function() comingSoon(false) end)
private.Activated:Connect(function() comingSoon(true) end)
local blur=Instance.new("BlurEffect"); blur.Name="AtheriaCampaignBlur"; blur.Size=0; blur.Parent=Lighting
local controls=nil
local previousSelection
local currentPrompt
local function setOpen(open)
 gui.Enabled=open
 if currentPrompt then currentPrompt.Enabled=not open end
 TweenService:Create(blur,TweenInfo.new(.2),{Size=open and 12 or 0}):Play()
 if controls then if open then controls:Enable() else controls:Enable() end end
 if open then
  previousSelection=GuiService.SelectedObject
  if Input.GamepadEnabled then GuiService.SelectedObject=nodes[selected].button end
 else GuiService.SelectedObject=previousSelection end
end
close.Activated:Connect(function() setOpen(false) end)
Input.InputBegan:Connect(function(input,processed)
 if not processed and gui.Enabled and input.KeyCode==Enum.KeyCode.M then setOpen(false) end
end)
player.CharacterRemoving:Connect(function() if gui.Enabled then setOpen(false) end end)


-- ATHERIA_WALK_IN_GATE
refresh()
gui:SetAttribute("AtlasReady",true)
]==]
controller.Parent=scripts

local previous=scripts:FindFirstChild("AtheriaBattleGateAutoOpen")
if previous then previous:Destroy() end
local detector=Instance.new("LocalScript")
detector.Name="AtheriaBattleGateAutoOpen"
detector.Source=[==[
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local TweenService=game:GetService("TweenService")
local Lighting=game:GetService("Lighting")
local Input=game:GetService("UserInputService")
local GuiService=game:GetService("GuiService")
local player=Players.LocalPlayer
local playerGui=player:WaitForChild("PlayerGui")
local wasInside=false
local lastGui=nil
local elapsed=0
local started=os.clock()
local warned=false
local touchGui,touchOrder
local function syncTouch()
    if not Input.TouchEnabled then return end
    local current=playerGui:FindFirstChild("TouchGui")
    if current and current~=touchGui then touchGui=current; touchOrder=current.DisplayOrder end
    if touchGui and touchGui.Parent then
        touchGui.DisplayOrder=lastGui and lastGui.Enabled and math.max(touchOrder,lastGui.DisplayOrder+1) or touchOrder
    end
end
local function open(gui,value)
    gui.Enabled=value
    GuiService.SelectedObject=nil
    local blur=Lighting:FindFirstChild("AtheriaCampaignBlur")
    if blur then TweenService:Create(blur,TweenInfo.new(.15),{Size=value and 12 or 0}):Play() end
    syncTouch()
end
RunService.Heartbeat:Connect(function(dt)
    elapsed=elapsed+dt
    if elapsed<.1 then return end
    elapsed=0
    local folder=workspace:FindFirstChild("AtheriaServiceCircles")
    local gate=folder and folder:FindFirstChild("BattleGate")
    local anchor=gate and gate:FindFirstChild("Anchor")
    local gui=playerGui:FindFirstChild("AtheriaCampaignAtlas")
    local ready=gui and gui:GetAttribute("AtlasReady")
    if not (anchor and ready) then
        if lastGui and lastGui.Parent and lastGui.Enabled then open(lastGui,false) end
        wasInside=false
        if not warned and os.clock()-started>12 then
            warned=true
            warn("Atheria gate: atlas or circle is not ready. Check Output for AtheriaCampaignUI errors.")
        end
        return
    end
    if gui~=lastGui then
        lastGui=gui; wasInside=false
        gui:GetPropertyChangedSignal("Enabled"):Connect(syncTouch)
    end
    -- Measure the visible outer ring instead of relying on a stale radius.
    local points={}
    local sum=Vector3.zero
    local glow=gate:FindFirstChild("Glow")
    if glow then
        for _, part in ipairs(glow:GetDescendants()) do
            if part:IsA("BasePart") and part.Name=="Outer Light" then
                table.insert(points,part.Position); sum=sum+part.Position
            end
        end
    end
    local center=anchor.Position
    local radius=gate:GetAttribute("Radius") or 8
    if #points>2 then
        center=sum/#points
        radius=0
        for _, point in ipairs(points) do
            radius=radius+Vector2.new(point.X-center.X,point.Z-center.Z).Magnitude
        end
        radius=radius/#points
    end
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    local inside=false
    if root then
        local delta=root.Position-center
        inside=Vector2.new(delta.X,delta.Z).Magnitude<=radius*(wasInside and 1.03 or .98)
            and math.abs(delta.Y)<math.max(12,radius*1.5)
    end
    if inside~=wasInside then
        open(gui,inside)
        print(inside and "Atheria: entered Battle Gate circle; atlas opened." or "Atheria: left Battle Gate circle; atlas closed.")
    end
    wasInside=inside
    syncTouch()
end)
]==]
detector.Parent=scripts

History:SetWaypoint("Atheria Battle Gate UI installed")
print("Campaign atlas installed. Press Play, approach Battle Gate, walk into its circle. Save your place.")
