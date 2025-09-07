local _, _, class = UnitClass("player")
local specIndex = C_SpecializationInfo.GetSpecialization()
local specID = C_SpecializationInfo.GetSpecializationInfo(specIndex)
local _, _, race = UnitRace("player")

local blackSmithingIdx = 6
local blackSmithingLevelRequirement = 550

local data = {}

data['specID'] = specID
data['class'] = class
data['race'] = race
data['stats'] = {
    ['ITEM_MOD_DODGE_RATING'] = GetCombatRating(CR_DODGE),
    ['ITEM_MOD_PARRY_RATING'] = GetCombatRating(CR_PARRY),
    ['ITEM_MOD_HIT_RATING'] = GetCombatRating(CR_HIT_MELEE),
    ['ITEM_MOD_EXPERTISE_RATING'] = GetCombatRating(CR_EXPERTISE),
    ['ITEM_MOD_HASTE_RATING'] = GetCombatRating(CR_HASTE_MELEE),
    ['ITEM_MOD_MASTERY_RATING_SHORT'] = GetCombatRating(CR_MASTERY),
    ['ITEM_MOD_CRIT_RATING'] = GetCombatRating(CR_CRIT_MELEE),
    ['ITEM_MOD_STRENGTH_SHORT'] = UnitStat("player", 1),
    ['ITEM_MOD_AGILITY_SHORT'] = UnitStat("player", 2),
    ['ITEM_MOD_STAMINA_SHORT'] = UnitStat("player", 3),
    ['ITEM_MOD_INTELLECT_SHORT'] = UnitStat("player", 4),
    ['ITEM_MOD_SPIRIT_SHORT'] = UnitStat("player", 5),
}

local statlist = {
    ['Expertise'] = 'ITEM_MOD_EXPERTISE_RATING',
    ['Hit'] = 'ITEM_MOD_HIT_RATING',
    ['Crit'] = 'ITEM_MOD_CRIT_RATING',
    ['Haste'] = 'ITEM_MOD_HASTE_RATING',
    ['Mastery'] = 'ITEM_MOD_MASTERY_RATING_SHORT',
    ['Dodge'] = 'ITEM_MOD_DODGE_RATING',
    ['Parry'] = 'ITEM_MOD_PARRY_RATING',
    ['Spirit'] = 'ITEM_MOD_SPIRIT_SHORT',
    --['Intellect'] = 'ITEM_MOD_INTELLECT_SHORT',
    --['Agility'] = 'ITEM_MOD_AGILITY_SHORT',
    --['Strength'] = 'ITEM_MOD_STRENGTH_SHORT',
    --['Stamina'] = 'ITEM_MOD_STAMINA_SHORT',
    ['Power'] = 'power',
    ['Resilience'] = 'resilience',
}

local socketColorList = {
    ['red'] = 'EMPTY_SOCKET_RED',
    ['blue'] = 'EMPTY_SOCKET_BLUE',
    ['yellow'] = 'EMPTY_SOCKET_YELLOW',
    ['prismatic'] = 'EMPTY_SOCKET_PRISMATIC',
}

-- caching all items so they can be scanned
local function cacheEquippedItems()
    for slot = 1, 19 do
        local a = GetInventoryItemID("player", slot)
        if a then
            local b = GetItemInfo(a)
        end
    end
end

local function ParseStatLine(line)
    for name, token in pairs(statlist) do
        -- Check if line contains the stat name (case-insensitive)
        if line:lower():find(name:lower()) then
            -- Extract number (handles e.g. "+1300 Parry Rating" or "1300 Parry")
            local value = line:match("([%+%-]?%d+)")
            
            if value then
                return token, tonumber(value)
            end
        end
    end
    
    return nil, nil
end

function GigaforgeGetEquippedItemInfo()
    local tooltip = CreateFrame("GameTooltip", "SocketScannerTooltip", nil, "GameTooltipTemplate")
    tooltip:SetOwner(UIParent, "ANCHOR_NONE")
    
    cacheEquippedItems()

    local itemData = {}
    
    local hasBlackSmithing = false
    for idx = 1, 2 do
        local profIdx = (select(idx, GetProfessions()))
        local _, _, skillLevel = GetProfessionInfo(profIdx)
        if profIdx == blackSmithingIdx and skillLevel > blackSmithingLevelRequirement then
            hasBlackSmithing = true
        end
    end


    for slot = 1, 19 do
        local itemLink = GetInventoryItemLink("player", slot)
        
        if itemLink then
            tooltip:ClearLines()
            tooltip:SetInventoryItem("player", slot)
            
            local sockets = {}
            local equippedGems = {}
            local bonus = {}
            local itemStats = GetItemStats(itemLink)
            local stats = {}

            --print(slot)
            --for k, v in pairs(itemStats) do
                --print(k, v)
            --end
            --print()

            for gemidx = 1, 3 do
                gem = C_Item.GetItemGem(GetInventoryItemLink("player", slot), gemidx)
                if gem then
                    table.insert(equippedGems, gem)
                end
            end
            
            for statName, statValue in pairs(itemStats) do
                for _, value in pairs(statlist) do
                    if value == statName then
                        --stat = {}
                        --stat[statName] = statValue
                        --table.insert(stats, stat)
                        stats[statName] = statValue
                    end
                end
                for color, socket in pairs(socketColorList) do
                    if socket == statName then
                        for i = 1, statValue do
                            table.insert(sockets, color)
                        end
                    end
                end
            end

            -- adding prismatic sockets
            if slot == 6 then
                table.insert(sockets, "prismatic")
            end

            if hasBlackSmithing then
                if slot == 10 or slot == 9 then
                    table.insert(sockets, "prismatic")
                end
            end

            
            
        --[[     for i = 1, tooltip:NumLines() do
                local line = _G["SocketScannerTooltipTextLeft" .. i]:GetText()
                if line then
                    
                    if line:find("Red Socket") then
                        table.insert(sockets, "red")
                    elseif line:find("Blue Socket") then
                        table.insert(sockets, "blue")
                    elseif line:find("Yellow Socket") then
                        table.insert(sockets, "yellow")
                    elseif line:find("Prismatic Socket") then
                        table.insert(sockets, "prismatic")
                    end
                    
                    if line:find("Socket Bonus") then
                        local statText = line:match("Socket Bonus: (.+)")
                        if statText then
                            local token, value = ParseStatLine(statText)
                            if token and value then
                                bonus[token] = value
                            end
                        end
                    end
                end
            end ]]
            table.insert(itemData, {
                    slotID = slot,
                    locked = false,
                    stats = stats,
                    sockets = sockets,
                    equippedGems = equippedGems,
                    bonus = bonus
            })
        end
    end
    
    return itemData
    
