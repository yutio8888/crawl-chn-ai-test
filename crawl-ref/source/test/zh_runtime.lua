-- Layer 2 runtime translation tests (plan v2 §3).  dlua / -test mode.
--
-- Invoked by `./crawl -test zh_runtime` (build with `make debug -j4`).
-- Requires `-extra-opt-first 'language=zh'` so that the i18n TextDB is
-- loaded before databaseSystemInit() runs (startup.cc:140 → 140 order).
--
-- The dlua VM (init_dungeon_lua, dlua.cc:289-305) exposes a limited API
-- surface. We added crawl.stderr / crawl.t_ / crawl.language /
-- crawl.messages to crawl_dlib (l-crawl.cc:1902-1927) specifically for
-- Layer 2, and use crawl.god_speaks from the existing dlib functions
-- to exercise mprf output paths without needing crawl.sendkeys.
--
-- Full runtime message capture (item ego names, combat messages, god
-- speech triggered by piety changes) is deferred to Layer 3 (RC bot,
-- clua, full API).  This smoke test validates that the infrastructure
-- works: i18n DB loads, T_() returns Chinese, and dlua can capture
-- game-generated message text.
--
-- Run:
--   cd crawl-ref/source && make debug -j4
--   ./crawl -seed 1 -headless -no-save -name test -wizard -no-throttle \
--           -extra-opt-first 'language=zh' -test zh_runtime

local eol = string.char(13)

local function emit(case_id, text)
    if text == nil then text = "<nil>" end
    local one_line = tostring(text):gsub("\r\n", "\\n"):gsub("\n", "\\n")
    crawl.stderr("FRAME_MARKER: " .. case_id .. " | " .. one_line .. eol)
end

-- Gate: only run in wizard mode (matches fsim.lua convention) --------------
if not you.wizard then
    crawl.stderr("FRAME_MARKER: skipped | not in wizard mode" .. eol)
    return
end

-- 1.  Probe: verify i18n DB loaded + T_() returns Chinese -----------------
crawl.stderr("FRAME_MARKER: setup | language=" .. crawl.language()
             .. " t_probe=" .. crawl.t_("You attack %s.") .. eol)

if crawl.t_("You attack %s.") == "You attack %s." then
    crawl.stderr("FRAME_MARKER: error | T_() returns English; i18n DB not loaded"
                 .. eol)
    return
end

-- 2.  Character + level setup -----------------------------------------------
you.init("mifi", "mace")
-- Protocol identities must remain canonical English even while display text is ZH.
assert(you.race() == "Minotaur", "you.race() is not canonical English")
assert(you.species() == "Minotaur", "you.species() is not canonical English")
assert(you.class() == "Fighter", "you.class() is not canonical English")
assert(you.monster() == "minotaur", "you.monster() is not canonical English")
assert(you.genus() == "minotaur", "you.genus() is not canonical English")
emit("lua_identity", table.concat({you.race(), you.species(), you.genus(),
                                   you.class(), you.monster()}, ","))

-- Issue 68 S1: execute the real ZH TextDB entries and their embedded Lua.
crawl.set_test_god("Trog")
assert(you.god() == "Trog", "raw Trog comparison identity changed")
local race_display = crawl.t_(you.race())
local class_display = crawl.t_(you.class())
local god_display = crawl.t_(you.god())
local genus_display = crawl.t_(you.genus())
for raw, display in pairs({[you.race()]=race_display,
                           [you.class()]=class_display,
                           [you.god()]=god_display,
                           [you.genus()]=genus_display}) do
    assert(display ~= raw, "missing dynamic ZH source key: " .. raw)
end
local welcome = crawl.test_hint_text("welcome")
assert(string.find(welcome, race_display, 1, true)
       and string.find(welcome, class_display, 1, true),
       "welcome hint did not render localized race/class")
assert(not string.find(welcome, you.race(), 1, true)
       and not string.find(welcome, you.class(), 1, true),
       "welcome hint leaked raw race/class")
