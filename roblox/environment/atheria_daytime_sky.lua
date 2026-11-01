-- ATHERIA: BRIGHT BLUE DAYTIME SKY
-- Roblox Studio Command Bar. Stop Play before running, then save your place.
-- Uses Roblox's built-in sky textures; no uploads are required.

local Lighting = game:GetService("Lighting")
local History = game:GetService("ChangeHistoryService")
local RunService = game:GetService("RunService")
local Terrain = workspace.Terrain

assert(not RunService:IsRunning(), "Stop Play before changing the sky.")
History:SetWaypoint("Before Atheria daytime sky")

-- Replace conflicting sky/atmosphere objects. Re-running will not stack them.
for _, object in ipairs(Lighting:GetChildren()) do
    if object:IsA("Sky") or object:IsA("Atmosphere") then
        object:Destroy()
    end
end

local sky = Instance.new("Sky")
sky.Name = "Atheria Blue Day"
sky.SkyboxBk = "rbxasset://textures/sky/sky512_bk.tex"
sky.SkyboxDn = "rbxasset://textures/sky/sky512_dn.tex"
sky.SkyboxFt = "rbxasset://textures/sky/sky512_ft.tex"
sky.SkyboxLf = "rbxasset://textures/sky/sky512_lf.tex"
sky.SkyboxRt = "rbxasset://textures/sky/sky512_rt.tex"
sky.SkyboxUp = "rbxasset://textures/sky/sky512_up.tex"
sky.CelestialBodiesShown = true
sky.SunAngularSize = 10
sky.StarCount = 0
sky.Parent = Lighting

local atmosphere = Instance.new("Atmosphere")
atmosphere.Name = "Atheria Clear Day Air"
atmosphere.Density = 0.22
atmosphere.Offset = 0.15
atmosphere.Color = Color3.fromRGB(190, 215, 255)
atmosphere.Decay = Color3.fromRGB(100, 130, 175)
atmosphere.Glare = 0.12
atmosphere.Haze = 0.7
atmosphere.Parent = Lighting

Lighting.ClockTime = 13.5
Lighting.GeographicLatitude = 30
Lighting.Brightness = 2.3
Lighting.ExposureCompensation = 0
Lighting.GlobalShadows = true
Lighting.ShadowSoftness = 0.3
Lighting.Ambient = Color3.fromRGB(80, 94, 117)
Lighting.OutdoorAmbient = Color3.fromRGB(140, 156, 182)
Lighting.EnvironmentDiffuseScale = 1
Lighting.EnvironmentSpecularScale = 1
Lighting.FogStart = 10000
Lighting.FogEnd = 100000

local clouds = Terrain:FindFirstChildOfClass("Clouds")
if not clouds then
    clouds = Instance.new("Clouds")
    clouds.Parent = Terrain
end
clouds.Name = "Atheria Soft Day Clouds"
clouds.Enabled = true
clouds.Cover = 0.4
clouds.Density = 0.4
clouds.Color = Color3.fromRGB(249, 251, 255)

History:SetWaypoint("Atheria daytime sky")
print("Atheria daytime sky applied. Save your place to keep it.")
