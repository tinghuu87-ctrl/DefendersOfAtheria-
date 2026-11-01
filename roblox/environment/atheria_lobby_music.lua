-- Run in the lobby place's Studio Command Bar with Play stopped.
assert(not game:GetService("RunService"):IsRunning(), "Stop Play first.")
local scripts = game:GetService("ServerScriptService")
local controller = scripts:FindFirstChild("AtheriaLobbyMusic")
if controller then
    assert(controller:IsA("Script"), "AtheriaLobbyMusic must be a Script.")
else
    controller = Instance.new("Script")
    controller.Name = "AtheriaLobbyMusic"
end
controller.Source = [[
local SoundService = game:GetService("SoundService")
local music = SoundService:FindFirstChild("AtheriaLobbyTheme")
if not music then
    music = Instance.new("Sound")
    music.Name = "AtheriaLobbyTheme"
    music.Parent = SoundService
end
music.SoundId = "rbxassetid://76612846505659"
music.Volume = 0.25
music.PlaybackSpeed = 1
music.Looped = true
music:Play()
]]
controller.Disabled = false
controller.Parent = scripts
print("Atheria lobby music installed at volume 0.25. Save your place.")
