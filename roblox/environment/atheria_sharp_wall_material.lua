-- ATHERIA: SHARPER REPEATING WALL MASONRY
-- Roblox Studio Command Bar. Stop Play before running.
-- Select wall MeshParts directly, or select the imported town Model.
-- Model selection automatically targets the exported connected wall section.

local Selection = game:GetService("Selection")
local History = game:GetService("ChangeHistoryService")
local RunService = game:GetService("RunService")

local WALL_MATERIAL = Enum.Material.Brick
local WALL_COLOR = Color3.fromRGB(166, 177, 184)

assert(not RunService:IsRunning(), "Stop Play before updating wall materials.")
local roots = Selection:Get()
assert(#roots > 0, "Select your wall MeshParts or imported town Model first.")

local targets = {}
local function isExportedWall(object)
    local name = object.Name:lower():gsub("[^%w]", "")
    return name:find("connectedfinishedwalls", 1, true) ~= nil
        or name:find("joinedmasonrywallnetwork", 1, true) ~= nil
        or name:find("continuouswallfoundations", 1, true) ~= nil
        or name:find("continuouscopingandcornercaps", 1, true) ~= nil
end

for _, root in ipairs(roots) do
    assert(root ~= workspace, "Select the imported town Model rather than Workspace.")
    if root:IsA("MeshPart") then
        targets[root] = true
    else
        for _, object in ipairs(root:GetDescendants()) do
            if object:IsA("MeshPart") and isExportedWall(object) then
                targets[object] = true
            end
        end
    end
end

assert(next(targets), "No matching walls found. Select the wall MeshParts directly in Explorer.")
History:SetWaypoint("Before Atheria wall texture upgrade")

local count = 0
for wall in pairs(targets) do
    -- Remove the low-density atlas so Roblox's repeating material is visible.
    for _, child in ipairs(wall:GetChildren()) do
        if child:IsA("SurfaceAppearance") then
            child:Destroy()
        end
    end
    wall.TextureID = ""
    wall.MaterialVariant = ""
    wall.Material = WALL_MATERIAL
    wall.Color = WALL_COLOR
    count += 1
end

History:SetWaypoint("Atheria wall texture upgrade")
print(string.format("Updated %d wall meshes with repeating stone-gray masonry. Save your place to keep it.", count))
