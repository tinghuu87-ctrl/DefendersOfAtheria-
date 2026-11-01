-- ATHERIA SERVICE CIRCLES / Roblox Studio Command Bar
-- Stop Play and select the complete imported town Model before running.
local Selection = game:GetService("Selection")
local StarterPlayer = game:GetService("StarterPlayer")
local History = game:GetService("ChangeHistoryService")
assert(not game:GetService("RunService"):IsRunning(), "Stop Play first.")
local roots = Selection:Get()
assert(#roots == 1 and (roots[1]:IsA("Model") or roots[1]:IsA("Folder")), "Select the complete imported town Model in Explorer.")
local town = roots[1]
local function compact(s) return s:lower():gsub("[^%w]", "") end
local function bounds(token)
    local low, high, count = Vector3.new(math.huge,math.huge,math.huge), Vector3.new(-math.huge,-math.huge,-math.huge), 0
    for _, p in ipairs(town:GetDescendants()) do
        if p:IsA("MeshPart") and compact(p.Name):find(token, 1, true) then
            count += 1
            for _, x in ipairs({-1,1}) do for _, y in ipairs({-1,1}) do for _, z in ipairs({-1,1}) do
                local v = p.CFrame:PointToWorldSpace(p.Size * Vector3.new(x,y,z) / 2)
                low = Vector3.new(math.min(low.X,v.X),math.min(low.Y,v.Y),math.min(low.Z,v.Z))
                high = Vector3.new(math.max(high.X,v.X),math.max(high.Y,v.Y),math.max(high.Z,v.Z))
            end end end
        end
    end
    assert(count > 0, "Cannot locate " .. token .. ". Select the original complete exported town; retain its section names.")
    return Vector3.new((low.X+high.X)/2,0,(low.Z+high.Z)/2), low.Y
end

-- Recover the imported town's position, horizontal orientation and scale.
-- Reference bounds come from the finished revision 07 Blender town.
local forge, fy = bounds("05forgeanddefenceworkshop")
local quest, qy = bounds("06questhallandwarmap")
local tavern, ty = bounds("07tavernandwelcomecourt")
local fx, fz = -21.1539955, 14.7749996
local ax, az = 28.2169256-fx, 16.4527364-fz
local bx, bz = -21.2749996-fx, -16.684-fz
local determinant = ax*bz-bx*az
local axisX = ((quest-forge)*bz-(tavern-forge)*az)/determinant
local axisZ = ((tavern-forge)*ax-(quest-forge)*bx)/determinant
local scale = (axisX.Magnitude+axisZ.Magnitude)/2
assert(scale > 0.05 and math.abs(axisX.Unit:Dot(axisZ.Unit)) < 0.2
    and math.abs(axisX.Magnitude-axisZ.Magnitude)/scale < 0.25,
    "Town alignment could not be recovered. The imported sections may have been moved independently.")
local groundY = ((fy-0.25*scale)+(qy-0.30*scale)+(ty-0.13*scale))/3+0.34*scale
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Include
ray.FilterDescendantsInstances = {town}
local function position(x,z)
    local horizontal = forge+axisX*(x-fx)+axisZ*(z-fz)
    local hit = workspace:Raycast(Vector3.new(horizontal.X,groundY+1.5*scale,horizontal.Z),Vector3.new(0,-4*scale,0),ray)
    return Vector3.new(horizontal.X,hit and hit.Position.Y or groundY,horizontal.Z)
end

History:SetWaypoint("Before Atheria circles")
local old = workspace:FindFirstChild("AtheriaServiceCircles")
if old then old:Destroy() end
local folder = Instance.new("Folder")
folder.Name = "AtheriaServiceCircles"
folder.Parent = workspace
local GOLD = Color3.fromRGB(155,113,55)
local definitions = {
    {id="QuestHall", x=20.6,z=16,r=1.65,color=Color3.fromRGB(255,210,95)},
    {id="Tavern", x=-20.5,z=-18,r=1.7,color=Color3.fromRGB(81,234,199)},
    {id="Forge", x=-24,z=15,r=1.9,color=Color3.fromRGB(255,148,56)},
    {id="BattleGate", x=12,z=27,r=2.5,color=Color3.fromRGB(95,194,255)},
}
local icons = {
    QuestHall={{{-.4,-.5},{.4,-.5},{.4,.5},{-.4,.5},{-.4,-.5}},{{-.22,-.2},{.22,-.2}},{{-.22,0},{.22,0}},{{-.22,.2},{.1,.2}}},
    Tavern={{{-.35,-.4},{.2,-.4},{.2,.4},{-.35,.4},{-.35,-.4}},{{.2,-.2},{.48,-.2},{.48,.2},{.2,.2}},{{-.42,-.48},{.28,-.48}}},
    Forge={{{-.55,-.2},{.5,-.2},{.35,.04},{.12,.09},{.12,.3},{.4,.4},{-.4,.4},{-.15,.27},{-.15,.03},{-.55,-.2}}},
    BattleGate={{{0,-.65},{.38,0},{0,.65},{-.38,0},{0,-.65}},{{0,-.65},{0,.65}},{{-.38,0},{.38,0}}},
}
local function part(parent,name,size,cf,color,material)
    local p = Instance.new("Part")
    p.Name=name; p.Size=size; p.CFrame=cf
    p.Color=color; p.Material=material
    p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false
    p.CastShadow=false; p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
    p.Parent=parent
    return p
end
local function line(parent,name,a,b,width,height,color,material)
    return part(parent,name,Vector3.new(width,height,(b-a).Magnitude+0.015*scale),CFrame.lookAt((a+b)/2,b),color,material)
end
local function ring(parent,name,origin,radius,y,width,color,material,segments)
    for i=1,segments do
        local a,b=(i-1)*math.pi*2/segments,i*math.pi*2/segments
        line(parent,name,origin+Vector3.new(math.cos(a)*radius,y,math.sin(a)*radius),
            origin+Vector3.new(math.cos(b)*radius,y,math.sin(b)*radius),width,0.025*scale,color,material)
    end
end
for _, info in ipairs(definitions) do
    local model=Instance.new("Model"); model.Name=info.id
    model.ModelStreamingMode=Enum.ModelStreamingMode.Persistent; model.Parent=folder
    model:SetAttribute("StationId",info.id); model:SetAttribute("Radius",info.r*scale)
    model:SetAttribute("UnitScale",scale); model:SetAttribute("EffectColor",info.color)
    local origin=position(info.x,info.z)
    local anchor=part(model,"Anchor",Vector3.new(.1,.1,.1),CFrame.new(origin),info.color,Enum.Material.SmoothPlastic)
    anchor.Transparency=1; model.PrimaryPart=anchor
    local radius=info.r*scale
    local base=part(model,"Carved Stone Disc",Vector3.new(.035*scale,radius*2.12,radius*2.12),
        CFrame.new(origin+Vector3.new(0,.018*scale,0))*CFrame.Angles(0,0,math.pi/2),Color3.fromRGB(100,115,126),Enum.Material.Slate)
    base.Shape=Enum.PartType.Cylinder
    ring(model,"Bronze Border",origin,radius*1.035,.055*scale,.075*scale,GOLD,Enum.Material.Metal,48)
    local glow=Instance.new("Folder"); glow.Name="Glow"; glow.Parent=model
    ring(glow,"Outer Light",origin,radius,.08*scale,.065*scale,info.color,Enum.Material.Neon,48)
    ring(glow,"Inner Light",origin,radius*.79,.065*scale,.025*scale,info.color,Enum.Material.Neon,40)
    for _, path in ipairs(icons[info.id]) do
        for i=1,#path-1 do
            local a,b=path[i],path[i+1]
            line(glow,"Service Emblem",origin+Vector3.new(a[1]*radius*.85,.075*scale,a[2]*radius*.85),
                origin+Vector3.new(b[1]*radius*.85,.075*scale,b[2]*radius*.85),.04*scale,.022*scale,info.color,Enum.Material.Neon)
        end
    end
    local runes=Instance.new("Model"); runes.Name="Orbiting Runes"; runes.Parent=model
    for i=1,8 do
        local angle=i*math.pi/4
        part(runes,"Crystal Glyph",Vector3.new(.11*scale,.025*scale,.11*scale),
            CFrame.new(origin+Vector3.new(math.cos(angle)*radius*.9,.09*scale,math.sin(angle)*radius*.9))
            *CFrame.Angles(0,angle+math.pi/4,0),info.color,Enum.Material.Neon)
    end
    runes.WorldPivot=CFrame.new(origin)
    for i=1,12 do
        local angle=i*math.pi/6
        local attachment=Instance.new("Attachment"); attachment.Name="Edge Energy"
        attachment.Position=Vector3.new(math.cos(angle)*radius,.1*scale,math.sin(angle)*radius)
        attachment.Parent=anchor
        local emitter=Instance.new("ParticleEmitter"); emitter.Name="Wisps"
        emitter.Texture="rbxasset://textures/particles/smoke_main.dds"
        emitter.Color=ColorSequence.new(info.color,info.color:Lerp(Color3.new(1,1,1),.6))
        emitter.Size=NumberSequence.new({NumberSequenceKeypoint.new(0,.16*scale),NumberSequenceKeypoint.new(.45,.28*scale),NumberSequenceKeypoint.new(1,.035*scale)})
        emitter.Transparency=NumberSequence.new({NumberSequenceKeypoint.new(0,.6),NumberSequenceKeypoint.new(.3,.3),NumberSequenceKeypoint.new(1,1)})
        emitter.Lifetime=NumberRange.new(.55,1.1); emitter.Speed=NumberRange.new(.35*scale,.75*scale)
        emitter.SpreadAngle=Vector2.new(12,12); emitter.Rotation=NumberRange.new(0,360)
        emitter.RotSpeed=NumberRange.new(-35,35); emitter.Rate=2
        emitter.LightEmission=.85; emitter.LightInfluence=0; emitter.Parent=attachment
        if i%2==0 then
            local spark=Instance.new("ParticleEmitter"); spark.Name="Motes"
            spark.Texture="rbxasset://textures/particles/sparkles_main.dds"
            spark.Color=ColorSequence.new(info.color:Lerp(Color3.new(1,1,1),.4))
            spark.Size=NumberSequence.new({NumberSequenceKeypoint.new(0,.075*scale),NumberSequenceKeypoint.new(1,0)})
            spark.Transparency=NumberSequence.new(.15,1); spark.Lifetime=NumberRange.new(.8,1.5)
            spark.Speed=NumberRange.new(.2*scale,.6*scale); spark.Rate=.7
            spark.LightEmission=1; spark.LightInfluence=0; spark.Parent=attachment
        end
    end
    local light=Instance.new("PointLight"); light.Name="Service Glow"; light.Color=info.color
    light.Range=radius*1.6; light.Brightness=.3; light.Shadows=false; light.Parent=anchor
end

local scripts=StarterPlayer:WaitForChild("StarterPlayerScripts")
local previous=scripts:FindFirstChild("AtheriaCircleEffects")
if previous then previous:Destroy() end
local controller=Instance.new("LocalScript"); controller.Name="AtheriaCircleEffects"
controller.Source=[[
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
local folder=workspace:WaitForChild("AtheriaServiceCircles")
local stations={}
for _, model in ipairs(folder:GetChildren()) do
    local anchor=model:WaitForChild("Anchor")
    local glow=model:WaitForChild("Glow")
    local runes=model:WaitForChild("Orbiting Runes")
    runes.WorldPivot=anchor.CFrame
    local emitters={}
    for _, item in ipairs(anchor:GetDescendants()) do
        if item:IsA("ParticleEmitter") then table.insert(emitters,item) end
    end
    table.insert(stations,{model=model,anchor=anchor,runes=runes,glow=glow:GetChildren(),
        emitters=emitters,color=model:GetAttribute("EffectColor"),radius=model:GetAttribute("Radius"),
        scale=model:GetAttribute("UnitScale"),amount=0,inside=false,flash=0,angle=0})
end
RunService.RenderStepped:Connect(function(dt)
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    local now=os.clock()
    for _, station in ipairs(stations) do
        local offset=root and root.Position-station.anchor.Position
        local distance=offset and Vector2.new(offset.X,offset.Z).Magnitude or math.huge
        local close=offset and math.abs(offset.Y)<3*station.scale
        local inside=close and distance<station.radius*.85 or false
        local target=inside and 1 or (close and distance<station.radius*1.7 and .35 or 0)
        if inside and not station.inside then
            station.flash=1
            for _, emitter in ipairs(station.emitters) do emitter:Emit(emitter.Name=="Motes" and 2 or 1) end
        end
        station.inside=inside
        station.model:SetAttribute("LocalPlayerInside",inside)
        station.amount+=(target-station.amount)*(1-math.exp(-dt*6))
        station.flash=math.max(0,station.flash-dt*1.8)
        local pulse=(math.sin(now*1.8)+1)/2
        for _, p in ipairs(station.glow) do
            p.Transparency=.17-.10*station.amount+.04*pulse
            p.Color=station.color:Lerp(Color3.new(1,1,1),.035+.10*station.amount+.18*station.flash)
        end
        station.angle+=dt*(.07+.10*station.amount)
        station.runes:PivotTo(station.anchor.CFrame*CFrame.Angles(0,station.angle,0))
        station.anchor["Service Glow"].Brightness=.25+.5*station.amount+.35*station.flash
        for _, emitter in ipairs(station.emitters) do
            local active=distance<station.radius*10
            emitter.Enabled=active
            emitter.Rate=(emitter.Name=="Motes" and .7 or 2)*(1+.6*station.amount)
        end
    end
end)
]]
controller.Parent=scripts
History:SetWaypoint("Atheria service circles installed")
print("Four Atheria circles installed. Press Play for proximity effects. Save your place. Move a whole station Model to fine-tune placement.")
