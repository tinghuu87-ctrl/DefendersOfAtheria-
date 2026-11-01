-- ATHERIA CIRCLE CLEARANCE + VISIBILITY UPDATE / Studio Command Bar
-- Stop Play first. The original four service circles must be installed.
local History=game:GetService("ChangeHistoryService")
local StarterPlayer=game:GetService("StarterPlayer")
assert(not game:GetService("RunService"):IsRunning(), "Stop Play first.")
local folder=workspace:FindFirstChild("AtheriaServiceCircles")
assert(folder, "Install the four Atheria service circles first.")
local ids={"QuestHall","Tavern","Forge","BattleGate"}
for _, id in ipairs(ids) do
    assert(folder:FindFirstChild(id) and folder[id].PrimaryPart, "Missing circle: "..id)
end
local function original(id)
    local key="ClearanceOriginal_"..id
    return folder:GetAttribute(key) or folder[id].PrimaryPart.Position
end
local f,q,t=original("Forge"),original("QuestHall"),original("Tavern")
-- Original circle coordinates: Forge(-24,15), Quest(20.6,16), Tavern(-20.5,-18).
local determinant=44.6*(-33)-3.5
local axisX=((q-f)*(-33)-(t-f))/determinant
local axisZ=((t-f)*44.6-(q-f)*3.5)/determinant
axisX=Vector3.new(axisX.X,0,axisX.Z)
axisZ=Vector3.new(axisZ.X,0,axisZ.Z)
assert(axisX.Magnitude>0.01 and axisZ.Magnitude>0.01, "Circle alignment is invalid.")
local scale=folder.Forge:GetAttribute("ClearanceOriginalUnitScale") or folder.Forge:GetAttribute("UnitScale")
local function horizontal(v) return Vector3.new(v.X,0,v.Z) end
local function authored(x,z) return f+axisX*(x+24)+axisZ*(z-15) end
local exclusions={
    {center=authored(-17,-19),radius=1.6*scale}, -- spawn medallion
    {center=authored(11,13),radius=7.2*scale}, -- sacred crystal platform
}

History:SetWaypoint("Before Atheria circle clearance")
for _, id in ipairs(ids) do
    if not folder:GetAttribute("ClearanceOriginal_"..id) then
        folder:SetAttribute("ClearanceOriginal_"..id, folder[id].PrimaryPart.Position)
    end
    local station=folder[id]
    if not station:GetAttribute("ClearanceOriginalRadius") then
        station:SetAttribute("ClearanceOriginalRadius",station:GetAttribute("Radius"))
        station:SetAttribute("ClearanceOriginalUnitScale",station:GetAttribute("UnitScale"))
        station:SetAttribute("ClearanceOriginalModelScale",station:GetScale())
    end
end

-- These are exported design captions, not the building signs or engravings.
local hidden=0
for _, item in ipairs(workspace:GetDescendants()) do
    if item:IsA("MeshPart") then
        local name=item.Name:lower():gsub("[^%w]", "")
        if name:find("optionalplanninglabels",1,true) or name:find("planningcaption",1,true) then
            item.Transparency=1; item.CanCollide=false; item.CanTouch=false; item.CanQuery=false
            hidden+=1
        end
    end
end
local ray=RaycastParams.new()
ray.FilterType=Enum.RaycastFilterType.Exclude
ray.FilterDescendantsInstances={folder}
local function clearFloor(point,radius,referenceY)
    for _, zone in ipairs(exclusions) do
        if horizontal(point-zone.center).Magnitude < radius+zone.radius+.15*scale then return nil end
    end
    local heights={}
    local function probe(dx,dz)
        local hit=workspace:Raycast(Vector3.new(point.X+dx,referenceY+1.8*scale,point.Z+dz),
            Vector3.new(0,-3.6*scale,0),ray)
        if not hit or math.abs(hit.Position.Y-referenceY)>.55*scale then return false end
        table.insert(heights,hit.Position.Y)
        return true
    end
    if not probe(0,0) then return nil end
    -- Sample a grid and the full perimeter with a small clearance margin.
    local extent=radius+.18*scale
    for x=-2,2 do for z=-2,2 do
        local dx,dz=x*extent/2,z*extent/2
        if dx*dx+dz*dz<=extent*extent and not probe(dx,dz) then return nil end
    end end
    for i=1,24 do
        local a=i*math.pi/12
        if not probe(math.cos(a)*extent,math.sin(a)*extent) then return nil end
    end
    local low,high=math.huge,-math.huge
    for _, y in ipairs(heights) do low=math.min(low,y); high=math.max(high,y) end
    if high-low>.07*scale then return nil end
    -- Check low props and body-height obstacles around the footprint.
    for _, height in ipairs({.4,1.15}) do
        local start=Vector3.new(point.X,high+height*scale,point.Z)
        for i=1,16 do
            local a=i*math.pi/8
            if workspace:Raycast(start,Vector3.new(math.cos(a)*extent,0,math.sin(a)*extent),ray) then return nil end
        end
    end
    return Vector3.new(point.X,high+.012*scale,point.Z)
end

