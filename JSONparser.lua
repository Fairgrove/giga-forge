-- SimpleJSON.lua

SimpleJSON = {}

local function decode_error(str, i, msg)
    error("JSON decode error at position " .. i .. ": " .. msg)
end

local function skip_whitespace(str, i)
    local _, j = str:find("^[ \n\r\t]*", i)
    return (j or i), str:sub((j or i)+1, (j or i)+1)
end

local function parse_null(str, i)
    if str:sub(i, i+3) == "null" then
        return nil, i + 4
    else
        decode_error(str, i, "expected 'null'")
    end
end

local function parse_true(str, i)
    if str:sub(i, i+3) == "true" then
        return true, i + 4
    else
        decode_error(str, i, "expected 'true'")
    end
end

local function parse_false(str, i)
    if str:sub(i, i+4) == "false" then
        return false, i + 5
    else
        decode_error(str, i, "expected 'false'")
    end
end

local function parse_number(str, i)
    local num_str = str:match("^%-?%d+%.?%d*[eE]?[+%-]?%d*", i)
    if not num_str then
        decode_error(str, i, "invalid number")
    end
    local num = tonumber(num_str)
    if not num then
        decode_error(str, i, "invalid number value")
    end
    return num, i + #num_str
end

local function parse_string(str, i)
    if str:sub(i, i) ~= '"' then
        decode_error(str, i, "expected '\"' to begin string")
    end
    i = i + 1
    local result = ""
    while i <= #str do
        local c = str:sub(i, i)
        if c == '"' then
            return result, i + 1
        elseif c == '\\' then
            local esc = str:sub(i+1, i+1)
            local map = {
                ['"'] = '"', ['\\'] = '\\', ['/'] = '/',
                ['b'] = '\b', ['f'] = '\f', ['n'] = '\n',
                ['r'] = '\r', ['t'] = '\t'
            }
            if map[esc] then
                result = result .. map[esc]
                i = i + 2
            elseif esc == 'u' then
                local hex = str:sub(i+2, i+5)
                if not hex:match("^%x%x%x%x$") then
                    decode_error(str, i, "invalid unicode escape")
                end
                result = result .. utf8.char(tonumber(hex, 16))
                i = i + 6
            else
                decode_error(str, i, "invalid escape character")
            end
        else
            result = result .. c
            i = i + 1
        end
    end
    decode_error(str, i, "unterminated string")
end

local function parse_array(str, i)
    local result = {}
    i = skip_whitespace(str, i)
    if str:sub(i, i) == ']' then
        return result, i + 1
    end
    while true do
        local val
        val, i = SimpleJSON.parse_value(str, i)
        table.insert(result, val)
        i = skip_whitespace(str, i)
        local c = str:sub(i, i)
        if c == ']' then
            return result, i + 1
        elseif c ~= ',' then
            decode_error(str, i, "expected ',' or ']' in array")
        end
        i = i + 1
    end
end

local function parse_object(str, i)
    local result = {}
    i = skip_whitespace(str, i)
    if str:sub(i, i) == '}' then
        return result, i + 1
    end
    while true do
        local key
        key, i = parse_string(str, i)
        i = skip_whitespace(str, i)
        if str:sub(i, i) ~= ':' then
            decode_error(str, i, "expected ':' after key in object")
        end
        i = i + 1
        local val
        val, i = SimpleJSON.parse_value(str, i)
        result[key] = val
        i = skip_whitespace(str, i)
        local c = str:sub(i, i)
        if c == '}' then
            return result, i + 1
        elseif c ~= ',' then
            decode_error(str, i, "expected ',' or '}' in object")
        end
        i = i + 1
    end
end

function SimpleJSON.parse_value(str, i)
    i = skip_whitespace(str, i)
    local c = str:sub(i, i)
    if c == '"' then
        return parse_string(str, i)
    elseif c == '{' then
        return parse_object(str, i + 1)
    elseif c == '[' then
        return parse_array(str, i + 1)
    elseif c == 'n' then
        return parse_null(str, i)
    elseif c == 't' then
        return parse_true(str, i)
    elseif c == 'f' then
        return parse_false(str, i)
    elseif c == '-' or c:match("%d") then
        return parse_number(str, i)
    else
        decode_error(str, i, "unexpected character '" .. c .. "'")
    end
end

function SimpleJSON.decode(str)
    if type(str) ~= "string" then
        error("Expected string to decode")
    end
    local result, i = SimpleJSON.parse_value(str, 1)
    i = skip_whitespace(str, i)
    if i <= #str then
        decode_error(str, i, "trailing garbage")
    end
    return result
end
