// This display producer is intentionally outside the five Lua bindings.
string display_name(monster_type m) { return mons_type_name(m, DESC_PLAIN); }