for _, hint_key in ipairs({"dissection reminder", "HINT_CONVERT"}) do
    local hint = crawl.test_hint_text(hint_key)
    assert(string.find(hint, god_display, 1, true),
           hint_key .. " did not render localized god")
    assert(not string.find(hint, you.god(), 1, true),
           hint_key .. " leaked raw god")
end
local web = crawl.test_long_description("A web")
assert(string.find(web, genus_display, 1, true),
       "web description did not render localized singular genus")
assert(not string.find(web, you.genus(), 1, true),
       "web description leaked raw genus")

local race_speech = crawl.test_speak_text(
    "_hostile_orc_beogh_believer_speech_common_")
local genus_speech = crawl.test_speak_text("_vassalage_")
assert(race_speech ~= "" and genus_speech ~= "",
       "production SpeakDB entries did not materialize")
assert(not string.find(race_speech, you.race(), 1, true)
       and not string.find(genus_speech, you.genus(), 1, true),
       "production SpeakDB sample leaked raw dynamic identity")

local original_species = you.species()
for _, species_case in ipairs({
    {"felid", "cat", "Felid"},
    {"octopode", "octopus", "Octopode"},
    {"formicid", "ant", "Formicid"},
    {"barachi", "frog", "Barachi"},
    {"poltergeist", "geist", "Poltergeist"},
}) do
    assert(you.change_species(species_case[1]),
           "could not set dynamic-key species: " .. species_case[1])
    assert(you.genus() == species_case[2],
           "unexpected genus for " .. species_case[1] .. ": " .. you.genus())
    assert(you.race() == species_case[3],
           "raw race comparison identity changed for " .. species_case[1])
    assert(crawl.t_(you.genus()) ~= you.genus(),
           "missing dynamic genus source key: " .. you.genus())
end
assert(you.change_species(original_species), "could not restore test species")
crawl.set_test_god("restore")
emit("display_assets", table.concat({race_display, class_display, god_display,
                                     genus_display}, ",") .. " || "
     .. race_speech .. " || " .. genus_speech .. " || " .. web)

debug.reset_player_data()
debug.goto_place("D:1")
debug.generate_level()
dgn.grid(2, 2, "floor")
-- Exercise the production map placement path, including the vault Lua prelude.
local arrival = dgn.map_by_name("heliophobic_arrival_battle_scene")
assert(arrival, "named vault not found: heliophobic_arrival_battle_scene")
assert(dgn.place_map(arrival, true, true),
       "named vault could not be placed: heliophobic_arrival_battle_scene")
emit("arrival_vault", "heliophobic_arrival_battle_scene placed")
you.moveto(2, 2)
crawl.clear_message_store()

-- Issue 68 S6: exercise the production trove table producer, canonical marker
-- fields, matching, and display path with real item userdata.
local function is_ascii(value)
    if value == false or value == nil then return true end
    for i = 1, #value do
        if string.byte(value, i) > 127 then return false end
    end
    return true
end

local function flat_table_signature(value)
    local fields = {}
    for key, field in pairs(value) do
        assert(type(field) ~= "table",
               "unexpected nested trove item field: " .. tostring(key))
        table.insert(fields, tostring(key) .. "=" .. tostring(field))
    end
    table.sort(fields)
    return table.concat(fields, "\31")
end

local function assert_trove_marker_shape(item, label)
    local field_types = {
        quantity = {number=true},
        base_type = {string=true},
        sub_type = {string=true},
        ego_type = {string=true, boolean=true},
        plus1 = {number=true, boolean=true},
        artefact_name = {string=true, boolean=true},
    }
    if crawl.version("major") == "0.34" then
        field_types.plus2 = {number=true, boolean=true}
    end
    local count = 0
    for field, value in pairs(item) do
        count = count + 1
        assert(field_types[field],
               label .. " marker has unexpected field: " .. tostring(field))
        assert(field_types[field][type(value)],
               label .. " marker field has wrong type: " .. field .. "="
               .. type(value))
    end
    local expected_count = 0
    for field, _ in pairs(field_types) do
        expected_count = expected_count + 1
        assert(item[field] ~= nil, label .. " marker omitted field: " .. field)
    end
    assert(count == expected_count,
           label .. " marker field count changed: " .. count .. " != "
           .. expected_count)