local outward={QuestHall=-axisX.Unit,Tavern=axisX.Unit,Forge=-axisZ.Unit,BattleGate=-axisZ.Unit}
local preferred={QuestHall={.4,-2.3},Tavern={1.2,1.8},Forge={.35,-1.4},BattleGate={0,0}}
local plans={}
local failed={}
for _, id in ipairs(ids) do
    local station=folder[id]
    local origin=original(id)
    local originalRadius=station:GetAttribute("ClearanceOriginalRadius")
    local forward=outward[id]
    local side=(id=="QuestHall" or id=="Tavern") and axisZ.Unit or axisX.Unit
    local candidates={preferred[id]}
    for _, front in ipairs({.2,.4,.8,1.2,1.6,2}) do
        for _, lateral in ipairs({0,-.7,.7,-1.4,1.4,-2.1,2.1,-2.8,2.8,-3.5,3.5,-4.2,4.2}) do
            table.insert(candidates,{front,lateral})
        end
    end
    local best,bestFactor=nil,1
    -- Prefer the intended nearby spot, with a modest size adjustment if needed.
    for _, factor in ipairs({1,.85,.75}) do
        local radius=originalRadius*factor
        local offset=preferred[id]
        local clear=clearFloor(origin+forward*offset[1]*radius+side*offset[2]*radius,radius,origin.Y)
        if clear then best,bestFactor=clear,factor; break end
    end
    if not best then
        for _, factor in ipairs({1,.85,.75}) do
            local radius=originalRadius*factor
            local bestScore=math.huge
            for _, offset in ipairs(candidates) do
                local point=origin+forward*offset[1]*radius+side*offset[2]*radius
                local clear=clearFloor(point,radius,origin.Y)
                local score=offset[1]^2+offset[2]^2
                if clear and score<bestScore then best,bestFactor,bestScore=clear,factor,score end
            end
            if best then break end
        end
    end
    if best then plans[id]={position=best,factor=bestFactor} else table.insert(failed,id) end
end
for _, id in ipairs(ids) do
    local station=folder[id]
    if plans[id] then
        local plan=plans[id]
        station:ScaleTo(station:GetAttribute("ClearanceOriginalModelScale")*plan.factor)
        station:SetAttribute("Radius",station:GetAttribute("ClearanceOriginalRadius")*plan.factor)
        station:SetAttribute("UnitScale",station:GetAttribute("ClearanceOriginalUnitScale")*plan.factor)
        local delta=plan.position-station.PrimaryPart.Position
        station:PivotTo(station:GetPivot()+delta)
    end
    for _, item in ipairs(station:GetDescendants()) do
        if item:IsA("BasePart") then
            item.CanCollide=false; item.CanTouch=false; item.CanQuery=false
            if item.Name=="Carved Stone Disc" then item.Color=Color3.fromRGB(65,80,94) end
            if item.Name=="Outer Light" and not item:GetAttribute("VisibilityUpgraded") then
                item.Size=Vector3.new(item.Size.X*1.6,item.Size.Y*1.3,item.Size.Z)
                item:SetAttribute("VisibilityUpgraded",true)
            end
        end
    end
end

local controller=StarterPlayer.StarterPlayerScripts:FindFirstChild("AtheriaCircleEffects")
assert(controller and controller:IsA("LocalScript"), "The circle animation controller is missing.")
controller.Source=[[
local player=game:GetService("Players").LocalPlayer
local RunService=game:GetService("RunService")
local folder=workspace:WaitForChild("AtheriaServiceCircles")
local stations={}
for _, model in ipairs(folder:GetChildren()) do
    local anchor=model:WaitForChild("Anchor")
    local runes=model:WaitForChild("Orbiting Runes")
    runes.WorldPivot=anchor.CFrame
    local emitters={}
    for _, item in ipairs(anchor:GetDescendants()) do
        if item:IsA("ParticleEmitter") then table.insert(emitters,item) end
    end
    table.insert(stations,{model=model,anchor=anchor,runes=runes,emitters=emitters,
        glow=model:WaitForChild("Glow"):GetChildren(),radius=model:GetAttribute("Radius"),
        color=model:GetAttribute("EffectColor"),scale=model:GetAttribute("UnitScale"),
        amount=0,flash=0,inside=false,angle=0})
end
local elapsed=0
RunService.RenderStepped:Connect(function(dt)
    elapsed+=dt
    if elapsed<1/30 then return end
    dt=elapsed; elapsed=0
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    for _, station in ipairs(stations) do
        local delta=root and root.Position-station.anchor.Position
        local distance=delta and Vector2.new(delta.X,delta.Z).Magnitude or math.huge
        local near=delta and math.abs(delta.Y)<3*station.scale
        local inside=near and distance<station.radius*.85 or false
        local target=inside and 1 or (near and distance<station.radius*1.7 and .4 or 0)
        if inside and not station.inside then
            station.flash=1
            for _, emitter in ipairs(station.emitters) do emitter:Emit(2) end
        end
        station.inside=inside
        station.model:SetAttribute("LocalPlayerInside",inside)
        station.amount+=(target-station.amount)*(1-math.exp(-dt*6))
        station.flash=math.max(0,station.flash-dt*1.8)
        for _, p in ipairs(station.glow) do
            p.Transparency=.055-.035*station.amount
            p.Color=station.color:Lerp(Color3.new(1,1,1),.07+.10*station.amount+.15*station.flash)
        end
        station.angle+=dt*(.08+.10*station.amount)
        station.runes:PivotTo(station.anchor.CFrame*CFrame.Angles(0,station.angle,0))
        station.anchor["Service Glow"].Brightness=.45+.5*station.amount+.25*station.flash
        for _, emitter in ipairs(station.emitters) do
            emitter.Enabled=distance<station.radius*10
            emitter.Rate=(emitter.Name=="Motes" and 1 or 3)*(1+.5*station.amount)
        end
    end
end)
]]
History:SetWaypoint("Atheria circle clearance and visibility")
print("Circle visibility updated; planning caption meshes hidden: "..hidden)
if #failed>0 then
    warn("No clear position found for: "..table.concat(failed,", ")..". These circles were left in place. Move their whole Models to open paving.")
else
    print("All four circles passed sampled footprint and obstacle checks. Press Play to inspect, then save.")
end
