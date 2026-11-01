-- ROBLOX STUDIO COMMAND BAR / Stop Play before running.
local History=game:GetService("ChangeHistoryService")
assert(not game:GetService("RunService"):IsRunning(),"Stop Play first.")
local scripts=game:GetService("StarterPlayer").StarterPlayerScripts
local controller=scripts:FindFirstChild("AtheriaCampaignUI")
assert(controller and controller:IsA("LocalScript"),"Install the Atheria campaign UI first.")
local source=controller.Source
local cut=source:find("-- ATHERIA_WALK_IN_GATE",1,true)
    or source:find('local gate%s*=%s*workspace:WaitForChild%("AtheriaServiceCircles"%)')
assert(cut,"Could not locate the original Battle Gate opener. No changes made.")
local prefix=source:sub(1,cut-1)
prefix=prefix:gsub("controls:Disable%s*%(%s*%)","controls:Enable()")
local replacement=[==[
-- ATHERIA_WALK_IN_GATE
local gate=workspace:WaitForChild("AtheriaServiceCircles"):WaitForChild("BattleGate")
local anchor=gate:WaitForChild("Anchor")
local existing=anchor:FindFirstChild("AtheriaCampaignPrompt")
if existing then existing:Destroy() end
local wasInside=false
local elapsed=0
local touchGui,originalTouchOrder
local function updateTouchControls()
    if not Input.TouchEnabled then return end
    local current=playerGui:FindFirstChild("TouchGui")
    if current and current~=touchGui then
        touchGui=current; originalTouchOrder=current.DisplayOrder
    end
    if touchGui and touchGui.Parent then
        touchGui.DisplayOrder=gui.Enabled and math.max(originalTouchOrder,gui.DisplayOrder+1) or originalTouchOrder
    end
end
gui:GetPropertyChangedSignal("Enabled"):Connect(updateTouchControls)
playerGui.ChildAdded:Connect(function(child)
    if child.Name=="TouchGui" then updateTouchControls() end
end)
game:GetService("RunService").Heartbeat:Connect(function(dt)
    elapsed=elapsed+dt
    if elapsed<.08 then return end
    elapsed=0
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    local radius=gate:GetAttribute("Radius") or 8
    local unit=gate:GetAttribute("UnitScale") or 1
    local inside=false
    if root and anchor.Parent then
        local delta=root.Position-anchor.Position
        local distance=Vector2.new(delta.X,delta.Z).Magnitude
        -- Small edge tolerance prevents rapid opening/closing at the rim.
        local boundary=radius*(wasInside and 1.03 or .97)
        inside=distance<=boundary and math.abs(delta.Y)<math.max(12,unit*3)
    end
    if inside and not wasInside then
        refresh()
        setOpen(true)
    elseif not inside and wasInside then
        setOpen(false)
    end
    wasInside=inside
end)
refresh()
updateTouchControls()
]==]
History:SetWaypoint("Before Battle Gate walk-in UI")
controller.Source=prefix..replacement
local circles=workspace:FindFirstChild("AtheriaServiceCircles")
local gate=circles and circles:FindFirstChild("BattleGate")
local prompt=gate and gate:FindFirstChild("Anchor") and gate.Anchor:FindFirstChild("AtheriaCampaignPrompt")
if prompt then prompt:Destroy() end
History:SetWaypoint("Battle Gate walk-in UI")
print("Walk into Battle Gate's circle to open the atlas; walk out to close it. Movement remains enabled. Save your place.")
