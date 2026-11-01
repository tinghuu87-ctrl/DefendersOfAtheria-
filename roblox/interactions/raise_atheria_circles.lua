-- Restore original circle positions and sizes, then lift covered effects.
-- Roblox Studio Command Bar; stop Play first.
local History=game:GetService("ChangeHistoryService")
assert(not game:GetService("RunService"):IsRunning(), "Stop Play first.")
local folder=workspace:FindFirstChild("AtheriaServiceCircles")
assert(folder, "The Atheria service circles are missing.")
local ids={"QuestHall","Tavern","Forge","BattleGate"}
local raise={QuestHall=true,Tavern=true}
for _, id in ipairs(ids) do
    assert(folder:FindFirstChild(id) and folder[id].PrimaryPart, "Missing circle: "..id)
end
local ray=RaycastParams.new()
ray.FilterType=Enum.RaycastFilterType.Exclude
ray.FilterDescendantsInstances={folder}
History:SetWaypoint("Before restoring Atheria circles")
for _, id in ipairs(ids) do
    local model=folder[id]
    local anchor=model.PrimaryPart
    local glow=model:FindFirstChild("Glow")
    local runes=model:FindFirstChild("Orbiting Runes")
    -- Undo this script's earlier lift before restoring the complete model.
    local previousLift=model:GetAttribute("AtheriaEffectLift") or 0
    local previousOffset=Vector3.new(0,previousLift,0)
    if previousLift~=0 then
        if glow then
            for _, p in ipairs(glow:GetDescendants()) do
                if p:IsA("BasePart") then p.CFrame=p.CFrame-previousOffset end
            end
        end
        if runes then runes:PivotTo(runes:GetPivot()-previousOffset) end
        anchor.CFrame=anchor.CFrame-previousOffset
    end
    local origin=folder:GetAttribute("ClearanceOriginal_"..id)
        or model:GetAttribute("HeightOriginalPosition") or anchor.Position
    local originalScale=model:GetAttribute("ClearanceOriginalModelScale")
        or model:GetAttribute("HeightOriginalModelScale") or model:GetScale()
    local radius=model:GetAttribute("ClearanceOriginalRadius")
        or model:GetAttribute("HeightOriginalRadius") or model:GetAttribute("Radius")
    local unit=model:GetAttribute("ClearanceOriginalUnitScale")
        or model:GetAttribute("HeightOriginalUnitScale") or model:GetAttribute("UnitScale")
    model:SetAttribute("HeightOriginalPosition",origin)
    model:SetAttribute("HeightOriginalModelScale",originalScale)
    model:SetAttribute("HeightOriginalRadius",radius)
    model:SetAttribute("HeightOriginalUnitScale",unit)
    model:ScaleTo(originalScale)
    model:PivotTo(CFrame.new(origin))
    model:SetAttribute("Radius",radius)
    model:SetAttribute("UnitScale",unit)

    local highest=origin.Y
    if raise[id] then
        -- Inspect low entrance steps throughout the original footprint.
        local function sample(dx,dz)
            local hit=workspace:Raycast(Vector3.new(origin.X+dx,origin.Y+.9*unit,origin.Z+dz),
                Vector3.new(0,-1.3*unit,0),ray)
            if hit and hit.Position.Y>=origin.Y-.05*unit then
                highest=math.max(highest,hit.Position.Y)
            end
        end
        sample(0,0)
        for x=-4,4 do for z=-4,4 do
            local dx,dz=x*radius/4,z*radius/4
            if dx*dx+dz*dz<=radius*radius then sample(dx,dz) end
        end end
        for i=1,48 do
            local a=i*math.pi/24
            sample(math.cos(a)*radius,math.sin(a)*radius)
        end
    end
    local lift=(raise[id] and highest>origin.Y+.06*unit)
        and (highest-origin.Y+.035*unit) or 0
    local offset=Vector3.new(0,lift,0)
    -- The stone disc stays on the paving; only the magical effects rise.
    if glow then
        for _, p in ipairs(glow:GetDescendants()) do
            if p:IsA("BasePart") then p.CFrame=p.CFrame+offset end
        end
    end
    if runes then runes:PivotTo(runes:GetPivot()+offset) end
    anchor.CFrame=anchor.CFrame+offset
    model:SetAttribute("AtheriaEffectLift",lift)
    print(string.format("%s: original position/size restored; effects raised %.2f studs.",id,lift))
end
History:SetWaypoint("Atheria original circles with raised effects")
print("Press Play to inspect the raised circles, then save your place.")