end

-- Load the production .des producer and DLua marker, then run every display
-- case through the real userdata -> persistent table -> TroveMarker path.
assert(dgn.map_by_name("due_enter_trove_mix"),
       "production trove vault was not loaded")
crawl_require("dlua/lm_trove.lua")
assert(trove and trove.get_trove_item and TroveMarker,
       "production trove producer/marker was not initialized")
local invalid_horn_quantity = pcall(items.trove_name, "miscellaneous",
                                    "horn of Geryon", 2, false, false, true)
assert(not invalid_horn_quantity,
       "trove renderer accepted an impossible stacked horn marker")

local trove_cases = {
    {label="quantity", spec="scroll of acquirement q:2 pre_id"},
    {label="plus", spec="golden dragon scales plus:4 pre_id"},
    {label="rune", spec="slimy rune of Zot", rune=true},
    {label="horn", spec="horn of Geryon", horn=true},
    {label="ego", spec="war axe ego:flaming plus:2 pre_id"},
    {label="jewellery", spec="ring of protection plus:3 pre_id"},
    {label="demon", spec="demon whip ego:flaming plus:3 pre_id", demon=true},
    {label="demon_alternative", spec="demon blade ego:flaming plus:3 pre_id",
     demon=true},
}
local trove_marker_ids = {
    quantity = "trove_quantity",
    plus = "trove_plus",
    rune = "trove_rune",
    horn = "trove_horn",
    ego = "trove_ego",
    jewellery = "trove_jewellery",
    demon = "trove_demon_weapon",
    demon_alternative = "trove_demon_alternative",
}
local demon_toll_marker
for index, trove_case in ipairs(trove_cases) do
    local x, y = 3 + index, 4
    dgn.create_item(x, y, trove_case.spec)
    local produced = dgn.items_at(x, y)
    assert(#produced == 1,
           "could not create trove item: " .. trove_case.spec)
    local source_item = produced[1]
    local marker_item = trove.get_trove_item(nil, 0, source_item)
    if trove_case.rune then
        assert(marker_item.base_type == "miscellaneous"
               and marker_item.sub_type == "rune of Zot",
               "real rune producer did not preserve trove marker protocol")
    end
    for field, value in pairs(marker_item) do
        if type(value) == "string" then
            assert(is_ascii(value),
                   "trove marker field was localized: " .. tostring(field)
                   .. "=" .. value)
        end
    end

    local marker = TroveMarker:new {
        toll = {type="item", item=marker_item},
        desc = "treasure trove",
        toll_desc = "to enter a treasure trove",
    }
    assert_trove_marker_shape(marker_item, trove_case.label)
    local original_signature = flat_table_signature(marker_item)
    local displays = {}
    for _, language in ipairs({"en", "zh"}) do
        crawl.set_test_language(language)
        local plain = marker:item_name(false)
        local grammatical = marker:item_name()
        local expected_plain
        local expected_grammar
        if trove_case.demon then
            expected_plain = string.format("%+d %s", marker_item.plus1,
                                           crawl.t_("demon weapon"))
            expected_grammar = crawl.grammar(expected_plain, "a")
        elseif trove_case.horn then
            expected_plain = source_item.name("db")
            expected_grammar = crawl.grammar(expected_plain, "the")
        else
            expected_plain = source_item.name("plain")
            expected_grammar = source_item.name(trove_case.rune and "the" or "a")
        end
        assert(plain == expected_plain,
               trove_case.label .. " plain display mismatch in " .. language
               .. ": " .. plain .. " != " .. expected_plain)
        assert(grammatical == expected_grammar,
               trove_case.label .. " grammatical display mismatch in "
               .. language .. ": " .. grammatical .. " != "
               .. expected_grammar)
        assert(flat_table_signature(marker_item) == original_signature,
               trove_case.label .. " display modified persistent marker")
        if language == "zh" then
            assert(not is_ascii(plain),
                   trove_case.label .. " display was not localized")
        end
        table.insert(displays, plain)
    end

    local loaded_marker = crawl.roundtrip_trove_marker(marker)
    local loaded_item = get_toll(loaded_marker).item
    assert_trove_marker_shape(loaded_item, trove_case.label .. " loaded")
    assert(flat_table_signature(loaded_item) == original_signature,
           trove_case.label .. " marker changed during save/load")
    assert(loaded_marker:item_name(false) == displays[2],
           trove_case.label .. " display changed after save/load")

    if trove_case.rune then
        assert(not marker:search_for_rune(),
               "rune search accepted an unobtained rune")
        crawl.set_test_rune(marker_item.plus1, true)
        assert(marker:search_for_rune(),
               "rune search rejected the requested obtained rune")
        crawl.set_test_rune(marker_item.plus1, false)
    else
        local accepted = marker:search_for_item(nil, nil, {source_item})
        assert(#accepted == 1 and accepted[1] == source_item,
               trove_case.label .. " search rejected its production item")
        if trove_case.label == "quantity" then
            accepted[1].dec_quantity(marker_item.quantity)
            assert(#dgn.items_at(x, y) == 0,
                   "trove quantity consume did not remove the requested stack")
        end
    end
    if trove_case.label == "demon" then
        demon_toll_marker = marker
    elseif trove_case.label == "demon_alternative" then
        local alternative = demon_toll_marker:search_for_item(
            nil, nil, {source_item})
        assert(#alternative == 1 and alternative[1] == source_item,
               "demon whip toll rejected interchangeable demon blade")
    end
    emit(trove_marker_ids[trove_case.label],
         tostring(marker_item.base_type) .. " || "
         .. tostring(marker_item.sub_type) .. " || "
         .. tostring(marker_item.ego_type) .. " || " .. displays[2])
