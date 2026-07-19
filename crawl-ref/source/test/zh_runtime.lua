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
