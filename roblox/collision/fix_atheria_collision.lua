-- ROBLOX STUDIO COMMAND BAR. Stop Play, then select your imported town Model.
-- Applies only to collidable MeshParts inside the current selection.
local Selection = game:GetService("Selection")
local History = game:GetService("ChangeHistoryService")
local RunService = game:GetService("RunService")

assert(not RunService:IsRunning(), "Stop Play before running this repair.")
local roots = Selection:Get()
assert(#roots > 0, "Select the imported Atheria town Model in Explorer first.")

local meshes = {}
local function collect(object)
    if object:IsA("MeshPart") and object.CanCollide then
        meshes[object] = true
    end
end
for _, root in ipairs(roots) do
    assert(root ~= workspace, "Select the town Model rather than Workspace.")
    collect(root)
    for _, descendant in ipairs(root:GetDescendants()) do
        collect(descendant)
    end
end
assert(next(meshes), "No collidable MeshParts were found in your selection.")

History:SetWaypoint("Before Atheria collision repair")
local changed, failed = 0, 0
for mesh in pairs(meshes) do
    if mesh.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
        local ok, message = pcall(function()
            mesh.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
        end)
        if ok then
            changed += 1
        else
            failed += 1
            warn("Collision update failed: " .. mesh:GetFullName() .. " / " .. tostring(message))
        end
    end
end
History:SetWaypoint("Atheria collision repair")
print(string.format("Atheria collision: %d meshes updated, %d failed. Test the passage in Play mode.", changed, failed))
