-- hidden tooltip
local scanner = CreateFrame("GameTooltip", "TooltipScannerTooltip", nil, "GameTooltipTemplate")
scanner:SetOwner(WorldFrame, "ANCHOR_NONE")

-- slots to check
local slots = {
    "HeadSlot", "NeckSlot", "ShoulderSlot", "BackSlot", "ChestSlot", "WristSlot",
    "HandsSlot", "WaistSlot", "LegsSlot", "FeetSlot", "Finger0Slot", "Finger1Slot",
    "Trinket0Slot", "Trinket1Slot", "MainHandSlot", "SecondaryHandSlot"
}

local socketColorList = {
    ['red'] = 'EMPTY_SOCKET_RED',
    ['blue'] = 'EMPTY_SOCKET_BLUE',
    ['yellow'] = 'EMPTY_SOCKET_YELLOW',
    ['prismatic'] = 'EMPTY_SOCKET_PRISMATIC',
}

local statlist = {
    ['Expertise'] = 'ITEM_MOD_EXPERTISE_RATING',
    ['Hit'] = 'ITEM_MOD_HIT_RATING',
    ['Critical Strike'] = 'ITEM_MOD_CRIT_RATING',
    ['Haste'] = 'ITEM_MOD_HASTE_RATING',
    ['Mastery'] = 'ITEM_MOD_MASTERY_RATING_SHORT',
    ['Dodge'] = 'ITEM_MOD_DODGE_RATING',
    ['Parry'] = 'ITEM_MOD_PARRY_RATING',
    ['Spirit'] = 'ITEM_MOD_SPIRIT_SHORT',
}

-- only these stats
local tracked = {
    ["Dodge"]     = true,
    ["Parry"]     = true,
    ["Mastery"]   = true,
    ["Haste"]     = true,
    ["Critical Strike"] = true,
    ["Crit"]      = true,
    ["Spirit"]    = true,
    ["Expertise"] = true,
    ["Hit"]       = true,
}

local function hasKey(tbl, key)
    return tbl[key] ~= nil
end

-- helper to normalize numbers with separators
local function CleanNumber(numstr)
    -- remove , and . (thousand separators)
    local clean = numstr:gsub("[,%.]", "")
    return tonumber(clean)
end

local function hasBlackSmithingRequired()
    local blackSmithingIdx = 6
    local blackSmithingLevelRequirement = 550

    for idx = 1, 2 do
        local profIdx = (select(idx, GetProfessions()))
        local _, _, skillLevel = GetProfessionInfo(profIdx)
        
        if profIdx then
            if profIdx == blackSmithingIdx and skillLevel > blackSmithingLevelRequirement then
                return true
            end
        end

    end
    
    return false
end

-- extract stats from tooltip
local function GetItemStatsFromTooltip(slotId)
    local itemLink = GetInventoryItemLink("player", slotId)
    if not itemLink then return nil end

    local itemStats = GetItemStats(itemLink)

    local sockets = {}
    local equippedGems = {}
    local bonus = {}
    local itemStats = GetItemStats(itemLink)
    local stats = {}

    local seen = {}  -- keep track of already saved stats

    scanner:ClearLines()
    scanner:SetInventoryItem("player", slotId)

    for i = 2, scanner:NumLines() do
        local line = _G["TooltipScannerTooltipTextLeft"..i]
        if line then
            local text = line:GetText()
            if text then
                -- Case 1: normal stat
                local amount, stat = text:match("^%+([%d,%.]+)%s(.+)$")
                if amount and stat and tracked[stat] and not seen[stat] then
                    if hasKey(itemStats, statlist[stat]) then
                        table.insert(stats, { stat = statlist[stat], value = CleanNumber(amount) })
                        seen[stat] = true
                    end
                end

                -- Case 2: reforged stat: "+326 Expertise (Reforged from Mastery)"
                local amount2, stat2, fromStat = text:match("^%+([%d,%.]+)%s(.+)%s%((Reforged from .+)%)$")
                if amount2 and stat2 and tracked[stat2] then
                    local from = fromStat:match("Reforged from%s(.+)")
                    table.insert(stats, {
                        stat = statlist[stat2],
                        value = CleanNumber(amount2),
                        reforgedFrom = statlist[from]
                    })
                end
            end
        end
    end

    --equipped gems
    for gemidx = 1, 3 do
        gem = C_Item.GetItemGem(GetInventoryItemLink("player", slot), gemidx)
        if gem then
            table.insert(equippedGems, gem)
        end
    end
    
    -- getting all gems in the item
    for statName, statValue in pairs(itemStats) do
        for color, socket in pairs(socketColorList) do
            if socket == statName then
                for i = 1, statValue do
                    table.insert(sockets, color)
                end
            end
        end
    end

    -- adding prismatic sockets
    if slotId == 6 then
        table.insert(sockets, "prismatic")
    end

    if hasBlackSmithingRequired() then
        if slotId == 10 or slotId == 9 then
            table.insert(sockets, "prismatic")
        end
    end

    local itemData = {}

    table.insert(itemData, {
            slotID = slotId,
            locked = false,
            stats = stats,
            sockets = sockets,
            equippedGems = equippedGems,
            bonus = bonus
        })

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

-- caching all items so they can be scanned
local function cacheEquippedItems()
    for slot = 1, 19 do
        local a = GetInventoryItemID("player", slot)
        if a then
            local b = GetItemInfo(a)
        end
    end
end



local function generate_character_data()
    cacheEquippedItems()

    local data = {}
    
    local _, _, class = UnitClass("player")
    local specIndex = C_SpecializationInfo.GetSpecialization()
    local specID = C_SpecializationInfo.GetSpecializationInfo(specIndex)
    local _, _, race = UnitRace("player")

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
    local allStats = {}

    for _, slotName in ipairs(slots) do
        local slotId = GetInventorySlotInfo(slotName)
        local itemStats = GetItemStatsFromTooltip(slotId)
        if itemStats and #itemStats > 0 then
            allStats[slotName] = itemStats
        end
    end
    
    data['items'] = allStats
    
    local encoded = encode_json(data)
    
    return encoded
end




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

-- Auto-highlight text when shown
infoFrame:SetScript("OnShow", function()
    local text = generate_character_data()
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