end
crawl.set_test_language("zh")

-- Issue 68 S8: protocol accessors are covered by the RC fixture; exercise the
-- paired production C++ display helpers here to prove they remain localized.
local trap_display = crawl.test_trap_display_name("permanent teleport")
assert(not is_ascii(trap_display) and trap_display ~= "permanent teleport",
       "trap UI helper did not remain localized")
for _, cloud_name in ipairs({
    "noxious fumes", "freezing vapour", "foul pestilence",
}) do
    local cloud_display = crawl.test_cloud_display_name(cloud_name)
    assert(not is_ascii(cloud_display) and cloud_display ~= cloud_name,
           "cloud UI helper did not remain localized: " .. cloud_name)
end

-- Issue 68 S7: capture a real unidentified item, round-trip the production
-- trigger serializer, then change identification state and language.
dgn.create_item(11, 3, "scroll of blinking q:2")
local trigger_items = dgn.items_at(11, 3)
assert(#trigger_items == 1, "could not create trigger identity item")
local trigger_item = trigger_items[1]
assert(not trigger_item.is_identified, "trigger fixture unexpectedly identified")
local canonical_target = trigger_item.marker_identity()
assert(is_ascii(canonical_target), "marker identity is not canonical ASCII")
assert(canonical_target == "scroll of blinking",
       "unexpected canonical marker identity: " .. canonical_target)
assert(trigger_item.quantity == 2, "trigger quantity fixture was not stacked")
trigger_item.inc_quantity(1)
assert(trigger_item.quantity == 3
       and trigger_item.marker_identity() == canonical_target,
       "quantity changed marker identity")
assert(trigger_item.inscribe("fixture note", false),
       "could not add trigger fixture inscription")
assert(trigger_item.marker_identity() == canonical_target,
       "inscription changed marker identity")

local trigger_marker = {
    pos = function () return 11, 3 end,
}
local auto_trigger = DgnTriggerer:new {
    type = "item_pickup", target = "auto",
}
auto_trigger:capture_item_target(trigger_marker)
assert(auto_trigger.target == canonical_target,
       "target=auto did not store canonical marker identity")
local loaded_trigger = crawl.roundtrip_dgn_triggerer(auto_trigger)
assert(loaded_trigger.target == canonical_target,
       "save/load changed canonical marker identity")

wiz.identify_all_items()
assert(trigger_item.is_identified, "fixture item was not identified")
crawl.set_test_language("en")
assert(loaded_trigger:item_target_matches(trigger_item),
       "ZH capture did not survive EN load/identification")
crawl.set_test_language("zh")
assert(loaded_trigger:item_target_matches(trigger_item),
       "canonical trigger did not survive return to ZH")

local legacy_en = DgnTriggerer:new {
    type = "item_moved", target = trigger_item.name_en(),
}
assert(legacy_en:item_target_matches(trigger_item),
       "legacy English item target fallback failed")
local legacy_zh = DgnTriggerer:new {
    type = "item_moved", target = trigger_item.name(),
}
assert(legacy_zh:item_target_matches(trigger_item),
       "legacy Chinese same-language target fallback failed")
crawl.clear_message_store()
local loaded_legacy_zh = crawl.roundtrip_dgn_triggerer(legacy_zh)
assert(loaded_legacy_zh.target == legacy_zh.target,
       "legacy Chinese target changed during save/load")
crawl.set_test_language("en")
assert(not loaded_legacy_zh:item_target_matches(trigger_item),
       "legacy Chinese marker was guessed across languages")
crawl.set_test_language("zh")
assert(loaded_legacy_zh:item_target_matches(trigger_item),
       "legacy Chinese marker no longer matched in its original language")
emit("item_trigger_identity",
     canonical_target .. " || legacy_zh=" .. legacy_zh.target)

-- Issue 68 S3: canonical status queries coexist with localized status lists.
crawl.set_test_duration("immotile")
local immotile_display = you.status()
assert(not is_ascii(immotile_display)
       and you.status(immotile_display),
       "player status rejected its exact current display value")
crawl.set_test_duration("mighty")
assert(you.status("immotile"), "canonical immotile status query failed")
assert(you.status("mighty"), "canonical mighty status query failed")
assert(not you.status("issue68-unknown"), "unknown status query was accepted")
local status_display = you.status()
assert(not is_ascii(status_display), "status display was not localized")
assert(not string.find(status_display, "immotile", 1, true),
       "status display leaked canonical immotile key")
emit("status_boundary", "immotile=true mighty=true || " .. status_display)

-- Issue 68 S4: DLua legacy names stay canonical while display_name is ZH.
dgn.reset_level()
dgn.fill_grd_area(1, 1, dgn.GXM - 2, dgn.GYM - 2, "floor")
you.moveto(18, 18)
local protocol_monster = dgn.create_monster(20, 20, "orc priest perm_ench:haste")
assert(protocol_monster, "could not create protocol monster")
assert(protocol_monster.name == "orc priest",
       "DLua monster name is not canonical English")
assert(protocol_monster.full_name == "orc priest",
       "DLua monster full_name is not canonical English")
assert(protocol_monster.type_name == "orc priest",
       "DLua monster type_name is not canonical English")
assert(not is_ascii(protocol_monster.display_name),
       "DLua monster display_name was not localized")
local protocol_moninfo = protocol_monster.get_info()
assert(protocol_moninfo:status("fast"),
       "monster status rejected canonical fast key")
assert(not protocol_moninfo:status("issue68-unknown"),
       "monster status accepted an unknown key")
local monster_status_display = protocol_moninfo:status()
assert(not is_ascii(monster_status_display),
       "monster status display was not localized")
assert(not string.find(monster_status_display, "fast", 1, true),
       "monster status display leaked canonical fast key")
local slow_monster = dgn.create_monster(21, 20, "orc perm_ench:slow")
local slow_info = slow_monster and slow_monster.get_info()
assert(slow_info and slow_info:status("slow"),
       "monster status rejected canonical slow key")
local slow_display = slow_info:status()
local slow_display_key = string.match(slow_display, "^[^,]+")
slow_display_key = string.gsub(slow_display_key, "%s+$", "")
assert(not is_ascii(slow_display_key) and slow_info:status(slow_display_key),
       "monster status rejected its exact current display value")
local possessive_monster = dgn.create_monster(22, 20,
                                              "orc perm_ench:pain_bond")
assert(possessive_monster
       and possessive_monster.get_info():status("sharing its pain"),
       "monster status lost canonical possessive attribute")
local bullseye_monster = dgn.create_monster(
    23, 20, "orc perm_ench:bullseye_target")
assert(bullseye_monster
       and bullseye_monster.get_info():is("bullseye_target"),
       "bullseye consumer flag was not exposed as raw identity")
crawl_require("dlua/explorer.lua")
local old_mons_notable = explorer.mons_notable
local old_rare_ood = explorer.rare_ood
explorer.mons_notable = function () return true end
explorer.rare_ood = function () return false end
local explorer_monster = dgn.create_monster(36, 20, "butterfly")
assert(explorer_monster, "could not create explorer display monster")
local explorer_display = explorer.describe_mons(explorer_monster)
explorer.mons_notable = old_mons_notable
explorer.rare_ood = old_rare_ood
assert(explorer_display
       and string.find(explorer_display, explorer_monster.display_name, 1, true),
       "explorer did not use the localized monster display sink")
assert(not string.find(explorer_display, explorer_monster.type_name, 1, true),
       "explorer leaked canonical monster identity")

-- Exercise the production monster_dies listener with the canonical full_name
-- exposed by DLua.  Registering the marker during a -test level requires an
-- explicit activation, matching map_markers::activate_all on normal entry.
crawl_require("dlua/lm_monst.lua")
local death_spawn = monster_on_death {
    target = "orc",
    new_monster = "butterfly",
}
dgn.gridmark(34, 22, "floor", death_spawn)
local death_marker = dgn.marker_at_pos(34, 22)
assert(death_marker, "could not register monster death marker")
death_spawn:activate(death_marker)
local death_target = dgn.create_monster(35, 22, "orc")
assert(death_target and death_target.full_name == "orc",
       "monster death target identity was not canonical")
death_target.dismiss()
local death_result = dgn.mons_at(34, 22)
assert(death_result and death_result.type_name == "butterfly",
       "canonical monster death trigger did not fire")

local monster_identity_cases = {
    {"orc wizard", "orc wizard"},
    {"butterfly", "butterfly"},
    {"orb of destruction", "orb of destruction"},
    {"ballistomycete", "ballistomycete"},
    {"plant", "plant"},
    {"fungus", "fungus"},
    {"bush", "bush"},
    {"player ghost", "player ghost", true},
    {"pandemonium lord", "pandemonium lord", true},
    {"dancing weapon ; long sword", "dancing weapon"},
}
local monster_types = {}
for index, identity_case in ipairs(monster_identity_cases) do
    local mon = dgn.create_monster(24 + index, 20, identity_case[1])
    assert(mon, "could not create identity monster: " .. identity_case[1])
    assert(mon.type_name == identity_case[2],
           "DLua type_name was not canonical: " .. identity_case[1])
    assert(identity_case[3] or not is_ascii(mon.display_name),
           "DLua display_name was not localized: " .. identity_case[1])
    local info = mon.get_info()
    assert(info, "could not get monster.info: " .. identity_case[1])
    assert(identity_case[3] or not is_ascii(info:display_name()),
           "monster.info display_name was not localized: " .. identity_case[1])
    table.insert(monster_types, mon.type_name)
end
emit("monster_boundary",
     protocol_monster.name .. " || " .. protocol_monster.display_name
     .. " || " .. monster_status_display .. " || "
     .. table.concat(monster_types, ",") .. " || death="
     .. death_result.type_name)

-- Issue 68 S2: all three canonical Zot bindings drive the real production
-- multi-branch vault, while the overview remains localized.
local zot_cases = {
    {"fire", "orb of fire", "orbs of fire"},
    {"winter", "orb of winter", "orbs of winter"},
    {"entropy", "orb of entropy", "orbs of entropy"},
}
local zot_evidence = {}
local zot_overview
for _, zot_case in ipairs(zot_cases) do
    crawl.set_zot_orb_monster(zot_case[1])
    assert(dgn.zot_orb_type() == zot_case[2],
           "dgn.zot_orb_type localized " .. zot_case[1])
    local zot_plural = you.zot_orb_monster()
    assert(zot_plural == zot_case[3],
           "you.zot_orb_monster morphology failed " .. zot_case[1]
           .. ": " .. tostring(zot_plural))
    local milestone = crawl.zot_milestone()
    assert(milestone == "will face " .. zot_case[3],
           "Zot milestone identity failed " .. zot_case[1]
           .. ": " .. tostring(milestone))
    local found = false
    for attempt = 1, 40 do
        dgn.reset_level()
        dgn.fill_grd_area(1, 1, dgn.GXM - 2, dgn.GYM - 2, "floor")
        local zot_map = dgn.map_by_name("chapayev_index_zotdef_columnade")
        assert(zot_map, "production Zot fixture vault not found")
        assert(dgn.place_map(zot_map, true, true),
               "production Zot fixture vault could not be placed")
        for y = 1, dgn.GYM - 2 do
            for x = 1, dgn.GXM - 2 do
                local mon = dgn.mons_at(x, y)
                if mon and mon.type_name == zot_case[2] then
                    found = true
                end
            end
        end
        if found then break end
    end
    assert(found, "Zot vault branch omitted " .. zot_case[2])
    zot_overview = crawl.zot_overview()
    local localized_orb = crawl.t_(zot_case[2])
    assert(not is_ascii(localized_orb),
           "missing localized Zot orb name: " .. zot_case[2])
    assert(string.find(zot_overview, localized_orb, 1, true),
           "Zot overview omitted localized orb name: " .. localized_orb)
    assert(not string.find(zot_overview, "orbs of ", 1, true),
           "Zot overview used English plural morphology")
    table.insert(zot_evidence, zot_case[2])
end
assert(not is_ascii(zot_overview), "Zot overview was not localized")
emit("zot_boundary", table.concat(zot_evidence, ",")
     .. " || " .. zot_overview)
crawl.set_zot_orb_monster("restore")

-- 3.  Capture level-up messages from you.set_xl(20) ------------------------
-- Produces ~19 "你已达到 N 级！" messages through mprf via gain_exp →
-- set_xl. These are all T_()-wrapped and provide a strong baseline
-- verification that runtime mprf output includes Chinese text.
you.set_xl(20)
crawl.redraw_view()
local msgs1 = crawl.messages(30) or ""
emit("level_up", msgs1)
crawl.clear_message_store()

-- 4.  Use case: crawl.god_speaks (synthetic mprf path) -------------------
-- Sends raw text through god_speaks → mprf, exercising the message
-- delivery path that Layer 1 Catch2 can't reach.
crawl.god_speaks("Trog", "Trog bestows a gift upon you!")
crawl.redraw_view()
local msgs2 = crawl.messages(5) or ""
emit("godspeak_trog", msgs2)
crawl.clear_message_store()

crawl.god_speaks("Xom", "Xom thinks this is hilarious!")
crawl.redraw_view()
local msgs3 = crawl.messages(5) or ""
emit("godspeak_xom", msgs3)

-- Mark test complete -----------------------------------------------------
crawl.stderr("FRAME_MARKER: end | ok" .. eol)