end


local function escape_str(s)
    return s:gsub('[%c\\"]', function(c)
            local escape_map = {
                ['"']  = '\\"',
                ['\\'] = '\\\\',
                ['\b'] = '\\b',
                ['\f'] = '\\f',
                ['\n'] = '\\n',
                ['\r'] = '\\r',
                ['\t'] = '\\t',
            }
            return escape_map[c] or string.format("\\u%04x", c:byte())
    end)
end

local function is_array(t)
    local i = 0
    for k in pairs(t) do
        i = i + 1
        if t[i] == nil then return false end
    end
    return true
end

local function encode_json(val)
    local val_type = type(val)
    
    if val_type == "string" then
        return '"' .. escape_str(val) .. '"'
    elseif val_type == "number" or val_type == "boolean" then
        return tostring(val)
    elseif val_type == "table" then
        local result = {}
        if is_array(val) then
            for _, v in ipairs(val) do
                table.insert(result, encode_json(v))
            end
            return "[" .. table.concat(result, ",") .. "]"
        else
            for k, v in pairs(val) do
                if type(k) ~= "string" then
                    error("Only string keys are allowed in JSON objects")
                end
                table.insert(result, '"' .. escape_str(k) .. '":' .. encode_json(v))
            end
            return "{" .. table.concat(result, ",") .. "}"
        end
    else
        return "null"
    end
end

local items = GigaforgeGetEquippedItemInfo()
data['items'] = items

local encoded = encode_json(data)

-- Create the popup frame
--local infoFrame = CreateFrame("Frame", "GigaforgeFrame", UIParent, "BackdropTemplate")
local infoFrame = CreateFrame("Frame", "GigaforgeFrame", UIParent, "BackdropTemplate")
infoFrame:SetSize(400, 300)
infoFrame:SetPoint("CENTER")
infoFrame:SetBackdrop({
    bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background",
    edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
    tile = true, tileSize = 32, edgeSize = 32,
    insets = { left = 11, right = 12, top = 12, bottom = 11 }
})
infoFrame:Hide()


local scrollFrame = CreateFrame("ScrollFrame", nil, infoFrame, "UIPanelScrollFrameTemplate")
scrollFrame:SetSize(350, 250)
scrollFrame:SetPoint("CENTER")


local editBox = CreateFrame("EditBox", nil, infoFrame)
editBox:SetFontObject(ChatFontNormal)
editBox:SetMultiLine(true)
editBox:SetWidth(400)
scrollFrame:SetScrollChild(editBox)
editBox:SetScript("OnEscapePressed", function() infoFrame:Hide() end)
editBox:SetAutoFocus(true)

-- Allow text wrapping
--editBox:SetWordWrap(true)




--[[
-- Create the editable text box
local editBox = CreateFrame("EditBox", nil, infoFrame, "InputBoxTemplate")
editBox:SetMultiLine(true)
editBox:SetSize(360, 240)
editBox:SetPoint("CENTER")


]]
-- Auto-highlight text when shown
infoFrame:SetScript("OnShow", function()
    local text = encoded
    editBox:SetText(text)
    editBox:HighlightText()
end)

-- Function to toggle the info window
local function ToggleGigaforge()
    if infoFrame:IsShown() then
        infoFrame:Hide()
    else
        infoFrame:Show()
    end
end

-- Create the toggle button on the character frame
local btn = CreateFrame("Button", "GigaforgeButton", CharacterFrame, "UIPanelButtonTemplate")
btn:SetSize(100, 22)
btn:SetText("Gigaforge")
btn:SetPoint("TOP", CharacterFrame, "TOP", 0, 25)
btn:SetScript("OnClick", ToggleGigaforge)

-- Register slash commands
SLASH_GIGAFORGE1 = "/gigaforge"
SLASH_GIGAFORGE2 = "/giga"
SlashCmdList["GIGAFORGE"] = ToggleGigaforge