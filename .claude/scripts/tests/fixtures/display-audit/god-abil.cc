bool wu_jian_can_wall_jump(string &error_ret, bool blocked)
{
    if (blocked)
    {
        error_ret = "No room to jump.";
        return false;
    }
    error_ret = T_("Translated out parameter.");
    return true;
}
