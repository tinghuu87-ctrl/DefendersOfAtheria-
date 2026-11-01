-- STUDIO COMMAND BAR: stop Play and select the reimported town Model.
local Selection=game:GetService("Selection")
local History=game:GetService("ChangeHistoryService")
assert(not game:GetService("RunService"):IsRunning(),"Stop Play first.")
local roots=Selection:Get()
assert(#roots>0,"Select the reimported town Model in Explorer first.")
local scripts=game:GetService("StarterPlayer").StarterPlayerScripts
local atlas=scripts:FindFirstChild("AtheriaCampaignUI")
assert(atlas and atlas:IsA("LocalScript"),"The AtheriaCampaignUI LocalScript is missing.")
local circles=workspace:FindFirstChild("AtheriaServiceCircles")
local gate=circles and circles:FindFirstChild("BattleGate")
assert(gate and gate:FindFirstChild("Anchor"),"The BattleGate circle is missing.")
local source=atlas.Source
local cut=source:find("-- ATHERIA_WALK_IN_GATE",1,true)
    or source:find('local gate%s*=%s*workspace:WaitForChild%("AtheriaServiceCircles"%)')
assert(cut,"Atlas opener not recognized. No changes made.")
local prefix=source:sub(1,cut-1)
local controlsStart=prefix:find("local controls",1,true)
local controlsEnd=controlsStart and prefix:find("local previousSelection",controlsStart,true)
if controlsStart and controlsEnd then
    prefix=prefix:sub(1,controlsStart-1).."local controls=nil\n"..prefix:sub(controlsEnd)
end
prefix=prefix:gsub("controls:Disable%s*%(%s*%)","controls:Enable()")

local meshes={}
for _, root in ipairs(roots) do
    assert(root~=workspace,"Select the town Model rather than Workspace.")
    if root:IsA("MeshPart") then meshes[root]=true end
    for _, item in ipairs(root:GetDescendants()) do
        if item:IsA("MeshPart") then meshes[item]=true end
    end
end
assert(next(meshes),"No imported MeshParts found in the selection.")
History:SetWaypoint("Before Atheria UI and collision repair")
atlas.Source=prefix..[[
-- ATHERIA_WALK_IN_GATE
refresh()
gui:SetAttribute("AtlasReady",true)
print("Atheria atlas ready.")
]]
for _, item in ipairs(gate:GetDescendants()) do
    if item:IsA("ProximityPrompt") then item:Destroy() end
end
local changed,failed=0,0
for mesh in pairs(meshes) do
    if mesh.CanCollide and mesh.CollisionFidelity~=Enum.CollisionFidelity.PreciseConvexDecomposition then
        local ok,message=pcall(function()
            mesh.CollisionFidelity=Enum.CollisionFidelity.PreciseConvexDecomposition
        end)
        if ok then changed=changed+1 else
            failed=failed+1; warn(mesh:GetFullName()..": "..tostring(message))
        end
    end
end
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
History:SetWaypoint("Atheria UI and collision repaired")
print(string.format("Collision: %d meshes updated, %d failed. Save, then start a fresh Play session and walk into Battle Gate.",changed,failed))
