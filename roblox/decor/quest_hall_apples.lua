-- Roblox Studio Command Bar. Requires the installed Atheria service circles.
assert(not game:GetService("RunService"):IsRunning(), "Stop Play first.")
local History=game:GetService("ChangeHistoryService")
local circles=workspace:FindFirstChild("AtheriaServiceCircles")
assert(circles,"The Atheria service circles are required to locate the building.")
local function origin(id)
    local model=circles:FindFirstChild(id)
    assert(model and model.PrimaryPart,"Missing circle: "..id)
    return circles:GetAttribute("ClearanceOriginal_"..id)
        or model:GetAttribute("HeightOriginalPosition") or model.PrimaryPart.Position
end
local f,q,t=origin("Forge"),origin("QuestHall"),origin("Tavern")
local determinant=44.6*(-33)-3.5
local axisX=((q-f)*(-33)-(t-f))/determinant
local axisZ=((t-f)*44.6-(q-f)*3.5)/determinant
axisX=Vector3.new(axisX.X,0,axisX.Z)
axisZ=Vector3.new(axisZ.X,0,axisZ.Z)
local scale=circles.Forge:GetAttribute("ClearanceOriginalUnitScale")
    or circles.Forge:GetAttribute("HeightOriginalUnitScale") or circles.Forge:GetAttribute("UnitScale")
assert(axisX.Magnitude>.01 and scale,"Town alignment is unavailable.")
local horizontal=f+axisX*(35.24+24)+axisZ*(16-15)
local position=Vector3.new(horizontal.X,f.Y+(6.7-.245)*scale,horizontal.Z)
local normal=axisX.Unit
local up=Vector3.yAxis
local back=-normal
local right=up:Cross(back).Unit
local frame=CFrame.fromMatrix(position,right,up,back)

History:SetWaypoint("Before Quest Hall Apples plaque")
local old=workspace:FindFirstChild("AtheriaQuestHallApplesPlaque")
if old then old:Destroy() end
local model=Instance.new("Model"); model.Name="AtheriaQuestHallApplesPlaque"; model.Parent=workspace
local plaque=Instance.new("Part")
plaque.Name="Apples Wall Plaque"
plaque.Size=Vector3.new(3.9*scale,3.216*scale,.06*scale)
plaque.CFrame=frame
plaque.Anchored=true; plaque.CanCollide=false; plaque.CanTouch=false; plaque.CanQuery=false
plaque.Material=Enum.Material.Slate; plaque.Color=Color3.fromRGB(127,127,127)
plaque.Parent=model; model.PrimaryPart=plaque
local surface=Instance.new("SurfaceGui")
surface.Name="Apples Artwork"; surface.Face=Enum.NormalId.Front
surface.CanvasSize=Vector2.new(810,668)
surface.SizingMode=Enum.SurfaceGuiSizingMode.FixedSize
surface.AlwaysOnTop=false; surface.LightInfluence=.65; surface.MaxDistance=300
surface.Parent=plaque
local canvas=Instance.new("Frame")
canvas.Size=UDim2.fromScale(1,1); canvas.BackgroundColor3=Color3.fromRGB(127,127,127)
canvas.BorderSizePixel=0; canvas.Parent=surface
local function stroke(a,b,width)
    local delta=b-a
    local line=Instance.new("Frame")
    line.AnchorPoint=Vector2.new(.5,.5); line.Position=UDim2.fromOffset((a.X+b.X)/2,(a.Y+b.Y)/2)
    line.Size=UDim2.fromOffset(delta.Magnitude+2,width or 10)
    line.Rotation=math.deg(math.atan2(delta.Y,delta.X))
    line.BackgroundColor3=Color3.new(0,0,0); line.BorderSizePixel=0; line.Parent=canvas
    local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(1,0); corner.Parent=line
end
local function path(points,smooth)
    local p={}
    for _,v in ipairs(points) do table.insert(p,Vector2.new(v[1],v[2])) end
    for i=1,#p-1 do
        if smooth then
            local a,b,c,d=p[math.max(1,i-1)],p[i],p[i+1],p[math.min(#p,i+2)]
            local last=b
            for step=1,12 do
                local t=step/12
                local nextPoint=(b*2+(c-a)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5
                stroke(last,nextPoint); last=nextPoint
            end
        else
            stroke(p[i],p[i+1])
        end
    end
end
path({{136,239},{160,168},{192,50},{221,99},{249,155},{268,198},{315,181},{363,167},{448,167},{511,176},{537,132},{560,78},{585,121},{605,190}},false)
path({{338,408},{309,410},{278,432},{257,468},{258,495},{280,513},{319,512},{355,499},{385,479},{404,494},{452,507},{494,508},{526,497},{543,478},{537,452},{513,426}},true)
for _, whisker in ipairs({
    {{69,326},{135,349},{201,377}},{{95,423},{150,419},{209,418}},{{92,495},{149,479},{203,465}},
    {{650,331},{704,306},{749,283}},{{661,386},{717,386},{778,383}},{{649,437},{709,454},{778,470}},
}) do path(whisker,true) end
for _, eye in ipairs({{315,333,-24},{505,325,25}}) do
    local oval=Instance.new("Frame"); oval.AnchorPoint=Vector2.new(.5,.5)
    oval.Position=UDim2.fromOffset(eye[1],eye[2]); oval.Size=UDim2.fromOffset(61,25)
    oval.Rotation=eye[3]; oval.BackgroundColor3=Color3.new(0,0,0); oval.BorderSizePixel=0; oval.Parent=canvas
    local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(1,0); corner.Parent=oval
end
local function text(body,y,height,size)
    local label=Instance.new("TextLabel")
    label.BackgroundTransparency=1; label.Position=UDim2.fromOffset(0,y)
    label.Size=UDim2.fromOffset(810,height); label.Text=body
    label.Font=Enum.Font.Arial; label.TextSize=size; label.TextColor3=Color3.new(0,0,0)
    label.Parent=canvas
end
text("Apples",548,58,49)
text("Lord of Poop",607,56,47)
History:SetWaypoint("Quest Hall Apples plaque placed")
print("Apples artwork added to the back of Quest Hall. Save your place. Move the whole AtheriaQuestHallApplesPlaque Model to adjust it.")
