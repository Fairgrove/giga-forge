local frame = CreateFrame("Frame")
frame.name = "Simple Reforge Applier"

local reforgeFrame

local reforgeQueue = {}
local isReforging = false

function parse_input_string(str)
    local result = {}

    -- Iterate over all matches of {key: value}
    for key, value in string.gmatch(str, "{(%d+):%s*(%d+)}") do
        key = tonumber(key)
        value = tonumber(value)
        result[#result + 1] = { [key] = value }
    end

    return result
end

local f = CreateFrame("Frame")
f:SetScript("OnUpdate", function(self, elapsed)
    if not isReforging and #reforgeQueue > 0 then
        local job = table.remove(reforgeQueue, 1)
        DoReforge(job.slot, job.option)
    end
end)

function DoReforge(slot, option)
    isReforging = true

    ClearCursor()
    PickupInventoryItem(slot)
    C_Reforge.SetReforgeFromCursorItem()
    C_Reforge.ReforgeItem(option)

    -- lol good enough for now
    C_Timer.After(0.5, function()
        isReforging = false
    end)
end

-- Create the UI frame
local function CreateUI()
    if reforgeFrame then return end

    reforgeFrame = CreateFrame("Frame", "SimpleReforgeFrame", UIParent, "BasicFrameTemplateWithInset")
    reforgeFrame:SetSize(400, 200)
    reforgeFrame:SetPoint("CENTER")
    reforgeFrame:SetMovable(true)
    reforgeFrame:EnableMouse(true)
    reforgeFrame:RegisterForDrag("LeftButton")
    reforgeFrame:SetScript("OnDragStart", reforgeFrame.StartMoving)
    reforgeFrame:SetScript("OnDragStop", reforgeFrame.StopMovingOrSizing)

    -- Title text
    reforgeFrame.title = reforgeFrame:CreateFontString(nil, "OVERLAY")
    reforgeFrame.title:SetFontObject("GameFontHighlight")
    reforgeFrame.title:SetPoint("LEFT", reforgeFrame.TitleBg, "LEFT", 5, 0)
    reforgeFrame.title:SetText("Simple Reforge Applier")

    -- ScrollFrame for the edit box
    local scrollFrame = CreateFrame("ScrollFrame", "SimpleReforgeScrollFrame", reforgeFrame, "UIPanelScrollFrameTemplate")
    scrollFrame:SetPoint("TOPLEFT", reforgeFrame, "TOPLEFT", 15, -40)
    scrollFrame:SetSize(370, 120)

    -- Multiline EditBox inside ScrollFrame
    local editBox = CreateFrame("EditBox", "SimpleReforgeEditBox", scrollFrame)
    editBox:SetMultiLine(true)
    editBox:SetFontObject("GameFontHighlight")
    editBox:SetWidth(350)
    editBox:SetAutoFocus(false)
    editBox:SetScript("OnEscapePressed", editBox.ClearFocus)

    -- Required to make scrolling work
    scrollFrame:SetScrollChild(editBox)

    -- Initial placeholder text
    editBox:SetText("Paste output from gigaforge simulator here")

    -- Button to apply reforges
    local button = CreateFrame("Button", nil, reforgeFrame, "GameMenuButtonTemplate")
    button:SetPoint("BOTTOM", reforgeFrame, "BOTTOM", 0, 15)
    button:SetSize(140, 30)
    button:SetText("Apply Reforges")

    button:SetScript("OnClick", function()
        local text = editBox:GetText()
        if not text or text == "" then
            print("Simple Reforge Applier: Please paste a JSON string.")
            return
        end
        
        parsed_input = parse_input_string(text)
        
        -- Input handling
        local parsed_input = parse_input_string(text)
        for _, entry in ipairs(parsed_input) do
            for k, v in pairs(entry) do
                table.insert(reforgeQueue, { slot = k, option = v })
            end
        end
        
        collectgarbage()
        --C_Reforge.CloseReforge()
    end)

    reforgeFrame.button = button
end

-- Open UI when Reforging Frame opens
local function OnReforgeFrameShow()
    CreateUI()
    reforgeFrame:Show()
end

local function OnReforgeFrameHide()
    if reforgeFrame then
        reforgeFrame:Hide()
    end
end

frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, event, arg1)
    if event == "ADDON_LOADED" and arg1 == "Blizzard_ReforgingUI" then
        -- Hook reforging frame show/hide
        local reforgingFrame = _G["ReforgingFrame"]
        if reforgingFrame then
            reforgingFrame:HookScript("OnShow", OnReforgeFrameShow)
            reforgingFrame:HookScript("OnHide", OnReforgeFrameHide)
        end
    end
end)
