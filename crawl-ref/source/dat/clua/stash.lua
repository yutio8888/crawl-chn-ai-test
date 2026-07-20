---------------------------------------------------------------------------
-- stash.lua
-- Annotates items for the stash-tracker's search, and for autopickup
-- exception matches.
--
-- Available annotations:
-- {dropped} for dropped items.
-- {throwable} for items you can throw.
-- {artefact} for artefacts.
-- {ego} for identified branded items.
-- { <skill> } - the relevant weapon skill for weapons.
-- { <num>-handed } - the handedness of the weapon for weapons.
-- { <class> } - item class: gold, weapon, missile, wand, carrion,
--               scroll, jewellery, potion, book, magical staff, orb, misc,
--               <armourtype> armour
-- { <ego> } - short item ego description: rC+, rPois, SInv, freeze etc.
-- {god gift} for god gifts
--
-- Item annotations are always prefixed to the item name. For instance:
-- {artefact} the crystal ball of Wucad Mu
---------------------------------------------------------------------------

-- Annotate items for searches
function ch_stash_search_annotate_item(it)
  local annot = ""

  if it.dropped then
    annot = annot .. "{dropped} "
  end

  if it.ininventory then
    annot = annot .. "{inventory} "
  end

  if it.is_in_shop then
    annot = annot .. "{in_shop} "
  end

  if it.is_throwable then
    annot = annot .. "{throwable} "
  end

  if it.artefact then
    annot = annot .. "{artefact} {artifact} "
  elseif it.branded then
    annot = annot .. "{ego} {branded} "
  end

  if it.is_xp_evoker then
    annot = annot .. "{evoker} "
  end

  if it.god_gift then
    annot = annot .. "{god gift} "
  end

  local skill = it.weap_skill_en
  if skill then
    local skills = crawl.split(skill, ",")
    for i = 1, #skills, 1
    do
        annot = annot .. "{" .. skills[i] .. "} "
    end
    if skill ~= "Throwing" then
      local hands = it.hands
      local hands_adj
      if hands == 2 then
        hands_adj = "two-handed"
      else
        hands_adj = "one-handed"
      end
      annot = annot .. "{" .. hands_adj .. "} "
    end
  end

  local ego = it.ego_en(true) or ""
  if ego ~= "" and ego ~= "unknown" then
    if it.class(true) == "jewellery" then
      annot = annot .. "{" .. ego
      if ego == "Ice" then
        annot = annot .. " rC+ rF-"
      elseif ego == "Fire" then
        annot = annot .. " rF+ rC-"
      elseif ego == "Str" or ego == "Int"
         or ego == "Dex" or ego == "Slay"
         or ego == "EV" or ego == "AC" then
        if it.plus == nil then
          annot = annot .. "+"
        else
          annot = annot .. string.format("%+d", it.plus)
        end
      end
      annot = annot .. "} "
    else
      if ego == "Fly" then
        annot = annot .. "{flight} "
      end
      annot = annot .. "{" .. ego .. "} "
    end
  end

  if it.class(true) == "potion" or it.class(true) == "scroll" then
    local props = {
      ["enlightenment"] = "Will+ flight Fly",
      ["lignification"] = "rPois rTorment rDrown",
      ["resistance"] = "rF+ rC+ rElec rPois rCorr",
      ["revelation"] = "sInv"
    }
    if props[it.subtype_en()] then
      annot = annot .. "{" .. props[it.subtype_en()] .. "} "
    end
  end

  if it.class(true) == "magical staff" and not it.artefact then
    annot = annot .. "{weapon} "
    local props = {
      ["air"] = "rElec",
      ["cold"] = "rC+",
      ["necromancy"] = "rN+",
      ["fire"] = "rF+",
      ["alchemy"] = "rPois"
    }
    if props[it.subtype_en()] then
      annot = annot .. "{" .. props[it.subtype_en()] .. "} "
    end
  end

  if it.class(true) == "armour" and not it.artefact then
    local props = {
      ["troll"] = "Regen+",
      ["steam"] = "rSteam",
      ["acid"] = "rCorr",
      ["quicksilver"] = "Will+",
      ["swamp"] = "rPois",
      ["fire"] = "rF++ rC-",
      ["ice"] = "rC++ rF-",
      ["pearl"] = "rN+",
      ["storm"] = "rElec",
      ["shadow"] = "Stlth+",
      ["golden"] = "rF+ rC+ rPois"
    }
    local t = it.name("base"):match("%a+")
    if props[t] then
      annot = annot .. "{" .. props[t] .. "} "
    end
  end

  if it.class(true) == "armour" then
      annot = annot .. "{" .. it.subtype_en() .. " "
  elseif it.class(true) == "weapon" then
      if it.is_ranged then
        annot = annot .. "{ranged "
      else
        annot = annot .. "{melee "
      end
  else
      annot = annot .. "{"
  end
  annot = annot .. it.class(true) .. "}"

  if it.class(true) == "armour" then
      annot = annot .. " {" .. it.subtype_en() .. " armor}"
      if it.subtype_en() ~= "body" then
          annot = annot .. " {auxiliary armor} {auxiliary armour}"
      end
      if it.is_shield() then
          annot = annot .. " {shield}"
      end
  end

  local resistances = {
    ["Will+"] = "willpower",
    ["rC+"] = "cold",
    ["rCorr"] = "corrosion",
    ["rElec"] = "electricity",
    ["rF+"] = "fire",
    ["rMut"] = "mutation",
    ["rN+"] = "negative energy",
    ["rPois"] = "poison"
  }
  for inscription,res in pairs(resistances) do
    if annot:find(inscription, 1, true) then
      annot = annot .. " {resist " .. res .. "} {" .. res .. " resistance}"
    end
  end

  -- Tag Willpower items as MR for back-compat.
  if annot:find("Will+", 1, true) then
    annot = annot .. " {MR} {resist magic} {magic resistance}"
  end

  -- Tag revelation as mapping for back-compat.
  if it.class(true) == "scroll" and it.subtype_en() == "revelation" then
    annot = annot .. " {magic mapping}"
  end

  return annot
end

--- If you want dumps (.lst files) to be annotated, uncomment this line:
-- ch_stash_dump_annotate_item = ch_stash_search_annotate_item
