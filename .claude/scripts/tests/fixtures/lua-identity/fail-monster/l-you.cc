LUARET1(you_species, string, species::name(you.species, species::SPNAME_PLAIN, true).c_str())
LUARET1(you_race, string, species::name(you.species, species::SPNAME_PLAIN, true).c_str())
LUARET1(you_class, string, get_job_name_en(you.char_class))
static int l_you_genus(lua_State *ls) { string genus = species::name(you.species, species::SPNAME_GENUS, true); lowercase(genus); if (lua_toboolean(ls, 1)) genus = pluralise(genus); lua_pushstring(ls, genus.c_str()); return 1; }
static int l_you_monster(lua_State *ls) { string name = mons_type_name_en(you.mons_species(), DESC_PLAIN); lua_pushstring(ls, name.c_str()); return 1; }
