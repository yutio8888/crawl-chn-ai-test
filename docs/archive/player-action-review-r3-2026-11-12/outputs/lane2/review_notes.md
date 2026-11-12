# 第三轮 lane2 审查

模型：GPT-6 / Codex；精确模型后缀、温度和推理配置未由运行时提供。

Glossary SHA-256：fb814f3252f249fc230e81fa132dce6a9bb194b014d687fc1524c66827b351d7。已运行 context_resolve，非盲评。

固定基线 stable 4af734c175cee41cfaf75142e04bf1a9aea9ee1c，trunk 40a7b9976ad10aade1a703e510c68ed0667d3ca5。只读仓库，仅使用 lane2 输入。

方法：分段提取英文模板、生产调用和参数生成，逐族判断；高风险所有格、动作词、程度词、可选后缀和顺序改写进行静态参数还原。以下示例不是运行时截屏；形如商店名称的是有明确类型的符号值，不伪称固定的实际商店名。未运行游戏，不认证像素排版、所有终端宽度或未枚举状态。

输入更正：A-01 的危险地形句使用关闭的门不是可达状态；D-05 自动抓取的 false/n 属外层 yesno，不能作为 printf 实参；E-05 hands_act 使用完整中文动作键；stable F-02 的 amulet 英文则确实由生产源码产生。

D-HERE 共76组，独立于72个随机族计数。列表标题与普通单栈物品提示分别判断，未将此处列为禁词。所有结论只覆盖本批样本，不外推全库。


## E-02 — ok


### stable

完整英文：
```text
You attempt to bind %s soul, but %s is merely a clone!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3392}

参数表达式与来源：
```text
T_("You attempt to bind %s soul, but %s is merely a clone!")
mons->name(DESC_ITS).c_str()
mons->pronoun(PRONOUN_SUBJECTIVE).c_str()
3367:                                    _yred_hurl_torchlight_power(),
3368:                                    false, nullptr, target, fail);
3369:
3370:         if (result == spret::success)
3371:             you.props[YRED_TORCH_POWER_KEY].get_int() -= 1;
3372:
3373:         return result;
3374:     }
3375:
3376:     case ABIL_YRED_FATHOMLESS_SHACKLES:
3377:         fail_check();
3378:         mprf(MSGCH_DURATION, T_("You call down Yredelemnul's inexorable grip."));
3379:         // XXX: Some invo formula
3380:         you.duration[DUR_FATHOMLESS_SHACKLES] = random_range(15, 25) * BASELINE_DELAY;
3381:         yred_make_blasphemy();
3382:         invalidate_agrid(true);
3383:         break;
3384:
3385:     case ABIL_YRED_BIND_SOUL:
3386:     {
3387:         monster* mons = monster_at(beam.target);
3388:
3389:         if (mons && you.can_see(*mons) && mons->is_illusion())
3390:         {
3391:             fail_check();
3392:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3393:                  mons->name(DESC_ITS).c_str(),
3394:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3395:             // Still costs a turn to gain the information.
3396:             return spret::success;
3397:         }
3398:
3399:         fail_check();
3400:
3401:         int pain = you.hp / 3;
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
```

当前中文模板：你试图束缚%s灵魂，但%s只是个克隆体！

输入还原：None


### trunk

完整英文：
```text
You attempt to bind %s soul, but %s is merely a clone!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3534}

参数表达式与来源：
```text
T_("You attempt to bind %s soul, but %s is merely a clone!")
mons->name(DESC_ITS).c_str()
mons->pronoun(PRONOUN_SUBJECTIVE).c_str()
3509:                                    _yred_hurl_torchlight_power(),
3510:                                    false, nullptr, target, fail);
3511:
3512:         if (result == spret::success)
3513:             you.props[YRED_TORCH_POWER_KEY].get_int() -= 1;
3514:
3515:         return result;
3516:     }
3517:
3518:     case ABIL_YRED_FATHOMLESS_SHACKLES:
3519:         fail_check();
3520:         mprf(MSGCH_DURATION, T_("You call down Yredelemnul's inexorable grip."));
3521:         // XXX: Some invo formula
3522:         you.duration[DUR_FATHOMLESS_SHACKLES] = random_range(15, 25) * BASELINE_DELAY;
3523:         yred_make_blasphemy();
3524:         invalidate_agrid();
3525:         break;
3526:
3527:     case ABIL_YRED_BIND_SOUL:
3528:     {
3529:         monster* mons = monster_at(beam.target);
3530:
3531:         if (mons->is_illusion())
3532:         {
3533:             fail_check();
3534:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3535:                  mons->name(DESC_ITS).c_str(),
3536:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3537:             // Still costs a turn to gain the information.
3538:             return spret::success;
3539:         }
3540:
3541:         fail_check();
3542:
3543:         int pain = you.hp / 3;
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
```

当前中文模板：你试图束缚%s灵魂，但%s只是个克隆体！

输入还原：None

独立判断与参数还原：DESC_ITS 提供兽人的、主格提供他/它：你试图束缚兽人的灵魂，但他只是个克隆体！已保留只是、克隆及目标灵魂。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-03 — objective_error


### stable

完整英文：
```text
%s %s shatters into small pieces.
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 896}

参数表达式与来源：
```text
T_("%s %s shatters into small pieces.")
agent() && agent()->is_player() ? T_("The") : T_("Some")
wall.c_str()
871:                 {
872:                     mprf(MSGCH_SOUND, T_("You hear a grinding noise."));
873:                     obvious_effect = true; // You may still see the caster.
874:                     msg_generated = true;
875:                 }
876:                 return;
877:             }
878:
879:             obvious_effect = true;
880:             msg_generated = true;
881:
882:             string wall;
883:             if (feat == DNGN_GRATE)
884:             {
885:                 // XXX: should this change for monsters?
886:                 mpr(T_("The damaged grate falls apart."));
887:                 return;
888:             }
889:             else if (feat == DNGN_SLIMY_WALL)
890:                 wall = T_("slime");
891:             else if (player_in_branch(BRANCH_PANDEMONIUM))
892:                 wall = T_("weird stuff");
893:             else
894:                 wall = T_("rock");
895:
896:             mprf(T_("%s %s shatters into small pieces."),
897:                  agent() && agent()->is_player() ? T_("The") : T_("Some"),
898:                  wall.c_str());
899:         }
900:     }
901:     else if (feat_is_wall(feat))
902:         finish_beam();
903: }
904:
905: void bolt::burn_wall_effect()
906: {
907:     dungeon_feature_type feat = env.grid(pos());
908:     // Fire only affects things that can burn.
909:     if (!feat_is_flammable(feat)
910:         || env.markers.property_at(pos(), MAT_ANY, "veto_destroy") == "veto"
911:         || !can_burn_trees()) // sanity
912:     {
913:         finish_beam();
914:         return;
915:     }
916:
917:     if (have_passive(passive_t::shoot_through_plants))
918:     {
919:         emit_message(T_("Fedhas protects the tree from harm."));
920:         finish_beam();
921:         return;
922:     }
923:
```

当前中文模板：%s%s碎成了小片。

输入还原：None

完整英文：
```text
The
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 896}

参数表达式与来源：
```text
T_("%s %s shatters into small pieces.")
agent() && agent()->is_player() ? T_("The") : T_("Some")
wall.c_str()
871:                 {
872:                     mprf(MSGCH_SOUND, T_("You hear a grinding noise."));
873:                     obvious_effect = true; // You may still see the caster.
874:                     msg_generated = true;
875:                 }
876:                 return;
877:             }
878:
879:             obvious_effect = true;
880:             msg_generated = true;
881:
882:             string wall;
883:             if (feat == DNGN_GRATE)
884:             {
885:                 // XXX: should this change for monsters?
886:                 mpr(T_("The damaged grate falls apart."));
887:                 return;
888:             }
889:             else if (feat == DNGN_SLIMY_WALL)
890:                 wall = T_("slime");
891:             else if (player_in_branch(BRANCH_PANDEMONIUM))
892:                 wall = T_("weird stuff");
893:             else
894:                 wall = T_("rock");
895:
896:             mprf(T_("%s %s shatters into small pieces."),
897:                  agent() && agent()->is_player() ? T_("The") : T_("Some"),
898:                  wall.c_str());
899:         }
900:     }
901:     else if (feat_is_wall(feat))
902:         finish_beam();
903: }
904:
905: void bolt::burn_wall_effect()
906: {
907:     dungeon_feature_type feat = env.grid(pos());
908:     // Fire only affects things that can burn.
909:     if (!feat_is_flammable(feat)
910:         || env.markers.property_at(pos(), MAT_ANY, "veto_destroy") == "veto"
911:         || !can_burn_trees()) // sanity
912:     {
913:         finish_beam();
914:         return;
915:     }
916:
917:     if (have_passive(passive_t::shoot_through_plants))
918:     {
919:         emit_message(T_("Fedhas protects the tree from harm."));
920:         finish_beam();
921:         return;
922:     }
923:
```

当前中文模板：None

输入还原：None

完整英文：
```text
Some
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 896}

参数表达式与来源：
```text
T_("%s %s shatters into small pieces.")
agent() && agent()->is_player() ? T_("The") : T_("Some")
wall.c_str()
871:                 {
872:                     mprf(MSGCH_SOUND, T_("You hear a grinding noise."));
873:                     obvious_effect = true; // You may still see the caster.
874:                     msg_generated = true;
875:                 }
876:                 return;
877:             }
878:
879:             obvious_effect = true;
880:             msg_generated = true;
881:
882:             string wall;
883:             if (feat == DNGN_GRATE)
884:             {
885:                 // XXX: should this change for monsters?
886:                 mpr(T_("The damaged grate falls apart."));
887:                 return;
888:             }
889:             else if (feat == DNGN_SLIMY_WALL)
890:                 wall = T_("slime");
891:             else if (player_in_branch(BRANCH_PANDEMONIUM))
892:                 wall = T_("weird stuff");
893:             else
894:                 wall = T_("rock");
895:
896:             mprf(T_("%s %s shatters into small pieces."),
897:                  agent() && agent()->is_player() ? T_("The") : T_("Some"),
898:                  wall.c_str());
899:         }
900:     }
901:     else if (feat_is_wall(feat))
902:         finish_beam();
903: }
904:
905: void bolt::burn_wall_effect()
906: {
907:     dungeon_feature_type feat = env.grid(pos());
908:     // Fire only affects things that can burn.
909:     if (!feat_is_flammable(feat)
910:         || env.markers.property_at(pos(), MAT_ANY, "veto_destroy") == "veto"
911:         || !can_burn_trees()) // sanity
912:     {
913:         finish_beam();
914:         return;
915:     }
916:
917:     if (have_passive(passive_t::shoot_through_plants))
918:     {
919:         emit_message(T_("Fedhas protects the tree from harm."));
920:         finish_beam();
921:         return;
922:     }
923:
```

当前中文模板：None

输入还原：None


### trunk

完整英文：
```text
The %s shatters into small pieces.
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 981}

参数表达式与来源：
```text
agent() && agent()->is_player()
                     ? T_("The %s shatters into small pieces.")
                     : T_("Some %s shatters into small pieces.")
wall.c_str()
956:                 {
957:                     mprf(MSGCH_SOUND, T_("You hear a grinding noise."));
958:                     obvious_effect = true; // You may still see the caster.
959:                     msg_generated = true;
960:                 }
961:                 return;
962:             }
963:
964:             obvious_effect = true;
965:             msg_generated = true;
966:
967:             string wall;
968:             if (feat == DNGN_GRATE)
969:             {
970:                 // XXX: should this change for monsters?
971:                 mpr(T_("The damaged grate falls apart."));
972:                 return;
973:             }
974:             else if (feat == DNGN_SLIMY_WALL)
975:                 wall = T_("slime");
976:             else if (player_in_branch(BRANCH_PANDEMONIUM))
977:                 wall = T_("weird stuff");
978:             else
979:                 wall = T_("rock");
980:
981:             mprf(agent() && agent()->is_player()
982:                      ? T_("The %s shatters into small pieces.")
983:                      : T_("Some %s shatters into small pieces."),
984:                  wall.c_str());
985:         }
986:     }
987:     else if (feat_is_wall(feat))
988:         finish_beam();
989: }
990:
991: void bolt::burn_wall_effect()
992: {
993:     dungeon_feature_type feat = env.grid(pos());
994:     // Fire only affects things that can burn.
995:     if (!feat_is_flammable(feat)
996:         || env.markers.property_at(pos(), MAT_ANY, "veto_destroy") == "veto"
997:         || !can_burn_trees()) // sanity
998:     {
999:         finish_beam();
1000:         return;
1001:     }
1002:
1003:     if (have_passive(passive_t::shoot_through_plants))
1004:     {
1005:         emit_message(T_("Fedhas protects the tree from harm."));
1006:         finish_beam();
1007:         return;
1008:     }
1009:
```

当前中文模板：%s碎成了小片。

输入还原：None

完整英文：
```text
Some %s shatters into small pieces.
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 981}

参数表达式与来源：
```text
agent() && agent()->is_player()
                     ? T_("The %s shatters into small pieces.")
                     : T_("Some %s shatters into small pieces.")
wall.c_str()
956:                 {
957:                     mprf(MSGCH_SOUND, T_("You hear a grinding noise."));
958:                     obvious_effect = true; // You may still see the caster.
959:                     msg_generated = true;
960:                 }
961:                 return;
962:             }
963:
964:             obvious_effect = true;
965:             msg_generated = true;
966:
967:             string wall;
968:             if (feat == DNGN_GRATE)
969:             {
970:                 // XXX: should this change for monsters?
971:                 mpr(T_("The damaged grate falls apart."));
972:                 return;
973:             }
974:             else if (feat == DNGN_SLIMY_WALL)
975:                 wall = T_("slime");
976:             else if (player_in_branch(BRANCH_PANDEMONIUM))
977:                 wall = T_("weird stuff");
978:             else
979:                 wall = T_("rock");
980:
981:             mprf(agent() && agent()->is_player()
982:                      ? T_("The %s shatters into small pieces.")
983:                      : T_("Some %s shatters into small pieces."),
984:                  wall.c_str());
985:         }
986:     }
987:     else if (feat_is_wall(feat))
988:         finish_beam();
989: }
990:
991: void bolt::burn_wall_effect()
992: {
993:     dungeon_feature_type feat = env.grid(pos());
994:     // Fire only affects things that can burn.
995:     if (!feat_is_flammable(feat)
996:         || env.markers.property_at(pos(), MAT_ANY, "veto_destroy") == "veto"
997:         || !can_burn_trees()) // sanity
998:     {
999:         finish_beam();
1000:         return;
1001:     }
1002:
1003:     if (have_passive(passive_t::shoot_through_plants))
1004:     {
1005:         emit_message(T_("Fedhas protects the tree from harm."));
1006:         finish_beam();
1007:         return;
1008:     }
1009:
```

当前中文模板：一些%s碎成了小片。

输入还原：None

独立判断与参数还原：The/Some 没有对应单词中文键，T_ 回退英文，与中文材料名混排。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "untranslated_parameter", "line": "stable", "english": "%s %s shatters into small pieces.", "current_full_zh": "The岩石碎成了小片。 / Some黏液碎成了小片。", "problem": "The/Some 没有对应单词中文键，T_ 回退英文，与中文材料名混排。", "suggested_zh": "岩石碎成了小片。 / 一些黏液碎成了小片。", "evidence": "stable beam.cc:896-898；source.txt 无 The、Some 独立键；trunk 已改成完整句。", "defect_points": 1}


## C-06 — ok


### stable

完整英文：
```text
You %s %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 1634}

参数表达式与来源：
```text
T_("You %s %s.")
item_unequip_verb(*item).c_str()
item->name(DESC_YOUR).c_str()
1609:     for (const item_def* item : to_remove)
1610:         if (_is_slow_equip(*item))
1611:             needs_delay = true;
1612:
1613:     const bool is_multi = (to_equip != nullptr && !to_remove.empty())
1614:                             || to_remove.size() > 1;
1615:
1616:     // Removals happen first
1617:     if (!to_remove.empty())
1618:     {
1619:         // We remove items in reverse of the order they are selected, to account
1620:         // for chain removals (ie: removing our third ring before removing the
1621:         // Macabre Finger)
1622:         for (int i = to_remove.size() - 1; i >= 0; --i)
1623:         {
1624:             item_def* item = to_remove[i];
1625:             if (_is_slow_equip(*item))
1626:                 start_delay<EquipOffDelay>(ARMOUR_EQUIP_DELAY, *item);
1627:             // If this removal is queued after another removal, it needs to use
1628:             // a delay. (This means it takes 10 aut instead of 5, but this should
1629:             // matter so rarely that I'm not sure it's worth fixing?)
1630:             else if (needs_delay)
1631:                 start_delay<EquipOffDelay>(1, *item);
1632:             else
1633:             {
1634:                 mprf(T_("You %s %s."),
1635:                      item_unequip_verb(*item).c_str(),
1636:                      item->name(DESC_YOUR).c_str());
1637:                 unequip_item(*item);
1638:             }
1639:         }
1640:     }
1641:
1642:     if (to_equip)
1643:     {
1644:         if (_is_slow_equip(*to_equip))
1645:             start_delay<EquipOnDelay>(ARMOUR_EQUIP_DELAY, *to_equip, equip_slot);
1646:         else if (needs_delay)
1647:             start_delay<EquipOnDelay>(1, *to_equip, equip_slot);
1648:         else
1649:             equip_item(equip_slot, to_equip->link);
1650:     }
1651:
1652:     // If we did only a single fast equip action, it only takes half a turn.
1653:     if (!needs_delay && !is_multi)
1654:         you.time_taken /= 2;
1655:     // If we did slow actions, no time should pass immediately (since time
1656:     // passing will be handled by the delays).
1657:     else if (needs_delay)
1658:         you.time_taken = 0;
1659:
1660:     you.turn_is_over = true;
1661: }
```

当前中文模板：你%s了%s。

输入还原：None


### trunk

完整英文：
```text
You %s %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 1702}

参数表达式与来源：
```text
T_("You %s %s.")
item_unequip_verb(*item).c_str()
item->name(DESC_YOUR).c_str()
1677:     // Removals happen first
1678:     if (!to_remove.empty())
1679:     {
1680:         // We remove items in reverse of the order they are selected, to account
1681:         // for chain removals (ie: removing our third ring before removing the
1682:         // Macabre Finger)
1683:         for (int i = to_remove.size() - 1; i >= 0; --i)
1684:         {
1685:             item_def* item = to_remove[i];
1686:             if (!instant && _is_slow_equip(*item))
1687:                 start_delay<EquipOffDelay>(ARMOUR_EQUIP_DELAY, *item);
1688:             // If this removal is queued after another removal, it needs to use
1689:             // a delay. (This means it takes 10 aut instead of 5, but this should
1690:             // matter so rarely that I'm not sure it's worth fixing?)
1691:             else if (needs_delay)
1692:                 start_delay<EquipOffDelay>(1, *item);
1693:             else
1694:             {
1695:                 if (item->is_type(OBJ_WEAPONS, WPN_CENTIPEDE))
1696:                 {
1697:                     mprf(T_("You rip the centipede off your %s and it falls limp."),
1698:                          you.arm_name(false).c_str());
1699:                 }
1700:                 else
1701:                 {
1702:                     mprf(T_("You %s %s."), item_unequip_verb(*item).c_str(),
1703:                                     item->name(DESC_YOUR).c_str());
1704:                 }
1705:                 unequip_item(*item);
1706:             }
1707:         }
1708:
1709:         // If we're swapping a real item for a temporary item, remember which
1710:         // item was swapped out.
1711:         //
1712:         // (For simplicity, we only do this in cases where a single item was
1713:         // changed. I'm not sure what more elaborate chain removals might be
1714:         // involved in this in future, but it's safer to not swap back than do
1715:         // do poorly-defined things.)
1716:         if (is_summoned && to_remove.size() == 1 && to_remove[0]->defined())
1717:         {
1718:             const mid_t id = to_remove[0]->give_unique_id();
1719:             to_equip->props[ITEM_SWAP_BACK_KEY].get_int() = id;
1720:         }
1721:     }
1722:
1723:     if (to_equip)
1724:     {
1725:         if (!instant && _is_slow_equip(*to_equip))
1726:             start_delay<EquipOnDelay>(ARMOUR_EQUIP_DELAY, *to_equip, equip_slot);
1727:         else if (needs_delay)
1728:             start_delay<EquipOnDelay>(1, *to_equip, equip_slot);
```

当前中文模板：你%s了%s。

输入还原：None

独立判断与参数还原：卸下/摘下/脱下加 DESC_YOUR，例你卸下了你的匕首。体标记了位于动词后，所有格未重复。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-07 — objective_error


### stable

完整英文：
```text
You really shouldn't be using a holy item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1848}

参数表达式与来源：
```text
T_("You really shouldn't be using a holy item like this.")

```

当前中文模板：你真的不应该这样使用神圣物品。

输入还原：你真的不应该这样使用神圣物品。

完整英文：
```text
You really shouldn't be using an evil item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1850}

参数表达式与来源：
```text
T_("You really shouldn't be using an evil item like this.")

```

当前中文模板：你真的不应该这样使用邪恶物品。

输入还原：你真的不应该这样使用邪恶物品。

完整英文：
```text
You really shouldn't be using an unclean item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1852}

参数表达式与来源：
```text
T_("You really shouldn't be using an unclean item like this.")

```

当前中文模板：你真的不应该这样使用不洁物品。

输入还原：你真的不应该这样使用不洁物品。

完整英文：
```text
You really shouldn't be using a chaotic item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1854}

参数表达式与来源：
```text
T_("You really shouldn't be using a chaotic item like this.")

```

当前中文模板：你真的不应该这样使用混乱物品。

输入还原：你真的不应该这样使用混乱物品。

完整英文：
```text
You really shouldn't be using a hasty item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1856}

参数表达式与来源：
```text
T_("You really shouldn't be using a hasty item like this.")

```

当前中文模板：你真的不应该这样使用急躁物品。

输入还原：你真的不应该这样使用急躁物品。

完整英文：
```text
You really shouldn't be using a wizardly item like this.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1858}

参数表达式与来源：
```text
T_("You really shouldn't be using a wizardly item like this.")

```

当前中文模板：你真的不应该这样使用巫师物品。

输入还原：你真的不应该这样使用巫师物品。


### trunk

独立判断与参数还原：like this 修饰物品种类，现译却指使用方式；同族 evil/unclean/chaotic/hasty/wizardly 六句均有此歧义，玩家被禁止的是使用这类物品。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "scope", "line": "stable", "english": "You really shouldn't be using a holy item like this.", "current_full_zh": "你真的不应该这样使用神圣物品。", "problem": "like this 修饰物品种类，现译却指使用方式；同族 evil/unclean/chaotic/hasty/wizardly 六句均有此歧义，玩家被禁止的是使用这类物品。", "suggested_zh": "你真的不应该使用这样的神圣物品。", "evidence": "stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1848}; stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1850}; stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1852}; stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1854}; stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1856}; stable {'path': 'crawl-ref/source/player-equip.cc', 'line': 1858}", "defect_points": 1}


## D-05 — ok


### stable

完整英文：
```text
Really %s?%s
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2937}

参数表达式与来源：
```text
make_stringf(T_("Really %s?%s"),
                                        verb_object.c_str(),
                                        hostile_check ? ""
                        : T_(" You can't even see any enemies this would affect.")
                                        ).c_str()
false
'n'
2912:                     : T_(" and you can't even see any enemies this would affect"));
2913:
2914:         targeter_radius hitfunc(&you, LOS_NO_TRANS);
2915:
2916:         const bool bad_item = (is_dangerous_item(*scroll, true)
2917:                                     || is_bad_item(*scroll))
2918:                             && Options.bad_item_prompt
2919:                             // Don't double-prompt if we're already asking for confirmation.
2920:                             && !_scroll_has_forced_targeter(static_cast<scroll_type>(scroll->sub_type));
2921:
2922:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
2923:                                [which_scroll] (const actor* m)
2924:                                {
2925:                                    return _scroll_will_harm(which_scroll, *m);
2926:                                },
2927:                                nullptr, nullptr))
2928:         {
2929:             return false;
2930:         }
2931:         else if (penance && !yesno(penance_prompt.c_str(), false, 'n'))
2932:         {
2933:             canned_msg(MSG_OK);
2934:             return false;
2935:         }
2936:         else if (bad_item
2937:                  && !yesno(make_stringf(T_("Really %s?%s"),
2938:                                         verb_object.c_str(),
2939:                                         hostile_check ? ""
2940:                         : T_(" You can't even see any enemies this would affect.")
2941:                                         ).c_str(),
2942:                            false, 'n'))
2943:         {
2944:             canned_msg(MSG_OK);
2945:             return false;
2946:         }
2947:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
2948:             "You can't see any enemies this would affect, really %s?"),
2949:                                         verb_object.c_str()).c_str(),
2950:                                                 false, 'n'))
2951:         {
2952:             // is this too nanny dev?
2953:             canned_msg(MSG_OK);
2954:             return false;
2955:         }
2956:     }
2957:
2958:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
2959:     if (you.unrand_equipped(UNRAND_VICTORY, true)
2960:         && !you.props.exists(VICTORY_CONDUCT_KEY))
2961:     {
2962:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
2963:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
2964:                                             "while wearing %s?"),
2965:                                             item->name(DESC_THE, false, true,
2966:                                                        false).c_str());
2967:
```

当前中文模板：确定要%s吗？%s

输入还原：None

完整英文：
```text
 You can't even see any enemies this would affect.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2937}

参数表达式与来源：
```text
make_stringf(T_("Really %s?%s"),
                                        verb_object.c_str(),
                                        hostile_check ? ""
                        : T_(" You can't even see any enemies this would affect.")
                                        ).c_str()
false
'n'

```

当前中文模板： 你甚至看不到会被此影响的敌人。

输入还原：None

完整英文：
```text
You can't see any enemies this would affect, really %s?
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2947}

参数表达式与来源：
```text
make_stringf(T_(
            "You can't see any enemies this would affect, really %s?"),
                                        verb_object.c_str()).c_str()
false
'n'
2922:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
2923:                                [which_scroll] (const actor* m)
2924:                                {
2925:                                    return _scroll_will_harm(which_scroll, *m);
2926:                                },
2927:                                nullptr, nullptr))
2928:         {
2929:             return false;
2930:         }
2931:         else if (penance && !yesno(penance_prompt.c_str(), false, 'n'))
2932:         {
2933:             canned_msg(MSG_OK);
2934:             return false;
2935:         }
2936:         else if (bad_item
2937:                  && !yesno(make_stringf(T_("Really %s?%s"),
2938:                                         verb_object.c_str(),
2939:                                         hostile_check ? ""
2940:                         : T_(" You can't even see any enemies this would affect.")
2941:                                         ).c_str(),
2942:                            false, 'n'))
2943:         {
2944:             canned_msg(MSG_OK);
2945:             return false;
2946:         }
2947:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
2948:             "You can't see any enemies this would affect, really %s?"),
2949:                                         verb_object.c_str()).c_str(),
2950:                                                 false, 'n'))
2951:         {
2952:             // is this too nanny dev?
2953:             canned_msg(MSG_OK);
2954:             return false;
2955:         }
2956:     }
2957:
2958:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
2959:     if (you.unrand_equipped(UNRAND_VICTORY, true)
2960:         && !you.props.exists(VICTORY_CONDUCT_KEY))
2961:     {
2962:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
2963:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
2964:                                             "while wearing %s?"),
2965:                                             item->name(DESC_THE, false, true,
2966:                                                        false).c_str());
2967:
2968:         if (item->props[VICTORY_STAT_KEY].get_int() > 0
2969:             && nearby_mons
2970:             && !yesno(unrand_prompt.c_str(), false, 'n'))
2971:         {
2972:             canned_msg(MSG_OK);
2973:             return false;
2974:         }
2975:     }
```

当前中文模板：你看不到任何会受此影响的敌人，确定要%s吗？

输入还原：None


### trunk

完整英文：
```text
Really %s?%s
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3076}

参数表达式与来源：
```text
make_stringf(T_("Really %s?%s"),
                                        verb_object.c_str(),
                                        hostile_check ? ""
                        : T_(" You can't even see any enemies this would affect.")
                                        ).c_str()
false
'n'
3051:     // Handle player cancels before we waste time
3052:     if (alreadyknown)
3053:     {
3054:         const bool hostile_check = scroll_hostile_check(which_scroll);
3055:         const string verb_object = make_stringf(
3056:             T_("read the %s"), scroll->name(DESC_DBNAME).c_str());
3057:
3058:         targeter_radius hitfunc(&you, LOS_NO_TRANS);
3059:
3060:         const bool bad_item = (is_dangerous_item(*scroll, true)
3061:                                     || is_bad_item(*scroll))
3062:                             && Options.bad_item_prompt
3063:                             // Don't double-prompt if we're already asking for confirmation.
3064:                             && !_scroll_has_forced_targeter(which_scroll);
3065:
3066:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
3067:                                [which_scroll] (const actor* m)
3068:                                {
3069:                                    return _scroll_will_harm(which_scroll, *m);
3070:                                },
3071:                                nullptr, nullptr))
3072:         {
3073:             return false;
3074:         }
3075:         else if (bad_item
3076:                  && !yesno(make_stringf(T_("Really %s?%s"),
3077:                                         verb_object.c_str(),
3078:                                         hostile_check ? ""
3079:                         : T_(" You can't even see any enemies this would affect.")
3080:                                         ).c_str(),
3081:                            false, 'n'))
3082:         {
3083:             canned_msg(MSG_OK);
3084:             return false;
3085:         }
3086:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
3087:             "You can't see any enemies this would affect, really %s?"),
3088:                                         verb_object.c_str()).c_str(),
3089:                                                 false, 'n'))
3090:         {
3091:             // is this too nanny dev?
3092:             canned_msg(MSG_OK);
3093:             return false;
3094:         }
3095:     }
3096:
3097:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
3098:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3099:         && !you.props.exists(VICTORY_CONDUCT_KEY))
3100:     {
3101:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
3102:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
3103:                                             "while wearing %s?"),
3104:                                             item->name(DESC_THE, false, true,
3105:                                                        false).c_str());
3106:
```

当前中文模板：确定要%s吗？%s

输入还原：None

完整英文：
```text
 You can't even see any enemies this would affect.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3076}

参数表达式与来源：
```text
make_stringf(T_("Really %s?%s"),
                                        verb_object.c_str(),
                                        hostile_check ? ""
                        : T_(" You can't even see any enemies this would affect.")
                                        ).c_str()
false
'n'

```

当前中文模板： 你甚至看不到会被此影响的敌人。

输入还原：None

完整英文：
```text
You can't see any enemies this would affect, really %s?
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3086}

参数表达式与来源：
```text
make_stringf(T_(
            "You can't see any enemies this would affect, really %s?"),
                                        verb_object.c_str()).c_str()
false
'n'
3061:                                     || is_bad_item(*scroll))
3062:                             && Options.bad_item_prompt
3063:                             // Don't double-prompt if we're already asking for confirmation.
3064:                             && !_scroll_has_forced_targeter(which_scroll);
3065:
3066:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
3067:                                [which_scroll] (const actor* m)
3068:                                {
3069:                                    return _scroll_will_harm(which_scroll, *m);
3070:                                },
3071:                                nullptr, nullptr))
3072:         {
3073:             return false;
3074:         }
3075:         else if (bad_item
3076:                  && !yesno(make_stringf(T_("Really %s?%s"),
3077:                                         verb_object.c_str(),
3078:                                         hostile_check ? ""
3079:                         : T_(" You can't even see any enemies this would affect.")
3080:                                         ).c_str(),
3081:                            false, 'n'))
3082:         {
3083:             canned_msg(MSG_OK);
3084:             return false;
3085:         }
3086:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
3087:             "You can't see any enemies this would affect, really %s?"),
3088:                                         verb_object.c_str()).c_str(),
3089:                                                 false, 'n'))
3090:         {
3091:             // is this too nanny dev?
3092:             canned_msg(MSG_OK);
3093:             return false;
3094:         }
3095:     }
3096:
3097:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
3098:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3099:         && !you.props.exists(VICTORY_CONDUCT_KEY))
3100:     {
3101:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
3102:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
3103:                                             "while wearing %s?"),
3104:                                             item->name(DESC_THE, false, true,
3105:                                                        false).c_str());
3106:
3107:         if (item->props[VICTORY_STAT_KEY].get_int() > 0
3108:             && nearby_mons
3109:             && !yesno(unrand_prompt.c_str(), false, 'n'))
3110:         {
3111:             canned_msg(MSG_OK);
3112:             return false;
3113:         }
3114:     }
```

当前中文模板：你看不到任何会受此影响的敌人，确定要%s吗？

输入还原：None

独立判断与参数还原：实际参数是 verb_object 与可选敌人提示，不是 yesno 的 false/n。阅读卷轴与敌人可见性两条件完整；可还原确定要阅读恐惧卷轴吗？ 你甚至看不到会被此影响的敌人。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-06 — ok


### stable

完整英文：
```text
You miscast %s.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 2456}

参数表达式与来源：
```text
T_("You miscast %s.")
spell_title(spell)
2431:             && battlesphere_can_mirror(spell))
2432:         {
2433:             trigger_battlesphere(&you);
2434:         }
2435:
2436:         if (will_have_passive(passive_t::shadow_spells) && actual_spell)
2437:             dithmenos_shadow_spell(spell);
2438:         _spellcasting_side_effects(spell, god, !actual_spell);
2439:
2440:         if (you.wearing_ego(OBJ_GIZMOS, SPGIZMO_SPELLMOTOR) && actual_spell)
2441:             coglin_spellmotor_attack();
2442:
2443:         // Handle revenant passives
2444:         if (can_enkindle && you.has_mutation(MUT_SPELLCLAWS))
2445:             spellclaws_attack(spell_difficulty(spell));
2446:
2447:         if (enkindled && --you.props[ENKINDLE_CHARGES_KEY].get_int() == 0)
2448:             end_enkindled_status();
2449:
2450:         return spret::success;
2451:     }
2452:     case spret::fail:
2453:     {
2454:         if (actual_spell)
2455:         {
2456:             mprf(T_("You miscast %s."),
2457:                  spell_title(spell));
2458:             flush_input_buffer(FLUSH_ON_FAILURE);
2459:             learned_something_new(HINT_SPELL_MISCAST);
2460:             miscast_effect(spell, fail);
2461:         }
2462:
2463:         return spret::fail;
2464:     }
2465:
2466:     case spret::abort:
2467:         return spret::abort;
2468:
2469:     case spret::none:
2470: #ifdef WIZARD
2471:         if (you.wizard && !actual_spell && is_valid_spell(spell)
2472:             && (flags & spflag::monster))
2473:         {
2474:             _try_monster_cast(spell, powc, *target, beam);
2475:             return spret::success;
2476:         }
2477: #endif
2478:
2479:         if (is_valid_spell(spell))
2480:         {
2481:             mprf(MSGCH_ERROR,
2482:                  T_("Spell '%s' is not a player castable spell."),
```

当前中文模板：你施放%s时出现施法失误。

输入还原：你施放魔法飞弹时出现施法失误。


### trunk

完整英文：
```text
You miscast %s.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 2525}

参数表达式与来源：
```text
T_("You miscast %s.")
spell_title(spell)
2500:         _apply_post_zap_effect(spell, orig_target_pos);
2501:
2502:         if (evoked_wand && you.get_mutation_level(MUT_DEMONIC_MAGIC) == 3)
2503:             do_demonic_magic(spell_difficulty(spell) * 6, 3);
2504:
2505:         // Handle a variety of things that trigger off nominally casting a spell.
2506:         if (actual_spell || you.divine_exegesis)
2507:             do_post_spellcast_effects(spell);
2508:
2509:         // Make some noise if it's actually the player casting.
2510:         if (god == GOD_NO_GOD)
2511:             noisy(spell_noise(spell), you.pos());
2512:
2513:         if (enkindled && --you.props[ENKINDLE_CHARGES_KEY].get_int() == 0)
2514:             end_enkindled_status();
2515:
2516:         if (god == GOD_NO_GOD)
2517:             xom_end_disguise();
2518:
2519:         return spret::success;
2520:     }
2521:     case spret::fail:
2522:     {
2523:         if (actual_spell)
2524:         {
2525:             mprf(T_("You miscast %s."),
2526:                  spell_title(spell));
2527:             flush_input_buffer(FLUSH_ON_FAILURE);
2528:             learned_something_new(HINT_SPELL_MISCAST);
2529:             miscast_effect(spell, fail);
2530:         }
2531:
2532:         return spret::fail;
2533:     }
2534:
2535:     case spret::abort:
2536:     default:
2537:         return spret::abort;
2538:
2539:     case spret::none:
2540: #ifdef WIZARD
2541:         if (you.wizard && !actual_spell && is_valid_spell(spell)
2542:             && (flags & spflag::monster))
2543:         {
2544:             _try_monster_cast(spell, powc, *target, beam);
2545:             return spret::success;
2546:         }
2547: #endif
2548:
2549:         if (is_valid_spell(spell))
2550:         {
2551:             mprf(MSGCH_ERROR,
```

当前中文模板：你施放%s时出现施法失误。

输入还原：你施放魔法飞弹时出现施法失误。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-06 — ok


### stable

完整英文：
```text
You feel %s sick.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4835}

参数表达式与来源：
```text
channel
T_("You feel %s sick.")
adj
4810:             - (25000 / 1000);
4811:         if (dmg < 0)
4812:             dmg = 0;
4813:     }
4814: #endif
4815:
4816:     msg_channel_type channel = MSGCH_PLAIN;
4817:     const char *adj = "";
4818:
4819:     if (dmg > 6)
4820:     {
4821:         channel = MSGCH_DANGER;
4822:         adj = T_("extremely ");
4823:     }
4824:     else if (dmg > 2)
4825:     {
4826:         channel = MSGCH_WARN;
4827:         adj = T_("very ");
4828:     }
4829:
4830:     if (do_dmg && dmg > 0)
4831:     {
4832:         int oldhp = you.hp;
4833:         ouch(dmg, KILLED_BY_POISON);
4834:         if (you.hp < oldhp)
4835:             mprf(channel, T_("You feel %s sick."), adj);
4836:     }
4837:
4838:     // Now decrease the poison in our system
4839:     reduce_player_poison(decrease);
4840: }
4841:
4842: void reduce_player_poison(int amount)
4843: {
4844:     if (amount <= 0)
4845:         return;
4846:
4847:     you.duration[DUR_POISONING] -= amount;
4848:
4849:     // Less than 1 point of damage remaining, so just end the poison
4850:     if (you.duration[DUR_POISONING] < 1000)
4851:         you.duration[DUR_POISONING] = 0;
4852:
4853:     if (you.duration[DUR_POISONING] <= 0)
4854:     {
4855:         you.duration[DUR_POISONING] = 0;
4856:         you.props.erase(POISONER_KEY);
4857:         you.props.erase(POISON_AUX_KEY);
4858:         mprf(MSGCH_RECOVERY, T_("You are no longer poisoned."));
4859:     }
4860:
```

当前中文模板：你感觉%s不适。

输入还原：你感觉不适。


### trunk

完整英文：
```text
You feel %s sick.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 5050}

参数表达式与来源：
```text
channel
T_("You feel %s sick.")
adj
5025:             - (25000 / 1000);
5026:         if (dmg < 0)
5027:             dmg = 0;
5028:     }
5029: #endif
5030:
5031:     msg_channel_type channel = MSGCH_PLAIN;
5032:     const char *adj = "";
5033:
5034:     if (dmg > 6)
5035:     {
5036:         channel = MSGCH_DANGER;
5037:         adj = T_("extremely ");
5038:     }
5039:     else if (dmg > 2)
5040:     {
5041:         channel = MSGCH_WARN;
5042:         adj = T_("very ");
5043:     }
5044:
5045:     if (do_dmg && dmg > 0)
5046:     {
5047:         int oldhp = you.hp;
5048:         ouch(dmg, KILLED_BY_POISON);
5049:         if (you.hp < oldhp)
5050:             mprf(channel, T_("You feel %s sick."), adj);
5051:     }
5052:
5053:     // Now decrease the poison in our system
5054:     reduce_player_poison(decrease);
5055: }
5056:
5057: void reduce_player_poison(int amount)
5058: {
5059:     if (amount <= 0)
5060:         return;
5061:
5062:     you.duration[DUR_POISONING] -= amount;
5063:
5064:     // Less than 1 point of damage remaining, so just end the poison
5065:     if (you.duration[DUR_POISONING] < 1000)
5066:         you.duration[DUR_POISONING] = 0;
5067:
5068:     if (you.duration[DUR_POISONING] <= 0)
5069:     {
5070:         you.duration[DUR_POISONING] = 0;
5071:         you.props.erase(POISONER_KEY);
5072:         you.props.erase(POISON_AUX_KEY);
5073:         mprf(MSGCH_RECOVERY, T_("You are no longer poisoned."));
5074:     }
5075:
```

当前中文模板：你感觉%s不适。

输入还原：你感觉不适。

独立判断与参数还原：按伤害三档还原你感觉不适。/你感觉非常不适。/你感觉极度不适。；只有实际扣血才显示，程度均保留。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-09 — ok


### stable

完整英文：
```text
You produce a hideous howling noise!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 89}

参数表达式与来源：
```text
MSGCH_SOUND
T_("You produce a hideous howling noise!")

```

当前中文模板：你发出了一声可怕的嚎叫！

输入还原：你发出了一声可怕的嚎叫！


### trunk

完整英文：
```text
You produce a hideous howling noise!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 90}

参数表达式与来源：
```text
MSGCH_SOUND
T_("You produce a hideous howling noise!")

```

当前中文模板：你发出了一声可怕的嚎叫！

输入还原：你发出了一声可怕的嚎叫！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-05 — ok


### stable

完整英文：
```text
%s glow green for a %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2523}

参数表达式与来源：
```text
plural ? T_("%s glow green for a %s.")
                    : T_("%s glows green for a %s.")
name.c_str()
dur.c_str()
2498:     return _handle_enchant_weapon(false, "");
2499: }
2500:
2501: bool enchant_armour(item_def &arm, bool quiet)
2502: {
2503:     ASSERT(arm.defined());
2504:     ASSERT(arm.base_type == OBJ_ARMOUR);
2505:
2506:     // Cannot be enchanted.
2507:     if (!is_enchantable_armour(arm))
2508:     {
2509:         if (!quiet)
2510:             canned_msg(MSG_NOTHING_HAPPENS);
2511:         return false;
2512:     }
2513:
2514:     string name = _item_name(arm);
2515:
2516:     ++arm.plus;
2517:
2518:     if (!quiet)
2519:     {
2520:         const bool plural = armour_is_hide(arm)
2521:                             && arm.sub_type != ARM_TROLL_LEATHER_ARMOUR;
2522:         const string dur = is_enchantable_armour(arm) ? T_("moment") : T_("while");
2523:         mprf(plural ? T_("%s glow green for a %s.")
2524:                     : T_("%s glows green for a %s."),
2525:              name.c_str(), dur.c_str());
2526:     }
2527:
2528:     return true;
2529: }
2530:
2531: /// Returns whether the scroll is used up.
2532: static bool _handle_enchant_armour(bool alreadyknown, const string &pre_msg)
2533: {
2534:     item_def* target= nullptr;
2535:     string letter = "";
2536:     if (!clua.callfn("c_choose_enchant_armour", ">s", &letter))
2537:     {
2538:         if (!clua.error.empty())
2539:             mprf(MSGCH_ERROR, T_("Lua error: %s"), clua.error.c_str());
2540:     }
2541:     else if (isaalpha(letter.c_str()[0]))
2542:     {
2543:         item_def &item = you.inv[letter_to_index(letter.c_str()[0])];
2544:         if (item.defined() && is_enchantable_armour(item, true))
2545:             target = &item;
2546:     }
2547:
2548:     if (!target)
2549:     {
2550:         target = _choose_target_item_for_scroll(alreadyknown,
```

当前中文模板：%s泛起绿光，持续了%s。

输入还原：None

完整英文：
```text
%s glows green for a %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2523}

参数表达式与来源：
```text
plural ? T_("%s glow green for a %s.")
                    : T_("%s glows green for a %s.")
name.c_str()
dur.c_str()
2498:     return _handle_enchant_weapon(false, "");
2499: }
2500:
2501: bool enchant_armour(item_def &arm, bool quiet)
2502: {
2503:     ASSERT(arm.defined());
2504:     ASSERT(arm.base_type == OBJ_ARMOUR);
2505:
2506:     // Cannot be enchanted.
2507:     if (!is_enchantable_armour(arm))
2508:     {
2509:         if (!quiet)
2510:             canned_msg(MSG_NOTHING_HAPPENS);
2511:         return false;
2512:     }
2513:
2514:     string name = _item_name(arm);
2515:
2516:     ++arm.plus;
2517:
2518:     if (!quiet)
2519:     {
2520:         const bool plural = armour_is_hide(arm)
2521:                             && arm.sub_type != ARM_TROLL_LEATHER_ARMOUR;
2522:         const string dur = is_enchantable_armour(arm) ? T_("moment") : T_("while");
2523:         mprf(plural ? T_("%s glow green for a %s.")
2524:                     : T_("%s glows green for a %s."),
2525:              name.c_str(), dur.c_str());
2526:     }
2527:
2528:     return true;
2529: }
2530:
2531: /// Returns whether the scroll is used up.
2532: static bool _handle_enchant_armour(bool alreadyknown, const string &pre_msg)
2533: {
2534:     item_def* target= nullptr;
2535:     string letter = "";
2536:     if (!clua.callfn("c_choose_enchant_armour", ">s", &letter))
2537:     {
2538:         if (!clua.error.empty())
2539:             mprf(MSGCH_ERROR, T_("Lua error: %s"), clua.error.c_str());
2540:     }
2541:     else if (isaalpha(letter.c_str()[0]))
2542:     {
2543:         item_def &item = you.inv[letter_to_index(letter.c_str()[0])];
2544:         if (item.defined() && is_enchantable_armour(item, true))
2545:             target = &item;
2546:     }
2547:
2548:     if (!target)
2549:     {
2550:         target = _choose_target_item_for_scroll(alreadyknown,
```

当前中文模板：%s泛起绿光，持续了%s。

输入还原：None


### trunk

完整英文：
```text
%s glow green for a %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2600}

参数表达式与来源：
```text
plural ? T_("%s glow green for a %s.")
                    : T_("%s glows green for a %s.")
iname.c_str()
dur.c_str()
2575: bool enchant_armour(item_def &arm, bool quiet)
2576: {
2577:     ASSERT(arm.defined());
2578:     ASSERT(arm.base_type == OBJ_ARMOUR);
2579:
2580:     // Cannot be enchanted.
2581:     if (!is_enchantable_armour(arm))
2582:     {
2583:         if (!quiet)
2584:             canned_msg(MSG_NOTHING_HAPPENS);
2585:         return false;
2586:     }
2587:
2588:     // Get item name now before changing enchantment.
2589:     string iname = _item_name(arm);
2590:
2591:     arm.plus++;
2592:     // Make sure newly enchanted items appear as such.
2593:     item_set_appearance(arm);
2594:
2595:     if (!quiet)
2596:     {
2597:         const bool plural = armour_is_hide(arm)
2598:                             && arm.sub_type != ARM_TROLL_LEATHER_ARMOUR;
2599:         const string dur = is_enchantable_armour(arm) ? T_("moment") : T_("while");
2600:         mprf(plural ? T_("%s glow green for a %s.")
2601:                     : T_("%s glows green for a %s."),
2602:              iname.c_str(), dur.c_str());
2603:     }
2604:
2605:     return true;
2606: }
2607:
2608: static spret _handle_enchant_armour(bool alreadyknown, const string &pre_msg)
2609: {
2610:     item_def* target= nullptr;
2611:     string letter = "";
2612:     spret result = spret::success;
2613:     if (!clua.callfn("c_choose_enchant_armour", ">s", &letter))
2614:     {
2615:         if (!clua.error.empty())
2616:             mprf(MSGCH_ERROR, T_("Lua error: %s"), clua.error.c_str());
2617:     }
2618:     else if (isaalpha(letter.c_str()[0]))
2619:     {
2620:         item_def &item = you.inv[letter_to_index(letter.c_str()[0])];
2621:         if (item.defined() && is_enchantable_armour(item, true))
2622:             target = &item;
2623:     }
2624:
2625:     if (!target)
2626:     {
2627:         result = _choose_target_item_for_scroll(alreadyknown,
```

当前中文模板：%s泛起绿光，持续了%s。

输入还原：None

完整英文：
```text
%s glows green for a %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2600}

参数表达式与来源：
```text
plural ? T_("%s glow green for a %s.")
                    : T_("%s glows green for a %s.")
iname.c_str()
dur.c_str()
2575: bool enchant_armour(item_def &arm, bool quiet)
2576: {
2577:     ASSERT(arm.defined());
2578:     ASSERT(arm.base_type == OBJ_ARMOUR);
2579:
2580:     // Cannot be enchanted.
2581:     if (!is_enchantable_armour(arm))
2582:     {
2583:         if (!quiet)
2584:             canned_msg(MSG_NOTHING_HAPPENS);
2585:         return false;
2586:     }
2587:
2588:     // Get item name now before changing enchantment.
2589:     string iname = _item_name(arm);
2590:
2591:     arm.plus++;
2592:     // Make sure newly enchanted items appear as such.
2593:     item_set_appearance(arm);
2594:
2595:     if (!quiet)
2596:     {
2597:         const bool plural = armour_is_hide(arm)
2598:                             && arm.sub_type != ARM_TROLL_LEATHER_ARMOUR;
2599:         const string dur = is_enchantable_armour(arm) ? T_("moment") : T_("while");
2600:         mprf(plural ? T_("%s glow green for a %s.")
2601:                     : T_("%s glows green for a %s."),
2602:              iname.c_str(), dur.c_str());
2603:     }
2604:
2605:     return true;
2606: }
2607:
2608: static spret _handle_enchant_armour(bool alreadyknown, const string &pre_msg)
2609: {
2610:     item_def* target= nullptr;
2611:     string letter = "";
2612:     spret result = spret::success;
2613:     if (!clua.callfn("c_choose_enchant_armour", ">s", &letter))
2614:     {
2615:         if (!clua.error.empty())
2616:             mprf(MSGCH_ERROR, T_("Lua error: %s"), clua.error.c_str());
2617:     }
2618:     else if (isaalpha(letter.c_str()[0]))
2619:     {
2620:         item_def &item = you.inv[letter_to_index(letter.c_str()[0])];
2621:         if (item.defined() && is_enchantable_armour(item, true))
2622:             target = &item;
2623:     }
2624:
2625:     if (!target)
2626:     {
2627:         result = _choose_target_item_for_scroll(alreadyknown,
```

当前中文模板：%s泛起绿光，持续了%s。

输入还原：None

独立判断与参数还原：moment=一瞬、while=一段时间，例你的皮甲泛起绿光，持续了一瞬。与持续了一段时间。；按附魔后是否仍可附魔选择时长。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-05 — ok


### stable

完整英文：
```text
%s vents fumes.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4590}

参数表达式与来源：
```text
T_("%s vents fumes.")
attacker->name(DESC_THE).c_str()
4565:                     simple_god_message(T_(" protects your body from unnatural transformation!"));
4566:                 else
4567:                 {
4568:                     bool initial = you.duration[DUR_SLIMIFYING] == 0;
4569:                     you.duration[DUR_SLIMIFYING] += random_range(70, 90);
4570:                     if (you.duration[DUR_SLIMIFYING] >= 200)
4571:                     {
4572:                         you.duration[DUR_SLIMIFYING] = 0;
4573:                         transform(20 + roll_dice(3, 10),
4574:                                   transformation::jelly, true, false);
4575:                         you.transform_uncancellable = true;
4576:                     }
4577:                     else
4578:                     {
4579:                         mprf(MSGCH_DANGER, T_("You %s!"),
4580:                             initial ? T_("start to liquefy") : T_("liquefy further"));
4581:                     }
4582:                 }
4583:             }
4584:         }
4585:         break;
4586:
4587:     case AF_ALEMBIC:
4588:     {
4589:         if (needs_message)
4590:             mprf(T_("%s vents fumes."), attacker->name(DESC_THE).c_str());
4591:
4592:         int dur = random_range(3, 7);
4593:         place_cloud(CLOUD_POISON, defender->pos(), dur, attacker);
4594:
4595:         if (coinflip())
4596:         {
4597:             const int num_clouds = random_range(3, 4);
4598:             int placed = 0;
4599:             for (fair_adjacent_iterator ai(defender->pos()); ai && (placed < num_clouds); ++ai)
4600:             {
4601:                 if ((!actor_at(*ai) || !mons_aligned(attacker, actor_at(*ai)))
4602:                     && place_cloud(CLOUD_POISON, *ai, dur, attacker))
4603:                 {
4604:                     ++placed;
4605:                 }
4606:             }
4607:         }
4608:
4609:         // No brewing potions via punching plants.
4610:         if (!defender || defender->is_firewood())
4611:             break;
4612:
4613:         if (--attacker->as_monster()->number == 0)
4614:             alembic_brew_potion(*attacker->as_monster());
4615:     }
```

当前中文模板：%s喷出了烟雾。

输入还原：兽人喷出了烟雾。


### trunk

完整英文：
```text
%s vents fumes.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4784}

参数表达式与来源：
```text
T_("%s vents fumes.")
attacker->name(DESC_THE).c_str()
4759:                     simple_god_message(T_(" protects your body from unnatural transformation!"));
4760:                 else
4761:                 {
4762:                     bool initial = you.duration[DUR_SLIMIFYING] == 0;
4763:                     you.duration[DUR_SLIMIFYING] += random_range(70, 90);
4764:                     if (you.duration[DUR_SLIMIFYING] >= 200)
4765:                     {
4766:                         you.duration[DUR_SLIMIFYING] = 0;
4767:                         transform(20 + roll_dice(3, 10),
4768:                                   transformation::jelly, true, false);
4769:                         you.transform_uncancellable = true;
4770:                     }
4771:                     else
4772:                     {
4773:                         mprf(MSGCH_DANGER, T_("You %s!"),
4774:                             initial ? T_("start to liquefy") : T_("liquefy further"));
4775:                     }
4776:                 }
4777:             }
4778:         }
4779:         break;
4780:
4781:     case AF_ALEMBIC:
4782:     {
4783:         if (needs_message)
4784:             mprf(T_("%s vents fumes."), attacker->name(DESC_THE).c_str());
4785:
4786:         int dur = random_range(3, 7);
4787:         place_cloud(CLOUD_POISON, defender->pos(), dur, attacker);
4788:
4789:         if (coinflip())
4790:         {
4791:             const int num_clouds = random_range(3, 4);
4792:             int placed = 0;
4793:             for (fair_adjacent_iterator ai(defender->pos()); ai && (placed < num_clouds); ++ai)
4794:             {
4795:                 if ((!actor_at(*ai) || !mons_aligned(attacker, actor_at(*ai)))
4796:                     && place_cloud(CLOUD_POISON, *ai, dur, attacker))
4797:                 {
4798:                     ++placed;
4799:                 }
4800:             }
4801:         }
4802:
4803:         // No brewing potions via punching plants.
4804:         if (!defender || defender->is_firewood())
4805:             break;
4806:
4807:         if (--attacker->as_monster()->number == 0)
4808:             alembic_brew_potion(*attacker->as_monster());
4809:     }
```

当前中文模板：%s喷出了烟雾。

输入还原：兽人喷出了烟雾。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-02 — ok


### stable

完整英文：
```text
%s %s held in place!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5070}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()
5045:         return false; // don't even print a message
5046:
5047:     const int size_diff =
5048:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5049:     const coord_def old_pos = defender->pos();
5050:     const coord_def new_pos = old_pos + old_pos - attack_position;
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
```

当前中文模板：%s%s紧紧束缚在原地！

输入还原：None

完整英文：
```text
are
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5070}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()

```

当前中文模板：被

输入还原：None

完整英文：
```text
verb
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5070}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()
5045:         return false; // don't even print a message
5046:
5047:     const int size_diff =
5048:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5049:     const coord_def old_pos = defender->pos();
5050:     const coord_def new_pos = old_pos + old_pos - attack_position;
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
```

当前中文模板：None

输入还原：None

完整英文：
```text
%s %s %s ground!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5076}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
5098:
5099:     // Schedule following _before_ actually trampling -- if the defender
5100:     // is a player, a shaft trap will unload the level. If trampling will
5101:     // somehow fail, move attempt will be ignored.
5102:     if (!attacker->cannot_move())
5103:         schedule_trample_follow_fineff(attacker, old_pos);
5104:     defender->move_to(new_pos);
```

当前中文模板：%s%s了%s阵地！

输入还原：None

完整英文：
```text
hold
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5076}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()

```

当前中文模板：死死守住

输入还原：None

完整英文：
```text
verb
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5076}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
5098:
5099:     // Schedule following _before_ actually trampling -- if the defender
5100:     // is a player, a shaft trap will unload the level. If trampling will
5101:     // somehow fail, move attempt will be ignored.
5102:     if (!attacker->cannot_move())
5103:         schedule_trample_follow_fineff(attacker, old_pos);
5104:     defender->move_to(new_pos);
```

当前中文模板：None

输入还原：None


### trunk

完整英文：
```text
%s %s held in place!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5277}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()
5252:         return false; // don't even print a message
5253:
5254:     const int size_diff =
5255:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5256:     const coord_def old_pos = defender->pos();
5257:     const coord_def new_pos = old_pos + old_pos - attack_position;
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
```

当前中文模板：%s%s紧紧束缚在原地！

输入还原：None

完整英文：
```text
are
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5277}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()

```

当前中文模板：被

输入还原：None

完整英文：
```text
verb
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5277}

参数表达式与来源：
```text
T_("%s %s held in place!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "are"), "verb").c_str()
5252:         return false; // don't even print a message
5253:
5254:     const int size_diff =
5255:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5256:     const coord_def old_pos = defender->pos();
5257:     const coord_def new_pos = old_pos + old_pos - attack_position;
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
```

当前中文模板：None

输入还原：None

完整英文：
```text
%s %s %s ground!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5283}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
5305:     }
5306:
5307:     // Schedule following _before_ actually trampling -- if the defender
5308:     // is a player, a shaft trap will unload the level. If trampling will
5309:     // somehow fail, move attempt will be ignored.
5310:     if (!attacker->cannot_move())
5311:         schedule_trample_follow_fineff(attacker, old_pos);
```

当前中文模板：%s%s了%s阵地！

输入还原：None

完整英文：
```text
hold
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5283}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()

```

当前中文模板：死死守住

输入还原：None

完整英文：
```text
verb
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5283}

参数表达式与来源：
```text
T_("%s %s %s ground!")
defender_name(false).c_str()
defender->verb_for_display(NC_("verb", "hold"), "verb").c_str()
defender->pronoun(PRONOUN_POSSESSIVE).c_str()
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
5305:     }
5306:
5307:     // Schedule following _before_ actually trampling -- if the defender
5308:     // is a player, a shaft trap will unload the level. If trampling will
5309:     // somehow fail, move attempt will be ignored.
5310:     if (!attacker->cannot_move())
5311:         schedule_trample_follow_fineff(attacker, old_pos);
```

当前中文模板：None

输入还原：None

独立判断与参数还原：可还原兽人被紧紧束缚在原地！与兽人死死守住了他的阵地！；are/hold 经 verb 上下文显示，主被动分支各自成立。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-07 — ok


### stable

完整英文：
```text
A part of your body evaporates into steam!
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 4593}

参数表达式与来源：
```text
T_("A part of your body evaporates into steam!")

```

当前中文模板：你身体的一部分蒸发成了蒸汽！

输入还原：你身体的一部分蒸发成了蒸汽！


### trunk

完整英文：
```text
A part of your body evaporates into steam!
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 4629}

参数表达式与来源：
```text
T_("A part of your body evaporates into steam!")

```

当前中文模板：你身体的一部分蒸发成了蒸汽！

输入还原：你身体的一部分蒸发成了蒸汽！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-10 — ok


### stable

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1827}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3501}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。


### trunk

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1790}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3674}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-12 — ok


### stable

完整英文：
```text
Monsters! Monsters everywhere! You have to get out of here!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 386}

参数表达式与来源：
```text
T_("Monsters! Monsters everywhere! You have to get out of here!")

```

当前中文模板：怪物！到处都是怪物！你必须离开这里！

输入还原：怪物！到处都是怪物！你必须离开这里！

完整英文：
```text
You reel with horror at the sight of these foes!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 388}

参数表达式与来源：
```text
T_("You reel with horror at the sight of these foes!")

```

当前中文模板：看到这些敌人，你恐惧得晕头转向！

输入还原：看到这些敌人，你恐惧得晕头转向！

完整英文：
```text
You feel a twist of horror at the sight of this foe.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 390}

参数表达式与来源：
```text
T_("You feel a twist of horror at the sight of this foe.")

```

当前中文模板：看到这个敌人，你感到一阵恐惧。

输入还原：看到这个敌人，你感到一阵恐惧。


### trunk

完整英文：
```text
Monsters! Monsters everywhere! You have to get out of here!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 388}

参数表达式与来源：
```text
T_("Monsters! Monsters everywhere! You have to get out of here!")

```

当前中文模板：怪物！到处都是怪物！你必须离开这里！

输入还原：怪物！到处都是怪物！你必须离开这里！

完整英文：
```text
You reel with horror at the sight of these foes!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 390}

参数表达式与来源：
```text
T_("You reel with horror at the sight of these foes!")

```

当前中文模板：看到这些敌人，你恐惧得晕头转向！

输入还原：看到这些敌人，你恐惧得晕头转向！

完整英文：
```text
You feel a twist of horror at the sight of this foe.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 392}

参数表达式与来源：
```text
T_("You feel a twist of horror at the sight of this foe.")

```

当前中文模板：看到这个敌人，你感到一阵恐惧。

输入还原：看到这个敌人，你感到一阵恐惧。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-08 — ok


### stable

完整英文：
```text
You cannot move. (Use ctrl+direction or * direction to attack while stationary and confused.)
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 672}

参数表达式与来源：
```text
T_("You cannot move. (Use ctrl+direction or * direction to "
            "attack while stationary and confused.)")

```

当前中文模板：你无法移动。（使用ctrl+方向或*方向在混乱状态下原地攻击。）

输入还原：你无法移动。（使用ctrl+方向或*方向在混乱状态下原地攻击。）


### trunk

完整英文：
```text
You cannot move. (Use ctrl+direction or * direction to attack while stationary and confused.)
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 672}

参数表达式与来源：
```text
T_("You cannot move. (Use ctrl+direction or * direction to "
            "attack while stationary and confused.)")

```

当前中文模板：你无法移动。（使用ctrl+方向或*方向在混乱状态下原地攻击。）

输入还原：你无法移动。（使用ctrl+方向或*方向在混乱状态下原地攻击。）

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-05 — ok


### stable

完整英文：
```text
If you enter this portal you might not be able to return immediately. Continue?
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 521}

参数表达式与来源：
```text
T_("If you enter this portal you might not be able to return "
                     "immediately. Continue?")
false
'n'

```

当前中文模板：进入这个传送门后可能无法立即返回。继续吗？

输入还原：进入这个传送门后可能无法立即返回。继续吗？

完整英文：
```text
If you enter this portal you could be pulled as deep as Abyss:%d and might not be able to return immediately. Continue?
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 525}

参数表达式与来源：
```text
make_stringf(T_("If you enter this portal you could be pulled as "
                     "deep as Abyss:%d and might not be able to return immediately. "
                     "Continue?"), abyss_default_depth(true)).c_str()
false
'n'
500:     case DNGN_SEALED_CLEAR_DOOR:
501:         mpr(T_("It's already closed!"));
502:         break;
503:     case DNGN_BROKEN_DOOR:
504:     case DNGN_BROKEN_CLEAR_DOOR:
505:         mpr(T_("It's broken and can't be closed!"));
506:         break;
507:     default:
508:         mpr(T_("There isn't anything that you can close there!"));
509:         break;
510:     }
511: }
512:
513: // Maybe prompt to enter a portal, return true if we should enter the
514: // portal, false if the user said no at the prompt.
515: bool prompt_dangerous_portal(dungeon_feature_type ftype)
516: {
517:     switch (ftype)
518:     {
519:     case DNGN_ENTER_PANDEMONIUM:
520:     case DNGN_ENTER_ZIGGURAT:
521:         return yesno(T_("If you enter this portal you might not be able to return "
522:                      "immediately. Continue?"), false, 'n');
523:     case DNGN_ENTER_ABYSS:
524:     {
525:         return yesno(make_stringf(T_("If you enter this portal you could be pulled as "
526:                      "deep as Abyss:%d and might not be able to return immediately. "
527:                      "Continue?"), abyss_default_depth(true)).c_str(), false, 'n');
528:     }
529:     default:
530:         return true;
531:     }
532: }
533:
534: bool prompt_descent_shortcut(dungeon_feature_type ftype)
535: {
536:     if (ftype == DNGN_ENTER_DEPTHS && !player_in_branch(BRANCH_SLIME)
537:         || ftype == DNGN_ENTER_SLIME && !player_in_branch(BRANCH_VAULTS))
538:     {
539:         return yesno(T_("This entrance appears to skip some branches and may be "
540:                      "quite dangerous. Continue anyway?"), false, 'n');
541:     }
542:     return true;
543: }
544:
545: static coord_def _rampage_destination(coord_def move, monster* target)
546: {
547:     const int dist = min(grid_distance(you.pos(), target->pos()) - 1,
548:                          you.rampaging());
549:     return you.pos() + move * dist;
550: }
551:
552: /// What can the player rampage towards in the given direction, if anything?
```

当前中文模板：进入这个传送门后可能会被拉到深渊第%d层，且可能无法立即返回。继续吗？

输入还原：None


### trunk

完整英文：
```text
If you enter this portal you might not be able to return immediately. Continue?
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 529}

参数表达式与来源：
```text
T_("If you enter this portal you might not be able to return "
                     "immediately. Continue?")
false
'n'

```

当前中文模板：进入这个传送门后可能无法立即返回。继续吗？

输入还原：进入这个传送门后可能无法立即返回。继续吗？

完整英文：
```text
If you enter this portal you could be pulled as deep as Abyss:%d and might not be able to return immediately. Continue?
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 533}

参数表达式与来源：
```text
make_stringf(T_("If you enter this portal you could be pulled as "
                     "deep as Abyss:%d and might not be able to return immediately. "
                     "Continue?"), abyss_default_depth(true)).c_str()
false
'n'
508:     case DNGN_SEALED_CLEAR_DOOR:
509:         mpr(T_("It's already closed!"));
510:         break;
511:     case DNGN_BROKEN_DOOR:
512:     case DNGN_BROKEN_CLEAR_DOOR:
513:         mpr(T_("It's broken and can't be closed!"));
514:         break;
515:     default:
516:         mpr(T_("There isn't anything that you can close there!"));
517:         break;
518:     }
519: }
520:
521: // Maybe prompt to enter a portal, return true if we should enter the
522: // portal, false if the user said no at the prompt.
523: bool prompt_dangerous_portal(dungeon_feature_type ftype)
524: {
525:     switch (ftype)
526:     {
527:     case DNGN_ENTER_PANDEMONIUM:
528:     case DNGN_ENTER_ZIGGURAT:
529:         return yesno(T_("If you enter this portal you might not be able to return "
530:                      "immediately. Continue?"), false, 'n');
531:     case DNGN_ENTER_ABYSS:
532:     {
533:         return yesno(make_stringf(T_("If you enter this portal you could be pulled as "
534:                      "deep as Abyss:%d and might not be able to return immediately. "
535:                      "Continue?"), abyss_default_depth(true)).c_str(), false, 'n');
536:     }
537:     case DNGN_ENTER_GULCH:
538:         return yesno(T_("If you enter this portal, the magical contamination on the "
539:                      "other side will temporarily mutate you thrice. Continue?"), false, 'n');
540:     default:
541:         return true;
542:     }
543: }
544:
545: bool prompt_descent_shortcut(dungeon_feature_type ftype)
546: {
547:     if (ftype == DNGN_ENTER_DEPTHS && !player_in_branch(BRANCH_SLIME)
548:         || ftype == DNGN_ENTER_SLIME && !player_in_branch(BRANCH_VAULTS))
549:     {
550:         return yesno(T_("This entrance appears to skip some branches and may be "
551:                      "quite dangerous. Continue anyway?"), false, 'n');
552:     }
553:     return true;
554: }
555:
556: static coord_def _rampage_destination(coord_def move, monster* target)
557: {
558:     const int dist = min(grid_distance(you.pos(), target->pos()) - 1,
559:                          you.rampaging());
560:     return you.pos() + move * dist;
```

当前中文模板：进入这个传送门后可能会被拉到深渊第%d层，且可能无法立即返回。继续吗？

输入还原：None

独立判断与参数还原：例可能会被拉到深渊第5层，且可能无法立即返回；as deep as 表示可达最大深度，现译作为可能目的地未断言固定深度。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-12 — ok


### stable

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5238}

参数表达式与来源：
```text
T_("You're already here!")

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5243}

参数表达式与来源：
```text
T_("Sorry, you can't auto-travel out of here.")

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。


### trunk

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5346}

参数表达式与来源：
```text
T_("You're already here!")

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5351}

参数表达式与来源：
```text
T_("Sorry, you can't auto-travel out of here.")

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-04 — ok


### stable

完整英文：
```text
Key pressed, stopping %s.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 1073}

参数表达式与来源：
```text
T_("Key pressed, stopping %s.")
you.running.runmode_name().c_str()
1048:     // retake them after this command.
1049:     last_stair.id = level_id::current();
1050:     last_stair.pos = you.pos();
1051:
1052:     return feat_stair_direction(env.grid(you.pos()));
1053: }
1054:
1055: // Top-level travel control (called indirectly from TravelDelay::handle()).
1056: //
1057: // travel() is responsible for making the individual moves that constitute
1058: // (interlevel) travel and explore and deciding when travel and explore
1059: // end.
1060: //
1061: // Don't call travel() if you.running >= 0.
1062: command_type travel()
1063: {
1064:     int holdx, holdy;
1065:     int *move_x = &holdx;
1066:     int *move_y = &holdy;
1067:     holdx = holdy = 0;
1068:
1069:     command_type result = CMD_NO_CMD;
1070:
1071:     if (Options.travel_key_stop && kbhit())
1072:     {
1073:         mprf(T_("Key pressed, stopping %s."),
1074:              you.running.runmode_name().c_str());
1075:         stop_running();
1076:         return CMD_NO_CMD;
1077:     }
1078:
1079:     // Excluded squares are only safe if marking stairs, i.e. another level.
1080:     if (is_excluded(you.pos()) && !is_stair_exclusion(you.pos()))
1081:     {
1082:         mprf(T_("You're in a travel-excluded area, stopping %s."),
1083:              you.running.runmode_name().c_str());
1084:         stop_running();
1085:         return CMD_NO_CMD;
1086:     }
1087:
1088:     if (you.running.is_explore())
1089:     {
1090:         // XXX: It is possible for the player to manually add a non-duration-based
1091:         //      status effect to this option, resulting in situations where
1092:         //      autoexplore can never move. We wait an arbitrary 500 turns before
1093:         //      deciding something must be wrong and stopping (to prevent an assert).
1094:         if (you.elapsed_time > you.elapsed_time_at_last_input + 5000
1095:             && you.props.exists(AUTO_REST_STATUS_POS)
1096:             && you.props[AUTO_REST_STATUS_POS].get_coord() == you.pos())
1097:         {
1098:             mprf(MSGCH_ERROR, "%s",
1099:                  T_("You appear to be waiting for the end of something which may "
```

当前中文模板：按下按键，停止%s。

输入还原：按下按键，停止探索。

完整英文：
```text
You're in a travel-excluded area, stopping %s.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 1082}

参数表达式与来源：
```text
T_("You're in a travel-excluded area, stopping %s.")
you.running.runmode_name().c_str()
1057: // travel() is responsible for making the individual moves that constitute
1058: // (interlevel) travel and explore and deciding when travel and explore
1059: // end.
1060: //
1061: // Don't call travel() if you.running >= 0.
1062: command_type travel()
1063: {
1064:     int holdx, holdy;
1065:     int *move_x = &holdx;
1066:     int *move_y = &holdy;
1067:     holdx = holdy = 0;
1068:
1069:     command_type result = CMD_NO_CMD;
1070:
1071:     if (Options.travel_key_stop && kbhit())
1072:     {
1073:         mprf(T_("Key pressed, stopping %s."),
1074:              you.running.runmode_name().c_str());
1075:         stop_running();
1076:         return CMD_NO_CMD;
1077:     }
1078:
1079:     // Excluded squares are only safe if marking stairs, i.e. another level.
1080:     if (is_excluded(you.pos()) && !is_stair_exclusion(you.pos()))
1081:     {
1082:         mprf(T_("You're in a travel-excluded area, stopping %s."),
1083:              you.running.runmode_name().c_str());
1084:         stop_running();
1085:         return CMD_NO_CMD;
1086:     }
1087:
1088:     if (you.running.is_explore())
1089:     {
1090:         // XXX: It is possible for the player to manually add a non-duration-based
1091:         //      status effect to this option, resulting in situations where
1092:         //      autoexplore can never move. We wait an arbitrary 500 turns before
1093:         //      deciding something must be wrong and stopping (to prevent an assert).
1094:         if (you.elapsed_time > you.elapsed_time_at_last_input + 5000
1095:             && you.props.exists(AUTO_REST_STATUS_POS)
1096:             && you.props[AUTO_REST_STATUS_POS].get_coord() == you.pos())
1097:         {
1098:             mprf(MSGCH_ERROR, "%s",
1099:                  T_("You appear to be waiting for the end of something which may "
1100:                     "never occur. Examine your explore_auto_rest_status option."));
1101:             stop_running();
1102:             return CMD_NO_CMD;
1103:         }
1104:
1105:         if (you.duration[DUR_NO_MOMENTUM]
1106:             || (Options.explore_auto_rest && !you.running.skip_autorest
1107:                 && !you.is_sufficiently_rested())
1108:             )
```

当前中文模板：你处于旅行禁区内，停止%s。

输入还原：你处于旅行禁区内，停止探索。


### trunk

完整英文：
```text
Key pressed, stopping %s.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 1108}

参数表达式与来源：
```text
T_("Key pressed, stopping %s.")
you.running.runmode_name().c_str()
1083:         }
1084:     case nonmove_reason::invalid:
1085:         die("_get_non_move_command with a move");
1086:     }
1087:     return CMD_NO_CMD;
1088: }
1089:
1090: // Top-level travel control (called indirectly from TravelDelay::handle()).
1091: //
1092: // travel() is responsible for making the individual moves that constitute
1093: // (interlevel) travel and explore and deciding when travel and explore
1094: // end.
1095: //
1096: // Don't call travel() if you.running >= 0.
1097: command_type travel()
1098: {
1099:     int holdx, holdy;
1100:     int *move_x = &holdx;
1101:     int *move_y = &holdy;
1102:     holdx = holdy = 0;
1103:
1104:     command_type result = CMD_NO_CMD;
1105:
1106:     if (Options.travel_key_stop && kbhit())
1107:     {
1108:         mprf(T_("Key pressed, stopping %s."),
1109:              you.running.runmode_name().c_str());
1110:         stop_running();
1111:         return CMD_NO_CMD;
1112:     }
1113:
1114:     // Excluded squares are only safe if marking stairs, i.e. another level.
1115:     if (is_excluded(you.pos()) && !is_stair_exclusion(you.pos()))
1116:     {
1117:         mprf(T_("You're in a travel-excluded area, stopping %s."),
1118:              you.running.runmode_name().c_str());
1119:         stop_running();
1120:         return CMD_NO_CMD;
1121:     }
1122:
1123:     if (you.running.is_explore())
1124:     {
1125:         // XXX: It is possible for the player to manually add a non-duration-based
1126:         //      status effect to this option, resulting in situations where
1127:         //      autoexplore can never move. We wait an arbitrary 500 turns before
1128:         //      deciding something must be wrong and stopping (to prevent an assert).
1129:         if (you.elapsed_time > you.elapsed_time_at_last_input + 5000
1130:             && you.props.exists(AUTO_REST_STATUS_POS)
1131:             && you.props[AUTO_REST_STATUS_POS].get_coord() == you.pos())
1132:         {
1133:             mprf(MSGCH_ERROR, "%s",
1134:                  T_("You appear to be waiting for the end of something which may "
```

当前中文模板：按下按键，停止%s。

输入还原：按下按键，停止探索。

完整英文：
```text
You're in a travel-excluded area, stopping %s.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 1117}

参数表达式与来源：
```text
T_("You're in a travel-excluded area, stopping %s.")
you.running.runmode_name().c_str()
1092: // travel() is responsible for making the individual moves that constitute
1093: // (interlevel) travel and explore and deciding when travel and explore
1094: // end.
1095: //
1096: // Don't call travel() if you.running >= 0.
1097: command_type travel()
1098: {
1099:     int holdx, holdy;
1100:     int *move_x = &holdx;
1101:     int *move_y = &holdy;
1102:     holdx = holdy = 0;
1103:
1104:     command_type result = CMD_NO_CMD;
1105:
1106:     if (Options.travel_key_stop && kbhit())
1107:     {
1108:         mprf(T_("Key pressed, stopping %s."),
1109:              you.running.runmode_name().c_str());
1110:         stop_running();
1111:         return CMD_NO_CMD;
1112:     }
1113:
1114:     // Excluded squares are only safe if marking stairs, i.e. another level.
1115:     if (is_excluded(you.pos()) && !is_stair_exclusion(you.pos()))
1116:     {
1117:         mprf(T_("You're in a travel-excluded area, stopping %s."),
1118:              you.running.runmode_name().c_str());
1119:         stop_running();
1120:         return CMD_NO_CMD;
1121:     }
1122:
1123:     if (you.running.is_explore())
1124:     {
1125:         // XXX: It is possible for the player to manually add a non-duration-based
1126:         //      status effect to this option, resulting in situations where
1127:         //      autoexplore can never move. We wait an arbitrary 500 turns before
1128:         //      deciding something must be wrong and stopping (to prevent an assert).
1129:         if (you.elapsed_time > you.elapsed_time_at_last_input + 5000
1130:             && you.props.exists(AUTO_REST_STATUS_POS)
1131:             && you.props[AUTO_REST_STATUS_POS].get_coord() == you.pos())
1132:         {
1133:             mprf(MSGCH_ERROR, "%s",
1134:                  T_("You appear to be waiting for the end of something which may "
1135:                     "never occur. Examine your explore_auto_rest_status option."));
1136:             stop_running();
1137:             return CMD_NO_CMD;
1138:         }
1139:
1140:         if (you.duration[DUR_NO_MOMENTUM]
1141:             || (Options.explore_auto_rest && !you.running.skip_autorest
1142:                 && !you.is_sufficiently_rested())
1143:             )
```

当前中文模板：你处于旅行禁区内，停止%s。

输入还原：你处于旅行禁区内，停止探索。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-05 — ok


### stable

完整英文：
```text
%s
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3427}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
3439:
3440:     case ABIL_OKAWARU_DUEL:
3441:         return okawaru_duel(beam.target, fail);
3442:
3443:     case ABIL_OKAWARU_GIFT_WEAPON:
3444:         if (!okawaru_gift_weapon())
3445:             return spret::abort;
3446:         break;
3447:
3448:     case ABIL_OKAWARU_GIFT_ARMOUR:
3449:         if (!okawaru_gift_armour())
3450:             return spret::abort;
3451:         break;
3452:
3453:     case ABIL_MAKHLEB_ANNIHILATION:
```

当前中文模板：%s

输入还原：None

完整英文：
```text
get
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3427}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
3439:
3440:     case ABIL_OKAWARU_DUEL:
3441:         return okawaru_duel(beam.target, fail);
3442:
3443:     case ABIL_OKAWARU_GIFT_WEAPON:
3444:         if (!okawaru_gift_weapon())
3445:             return spret::abort;
3446:         break;
3447:
3448:     case ABIL_OKAWARU_GIFT_ARMOUR:
3449:         if (!okawaru_gift_armour())
3450:             return spret::abort;
3451:         break;
3452:
3453:     case ABIL_MAKHLEB_ANNIHILATION:
```

当前中文模板：None

输入还原：None

完整英文：
```text
new energy.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3427}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
3439:
3440:     case ABIL_OKAWARU_DUEL:
3441:         return okawaru_duel(beam.target, fail);
3442:
3443:     case ABIL_OKAWARU_GIFT_WEAPON:
3444:         if (!okawaru_gift_weapon())
3445:             return spret::abort;
3446:         break;
3447:
3448:     case ABIL_OKAWARU_GIFT_ARMOUR:
3449:         if (!okawaru_gift_armour())
3450:             return spret::abort;
3451:         break;
3452:
3453:     case ABIL_MAKHLEB_ANNIHILATION:
```

当前中文模板：None

输入还原：None

完整英文：
```text
You can now deal lightning-fast blows.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3431}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You can now deal lightning-fast blows.")

```

当前中文模板：你现在可以施展闪电般的快速攻击了。

输入还原：你现在可以施展闪电般的快速攻击了。


### trunk

完整英文：
```text
%s
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3569}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
3581:     case ABIL_OKAWARU_DUEL:
3582:         return okawaru_duel(beam.target, fail);
3583:
3584:     case ABIL_OKAWARU_GIFT_WEAPON:
3585:         if (!okawaru_gift_weapon())
3586:             return spret::abort;
3587:         break;
3588:
3589:     case ABIL_OKAWARU_GIFT_ARMOUR:
3590:         if (!okawaru_gift_armour())
3591:             return spret::abort;
3592:         break;
3593:
3594:     case ABIL_MAKHLEB_ANNIHILATION:
3595:         return cast_iood(&you, _makhleb_annihilation_power(), &beam, 0, 0, MHITNOT,
```

当前中文模板：%s

输入还原：None

完整英文：
```text
get
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3569}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
3581:     case ABIL_OKAWARU_DUEL:
3582:         return okawaru_duel(beam.target, fail);
3583:
3584:     case ABIL_OKAWARU_GIFT_WEAPON:
3585:         if (!okawaru_gift_weapon())
3586:             return spret::abort;
3587:         break;
3588:
3589:     case ABIL_OKAWARU_GIFT_ARMOUR:
3590:         if (!okawaru_gift_armour())
3591:             return spret::abort;
3592:         break;
3593:
3594:     case ABIL_MAKHLEB_ANNIHILATION:
3595:         return cast_iood(&you, _makhleb_annihilation_power(), &beam, 0, 0, MHITNOT,
```

当前中文模板：None

输入还原：None

完整英文：
```text
new energy.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3569}

参数表达式与来源：
```text
MSGCH_DURATION
"%s"
you.hands_act("get", "new energy.").c_str()
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
3581:     case ABIL_OKAWARU_DUEL:
3582:         return okawaru_duel(beam.target, fail);
3583:
3584:     case ABIL_OKAWARU_GIFT_WEAPON:
3585:         if (!okawaru_gift_weapon())
3586:             return spret::abort;
3587:         break;
3588:
3589:     case ABIL_OKAWARU_GIFT_ARMOUR:
3590:         if (!okawaru_gift_armour())
3591:             return spret::abort;
3592:         break;
3593:
3594:     case ABIL_MAKHLEB_ANNIHILATION:
3595:         return cast_iood(&you, _makhleb_annihilation_power(), &beam, 0, 0, MHITNOT,
```

当前中文模板：None

输入还原：None

完整英文：
```text
You can now deal lightning-fast blows.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3573}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You can now deal lightning-fast blows.")

```

当前中文模板：你现在可以施展闪电般的快速攻击了。

输入还原：你现在可以施展闪电般的快速攻击了。

独立判断与参数还原：调用 get/new energy. 由 player::hands_act 中文专用整句键转成你的双手焕发出新的活力。；不能据裸 get 判英文泄漏。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-04 — ok


### stable

完整英文：
```text
 convulses!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2889}

参数表达式与来源：
```text
*mon
T_(" convulses!")
2864:         }
2865:     }
2866:     return victims;
2867: }
2868:
2869: static spret _siphon_essence(bool fail)
2870: {
2871:     if (_get_siphon_victims(true).empty()
2872:         && !yesno(T_("There are no victims visible. Siphon anyway?"), true, 'n'))
2873:     {
2874:         canned_msg(MSG_OK);
2875:         return spret::abort;
2876:     }
2877:
2878:     fail_check();
2879:
2880:     int damage = 0;
2881:     bool seen = false;
2882:     for (monster* mon : _get_siphon_victims(false))
2883:     {
2884:         const int dam = mon->hit_points / 2;
2885:         mon->hurt(&you, dam, BEAM_TORMENT_DAMAGE /*dubious*/);
2886:         damage += dam;
2887:         if (damage && mon->observable())
2888:         {
2889:             simple_monster_message(*mon, T_(" convulses!"));
2890:             behaviour_event(mon, ME_ANNOY);
2891:             seen = true;
2892:         }
2893:     }
2894:
2895:     you.increase_duration(DUR_SIPHON_COOLDOWN, 12 + random2(5));
2896:
2897:     if (!damage)
2898:     {
2899:         canned_msg(MSG_NOTHING_HAPPENS);
2900:         return spret::success;
2901:     }
2902:
2903:     if (seen)
2904:         mpr(T_("You feel stolen life flooding into you!"));
2905:     else
2906:         mpr(T_("You feel stolen life flooding into you from an unseen source!"));
2907:
2908:     if (you.hp == you.hp_max)
2909:         return spret::success;
2910:
2911:     // no death's door check because death form is incompatible with doors
2912:     // TODO: move this into transform.cc, use proper scaling and scale meaningfully
2913:     const int skillcap = 19 + get_form()->get_level(3);
2914:     const int healing = div_rand_round(min(damage, skillcap) * 2, 3); // max 67
```

当前中文模板：抽搐起来！

输入还原：兽人抽搐起来！


### trunk

完整英文：
```text
 convulses!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3032}

参数表达式与来源：
```text
*mon
T_(" convulses!")
3007:         }
3008:     }
3009:     return victims;
3010: }
3011:
3012: static spret _siphon_essence(bool fail)
3013: {
3014:     if (_get_siphon_victims(true).empty()
3015:         && !yesno(T_("There are no victims visible. Siphon anyway?"), true, 'n'))
3016:     {
3017:         canned_msg(MSG_OK);
3018:         return spret::abort;
3019:     }
3020:
3021:     fail_check();
3022:
3023:     int damage = 0;
3024:     bool seen = false;
3025:     for (monster* mon : _get_siphon_victims(false))
3026:     {
3027:         const int dam = mon->hit_points / 2;
3028:         mon->hurt(&you, dam, BEAM_TORMENT_DAMAGE /*dubious*/);
3029:         damage += dam;
3030:         if (damage && mon->observable())
3031:         {
3032:             simple_monster_message(*mon, T_(" convulses!"));
3033:             behaviour_event(mon, ME_ANNOY);
3034:             seen = true;
3035:         }
3036:     }
3037:
3038:     you.increase_duration(DUR_SIPHON_COOLDOWN, 12 + random2(5));
3039:
3040:     if (!damage)
3041:     {
3042:         canned_msg(MSG_NOTHING_HAPPENS);
3043:         return spret::success;
3044:     }
3045:
3046:     if (seen)
3047:         mpr(T_("You feel stolen life flooding into you!"));
3048:     else
3049:         mpr(T_("You feel stolen life flooding into you from an unseen source!"));
3050:
3051:     if (you.hp == you.hp_max)
3052:         return spret::success;
3053:
3054:     // no death's door check because death form is incompatible with doors
3055:     // TODO: move this into transform.cc, use proper scaling and scale meaningfully
3056:     const int skillcap = 19 + get_form()->get_level(3);
3057:     const int healing = div_rand_round(min(damage, skillcap) * 2, 3); // max 67
```

当前中文模板：抽搐起来！

输入还原：兽人抽搐起来！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-03 — ok


### stable

完整英文：
```text
%s burns to shimmering ash in your grasp.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1910}

参数表达式与来源：
```text
T_("%s burns to shimmering ash in your grasp.")
it.name(DESC_THE).c_str()
1885:     {
1886:         dungeon_events.fire_position_event(dgn_event(DET_ITEM_PICKUP,
1887:                                                      you.pos(), 0, obj,
1888:                                                      -1),
1889:                                            you.pos());
1890:
1891:         // XXX: Waiting until now to decrement the quantity may give Windows
1892:         // tiles players the opportunity to close the window and duplicate the
1893:         // item (a variant of bug #6486). However, we can't decrement the
1894:         // quantity before firing the position event, because the latter needs
1895:         // the object's index.
1896:         dec_mitm_item_quantity(obj, quant_got);
1897:
1898:         you.turn_is_over = true;
1899:     }
1900:
1901:     return keep_going;
1902: }
1903:
1904: static void _get_book(item_def& it)
1905: {
1906:     if (it.sub_type != BOOK_MANUAL)
1907:     {
1908:         if (you.has_mutation(MUT_INNATE_CASTER))
1909:         {
1910:             mprf(T_("%s burns to shimmering ash in your grasp."),
1911:                  it.name(DESC_THE).c_str());
1912:             return;
1913:         }
1914:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1915:
1916:         if (!library_add_spells(spells_in_book(it)))
1917:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1918:
1919:         taken_new_item(it.base_type);
1920:
1921:         return;
1922:     }
1923:     // This is mainly for save compat: if a manual generated somehow that is not
1924:     // id'd, the following message is completely useless
1925:     identify_item(it);
1926:     const skill_type sk = static_cast<skill_type>(it.plus);
1927:
1928:     if (is_useless_skill(sk))
1929:     {
1930:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1931:              it.name(DESC_A).c_str());
1932:         return;
1933:     }
1934:
1935:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1936:     {
```

当前中文模板：%s在你手中化为闪亮的灰烬。

输入还原：None

完整英文：
```text
You pick up the %s and begin to read...
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1914}

参数表达式与来源：
```text
T_("You pick up the %s and begin to read...")
it.name(DESC_A).c_str()
1889:                                            you.pos());
1890:
1891:         // XXX: Waiting until now to decrement the quantity may give Windows
1892:         // tiles players the opportunity to close the window and duplicate the
1893:         // item (a variant of bug #6486). However, we can't decrement the
1894:         // quantity before firing the position event, because the latter needs
1895:         // the object's index.
1896:         dec_mitm_item_quantity(obj, quant_got);
1897:
1898:         you.turn_is_over = true;
1899:     }
1900:
1901:     return keep_going;
1902: }
1903:
1904: static void _get_book(item_def& it)
1905: {
1906:     if (it.sub_type != BOOK_MANUAL)
1907:     {
1908:         if (you.has_mutation(MUT_INNATE_CASTER))
1909:         {
1910:             mprf(T_("%s burns to shimmering ash in your grasp."),
1911:                  it.name(DESC_THE).c_str());
1912:             return;
1913:         }
1914:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1915:
1916:         if (!library_add_spells(spells_in_book(it)))
1917:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1918:
1919:         taken_new_item(it.base_type);
1920:
1921:         return;
1922:     }
1923:     // This is mainly for save compat: if a manual generated somehow that is not
1924:     // id'd, the following message is completely useless
1925:     identify_item(it);
1926:     const skill_type sk = static_cast<skill_type>(it.plus);
1927:
1928:     if (is_useless_skill(sk))
1929:     {
1930:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1931:              it.name(DESC_A).c_str());
1932:         return;
1933:     }
1934:
1935:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1936:     {
1937:         mprf(T_("You pick up %s, but it has nothing more to teach you."),
1938:              it.name(DESC_A).c_str());
1939:         return;
```

当前中文模板：你捡起了%s并开始阅读……

输入还原：None

完整英文：
```text
Unfortunately, you learned nothing new or useful.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1917}

参数表达式与来源：
```text
T_("Unfortunately, you learned nothing new or useful.")

```

当前中文模板：遗憾的是，你没有学到任何新的或有用的东西。

输入还原：遗憾的是，你没有学到任何新的或有用的东西。


### trunk

完整英文：
```text
%s burns to shimmering ash in your grasp.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1873}

参数表达式与来源：
```text
T_("%s burns to shimmering ash in your grasp.")
it.name(DESC_THE).c_str()
1848:     {
1849:         dungeon_events.fire_position_event(dgn_event(DET_ITEM_PICKUP,
1850:                                                      you.pos(), 0, obj,
1851:                                                      -1),
1852:                                            you.pos());
1853:
1854:         // XXX: Waiting until now to decrement the quantity may give Windows
1855:         // tiles players the opportunity to close the window and duplicate the
1856:         // item (a variant of bug #6486). However, we can't decrement the
1857:         // quantity before firing the position event, because the latter needs
1858:         // the object's index.
1859:         dec_mitm_item_quantity(obj, quant_got);
1860:
1861:         you.turn_is_over = true;
1862:     }
1863:
1864:     return keep_going;
1865: }
1866:
1867: static void _get_book(item_def& it)
1868: {
1869:     if (it.sub_type != BOOK_MANUAL)
1870:     {
1871:         if (you.has_mutation(MUT_INNATE_CASTER))
1872:         {
1873:             mprf(T_("%s burns to shimmering ash in your grasp."),
1874:                  it.name(DESC_THE).c_str());
1875:             return;
1876:         }
1877:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1878:
1879:         if (!library_add_spells(spells_in_book(it)))
1880:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1881:
1882:         taken_new_item(it.base_type);
1883:
1884:         return;
1885:     }
1886:     // This is mainly for save compat: if a manual generated somehow that is not
1887:     // id'd, the following message is completely useless
1888:     identify_item(it);
1889:     const skill_type sk = static_cast<skill_type>(it.plus);
1890:
1891:     if (is_useless_skill(sk))
1892:     {
1893:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1894:              it.name(DESC_A).c_str());
1895:         return;
1896:     }
1897:
1898:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1899:     {
```

当前中文模板：%s在你手中化为闪亮的灰烬。

输入还原：None

完整英文：
```text
You pick up the %s and begin to read...
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1877}

参数表达式与来源：
```text
T_("You pick up the %s and begin to read...")
it.name(DESC_A).c_str()
1852:                                            you.pos());
1853:
1854:         // XXX: Waiting until now to decrement the quantity may give Windows
1855:         // tiles players the opportunity to close the window and duplicate the
1856:         // item (a variant of bug #6486). However, we can't decrement the
1857:         // quantity before firing the position event, because the latter needs
1858:         // the object's index.
1859:         dec_mitm_item_quantity(obj, quant_got);
1860:
1861:         you.turn_is_over = true;
1862:     }
1863:
1864:     return keep_going;
1865: }
1866:
1867: static void _get_book(item_def& it)
1868: {
1869:     if (it.sub_type != BOOK_MANUAL)
1870:     {
1871:         if (you.has_mutation(MUT_INNATE_CASTER))
1872:         {
1873:             mprf(T_("%s burns to shimmering ash in your grasp."),
1874:                  it.name(DESC_THE).c_str());
1875:             return;
1876:         }
1877:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1878:
1879:         if (!library_add_spells(spells_in_book(it)))
1880:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1881:
1882:         taken_new_item(it.base_type);
1883:
1884:         return;
1885:     }
1886:     // This is mainly for save compat: if a manual generated somehow that is not
1887:     // id'd, the following message is completely useless
1888:     identify_item(it);
1889:     const skill_type sk = static_cast<skill_type>(it.plus);
1890:
1891:     if (is_useless_skill(sk))
1892:     {
1893:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1894:              it.name(DESC_A).c_str());
1895:         return;
1896:     }
1897:
1898:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1899:     {
1900:         mprf(T_("You pick up %s, but it has nothing more to teach you."),
1901:              it.name(DESC_A).c_str());
1902:         return;
```

当前中文模板：你捡起了%s并开始阅读……

输入还原：None

完整英文：
```text
Unfortunately, you learned nothing new or useful.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1880}

参数表达式与来源：
```text
T_("Unfortunately, you learned nothing new or useful.")

```

当前中文模板：遗憾的是，你没有学到任何新的或有用的东西。

输入还原：遗憾的是，你没有学到任何新的或有用的东西。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-03 — objective_error


### stable

完整英文：
```text
%s's hold on you weakens, but your attempt to escape fails.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 8644}

参数表达式与来源：
```text
T_("%s's hold on you weakens, but your attempt to escape fails.")
object.c_str()
8619:               ? C_("constrictor possessive", "the zombie hands'")
8620:           : constricted_type == CONSTRICT_ENTANGLE
8621:               ? C_("constrictor possessive", "the vines'")
8622:               : themonst->name(DESC_ITS, true);
8623:
8624:     if (x_chance_in_y(_constriction_escape_chance(escape_attempts), 100))
8625:     {
8626:         mprf(C_("constriction escape", "You break free of %s grasp."),
8627:              object.c_str());
8628:
8629:         // Stun the monster we struggled again and prevent the player from being
8630:         // constricted for several turns (so that they are guaranteed to be able
8631:         // to make it up the stairs after pulling away this way)
8632:         if (constricted_type == CONSTRICT_MELEE)
8633:         {
8634:             themonst->speed_increment -= 10;
8635:             you.duration[DUR_CONSTRICTION_IMMUNITY] = 20;
8636:         }
8637:
8638:         stop_being_constricted(true);
8639:
8640:         return true;
8641:     }
8642:     else
8643:     {
8644:         mprf(T_("%s's hold on you weakens, but your attempt to escape fails."),
8645:              object.c_str());
8646:         turn_is_over = true;
8647:         return false;
8648:     }
8649: }
8650:
8651: void player::sentinel_mark(bool trap)
8652: {
8653:     flash_tile(you.pos(), YELLOW, 120, TILE_BOLT_SENTINEL_MARK);
8654:     if (duration[DUR_SENTINEL_MARK])
8655:     {
8656:         mpr(T_("The mark on you glows brighter."));
8657:         increase_duration(DUR_SENTINEL_MARK, random_range(20, 40), 180);
8658:     }
8659:     else
8660:     {
8661:         mprf(MSGCH_WARN, T_("A sentinel's mark forms upon you."));
8662:         increase_duration(DUR_SENTINEL_MARK, trap ? random_range(25, 40)
8663:                                                   : random_range(35, 60),
8664:                           250);
8665:     }
8666: }
8667:
8668: /*
8669:  * Is the player too terrified to move (because of fungusform)?
8670:  *
```

当前中文模板：%s对你的掌控减弱了，但你逃脱的尝试失败了。

输入还原：None


### trunk

完整英文：
```text
%s hold on you weakens, but your attempt to escape fails.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 8924}

参数表达式与来源：
```text
T_("%s hold on you weakens, but your attempt to escape fails.")
object.c_str()
8899:     const string object
8900:         = constricted_type == CONSTRICT_ROOTS      ? C_("constrictor possessive", "the roots'")
8901:           : constricted_type == CONSTRICT_BVC      ? C_("constrictor possessive", "the zombie hands'")
8902:           : constricted_type == CONSTRICT_ENTANGLE ? C_("constrictor possessive", "the vines'")
8903:           : you.aware_of(*themonst) ? themonst->name(DESC_ITS, true) : C_("constrictor possessive", "something's");
8904:
8905:     if (x_chance_in_y(_constriction_escape_chance(escape_attempts), 100))
8906:     {
8907:         mprf(C_("constriction escape", "You break free of %s grasp."), object.c_str());
8908:
8909:         // Stun the monster we struggled again and prevent the player from being
8910:         // constricted for several turns (so that they are guaranteed to be able
8911:         // to make it up the stairs after pulling away this way)
8912:         if (constricted_type == CONSTRICT_MELEE)
8913:         {
8914:             themonst->speed_increment -= 10;
8915:             you.duration[DUR_CONSTRICTION_IMMUNITY] = 20;
8916:         }
8917:
8918:         stop_being_constricted(true);
8919:
8920:         return true;
8921:     }
8922:     else
8923:     {
8924:         mprf(T_("%s hold on you weakens, but your attempt to escape fails."),
8925:              object.c_str());
8926:         turn_is_over = true;
8927:         return false;
8928:     }
8929: }
8930:
8931: void player::sentinel_mark(bool trap)
8932: {
8933:     flash_tile(you.pos(), YELLOW, 120, TILE_BOLT_SENTINEL_MARK);
8934:     if (duration[DUR_SENTINEL_MARK])
8935:     {
8936:         mpr(T_("The mark on you glows brighter."));
8937:         increase_duration(DUR_SENTINEL_MARK, random_range(20, 40), 180);
8938:     }
8939:     else
8940:     {
8941:         mprf(MSGCH_WARN, T_("A sentinel's mark forms upon you."));
8942:         increase_duration(DUR_SENTINEL_MARK, trap ? random_range(25, 40)
8943:                                                   : random_range(35, 60),
8944:                           250);
8945:     }
8946: }
8947:
8948: /*
8949:  * Is the player too terrified to move (because of fungusform)?
8950:  *
```

当前中文模板：%s束缚减弱了，但你逃脱的尝试失败了。

输入还原：None

独立判断与参数还原：object 已是 DESC_ITS 所有格，直接接“对你的掌控”产生“兽人的对你的”语病。；树根、尸手、藤蔓所有格上下文键的值为空，回退英文；独立于中文所有格语序问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "composition", "line": "stable", "english": "%s's hold on you weakens, but your attempt to escape fails.", "current_full_zh": "兽人的对你的掌控减弱了，但你逃脱的尝试失败了。", "problem": "object 已是 DESC_ITS 所有格，直接接“对你的掌控”产生“兽人的对你的”语病。", "suggested_zh": "兽人对你的束缚减弱了，但你逃脱的尝试失败了。", "evidence": "stable player.cc:8622,8644；apostrophise 经 %s's→%s的。", "defect_points": 1}

发现：{"type": "untranslated_parameter", "line": "stable", "english": "%s's hold on you weakens, but your attempt to escape fails.", "current_full_zh": "the roots'对你的掌控减弱了，但你逃脱的尝试失败了。", "problem": "树根、尸手、藤蔓所有格上下文键的值为空，回退英文；独立于中文所有格语序问题。", "suggested_zh": "树根对你的束缚减弱了，但你逃脱的尝试失败了。", "evidence": "stable player.cc:8619-8622；source.txt:48970,48974,48978 空译文；trunk 对应键已译。", "defect_points": 1}


## E-07 — ok


### stable

完整英文：
```text
You feel the orb feeding on your energy!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2837}

参数表达式与来源：
```text
T_("You feel the orb feeding on your energy!")

```

当前中文模板：你感到宝珠在汲取你的能量！

输入还原：你感到宝珠在汲取你的能量！


### trunk

完整英文：
```text
You feel the orb feeding on your energy!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2981}

参数表达式与来源：
```text
T_("You feel the orb feeding on your energy!")

```

当前中文模板：你感到宝珠在汲取你的能量！

输入还原：你感到宝珠在汲取你的能量！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-06 — readability


### stable

完整英文：
```text
You reflect %s with the mirror!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 711}

参数表达式与来源：
```text
T_("You reflect %s with the mirror!")
victim->name(DESC_THE).c_str()
686:     monster* mon = clone_mons(victim, true, nullptr, ATT_FRIENDLY);
687:     if (!mon)
688:     {
689:         canned_msg(MSG_NOTHING_HAPPENS);
690:         return spret::fail;
691:     }
692:     const int power = 5 + you.skill(SK_EVOCATIONS, 3);
693:     int dur = min(6, max(1, (you.skill(SK_EVOCATIONS, 1) / 4 + 1)
694:                          * (100 - victim->check_willpower(&you, power)) / 100));
695:
696:     mon->mark_summoned(SPELL_PHANTOM_MIRROR, summ_dur(dur), true, true);
697:
698:     mon->summoner = MID_PLAYER;
699:     mons_add_blame(mon, "mirrored by the player character");
700:     mon->add_ench(ENCH_PHANTOM_MIRROR);
701:     mon->add_ench(mon_enchant(ENCH_DRAINED, &you, INFINITE_DURATION,
702:                               div_rand_round(mon->get_experience_level(), 3)));
703:
704:     mon->behaviour = BEH_SEEK;
705:     set_nearest_monster_foe(mon);
706:
707:     // If the original monster was unrewarding, and these flags are copied, the
708:     // mirrored copy will not properly count as summoned for some purposes.
709:     mon->flags &= ~(MF_HARD_RESET | MF_NO_REWARD);
710:
711:     mprf(T_("You reflect %s with the mirror!"),
712:          victim->name(DESC_THE).c_str());
713:
714:     return spret::success;
715: }
716:
717: static bool _valid_tremorstone_target(const monster &m)
718: {
719:     return !m.is_firewood();
720: }
721:
722: /**
723:  * Find the cell at range 3 closest to the center of mass of monsters in range,
724:  * or a random range 3 cell if there are none.
725:  *
726:  * @param see_targets a boolean parameter indicating if the user can see any of
727:  * the targets
728:  * @return The cell in question.
729:  */
730: static coord_def _find_tremorstone_target(bool& see_targets)
731: {
732:     coord_def com = {0, 0};
733:     see_targets = false;
734:     int num = 0;
735:
736:     for (radius_iterator ri(you.pos(), LOS_NO_TRANS); ri; ++ri)
737:     {
```

当前中文模板：你用镜子反射了%s！

输入还原：你用镜子反射了兽人！


### trunk

完整英文：
```text
You reflect %s with the mirror!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 685}

参数表达式与来源：
```text
T_("You reflect %s with the mirror!")
victim->name(DESC_THE).c_str()
660:     monster* mon = clone_mons(victim, true, nullptr, ATT_FRIENDLY);
661:     if (!mon)
662:     {
663:         canned_msg(MSG_NOTHING_HAPPENS);
664:         return spret::fail;
665:     }
666:     const int power = 5 + you.skill(SK_EVOCATIONS, 3);
667:     int dur = min(6, max(1, (you.skill(SK_EVOCATIONS, 1) / 4 + 1)
668:                          * (100 - victim->check_willpower(&you, power)) / 100));
669:
670:     mon->mark_summoned(SPELL_PHANTOM_MIRROR, summ_dur(dur), true, true);
671:
672:     mon->summoner = MID_PLAYER;
673:     mons_add_blame(mon, "mirrored by the player character");
674:     mon->add_ench(ENCH_PHANTOM_MIRROR);
675:     mon->add_ench(mon_enchant(ENCH_DRAINED, &you, INFINITE_DURATION,
676:                               div_rand_round(mon->get_experience_level(), 3)));
677:
678:     mon->behaviour = BEH_SEEK;
679:     set_nearest_monster_foe(mon);
680:
681:     // If the original monster was unrewarding, and these flags are copied, the
682:     // mirrored copy will not properly count as summoned for some purposes.
683:     mon->flags &= ~(MF_HARD_RESET | MF_NO_REWARD);
684:
685:     mprf(T_("You reflect %s with the mirror!"),
686:          victim->name(DESC_THE).c_str());
687:
688:     return spret::success;
689: }
690:
691: static bool _valid_tremorstone_target(const monster &m)
692: {
693:     return !m.is_firewood();
694: }
695:
696: /**
697:  * Find the cell at range 3 closest to the center of mass of monsters in range,
698:  * or a random range 3 cell if there are none.
699:  *
700:  * @param see_targets a boolean parameter indicating if the user can see any of
701:  * the targets
702:  * @return The cell in question.
703:  */
704: static coord_def _find_tremorstone_target(bool& see_targets)
705: {
706:     coord_def com = {0, 0};
707:     see_targets = false;
708:     int num = 0;
709:
710:     for (radius_iterator ri(you.pos(), LOS_NO_TRANS); ri; ++ri)
711:     {
```

当前中文模板：你用镜子反射了%s！

输入还原：你用镜子反射了兽人！

独立判断与参数还原：反射兽人的搭配较生硬，可用映像表达镜像克隆。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "wording", "line": "both", "english": "You reflect %s with the mirror!", "current_full_zh": "你用镜子反射了兽人！", "problem": "反射兽人的搭配较生硬，可用映像表达镜像克隆。", "suggested_zh": "你用镜子映出了兽人的镜像！", "evidence": "stable {'path': 'crawl-ref/source/evoke.cc', 'line': 711}; trunk {'path': 'crawl-ref/source/evoke.cc', 'line': 685}", "defect_points": 0}


## E-10 — ok


### stable

完整英文：
```text
You invoke the name of Kikubaaqudgha!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3338}

参数表达式与来源：
```text
T_("You invoke the name of Kikubaaqudgha!")

```

当前中文模板：你唤起了奇库巴库哈之名！

输入还原：你唤起了奇库巴库哈之名！


### trunk

完整英文：
```text
You invoke the name of Kikubaaqudgha!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3480}

参数表达式与来源：
```text
T_("You invoke the name of Kikubaaqudgha!")

```

当前中文模板：你唤起了奇库巴库哈之名！

输入还原：你唤起了奇库巴库哈之名！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-11 — ok


### stable

完整英文：
```text
You have traversed the Zig. Zot will no longer hunt you.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 286}

参数表达式与来源：
```text
T_("You have traversed the Zig. Zot will no longer hunt you.")

```

当前中文模板：你已穿越通天塔。佐特将不再追猎你。

输入还原：你已穿越通天塔。佐特将不再追猎你。


### trunk

完整英文：
```text
You have traversed the Zig. Zot will no longer hunt you.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 288}

参数表达式与来源：
```text
T_("You have traversed the Zig. Zot will no longer hunt you.")

```

当前中文模板：你已穿越通天塔。佐特将不再追猎你。

输入还原：你已穿越通天塔。佐特将不再追猎你。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-01 — ok


### stable

完整英文：
```text
You whisper farewell to %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 5180}

参数表达式与来源：
```text
T_("You whisper farewell to %s.")
name.c_str()
5155:
5156: void maybe_name_weapon(item_def &item, bool silent)
5157: {
5158:     const bool has_own_name = is_artefact(item);
5159:     const bool new_name = has_own_name
5160:                           || !item.props.exists(WEAPON_NAME_KEY);
5161:
5162:     if (new_name && !has_own_name)
5163:         name_weapon(item);
5164:
5165:     if (silent)
5166:         return;
5167:
5168:     string full_name = get_weapon_name(item, true);
5169:
5170:     // TODO: variant messages? (in the database?)
5171:     mprf(new_name ? T_("You welcome %s into your grasp.")
5172:                   : T_("You welcome %s back into your grasp."), full_name.c_str());
5173: }
5174:
5175: void say_farewell_to_weapon(const item_def &item)
5176: {
5177:     string name = get_weapon_name(item, false);
5178:
5179:     // TODO: variant messages? (in the database?)
5180:     mprf(T_("You whisper farewell to %s."), name.c_str());
5181: }
5182:
5183: // Returns whether an additional copy of a given item in the player's inventory
5184: // would be strictly redundant with ones they already have.
5185: bool jewellery_is_redundant(const item_def& item)
5186: {
5187:     if (item.base_type != OBJ_JEWELLERY || is_artefact(item))
5188:         return false;
5189:
5190:     const jewellery_type type = static_cast<jewellery_type>(item.sub_type);
5191:     const int slots = jewellery_is_amulet(type) ? you.equipment.num_slots[SLOT_AMULET]
5192:                                                 : you.equipment.num_slots[SLOT_RING];
5193:     const int limit = min(slots, jewellery_usefulness_limit(type));
5194:
5195:     // A new item would be useless if we already have as many copies as we can use.
5196:     int count = 0;
5197:     for (int i = 0; i < MAX_GEAR; ++i)
5198:     {
5199:         if (you.inv[i].is_type(OBJ_JEWELLERY, type) && !is_artefact(you.inv[i]))
5200:         {
5201:             ++count;
5202:             if (count >= limit)
5203:                 return true;
5204:         }
5205:     }
```

当前中文模板：你低声向%s告别。

输入还原：None


### trunk

完整英文：
```text
You whisper farewell to %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 5118}

参数表达式与来源：
```text
T_("You whisper farewell to %s.")
name.c_str()
5093:
5094: void maybe_name_weapon(item_def &item, bool silent)
5095: {
5096:     const bool has_own_name = is_artefact(item);
5097:     const bool new_name = has_own_name
5098:                           || !item.props.exists(WEAPON_NAME_KEY);
5099:
5100:     if (new_name && !has_own_name)
5101:         name_weapon(item);
5102:
5103:     if (silent)
5104:         return;
5105:
5106:     string full_name = get_weapon_name(item, true);
5107:
5108:     // TODO: variant messages? (in the database?)
5109:     mprf(new_name ? T_("You welcome %s into your grasp.")
5110:                   : T_("You welcome %s back into your grasp."), full_name.c_str());
5111: }
5112:
5113: void say_farewell_to_weapon(const item_def &item)
5114: {
5115:     string name = get_weapon_name(item, false);
5116:
5117:     // TODO: variant messages? (in the database?)
5118:     mprf(T_("You whisper farewell to %s."), name.c_str());
5119: }
5120:
5121: // Returns whether an additional copy of a given item in the player's inventory
5122: // would be strictly redundant with ones they already have.
5123: bool jewellery_is_redundant(const item_def& item)
5124: {
5125:     if (item.base_type != OBJ_JEWELLERY || is_artefact(item))
5126:         return false;
5127:
5128:     const jewellery_type type = static_cast<jewellery_type>(item.sub_type);
5129:     const int slots = jewellery_is_amulet(type) ? you.equipment.num_slots[SLOT_AMULET]
5130:                                                 : you.equipment.num_slots[SLOT_RING];
5131:     const int limit = min(slots, jewellery_usefulness_limit(type));
5132:
5133:     // A new item would be useless if we already have as many copies as we can use.
5134:     int count = 0;
5135:     for (int i = 0; i < MAX_GEAR; ++i)
5136:     {
5137:         if (you.inv[i].is_type(OBJ_JEWELLERY, type) && !is_artefact(you.inv[i]))
5138:         {
5139:             ++count;
5140:             if (count >= limit)
5141:                 return true;
5142:         }
5143:     }
```

当前中文模板：你低声向%s告别。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-03 — objective_error


### stable

完整英文：
```text
You wrap your dark will around %s soul!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3404}

参数表达式与来源：
```text
T_("You wrap your dark will around %s soul!")
mons->name(DESC_ITS).c_str()
3379:         // XXX: Some invo formula
3380:         you.duration[DUR_FATHOMLESS_SHACKLES] = random_range(15, 25) * BASELINE_DELAY;
3381:         yred_make_blasphemy();
3382:         invalidate_agrid(true);
3383:         break;
3384:
3385:     case ABIL_YRED_BIND_SOUL:
3386:     {
3387:         monster* mons = monster_at(beam.target);
3388:
3389:         if (mons && you.can_see(*mons) && mons->is_illusion())
3390:         {
3391:             fail_check();
3392:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3393:                  mons->name(DESC_ITS).c_str(),
3394:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3395:             // Still costs a turn to gain the information.
3396:             return spret::success;
3397:         }
3398:
3399:         fail_check();
3400:
3401:         int pain = you.hp / 3;
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
```

当前中文模板：你用黑暗意志包裹了%s灵魂！

输入还原：你用黑暗意志包裹了兽人的灵魂！

完整英文：
```text
You feel more confident with your borrowed prowess.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3411}

参数表达式与来源：
```text
MSGCH_DURATION
you.duration[DUR_HEROISM]
             ? "You feel more confident with your borrowed prowess."
             : "You gain the combat prowess of a mighty hero."
3386:     {
3387:         monster* mons = monster_at(beam.target);
3388:
3389:         if (mons && you.can_see(*mons) && mons->is_illusion())
3390:         {
3391:             fail_check();
3392:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3393:                  mons->name(DESC_ITS).c_str(),
3394:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3395:             // Still costs a turn to gain the information.
3396:             return spret::success;
3397:         }
3398:
3399:         fail_check();
3400:
3401:         int pain = you.hp / 3;
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
```

当前中文模板：None

输入还原：None

完整英文：
```text
You gain the combat prowess of a mighty hero.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3411}

参数表达式与来源：
```text
MSGCH_DURATION
you.duration[DUR_HEROISM]
             ? "You feel more confident with your borrowed prowess."
             : "You gain the combat prowess of a mighty hero."
3386:     {
3387:         monster* mons = monster_at(beam.target);
3388:
3389:         if (mons && you.can_see(*mons) && mons->is_illusion())
3390:         {
3391:             fail_check();
3392:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3393:                  mons->name(DESC_ITS).c_str(),
3394:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3395:             // Still costs a turn to gain the information.
3396:             return spret::success;
3397:         }
3398:
3399:         fail_check();
3400:
3401:         int pain = you.hp / 3;
3402:         dec_hp(pain, false);
3403:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3404:         mprf(T_("You wrap your dark will around %s soul!"),
3405:               mons->name(DESC_ITS).c_str());
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
```

当前中文模板：None

输入还原：None


### trunk

完整英文：
```text
You wrap your dark will around %s soul!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3546}

参数表达式与来源：
```text
T_("You wrap your dark will around %s soul!")
mons->name(DESC_ITS).c_str()
3521:         // XXX: Some invo formula
3522:         you.duration[DUR_FATHOMLESS_SHACKLES] = random_range(15, 25) * BASELINE_DELAY;
3523:         yred_make_blasphemy();
3524:         invalidate_agrid();
3525:         break;
3526:
3527:     case ABIL_YRED_BIND_SOUL:
3528:     {
3529:         monster* mons = monster_at(beam.target);
3530:
3531:         if (mons->is_illusion())
3532:         {
3533:             fail_check();
3534:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3535:                  mons->name(DESC_ITS).c_str(),
3536:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3537:             // Still costs a turn to gain the information.
3538:             return spret::success;
3539:         }
3540:
3541:         fail_check();
3542:
3543:         int pain = you.hp / 3;
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
```

当前中文模板：你用黑暗意志包裹了%s灵魂！

输入还原：你用黑暗意志包裹了兽人的灵魂！

完整英文：
```text
You feel more confident with your borrowed prowess.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3553}

参数表达式与来源：
```text
MSGCH_DURATION
you.duration[DUR_HEROISM]
             ? T_("You feel more confident with your borrowed prowess.")
             : T_("You gain the combat prowess of a mighty hero.")

```

当前中文模板：借来的武艺让你更加自信。

输入还原：借来的武艺让你更加自信。

完整英文：
```text
You gain the combat prowess of a mighty hero.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3553}

参数表达式与来源：
```text
MSGCH_DURATION
you.duration[DUR_HEROISM]
             ? T_("You feel more confident with your borrowed prowess.")
             : T_("You gain the combat prowess of a mighty hero.")

```

当前中文模板：你获得了强大英雄的战斗技艺。

输入还原：你获得了强大英雄的战斗技艺。

独立判断与参数还原：Heroism 两分支直接传英文，未调用 T_，会显示英文。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "untranslated", "line": "stable", "english": "You feel more confident with your borrowed prowess. / You gain the combat prowess of a mighty hero.", "current_full_zh": "You feel more confident with your borrowed prowess. / You gain the combat prowess of a mighty hero.", "problem": "Heroism 两分支直接传英文，未调用 T_，会显示英文。", "suggested_zh": "借来的武艺让你更加自信。 / 你获得了强大英雄的战斗技艺。", "evidence": "stable ability.cc:3411-3413；trunk :3553-3555 已加 T_。", "defect_points": 1}


## D-10 — ok


### stable

完整英文：
```text
It is a scroll of brand weapon.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3181}

参数表达式与来源：
```text
T_("It is a scroll of brand weapon.")

```

当前中文模板：这是一张武器铭印卷轴。

输入还原：这是一张武器铭印卷轴。


### trunk

完整英文：
```text
It is a scroll of brand weapon.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3315}

参数表达式与来源：
```text
T_("It is a scroll of brand weapon.")

```

当前中文模板：这是一张武器铭印卷轴。

输入还原：这是一张武器铭印卷轴。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-11 — ok


### stable

完整英文：
```text
That put a bit of spring back into your slither.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2402}

参数表达式与来源：
```text
you.species == SP_NAGA
            ? T_("That put a bit of spring back into your slither.")
            : T_("That put a bit of spring back into your step.")

```

当前中文模板：这让你的滑行恢复了几分轻快。

输入还原：这让你的滑行恢复了几分轻快。

完整英文：
```text
That put a bit of spring back into your step.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2402}

参数表达式与来源：
```text
you.species == SP_NAGA
            ? T_("That put a bit of spring back into your slither.")
            : T_("That put a bit of spring back into your step.")

```

当前中文模板：这让你的步伐恢复了几分轻快。

输入还原：这让你的步伐恢复了几分轻快。


### trunk

完整英文：
```text
That put a bit of spring back into your slither.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2486}

参数表达式与来源：
```text
you.species == SP_NAGA
            ? T_("That put a bit of spring back into your slither.")
            : T_("That put a bit of spring back into your step.")

```

当前中文模板：这让你的滑行恢复了几分轻快。

输入还原：这让你的滑行恢复了几分轻快。

完整英文：
```text
That put a bit of spring back into your step.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2486}

参数表达式与来源：
```text
you.species == SP_NAGA
            ? T_("That put a bit of spring back into your slither.")
            : T_("That put a bit of spring back into your step.")

```

当前中文模板：这让你的步伐恢复了几分轻快。

输入还原：这让你的步伐恢复了几分轻快。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-02 — ok


### stable

完整英文：
```text
Found %s
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5212}

参数表达式与来源：
```text
T_("Found %s")
marked.c_str()
5187:     };
5188:
5189:     vector<string> things;
5190:     for (const named_thing<int> &nt : v)
5191:     {
5192:         if (nt.thing == 1)
5193:             things.push_back(make_stringf_p(T_("a %1$s"), nt.name.c_str()));
5194:         else
5195:         {
5196:             things.push_back(number_in_words(nt.thing)
5197:                              + " "
5198:                              + pluralise(nt.name, feature_plural_qualifiers));
5199:         }
5200:     }
5201:     return things;
5202: }
5203:
5204: bool explore_discoveries::stop_explore() const
5205: {
5206:     const bool marker_stop = !marker_msgs.empty() || !marked_feats.empty();
5207:
5208:     for (const string &msg : marker_msgs)
5209:         mpr(msg);
5210:
5211:     for (const string &marked : marked_feats)
5212:         mprf(T_("Found %s"), marked.c_str());
5213:
5214:     if (!es_flags)
5215:         return marker_stop;
5216:
5217:     say_any(items, "item");
5218:     say_any(shops, "shop");
5219:     say_any(apply_quantities(altars), "altar");
5220:     say_any(apply_quantities(portals), "portal");
5221:     say_any(apply_quantities(stairs), "stair");
5222:     say_any(apply_quantities(transporters), "transporter");
5223:     say_any(apply_quantities(runed_doors), "runed door");
5224:     say_any(apply_quantities(runelights), "runelights");
5225:
5226:     return true;
5227: }
5228:
5229: void do_interlevel_travel()
5230: {
5231:     if (Hints.hints_travel)
5232:         Hints.hints_travel = 0;
5233:
5234:     if (!can_travel_interlevel())
5235:     {
5236:         if (you.running.pos == you.pos())
5237:         {
```

当前中文模板：发现了%s

输入还原：None


### trunk

完整英文：
```text
Found %s
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5295}

参数表达式与来源：
```text
T_("Found %s")
marked.c_str()
5270:     };
5271:
5272:     vector<string> things;
5273:     for (const named_thing<int> &nt : v)
5274:     {
5275:         if (nt.thing == 1)
5276:             things.push_back(make_stringf_p(T_("a %1$s"), nt.name.c_str()));
5277:         else
5278:         {
5279:             things.push_back(number_in_words(nt.thing)
5280:                              + " "
5281:                              + pluralise(nt.name, feature_plural_qualifiers));
5282:         }
5283:     }
5284:     return things;
5285: }
5286:
5287: bool explore_discoveries::stop_explore() const
5288: {
5289:     const bool marker_stop = !marker_msgs.empty() || !marked_feats.empty();
5290:
5291:     for (const string &msg : marker_msgs)
5292:         mpr(msg);
5293:
5294:     for (const string &marked : marked_feats)
5295:         mprf(T_("Found %s"), marked.c_str());
5296:
5297:     if (!es_flags)
5298:         return marker_stop;
5299:
5300:     say_any(items, "item");
5301:     say_any(shops, "shop");
5302:     say_any(apply_quantities(altars), "altar");
5303:     say_any(apply_quantities(portals), "portal");
5304:     if (Options.language == lang_t::ZH)
5305:     {
5306:         vector<string> stair_descs;
5307:         int stair_count = 0;
5308:         for (const auto &stair : stairs)
5309:         {
5310:             stair_count += stair.thing;
5311:             stair_descs.push_back(make_stringf(C_("stair quantity", "%d %s"),
5312:                                                stair.thing, stair.name.c_str()));
5313:         }
5314:         if (!stair_descs.empty())
5315:         {
5316:             const string message = make_stringf(T_("Found %s."),
5317:                 comma_separated_line(stair_descs.begin(), stair_descs.end(),
5318:                 Options.language == lang_t::ZH ? T_(",") : T_(" and "),
5319:                 Options.language == lang_t::ZH ? T_(",") : ", ").c_str());
5320:             if (formatted_string::parse_string(message).width() >= get_number_of_cols())
```

当前中文模板：发现了%s

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-08 — ok


### stable

完整英文：
```text
You don't know that spell.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 1045}

参数表达式与来源：
```text
T_("You don't know that spell.")

```

当前中文模板：你还没有掌握那个法术。

输入还原：你还没有掌握那个法术。


### trunk

完整英文：
```text
You don't know that spell.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 1075}

参数表达式与来源：
```text
T_("You don't know that spell.")

```

当前中文模板：你还没有掌握那个法术。

输入还原：你还没有掌握那个法术。

完整英文：
```text
You don't know that spell.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 1085}

参数表达式与来源：
```text
T_("You don't know that spell.")

```

当前中文模板：你还没有掌握那个法术。

输入还原：你还没有掌握那个法术。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-09 — readability


### stable

完整英文：
```text
You announce your regal presence to all who look upon you.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 569}

参数表达式与来源：
```text
MSGCH_WARN
T_("You announce your regal presence to all who look upon you.")

```

当前中文模板：你向所有仰望你的人宣告了你的王者存在。

输入还原：你向所有仰望你的人宣告了你的王者存在。


### trunk

完整英文：
```text
You announce your regal presence to all who look upon you.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 581}

参数表达式与来源：
```text
MSGCH_WARN
T_("You announce your regal presence to all who look upon you.")

```

当前中文模板：你向所有仰望你的人宣告了你的王者存在。

输入还原：你向所有仰望你的人宣告了你的王者存在。

独立判断与参数还原：王者存在不够自然，仰望也比普通看见稍强；属措辞建议，不改变机制。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "wording", "line": "both", "english": "You announce your regal presence to all who look upon you.", "current_full_zh": "你向所有仰望你的人宣告了你的王者存在。", "problem": "王者存在不够自然，仰望也比普通看见稍强；属措辞建议，不改变机制。", "suggested_zh": "你向所有注视你的人彰显了王者威仪。", "evidence": "stable {'path': 'crawl-ref/source/stairs.cc', 'line': 569}; trunk {'path': 'crawl-ref/source/stairs.cc', 'line': 581}", "defect_points": 0}


## D-03 — ok


### stable

完整英文：
```text
It was %s.
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 999}

参数表达式与来源：
```text
T_("It was %s.")
article_a(potion.name(DESC_QUALNAME)).c_str()
974:
975:
976:     mprf(T_("Your fungus emits %s spores!"),
977:          C_("fungus spores", _spore_msg.at(potion).c_str()));
978:
979:
980:     for (int i = 0; i < num_affected; ++i)
981:         mons_potion_effect(*targs[i], potion, you);
982: }
983:
984: /**
985:  * Quaff a potion, identifying it if appropriate & triggering its effects on
986:  * the player. Does not handle decrementing item quantities.
987:  *
988:  * @param potion    The potion (stack) being quaffed.
989:  * @param force     Whether to consume the potion even if it is known to be useless.
990:  * @return          true if the potion was used; false if the player aborted.
991:  */
992: bool quaff_potion(item_def &potion, bool force)
993: {
994:     const bool was_known = item_type_known(potion);
995:
996:     if (!was_known)
997:     {
998:         identify_item(potion);
999:         mprf(T_("It was %s."),
1000:              article_a(potion.name(DESC_QUALNAME)).c_str());
1001:     }
1002:
1003:     const potion_type ptyp = static_cast<potion_type>(potion.sub_type);
1004:     if (get_potion_effect(ptyp)->quaff(was_known && !force))
1005:     {
1006:         if (you.wearing(OBJ_JEWELLERY, AMU_CHEMISTRY, false, true)
1007:             && you.magic_points < you.max_magic_points)
1008:         {
1009:             mpr(T_("You extract magical energy from the potion."));
1010:             inc_mp(random_range(5, 9));
1011:         }
1012:
1013:         if (you.has_mutation(MUT_POTION_FUNGUS))
1014:             _handle_potion_fungus(ptyp);
1015:
1016:         return true;
1017:     }
1018:
1019:     return false;
1020: }
1021:
1022: /**
1023:  * Trigger an effect on the player corresponding to the given potion type.
1024:  *
1025:  * @param effect        The type of potion in question.
```

当前中文模板：那是%s。

输入还原：那是治疗药水。


### trunk

完整英文：
```text
It was %s.
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1126}

参数表达式与来源：
```text
T_("It was %s.")
article_a(potion.name(DESC_QUALNAME)).c_str()
1101:
1102:
1103:     mprf(T_("Your fungus emits %s spores!"),
1104:          C_("fungus spores", _spore_msg.at(potion).c_str()));
1105:
1106:
1107:     for (int i = 0; i < num_affected; ++i)
1108:         mons_potion_effect(*targs[i], potion, you);
1109: }
1110:
1111: /**
1112:  * Quaff a potion, identifying it if appropriate & triggering its effects on
1113:  * the player. Does not handle decrementing item quantities.
1114:  *
1115:  * @param potion    The potion (stack) being quaffed.
1116:  * @param force     Whether to consume the potion even if it is known to be useless.
1117:  * @return          true if the potion was used; false if the player aborted.
1118:  */
1119: bool quaff_potion(item_def &potion, bool force)
1120: {
1121:     const bool was_known = item_type_known(potion);
1122:
1123:     if (!was_known)
1124:     {
1125:         identify_item(potion);
1126:         mprf(T_("It was %s."),
1127:              article_a(potion.name(DESC_QUALNAME)).c_str());
1128:     }
1129:
1130:     const potion_type ptyp = static_cast<potion_type>(potion.sub_type);
1131:     if (get_potion_effect(ptyp)->quaff(was_known && !force))
1132:     {
1133:         if (you.wearing(OBJ_JEWELLERY, AMU_CHEMISTRY, false, true)
1134:             && you.magic_points < you.max_magic_points)
1135:         {
1136:             mpr(T_("You extract magical energy from the potion."));
1137:             inc_mp(random_range(5, 9));
1138:         }
1139:
1140:         if (you.form == transformation::mistmane)
1141:             mistmane_quaff_potion(ptyp);
1142:
1143:         if (you.has_mutation(MUT_POTION_FUNGUS))
1144:             _handle_potion_fungus(ptyp);
1145:
1146:         return true;
1147:     }
1148:
1149:     return false;
1150: }
1151:
1152: /**
```

当前中文模板：那是%s。

输入还原：那是治疗药水。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-10 — ok


### stable

完整英文：
```text
You feel an ill-omen....
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 4041}

参数表达式与来源：
```text
T_("You feel an ill-omen....")

```

当前中文模板：你感到不祥的预兆……

输入还原：你感到不祥的预兆……


### trunk

完整英文：
```text
You feel an ill-omen....
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 4120}

参数表达式与来源：
```text
T_("You feel an ill-omen....")

```

当前中文模板：你感到不祥的预兆……

输入还原：你感到不祥的预兆……

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-06 — ok


### stable

完整英文：
```text
You can't close doors while %s.
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 444}

参数表达式与来源：
```text
T_("You can't close doors while %s.")
held_status()
419:         {
420:             door_already_open = env.markers.property_at(doorpos, MAT_ANY,
421:                                                     "door_verb_already_open");
422:         }
423:
424:         if (!door_already_open.empty())
425:             mpr(door_already_open);
426:         else
427:             mpr(T_("It's already open!"));
428:         break;
429:     }
430:     case DNGN_SEALED_DOOR:
431:     case DNGN_SEALED_CLEAR_DOOR:
432:         mpr(T_("That door is sealed shut!")); // should use door noun?
433:         break;
434:     default:
435:         mpr(T_("There isn't anything that you can open there!"));
436:         break;
437:     }
438: }
439:
440: void close_door_action(coord_def move)
441: {
442:     if (you.attribute[ATTR_HELD])
443:     {
444:         mprf(T_("You can't close doors while %s."), held_status());
445:         return;
446:     }
447:
448:     if (you.confused())
449:     {
450:         canned_msg(MSG_TOO_CONFUSED);
451:         return;
452:     }
453:
454:     coord_def delta;
455:
456:     if (move.origin())
457:     {
458:         // If there's only one door to close, don't ask.
459:         int num = _check_adjacent(DNGN_OPEN_DOOR, move)
460:                   + _check_adjacent(DNGN_OPEN_CLEAR_DOOR, move);
461:         if (num == 0)
462:         {
463:             if (_check_adjacent(DNGN_BROKEN_DOOR, move)
464:                 || _check_adjacent(DNGN_BROKEN_CLEAR_DOOR, move))
465:             {
466:                 mpr(T_("It's broken and can't be closed."));
467:             }
468:             else
469:                 mpr(T_("There's nothing to close nearby."));
```

当前中文模板：你在%s时无法关门。

输入还原：你在被网困住时无法关门。


### trunk

完整英文：
```text
You can't close doors while %s.
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 452}

参数表达式与来源：
```text
T_("You can't close doors while %s.")
held_status()
427:         {
428:             door_already_open = env.markers.property_at(doorpos, MAT_ANY,
429:                                                     "door_verb_already_open");
430:         }
431:
432:         if (!door_already_open.empty())
433:             mpr(door_already_open);
434:         else
435:             mpr(T_("It's already open!"));
436:         break;
437:     }
438:     case DNGN_SEALED_DOOR:
439:     case DNGN_SEALED_CLEAR_DOOR:
440:         mpr(T_("That door is sealed shut!")); // should use door noun?
441:         break;
442:     default:
443:         mpr(T_("There isn't anything that you can open there!"));
444:         break;
445:     }
446: }
447:
448: void close_door_action(coord_def move)
449: {
450:     if (you.attribute[ATTR_HELD])
451:     {
452:         mprf(T_("You can't close doors while %s."), held_status());
453:         return;
454:     }
455:
456:     if (you.confused())
457:     {
458:         canned_msg(MSG_TOO_CONFUSED);
459:         return;
460:     }
461:
462:     coord_def delta;
463:
464:     if (move.origin())
465:     {
466:         // If there's only one door to close, don't ask.
467:         int num = _check_adjacent(DNGN_OPEN_DOOR, move)
468:                   + _check_adjacent(DNGN_OPEN_CLEAR_DOOR, move);
469:         if (num == 0)
470:         {
471:             if (_check_adjacent(DNGN_BROKEN_DOOR, move)
472:                 || _check_adjacent(DNGN_BROKEN_CLEAR_DOOR, move))
473:             {
474:                 mpr(T_("It's broken and can't be closed."));
475:             }
476:             else
477:                 mpr(T_("There's nothing to close nearby."));
```

当前中文模板：你在%s时无法关门。

输入还原：你在被网困住时无法关门。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-12 — ok


### stable

完整英文：
```text
Casting this spell will place you under penance. Really cast?
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 1089}

参数表达式与来源：
```text
T_("Casting this spell will place you under penance. "
                   "Really cast?")
true
'n'

```

当前中文模板：施放此法术会使你遭受苦修。确定要施放吗？

输入还原：施放此法术会使你遭受苦修。确定要施放吗？


### trunk

独立判断与参数还原：penance 是违背神规后的惩处，苦修表达略硬；当前 glossary 允许按神祇类型使用苦修；本次不因该旧术语本身增列机制错误。条件 god_punishes_spell 明确是在神规惩罚提示，建议措辞时需保持这一含义。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-11 — ok


### stable

完整英文：
```text
You have nothing you can fire or use right now.
```

生产调用：{'path': 'crawl-ref/source/throw.cc', 'line': 291}

参数表达式与来源：
```text
T_("You have nothing you can fire or use right now.")

```

当前中文模板：你现在没有可以发射或使用的东西。

输入还原：你现在没有可以发射或使用的东西。


### trunk

完整英文：
```text
You have nothing you can fire or use right now.
```

生产调用：{'path': 'crawl-ref/source/throw.cc', 'line': 309}

参数表达式与来源：
```text
T_("You have nothing you can fire or use right now.")

```

当前中文模板：你现在没有可以发射或使用的东西。

输入还原：你现在没有可以发射或使用的东西。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-09 — ok


### stable

完整英文：
```text
* * * LOW HITPOINT WARNING * * *
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4078}

参数表达式与来源：
```text
MSGCH_DANGER
T_("* * * LOW HITPOINT WARNING * * *")

```

当前中文模板：* * * 低生命警告 * * *

输入还原：* * * 低生命警告 * * *


### trunk

完整英文：
```text
* * * LOW HITPOINT WARNING * * *
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4289}

参数表达式与来源：
```text
MSGCH_DANGER
T_("* * * LOW HITPOINT WARNING * * *")

```

当前中文模板：* * * 低生命警告 * * *

输入还原：* * * 低生命警告 * * *

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-03 — ok


### stable

完整英文：
```text
You %s towards %s!
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 1026}

参数表达式与来源：
```text
T_("You %s towards %s!")
translated_move_phrase(move_verb.c_str(),
                                    move_phrase_context::toward_target)
mon_target->name(DESC_THE, true).c_str()
1001:             coord_def dummy;
1002:             if (you.can_see(*mon_at)
1003:                 && !mon_at->wont_attack()
1004:                    || !(fedhas_passthrough(mon_at)
1005:                         || swap_check(mon_at, dummy, true)))
1006:             {
1007:                 break;
1008:             }
1009:         }
1010:
1011:         // Check for moving *over* all spaces but our destination.
1012:         // (ie: ignore clouds, since we don't expect to be staying here).
1013:         if (i == end_step)
1014:         {
1015:             if (!check_moveto(targ, move_verb))
1016:                 return;
1017:         }
1018:         // At the destination, also warn about clouds and similar.
1019:         else if (!check_move_over(targ, move_verb))
1020:             return;
1021:     }
1022:
1023:     // Print a message, if rampaging.
1024:     if (num_steps > 1)
1025:     {
1026:         mprf(T_("You %s towards %s!"),
1027:              translated_move_phrase(move_verb.c_str(),
1028:                                     move_phrase_context::toward_target),
1029:              mon_target->name(DESC_THE, true).c_str());
1030:
1031:         // Prevent full-LoS stabbing with Seven League Boots.
1032:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
1033:             behaviour_event(mon_target, ME_ALERT, &you, you.pos());
1034:     }
1035:
1036:     // Now, we can assume the player has been fully prompted for any movement,
1037:     // so take each step in order (tracking whether we actually moved or attack,
1038:     // and how much time it took to move through each space).
1039:     const coord_def initial_pos = you.pos();
1040:     targ = you.pos();
1041:     int delay = 0;
1042:     int steps_taken = 0;
1043:     bool did_move = false;
1044:     bool did_attack = false;
1045:     bool did_open_door = false;
1046:     for (; steps_taken < num_steps; ++steps_taken)
1047:     {
1048:         // If we have somehow ended up somewhere other than where we tried
1049:         // to move (likely due to a trap), abort any further steps.
1050:         if (you.pos() != targ || you.caught())
1051:             break;
1052:
1053:         targ += move;
1054:
```

当前中文模板：你%s%s！

输入还原：None


### trunk

完整英文：
```text
You %s towards %s%s!
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 1235}

参数表达式与来源：
```text
T_("You %s towards %s%s!")
translated_move_phrase(move_verb.c_str(),
                                       move_phrase_context::toward_target)
mon_target->name(DESC_THE, true).c_str()
did_tailwind ? T_(" with incredible speed") : ""
1210:                          || swap_check(mon_at, dummy, true))))
1211:             {
1212:                 break;
1213:             }
1214:         }
1215:
1216:         // Check for moving *over* all spaces but our destination.
1217:         // (ie: ignore clouds, since we don't expect to be staying here).
1218:         if (i == end_step)
1219:         {
1220:             if (!check_moveto(targ, move_verb))
1221:                 return;
1222:         }
1223:         // At the destination, also warn about clouds and similar.
1224:         else if (!check_move_over(targ, move_verb))
1225:             return;
1226:     }
1227:
1228:     const bool did_tailwind = num_steps > 1 && you.duration[DUR_TAILWIND];
1229:     if (did_tailwind)
1230:         you.duration[DUR_TAILWIND] = 0;
1231:
1232:     // Print a message, if rampaging.
1233:     if (num_steps > 1 && mon_target)
1234:     {
1235:         mprf_p(T_("You %s towards %s%s!"),
1236:                 translated_move_phrase(move_verb.c_str(),
1237:                                        move_phrase_context::toward_target),
1238:                 mon_target->name(DESC_THE, true).c_str(),
1239:                 did_tailwind ? T_(" with incredible speed") : "");
1240:
1241:         // Prevent full-LoS stabbing with Seven League Boots.
1242:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
1243:             behaviour_event(mon_target, ME_ALERT, &you, you.pos());
1244:     }
1245:
1246:     // Now, we can assume the player has been fully prompted for any movement,
1247:     // so take each step in order (tracking whether we actually moved or attack,
1248:     // and how much time it took to move through each space).
1249:     const coord_def initial_pos = you.pos();
1250:     targ = you.pos();
1251:     int delay = 0;
1252:     int delay_scale = 60;
1253:     int steps_taken = 0;
1254:     bool did_move = false;
1255:     bool did_attack = false;
1256:     bool did_open_door = false;
1257:     bool did_stampede = false;
1258:     for (; steps_taken < num_steps; ++steps_taken)
1259:     {
1260:         // If we have somehow ended up somewhere other than where we tried
1261:         // to move (likely due to a trap), abort any further steps.
1262:         if (you.pos() != targ || you.caught())
1263:             break;
1264:
```

当前中文模板：你%s%s%s！

输入还原：None

完整英文：
```text
 with incredible speed
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 1235}

参数表达式与来源：
```text
T_("You %s towards %s%s!")
translated_move_phrase(move_verb.c_str(),
                                       move_phrase_context::toward_target)
mon_target->name(DESC_THE, true).c_str()
did_tailwind ? T_(" with incredible speed") : ""

```

当前中文模板：，速度快得惊人

输入还原：None

独立判断与参数还原：toward_target 动作词组内含朝向，例你冲向兽人！；trunk tailwind 后缀可还原你冲向兽人，速度快得惊人！；无后缀分支标点仍完整。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-04 — ok


### stable

完整英文：
```text
You feel less strong-willed.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2415}

参数表达式与来源：
```text
T_("You feel less strong-willed.")

```

当前中文模板：你感到意志不再那么坚定。

输入还原：你感到意志不再那么坚定。

完整英文：
```text
You feel less protected.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2419}

参数表达式与来源：
```text
T_("You feel less protected.")

```

当前中文模板：你感到保护减弱了。

输入还原：你感到保护减弱了。

完整英文：
```text
You feel less stealthy.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2424}

参数表达式与来源：
```text
T_("You feel less stealthy.")

```

当前中文模板：你感到不再那么隐秘。

输入还原：你感到不再那么隐秘。

完整英文：
```text
You feel hot and cold all over.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2428}

参数表达式与来源：
```text
T_("You feel hot and cold all over.")

```

当前中文模板：你感到全身忽冷忽热。

输入还原：你感到全身忽冷忽热。

完整英文：
```text
You feel less protected from negative energy.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2432}

参数表达式与来源：
```text
T_("You feel less protected from negative energy.")

```

当前中文模板：你感到对负能量的抵抗力减弱了。

输入还原：你感到对负能量的抵抗力减弱了。

完整英文：
```text
You feel strangely numb.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2436}

参数表达式与来源：
```text
T_("You feel strangely numb.")

```

当前中文模板：你奇怪地感到麻木。

输入还原：你奇怪地感到麻木。

完整英文：
```text
You feel strangely alone.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2442}

参数表达式与来源：
```text
T_("You feel strangely alone.")

```

当前中文模板：你莫名感到孤独。

输入还原：你莫名感到孤独。

完整英文：
```text
Your magic begins regenerating once more.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2445}

参数表达式与来源：
```text
T_("Your magic begins regenerating once more.")

```

当前中文模板：你的法力重新开始恢复。

输入还原：你的法力重新开始恢复。

完整英文：
```text
Your aim is not that steady anymore.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2451}

参数表达式与来源：
```text
T_("Your aim is not that steady anymore.")

```

当前中文模板：你的瞄准不再那么稳定。

输入还原：你的瞄准不再那么稳定。

完整英文：
```text
The haze of the repulsion field disappears.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2455}

参数表达式与来源：
```text
T_("The haze of the repulsion field disappears.")

```

当前中文模板：排斥力场的薄雾消失了。

输入还原：排斥力场的薄雾消失了。

完整英文：
```text
The dungeon's light returns to normal.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2459}

参数表达式与来源：
```text
T_("The dungeon's light returns to normal.")

```

当前中文模板：地牢的光线恢复了正常。

输入还原：地牢的光线恢复了正常。

完整英文：
```text
You no longer feel able to launch a frenzied charge at your enemies.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2465}

参数表达式与来源：
```text
T_("You no longer feel able to launch a frenzied charge at your enemies.")

```

当前中文模板：你不再感觉能够向敌人狂暴冲锋了。

输入还原：你不再感觉能够向敌人狂暴冲锋了。

完整英文：
```text
You feel magic leave your %s.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2470}

参数表达式与来源：
```text
T_("You feel magic leave your %s.")
you.hand_name(true).c_str()
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2471:         break;
2472:
2473:     case SPARM_LIGHT:
2474:         invalidate_agrid(true);
2475:         break;
2476:
2477:     default:
2478:         break;
2479:     }
2480: }
2481:
2482: static void _remove_amulet_of_faith(item_def &item)
2483: {
2484: #ifndef DEBUG_DIAGNOSTICS
2485:     UNUSED(item);
2486: #endif
2487:     if (!faith_has_penalty())
2488:         return;
2489:     if (you_worship(GOD_RU))
2490:     {
2491:         // next sacrifice is going to be delaaaayed.
2492:         ASSERT(you.raw_piety < piety_breakpoint(5));
2493: #ifdef DEBUG_DIAGNOSTICS
2494:         const int cur_delay = you.props[RU_SACRIFICE_DELAY_KEY].get_int();
2495: #endif
```

当前中文模板：你感到法力离开了你的%s。

输入还原：None


### trunk

完整英文：
```text
You feel less strong-willed.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2499}

参数表达式与来源：
```text
T_("You feel less strong-willed.")

```

当前中文模板：你感到意志不再那么坚定。

输入还原：你感到意志不再那么坚定。

完整英文：
```text
You feel less protected.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2503}

参数表达式与来源：
```text
T_("You feel less protected.")

```

当前中文模板：你感到保护减弱了。

输入还原：你感到保护减弱了。

完整英文：
```text
You feel less stealthy.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2508}

参数表达式与来源：
```text
T_("You feel less stealthy.")

```

当前中文模板：你感到不再那么隐秘。

输入还原：你感到不再那么隐秘。

完整英文：
```text
You feel hot and cold all over.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2512}

参数表达式与来源：
```text
T_("You feel hot and cold all over.")

```

当前中文模板：你感到全身忽冷忽热。

输入还原：你感到全身忽冷忽热。

完整英文：
```text
You feel less protected from negative energy.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2516}

参数表达式与来源：
```text
T_("You feel less protected from negative energy.")

```

当前中文模板：你感到对负能量的抵抗力减弱了。

输入还原：你感到对负能量的抵抗力减弱了。

完整英文：
```text
You feel strangely numb.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2520}

参数表达式与来源：
```text
T_("You feel strangely numb.")

```

当前中文模板：你奇怪地感到麻木。

输入还原：你奇怪地感到麻木。

完整英文：
```text
You feel strangely alone.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2526}

参数表达式与来源：
```text
T_("You feel strangely alone.")

```

当前中文模板：你莫名感到孤独。

输入还原：你莫名感到孤独。

完整英文：
```text
Your magic begins regenerating once more.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2529}

参数表达式与来源：
```text
T_("Your magic begins regenerating once more.")

```

当前中文模板：你的法力重新开始恢复。

输入还原：你的法力重新开始恢复。

完整英文：
```text
Your aim is not that steady anymore.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2535}

参数表达式与来源：
```text
T_("Your aim is not that steady anymore.")

```

当前中文模板：你的瞄准不再那么稳定。

输入还原：你的瞄准不再那么稳定。

完整英文：
```text
The haze of the repulsion field disappears.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2539}

参数表达式与来源：
```text
T_("The haze of the repulsion field disappears.")

```

当前中文模板：排斥力场的薄雾消失了。

输入还原：排斥力场的薄雾消失了。

完整英文：
```text
The dungeon's light returns to normal.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2543}

参数表达式与来源：
```text
T_("The dungeon's light returns to normal.")

```

当前中文模板：地牢的光线恢复了正常。

输入还原：地牢的光线恢复了正常。

完整英文：
```text
You no longer feel able to launch a frenzied charge at your enemies.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2549}

参数表达式与来源：
```text
T_("You no longer feel able to launch a frenzied charge at your enemies.")

```

当前中文模板：你不再感觉能够向敌人狂暴冲锋了。

输入还原：你不再感觉能够向敌人狂暴冲锋了。

完整英文：
```text
You feel magic leave your %s.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 2554}

参数表达式与来源：
```text
T_("You feel magic leave your %s.")
you.hand_name(true).c_str()
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2555:         break;
2556:
2557:     default:
2558:         break;
2559:     }
2560: }
2561:
2562: static void _remove_amulet_of_faith(item_def &item)
2563: {
2564: #ifndef DEBUG_DIAGNOSTICS
2565:     UNUSED(item);
2566: #endif
2567:     if (!faith_has_penalty())
2568:         return;
2569:     if (you_worship(GOD_RU))
2570:     {
2571:         // next sacrifice is going to be delaaaayed.
2572:         ASSERT(you.raw_piety < piety_breakpoint(5));
2573: #ifdef DEBUG_DIAGNOSTICS
2574:         const int cur_delay = you.props[RU_SACRIFICE_DELAY_KEY].get_int();
2575: #endif
2576:         ru_reject_sacrifices(true);
2577:         dprf("prev delay %d, new delay %d", cur_delay,
2578:              you.props[RU_SACRIFICE_DELAY_KEY].get_int());
2579:         return;
```

当前中文模板：你感到法力离开了你的%s。

输入还原：None

独立判断与参数还原：各抗性、保护、潜行及充能消退分支逐条核对；你的双手中法力消退的意象虽直译，但原文也使用 magic leave，并未明确声称直接扣 MP，不机械改判。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-09 — ok


### stable

完整英文：
```text
Your doom draws closer.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4684}

参数表达式与来源：
```text
T_("Your doom draws closer.")

```

当前中文模板：你的厄运越来越近了。

输入还原：你的厄运越来越近了。


### trunk

完整英文：
```text
Your doom draws closer.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4878}

参数表达式与来源：
```text
T_("Your doom draws closer.")

```

当前中文模板：你的厄运越来越近了。

输入还原：你的厄运越来越近了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-09 — ok


### stable

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1447}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。

完整英文：
```text
Are you sure you want to pick up this pile of gold now?
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1451}

参数表达式与来源：
```text
T_("Are you sure you want to pick up this pile of gold now?")
true
'n'

```

当前中文模板：你确定现在要拾取这堆金币吗？

输入还原：你确定现在要拾取这堆金币吗？


### trunk

完整英文：
```text
You can't pick that up.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1413}

参数表达式与来源：
```text
T_("You can't pick that up.")

```

当前中文模板：你无法捡起那个。

输入还原：你无法捡起那个。

完整英文：
```text
Are you sure you want to pick up this pile of gold now?
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1417}

参数表达式与来源：
```text
T_("Are you sure you want to pick up this pile of gold now?")
true
'n'

```

当前中文模板：你确定现在要拾取这堆金币吗？

输入还原：你确定现在要拾取这堆金币吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-12 — ok


### stable

完整英文：
```text
The last of your unstable energy dissipates and you return to your previous form.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 748}

参数表达式与来源：
```text
MSGCH_DURATION
T_("The last of your unstable energy dissipates and you return to your previous form.")

```

当前中文模板：你最后一点不稳定能量消散了，你恢复了之前的形态。

输入还原：你最后一点不稳定能量消散了，你恢复了之前的形态。

完整英文：
```text
You feel the transmutational energy in your body is nearly expended.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 752}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You feel the transmutational energy in your body is nearly expended.")

```

当前中文模板：你感到体内的变形能量几乎耗尽了。

输入还原：你感到体内的变形能量几乎耗尽了。


### trunk

完整英文：
```text
The last of your unstable energy dissipates and you return to your previous form.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 749}

参数表达式与来源：
```text
MSGCH_DURATION
T_("The last of your unstable energy dissipates and you return to your previous form.")

```

当前中文模板：你最后一点不稳定能量消散了，你恢复了之前的形态。

输入还原：你最后一点不稳定能量消散了，你恢复了之前的形态。

完整英文：
```text
You feel the transmutational energy in your body is nearly expended.
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 753}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You feel the transmutational energy in your body is nearly expended.")

```

当前中文模板：你感到体内的变形能量几乎耗尽了。

输入还原：你感到体内的变形能量几乎耗尽了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-12 — ok


### stable

完整英文：
```text
It is a scroll of enchant weapon.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3167}

参数表达式与来源：
```text
T_("It is a scroll of enchant weapon.")

```

当前中文模板：这是一张附魔武器卷轴。

输入还原：这是一张附魔武器卷轴。


### trunk

完整英文：
```text
It is a scroll of enchant weapon.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3301}

参数表达式与来源：
```text
T_("It is a scroll of enchant weapon.")

```

当前中文模板：这是一张附魔武器卷轴。

输入还原：这是一张附魔武器卷轴。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-01 — ok


### stable

完整英文：
```text
Your base attributes are Str %d, Int %d, Dex %d.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 3767}

参数表达式与来源：
```text
T_("Your base attributes are Str %d, Int %d, Dex %d.")
innate_stat(STAT_STR)
innate_stat(STAT_INT)
innate_stat(STAT_DEX)
3742:         mpr(T_("An external divine aura illuminates you."));
3743:
3744:     status_info inf;
3745:     for (unsigned i = 0; i <= STATUS_LAST_STATUS; ++i)
3746:     {
3747:         if (fill_status_info(i, inf) && !inf.long_text.empty())
3748:             mpr(inf.long_text);
3749:     }
3750:     string cinfo = _constriction_description();
3751:     if (!cinfo.empty())
3752:         mpr(cinfo);
3753:
3754:     const item_def* offhand = you.offhand_weapon();
3755:     _display_movement_speed();
3756:     _display_tohit();
3757:     _display_attack_delay(offhand);
3758:     _display_damage_rating(you.weapon());
3759:     if (offhand)
3760:         _display_damage_rating(offhand);
3761:
3762:     // Display base attributes, if necessary.
3763:     if (innate_stat(STAT_STR) != you.strength()
3764:         || innate_stat(STAT_INT) != you.intel()
3765:         || innate_stat(STAT_DEX) != you.dex())
3766:     {
3767:         mprf(T_("Your base attributes are Str %d, Int %d, Dex %d."),
3768:              innate_stat(STAT_STR),
3769:              innate_stat(STAT_INT),
3770:              innate_stat(STAT_DEX));
3771:     }
3772: }
3773:
3774: bool player::clarity(bool items) const
3775: {
3776:     if (you.get_mutation_level(MUT_CLARITY))
3777:         return true;
3778:
3779:     if (have_passive(passive_t::clarity))
3780:         return true;
3781:
3782:     return actor::clarity(items);
3783: }
3784:
3785: bool player::faith(bool items) const
3786: {
3787:     return you.has_mutation(MUT_FAITH) || actor::faith(items);
3788: }
3789:
3790: bool player::reflection(bool items) const
3791: {
3792:     if (you.duration[DUR_DIVINE_SHIELD])
3793:         return true;
3794:
3795:     return actor::reflection(items);
```

当前中文模板：你的基础属性是力量%d，智力%d，敏捷%d。

输入还原：你的基础属性是力量10，智力10，敏捷10。


### trunk

完整英文：
```text
Your base attributes are Str %d, Int %d, Dex %d.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 3975}

参数表达式与来源：
```text
T_("Your base attributes are Str %d, Int %d, Dex %d.")
innate_stat(STAT_STR)
innate_stat(STAT_INT)
innate_stat(STAT_DEX)
3950:         mpr(T_("An external divine aura illuminates you."));
3951:
3952:     status_info inf;
3953:     for (unsigned i = 0; i <= STATUS_LAST_STATUS; ++i)
3954:     {
3955:         if (fill_status_info(i, inf) && !inf.long_text.empty())
3956:             mpr(inf.long_text);
3957:     }
3958:     string cinfo = _constriction_description();
3959:     if (!cinfo.empty())
3960:         mpr(cinfo);
3961:
3962:     const item_def* offhand = you.offhand_weapon();
3963:     _display_movement_speed();
3964:     _display_tohit();
3965:     _display_attack_delay(offhand);
3966:     _display_damage_rating(you.weapon());
3967:     if (offhand)
3968:         _display_damage_rating(offhand);
3969:
3970:     // Display base attributes, if necessary.
3971:     if (innate_stat(STAT_STR) != you.strength()
3972:         || innate_stat(STAT_INT) != you.intel()
3973:         || innate_stat(STAT_DEX) != you.dex())
3974:     {
3975:         mprf(T_("Your base attributes are Str %d, Int %d, Dex %d."),
3976:              innate_stat(STAT_STR),
3977:              innate_stat(STAT_INT),
3978:              innate_stat(STAT_DEX));
3979:     }
3980: }
3981:
3982: bool player::clarity(bool items) const
3983: {
3984:     if (you.get_mutation_level(MUT_CLARITY))
3985:         return true;
3986:
3987:     if (have_passive(passive_t::clarity))
3988:         return true;
3989:
3990:     return actor::clarity(items);
3991: }
3992:
3993: bool player::faith(bool items) const
3994: {
3995:     return you.has_mutation(MUT_FAITH) || actor::faith(items);
3996: }
3997:
3998: /// Does the player have permastasis?
3999: bool player::stasis() const
4000: {
4001:     return species == SP_FORMICID;
4002: }
4003:
```

当前中文模板：你的基础属性是力量%d，智力%d，敏捷%d。

输入还原：你的基础属性是力量10，智力10，敏捷10。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-02 — ok


### stable

完整英文：
```text
Your %1$s meld%2$s into your body.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1200}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"
1175:                     entry.melded = true;
1176:                     if (entry.is_overflow)
1177:                     {
1178:                         for (player_equip_entry& overflow : items)
1179:                         {
1180:                             if (overflow.item == entry.item)
1181:                                 overflow.melded = true;
1182:                         }
1183:                     }
1184:                 }
1185:             }
1186:         }
1187:     }
1188:
1189:     if (to_meld.empty())
1190:         return;
1191:
1192:     if (skip_effects)
1193:         return;
1194:
1195:     // Print a message.
1196:     vector<string> meld_msg;
1197:     for (item_def* meld_item : to_meld)
1198:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1199:
1200:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1201:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1202:                 T_(" and "), T_(", ")).c_str(),
1203:             meld_msg.size() > 1 ? "" : "s");
1204:
1205:     update();
1206:
1207:     // Now, simultaneously do unequip effects for all melded items.
1208:     for (item_def* meld_item : to_meld)
1209:         unequip_effect(meld_item->link, true, true);
1210: }
1211:
1212: /**
1213:  * Unmelds equipment in a single slot and does associated bookeeping.
1214:  *
1215:  * @param slot           The slot type to unmeld.
1216:  * @param skip_effects   If true, no message will be printed about doing any of
1217:  *                       this, and no equip effects will be processed.
1218:  */
1219: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1220: {
1221:     vector<item_def*> was_unmelded;
1222:     for (player_equip_entry& entry : items)
1223:     {
1224:         if (entry.slot == slot)
1225:         {
1226:             if (entry.melded)
1227:             {
1228:                 if (entry.is_overflow)
```

当前中文模板：你的%1$s融入了你的身体。

输入还原：None

完整英文：
```text
 and
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1200}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板： 以及

输入还原：None

完整英文：
```text
,
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1200}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板：、

输入还原：None

完整英文：
```text
s
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1200}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板：

输入还原：None


### trunk

完整英文：
```text
Your %1$s meld%2$s into your body.
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1216}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"
1191:                     entry.melded = true;
1192:                     if (entry.is_overflow)
1193:                     {
1194:                         for (player_equip_entry& overflow : items)
1195:                         {
1196:                             if (overflow.item == entry.item)
1197:                                 overflow.melded = true;
1198:                         }
1199:                     }
1200:                 }
1201:             }
1202:         }
1203:     }
1204:
1205:     if (to_meld.empty())
1206:         return;
1207:
1208:     if (skip_effects)
1209:         return;
1210:
1211:     // Print a message.
1212:     vector<string> meld_msg;
1213:     for (item_def* meld_item : to_meld)
1214:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1215:
1216:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1217:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1218:                 T_(" and "), T_(", ")).c_str(),
1219:             meld_msg.size() > 1 ? "" : "s");
1220:
1221:     update();
1222:
1223:     // Now, simultaneously do unequip effects for all melded items.
1224:     for (item_def* meld_item : to_meld)
1225:         unequip_effect(meld_item->link, true, true, false, true);
1226: }
1227:
1228: /**
1229:  * Unmelds equipment in a single slot and does associated bookeeping.
1230:  *
1231:  * @param slot           The slot type to unmeld.
1232:  * @param skip_effects   If true, no message will be printed about doing any of
1233:  *                       this, and no equip effects will be processed.
1234:  */
1235: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1236: {
1237:     vector<item_def*> was_unmelded;
1238:     for (player_equip_entry& entry : items)
1239:     {
1240:         if (entry.slot == slot)
1241:         {
1242:             if (entry.melded)
1243:             {
1244:                 if (entry.is_overflow)
```

当前中文模板：你的%1$s融入了你的身体。

输入还原：None

完整英文：
```text
 and
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1216}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板： 以及

输入还原：None

完整英文：
```text
,
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1216}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板：、

输入还原：None

完整英文：
```text
s
```

生产调用：{'path': 'crawl-ref/source/player-equip.cc', 'line': 1216}

参数表达式与来源：
```text
T_("Your %1$s meld%2$s into your body.")
comma_separated_line(meld_msg.begin(), meld_msg.end(),
                T_(" and "), T_(", ")).c_str()
meld_msg.size() > 1 ? "" : "s"

```

当前中文模板：

输入还原：None

独立判断与参数还原：meld_msg 使用 DESC_PLAIN，例你的匕首融入了你的身体。；多项由中文以及/顿号连接，英文单复数后缀不输出，语义完整。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-11 — ok


### stable

完整英文：
```text
It is a scroll of amnesia.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3246}

参数表达式与来源：
```text
T_("It is a scroll of amnesia.")

```

当前中文模板：这是一张遗忘卷轴。

输入还原：这是一张遗忘卷轴。

完整英文：
```text
You feel briefly forgetful.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3251}

参数表达式与来源：
```text
T_("You feel briefly forgetful.")

```

当前中文模板：你短暂地感到健忘。

输入还原：你短暂地感到健忘。


### trunk

完整英文：
```text
It is a scroll of amnesia.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3380}

参数表达式与来源：
```text
T_("It is a scroll of amnesia.")

```

当前中文模板：这是一张遗忘卷轴。

输入还原：这是一张遗忘卷轴。

完整英文：
```text
You feel briefly forgetful.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3385}

参数表达式与来源：
```text
T_("You feel briefly forgetful.")

```

当前中文模板：你短暂地感到健忘。

输入还原：你短暂地感到健忘。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-08 — ok


### stable

完整英文：
```text
No item to drop.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 2985}

参数表达式与来源：
```text
T_("No item to drop.")

```

当前中文模板：没有物品可丢。

输入还原：没有物品可丢。


### trunk

完整英文：
```text
No item to drop.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 2932}

参数表达式与来源：
```text
T_("No item to drop.")

```

当前中文模板：没有物品可丢。

输入还原：没有物品可丢。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-01 — ok


### stable

完整英文：
```text
Without enough magic to sustain it, your %s dissipates.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 3520}

参数表达式与来源：
```text
T_("Without enough magic to sustain it, your %s dissipates.")
spell_title(spell)
3495:         return;
3496:
3497:     // Skip processing at the end of the turn this is cast (since that already
3498:     // happened *as* it was cast and shouldn't happen a second time.)
3499:     if (++you.attribute[ATTR_CHANNEL_DURATION] == 1)
3500:         return;
3501:
3502:     const spell_type spell = (spell_type)you.attribute[ATTR_CHANNELLED_SPELL];
3503:
3504:     // This value is -1 at the moment the spell is started. 0 is 'skipped' as
3505:     // the end of the turn it is started. 1+ represents subsequent turns.
3506:     const int turn = (you.attribute[ATTR_CHANNEL_DURATION] == 0 ? 1
3507:                         : you.attribute[ATTR_CHANNEL_DURATION]);
3508:
3509:     // Don't stop on non-wait for the first turn of a channelled spell, since
3510:     // that was the turn we cast it on.
3511:     if (turn > 1 && crawl_state.prev_cmd != CMD_WAIT || !can_cast_spells(true))
3512:     {
3513:         stop_channelling_spells();
3514:         return;
3515:     }
3516:
3517:     if ((spell == SPELL_FLAME_WAVE || spell == SPELL_SEARING_RAY)
3518:         && turn > 1 && !enough_mp(1, true))
3519:     {
3520:         mprf(T_("Without enough magic to sustain it, your %s dissipates."),
3521:              spell_title(spell));
3522:         stop_channelling_spells(true);
3523:         return;
3524:     }
3525:
3526:     switch (you.attribute[ATTR_CHANNELLED_SPELL])
3527:     {
3528:         case SPELL_MAXWELLS_COUPLING:
3529:             handle_maxwells_coupling();
3530:             return;
3531:
3532:         case SPELL_FLAME_WAVE:
3533:             handle_flame_wave(turn);
3534:             return;
3535:
3536:         case SPELL_SEARING_RAY:
3537:             handle_searing_ray(you, turn);
3538:             return;
3539:
3540:         case SPELL_CLOCKWORK_BEE:
3541:             handle_clockwork_bee_spell(turn);
3542:             return;
3543:
3544:         default:
3545:             mprf(MSGCH_WARN, T_("Attempting to channel buggy spell: %s"), spell_title(spell));
3546:     }
```

当前中文模板：没有足够的法力维持，你的%s消散了。

输入还原：没有足够的法力维持，你的灼热射线消散了。


### trunk

完整英文：
```text
Without enough magic to sustain it, your %s dissipates.
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 3938}

参数表达式与来源：
```text
T_("Without enough magic to sustain it, your %s dissipates.")
spell_title(spell)
3913:         return;
3914:
3915:     // Skip processing at the end of the turn this is cast (since that already
3916:     // happened *as* it was cast and shouldn't happen a second time.)
3917:     if (++you.attribute[ATTR_CHANNEL_DURATION] == 1)
3918:         return;
3919:
3920:     const spell_type spell = (spell_type)you.attribute[ATTR_CHANNELLED_SPELL];
3921:
3922:     // This value is -1 at the moment the spell is started. 0 is 'skipped' as
3923:     // the end of the turn it is started. 1+ represents subsequent turns.
3924:     const int turn = (you.attribute[ATTR_CHANNEL_DURATION] == 0 ? 1
3925:                         : you.attribute[ATTR_CHANNEL_DURATION]);
3926:
3927:     // Don't stop on non-wait for the first turn of a channelled spell, since
3928:     // that was the turn we cast it on.
3929:     if (turn > 1 && crawl_state.prev_cmd != CMD_WAIT || !can_cast_spells(true))
3930:     {
3931:         stop_channelling_spells();
3932:         return;
3933:     }
3934:
3935:     if ((spell == SPELL_FLAME_WAVE || spell == SPELL_SEARING_RAY)
3936:         && turn > 1 && !enough_mp(1, true))
3937:     {
3938:         mprf(T_("Without enough magic to sustain it, your %s dissipates."),
3939:              spell_title(spell));
3940:         stop_channelling_spells(true);
3941:         return;
3942:     }
3943:
3944:     if (you.duration[DUR_STAMPEDE] && you.has_mutation(MUT_EAST_WIND))
3945:         you.duration[DUR_STAMPEDE] += you.time_taken;
3946:
3947:     switch (you.attribute[ATTR_CHANNELLED_SPELL])
3948:     {
3949:         case SPELL_MAXWELLS_COUPLING:
3950:             handle_maxwells_coupling();
3951:             return;
3952:
3953:         case SPELL_FLAME_WAVE:
3954:             handle_flame_wave(turn);
3955:             return;
3956:
3957:         case SPELL_SEARING_RAY:
3958:             handle_searing_ray(you, turn);
3959:             return;
3960:
3961:         case SPELL_CLOCKWORK_BEE:
3962:             handle_clockwork_bee_spell(turn);
3963:             return;
3964:
```

当前中文模板：没有足够的法力维持，你的%s消散了。

输入还原：没有足够的法力维持，你的灼热射线消散了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-10 — ok


### stable

完整英文：
```text
You feel yourself speed up.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 5165}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You feel yourself speed up.")

```

当前中文模板：你感觉自己加速了。

输入还原：你感觉自己加速了。


### trunk

完整英文：
```text
You feel yourself speed up.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 5382}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You feel yourself speed up.")

```

当前中文模板：你感觉自己加速了。

输入还原：你感觉自己加速了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-11 — ok


### stable

完整英文：
```text
Your divine stamina protects you from poison!
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4664}

参数表达式与来源：
```text
T_("Your divine stamina protects you from poison!")

```

当前中文模板：你的神圣耐力保护了你免受毒素伤害！

输入还原：你的神圣耐力保护了你免受毒素伤害！


### trunk

完整英文：
```text
Your divine stamina protects you from poison!
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4884}

参数表达式与来源：
```text
T_("Your divine stamina protects you from poison!")

```

当前中文模板：你的神圣耐力保护了你免受毒素伤害！

输入还原：你的神圣耐力保护了你免受毒素伤害！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-09 — ok


### stable

完整英文：
```text
You extend your mandibles.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3064}

参数表达式与来源：
```text
T_("You extend your mandibles.")

```

当前中文模板：你伸出了大颚。

输入还原：你伸出了大颚。

完整英文：
```text
You retract your mandibles.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3069}

参数表达式与来源：
```text
T_("You retract your mandibles.")

```

当前中文模板：你收回了大颚。

输入还原：你收回了大颚。


### trunk

完整英文：
```text
You extend your mandibles.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3215}

参数表达式与来源：
```text
T_("You extend your mandibles.")

```

当前中文模板：你伸出了大颚。

输入还原：你伸出了大颚。

完整英文：
```text
You retract your mandibles.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 3220}

参数表达式与来源：
```text
T_("You retract your mandibles.")

```

当前中文模板：你收回了大颚。

输入还原：你收回了大颚。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## E-11 — ok


### stable

完整英文：
```text
Something interferes with your magic!
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 773}

参数表达式与来源：
```text
T_("Something interferes with your magic!")

```

当前中文模板：有什么东西干扰了你的魔力！

输入还原：有什么东西干扰了你的魔力！


### trunk

完整英文：
```text
Something interferes with your magic!
```

生产调用：{'path': 'crawl-ref/source/spl-cast.cc', 'line': 805}

参数表达式与来源：
```text
T_("Something interferes with your magic!")

```

当前中文模板：有什么东西干扰了你的魔力！

输入还原：有什么东西干扰了你的魔力！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-04 — ok


### stable

完整英文：
```text
Faint brimstone surges around %s!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4500}

参数表达式与来源：
```text
T_("Faint brimstone surges around %s!")
defender_name(true).c_str()
4475:
4476:         break;
4477:
4478:     case AF_SPIDER:
4479:     {
4480:         if (!one_chance_in(3))
4481:             break;
4482:
4483:         if (summon_spider(*attacker, defender->pos(), SPELL_NO_SPELL,
4484:                           attacker->get_hit_dice() * 12))
4485:         {
4486:             if (needs_message)
4487:                 mpr(T_("A spider bursts forth from the wound!"));
4488:         }
4489:         break;
4490:     }
4491:     case AF_HELL_HUNT:
4492:     {
4493:         if (one_chance_in(3))
4494:             break;
4495:
4496:         if (summon_hell_out_of_bat(*attacker, defender->pos()))
4497:         {
4498:             if (needs_message)
4499:             {
4500:                 mprf(T_("Faint brimstone surges around %s!"),
4501:                     defender_name(true).c_str());
4502:             }
4503:         }
4504:         break;
4505:     }
4506:
4507:     case AF_SWARM:
4508:         if (!defender->is_firewood())
4509:             summon_swarm_clone(*attacker->as_monster(), defender->pos());
4510:         break;
4511:
4512:     case AF_BLOODZERK:
4513:     {
4514:         if (!defender->has_blood() || !attacker->can_go_berserk())
4515:             break;
4516:
4517:         monster* mon = attacker->as_monster();
4518:         if (mon->has_ench(ENCH_MIGHT))
4519:         {
4520:             mon->del_ench(ENCH_MIGHT, true);
4521:             mon->add_ench(mon_enchant(ENCH_BERSERK, mon, random_range(100, 200)));
4522:             simple_monster_message(*mon, T_(" enters a blood-rage!"));
4523:         }
4524:         else
4525:         {
4526:             mon->add_ench(mon_enchant(ENCH_MIGHT, mon, random_range(100, 200)));
```

当前中文模板：淡淡的硫磺在%s周围涌动！

输入还原：淡淡的硫磺在兽人周围涌动！


### trunk

完整英文：
```text
Faint brimstone surges around %s!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4694}

参数表达式与来源：
```text
T_("Faint brimstone surges around %s!")
defender_name(true).c_str()
4669:
4670:         break;
4671:
4672:     case AF_SPIDER:
4673:     {
4674:         if (!one_chance_in(3))
4675:             break;
4676:
4677:         if (summon_spider(*attacker, defender->pos(), SPELL_NO_SPELL,
4678:                           attacker->get_hit_dice() * 12))
4679:         {
4680:             if (needs_message)
4681:                 mpr(T_("A spider bursts forth from the wound!"));
4682:         }
4683:         break;
4684:     }
4685:     case AF_HELL_HUNT:
4686:     {
4687:         if (one_chance_in(3))
4688:             break;
4689:
4690:         if (summon_hell_out_of_bat(*attacker, defender->pos()))
4691:         {
4692:             if (needs_message)
4693:             {
4694:                 mprf(T_("Faint brimstone surges around %s!"),
4695:                     defender_name(true).c_str());
4696:             }
4697:         }
4698:         break;
4699:     }
4700:
4701:     case AF_SWARM:
4702:         if (!defender->is_firewood())
4703:             summon_swarm_clone(*attacker->as_monster(), defender->pos());
4704:         break;
4705:
4706:     case AF_BLOODZERK:
4707:     {
4708:         if (!defender->has_blood() || !attacker->can_go_berserk())
4709:             break;
4710:
4711:         monster* mon = attacker->as_monster();
4712:         if (mon->has_ench(ENCH_MIGHT))
4713:         {
4714:             mon->del_ench(ENCH_MIGHT, true);
4715:             mon->add_ench(mon_enchant(ENCH_BERSERK, mon, random_range(100, 200)));
4716:             simple_monster_message(*mon, T_(" enters a blood-rage!"));
4717:         }
4718:         else
4719:         {
4720:             mon->add_ench(mon_enchant(ENCH_MIGHT, mon, random_range(100, 200)));
```

当前中文模板：淡淡的硫磺在%s周围涌动！

输入还原：淡淡的硫磺在兽人周围涌动！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-01 — ok


### stable

完整英文：
```text
You bump into %s.
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 701}

参数表达式与来源：
```text
T_("You bump into %s.")
feature_description_at(new_targ, false,
                                        DESC_THE).c_str()
676:
677:     if (cancel_confused_move(false))
678:         return false;
679:
680:     if (cancel_harmful_move())
681:         return false;
682:
683:     if (!one_chance_in(3))
684:     {
685:         move.x = random2(3) - 1;
686:         move.y = random2(3) - 1;
687:         if (move.origin())
688:         {
689:             mpr(T_("You're too confused to move!"));
690:             you.turn_is_over = true;
691:             crawl_state.cancel_cmd_repeat();
692:             return false;
693:         }
694:     }
695:
696:     const coord_def new_targ = you.pos() + move;
697:
698:     // Test if our new location is somewhere we cannot move, and abort early if so.
699:     if (!in_bounds(new_targ) || !you.can_pass_through(new_targ))
700:     {
701:         mprf(T_("You bump into %s."),
702:                     feature_description_at(new_targ, false,
703:                                         DESC_THE).c_str());
704:         you.turn_is_over = true;
705:         crawl_state.cancel_cmd_repeat();
706:         return false;
707:     }
708:     else if (is_feat_dangerous(env.grid(new_targ)))
709:     {
710:         mprf(T_("You nearly stumble into %s!"),
711:                 feature_description_at(new_targ, false, DESC_THE).c_str());
712:         you.turn_is_over = true;
713:         crawl_state.cancel_cmd_repeat();
714:         return false;
715:     }
716:
717:     // Otherwise, we're good to attempt stumbling this way.
718:     return true;
719: }
720:
721: static string _get_move_verb(bool is_rampage)
722: {
723:     if (is_rampage)
724:     {
725:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
726:             return "stride";
727:         else if (you.has_mutation(MUT_ROLLPAGE))
728:             return "roll";
```

当前中文模板：你撞到了%s。

输入还原：你撞到了关闭的门。

完整英文：
```text
You nearly stumble into %s!
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 710}

参数表达式与来源：
```text
T_("You nearly stumble into %s!")
feature_description_at(new_targ, false, DESC_THE).c_str()
685:         move.x = random2(3) - 1;
686:         move.y = random2(3) - 1;
687:         if (move.origin())
688:         {
689:             mpr(T_("You're too confused to move!"));
690:             you.turn_is_over = true;
691:             crawl_state.cancel_cmd_repeat();
692:             return false;
693:         }
694:     }
695:
696:     const coord_def new_targ = you.pos() + move;
697:
698:     // Test if our new location is somewhere we cannot move, and abort early if so.
699:     if (!in_bounds(new_targ) || !you.can_pass_through(new_targ))
700:     {
701:         mprf(T_("You bump into %s."),
702:                     feature_description_at(new_targ, false,
703:                                         DESC_THE).c_str());
704:         you.turn_is_over = true;
705:         crawl_state.cancel_cmd_repeat();
706:         return false;
707:     }
708:     else if (is_feat_dangerous(env.grid(new_targ)))
709:     {
710:         mprf(T_("You nearly stumble into %s!"),
711:                 feature_description_at(new_targ, false, DESC_THE).c_str());
712:         you.turn_is_over = true;
713:         crawl_state.cancel_cmd_repeat();
714:         return false;
715:     }
716:
717:     // Otherwise, we're good to attempt stumbling this way.
718:     return true;
719: }
720:
721: static string _get_move_verb(bool is_rampage)
722: {
723:     if (is_rampage)
724:     {
725:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
726:             return "stride";
727:         else if (you.has_mutation(MUT_ROLLPAGE))
728:             return "roll";
729:         else
730:             return "rampage";
731:     }
732:
733:     return you.airborne()                          ? "fly"
734:            : you.swimming()                        ? "swim"
735:            : you.form == transformation::serpent   ? "slither"
736:            : you.form != transformation::none      ? "walk" // XX
```

当前中文模板：你差点跌进%s！

输入还原：你差点跌进关闭的门！


### trunk

完整英文：
```text
You bump into %s.
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 704}

参数表达式与来源：
```text
T_("You bump into %s.")
feature_description_at(new_targ, false,
                                        DESC_THE).c_str()
679:         return false;
680:
681:     // Now check the squares we might reach for warnings.
682:     if (!check_confused_move(false))
683:         return false;
684:
685:     // Randomise the move destination.
686:     if (!one_chance_in(3))
687:     {
688:         move.x = random2(3) - 1;
689:         move.y = random2(3) - 1;
690:         if (move.origin())
691:         {
692:             mpr(T_("You're too confused to move!"));
693:             you.turn_is_over = true;
694:             crawl_state.cancel_cmd_repeat();
695:             return false;
696:         }
697:     }
698:
699:     const coord_def new_targ = you.pos() + move;
700:
701:     // Test if our new location is somewhere we cannot move, and abort early if so.
702:     if (!in_bounds(new_targ) || !you.can_pass_through(new_targ))
703:     {
704:         mprf(T_("You bump into %s."),
705:                     feature_description_at(new_targ, false,
706:                                         DESC_THE).c_str());
707:         you.turn_is_over = true;
708:         crawl_state.cancel_cmd_repeat();
709:         return false;
710:     }
711:     else if (is_feat_dangerous(env.grid(new_targ)))
712:     {
713:         mprf(T_("You nearly stumble into %s!"),
714:                 feature_description_at(new_targ, false, DESC_THE).c_str());
715:         you.turn_is_over = true;
716:         crawl_state.cancel_cmd_repeat();
717:         return false;
718:     }
719:
720:     // Otherwise, we're good to attempt stumbling this way.
721:     return true;
722: }
723:
724: static string _get_move_verb(bool is_rampage)
725: {
726:     if (is_rampage)
727:     {
728:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
729:             return "stride";
730:         else if (you.has_mutation(MUT_STAMPEDE))
731:             return "stampede";
```

当前中文模板：你撞到了%s。

输入还原：你撞到了关闭的门。

完整英文：
```text
You nearly stumble into %s!
```

生产调用：{'path': 'crawl-ref/source/movement.cc', 'line': 713}

参数表达式与来源：
```text
T_("You nearly stumble into %s!")
feature_description_at(new_targ, false, DESC_THE).c_str()
688:         move.x = random2(3) - 1;
689:         move.y = random2(3) - 1;
690:         if (move.origin())
691:         {
692:             mpr(T_("You're too confused to move!"));
693:             you.turn_is_over = true;
694:             crawl_state.cancel_cmd_repeat();
695:             return false;
696:         }
697:     }
698:
699:     const coord_def new_targ = you.pos() + move;
700:
701:     // Test if our new location is somewhere we cannot move, and abort early if so.
702:     if (!in_bounds(new_targ) || !you.can_pass_through(new_targ))
703:     {
704:         mprf(T_("You bump into %s."),
705:                     feature_description_at(new_targ, false,
706:                                         DESC_THE).c_str());
707:         you.turn_is_over = true;
708:         crawl_state.cancel_cmd_repeat();
709:         return false;
710:     }
711:     else if (is_feat_dangerous(env.grid(new_targ)))
712:     {
713:         mprf(T_("You nearly stumble into %s!"),
714:                 feature_description_at(new_targ, false, DESC_THE).c_str());
715:         you.turn_is_over = true;
716:         crawl_state.cancel_cmd_repeat();
717:         return false;
718:     }
719:
720:     // Otherwise, we're good to attempt stumbling this way.
721:     return true;
722: }
723:
724: static string _get_move_verb(bool is_rampage)
725: {
726:     if (is_rampage)
727:     {
728:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
729:             return "stride";
730:         else if (you.has_mutation(MUT_STAMPEDE))
731:             return "stampede";
732:         else
733:             return "rampage";
734:     }
735:
736:     return you.airborne()                          ? "fly"
737:            : you.swimming()                        ? "swim"
738:            : you.form == transformation::serpent   ? "slither"
739:            : you.form != transformation::none      ? "walk" // XX
```

当前中文模板：你差点跌进%s！

输入还原：你差点跌进关闭的门！

独立判断与参数还原：输入将 near stumble 危险地形分支还原为关闭的门不成立。该分支要求 is_feat_dangerous；合法还原你差点跌进深水！或岩浆！，碰撞分支才是你撞到了关闭的门。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-01 — ok


### stable

完整英文：
```text
%s is dispelled%s
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 6284}

参数表达式与来源：
```text
T_("%s is dispelled%s")
mon->name(DESC_THE).c_str()
attack_strength_punctuation(dam).c_str()
6259:             did_god_conduct(DID_DELIBERATE_MUTATING, level, god_cares());
6260:         }
6261:         return MON_AFFECTED;
6262:
6263:     case BEAM_MALMUTATE:
6264:     case BEAM_UNRAVELLED_MAGIC:
6265:         if (mon->malmutate(agent())) // exact source doesn't matter
6266:             obvious_effect = true;
6267:         if (BLAME_KILL(thrower))
6268:         {
6269:             const int level = 2 + random2(3);
6270:             did_god_conduct(DID_DELIBERATE_MUTATING, level, god_cares());
6271:         }
6272:         return MON_AFFECTED;
6273:
6274:     case BEAM_BANISH:
6275:         mon->banish(agent());
6276:         obvious_effect = true;
6277:         return MON_AFFECTED;
6278:
6279:     case BEAM_DISPEL_UNDEAD:
6280:     {
6281:         const int dam = damage.roll();
6282:         if (you.see_cell(mon->pos()))
6283:         {
6284:             mprf(T_("%s is dispelled%s"),
6285:                  mon->name(DESC_THE).c_str(),
6286:                  attack_strength_punctuation(dam).c_str());
6287:             obvious_effect = true;
6288:         }
6289:         mon->hurt(agent(), dam);
6290:         return MON_AFFECTED;
6291:     }
6292:
6293:     case BEAM_VAMPIRIC_DRAINING:
6294:     {
6295:         const int dam = resist_adjust_damage(mon, flavour, damage.roll());
6296:         if (dam && actor_is_susceptible_to_vampirism(*mon))
6297:         {
6298:             _vampiric_draining_effect(*mon, *agent(), dam);
6299:             obvious_effect = true;
6300:             return MON_AFFECTED;
6301:         }
6302:         else
6303:             return MON_UNAFFECTED;
6304:     }
6305:
6306:     case BEAM_PAIN:
6307:     {
6308:         const int dam = resist_adjust_damage(mon, flavour, damage.roll());
6309:         if (!dam)
6310:             return MON_UNAFFECTED;
6311:         if (you.see_cell(mon->pos()))
```

当前中文模板：%s被驱散了%s

输入还原：兽人被驱散了。


### trunk

完整英文：
```text
%s is dispelled%s
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 6322}

参数表达式与来源：
```text
T_("%s is dispelled%s")
mon->name(DESC_THE).c_str()
attack_strength_punctuation(dam).c_str()
6297:     case BEAM_BECKONING:
6298:         obvious_effect = beckon(*mon, *this);
6299:         return obvious_effect ? MON_AFFECTED : MON_OTHER; // ?
6300:
6301:     case BEAM_POLYMORPH:
6302:         if (mon->polymorph(PPT_WAND))
6303:             obvious_effect = true;
6304:         return MON_AFFECTED;
6305:
6306:     case BEAM_MALMUTATE:
6307:     case BEAM_UNRAVELLED_MAGIC:
6308:         if (mon->malmutate(agent())) // exact source doesn't matter
6309:             obvious_effect = true;
6310:         return MON_AFFECTED;
6311:
6312:     case BEAM_BANISH:
6313:         mon->banish(agent());
6314:         obvious_effect = true;
6315:         return MON_AFFECTED;
6316:
6317:     case BEAM_DISPEL_UNDEAD:
6318:     {
6319:         const int dam = damage.roll();
6320:         if (you.see_cell(mon->pos()))
6321:         {
6322:             mprf(T_("%s is dispelled%s"),
6323:                  mon->name(DESC_THE).c_str(),
6324:                  attack_strength_punctuation(dam).c_str());
6325:             obvious_effect = true;
6326:         }
6327:         mon->hurt(agent(), dam);
6328:         return MON_AFFECTED;
6329:     }
6330:
6331:     case BEAM_VAMPIRIC_DRAINING:
6332:     {
6333:         const int dam = resist_adjust_damage(mon, flavour, damage.roll());
6334:         if (dam > 0)
6335:         {
6336:             _vampiric_draining_effect(*mon, *agent(), dam);
6337:             obvious_effect = true;
6338:             return MON_AFFECTED;
6339:         }
6340:         else
6341:             return MON_UNAFFECTED;
6342:     }
6343:
6344:     case BEAM_PAIN:
6345:     {
6346:         const int dam = resist_adjust_damage(mon, flavour, damage.roll());
6347:         if (!dam)
6348:             return MON_UNAFFECTED;
6349:         if (you.see_cell(mon->pos()))
```

当前中文模板：%s被驱散了%s

输入还原：兽人被驱散了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-06 — ok


### stable

完整英文：
```text
 surges with doubled vitality!
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 6436}

参数表达式与来源：
```text
*mon
T_(" surges with doubled vitality!")
6411:         if (!mon->has_ench(ENCH_HASTE)
6412:             && mon->add_ench(ENCH_HASTE))
6413:         {
6414:             if (!mons_is_immotile(*mon)
6415:                 && simple_monster_message(*mon, T_(" seems to speed up.")))
6416:             {
6417:                 obvious_effect = true;
6418:             }
6419:         }
6420:         return MON_AFFECTED;
6421:
6422:     case BEAM_MIGHT:
6423:         if (!mon->has_ench(ENCH_MIGHT)
6424:             && mons_has_attacks(*mon)
6425:             && mon->add_ench(ENCH_MIGHT))
6426:         {
6427:             if (simple_monster_message(*mon, T_(" seems to grow stronger.")))
6428:                 obvious_effect = true;
6429:         }
6430:         return MON_AFFECTED;
6431:
6432:     case BEAM_DOUBLE_VIGOUR:
6433:         if (!mon->has_ench(ENCH_DOUBLED_VIGOUR)
6434:             && mon->add_ench(ENCH_DOUBLED_VIGOUR))
6435:         {
6436:             if (simple_monster_message(*mon, T_(" surges with doubled vitality!")))
6437:                 obvious_effect = true;
6438:         }
6439:         return MON_AFFECTED;
6440:
6441:     case BEAM_WEAKNESS:
6442:         mon->weaken(agent(), 8 + random2(4));
6443:         obvious_effect = true;
6444:         return MON_AFFECTED;
6445:
6446:     case BEAM_BERSERK:
6447:         if (!mon->berserk_or_frenzied())
6448:         {
6449:             // currently from potion, hence voluntary
6450:             mon->go_berserk(true);
6451:             // can't return this from go_berserk, unfortunately
6452:             obvious_effect = you.can_see(*mon);
6453:         }
6454:         return MON_AFFECTED;
6455:
6456:     case BEAM_HEALING:
6457:         // No KILL_YOU_CONF, or we get "You heal ..."
6458:         if (thrower == KILL_YOU || thrower == KILL_YOU_MISSILE)
6459:         {
6460:             const int pow = min(50, 3 + damage.roll());
6461:             const int amount = pow + roll_dice(2, pow) - 2;
```

当前中文模板：涌动着双倍活力！

输入还原：兽人涌动着双倍活力！


### trunk

完整英文：
```text
 surges with doubled vitality!
```

生产调用：{'path': 'crawl-ref/source/beam.cc', 'line': 6470}

参数表达式与来源：
```text
*mon
T_(" surges with doubled vitality!")
6445:         if (!mon->has_ench(ENCH_HASTE)
6446:             && mon->add_ench(ENCH_HASTE))
6447:         {
6448:             if (!mons_is_immotile(*mon)
6449:                 && simple_monster_message(*mon, T_(" seems to speed up.")))
6450:             {
6451:                 obvious_effect = true;
6452:             }
6453:         }
6454:         return MON_AFFECTED;
6455:
6456:     case BEAM_MIGHT:
6457:         if (!mon->has_ench(ENCH_MIGHT)
6458:             && mons_has_attacks(*mon)
6459:             && mon->add_ench(ENCH_MIGHT))
6460:         {
6461:             if (simple_monster_message(*mon, T_(" seems to grow stronger.")))
6462:                 obvious_effect = true;
6463:         }
6464:         return MON_AFFECTED;
6465:
6466:     case BEAM_DOUBLE_VIGOUR:
6467:         if (!mon->has_ench(ENCH_DOUBLED_VIGOUR)
6468:             && mon->add_ench(ENCH_DOUBLED_VIGOUR))
6469:         {
6470:             if (simple_monster_message(*mon, T_(" surges with doubled vitality!")))
6471:                 obvious_effect = true;
6472:         }
6473:         return MON_AFFECTED;
6474:
6475:     case BEAM_WEAKNESS:
6476:         mon->weaken(agent(), 8 + random2(4));
6477:         obvious_effect = true;
6478:         return MON_AFFECTED;
6479:
6480:     case BEAM_BERSERK:
6481:         if (!mon->berserk_or_frenzied())
6482:         {
6483:             // currently from potion, hence voluntary
6484:             mon->go_berserk(true);
6485:             // can't return this from go_berserk, unfortunately
6486:             obvious_effect = you.can_see(*mon);
6487:         }
6488:         return MON_AFFECTED;
6489:
6490:     case BEAM_HEALING:
6491:         if (mon->heal(HEALING_BEAM_BONUS + damage.roll()))
6492:         {
6493:             if (mon->hit_points == mon->max_hit_points)
6494:             {
6495:                 if (simple_monster_message(*mon, T_(" wounds heal themselves!"), true))
```

当前中文模板：涌动着双倍活力！

输入还原：兽人涌动着双倍活力！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-07 — ok


### stable

完整英文：
```text
The nature of this place prevents your teleportation.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 518}

参数表达式与来源：
```text
MSGCH_WARN
T_("The nature of this place prevents your teleportation.")

```

当前中文模板：这个地方的本质阻止了你的传送。

输入还原：这个地方的本质阻止了你的传送。

完整英文：
```text
You feel stable on this level.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 521}

参数表达式与来源：
```text
T_("You feel stable on this level.")

```

当前中文模板：你在这个楼层感到稳定。

输入还原：你在这个楼层感到稳定。


### trunk

完整英文：
```text
The nature of this place prevents your teleportation.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 530}

参数表达式与来源：
```text
MSGCH_WARN
T_("The nature of this place prevents your teleportation.")

```

当前中文模板：这个地方的本质阻止了你的传送。

输入还原：这个地方的本质阻止了你的传送。

完整英文：
```text
You feel stable on this level.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 533}

参数表达式与来源：
```text
T_("You feel stable on this level.")

```

当前中文模板：你在这个楼层感到稳定。

输入还原：你在这个楼层感到稳定。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-02 — ok


### stable

完整英文：
```text
 magic is enhanced!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1103}

参数表达式与来源：
```text
mon
T_(" magic is enhanced!")
true
1078:
1079:         case POT_BERSERK_RAGE:
1080:             return !mon.has_ench(ENCH_BERSERK) && mon.can_go_berserk();
1081:
1082:         case POT_RESISTANCE:
1083:             return !mon.has_ench(ENCH_RESISTANCE);
1084:
1085:         default:
1086:             return false;
1087:     }
1088: }
1089:
1090: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1091: {
1092:     switch (potion)
1093:     {
1094:         case POT_HASTE:
1095:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1096:             break;
1097:
1098:         case POT_MIGHT:
1099:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1100:             break;
1101:
1102:         case POT_BRILLIANCE:
1103:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1104:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1105:             break;
1106:
1107:         case POT_HEAL_WOUNDS:
1108:             simple_monster_message(mon, T_(" is healed!"));
1109:             mon.heal(random_range(30, 50));
1110:             break;
1111:
1112:         case POT_CURING:
1113:             simple_monster_message(mon, T_(" is healed!"));
1114:             mon.heal(random_range(10, 20));
1115:             mon.del_ench(ENCH_POISON);
1116:             mon.del_ench(ENCH_CONFUSION);
1117:             break;
1118:
1119:         case POT_ENLIGHTENMENT:
1120:         {
1121:             simple_monster_message(mon, T_(" is enlightened!"));
1122:             const int dur = random_range(300, 450);
1123:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1124:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1125:         }
1126:             break;
1127:
1128:         case POT_INVISIBILITY:
```

当前中文模板：魔力增强了！

输入还原：兽人的魔力增强了！

完整英文：
```text
 is healed!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1108}

参数表达式与来源：
```text
mon
T_(" is healed!")
1083:             return !mon.has_ench(ENCH_RESISTANCE);
1084:
1085:         default:
1086:             return false;
1087:     }
1088: }
1089:
1090: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1091: {
1092:     switch (potion)
1093:     {
1094:         case POT_HASTE:
1095:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1096:             break;
1097:
1098:         case POT_MIGHT:
1099:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1100:             break;
1101:
1102:         case POT_BRILLIANCE:
1103:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1104:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1105:             break;
1106:
1107:         case POT_HEAL_WOUNDS:
1108:             simple_monster_message(mon, T_(" is healed!"));
1109:             mon.heal(random_range(30, 50));
1110:             break;
1111:
1112:         case POT_CURING:
1113:             simple_monster_message(mon, T_(" is healed!"));
1114:             mon.heal(random_range(10, 20));
1115:             mon.del_ench(ENCH_POISON);
1116:             mon.del_ench(ENCH_CONFUSION);
1117:             break;
1118:
1119:         case POT_ENLIGHTENMENT:
1120:         {
1121:             simple_monster_message(mon, T_(" is enlightened!"));
1122:             const int dur = random_range(300, 450);
1123:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1124:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1125:         }
1126:             break;
1127:
1128:         case POT_INVISIBILITY:
1129:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1130:             break;
1131:
1132:         case POT_MAGIC:
1133:             mon.del_ench(ENCH_ANTIMAGIC);
```

当前中文模板：被治愈了！

输入还原：兽人被治愈了！

完整英文：
```text
 is healed!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1113}

参数表达式与来源：
```text
mon
T_(" is healed!")
1088: }
1089:
1090: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1091: {
1092:     switch (potion)
1093:     {
1094:         case POT_HASTE:
1095:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1096:             break;
1097:
1098:         case POT_MIGHT:
1099:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1100:             break;
1101:
1102:         case POT_BRILLIANCE:
1103:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1104:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1105:             break;
1106:
1107:         case POT_HEAL_WOUNDS:
1108:             simple_monster_message(mon, T_(" is healed!"));
1109:             mon.heal(random_range(30, 50));
1110:             break;
1111:
1112:         case POT_CURING:
1113:             simple_monster_message(mon, T_(" is healed!"));
1114:             mon.heal(random_range(10, 20));
1115:             mon.del_ench(ENCH_POISON);
1116:             mon.del_ench(ENCH_CONFUSION);
1117:             break;
1118:
1119:         case POT_ENLIGHTENMENT:
1120:         {
1121:             simple_monster_message(mon, T_(" is enlightened!"));
1122:             const int dur = random_range(300, 450);
1123:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1124:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1125:         }
1126:             break;
1127:
1128:         case POT_INVISIBILITY:
1129:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1130:             break;
1131:
1132:         case POT_MAGIC:
1133:             mon.del_ench(ENCH_ANTIMAGIC);
1134:             break;
1135:
1136:         case POT_BERSERK_RAGE:
1137:             mon.go_berserk(false);
1138:             break;
```

当前中文模板：被治愈了！

输入还原：兽人被治愈了！

完整英文：
```text
 is enlightened!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1121}

参数表达式与来源：
```text
mon
T_(" is enlightened!")
1096:             break;
1097:
1098:         case POT_MIGHT:
1099:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1100:             break;
1101:
1102:         case POT_BRILLIANCE:
1103:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1104:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1105:             break;
1106:
1107:         case POT_HEAL_WOUNDS:
1108:             simple_monster_message(mon, T_(" is healed!"));
1109:             mon.heal(random_range(30, 50));
1110:             break;
1111:
1112:         case POT_CURING:
1113:             simple_monster_message(mon, T_(" is healed!"));
1114:             mon.heal(random_range(10, 20));
1115:             mon.del_ench(ENCH_POISON);
1116:             mon.del_ench(ENCH_CONFUSION);
1117:             break;
1118:
1119:         case POT_ENLIGHTENMENT:
1120:         {
1121:             simple_monster_message(mon, T_(" is enlightened!"));
1122:             const int dur = random_range(300, 450);
1123:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1124:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1125:         }
1126:             break;
1127:
1128:         case POT_INVISIBILITY:
1129:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1130:             break;
1131:
1132:         case POT_MAGIC:
1133:             mon.del_ench(ENCH_ANTIMAGIC);
1134:             break;
1135:
1136:         case POT_BERSERK_RAGE:
1137:             mon.go_berserk(false);
1138:             break;
1139:
1140:         case POT_RESISTANCE:
1141:             enchant_actor_with_flavour(&mon, &source, BEAM_RESISTANCE);
1142:             break;
1143:
1144:         default:
1145:             break;
1146:     }
```

当前中文模板：被启迪了！

输入还原：兽人被启迪了！


### trunk

完整英文：
```text
 magic is enhanced!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1236}

参数表达式与来源：
```text
mon
T_(" magic is enhanced!")
true
1211:
1212:         case POT_RESISTANCE:
1213:             return !mon.has_ench(ENCH_RESISTANCE);
1214:
1215:         case POT_MIST:
1216:             return !mon.is_insubstantial();
1217:
1218:         default:
1219:             return false;
1220:     }
1221: }
1222:
1223: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1224: {
1225:     switch (potion)
1226:     {
1227:         case POT_HASTE:
1228:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1229:             break;
1230:
1231:         case POT_MIGHT:
1232:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1233:             break;
1234:
1235:         case POT_BRILLIANCE:
1236:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1237:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1238:             break;
1239:
1240:         case POT_HEAL_WOUNDS:
1241:             simple_monster_message(mon, T_(" is healed!"));
1242:             mon.heal(random_range(30, 50));
1243:             break;
1244:
1245:         case POT_CURING:
1246:             simple_monster_message(mon, T_(" is healed!"));
1247:             mon.heal(random_range(10, 20));
1248:             mon.del_ench(ENCH_POISON);
1249:             mon.del_ench(ENCH_CONFUSION);
1250:             break;
1251:
1252:         case POT_ENLIGHTENMENT:
1253:         {
1254:             simple_monster_message(mon, T_(" is enlightened!"));
1255:             const int dur = random_range(300, 450);
1256:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1257:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1258:         }
1259:             break;
1260:
1261:         case POT_INVISIBILITY:
```

当前中文模板：魔力增强了！

输入还原：兽人的魔力增强了！

完整英文：
```text
 is healed!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1241}

参数表达式与来源：
```text
mon
T_(" is healed!")
1216:             return !mon.is_insubstantial();
1217:
1218:         default:
1219:             return false;
1220:     }
1221: }
1222:
1223: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1224: {
1225:     switch (potion)
1226:     {
1227:         case POT_HASTE:
1228:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1229:             break;
1230:
1231:         case POT_MIGHT:
1232:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1233:             break;
1234:
1235:         case POT_BRILLIANCE:
1236:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1237:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1238:             break;
1239:
1240:         case POT_HEAL_WOUNDS:
1241:             simple_monster_message(mon, T_(" is healed!"));
1242:             mon.heal(random_range(30, 50));
1243:             break;
1244:
1245:         case POT_CURING:
1246:             simple_monster_message(mon, T_(" is healed!"));
1247:             mon.heal(random_range(10, 20));
1248:             mon.del_ench(ENCH_POISON);
1249:             mon.del_ench(ENCH_CONFUSION);
1250:             break;
1251:
1252:         case POT_ENLIGHTENMENT:
1253:         {
1254:             simple_monster_message(mon, T_(" is enlightened!"));
1255:             const int dur = random_range(300, 450);
1256:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1257:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1258:         }
1259:             break;
1260:
1261:         case POT_INVISIBILITY:
1262:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1263:             break;
1264:
1265:         case POT_MAGIC:
1266:             mon.del_ench(ENCH_ANTIMAGIC);
```

当前中文模板：被治愈了！

输入还原：兽人被治愈了！

完整英文：
```text
 is healed!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1246}

参数表达式与来源：
```text
mon
T_(" is healed!")
1221: }
1222:
1223: void mons_potion_effect(monster& mon, potion_type potion, const actor& source)
1224: {
1225:     switch (potion)
1226:     {
1227:         case POT_HASTE:
1228:             enchant_actor_with_flavour(&mon, &source, BEAM_HASTE);
1229:             break;
1230:
1231:         case POT_MIGHT:
1232:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1233:             break;
1234:
1235:         case POT_BRILLIANCE:
1236:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1237:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1238:             break;
1239:
1240:         case POT_HEAL_WOUNDS:
1241:             simple_monster_message(mon, T_(" is healed!"));
1242:             mon.heal(random_range(30, 50));
1243:             break;
1244:
1245:         case POT_CURING:
1246:             simple_monster_message(mon, T_(" is healed!"));
1247:             mon.heal(random_range(10, 20));
1248:             mon.del_ench(ENCH_POISON);
1249:             mon.del_ench(ENCH_CONFUSION);
1250:             break;
1251:
1252:         case POT_ENLIGHTENMENT:
1253:         {
1254:             simple_monster_message(mon, T_(" is enlightened!"));
1255:             const int dur = random_range(300, 450);
1256:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1257:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1258:         }
1259:             break;
1260:
1261:         case POT_INVISIBILITY:
1262:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1263:             break;
1264:
1265:         case POT_MAGIC:
1266:             mon.del_ench(ENCH_ANTIMAGIC);
1267:             break;
1268:
1269:         case POT_BERSERK_RAGE:
1270:             mon.go_berserk(false);
1271:             break;
```

当前中文模板：被治愈了！

输入还原：兽人被治愈了！

完整英文：
```text
 is enlightened!
```

生产调用：{'path': 'crawl-ref/source/potion.cc', 'line': 1254}

参数表达式与来源：
```text
mon
T_(" is enlightened!")
1229:             break;
1230:
1231:         case POT_MIGHT:
1232:             enchant_actor_with_flavour(&mon, &source, BEAM_MIGHT);
1233:             break;
1234:
1235:         case POT_BRILLIANCE:
1236:             simple_monster_message(mon, T_(" magic is enhanced!"), true);
1237:             mon.add_ench(mon_enchant(ENCH_EMPOWERED_SPELLS, &source));
1238:             break;
1239:
1240:         case POT_HEAL_WOUNDS:
1241:             simple_monster_message(mon, T_(" is healed!"));
1242:             mon.heal(random_range(30, 50));
1243:             break;
1244:
1245:         case POT_CURING:
1246:             simple_monster_message(mon, T_(" is healed!"));
1247:             mon.heal(random_range(10, 20));
1248:             mon.del_ench(ENCH_POISON);
1249:             mon.del_ench(ENCH_CONFUSION);
1250:             break;
1251:
1252:         case POT_ENLIGHTENMENT:
1253:         {
1254:             simple_monster_message(mon, T_(" is enlightened!"));
1255:             const int dur = random_range(300, 450);
1256:             mon.add_ench(mon_enchant(ENCH_FLIGHT, &source, dur));
1257:             mon.add_ench(mon_enchant(ENCH_STRONG_WILLED, &source, dur));
1258:         }
1259:             break;
1260:
1261:         case POT_INVISIBILITY:
1262:             enchant_actor_with_flavour(&mon, &source, BEAM_INVISIBILITY);
1263:             break;
1264:
1265:         case POT_MAGIC:
1266:             mon.del_ench(ENCH_ANTIMAGIC);
1267:             break;
1268:
1269:         case POT_BERSERK_RAGE:
1270:             mon.go_berserk(false);
1271:             break;
1272:
1273:         case POT_RESISTANCE:
1274:             enchant_actor_with_flavour(&mon, &source, BEAM_RESISTANCE);
1275:             break;
1276:
1277:         case POT_MIST:
1278:             simple_monster_message(mon, T_(" becomes insubstantial!"));
1279:             mon.add_ench(mon_enchant(ENCH_INSUBSTANTIAL, &source, random_range(300, 450)));
```

当前中文模板：被启迪了！

输入还原：兽人被启迪了！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-01 — ok


### stable

完整英文：
```text
It was %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3296}

参数表达式与来源：
```text
scroll->quantity < prev_quantity ? T_("It was %s.") : T_("It is %s.")
article_a(scroll_name).c_str()
3271:
3272:     string scroll_name = scroll->name(DESC_QUALNAME);
3273:
3274:     if (!cancel_scroll)
3275:     {
3276:         if (in_inventory(*scroll))
3277:             dec_inv_item_quantity(link, 1);
3278:         else
3279:             dec_mitm_item_quantity(scroll->index(), 1);
3280:
3281:         count_action(CACT_USE, OBJ_SCROLLS);
3282:         count_action(CACT_READ, scroll->sub_type);
3283:
3284:         if (is_loud)
3285:             noisy(40, original_pos, MID_PLAYER);
3286:     }
3287:
3288:     if (!alreadyknown
3289:         && which_scroll != SCR_BRAND_WEAPON
3290:         && which_scroll != SCR_ENCHANT_WEAPON
3291:         && which_scroll != SCR_IDENTIFY
3292:         && which_scroll != SCR_ENCHANT_ARMOUR
3293:         && which_scroll != SCR_AMNESIA
3294:         && which_scroll != SCR_ACQUIREMENT)
3295:     {
3296:         mprf(scroll->quantity < prev_quantity ? T_("It was %s.") : T_("It is %s."),
3297:              article_a(scroll_name).c_str());
3298:     }
3299:
3300:     if (!alreadyknown)
3301:     {
3302:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3303:         {
3304:             mpr(T_("The power of discovery flows from your fingertips!"));
3305:             potionlike_effect(POT_MAGIC, 40);
3306:         }
3307:
3308:         if (dangerous)
3309:         {
3310:             // Xom loves it when you read an unknown scroll and there is a
3311:             // dangerous monster nearby... (though not as much as potions
3312:             // since there are no *really* bad scrolls, merely useless ones).
3313:             xom_is_stimulated(bad_effect ? 100 : 50);
3314:         }
3315:     }
3316:
3317:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3318:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3319:         && nearby_mons
3320:         && !cancel_scroll)
3321:     {
3322:         you.props[VICTORY_CONDUCT_KEY] = true;
```

当前中文模板：那是%s。

输入还原：None

完整英文：
```text
It is %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3296}

参数表达式与来源：
```text
scroll->quantity < prev_quantity ? T_("It was %s.") : T_("It is %s.")
article_a(scroll_name).c_str()
3271:
3272:     string scroll_name = scroll->name(DESC_QUALNAME);
3273:
3274:     if (!cancel_scroll)
3275:     {
3276:         if (in_inventory(*scroll))
3277:             dec_inv_item_quantity(link, 1);
3278:         else
3279:             dec_mitm_item_quantity(scroll->index(), 1);
3280:
3281:         count_action(CACT_USE, OBJ_SCROLLS);
3282:         count_action(CACT_READ, scroll->sub_type);
3283:
3284:         if (is_loud)
3285:             noisy(40, original_pos, MID_PLAYER);
3286:     }
3287:
3288:     if (!alreadyknown
3289:         && which_scroll != SCR_BRAND_WEAPON
3290:         && which_scroll != SCR_ENCHANT_WEAPON
3291:         && which_scroll != SCR_IDENTIFY
3292:         && which_scroll != SCR_ENCHANT_ARMOUR
3293:         && which_scroll != SCR_AMNESIA
3294:         && which_scroll != SCR_ACQUIREMENT)
3295:     {
3296:         mprf(scroll->quantity < prev_quantity ? T_("It was %s.") : T_("It is %s."),
3297:              article_a(scroll_name).c_str());
3298:     }
3299:
3300:     if (!alreadyknown)
3301:     {
3302:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3303:         {
3304:             mpr(T_("The power of discovery flows from your fingertips!"));
3305:             potionlike_effect(POT_MAGIC, 40);
3306:         }
3307:
3308:         if (dangerous)
3309:         {
3310:             // Xom loves it when you read an unknown scroll and there is a
3311:             // dangerous monster nearby... (though not as much as potions
3312:             // since there are no *really* bad scrolls, merely useless ones).
3313:             xom_is_stimulated(bad_effect ? 100 : 50);
3314:         }
3315:     }
3316:
3317:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3318:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3319:         && nearby_mons
3320:         && !cancel_scroll)
3321:     {
3322:         you.props[VICTORY_CONDUCT_KEY] = true;
```

当前中文模板：那是%s。

输入还原：None

完整英文：
```text
The power of discovery flows from your fingertips!
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3304}

参数表达式与来源：
```text
T_("The power of discovery flows from your fingertips!")

```

当前中文模板：发现之能量从你的指尖流出！

输入还原：发现之能量从你的指尖流出！


### trunk

完整英文：
```text
The power of discovery flows from your fingertips!
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 2120}

参数表达式与来源：
```text
T_("The power of discovery flows from your fingertips!")

```

当前中文模板：发现之能量从你的指尖流出！

输入还原：发现之能量从你的指尖流出！

完整英文：
```text
It is %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3458}

参数表达式与来源：
```text
read_result == spret::abort ? T_("It is %s.") : T_("It was %s.")
article_a(scroll_name).c_str()
3433:     {
3434:         int link = in_inventory(*scroll) ? scroll->link : -1;
3435:
3436:         if (in_inventory(*scroll))
3437:             dec_inv_item_quantity(link, 1);
3438:         else
3439:             dec_mitm_item_quantity(scroll->index(), 1);
3440:
3441:         count_action(CACT_USE, OBJ_SCROLLS);
3442:         count_action(CACT_READ, scroll->sub_type);
3443:
3444:         if (is_loud)
3445:             noisy(40, original_pos, MID_PLAYER);
3446:     }
3447:
3448:     const scroll_type which_scroll = static_cast<scroll_type>(scroll->sub_type);
3449:
3450:     if (!alreadyknown
3451:         && which_scroll != SCR_BRAND_WEAPON
3452:         && which_scroll != SCR_ENCHANT_WEAPON
3453:         && which_scroll != SCR_IDENTIFY
3454:         && which_scroll != SCR_ENCHANT_ARMOUR
3455:         && which_scroll != SCR_AMNESIA
3456:         && which_scroll != SCR_ACQUIREMENT)
3457:     {
3458:         mprf(read_result == spret::abort ? T_("It is %s.") : T_("It was %s."),
3459:              article_a(scroll_name).c_str());
3460:     }
3461:
3462:     if (!alreadyknown)
3463:     {
3464:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3465:         {
3466:             mpr(T_("The power of discovery flows from your fingertips!"));
3467:             potionlike_effect(POT_MAGIC, 40);
3468:         }
3469:
3470:         if (dangerous)
3471:         {
3472:             // Xom loves it when you read an unknown scroll and there is a
3473:             // dangerous monster nearby... (though not as much as potions
3474:             // since there are no *really* bad scrolls, merely useless ones).
3475:             xom_is_stimulated(bad_effect ? 100 : 50);
3476:         }
3477:     }
3478:
3479:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3480:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3481:         && nearby_mons
3482:         && read_result != spret::abort)
3483:     {
3484:         you.props[VICTORY_CONDUCT_KEY] = true;
```

当前中文模板：那是%s。

输入还原：None

完整英文：
```text
It was %s.
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3458}

参数表达式与来源：
```text
read_result == spret::abort ? T_("It is %s.") : T_("It was %s.")
article_a(scroll_name).c_str()
3433:     {
3434:         int link = in_inventory(*scroll) ? scroll->link : -1;
3435:
3436:         if (in_inventory(*scroll))
3437:             dec_inv_item_quantity(link, 1);
3438:         else
3439:             dec_mitm_item_quantity(scroll->index(), 1);
3440:
3441:         count_action(CACT_USE, OBJ_SCROLLS);
3442:         count_action(CACT_READ, scroll->sub_type);
3443:
3444:         if (is_loud)
3445:             noisy(40, original_pos, MID_PLAYER);
3446:     }
3447:
3448:     const scroll_type which_scroll = static_cast<scroll_type>(scroll->sub_type);
3449:
3450:     if (!alreadyknown
3451:         && which_scroll != SCR_BRAND_WEAPON
3452:         && which_scroll != SCR_ENCHANT_WEAPON
3453:         && which_scroll != SCR_IDENTIFY
3454:         && which_scroll != SCR_ENCHANT_ARMOUR
3455:         && which_scroll != SCR_AMNESIA
3456:         && which_scroll != SCR_ACQUIREMENT)
3457:     {
3458:         mprf(read_result == spret::abort ? T_("It is %s.") : T_("It was %s."),
3459:              article_a(scroll_name).c_str());
3460:     }
3461:
3462:     if (!alreadyknown)
3463:     {
3464:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3465:         {
3466:             mpr(T_("The power of discovery flows from your fingertips!"));
3467:             potionlike_effect(POT_MAGIC, 40);
3468:         }
3469:
3470:         if (dangerous)
3471:         {
3472:             // Xom loves it when you read an unknown scroll and there is a
3473:             // dangerous monster nearby... (though not as much as potions
3474:             // since there are no *really* bad scrolls, merely useless ones).
3475:             xom_is_stimulated(bad_effect ? 100 : 50);
3476:         }
3477:     }
3478:
3479:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3480:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3481:         && nearby_mons
3482:         && read_result != spret::abort)
3483:     {
3484:         you.props[VICTORY_CONDUCT_KEY] = true;
```

当前中文模板：那是%s。

输入还原：None

完整英文：
```text
The power of discovery flows from your fingertips!
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3466}

参数表达式与来源：
```text
T_("The power of discovery flows from your fingertips!")

```

当前中文模板：发现之能量从你的指尖流出！

输入还原：发现之能量从你的指尖流出！

独立判断与参数还原：按消耗/取消分支选择 It was/is，汉语那是无强制过去时区别，不因此改写；例那是鉴定卷轴。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-05 — ok


### stable

完整英文：
```text
You are lethally poisoned!
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4692}

参数表达式与来源：
```text
MSGCH_DANGER
T_("You are lethally poisoned!")

```

当前中文模板：你的中毒已达到致命程度！

输入还原：你的中毒已达到致命程度！

完整英文：
```text
%s
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4697}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                         : T_("You are poisoned.")
4672:     }
4673:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4674:         return false;
4675:
4676:     const int old_value = you.duration[DUR_POISONING];
4677:     const bool was_fatal = poison_is_lethal();
4678:
4679:     if (player_res_poison() < 0)
4680:         amount *= 2;
4681:
4682:     // TODO: support being poisoned by monsters wearing "harm (ha)
4683:     if (you.extra_harm())
4684:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4685:
4686:     you.duration[DUR_POISONING] += amount * 1000;
4687:
4688:     if (you.duration[DUR_POISONING] > old_value)
4689:     {
4690:         if (poison_is_lethal() && !was_fatal)
4691:         {
4692:             mprf(MSGCH_DANGER,
4693:                 T_("You are lethally poisoned!"));
4694:         }
4695:         else
4696:         {
4697:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4698:                                          : T_("You are poisoned."));
4699:         }
4700:
4701:         learned_something_new(HINT_YOU_POISON);
4702:     }
4703:
4704:     you.props[POISONER_KEY] = source;
4705:     you.props[POISON_AUX_KEY] = source_aux;
4706:
4707:     // Display the poisoned segment of our health, in case we take no damage
4708:     you.redraw_hit_points = true;
4709:
4710:     return amount;
4711: }
4712:
4713: int get_player_poisoning()
4714: {
4715:     if (player_res_poison() >= 3)
4716:         return 0;
4717: #if TAG_MAJOR_VERSION == 34
4718:     // Approximate the effect of damage shaving by giving the first
4719:     // 25 points of poison damage for 'free'
4720:     if (can_shave_damage())
4721:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4722: #endif
4723:     return you.duration[DUR_POISONING] / 1000;
```

当前中文模板：%s

输入还原：你的中毒加重了。

完整英文：
```text
You are more poisoned.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4697}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                         : T_("You are poisoned.")

```

当前中文模板：你的中毒加重了。

输入还原：None

完整英文：
```text
You are poisoned.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4697}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                         : T_("You are poisoned.")

```

当前中文模板：你中毒了。

输入还原：None


### trunk

完整英文：
```text
You are lethally poisoned!
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4912}

参数表达式与来源：
```text
MSGCH_DANGER
T_("You are lethally poisoned!")

```

当前中文模板：你的中毒已达到致命程度！

输入还原：你的中毒已达到致命程度！

完整英文：
```text
%s
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4917}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                                : T_("You are poisoned.")
4892:     }
4893:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4894:         return false;
4895:
4896:     const int old_value = you.duration[DUR_POISONING];
4897:     const bool was_fatal = poison_is_lethal();
4898:
4899:     if (player_res_poison() < 0)
4900:         amount = amount * 3 / 2;
4901:
4902:     // TODO: support being poisoned by monsters wearing "harm (ha)
4903:     if (you.extra_harm())
4904:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4905:
4906:     you.duration[DUR_POISONING] += amount * 1000;
4907:
4908:     if (you.duration[DUR_POISONING] > old_value)
4909:     {
4910:         if (poison_is_lethal() && !was_fatal)
4911:         {
4912:             mprf(MSGCH_DANGER,
4913:                 T_("You are lethally poisoned!"));
4914:         }
4915:         else
4916:         {
4917:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4918:                                                 : T_("You are poisoned."));
4919:         }
4920:
4921:         learned_something_new(HINT_YOU_POISON);
4922:     }
4923:
4924:     you.props[POISONER_KEY] = source;
4925:     you.props[POISON_AUX_KEY] = source_aux;
4926:
4927:     // Display the poisoned segment of our health, in case we take no damage
4928:     you.redraw_hit_points = true;
4929:
4930:     return amount;
4931: }
4932:
4933: int get_player_poisoning()
4934: {
4935:     if (player_res_poison() >= 3)
4936:         return 0;
4937: #if TAG_MAJOR_VERSION == 34
4938:     // Approximate the effect of damage shaving by giving the first
4939:     // 25 points of poison damage for 'free'
4940:     if (can_shave_damage())
4941:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4942: #endif
4943:     return you.duration[DUR_POISONING] / 1000;
```

当前中文模板：%s

输入还原：你的中毒加重了。

完整英文：
```text
You are more poisoned.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4917}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                                : T_("You are poisoned.")

```

当前中文模板：你的中毒加重了。

输入还原：None

完整英文：
```text
You are poisoned.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4917}

参数表达式与来源：
```text
MSGCH_WARN
"%s"
old_value > 0 ? T_("You are more poisoned.")
                                                : T_("You are poisoned.")

```

当前中文模板：你中毒了。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## B-08 — ok


### stable

完整英文：
```text
You emit a cloud of foul miasma!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 4939}

参数表达式与来源：
```text
T_("You emit a cloud of foul miasma!")

```

当前中文模板：你释放出一团恶臭的瘴气！

输入还原：你释放出一团恶臭的瘴气！


### trunk

完整英文：
```text
You emit a cloud of foul miasma!
```

生产调用：{'path': 'crawl-ref/source/melee-attack.cc', 'line': 5132}

参数表达式与来源：
```text
T_("You emit a cloud of foul miasma!")

```

当前中文模板：你释放出一团恶臭的瘴气！

输入还原：你释放出一团恶臭的瘴气！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-07 — ok


### stable

完整英文：
```text
You can't see anything. Try to condense clouds anyway?
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 920}

参数表达式与来源：
```text
T_("You can't see anything. Try to condense clouds anyway?")
true
'n'

```

当前中文模板：你什么也看不见。仍然尝试凝结云雾吗？

输入还原：你什么也看不见。仍然尝试凝结云雾吗？


### trunk

完整英文：
```text
You can't see anything. Try to condense clouds anyway?
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 893}

参数表达式与来源：
```text
T_("You can't see anything. Try to condense clouds anyway?")
true
'n'

```

当前中文模板：你什么也看不见。仍然尝试凝结云雾吗？

输入还原：你什么也看不见。仍然尝试凝结云雾吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-07 — ok


### stable

完整英文：
```text
You are ready to perform a blood rite again.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 1069}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You are ready to perform a blood rite again.")

```

当前中文模板：你准备好再次执行血之仪式了。

输入还原：你准备好再次执行血之仪式了。


### trunk

完整英文：
```text
You are ready to perform a blood rite again.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 1178}

参数表达式与来源：
```text
MSGCH_DURATION
T_("You are ready to perform a blood rite again.")

```

当前中文模板：你准备好再次执行血之仪式了。

输入还原：你准备好再次执行血之仪式了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-08 — ok


### stable

完整英文：
```text
You don't have enough health right now.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4168}

参数表达式与来源：
```text
T_("You don't have enough health right now.")

```

当前中文模板：你当前没有足够的生命值。

输入还原：你当前没有足够的生命值。


### trunk

完整英文：
```text
You don't have enough health right now.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 4379}

参数表达式与来源：
```text
T_("You don't have enough health right now.")

```

当前中文模板：你当前没有足够的生命值。

输入还原：你当前没有足够的生命值。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-02 — objective_error


### stable

完整英文：
```text
Your %1$s attune%2$s to your body, and you begin to %3$s.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 1198}

参数表达式与来源：
```text
T_("Your %1$s attune%2$s to your body, and you begin to %3$s.")
eq_str.c_str()
verb_form
msg_str.c_str()
1173:                 plural = true;
1174:             entry.attuned = true;
1175:         }
1176:     }
1177:
1178:     if (eq_list.empty())
1179:         return;
1180:
1181:     vector<string> msgs;
1182:
1183:     if (gained_regen || gained_mana_regen)
1184:     {
1185:         const char* regen_type = gained_regen && gained_mana_regen
1186:             ? T_(" health and magic")
1187:             : (gained_regen ? "" : T_(" magic"));
1188:         msgs.emplace_back(make_stringf(
1189:             T_("regenerate%s more quickly"), regen_type));
1190:     }
1191:     if (gained_chemistry)
1192:         msgs.emplace_back(T_("extract magic from the potions you drink"));
1193:
1194:     plural = plural || eq_list.size() > 1;
1195:     string eq_str = comma_separated_line(eq_list.begin(), eq_list.end());
1196:     string msg_str = comma_separated_line(msgs.begin(), msgs.end());
1197:     const char* verb_form = plural ? "attune themselves" : "attunes itself";
1198:     mprf_p(T_("Your %1$s attune%2$s to your body, and you begin to %3$s."),
1199:            eq_str.c_str(), verb_form, msg_str.c_str());
1200: }
1201:
1202: // cjo: Handles player hp and mp regeneration. If the counter
1203: // you.hit_points_regeneration is over 100, a loop restores 1 hp and decreases
1204: // the counter by 100 (so you can regen more than 1 hp per turn). If the counter
1205: // is below 100, it is increased by a variable calculated from delay,
1206: // BASELINE_DELAY, and your regeneration rate. MP regeneration happens
1207: // similarly, but the countup depends on delay, BASELINE_DELAY, and
1208: // you.max_magic_points
1209: static void _regenerate_hp_and_mp(int delay)
1210: {
1211:     if (crawl_state.disables[DIS_PLAYER_REGEN])
1212:         return;
1213:
1214:     const int old_hp = you.hp;
1215:     const int old_mp = you.magic_points;
1216:
1217:     // HP Regeneration
1218:     if (!you.duration[DUR_DEATHS_DOOR])
1219:     {
1220:         const int base_val = player_regen();
1221:         you.hit_points_regeneration += div_rand_round(base_val * delay, BASELINE_DELAY);
1222:     }
1223:
1224:     while (you.hit_points_regeneration >= 100)
```

当前中文模板：你的%1$s适应了你的身体，你开始%3$s。

输入还原：你的amulet适应了你的身体，你开始更快地再生。


### trunk

完整英文：
```text
Your %1$s attune%2$s to your body, and you begin to %3$s.
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 1315}

参数表达式与来源：
```text
T_("Your %1$s attune%2$s to your body, and you begin to %3$s.")
eq_str.c_str()
verb_suffix
msg_str.c_str()
1290:
1291:     if (eq_list.empty())
1292:         return;
1293:
1294:     vector<string> msgs;
1295:
1296:     if (gained_regen || gained_mana_regen)
1297:     {
1298:         const char* regen_type = gained_regen && gained_mana_regen
1299:             ? T_(" health and magic")
1300:             : (gained_regen ? "" : T_(" magic"));
1301:         msgs.emplace_back(make_stringf(
1302:             T_("regenerate%s more quickly"), regen_type));
1303:     }
1304:     if (gained_chemistry)
1305:         msgs.emplace_back(T_("extract magic from the potions you drink"));
1306:
1307:     plural = plural || eq_list.size() > 1;
1308:     string eq_str = comma_separated_line(eq_list.begin(), eq_list.end(),
1309:                 Options.language == lang_t::ZH ? T_(",") : T_(" and "),
1310:                 Options.language == lang_t::ZH ? T_(",") : ", ");
1311:     string msg_str = comma_separated_line(msgs.begin(), msgs.end(),
1312:                 Options.language == lang_t::ZH ? T_(",") : T_(" and "),
1313:                 Options.language == lang_t::ZH ? T_(",") : ", ");
1314:     const char* verb_suffix = plural ? " themselves" : "s itself";
1315:     mprf_p(T_("Your %1$s attune%2$s to your body, and you begin to %3$s."),
1316:            eq_str.c_str(), verb_suffix, msg_str.c_str());
1317: }
1318:
1319: // cjo: Handles player hp and mp regeneration. If the counter
1320: // you.hit_points_regeneration is over 100, a loop restores 1 hp and decreases
1321: // the counter by 100 (so you can regen more than 1 hp per turn). If the counter
1322: // is below 100, it is increased by a variable calculated from delay,
1323: // BASELINE_DELAY, and your regeneration rate. MP regeneration happens
1324: // similarly, but the countup depends on delay, BASELINE_DELAY, and
1325: // you.max_magic_points
1326: static void _regenerate_hp_and_mp(int delay)
1327: {
1328:     if (crawl_state.disables[DIS_PLAYER_REGEN])
1329:         return;
1330:
1331:     // HP Regeneration
1332:     if (!you.duration[DUR_DEATHS_DOOR])
1333:     {
1334:         const int base_val = player_regen();
1335:         you.hit_points_regeneration += div_rand_round(base_val * delay, BASELINE_DELAY);
1336:     }
1337:
1338:     if (you.duration[DUR_INDOMITABLE])
1339:     {
1340:         const int per_aut = player_indomitable_regen_rate();
1341:         const int total = min(per_aut * delay, you.duration[DUR_INDOMITABLE]);
```

当前中文模板：你的%1$s适应了你的身体，你开始%3$s。

输入还原：你的项链适应了你的身体，你开始更快地再生。

独立判断与参数还原：非神器项链名由裸英文 amulet 提供，多件装备及效果还使用默认英语列表连接词，产生中英混排。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "untranslated_parameter", "line": "stable", "english": "Your %1$s attune%2$s to your body, and you begin to %3$s.", "current_full_zh": "你的amulet适应了你的身体，你开始更快地再生。", "problem": "非神器项链名由裸英文 amulet 提供，多件装备及效果还使用默认英语列表连接词，产生中英混排。", "suggested_zh": "你的项链适应了你的身体，你开始更快地再生。", "evidence": "stable player-reacts.cc:1169-1171,1195-1196；trunk :1285,1308-1313 已本地化。", "defect_points": 1}


## D-04 — ok


### stable

完整英文：
```text
...but nothing happens.
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 292}

参数表达式与来源：
```text
T_("...but nothing happens.")

```

当前中文模板：……但什么也没发生。

输入还原：……但什么也没发生。

完整英文：
```text
...and %s %s out!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 298}

参数表达式与来源：
```text
T_("...and %s %s out!")
mons->name(DESC_A).c_str()
verb
273:
274:     // two rolls to reduce std deviation - +-6 so can get < max even at 27 sk
275:     int rnd_factor = random2(7);
276:     rnd_factor -= random2(7);
277:     const int hd_min = min(27, you.skill(SK_EVOCATIONS) + rnd_factor);
278:     const int tier = mutant_beast_tier(hd_min);
279:     ASSERT(tier < NUM_BEAST_TIERS);
280:
281:     mgen_data mg(MONS_MUTANT_BEAST, BEH_FRIENDLY, you.pos(), MHITYOU,
282:                  MG_AUTOFOE);
283:     mg.set_summoned(&you, 0, summ_dur(3 + random2(3)));
284:
285:     mg.hd = beast_tiers[tier];
286:     dprf("hd %d (min %d, tier %d)", mg.hd, hd_min, tier);
287:     const monster* mons = create_monster(mg);
288:
289:     if (!mons)
290:     {
291:         // Failed to create monster for some reason
292:         mpr(T_("...but nothing happens."));
293:         return true;
294:     }
295:
296:     // T_() handles language-dependent verb fragments (flies/飞 vs leaps/跳)
297:     const char* verb = mons->airborne() ? T_("flies") : T_("leaps");
298:     mprf(T_("...and %s %s out!"),
299:          mons->name(DESC_A).c_str(), verb);
300:     did_god_conduct(DID_CHAOS, random_range(5,10));
301:
302:     return true;
303: }
304:
305: // Generate webs on hostile monsters and trap them.
306: static bool _place_webs()
307: {
308:     bool webbed = false;
309:     const int evo_skill = you.skill(SK_EVOCATIONS);
310:     // At 0 evo skill, this is about a 1/3 chance of webbing each
311:     // enemy. At 27 skill, it's about an 9/10 chance.
312:     const int web_chance = 36 + evo_skill * 2;
313:     const int max_range = LOS_DEFAULT_RANGE / 2 + 2;
314:     for (monster_near_iterator mi(you.pos(), LOS_SOLID); mi; ++mi)
315:     {
316:         trap_def *trap = trap_at((*mi)->pos());
317:         // Don't destroy non-web traps or try to trap monsters
318:         // currently caught by something.
319:         if (you.pos().distance_from((*mi)->pos()) > max_range
320:             || (!trap && env.grid((*mi)->pos()) != DNGN_FLOOR)
321:             || (trap && trap->type != TRAP_WEB)
322:             || (*mi)->friendly()
323:             || (*mi)->caught())
324:         {
```

当前中文模板：...%s%s了出来！

输入还原：None


### trunk

完整英文：
```text
...but nothing happens.
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 292}

参数表达式与来源：
```text
T_("...but nothing happens.")

```

当前中文模板：……但什么也没发生。

输入还原：……但什么也没发生。

完整英文：
```text
...and %s %s out!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 298}

参数表达式与来源：
```text
T_("...and %s %s out!")
mons->name(DESC_A).c_str()
verb.c_str()
273:
274:     // two rolls to reduce std deviation - +-6 so can get < max even at 27 sk
275:     int rnd_factor = random2(7);
276:     rnd_factor -= random2(7);
277:     const int hd_min = min(27, you.skill(SK_EVOCATIONS) + rnd_factor);
278:     const int tier = mutant_beast_tier(hd_min);
279:     ASSERT(tier < NUM_BEAST_TIERS);
280:
281:     mgen_data mg(MONS_MUTANT_BEAST, BEH_FRIENDLY, you.pos(), MHITYOU,
282:                  MG_AUTOFOE);
283:     mg.set_summoned(&you, 0, summ_dur(3 + random2(3)));
284:
285:     mg.hd = beast_tiers[tier];
286:     dprf("hd %d (min %d, tier %d)", mg.hd, hd_min, tier);
287:     const monster* mons = create_monster(mg);
288:
289:     if (!mons)
290:     {
291:         // Failed to create monster for some reason
292:         mpr(T_("...but nothing happens."));
293:         return true;
294:     }
295:
296:     // T_() handles language-dependent verb fragments (flies/飞 vs leaps/跳)
297:     const string verb = mons->airborne() ? T_("flies") : T_("leaps");
298:     mprf(T_("...and %s %s out!"),
299:          mons->name(DESC_A).c_str(), verb.c_str());
300:
301:     return true;
302: }
303:
304: // Generate webs on hostile monsters and trap them.
305: static bool _place_webs()
306: {
307:     bool webbed = false;
308:     const int evo_skill = you.skill(SK_EVOCATIONS);
309:     // At 0 evo skill, this is about a 1/3 chance of webbing each
310:     // enemy. At 27 skill, it's about an 9/10 chance.
311:     const int web_chance = 36 + evo_skill * 2;
312:     const int max_range = LOS_DEFAULT_RANGE / 2 + 2;
313:     for (monster_near_iterator mi(you.pos(), LOS_SOLID); mi; ++mi)
314:     {
315:         if (you.pos().distance_from((*mi)->pos()) > max_range
316:             || (*mi)->friendly()
317:             || (*mi)->caught())
318:         {
319:             continue;
320:         }
321:
322:         if (!x_chance_in_y(web_chance, 100))
323:             continue;
324:
```

当前中文模板：...%s%s了出来！

输入还原：None

独立判断与参数还原：flies=飞、leaps=跳，例...蝙蝠飞了出来！/...兽人跳了出来！，失败分支……但什么也没发生。；ASCII省略号略不统一，不独立判错。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-08 — ok


### stable

完整英文：
```text
The mirror clouds!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 1207}

参数表达式与来源：
```text
T_("The mirror clouds!")

```

当前中文模板：镜子变模糊了！

输入还原：镜子变模糊了！


### trunk

完整英文：
```text
The mirror clouds!
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 1254}

参数表达式与来源：
```text
T_("The mirror clouds!")

```

当前中文模板：镜子变模糊了！

输入还原：镜子变模糊了！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## F-04 — ok


### stable

完整英文：
```text
%s emerges from the mists of memory!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 669}

参数表达式与来源：
```text
T_("%s emerges from the mists of memory!")
ancestor->name(DESC_YOUR).c_str()
644:     {
645:         const string title = zin_recite_text(you.attribute[ATTR_RECITE_SEED],
646:                                              you.attribute[ATTR_RECITE_TYPE], -1);
647:         string speech = make_stringf(T_("You finish reciting %s."),
648:                                      title.c_str());
649:         if (one_chance_in(27))
650:         {
651:             const string closure = getSpeakString("recite_closure");
652:             if (!closure.empty())
653:                 speech += " " + closure;
654:         }
655:         mprf(MSGCH_DURATION, "%s", speech.c_str());
656:         you.set_duration(DUR_RECITE_COOLDOWN, 1 + random2(10) + random2(30));
657:     }
658: }
659:
660: /**
661:  * Try to respawn the player's ancestor, if possible.
662:  */
663: static void _try_to_respawn_ancestor()
664: {
665:     monster *ancestor = create_monster(hepliaklqana_ancestor_gen_data());
666:     if (!ancestor)
667:         return;
668:
669:     mprf(T_("%s emerges from the mists of memory!"),
670:          ancestor->name(DESC_YOUR).c_str());
671:     add_companion(ancestor);
672:     place_cloud(CLOUD_MIST, ancestor->pos(), random_range(1,2), ancestor); // ;)
673: }
674:
675: static void _decrement_transform_duration(int delay)
676: {
677:     if (you.form == you.default_form || you.form == transformation::flux)
678:         return;
679:
680:     // FIXME: [ds] Remove this once we've ensured durations can never go < 0?
681:     if (you.duration[DUR_TRANSFORMATION] <= 0
682:         && you.form != transformation::none)
683:     {
684:         you.duration[DUR_TRANSFORMATION] = 1;
685:     }
686:
687:     if (form_can_fly()
688:         || form_can_swim() && feat_is_water(env.grid(you.pos())))
689:     {
690:         // Disable emergency flight if it was active
691:         you.props.erase(EMERGENCY_FLIGHT_KEY);
692:     }
693:     if (_decrement_a_duration(DUR_TRANSFORMATION, delay, nullptr, random2(3),
694:                                 T_("Your transformation is almost over.")))
695:     {
```

当前中文模板：%s从记忆之雾中浮现！

输入还原：None


### trunk

完整英文：
```text
%s emerges from the mists of memory!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 789}

参数表达式与来源：
```text
T_("%s emerges from the mists of memory!")
ancestor->name(DESC_YOUR).c_str()
764:     if (step == 0)
765:     {
766:         const string title = zin_recite_text(you.attribute[ATTR_RECITE_SEED],
767:                                              you.attribute[ATTR_RECITE_TYPE], -1);
768:         string speech = make_stringf(T_("You finish reciting %s."), title.c_str());
769:         if (one_chance_in(27))
770:         {
771:             const string closure = getSpeakString("recite_closure");
772:             if (!closure.empty())
773:                 speech += " " + closure;
774:         }
775:         mprf(MSGCH_DURATION, "%s", speech.c_str());
776:         you.set_duration(DUR_RECITE_COOLDOWN, 1 + random2(10) + random2(30));
777:     }
778: }
779:
780: /**
781:  * Try to respawn the player's ancestor, if possible.
782:  */
783: static void _try_to_respawn_ancestor()
784: {
785:     monster *ancestor = create_monster(hepliaklqana_ancestor_gen_data());
786:     if (!ancestor)
787:         return;
788:
789:     mprf(T_("%s emerges from the mists of memory!"),
790:          ancestor->name(DESC_YOUR).c_str());
791:     add_companion(ancestor);
792:     place_cloud(CLOUD_MIST, ancestor->pos(), random_range(1,2), ancestor); // ;)
793: }
794:
795: static void _decrement_transform_duration(int delay)
796: {
797:     if (you.form == you.default_form || you.form == transformation::flux)
798:         return;
799:
800:     // FIXME: [ds] Remove this once we've ensured durations can never go < 0?
801:     if (you.duration[DUR_TRANSFORMATION] <= 0
802:         && you.form != transformation::none)
803:     {
804:         you.duration[DUR_TRANSFORMATION] = 1;
805:     }
806:
807:     if (form_can_fly()
808:         || form_can_swim() && feat_is_water(env.grid(you.pos())))
809:     {
810:         // Disable emergency flight if it was active
811:         you.props.erase(EMERGENCY_FLIGHT_KEY);
812:     }
813:     if (_decrement_a_duration(DUR_TRANSFORMATION, delay, nullptr, random2(3),
814:                                 T_("Your transformation is almost over.")))
815:     {
```

当前中文模板：%s从记忆之雾中浮现！

输入还原：None

独立判断与参数还原：DESC_YOUR 先祖名本身包含所有格，模板不再加你的，例你的先祖从记忆之雾中浮现！。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## C-12 — ok


### stable

完整英文：
```text
There are no items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1526}

参数表达式与来源：
```text
T_("There are no items here.")

```

当前中文模板：这里没有任何物品。

输入还原：这里没有任何物品。


### trunk

完整英文：
```text
There are no items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1492}

参数表达式与来源：
```text
T_("There are no items here.")

```

当前中文模板：这里没有任何物品。

输入还原：这里没有任何物品。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## A-10 — ok


### stable

完整英文：
```text
With a burst of heat and light, you rocket upwards!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 767}

参数表达式与来源：
```text
T_("With a burst of heat and light, you rocket upwards!")

```

当前中文模板：随着一阵热与光的爆发，你像火箭一样向上冲！

输入还原：随着一阵热与光的爆发，你像火箭一样向上冲！

完整英文：
```text
In a burst of heat and light, you briefly surge upwards...but you can't rise from here.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 773}

参数表达式与来源：
```text
T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here.")

```

当前中文模板：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

输入还原：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

完整英文：
```text
With a burst of heat and light, you rocket upwards!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 777}

参数表达式与来源：
```text
T_("With a burst of heat and light, you rocket upwards!")

```

当前中文模板：随着一阵热与光的爆发，你像火箭一样向上冲！

输入还原：随着一阵热与光的爆发，你像火箭一样向上冲！


### trunk

完整英文：
```text
With a burst of heat and light, you rocket upwards!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 783}

参数表达式与来源：
```text
T_("With a burst of heat and light, you rocket upwards!")

```

当前中文模板：随着一阵热与光的爆发，你像火箭一样向上冲！

输入还原：随着一阵热与光的爆发，你像火箭一样向上冲！

完整英文：
```text
In a burst of heat and light, you briefly surge upwards...but you can't rise from here.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 789}

参数表达式与来源：
```text
T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here.")

```

当前中文模板：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

输入还原：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

完整英文：
```text
With a burst of heat and light, you rocket upwards!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 793}

参数表达式与来源：
```text
T_("With a burst of heat and light, you rocket upwards!")

```

当前中文模板：随着一阵热与光的爆发，你像火箭一样向上冲！

输入还原：随着一阵热与光的爆发，你像火箭一样向上冲！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-01 — ok


### stable


### trunk

完整英文：
```text


It seems like it would really prefer not to be here right now.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 1181}

参数表达式与来源：
```text
if (!descriptor.empty())
        description << T_("\n\nIt seems like it would really prefer not to be here right now.");

```

当前中文模板：

它看起来现在真的宁愿待在别的地方。

输入还原：

它看起来现在真的宁愿待在别的地方。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-02 — ok


### stable

完整英文：
```text

Pray here with <w>%s</w> to learn more.

```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3569}

参数表达式与来源：
```text
long_desc +=
            make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
                         command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3547:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3548:             }
3549:             else
3550:             {
3551:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3552:                                       ? T_("enter") : T_("exit");
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
3560:                        "with the <w>%3$s</w> key%4$s."),
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
3569:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3570:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3571:     }
3572:     else if (feat == DNGN_ENTER_SHOP)
3573:     {
3574:         long_desc += make_stringf(
3575:                 T_("\nWhile standing here, you can enter <w>%s</w> with "
3576:                 "the <w>%s</w> key."),
3577:                 desc.c_str(),
3578:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3579:     }
3580:     else if (feat == DNGN_TRANSPORTER)
3581:     {
3582:         long_desc += make_stringf_p(
3583:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3584:                 desc_the.c_str(),
3585:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3586:     }
3587:
3588:     // mention that permanent trees are usually flammable
3589:     // (except for autumnal trees in Wucad Mu's Monastery)
3590:     if (feat_is_flammable(feat) && !is_temp_terrain(pos) && in_bounds(pos)
3591:         && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
3592:     {
```

当前中文模板：
在此用<w>%s</w>祈祷以了解更多。


输入还原：None


### trunk

完整英文：
```text

Pray here with <w>%s</w> to learn more.

```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3847}

参数表达式与来源：
```text
long_desc +=
            make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
                         command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3825:             }
3826:             else
3827:             {
3828:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3829:                                       ? T_("enter") : T_("exit");
3830:                 const string condition =
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
3837:                     T_("\nWhile standing here, you can %1$s through %2$s "
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
3846:         long_desc +=
3847:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3848:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3849:     }
3850:     else if (feat == DNGN_ENTER_SHOP)
3851:     {
3852:         long_desc += make_stringf_p(
3853:                 T_("\nWhile standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key."),
3854:                 desc.c_str(),
3855:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3856:     }
3857:     else if (feat == DNGN_TRANSPORTER)
3858:     {
3859:         long_desc += make_stringf_p(
3860:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3861:                 desc_the.c_str(),
3862:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3863:     }
3864:     else if (feat == DNGN_PURIFIED_MUTATION_CATALYST)
3865:     {
3866:         if (you.religion == GOD_ZIN)
3867:         {
3868:             long_desc += T_("\nYour adherence to the laws of Zin forbids you from using "
3869:                             "such a device.");
3870:         }
```

当前中文模板：
在此用<w>%s</w>祈祷以了解更多。


输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-03 — ok


### stable

完整英文：
```text

While standing here, you can %1$s through %2$s with the <w>%3$s</w> key%4$s.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3559}

参数表达式与来源：
```text
// Keep the route inside the complete sentence so the localized
                // action keeps its own word order.
                long_desc += make_stringf_p(
                    T_("\nWhile standing here, you can %1$s through %2$s "
                       "with the <w>%3$s</w> key%4$s."),
                    action.c_str(), desc_the.c_str(), key.c_str(),
                    condition.c_str());
3537:                     _esc_cmd_to_str(stair_dir).c_str());
3538:         }
3539:         else if (feat_is_gate(feat))
3540:         {
3541:             const string key = _esc_cmd_to_str(stair_dir);
3542:             if (feat == DNGN_ENTER_HELL)
3543:             {
3544:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3545:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3546:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3547:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3548:             }
3549:             else
3550:             {
3551:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3552:                                       ? T_("enter") : T_("exit");
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
3560:                        "with the <w>%3$s</w> key%4$s."),
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
3569:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3570:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3571:     }
3572:     else if (feat == DNGN_ENTER_SHOP)
3573:     {
3574:         long_desc += make_stringf(
3575:                 T_("\nWhile standing here, you can enter <w>%s</w> with "
3576:                 "the <w>%s</w> key."),
3577:                 desc.c_str(),
3578:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3579:     }
3580:     else if (feat == DNGN_TRANSPORTER)
3581:     {
3582:         long_desc += make_stringf_p(
3583:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3584:                 desc_the.c_str(),
```

当前中文模板：
站在这里时，%4$s你可以按<w>%3$s</w>键通过%2$s%1$s。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can %1$s through %2$s with the <w>%3$s</w> key%4$s.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3837}

参数表达式与来源：
```text
// Keep the route in the complete sentence. Translating an
                // independent "through" fragment would force English word
                // order on the localized enter/exit action.
                long_desc += make_stringf_p(
                    T_("\nWhile standing here, you can %1$s through %2$s "
                       "with the <w>%3$s</w> key%4$s."),
                    action.c_str(), desc_the.c_str(), key.c_str(),
                    condition.c_str());
3815:         }
3816:         else if (feat_is_gate(feat))
3817:         {
3818:             const string key = _esc_cmd_to_str(stair_dir);
3819:             if (feat == DNGN_ENTER_HELL)
3820:             {
3821:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3822:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3823:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3824:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3825:             }
3826:             else
3827:             {
3828:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3829:                                       ? T_("enter") : T_("exit");
3830:                 const string condition =
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
3837:                     T_("\nWhile standing here, you can %1$s through %2$s "
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
3846:         long_desc +=
3847:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3848:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3849:     }
3850:     else if (feat == DNGN_ENTER_SHOP)
3851:     {
3852:         long_desc += make_stringf_p(
3853:                 T_("\nWhile standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key."),
3854:                 desc.c_str(),
3855:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3856:     }
3857:     else if (feat == DNGN_TRANSPORTER)
3858:     {
3859:         long_desc += make_stringf_p(
3860:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3861:                 desc_the.c_str(),
3862:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
```

当前中文模板：
站在这里时，%4$s你可以按<w>%3$s</w>键通过%2$s%1$s。

输入还原：None

独立判断与参数还原：例站在这里时，如果你有足够的符文，你可以按<w>></w>键通过佐特入口进入。动作位于路线后，条件已移到句首，两个分支无重复通过。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-04 — ok


### stable

完整英文：
```text

While standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish after you do so.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3533}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                    T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
                    "after you do so."),
                    feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());
3511:                 const command_type look_dir =
3512:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3513:                                          ? CMD_MAP_PREV_LEVEL
3514:                                          : CMD_MAP_NEXT_LEVEL;
3515:                 long_desc +=
3516:                     make_stringf(T_(" You can view the location it leads to by "
3517:                                  "examining it with <w>%s</w> and pressing "
3518:                                  "<w>%s</w>."),
3519:                                  command_to_string(CMD_DISPLAY_MAP).c_str(),
3520:                                  command_to_string(look_dir).c_str());
3521:             }
3522:         }
3523:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3524:         {
3525:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3526:                                           "pulled as deep as Abyss:%d.)"),
3527:                                       abyss_default_depth(true));
3528:         }
3529:         else if (feat_is_portal(feat)
3530:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3531:         {
3532:             long_desc += make_stringf_p(
3533:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3534:                     "after you do so."),
3535:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3536:                     desc_the.c_str(),
3537:                     _esc_cmd_to_str(stair_dir).c_str());
3538:         }
3539:         else if (feat_is_gate(feat))
3540:         {
3541:             const string key = _esc_cmd_to_str(stair_dir);
3542:             if (feat == DNGN_ENTER_HELL)
3543:             {
3544:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3545:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3546:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3547:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3548:             }
3549:             else
3550:             {
3551:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3552:                                       ? T_("enter") : T_("exit");
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
```

当前中文模板：
站在这里时，你可以按<w>%3$s</w>键%1$s进入%2$s；进入后它就会消失。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish after you do so.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3810}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                    T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
                    "after you do so."),
                    feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());
3788:                 const command_type look_dir =
3789:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3790:                                          ? CMD_MAP_PREV_LEVEL
3791:                                          : CMD_MAP_NEXT_LEVEL;
3792:                 long_desc +=
3793:                     make_stringf(T_(" You can view the location it leads to by "
3794:                                  "examining it with <w>%s</w> and pressing "
3795:                                  "<w>%s</w>."),
3796:                                  command_to_string(CMD_DISPLAY_MAP).c_str(),
3797:                                  command_to_string(look_dir).c_str());
3798:             }
3799:         }
3800:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3801:         {
3802:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3803:                                           "pulled as deep as Abyss:%d.)"),
3804:                                       abyss_default_depth(true));
3805:         }
3806:         else if (feat_is_portal(feat)
3807:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3808:         {
3809:             long_desc += make_stringf_p(
3810:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3811:                     "after you do so."),
3812:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3813:                     desc_the.c_str(),
3814:                     _esc_cmd_to_str(stair_dir).c_str());
3815:         }
3816:         else if (feat_is_gate(feat))
3817:         {
3818:             const string key = _esc_cmd_to_str(stair_dir);
3819:             if (feat == DNGN_ENTER_HELL)
3820:             {
3821:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3822:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3823:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3824:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3825:             }
3826:             else
3827:             {
3828:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3829:                                       ? T_("enter") : T_("exit");
3830:                 const string condition =
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
```

当前中文模板：
站在这里时，你可以按<w>%3$s</w>键%1$s进入%2$s；进入后它就会消失。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-05 — ok


### stable

完整英文：
```text

While standing here, you can enter %1$s with the <w>%2$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3583}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
                desc_the.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
3569:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3570:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3571:     }
3572:     else if (feat == DNGN_ENTER_SHOP)
3573:     {
3574:         long_desc += make_stringf(
3575:                 T_("\nWhile standing here, you can enter <w>%s</w> with "
3576:                 "the <w>%s</w> key."),
3577:                 desc.c_str(),
3578:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3579:     }
3580:     else if (feat == DNGN_TRANSPORTER)
3581:     {
3582:         long_desc += make_stringf_p(
3583:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3584:                 desc_the.c_str(),
3585:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3586:     }
3587:
3588:     // mention that permanent trees are usually flammable
3589:     // (except for autumnal trees in Wucad Mu's Monastery)
3590:     if (feat_is_flammable(feat) && !is_temp_terrain(pos) && in_bounds(pos)
3591:         && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
3592:     {
3593:         if (feat == DNGN_TREE)
3594:             long_desc += "\n" + getLongDescription("tree burning");
3595:         else if (feat == DNGN_MANGROVE)
3596:             long_desc += "\n" + getLongDescription("mangrove burning");
3597:         else if (feat == DNGN_DEMONIC_TREE)
3598:             long_desc += "\n" + getLongDescription("demonic tree burning");
3599:     }
3600:
3601:     if (feat_is_door(feat) && feat != DNGN_BROKEN_DOOR && feat != DNGN_BROKEN_CLEAR_DOOR)
3602:     {
3603:         const bool openable = feat_is_closed_door(feat);
3604:         const bool sealed = feat_is_sealed(feat);
3605:
3606:         long_desc += make_stringf(
3607:             T_("\nWhile adjacent to it, you can %s%s it by pressing the "
```

当前中文模板：
站在这里时，你可以按<w>%2$s</w>键进入%1$s。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can enter %1$s with the <w>%2$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3860}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
                desc_the.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
3846:         long_desc +=
3847:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3848:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3849:     }
3850:     else if (feat == DNGN_ENTER_SHOP)
3851:     {
3852:         long_desc += make_stringf_p(
3853:                 T_("\nWhile standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key."),
3854:                 desc.c_str(),
3855:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3856:     }
3857:     else if (feat == DNGN_TRANSPORTER)
3858:     {
3859:         long_desc += make_stringf_p(
3860:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3861:                 desc_the.c_str(),
3862:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3863:     }
3864:     else if (feat == DNGN_PURIFIED_MUTATION_CATALYST)
3865:     {
3866:         if (you.religion == GOD_ZIN)
3867:         {
3868:             long_desc += T_("\nYour adherence to the laws of Zin forbids you from using "
3869:                             "such a device.");
3870:         }
3871:         else if (you.form == transformation::death)
3872:             long_desc += T_("\nYou must first come back to life before you may mutate.");
3873:         else if (you.is_lifeless_undead()
3874:              || you.get_mutation_level(MUT_MUTATION_RESISTANCE) == 3)
3875:         {
3876:             long_desc += T_("\nThis is completely useless to you, as you cannot mutate.");
3877:         }
3878:         else
3879:         {
3880:             long_desc += make_stringf_p(
3881:                       T_("<w>\nWhile standing here, you can crack open %1$s with "
3882:                          "the</w> <cyan>%2$s</cyan> <w>key</w>."), desc_the.c_str(),
3883:                        command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3884:         }
```

当前中文模板：
站在这里时，你可以按<w>%2$s</w>键进入%1$s。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-06 — ok


### stable


### trunk

完整英文：
```text

While standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3853}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                T_("\nWhile standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key."),
                desc.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
3837:                     T_("\nWhile standing here, you can %1$s through %2$s "
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
3846:         long_desc +=
3847:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3848:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3849:     }
3850:     else if (feat == DNGN_ENTER_SHOP)
3851:     {
3852:         long_desc += make_stringf_p(
3853:                 T_("\nWhile standing here, you can enter <w>%1$s</w> with the <w>%2$s</w> key."),
3854:                 desc.c_str(),
3855:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3856:     }
3857:     else if (feat == DNGN_TRANSPORTER)
3858:     {
3859:         long_desc += make_stringf_p(
3860:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3861:                 desc_the.c_str(),
3862:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3863:     }
3864:     else if (feat == DNGN_PURIFIED_MUTATION_CATALYST)
3865:     {
3866:         if (you.religion == GOD_ZIN)
3867:         {
3868:             long_desc += T_("\nYour adherence to the laws of Zin forbids you from using "
3869:                             "such a device.");
3870:         }
3871:         else if (you.form == transformation::death)
3872:             long_desc += T_("\nYou must first come back to life before you may mutate.");
3873:         else if (you.is_lifeless_undead()
3874:              || you.get_mutation_level(MUT_MUTATION_RESISTANCE) == 3)
3875:         {
3876:             long_desc += T_("\nThis is completely useless to you, as you cannot mutate.");
3877:         }
```

当前中文模板：
站在这里时，你可以按<w>%2$s</w>键进入<w>%1$s</w>。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-07 — objective_error


### stable

完整英文：
```text

While standing here, you can enter <w>%s</w> with the <w>%s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3575}

参数表达式与来源：
```text
long_desc += make_stringf(
                T_("\nWhile standing here, you can enter <w>%s</w> with "
                "the <w>%s</w> key."),
                desc.c_str(),
                command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
3560:                        "with the <w>%3$s</w> key%4$s."),
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
3569:             make_stringf(T_("\nPray here with <w>%s</w> to learn more.\n"),
3570:                          command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3571:     }
3572:     else if (feat == DNGN_ENTER_SHOP)
3573:     {
3574:         long_desc += make_stringf(
3575:                 T_("\nWhile standing here, you can enter <w>%s</w> with "
3576:                 "the <w>%s</w> key."),
3577:                 desc.c_str(),
3578:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3579:     }
3580:     else if (feat == DNGN_TRANSPORTER)
3581:     {
3582:         long_desc += make_stringf_p(
3583:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3584:                 desc_the.c_str(),
3585:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3586:     }
3587:
3588:     // mention that permanent trees are usually flammable
3589:     // (except for autumnal trees in Wucad Mu's Monastery)
3590:     if (feat_is_flammable(feat) && !is_temp_terrain(pos) && in_bounds(pos)
3591:         && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
3592:     {
3593:         if (feat == DNGN_TREE)
3594:             long_desc += "\n" + getLongDescription("tree burning");
3595:         else if (feat == DNGN_MANGROVE)
3596:             long_desc += "\n" + getLongDescription("mangrove burning");
3597:         else if (feat == DNGN_DEMONIC_TREE)
3598:             long_desc += "\n" + getLongDescription("demonic tree burning");
3599:     }
3600:
```

当前中文模板：
站在这里时，你可以按<w>%s</w>键进入<w>%s</w>。

输入还原：None


### trunk

独立判断与参数还原：实参先商店名后按键，译文交换两个未编号占位符，实际把商店名当按键。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "parameter_order", "line": "stable", "english": "\nWhile standing here, you can enter <w>%s</w> with the <w>%s</w> key.", "current_full_zh": "\n站在这里时，你可以按<w>商店名称</w>键进入<w>></w>。", "problem": "实参先商店名后按键，译文交换两个未编号占位符，实际把商店名当按键。", "suggested_zh": "\n站在这里时，你可以按<w>></w>键进入<w>商店名称</w>。", "evidence": "stable describe.cc:3575-3578；trunk :3852-3855 改为编号占位符。", "defect_points": 1}


## D-HERE-08 — ok


### stable

完整英文：
```text

While standing here, you can enter Hell with the <w>%1$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3546}

参数表达式与来源：
```text
const char *sentence = stair_dir == CMD_GO_UPSTAIRS
                    ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
                    : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3524:         {
3525:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3526:                                           "pulled as deep as Abyss:%d.)"),
3527:                                       abyss_default_depth(true));
3528:         }
3529:         else if (feat_is_portal(feat)
3530:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3531:         {
3532:             long_desc += make_stringf_p(
3533:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3534:                     "after you do so."),
3535:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3536:                     desc_the.c_str(),
3537:                     _esc_cmd_to_str(stair_dir).c_str());
3538:         }
3539:         else if (feat_is_gate(feat))
3540:         {
3541:             const string key = _esc_cmd_to_str(stair_dir);
3542:             if (feat == DNGN_ENTER_HELL)
3543:             {
3544:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3545:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3546:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3547:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3548:             }
3549:             else
3550:             {
3551:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3552:                                       ? T_("enter") : T_("exit");
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
3560:                        "with the <w>%3$s</w> key%4$s."),
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
```

当前中文模板：
站在这里时，你可以按<w>%1$s</w>键进入地狱。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can enter Hell with the <w>%1$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3823}

参数表达式与来源：
```text
const char *sentence = stair_dir == CMD_GO_UPSTAIRS
                    ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
                    : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3801:         {
3802:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3803:                                           "pulled as deep as Abyss:%d.)"),
3804:                                       abyss_default_depth(true));
3805:         }
3806:         else if (feat_is_portal(feat)
3807:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3808:         {
3809:             long_desc += make_stringf_p(
3810:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3811:                     "after you do so."),
3812:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3813:                     desc_the.c_str(),
3814:                     _esc_cmd_to_str(stair_dir).c_str());
3815:         }
3816:         else if (feat_is_gate(feat))
3817:         {
3818:             const string key = _esc_cmd_to_str(stair_dir);
3819:             if (feat == DNGN_ENTER_HELL)
3820:             {
3821:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3822:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3823:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3824:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3825:             }
3826:             else
3827:             {
3828:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3829:                                       ? T_("enter") : T_("exit");
3830:                 const string condition =
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
3837:                     T_("\nWhile standing here, you can %1$s through %2$s "
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
```

当前中文模板：
站在这里时，你可以按<w>%1$s</w>键进入地狱。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-09 — ok


### stable

完整英文：
```text

While standing here, you can exit the dungeon with the <w>%s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3492}

参数表达式与来源：
```text
// XX custom messages for other branch entrances/exits?
            long_desc += make_stringf(
                    T_("\nWhile standing here, you can exit the dungeon "
                    "with the <w>%s</w> key."),
                    _esc_cmd_to_str(stair_dir).c_str());
3470:         long_desc += marker_desc;
3471:
3472:     // Display branch descriptions on the entries to those branches.
3473:     if (feat_is_stair(feat))
3474:     {
3475:         for (branch_iterator it; it; ++it)
3476:         {
3477:             if (it->entry_stairs == feat)
3478:             {
3479:                 long_desc += "\n";
3480:                 long_desc += getLongDescription(it->shortname);
3481:                 break;
3482:             }
3483:         }
3484:         const auto stair_dir = feat_stair_direction(feat);
3485:
3486:         // it seems like there must be some way to refactor all this stuff so
3487:         // it's cleaner...
3488:         if (feat == DNGN_EXIT_DUNGEON)
3489:         {
3490:             // XX custom messages for other branch entrances/exits?
3491:             long_desc += make_stringf(
3492:                     T_("\nWhile standing here, you can exit the dungeon "
3493:                     "with the <w>%s</w> key."),
3494:                     _esc_cmd_to_str(stair_dir).c_str());
3495:         }
3496:         else if (feat_is_staircase(feat) || feat_is_escape_hatch(feat))
3497:         {
3498:             long_desc += make_stringf(
3499:                     T_("\nWhile standing here, you can traverse %s "
3500:                     "with the <w>%s</w> key."),
3501:                     desc_the.c_str(),
3502:                     _esc_cmd_to_str(stair_dir).c_str());
3503:
3504:             if (is_unknown_stair(pos))
3505:             {
3506:                 long_desc += T_(" You have not yet explored it and cannot tell "
3507:                              "where it leads.");
3508:             }
3509:             else
3510:             {
3511:                 const command_type look_dir =
3512:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3513:                                          ? CMD_MAP_PREV_LEVEL
3514:                                          : CMD_MAP_NEXT_LEVEL;
3515:                 long_desc +=
3516:                     make_stringf(T_(" You can view the location it leads to by "
```

当前中文模板：
站在这里时，你可以按<w>%s</w>键离开地牢。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can exit the dungeon with the <w>%s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3770}

参数表达式与来源：
```text
// XX custom messages for other branch entrances/exits?
            long_desc += make_stringf(
                    T_("\nWhile standing here, you can exit the dungeon "
                    "with the <w>%s</w> key."),
                    _esc_cmd_to_str(stair_dir).c_str());
3748:         long_desc += marker_desc;
3749:
3750:     // Display branch descriptions on the entries to those branches.
3751:     if (feat_is_stair(feat))
3752:     {
3753:         for (branch_iterator it; it; ++it)
3754:         {
3755:             if (it->entry_stairs == feat)
3756:             {
3757:                 long_desc += "\n";
3758:                 long_desc += getLongDescription(it->shortname);
3759:                 break;
3760:             }
3761:         }
3762:         const auto stair_dir = feat_stair_direction(feat);
3763:
3764:         // it seems like there must be some way to refactor all this stuff so
3765:         // it's cleaner...
3766:         if (feat == DNGN_EXIT_DUNGEON)
3767:         {
3768:             // XX custom messages for other branch entrances/exits?
3769:             long_desc += make_stringf(
3770:                     T_("\nWhile standing here, you can exit the dungeon "
3771:                     "with the <w>%s</w> key."),
3772:                     _esc_cmd_to_str(stair_dir).c_str());
3773:         }
3774:         else if (feat_is_staircase(feat) || feat_is_escape_hatch(feat))
3775:         {
3776:             long_desc += make_stringf_p(
3777:                     T_("\nWhile standing here, you can traverse %1$s with the <w>%2$s</w> key."),
3778:                     desc_the.c_str(),
3779:                     _esc_cmd_to_str(stair_dir).c_str());
3780:
3781:             if (is_unknown_stair(pos))
3782:             {
3783:                 long_desc += T_(" You have not yet explored it and cannot tell "
3784:                              "where it leads.");
3785:             }
3786:             else
3787:             {
3788:                 const command_type look_dir =
3789:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3790:                                          ? CMD_MAP_PREV_LEVEL
3791:                                          : CMD_MAP_NEXT_LEVEL;
3792:                 long_desc +=
3793:                     make_stringf(T_(" You can view the location it leads to by "
3794:                                  "examining it with <w>%s</w> and pressing "
```

当前中文模板：
站在这里时，你可以按<w>%s</w>键离开地牢。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-10 — ok


### stable

完整英文：
```text

While standing here, you can exit to Hell with the <w>%1$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3545}

参数表达式与来源：
```text
const char *sentence = stair_dir == CMD_GO_UPSTAIRS
                    ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
                    : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3523:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3524:         {
3525:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3526:                                           "pulled as deep as Abyss:%d.)"),
3527:                                       abyss_default_depth(true));
3528:         }
3529:         else if (feat_is_portal(feat)
3530:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3531:         {
3532:             long_desc += make_stringf_p(
3533:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3534:                     "after you do so."),
3535:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3536:                     desc_the.c_str(),
3537:                     _esc_cmd_to_str(stair_dir).c_str());
3538:         }
3539:         else if (feat_is_gate(feat))
3540:         {
3541:             const string key = _esc_cmd_to_str(stair_dir);
3542:             if (feat == DNGN_ENTER_HELL)
3543:             {
3544:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3545:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3546:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3547:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3548:             }
3549:             else
3550:             {
3551:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3552:                                       ? T_("enter") : T_("exit");
3553:                 const string condition =
3554:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3555:                     ? T_(" if you have enough runes") : "";
3556:                 // Keep the route inside the complete sentence so the localized
3557:                 // action keeps its own word order.
3558:                 long_desc += make_stringf_p(
3559:                     T_("\nWhile standing here, you can %1$s through %2$s "
3560:                        "with the <w>%3$s</w> key%4$s."),
3561:                     action.c_str(), desc_the.c_str(), key.c_str(),
3562:                     condition.c_str());
3563:             }
3564:         }
3565:     }
3566:     else if (feat_is_altar(feat))
3567:     {
3568:         long_desc +=
```

当前中文模板：
站在这里时，你可以按<w>%1$s</w>键离开这里，前往地狱。

输入还原：None


### trunk

完整英文：
```text

While standing here, you can exit to Hell with the <w>%1$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3822}

参数表达式与来源：
```text
const char *sentence = stair_dir == CMD_GO_UPSTAIRS
                    ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
                    : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3800:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3801:         {
3802:             long_desc += make_stringf(T_("\n(If you entered the Abyss now, you could be "
3803:                                           "pulled as deep as Abyss:%d.)"),
3804:                                       abyss_default_depth(true));
3805:         }
3806:         else if (feat_is_portal(feat)
3807:             || feat == DNGN_ENTER_ZIGGURAT) // augh this is technically a gate
3808:         {
3809:             long_desc += make_stringf_p(
3810:                     T_("\nWhile standing here, you can %1$senter %2$s with the <w>%3$s</w> key; it will vanish "
3811:                     "after you do so."),
3812:                     feat == DNGN_ENTER_TROVE ? T_("try to ") : "",
3813:                     desc_the.c_str(),
3814:                     _esc_cmd_to_str(stair_dir).c_str());
3815:         }
3816:         else if (feat_is_gate(feat))
3817:         {
3818:             const string key = _esc_cmd_to_str(stair_dir);
3819:             if (feat == DNGN_ENTER_HELL)
3820:             {
3821:                 const char *sentence = stair_dir == CMD_GO_UPSTAIRS
3822:                     ? N_("\nWhile standing here, you can exit to Hell with the <w>%1$s</w> key.")
3823:                     : N_("\nWhile standing here, you can enter Hell with the <w>%1$s</w> key.");
3824:                 long_desc += make_stringf_p(T_(sentence), key.c_str());
3825:             }
3826:             else
3827:             {
3828:                 const string action = stair_dir == CMD_GO_DOWNSTAIRS
3829:                                       ? T_("enter") : T_("exit");
3830:                 const string condition =
3831:                     (feat == DNGN_ENTER_ZOT || feat == DNGN_EXIT_VAULTS)
3832:                     ? T_(" if you have enough runes") : "";
3833:                 // Keep the route in the complete sentence. Translating an
3834:                 // independent "through" fragment would force English word
3835:                 // order on the localized enter/exit action.
3836:                 long_desc += make_stringf_p(
3837:                     T_("\nWhile standing here, you can %1$s through %2$s "
3838:                        "with the <w>%3$s</w> key%4$s."),
3839:                     action.c_str(), desc_the.c_str(), key.c_str(),
3840:                     condition.c_str());
3841:             }
3842:         }
3843:     }
3844:     else if (feat_is_altar(feat))
3845:     {
```

当前中文模板：
站在这里时，你可以按<w>%1$s</w>键离开这里，前往地狱。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-11 — ok


### stable


### trunk

完整英文：
```text

While standing here, you can traverse %1$s with the <w>%2$s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3777}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                    T_("\nWhile standing here, you can traverse %1$s with the <w>%2$s</w> key."),
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());
3755:             if (it->entry_stairs == feat)
3756:             {
3757:                 long_desc += "\n";
3758:                 long_desc += getLongDescription(it->shortname);
3759:                 break;
3760:             }
3761:         }
3762:         const auto stair_dir = feat_stair_direction(feat);
3763:
3764:         // it seems like there must be some way to refactor all this stuff so
3765:         // it's cleaner...
3766:         if (feat == DNGN_EXIT_DUNGEON)
3767:         {
3768:             // XX custom messages for other branch entrances/exits?
3769:             long_desc += make_stringf(
3770:                     T_("\nWhile standing here, you can exit the dungeon "
3771:                     "with the <w>%s</w> key."),
3772:                     _esc_cmd_to_str(stair_dir).c_str());
3773:         }
3774:         else if (feat_is_staircase(feat) || feat_is_escape_hatch(feat))
3775:         {
3776:             long_desc += make_stringf_p(
3777:                     T_("\nWhile standing here, you can traverse %1$s with the <w>%2$s</w> key."),
3778:                     desc_the.c_str(),
3779:                     _esc_cmd_to_str(stair_dir).c_str());
3780:
3781:             if (is_unknown_stair(pos))
3782:             {
3783:                 long_desc += T_(" You have not yet explored it and cannot tell "
3784:                              "where it leads.");
3785:             }
3786:             else
3787:             {
3788:                 const command_type look_dir =
3789:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3790:                                          ? CMD_MAP_PREV_LEVEL
3791:                                          : CMD_MAP_NEXT_LEVEL;
3792:                 long_desc +=
3793:                     make_stringf(T_(" You can view the location it leads to by "
3794:                                  "examining it with <w>%s</w> and pressing "
3795:                                  "<w>%s</w>."),
3796:                                  command_to_string(CMD_DISPLAY_MAP).c_str(),
3797:                                  command_to_string(look_dir).c_str());
3798:             }
3799:         }
3800:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3801:         {
```

当前中文模板：
站在这里时，你可以按<w>%2$s</w>键通过%1$s。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-12 — objective_error


### stable

完整英文：
```text

While standing here, you can traverse %s with the <w>%s</w> key.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3499}

参数表达式与来源：
```text
long_desc += make_stringf(
                    T_("\nWhile standing here, you can traverse %s "
                    "with the <w>%s</w> key."),
                    desc_the.c_str(),
                    _esc_cmd_to_str(stair_dir).c_str());
3477:             if (it->entry_stairs == feat)
3478:             {
3479:                 long_desc += "\n";
3480:                 long_desc += getLongDescription(it->shortname);
3481:                 break;
3482:             }
3483:         }
3484:         const auto stair_dir = feat_stair_direction(feat);
3485:
3486:         // it seems like there must be some way to refactor all this stuff so
3487:         // it's cleaner...
3488:         if (feat == DNGN_EXIT_DUNGEON)
3489:         {
3490:             // XX custom messages for other branch entrances/exits?
3491:             long_desc += make_stringf(
3492:                     T_("\nWhile standing here, you can exit the dungeon "
3493:                     "with the <w>%s</w> key."),
3494:                     _esc_cmd_to_str(stair_dir).c_str());
3495:         }
3496:         else if (feat_is_staircase(feat) || feat_is_escape_hatch(feat))
3497:         {
3498:             long_desc += make_stringf(
3499:                     T_("\nWhile standing here, you can traverse %s "
3500:                     "with the <w>%s</w> key."),
3501:                     desc_the.c_str(),
3502:                     _esc_cmd_to_str(stair_dir).c_str());
3503:
3504:             if (is_unknown_stair(pos))
3505:             {
3506:                 long_desc += T_(" You have not yet explored it and cannot tell "
3507:                              "where it leads.");
3508:             }
3509:             else
3510:             {
3511:                 const command_type look_dir =
3512:                     feat_stair_direction(feat) == CMD_GO_UPSTAIRS
3513:                                          ? CMD_MAP_PREV_LEVEL
3514:                                          : CMD_MAP_NEXT_LEVEL;
3515:                 long_desc +=
3516:                     make_stringf(T_(" You can view the location it leads to by "
3517:                                  "examining it with <w>%s</w> and pressing "
3518:                                  "<w>%s</w>."),
3519:                                  command_to_string(CMD_DISPLAY_MAP).c_str(),
3520:                                  command_to_string(look_dir).c_str());
3521:             }
3522:         }
3523:         else if (feat == DNGN_ENTER_ABYSS || feat == DNGN_EXIT_THROUGH_ABYSS)
3524:         {
```

当前中文模板：
站在这里时，你可以按<w>%s</w>键穿越%s。

输入还原：None


### trunk

独立判断与参数还原：实参先楼梯描述后按键，中文却先输出按键，未编号导致互换。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "parameter_order", "line": "stable", "english": "\nWhile standing here, you can traverse %s with the <w>%s</w> key.", "current_full_zh": "\n站在这里时，你可以按<w>向下的楼梯</w>键穿越>。", "problem": "实参先楼梯描述后按键，中文却先输出按键，未编号导致互换。", "suggested_zh": "\n站在这里时，你可以按<w>></w>键通过向下的楼梯。", "evidence": "stable describe.cc:3499-3502；trunk 使用编号参数。", "defect_points": 1}


## D-HERE-13 — ok


### stable

完整英文：
```text

You are here.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3635}

参数表达式与来源：
```text
if (pos == you.pos() && you.on_current_level)
        long_desc += T_("\nYou are here.");

```

当前中文模板：
你在这里。

输入还原：
你在这里。


### trunk

完整英文：
```text

You are here.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3957}

参数表达式与来源：
```text
if (pos == you.pos() && you.on_current_level)
        long_desc += T_("\nYou are here.");

```

当前中文模板：
你在这里。

输入还原：
你在这里。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-14 — ok


### stable

完整英文：
```text
 (here)
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 490}

参数表达式与来源：
```text
if (item && item->pos == you.pos())
            return t + T_(" (here)");

```

当前中文模板：（此处）

输入还原：（此处）


### trunk

完整英文：
```text
 (here)
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 471}

参数表达式与来源：
```text
if (item && item->pos == you.pos())
            return t + T_(" (here)");

```

当前中文模板：（此处）

输入还原：（此处）

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-15 — ok


### stable

完整英文：
```text
 probably won't like it if you switch allegiance. If you want to take the risk, you can convert here by pressing <w>></w> while standing on the altar. Doing so will enter you into service of a random god, who will grant you some additional piety in thanks.
```

生产调用：{'path': 'crawl-ref/source/hints.cc', 'line': 2639}

参数表达式与来源：
```text
ostr << T_("This particular altar is so ancient that you cannot "
                        "make out which god it is dedicated to, and ")
                     << god_name(you.religion)
                     << T_(" probably won't like it if you switch allegiance. If "
                        "you want to take the risk, you can convert here by "
                        "pressing <w>></w> while standing on the altar. Doing "
                        "so will enter you into service of a random god, who "
                        "will grant you some additional piety in thanks.");

```

当前中文模板： 可能不会喜欢你改换门庭。如果你愿意冒这个险，你可以站在祭坛上按<w>></w>来改信。这样做会让你投入一位随机神祇的麾下，祂会赐予你一些额外的虔诚作为感谢。

输入还原： 可能不会喜欢你改换门庭。如果你愿意冒这个险，你可以站在祭坛上按<w>></w>来改信。这样做会让你投入一位随机神祇的麾下，祂会赐予你一些额外的虔诚作为感谢。


### trunk

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-16 — objective_error


### stable

完整英文：
```text
%s%s here.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 3048}

参数表达式与来源：
```text
mprf(channel, T_("%s%s here."), prefix, feat.c_str());
3026:     case DNGN_FLOOR:
3027:     case DNGN_MUD:
3028:         return;
3029:
3030:     case DNGN_ENTER_SHOP:
3031:         prefix = T_("There is an entrance to ");
3032:         break;
3033:
3034:     default:
3035:         break;
3036:     }
3037:
3038:     feat = feature_description_at(you.pos(), true, DESC_A);
3039:     if (feat.empty())
3040:         return;
3041:
3042:     msg_channel_type channel = MSGCH_EXAMINE;
3043:
3044:     // Messages for water/lava are too spammy use a status light instead.
3045:     if (feat_is_water(grid) || feat_is_lava(grid))
3046:         return;
3047:
3048:     mprf(channel, T_("%s%s here."), prefix, feat.c_str());
3049:     if (grid == DNGN_ENTER_GAUNTLET)
3050:         mprf(MSGCH_EXAMINE, T_("Beware, the minotaur awaits!"));
3051:     else if (feat_is_fountain(grid) || feat_is_food(grid))
3052:         _walk_on_decor(grid);
3053: }
3054:
3055: decor_cache_result decor_cache_lookup(const string &messageLookup)
3056: {
3057:     string line = getMiscString(get_form(you.form)->wiz_name + " " + messageLookup);
3058:     if (!line.empty())
3059:         return {line, decor_cache_hit::form};
3060:
3061:     // The species prefix must stay the English raw plain name: the
3062:     // canonical decorlines keys (EN and ZH) are English, so a localized
3063:     // display name (what raw=false returns under ZH) can never match and
3064:     // every species cache key would silently fall back to the generic
3065:     // line below.
3066:     line = getMiscString(species::name(you.species,
3067:                                        species::SPNAME_PLAIN,
3068:                                        true)
3069:                          + " " + messageLookup);
3070:     if (!line.empty())
```

当前中文模板：%s%s。

输入还原：None


### trunk

独立判断与参数还原：prefix 的精确键带尾空格且中文为空；另一个不带尾空格的已译键不能匹配，生产会混入英文。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "untranslated_parameter", "line": "stable", "english": "%s%s here.", "current_full_zh": "There is 向下的楼梯。 / There is an entrance to 商店名称。", "problem": "prefix 的精确键带尾空格且中文为空；另一个不带尾空格的已译键不能匹配，生产会混入英文。", "suggested_zh": "这里有向下的楼梯。 / 这里有通往商店名称的入口。", "evidence": "stable directn.cc:3021,3031,3048；source.txt:27258、12664 的带空格键为空。", "defect_points": 1}


## D-HERE-17 — ok


### stable

完整英文：
```text
<cyan>Here:</cyan>
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1965}

参数表达式与来源：
```text
if (mon_desc.empty())
            out << T_("<cyan>Here:</cyan>") << " ";

```

当前中文模板：<cyan>这里：</cyan>

输入还原：<cyan>这里：</cyan>


### trunk

完整英文：
```text
<cyan>Here:</cyan>
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1990}

参数表达式与来源：
```text
if (mon_desc.empty())
            out << T_("<cyan>Here:</cyan>") << " ";

```

当前中文模板：<cyan>这里：</cyan>

输入还原：<cyan>这里：</cyan>

独立判断与参数还原：青色位置标题，不是普通提示；保留这里：及冒号。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-18 — readability


### stable


### trunk

完整英文：
```text
<cyan>Here:</cyan> %s
```

生产调用：{'path': 'crawl-ref/source/viewmap.cc', 'line': 459}

参数表达式与来源：
```text
if (!mon.empty())
        mprf(MSGCH_EXAMINE, T_("<cyan>Here:</cyan> %s"), uppercase_first(mon).c_str());
437:                 s.add_glyph(gly);
438:         return s;
439:     }
440: };
441:
442: #ifdef USE_TILE
443: static void _describe_cell(const map_control_state &m_state)
444: {
445:     const coord_def &cpos = m_state.lpos.pos;
446:     const map_cell &cell = env.map_knowledge(cpos);
447:     msgwin_clear_temporary();
448:     mprf(MSGCH_PROMPT, T_("Press: ? - help, v - describe, . - travel"));
449:
450:     // If viewing the level we are on, player-centered coordinates.
451:     if (Options.monster_item_view_coordinates && m_state.on_level)
452:     {
453:         const coord_def relpos = cpos - you.pos();
454:         mprf(MSGCH_PLAIN, T_("Location (%d, %d)"), relpos.x, -relpos.y);
455:     }
456:
457:     const string mon = cell_monster_description(cpos);
458:     if (!mon.empty())
459:         mprf(MSGCH_EXAMINE, T_("<cyan>Here:</cyan> %s"), uppercase_first(mon).c_str());
460:
461:     const string items = cell_items_description(cpos);
462:     if (!items.empty())
463:         mprf(MSGCH_EXAMINE, "%s", items.c_str());
464:
465:     string desc = feature_description(cell.feat()).c_str();
466:     if (!desc.empty())
467:         mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
468:
469:     const cloud_type cloud = cell.cloud();
470:     if (cloud != CLOUD_NONE)
471:     {
472:         mprf(MSGCH_EXAMINE, T_("There is a cloud of %s here."),
473:              cloud_type_name(cloud).c_str());
474:     }
475:
476:     flush_prev_message();
477: }
478: #endif
479:
480: #ifndef USE_TILE_LOCAL
481: // Describe the symbol displayed for a cell, unless it's boring terrain.
```

当前中文模板：<cyan>此处：</cyan> %s

输入还原：None

独立判断与参数还原：与同类地图标题的“这里：”不一致，可统一；仍是标题，不应强改成散文。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "consistency", "line": "trunk", "english": "<cyan>Here:</cyan> %s", "current_full_zh": "<cyan>此处：</cyan> 兽人", "problem": "与同类地图标题的“这里：”不一致，可统一；仍是标题，不应强改成散文。", "suggested_zh": "<cyan>这里：</cyan> 兽人", "evidence": "trunk {'path': 'crawl-ref/source/viewmap.cc', 'line': 459}", "defect_points": 0}


## D-HERE-19 — ok


### stable

完整英文：
```text
<cyan>Here:</cyan> %s

```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1955}

参数表达式与来源：
```text
if (!mon_desc.empty())
        out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1933: {
1934:     string desc = cell_floor_description(target(), boring_too);
1935:     if (desc.empty())
1936:         return;
1937:
1938: #ifdef DEBUG_DIAGNOSTICS
1939:     // [ds] Be more verbose in debug mode.
1940:     if (you.wizard)
1941:         _debug_describe_feature_at(target());
1942:     else
1943: #endif
1944:
1945:     mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
1946: }
1947:
1948: // Get a brief of monster, items, and features in a given cell.
1949: string get_square_desc(const coord_def &pos)
1950: {
1951:     ostringstream out;
1952:
1953:     string mon_desc = cell_monster_description(pos);
1954:     if (!mon_desc.empty())
1955:         out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1956:
1957:     string desc = cell_items_description(pos);
1958:     if (!desc.empty())
1959:         out << desc << "\n";
1960:
1961:     desc = cell_floor_description(pos, false);
1962:     if (!desc.empty())
1963:     {
1964:         if (mon_desc.empty())
1965:             out << T_("<cyan>Here:</cyan>") << " ";
1966:         out << desc << "\n";
1967:     }
1968:
1969:     desc = _get_cloud_desc(pos);
1970:     if (!desc.empty())
1971:         out << desc << "\n";
1972:
1973:     if (out.tellp() > 0)
1974:         out << T_("\n(Right-click to examine)");
1975:
1976:     return out.str();
1977: }
```

当前中文模板：<cyan>这里：</cyan> %s


输入还原：None


### trunk

完整英文：
```text
<cyan>Here:</cyan> %s

```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1980}

参数表达式与来源：
```text
if (!mon_desc.empty())
        out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1958: {
1959:     string desc = cell_floor_description(target(), boring_too);
1960:     if (desc.empty())
1961:         return;
1962:
1963: #ifdef DEBUG_DIAGNOSTICS
1964:     // [ds] Be more verbose in debug mode.
1965:     if (you.wizard)
1966:         _debug_describe_feature_at(target());
1967:     else
1968: #endif
1969:
1970:     mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
1971: }
1972:
1973: // Get a brief of monster, items, and features in a given cell.
1974: string get_square_desc(const coord_def &pos)
1975: {
1976:     ostringstream out;
1977:
1978:     string mon_desc = cell_monster_description(pos);
1979:     if (!mon_desc.empty())
1980:         out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1981:
1982:     string desc = cell_items_description(pos);
1983:     if (!desc.empty())
1984:         out << desc << "\n";
1985:
1986:     desc = cell_floor_description(pos, false);
1987:     if (!desc.empty())
1988:     {
1989:         if (mon_desc.empty())
1990:             out << T_("<cyan>Here:</cyan>") << " ";
1991:         out << desc << "\n";
1992:     }
1993:
1994:     desc = _get_cloud_desc(pos);
1995:     if (!desc.empty())
1996:         out << desc << "\n";
1997:
1998:     if (out.tellp() > 0)
1999:         out << T_("\n(Right-click to examine)");
2000:
2001:     return out.str();
2002: }
```

当前中文模板：<cyan>这里：</cyan> %s


输入还原：None

独立判断与参数还原：青色位置标题后接说明及换行，保留标题形式与冒号。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-20 — ok


### stable

完整英文：
```text
<cyan>Item%1$s here:</cyan> %2$s.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1908}

参数表达式与来源：
```text
return make_stringf_p(T_("<cyan>Item%1$s here:</cyan> %2$s."),
                        items.size() > 1 ? "s" : "",
                        item_message(items).c_str());
1886:         return;
1887:
1888:     const item_def* item = top_item_at(target());
1889:     if (!item)
1890:         return;
1891:
1892:     // FIXME: remove the duplication with print_items_description().
1893:     mprf(MSGCH_PROMPT, T_("%s: %s"),
1894:          target_prefix ? target_prefix : T_("Aim"),
1895:          menu_colour_item_name(*item, DESC_A).c_str());
1896: }
1897:
1898: string cell_items_description(const coord_def& pos)
1899: {
1900:     if (!in_bounds(pos))
1901:         return "";
1902:
1903:     auto items = const_item_list_on_square(you.visible_igrd(pos));
1904:
1905:     if (items.empty())
1906:         return "";
1907:
1908:     return make_stringf_p(T_("<cyan>Item%1$s here:</cyan> %2$s."),
1909:                         items.size() > 1 ? "s" : "",
1910:                         item_message(items).c_str());
1911: }
1912:
1913: void direction_chooser::print_items_description() const
1914: {
1915:     string items = cell_items_description(target());
1916:
1917:     if (items.empty())
1918:         return;
1919:
1920:     mprf(MSGCH_FLOOR_ITEMS, "%s", items.c_str());
1921: }
1922:
1923: string cell_floor_description(const coord_def& pos, bool boring_too)
1924: {
1925:     const dungeon_feature_type feat = env.grid(pos);
1926:     if (!boring_too && feat == DNGN_FLOOR)
1927:         return "";
1928:
1929:     return feature_description_at(pos, true);
1930: }
1931:
1932: void direction_chooser::print_floor_description(bool boring_too) const
```

当前中文模板：<cyan>此处物品：</cyan> %2$s。

输入还原：None


### trunk

完整英文：
```text
<cyan>Item%1$s here:</cyan> %2$s.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1933}

参数表达式与来源：
```text
return make_stringf_p(T_("<cyan>Item%1$s here:</cyan> %2$s."),
                        items.size() > 1 ? "s" : "",
                        item_message(items).c_str());
1911:          menu_colour_item_name(*item, DESC_A).c_str());
1912: }
1913:
1914: string cell_items_description(const coord_def& pos)
1915: {
1916:     if (!in_bounds(pos))
1917:         return "";
1918:
1919:     vector<item_def> remembered;
1920:     vector<const item_def *> items;
1921:     if (env.map_knowledge(pos).visible())
1922:         items = const_item_list_on_square(you.visible_igrd(pos));
1923:     else
1924:     {
1925:         remembered = item_list_in_stash(pos);
1926:         for (const item_def &item : remembered)
1927:             items.push_back(&item);
1928:     }
1929:
1930:     if (items.empty())
1931:         return "";
1932:
1933:     return make_stringf_p(T_("<cyan>Item%1$s here:</cyan> %2$s."),
1934:                         items.size() > 1 ? "s" : "",
1935:                         item_message(items).c_str());
1936: }
1937:
1938: void direction_chooser::print_items_description() const
1939: {
1940:     string items = cell_items_description(target());
1941:
1942:     if (items.empty())
1943:         return;
1944:
1945:     mprf(MSGCH_FLOOR_ITEMS, "%s", items.c_str());
1946: }
1947:
1948: string cell_floor_description(const coord_def& pos, bool boring_too)
1949: {
1950:     const dungeon_feature_type feat = env.grid(pos);
1951:     if (!boring_too && feat == DNGN_FLOOR)
1952:         return "";
1953:
1954:     return feature_description_at(pos, true);
1955: }
1956:
1957: void direction_chooser::print_floor_description(bool boring_too) const
```

当前中文模板：<cyan>此处物品：</cyan> %2$s。

输入还原：None

独立判断与参数还原：物品枚举标题，%1$s 是英语复数后缀而中文省略，%2$s 为物品全名列表，例<cyan>此处物品：</cyan> 3支标枪。可成句。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-21 — ok


### stable


### trunk

完整英文：
```text
<w>
While standing here, you can crack open %1$s with the</w> <cyan>%2$s</cyan> <w>key</w>.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 3881}

参数表达式与来源：
```text
long_desc += make_stringf_p(
                      T_("<w>\nWhile standing here, you can crack open %1$s with "
                         "the</w> <cyan>%2$s</cyan> <w>key</w>."), desc_the.c_str(),
                       command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3859:         long_desc += make_stringf_p(
3860:                 T_("\nWhile standing here, you can enter %1$s with the <w>%2$s</w> key."),
3861:                 desc_the.c_str(),
3862:                 command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3863:     }
3864:     else if (feat == DNGN_PURIFIED_MUTATION_CATALYST)
3865:     {
3866:         if (you.religion == GOD_ZIN)
3867:         {
3868:             long_desc += T_("\nYour adherence to the laws of Zin forbids you from using "
3869:                             "such a device.");
3870:         }
3871:         else if (you.form == transformation::death)
3872:             long_desc += T_("\nYou must first come back to life before you may mutate.");
3873:         else if (you.is_lifeless_undead()
3874:              || you.get_mutation_level(MUT_MUTATION_RESISTANCE) == 3)
3875:         {
3876:             long_desc += T_("\nThis is completely useless to you, as you cannot mutate.");
3877:         }
3878:         else
3879:         {
3880:             long_desc += make_stringf_p(
3881:                       T_("<w>\nWhile standing here, you can crack open %1$s with "
3882:                          "the</w> <cyan>%2$s</cyan> <w>key</w>."), desc_the.c_str(),
3883:                        command_to_string(CMD_GO_DOWNSTAIRS).c_str());
3884:         }
3885:     }
3886:     else if (feat == DNGN_SPIKE_LAUNCHER)
3887:     {
3888:         map_active_feature_marker* mark = env.markers.get_active_feature_at(pos, DNGN_SPIKE_LAUNCHER);
3889:         if (mark)
3890:         {
3891:             dice_def dmg = zap_damage(ZAP_SPIKE_LAUNCHER, mark->power, mark->owner != MID_PLAYER, false);
3892:             long_desc += make_stringf(T_("\nIt does %dd%d damage."), dmg.num, dmg.size);
3893:         }
3894:     }
3895:     else if (feat_is_dragon_vein(feat))
3896:     {
3897:         long_desc += make_stringf(T_("\nIt inflicts %s damage when channelled."),
3898:                         spell_damage_string(dragon_vein_to_spell(feat),
3899:                                             false, calc_spell_power(SPELL_DRAGON_VEINS)).c_str());
3900:     }
3901:     else if (feat == DNGN_ICE_THORNS)
3902:     {
3903:         map_terrain_change_marker* mark = env.markers.get_terrain_change_at(pos, TERRAIN_CHANGE_ICE_THORNS);
3904:         if (mark)
3905:         {
```

当前中文模板：<w>
站在这里时，你可以按</w> <cyan>%2$s</cyan> <w>键敲开%1$s</w>。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-22 — ok


### stable

完整英文：
```text
<yellow>A demonic rune of Zot can be found here... for a price.</yellow>
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 2670}

参数表达式与来源：
```text
"<yellow>A demonic rune of Zot can be found here... " ..
              "for a price.</yellow>"

```

当前中文模板：<yellow>这里能找到佐特恶魔符文……只要你付得起代价。</yellow>

输入还原：<yellow>这里能找到佐特恶魔符文……只要你付得起代价。</yellow>


### trunk

完整英文：
```text
<yellow>A demonic rune of Zot can be found here... for a price.</yellow>
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 2670}

参数表达式与来源：
```text
"<yellow>A demonic rune of Zot can be found here... " ..
              "for a price.</yellow>"

```

当前中文模板：<yellow>这里能找到佐特恶魔符文……只要你付得起代价。</yellow>

输入还原：<yellow>这里能找到佐特恶魔符文……只要你付得起代价。</yellow>

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-23 — ok


### stable

完整英文：
```text
A forested plane collides here with a resounding crunch!
```

生产调用：{'path': 'crawl-ref/source/spl-summoning.cc', 'line': 1546}

参数表达式与来源：
```text
mpr(T_("A forested plane collides here with a resounding crunch!"));

```

当前中文模板：一个森林遍布的位面在这里碰撞，发出了响亮的嘎吱声！

输入还原：一个森林遍布的位面在这里碰撞，发出了响亮的嘎吱声！


### trunk

完整英文：
```text
A forested plane collides here with a resounding crunch!
```

生产调用：{'path': 'crawl-ref/source/spl-summoning.cc', 'line': 1482}

参数表达式与来源：
```text
mpr(T_("A forested plane collides here with a resounding crunch!"));

```

当前中文模板：一个森林遍布的位面在这里碰撞，发出了响亮的嘎吱声！

输入还原：一个森林遍布的位面在这里碰撞，发出了响亮的嘎吱声！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-24 — ok


### stable

完整英文：
```text
A powerful Pandemonium lord resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 2669}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")

```

当前中文模板：一位强大的万魔殿领主盘踞于此。

输入还原：一位强大的万魔殿领主盘踞于此。

完整英文：
```text
A powerful Pandemonium lord resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 287}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")

```

当前中文模板：一位强大的万魔殿领主盘踞于此。

输入还原：一位强大的万魔殿领主盘踞于此。


### trunk

完整英文：
```text
A powerful Pandemonium lord resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 2669}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")

```

当前中文模板：一位强大的万魔殿领主盘踞于此。

输入还原：一位强大的万魔殿领主盘踞于此。

完整英文：
```text
A powerful Pandemonium lord resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 287}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")

```

当前中文模板：一位强大的万魔殿领主盘踞于此。

输入还原：一位强大的万魔殿领主盘踞于此。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-25 — ok


### stable

完整英文：
```text
Any gift you received here would fall and be lost!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 1996}

参数表达式与来源：
```text
case ABIL_OKAWARU_GIFT_WEAPON:
    case ABIL_OKAWARU_GIFT_ARMOUR:
        if (feat_eliminates_items(env.grid(you.pos())))
            return fail(T_("Any gift you received here would fall and be lost!"));

```

当前中文模板：你在这里收到的任何礼物都会掉落丢失！

输入还原：你在这里收到的任何礼物都会掉落丢失！


### trunk

完整英文：
```text
Any gift you received here would fall and be lost!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2088}

参数表达式与来源：
```text
case ABIL_OKAWARU_GIFT_WEAPON:
    case ABIL_OKAWARU_GIFT_ARMOUR:
        if (feat_eliminates_items(env.grid(you.pos())))
            return fail(T_("Any gift you received here would fall and be lost!"));

```

当前中文模板：你在这里收到的任何礼物都会掉落丢失！

输入还原：你在这里收到的任何礼物都会掉落丢失！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-26 — ok


### stable

完整英文：
```text
Anything you acquire here would fall and be lost!
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3081}

参数表达式与来源：
```text
mpr(T_("Anything you acquire here would fall and be lost!"));

```

当前中文模板：你在这里获取的任何东西都会掉落并丢失！

输入还原：你在这里获取的任何东西都会掉落并丢失！


### trunk

完整英文：
```text
Anything you acquire here would fall and be lost!
```

生产调用：{'path': 'crawl-ref/source/item-use.cc', 'line': 3212}

参数表达式与来源：
```text
mpr(T_("Anything you acquire here would fall and be lost!"));

```

当前中文模板：你在这里获取的任何东西都会掉落并丢失！

输入还原：你在这里获取的任何东西都会掉落并丢失！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-27 — ok


### stable

完整英文：
```text
Could not pick up %s here; Ignore %s?
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 858}

参数表达式与来源：
```text
// XX [A] doesn't make sense for items being picked up only because
            // of an =g inscription
            const string prompt =
                make_stringf(T_("Could not pick up %s here; Ignore %s?"),
                             wishlist.c_str(),
                             tried_pickup == 1 ? T_("it") : T_("them"));
836:             stop_delay();
837:     }
838:
839:     // Greedy explore has no good way to deal with an item that we can't
840:     // pick up, so the only thing to do is to stop.
841:     if (tried_pickup && you.running == RMODE_EXPLORE_GREEDY)
842:     {
843:         if (explore_stopped_pos == you.pos())
844:         {
845:             vector<item_def*> to_pickup;
846:             for (stack_iterator si(you.pos()); si; ++si)
847:             {
848:                 if (item_needs_autopickup(*si))
849:                     to_pickup.push_back(&*si);
850:             }
851:
852:             string wishlist = comma_separated_fn(to_pickup.begin(), to_pickup.end(),
853:                     [] (const item_def* item) { return item->name(DESC_A); });
854:
855:             // XX [A] doesn't make sense for items being picked up only because
856:             // of an =g inscription
857:             const string prompt =
858:                 make_stringf(T_("Could not pick up %s here; Ignore %s?"),
859:                              wishlist.c_str(),
860:                              tried_pickup == 1 ? T_("it") : T_("them"));
861:
862:             // Make Escape => 'n' and stop run.
863:             explicit_keymap map;
864:             map[ESCAPE] = 'n';
865:             map[CONTROL('G')] = 'n';
866:             map[' '] = 'y';
867:
868:             const bool allow_always = to_pickup.size() == 1 && !is_artefact(*to_pickup[0]);
869:
870:             // If response is Yes (1) or Always (2), mark items for no pickup
871:             // If the response is Always, remove the item from autopickup
872:             // Otherwise, stop autoexplore.
873:             int response = yesno(prompt.c_str(), true, 'n', true, false,
874:                                  false, &map, true, allow_always);
875:             switch (response)
876:             {
877:                 case 2:
878:                 {
879:                     vector<string> ap_disabled;
880:                     for (stack_iterator si(you.pos()); si; ++si)
881:                     {
882:                         if (!item_needs_autopickup(*si)
```

当前中文模板：在这里无法拾取%s；忽略%s吗？

输入还原：None


### trunk

完整英文：
```text
Could not pick up %s here; Ignore %s?
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 854}

参数表达式与来源：
```text
// XX [A] doesn't make sense for items being picked up only because
            // of an =g inscription
            const string prompt =
                make_stringf(T_("Could not pick up %s here; Ignore %s?"),
                             wishlist.c_str(),
                             tried_pickup == 1 ? T_("it") : T_("them"));
832:             stop_delay();
833:     }
834:
835:     // Greedy explore has no good way to deal with an item that we can't
836:     // pick up, so the only thing to do is to stop.
837:     if (tried_pickup && you.running == RMODE_EXPLORE_GREEDY)
838:     {
839:         if (explore_stopped_pos == you.pos())
840:         {
841:             vector<item_def*> to_pickup;
842:             for (stack_iterator si(you.pos()); si; ++si)
843:             {
844:                 if (item_needs_autopickup(*si))
845:                     to_pickup.push_back(&*si);
846:             }
847:
848:             string wishlist = comma_separated_fn(to_pickup.begin(), to_pickup.end(),
849:                     [] (const item_def* item) { return item->name(DESC_A); });
850:
851:             // XX [A] doesn't make sense for items being picked up only because
852:             // of an =g inscription
853:             const string prompt =
854:                 make_stringf(T_("Could not pick up %s here; Ignore %s?"),
855:                              wishlist.c_str(),
856:                              tried_pickup == 1 ? T_("it") : T_("them"));
857:
858:             // Make Escape => 'n' and stop run.
859:             explicit_keymap map;
860:             map[ESCAPE] = 'n';
861:             map[CONTROL('G')] = 'n';
862:             map[' '] = 'y';
863:
864:             const bool allow_always = to_pickup.size() == 1 && !is_artefact(*to_pickup[0]);
865:
866:             // If response is Yes (1) or Always (2), mark items for no pickup
867:             // If the response is Always, remove the item from autopickup
868:             // Otherwise, stop autoexplore.
869:             int response = yesno(prompt.c_str(), true, 'n', true, false,
870:                                  false, &map, true, allow_always);
871:             switch (response)
872:             {
873:                 case 2:
874:                 {
875:                     vector<string> ap_disabled;
876:                     for (stack_iterator si(you.pos()); si; ++si)
877:                     {
878:                         if (!item_needs_autopickup(*si)
```

当前中文模板：在这里无法拾取%s；忽略%s吗？

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-28 — ok


### stable

完整英文：
```text
Here
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 933}

参数表达式与来源：
```text
const string target_prefix = T_("Here");

```

当前中文模板：这里

输入还原：这里


### trunk

完整英文：
```text
Here
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 916}

参数表达式与来源：
```text
args.target_prefix = "Here";

```

当前中文模板：这里

输入还原：这里

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-29 — ok


### stable

完整英文：
```text
Here, spectral monks perform complicated, martial routines; they fade quickly.
```

生产调用：{'path': 'crawl-ref/source/dat/des/portals/wizlab.des', 'line': 363}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("Here, spectral monks perform complicated, martial routines; they fade quickly."), "talk_visual")

```

当前中文模板：幽魂僧侣在这里演练复杂的武术套路；他们很快便消散了。

输入还原：幽魂僧侣在这里演练复杂的武术套路；他们很快便消散了。


### trunk

完整英文：
```text
Here, spectral monks perform complicated, martial routines; they fade quickly.
```

生产调用：{'path': 'crawl-ref/source/dat/des/portals/wizlab.des', 'line': 363}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("Here, spectral monks perform complicated, martial routines; they fade quickly."), "talk_visual")

```

当前中文模板：幽魂僧侣在这里演练复杂的武术套路；他们很快便消散了。

输入还原：幽魂僧侣在这里演练复杂的武术套路；他们很快便消散了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-30 — ok


### stable

完整英文：
```text
In a burst of heat and light, you briefly surge upwards...but you can't rise from here.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 773}

参数表达式与来源：
```text
mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));

```

当前中文模板：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

输入还原：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。


### trunk

完整英文：
```text
In a burst of heat and light, you briefly surge upwards...but you can't rise from here.
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 789}

参数表达式与来源：
```text
mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));

```

当前中文模板：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

输入还原：在一阵热与光的爆发中，你短暂地向上冲去……但无法从这里升起。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-31 — ok


### stable

完整英文：
```text
It would be unwise to walk in here.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 598}

参数表达式与来源：
```text
if (!quiet)
            mpr(T_("It would be unwise to walk in here."));

```

当前中文模板：走进这里是不明智的。

输入还原：走进这里是不明智的。


### trunk

完整英文：
```text
It would be unwise to walk in here.
```

生产调用：{'path': 'crawl-ref/source/player.cc', 'line': 658}

参数表达式与来源：
```text
if (!quiet)
            mpr(T_("It would be unwise to walk in here."));

```

当前中文模板：走进这里是不明智的。

输入还原：走进这里是不明智的。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-32 — ok


### stable

完整英文：
```text
Items here: %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 945}

参数表达式与来源：
```text
// Stack summary case
    if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
        mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
923:     origin_set(you.pos());
924:
925:     ostream& strm = msg::streams(MSGCH_FLOOR_ITEMS);
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
```

当前中文模板：此处物品：%s。

输入还原：None


### trunk

完整英文：
```text
Items here: %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 945}

参数表达式与来源：
```text
// Stack summary case
    if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
        mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
923:     origin_set(you.pos());
924:
925:     ostream& strm = msg::streams(MSGCH_FLOOR_ITEMS);
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
```

当前中文模板：此处物品：%s。

输入还原：None

独立判断与参数还原：items.size 达摘要阈值的枚举摘要，例此处物品：3支标枪；一把匕首。可保留冒号和物品列表。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-33 — ok


### stable

完整英文：
```text
Monsters! Monsters everywhere! You have to get out of here!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 386}

参数表达式与来源：
```text
if (horror_level >= HORROR_LVL_OVERWHELMING)
        mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));

```

当前中文模板：怪物！到处都是怪物！你必须离开这里！

输入还原：怪物！到处都是怪物！你必须离开这里！


### trunk

完整英文：
```text
Monsters! Monsters everywhere! You have to get out of here!
```

生产调用：{'path': 'crawl-ref/source/player-reacts.cc', 'line': 388}

参数表达式与来源：
```text
if (horror_level >= HORROR_LVL_OVERWHELMING)
        mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));

```

当前中文模板：怪物！到处都是怪物！你必须离开这里！

输入还原：怪物！到处都是怪物！你必须离开这里！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-34 — ok


### stable


### trunk

完整英文：
```text
Now pick up the Orb and get out of here!
```

生产调用：{'path': 'crawl-ref/source/spl-transloc.cc', 'line': 1688}

参数表达式与来源：
```text
start_orb_run(CHAPTER_ANGERED_PANDEMONIUM, T_("Now pick up the Orb and get out of here!"));

```

当前中文模板：现在拾起佐特宝珠，逃出去！

输入还原：现在拾起佐特宝珠，逃出去！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-35 — ok


### stable


### trunk

完整英文：
```text
Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?
```

生产调用：{'path': 'crawl-ref/source/god-prayer.cc', 'line': 132}

参数表达式与来源：
```text
const string prompt = form_at_risk && gear_at_risk
            ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
            : form_at_risk
                ? T_("Praying here may force you to leave your current form. Pray anyway?")
                : T_("Praying here may force you to remove some of your equipment. Pray anyway?");

```

当前中文模板：在此祈祷可能迫使你解除当前形态或卸下部分装备。仍要祈祷吗？

输入还原：在此祈祷可能迫使你解除当前形态或卸下部分装备。仍要祈祷吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-36 — ok


### stable


### trunk

完整英文：
```text
Praying here may force you to leave your current form. Pray anyway?
```

生产调用：{'path': 'crawl-ref/source/god-prayer.cc', 'line': 134}

参数表达式与来源：
```text
const string prompt = form_at_risk && gear_at_risk
            ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
            : form_at_risk
                ? T_("Praying here may force you to leave your current form. Pray anyway?")
                : T_("Praying here may force you to remove some of your equipment. Pray anyway?");

```

当前中文模板：在此祈祷可能迫使你解除当前形态。仍要祈祷吗？

输入还原：在此祈祷可能迫使你解除当前形态。仍要祈祷吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-37 — ok


### stable


### trunk

完整英文：
```text
Praying here may force you to remove some of your equipment. Pray anyway?
```

生产调用：{'path': 'crawl-ref/source/god-prayer.cc', 'line': 135}

参数表达式与来源：
```text
const string prompt = form_at_risk && gear_at_risk
            ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
            : form_at_risk
                ? T_("Praying here may force you to leave your current form. Pray anyway?")
                : T_("Praying here may force you to remove some of your equipment. Pray anyway?");

```

当前中文模板：在此祈祷可能迫使你卸下部分装备。仍要祈祷吗？

输入还原：在此祈祷可能迫使你卸下部分装备。仍要祈祷吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-38 — ok


### stable

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 2990}

参数表达式与来源：
```text
if (!can_travel_interlevel())
            mpr(T_("Sorry, you can't auto-travel out of here."));

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5243}

参数表达式与来源：
```text
mpr(T_("Sorry, you can't auto-travel out of here."));

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。


### trunk

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 3028}

参数表达式与来源：
```text
if (!can_travel_interlevel())
            mpr(T_("Sorry, you can't auto-travel out of here."));

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。

完整英文：
```text
Sorry, you can't auto-travel out of here.
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5351}

参数表达式与来源：
```text
mpr(T_("Sorry, you can't auto-travel out of here."));

```

当前中文模板：抱歉，你无法自动旅行离开这里。

输入还原：抱歉，你无法自动旅行离开这里。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-39 — ok


### stable

完整英文：
```text
Tap here or press Back to view the score summary.
```

生产调用：{'path': 'crawl-ref/source/invent.cc', 'line': 1549}

参数表达式与来源：
```text
const string continue_text = string("<bg:brown><white>")
            + T_("Tap here or press Back to view the score summary.")
            + "</white></bg:brown>";

```

当前中文模板：点按此处或按返回键查看战绩。

输入还原：点按此处或按返回键查看战绩。


### trunk

完整英文：
```text
Tap here or press Back to view the score summary.
```

生产调用：{'path': 'crawl-ref/source/invent.cc', 'line': 1571}

参数表达式与来源：
```text
const string continue_text = string("<bg:brown><white>")
            + T_("Tap here or press Back to view the score summary.")
            + "</white></bg:brown>";

```

当前中文模板：点按此处或按返回键查看战绩。

输入还原：点按此处或按返回键查看战绩。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-40 — ok


### stable

完整英文：
```text
The air here is shimmering with an eerie glow.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 24}

参数表达式与来源：
```text
Mnoleg = "The air here is shimmering with an eerie glow.",

```

当前中文模板：此处的空气闪烁着诡异的光芒。

输入还原：此处的空气闪烁着诡异的光芒。


### trunk

完整英文：
```text
The air here is shimmering with an eerie glow.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 24}

参数表达式与来源：
```text
Mnoleg = "The air here is shimmering with an eerie glow.",

```

当前中文模板：此处的空气闪烁着诡异的光芒。

输入还原：此处的空气闪烁着诡异的光芒。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-41 — ok


### stable

完整英文：
```text
The demonic rune of Zot may be found here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 285}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))

```

当前中文模板：这里或许能找到佐特恶魔符文。

输入还原：这里或许能找到佐特恶魔符文。


### trunk

完整英文：
```text
The demonic rune of Zot may be found here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 285}

参数表达式与来源：
```text
crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))

```

当前中文模板：这里或许能找到佐特恶魔符文。

输入还原：这里或许能找到佐特恶魔符文。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-42 — ok


### stable

完整英文：
```text
The dungeon contains a number of natural obstacles such as shafts, which lead one to three levels down. Once you know the shaft is there, you can safely step over it.
If you want to jump down there, use <w>></w> to do so. Be warned that getting back here might be difficult.
```

生产调用：{'path': 'crawl-ref/source/hints.cc', 'line': 2503}

参数表达式与来源：
```text
case DNGN_TRAP_SHAFT:
        ostr << T_("The dungeon contains a number of natural obstacles such "
                "as shafts, which lead one to three levels down. Once you "
                "know the shaft is there, you can safely step over it.\n"
                "If you want to jump down there, use <w>></w> to do so. "
                "Be warned that getting back here might be difficult.");

```

当前中文模板：地牢中有许多天然障碍，比如陷坑，会让你掉下一到三层。一旦你知道陷坑在那里，就可以安全地从上面走过。
如果想跳下去，请按<w>></w>。但要注意，返回这里可能会很困难。

输入还原：地牢中有许多天然障碍，比如陷坑，会让你掉下一到三层。一旦你知道陷坑在那里，就可以安全地从上面走过。
如果想跳下去，请按<w>></w>。但要注意，返回这里可能会很困难。


### trunk

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-43 — ok


### stable

完整英文：
```text
The mighty Pandemonium lord %s resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 38}

参数表达式与来源：
```text
crawl.t_("The mighty Pandemonium lord %s resides here."),
16:
17: : crawl_require('dlua/vault.lua')
18:
19: # The generic pan lord warning message.
20:
21: {{
22: function pan_lord_epilogue(name)
23:     local msgs = {
24:         Mnoleg = "The air here is shimmering with an eerie glow.",
25:         ['Lom Lobon'] = "You sense a powerful magical presence. It is not pleased.",
26:         Cerebov = "Searing heat pours from the floors and walls of this place.",
27:         ['Gloorx Vloq'] = "Shadowy figures dance across your vision."
28:     }
29:     local runes = {
30:         Mnoleg = "glowing",
31:         ['Lom Lobon'] = "magical",
32:         Cerebov = "fiery",
33:         ['Gloorx Vloq'] = "dark"
34:     }
35:
36:     crawl.mpr(crawl.t_(msgs[name]), "warning")
37:     crawl.mpr(string.format(
38:         crawl.t_("The mighty Pandemonium lord %s resides here."),
39:         crawl.t_(name)), "warning")
40:     -- Counterpart to branch_rune_desc from lookup-help.cc
41:     crawl.mpr(string.format(crawl.t_("They guard the %s rune of Zot."),
42:                            crawl.t_(runes[name])))
43:     crawl.take_note(util.i18n_format_or_english(
44:         "Entered the realm of %s.", name))
45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', "")
46: end
47:
48: function pan_lord_setup(_G, name)
49:     _G.tags("unrand")
50:
51:     local monsters = {
52:         Mnoleg = "sin beast band w:100 / " ..
53:                  "neqoxec w:250 / chaos spawn w:250 / " ..
54:                  "zykzyl w:300 / tormentor / " ..
55:                  "tentacled monstrosity / protean progenitor band / " ..
56:                  "very ugly thing / glass eye band / " ..
57:                  "golden eye band / eye of devastation / "..
58:                  "shining eye / demonspawn corrupter",
59:         ['Lom Lobon'] = "hellwing w:100 / sixfirhy w:100 / " ..
60:                  "smoke demon w:200 / nekomata w:50 / green death w:200 / " ..
```

当前中文模板：强大的万魔殿领主%s盘踞于此。

输入还原：None


### trunk

完整英文：
```text
The mighty Pandemonium lord %s resides here.
```

生产调用：{'path': 'crawl-ref/source/dat/des/branches/pan.des', 'line': 38}

参数表达式与来源：
```text
crawl.t_("The mighty Pandemonium lord %s resides here."),
16:
17: : crawl_require('dlua/vault.lua')
18:
19: # The generic pan lord warning message.
20:
21: {{
22: function pan_lord_epilogue(name)
23:     local msgs = {
24:         Mnoleg = "The air here is shimmering with an eerie glow.",
25:         ['Lom Lobon'] = "You sense a powerful magical presence. It is not pleased.",
26:         Cerebov = "Searing heat pours from the floors and walls of this place.",
27:         ['Gloorx Vloq'] = "Shadowy figures dance across your vision."
28:     }
29:     local runes = {
30:         Mnoleg = "glowing",
31:         ['Lom Lobon'] = "magical",
32:         Cerebov = "fiery",
33:         ['Gloorx Vloq'] = "dark"
34:     }
35:
36:     crawl.mpr(crawl.t_(msgs[name]), "warning")
37:     crawl.mpr(string.format(
38:         crawl.t_("The mighty Pandemonium lord %s resides here."),
39:         crawl.t_(name)), "warning")
40:     -- Counterpart to branch_rune_desc from lookup-help.cc
41:     crawl.mpr(string.format(crawl.t_("They guard the %s rune of Zot."),
42:                            crawl.t_(runes[name])))
43:     crawl.take_note(util.i18n_format_or_english(
44:         "Entered the realm of %s.", name))
45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', "")
46: end
47:
48: function pan_lord_setup(_G, name)
49:     _G.tags("unrand")
50:
51:     local monsters = {
52:         Mnoleg = "sin beast band w:100 / " ..
53:                  "neqoxec w:250 / chaos spawn w:250 / " ..
54:                  "zykzyl w:300 / tormentor / " ..
55:                  "tentacled monstrosity / protean progenitor band / " ..
56:                  "very ugly thing / glass eye band / " ..
57:                  "golden eye band / eye of devastation / "..
58:                  "shining eye / demonspawn corrupter",
59:         ['Lom Lobon'] = "hellwing w:100 / sixfirhy w:100 / " ..
60:                  "smoke demon w:200 / nekomata w:50 / green death w:200 / " ..
```

当前中文模板：强大的万魔殿领主%s盘踞于此。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-44 — ok


### stable

完整英文：
```text
There are many items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 952}

参数表达式与来源：
```text
else
        strm << (T_("There are many items here.")) << endl;

```

当前中文模板：这里有很多物品。

输入还原：这里有很多物品。


### trunk

完整英文：
```text
There are many items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 952}

参数表达式与来源：
```text
else
        strm << (T_("There are many items here.")) << endl;

```

当前中文模板：这里有很多物品。

输入还原：这里有很多物品。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-45 — ok


### stable

完整英文：
```text
There are no items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1526}

参数表达式与来源：
```text
if (o == NON_ITEM)
        mpr(T_("There are no items here."));

```

当前中文模板：这里没有任何物品。

输入还原：这里没有任何物品。


### trunk

完整英文：
```text
There are no items here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1492}

参数表达式与来源：
```text
if (o == NON_ITEM)
        mpr(T_("There are no items here."));

```

当前中文模板：这里没有任何物品。

输入还原：这里没有任何物品。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-46 — ok


### stable

完整英文：
```text
There are no objects that can be picked up here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1545}

参数表达式与来源：
```text
if (num_items == 0)
            mpr(T_("There are no objects that can be picked up here."));

```

当前中文模板：这里没有可以捡起的物品。

输入还原：这里没有可以捡起的物品。


### trunk

完整英文：
```text
There are no objects that can be picked up here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1511}

参数表达式与来源：
```text
if (num_items == 0)
            mpr(T_("There are no objects that can be picked up here."));

```

当前中文模板：这里没有可以捡起的物品。

输入还原：这里没有可以捡起的物品。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-47 — ok


### stable

完整英文：
```text
There are no souls to scour here; only the pathetic idols of powerless gods.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 1450}

参数表达式与来源：
```text
// First check invalid locations
    if (player_in_branch(BRANCH_TEMPLE))
        return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");

```

当前中文模板：这里没有可收割的灵魂；只有无能之神的可怜偶像。

输入还原：这里没有可收割的灵魂；只有无能之神的可怜偶像。


### trunk

完整英文：
```text
There are no souls to scour here; only the pathetic idols of powerless gods.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 1541}

参数表达式与来源：
```text
// First check invalid locations
    if (player_in_branch(BRANCH_TEMPLE))
        return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");

```

当前中文模板：这里没有可收割的灵魂；只有无能之神的可怜偶像。

输入还原：这里没有可收割的灵魂；只有无能之神的可怜偶像。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-48 — ok


### stable

完整英文：
```text
There are no souls worth scouring here.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 1452}

参数表达式与来源：
```text
else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
        return T_("There are no souls worth scouring here.");

```

当前中文模板：这里没有值得收割的灵魂。

输入还原：这里没有值得收割的灵魂。


### trunk

完整英文：
```text
There are no souls worth scouring here.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 1543}

参数表达式与来源：
```text
else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
        return T_("There are no souls worth scouring here.");

```

当前中文模板：这里没有值得收割的灵魂。

输入还原：这里没有值得收割的灵魂。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-49 — ok


### stable

完整英文：
```text
There are several objects here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1547}

参数表达式与来源：
```text
else
            mpr(T_("There are several objects here."));

```

当前中文模板：这里有几样物品。

输入还原：这里有几样物品。


### trunk

完整英文：
```text
There are several objects here.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1513}

参数表达式与来源：
```text
else
            mpr(T_("There are several objects here."));

```

当前中文模板：这里有几样物品。

输入还原：这里有几样物品。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-50 — ok


### stable


### trunk

完整英文：
```text
There is %s here.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 3068}

参数表达式与来源：
```text
mprf(channel, grid == DNGN_ENTER_SHOP
         ? T_("There is an entrance to %s here.")
         : T_("There is %s here."), feat.c_str());
3046:     return features;
3047: }
3048:
3049: void describe_floor()
3050: {
3051:     dungeon_feature_type grid = env.map_knowledge(you.pos()).feat();
3052:
3053:     if (grid == DNGN_FLOOR || grid == DNGN_MUD)
3054:         return;
3055:
3056:     const string feat = feature_description_at(you.pos(), true, DESC_A);
3057:     if (feat.empty())
3058:         return;
3059:
3060:     msg_channel_type channel = MSGCH_EXAMINE;
3061:
3062:     // Messages for water/lava are too spammy use a status light instead.
3063:     if (feat_is_water(grid) || feat_is_lava(grid))
3064:         return;
3065:
3066:     mprf(channel, grid == DNGN_ENTER_SHOP
3067:          ? T_("There is an entrance to %s here.")
3068:          : T_("There is %s here."), feat.c_str());
3069:     if (grid == DNGN_ENTER_GAUNTLET)
3070:         mprf(MSGCH_EXAMINE, T_("Beware, the minotaur awaits!"));
3071:     else if (feat_is_fountain(grid) || feat_is_food(grid))
3072:         _walk_on_decor(grid);
3073: }
3074:
3075: decor_cache_result decor_cache_lookup(const string &messageLookup)
3076: {
3077:     string line = getMiscString(get_form(you.form)->wiz_name + " " + messageLookup);
3078:     if (!line.empty())
3079:         return {line, decor_cache_hit::form};
3080:
3081:     // The species prefix must stay the English raw plain name: the
3082:     // canonical decorlines keys (EN and ZH) are English, so a localized
3083:     // display name (what raw=false returns under ZH) can never match and
3084:     // every species cache key would silently fall back to the generic
3085:     // line below.
3086:     line = getMiscString(species::name(you.species,
3087:                                        species::SPNAME_PLAIN,
3088:                                        true)
3089:                          + " " + messageLookup);
3090:     if (!line.empty())
```

当前中文模板：这里有%s。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-51 — ok


### stable

完整英文：
```text
There is a cloud of %s here.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 3760}

参数表达式与来源：
```text
out << make_stringf(T_("There is a cloud of %s here."),
                                cloud->cloud_name(true).c_str());
3738:         areas.emplace_back(T_("is covered in magical glow"));
3739:     if (disjunction_haloed(where))
3740:         areas.emplace_back(T_("is bathed in translocational energy"));
3741:     if (is_blasphemy(where))
3742:         areas.emplace_back(T_("within Yredelemnul's grip"));
3743:     if (env.map_knowledge(where).flags & MAP_CORRODING
3744:         && !feat_is_wall(env.map_knowledge(where).feat()))
3745:     {
3746:         areas.emplace_back(T_("is covered in acidic slime"));
3747:     }
3748:
3749:     if (!areas.empty())
3750:     {
3751:         out << make_stringf(T_("This square %s."),
3752:              comma_separated_line(areas.begin(), areas.end()).c_str());
3753:     }
3754:
3755:     if (cloud_struct* cloud = cloud_at(where))
3756:     {
3757:         if (out.tellp() > 0)
3758:             out << "\n";
3759:
3760:         out << make_stringf(T_("There is a cloud of %s here."),
3761:                                 cloud->cloud_name(true).c_str());
3762:     }
3763:
3764:     return out.str();
3765: }
3766:
3767: #ifdef DEBUG_DIAGNOSTICS
3768: static void _debug_describe_feature_at(const coord_def &where)
3769: {
3770:     const string feature_desc = feature_description_at(where, true);
3771:     string marker;
3772:     if (map_marker *mark = env.markers.find(where, MAT_ANY))
3773:     {
3774:         string desc = mark->debug_describe();
3775:         if (desc.empty())
3776:             desc = "?";
3777:         marker = " (" + desc + ")";
3778:     }
3779:     const string traveldest = _stair_destination_description(where);
3780:     string height_desc;
3781:     if (env.heightmap)
3782:         height_desc = make_stringf(" (height: %d)", (*env.heightmap)(where));
3783:     const dungeon_feature_type feat = env.grid(where);
```

当前中文模板：这里有一团%s。

输入还原：None


### trunk

完整英文：
```text
There is a cloud of %s here.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 3776}

参数表达式与来源：
```text
out << make_stringf(T_("There is a cloud of %s here."),
                                cloud->cloud_name(true).c_str());
3754:         areas.emplace_back(T_("is bathed in translocational energy"));
3755:     if (is_blasphemy(where))
3756:         areas.emplace_back(T_("within Yredelemnul's grip"));
3757:     if (env.map_knowledge(where).flags & MAP_CORRODING
3758:         && !feat_is_wall(env.map_knowledge(where).feat()))
3759:     {
3760:         areas.emplace_back(T_("is covered in acidic slime"));
3761:     }
3762:
3763:     if (!areas.empty())
3764:     {
3765:         out << make_stringf(T_("This square %s."),
3766:              comma_separated_line(areas.begin(), areas.end(),
3767:                 Options.language == lang_t::ZH ? T_(",") : T_(" and "),
3768:                 Options.language == lang_t::ZH ? T_(",") : ", ").c_str());
3769:     }
3770:
3771:     if (cloud_struct* cloud = cloud_at(where))
3772:     {
3773:         if (out.tellp() > 0)
3774:             out << "\n";
3775:
3776:         out << make_stringf(T_("There is a cloud of %s here."),
3777:                                 cloud->cloud_name(true).c_str());
3778:     }
3779:
3780:     return out.str();
3781: }
3782:
3783: #ifdef DEBUG_DIAGNOSTICS
3784: static void _debug_describe_feature_at(const coord_def &where)
3785: {
3786:     const string feature_desc = feature_description_at(where, true);
3787:     string marker;
3788:     if (map_marker *mark = env.markers.find(where, MAT_ANY))
3789:     {
3790:         string desc = mark->debug_describe();
3791:         if (desc.empty())
3792:             desc = "?";
3793:         marker = " (" + desc + ")";
3794:     }
3795:     const string traveldest = _stair_destination_description(where);
3796:     string height_desc;
3797:     if (env.heightmap)
3798:         height_desc = make_stringf(" (height: %d)", (*env.heightmap)(where));
3799:     const dungeon_feature_type feat = env.grid(where);
```

当前中文模板：这里有一团%s。

输入还原：None

完整英文：
```text
There is a cloud of %s here.
```

生产调用：{'path': 'crawl-ref/source/viewmap.cc', 'line': 472}

参数表达式与来源：
```text
mprf(MSGCH_EXAMINE, T_("There is a cloud of %s here."),
             cloud_type_name(cloud).c_str());
450:     // If viewing the level we are on, player-centered coordinates.
451:     if (Options.monster_item_view_coordinates && m_state.on_level)
452:     {
453:         const coord_def relpos = cpos - you.pos();
454:         mprf(MSGCH_PLAIN, T_("Location (%d, %d)"), relpos.x, -relpos.y);
455:     }
456:
457:     const string mon = cell_monster_description(cpos);
458:     if (!mon.empty())
459:         mprf(MSGCH_EXAMINE, T_("<cyan>Here:</cyan> %s"), uppercase_first(mon).c_str());
460:
461:     const string items = cell_items_description(cpos);
462:     if (!items.empty())
463:         mprf(MSGCH_EXAMINE, "%s", items.c_str());
464:
465:     string desc = feature_description(cell.feat()).c_str();
466:     if (!desc.empty())
467:         mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
468:
469:     const cloud_type cloud = cell.cloud();
470:     if (cloud != CLOUD_NONE)
471:     {
472:         mprf(MSGCH_EXAMINE, T_("There is a cloud of %s here."),
473:              cloud_type_name(cloud).c_str());
474:     }
475:
476:     flush_prev_message();
477: }
478: #endif
479:
480: #ifndef USE_TILE_LOCAL
481: // Describe the symbol displayed for a cell, unless it's boring terrain.
482: // Return a description, and also (…) if there is something underneath it.
483: static pair<string, string> _describe_top_thing_in_cell(const coord_def &cpos)
484: {
485:     const map_cell &cell = env.map_knowledge(cpos);
486:     string out, feat, item;
487:     const string etc = " (…)";
488:
489:     if (auto mi = cell.monsterinfo())
490:         out = get_monster_equipment_desc(*mi);
491:
492:     if (cell.cloud() != CLOUD_NONE)
493:     {
494:         if (!out.empty())
495:             return {out, etc};
```

当前中文模板：这里有一团%s。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-52 — ok


### stable


### trunk

完整英文：
```text
There is an entrance to %s here.
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 3067}

参数表达式与来源：
```text
mprf(channel, grid == DNGN_ENTER_SHOP
         ? T_("There is an entrance to %s here.")
         : T_("There is %s here."), feat.c_str());
3045:     }
3046:     return features;
3047: }
3048:
3049: void describe_floor()
3050: {
3051:     dungeon_feature_type grid = env.map_knowledge(you.pos()).feat();
3052:
3053:     if (grid == DNGN_FLOOR || grid == DNGN_MUD)
3054:         return;
3055:
3056:     const string feat = feature_description_at(you.pos(), true, DESC_A);
3057:     if (feat.empty())
3058:         return;
3059:
3060:     msg_channel_type channel = MSGCH_EXAMINE;
3061:
3062:     // Messages for water/lava are too spammy use a status light instead.
3063:     if (feat_is_water(grid) || feat_is_lava(grid))
3064:         return;
3065:
3066:     mprf(channel, grid == DNGN_ENTER_SHOP
3067:          ? T_("There is an entrance to %s here.")
3068:          : T_("There is %s here."), feat.c_str());
3069:     if (grid == DNGN_ENTER_GAUNTLET)
3070:         mprf(MSGCH_EXAMINE, T_("Beware, the minotaur awaits!"));
3071:     else if (feat_is_fountain(grid) || feat_is_food(grid))
3072:         _walk_on_decor(grid);
3073: }
3074:
3075: decor_cache_result decor_cache_lookup(const string &messageLookup)
3076: {
3077:     string line = getMiscString(get_form(you.form)->wiz_name + " " + messageLookup);
3078:     if (!line.empty())
3079:         return {line, decor_cache_hit::form};
3080:
3081:     // The species prefix must stay the English raw plain name: the
3082:     // canonical decorlines keys (EN and ZH) are English, so a localized
3083:     // display name (what raw=false returns under ZH) can never match and
3084:     // every species cache key would silently fall back to the generic
3085:     // line below.
3086:     line = getMiscString(species::name(you.species,
3087:                                        species::SPNAME_PLAIN,
3088:                                        true)
3089:                          + " " + messageLookup);
3090:     if (!line.empty())
```

当前中文模板：这里有通往%s的入口。

输入还原：None

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-53 — ok


### stable

完整英文：
```text
There is nothing to wall jump against here.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2272}

参数表达式与来源：
```text
if (!has_targets)
            return fail(T_("There is nothing to wall jump against here."));

```

当前中文模板：这里没有可以蹬墙跳的墙面。

输入还原：这里没有可以蹬墙跳的墙面。

完整英文：
```text
There is nothing to wall jump against here.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 6495}

参数表达式与来源：
```text
mpr(T_("There is nothing to wall jump against here."));

```

当前中文模板：这里没有可以蹬墙跳的墙面。

输入还原：这里没有可以蹬墙跳的墙面。


### trunk

完整英文：
```text
There is nothing to wall jump against here.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2382}

参数表达式与来源：
```text
if (!has_targets)
            return fail(T_("There is nothing to wall jump against here."));

```

当前中文模板：这里没有可以蹬墙跳的墙面。

输入还原：这里没有可以蹬墙跳的墙面。

完整英文：
```text
There is nothing to wall jump against here.
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 6552}

参数表达式与来源：
```text
mpr(T_("There is nothing to wall jump against here."));

```

当前中文模板：这里没有可以蹬墙跳的墙面。

输入还原：这里没有可以蹬墙跳的墙面。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-54 — ok


### stable

完整英文：
```text
There isn't enough space here!
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 4248}

参数表达式与来源：
```text
mpr(T_("There isn't enough space here!"));

```

当前中文模板：这里空间不足！

输入还原：这里空间不足！


### trunk

完整英文：
```text
There isn't enough space here!
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 4430}

参数表达式与来源：
```text
mpr(T_("There isn't enough space here!"));

```

当前中文模板：这里空间不足！

输入还原：这里空间不足！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-55 — ok


### stable

完整英文：
```text
There isn't enough space to grow briars here.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2053}

参数表达式与来源：
```text
if (spaces.empty())
            return fail(T_("There isn't enough space to grow briars here."));

```

当前中文模板：这里没有足够的空间生长荆棘。

输入还原：这里没有足够的空间生长荆棘。


### trunk

完整英文：
```text
There isn't enough space to grow briars here.
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2146}

参数表达式与来源：
```text
if (spaces.empty())
            return fail(T_("There isn't enough space to grow briars here."));

```

当前中文模板：这里没有足够的空间生长荆棘。

输入还原：这里没有足够的空间生长荆棘。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-56 — ok


### stable

完整英文：
```text
There's already a cloud here!
```

生产调用：{'path': 'crawl-ref/source/spl-clouds.cc', 'line': 63}

参数表达式与来源：
```text
mpr(T_("There's already a cloud here!"));

```

当前中文模板：这里已经有一片云雾了！

输入还原：这里已经有一片云雾了！


### trunk

完整英文：
```text
There's already a cloud here!
```

生产调用：{'path': 'crawl-ref/source/spl-clouds.cc', 'line': 69}

参数表达式与来源：
```text
mpr(T_("There's already a cloud here!"));

```

当前中文模板：这里已经有一片云雾了！

输入还原：这里已经有一片云雾了！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-57 — ok


### stable

完整英文：
```text
There's no space to create foxfire here.
```

生产调用：{'path': 'crawl-ref/source/spl-summoning.cc', 'line': 3029}

参数表达式与来源：
```text
mpr(T_("There's no space to create foxfire here."));

```

当前中文模板：这里没有创造狐火的空间。

输入还原：这里没有创造狐火的空间。


### trunk

完整英文：
```text
There's no space to create foxfire here.
```

生产调用：{'path': 'crawl-ref/source/spl-summoning.cc', 'line': 3114}

参数表达式与来源：
```text
mpr(T_("There's no space to create foxfire here."));

```

当前中文模板：这里没有创造狐火的空间。

输入还原：这里没有创造狐火的空间。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-58 — ok


### stable

完整英文：
```text
Things that are here:
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 948}

参数表达式与来源：
```text
mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));

```

当前中文模板：此处有：

输入还原：此处有：


### trunk

完整英文：
```text
Things that are here:
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 948}

参数表达式与来源：
```text
mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));

```

当前中文模板：此处有：

输入还原：此处有：

独立判断与参数还原：items.size>1 且可完整显示时先输出此处有：再输出物品列表；这是列表标题，差异合理，保留冒号。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-59 — ok


### stable

完整英文：
```text
This branch is noisy: sounds don't travel as far here.
```

生产调用：{'path': 'crawl-ref/source/branch.cc', 'line': 336}

参数表达式与来源：
```text
if (noise > 0)
            desc = T_("This branch is noisy: sounds don't travel as far here.");

```

当前中文模板：嘈杂：声音在此处传播得更近。

输入还原：嘈杂：声音在此处传播得更近。


### trunk

完整英文：
```text
This branch is noisy: sounds don't travel as far here.
```

生产调用：{'path': 'crawl-ref/source/branch.cc', 'line': 341}

参数表达式与来源：
```text
if (noise > 0)
            desc = T_("This branch is noisy: sounds don't travel as far here.");

```

当前中文模板：嘈杂：声音在此处传播得更近。

输入还原：嘈杂：声音在此处传播得更近。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-60 — ok


### stable

完整英文：
```text
This branch is unnaturally silent: sounds travel farther here.
```

生产调用：{'path': 'crawl-ref/source/branch.cc', 'line': 338}

参数表达式与来源：
```text
else
            desc = T_("This branch is unnaturally silent: sounds travel farther here.");

```

当前中文模板：异常安静：声音在此处传播得更远。

输入还原：异常安静：声音在此处传播得更远。


### trunk

完整英文：
```text
This branch is unnaturally silent: sounds travel farther here.
```

生产调用：{'path': 'crawl-ref/source/branch.cc', 'line': 343}

参数表达式与来源：
```text
else
            desc = T_("This branch is unnaturally silent: sounds travel farther here.");

```

当前中文模板：异常安静：声音在此处传播得更远。

输入还原：异常安静：声音在此处传播得更远。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-61 — ok


### stable

完整英文：
```text
This particular altar is so ancient that you cannot make out which god it is dedicated to! Converting here by pressing <w>></w> while standing on the altar will enter you into service of a random god, who will grant you some additional piety in thanks.
```

生产调用：{'path': 'crawl-ref/source/hints.cc', 'line': 2613}

参数表达式与来源：
```text
ostr << T_("This particular altar is so ancient that you "
                            "cannot make out which god it is dedicated to! "
                            "Converting here by pressing <w>></w> while "
                            "standing on the altar will enter you into service "
                            "of a random god, who will grant you some "
                            "additional piety in thanks.");

```

当前中文模板：这座祭坛古老得令你无法辨认它供奉哪位神祇！站在祭坛上按<w>></w>改信，会使你投入一位随机神祇的麾下；祂会赐予你一些额外的虔诚作为感谢。

输入还原：这座祭坛古老得令你无法辨认它供奉哪位神祇！站在祭坛上按<w>></w>改信，会使你投入一位随机神祇的麾下；祂会赐予你一些额外的虔诚作为感谢。


### trunk

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-62 — ok


### stable

完整英文：
```text
This screen shows the spells in your spell library. From here you can memorise spells by selecting them, as well as view spell descriptions, search for them, and organize them. As a conjurer, you start with Magic Dart already memorised and three other spells in your library, which you can memorise when you meet their requirements. (To view memorised spells, you can exit this menu and select <w>I</w>.)
```

生产调用：{'path': 'crawl-ref/source/hints.cc', 'line': 1937}

参数表达式与来源：
```text
string m = T_("This screen shows the spells in your spell library. From here "
               "you can memorise spells by selecting them, as well as view "
               "spell descriptions, search for them, and organize them. As a "
               "conjurer, you start with Magic Dart already memorised and three "
               "other spells in your library, which you can memorise when you "
               "meet their requirements. (To view memorised spells, you can "
               "exit this menu and select <w>I</w>.)");

```

当前中文模板：此界面显示你法术库中的法术。你可以在此选择法术进行记忆，也可以查看法术说明、搜索并整理它们。作为咒法师，你一开始已记忆魔法飞弹，法术库中另有三个法术，满足条件后即可记忆。（要查看已记忆的法术，可退出此菜单并按<w>I</w>。）

输入还原：此界面显示你法术库中的法术。你可以在此选择法术进行记忆，也可以查看法术说明、搜索并整理它们。作为咒法师，你一开始已记忆魔法飞弹，法术库中另有三个法术，满足条件后即可记忆。（要查看已记忆的法术，可退出此菜单并按<w>I</w>。）


### trunk

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-63 — ok


### stable

完整英文：
```text
Welcome to the Realm of Zot!
You feel the power of the Orb interfering with translocations here.
```

生产调用：{'path': 'crawl-ref/source/branch-data.h', 'line': 218}

参数表达式与来源：
```text
BRANCH_ZOT, BRANCH_DEPTHS, 4, 4, 5, 27,
      brflag::dangerous_end,
      DNGN_ENTER_ZOT, DNGN_EXIT_ZOT, NUM_FEATURES,
      "Zot", "the Realm of Zot", "Zot",
      "Welcome to the Realm of Zot!\n"
      "You feel the power of the Orb interfering with translocations here.",
      BLACK, BLACK, // set per-map
      'Z', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {BRANCH_DEPTHS} },
#if TAG_MAJOR_VERSION == 34

    { BRANCH_FOREST, BRANCH_VAULTS, 2, 3, 5, 19,
      brflag::spotty,
      DNGN_ENTER_FOREST, DNGN_EXIT_FOREST, NUM_FEATURES,
      "Forest", "the Enchanted Forest", "Forest",
      nullptr,
      BROWN, BROWN,
      'F', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ABYSS, NUM_BRANCHES, -1, -1, 7, 24,
      brflag::no_x_level_travel | brflag::no_map | brflag::no_items,
      DNGN_ENTER_ABYSS, DNGN_EXIT_ABYSS, DNGN_FLOOR, // can't get trapped in abyss
      "Abyss", "the Abyss", "Abyss",
      nullptr,
      BLACK, BLACK, // set specially
      'J', { RUNE_ABYSSAL }, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_PANDEMONIUM, NUM_BRANCHES, -1, -1, 1, 24,
      brflag::no_x_level_travel,
      DNGN_ENTER_PANDEMONIUM, DNGN_EXIT_PANDEMONIUM, DNGN_TRANSIT_PANDEMONIUM,
      "Pandemonium", "Pandemonium", "Pan",
      "You enter the halls of Pandemonium!\n"
      "To return, you must find a gate leading back.",
      BLACK, BLACK, // set specially
      'R', { RUNE_DEMONIC, RUNE_MNOLEG, RUNE_LOM_LOBON, RUNE_CEREBOV,
             RUNE_GLOORX_VLOQ }, branch_noise::normal, 8,
      {} },

    { BRANCH_ZIGGURAT, BRANCH_DEPTHS, 1, 4, 27, 27,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_ZIGGURAT, DNGN_EXIT_ZIGGURAT, DNGN_FLOOR,
      "Ziggurat", "a ziggurat", "Zig",
      "You land on top of a ziggurat so tall you cannot make out the ground.",
      BLACK, BLACK,
      'Q', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#if TAG_MAJOR_VERSION == 34

    { BRANCH_LABYRINTH, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_LABYRINTH, DNGN_EXIT_LABYRINTH, DNGN_EXIT_THROUGH_ABYSS,
      "Labyrinth", "a Labyrinth", "Lab",
      "You enter a labyrinth!",
      BLACK, BLACK,
      '0', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_BAZAAR, NUM_BRANCHES, -1, -1, 1, 18,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_BAZAAR, DNGN_EXIT_BAZAAR, NUM_FEATURES,
      "Bazaar", "a bazaar", "Bazaar",
      "You enter an inter-dimensional bazaar!",
      BLUE, YELLOW,
      '1', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_TROVE, NUM_BRANCHES, -1, -1, 1, 18,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_TROVE, DNGN_EXIT_TROVE, NUM_FEATURES,
      "Trove", "a treasure trove", "Trove",
      "You enter a treasure trove!",
      DARKGREY, BLUE,
      '2', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_SEWER, NUM_BRANCHES, -1, -1, 1, 4,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_SEWER, DNGN_EXIT_SEWER, NUM_FEATURES,
      "Sewer", "a sewer", "Sewer",
      "You enter a sewer!",
      LIGHTGREY, BLUE,
      '3', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_OSSUARY, NUM_BRANCHES, -1, -1, 1, 6,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_OSSUARY, DNGN_EXIT_OSSUARY, NUM_FEATURES,
      "Ossuary", "an ossuary", "Ossuary",
      "You enter an ossuary!",
      WHITE, YELLOW,
      '4', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_BAILEY, NUM_BRANCHES, -1, -1, 1, 11,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_BAILEY, DNGN_EXIT_BAILEY, NUM_FEATURES,
      "Bailey", "a bailey", "Bailey",
      "You enter a bailey!",
      WHITE, LIGHTRED,
      '5', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#if TAG_MAJOR_VERSION > 34

    { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
      "Gauntlet", "a Gauntlet", "Gauntlet",
      "You enter a gauntlet!",
      BLACK, BLACK,
      '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ICE_CAVE, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_ICE_CAVE, DNGN_EXIT_ICE_CAVE, NUM_FEATURES,
      "Ice Cave", "an ice cave", "IceCv",
      "You enter an ice cave!",
      BLUE, WHITE,
#if TAG_MAJOR_VERSION == 34
      '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_VOLCANO, NUM_BRANCHES, -1, -1, 1, 14,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_VOLCANO, DNGN_EXIT_VOLCANO, NUM_FEATURES,
      "Volcano", "a volcano", "Volcano",
      "You enter a volcano!",
      RED, RED,
#if TAG_MAJOR_VERSION == 34
      '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_WIZLAB, NUM_BRANCHES, -1, -1, 1, 24,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_WIZLAB, DNGN_EXIT_WIZLAB, NUM_FEATURES,
      "Wizlab", "a wizard's laboratory", "WizLab",
      "You enter a wizard's laboratory!",
      LIGHTGREY, BROWN, // set per-map
#if TAG_MAJOR_VERSION == 34
      '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '9', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION == 34

    { BRANCH_DEPTHS, BRANCH_DUNGEON, 15, 15, 4, 22,
      brflag::none,
      DNGN_ENTER_DEPTHS, DNGN_EXIT_DEPTHS, NUM_FEATURES,
      "Depths", "the Depths", "Depths",
      nullptr,
      LIGHTGREY, BROWN,
      'U', {}, branch_noise::normal, 10,
      {BRANCH_VAULTS, BRANCH_SLIME} },
#endif

    { BRANCH_DESOLATION, NUM_BRANCHES, -1, -1, 1, 20,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_DESOLATION, DNGN_EXIT_DESOLATION, NUM_FEATURES, // TODO
      "Desolation", "the Desolation of Salt", "Desolation",
      "You enter a great desolation of salt!",
      LIGHTGREY, BROWN, // TODO
#if TAG_MAJOR_VERSION == 34
      '9', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '0', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION == 34

    { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
      "Gauntlet", "a Gauntlet", "Gauntlet",
      "You enter a gauntlet!",
      BLACK, BLACK,
      '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_ARENA, DNGN_EXIT_ARENA, NUM_FEATURES,
      "Arena", "the Arena", "Arena",
      "You enter Okawaru's Arena!",
      BLACK, BLACK,
#if TAG_MAJOR_VERSION == 34
      '"', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#else
      '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_CRUCIBLE, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_CRUCIBLE, DNGN_EXIT_CRUCIBLE, NUM_FEATURES,
      "Crucible", "the Crucible of Flesh", "Crucible",
      "You are dragged down into the Crucible of Flesh!",
      BLACK, BLACK,
      '@', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },

    { BRANCH_NECROPOLIS, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_NECROPOLIS, DNGN_EXIT_NECROPOLIS, NUM_FEATURES,
      "Necropolis", "the Necropolis", "Necropolis",
      "You enter an ornate necropolis!",
      MAGENTA, LIGHTGREY,
      '%', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },
};

```

当前中文模板：欢迎来到佐特领域！
你感到宝珠的力量在这里干扰着空间转移。

输入还原：欢迎来到佐特领域！
你感到宝珠的力量在这里干扰着空间转移。


### trunk

完整英文：
```text
Welcome to the Realm of Zot!
You feel the power of the Orb interfering with translocations here.
```

生产调用：{'path': 'crawl-ref/source/branch-data.h', 'line': 218}

参数表达式与来源：
```text
BRANCH_ZOT, BRANCH_DEPTHS, 4, 4, 5, 27,
      brflag::dangerous_end,
      DNGN_ENTER_ZOT, DNGN_EXIT_ZOT, NUM_FEATURES,
      "Zot", "the Realm of Zot", "Zot",
      "Welcome to the Realm of Zot!\n"
      "You feel the power of the Orb interfering with translocations here.",
      BLACK, BLACK, // set per-map
      'Z', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {BRANCH_DEPTHS} },
#if TAG_MAJOR_VERSION == 34

    { BRANCH_FOREST, BRANCH_VAULTS, 2, 3, 5, 19,
      brflag::spotty,
      DNGN_ENTER_FOREST, DNGN_EXIT_FOREST, NUM_FEATURES,
      "Forest", "the Enchanted Forest", "Forest",
      nullptr,
      BROWN, BROWN,
      'F', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ABYSS, NUM_BRANCHES, -1, -1, 7, 24,
      brflag::no_x_level_travel | brflag::no_map | brflag::no_items,
      DNGN_ENTER_ABYSS, DNGN_EXIT_ABYSS, DNGN_FLOOR, // can't get trapped in abyss
      "Abyss", "the Abyss", "Abyss",
      nullptr,
      BLACK, BLACK, // set specially
      'J', { RUNE_ABYSSAL }, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_PANDEMONIUM, NUM_BRANCHES, -1, -1, 1, 24,
      brflag::no_x_level_travel,
      DNGN_ENTER_PANDEMONIUM, DNGN_EXIT_PANDEMONIUM, DNGN_TRANSIT_PANDEMONIUM,
      "Pandemonium", "Pandemonium", "Pan",
      "You enter the halls of Pandemonium!\n"
      "To return, you must find a gate leading back.",
      BLACK, BLACK, // set specially
      'R', { RUNE_DEMONIC, RUNE_MNOLEG, RUNE_LOM_LOBON, RUNE_CEREBOV,
             RUNE_GLOORX_VLOQ }, branch_noise::normal, 8,
      {} },

    { BRANCH_ZIGGURAT, BRANCH_DEPTHS, 1, 4, 27, 27,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_ZIGGURAT, DNGN_EXIT_ZIGGURAT, DNGN_FLOOR,
      "Ziggurat", "a ziggurat", "Zig",
      "You land on top of a ziggurat so tall you cannot make out the ground.",
      BLACK, BLACK,
      'Q', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#if TAG_MAJOR_VERSION == 34

    { BRANCH_LABYRINTH, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_LABYRINTH, DNGN_EXIT_LABYRINTH, DNGN_EXIT_THROUGH_ABYSS,
      "Labyrinth", "a Labyrinth", "Lab",
      "You enter a labyrinth!",
      BLACK, BLACK,
      '0', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_BAZAAR, NUM_BRANCHES, -1, -1, 1, 18,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_BAZAAR, DNGN_EXIT_BAZAAR, NUM_FEATURES,
      "Bazaar", "a bazaar", "Bazaar",
      "You enter an inter-dimensional bazaar!",
      BLUE, YELLOW,
      '1', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_TROVE, NUM_BRANCHES, -1, -1, 1, 18,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_TROVE, DNGN_EXIT_TROVE, NUM_FEATURES,
      "Trove", "a treasure trove", "Trove",
      "You enter a treasure trove!",
      DARKGREY, BLUE,
      '2', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_SEWER, NUM_BRANCHES, -1, -1, 1, 4,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_SEWER, DNGN_EXIT_SEWER, NUM_FEATURES,
      "Sewer", "a sewer", "Sewer",
      "You enter a sewer!",
      LIGHTGREY, BLUE,
      '3', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_OSSUARY, NUM_BRANCHES, -1, -1, 1, 6,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_OSSUARY, DNGN_EXIT_OSSUARY, NUM_FEATURES,
      "Ossuary", "an ossuary", "Ossuary",
      "You enter an ossuary!",
      WHITE, YELLOW,
      '4', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },

    { BRANCH_BAILEY, NUM_BRANCHES, -1, -1, 1, 11,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_BAILEY, DNGN_EXIT_BAILEY, NUM_FEATURES,
      "Bailey", "a bailey", "Bailey",
      "You enter a bailey!",
      WHITE, LIGHTRED,
      '5', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#if TAG_MAJOR_VERSION > 34

    { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
      "Gauntlet", "a Gauntlet", "Gauntlet",
      "You enter a gauntlet!",
      BLACK, BLACK,
      '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ICE_CAVE, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_ICE_CAVE, DNGN_EXIT_ICE_CAVE, NUM_FEATURES,
      "Ice Cave", "an ice cave", "IceCv",
      "You enter an ice cave!",
      BLUE, WHITE,
#if TAG_MAJOR_VERSION == 34
      '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_VOLCANO, NUM_BRANCHES, -1, -1, 1, 14,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_VOLCANO, DNGN_EXIT_VOLCANO, NUM_FEATURES,
      "Volcano", "a volcano", "Volcano",
      "You enter a volcano!",
      RED, RED,
#if TAG_MAJOR_VERSION == 34
      '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_WIZLAB, NUM_BRANCHES, -1, -1, 1, 24,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_WIZLAB, DNGN_EXIT_WIZLAB, NUM_FEATURES,
      "Wizlab", "a wizard's laboratory", "WizLab",
      "You enter a wizard's laboratory!",
      LIGHTGREY, BROWN, // set per-map
#if TAG_MAJOR_VERSION == 34
      '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '9', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION == 34

    { BRANCH_DEPTHS, BRANCH_DUNGEON, 15, 15, 4, 22,
      brflag::none,
      DNGN_ENTER_DEPTHS, DNGN_EXIT_DEPTHS, NUM_FEATURES,
      "Depths", "the Depths", "Depths",
      nullptr,
      LIGHTGREY, BROWN,
      'U', {}, branch_noise::normal, 10,
      {BRANCH_VAULTS, BRANCH_SLIME} },
#endif

    { BRANCH_DESOLATION, NUM_BRANCHES, -1, -1, 1, 20,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_DESOLATION, DNGN_EXIT_DESOLATION, NUM_FEATURES, // TODO
      "Desolation", "the Desolation of Salt", "Desolation",
      "You enter a great desolation of salt!",
      LIGHTGREY, BROWN, // TODO
#if TAG_MAJOR_VERSION == 34
      '9', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION > 34
      '0', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
      {} },
#endif
#if TAG_MAJOR_VERSION == 34

    { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
      "Gauntlet", "a Gauntlet", "Gauntlet",
      "You enter a gauntlet!",
      BLACK, BLACK,
      '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_ARENA, DNGN_EXIT_ARENA, NUM_FEATURES,
      "Arena", "the Arena", "Arena",
      "You enter Okawaru's Arena!",
      BLACK, BLACK,
#if TAG_MAJOR_VERSION == 34
      '"', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#else
      '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {} },
#endif

    { BRANCH_CRUCIBLE, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_CRUCIBLE, DNGN_EXIT_CRUCIBLE, NUM_FEATURES,
      "Crucible", "the Crucible of Flesh", "Crucible",
      "You are dragged down into the Crucible of Flesh!",
      BLACK, BLACK,
      '@', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },

    { BRANCH_NECROPOLIS, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_NECROPOLIS, DNGN_EXIT_NECROPOLIS, NUM_FEATURES,
      "Necropolis", "the Necropolis", "Necropolis",
      "You enter an ornate necropolis!",
      MAGENTA, LIGHTGREY,
      '%', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },

    { BRANCH_GULCH, NUM_BRANCHES, -1, -1, 1, 20,
      brflag::no_x_level_travel | brflag::no_items,
      DNGN_ENTER_GULCH, DNGN_EXIT_GULCH, NUM_FEATURES,
      "Gulch", "a gutter gulch", "Gulch",
      "You enter the Vaults' gutter gulch!",
      GREEN, LIGHTBLUE,
      '^', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },

    { BRANCH_XOM_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
      brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
      DNGN_ENTER_XOM_ARENA, DNGN_EXIT_XOM_ARENA, NUM_FEATURES,
      "Arena?", "Xom's Arena of Wonders", "Arena?",
      "You are whisked away to a strange place.",
      BLACK, BLACK,
      '?', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
      {}
    },

};

```

当前中文模板：欢迎来到佐特领域！
你感到宝珠的力量在这里干扰着空间转移。

输入还原：欢迎来到佐特领域！
你感到宝珠的力量在这里干扰着空间转移。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-64 — ok


### stable

完整英文：
```text
You can't go down here!
```

生产调用：{'path': 'crawl-ref/source/main.cc', 'line': 1455}

参数表达式与来源：
```text
else if (down)
                mpr(T_("You can't go down here!"));

```

当前中文模板：你无法从这里下去！

输入还原：你无法从这里下去！

完整英文：
```text
You can't go down here!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 400}

参数表达式与来源：
```text
else
                mpr(T_("You can't go down here!"));

```

当前中文模板：你无法从这里下去！

输入还原：你无法从这里下去！


### trunk

完整英文：
```text
You can't go down here!
```

生产调用：{'path': 'crawl-ref/source/main.cc', 'line': 1511}

参数表达式与来源：
```text
else if (down)
                mpr(T_("You can't go down here!"));

```

当前中文模板：你无法从这里下去！

输入还原：你无法从这里下去！

完整英文：
```text
You can't go down here!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 412}

参数表达式与来源：
```text
else
                mpr(T_("You can't go down here!"));

```

当前中文模板：你无法从这里下去！

输入还原：你无法从这里下去！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-65 — ok


### stable

完整英文：
```text
You can't go up here!
```

生产调用：{'path': 'crawl-ref/source/main.cc', 'line': 1457}

参数表达式与来源：
```text
else
                mpr(T_("You can't go up here!"));

```

当前中文模板：你无法从这里上去！

输入还原：你无法从这里上去！

完整英文：
```text
You can't go up here!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 398}

参数表达式与来源：
```text
else if (going_up)
                mpr(T_("You can't go up here!"));

```

当前中文模板：你无法从这里上去！

输入还原：你无法从这里上去！


### trunk

完整英文：
```text
You can't go up here!
```

生产调用：{'path': 'crawl-ref/source/main.cc', 'line': 1513}

参数表达式与来源：
```text
else
                mpr(T_("You can't go up here!"));

```

当前中文模板：你无法从这里上去！

输入还原：你无法从这里上去！

完整英文：
```text
You can't go up here!
```

生产调用：{'path': 'crawl-ref/source/stairs.cc', 'line': 410}

参数表达式与来源：
```text
else if (going_up)
                mpr(T_("You can't go up here!"));

```

当前中文模板：你无法从这里上去！

输入还原：你无法从这里上去！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-66 — ok


### stable

完整英文：
```text
You can't place a gateway to a ziggurat here.
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 423}

参数表达式与来源：
```text
mpr(T_("You can't place a gateway to a ziggurat here."));

```

当前中文模板：你不能在这里放置通往通天塔的传送门。

输入还原：你不能在这里放置通往通天塔的传送门。


### trunk

完整英文：
```text
You can't place a gateway to a ziggurat here.
```

生产调用：{'path': 'crawl-ref/source/evoke.cc', 'line': 411}

参数表达式与来源：
```text
mpr(T_("You can't place a gateway to a ziggurat here."));

```

当前中文模板：你不能在这里放置通往通天塔的传送门。

输入还原：你不能在这里放置通往通天塔的传送门。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-67 — ok


### stable


### trunk

完整英文：
```text
You cannot currently see %1$s and %2$s true position is unknown, but %3$s was last observed here.
```

生产调用：{'path': 'crawl-ref/source/describe.cc', 'line': 8168}

参数表达式与来源：
```text
inf.body << "\n<magenta>" << make_stringf_p(
                C_("monster description",
                   "You cannot currently see %1$s and %2$s true position is unknown, "
                   "but %3$s was last observed here."),
                it_o.c_str(), mi.pronoun(PRONOUN_POSSESSIVE), it.c_str())
                     << "</magenta>";
8146:                    "accuracy and defense against %2$s attacks are reduced."),
8147:                 it_o.c_str(), mi.pronoun(PRONOUN_POSSESSIVE),
8148:                 uppercase_first(mi.pronoun(PRONOUN_POSSESSIVE)).c_str())
8149:                      << "</magenta>";
8150:         }
8151:         else
8152:         {
8153:             inf.body << "\n<magenta>"
8154:                      << It << " " << is << " currently invisible to you and "
8155:                      << "you have merely inferred " << mi.pronoun(PRONOUN_POSSESSIVE)
8156:                      << " position. " << uppercase_first(mi.pronoun(PRONOUN_POSSESSIVE))
8157:                      << " current health and status is unknown to you and your"
8158:                         " accuracy and defence against " << mi.pronoun(PRONOUN_POSSESSIVE)
8159:                      << " attacks is reduced. </magenta>";
8160:         }
8161:     }
8162:     else if (mi.is(MB_REMEMBERED_INVIS))
8163:     {
8164:         if (Options.language == lang_t::ZH)
8165:         {
8166:             inf.body << "\n<magenta>" << make_stringf_p(
8167:                 C_("monster description",
8168:                    "You cannot currently see %1$s and %2$s true position is unknown, "
8169:                    "but %3$s was last observed here."),
8170:                 it_o.c_str(), mi.pronoun(PRONOUN_POSSESSIVE), it.c_str())
8171:                      << "</magenta>";
8172:         }
8173:         else
8174:         {
8175:             inf.body << "\n<magenta>"
8176:                      << It << " " << is << " currently invisible to you and "
8177:                      << mi.pronoun(PRONOUN_POSSESSIVE) << " true position is unknown, "
8178:                      << "but " << it << " was last observed here."
8179:                      << "</magenta>";
8180:         }
8181:     }
8182:
8183:     if (mi.is(MB_SUMMONED))
8184:     {
8185:         // TODO: hacks; convert angered_by_attacks to a monster_info check
8186:         // (but on the other hand, it is really limiting to not have access
8187:         // to the monster...)
8188:         const bool vanishes_when_angered = !mi.pos.origin()
8189:                                            && monster_at(mi.pos)
8190:                                            && monster_at(mi.pos)->angered_by_attacks()
8191:                                            && mi.attitude == ATT_FRIENDLY;
8192:         if (Options.language == lang_t::ZH)
8193:         {
```

当前中文模板：你目前看不到%1$s，无法确定%2$s真实位置，但最后一次看到%3$s是在这里。

输入还原：None

独立判断与参数还原：主格宾格与所有格分别为他/他的，例你目前看不到他，无法确定他的真实位置，但最后一次看到他是在这里。；所有格已自带的，模板不再补的。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-68 — ok


### stable

完整英文：
```text
You cannot grow anything here.
```

生产调用：{'path': 'crawl-ref/source/target.cc', 'line': 1676}

参数表达式与来源：
```text
if (!overgrow_affects_pos(a))
        return notify_fail(T_("You cannot grow anything here."));

```

当前中文模板：你无法在这里种植任何东西。

输入还原：你无法在这里种植任何东西。


### trunk

完整英文：
```text
You cannot grow anything here.
```

生产调用：{'path': 'crawl-ref/source/target.cc', 'line': 1657}

参数表达式与来源：
```text
if (!overgrow_affects_pos(a))
        return notify_fail(T_("You cannot grow anything here."));

```

当前中文模板：你无法在这里种植任何东西。

输入还原：你无法在这里种植任何东西。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-69 — readability


### stable

完整英文：
```text
You see here
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 937}

参数表达式与来源：
```text
strm << (T_("You see here "))
             << name << (T_(".")) << endl;

```

当前中文模板：你在这里看到了

输入还原：你在这里看到了


### trunk

完整英文：
```text
You see here
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 937}

参数表达式与来源：
```text
strm << (T_("You see here "))
             << name << (T_(".")) << endl;

```

当前中文模板：你在这里看到了

输入还原：你在这里看到了

独立判断与参数还原：与同场景普通物品提示可统一为自然的这里有，数量短语本身可成句。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "consistency", "line": "both", "english": "You see here ", "current_full_zh": "你在这里看到了3支标枪。", "problem": "与同场景普通物品提示可统一为自然的这里有，数量短语本身可成句。", "suggested_zh": "这里有3支标枪。", "evidence": "items.cc:937-938 为单项物品整栈提示，物品名可自带数量；并非多项列表标题。", "defect_points": 0}


## D-HERE-70 — readability


### stable

完整英文：
```text
You see here %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 2725}

参数表达式与来源：
```text
mprf(T_("You see here %s."),
             item.name(DESC_A).c_str());
2703:     }
2704:     // Movable item or no movable items in pile, link item to top of list.
2705:     else
2706:     {
2707:         item.link = env.igrid(p);
2708:         env.igrid(p) = ob;
2709:     }
2710:
2711:     if (item_is_orb(item))
2712:         env.orb_pos = p;
2713:
2714:     if (item.base_type != OBJ_GOLD)
2715:         gozag_move_gold_to_top(p);
2716:
2717:     if (you.see_cell(p))
2718:     {
2719:         ash_id_item(item);
2720:         maybe_identify_base_type(item);
2721:     }
2722:
2723:     if (p == you.pos() && _id_floor_item(item))
2724:     {
2725:         mprf(T_("You see here %s."),
2726:              item.name(DESC_A).c_str());
2727:     }
2728:
2729:     return true;
2730: }
2731:
2732: void move_item_stack_to_grid(const coord_def& from, const coord_def& to)
2733: {
2734:     if (env.igrid(from) == NON_ITEM)
2735:         return;
2736:
2737:     // Tell all items in stack what the new coordinate is.
2738:     for (stack_iterator si(from); si; ++si)
2739:     {
2740:         si->pos = to;
2741:
2742:         // Link last of the stack to the top of the old stack.
2743:         if (si->link == NON_ITEM && env.igrid(to) != NON_ITEM)
2744:         {
2745:             si->link = env.igrid(to);
2746:             break;
2747:         }
2748:     }
```

当前中文模板：你在这里看到%s。

输入还原：None


### trunk

完整英文：
```text
You see here %s.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 2678}

参数表达式与来源：
```text
mprf(T_("You see here %s."),
             item.name(DESC_A).c_str());
2656:     // Need to move this stationary item to the position in the pile
2657:     // below the lowest non-stationary, non-net item.
2658:     if (move_below && movable_ind >= 0)
2659:     {
2660:         item.link = env.item[movable_ind].link;
2661:         env.item[movable_ind].link = item.index();
2662:     }
2663:     // Movable item or no movable items in pile, link item to top of list.
2664:     else
2665:     {
2666:         item.link = env.igrid(p);
2667:         env.igrid(p) = ob;
2668:     }
2669:
2670:     if (you.see_cell(p))
2671:     {
2672:         ash_id_item(item);
2673:         maybe_identify_base_type(item);
2674:     }
2675:
2676:     if (p == you.pos() && _id_floor_item(item))
2677:     {
2678:         mprf(T_("You see here %s."),
2679:              item.name(DESC_A).c_str());
2680:     }
2681:
2682:     return true;
2683: }
2684:
2685: void move_item_stack_to_grid(const coord_def& from, const coord_def& to)
2686: {
2687:     if (env.igrid(from) == NON_ITEM)
2688:         return;
2689:
2690:     // Tell all items in stack what the new coordinate is.
2691:     for (stack_iterator si(from); si; ++si)
2692:     {
2693:         si->pos = to;
2694:
2695:         // Link last of the stack to the top of the old stack.
2696:         if (si->link == NON_ITEM && env.igrid(to) != NON_ITEM)
2697:         {
2698:             si->link = env.igrid(to);
2699:             break;
2700:         }
2701:     }
```

当前中文模板：你在这里看到%s。

输入还原：None

独立判断与参数还原：与单栈物品提示句式不一致，可统一；当前并无搭配错误。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。

发现：{"type": "consistency", "line": "both", "english": "You see here %s.", "current_full_zh": "你在这里看到3支标枪。", "problem": "与单栈物品提示句式不一致，可统一；当前并无搭配错误。", "suggested_zh": "这里有3支标枪。", "evidence": "stable {'path': 'crawl-ref/source/items.cc', 'line': 2725}; trunk {'path': 'crawl-ref/source/items.cc', 'line': 2678}", "defect_points": 0}


## D-HERE-71 — ok


### stable

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2038}

参数表达式与来源：
```text
case ABIL_LUGONU_ABYSS_ENTER:
        if (player_in_branch(BRANCH_ABYSS))
            return fail(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 2957}

参数表达式与来源：
```text
mpr(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5238}

参数表达式与来源：
```text
mpr(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！


### trunk

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/ability.cc', 'line': 2130}

参数表达式与来源：
```text
case ABIL_LUGONU_ABYSS_ENTER:
        if (player_in_branch(BRANCH_ABYSS))
            return fail(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 2995}

参数表达式与来源：
```text
mpr(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

完整英文：
```text
You're already here!
```

生产调用：{'path': 'crawl-ref/source/travel.cc', 'line': 5346}

参数表达式与来源：
```text
mpr(T_("You're already here!"));

```

当前中文模板：你已经在这里了！

输入还原：你已经在这里了！

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-72 — ok


### stable

完整英文：
```text
You've emptied out Pandemonium! Nothing left here but demons.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 2014}

参数表达式与来源：
```text
if (player_in_branch(BRANCH_PANDEMONIUM) && _got_all_pan_runes())
                mpr(T_("You've emptied out Pandemonium! Nothing left here but demons."));

```

当前中文模板：你已经清空了万魔殿！这里只剩下恶魔了。

输入还原：你已经清空了万魔殿！这里只剩下恶魔了。


### trunk

完整英文：
```text
You've emptied out Pandemonium! Nothing left here but demons.
```

生产调用：{'path': 'crawl-ref/source/items.cc', 'line': 1976}

参数表达式与来源：
```text
if (player_in_branch(BRANCH_PANDEMONIUM) && _got_all_pan_runes())
                mpr(T_("You've emptied out Pandemonium! Nothing left here but demons."));

```

当前中文模板：你已经清空了万魔殿！这里只剩下恶魔了。

输入还原：你已经清空了万魔殿！这里只剩下恶魔了。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-73 — ok


### stable

完整英文：
```text
Your vengeful prayer will end if you leave here. Continue?
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 2812}

参数表达式与来源：
```text
if (!yesno(T_("Your vengeful prayer will end if you leave here."
                   " Continue?"), false, 'n'))
        {
            canned_msg(MSG_OK);

```

当前中文模板：如果你离开这里，你的复仇祈祷将会终止。继续吗？

输入还原：如果你离开这里，你的复仇祈祷将会终止。继续吗？


### trunk

完整英文：
```text
Your vengeful prayer will end if you leave here. Continue?
```

生产调用：{'path': 'crawl-ref/source/god-abil.cc', 'line': 2992}

参数表达式与来源：
```text
if (!yesno(T_("Your vengeful prayer will end if you leave here."
                   " Continue?"), false, 'n'))
        {
            canned_msg(MSG_OK);

```

当前中文模板：如果你离开这里，你的复仇祈祷将会终止。继续吗？

输入还原：如果你离开这里，你的复仇祈祷将会终止。继续吗？

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-74 — ok


### stable

完整英文：
```text
[right here]
```

生产调用：{'path': 'crawl-ref/source/stash.cc', 'line': 1796}

参数表达式与来源：
```text
if (here)
                matchtitle << T_("[right here]") << " ";

```

当前中文模板：【就在此处】

输入还原：【就在此处】


### trunk

完整英文：
```text
[right here]
```

生产调用：{'path': 'crawl-ref/source/stash.cc', 'line': 1938}

参数表达式与来源：
```text
if (here)
                matchtitle << T_("[right here]") << " ";

```

当前中文模板：【就在此处】

输入还原：【就在此处】

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-75 — ok


### stable


### trunk

完整英文：
```text
no longer here
```

生产调用：{'path': 'crawl-ref/source/directn.cc', 'line': 1840}

参数表达式与来源：
```text
if (mi.is(MB_REMEMBERED_INVIS))
        suffixes.push_back(T_("no longer here"));

```

当前中文模板：已不在此处

输入还原：已不在此处

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。


## D-HERE-76 — ok


### stable

完整英文：
```text
your pet crocodile is still here.
```

生产调用：{'path': 'crawl-ref/source/spl-util.cc', 'line': 2068}

参数表达式与来源：
```text
else if (count_summons(&you, SPELL_SURPRISING_CROCODILE))
                return T_("your pet crocodile is still here.");

```

当前中文模板：你的宠物鳄鱼还在。

输入还原：你的宠物鳄鱼还在。


### trunk

完整英文：
```text
your pet crocodile is still here.
```

生产调用：{'path': 'crawl-ref/source/spl-util.cc', 'line': 2086}

参数表达式与来源：
```text
else if (count_summons(&you, SPELL_SURPRISING_CROCODILE))
                return T_("your pet crocodile is still here.");

```

当前中文模板：你的宠物鳄鱼还在。

输入还原：你的宠物鳄鱼还在。

独立判断与参数还原：逐条核对本组英文与中文：主语、施受、否定及动作完整；参数按所列来源产生，冠词不机械补译，未发现额外的所有格、句尾或条件作用域问题。

术语对照：在上述实际动作语境检查当前 glossary；不把 magic 一律当 MP，不因 here 一词全局禁止此处；有词形参数时以生产生成器为准。



# 静态条件与版本补证

C-07 stable
```cpp
1823:
1824:     if (proprt[ARTP_SEE_INVISIBLE])
1825:         _mark_unseen_monsters();
1826:
1827:     if (is_unrandom_artefact(item))
1828:     {
1829:         const unrandart_entry *entry = get_unrand_entry(item.unrand_idx);
1830:
1831:         if (entry->unequip_func)
1832:             entry->unequip_func(&item, show_msgs);
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
```

C-07 stable
```cpp
1825:         _mark_unseen_monsters();
1826:
1827:     if (is_unrandom_artefact(item))
1828:     {
1829:         const unrandart_entry *entry = get_unrand_entry(item.unrand_idx);
1830:
1831:         if (entry->unequip_func)
1832:             entry->unequip_func(&item, show_msgs);
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
1874:         case SPWPN_FLAMING:
1875:             mprf(T_("%s bursts into flame!"), item_name.c_str());
```

C-07 stable
```cpp
1827:     if (is_unrandom_artefact(item))
1828:     {
1829:         const unrandart_entry *entry = get_unrand_entry(item.unrand_idx);
1830:
1831:         if (entry->unequip_func)
1832:             entry->unequip_func(&item, show_msgs);
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
1874:         case SPWPN_FLAMING:
1875:             mprf(T_("%s bursts into flame!"), item_name.c_str());
1876:             break;
1877:
```

C-07 stable
```cpp
1829:         const unrandart_entry *entry = get_unrand_entry(item.unrand_idx);
1830:
1831:         if (entry->unequip_func)
1832:             entry->unequip_func(&item, show_msgs);
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
1874:         case SPWPN_FLAMING:
1875:             mprf(T_("%s bursts into flame!"), item_name.c_str());
1876:             break;
1877:
1878:         case SPWPN_FREEZING:
1879:             mprf("%s %s", item_name.c_str(),
```

C-07 stable
```cpp
1831:         if (entry->unequip_func)
1832:             entry->unequip_func(&item, show_msgs);
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
1874:         case SPWPN_FLAMING:
1875:             mprf(T_("%s bursts into flame!"), item_name.c_str());
1876:             break;
1877:
1878:         case SPWPN_FREEZING:
1879:             mprf("%s %s", item_name.c_str(),
1880:                 is_range_weapon(item) ?
1881:                     T_("is covered in frost.") :
```

C-07 stable
```cpp
1833:     }
1834:
1835:     if (artefact_property(item, ARTP_FRAGILE) && !meld)
1836:     {
1837:         mprf(T_("%s crumbles to dust!"), item.name(DESC_THE).c_str());
1838:
1839:         // Hide unwield messages for weapons that have already been destroyed.
1840:         if (item.base_type == OBJ_WEAPONS)
1841:             *show_msgs = false;
1842:     }
1843: }
1844:
1845: static void _equip_use_warning(const item_def& item)
1846: {
1847:     if (is_holy_item(item) && you_worship(GOD_YREDELEMNUL))
1848:         mpr(T_("You really shouldn't be using a holy item like this."));
1849:     else if (is_evil_item(item) && is_good_god(you.religion))
1850:         mpr(T_("You really shouldn't be using an evil item like this."));
1851:     else if (is_unclean_item(item) && you_worship(GOD_ZIN))
1852:         mpr(T_("You really shouldn't be using an unclean item like this."));
1853:     else if (is_chaotic_item(item) && you_worship(GOD_ZIN))
1854:         mpr(T_("You really shouldn't be using a chaotic item like this."));
1855:     else if (is_hasty_item(item) && you_worship(GOD_CHEIBRIADOS))
1856:         mpr(T_("You really shouldn't be using a hasty item like this."));
1857:     else if (is_wizardly_item(item) && you_worship(GOD_TROG))
1858:         mpr(T_("You really shouldn't be using a wizardly item like this."));
1859: }
1860:
1861: // Provide a function for handling initial wielding of 'special' weapons
1862: static void _equip_weapon_effect(item_def& item, bool showMsgs, bool unmeld)
1863: {
1864:     you.wield_change = true;
1865:     quiver::on_weapon_changed();
1866:
1867:     // message first
1868:     int special = get_weapon_brand(item);
1869:     if (showMsgs && item.base_type != OBJ_STAVES)
1870:     {
1871:         const string item_name = item.name(DESC_YOUR);
1872:         switch (special)
1873:         {
1874:         case SPWPN_FLAMING:
1875:             mprf(T_("%s bursts into flame!"), item_name.c_str());
1876:             break;
1877:
1878:         case SPWPN_FREEZING:
1879:             mprf("%s %s", item_name.c_str(),
1880:                 is_range_weapon(item) ?
1881:                     T_("is covered in frost.") :
1882:                     T_("glows with a cold blue light!"));
1883:             break;
```

D-05 stable
```cpp
2912:                     : T_(" and you can't even see any enemies this would affect"));
2913:
2914:         targeter_radius hitfunc(&you, LOS_NO_TRANS);
2915:
2916:         const bool bad_item = (is_dangerous_item(*scroll, true)
2917:                                     || is_bad_item(*scroll))
2918:                             && Options.bad_item_prompt
2919:                             // Don't double-prompt if we're already asking for confirmation.
2920:                             && !_scroll_has_forced_targeter(static_cast<scroll_type>(scroll->sub_type));
2921:
2922:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
2923:                                [which_scroll] (const actor* m)
2924:                                {
2925:                                    return _scroll_will_harm(which_scroll, *m);
2926:                                },
2927:                                nullptr, nullptr))
2928:         {
2929:             return false;
2930:         }
2931:         else if (penance && !yesno(penance_prompt.c_str(), false, 'n'))
2932:         {
2933:             canned_msg(MSG_OK);
2934:             return false;
2935:         }
2936:         else if (bad_item
2937:                  && !yesno(make_stringf(T_("Really %s?%s"),
2938:                                         verb_object.c_str(),
2939:                                         hostile_check ? ""
2940:                         : T_(" You can't even see any enemies this would affect.")
2941:                                         ).c_str(),
2942:                            false, 'n'))
2943:         {
2944:             canned_msg(MSG_OK);
2945:             return false;
2946:         }
2947:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
2948:             "You can't see any enemies this would affect, really %s?"),
2949:                                         verb_object.c_str()).c_str(),
2950:                                                 false, 'n'))
2951:         {
2952:             // is this too nanny dev?
2953:             canned_msg(MSG_OK);
2954:             return false;
2955:         }
2956:     }
2957:
2958:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
2959:     if (you.unrand_equipped(UNRAND_VICTORY, true)
2960:         && !you.props.exists(VICTORY_CONDUCT_KEY))
2961:     {
2962:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
2963:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
2964:                                             "while wearing %s?"),
2965:                                             item->name(DESC_THE, false, true,
2966:                                                        false).c_str());
2967:
```

D-05 trunk
```cpp
3051:     // Handle player cancels before we waste time
3052:     if (alreadyknown)
3053:     {
3054:         const bool hostile_check = scroll_hostile_check(which_scroll);
3055:         const string verb_object = make_stringf(
3056:             T_("read the %s"), scroll->name(DESC_DBNAME).c_str());
3057:
3058:         targeter_radius hitfunc(&you, LOS_NO_TRANS);
3059:
3060:         const bool bad_item = (is_dangerous_item(*scroll, true)
3061:                                     || is_bad_item(*scroll))
3062:                             && Options.bad_item_prompt
3063:                             // Don't double-prompt if we're already asking for confirmation.
3064:                             && !_scroll_has_forced_targeter(which_scroll);
3065:
3066:         if (stop_attack_prompt(hitfunc, verb_object.c_str(),
3067:                                [which_scroll] (const actor* m)
3068:                                {
3069:                                    return _scroll_will_harm(which_scroll, *m);
3070:                                },
3071:                                nullptr, nullptr))
3072:         {
3073:             return false;
3074:         }
3075:         else if (bad_item
3076:                  && !yesno(make_stringf(T_("Really %s?%s"),
3077:                                         verb_object.c_str(),
3078:                                         hostile_check ? ""
3079:                         : T_(" You can't even see any enemies this would affect.")
3080:                                         ).c_str(),
3081:                            false, 'n'))
3082:         {
3083:             canned_msg(MSG_OK);
3084:             return false;
3085:         }
3086:         else if (!bad_item && !hostile_check && !yesno(make_stringf(T_(
3087:             "You can't see any enemies this would affect, really %s?"),
3088:                                         verb_object.c_str()).c_str(),
3089:                                                 false, 'n'))
3090:         {
3091:             // is this too nanny dev?
3092:             canned_msg(MSG_OK);
3093:             return false;
3094:         }
3095:     }
3096:
3097:     const bool nearby_mons = there_are_monsters_nearby(true, true, false);
3098:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3099:         && !you.props.exists(VICTORY_CONDUCT_KEY))
3100:     {
3101:         item_def *item = you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR, true);
3102:         string unrand_prompt = make_stringf(T_("Really read with monsters nearby "
3103:                                             "while wearing %s?"),
3104:                                             item->name(DESC_THE, false, true,
3105:                                                        false).c_str());
3106:
```

D-09 stable
```cpp
64: #include "state.h"
65: #include "stepdown.h"
66: #include "stringutil.h"
67: #include "tag-version.h"
68: #include "target.h"
69: #include "terrain.h"
70: #include "throw.h"
71: #ifdef USE_TILE
72:  #include "tilepick.h"
73: #endif
74: #include "transform.h"
75: #include "traps.h"
76: #include "unicode.h"
77: #include "view.h"
78: #include "database.h"
79:
80: #define PHIAL_RANGE 5
81:
82: static bool _evoke_horn_of_geryon()
83: {
84:     if (!player_summon_check(MONS_SIN_BEAST))
85:         return false;
86:
87:     bool created = false;
88:
89:     mprf(MSGCH_SOUND, T_("You produce a hideous howling noise!"));
90:     noisy(15, you.pos()); // same as hell effect noise
91:     did_god_conduct(DID_EVIL, 3);
92:     int num = 1;
93:     const int adjusted_power = you.skill(SK_EVOCATIONS, 10);
94:     if (adjusted_power + random2(90) > 130)
95:         ++num;
96:     if (adjusted_power + random2(90) > 180)
97:         ++num;
98:     if (adjusted_power + random2(90) > 230)
99:         ++num;
100:     for (int n = 0; n < num; ++n)
101:     {
102:         monster* mon;
103:         beh_type beh = BEH_HOSTILE;
104:
105:         if (random2(adjusted_power) > 7)
106:             beh = BEH_FRIENDLY;
107:         mgen_data mg(MONS_SIN_BEAST, beh, you.pos(), MHITYOU, MG_AUTOFOE);
108:         mg.set_summoned(&you, SPELL_NO_SPELL, summ_dur(3));
109:         mg.set_prox(PROX_CLOSE_TO_PLAYER);
110:         mon = create_monster(mg);
111:         if (mon)
112:             created = true;
113:     }
114:     if (!created)
```

D-09 trunk
```cpp
65: #include "state.h"
66: #include "stepdown.h"
67: #include "stringutil.h"
68: #include "tag-version.h"
69: #include "target.h"
70: #include "terrain.h"
71: #include "throw.h"
72: #ifdef USE_TILE
73:  #include "tilepick.h"
74: #endif
75: #include "transform.h"
76: #include "traps.h"
77: #include "unicode.h"
78: #include "view.h"
79: #include "database.h"
80:
81: #define PHIAL_RANGE 5
82:
83: static bool _evoke_horn_of_geryon()
84: {
85:     if (!player_summon_check(MONS_SIN_BEAST))
86:         return false;
87:
88:     bool created = false;
89:
90:     mprf(MSGCH_SOUND, T_("You produce a hideous howling noise!"));
91:     noisy(15, you.pos()); // same as hell effect noise
92:     int num = 1;
93:     const int adjusted_power = you.skill(SK_EVOCATIONS, 10);
94:     if (adjusted_power + random2(90) > 130)
95:         ++num;
96:     if (adjusted_power + random2(90) > 180)
97:         ++num;
98:     if (adjusted_power + random2(90) > 230)
99:         ++num;
100:     for (int n = 0; n < num; ++n)
101:     {
102:         monster* mon;
103:         beh_type beh = BEH_HOSTILE;
104:
105:         if (random2(adjusted_power) > 7)
106:             beh = BEH_FRIENDLY;
107:         mgen_data mg(MONS_SIN_BEAST, beh, you.pos(), MHITYOU, MG_AUTOFOE);
108:         mg.set_summoned(&you, SPELL_NO_SPELL, summ_dur(3));
109:         mg.set_prox(PROX_CLOSE_TO_PLAYER);
110:         mon = create_monster(mg);
111:         if (mon)
112:             created = true;
113:     }
114:     if (!created)
115:         mpr(T_("Nothing answers your call."));
```

B-02 stable
```cpp
5045:         return false; // don't even print a message
5046:
5047:     const int size_diff =
5048:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5049:     const coord_def old_pos = defender->pos();
5050:     const coord_def new_pos = old_pos + old_pos - attack_position;
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
```

B-02 stable
```cpp
5051:
5052:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5053:         // need a valid tile
5054:         || !defender->is_habitable(new_pos)
5055:         // don't trample anywhere the attacker can't follow
5056:         || !attacker->is_habitable(old_pos)
5057:         // don't trample into a monster - or do we want to cause a chain
5058:         // reaction here?
5059:         || actor_at(new_pos)
5060:         // Prevent trample/drown combo when flight is expiring
5061:         || defender->is_player() && need_expiration_warning(new_pos)
5062:         || defender->is_constricted()
5063:         || defender->resists_dislodge(needs_message
5064:             ? NC_("dislodge event", "being knocked back") : ""))
5065:     {
5066:         if (needs_message)
5067:         {
5068:             if (defender->is_constricted())
5069:             {
5070:                 mprf(T_("%s %s held in place!"),
5071:                      defender_name(false).c_str(),
5072:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5073:             }
5074:             else if (!slippery)
5075:             {
5076:                 mprf(T_("%s %s %s ground!"),
5077:                      defender_name(false).c_str(),
5078:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5079:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5080:             }
5081:         }
5082:
5083:         return false;
5084:     }
5085:
5086:     if (needs_message)
5087:     {
5088:         const bool can_stumble = !defender->airborne()
5089:                                   && !defender->incapacitated();
5090:         const char *verb = slippery ? N_("slip")
5091:                          : can_stumble ? N_("stumble")
5092:                                        : NC_("verb", "are shoved");
5093:         const char *context = slippery || can_stumble ? nullptr : "verb";
5094:         mprf(T_("%s %s backwards!"),
5095:              defender_name(false).c_str(),
5096:              defender->verb_for_display(verb, context).c_str());
5097:     }
5098:
5099:     // Schedule following _before_ actually trampling -- if the defender
5100:     // is a player, a shaft trap will unload the level. If trampling will
5101:     // somehow fail, move attempt will be ignored.
5102:     if (!attacker->cannot_move())
5103:         schedule_trample_follow_fineff(attacker, old_pos);
5104:     defender->move_to(new_pos);
```

B-02 trunk
```cpp
5252:         return false; // don't even print a message
5253:
5254:     const int size_diff =
5255:         attacker->body_size(PSIZE_BODY) - defender->body_size(PSIZE_BODY);
5256:     const coord_def old_pos = defender->pos();
5257:     const coord_def new_pos = old_pos + old_pos - attack_position;
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
```

B-02 trunk
```cpp
5258:
5259:     if (!slippery && !x_chance_in_y(size_diff + 3, 6)
5260:         // need a valid tile
5261:         || !defender->is_habitable(new_pos)
5262:         || !in_bounds(new_pos)
5263:         // don't trample anywhere the attacker can't follow
5264:         || !attacker->is_habitable(old_pos)
5265:         // don't trample into a monster - or do we want to cause a chain
5266:         // reaction here?
5267:         || actor_at(new_pos)
5268:         // Prevent trample/drown combo when flight is expiring
5269:         || defender->is_player() && need_expiration_warning(new_pos)
5270:         || defender->is_constricted()
5271:         || defender->resists_dislodge(needs_message ? NC_("dislodge event", "being knocked back") : ""))
5272:     {
5273:         if (needs_message)
5274:         {
5275:             if (defender->is_constricted())
5276:             {
5277:                 mprf(T_("%s %s held in place!"),
5278:                      defender_name(false).c_str(),
5279:                      defender->verb_for_display(NC_("verb", "are"), "verb").c_str());
5280:             }
5281:             else if (!slippery)
5282:             {
5283:                 mprf(T_("%s %s %s ground!"),
5284:                      defender_name(false).c_str(),
5285:                      defender->verb_for_display(NC_("verb", "hold"), "verb").c_str(),
5286:                      defender->pronoun(PRONOUN_POSSESSIVE).c_str());
5287:             }
5288:         }
5289:
5290:         return false;
5291:     }
5292:
5293:     if (needs_message)
5294:     {
5295:         const bool can_stumble = !defender->airborne()
5296:                                   && !defender->incapacitated();
5297:         const char *verb = slippery ? N_("slip")
5298:                          : can_stumble ? N_("stumble")
5299:                                        : NC_("verb", "are shoved");
5300:         const char *context = slippery ? "trample verb"
5301:                             : can_stumble ? nullptr : "verb";
5302:         mprf(T_("%s %s backwards!"),
5303:              defender_name(false).c_str(),
5304:              defender->verb_for_display(verb, context).c_str());
5305:     }
5306:
5307:     // Schedule following _before_ actually trampling -- if the defender
5308:     // is a player, a shaft trap will unload the level. If trampling will
5309:     // somehow fail, move attempt will be ignored.
5310:     if (!attacker->cannot_move())
5311:         schedule_trample_follow_fineff(attacker, old_pos);
```

B-07 stable
```cpp
4568:         const pie_effect effect = _random_pie_effect(you);
4569:         mprf("%s!", effect.desc);
4570:         effect.effect(you, *this);
4571:     }
4572:
4573:     knockback_actor(&you, final_dam);
4574:     pull_actor(&you, final_dam);
4575:
4576:     if (origin_spell == SPELL_FLASH_FREEZE
4577:         || origin_spell == SPELL_CREEPING_FROST
4578:         || name == "blast of ice"
4579:         || origin_spell == SPELL_HOARFROST_BULLET
4580:         || origin_spell == SPELL_GLACIATE && !is_explosion)
4581:     {
4582:         if (!you.duration[DUR_FROZEN])
4583:         {
4584:             mprf(MSGCH_WARN, T_("You are encased in ice."));
4585:             you.duration[DUR_FROZEN] = (random_range(3, 5)) * BASELINE_DELAY;
4586:         }
4587:     }
4588:
4589:     if (you.form == transformation::aqua
4590:         && is_fiery() && x_chance_in_y(final_dam, you.hp_max * 2 / 3))
4591:     {
4592:         const int pow = div_rand_round(final_dam * 100 / you.hp_max, 10);
4593:         mpr(T_("A part of your body evaporates into steam!"));
4594:         big_cloud(CLOUD_STEAM, monster_by_mid(MID_YOU_FAULTLESS), you.pos(),
4595:                   random_range(1, 4) + pow, random_range(2, 7));
4596:     }
4597: }
4598:
4599: bool bolt::ignores_player() const
4600: {
4601:     // Digging -- don't care.
4602:     if (flavour == BEAM_DIGGING)
4603:         return true;
4604:
4605:     if (origin_spell == SPELL_COMBUSTION_BREATH
4606:         || origin_spell == SPELL_NULLIFYING_BREATH
4607:         || origin_spell == SPELL_RIMEBLIGHT
4608:         || origin_spell == SPELL_SHADOW_PRISM
4609:         || origin_spell == SPELL_SHADOW_SHOT)
4610:     {
4611:         return true;
4612:     }
4613:
4614:     // XXX: Mostly to stop the targeter being weird with trying to keep you
4615:     //      out of splash damage.
4616:     if (origin_spell == SPELL_MERCURY_ARROW && agent() && agent()->is_player())
4617:         return true;
4618:
```

B-07 trunk
```cpp
4604:         const pie_effect effect = _random_pie_effect(you);
4605:         mprf("%s!", effect.desc);
4606:         effect.effect(you, *this);
4607:     }
4608:
4609:     knockback_actor(&you, final_dam);
4610:     pull_actor(&you, final_dam);
4611:
4612:     if (origin_spell == SPELL_FLASH_FREEZE
4613:         || origin_spell == SPELL_CREEPING_FROST
4614:         || name == "blast of ice"
4615:         || origin_spell == SPELL_HOARFROST_BULLET
4616:         || origin_spell == SPELL_GLACIATE && !is_explosion)
4617:     {
4618:         if (!you.duration[DUR_FROZEN])
4619:         {
4620:             mprf(MSGCH_WARN, T_("You are encased in ice."));
4621:             you.duration[DUR_FROZEN] = (random_range(3, 5)) * BASELINE_DELAY;
4622:         }
4623:     }
4624:
4625:     if (you.form == transformation::aqua
4626:         && is_fiery() && x_chance_in_y(final_dam, you.hp_max * 2 / 3))
4627:     {
4628:         const int pow = div_rand_round(final_dam * 100 / you.hp_max, 10);
4629:         mpr(T_("A part of your body evaporates into steam!"));
4630:         big_cloud(CLOUD_STEAM, monster_by_mid(MID_YOU_FAULTLESS), you.pos(),
4631:                   random_range(1, 4) + pow, random_range(2, 7));
4632:     }
4633: }
4634:
4635: bool bolt::ignores_player() const
4636: {
4637:     // Digging -- don't care.
4638:     if (flavour == BEAM_DIGGING)
4639:         return true;
4640:
4641:     if (origin_spell == SPELL_COMBUSTION_BREATH
4642:         || origin_spell == SPELL_NULLIFYING_BREATH
4643:         || origin_spell == SPELL_RIMEBLIGHT
4644:         || origin_spell == SPELL_SHADOW_PRISM
4645:         || origin_spell == SPELL_SHADOW_SHOT)
4646:     {
4647:         return true;
4648:     }
4649:
4650:     // XXX: Mostly to stop the targeter being weird with trying to keep you
4651:     //      out of splash damage.
4652:     if (origin_spell == SPELL_MERCURY_ARROW && agent() && agent()->is_player())
4653:         return true;
4654:
```

C-10 stable
```cpp
1802:
1803:     if (!quiet)
1804:     {
1805:         const string gain = quant != you.gold
1806:                             ? make_stringf(T_(" (gained %d)"), quant)
1807:                             : "";
1808:
1809:         mprf_p(T_("You now have %1$d gold piece%2$s."), you.gold, gain.c_str());
1810:         learned_something_new(HINT_SEEN_GOLD);
1811:     }
1812: }
1813:
1814: void note_inscribe_item(item_def &item)
1815: {
1816:     _autoinscribe_item(item);
1817:     _origin_freeze(item);
1818:     _check_note_item(item);
1819: }
1820:
1821: static bool _put_item_in_inv(item_def& it, int quant_got, bool quiet, bool& put_in_inv)
1822: {
1823:     put_in_inv = false;
1824:     if (item_is_stationary(it))
1825:     {
1826:         if (!quiet)
1827:             mpr(T_("You can't pick that up."));
1828:         // Fake a successful pickup (return 1), so we can continue to
1829:         // pick up anything else that might be on this square.
1830:         return true;
1831:     }
1832:
1833:     // sanity
1834:     if (quant_got > it.quantity || quant_got <= 0)
1835:         quant_got = it.quantity;
1836:
1837:     // attempt to put the item into your inventory.
1838:     int inv_slot;
1839:     if (_merge_items_into_inv(it, quant_got, inv_slot, quiet))
1840:     {
1841:         put_in_inv = true;
1842:
1843:         // cleanup items that ended up in an inventory slot (not gold, etc)
1844:         if (inv_slot != -1)
1845:             _got_item(you.inv[inv_slot]);
1846:         else if (it.base_type == OBJ_BOOKS)
1847:             _got_item(it);
1848:         _check_note_item(inv_slot == -1 ? it : you.inv[inv_slot]);
1849:         return true;
1850:     }
1851:
1852:     return false;
```

C-10 stable
```cpp
3476:     if (!check_transform_into(trans, false, &real_item))
3477:         return false;
3478:     if (transforming_is_unsafe(trans))
3479:         return false;
3480:     if (!i_feel_safe(true) && !yesno(T_("Still begin transforming?"), true, 'n'))
3481:     {
3482:         canned_msg(MSG_OK);
3483:         return false;
3484:     }
3485:
3486:     count_action(CACT_FORM, (int)trans);
3487:     start_delay<TransformDelay>(trans, &real_item);
3488:     if (god_despises_item(real_item, you.religion))
3489:         excommunication();
3490:     you.turn_is_over = true;
3491:     return true;
3492: }
3493:
3494: #ifdef USE_TILE
3495: // Interactive menu for item drop/use.
3496:
3497: void tile_item_pickup(int idx, bool part)
3498: {
3499:     if (item_is_stationary(env.item[idx]))
3500:     {
3501:         mpr(T_("You can't pick that up."));
3502:         return;
3503:     }
3504:
3505:     int quantity = env.item[idx].quantity;
3506:     if (part && quantity > 1)
3507:     {
3508:         quantity = prompt_for_int(T_("Pick up how many?"), true);
3509:         if (quantity < 1)
3510:         {
3511:             canned_msg(MSG_OK);
3512:             return;
3513:         }
3514:         if (quantity > env.item[idx].quantity)
3515:             quantity = env.item[idx].quantity;
3516:     }
3517:     pickup_single_item(idx, quantity);
3518: }
3519:
3520: void tile_item_drop(int idx, bool partdrop)
3521: {
3522:     if (!check_warning_inscriptions(you.inv[idx], OPER_DROP))
3523:     {
3524:         canned_msg(MSG_OK);
3525:         return;
3526:     }
```

C-10 trunk
```cpp
1765:
1766:     if (!quiet)
1767:     {
1768:         const string gain = quant != you.gold
1769:                             ? make_stringf(T_(" (gained %d)"), quant)
1770:                             : "";
1771:
1772:         mprf_p(T_("You now have %1$d gold piece%2$s."), you.gold, gain.c_str());
1773:         learned_something_new(HINT_SEEN_GOLD);
1774:     }
1775: }
1776:
1777: void note_inscribe_item(item_def &item)
1778: {
1779:     _autoinscribe_item(item);
1780:     _origin_freeze(item);
1781:     _check_note_item(item);
1782: }
1783:
1784: static bool _put_item_in_inv(item_def& it, int quant_got, bool quiet, bool& put_in_inv)
1785: {
1786:     put_in_inv = false;
1787:     if (item_is_stationary(it))
1788:     {
1789:         if (!quiet)
1790:             mpr(T_("You can't pick that up."));
1791:         // Fake a successful pickup (return 1), so we can continue to
1792:         // pick up anything else that might be on this square.
1793:         return true;
1794:     }
1795:
1796:     // sanity
1797:     if (quant_got > it.quantity || quant_got <= 0)
1798:         quant_got = it.quantity;
1799:
1800:     // attempt to put the item into your inventory.
1801:     int inv_slot;
1802:     if (_merge_items_into_inv(it, quant_got, inv_slot, quiet))
1803:     {
1804:         put_in_inv = true;
1805:
1806:         // cleanup items that ended up in an inventory slot (not gold, etc)
1807:         if (inv_slot != -1)
1808:             _got_item(you.inv[inv_slot]);
1809:         else if (it.base_type == OBJ_BOOKS)
1810:             _got_item(it);
1811:         _check_note_item(inv_slot == -1 ? it : you.inv[inv_slot]);
1812:         return true;
1813:     }
1814:
1815:     return false;
```

C-10 trunk
```cpp
3649:                                     ? transformation::none
3650:                                     : form_for_talisman(real_item);
3651:     if (!check_transform_into(trans, false, &real_item))
3652:         return false;
3653:     if (transforming_is_unsafe(trans))
3654:         return false;
3655:     if (!i_feel_safe(true) && !yesno(T_("Still begin transforming?"), true, 'n'))
3656:     {
3657:         canned_msg(MSG_OK);
3658:         return false;
3659:     }
3660:
3661:     count_action(CACT_FORM, (int)trans);
3662:     start_delay<TransformDelay>(trans, &real_item);
3663:     you.turn_is_over = true;
3664:     return true;
3665: }
3666:
3667: #ifdef USE_TILE
3668: // Interactive menu for item drop/use.
3669:
3670: void tile_item_pickup(int idx, bool part)
3671: {
3672:     if (item_is_stationary(env.item[idx]))
3673:     {
3674:         mpr(T_("You can't pick that up."));
3675:         return;
3676:     }
3677:
3678:     int quantity = env.item[idx].quantity;
3679:     if (part && quantity > 1)
3680:     {
3681:         quantity = prompt_for_int(T_("Pick up how many?"), true);
3682:         if (quantity < 1)
3683:         {
3684:             canned_msg(MSG_OK);
3685:             return;
3686:         }
3687:         if (quantity > env.item[idx].quantity)
3688:             quantity = env.item[idx].quantity;
3689:     }
3690:     pickup_single_item(idx, quantity);
3691: }
3692:
3693: void tile_item_drop(int idx, bool partdrop)
3694: {
3695:     if (!check_warning_inscriptions(you.inv[idx], OPER_DROP))
3696:     {
3697:         canned_msg(MSG_OK);
3698:         return;
3699:     }
```

F-12 stable
```cpp
361:     }
362:
363:     // Subtract one from the horror level so that you don't get a message
364:     // when a single tough monster appears.
365:     const int horror_level = max(0, current_horror_level() - 1);
366:
367:     if (horror_level <= 0)
368:     {
369:         // If you were horrified before & aren't now, clean up.
370:         _end_horror();
371:         return;
372:     }
373:
374:     // Lookup the old value before modifying it
375:     const int old_horror_level = _old_horror_level();
376:
377:     // as long as there's still scary enemies, keep the horror going
378:     you.props[HORROR_PENALTY_KEY] = horror_level;
379:     you.set_duration(DUR_HORROR, 1);
380:
381:     // only show a message on increase
382:     if (horror_level <= old_horror_level)
383:         return;
384:
385:     if (horror_level >= HORROR_LVL_OVERWHELMING)
386:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
387:     else if (horror_level >= HORROR_LVL_EXTREME)
388:         mpr(T_("You reel with horror at the sight of these foes!"));
389:     else
390:         mpr(T_("You feel a twist of horror at the sight of this foe."));
391: }
392:
393: static void _update_claustrophobia()
394: {
395:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
396:         return;
397:
398:     int count = 0;
399:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
400:     {
401:         if (feat_is_solid(env.grid(*ai)))
402:             ++count;
403:     }
404:
405:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
406: }
407:
408: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
409: // Using Uskayaw abilities can still take you under *.
410: static void _handle_uskayaw_piety(int time_taken)
411: {
```

F-12 stable
```cpp
363:     // Subtract one from the horror level so that you don't get a message
364:     // when a single tough monster appears.
365:     const int horror_level = max(0, current_horror_level() - 1);
366:
367:     if (horror_level <= 0)
368:     {
369:         // If you were horrified before & aren't now, clean up.
370:         _end_horror();
371:         return;
372:     }
373:
374:     // Lookup the old value before modifying it
375:     const int old_horror_level = _old_horror_level();
376:
377:     // as long as there's still scary enemies, keep the horror going
378:     you.props[HORROR_PENALTY_KEY] = horror_level;
379:     you.set_duration(DUR_HORROR, 1);
380:
381:     // only show a message on increase
382:     if (horror_level <= old_horror_level)
383:         return;
384:
385:     if (horror_level >= HORROR_LVL_OVERWHELMING)
386:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
387:     else if (horror_level >= HORROR_LVL_EXTREME)
388:         mpr(T_("You reel with horror at the sight of these foes!"));
389:     else
390:         mpr(T_("You feel a twist of horror at the sight of this foe."));
391: }
392:
393: static void _update_claustrophobia()
394: {
395:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
396:         return;
397:
398:     int count = 0;
399:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
400:     {
401:         if (feat_is_solid(env.grid(*ai)))
402:             ++count;
403:     }
404:
405:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
406: }
407:
408: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
409: // Using Uskayaw abilities can still take you under *.
410: static void _handle_uskayaw_piety(int time_taken)
411: {
412:     if (you.props[USKAYAW_NUM_MONSTERS_HURT].get_int() > 0)
413:     {
```

F-12 stable
```cpp
365:     const int horror_level = max(0, current_horror_level() - 1);
366:
367:     if (horror_level <= 0)
368:     {
369:         // If you were horrified before & aren't now, clean up.
370:         _end_horror();
371:         return;
372:     }
373:
374:     // Lookup the old value before modifying it
375:     const int old_horror_level = _old_horror_level();
376:
377:     // as long as there's still scary enemies, keep the horror going
378:     you.props[HORROR_PENALTY_KEY] = horror_level;
379:     you.set_duration(DUR_HORROR, 1);
380:
381:     // only show a message on increase
382:     if (horror_level <= old_horror_level)
383:         return;
384:
385:     if (horror_level >= HORROR_LVL_OVERWHELMING)
386:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
387:     else if (horror_level >= HORROR_LVL_EXTREME)
388:         mpr(T_("You reel with horror at the sight of these foes!"));
389:     else
390:         mpr(T_("You feel a twist of horror at the sight of this foe."));
391: }
392:
393: static void _update_claustrophobia()
394: {
395:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
396:         return;
397:
398:     int count = 0;
399:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
400:     {
401:         if (feat_is_solid(env.grid(*ai)))
402:             ++count;
403:     }
404:
405:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
406: }
407:
408: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
409: // Using Uskayaw abilities can still take you under *.
410: static void _handle_uskayaw_piety(int time_taken)
411: {
412:     if (you.props[USKAYAW_NUM_MONSTERS_HURT].get_int() > 0)
413:     {
414:         int num_hurt = you.props[USKAYAW_NUM_MONSTERS_HURT];
415:         int hurt_val = you.props[USKAYAW_MONSTER_HURT_VALUE];
```

F-12 trunk
```cpp
363:     }
364:
365:     // Subtract one from the horror level so that you don't get a message
366:     // when a single tough monster appears.
367:     const int horror_level = max(0, current_horror_level() - 1);
368:
369:     if (horror_level <= 0)
370:     {
371:         // If you were horrified before & aren't now, clean up.
372:         _end_horror();
373:         return;
374:     }
375:
376:     // Lookup the old value before modifying it
377:     const int old_horror_level = _old_horror_level();
378:
379:     // as long as there's still scary enemies, keep the horror going
380:     you.props[HORROR_PENALTY_KEY] = horror_level;
381:     you.set_duration(DUR_HORROR, 1);
382:
383:     // only show a message on increase
384:     if (horror_level <= old_horror_level)
385:         return;
386:
387:     if (horror_level >= HORROR_LVL_OVERWHELMING)
388:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
389:     else if (horror_level >= HORROR_LVL_EXTREME)
390:         mpr(T_("You reel with horror at the sight of these foes!"));
391:     else
392:         mpr(T_("You feel a twist of horror at the sight of this foe."));
393: }
394:
395: static void _update_claustrophobia()
396: {
397:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
398:         return;
399:
400:     int count = 0;
401:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
402:     {
403:         if (feat_is_solid(env.grid(*ai)))
404:             ++count;
405:     }
406:
407:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
408: }
409:
410: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
411: // Using Uskayaw abilities can still take you under *.
412: static void _handle_uskayaw_piety(int time_taken)
413: {
```

F-12 trunk
```cpp
365:     // Subtract one from the horror level so that you don't get a message
366:     // when a single tough monster appears.
367:     const int horror_level = max(0, current_horror_level() - 1);
368:
369:     if (horror_level <= 0)
370:     {
371:         // If you were horrified before & aren't now, clean up.
372:         _end_horror();
373:         return;
374:     }
375:
376:     // Lookup the old value before modifying it
377:     const int old_horror_level = _old_horror_level();
378:
379:     // as long as there's still scary enemies, keep the horror going
380:     you.props[HORROR_PENALTY_KEY] = horror_level;
381:     you.set_duration(DUR_HORROR, 1);
382:
383:     // only show a message on increase
384:     if (horror_level <= old_horror_level)
385:         return;
386:
387:     if (horror_level >= HORROR_LVL_OVERWHELMING)
388:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
389:     else if (horror_level >= HORROR_LVL_EXTREME)
390:         mpr(T_("You reel with horror at the sight of these foes!"));
391:     else
392:         mpr(T_("You feel a twist of horror at the sight of this foe."));
393: }
394:
395: static void _update_claustrophobia()
396: {
397:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
398:         return;
399:
400:     int count = 0;
401:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
402:     {
403:         if (feat_is_solid(env.grid(*ai)))
404:             ++count;
405:     }
406:
407:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
408: }
409:
410: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
411: // Using Uskayaw abilities can still take you under *.
412: static void _handle_uskayaw_piety(int time_taken)
413: {
414:     if (you.props[USKAYAW_NUM_MONSTERS_HURT].get_int() > 0)
415:     {
```

F-12 trunk
```cpp
367:     const int horror_level = max(0, current_horror_level() - 1);
368:
369:     if (horror_level <= 0)
370:     {
371:         // If you were horrified before & aren't now, clean up.
372:         _end_horror();
373:         return;
374:     }
375:
376:     // Lookup the old value before modifying it
377:     const int old_horror_level = _old_horror_level();
378:
379:     // as long as there's still scary enemies, keep the horror going
380:     you.props[HORROR_PENALTY_KEY] = horror_level;
381:     you.set_duration(DUR_HORROR, 1);
382:
383:     // only show a message on increase
384:     if (horror_level <= old_horror_level)
385:         return;
386:
387:     if (horror_level >= HORROR_LVL_OVERWHELMING)
388:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
389:     else if (horror_level >= HORROR_LVL_EXTREME)
390:         mpr(T_("You reel with horror at the sight of these foes!"));
391:     else
392:         mpr(T_("You feel a twist of horror at the sight of this foe."));
393: }
394:
395: static void _update_claustrophobia()
396: {
397:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
398:         return;
399:
400:     int count = 0;
401:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
402:     {
403:         if (feat_is_solid(env.grid(*ai)))
404:             ++count;
405:     }
406:
407:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
408: }
409:
410: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
411: // Using Uskayaw abilities can still take you under *.
412: static void _handle_uskayaw_piety(int time_taken)
413: {
414:     if (you.props[USKAYAW_NUM_MONSTERS_HURT].get_int() > 0)
415:     {
416:         int num_hurt = you.props[USKAYAW_NUM_MONSTERS_HURT];
417:         int hurt_val = you.props[USKAYAW_MONSTER_HURT_VALUE];
```

A-08 stable
```cpp
647:
648:     // Show the player the wall they've just bumped into, if they can't see it.
649:     if (you.current_vision == 0)
650:     {
651:         map_cell& knowledge = env.map_knowledge(targ);
652:         if (!knowledge.mapped() || knowledge.changed())
653:         {
654:             dungeon_feature_type newfeat = env.grid(targ);
655:             knowledge.set_feature(newfeat, env.grid_colours(targ), TRAP_UNASSIGNED);
656:             set_terrain_mapped(targ);
657:         }
658:     }
659: }
660:
661: // For confused players, adjust a passed movement direction randomly (with
662: // appropriate warning prompts) and possibly abort entirely if they try to
663: // stumble into a wall or lava).
664: // Returns true if movement handling should continue after this point.
665: static bool _adjust_confused_movement(coord_def& move)
666: {
667:     if (you.cannot_move())
668:     {
669:         // Don't choose a random location to try to attack into - allows
670:         // abuse, since trying to move (not attack) takes no time, and
671:         // shouldn't. Just force confused trees to use ctrl.
672:         mpr(T_("You cannot move. (Use ctrl+direction or * direction to "
673:             "attack while stationary and confused.)"));
674:         return false;
675:     }
676:
677:     if (cancel_confused_move(false))
678:         return false;
679:
680:     if (cancel_harmful_move())
681:         return false;
682:
683:     if (!one_chance_in(3))
684:     {
685:         move.x = random2(3) - 1;
686:         move.y = random2(3) - 1;
687:         if (move.origin())
688:         {
689:             mpr(T_("You're too confused to move!"));
690:             you.turn_is_over = true;
691:             crawl_state.cancel_cmd_repeat();
692:             return false;
693:         }
694:     }
695:
696:     const coord_def new_targ = you.pos() + move;
697:
698:     // Test if our new location is somewhere we cannot move, and abort early if so.
```

A-08 trunk
```cpp
647:
648:     // Show the player the wall they've just bumped into, if they can't see it.
649:     if (you.current_vision == 0)
650:     {
651:         map_cell& knowledge = env.map_knowledge(targ);
652:         if (!knowledge.mapped() || knowledge.changed())
653:         {
654:             update_terrain_knowledge(targ);
655:             update_grid_colour_knowledge(targ);
656:             set_terrain_mapped(targ);
657:         }
658:     }
659: }
660:
661: // For confused players, adjust a passed movement direction randomly (with
662: // appropriate warning prompts) and possibly abort entirely if they try to
663: // stumble into a wall or lava).
664: // Returns true if movement handling should continue after this point.
665: static bool _adjust_confused_movement(coord_def& move)
666: {
667:     if (you.cannot_move())
668:     {
669:         // Don't choose a random location to try to attack into - allows
670:         // abuse, since trying to move (not attack) takes no time, and
671:         // shouldn't. Just force confused trees to use ctrl.
672:         mpr(T_("You cannot move. (Use ctrl+direction or * direction to "
673:             "attack while stationary and confused.)"));
674:         return false;
675:     }
676:
677:     // First check general things that make movement unwise (e.g barbs).
678:     if (cancel_harmful_move())
679:         return false;
680:
681:     // Now check the squares we might reach for warnings.
682:     if (!check_confused_move(false))
683:         return false;
684:
685:     // Randomise the move destination.
686:     if (!one_chance_in(3))
687:     {
688:         move.x = random2(3) - 1;
689:         move.y = random2(3) - 1;
690:         if (move.origin())
691:         {
692:             mpr(T_("You're too confused to move!"));
693:             you.turn_is_over = true;
694:             crawl_state.cancel_cmd_repeat();
695:             return false;
696:         }
697:     }
698:
```

A-05 stable
```cpp
496:     case DNGN_CLOSED_CLEAR_DOOR:
497:     case DNGN_RUNED_DOOR:
498:     case DNGN_RUNED_CLEAR_DOOR:
499:     case DNGN_SEALED_DOOR:
500:     case DNGN_SEALED_CLEAR_DOOR:
501:         mpr(T_("It's already closed!"));
502:         break;
503:     case DNGN_BROKEN_DOOR:
504:     case DNGN_BROKEN_CLEAR_DOOR:
505:         mpr(T_("It's broken and can't be closed!"));
506:         break;
507:     default:
508:         mpr(T_("There isn't anything that you can close there!"));
509:         break;
510:     }
511: }
512:
513: // Maybe prompt to enter a portal, return true if we should enter the
514: // portal, false if the user said no at the prompt.
515: bool prompt_dangerous_portal(dungeon_feature_type ftype)
516: {
517:     switch (ftype)
518:     {
519:     case DNGN_ENTER_PANDEMONIUM:
520:     case DNGN_ENTER_ZIGGURAT:
521:         return yesno(T_("If you enter this portal you might not be able to return "
522:                      "immediately. Continue?"), false, 'n');
523:     case DNGN_ENTER_ABYSS:
524:     {
525:         return yesno(make_stringf(T_("If you enter this portal you could be pulled as "
526:                      "deep as Abyss:%d and might not be able to return immediately. "
527:                      "Continue?"), abyss_default_depth(true)).c_str(), false, 'n');
528:     }
529:     default:
530:         return true;
531:     }
532: }
533:
534: bool prompt_descent_shortcut(dungeon_feature_type ftype)
535: {
536:     if (ftype == DNGN_ENTER_DEPTHS && !player_in_branch(BRANCH_SLIME)
537:         || ftype == DNGN_ENTER_SLIME && !player_in_branch(BRANCH_VAULTS))
538:     {
539:         return yesno(T_("This entrance appears to skip some branches and may be "
540:                      "quite dangerous. Continue anyway?"), false, 'n');
541:     }
542:     return true;
543: }
544:
545: static coord_def _rampage_destination(coord_def move, monster* target)
546: {
547:     const int dist = min(grid_distance(you.pos(), target->pos()) - 1,
```

A-05 trunk
```cpp
504:     case DNGN_CLOSED_CLEAR_DOOR:
505:     case DNGN_RUNED_DOOR:
506:     case DNGN_RUNED_CLEAR_DOOR:
507:     case DNGN_SEALED_DOOR:
508:     case DNGN_SEALED_CLEAR_DOOR:
509:         mpr(T_("It's already closed!"));
510:         break;
511:     case DNGN_BROKEN_DOOR:
512:     case DNGN_BROKEN_CLEAR_DOOR:
513:         mpr(T_("It's broken and can't be closed!"));
514:         break;
515:     default:
516:         mpr(T_("There isn't anything that you can close there!"));
517:         break;
518:     }
519: }
520:
521: // Maybe prompt to enter a portal, return true if we should enter the
522: // portal, false if the user said no at the prompt.
523: bool prompt_dangerous_portal(dungeon_feature_type ftype)
524: {
525:     switch (ftype)
526:     {
527:     case DNGN_ENTER_PANDEMONIUM:
528:     case DNGN_ENTER_ZIGGURAT:
529:         return yesno(T_("If you enter this portal you might not be able to return "
530:                      "immediately. Continue?"), false, 'n');
531:     case DNGN_ENTER_ABYSS:
532:     {
533:         return yesno(make_stringf(T_("If you enter this portal you could be pulled as "
534:                      "deep as Abyss:%d and might not be able to return immediately. "
535:                      "Continue?"), abyss_default_depth(true)).c_str(), false, 'n');
536:     }
537:     case DNGN_ENTER_GULCH:
538:         return yesno(T_("If you enter this portal, the magical contamination on the "
539:                      "other side will temporarily mutate you thrice. Continue?"), false, 'n');
540:     default:
541:         return true;
542:     }
543: }
544:
545: bool prompt_descent_shortcut(dungeon_feature_type ftype)
546: {
547:     if (ftype == DNGN_ENTER_DEPTHS && !player_in_branch(BRANCH_SLIME)
548:         || ftype == DNGN_ENTER_SLIME && !player_in_branch(BRANCH_VAULTS))
549:     {
550:         return yesno(T_("This entrance appears to skip some branches and may be "
551:                      "quite dangerous. Continue anyway?"), false, 'n');
552:     }
553:     return true;
554: }
555:
```

A-12 stable
```cpp
5213:
5214:     if (!es_flags)
5215:         return marker_stop;
5216:
5217:     say_any(items, "item");
5218:     say_any(shops, "shop");
5219:     say_any(apply_quantities(altars), "altar");
5220:     say_any(apply_quantities(portals), "portal");
5221:     say_any(apply_quantities(stairs), "stair");
5222:     say_any(apply_quantities(transporters), "transporter");
5223:     say_any(apply_quantities(runed_doors), "runed door");
5224:     say_any(apply_quantities(runelights), "runelights");
5225:
5226:     return true;
5227: }
5228:
5229: void do_interlevel_travel()
5230: {
5231:     if (Hints.hints_travel)
5232:         Hints.hints_travel = 0;
5233:
5234:     if (!can_travel_interlevel())
5235:     {
5236:         if (you.running.pos == you.pos())
5237:         {
5238:             mpr(T_("You're already here!"));
5239:             return;
5240:         }
5241:         else if (!you.running.pos.x || !you.running.pos.y)
5242:         {
5243:             mpr(T_("Sorry, you can't auto-travel out of here."));
5244:             return;
5245:         }
5246:
5247:         // Don't ask for a destination if you can only travel
5248:         // within level anyway.
5249:         start_travel(you.running.pos);
5250:     }
5251:     else
5252:         _start_translevel_travel_prompt();
5253:
5254:     if (you.running)
5255:         clear_messages();
5256: }
5257:
5258: #ifdef USE_TILE
5259: // (0,0) = same position is handled elsewhere.
5260: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5261: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5262:
5263: static const command_type cmd_array[8] =
```

A-12 stable
```cpp
5218:     say_any(shops, "shop");
5219:     say_any(apply_quantities(altars), "altar");
5220:     say_any(apply_quantities(portals), "portal");
5221:     say_any(apply_quantities(stairs), "stair");
5222:     say_any(apply_quantities(transporters), "transporter");
5223:     say_any(apply_quantities(runed_doors), "runed door");
5224:     say_any(apply_quantities(runelights), "runelights");
5225:
5226:     return true;
5227: }
5228:
5229: void do_interlevel_travel()
5230: {
5231:     if (Hints.hints_travel)
5232:         Hints.hints_travel = 0;
5233:
5234:     if (!can_travel_interlevel())
5235:     {
5236:         if (you.running.pos == you.pos())
5237:         {
5238:             mpr(T_("You're already here!"));
5239:             return;
5240:         }
5241:         else if (!you.running.pos.x || !you.running.pos.y)
5242:         {
5243:             mpr(T_("Sorry, you can't auto-travel out of here."));
5244:             return;
5245:         }
5246:
5247:         // Don't ask for a destination if you can only travel
5248:         // within level anyway.
5249:         start_travel(you.running.pos);
5250:     }
5251:     else
5252:         _start_translevel_travel_prompt();
5253:
5254:     if (you.running)
5255:         clear_messages();
5256: }
5257:
5258: #ifdef USE_TILE
5259: // (0,0) = same position is handled elsewhere.
5260: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5261: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5262:
5263: static const command_type cmd_array[8] =
5264: {
5265:     CMD_MOVE_DOWN_LEFT,  CMD_MOVE_DOWN,  CMD_MOVE_DOWN_RIGHT,
5266:     CMD_MOVE_LEFT,                       CMD_MOVE_RIGHT,
5267:     CMD_MOVE_UP_LEFT,    CMD_MOVE_UP,    CMD_MOVE_UP_RIGHT,
5268: };
```

A-12 trunk
```cpp
5321:                 mprf(C_("stair discovery", "Found %d stairs."), stair_count);
5322:             else
5323:                 mpr(message);
5324:         }
5325:     }
5326:     else
5327:         say_any(apply_quantities(stairs), "stair");
5328:     say_any(apply_quantities(hatches), N_("hatch"));
5329:     say_any(apply_quantities(transporters), "transporter");
5330:     say_any(apply_quantities(runed_doors), "runed door");
5331:     say_any(apply_quantities(runelights), "runelights");
5332:     say_any(apply_quantities(mutation_catalysts), "mutation catalysts");
5333:
5334:     return true;
5335: }
5336:
5337: void do_interlevel_travel()
5338: {
5339:     if (Hints.hints_travel)
5340:         Hints.hints_travel = 0;
5341:
5342:     if (!can_travel_interlevel())
5343:     {
5344:         if (you.running.pos == you.pos())
5345:         {
5346:             mpr(T_("You're already here!"));
5347:             return;
5348:         }
5349:         else if (!you.running.pos.x || !you.running.pos.y)
5350:         {
5351:             mpr(T_("Sorry, you can't auto-travel out of here."));
5352:             return;
5353:         }
5354:
5355:         // Don't ask for a destination if you can only travel
5356:         // within level anyway.
5357:         start_travel(you.running.pos);
5358:     }
5359:     else
5360:         _start_translevel_travel_prompt();
5361:
5362:     if (you.running)
5363:         clear_messages();
5364: }
5365:
5366: #ifdef USE_TILE
5367: // (0,0) = same position is handled elsewhere.
5368: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5369: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5370:
5371: static const command_type cmd_array[8] =
```

A-12 trunk
```cpp
5326:     else
5327:         say_any(apply_quantities(stairs), "stair");
5328:     say_any(apply_quantities(hatches), N_("hatch"));
5329:     say_any(apply_quantities(transporters), "transporter");
5330:     say_any(apply_quantities(runed_doors), "runed door");
5331:     say_any(apply_quantities(runelights), "runelights");
5332:     say_any(apply_quantities(mutation_catalysts), "mutation catalysts");
5333:
5334:     return true;
5335: }
5336:
5337: void do_interlevel_travel()
5338: {
5339:     if (Hints.hints_travel)
5340:         Hints.hints_travel = 0;
5341:
5342:     if (!can_travel_interlevel())
5343:     {
5344:         if (you.running.pos == you.pos())
5345:         {
5346:             mpr(T_("You're already here!"));
5347:             return;
5348:         }
5349:         else if (!you.running.pos.x || !you.running.pos.y)
5350:         {
5351:             mpr(T_("Sorry, you can't auto-travel out of here."));
5352:             return;
5353:         }
5354:
5355:         // Don't ask for a destination if you can only travel
5356:         // within level anyway.
5357:         start_travel(you.running.pos);
5358:     }
5359:     else
5360:         _start_translevel_travel_prompt();
5361:
5362:     if (you.running)
5363:         clear_messages();
5364: }
5365:
5366: #ifdef USE_TILE
5367: // (0,0) = same position is handled elsewhere.
5368: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5369: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5370:
5371: static const command_type cmd_array[8] =
5372: {
5373:     CMD_MOVE_DOWN_LEFT,  CMD_MOVE_DOWN,  CMD_MOVE_DOWN_RIGHT,
5374:     CMD_MOVE_LEFT,                       CMD_MOVE_RIGHT,
5375:     CMD_MOVE_UP_LEFT,    CMD_MOVE_UP,    CMD_MOVE_UP_RIGHT,
5376: };
```

E-05 stable
```cpp
3406:         break;
3407:     }
3408:
3409:     case ABIL_OKAWARU_HEROISM:
3410:         fail_check();
3411:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3412:              ? "You feel more confident with your borrowed prowess."
3413:              : "You gain the combat prowess of a mighty hero.");
3414:
3415:         you.increase_duration(DUR_HEROISM,
3416:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3417:                               100);
3418:         you.redraw_evasion      = true;
3419:         you.redraw_armour_class = true;
3420:         break;
3421:
3422:     case ABIL_OKAWARU_FINESSE:
3423:         fail_check();
3424:         if (you.duration[DUR_FINESSE])
3425:         {
3426:             // "Your [hand(s)] get{s} new energy."
3427:             mprf(MSGCH_DURATION, "%s",
3428:                  you.hands_act("get", "new energy.").c_str());
3429:         }
3430:         else
3431:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3432:
3433:         you.increase_duration(DUR_FINESSE,
3434:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3435:                               100);
3436:
3437:         did_god_conduct(DID_HASTY, 8); // Currently irrelevant.
3438:         break;
3439:
3440:     case ABIL_OKAWARU_DUEL:
3441:         return okawaru_duel(beam.target, fail);
3442:
3443:     case ABIL_OKAWARU_GIFT_WEAPON:
3444:         if (!okawaru_gift_weapon())
3445:             return spret::abort;
3446:         break;
3447:
3448:     case ABIL_OKAWARU_GIFT_ARMOUR:
3449:         if (!okawaru_gift_armour())
3450:             return spret::abort;
3451:         break;
3452:
3453:     case ABIL_MAKHLEB_ANNIHILATION:
3454:         return cast_iood(&you, _makhleb_annihilation_power(), &beam, 0, 0, MHITNOT,
3455:                          fail, false, MONS_GLOBE_OF_ANNIHILATION);
3456:
```

E-05 trunk
```cpp
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
3581:     case ABIL_OKAWARU_DUEL:
3582:         return okawaru_duel(beam.target, fail);
3583:
3584:     case ABIL_OKAWARU_GIFT_WEAPON:
3585:         if (!okawaru_gift_weapon())
3586:             return spret::abort;
3587:         break;
3588:
3589:     case ABIL_OKAWARU_GIFT_ARMOUR:
3590:         if (!okawaru_gift_armour())
3591:             return spret::abort;
3592:         break;
3593:
3594:     case ABIL_MAKHLEB_ANNIHILATION:
3595:         return cast_iood(&you, _makhleb_annihilation_power(), &beam, 0, 0, MHITNOT,
3596:                          fail, false, MONS_GLOBE_OF_ANNIHILATION);
3597:
3598:     case ABIL_MAKHLEB_DESTRUCTION:
```

C-03 stable
```cpp
1892:         // tiles players the opportunity to close the window and duplicate the
1893:         // item (a variant of bug #6486). However, we can't decrement the
1894:         // quantity before firing the position event, because the latter needs
1895:         // the object's index.
1896:         dec_mitm_item_quantity(obj, quant_got);
1897:
1898:         you.turn_is_over = true;
1899:     }
1900:
1901:     return keep_going;
1902: }
1903:
1904: static void _get_book(item_def& it)
1905: {
1906:     if (it.sub_type != BOOK_MANUAL)
1907:     {
1908:         if (you.has_mutation(MUT_INNATE_CASTER))
1909:         {
1910:             mprf(T_("%s burns to shimmering ash in your grasp."),
1911:                  it.name(DESC_THE).c_str());
1912:             return;
1913:         }
1914:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1915:
1916:         if (!library_add_spells(spells_in_book(it)))
1917:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1918:
1919:         taken_new_item(it.base_type);
1920:
1921:         return;
1922:     }
1923:     // This is mainly for save compat: if a manual generated somehow that is not
1924:     // id'd, the following message is completely useless
1925:     identify_item(it);
1926:     const skill_type sk = static_cast<skill_type>(it.plus);
1927:
1928:     if (is_useless_skill(sk))
1929:     {
1930:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1931:              it.name(DESC_A).c_str());
1932:         return;
1933:     }
1934:
1935:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1936:     {
1937:         mprf(T_("You pick up %s, but it has nothing more to teach you."),
1938:              it.name(DESC_A).c_str());
1939:         return;
1940:     }
1941:
1942:     if (you.skill_manual_points[sk])
```

C-03 trunk
```cpp
1855:         // tiles players the opportunity to close the window and duplicate the
1856:         // item (a variant of bug #6486). However, we can't decrement the
1857:         // quantity before firing the position event, because the latter needs
1858:         // the object's index.
1859:         dec_mitm_item_quantity(obj, quant_got);
1860:
1861:         you.turn_is_over = true;
1862:     }
1863:
1864:     return keep_going;
1865: }
1866:
1867: static void _get_book(item_def& it)
1868: {
1869:     if (it.sub_type != BOOK_MANUAL)
1870:     {
1871:         if (you.has_mutation(MUT_INNATE_CASTER))
1872:         {
1873:             mprf(T_("%s burns to shimmering ash in your grasp."),
1874:                  it.name(DESC_THE).c_str());
1875:             return;
1876:         }
1877:         mprf(T_("You pick up the %s and begin to read..."), it.name(DESC_A).c_str());
1878:
1879:         if (!library_add_spells(spells_in_book(it)))
1880:             mpr(T_("Unfortunately, you learned nothing new or useful."));
1881:
1882:         taken_new_item(it.base_type);
1883:
1884:         return;
1885:     }
1886:     // This is mainly for save compat: if a manual generated somehow that is not
1887:     // id'd, the following message is completely useless
1888:     identify_item(it);
1889:     const skill_type sk = static_cast<skill_type>(it.plus);
1890:
1891:     if (is_useless_skill(sk))
1892:     {
1893:         mprf(T_("You pick up %s. Unfortunately, it's quite useless to you."),
1894:              it.name(DESC_A).c_str());
1895:         return;
1896:     }
1897:
1898:     if (you.skills[sk] >= MAX_SKILL_LEVEL)
1899:     {
1900:         mprf(T_("You pick up %s, but it has nothing more to teach you."),
1901:              it.name(DESC_A).c_str());
1902:         return;
1903:     }
1904:
1905:     if (you.skill_manual_points[sk])
```

E-07 stable
```cpp
2812: static bool _abort_if_stationary()
2813: {
2814:     if (you.cannot_move())
2815:     {
2816:         canned_msg(MSG_CANNOT_MOVE);
2817:         return true;
2818:     }
2819:
2820:     return false;
2821: }
2822:
2823: static int _orb_of_dispater_power()
2824: {
2825:     return you.skill(SK_EVOCATIONS, 8);
2826: }
2827:
2828: static bool _evoke_orb_of_dispater(dist *target)
2829: {
2830:     int power = _orb_of_dispater_power();
2831:
2832:     if (your_spells(SPELL_HURL_DAMNATION, power, false, nullptr, target)
2833:         == spret::abort)
2834:     {
2835:         return false;
2836:     }
2837:     mpr(T_("You feel the orb feeding on your energy!"));
2838:     return true;
2839: }
2840:
2841: static bool _evoke_staff_of_olgreb(dist *target)
2842: {
2843:     int power = div_rand_round(20 + you.skill(SK_EVOCATIONS, 20), 4);
2844:
2845:     if (your_spells(SPELL_OLGREBS_TOXIC_RADIANCE, power, false, nullptr, target)
2846:         == spret::abort)
2847:     {
2848:         return false;
2849:     }
2850:     did_god_conduct(DID_WIZARDLY_ITEM, 10);
2851:     return true;
2852: }
2853:
2854: static vector<monster*> _get_siphon_victims(bool known)
2855: {
2856:     vector<monster*> victims;
2857:     for (monster_near_iterator mi(you.pos(), LOS_NO_TRANS); mi; ++mi)
2858:     {
2859:         if (grid_distance(you.pos(), mi->pos()) <= siphon_essence_range()
2860:             && siphon_essence_affects(**mi)
2861:             && (you.can_see(**mi) || !known))
2862:         {
```

E-07 trunk
```cpp
2956: static bool _abort_if_stationary()
2957: {
2958:     if (you.cannot_move())
2959:     {
2960:         canned_msg(MSG_CANNOT_MOVE);
2961:         return true;
2962:     }
2963:
2964:     return false;
2965: }
2966:
2967: static int _orb_of_dispater_power()
2968: {
2969:     return you.skill(SK_EVOCATIONS, 8);
2970: }
2971:
2972: static bool _evoke_orb_of_dispater(dist *target)
2973: {
2974:     int power = _orb_of_dispater_power();
2975:
2976:     if (your_spells(SPELL_HURL_DAMNATION, power, false, nullptr, target)
2977:         == spret::abort)
2978:     {
2979:         return false;
2980:     }
2981:     mpr(T_("You feel the orb feeding on your energy!"));
2982:     return true;
2983: }
2984:
2985: static bool _evoke_staff_of_olgreb(dist *target)
2986: {
2987:     int power = div_rand_round(20 + you.skill(SK_EVOCATIONS, 20), 4);
2988:
2989:     if (your_spells(SPELL_OLGREBS_TOXIC_RADIANCE, power, false, nullptr, target)
2990:         == spret::abort)
2991:     {
2992:         return false;
2993:     }
2994:     return true;
2995: }
2996:
2997: static vector<monster*> _get_siphon_victims(bool only_known)
2998: {
2999:     vector<monster*> victims;
3000:     for (monster_near_iterator mi(you.pos(), LOS_NO_TRANS); mi; ++mi)
3001:     {
3002:         if (grid_distance(you.pos(), mi->pos()) <= siphon_essence_range()
3003:             && siphon_essence_affects(**mi)
3004:             && (you.aware_of(**mi) || !only_known))
3005:         {
3006:             victims.push_back(*mi);
```

E-10 stable
```cpp
3313:             {
3314:                 return spret::abort;
3315:             }
3316:         }
3317:         fail_check();
3318:         cleansing_flame(_tso_cleansing_flame_power(),
3319:                         cleansing_flame_source::invocation, you.pos(), &you);
3320:         break;
3321:     }
3322:
3323:     case ABIL_TSO_SUMMON_DIVINE_WARRIOR:
3324:         return cast_summon_holy_warrior(you.skill(SK_INVOCATIONS, 4), fail);
3325:
3326:     case ABIL_TSO_BLESS_WEAPON:
3327:         simple_god_message(T_(" will bless one of your weapons."));
3328:         // included in default force_more_message
3329:         if (!bless_weapon(GOD_SHINING_ONE, SPWPN_HOLY_WRATH, YELLOW))
3330:             return spret::abort;
3331:         break;
3332:
3333:     case ABIL_KIKU_UNEARTH_WRETCHES:
3334:         return kiku_unearth_wretches(fail);
3335:
3336:     case ABIL_KIKU_SIGN_OF_RUIN:
3337:         fail_check();
3338:         mpr(T_("You invoke the name of Kikubaaqudgha!"));
3339:         cast_sign_of_ruin(you, beam.target,
3340:                           (4 + you.skill_rdiv(SK_NECROMANCY, 4, 7)) * BASELINE_DELAY);
3341:         break;
3342:
3343:     case ABIL_KIKU_BLESS_WEAPON:
3344:         simple_god_message(T_(" will bloody one of your weapons with pain."));
3345:         // included in default force_more_message
3346:         if (!bless_weapon(GOD_KIKUBAAQUDGHA, SPWPN_PAIN, RED))
3347:             return spret::abort;
3348:         break;
3349:
3350:     case ABIL_KIKU_GIFT_CAPSTONE_SPELLS:
3351:         if (!kiku_gift_capstone_spells())
3352:             return spret::abort;
3353:         break;
3354:
3355:     case ABIL_YRED_RECALL_UNDEAD_HARVEST:
3356:         fail_check();
3357:         do_player_recall(recall_t::yred);
3358:         break;
3359:
3360:     case ABIL_YRED_LIGHT_THE_TORCH:
3361:         yred_light_the_torch();
3362:         break;
3363:
```

E-10 trunk
```cpp
3455:
3456:     case ABIL_TSO_CLEANSING_FLAME:
3457:     {
3458:         fail_check();
3459:         mpr(T_("You channel a blast of cleansing flame!"));
3460:         cleansing_flame(_tso_cleansing_flame_power(),
3461:                         cleansing_flame_source::invocation, you.pos(), &you);
3462:         break;
3463:     }
3464:
3465:     case ABIL_TSO_SUMMON_DIVINE_WARRIOR:
3466:         return cast_summon_holy_warrior(you.skill(SK_INVOCATIONS, 4), fail);
3467:
3468:     case ABIL_TSO_BLESS_WEAPON:
3469:         simple_god_message(T_(" will bless one of your weapons."));
3470:         // included in default force_more_message
3471:         if (!bless_weapon(GOD_SHINING_ONE, SPWPN_HOLY_WRATH, YELLOW))
3472:             return spret::abort;
3473:         break;
3474:
3475:     case ABIL_KIKU_UNEARTH_WRETCHES:
3476:         return kiku_unearth_wretches(fail);
3477:
3478:     case ABIL_KIKU_SIGN_OF_RUIN:
3479:         fail_check();
3480:         mpr(T_("You invoke the name of Kikubaaqudgha!"));
3481:         cast_sign_of_ruin(you, beam.target,
3482:                           (4 + you.skill_rdiv(SK_NECROMANCY, 4, 7)) * BASELINE_DELAY);
3483:         break;
3484:
3485:     case ABIL_KIKU_BLESS_WEAPON:
3486:         simple_god_message(T_(" will bloody one of your weapons with pain."));
3487:         // included in default force_more_message
3488:         if (!bless_weapon(GOD_KIKUBAAQUDGHA, SPWPN_PAIN, RED))
3489:             return spret::abort;
3490:         break;
3491:
3492:     case ABIL_KIKU_GIFT_CAPSTONE_SPELLS:
3493:         if (!kiku_gift_capstone_spells())
3494:             return spret::abort;
3495:         break;
3496:
3497:     case ABIL_YRED_RECALL_UNDEAD_HARVEST:
3498:         fail_check();
3499:         do_player_recall(recall_t::yred);
3500:         break;
3501:
3502:     case ABIL_YRED_LIGHT_THE_TORCH:
3503:         yred_light_the_torch();
3504:         break;
3505:
```

A-11 stable
```cpp
261:     }
262: }
263:
264: static void _clear_golubria_traps()
265: {
266:     for (auto c : find_golubria_on_level())
267:     {
268:         trap_def *trap = trap_at(c);
269:         if (trap && trap->type == TRAP_GOLUBRIA)
270:             trap->destroy();
271:     }
272: }
273:
274: static void _remove_unstable_monsters()
275: {
276:     for (auto &mons : menv_real)
277:     {
278:         if (mons_class_flag(mons.type, M_UNSTABLE) && mons.is_summoned())
279:             mons.reset();
280:     }
281: }
282:
283: static void _complete_zig()
284: {
285:     if (!zot_immune())
286:         mpr(T_("You have traversed the Zig. Zot will no longer hunt you."));
287:     you.zigs_completed++;
288: }
289:
290: void leaving_level_now(dungeon_feature_type stair_used)
291: {
292:     if (stair_used == DNGN_EXIT_ZIGGURAT)
293:     {
294:         if (you.depth == 27)
295:             _complete_zig();
296:         mark_milestone("zig.exit", make_stringf("left a ziggurat at level %d.",
297:                        you.depth));
298:     }
299:
300:     if (stair_used == DNGN_EXIT_ABYSS)
301:     {
302: #ifdef DEBUG
303:         auto &vault_list =  you.vault_list[level_id::current()];
304:         vault_list.push_back("[exit]");
305: #endif
306:         clear_abyssal_rune_knowledge();
307:     }
308:
309:     // XXX: Don't consider things like banishment or Duel, which use 'stairs'
310:     //      internally, to actually be taking the stairs the player is standing
311:     //      on or it will also consume portal entrances.
```

A-11 trunk
```cpp
263: {
264:     if (you.attribute[ATTR_XOM_BLESSING] == XOM_BLESSING_GUARDIAN)
265:     {
266:         for (monster_iterator mi; mi; ++mi)
267:         {
268:             if (mons_is_xom_guardian(**mi))
269:             {
270:                 // Without this flag, the monster may only *sometimes* be placed
271:                 // when we enter the Abyss via banishment, which can result in
272:                 // them getting lost forever.
273:                 mi->flags |= MF_TAKING_STAIRS;
274:                 mi->set_transit(destination);
275:                 monster_die(**mi, KILL_RESET, NON_MONSTER);
276:             }
277:         }
278:     }
279:
280:     // No pulling mannequins between floors, even if you do it during the delay
281:     // between killing and gifting.
282:     you.props.erase(XOM_MANNEQUIN_TROUPE);
283: }
284:
285: static void _complete_zig()
286: {
287:     if (!zot_immune())
288:         mpr(T_("You have traversed the Zig. Zot will no longer hunt you."));
289:     you.zigs_completed++;
290: }
291:
292: void leaving_level_now(dungeon_feature_type stair_used, level_id destination)
293: {
294:     if (stair_used == DNGN_EXIT_ZIGGURAT)
295:     {
296:         if (you.depth == 27)
297:             _complete_zig();
298:         mark_milestone("zig.exit", make_stringf("left a ziggurat at level %d.",
299:                        you.depth));
300:     }
301:
302:     if (stair_used == DNGN_EXIT_ABYSS)
303:     {
304: #ifdef DEBUG
305:         auto &vault_list =  you.vault_list[level_id::current()];
306:         vault_list.push_back("[exit]");
307: #endif
308:         clear_abyssal_rune_knowledge();
309:         you.props.erase(ABYSS_AREAS_SEEN_KEY);
310:     }
311:
312:     // XXX: Don't consider things like banishment or Duel, which use 'stairs'
313:     //      internally, to actually be taking the stairs the player is standing
```

E-03 trunk
```cpp
3528:     {
3529:         monster* mons = monster_at(beam.target);
3530:
3531:         if (mons->is_illusion())
3532:         {
3533:             fail_check();
3534:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3535:                  mons->name(DESC_ITS).c_str(),
3536:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3537:             // Still costs a turn to gain the information.
3538:             return spret::success;
3539:         }
3540:
3541:         fail_check();
3542:
3543:         int pain = you.hp / 3;
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
```

E-03 trunk
```cpp
3528:     {
3529:         monster* mons = monster_at(beam.target);
3530:
3531:         if (mons->is_illusion())
3532:         {
3533:             fail_check();
3534:             mprf(T_("You attempt to bind %s soul, but %s is merely a clone!"),
3535:                  mons->name(DESC_ITS).c_str(),
3536:                  mons->pronoun(PRONOUN_SUBJECTIVE).c_str());
3537:             // Still costs a turn to gain the information.
3538:             return spret::success;
3539:         }
3540:
3541:         fail_check();
3542:
3543:         int pain = you.hp / 3;
3544:         dec_hp(pain, false);
3545:         mons->add_ench(mon_enchant(ENCH_SOUL_RIPE, &you, INFINITE_DURATION, pain));
3546:         mprf(T_("You wrap your dark will around %s soul!"),
3547:               mons->name(DESC_ITS).c_str());
3548:         break;
3549:     }
3550:
3551:     case ABIL_OKAWARU_HEROISM:
3552:         fail_check();
3553:         mprf(MSGCH_DURATION, you.duration[DUR_HEROISM]
3554:              ? T_("You feel more confident with your borrowed prowess.")
3555:              : T_("You gain the combat prowess of a mighty hero."));
3556:
3557:         you.increase_duration(DUR_HEROISM,
3558:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3559:                               100);
3560:         you.redraw_evasion      = true;
3561:         you.redraw_armour_class = true;
3562:         break;
3563:
3564:     case ABIL_OKAWARU_FINESSE:
3565:         fail_check();
3566:         if (you.duration[DUR_FINESSE])
3567:         {
3568:             // "Your [hand(s)] get{s} new energy."
3569:             mprf(MSGCH_DURATION, "%s",
3570:                  you.hands_act("get", "new energy.").c_str());
3571:         }
3572:         else
3573:             mprf(MSGCH_DURATION, T_("You can now deal lightning-fast blows."));
3574:
3575:         you.increase_duration(DUR_FINESSE,
3576:                               10 + random2avg(you.skill(SK_INVOCATIONS, 6), 2),
3577:                               100);
3578:
3579:         break;
3580:
```

D-10 stable
```cpp
3156:         if (!cancel_scroll)
3157:             mpr(pre_succ_msg);
3158:         // amusing to Xom, at least
3159:         bad_effect = result == spret::success && !player_res_poison();
3160:         break;
3161:     }
3162:
3163:     case SCR_ENCHANT_WEAPON:
3164:         if (!alreadyknown)
3165:         {
3166:             mpr(pre_succ_msg);
3167:             mpr(T_("It is a scroll of enchant weapon."));
3168:             // included in default force_more_message (to show it before menu)
3169:
3170:             run_uncancel(UNC_ENCHANT_WEAPON);
3171:         }
3172:         else
3173:             cancel_scroll = !_handle_enchant_weapon(alreadyknown, pre_succ_msg);
3174:
3175:         break;
3176:
3177:     case SCR_BRAND_WEAPON:
3178:         if (!alreadyknown)
3179:         {
3180:             mpr(pre_succ_msg);
3181:             mpr(T_("It is a scroll of brand weapon."));
3182:             // included in default force_more_message (to show it before menu)
3183:
3184:             run_uncancel(UNC_BRAND_WEAPON);
3185:         }
3186:         else
3187:             cancel_scroll = !_handle_brand_weapon(alreadyknown, pre_succ_msg);
3188:
3189:         break;
3190:
3191:     case SCR_IDENTIFY:
3192:         if (!alreadyknown)
3193:         {
3194:             mpr(pre_succ_msg);
3195:             mpr(T_("It is a scroll of identify."));
3196:             // included in default force_more_message (to show it before menu)
3197:             // Do this here so it doesn't turn up in the ID menu.
3198:             identify_item(*scroll);
3199:
3200:             run_uncancel(UNC_IDENTIFY);
3201:         }
3202:         else
3203:             cancel_scroll = !_identify(alreadyknown, pre_succ_msg);
3204:
3205:         break;
3206:
```

D-10 trunk
```cpp
3290:         if (result != spret::abort)
3291:             mpr(pre_succ_msg);
3292:         // amusing to Xom, at least
3293:         bad_effect = result == spret::success && !player_res_poison();
3294:         break;
3295:     }
3296:
3297:     case SCR_ENCHANT_WEAPON:
3298:         if (!alreadyknown)
3299:         {
3300:             mpr(pre_succ_msg);
3301:             mpr(T_("It is a scroll of enchant weapon."));
3302:             // included in default force_more_message (to show it before menu)
3303:
3304:             result = _run_read_scroll_uncancel(UNC_ENCHANT_WEAPON, *scroll);
3305:         }
3306:         else
3307:             result = _handle_enchant_weapon(alreadyknown, pre_succ_msg);
3308:
3309:         break;
3310:
3311:     case SCR_BRAND_WEAPON:
3312:         if (!alreadyknown)
3313:         {
3314:             mpr(pre_succ_msg);
3315:             mpr(T_("It is a scroll of brand weapon."));
3316:             // included in default force_more_message (to show it before menu)
3317:
3318:             result = _run_read_scroll_uncancel(UNC_BRAND_WEAPON, *scroll);
3319:         }
3320:         else
3321:             result = _handle_brand_weapon(alreadyknown, pre_succ_msg);
3322:
3323:         break;
3324:
3325:     case SCR_IDENTIFY:
3326:         if (!alreadyknown)
3327:         {
3328:             mpr(pre_succ_msg);
3329:             mpr(T_("It is a scroll of identify."));
3330:             // included in default force_more_message (to show it before menu)
3331:             // Do this here so it doesn't turn up in the ID menu.
3332:             identify_item(*scroll);
3333:
3334:             result = _run_read_scroll_uncancel(UNC_IDENTIFY, *scroll);
3335:         }
3336:         else
3337:             result = _identify(alreadyknown, pre_succ_msg);
3338:
3339:         break;
3340:
```

C-11 stable
```cpp
2377:         break;
2378:
2379:     case SPARM_SEE_INVISIBLE:
2380:         if (!you.can_see_invisible())
2381:         {
2382:             mpr(T_("You feel less perceptive."));
2383:             _mark_unseen_monsters();
2384:         }
2385:         break;
2386:
2387:     case SPARM_STRENGTH:
2388:         notify_stat_change(STAT_STR, -3, false);
2389:         break;
2390:
2391:     case SPARM_DEXTERITY:
2392:         notify_stat_change(STAT_DEX, -3, false);
2393:         break;
2394:
2395:     case SPARM_INTELLIGENCE:
2396:         notify_stat_change(STAT_INT, -3, false);
2397:         break;
2398:
2399:     case SPARM_PONDEROUSNESS:
2400:     {
2401:         // XX can the noun here be derived from the species walking verb?
2402:         mpr(you.species == SP_NAGA
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
```

C-11 stable
```cpp
2377:         break;
2378:
2379:     case SPARM_SEE_INVISIBLE:
2380:         if (!you.can_see_invisible())
2381:         {
2382:             mpr(T_("You feel less perceptive."));
2383:             _mark_unseen_monsters();
2384:         }
2385:         break;
2386:
2387:     case SPARM_STRENGTH:
2388:         notify_stat_change(STAT_STR, -3, false);
2389:         break;
2390:
2391:     case SPARM_DEXTERITY:
2392:         notify_stat_change(STAT_DEX, -3, false);
2393:         break;
2394:
2395:     case SPARM_INTELLIGENCE:
2396:         notify_stat_change(STAT_INT, -3, false);
2397:         break;
2398:
2399:     case SPARM_PONDEROUSNESS:
2400:     {
2401:         // XX can the noun here be derived from the species walking verb?
2402:         mpr(you.species == SP_NAGA
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
```

C-11 trunk
```cpp
2461:         break;
2462:
2463:     case SPARM_SEE_INVISIBLE:
2464:         if (!you.can_see_invisible())
2465:         {
2466:             mpr(T_("You feel less perceptive."));
2467:             _mark_unseen_monsters();
2468:         }
2469:         break;
2470:
2471:     case SPARM_STRENGTH:
2472:         notify_stat_change(STAT_STR, -3, false);
2473:         break;
2474:
2475:     case SPARM_DEXTERITY:
2476:         notify_stat_change(STAT_DEX, -3, false);
2477:         break;
2478:
2479:     case SPARM_INTELLIGENCE:
2480:         notify_stat_change(STAT_INT, -3, false);
2481:         break;
2482:
2483:     case SPARM_PONDEROUSNESS:
2484:     {
2485:         // XX can the noun here be derived from the species walking verb?
2486:         mpr(you.species == SP_NAGA
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
```

C-11 trunk
```cpp
2461:         break;
2462:
2463:     case SPARM_SEE_INVISIBLE:
2464:         if (!you.can_see_invisible())
2465:         {
2466:             mpr(T_("You feel less perceptive."));
2467:             _mark_unseen_monsters();
2468:         }
2469:         break;
2470:
2471:     case SPARM_STRENGTH:
2472:         notify_stat_change(STAT_STR, -3, false);
2473:         break;
2474:
2475:     case SPARM_DEXTERITY:
2476:         notify_stat_change(STAT_DEX, -3, false);
2477:         break;
2478:
2479:     case SPARM_INTELLIGENCE:
2480:         notify_stat_change(STAT_INT, -3, false);
2481:         break;
2482:
2483:     case SPARM_PONDEROUSNESS:
2484:     {
2485:         // XX can the noun here be derived from the species walking verb?
2486:         mpr(you.species == SP_NAGA
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
```

E-08 stable
```cpp
1020:
1021:                 if (isaalpha(keyin) || key_is_escape(keyin))
1022:                     break;
1023:                 else
1024:                     clear_messages();
1025:
1026:                 keyin = 0;
1027:             }
1028:             else
1029:                 break;
1030:         }
1031:
1032:         if (key_is_escape(keyin))
1033:         {
1034:             canned_msg(MSG_OK);
1035:             crawl_state.zero_turns_taken();
1036:             return spret::abort;
1037:         }
1038:         else if (Options.enable_recast_spell
1039:                  && (keyin == '.' || keyin == CK_ENTER))
1040:         {
1041:             spell = you.last_cast_spell;
1042:         }
1043:         else if (!isaalpha(keyin))
1044:         {
1045:             mpr(T_("You don't know that spell."));
1046:             crawl_state.zero_turns_taken();
1047:             return spret::abort;
1048:         }
1049:         else
1050:             spell = get_spell_by_letter(keyin);
1051:     }
1052:
1053:     if (spell == SPELL_NO_SPELL)
1054:     {
1055:         mpr(T_("You don't know that spell."));
1056:         crawl_state.zero_turns_taken();
1057:         return spret::abort;
1058:     }
1059:
1060:     // MP, confusion, Ru sacs
1061:     const auto reason = casting_uselessness_reason(spell, true);
1062:     if (!reason.empty())
1063:     {
1064:         mpr(reason);
1065:         crawl_state.zero_turns_taken();
1066:         return spret::abort;
1067:     }
1068:
1069:     if (check_range && spell_no_hostile_in_range(spell))
1070:     {
```

E-08 trunk
```cpp
1050:
1051:                 if (isaalpha(keyin) || key_is_escape(keyin))
1052:                     break;
1053:                 else
1054:                     clear_messages();
1055:
1056:                 keyin = 0;
1057:             }
1058:             else
1059:                 break;
1060:         }
1061:
1062:         if (key_is_escape(keyin))
1063:         {
1064:             canned_msg(MSG_OK);
1065:             crawl_state.zero_turns_taken();
1066:             return spret::abort;
1067:         }
1068:         else if (Options.enable_recast_spell
1069:                  && (keyin == '.' || keyin == CK_ENTER))
1070:         {
1071:             spell = you.last_cast_spell;
1072:         }
1073:         else if (!isaalpha(keyin))
1074:         {
1075:             mpr(T_("You don't know that spell."));
1076:             crawl_state.zero_turns_taken();
1077:             return spret::abort;
1078:         }
1079:         else
1080:             spell = get_spell_by_letter(keyin);
1081:     }
1082:
1083:     if (spell == SPELL_NO_SPELL)
1084:     {
1085:         mpr(T_("You don't know that spell."));
1086:         crawl_state.zero_turns_taken();
1087:         return spret::abort;
1088:     }
1089:
1090:     // MP, confusion, Ru sacs
1091:     bool god_forbids = false;
1092:     const auto reason = casting_uselessness_reason(spell, true, &god_forbids);
1093:     if (!reason.empty())
1094:     {
1095:         mprf(god_forbids ? MSGCH_GOD : MSGCH_PLAIN, "%s", reason.c_str());
1096:         crawl_state.zero_turns_taken();
1097:         return spret::abort;
1098:     }
1099:
1100:     const bool needs_target = testbits(get_spell_flags(spell),
```

E-08 trunk
```cpp
1060:         }
1061:
1062:         if (key_is_escape(keyin))
1063:         {
1064:             canned_msg(MSG_OK);
1065:             crawl_state.zero_turns_taken();
1066:             return spret::abort;
1067:         }
1068:         else if (Options.enable_recast_spell
1069:                  && (keyin == '.' || keyin == CK_ENTER))
1070:         {
1071:             spell = you.last_cast_spell;
1072:         }
1073:         else if (!isaalpha(keyin))
1074:         {
1075:             mpr(T_("You don't know that spell."));
1076:             crawl_state.zero_turns_taken();
1077:             return spret::abort;
1078:         }
1079:         else
1080:             spell = get_spell_by_letter(keyin);
1081:     }
1082:
1083:     if (spell == SPELL_NO_SPELL)
1084:     {
1085:         mpr(T_("You don't know that spell."));
1086:         crawl_state.zero_turns_taken();
1087:         return spret::abort;
1088:     }
1089:
1090:     // MP, confusion, Ru sacs
1091:     bool god_forbids = false;
1092:     const auto reason = casting_uselessness_reason(spell, true, &god_forbids);
1093:     if (!reason.empty())
1094:     {
1095:         mprf(god_forbids ? MSGCH_GOD : MSGCH_PLAIN, "%s", reason.c_str());
1096:         crawl_state.zero_turns_taken();
1097:         return spret::abort;
1098:     }
1099:
1100:     const bool needs_target = testbits(get_spell_flags(spell),
1101:                                        spflag::needs_target);
1102:     if ((check_range || needs_target) && spell_no_hostile_in_range(spell))
1103:     {
1104:         // Abort if there are no hostiles within range, but flash the range
1105:         // markers for a short while.
1106:         mpr(needs_target
1107:             ? T_("You can't see any susceptible monsters within range!")
1108:             : T_("You can't see any susceptible monsters within range! (Use <w>Z</w> to cast anyway.)"));
1109:
1110:         if ((Options.use_animations & UA_RANGE) && Options.darken_beyond_range)
```

A-09 stable
```cpp
544:
545:     switch (random2(3))
546:     {
547:         case 0:
548:             you.doom(20);
549:             break;
550:         case 1:
551:             drain_player(85, true, true);
552:             break;
553:         default:
554:             break;
555:     }
556: }
557:
558: static void _vainglory_arrival()
559: {
560:     vector<monster*> mons;
561:     for (monster_near_iterator mi(you.pos()); mi; ++mi)
562:     {
563:         if (!mi->is_firewood() && !mi->wont_attack())
564:             mons.push_back(*mi);
565:     }
566:
567:     if (!mons.empty())
568:     {
569:         mprf(MSGCH_WARN, T_("You announce your regal presence to all who look upon you."));
570:         for (monster* mon : mons)
571:             behaviour_event(mon, ME_ANNOY, &you);
572:
573:         you.duration[DUR_VAINGLORY] = random_range(120, 220);
574:     }
575: }
576:
577: static void _new_level_amuses_xom(dungeon_feature_type feat,
578:                                   dungeon_feature_type old_feat,
579:                                   bool shaft, int shaft_depth, bool voluntary)
580: {
581:     switch (you.where_are_you)
582:     {
583:     default:
584:         // Xom thinks it's funny if you enter a new level via shaft
585:         // or escape hatch, for shafts it's funnier the deeper you fell.
586:         if (shaft || feat_is_escape_hatch(feat))
587:             xom_is_stimulated(shaft_depth * 50);
588:         else if (!is_connected_branch(you.where_are_you))
589:             xom_is_stimulated(25);
590:         else
591:             xom_is_stimulated(10);
592:         break;
593:
594:     case BRANCH_ZIGGURAT:
```

A-09 trunk
```cpp
556:
557:     switch (random2(3))
558:     {
559:         case 0:
560:             you.doom(20);
561:             break;
562:         case 1:
563:             drain_player(85, true, true);
564:             break;
565:         default:
566:             break;
567:     }
568: }
569:
570: static void _vainglory_arrival()
571: {
572:     vector<monster*> mons;
573:     for (monster_near_iterator mi(you.pos()); mi; ++mi)
574:     {
575:         if (!mi->is_firewood() && !mi->wont_attack())
576:             mons.push_back(*mi);
577:     }
578:
579:     if (!mons.empty())
580:     {
581:         mprf(MSGCH_WARN, T_("You announce your regal presence to all who look upon you."));
582:         for (monster* mon : mons)
583:             behaviour_event(mon, ME_ANNOY, &you);
584:
585:         you.duration[DUR_VAINGLORY] = random_range(120, 220);
586:     }
587: }
588:
589: static void _new_level_amuses_xom(dungeon_feature_type feat,
590:                                   dungeon_feature_type old_feat,
591:                                   bool shaft, int shaft_depth, bool voluntary)
592: {
593:     switch (you.where_are_you)
594:     {
595:     default:
596:         // Xom thinks it's funny if you enter a new level via shaft
597:         // or escape hatch, for shafts it's funnier the deeper you fell.
598:         if (shaft || feat_is_escape_hatch(feat))
599:             xom_is_stimulated(shaft_depth * 50);
600:         else if (!is_connected_branch(you.where_are_you))
601:             xom_is_stimulated(25);
602:         else
603:             xom_is_stimulated(10);
604:         break;
605:
606:     case BRANCH_ZIGGURAT:
```

B-10 stable
```cpp
4016:         nasty = false;
4017:         nice  = true;
4018:         break;
4019:
4020:     case BEAM_UNRAVELLING:
4021:         if (!player_is_debuffable())
4022:             break;
4023:
4024:         // If the player is unravelling themselves voluntarily, allow it to work.
4025:         debuff_player(agent() && agent()->is_player());
4026:         _unravelling_explode(*this);
4027:         obvious_effect = true;
4028:         break;
4029:
4030:     case BEAM_SOUL_SPLINTER:
4031:         obvious_effect = true;
4032:         if (you.holiness() & (MH_NATURAL | MH_DEMONIC | MH_HOLY))
4033:             make_soul_wisp(*agent(), you);
4034:         else
4035:             canned_msg(MSG_YOU_UNAFFECTED);
4036:         break;
4037:
4038:     case BEAM_ILL_OMEN:
4039:         obvious_effect = true;
4040:         if (!you.doom(random_range(16, 30) + ench_power / 20))
4041:             mpr(T_("You feel an ill-omen...."));
4042:         break;
4043:
4044:     case BEAM_ENFEEBLE:
4045:         obvious_effect = true;
4046:         enfeeble_player(agent(), ench_power);
4047:         break;
4048:
4049:     case BEAM_WARP_BODY:
4050:         obvious_effect = true;
4051:         mpr(T_("Your body is warped painfully!"));
4052:         if (temp_mutation_count() >= 3)
4053:             you.vitrify(agent(), random_range(12, 22));
4054:         else
4055:             temp_mutate(RANDOM_CORRUPT_MUTATION, "warp body");
4056:         you.hurt(agent(), damage.roll(), BEAM_WARP_BODY, KILLED_BY_BEAM);
4057:         break;
4058:
4059:     default:
4060:         // _All_ enchantments should be enumerated here!
4061:         mpr(T_("Software bugs nibble your toes!"));
4062:         break;
4063:     }
4064:
4065:     if (nasty)
4066:     {
```

B-10 trunk
```cpp
4095:         nasty = false;
4096:         nice  = true;
4097:         break;
4098:
4099:     case BEAM_UNRAVELLING:
4100:         if (!player_is_debuffable())
4101:             break;
4102:
4103:         // If the player is unravelling themselves voluntarily, allow it to work.
4104:         debuff_player(agent() && agent()->is_player());
4105:         _unravelling_explode(*this);
4106:         obvious_effect = true;
4107:         break;
4108:
4109:     case BEAM_SOUL_SPLINTER:
4110:         obvious_effect = true;
4111:         if (you.has_soul())
4112:             make_soul_wisp(*agent(), you);
4113:         else
4114:             canned_msg(MSG_YOU_UNAFFECTED);
4115:         break;
4116:
4117:     case BEAM_ILL_OMEN:
4118:         obvious_effect = true;
4119:         if (!you.doom(random_range(16, 30) + ench_power / 20))
4120:             mpr(T_("You feel an ill-omen...."));
4121:         break;
4122:
4123:     case BEAM_ENFEEBLE:
4124:         obvious_effect = true;
4125:         enfeeble_player(agent(), ench_power);
4126:         break;
4127:
4128:     case BEAM_WARP_BODY:
4129:         obvious_effect = true;
4130:         mpr(T_("Your body is warped painfully!"));
4131:         if (temp_mutation_count() >= 3)
4132:             you.vitrify(agent(), random_range(12, 22));
4133:         else
4134:             temp_mutate(RANDOM_CORRUPT_MUTATION, "warp body");
4135:         you.hurt(agent(), damage.roll(), BEAM_WARP_BODY, KILLED_BY_BEAM);
4136:         break;
4137:
4138:     default:
4139:         // _All_ enchantments should be enumerated here!
4140:         mpr(T_("Software bugs nibble your toes!"));
4141:         break;
4142:     }
4143:
4144:     if (nasty)
4145:     {
```

E-12 stable
```cpp
1064:         mpr(reason);
1065:         crawl_state.zero_turns_taken();
1066:         return spret::abort;
1067:     }
1068:
1069:     if (check_range && spell_no_hostile_in_range(spell))
1070:     {
1071:         // Abort if there are no hostiles within range, but flash the range
1072:         // markers for a short while.
1073:         mpr(T_("You can't see any susceptible monsters within range! (Use <w>Z</w> to cast anyway.)"));
1074:
1075:         if ((Options.use_animations & UA_RANGE) && Options.darken_beyond_range)
1076:         {
1077:             targeter_smite range(&you, spell_range(spell, &you), 0, 0, false, true);
1078:             range_view_annotator show_range(&range);
1079:             delay(50);
1080:         }
1081:         crawl_state.zero_turns_taken();
1082:         return spret::abort;
1083:     }
1084:
1085:     if (god_punishes_spell(spell, you.religion)
1086:         && !crawl_state.disables[DIS_CONFIRMATIONS])
1087:     {
1088:         // None currently dock just piety, right?
1089:         if (!yesno(T_("Casting this spell will place you under penance. "
1090:                    "Really cast?"), true, 'n'))
1091:         {
1092:             canned_msg(MSG_OK);
1093:             crawl_state.zero_turns_taken();
1094:             return spret::abort;
1095:         }
1096:     }
1097:
1098:     you.last_cast_spell = spell;
1099:     // Silently take MP before the spell.
1100:     const int cost = spell_mana(spell);
1101:     pay_mp(cost);
1102:
1103:     // Needs to happen after hp costs from HP casting
1104:     const int hp_cost = _spell_addition_hp_cost(spell);
1105:     if (hp_cost)
1106:         pay_hp(hp_cost);
1107:
1108:     const spret cast_result = your_spells(spell, 0, !you.divine_exegesis,
1109:                                           nullptr, _target, force_failure);
1110:     if (cast_result == spret::abort
1111:         || you.divine_exegesis && cast_result == spret::fail)
1112:     {
1113:         if (cast_result == spret::abort)
1114:             crawl_state.zero_turns_taken();
1115:         // Return the MP since the spell is aborted.
```

B-11 stable
```cpp
266:     }
267:     return chance / 100;
268: }
269:
270: // Bring up an inventory screen and have user choose an item.
271: // Returns an item slot, or -1 on abort/failure
272: // On failure, returns error text, if any.
273: // TODO: consolidate with menu code in quiver.cc?
274: static shared_ptr<quiver::action> _fire_prompt_for_item()
275: {
276:     if (inv_count() < 1)
277:         return nullptr;
278:
279:     // should this sound happen for `f` too? Not sure what the intent is
280: #ifdef USE_SOUND
281:     parse_sound(FIRE_PROMPT_SOUND);
282: #endif
283:
284:     const bool fireables = any_items_of_type(OSEL_QUIVER_ACTION);
285:     if (!fireables)
286:     {
287:         // TODO: right now disabled but valid items don't trigger this;
288:         // possibly they should get a similar message? They all do print a
289:         // more specific message if you try to use them, and some have a
290:         // prompt or the like (e.g. scroll of fear).
291:         mpr(T_("You have nothing you can fire or use right now."));
292:         return make_shared<quiver::action>(); // hack: prevent "Ok, then."
293:     }
294:
295:     // does it actually make sense that felid can't toss things?
296:     const bool can_throw = !you.has_mutation(MUT_NO_GRASPING)
297:         && !fire_warn_if_impossible(true, you.weapon()); // forms
298:
299:     int slot = -1;
300:     const string title = can_throw
301:         ? T_("<lightgray>Fire/throw/use which item?</lightgray>")
302:         : T_("<lightgray>Fire/use which item?</lightgray>");
303:     // TODO: the output api here is awkward
304:     // TODO: it would be nice if items with disabled actions got grayed out
305:     slot = prompt_invent_item(
306:                 title.c_str(),
307:                 menu_type::invlist,
308:                 OSEL_QUIVER_ACTION, OPER_FIRE,
309:                 invprompt_flag::no_warning, // warning handled in quiver
310:                 '\0');
311:     if (slot == -1)
312:         return nullptr;
313:
314:     return quiver::slot_to_action(slot);
315: }
316:
```

B-11 trunk
```cpp
284:     }
285:     return chance / 100;
286: }
287:
288: // Bring up an inventory screen and have user choose an item.
289: // Returns an item slot, or -1 on abort/failure
290: // On failure, returns error text, if any.
291: // TODO: consolidate with menu code in quiver.cc?
292: static shared_ptr<quiver::action> _fire_prompt_for_item()
293: {
294:     if (inv_count() < 1)
295:         return nullptr;
296:
297:     // should this sound happen for `f` too? Not sure what the intent is
298: #ifdef USE_SOUND
299:     parse_sound(FIRE_PROMPT_SOUND);
300: #endif
301:
302:     const bool fireables = any_items_of_type(OSEL_QUIVER_ACTION);
303:     if (!fireables)
304:     {
305:         // TODO: right now disabled but valid items don't trigger this;
306:         // possibly they should get a similar message? They all do print a
307:         // more specific message if you try to use them, and some have a
308:         // prompt or the like (e.g. scroll of fear).
309:         mpr(T_("You have nothing you can fire or use right now."));
310:         return make_shared<quiver::action>(); // hack: prevent "Ok, then."
311:     }
312:
313:     // does it actually make sense that felid can't toss things?
314:     const bool can_throw = !you.has_mutation(MUT_NO_GRASPING)
315:         && !fire_warn_if_impossible(true, you.weapon()); // forms
316:
317:     int slot = -1;
318:     const string title = can_throw
319:         ? T_("<lightgray>Fire/throw/use which item?</lightgray>")
320:         : T_("<lightgray>Fire/use which item?</lightgray>");
321:     // TODO: the output api here is awkward
322:     // TODO: it would be nice if items with disabled actions got grayed out
323:     slot = prompt_invent_item(
324:                 title.c_str(),
325:                 menu_type::invlist,
326:                 OSEL_QUIVER_ACTION, OPER_FIRE,
327:                 invprompt_flag::no_warning, // warning handled in quiver
328:                 '\0');
329:     if (slot == -1)
330:         return nullptr;
331:
332:     return quiver::slot_to_action(slot);
333: }
334:
```

F-09 stable
```cpp
4053:
4054:         if (you.magic_points == you.max_magic_points)
4055:             you.check_mp_regen_attunement = true;
4056:     }
4057: }
4058:
4059: void flush_mp()
4060: {
4061:     if (Options.magic_point_warning
4062:         && you.magic_points < you.max_magic_points
4063:                               * Options.magic_point_warning / 100)
4064:     {
4065:         mprf(MSGCH_DANGER, T_("* * * LOW MAGIC WARNING * * *"));
4066:     }
4067:
4068:     take_note(Note(NOTE_MP_CHANGE, you.magic_points, you.max_magic_points));
4069:     you.redraw_magic_points = true;
4070: }
4071:
4072: void flush_hp()
4073: {
4074:     if (Options.hp_warning
4075:         && you.hp <= (you.hp_max * Options.hp_warning) / 100)
4076:     {
4077:         flash_view_delay(UA_HP, RED, 50);
4078:         mprf(MSGCH_DANGER, T_("* * * LOW HITPOINT WARNING * * *"));
4079:         dungeon_events.fire_event(DET_HP_WARNING);
4080:     }
4081:     you.redraw_hit_points = true;
4082: }
4083:
4084: static void _dec_mp(int mp_loss, bool silent)
4085: {
4086:     ASSERT(!crawl_state.game_is_arena());
4087:
4088:     if (mp_loss < 1)
4089:         return;
4090:
4091:     you.magic_points -= mp_loss;
4092:
4093:     you.magic_points = max(0, you.magic_points);
4094:     if (!silent)
4095:         flush_mp();
4096: }
4097:
4098: void drain_mp(int mp_loss, bool ignore_resistance)
4099: {
4100:     if (!ignore_resistance && you.has_mutation(MUT_INVIOLATE_MAGIC))
4101:         mp_loss = mp_loss / 3;
4102:
4103:     _dec_mp(mp_loss, false);
```

F-09 trunk
```cpp
4264:
4265:         if (you.magic_points == you.max_magic_points)
4266:             you.check_mp_regen_attunement = true;
4267:     }
4268: }
4269:
4270: void flush_mp()
4271: {
4272:     if (Options.magic_point_warning
4273:         && you.magic_points < you.max_magic_points
4274:                               * Options.magic_point_warning / 100)
4275:     {
4276:         mprf(MSGCH_DANGER, T_("* * * LOW MAGIC WARNING * * *"));
4277:     }
4278:
4279:     take_note(Note(NOTE_MP_CHANGE, you.magic_points, you.max_magic_points));
4280:     you.redraw_magic_points = true;
4281: }
4282:
4283: void flush_hp()
4284: {
4285:     if (Options.hp_warning
4286:         && you.hp <= (you.hp_max * Options.hp_warning) / 100)
4287:     {
4288:         flash_view_delay(UA_HP, RED, 50);
4289:         mprf(MSGCH_DANGER, T_("* * * LOW HITPOINT WARNING * * *"));
4290:         dungeon_events.fire_event(DET_HP_WARNING);
4291:     }
4292:     you.redraw_hit_points = true;
4293: }
4294:
4295: static void _dec_mp(int mp_loss, bool silent)
4296: {
4297:     ASSERT(!crawl_state.game_is_arena());
4298:
4299:     if (mp_loss < 1)
4300:         return;
4301:
4302:     you.magic_points -= mp_loss;
4303:
4304:     you.magic_points = max(0, you.magic_points);
4305:     if (!silent)
4306:         flush_mp();
4307: }
4308:
4309: void drain_mp(int mp_loss, bool ignore_resistance)
4310: {
4311:     if (!ignore_resistance && you.has_mutation(MUT_INVIOLATE_MAGIC))
4312:         mp_loss = mp_loss / 3;
4313:
4314:     _dec_mp(mp_loss, false);
```

A-03 trunk
```cpp
1210:                          || swap_check(mon_at, dummy, true))))
1211:             {
1212:                 break;
1213:             }
1214:         }
1215:
1216:         // Check for moving *over* all spaces but our destination.
1217:         // (ie: ignore clouds, since we don't expect to be staying here).
1218:         if (i == end_step)
1219:         {
1220:             if (!check_moveto(targ, move_verb))
1221:                 return;
1222:         }
1223:         // At the destination, also warn about clouds and similar.
1224:         else if (!check_move_over(targ, move_verb))
1225:             return;
1226:     }
1227:
1228:     const bool did_tailwind = num_steps > 1 && you.duration[DUR_TAILWIND];
1229:     if (did_tailwind)
1230:         you.duration[DUR_TAILWIND] = 0;
1231:
1232:     // Print a message, if rampaging.
1233:     if (num_steps > 1 && mon_target)
1234:     {
1235:         mprf_p(T_("You %s towards %s%s!"),
1236:                 translated_move_phrase(move_verb.c_str(),
1237:                                        move_phrase_context::toward_target),
1238:                 mon_target->name(DESC_THE, true).c_str(),
1239:                 did_tailwind ? T_(" with incredible speed") : "");
1240:
1241:         // Prevent full-LoS stabbing with Seven League Boots.
1242:         if (you.unrand_equipped(UNRAND_SEVEN_LEAGUE_BOOTS))
1243:             behaviour_event(mon_target, ME_ALERT, &you, you.pos());
1244:     }
1245:
1246:     // Now, we can assume the player has been fully prompted for any movement,
1247:     // so take each step in order (tracking whether we actually moved or attack,
1248:     // and how much time it took to move through each space).
1249:     const coord_def initial_pos = you.pos();
1250:     targ = you.pos();
1251:     int delay = 0;
1252:     int delay_scale = 60;
1253:     int steps_taken = 0;
1254:     bool did_move = false;
1255:     bool did_attack = false;
1256:     bool did_open_door = false;
1257:     bool did_stampede = false;
1258:     for (; steps_taken < num_steps; ++steps_taken)
1259:     {
1260:         // If we have somehow ended up somewhere other than where we tried
1261:         // to move (likely due to a trap), abort any further steps.
1262:         if (you.pos() != targ || you.caught())
1263:             break;
1264:
```

C-04 stable
```cpp
2390:
2391:     case SPARM_DEXTERITY:
2392:         notify_stat_change(STAT_DEX, -3, false);
2393:         break;
2394:
2395:     case SPARM_INTELLIGENCE:
2396:         notify_stat_change(STAT_INT, -3, false);
2397:         break;
2398:
2399:     case SPARM_PONDEROUSNESS:
2400:     {
2401:         // XX can the noun here be derived from the species walking verb?
2402:         mpr(you.species == SP_NAGA
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
```

C-04 stable
```cpp
2394:
2395:     case SPARM_INTELLIGENCE:
2396:         notify_stat_change(STAT_INT, -3, false);
2397:         break;
2398:
2399:     case SPARM_PONDEROUSNESS:
2400:     {
2401:         // XX can the noun here be derived from the species walking verb?
2402:         mpr(you.species == SP_NAGA
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
```

C-04 stable
```cpp
2399:     case SPARM_PONDEROUSNESS:
2400:     {
2401:         // XX can the noun here be derived from the species walking verb?
2402:         mpr(you.species == SP_NAGA
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
```

C-04 stable
```cpp
2403:             ? T_("That put a bit of spring back into your slither.")
2404:             : T_("That put a bit of spring back into your step."));
2405:         break;
2406:     }
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
```

C-04 stable
```cpp
2407:
2408:     case SPARM_FLYING:
2409:         // XXX: Landing must be deferred until after form is actually changed.
2410:         if (!meld)
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
```

C-04 stable
```cpp
2411:             land_player();
2412:         break;
2413:
2414:     case SPARM_WILLPOWER:
2415:         mpr(T_("You feel less strong-willed."));
2416:         break;
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
```

C-04 stable
```cpp
2417:
2418:     case SPARM_PROTECTION:
2419:         mpr(T_("You feel less protected."));
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
```

C-04 stable
```cpp
2420:         break;
2421:
2422:     case SPARM_STEALTH:
2423:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2424:             mpr(T_("You feel less stealthy."));
2425:         break;
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
```

C-04 stable
```cpp
2426:
2427:     case SPARM_RESISTANCE:
2428:         mpr(T_("You feel hot and cold all over."));
2429:         break;
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2471:         break;
2472:
2473:     case SPARM_LIGHT:
2474:         invalidate_agrid(true);
2475:         break;
2476:
```

C-04 stable
```cpp
2430:
2431:     case SPARM_POSITIVE_ENERGY:
2432:         mpr(T_("You feel less protected from negative energy."));
2433:         break;
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2471:         break;
2472:
2473:     case SPARM_LIGHT:
2474:         invalidate_agrid(true);
2475:         break;
2476:
2477:     default:
2478:         break;
2479:     }
2480: }
```

C-04 stable
```cpp
2434:
2435:     case SPARM_ARCHMAGI:
2436:         mpr(T_("You feel strangely numb."));
2437:         break;
2438:
2439:     case SPARM_SPIRIT_SHIELD:
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2471:         break;
2472:
2473:     case SPARM_LIGHT:
2474:         invalidate_agrid(true);
2475:         break;
2476:
2477:     default:
2478:         break;
2479:     }
2480: }
2481:
2482: static void _remove_amulet_of_faith(item_def &item)
2483: {
2484: #ifndef DEBUG_DIAGNOSTICS
```

C-04 stable
```cpp
2440:         if (!you.spirit_shield())
2441:         {
2442:             mpr(T_("You feel strangely alone."));
2443: #if TAG_MAJOR_VERSION == 34
2444:             if (you.species == SP_DEEP_DWARF)
2445:                 mpr(T_("Your magic begins regenerating once more."));
2446: #endif
2447:         }
2448:         break;
2449:
2450:     case SPARM_HURLING:
2451:         mpr(T_("Your aim is not that steady anymore."));
2452:         break;
2453:
2454:     case SPARM_REPULSION:
2455:         mpr(T_("The haze of the repulsion field disappears."));
2456:         break;
2457:
2458:     case SPARM_SHADOWS:
2459:         mpr(T_("The dungeon's light returns to normal."));
2460:         update_vision_range();
2461:         break;
2462:
2463:     case SPARM_RAMPAGING:
2464:         if (!you.rampaging())
2465:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2466:         break;
2467:
2468:     case SPARM_INFUSION:
2469:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2470:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2471:         break;
2472:
2473:     case SPARM_LIGHT:
2474:         invalidate_agrid(true);
2475:         break;
2476:
2477:     default:
2478:         break;
2479:     }
2480: }
2481:
2482: static void _remove_amulet_of_faith(item_def &item)
2483: {
2484: #ifndef DEBUG_DIAGNOSTICS
2485:     UNUSED(item);
2486: #endif
2487:     if (!faith_has_penalty())
2488:         return;
2489:     if (you_worship(GOD_RU))
2490:     {
```

C-04 trunk
```cpp
2474:
2475:     case SPARM_DEXTERITY:
2476:         notify_stat_change(STAT_DEX, -3, false);
2477:         break;
2478:
2479:     case SPARM_INTELLIGENCE:
2480:         notify_stat_change(STAT_INT, -3, false);
2481:         break;
2482:
2483:     case SPARM_PONDEROUSNESS:
2484:     {
2485:         // XX can the noun here be derived from the species walking verb?
2486:         mpr(you.species == SP_NAGA
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
```

C-04 trunk
```cpp
2478:
2479:     case SPARM_INTELLIGENCE:
2480:         notify_stat_change(STAT_INT, -3, false);
2481:         break;
2482:
2483:     case SPARM_PONDEROUSNESS:
2484:     {
2485:         // XX can the noun here be derived from the species walking verb?
2486:         mpr(you.species == SP_NAGA
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
```

C-04 trunk
```cpp
2483:     case SPARM_PONDEROUSNESS:
2484:     {
2485:         // XX can the noun here be derived from the species walking verb?
2486:         mpr(you.species == SP_NAGA
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
```

C-04 trunk
```cpp
2487:             ? T_("That put a bit of spring back into your slither.")
2488:             : T_("That put a bit of spring back into your step."));
2489:         break;
2490:     }
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
```

C-04 trunk
```cpp
2491:
2492:     case SPARM_FLYING:
2493:         // XXX: Landing must be deferred until after form is actually changed.
2494:         if (!meld)
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
```

C-04 trunk
```cpp
2495:             land_player();
2496:         break;
2497:
2498:     case SPARM_WILLPOWER:
2499:         mpr(T_("You feel less strong-willed."));
2500:         break;
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
```

C-04 trunk
```cpp
2501:
2502:     case SPARM_PROTECTION:
2503:         mpr(T_("You feel less protected."));
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
```

C-04 trunk
```cpp
2504:         break;
2505:
2506:     case SPARM_STEALTH:
2507:         if (!you.get_mutation_level(MUT_NO_STEALTH))
2508:             mpr(T_("You feel less stealthy."));
2509:         break;
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
```

C-04 trunk
```cpp
2510:
2511:     case SPARM_RESISTANCE:
2512:         mpr(T_("You feel hot and cold all over."));
2513:         break;
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2555:         break;
2556:
2557:     default:
2558:         break;
2559:     }
2560: }
```

C-04 trunk
```cpp
2514:
2515:     case SPARM_POSITIVE_ENERGY:
2516:         mpr(T_("You feel less protected from negative energy."));
2517:         break;
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2555:         break;
2556:
2557:     default:
2558:         break;
2559:     }
2560: }
2561:
2562: static void _remove_amulet_of_faith(item_def &item)
2563: {
2564: #ifndef DEBUG_DIAGNOSTICS
```

C-04 trunk
```cpp
2518:
2519:     case SPARM_ARCHMAGI:
2520:         mpr(T_("You feel strangely numb."));
2521:         break;
2522:
2523:     case SPARM_SPIRIT_SHIELD:
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2555:         break;
2556:
2557:     default:
2558:         break;
2559:     }
2560: }
2561:
2562: static void _remove_amulet_of_faith(item_def &item)
2563: {
2564: #ifndef DEBUG_DIAGNOSTICS
2565:     UNUSED(item);
2566: #endif
2567:     if (!faith_has_penalty())
2568:         return;
```

C-04 trunk
```cpp
2524:         if (!you.spirit_shield())
2525:         {
2526:             mpr(T_("You feel strangely alone."));
2527: #if TAG_MAJOR_VERSION == 34
2528:             if (you.species == SP_DEEP_DWARF)
2529:                 mpr(T_("Your magic begins regenerating once more."));
2530: #endif
2531:         }
2532:         break;
2533:
2534:     case SPARM_HURLING:
2535:         mpr(T_("Your aim is not that steady anymore."));
2536:         break;
2537:
2538:     case SPARM_REPULSION:
2539:         mpr(T_("The haze of the repulsion field disappears."));
2540:         break;
2541:
2542:     case SPARM_SHADOWS:
2543:         mpr(T_("The dungeon's light returns to normal."));
2544:         update_vision_range();
2545:         break;
2546:
2547:     case SPARM_RAMPAGING:
2548:         if (!you.rampaging())
2549:             mpr(T_("You no longer feel able to launch a frenzied charge at your enemies."));
2550:         break;
2551:
2552:     case SPARM_INFUSION:
2553:         if (you.max_magic_points || you.has_mutation(MUT_HP_CASTING))
2554:             mprf(T_("You feel magic leave your %s."), you.hand_name(true).c_str());
2555:         break;
2556:
2557:     default:
2558:         break;
2559:     }
2560: }
2561:
2562: static void _remove_amulet_of_faith(item_def &item)
2563: {
2564: #ifndef DEBUG_DIAGNOSTICS
2565:     UNUSED(item);
2566: #endif
2567:     if (!faith_has_penalty())
2568:         return;
2569:     if (you_worship(GOD_RU))
2570:     {
2571:         // next sacrifice is going to be delaaaayed.
2572:         ASSERT(you.raw_piety < piety_breakpoint(5));
2573: #ifdef DEBUG_DIAGNOSTICS
2574:         const int cur_delay = you.props[RU_SACRIFICE_DELAY_KEY].get_int();
```

B-09 stable
```cpp
4659:             break;
4660:
4661:         switch (effects[random2(effects.size())])
4662:         {
4663:             default:
4664:             case ENCH_DAZED:
4665:                 defender->daze(random_range(1, 2));
4666:                 break;
4667:             case ENCH_DRAINED:
4668:                 defender->drain(attacker, false, 2);
4669:                 break;
4670:             case ENCH_CONFUSION:
4671:                 defender->confuse(attacker, 10);
4672:                 break;
4673:         }
4674:
4675:         break;
4676:     }
4677:
4678:     case AF_DOOM:
4679:     {
4680:         const int amount = random_range(5 + attacker->get_hit_dice() / 3,
4681:                                         8 + attacker->get_hit_dice());
4682:         const bool caused_bane = defender->doom(amount);
4683:         if (!caused_bane && defender->is_player())
4684:             mpr(T_("Your doom draws closer."));
4685:         break;
4686:     }
4687:
4688:     }
4689:
4690:     if (needs_message && !special_damage_message.empty())
4691:         mpr(special_damage_message);
4692:
4693:     if (special_damage > 0 && defender->alive())
4694:     {
4695:         inflict_damage(special_damage, special_damage_flavour);
4696:         special_damage = 0;
4697:         special_damage_message.clear();
4698:         special_damage_flavour = BEAM_NONE;
4699:     }
4700: }
4701:
4702: void melee_attack::do_fiery_armour_burn()
4703: {
4704:     if (!you.duration[DUR_FIERY_ARMOUR]
4705:         || !attacker->alive()
4706:         || !adjacent(you.pos(), attacker->pos()))
4707:     {
4708:         return;
4709:     }
```

B-09 trunk
```cpp
4853:             break;
4854:
4855:         switch (effects[random2(effects.size())])
4856:         {
4857:             default:
4858:             case ENCH_DAZED:
4859:                 defender->daze(random_range(1, 2));
4860:                 break;
4861:             case ENCH_DRAINED:
4862:                 defender->drain(attacker, false, 2);
4863:                 break;
4864:             case ENCH_CONFUSION:
4865:                 defender->confuse(attacker, 10);
4866:                 break;
4867:         }
4868:
4869:         break;
4870:     }
4871:
4872:     case AF_DOOM:
4873:     {
4874:         const int amount = random_range(5 + attacker->get_hit_dice() / 3,
4875:                                         8 + attacker->get_hit_dice());
4876:         const bool caused_bane = defender->doom(amount);
4877:         if (!caused_bane && defender->is_player())
4878:             mpr(T_("Your doom draws closer."));
4879:         break;
4880:     }
4881:
4882:     case AF_BURSTSHROOM:
4883:         grow_burstshrooms(attacker->get_hit_dice() * 2 / 3);
4884:         break;
4885:
4886:     }
4887:
4888:     if (needs_message && !special_damage_message.empty())
4889:         mpr(special_damage_message);
4890:
4891:     if (special_damage > 0 && defender->alive())
4892:     {
4893:         inflict_damage(special_damage, special_damage_flavour);
4894:         special_damage = 0;
4895:         special_damage_message.clear();
4896:         special_damage_flavour = BEAM_NONE;
4897:     }
4898: }
4899:
4900: void melee_attack::do_fiery_armour_burn()
4901: {
4902:     if (!you.duration[DUR_FIERY_ARMOUR]
4903:         || !attacker->alive()
```

C-09 stable
```cpp
1422:     if (!place.empty())
1423:     {
1424:         if (Options.language == lang_t::ZH)
1425:             desc = make_stringf(T_("%s%s"), place.c_str(), desc.c_str());
1426:         else
1427:             desc += place;
1428:     }
1429:     return desc;
1430: }
1431:
1432: /**
1433:  * Pickup a single item stack at the given location link
1434:  *
1435:  * @param link The location link
1436:  * @param qty If 0, prompt for quantity of that item to pick up, if < 0,
1437:  *            pick up the entire stack, otherwise pick up qty of the item.
1438:  * @return  True if any item was picked up, false otherwise.
1439: */
1440: bool pickup_single_item(int link, int qty)
1441: {
1442:     ASSERT(link != NON_ITEM);
1443:
1444:     item_def* item = &env.item[link];
1445:     if (item_is_stationary(env.item[link]))
1446:     {
1447:         mpr(T_("You can't pick that up."));
1448:         return false;
1449:     }
1450:     if (item->base_type == OBJ_GOLD && !qty && !i_feel_safe()
1451:         && !yesno(T_("Are you sure you want to pick up this pile of gold now?"),
1452:                   true, 'n'))
1453:     {
1454:         canned_msg(MSG_OK);
1455:         return false;
1456:     }
1457:     if (qty == 0 && item->quantity > 1 && item->base_type != OBJ_GOLD)
1458:     {
1459:         const string prompt
1460:                 = make_stringf(T_("Pick up how many of %s (; or enter for all)? "),
1461:                                item->name(DESC_THE, false,
1462:                                           false, false).c_str());
1463:
1464:         qty = prompt_for_quantity(prompt.c_str());
1465:         if (qty == -1)
1466:             qty = item->quantity;
1467:         else if (qty == 0)
1468:         {
1469:             canned_msg(MSG_OK);
1470:             return false;
1471:         }
1472:         else if (qty < item->quantity)
```

C-09 stable
```cpp
1426:         else
1427:             desc += place;
1428:     }
1429:     return desc;
1430: }
1431:
1432: /**
1433:  * Pickup a single item stack at the given location link
1434:  *
1435:  * @param link The location link
1436:  * @param qty If 0, prompt for quantity of that item to pick up, if < 0,
1437:  *            pick up the entire stack, otherwise pick up qty of the item.
1438:  * @return  True if any item was picked up, false otherwise.
1439: */
1440: bool pickup_single_item(int link, int qty)
1441: {
1442:     ASSERT(link != NON_ITEM);
1443:
1444:     item_def* item = &env.item[link];
1445:     if (item_is_stationary(env.item[link]))
1446:     {
1447:         mpr(T_("You can't pick that up."));
1448:         return false;
1449:     }
1450:     if (item->base_type == OBJ_GOLD && !qty && !i_feel_safe()
1451:         && !yesno(T_("Are you sure you want to pick up this pile of gold now?"),
1452:                   true, 'n'))
1453:     {
1454:         canned_msg(MSG_OK);
1455:         return false;
1456:     }
1457:     if (qty == 0 && item->quantity > 1 && item->base_type != OBJ_GOLD)
1458:     {
1459:         const string prompt
1460:                 = make_stringf(T_("Pick up how many of %s (; or enter for all)? "),
1461:                                item->name(DESC_THE, false,
1462:                                           false, false).c_str());
1463:
1464:         qty = prompt_for_quantity(prompt.c_str());
1465:         if (qty == -1)
1466:             qty = item->quantity;
1467:         else if (qty == 0)
1468:         {
1469:             canned_msg(MSG_OK);
1470:             return false;
1471:         }
1472:         else if (qty < item->quantity)
1473:         {
1474:             // Mark rest item as not eligible for autopickup.
1475:             item->flags |= ISFLAG_DROPPED;
1476:             item->flags &= ~ISFLAG_THROWN;
1477:         }
```

C-09 trunk
```cpp
1388:     if (!place.empty())
1389:     {
1390:         if (Options.language == lang_t::ZH)
1391:             desc = make_stringf(T_("%s%s"), place.c_str(), desc.c_str());
1392:         else
1393:             desc += place;
1394:     }
1395:     return desc;
1396: }
1397:
1398: /**
1399:  * Pickup a single item stack at the given location link
1400:  *
1401:  * @param link The location link
1402:  * @param qty If 0, prompt for quantity of that item to pick up, if < 0,
1403:  *            pick up the entire stack, otherwise pick up qty of the item.
1404:  * @return  True if any item was picked up, false otherwise.
1405: */
1406: bool pickup_single_item(int link, int qty)
1407: {
1408:     ASSERT(link != NON_ITEM);
1409:
1410:     item_def* item = &env.item[link];
1411:     if (item_is_stationary(env.item[link]))
1412:     {
1413:         mpr(T_("You can't pick that up."));
1414:         return false;
1415:     }
1416:     if (item->base_type == OBJ_GOLD && !qty && !i_feel_safe()
1417:         && !yesno(T_("Are you sure you want to pick up this pile of gold now?"),
1418:                   true, 'n'))
1419:     {
1420:         canned_msg(MSG_OK);
1421:         return false;
1422:     }
1423:     if (qty == 0 && item->quantity > 1 && item->base_type != OBJ_GOLD)
1424:     {
1425:         const string prompt
1426:                 = make_stringf(T_("Pick up how many of %s (; or enter for all)? "),
1427:                                item->name(DESC_THE, false,
1428:                                           false, false).c_str());
1429:
1430:         qty = prompt_for_quantity(prompt.c_str());
1431:         if (qty == -1)
1432:             qty = item->quantity;
1433:         else if (qty == 0)
1434:         {
1435:             canned_msg(MSG_OK);
1436:             return false;
1437:         }
1438:         else if (qty < item->quantity)
```

C-09 trunk
```cpp
1392:         else
1393:             desc += place;
1394:     }
1395:     return desc;
1396: }
1397:
1398: /**
1399:  * Pickup a single item stack at the given location link
1400:  *
1401:  * @param link The location link
1402:  * @param qty If 0, prompt for quantity of that item to pick up, if < 0,
1403:  *            pick up the entire stack, otherwise pick up qty of the item.
1404:  * @return  True if any item was picked up, false otherwise.
1405: */
1406: bool pickup_single_item(int link, int qty)
1407: {
1408:     ASSERT(link != NON_ITEM);
1409:
1410:     item_def* item = &env.item[link];
1411:     if (item_is_stationary(env.item[link]))
1412:     {
1413:         mpr(T_("You can't pick that up."));
1414:         return false;
1415:     }
1416:     if (item->base_type == OBJ_GOLD && !qty && !i_feel_safe()
1417:         && !yesno(T_("Are you sure you want to pick up this pile of gold now?"),
1418:                   true, 'n'))
1419:     {
1420:         canned_msg(MSG_OK);
1421:         return false;
1422:     }
1423:     if (qty == 0 && item->quantity > 1 && item->base_type != OBJ_GOLD)
1424:     {
1425:         const string prompt
1426:                 = make_stringf(T_("Pick up how many of %s (; or enter for all)? "),
1427:                                item->name(DESC_THE, false,
1428:                                           false, false).c_str());
1429:
1430:         qty = prompt_for_quantity(prompt.c_str());
1431:         if (qty == -1)
1432:             qty = item->quantity;
1433:         else if (qty == 0)
1434:         {
1435:             canned_msg(MSG_OK);
1436:             return false;
1437:         }
1438:         else if (qty < item->quantity)
1439:         {
1440:             // Mark rest item as not eligible for autopickup.
1441:             item->flags |= ISFLAG_DROPPED;
1442:             item->flags &= ~ISFLAG_THROWN;
1443:         }
```

B-12 stable
```cpp
723:         simple_monster_message(m, msg.c_str());
724:         if (dam)
725:         {
726:             m.hurt(&you, dam, BEAM_MMISSILE, KILLED_BY_BEAM /*eh*/);
727:             if (!m.alive())
728:                 return;
729:         }
730:         m.malmutate(&you);
731:         m.del_ench(ENCH_CONTAM, true);
732:         return;
733:     }
734:
735:     m.add_ench(mon_enchant(ENCH_CONTAM, &you, 0, 1));
736:     if (!old_glow.degree)
737:         simple_monster_message(m, T_(" begins to glow."));
738:     else
739:         simple_monster_message(m, T_(" glows dangerously bright."));
740:
741:     // Deduct player energy for the attack and maybe untransform.
742:     int& energy = you.props[FLUX_ENERGY_KEY].get_int();
743:     const bool above_warning = energy > FLUX_ENERGY_WARNING;
744:     energy -= random_range(1, 2);
745:
746:     if (energy <= 0)
747:     {
748:         mprf(MSGCH_DURATION, T_("The last of your unstable energy dissipates and you return to your previous form."));
749:         return_to_default_form();
750:     }
751:     else if (above_warning && energy < FLUX_ENERGY_WARNING)
752:         mprf(MSGCH_DURATION, T_("You feel the transmutational energy in your body is nearly expended."));
753: }
754:
755: void melee_attack::maybe_do_mesmerism()
756: {
757:     // Check if the effect is valid.
758:     if (!defender->wearing_ego(OBJ_ARMOUR, SPARM_MESMERISM))
759:         return;
760:
761:     if (defender->is_player() && you.duration[DUR_MESMERISM_COOLDOWN])
762:         return;
763:     else if (defender->is_monster() && defender->as_monster()->has_ench(ENCH_ORB_COOLDOWN))
764:         return;
765:
766:     const int radius = defender->is_player() ? mesmerism_orb_radius() : 3;
767:     const int max_dur = defender->is_player() ? 5 + you.skill_rdiv(SK_EVOCATIONS, 1, 5)
768:                                               : 3 + defender->get_hit_dice() / 4;
769:
770:     mprf(T_("%s orb emits a pulse of dizzying energy."), defender->name(DESC_ITS).c_str());
771:     draw_ring_animation(defender->pos(), radius, LIGHTMAGENTA, MAGENTA, true, 30);
772:
773:     for (radius_iterator ri(defender->pos(), radius, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
```

B-12 stable
```cpp
727:             if (!m.alive())
728:                 return;
729:         }
730:         m.malmutate(&you);
731:         m.del_ench(ENCH_CONTAM, true);
732:         return;
733:     }
734:
735:     m.add_ench(mon_enchant(ENCH_CONTAM, &you, 0, 1));
736:     if (!old_glow.degree)
737:         simple_monster_message(m, T_(" begins to glow."));
738:     else
739:         simple_monster_message(m, T_(" glows dangerously bright."));
740:
741:     // Deduct player energy for the attack and maybe untransform.
742:     int& energy = you.props[FLUX_ENERGY_KEY].get_int();
743:     const bool above_warning = energy > FLUX_ENERGY_WARNING;
744:     energy -= random_range(1, 2);
745:
746:     if (energy <= 0)
747:     {
748:         mprf(MSGCH_DURATION, T_("The last of your unstable energy dissipates and you return to your previous form."));
749:         return_to_default_form();
750:     }
751:     else if (above_warning && energy < FLUX_ENERGY_WARNING)
752:         mprf(MSGCH_DURATION, T_("You feel the transmutational energy in your body is nearly expended."));
753: }
754:
755: void melee_attack::maybe_do_mesmerism()
756: {
757:     // Check if the effect is valid.
758:     if (!defender->wearing_ego(OBJ_ARMOUR, SPARM_MESMERISM))
759:         return;
760:
761:     if (defender->is_player() && you.duration[DUR_MESMERISM_COOLDOWN])
762:         return;
763:     else if (defender->is_monster() && defender->as_monster()->has_ench(ENCH_ORB_COOLDOWN))
764:         return;
765:
766:     const int radius = defender->is_player() ? mesmerism_orb_radius() : 3;
767:     const int max_dur = defender->is_player() ? 5 + you.skill_rdiv(SK_EVOCATIONS, 1, 5)
768:                                               : 3 + defender->get_hit_dice() / 4;
769:
770:     mprf(T_("%s orb emits a pulse of dizzying energy."), defender->name(DESC_ITS).c_str());
771:     draw_ring_animation(defender->pos(), radius, LIGHTMAGENTA, MAGENTA, true, 30);
772:
773:     for (radius_iterator ri(defender->pos(), radius, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
774:     {
775:         if (actor* act = actor_at(*ri))
776:         {
777:             if (!act->is_firewood() && !act->clarity()
```

B-12 trunk
```cpp
724:         simple_monster_message(m, msg.c_str());
725:         if (dam)
726:         {
727:             m.hurt(&you, dam, BEAM_MMISSILE, KILLED_BY_BEAM /*eh*/);
728:             if (!m.alive())
729:                 return;
730:         }
731:         m.malmutate(&you);
732:         m.del_ench(ENCH_CONTAM, true);
733:         return;
734:     }
735:
736:     m.add_ench(mon_enchant(ENCH_CONTAM, &you, 0, 1));
737:     if (!old_glow.degree)
738:         simple_monster_message(m, T_(" begins to glow."));
739:     else
740:         simple_monster_message(m, T_(" glows dangerously bright."));
741:
742:     // Deduct player energy for the attack and maybe untransform.
743:     int& energy = you.props[FLUX_ENERGY_KEY].get_int();
744:     const bool above_warning = energy > FLUX_ENERGY_WARNING;
745:     energy -= random_range(1, 2);
746:
747:     if (energy <= 0)
748:     {
749:         mprf(MSGCH_DURATION, T_("The last of your unstable energy dissipates and you return to your previous form."));
750:         return_to_default_form();
751:     }
752:     else if (above_warning && energy < FLUX_ENERGY_WARNING)
753:         mprf(MSGCH_DURATION, T_("You feel the transmutational energy in your body is nearly expended."));
754: }
755:
756: void melee_attack::maybe_do_mesmerism()
757: {
758:     // Check if the effect is valid.
759:     if (!defender->wearing_ego(OBJ_ARMOUR, SPARM_MESMERISM))
760:         return;
761:
762:     if (defender->is_player() && you.duration[DUR_MESMERISM_COOLDOWN])
763:         return;
764:     else if (defender->is_monster() && defender->as_monster()->has_ench(ENCH_ORB_COOLDOWN))
765:         return;
766:
767:     const int radius = defender->is_player() ? mesmerism_orb_radius() : 3;
768:     const int max_dur = defender->is_player() ? 5 + you.skill_rdiv(SK_EVOCATIONS, 1, 5)
769:                                               : 3 + defender->get_hit_dice() / 4;
770:
771:     mprf(T_("%s orb emits a pulse of dizzying energy."), defender->name(DESC_ITS).c_str());
772:     draw_ring_animation(defender->pos(), radius, LIGHTMAGENTA, MAGENTA, true, 30);
773:
774:     for (radius_iterator ri(defender->pos(), radius, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
```

B-12 trunk
```cpp
728:             if (!m.alive())
729:                 return;
730:         }
731:         m.malmutate(&you);
732:         m.del_ench(ENCH_CONTAM, true);
733:         return;
734:     }
735:
736:     m.add_ench(mon_enchant(ENCH_CONTAM, &you, 0, 1));
737:     if (!old_glow.degree)
738:         simple_monster_message(m, T_(" begins to glow."));
739:     else
740:         simple_monster_message(m, T_(" glows dangerously bright."));
741:
742:     // Deduct player energy for the attack and maybe untransform.
743:     int& energy = you.props[FLUX_ENERGY_KEY].get_int();
744:     const bool above_warning = energy > FLUX_ENERGY_WARNING;
745:     energy -= random_range(1, 2);
746:
747:     if (energy <= 0)
748:     {
749:         mprf(MSGCH_DURATION, T_("The last of your unstable energy dissipates and you return to your previous form."));
750:         return_to_default_form();
751:     }
752:     else if (above_warning && energy < FLUX_ENERGY_WARNING)
753:         mprf(MSGCH_DURATION, T_("You feel the transmutational energy in your body is nearly expended."));
754: }
755:
756: void melee_attack::maybe_do_mesmerism()
757: {
758:     // Check if the effect is valid.
759:     if (!defender->wearing_ego(OBJ_ARMOUR, SPARM_MESMERISM))
760:         return;
761:
762:     if (defender->is_player() && you.duration[DUR_MESMERISM_COOLDOWN])
763:         return;
764:     else if (defender->is_monster() && defender->as_monster()->has_ench(ENCH_ORB_COOLDOWN))
765:         return;
766:
767:     const int radius = defender->is_player() ? mesmerism_orb_radius() : 3;
768:     const int max_dur = defender->is_player() ? 5 + you.skill_rdiv(SK_EVOCATIONS, 1, 5)
769:                                               : 3 + defender->get_hit_dice() / 4;
770:
771:     mprf(T_("%s orb emits a pulse of dizzying energy."), defender->name(DESC_ITS).c_str());
772:     draw_ring_animation(defender->pos(), radius, LIGHTMAGENTA, MAGENTA, true, 30);
773:
774:     for (radius_iterator ri(defender->pos(), radius, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
775:     {
776:         if (actor* act = actor_at(*ri))
777:         {
778:             if (!act->is_firewood() && !act->clarity()
```

D-12 stable
```cpp
3142:
3143:         if (had_effect)
3144:             mpr(T_("The creatures around you are filled with an inner flame!"));
3145:         else
3146:             mpr(T_("The air around you briefly surges with heat, but it quickly dissipates."));
3147:
3148:         bad_effect = true;
3149:         break;
3150:     }
3151:
3152:     case SCR_POISON:
3153:     {
3154:         const spret result = scroll_of_poison(!alreadyknown);
3155:         cancel_scroll = result == spret::abort;
3156:         if (!cancel_scroll)
3157:             mpr(pre_succ_msg);
3158:         // amusing to Xom, at least
3159:         bad_effect = result == spret::success && !player_res_poison();
3160:         break;
3161:     }
3162:
3163:     case SCR_ENCHANT_WEAPON:
3164:         if (!alreadyknown)
3165:         {
3166:             mpr(pre_succ_msg);
3167:             mpr(T_("It is a scroll of enchant weapon."));
3168:             // included in default force_more_message (to show it before menu)
3169:
3170:             run_uncancel(UNC_ENCHANT_WEAPON);
3171:         }
3172:         else
3173:             cancel_scroll = !_handle_enchant_weapon(alreadyknown, pre_succ_msg);
3174:
3175:         break;
3176:
3177:     case SCR_BRAND_WEAPON:
3178:         if (!alreadyknown)
3179:         {
3180:             mpr(pre_succ_msg);
3181:             mpr(T_("It is a scroll of brand weapon."));
3182:             // included in default force_more_message (to show it before menu)
3183:
3184:             run_uncancel(UNC_BRAND_WEAPON);
3185:         }
3186:         else
3187:             cancel_scroll = !_handle_brand_weapon(alreadyknown, pre_succ_msg);
3188:
3189:         break;
3190:
3191:     case SCR_IDENTIFY:
3192:         if (!alreadyknown)
```

D-12 trunk
```cpp
3276:         }
3277:
3278:         if (had_effect)
3279:             mpr(T_("The creatures around you are filled with an inner flame!"));
3280:         else
3281:             mpr(T_("The air around you briefly surges with heat, but it quickly dissipates."));
3282:
3283:         bad_effect = true;
3284:         break;
3285:     }
3286:
3287:     case SCR_POISON:
3288:     {
3289:         result = scroll_of_poison(!alreadyknown);
3290:         if (result != spret::abort)
3291:             mpr(pre_succ_msg);
3292:         // amusing to Xom, at least
3293:         bad_effect = result == spret::success && !player_res_poison();
3294:         break;
3295:     }
3296:
3297:     case SCR_ENCHANT_WEAPON:
3298:         if (!alreadyknown)
3299:         {
3300:             mpr(pre_succ_msg);
3301:             mpr(T_("It is a scroll of enchant weapon."));
3302:             // included in default force_more_message (to show it before menu)
3303:
3304:             result = _run_read_scroll_uncancel(UNC_ENCHANT_WEAPON, *scroll);
3305:         }
3306:         else
3307:             result = _handle_enchant_weapon(alreadyknown, pre_succ_msg);
3308:
3309:         break;
3310:
3311:     case SCR_BRAND_WEAPON:
3312:         if (!alreadyknown)
3313:         {
3314:             mpr(pre_succ_msg);
3315:             mpr(T_("It is a scroll of brand weapon."));
3316:             // included in default force_more_message (to show it before menu)
3317:
3318:             result = _run_read_scroll_uncancel(UNC_BRAND_WEAPON, *scroll);
3319:         }
3320:         else
3321:             result = _handle_brand_weapon(alreadyknown, pre_succ_msg);
3322:
3323:         break;
3324:
3325:     case SCR_IDENTIFY:
3326:         if (!alreadyknown)
```

C-02 stable
```cpp
1175:                     entry.melded = true;
1176:                     if (entry.is_overflow)
1177:                     {
1178:                         for (player_equip_entry& overflow : items)
1179:                         {
1180:                             if (overflow.item == entry.item)
1181:                                 overflow.melded = true;
1182:                         }
1183:                     }
1184:                 }
1185:             }
1186:         }
1187:     }
1188:
1189:     if (to_meld.empty())
1190:         return;
1191:
1192:     if (skip_effects)
1193:         return;
1194:
1195:     // Print a message.
1196:     vector<string> meld_msg;
1197:     for (item_def* meld_item : to_meld)
1198:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1199:
1200:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1201:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1202:                 T_(" and "), T_(", ")).c_str(),
1203:             meld_msg.size() > 1 ? "" : "s");
1204:
1205:     update();
1206:
1207:     // Now, simultaneously do unequip effects for all melded items.
1208:     for (item_def* meld_item : to_meld)
1209:         unequip_effect(meld_item->link, true, true);
1210: }
1211:
1212: /**
1213:  * Unmelds equipment in a single slot and does associated bookeeping.
1214:  *
1215:  * @param slot           The slot type to unmeld.
1216:  * @param skip_effects   If true, no message will be printed about doing any of
1217:  *                       this, and no equip effects will be processed.
1218:  */
1219: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1220: {
1221:     vector<item_def*> was_unmelded;
1222:     for (player_equip_entry& entry : items)
1223:     {
1224:         if (entry.slot == slot)
1225:         {
1226:             if (entry.melded)
1227:             {
1228:                 if (entry.is_overflow)
```

C-02 stable
```cpp
1175:                     entry.melded = true;
1176:                     if (entry.is_overflow)
1177:                     {
1178:                         for (player_equip_entry& overflow : items)
1179:                         {
1180:                             if (overflow.item == entry.item)
1181:                                 overflow.melded = true;
1182:                         }
1183:                     }
1184:                 }
1185:             }
1186:         }
1187:     }
1188:
1189:     if (to_meld.empty())
1190:         return;
1191:
1192:     if (skip_effects)
1193:         return;
1194:
1195:     // Print a message.
1196:     vector<string> meld_msg;
1197:     for (item_def* meld_item : to_meld)
1198:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1199:
1200:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1201:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1202:                 T_(" and "), T_(", ")).c_str(),
1203:             meld_msg.size() > 1 ? "" : "s");
1204:
1205:     update();
1206:
1207:     // Now, simultaneously do unequip effects for all melded items.
1208:     for (item_def* meld_item : to_meld)
1209:         unequip_effect(meld_item->link, true, true);
1210: }
1211:
1212: /**
1213:  * Unmelds equipment in a single slot and does associated bookeeping.
1214:  *
1215:  * @param slot           The slot type to unmeld.
1216:  * @param skip_effects   If true, no message will be printed about doing any of
1217:  *                       this, and no equip effects will be processed.
1218:  */
1219: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1220: {
1221:     vector<item_def*> was_unmelded;
1222:     for (player_equip_entry& entry : items)
1223:     {
1224:         if (entry.slot == slot)
1225:         {
1226:             if (entry.melded)
1227:             {
1228:                 if (entry.is_overflow)
```

C-02 stable
```cpp
1175:                     entry.melded = true;
1176:                     if (entry.is_overflow)
1177:                     {
1178:                         for (player_equip_entry& overflow : items)
1179:                         {
1180:                             if (overflow.item == entry.item)
1181:                                 overflow.melded = true;
1182:                         }
1183:                     }
1184:                 }
1185:             }
1186:         }
1187:     }
1188:
1189:     if (to_meld.empty())
1190:         return;
1191:
1192:     if (skip_effects)
1193:         return;
1194:
1195:     // Print a message.
1196:     vector<string> meld_msg;
1197:     for (item_def* meld_item : to_meld)
1198:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1199:
1200:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1201:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1202:                 T_(" and "), T_(", ")).c_str(),
1203:             meld_msg.size() > 1 ? "" : "s");
1204:
1205:     update();
1206:
1207:     // Now, simultaneously do unequip effects for all melded items.
1208:     for (item_def* meld_item : to_meld)
1209:         unequip_effect(meld_item->link, true, true);
1210: }
1211:
1212: /**
1213:  * Unmelds equipment in a single slot and does associated bookeeping.
1214:  *
1215:  * @param slot           The slot type to unmeld.
1216:  * @param skip_effects   If true, no message will be printed about doing any of
1217:  *                       this, and no equip effects will be processed.
1218:  */
1219: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1220: {
1221:     vector<item_def*> was_unmelded;
1222:     for (player_equip_entry& entry : items)
1223:     {
1224:         if (entry.slot == slot)
1225:         {
1226:             if (entry.melded)
1227:             {
1228:                 if (entry.is_overflow)
```

C-02 trunk
```cpp
1191:                     entry.melded = true;
1192:                     if (entry.is_overflow)
1193:                     {
1194:                         for (player_equip_entry& overflow : items)
1195:                         {
1196:                             if (overflow.item == entry.item)
1197:                                 overflow.melded = true;
1198:                         }
1199:                     }
1200:                 }
1201:             }
1202:         }
1203:     }
1204:
1205:     if (to_meld.empty())
1206:         return;
1207:
1208:     if (skip_effects)
1209:         return;
1210:
1211:     // Print a message.
1212:     vector<string> meld_msg;
1213:     for (item_def* meld_item : to_meld)
1214:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1215:
1216:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1217:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1218:                 T_(" and "), T_(", ")).c_str(),
1219:             meld_msg.size() > 1 ? "" : "s");
1220:
1221:     update();
1222:
1223:     // Now, simultaneously do unequip effects for all melded items.
1224:     for (item_def* meld_item : to_meld)
1225:         unequip_effect(meld_item->link, true, true, false, true);
1226: }
1227:
1228: /**
1229:  * Unmelds equipment in a single slot and does associated bookeeping.
1230:  *
1231:  * @param slot           The slot type to unmeld.
1232:  * @param skip_effects   If true, no message will be printed about doing any of
1233:  *                       this, and no equip effects will be processed.
1234:  */
1235: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1236: {
1237:     vector<item_def*> was_unmelded;
1238:     for (player_equip_entry& entry : items)
1239:     {
1240:         if (entry.slot == slot)
1241:         {
1242:             if (entry.melded)
1243:             {
1244:                 if (entry.is_overflow)
```

C-02 trunk
```cpp
1191:                     entry.melded = true;
1192:                     if (entry.is_overflow)
1193:                     {
1194:                         for (player_equip_entry& overflow : items)
1195:                         {
1196:                             if (overflow.item == entry.item)
1197:                                 overflow.melded = true;
1198:                         }
1199:                     }
1200:                 }
1201:             }
1202:         }
1203:     }
1204:
1205:     if (to_meld.empty())
1206:         return;
1207:
1208:     if (skip_effects)
1209:         return;
1210:
1211:     // Print a message.
1212:     vector<string> meld_msg;
1213:     for (item_def* meld_item : to_meld)
1214:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1215:
1216:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1217:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1218:                 T_(" and "), T_(", ")).c_str(),
1219:             meld_msg.size() > 1 ? "" : "s");
1220:
1221:     update();
1222:
1223:     // Now, simultaneously do unequip effects for all melded items.
1224:     for (item_def* meld_item : to_meld)
1225:         unequip_effect(meld_item->link, true, true, false, true);
1226: }
1227:
1228: /**
1229:  * Unmelds equipment in a single slot and does associated bookeeping.
1230:  *
1231:  * @param slot           The slot type to unmeld.
1232:  * @param skip_effects   If true, no message will be printed about doing any of
1233:  *                       this, and no equip effects will be processed.
1234:  */
1235: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1236: {
1237:     vector<item_def*> was_unmelded;
1238:     for (player_equip_entry& entry : items)
1239:     {
1240:         if (entry.slot == slot)
1241:         {
1242:             if (entry.melded)
1243:             {
1244:                 if (entry.is_overflow)
```

C-02 trunk
```cpp
1191:                     entry.melded = true;
1192:                     if (entry.is_overflow)
1193:                     {
1194:                         for (player_equip_entry& overflow : items)
1195:                         {
1196:                             if (overflow.item == entry.item)
1197:                                 overflow.melded = true;
1198:                         }
1199:                     }
1200:                 }
1201:             }
1202:         }
1203:     }
1204:
1205:     if (to_meld.empty())
1206:         return;
1207:
1208:     if (skip_effects)
1209:         return;
1210:
1211:     // Print a message.
1212:     vector<string> meld_msg;
1213:     for (item_def* meld_item : to_meld)
1214:         meld_msg.emplace_back(meld_item->name(DESC_PLAIN));
1215:
1216:     mprf_p(T_("Your %1$s meld%2$s into your body."),
1217:             comma_separated_line(meld_msg.begin(), meld_msg.end(),
1218:                 T_(" and "), T_(", ")).c_str(),
1219:             meld_msg.size() > 1 ? "" : "s");
1220:
1221:     update();
1222:
1223:     // Now, simultaneously do unequip effects for all melded items.
1224:     for (item_def* meld_item : to_meld)
1225:         unequip_effect(meld_item->link, true, true, false, true);
1226: }
1227:
1228: /**
1229:  * Unmelds equipment in a single slot and does associated bookeeping.
1230:  *
1231:  * @param slot           The slot type to unmeld.
1232:  * @param skip_effects   If true, no message will be printed about doing any of
1233:  *                       this, and no equip effects will be processed.
1234:  */
1235: void player_equip_set::unmeld_slot(equipment_slot slot, bool skip_effects)
1236: {
1237:     vector<item_def*> was_unmelded;
1238:     for (player_equip_entry& entry : items)
1239:     {
1240:         if (entry.slot == slot)
1241:         {
1242:             if (entry.melded)
1243:             {
1244:                 if (entry.is_overflow)
```

D-11 stable
```cpp
3221:     case SCR_CURSE_WEAPON:
3222:     case SCR_CURSE_ARMOUR:
3223:     case SCR_CURSE_JEWELLERY:
3224:     case SCR_RECHARGING:
3225:     case SCR_RANDOM_USELESSNESS:
3226:     case SCR_HOLY_WORD:
3227:     {
3228:         mpr(T_("This item has been removed, sorry!"));
3229:         cancel_scroll = true;
3230:         break;
3231:     }
3232: #endif
3233:
3234:     case SCR_SILENCE:
3235:         cast_silence(30);
3236:         break;
3237:
3238:     case SCR_VULNERABILITY:
3239:         _vulnerability_scroll();
3240:         break;
3241:
3242:     case SCR_AMNESIA:
3243:         if (!alreadyknown)
3244:         {
3245:             mpr(pre_succ_msg);
3246:             mpr(T_("It is a scroll of amnesia."));
3247:             // included in default force_more_message (to show it before menu)
3248:         }
3249:         if (you.spell_no == 0 || you.has_mutation(MUT_INNATE_CASTER))
3250:         {
3251:             mpr(T_("You feel briefly forgetful."));
3252:             break;
3253:         }
3254:
3255:         if (!alreadyknown)
3256:             run_uncancel(UNC_AMNESIA);
3257:         else
3258:             cancel_scroll = !_handle_amnesia(alreadyknown);
3259:
3260:         break;
3261:
3262:     default:
3263:         mpr(T_("Read a buggy scroll, please report this."));
3264:         break;
3265:     }
3266:
3267:     if (cancel_scroll)
3268:         you.turn_is_over = false;
3269:
3270:     identify_item(*scroll);
3271:
```

D-11 stable
```cpp
3226:     case SCR_HOLY_WORD:
3227:     {
3228:         mpr(T_("This item has been removed, sorry!"));
3229:         cancel_scroll = true;
3230:         break;
3231:     }
3232: #endif
3233:
3234:     case SCR_SILENCE:
3235:         cast_silence(30);
3236:         break;
3237:
3238:     case SCR_VULNERABILITY:
3239:         _vulnerability_scroll();
3240:         break;
3241:
3242:     case SCR_AMNESIA:
3243:         if (!alreadyknown)
3244:         {
3245:             mpr(pre_succ_msg);
3246:             mpr(T_("It is a scroll of amnesia."));
3247:             // included in default force_more_message (to show it before menu)
3248:         }
3249:         if (you.spell_no == 0 || you.has_mutation(MUT_INNATE_CASTER))
3250:         {
3251:             mpr(T_("You feel briefly forgetful."));
3252:             break;
3253:         }
3254:
3255:         if (!alreadyknown)
3256:             run_uncancel(UNC_AMNESIA);
3257:         else
3258:             cancel_scroll = !_handle_amnesia(alreadyknown);
3259:
3260:         break;
3261:
3262:     default:
3263:         mpr(T_("Read a buggy scroll, please report this."));
3264:         break;
3265:     }
3266:
3267:     if (cancel_scroll)
3268:         you.turn_is_over = false;
3269:
3270:     identify_item(*scroll);
3271:
3272:     string scroll_name = scroll->name(DESC_QUALNAME);
3273:
3274:     if (!cancel_scroll)
3275:     {
3276:         if (in_inventory(*scroll))
```

D-11 trunk
```cpp
3355:     case SCR_CURSE_WEAPON:
3356:     case SCR_CURSE_ARMOUR:
3357:     case SCR_CURSE_JEWELLERY:
3358:     case SCR_RECHARGING:
3359:     case SCR_RANDOM_USELESSNESS:
3360:     case SCR_HOLY_WORD:
3361:     {
3362:         mpr(T_("This item has been removed, sorry!"));
3363:         result = spret::abort;
3364:         break;
3365:     }
3366: #endif
3367:
3368:     case SCR_SILENCE:
3369:         cast_silence(30);
3370:         break;
3371:
3372:     case SCR_VULNERABILITY:
3373:         _vulnerability_scroll();
3374:         break;
3375:
3376:     case SCR_AMNESIA:
3377:         if (!alreadyknown)
3378:         {
3379:             mpr(pre_succ_msg);
3380:             mpr(T_("It is a scroll of amnesia."));
3381:             // included in default force_more_message (to show it before menu)
3382:         }
3383:         if (you.spell_no == 0 || you.has_mutation(MUT_INNATE_CASTER))
3384:         {
3385:             mpr(T_("You feel briefly forgetful."));
3386:             break;
3387:         }
3388:
3389:         if (!alreadyknown)
3390:             result = _run_read_scroll_uncancel(UNC_AMNESIA, *scroll);
3391:         else
3392:             result = _handle_amnesia(alreadyknown);
3393:
3394:         break;
3395:
3396:     case SCR_PLINKING:
3397:         _plinking_scroll();
3398:         break;
3399:
3400:     default:
3401:         mpr(T_("Read a buggy scroll, please report this."));
3402:         break;
3403:     }
3404:
3405:     if (alreadyknown && result == spret::seen_hups)
```

D-11 trunk
```cpp
3360:     case SCR_HOLY_WORD:
3361:     {
3362:         mpr(T_("This item has been removed, sorry!"));
3363:         result = spret::abort;
3364:         break;
3365:     }
3366: #endif
3367:
3368:     case SCR_SILENCE:
3369:         cast_silence(30);
3370:         break;
3371:
3372:     case SCR_VULNERABILITY:
3373:         _vulnerability_scroll();
3374:         break;
3375:
3376:     case SCR_AMNESIA:
3377:         if (!alreadyknown)
3378:         {
3379:             mpr(pre_succ_msg);
3380:             mpr(T_("It is a scroll of amnesia."));
3381:             // included in default force_more_message (to show it before menu)
3382:         }
3383:         if (you.spell_no == 0 || you.has_mutation(MUT_INNATE_CASTER))
3384:         {
3385:             mpr(T_("You feel briefly forgetful."));
3386:             break;
3387:         }
3388:
3389:         if (!alreadyknown)
3390:             result = _run_read_scroll_uncancel(UNC_AMNESIA, *scroll);
3391:         else
3392:             result = _handle_amnesia(alreadyknown);
3393:
3394:         break;
3395:
3396:     case SCR_PLINKING:
3397:         _plinking_scroll();
3398:         break;
3399:
3400:     default:
3401:         mpr(T_("Read a buggy scroll, please report this."));
3402:         break;
3403:     }
3404:
3405:     if (alreadyknown && result == spret::seen_hups)
3406:         result = spret::abort;
3407:     ASSERT(result != spret::seen_hups || has_uncancel());
3408:
3409:     handle_post_scroll_effects(scroll, result, original_pos,
3410:                                nearby_mons, alreadyknown, dangerous,
```

C-08 stable
```cpp
2960:         feat_splash_noise(env.grid(you.pos()));
2961:
2962:     dec_inv_item_quantity(item_dropped, quant_drop);
2963:
2964:     you.turn_is_over = true;
2965:
2966:     you.last_pickup.erase(item_dropped);
2967:     if (you.last_unequip == item.link)
2968:         you.last_unequip = -1;
2969:
2970:     return true;
2971: }
2972:
2973: void drop_last()
2974: {
2975:     vector<SelItem> items_to_drop;
2976:
2977:     for (const auto &entry : you.last_pickup)
2978:     {
2979:         const item_def* item = &you.inv[entry.first];
2980:         if (item->quantity > 0)
2981:             items_to_drop.emplace_back(entry.first, entry.second, item);
2982:     }
2983:
2984:     if (items_to_drop.empty())
2985:         mpr(T_("No item to drop."));
2986:     else
2987:     {
2988:         you.last_pickup.clear();
2989:         _maybe_disable_autopickup_for_dropped_items(items_to_drop);
2990:         _multidrop(items_to_drop);
2991:     }
2992: }
2993:
2994: mon_inv_type get_mon_equip_slot(const monster* mon, const item_def &item)
2995: {
2996:     ASSERT(mon->alive());
2997:
2998:     mon_inv_type slot = item_to_mslot(item);
2999:
3000:     if (slot == NUM_MONSTER_SLOTS)
3001:         return NUM_MONSTER_SLOTS;
3002:
3003:     if (mon->mslot_item(slot) == &item)
3004:         return slot;
3005:
3006:     if (slot == MSLOT_WEAPON && mon->mslot_item(MSLOT_ALT_WEAPON) == &item)
3007:         return MSLOT_ALT_WEAPON;
3008:
3009:     return NUM_MONSTER_SLOTS;
3010: }
```

C-08 trunk
```cpp
2907:         feat_splash_noise(env.grid(you.pos()));
2908:
2909:     dec_inv_item_quantity(item_dropped, quant_drop);
2910:
2911:     you.turn_is_over = true;
2912:
2913:     you.last_pickup.erase(item_dropped);
2914:     if (you.last_unequip == item.link)
2915:         you.last_unequip = -1;
2916:
2917:     return true;
2918: }
2919:
2920: void drop_last()
2921: {
2922:     vector<SelItem> items_to_drop;
2923:
2924:     for (const auto &entry : you.last_pickup)
2925:     {
2926:         const item_def* item = &you.inv[entry.first];
2927:         if (item->quantity > 0)
2928:             items_to_drop.emplace_back(entry.first, entry.second, item);
2929:     }
2930:
2931:     if (items_to_drop.empty())
2932:         mpr(T_("No item to drop."));
2933:     else
2934:     {
2935:         you.last_pickup.clear();
2936:         _maybe_disable_autopickup_for_dropped_items(items_to_drop);
2937:         _multidrop(items_to_drop);
2938:     }
2939: }
2940:
2941: mon_inv_type get_mon_equip_slot(const monster* mon, const item_def &item)
2942: {
2943:     ASSERT(mon->alive());
2944:
2945:     mon_inv_type slot = item_to_mslot(item);
2946:
2947:     if (slot == NUM_MONSTER_SLOTS)
2948:         return NUM_MONSTER_SLOTS;
2949:
2950:     if (mon->mslot_item(slot) == &item)
2951:         return slot;
2952:
2953:     if (slot == MSLOT_WEAPON && mon->mslot_item(MSLOT_ALT_WEAPON) == &item)
2954:         return MSLOT_ALT_WEAPON;
2955:
2956:     return NUM_MONSTER_SLOTS;
2957: }
```

F-10 stable
```cpp
5140:
5141: void dec_slow_player(int delay)
5142: {
5143:     if (!you.duration[DUR_SLOW])
5144:         return;
5145:
5146:     delay = delay * (1 + you.wearing_jewellery(AMU_DISSIPATION));
5147:
5148:     if (you.duration[DUR_SLOW] > BASELINE_DELAY)
5149:     {
5150:         // Make slowing and hasting effects last as long.
5151:         you.duration[DUR_SLOW] -= you.duration[DUR_HASTE]
5152:             ? haste_mul(delay) : delay;
5153:     }
5154:
5155:     if (aura_is_active_on_player(TORPOR_SLOWED_KEY))
5156:     {
5157:         you.duration[DUR_SLOW] = max(1, you.duration[DUR_SLOW]);
5158:         return;
5159:     }
5160:
5161:     if (you.duration[DUR_SLOW] <= BASELINE_DELAY)
5162:     {
5163:         you.duration[DUR_SLOW] = 0;
5164:         if (!have_stat_zero())
5165:             mprf(MSGCH_DURATION, T_("You feel yourself speed up."));
5166:     }
5167: }
5168:
5169: void barb_player(int turns, int pow)
5170: {
5171:     ASSERT(!crawl_state.game_is_arena());
5172:
5173:     if (turns <= 0 || pow <= 0 || you.is_insubstantial())
5174:         return;
5175:
5176:     const int max_turns = 12;
5177:     const int max_pow = 6;
5178:
5179:     if (!you.duration[DUR_BARBS])
5180:     {
5181:         mpr(T_("Barbed spikes embed themselves in your body."));
5182:         you.set_duration(DUR_BARBS, min(max_turns, turns));
5183:         you.attribute[ATTR_BARBS_POW] = min(max_pow, pow);
5184:     }
5185:     else
5186:     {
5187:         mpr(T_("More barbed spikes embed themselves in your body."));
5188:         you.increase_duration(DUR_BARBS, turns, max_turns);
5189:         you.attribute[ATTR_BARBS_POW] =
5190:             min(max_pow, you.attribute[ATTR_BARBS_POW]++);
```

F-10 trunk
```cpp
5357:
5358: void dec_slow_player(int delay)
5359: {
5360:     if (!you.duration[DUR_SLOW])
5361:         return;
5362:
5363:     delay = delay * (1 + you.wearing_jewellery(AMU_DISSIPATION));
5364:
5365:     if (you.duration[DUR_SLOW] > BASELINE_DELAY)
5366:     {
5367:         // Make slowing and hasting effects last as long.
5368:         you.duration[DUR_SLOW] -= you.duration[DUR_HASTE]
5369:             ? haste_mul(delay) : delay;
5370:     }
5371:
5372:     if (aura_is_active_on_player(TORPOR_SLOWED_KEY))
5373:     {
5374:         you.duration[DUR_SLOW] = max(1, you.duration[DUR_SLOW]);
5375:         return;
5376:     }
5377:
5378:     if (you.duration[DUR_SLOW] <= BASELINE_DELAY)
5379:     {
5380:         you.duration[DUR_SLOW] = 0;
5381:         if (!have_stat_zero())
5382:             mprf(MSGCH_DURATION, T_("You feel yourself speed up."));
5383:     }
5384: }
5385:
5386: void barb_player(int turns, int pow)
5387: {
5388:     ASSERT(!crawl_state.game_is_arena());
5389:
5390:     if (turns <= 0 || pow <= 0 || you.is_insubstantial())
5391:         return;
5392:
5393:     const int max_turns = 12;
5394:     const int max_pow = 6;
5395:
5396:     if (!you.duration[DUR_BARBS])
5397:     {
5398:         mpr(T_("Barbed spikes embed themselves in your body."));
5399:         you.set_duration(DUR_BARBS, min(max_turns, turns));
5400:         you.attribute[ATTR_BARBS_POW] = min(max_pow, pow);
5401:     }
5402:     else
5403:     {
5404:         mpr(T_("More barbed spikes embed themselves in your body."));
5405:         you.increase_duration(DUR_BARBS, turns, max_turns);
5406:         you.attribute[ATTR_BARBS_POW] =
5407:             min(max_pow, you.attribute[ATTR_BARBS_POW]++);
```

F-11 stable
```cpp
4639:
4640:         if (!quiet)
4641:         {
4642:             mprf(MSGCH_WARN, T_("You are %sconfused."),
4643:                  old_value > 0 ? T_("more ") : "");
4644:         }
4645:
4646:         learned_something_new(HINT_YOU_ENCHANTED);
4647:
4648:         xom_is_stimulated((you.duration[DUR_CONF] - old_value)
4649:                            / BASELINE_DELAY);
4650:     }
4651:
4652:     return true;
4653: }
4654:
4655: bool poison_player(int amount, string source, string source_aux, bool force)
4656: {
4657:     ASSERT(!crawl_state.game_is_arena());
4658:
4659:     if (crawl_state.disables[DIS_AFFLICTIONS])
4660:         return false;
4661:
4662:     if (you.duration[DUR_DIVINE_STAMINA] > 0)
4663:     {
4664:         mpr(T_("Your divine stamina protects you from poison!"));
4665:         return false;
4666:     }
4667:
4668:     if (player_res_poison() >= 3)
4669:     {
4670:         dprf("Cannot poison, you are immune!");
4671:         return false;
4672:     }
4673:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4674:         return false;
4675:
4676:     const int old_value = you.duration[DUR_POISONING];
4677:     const bool was_fatal = poison_is_lethal();
4678:
4679:     if (player_res_poison() < 0)
4680:         amount *= 2;
4681:
4682:     // TODO: support being poisoned by monsters wearing "harm (ha)
4683:     if (you.extra_harm())
4684:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4685:
4686:     you.duration[DUR_POISONING] += amount * 1000;
4687:
4688:     if (you.duration[DUR_POISONING] > old_value)
4689:     {
```

F-11 trunk
```cpp
4859:
4860:         if (!quiet)
4861:         {
4862:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more confused.")
4863:                                                 : T_("You are confused."));
4864:         }
4865:
4866:         learned_something_new(HINT_YOU_ENCHANTED);
4867:
4868:         xom_is_stimulated((you.duration[DUR_CONF] - old_value)
4869:                            / BASELINE_DELAY);
4870:     }
4871:
4872:     return true;
4873: }
4874:
4875: bool poison_player(int amount, string source, string source_aux, bool force)
4876: {
4877:     ASSERT(!crawl_state.game_is_arena());
4878:
4879:     if (crawl_state.disables[DIS_AFFLICTIONS])
4880:         return false;
4881:
4882:     if (you.duration[DUR_DIVINE_STAMINA] > 0)
4883:     {
4884:         mpr(T_("Your divine stamina protects you from poison!"));
4885:         return false;
4886:     }
4887:
4888:     if (player_res_poison() >= 3)
4889:     {
4890:         dprf("Cannot poison, you are immune!");
4891:         return false;
4892:     }
4893:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4894:         return false;
4895:
4896:     const int old_value = you.duration[DUR_POISONING];
4897:     const bool was_fatal = poison_is_lethal();
4898:
4899:     if (player_res_poison() < 0)
4900:         amount = amount * 3 / 2;
4901:
4902:     // TODO: support being poisoned by monsters wearing "harm (ha)
4903:     if (you.extra_harm())
4904:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4905:
4906:     you.duration[DUR_POISONING] += amount * 1000;
4907:
4908:     if (you.duration[DUR_POISONING] > old_value)
4909:     {
```

E-09 stable
```cpp
3039:  *  or was canceled (spret::abort). Never returns spret::none.
3040:  */
3041: static spret _do_ability(const ability_def& abil, bool fail, dist *target,
3042:                          bolt& beam)
3043: {
3044:     // Note: the costs will not be applied until after this switch
3045:     // statement... it's assumed that only failures have returned! - bwr
3046:     switch (abil.ability)
3047:     {
3048: #if TAG_MAJOR_VERSION == 34
3049:     case ABIL_HEAL_WOUNDS:
3050:         fail_check();
3051:         if (one_chance_in(4))
3052:         {
3053:             mpr(T_("Your magical essence is drained by the effort!"));
3054:             rot_mp(1);
3055:         }
3056:         potionlike_effect(POT_HEAL_WOUNDS, 40);
3057:         break;
3058: #endif
3059:
3060:     case ABIL_DIG:
3061:         if (!you.digging)
3062:         {
3063:             you.digging = true;
3064:             mpr(T_("You extend your mandibles."));
3065:         }
3066:         else
3067:         {
3068:             you.digging = false;
3069:             mpr(T_("You retract your mandibles."));
3070:         }
3071:         break;
3072:
3073:     case ABIL_SHAFT_SELF:
3074:         if (you.can_do_shaft_ability(false))
3075:         {
3076:             if (cancel_harmful_move())
3077:                 return spret::abort;
3078:
3079:             if (beogh_cancel_leaving_floor())
3080:                 return spret::abort;
3081:
3082:             if (yesno(T_("Are you sure you want to shaft yourself?"), true, 'n'))
3083:                 start_delay<ShaftSelfDelay>(1);
3084:             else
3085:             {
3086:                 canned_msg(MSG_OK);
3087:                 return spret::abort;
3088:             }
3089:         }
```

E-09 stable
```cpp
3044:     // Note: the costs will not be applied until after this switch
3045:     // statement... it's assumed that only failures have returned! - bwr
3046:     switch (abil.ability)
3047:     {
3048: #if TAG_MAJOR_VERSION == 34
3049:     case ABIL_HEAL_WOUNDS:
3050:         fail_check();
3051:         if (one_chance_in(4))
3052:         {
3053:             mpr(T_("Your magical essence is drained by the effort!"));
3054:             rot_mp(1);
3055:         }
3056:         potionlike_effect(POT_HEAL_WOUNDS, 40);
3057:         break;
3058: #endif
3059:
3060:     case ABIL_DIG:
3061:         if (!you.digging)
3062:         {
3063:             you.digging = true;
3064:             mpr(T_("You extend your mandibles."));
3065:         }
3066:         else
3067:         {
3068:             you.digging = false;
3069:             mpr(T_("You retract your mandibles."));
3070:         }
3071:         break;
3072:
3073:     case ABIL_SHAFT_SELF:
3074:         if (you.can_do_shaft_ability(false))
3075:         {
3076:             if (cancel_harmful_move())
3077:                 return spret::abort;
3078:
3079:             if (beogh_cancel_leaving_floor())
3080:                 return spret::abort;
3081:
3082:             if (yesno(T_("Are you sure you want to shaft yourself?"), true, 'n'))
3083:                 start_delay<ShaftSelfDelay>(1);
3084:             else
3085:             {
3086:                 canned_msg(MSG_OK);
3087:                 return spret::abort;
3088:             }
3089:         }
3090:         else
3091:             return spret::abort;
3092:         break;
3093:
3094:     case ABIL_HOP:
```

E-09 trunk
```cpp
3190:  *  or was canceled (spret::abort). Never returns spret::none.
3191:  */
3192: static spret _do_ability(const ability_def& abil, bool fail, dist *target,
3193:                          bolt& beam, int piety_cost, int mp_cost, int hp_cost)
3194: {
3195:     // Note: the costs will not be applied until after this switch
3196:     // statement... it's assumed that only failures have returned! - bwr
3197:     switch (abil.ability)
3198:     {
3199: #if TAG_MAJOR_VERSION == 34
3200:     case ABIL_HEAL_WOUNDS:
3201:         fail_check();
3202:         if (one_chance_in(4))
3203:         {
3204:             mpr(T_("Your magical essence is drained by the effort!"));
3205:             rot_mp(1);
3206:         }
3207:         potionlike_effect(POT_HEAL_WOUNDS, 40);
3208:         break;
3209: #endif
3210:
3211:     case ABIL_DIG:
3212:         if (!you.digging)
3213:         {
3214:             you.digging = true;
3215:             mpr(T_("You extend your mandibles."));
3216:         }
3217:         else
3218:         {
3219:             you.digging = false;
3220:             mpr(T_("You retract your mandibles."));
3221:         }
3222:         break;
3223:
3224:     case ABIL_SHAFT_SELF:
3225:         if (you.can_do_shaft_ability(false))
3226:         {
3227:             if (cancel_harmful_move())
3228:                 return spret::abort;
3229:
3230:             if (beogh_cancel_leaving_floor())
3231:                 return spret::abort;
3232:
3233:             if (yesno(T_("Are you sure you want to shaft yourself?"), true, 'n'))
3234:                 start_delay<ShaftSelfDelay>(1);
3235:             else
3236:             {
3237:                 canned_msg(MSG_OK);
3238:                 return spret::abort;
3239:             }
3240:         }
```

E-09 trunk
```cpp
3195:     // Note: the costs will not be applied until after this switch
3196:     // statement... it's assumed that only failures have returned! - bwr
3197:     switch (abil.ability)
3198:     {
3199: #if TAG_MAJOR_VERSION == 34
3200:     case ABIL_HEAL_WOUNDS:
3201:         fail_check();
3202:         if (one_chance_in(4))
3203:         {
3204:             mpr(T_("Your magical essence is drained by the effort!"));
3205:             rot_mp(1);
3206:         }
3207:         potionlike_effect(POT_HEAL_WOUNDS, 40);
3208:         break;
3209: #endif
3210:
3211:     case ABIL_DIG:
3212:         if (!you.digging)
3213:         {
3214:             you.digging = true;
3215:             mpr(T_("You extend your mandibles."));
3216:         }
3217:         else
3218:         {
3219:             you.digging = false;
3220:             mpr(T_("You retract your mandibles."));
3221:         }
3222:         break;
3223:
3224:     case ABIL_SHAFT_SELF:
3225:         if (you.can_do_shaft_ability(false))
3226:         {
3227:             if (cancel_harmful_move())
3228:                 return spret::abort;
3229:
3230:             if (beogh_cancel_leaving_floor())
3231:                 return spret::abort;
3232:
3233:             if (yesno(T_("Are you sure you want to shaft yourself?"), true, 'n'))
3234:                 start_delay<ShaftSelfDelay>(1);
3235:             else
3236:             {
3237:                 canned_msg(MSG_OK);
3238:                 return spret::abort;
3239:             }
3240:         }
3241:         else
3242:             return spret::abort;
3243:         break;
3244:
3245:     case ABIL_HOP:
```

E-11 stable
```cpp
748:         reason->clear();
749:     if (!get_form()->can_cast)
750:     {
751:         if (reason)
752:             *reason = T_("You can't do that in your present form.");
753:         if (!quiet)
754:             canned_msg(MSG_PRESENT_FORM);
755:         return false;
756:     }
757:
758:     if (you.duration[DUR_NO_CAST])
759:     {
760:         if (reason)
761:             *reason = T_("You are unable to access your magic!");
762:         if (!quiet)
763:             mpr(T_("You are unable to access your magic!"));
764:         return false;
765:     }
766:
767:     // Randart weapons.
768:     if (you.no_cast())
769:     {
770:         if (reason)
771:             *reason = T_("Something interferes with your magic!");
772:         if (!quiet)
773:             mpr(T_("Something interferes with your magic!"));
774:         return false;
775:     }
776:
777:     if (you.berserk())
778:     {
779:         if (reason)
780:             *reason = T_("You are too berserk!");
781:         if (!quiet)
782:             canned_msg(MSG_TOO_BERSERK);
783:         return false;
784:     }
785:
786:     if (you.confused())
787:     {
788:         if (reason)
789:             *reason = T_("You're too confused to cast spells.");
790:         if (!quiet)
791:             mpr(T_("You're too confused to cast spells."));
792:         return false;
793:     }
794:
795:     if (you.is_silenced())
796:     {
797:         if (reason)
798:         {
```

E-11 trunk
```cpp
780:         reason->clear();
781:     if (!get_form()->can_cast)
782:     {
783:         if (reason)
784:             *reason = T_("You can't do that in your present form.");
785:         if (!quiet)
786:             canned_msg(MSG_PRESENT_FORM);
787:         return false;
788:     }
789:
790:     if (you.duration[DUR_NO_CAST])
791:     {
792:         if (reason)
793:             *reason = T_("You are unable to access your magic!");
794:         if (!quiet)
795:             mpr(T_("You are unable to access your magic!"));
796:         return false;
797:     }
798:
799:     // Randart weapons.
800:     if (you.no_cast())
801:     {
802:         if (reason)
803:             *reason = T_("Something interferes with your magic!");
804:         if (!quiet)
805:             mpr(T_("Something interferes with your magic!"));
806:         return false;
807:     }
808:
809:     if (you.berserk())
810:     {
811:         if (reason)
812:             *reason = T_("You are too berserk!");
813:         if (!quiet)
814:             canned_msg(MSG_TOO_BERSERK);
815:         return false;
816:     }
817:
818:     if (you.confused())
819:     {
820:         if (reason)
821:             *reason = T_("You're too confused to cast spells.");
822:         if (!quiet)
823:             mpr(T_("You're too confused to cast spells."));
824:         return false;
825:     }
826:
827:     if (!ignore_silence && you.is_silenced())
828:     {
829:         if (reason)
830:         {
```

A-07 stable
```cpp
493: {
494:     switch (ftype)
495:     {
496:     case DNGN_ENTER_ZOT:
497:         if (!you.level_visited(level_id(BRANCH_ZOT, 1)) && !crawl_state.game_is_descent())
498:             _rune_effect(ftype);
499:         break;
500:     case DNGN_EXIT_VAULTS:
501:         if (vaults_is_locked())
502:         {
503:             unlock_vaults();
504:             _rune_effect(ftype);
505:         }
506:         break;
507:     default:
508:         break;
509:     }
510: }
511:
512: static void _gauntlet_effect()
513: {
514:     // already doomed
515:     if (you.stasis())
516:         return;
517:
518:     mprf(MSGCH_WARN, T_("The nature of this place prevents your teleportation."));
519:
520:     if (you.get_base_mutation_level(MUT_TELEPORTITIS))
521:         mpr(T_("You feel stable on this level."));
522: }
523:
524: static void _hell_effects()
525: {
526:
527:     // 50% chance at max piety
528:     if (have_passive(passive_t::resist_hell_effects)
529:         && x_chance_in_y(you.piety(), MAX_PIETY * 2))
530:     {
531:         simple_god_message(T_(" power protects you from the chaos of Hell!"), true);
532:         return;
533:     }
534:
535:     const bool loud = one_chance_in(6) && !silenced(you.pos());
536:     string msg = getMiscString(loud ? "hell_effect_noisy"
537:                                     : "hell_effect_quiet");
538:     if (msg.empty())
539:         msg = "Something hellishly buggy happens.";
540:
541:     mprf(MSGCH_HELL_EFFECT, "%s", msg.c_str());
542:     if (loud)
543:         noisy(15, you.pos());
```

A-07 stable
```cpp
496:     case DNGN_ENTER_ZOT:
497:         if (!you.level_visited(level_id(BRANCH_ZOT, 1)) && !crawl_state.game_is_descent())
498:             _rune_effect(ftype);
499:         break;
500:     case DNGN_EXIT_VAULTS:
501:         if (vaults_is_locked())
502:         {
503:             unlock_vaults();
504:             _rune_effect(ftype);
505:         }
506:         break;
507:     default:
508:         break;
509:     }
510: }
511:
512: static void _gauntlet_effect()
513: {
514:     // already doomed
515:     if (you.stasis())
516:         return;
517:
518:     mprf(MSGCH_WARN, T_("The nature of this place prevents your teleportation."));
519:
520:     if (you.get_base_mutation_level(MUT_TELEPORTITIS))
521:         mpr(T_("You feel stable on this level."));
522: }
523:
524: static void _hell_effects()
525: {
526:
527:     // 50% chance at max piety
528:     if (have_passive(passive_t::resist_hell_effects)
529:         && x_chance_in_y(you.piety(), MAX_PIETY * 2))
530:     {
531:         simple_god_message(T_(" power protects you from the chaos of Hell!"), true);
532:         return;
533:     }
534:
535:     const bool loud = one_chance_in(6) && !silenced(you.pos());
536:     string msg = getMiscString(loud ? "hell_effect_noisy"
537:                                     : "hell_effect_quiet");
538:     if (msg.empty())
539:         msg = "Something hellishly buggy happens.";
540:
541:     mprf(MSGCH_HELL_EFFECT, "%s", msg.c_str());
542:     if (loud)
543:         noisy(15, you.pos());
544:
545:     switch (random2(3))
546:     {
```

A-07 trunk
```cpp
505: {
506:     switch (ftype)
507:     {
508:     case DNGN_ENTER_ZOT:
509:         if (!you.level_visited(level_id(BRANCH_ZOT, 1)) && !crawl_state.game_is_descent())
510:             _rune_effect(ftype);
511:         break;
512:     case DNGN_EXIT_VAULTS:
513:         if (vaults_is_locked())
514:         {
515:             unlock_vaults();
516:             _rune_effect(ftype);
517:         }
518:         break;
519:     default:
520:         break;
521:     }
522: }
523:
524: static void _gauntlet_effect()
525: {
526:     // already doomed
527:     if (you.stasis())
528:         return;
529:
530:     mprf(MSGCH_WARN, T_("The nature of this place prevents your teleportation."));
531:
532:     if (you.get_base_mutation_level(MUT_TELEPORTITIS))
533:         mpr(T_("You feel stable on this level."));
534: }
535:
536: static void _hell_effects()
537: {
538:
539:     // 50% chance at max piety
540:     if (have_passive(passive_t::resist_hell_effects)
541:         && x_chance_in_y(you.piety(), MAX_PIETY * 2))
542:     {
543:         simple_god_message(T_(" power protects you from the chaos of Hell!"), true);
544:         return;
545:     }
546:
547:     const bool loud = one_chance_in(6) && !silenced(you.pos());
548:     string msg = getMiscString(loud ? "hell_effect_noisy"
549:                                     : "hell_effect_quiet");
550:     if (msg.empty())
551:         msg = "Something hellishly buggy happens.";
552:
553:     mprf(MSGCH_HELL_EFFECT, "%s", msg.c_str());
554:     if (loud)
555:         noisy(15, you.pos());
```

A-07 trunk
```cpp
508:     case DNGN_ENTER_ZOT:
509:         if (!you.level_visited(level_id(BRANCH_ZOT, 1)) && !crawl_state.game_is_descent())
510:             _rune_effect(ftype);
511:         break;
512:     case DNGN_EXIT_VAULTS:
513:         if (vaults_is_locked())
514:         {
515:             unlock_vaults();
516:             _rune_effect(ftype);
517:         }
518:         break;
519:     default:
520:         break;
521:     }
522: }
523:
524: static void _gauntlet_effect()
525: {
526:     // already doomed
527:     if (you.stasis())
528:         return;
529:
530:     mprf(MSGCH_WARN, T_("The nature of this place prevents your teleportation."));
531:
532:     if (you.get_base_mutation_level(MUT_TELEPORTITIS))
533:         mpr(T_("You feel stable on this level."));
534: }
535:
536: static void _hell_effects()
537: {
538:
539:     // 50% chance at max piety
540:     if (have_passive(passive_t::resist_hell_effects)
541:         && x_chance_in_y(you.piety(), MAX_PIETY * 2))
542:     {
543:         simple_god_message(T_(" power protects you from the chaos of Hell!"), true);
544:         return;
545:     }
546:
547:     const bool loud = one_chance_in(6) && !silenced(you.pos());
548:     string msg = getMiscString(loud ? "hell_effect_noisy"
549:                                     : "hell_effect_quiet");
550:     if (msg.empty())
551:         msg = "Something hellishly buggy happens.";
552:
553:     mprf(MSGCH_HELL_EFFECT, "%s", msg.c_str());
554:     if (loud)
555:         noisy(15, you.pos());
556:
557:     switch (random2(3))
558:     {
```

D-01 stable
```cpp
3279:             dec_mitm_item_quantity(scroll->index(), 1);
3280:
3281:         count_action(CACT_USE, OBJ_SCROLLS);
3282:         count_action(CACT_READ, scroll->sub_type);
3283:
3284:         if (is_loud)
3285:             noisy(40, original_pos, MID_PLAYER);
3286:     }
3287:
3288:     if (!alreadyknown
3289:         && which_scroll != SCR_BRAND_WEAPON
3290:         && which_scroll != SCR_ENCHANT_WEAPON
3291:         && which_scroll != SCR_IDENTIFY
3292:         && which_scroll != SCR_ENCHANT_ARMOUR
3293:         && which_scroll != SCR_AMNESIA
3294:         && which_scroll != SCR_ACQUIREMENT)
3295:     {
3296:         mprf(scroll->quantity < prev_quantity ? T_("It was %s.") : T_("It is %s."),
3297:              article_a(scroll_name).c_str());
3298:     }
3299:
3300:     if (!alreadyknown)
3301:     {
3302:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3303:         {
3304:             mpr(T_("The power of discovery flows from your fingertips!"));
3305:             potionlike_effect(POT_MAGIC, 40);
3306:         }
3307:
3308:         if (dangerous)
3309:         {
3310:             // Xom loves it when you read an unknown scroll and there is a
3311:             // dangerous monster nearby... (though not as much as potions
3312:             // since there are no *really* bad scrolls, merely useless ones).
3313:             xom_is_stimulated(bad_effect ? 100 : 50);
3314:         }
3315:     }
3316:
3317:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3318:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3319:         && nearby_mons
3320:         && !cancel_scroll)
3321:     {
3322:         you.props[VICTORY_CONDUCT_KEY] = true;
3323:     }
3324:
3325:     if (!alreadyknown)
3326:         auto_assign_item_slot(*scroll);
3327:     return true;
3328: }
3329:
```

D-01 trunk
```cpp
2095:
2096:     if (!quaff_potion(*potion, did_swing))
2097:         return false;
2098:
2099:     // XXX: maybe being a status-effect potion should be in item-prop.cc?
2100:     if (you.has_mutation(MUT_EFFICIENT_METABOLISM)
2101:         && (potion->sub_type == POT_AMBROSIA
2102:             || potion->sub_type == POT_ATTRACTION
2103:             || potion->sub_type == POT_BERSERK_RAGE
2104:             || potion->sub_type == POT_BRILLIANCE
2105:             || potion->sub_type == POT_ENLIGHTENMENT
2106:             || potion->sub_type == POT_HASTE
2107:             || potion->sub_type == POT_INVISIBILITY
2108:             || potion->sub_type == POT_LIGNIFY
2109:             || potion->sub_type == POT_MIGHT
2110:             || potion->sub_type == POT_RESISTANCE))
2111:         {
2112:             mprf(T_("Your mutated metabolism churns, savouring the %s."),
2113:                 potion->name(DESC_QUALNAME).c_str());
2114:         }
2115:
2116:     if (!alreadyknown)
2117:     {
2118:         if (heal_on_id)
2119:         {
2120:             mpr(T_("The power of discovery flows from your fingertips!"));
2121:             potionlike_effect(POT_HEAL_WOUNDS, 40);
2122:         }
2123:
2124:         if (dangerous)
2125:         {
2126:             // Xom loves it when you drink an unknown potion and there is
2127:             // a dangerous monster nearby...
2128:             xom_is_stimulated(200);
2129:         }
2130:     }
2131:
2132:     // Drinking with hostile visible mons nearby resets unrand "Victory" stats.
2133:     if (you.unrand_equipped(UNRAND_VICTORY, true) && nearby_mons)
2134:         you.props[VICTORY_CONDUCT_KEY] = true;
2135:
2136:     // We'll need this later, after destroying the item.
2137:     const bool was_exp = potion->sub_type == POT_EXPERIENCE;
2138:     if (in_inventory(*potion))
2139:     {
2140:         dec_inv_item_quantity(potion->link, 1);
2141:         if (!alreadyknown)
2142:             auto_assign_item_slot(*potion);
2143:     }
2144:     else
2145:         dec_mitm_item_quantity(potion->index(), 1);
```

D-01 trunk
```cpp
3441:         count_action(CACT_USE, OBJ_SCROLLS);
3442:         count_action(CACT_READ, scroll->sub_type);
3443:
3444:         if (is_loud)
3445:             noisy(40, original_pos, MID_PLAYER);
3446:     }
3447:
3448:     const scroll_type which_scroll = static_cast<scroll_type>(scroll->sub_type);
3449:
3450:     if (!alreadyknown
3451:         && which_scroll != SCR_BRAND_WEAPON
3452:         && which_scroll != SCR_ENCHANT_WEAPON
3453:         && which_scroll != SCR_IDENTIFY
3454:         && which_scroll != SCR_ENCHANT_ARMOUR
3455:         && which_scroll != SCR_AMNESIA
3456:         && which_scroll != SCR_ACQUIREMENT)
3457:     {
3458:         mprf(read_result == spret::abort ? T_("It is %s.") : T_("It was %s."),
3459:              article_a(scroll_name).c_str());
3460:     }
3461:
3462:     if (!alreadyknown)
3463:     {
3464:         if (you.unrand_equipped(UNRAND_DELATRAS_GLOVES))
3465:         {
3466:             mpr(T_("The power of discovery flows from your fingertips!"));
3467:             potionlike_effect(POT_MAGIC, 40);
3468:         }
3469:
3470:         if (dangerous)
3471:         {
3472:             // Xom loves it when you read an unknown scroll and there is a
3473:             // dangerous monster nearby... (though not as much as potions
3474:             // since there are no *really* bad scrolls, merely useless ones).
3475:             xom_is_stimulated(bad_effect ? 100 : 50);
3476:         }
3477:     }
3478:
3479:     // Reading with hostile visible mons nearby resets unrand "Victory" stats.
3480:     if (you.unrand_equipped(UNRAND_VICTORY, true)
3481:         && nearby_mons
3482:         && read_result != spret::abort)
3483:     {
3484:         you.props[VICTORY_CONDUCT_KEY] = true;
3485:     }
3486:
3487:     if (!alreadyknown)
3488:         auto_assign_item_slot(*scroll);
3489: }
3490:
3491: class targeter_invisibility : public targeter_multimonster
```

F-05 stable
```cpp
4667:
4668:     if (player_res_poison() >= 3)
4669:     {
4670:         dprf("Cannot poison, you are immune!");
4671:         return false;
4672:     }
4673:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4674:         return false;
4675:
4676:     const int old_value = you.duration[DUR_POISONING];
4677:     const bool was_fatal = poison_is_lethal();
4678:
4679:     if (player_res_poison() < 0)
4680:         amount *= 2;
4681:
4682:     // TODO: support being poisoned by monsters wearing "harm (ha)
4683:     if (you.extra_harm())
4684:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4685:
4686:     you.duration[DUR_POISONING] += amount * 1000;
4687:
4688:     if (you.duration[DUR_POISONING] > old_value)
4689:     {
4690:         if (poison_is_lethal() && !was_fatal)
4691:         {
4692:             mprf(MSGCH_DANGER,
4693:                 T_("You are lethally poisoned!"));
4694:         }
4695:         else
4696:         {
4697:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4698:                                          : T_("You are poisoned."));
4699:         }
4700:
4701:         learned_something_new(HINT_YOU_POISON);
4702:     }
4703:
4704:     you.props[POISONER_KEY] = source;
4705:     you.props[POISON_AUX_KEY] = source_aux;
4706:
4707:     // Display the poisoned segment of our health, in case we take no damage
4708:     you.redraw_hit_points = true;
4709:
4710:     return amount;
4711: }
4712:
4713: int get_player_poisoning()
4714: {
4715:     if (player_res_poison() >= 3)
4716:         return 0;
4717: #if TAG_MAJOR_VERSION == 34
4718:     // Approximate the effect of damage shaving by giving the first
```

F-05 stable
```cpp
4672:     }
4673:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4674:         return false;
4675:
4676:     const int old_value = you.duration[DUR_POISONING];
4677:     const bool was_fatal = poison_is_lethal();
4678:
4679:     if (player_res_poison() < 0)
4680:         amount *= 2;
4681:
4682:     // TODO: support being poisoned by monsters wearing "harm (ha)
4683:     if (you.extra_harm())
4684:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4685:
4686:     you.duration[DUR_POISONING] += amount * 1000;
4687:
4688:     if (you.duration[DUR_POISONING] > old_value)
4689:     {
4690:         if (poison_is_lethal() && !was_fatal)
4691:         {
4692:             mprf(MSGCH_DANGER,
4693:                 T_("You are lethally poisoned!"));
4694:         }
4695:         else
4696:         {
4697:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4698:                                          : T_("You are poisoned."));
4699:         }
4700:
4701:         learned_something_new(HINT_YOU_POISON);
4702:     }
4703:
4704:     you.props[POISONER_KEY] = source;
4705:     you.props[POISON_AUX_KEY] = source_aux;
4706:
4707:     // Display the poisoned segment of our health, in case we take no damage
4708:     you.redraw_hit_points = true;
4709:
4710:     return amount;
4711: }
4712:
4713: int get_player_poisoning()
4714: {
4715:     if (player_res_poison() >= 3)
4716:         return 0;
4717: #if TAG_MAJOR_VERSION == 34
4718:     // Approximate the effect of damage shaving by giving the first
4719:     // 25 points of poison damage for 'free'
4720:     if (can_shave_damage())
4721:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4722: #endif
4723:     return you.duration[DUR_POISONING] / 1000;
```

F-05 stable
```cpp
4672:     }
4673:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4674:         return false;
4675:
4676:     const int old_value = you.duration[DUR_POISONING];
4677:     const bool was_fatal = poison_is_lethal();
4678:
4679:     if (player_res_poison() < 0)
4680:         amount *= 2;
4681:
4682:     // TODO: support being poisoned by monsters wearing "harm (ha)
4683:     if (you.extra_harm())
4684:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4685:
4686:     you.duration[DUR_POISONING] += amount * 1000;
4687:
4688:     if (you.duration[DUR_POISONING] > old_value)
4689:     {
4690:         if (poison_is_lethal() && !was_fatal)
4691:         {
4692:             mprf(MSGCH_DANGER,
4693:                 T_("You are lethally poisoned!"));
4694:         }
4695:         else
4696:         {
4697:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4698:                                          : T_("You are poisoned."));
4699:         }
4700:
4701:         learned_something_new(HINT_YOU_POISON);
4702:     }
4703:
4704:     you.props[POISONER_KEY] = source;
4705:     you.props[POISON_AUX_KEY] = source_aux;
4706:
4707:     // Display the poisoned segment of our health, in case we take no damage
4708:     you.redraw_hit_points = true;
4709:
4710:     return amount;
4711: }
4712:
4713: int get_player_poisoning()
4714: {
4715:     if (player_res_poison() >= 3)
4716:         return 0;
4717: #if TAG_MAJOR_VERSION == 34
4718:     // Approximate the effect of damage shaving by giving the first
4719:     // 25 points of poison damage for 'free'
4720:     if (can_shave_damage())
4721:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4722: #endif
4723:     return you.duration[DUR_POISONING] / 1000;
```

F-05 trunk
```cpp
4887:
4888:     if (player_res_poison() >= 3)
4889:     {
4890:         dprf("Cannot poison, you are immune!");
4891:         return false;
4892:     }
4893:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4894:         return false;
4895:
4896:     const int old_value = you.duration[DUR_POISONING];
4897:     const bool was_fatal = poison_is_lethal();
4898:
4899:     if (player_res_poison() < 0)
4900:         amount = amount * 3 / 2;
4901:
4902:     // TODO: support being poisoned by monsters wearing "harm (ha)
4903:     if (you.extra_harm())
4904:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4905:
4906:     you.duration[DUR_POISONING] += amount * 1000;
4907:
4908:     if (you.duration[DUR_POISONING] > old_value)
4909:     {
4910:         if (poison_is_lethal() && !was_fatal)
4911:         {
4912:             mprf(MSGCH_DANGER,
4913:                 T_("You are lethally poisoned!"));
4914:         }
4915:         else
4916:         {
4917:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4918:                                                 : T_("You are poisoned."));
4919:         }
4920:
4921:         learned_something_new(HINT_YOU_POISON);
4922:     }
4923:
4924:     you.props[POISONER_KEY] = source;
4925:     you.props[POISON_AUX_KEY] = source_aux;
4926:
4927:     // Display the poisoned segment of our health, in case we take no damage
4928:     you.redraw_hit_points = true;
4929:
4930:     return amount;
4931: }
4932:
4933: int get_player_poisoning()
4934: {
4935:     if (player_res_poison() >= 3)
4936:         return 0;
4937: #if TAG_MAJOR_VERSION == 34
4938:     // Approximate the effect of damage shaving by giving the first
```

F-05 trunk
```cpp
4892:     }
4893:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4894:         return false;
4895:
4896:     const int old_value = you.duration[DUR_POISONING];
4897:     const bool was_fatal = poison_is_lethal();
4898:
4899:     if (player_res_poison() < 0)
4900:         amount = amount * 3 / 2;
4901:
4902:     // TODO: support being poisoned by monsters wearing "harm (ha)
4903:     if (you.extra_harm())
4904:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4905:
4906:     you.duration[DUR_POISONING] += amount * 1000;
4907:
4908:     if (you.duration[DUR_POISONING] > old_value)
4909:     {
4910:         if (poison_is_lethal() && !was_fatal)
4911:         {
4912:             mprf(MSGCH_DANGER,
4913:                 T_("You are lethally poisoned!"));
4914:         }
4915:         else
4916:         {
4917:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4918:                                                 : T_("You are poisoned."));
4919:         }
4920:
4921:         learned_something_new(HINT_YOU_POISON);
4922:     }
4923:
4924:     you.props[POISONER_KEY] = source;
4925:     you.props[POISON_AUX_KEY] = source_aux;
4926:
4927:     // Display the poisoned segment of our health, in case we take no damage
4928:     you.redraw_hit_points = true;
4929:
4930:     return amount;
4931: }
4932:
4933: int get_player_poisoning()
4934: {
4935:     if (player_res_poison() >= 3)
4936:         return 0;
4937: #if TAG_MAJOR_VERSION == 34
4938:     // Approximate the effect of damage shaving by giving the first
4939:     // 25 points of poison damage for 'free'
4940:     if (can_shave_damage())
4941:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4942: #endif
4943:     return you.duration[DUR_POISONING] / 1000;
```

F-05 trunk
```cpp
4892:     }
4893:     else if (!force && player_res_poison() > 0 && !one_chance_in(3))
4894:         return false;
4895:
4896:     const int old_value = you.duration[DUR_POISONING];
4897:     const bool was_fatal = poison_is_lethal();
4898:
4899:     if (player_res_poison() < 0)
4900:         amount = amount * 3 / 2;
4901:
4902:     // TODO: support being poisoned by monsters wearing "harm (ha)
4903:     if (you.extra_harm())
4904:         amount *= (100 + incoming_harm_amount(you.extra_harm())) / 100;
4905:
4906:     you.duration[DUR_POISONING] += amount * 1000;
4907:
4908:     if (you.duration[DUR_POISONING] > old_value)
4909:     {
4910:         if (poison_is_lethal() && !was_fatal)
4911:         {
4912:             mprf(MSGCH_DANGER,
4913:                 T_("You are lethally poisoned!"));
4914:         }
4915:         else
4916:         {
4917:             mprf(MSGCH_WARN, "%s", old_value > 0 ? T_("You are more poisoned.")
4918:                                                 : T_("You are poisoned."));
4919:         }
4920:
4921:         learned_something_new(HINT_YOU_POISON);
4922:     }
4923:
4924:     you.props[POISONER_KEY] = source;
4925:     you.props[POISON_AUX_KEY] = source_aux;
4926:
4927:     // Display the poisoned segment of our health, in case we take no damage
4928:     you.redraw_hit_points = true;
4929:
4930:     return amount;
4931: }
4932:
4933: int get_player_poisoning()
4934: {
4935:     if (player_res_poison() >= 3)
4936:         return 0;
4937: #if TAG_MAJOR_VERSION == 34
4938:     // Approximate the effect of damage shaving by giving the first
4939:     // 25 points of poison damage for 'free'
4940:     if (can_shave_damage())
4941:         return max(0, (you.duration[DUR_POISONING] / 1000) - 25);
4942: #endif
4943:     return you.duration[DUR_POISONING] / 1000;
```

B-08 stable
```cpp
4914:                  attack_strength_punctuation(dmg).c_str());
4915:
4916:             // ...until now, since we know damage was done.
4917:             mons_adjust_flavoured(mon, beam, raw_dmg);
4918:
4919:             mon->hurt(&you, dmg);
4920:
4921:             if (mon->alive())
4922:                 print_wounds(*mon);
4923:         }
4924:     }
4925: }
4926:
4927: void melee_attack::emit_foul_stench()
4928: {
4929:     monster* mon = attacker->as_monster();
4930:
4931:     if (you.has_mutation(MUT_FOUL_STENCH)
4932:         && attacker->alive()
4933:         && adjacent(you.pos(), mon->pos()))
4934:     {
4935:         const int mut = you.get_mutation_level(MUT_FOUL_STENCH);
4936:
4937:         if (damage_done > 0 && x_chance_in_y(mut * 3 - 1, 20))
4938:         {
4939:             mpr(T_("You emit a cloud of foul miasma!"));
4940:             place_cloud(CLOUD_MIASMA, mon->pos(), 5 + random2(6), &you);
4941:         }
4942:     }
4943: }
4944:
4945: /** For UNRAND_STARLIGHT's dazzle effect, currently only when worn by the player.
4946:  */
4947: void melee_attack::do_starlight()
4948: {
4949:     static const vector<string> dazzle_msgs = {
4950:         "@The_monster@ is blinded by the light from your cloak!",
4951:         "@The_monster@ is temporarily struck blind!",
4952:         "@The_monster_possessive@ sight is seared by the starlight!",
4953:         "@The_monster_possessive@ vision is obscured by starry radiance!",
4954:     };
4955:
4956:     if (attacker->is_monster()
4957:         && attacker->res_blind() <= 1
4958:         && !attacker->as_monster()->has_ench(ENCH_BLIND)
4959:         && adjacent(attacker->pos(), defender->pos())
4960:         && x_chance_in_y(min(50, (95 - defender->get_hit_dice() * 4) / 5), 50))
4961:     {
4962:         attacker->as_monster()->add_ench(mon_enchant(ENCH_BLIND, &you,
4963:                                          random_range(4, 8) * BASELINE_DELAY));
4964:
```

B-08 trunk
```cpp
5107:                  attack_strength_punctuation(dmg).c_str());
5108:
5109:             // ...until now, since we know damage was done.
5110:             mons_adjust_flavoured(mon, beam, raw_dmg);
5111:
5112:             mon->hurt(&you, dmg);
5113:
5114:             if (mon->alive())
5115:                 print_wounds(*mon);
5116:         }
5117:     }
5118: }
5119:
5120: void melee_attack::emit_foul_stench()
5121: {
5122:     monster* mon = attacker->as_monster();
5123:
5124:     if (you.has_mutation(MUT_FOUL_STENCH)
5125:         && attacker->alive()
5126:         && adjacent(you.pos(), mon->pos()))
5127:     {
5128:         const int mut = you.get_mutation_level(MUT_FOUL_STENCH);
5129:
5130:         if (damage_done > 0 && x_chance_in_y(mut * 3 - 1, 20))
5131:         {
5132:             mpr(T_("You emit a cloud of foul miasma!"));
5133:             place_cloud(CLOUD_MIASMA, mon->pos(), 5 + random2(6), &you);
5134:         }
5135:     }
5136: }
5137:
5138: /** For UNRAND_STARLIGHT's dazzle effect, currently only when worn by the player.
5139:  */
5140: void melee_attack::do_starlight()
5141: {
5142:     static const vector<string> dazzle_msgs = {
5143:         "@The_monster@ is blinded by the light from your cloak!",
5144:         "@The_monster@ is temporarily struck blind!",
5145:         "@The_monster_possessive@ sight is seared by the starlight!",
5146:         "@The_monster_possessive@ vision is obscured by starry radiance!",
5147:     };
5148:
5149:     if (attacker->is_monster()
5150:         && attacker->res_blind() <= 1
5151:         && !attacker->as_monster()->has_ench(ENCH_BLIND)
5152:         && adjacent(attacker->pos(), defender->pos())
5153:         && x_chance_in_y(min(50, (95 - defender->get_hit_dice() * 4) / 5), 50))
5154:     {
5155:         attacker->as_monster()->add_ench(mon_enchant(ENCH_BLIND, &you,
5156:                                          random_range(4, 8) * BASELINE_DELAY));
5157:
```

D-07 stable
```cpp
895:
896:     set<coord_def> target_cells;
897:     bool see_targets = false;
898:
899:     for (radius_iterator di(you.pos(), LOS_NO_TRANS); di; ++di)
900:     {
901:         monster *mons = monster_at(*di);
902:
903:         if (!mons || mons->wont_attack() || !mons_is_threatening(*mons))
904:             continue;
905:
906:         if (you.can_see(*mons))
907:             see_targets = true;
908:
909:         for (adjacent_iterator ai(mons->pos(), false); ai; ++ai)
910:         {
911:             if (cell_is_solid(*ai) || !you.see_cell(*ai) || cloud_at(*ai))
912:                 continue;
913:             const actor *act = actor_at(*ai);
914:             if (!act || !act->wont_attack())
915:                 target_cells.insert(*ai);
916:         }
917:     }
918:
919:     if (!see_targets
920:         && !yesno(T_("You can't see anything. Try to condense clouds anyway?"),
921:                   true, 'n'))
922:     {
923:         canned_msg(MSG_OK);
924:         return spret::abort;
925:     }
926:
927:     if (target_cells.empty())
928:     {
929:         canned_msg(MSG_NOTHING_HAPPENS);
930:         return spret::fail;
931:     }
932:
933:     vector<coord_def> target_list;
934:     for (coord_def t : target_cells)
935:         target_list.push_back(t);
936:     shuffle_array(target_list);
937:     bool did_something = false;
938:
939:     for (auto p : target_list)
940:     {
941:         cloud_type cloud = cloud_picker.pick(condenser_clouds, pow, CLOUD_NONE);
942:
943:         // Reroll misery clouds until we get something our god is okay with
944:         while (is_good_god(you.religion) && cloud == CLOUD_MISERY)
945:             cloud = cloud_picker.pick(condenser_clouds, pow, CLOUD_NONE);
946:
```

D-07 trunk
```cpp
868:
869:     set<coord_def> target_cells;
870:     bool see_targets = false;
871:
872:     for (radius_iterator di(you.pos(), LOS_NO_TRANS); di; ++di)
873:     {
874:         monster *mons = monster_at(*di);
875:
876:         if (!mons || mons->wont_attack() || !mons_is_threatening(*mons))
877:             continue;
878:
879:         if (you.can_see(*mons))
880:             see_targets = true;
881:
882:         for (adjacent_iterator ai(mons->pos(), false); ai; ++ai)
883:         {
884:             if (cell_is_solid(*ai) || !you.see_cell(*ai) || cloud_at(*ai))
885:                 continue;
886:             const actor *act = actor_at(*ai);
887:             if (!act || !act->wont_attack())
888:                 target_cells.insert(*ai);
889:         }
890:     }
891:
892:     if (!see_targets
893:         && !yesno(T_("You can't see anything. Try to condense clouds anyway?"),
894:                   true, 'n'))
895:     {
896:         canned_msg(MSG_OK);
897:         return spret::abort;
898:     }
899:
900:     if (target_cells.empty())
901:     {
902:         canned_msg(MSG_NOTHING_HAPPENS);
903:         return spret::fail;
904:     }
905:
906:     vector<coord_def> target_list;
907:     for (coord_def t : target_cells)
908:         target_list.push_back(t);
909:     shuffle_array(target_list);
910:     bool did_something = false;
911:
912:     for (auto p : target_list)
913:     {
914:         cloud_type cloud = cloud_picker.pick(condenser_clouds, pow, CLOUD_NONE);
915:
916:         // Reroll misery clouds until we get something our god is okay with
917:         while (is_good_god(you.religion) && cloud == CLOUD_MISERY)
918:             cloud = cloud_picker.pick(condenser_clouds, pow, CLOUD_NONE);
919:
```

F-07 stable
```cpp
1044:                 found = true;
1045:                 break;
1046:             }
1047:         }
1048:         if (!found)
1049:         {
1050:             mprf(MSGCH_DURATION, T_("As the last of your armour is driven back to you, your cacophony ends."));
1051:             you.duration[DUR_CACOPHONY] = 0;
1052:         }
1053:         else if (_decrement_a_duration(DUR_CACOPHONY, delay,
1054:                 T_("Your cacophony subsides and your armour settles down once more.")))
1055:         {
1056:             for (monster_iterator mi; mi; ++mi)
1057:                 if (mi->was_created_by(MON_SUMM_CACOPHONY))
1058:                     monster_die(**mi, KILL_RESET, NON_MONSTER, true);
1059:         }
1060:         else
1061:             noisy(20, you.pos());
1062:     }
1063:
1064:     if (you.duration[DUR_FUSILLADE] && you.time_taken > 0)
1065:         fire_fusillade();
1066:
1067:     if (you.duration[DUR_CELEBRANT_COOLDOWN] && you.hp == you.hp_max)
1068:     {
1069:         mprf(MSGCH_DURATION, T_("You are ready to perform a blood rite again."));
1070:         you.duration[DUR_CELEBRANT_COOLDOWN] = 0;
1071:     }
1072:
1073:     if (you.duration[DUR_TIME_WARPED_BLOOD_COOLDOWN] && you.hp == you.hp_max)
1074:     {
1075:         // Don't print it the message if the mutation is lost
1076:         // before the cooldown wears off.
1077:         if (you.get_mutation_level(MUT_TIME_WARPED_BLOOD))
1078:             mprf(MSGCH_DURATION, T_("Your time-warped blood is ready to ripple again."));
1079:
1080:         you.duration[DUR_TIME_WARPED_BLOOD_COOLDOWN] = 0;
1081:     }
1082:
1083:     if (you.duration[DUR_HIVE_COOLDOWN] && you.hp == you.hp_max)
1084:     {
1085:         mprf(MSGCH_DURATION, T_("The buzzing within you returns to its normal rhythm."));
1086:         you.duration[DUR_HIVE_COOLDOWN] = 0;
1087:     }
1088:
1089:     if (you.duration[DUR_MEDUSA_COOLDOWN] && you.hp == you.hp_max)
1090:     {
1091:         mprf(MSGCH_DURATION, T_("You feel your defenses recover."));
1092:         you.duration[DUR_MEDUSA_COOLDOWN] = 0;
1093:     }
1094:
```

F-07 trunk
```cpp
1153:         }
1154:         if (!found)
1155:         {
1156:             mprf(MSGCH_DURATION, T_("As the last of your armour is driven back to you, your cacophony ends."));
1157:             you.duration[DUR_CACOPHONY] = 0;
1158:         }
1159:         else if (_decrement_a_duration(DUR_CACOPHONY, delay,
1160:                 T_("Your cacophony subsides and your armour settles down once more.")))
1161:         {
1162:             for (monster_iterator mi; mi; ++mi)
1163:                 if (mi->was_created_by(MON_SUMM_CACOPHONY))
1164:                     monster_die(**mi, KILL_RESET, NON_MONSTER, true);
1165:         }
1166:         else
1167:             noisy(20, you.pos());
1168:     }
1169:
1170:     if (you.duration[DUR_FUSILLADE] && you.time_taken > 0)
1171:         fire_fusillade();
1172:
1173:     if (you.duration[DUR_PLINKING] && you.time_taken > 0)
1174:         do_plinking_effect();
1175:
1176:     if (you.duration[DUR_CELEBRANT_COOLDOWN] && you.hp == you.hp_max)
1177:     {
1178:         mprf(MSGCH_DURATION, T_("You are ready to perform a blood rite again."));
1179:         you.duration[DUR_CELEBRANT_COOLDOWN] = 0;
1180:     }
1181:
1182:     if (you.duration[DUR_TIME_WARPED_BLOOD_COOLDOWN] && you.hp == you.hp_max)
1183:     {
1184:         // Don't print it the message if the mutation is lost
1185:         // before the cooldown wears off.
1186:         if (you.get_mutation_level(MUT_TIME_WARPED_BLOOD))
1187:             mprf(MSGCH_DURATION, T_("Your time-warped blood is ready to ripple again."));
1188:
1189:         you.duration[DUR_TIME_WARPED_BLOOD_COOLDOWN] = 0;
1190:     }
1191:
1192:     if (you.duration[DUR_HIVE_COOLDOWN] && you.hp == you.hp_max)
1193:     {
1194:         mprf(MSGCH_DURATION, T_("The buzzing within you returns to its normal rhythm."));
1195:         you.duration[DUR_HIVE_COOLDOWN] = 0;
1196:     }
1197:
1198:     if (you.duration[DUR_MEDUSA_COOLDOWN] && you.hp == you.hp_max)
1199:     {
1200:         mprf(MSGCH_DURATION, T_("You feel your defences recover."));
1201:         you.duration[DUR_MEDUSA_COOLDOWN] = 0;
1202:     }
1203:
```

F-08 stable
```cpp
4143:     if (!you.has_mutation(MUT_HP_CASTING))
4144:         flush_mp();
4145: }
4146:
4147: bool enough_hp(int minimum, bool suppress_msg, bool abort_macros)
4148: {
4149:     ASSERT(!crawl_state.game_is_arena());
4150:
4151:     if (you.duration[DUR_DEATHS_DOOR])
4152:     {
4153:         if (!suppress_msg)
4154:             mpr(T_("You are functionally dead and cannot pay life."));
4155:
4156:         if (abort_macros)
4157:         {
4158:             crawl_state.cancel_cmd_again();
4159:             crawl_state.cancel_cmd_repeat();
4160:         }
4161:         return false;
4162:     }
4163:
4164:     // We want to at least keep 1 HP. -- bwr
4165:     if (you.hp < minimum + 1)
4166:     {
4167:         if (!suppress_msg)
4168:             mpr(T_("You don't have enough health right now."));
4169:
4170:         if (abort_macros)
4171:         {
4172:             crawl_state.cancel_cmd_again();
4173:             crawl_state.cancel_cmd_repeat();
4174:         }
4175:         return false;
4176:     }
4177:
4178:     return true;
4179: }
4180:
4181: bool enough_mp(int minimum, bool suppress_msg, bool abort_macros)
4182: {
4183:     ASSERT(!crawl_state.game_is_arena());
4184:
4185:     if (you.has_mutation(MUT_HP_CASTING))
4186:         return enough_hp(minimum, suppress_msg, abort_macros);
4187:
4188:     if (you.magic_points < minimum)
4189:     {
4190:         if (!suppress_msg)
4191:         {
4192:             if (get_real_mp(true) < minimum)
4193:                 mpr(T_("You don't have enough magic capacity right now."));
```

F-08 trunk
```cpp
4354:     if (!you.has_mutation(MUT_HP_CASTING))
4355:         flush_mp();
4356: }
4357:
4358: bool enough_hp(int minimum, bool suppress_msg, bool abort_macros)
4359: {
4360:     ASSERT(!crawl_state.game_is_arena());
4361:
4362:     if (you.duration[DUR_DEATHS_DOOR])
4363:     {
4364:         if (!suppress_msg)
4365:             mpr(T_("You are functionally dead and cannot pay life."));
4366:
4367:         if (abort_macros)
4368:         {
4369:             crawl_state.cancel_cmd_again();
4370:             crawl_state.cancel_cmd_repeat();
4371:         }
4372:         return false;
4373:     }
4374:
4375:     // We want to at least keep 1 HP. -- bwr
4376:     if (you.hp < minimum + 1)
4377:     {
4378:         if (!suppress_msg)
4379:             mpr(T_("You don't have enough health right now."));
4380:
4381:         if (abort_macros)
4382:         {
4383:             crawl_state.cancel_cmd_again();
4384:             crawl_state.cancel_cmd_repeat();
4385:         }
4386:         return false;
4387:     }
4388:
4389:     return true;
4390: }
4391:
4392: bool enough_mp(int minimum, bool suppress_msg, bool abort_macros)
4393: {
4394:     ASSERT(!crawl_state.game_is_arena());
4395:
4396:     if (you.has_mutation(MUT_HP_CASTING))
4397:         return enough_hp(minimum, suppress_msg, abort_macros);
4398:
4399:     if (you.magic_points < minimum)
4400:     {
4401:         if (!suppress_msg)
4402:         {
4403:             if (get_real_mp(true) < minimum)
4404:                 mpr(T_("You don't have enough magic capacity right now."));
```

D-04 stable
```cpp
267:     // While some mutant beasts can fly, the game still refuses to place them
268:     // on top of water (since they can't fly until facets are fully generated).
269:     if (!player_summon_check(MONS_MUTANT_BEAST))
270:         return false;
271:
272:     mpr(T_("You open the lid..."));
273:
274:     // two rolls to reduce std deviation - +-6 so can get < max even at 27 sk
275:     int rnd_factor = random2(7);
276:     rnd_factor -= random2(7);
277:     const int hd_min = min(27, you.skill(SK_EVOCATIONS) + rnd_factor);
278:     const int tier = mutant_beast_tier(hd_min);
279:     ASSERT(tier < NUM_BEAST_TIERS);
280:
281:     mgen_data mg(MONS_MUTANT_BEAST, BEH_FRIENDLY, you.pos(), MHITYOU,
282:                  MG_AUTOFOE);
283:     mg.set_summoned(&you, 0, summ_dur(3 + random2(3)));
284:
285:     mg.hd = beast_tiers[tier];
286:     dprf("hd %d (min %d, tier %d)", mg.hd, hd_min, tier);
287:     const monster* mons = create_monster(mg);
288:
289:     if (!mons)
290:     {
291:         // Failed to create monster for some reason
292:         mpr(T_("...but nothing happens."));
293:         return true;
294:     }
295:
296:     // T_() handles language-dependent verb fragments (flies/飞 vs leaps/跳)
297:     const char* verb = mons->airborne() ? T_("flies") : T_("leaps");
298:     mprf(T_("...and %s %s out!"),
299:          mons->name(DESC_A).c_str(), verb);
300:     did_god_conduct(DID_CHAOS, random_range(5,10));
301:
302:     return true;
303: }
304:
305: // Generate webs on hostile monsters and trap them.
306: static bool _place_webs()
307: {
308:     bool webbed = false;
309:     const int evo_skill = you.skill(SK_EVOCATIONS);
310:     // At 0 evo skill, this is about a 1/3 chance of webbing each
311:     // enemy. At 27 skill, it's about an 9/10 chance.
312:     const int web_chance = 36 + evo_skill * 2;
313:     const int max_range = LOS_DEFAULT_RANGE / 2 + 2;
314:     for (monster_near_iterator mi(you.pos(), LOS_SOLID); mi; ++mi)
315:     {
316:         trap_def *trap = trap_at((*mi)->pos());
317:         // Don't destroy non-web traps or try to trap monsters
```

D-04 trunk
```cpp
267:     // While some mutant beasts can fly, the game still refuses to place them
268:     // on top of water (since they can't fly until facets are fully generated).
269:     if (!player_summon_check(MONS_MUTANT_BEAST))
270:         return false;
271:
272:     mpr(T_("You open the lid..."));
273:
274:     // two rolls to reduce std deviation - +-6 so can get < max even at 27 sk
275:     int rnd_factor = random2(7);
276:     rnd_factor -= random2(7);
277:     const int hd_min = min(27, you.skill(SK_EVOCATIONS) + rnd_factor);
278:     const int tier = mutant_beast_tier(hd_min);
279:     ASSERT(tier < NUM_BEAST_TIERS);
280:
281:     mgen_data mg(MONS_MUTANT_BEAST, BEH_FRIENDLY, you.pos(), MHITYOU,
282:                  MG_AUTOFOE);
283:     mg.set_summoned(&you, 0, summ_dur(3 + random2(3)));
284:
285:     mg.hd = beast_tiers[tier];
286:     dprf("hd %d (min %d, tier %d)", mg.hd, hd_min, tier);
287:     const monster* mons = create_monster(mg);
288:
289:     if (!mons)
290:     {
291:         // Failed to create monster for some reason
292:         mpr(T_("...but nothing happens."));
293:         return true;
294:     }
295:
296:     // T_() handles language-dependent verb fragments (flies/飞 vs leaps/跳)
297:     const string verb = mons->airborne() ? T_("flies") : T_("leaps");
298:     mprf(T_("...and %s %s out!"),
299:          mons->name(DESC_A).c_str(), verb.c_str());
300:
301:     return true;
302: }
303:
304: // Generate webs on hostile monsters and trap them.
305: static bool _place_webs()
306: {
307:     bool webbed = false;
308:     const int evo_skill = you.skill(SK_EVOCATIONS);
309:     // At 0 evo skill, this is about a 1/3 chance of webbing each
310:     // enemy. At 27 skill, it's about an 9/10 chance.
311:     const int web_chance = 36 + evo_skill * 2;
312:     const int max_range = LOS_DEFAULT_RANGE / 2 + 2;
313:     for (monster_near_iterator mi(you.pos(), LOS_SOLID); mi; ++mi)
314:     {
315:         if (you.pos().distance_from((*mi)->pos()) > max_range
316:             || (*mi)->friendly()
317:             || (*mi)->caught())
```

D-08 stable
```cpp
1182:                 if (!evoker_charges(item.sub_type))
1183:                     mpr(T_("The lightning rod overheats!"));
1184:             }
1185:             else
1186:                 return false;
1187:             break;
1188:
1189:         case MISC_QUAD_DAMAGE:
1190:             mpr(T_("QUAD DAMAGE!"));
1191:             you.duration[DUR_QUAD_DAMAGE] = 30 * BASELINE_DELAY;
1192:             ASSERT(in_inventory(item));
1193:             dec_inv_item_quantity(item.link, 1);
1194:             invalidate_agrid(true);
1195:             break;
1196:
1197:         case MISC_PHANTOM_MIRROR:
1198:             switch (_phantom_mirror(preselect))
1199:             {
1200:                 default:
1201:                 case spret::abort:
1202:                     return false;
1203:
1204:                 case spret::success:
1205:                     expend_xp_evoker(item.sub_type);
1206:                     if (!evoker_charges(item.sub_type))
1207:                         mpr(T_("The mirror clouds!"));
1208:                     // deliberate fall-through
1209:                 case spret::fail:
1210:                     practise_evoking(1);
1211:                     break;
1212:             }
1213:             break;
1214:
1215:         case MISC_ZIGGURAT:
1216:             // Don't set did_work to false, _make_zig handles the message.
1217:             unevokable = !_make_zig(item);
1218:             break;
1219:
1220:         case MISC_TIN_OF_TREMORSTONES:
1221:             switch (_tremorstone())
1222:             {
1223:                 default:
1224:                 case spret::abort:
1225:                     return false;
1226:
1227:                 case spret::success:
1228:                     expend_xp_evoker(item.sub_type);
1229:                     if (!evoker_charges(item.sub_type))
1230:                         mpr(T_("The tin is emptied!"));
1231:                 case spret::fail:
1232:                     practise_evoking(1);
```

D-08 trunk
```cpp
1229:                 if (!evoker_charges(item.sub_type))
1230:                     mpr(T_("The lightning rod overheats!"));
1231:             }
1232:             else
1233:                 return false;
1234:             break;
1235:
1236:         case MISC_QUAD_DAMAGE:
1237:             mpr(T_("QUAD DAMAGE!"));
1238:             you.duration[DUR_QUAD_DAMAGE] = 30 * BASELINE_DELAY;
1239:             ASSERT(in_inventory(item));
1240:             dec_inv_item_quantity(item.link, 1);
1241:             invalidate_agrid();
1242:             break;
1243:
1244:         case MISC_PHANTOM_MIRROR:
1245:             switch (_phantom_mirror(preselect))
1246:             {
1247:                 default:
1248:                 case spret::abort:
1249:                     return false;
1250:
1251:                 case spret::success:
1252:                     expend_xp_evoker(item.sub_type);
1253:                     if (!evoker_charges(item.sub_type))
1254:                         mpr(T_("The mirror clouds!"));
1255:                     // deliberate fall-through
1256:                 case spret::fail:
1257:                     practise_evoking(1);
1258:                     break;
1259:             }
1260:             break;
1261:
1262:         case MISC_ZIGGURAT:
1263:             // Don't set did_work to false, _make_zig handles the message.
1264:             unevokable = !_make_zig(item);
1265:             break;
1266:
1267:         case MISC_TIN_OF_TREMORSTONES:
1268:             switch (_tremorstone())
1269:             {
1270:                 default:
1271:                 case spret::abort:
1272:                     return false;
1273:
1274:                 case spret::success:
1275:                     expend_xp_evoker(item.sub_type);
1276:                     if (!evoker_charges(item.sub_type))
1277:                         mpr(T_("The tin is emptied!"));
1278:                 case spret::fail:
1279:                     practise_evoking(1);
```

C-12 stable
```cpp
1501:     if (o == NON_ITEM)
1502:         return false;
1503:     else
1504:         return env.item[o].link == NON_ITEM && env.item[o].quantity > 1;
1505: }
1506:
1507: /**
1508:  * Do the pickup command.
1509:  *
1510:  * @param partial_quantity If true, prompt for a quantity to pick up when
1511:  *                         picking up a single stack.
1512: */
1513: void pickup(bool partial_quantity)
1514: {
1515:     int keyin = 'x';
1516:
1517:     int o = you.visible_igrd(you.pos());
1518:     const int num_items = count_movable_items(o);
1519:
1520:     // Store last_pickup in case we need to restore it.
1521:     // Then clear it to fill with items picked up.
1522:     map<int,int> tmp_l_p = you.last_pickup;
1523:     you.last_pickup.clear();
1524:
1525:     if (o == NON_ITEM)
1526:         mpr(T_("There are no items here."));
1527:     else if (num_items == 1) // just one movable item?
1528:     {
1529:         // Get the link to the movable item in the pile.
1530:         while (item_is_stationary(env.item[o]))
1531:             o = env.item[o].link;
1532:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1533:     }
1534:     else if (Options.pickup_menu_limit
1535:              && num_items > (Options.pickup_menu_limit > 0
1536:                              ? Options.pickup_menu_limit
1537:                              : Options.item_stack_summary_minimum - 1))
1538:     {
1539:         pickup_menu(o);
1540:     }
1541:     else
1542:     {
1543:         int next;
1544:         if (num_items == 0)
1545:             mpr(T_("There are no objects that can be picked up here."));
1546:         else
1547:             mpr(T_("There are several objects here."));
1548:         string pickup_warning;
1549:         bool any_selectable = false;
1550:         while (o != NON_ITEM)
1551:         {
```

C-12 trunk
```cpp
1467:     if (o == NON_ITEM)
1468:         return false;
1469:     else
1470:         return env.item[o].link == NON_ITEM && env.item[o].quantity > 1;
1471: }
1472:
1473: /**
1474:  * Do the pickup command.
1475:  *
1476:  * @param partial_quantity If true, prompt for a quantity to pick up when
1477:  *                         picking up a single stack.
1478: */
1479: void pickup(bool partial_quantity)
1480: {
1481:     int keyin = 'x';
1482:
1483:     int o = you.visible_igrd(you.pos());
1484:     const int num_items = count_movable_items(o);
1485:
1486:     // Store last_pickup in case we need to restore it.
1487:     // Then clear it to fill with items picked up.
1488:     map<int,int> tmp_l_p = you.last_pickup;
1489:     you.last_pickup.clear();
1490:
1491:     if (o == NON_ITEM)
1492:         mpr(T_("There are no items here."));
1493:     else if (num_items == 1) // just one movable item?
1494:     {
1495:         // Get the link to the movable item in the pile.
1496:         while (item_is_stationary(env.item[o]))
1497:             o = env.item[o].link;
1498:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1499:     }
1500:     else if (Options.pickup_menu_limit
1501:              && num_items > (Options.pickup_menu_limit > 0
1502:                              ? Options.pickup_menu_limit
1503:                              : Options.item_stack_summary_minimum - 1))
1504:     {
1505:         pickup_menu(o);
1506:     }
1507:     else
1508:     {
1509:         int next;
1510:         if (num_items == 0)
1511:             mpr(T_("There are no objects that can be picked up here."));
1512:         else
1513:             mpr(T_("There are several objects here."));
1514:         string pickup_warning;
1515:         bool any_selectable = false;
1516:         while (o != NON_ITEM)
1517:         {
```

A-10 stable
```cpp
742:
743: level_id level_above()
744: {
745:     if (crawl_state.game_is_sprint())
746:         return level_id();
747:     // can't re-enter old zig floors; they get regenerated
748:     if (player_in_branch(BRANCH_ZIGGURAT))
749:         return level_id();
750:     if (you.depth > 1)
751:         return level_id(you.where_are_you, you.depth - 1);
752:     if (!is_connected_branch(you.where_are_you))
753:         return level_id(); // no rocketing out of the abyss, portals, pan...
754:     const level_id entry = brentry[you.where_are_you];
755:     if (entry.is_valid())
756:         return entry;
757:     return level_id();
758: }
759:
760: void rise_through_ceiling()
761: {
762:     const level_id whither = level_above();
763:     if (you.where_are_you == BRANCH_DUNGEON
764:         && you.depth == 1
765:         && player_has_orb())
766:     {
767:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
768:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
769:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
770:     }
771:     if (!whither.is_valid())
772:     {
773:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
774:         return;
775:     }
776:
777:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
778:     untag_followers(); // XXX: is this needed?
779:     stop_delay(true);
780:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
781:                      whither, true, true, false, false);
782:
783:     // flavour! blow a hole through the floor
784:     if (env.grid(you.pos()) == DNGN_FLOOR
785:         && !trap_at(you.pos()) /*needed?*/
786:         && is_valid_shaft_level())
787:     {
788:         place_specific_trap(you.pos(), TRAP_SHAFT);
789:     }
790: }
791:
792: /**
```

A-10 stable
```cpp
748:     if (player_in_branch(BRANCH_ZIGGURAT))
749:         return level_id();
750:     if (you.depth > 1)
751:         return level_id(you.where_are_you, you.depth - 1);
752:     if (!is_connected_branch(you.where_are_you))
753:         return level_id(); // no rocketing out of the abyss, portals, pan...
754:     const level_id entry = brentry[you.where_are_you];
755:     if (entry.is_valid())
756:         return entry;
757:     return level_id();
758: }
759:
760: void rise_through_ceiling()
761: {
762:     const level_id whither = level_above();
763:     if (you.where_are_you == BRANCH_DUNGEON
764:         && you.depth == 1
765:         && player_has_orb())
766:     {
767:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
768:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
769:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
770:     }
771:     if (!whither.is_valid())
772:     {
773:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
774:         return;
775:     }
776:
777:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
778:     untag_followers(); // XXX: is this needed?
779:     stop_delay(true);
780:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
781:                      whither, true, true, false, false);
782:
783:     // flavour! blow a hole through the floor
784:     if (env.grid(you.pos()) == DNGN_FLOOR
785:         && !trap_at(you.pos()) /*needed?*/
786:         && is_valid_shaft_level())
787:     {
788:         place_specific_trap(you.pos(), TRAP_SHAFT);
789:     }
790: }
791:
792: /**
793:  * Transition to a different level.
794:  *
795:  * @param how The type of stair/portal tile the player is being conveyed through
796:  * @param whence The tile the player was on at the beginning of the transition
797:  *               (likely the same as how, unless forced is true)
798:  * @param whither The destination level
```

A-10 stable
```cpp
752:     if (!is_connected_branch(you.where_are_you))
753:         return level_id(); // no rocketing out of the abyss, portals, pan...
754:     const level_id entry = brentry[you.where_are_you];
755:     if (entry.is_valid())
756:         return entry;
757:     return level_id();
758: }
759:
760: void rise_through_ceiling()
761: {
762:     const level_id whither = level_above();
763:     if (you.where_are_you == BRANCH_DUNGEON
764:         && you.depth == 1
765:         && player_has_orb())
766:     {
767:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
768:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
769:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
770:     }
771:     if (!whither.is_valid())
772:     {
773:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
774:         return;
775:     }
776:
777:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
778:     untag_followers(); // XXX: is this needed?
779:     stop_delay(true);
780:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
781:                      whither, true, true, false, false);
782:
783:     // flavour! blow a hole through the floor
784:     if (env.grid(you.pos()) == DNGN_FLOOR
785:         && !trap_at(you.pos()) /*needed?*/
786:         && is_valid_shaft_level())
787:     {
788:         place_specific_trap(you.pos(), TRAP_SHAFT);
789:     }
790: }
791:
792: /**
793:  * Transition to a different level.
794:  *
795:  * @param how The type of stair/portal tile the player is being conveyed through
796:  * @param whence The tile the player was on at the beginning of the transition
797:  *               (likely the same as how, unless forced is true)
798:  * @param whither The destination level
799:  * @param shaft Is the player going down a shaft?
800:  */
801: void floor_transition(dungeon_feature_type how,
802:                       const dungeon_feature_type whence, level_id whither,
```

A-10 trunk
```cpp
758:
759: level_id level_above()
760: {
761:     if (crawl_state.game_is_sprint())
762:         return level_id();
763:     // can't re-enter old zig floors; they get regenerated
764:     if (player_in_branch(BRANCH_ZIGGURAT))
765:         return level_id();
766:     if (you.depth > 1)
767:         return level_id(you.where_are_you, you.depth - 1);
768:     if (!is_connected_branch(you.where_are_you))
769:         return level_id(); // no rocketing out of the abyss, portals, pan...
770:     const level_id entry = brentry[you.where_are_you];
771:     if (entry.is_valid())
772:         return entry;
773:     return level_id();
774: }
775:
776: void rise_through_ceiling()
777: {
778:     const level_id whither = level_above();
779:     if (you.where_are_you == BRANCH_DUNGEON
780:         && you.depth == 1
781:         && player_has_orb())
782:     {
783:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
784:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
785:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
786:     }
787:     if (!whither.is_valid())
788:     {
789:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
790:         return;
791:     }
792:
793:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
794:     untag_followers(); // XXX: is this needed?
795:     stop_delay(true);
796:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
797:                      whither, true, true, false, false);
798:
799:     // flavour! blow a hole through the floor
800:     if (env.grid(you.pos()) == DNGN_FLOOR && is_valid_shaft_level())
801:         dungeon_terrain_changed(you.pos(), DNGN_TRAP_SHAFT);
802: }
803:
804: /**
805:  * Transition to a different level.
806:  *
807:  * @param how The type of stair/portal tile the player is being conveyed through
808:  * @param whence The tile the player was on at the beginning of the transition
```

A-10 trunk
```cpp
764:     if (player_in_branch(BRANCH_ZIGGURAT))
765:         return level_id();
766:     if (you.depth > 1)
767:         return level_id(you.where_are_you, you.depth - 1);
768:     if (!is_connected_branch(you.where_are_you))
769:         return level_id(); // no rocketing out of the abyss, portals, pan...
770:     const level_id entry = brentry[you.where_are_you];
771:     if (entry.is_valid())
772:         return entry;
773:     return level_id();
774: }
775:
776: void rise_through_ceiling()
777: {
778:     const level_id whither = level_above();
779:     if (you.where_are_you == BRANCH_DUNGEON
780:         && you.depth == 1
781:         && player_has_orb())
782:     {
783:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
784:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
785:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
786:     }
787:     if (!whither.is_valid())
788:     {
789:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
790:         return;
791:     }
792:
793:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
794:     untag_followers(); // XXX: is this needed?
795:     stop_delay(true);
796:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
797:                      whither, true, true, false, false);
798:
799:     // flavour! blow a hole through the floor
800:     if (env.grid(you.pos()) == DNGN_FLOOR && is_valid_shaft_level())
801:         dungeon_terrain_changed(you.pos(), DNGN_TRAP_SHAFT);
802: }
803:
804: /**
805:  * Transition to a different level.
806:  *
807:  * @param how The type of stair/portal tile the player is being conveyed through
808:  * @param whence The tile the player was on at the beginning of the transition
809:  *               (likely the same as how, unless forced is true)
810:  * @param whither The destination level
811:  * @param shaft Is the player going down a shaft?
812:  */
813: void floor_transition(dungeon_feature_type how,
814:                       const dungeon_feature_type whence, level_id whither,
```

A-10 trunk
```cpp
768:     if (!is_connected_branch(you.where_are_you))
769:         return level_id(); // no rocketing out of the abyss, portals, pan...
770:     const level_id entry = brentry[you.where_are_you];
771:     if (entry.is_valid())
772:         return entry;
773:     return level_id();
774: }
775:
776: void rise_through_ceiling()
777: {
778:     const level_id whither = level_above();
779:     if (you.where_are_you == BRANCH_DUNGEON
780:         && you.depth == 1
781:         && player_has_orb())
782:     {
783:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
784:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
785:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
786:     }
787:     if (!whither.is_valid())
788:     {
789:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
790:         return;
791:     }
792:
793:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
794:     untag_followers(); // XXX: is this needed?
795:     stop_delay(true);
796:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
797:                      whither, true, true, false, false);
798:
799:     // flavour! blow a hole through the floor
800:     if (env.grid(you.pos()) == DNGN_FLOOR && is_valid_shaft_level())
801:         dungeon_terrain_changed(you.pos(), DNGN_TRAP_SHAFT);
802: }
803:
804: /**
805:  * Transition to a different level.
806:  *
807:  * @param how The type of stair/portal tile the player is being conveyed through
808:  * @param whence The tile the player was on at the beginning of the transition
809:  *               (likely the same as how, unless forced is true)
810:  * @param whither The destination level
811:  * @param shaft Is the player going down a shaft?
812:  */
813: void floor_transition(dungeon_feature_type how,
814:                       const dungeon_feature_type whence, level_id whither,
815:                       bool forced, bool going_up, bool shaft,
816:                       bool update_travel_cache)
817: {
818:     const level_id old_level = level_id::current();
```

D-HERE-01 trunk
```cpp
1159:         if (flying)
1160:             description << wings << " ";
1161:
1162:         description << "and " << head << ".";
1163:     }
1164:
1165:     if (!hash_with_seed(5, seed, 4) && you.can_smell()) // 20%
1166:     {
1167:         const string smell = T_(HRANDOM_ELEMENT(smell_descs, 5));
1168:         description << smell;
1169:     }
1170:
1171:     if (hash_with_seed(2, seed, 6)) // 50%
1172:     {
1173:         const string misc = T_(HRANDOM_ELEMENT(misc_descs, 6));
1174:         description << misc;
1175:     }
1176:
1177:     if (colour == ETC_RANDOM)
1178:         description << T_(" It changes colour whenever you look at it.");
1179:
1180:     if (!descriptor.empty())
1181:         description << T_("\n\nIt seems like it would really prefer not to be here right now.");
1182:
1183:     return description.str();
1184: }
1185:
1186: /**
1187:  * Describe a given mutant beast's tier.
1188:  *
1189:  * @param tier      The mutant_beast_tier of the beast in question.
1190:  * @return          A string describing the tier; e.g.
1191:  *              "It is a juvenile, out of the larval stage but still below its
1192:  *              mature strength."
1193:  */
1194: static string _describe_mutant_beast_tier(int tier)
1195: {
1196:     const string tier_descs[] = {
1197:         T_("It is of an unusually buggy age."),
1198:         T_("It is larval and weak, freshly emerged from its mother's pouch."),
1199:         T_("It is a juvenile, no longer larval but below its mature strength."),
1200:         T_("It is mature, stronger than a juvenile but weaker than its elders."),
1201:         T_("It is an elder, stronger than mature beasts."),
1202:         T_("It is a primal beast, the most powerful of its kind."),
1203:     };
```

D-HERE-13 stable
```cpp
3613:             long_desc += T_(" However, this will not work until the sealing runes wear off.");
3614:     }
3615:
3616:     // mention that diggable walls are
3617:     if (feat_is_diggable(feat) && in_bounds(pos)
3618:         && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
3619:     {
3620:         long_desc += T_("\nIt can be dug through.");
3621:     }
3622:
3623:     // Mention things which don't stop LOS_NO_TRANS or reaching weapons,
3624:     // but block movement.
3625:     if (feat_is_solid(feat) && !feat_is_opaque(feat) && !feat_is_wall(feat)
3626:         && !feat_is_closed_door(feat) && !feat_is_endless(feat))
3627:     {
3628:         if (feat_is_reachable_past(feat))
3629:             long_desc += T_("\nA suitable weapon or spell can reach past it.");
3630:         else
3631:             long_desc += T_("\nSome spells can be cast through it.");
3632:     }
3633:
3634:     if (pos == you.pos() && you.on_current_level)
3635:         long_desc += T_("\nYou are here.");
3636:
3637:     inf.body << long_desc;
3638:
3639:     if (include_extra)
3640:     {
3641:         const auto extra_descs = _get_feature_extra_descs(pos);
3642:         for (const auto &d : extra_descs)
3643:             inf.body << (d.title == extra_descs.back().title ? "" : "\n") << d.description;
3644:     }
3645:
3646:     inf.quote = getQuoteString(db_name);
3647: }
3648:
3649: static bool _do_feat_action(const coord_def &pos, const command_type action)
3650: {
3651:     if (action == CMD_NO_CMD)
3652:         return true;
3653:
3654:     switch (action)
3655:     {
3656:     case CMD_GO_UPSTAIRS:
3657:     case CMD_GO_DOWNSTAIRS:
```

D-HERE-13 trunk
```cpp
3935:             long_desc += T_(" However, this will not work until the sealing runes wear off.");
3936:     }
3937:
3938:     // mention that diggable walls are
3939:     if (feat_is_diggable(feat) && in_bounds(pos)
3940:         && env.markers.property_at(pos, MAT_ANY, "veto_destroy") != "veto")
3941:     {
3942:         long_desc += T_("\nIt can be dug through.");
3943:     }
3944:
3945:     // Mention things which don't stop LOS_NO_TRANS or reaching weapons,
3946:     // but block movement.
3947:     if (feat_is_solid(feat) && !feat_is_opaque(feat) && !feat_is_wall(feat)
3948:         && !feat_is_closed_door(feat) && !feat_is_endless(feat))
3949:     {
3950:         if (feat_is_reachable_past(feat))
3951:             long_desc += T_("\nA suitable weapon or spell can reach past it.");
3952:         else
3953:             long_desc += T_("\nSome spells can be cast through it.");
3954:     }
3955:
3956:     if (pos == you.pos() && you.on_current_level)
3957:         long_desc += T_("\nYou are here.");
3958:
3959:     inf.body << long_desc;
3960:
3961:     if (include_extra)
3962:     {
3963:         const auto extra_descs = _get_feature_extra_descs(pos);
3964:         for (const auto &d : extra_descs)
3965:             inf.body << (d.title == extra_descs.back().title ? "" : "\n") << d.description;
3966:     }
3967:
3968:     inf.quote = getQuoteString(db_name);
3969: }
3970:
3971: static bool _do_feat_action(const coord_def &pos, const command_type action)
3972: {
3973:     if (action == CMD_NO_CMD)
3974:         return true;
3975:
3976:     switch (action)
3977:     {
3978:     case CMD_GO_UPSTAIRS:
3979:     case CMD_GO_DOWNSTAIRS:
```

D-HERE-14 stable
```cpp
468:     {
469:         // This thing seems to be starting off 1 line above where it
470:         // should be. -cao
471:         nextline();
472:     }
473:     int width() { return crawl_view.msgsz.x; }
474:     int height() { return crawl_view.msgsz.y; }
475:     void print(const string &str) { cprintf("%s", str.c_str()); }
476:     void nextline() { cgotoxy(1, wherey() + 1); }
477: };
478:
479: class FullViewInvEntry : public InvEntry
480: {
481: public:
482:     FullViewInvEntry(const item_def &i)
483:         : InvEntry(i)
484:     { }
485:
486:     string get_text() const override
487:     {
488:         const string t = MenuEntry::get_text();
489:         if (item && item->pos == you.pos())
490:             return t + T_(" (here)");
491:         return t;
492:     }
493: };
494:
495: namespace
496: {
497:     // XX this probably shouldn't use InvMenu, why does it?
498:     class DescMenu : public InvMenu
499:     {
500:     public:
501:         DescMenu()
502:             : InvMenu(MF_SINGLESELECT | MF_ANYPRINTABLE
503:                             | MF_ALLOW_FORMATTING
504:                             | MF_INIT_HOVER)
505:         { }
506:
507:         // TODO: move more stuff into this class
508:         bool skip_process_command(int) override
509:         {
510:             // override InvMenu behavior
511:             return false;
512:         }
```

D-HERE-14 trunk
```cpp
449:     {
450:         // This thing seems to be starting off 1 line above where it
451:         // should be. -cao
452:         nextline();
453:     }
454:     int width() { return crawl_view.msgsz.x; }
455:     int height() { return crawl_view.msgsz.y; }
456:     void print(const string &str) { cprintf("%s", str.c_str()); }
457:     void nextline() { cgotoxy(1, wherey() + 1); }
458: };
459:
460: class FullViewInvEntry : public InvEntry
461: {
462: public:
463:     FullViewInvEntry(const item_def &i)
464:         : InvEntry(i)
465:     { }
466:
467:     string get_text() const override
468:     {
469:         const string t = MenuEntry::get_text();
470:         if (item && item->pos == you.pos())
471:             return t + T_(" (here)");
472:         return t;
473:     }
474: };
475:
476: namespace
477: {
478:     // XX this probably shouldn't use InvMenu, why does it?
479:     class DescMenu : public InvMenu
480:     {
481:     public:
482:         DescMenu()
483:             : InvMenu(MF_SINGLESELECT | MF_ANYPRINTABLE
484:                             | MF_ALLOW_FORMATTING
485:                             | MF_INIT_HOVER)
486:         { }
487:
488:         // TODO: move more stuff into this class
489:         bool skip_process_command(int) override
490:         {
491:             // override InvMenu behavior
492:             return false;
493:         }
```

D-HERE-15 stable
```cpp
2617:                             "of a random god, who will grant you some "
2618:                             "additional piety in thanks.");
2619:                 }
2620:                 else
2621:                 {
2622:                     ostr << T_("You can get information about <w>")
2623:                          << god_name(altar_god)
2624:                          << T_("</w> by pressing <w>></w> while standing on the "
2625:                             "altar. Before taking up the responding faith "
2626:                             "you'll be asked for confirmation.");
2627:                 }
2628:             }
2629:             else if (you_worship(altar_god))
2630:             {
2631:                 // If we don't have anything to say, return early.
2632:                 return;
2633:             }
2634:             else if (altar_god == GOD_ECUMENICAL)
2635:             {
2636:                 ostr << T_("This particular altar is so ancient that you cannot "
2637:                         "make out which god it is dedicated to, and ")
2638:                      << god_name(you.religion)
2639:                      << T_(" probably won't like it if you switch allegiance. If "
2640:                         "you want to take the risk, you can convert here by "
2641:                         "pressing <w>></w> while standing on the altar. Doing "
2642:                         "so will enter you into service of a random god, who "
2643:                         "will grant you some additional piety in thanks.");
2644:             }
2645:             else
2646:             {
2647:                 const string current_god = god_name(you.religion);
2648:                 ostr << current_god
2649:                      << T_(" probably won't like it if you switch allegiance, "
2650:                         "but having a look won't hurt: to get information "
2651:                         "on <w>");
2652:                 ostr << god_name(altar_god);
2653:                 ostr << T_("</w>, press <w>></w> while standing on the "
2654:                         "altar. Before taking up the responding faith (and "
2655:                         "abandoning your current one!) you'll be asked for "
2656:                         "confirmation."
2657:                         );
2658: #ifdef USE_TILE
2659:                 ostr << make_stringf(T_("\nTo see your current standing with %s "
2660:                                         "press <w>^</w>, or click with your <w>right "
2661:                                         "mouse button</w> on your avatar while "
2662:                                         "pressing <w>Shift</w>."), current_god.c_str());
2663: #else
2664:                 ostr << make_stringf(T_("\nTo see your current standing with %s "
2665:                                         "press <w>^</w>."), current_god.c_str());
```

D-HERE-17 stable
```cpp
1943: #endif
1944:
1945:     mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
1946: }
1947:
1948: // Get a brief of monster, items, and features in a given cell.
1949: string get_square_desc(const coord_def &pos)
1950: {
1951:     ostringstream out;
1952:
1953:     string mon_desc = cell_monster_description(pos);
1954:     if (!mon_desc.empty())
1955:         out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1956:
1957:     string desc = cell_items_description(pos);
1958:     if (!desc.empty())
1959:         out << desc << "\n";
1960:
1961:     desc = cell_floor_description(pos, false);
1962:     if (!desc.empty())
1963:     {
1964:         if (mon_desc.empty())
1965:             out << T_("<cyan>Here:</cyan>") << " ";
1966:         out << desc << "\n";
1967:     }
1968:
1969:     desc = _get_cloud_desc(pos);
1970:     if (!desc.empty())
1971:         out << desc << "\n";
1972:
1973:     if (out.tellp() > 0)
1974:         out << T_("\n(Right-click to examine)");
1975:
1976:     return out.str();
1977: }
1978:
1979: void direction_chooser::reinitialize_move_flags()
1980: {
1981:     moves.isValid    = false;
1982:     moves.isTarget   = false;
1983:     moves.isCancel   = false;
1984:     moves.isEndpoint = false;
1985:     moves.choseRay   = false;
1986: }
1987:
```

D-HERE-17 trunk
```cpp
1968: #endif
1969:
1970:     mprf(MSGCH_EXAMINE_FILTER, "%s.", desc.c_str());
1971: }
1972:
1973: // Get a brief of monster, items, and features in a given cell.
1974: string get_square_desc(const coord_def &pos)
1975: {
1976:     ostringstream out;
1977:
1978:     string mon_desc = cell_monster_description(pos);
1979:     if (!mon_desc.empty())
1980:         out << make_stringf(T_("<cyan>Here:</cyan> %s\n"), mon_desc.c_str());
1981:
1982:     string desc = cell_items_description(pos);
1983:     if (!desc.empty())
1984:         out << desc << "\n";
1985:
1986:     desc = cell_floor_description(pos, false);
1987:     if (!desc.empty())
1988:     {
1989:         if (mon_desc.empty())
1990:             out << T_("<cyan>Here:</cyan>") << " ";
1991:         out << desc << "\n";
1992:     }
1993:
1994:     desc = _get_cloud_desc(pos);
1995:     if (!desc.empty())
1996:         out << desc << "\n";
1997:
1998:     if (out.tellp() > 0)
1999:         out << T_("\n(Right-click to examine)");
2000:
2001:     return out.str();
2002: }
2003:
2004: void direction_chooser::reinitialize_move_flags()
2005: {
2006:     moves.isValid    = false;
2007:     moves.isTarget   = false;
2008:     moves.isCancel   = false;
2009:     moves.isEndpoint = false;
2010:     moves.choseRay   = false;
2011: }
2012:
```

D-HERE-22 stable
```cpp
2648:            greater demon w:55 / nekomata w:5 / demonspawn warmonger w:2 / \
2649:            demonspawn soul scholar w:2 / demonspawn blood saint w:2 / \
2650:            demonspawn corrupter w:2 / any demon w:112 / nothing w:300
2651: KMONS:   YPQR = greater demon w:340 / nekomata w:20 / demonspawn soul scholar / \
2652:            demonspawn blood saint / demonspawn corrupter / demonspawn warmonger
2653: KFEAT:   _ = altar_gozag
2654: KFEAT:   P = exit_pandemonium
2655: KFEAT:   QR = transit_pandemonium
2656: KFEAT:   Y = Y
2657: SHUFFLE: Pp/Qq/Rr, S_, TU
2658: SUBST:   p = +, qr = c
2659: NSUBST:  D = + / x, E = + / x, F = + / x
2660: NSUBST:  S = H / J / K
2661: SHUFFLE: HJKLMNOS
2662: FTILE:   HJKLMNOPQRSTUYZcx-+_. = floor_limestone
2663: # This vault has a special announcement to provide a heads-up that this rune
2664: # is not obtained in the usual way. It uses yellow text to evoke Gozag's gold
2665: # related messages, as well the messages from arriving in the four unique
2666: # lords' levels.
2667: epilogue {{
2668: if not you.have_rune("demonic") then
2669:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
2670:     crawl.mpr(crawl.t_("<yellow>A demonic rune of Zot can be found here... " ..
2671:               "for a price.</yellow>"))
2672: end
2673: }}
2674: MAP
2675:         xxDxx
2676:        xx...xx
2677:        D.....D
2678:       xx.....xx
2679:   xxDxx...U...xxDxx
2680:  xx...---...---...xx
2681:  x....-_-...-S-....x
2682: xx....---...---....xx
2683: x...T...ccccc...T...x
2684: xx.....cc...cc.....xx
2685:  F.....r..P..q.....E
2686:  xx---ccY...Ycc---xx
2687:   x-S-c...Z...c-_-x
2688:  xx---ccQ...Rcc---xx
2689:  F.....c..Y..c.....E
2690: xx.....cc...cc.....xx
2691: x...U...ccpcc...U...x
2692: xx....---...---....xx
2693:  F....-_-...-S-....E
```

D-HERE-22 trunk
```cpp
2648:            greater demon w:55 / nekomata w:5 / demonspawn warmonger w:2 / \
2649:            demonspawn soul scholar w:2 / demonspawn blood saint w:2 / \
2650:            demonspawn corrupter w:2 / any demon w:112 / nothing w:300
2651: KMONS:   YPQR = greater demon w:340 / nekomata w:20 / demonspawn soul scholar / \
2652:            demonspawn blood saint / demonspawn corrupter / demonspawn warmonger
2653: KFEAT:   _ = altar_gozag
2654: KFEAT:   P = exit_pandemonium
2655: KFEAT:   QR = transit_pandemonium
2656: KFEAT:   Y = Y
2657: SHUFFLE: Pp/Qq/Rr, S_, TU
2658: SUBST:   p = +, qr = c
2659: NSUBST:  D = + / x, E = + / x, F = + / x
2660: NSUBST:  S = H / J / K
2661: SHUFFLE: HJKLMNOS
2662: FTILE:   HJKLMNOPQRSTUYZcx-+_. = floor_limestone
2663: # This vault has a special announcement to provide a heads-up that this rune
2664: # is not obtained in the usual way. It uses yellow text to evoke Gozag's gold
2665: # related messages, as well the messages from arriving in the four unique
2666: # lords' levels.
2667: epilogue {{
2668: if not you.have_rune("demonic") then
2669:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
2670:     crawl.mpr(crawl.t_("<yellow>A demonic rune of Zot can be found here... " ..
2671:               "for a price.</yellow>"))
2672: end
2673: }}
2674: MAP
2675:         xxDxx
2676:        xx...xx
2677:        D.....D
2678:       xx.....xx
2679:   xxDxx...U...xxDxx
2680:  xx...---...---...xx
2681:  x....-_-...-S-....x
2682: xx....---...---....xx
2683: x...T...ccccc...T...x
2684: xx.....cc...cc.....xx
2685:  F.....r..P..q.....E
2686:  xx---ccY...Ycc---xx
2687:   x-S-c...Z...c-_-x
2688:  xx---ccQ...Rcc---xx
2689:  F.....c..Y..c.....E
2690: xx.....cc...cc.....xx
2691: x...U...ccpcc...U...x
2692: xx....---...---....xx
2693:  F....-_-...-S-....E
```

D-HERE-23 stable
```cpp
1524:         for (distance_iterator di(pond, true, false, 4); di && num > 0; ++di)
1525:         {
1526:             if (env.grid(*di) == DNGN_FLOOR
1527:                 && (di.radius() == 0 || _water_adjacent(*di))
1528:                 && x_chance_in_y(4, di.radius() + 3))
1529:             {
1530:                 num--;
1531:                 deep--;
1532:
1533:                 dungeon_feature_type feat = DNGN_SHALLOW_WATER;
1534:                 if (deep > 0 && *di != you.pos())
1535:                 {
1536:                     monster* mon = monster_at(*di);
1537:                     if (!mon || mon->is_habitable_feat(DNGN_DEEP_WATER))
1538:                         feat = DNGN_DEEP_WATER;
1539:                 }
1540:
1541:                 temp_change_terrain(*di, feat, duration, TERRAIN_CHANGE_FORESTED);
1542:             }
1543:         }
1544:     }
1545:
1546:     mpr(T_("A forested plane collides here with a resounding crunch!"));
1547:     noisy(spell_effect_noise(SPELL_SUMMON_FOREST), caster->pos());
1548:
1549:     mgen_data dryad_data = _pal_data(MONS_DRYAD, 1, SPELL_SUMMON_FOREST);
1550:     dryad_data.hd = 6 + div_rand_round(pow, 16);
1551:
1552:     if (monster *dryad = create_monster(dryad_data))
1553:     {
1554:         mon_enchant timer = dryad->get_ench(ENCH_SUMMON_TIMER);
1555:         timer.duration = duration - 10;
1556:         dryad->update_ench(timer);
1557:
1558:         // Pre-awaken the forest just summoned.
1559:         bolt dummy;
1560:         mons_cast(dryad, dummy, SPELL_AWAKEN_FOREST,
1561:                   dryad->spell_slot_flags(SPELL_AWAKEN_FOREST));
1562:     }
1563:
1564:     you.duration[DUR_FORESTED] = duration;
1565:
1566:     return spret::success;
1567: }
1568:
```

D-HERE-23 trunk
```cpp
1460:         for (distance_iterator di(pond, true, false, 4); di && num > 0; ++di)
1461:         {
1462:             if (env.grid(*di) == DNGN_FLOOR
1463:                 && (di.radius() == 0 || _water_adjacent(*di))
1464:                 && x_chance_in_y(4, di.radius() + 3))
1465:             {
1466:                 num--;
1467:                 deep--;
1468:
1469:                 dungeon_feature_type feat = DNGN_SHALLOW_WATER;
1470:                 if (deep > 0 && *di != you.pos())
1471:                 {
1472:                     monster* mon = monster_at(*di);
1473:                     if (!mon || mon->is_habitable_feat(DNGN_DEEP_WATER))
1474:                         feat = DNGN_DEEP_WATER;
1475:                 }
1476:
1477:                 temp_change_terrain(*di, feat, duration, TERRAIN_CHANGE_FORESTED);
1478:             }
1479:         }
1480:     }
1481:
1482:     mpr(T_("A forested plane collides here with a resounding crunch!"));
1483:     noisy(spell_effect_noise(SPELL_SUMMON_FOREST), caster->pos());
1484:
1485:     mgen_data dryad_data = _pal_data(MONS_DRYAD, 1, SPELL_SUMMON_FOREST);
1486:     dryad_data.hd = 6 + div_rand_round(pow, 16);
1487:
1488:     if (monster *dryad = create_monster(dryad_data))
1489:     {
1490:         mon_enchant timer = dryad->get_ench(ENCH_SUMMON_TIMER);
1491:         timer.duration = duration - 10;
1492:         dryad->update_ench(timer);
1493:
1494:         // Pre-awaken the forest just summoned.
1495:         bolt dummy;
1496:         mons_cast(dryad, dummy, SPELL_AWAKEN_FOREST,
1497:                   dryad->spell_slot_flags(SPELL_AWAKEN_FOREST));
1498:     }
1499:
1500:     you.duration[DUR_FORESTED] = duration;
1501:
1502:     return spret::success;
1503: }
1504:
```

D-HERE-24 stable
```cpp
2647:            mummy priest / orc high priest / orc sorcerer / dread lich / \
2648:            greater demon w:55 / nekomata w:5 / demonspawn warmonger w:2 / \
2649:            demonspawn soul scholar w:2 / demonspawn blood saint w:2 / \
2650:            demonspawn corrupter w:2 / any demon w:112 / nothing w:300
2651: KMONS:   YPQR = greater demon w:340 / nekomata w:20 / demonspawn soul scholar / \
2652:            demonspawn blood saint / demonspawn corrupter / demonspawn warmonger
2653: KFEAT:   _ = altar_gozag
2654: KFEAT:   P = exit_pandemonium
2655: KFEAT:   QR = transit_pandemonium
2656: KFEAT:   Y = Y
2657: SHUFFLE: Pp/Qq/Rr, S_, TU
2658: SUBST:   p = +, qr = c
2659: NSUBST:  D = + / x, E = + / x, F = + / x
2660: NSUBST:  S = H / J / K
2661: SHUFFLE: HJKLMNOS
2662: FTILE:   HJKLMNOPQRSTUYZcx-+_. = floor_limestone
2663: # This vault has a special announcement to provide a heads-up that this rune
2664: # is not obtained in the usual way. It uses yellow text to evoke Gozag's gold
2665: # related messages, as well the messages from arriving in the four unique
2666: # lords' levels.
2667: epilogue {{
2668: if not you.have_rune("demonic") then
2669:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
2670:     crawl.mpr(crawl.t_("<yellow>A demonic rune of Zot can be found here... " ..
2671:               "for a price.</yellow>"))
2672: end
2673: }}
2674: MAP
2675:         xxDxx
2676:        xx...xx
2677:        D.....D
2678:       xx.....xx
2679:   xxDxx...U...xxDxx
2680:  xx...---...---...xx
2681:  x....-_-...-S-....x
2682: xx....---...---....xx
2683: x...T...ccccc...T...x
2684: xx.....cc...cc.....xx
2685:  F.....r..P..q.....E
2686:  xx---ccY...Ycc---xx
2687:   x-S-c...Z...c-_-x
2688:  xx---ccQ...Rcc---xx
2689:  F.....c..Y..c.....E
2690: xx.....cc...cc.....xx
2691: x...U...ccpcc...U...x
```

D-HERE-24 stable
```cpp
265:     if e.is_validating() then return end
266:     if crawl.x_chance_in_y(you.depth() + 3, you.depth() + 5) then
267:         e.tags("luniq_hellpanabyss_threat_entry")
268:         e.kmons(glyph .. "1 = " .. tiertwo)
269:         e.kmons("2 = " .. tierthree)
270:         e.nsubst("2 = 2 = 22. / *:.")
271:         e.nsubst("1 = 1:1 / *:.")
272:     else
273:         e.subst("12 = .")
274:         e.kmons(glyph .. " = " .. tiertwo .. " / " ..
275:                 tierthree .. " / " .. tierthree)
276:     end
277:
278:     e.ftile(".+12O$ : floor_demonic_red / floor_demonic_blue / " ..
279:                      "floor_demonic_green / floor_demonic_magenta")
280: end
281:
282: function pan_declare_demonic_rune(holy)
283:   if holy then
284:     crawl.mpr(crawl.t_("The tension of great conflict fills the air!"), "warning")
285:     crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))
286:   else
287:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
288:     crawl.mpr(crawl.t_("It guards the demonic rune of Zot."))
289:   end
290: end
291:
292: function pan_highlights_setup(e)
293:   -- Choose fixed demonic rune vaults.
294:   local set = { "boxes", "hellions", "pain", "frozen", "disco" }
295:   local vaultone = "_" .. util.random_from(set)
296:   local vaulttwo = vaultone
297:   while vaulttwo == vaultone do
298:      vaulttwo = "_" .. util.random_from(set)
299:   end
300:   e.hook('post_place', function ()
301:     dgn.place_maps{tag=("pan_fixed_rune" .. vaultone), count=1, die_on_error=true}
302:     dgn.place_maps{tag=("pan_fixed_lure" .. vaulttwo), count=1, die_on_error=true}
303:     dgn.place_maps{tag=("serial_pan" .. vaultone), count=3}
304:     dgn.place_maps{tag=("serial_pan" .. vaulttwo), count=3}
305:   end)
306: end
307:
308: function demonic_rune_vault_is_decoy(e)
309:   local params = dgn.map_parameters()
```

D-HERE-24 trunk
```cpp
2647:            mummy priest / orc high priest / orc sorcerer / dread lich / \
2648:            greater demon w:55 / nekomata w:5 / demonspawn warmonger w:2 / \
2649:            demonspawn soul scholar w:2 / demonspawn blood saint w:2 / \
2650:            demonspawn corrupter w:2 / any demon w:112 / nothing w:300
2651: KMONS:   YPQR = greater demon w:340 / nekomata w:20 / demonspawn soul scholar / \
2652:            demonspawn blood saint / demonspawn corrupter / demonspawn warmonger
2653: KFEAT:   _ = altar_gozag
2654: KFEAT:   P = exit_pandemonium
2655: KFEAT:   QR = transit_pandemonium
2656: KFEAT:   Y = Y
2657: SHUFFLE: Pp/Qq/Rr, S_, TU
2658: SUBST:   p = +, qr = c
2659: NSUBST:  D = + / x, E = + / x, F = + / x
2660: NSUBST:  S = H / J / K
2661: SHUFFLE: HJKLMNOS
2662: FTILE:   HJKLMNOPQRSTUYZcx-+_. = floor_limestone
2663: # This vault has a special announcement to provide a heads-up that this rune
2664: # is not obtained in the usual way. It uses yellow text to evoke Gozag's gold
2665: # related messages, as well the messages from arriving in the four unique
2666: # lords' levels.
2667: epilogue {{
2668: if not you.have_rune("demonic") then
2669:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
2670:     crawl.mpr(crawl.t_("<yellow>A demonic rune of Zot can be found here... " ..
2671:               "for a price.</yellow>"))
2672: end
2673: }}
2674: MAP
2675:         xxDxx
2676:        xx...xx
2677:        D.....D
2678:       xx.....xx
2679:   xxDxx...U...xxDxx
2680:  xx...---...---...xx
2681:  x....-_-...-S-....x
2682: xx....---...---....xx
2683: x...T...ccccc...T...x
2684: xx.....cc...cc.....xx
2685:  F.....r..P..q.....E
2686:  xx---ccY...Ycc---xx
2687:   x-S-c...Z...c-_-x
2688:  xx---ccQ...Rcc---xx
2689:  F.....c..Y..c.....E
2690: xx.....cc...cc.....xx
2691: x...U...ccpcc...U...x
```

D-HERE-24 trunk
```cpp
265:     if e.is_validating() then return end
266:     if crawl.x_chance_in_y(you.depth() + 3, you.depth() + 5) then
267:         e.tags("luniq_hellpanabyss_threat_entry")
268:         e.kmons(glyph .. "1 = " .. tiertwo)
269:         e.kmons("2 = " .. tierthree)
270:         e.nsubst("2 = 2 = 22. / *:.")
271:         e.nsubst("1 = 1:1 / *:.")
272:     else
273:         e.subst("12 = .")
274:         e.kmons(glyph .. " = " .. tiertwo .. " / " ..
275:                 tierthree .. " / " .. tierthree)
276:     end
277:
278:     e.ftile(".+12O$ : floor_demonic_red / floor_demonic_blue / " ..
279:                      "floor_demonic_green / floor_demonic_magenta")
280: end
281:
282: function pan_declare_demonic_rune(holy)
283:   if holy then
284:     crawl.mpr(crawl.t_("The tension of great conflict fills the air!"), "warning")
285:     crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))
286:   else
287:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
288:     crawl.mpr(crawl.t_("It guards the demonic rune of Zot."))
289:   end
290: end
291:
292: function pan_highlights_setup(e)
293:   -- Choose fixed demonic rune vaults.
294:   local set = { "boxes", "hellions", "pain", "frozen", "disco" }
295:   local vaultone = "_" .. util.random_from(set)
296:   local vaulttwo = vaultone
297:   while vaulttwo == vaultone do
298:      vaulttwo = "_" .. util.random_from(set)
299:   end
300:   e.hook('post_place', function ()
301:     dgn.place_maps{tag=("pan_fixed_rune" .. vaultone), count=1, die_on_error=true}
302:     dgn.place_maps{tag=("pan_fixed_lure" .. vaulttwo), count=1, die_on_error=true}
303:     dgn.place_maps{tag=("serial_pan" .. vaultone), count=3}
304:     dgn.place_maps{tag=("serial_pan" .. vaulttwo), count=3}
305:   end)
306: end
307:
308: function demonic_rune_vault_is_decoy(e)
309:   local params = dgn.map_parameters()
```

D-HERE-25 stable
```cpp
1974:         }
1975:         return true;
1976:     }
1977:
1978:     case ABIL_ZIN_SANCTUARY:
1979:         if (env.sanctuary_time)
1980:             return fail(T_("There's already a sanctuary in place on this level."));
1981:         return true;
1982:
1983:     case ABIL_ZIN_DONATE_GOLD:
1984:         if (!you.gold)
1985:             return fail(T_("You have nothing to donate!"));
1986:         return true;
1987:
1988:     case ABIL_OKAWARU_DUEL:
1989:         if (okawaru_duel_active() || player_in_branch(BRANCH_ARENA))
1990:             return fail(T_("You are already engaged in single combat!"));
1991:         return true;
1992:
1993:     case ABIL_OKAWARU_GIFT_WEAPON:
1994:     case ABIL_OKAWARU_GIFT_ARMOUR:
1995:         if (feat_eliminates_items(env.grid(you.pos())))
1996:             return fail(T_("Any gift you received here would fall and be lost!"));
1997:         return true;
1998:
1999:     case ABIL_ELYVILON_HEAL_SELF:
2000:         if (you.hp == you.hp_max)
2001:             return fail_canned(MSG_FULL_HEALTH, T_("Your health is already full."));
2002:         if (you.duration[DUR_DEATHS_DOOR])
2003:             return fail(T_("You can't heal while in death's door."));
2004:         return true;
2005:
2006:     case ABIL_ELYVILON_PURIFICATION:
2007:         if (!you.duration[DUR_SICKNESS]
2008:             && !you.duration[DUR_POISONING]
2009:             && !you.duration[DUR_CONF] && !you.duration[DUR_SLOW]
2010:             && !you.petrifying()
2011:             && !player_drained()
2012:             && !you.duration[DUR_WEAK])
2013:         {
2014:             return fail(T_("Nothing ails you!"));
2015:         }
2016:         return true;
2017:
2018:     case ABIL_ELYVILON_DIVINE_VIGOUR:
```

D-HERE-25 trunk
```cpp
2066:         }
2067:         return true;
2068:     }
2069:
2070:     case ABIL_ZIN_SANCTUARY:
2071:         if (env.sanctuary_time)
2072:             return fail(T_("There's already a sanctuary in place on this level."));
2073:         return true;
2074:
2075:     case ABIL_ZIN_DONATE_GOLD:
2076:         if (!you.gold)
2077:             return fail(T_("You have nothing to donate!"));
2078:         return true;
2079:
2080:     case ABIL_OKAWARU_DUEL:
2081:         if (okawaru_duel_active() || player_in_branch(BRANCH_ARENA))
2082:             return fail(T_("You are already engaged in single combat!"));
2083:         return true;
2084:
2085:     case ABIL_OKAWARU_GIFT_WEAPON:
2086:     case ABIL_OKAWARU_GIFT_ARMOUR:
2087:         if (feat_eliminates_items(env.grid(you.pos())))
2088:             return fail(T_("Any gift you received here would fall and be lost!"));
2089:         return true;
2090:
2091:     case ABIL_ELYVILON_HEAL_SELF:
2092:         if (you.hp == you.hp_max)
2093:             return fail_canned(MSG_FULL_HEALTH, T_("Your health is already full."));
2094:         if (you.duration[DUR_DEATHS_DOOR])
2095:             return fail(T_("You can't heal while in death's door."));
2096:         return true;
2097:
2098:     case ABIL_ELYVILON_PURIFICATION:
2099:         if (!you.duration[DUR_SICKNESS]
2100:             && !you.duration[DUR_POISONING]
2101:             && !you.duration[DUR_CONF] && !you.duration[DUR_SLOW]
2102:             && !you.petrifying()
2103:             && !player_drained()
2104:             && !you.duration[DUR_WEAK])
2105:         {
2106:             return fail(T_("Nothing ails you!"));
2107:         }
2108:         return true;
2109:
2110:     case ABIL_ELYVILON_AURA_OF_VIGOUR:
```

D-HERE-26 stable
```cpp
3059:         const string reason = you.no_tele_reason();
3060:         if (!reason.empty())
3061:         {
3062:             mpr(pre_succ_msg);
3063:             mpr(reason);
3064:             break;
3065:         }
3066:
3067:         you_teleport();
3068:     }
3069:         break;
3070:
3071:     case SCR_ACQUIREMENT:
3072:         if (!alreadyknown)
3073:             mpr(T_("It is a scroll of acquirement!"));
3074:
3075:         // included in default force_more_message
3076:         // Identify it early in case the player checks the '\' screen.
3077:         identify_item(*scroll);
3078:
3079:         if (feat_eliminates_items(env.grid(you.pos())))
3080:         {
3081:             mpr(T_("Anything you acquire here would fall and be lost!"));
3082:             cancel_scroll = true;
3083:             break;
3084:         }
3085:
3086:         cancel_scroll = !acquirement_menu();
3087:         break;
3088:
3089:     case SCR_FEAR:
3090:         mpr(T_("You assume a fearsome visage."));
3091:         mass_enchantment(ENCH_FEAR, 1000);
3092:         break;
3093:
3094:     case SCR_NOISE:
3095:         noisy(25, you.pos(), T_("You hear a loud clanging noise!"));
3096:         break;
3097:
3098:     case SCR_SUMMONING:
3099:         cancel_scroll = summon_shadow_creatures() == spret::abort
3100:                         && alreadyknown;
3101:         break;
3102:
3103:     case SCR_BUTTERFLIES:
```

D-HERE-26 trunk
```cpp
3190:         const string reason = you.no_tele_reason();
3191:         if (!reason.empty())
3192:         {
3193:             mpr(pre_succ_msg);
3194:             mpr(reason);
3195:             break;
3196:         }
3197:
3198:         you_teleport();
3199:     }
3200:         break;
3201:
3202:     case SCR_ACQUIREMENT:
3203:         if (!alreadyknown)
3204:             mpr(T_("It is a scroll of acquirement!"));
3205:
3206:         // included in default force_more_message
3207:         // Identify it early in case the player checks the '\' screen.
3208:         identify_item(*scroll);
3209:
3210:         if (feat_eliminates_items(env.grid(you.pos())))
3211:         {
3212:             mpr(T_("Anything you acquire here would fall and be lost!"));
3213:             result = spret::abort;
3214:             break;
3215:         }
3216:
3217:         if (!acquirement_menu())
3218:             result = spret::abort;
3219:         break;
3220:
3221:     case SCR_FEAR:
3222:         mpr(T_("You assume a fearsome visage."));
3223:         mass_enchantment(ENCH_FEAR, 1000);
3224:         break;
3225:
3226:     case SCR_NOISE:
3227:         noisy(25, you.pos(), T_("You hear a loud clanging noise!"));
3228:         break;
3229:
3230:     case SCR_SUMMONING:
3231:         result = summon_shadow_creatures();
3232:         break;
3233:
3234:     case SCR_BUTTERFLIES:
```

D-HERE-28 stable
```cpp
911:         && !crawl_state.arena_suspended)
912:     {
913:         start_travel(lmove.target);
914:     }
915: }
916:
917: bool get_look_position(coord_def *c)
918: {
919:     dist lmove = _look_around_target(you.pos());
920:     if (lmove.isCancel)
921:         return false;
922:     *c = lmove.target;
923:     return true;
924: }
925:
926: static dist _look_around_target(const coord_def &whence)
927: {
928:     dist lmove;   // Will be initialised by direction().
929:     direction_chooser_args args;
930:     args.restricts = DIR_TARGET;
931:     args.just_looking = true;
932:     args.needs_path = false;
933:     const string target_prefix = T_("Here");
934:     args.target_prefix = target_prefix.c_str();
935:     args.default_place = whence - you.pos();
936:     direction(lmove, args);
937:     return lmove;
938: }
939:
940: range_view_annotator::range_view_annotator(targeter *range)
941: {
942:     if (range && Options.darken_beyond_range)
943:         crawl_state.darken_range = range;
944: }
945:
946: range_view_annotator::~range_view_annotator()
947: {
948:     crawl_state.darken_range = nullptr;
949: }
950:
951: monster_view_annotator::monster_view_annotator(vector<monster *> *monsters)
952: {
953:     if ((Options.use_animations & UA_MONSTER_IN_SIGHT) && monsters->size())
954:     {
955:         crawl_state.flash_monsters = monsters;
```

D-HERE-28 trunk
```cpp
894:         && !crawl_state.arena_suspended)
895:     {
896:         start_travel(lmove.target);
897:     }
898: }
899:
900: bool get_look_position(coord_def *c)
901: {
902:     dist lmove = _look_around_target(you.pos());
903:     if (lmove.isCancel)
904:         return false;
905:     *c = lmove.target;
906:     return true;
907: }
908:
909: static dist _look_around_target(const coord_def &whence)
910: {
911:     dist lmove;   // Will be initialised by direction().
912:     direction_chooser_args args;
913:     args.restricts = DIR_TARGET;
914:     args.just_looking = true;
915:     args.needs_path = false;
916:     args.target_prefix = "Here";
917:     args.default_place = whence - you.pos();
918:     direction(lmove, args);
919:     return lmove;
920: }
921:
922: range_view_annotator::range_view_annotator(targeter *range)
923: {
924:     if (range && Options.darken_beyond_range)
925:         crawl_state.darken_range = range;
926: }
927:
928: range_view_annotator::~range_view_annotator()
929: {
930:     crawl_state.darken_range = nullptr;
931: }
932:
933: monster_view_annotator::monster_view_annotator(vector<coord_def> *monsters)
934: {
935:     if ((Options.use_animations & UA_MONSTER_IN_SIGHT) && monsters->size())
936:     {
937:         crawl_state.flash_monsters = monsters;
938:         viewwindow(false);
```

D-HERE-29 stable
```cpp
341: end
342:
343: function wizlab_wucad_msgfn(data, triggerable, triggerer, marker, ev)
344:   if data.trig == true then
345:     return
346:   end
347:
348:   if crawl.one_chance_in(3) then
349:     return
350:   end
351:
352:   if dgn.persist.wucad_mu_died == true then
353:     return
354:   end
355:
356:   if data.spot == 1 then
357:     crawl.mpr(crawl.t_("Strange, shadowy figures dance through the air in front of you."), "talk_visual")
358:     data.trig = true
359:   elseif data.spot == 2 then
360:     crawl.mpr(crawl.t_("This room is filled with shadowy figures, quietly meditating."), "talk_visual")
361:     data.trig = true
362:   elseif data.spot == 3 then
363:     crawl.mpr(crawl.t_("Here, spectral monks perform complicated, martial routines; they fade quickly."), "talk_visual")
364:     data.trig = true
365:   elseif data.spot == 4 then
366:     if you.silenced() then
367:       return
368:     end
369:     crawl.mpr(crawl.t_("Faint laughter comes from somewhere. Too faint to be real."), "talk_visual")
370:     data.trig = true
371:   elseif data.spot == 5 then
372:     if you.silenced() then
373:       return
374:     end
375:     crawl.mpr(crawl.t_("There is a faint scream of pain from a crouched figure. This too fades quickly."), "talk_visual")
376:     data.trig = true
377:   elseif data.spot == 6 then
378:     crawl.mpr(crawl.t_("Grey monks gather around the fountain. They do not speak, nor look at each other."), "talk_visual")
379:     data.trig = true
380:   elseif data.spot == 7 then
381:     crawl.mpr(crawl.t_("A figure sits in silent meditation. It spots you, gestures wildly, and disappears."), "talk_visual")
382:     data.trig = true
383:   end
384: end
385:
```

D-HERE-29 trunk
```cpp
341: end
342:
343: function wizlab_wucad_msgfn(data, triggerable, triggerer, marker, ev)
344:   if data.trig == true then
345:     return
346:   end
347:
348:   if crawl.one_chance_in(3) then
349:     return
350:   end
351:
352:   if dgn.persist.wucad_mu_died == true then
353:     return
354:   end
355:
356:   if data.spot == 1 then
357:     crawl.mpr(crawl.t_("Strange, shadowy figures dance through the air in front of you."), "talk_visual")
358:     data.trig = true
359:   elseif data.spot == 2 then
360:     crawl.mpr(crawl.t_("This room is filled with shadowy figures, quietly meditating."), "talk_visual")
361:     data.trig = true
362:   elseif data.spot == 3 then
363:     crawl.mpr(crawl.t_("Here, spectral monks perform complicated, martial routines; they fade quickly."), "talk_visual")
364:     data.trig = true
365:   elseif data.spot == 4 then
366:     if you.silenced() then
367:       return
368:     end
369:     crawl.mpr(crawl.t_("Faint laughter comes from somewhere. Too faint to be real."), "talk_visual")
370:     data.trig = true
371:   elseif data.spot == 5 then
372:     if you.silenced() then
373:       return
374:     end
375:     crawl.mpr(crawl.t_("There is a faint scream of pain from a crouched figure. This too fades quickly."), "talk_visual")
376:     data.trig = true
377:   elseif data.spot == 6 then
378:     crawl.mpr(crawl.t_("Grey monks gather around the fountain. They do not speak, nor look at each other."), "talk_visual")
379:     data.trig = true
380:   elseif data.spot == 7 then
381:     crawl.mpr(crawl.t_("A figure sits in silent meditation. It spots you, gestures wildly, and disappears."), "talk_visual")
382:     data.trig = true
383:   end
384: end
385:
```

D-HERE-30 stable
```cpp
751:         return level_id(you.where_are_you, you.depth - 1);
752:     if (!is_connected_branch(you.where_are_you))
753:         return level_id(); // no rocketing out of the abyss, portals, pan...
754:     const level_id entry = brentry[you.where_are_you];
755:     if (entry.is_valid())
756:         return entry;
757:     return level_id();
758: }
759:
760: void rise_through_ceiling()
761: {
762:     const level_id whither = level_above();
763:     if (you.where_are_you == BRANCH_DUNGEON
764:         && you.depth == 1
765:         && player_has_orb())
766:     {
767:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
768:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
769:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
770:     }
771:     if (!whither.is_valid())
772:     {
773:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
774:         return;
775:     }
776:
777:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
778:     untag_followers(); // XXX: is this needed?
779:     stop_delay(true);
780:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
781:                      whither, true, true, false, false);
782:
783:     // flavour! blow a hole through the floor
784:     if (env.grid(you.pos()) == DNGN_FLOOR
785:         && !trap_at(you.pos()) /*needed?*/
786:         && is_valid_shaft_level())
787:     {
788:         place_specific_trap(you.pos(), TRAP_SHAFT);
789:     }
790: }
791:
792: /**
793:  * Transition to a different level.
794:  *
795:  * @param how The type of stair/portal tile the player is being conveyed through
```

D-HERE-30 trunk
```cpp
767:         return level_id(you.where_are_you, you.depth - 1);
768:     if (!is_connected_branch(you.where_are_you))
769:         return level_id(); // no rocketing out of the abyss, portals, pan...
770:     const level_id entry = brentry[you.where_are_you];
771:     if (entry.is_valid())
772:         return entry;
773:     return level_id();
774: }
775:
776: void rise_through_ceiling()
777: {
778:     const level_id whither = level_above();
779:     if (you.where_are_you == BRANCH_DUNGEON
780:         && you.depth == 1
781:         && player_has_orb())
782:     {
783:         mpr(T_("With a burst of heat and light, you rocket upwards!"));
784:         floor_transition(DNGN_EXIT_DUNGEON, DNGN_EXIT_DUNGEON,
785:                          level_id(BRANCH_DUNGEON, 0), true, true, false, false);
786:     }
787:     if (!whither.is_valid())
788:     {
789:         mpr(T_("In a burst of heat and light, you briefly surge upwards...but you can't rise from here."));
790:         return;
791:     }
792:
793:     mpr(T_("With a burst of heat and light, you rocket upwards!"));
794:     untag_followers(); // XXX: is this needed?
795:     stop_delay(true);
796:     floor_transition(DNGN_ALTAR_IGNIS /*hack*/, DNGN_ALTAR_IGNIS,
797:                      whither, true, true, false, false);
798:
799:     // flavour! blow a hole through the floor
800:     if (env.grid(you.pos()) == DNGN_FLOOR && is_valid_shaft_level())
801:         dungeon_terrain_changed(you.pos(), DNGN_TRAP_SHAFT);
802: }
803:
804: /**
805:  * Transition to a different level.
806:  *
807:  * @param how The type of stair/portal tile the player is being conveyed through
808:  * @param whence The tile the player was on at the beginning of the transition
809:  *               (likely the same as how, unless forced is true)
810:  * @param whither The destination level
811:  * @param shaft Is the player going down a shaft?
```

D-HERE-31 stable
```cpp
576:
577: // Returns true if this is a valid swap for this monster. If true, then
578: // the valid location is set in loc. (Otherwise loc becomes garbage.)
579: bool swap_check(monster* mons, coord_def &loc, bool quiet)
580: {
581:     loc = you.pos();
582:
583:     if (you.cannot_move())
584:         return false;
585:
586:     // Don't move onto dangerous terrain.
587:     if (is_feat_dangerous(env.grid(mons->pos())))
588:     {
589:         canned_msg(MSG_UNTHINKING_ACT);
590:         return false;
591:     }
592:
593:     if (mons_is_projectile(*mons)
594:         || mons->type == MONS_BOULDER
595:         || mons->type == MONS_BLAZEHEART_CORE)
596:     {
597:         if (!quiet)
598:             mpr(T_("It would be unwise to walk in here."));
599:         return false;
600:     }
601:
602:     if (mons->caught())
603:     {
604:         if (!quiet)
605:         {
606:             simple_monster_message(*mons,
607:                 make_stringf(T_(" is %s!"), held_status(mons)).c_str());
608:         }
609:         return false;
610:     }
611:
612:     if (mons->is_constricted())
613:     {
614:         if (!quiet)
615:             simple_monster_message(*mons, T_(" is being constricted!"));
616:         return false;
617:     }
618:
619:     // TODO: consider waking up sleeping monsters when you push em?
620:     // (That's what happens for monsters pushing monsters...)
```

D-HERE-31 trunk
```cpp
636: {
637:     loc = you.pos();
638:
639:     if (you.cannot_move())
640:     {
641:         if (!quiet)
642:             canned_msg(MSG_CANNOT_MOVE);
643:         return false;
644:     }
645:
646:     // Don't move onto dangerous terrain.
647:     if (is_feat_dangerous(env.grid(mons->pos())))
648:     {
649:         canned_msg(MSG_UNTHINKING_ACT);
650:         return false;
651:     }
652:
653:     if (mons_is_projectile(*mons)
654:         || mons->type == MONS_BOULDER
655:         || mons->type == MONS_BLAZEHEART_CORE)
656:     {
657:         if (!quiet)
658:             mpr(T_("It would be unwise to walk in here."));
659:         return false;
660:     }
661:
662:     if (mons->caught())
663:     {
664:         if (!quiet)
665:         {
666:             simple_monster_message(*mons,
667:                 make_stringf(T_(" is %s!"), held_status(mons)).c_str());
668:         }
669:         return false;
670:     }
671:
672:     if (mons->is_constricted())
673:     {
674:         if (!quiet)
675:             simple_monster_message(*mons, T_(" is being constricted!"));
676:         return false;
677:     }
678:
679:     // TODO: consider waking up sleeping monsters when you push em?
680:     // (That's what happens for monsters pushing monsters...)
```

D-HERE-33 stable
```cpp
364:     // when a single tough monster appears.
365:     const int horror_level = max(0, current_horror_level() - 1);
366:
367:     if (horror_level <= 0)
368:     {
369:         // If you were horrified before & aren't now, clean up.
370:         _end_horror();
371:         return;
372:     }
373:
374:     // Lookup the old value before modifying it
375:     const int old_horror_level = _old_horror_level();
376:
377:     // as long as there's still scary enemies, keep the horror going
378:     you.props[HORROR_PENALTY_KEY] = horror_level;
379:     you.set_duration(DUR_HORROR, 1);
380:
381:     // only show a message on increase
382:     if (horror_level <= old_horror_level)
383:         return;
384:
385:     if (horror_level >= HORROR_LVL_OVERWHELMING)
386:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
387:     else if (horror_level >= HORROR_LVL_EXTREME)
388:         mpr(T_("You reel with horror at the sight of these foes!"));
389:     else
390:         mpr(T_("You feel a twist of horror at the sight of this foe."));
391: }
392:
393: static void _update_claustrophobia()
394: {
395:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
396:         return;
397:
398:     int count = 0;
399:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
400:     {
401:         if (feat_is_solid(env.grid(*ai)))
402:             ++count;
403:     }
404:
405:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
406: }
407:
408: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
```

D-HERE-33 trunk
```cpp
366:     // when a single tough monster appears.
367:     const int horror_level = max(0, current_horror_level() - 1);
368:
369:     if (horror_level <= 0)
370:     {
371:         // If you were horrified before & aren't now, clean up.
372:         _end_horror();
373:         return;
374:     }
375:
376:     // Lookup the old value before modifying it
377:     const int old_horror_level = _old_horror_level();
378:
379:     // as long as there's still scary enemies, keep the horror going
380:     you.props[HORROR_PENALTY_KEY] = horror_level;
381:     you.set_duration(DUR_HORROR, 1);
382:
383:     // only show a message on increase
384:     if (horror_level <= old_horror_level)
385:         return;
386:
387:     if (horror_level >= HORROR_LVL_OVERWHELMING)
388:         mpr(T_("Monsters! Monsters everywhere! You have to get out of here!"));
389:     else if (horror_level >= HORROR_LVL_EXTREME)
390:         mpr(T_("You reel with horror at the sight of these foes!"));
391:     else
392:         mpr(T_("You feel a twist of horror at the sight of this foe."));
393: }
394:
395: static void _update_claustrophobia()
396: {
397:     if (!you.has_bane(BANE_CLAUSTROPHOBIA))
398:         return;
399:
400:     int count = 0;
401:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
402:     {
403:         if (feat_is_solid(env.grid(*ai)))
404:             ++count;
405:     }
406:
407:     you.props[CLAUSTROPHOBIA_KEY] = count * 2;
408: }
409:
410: // Uskayaw piety decays incredibly fast, but only to a baseline level of *.
```

D-HERE-34 trunk
```cpp
1666:     fail_check();
1667:
1668:     for (stack_iterator si(where); si; ++si)
1669:     {
1670:         if (item_is_orb(*si))
1671:         {
1672:             fake_noisy(30, where);
1673:
1674:             // There's also a 1-in-3 flat chance of apport failing.
1675:             if (one_chance_in(3))
1676:             {
1677:                 orb_pickup_noise(where, 30,
1678:                     T_("The Orb shrieks and becomes a dead weight against your magic!"),
1679:                     T_("The Orb lets out a furious burst of light and becomes "
1680:                        "a dead weight against your magic!"));
1681:                 return spret::success;
1682:             }
1683:             else // Otherwise it's just a noisy little shiny thing
1684:             {
1685:                 orb_pickup_noise(where, 30,
1686:                     T_("The Orb shrieks as your magic touches it!"),
1687:                     T_("The Orb lets out a furious burst of light as your magic touches it!"));
1688:                 start_orb_run(CHAPTER_ANGERED_PANDEMONIUM, T_("Now pick up the Orb and get out of here!"));
1689:             }
1690:         }
1691:     }
1692:
1693:     dprf("Apport: new spot is %d/%d", new_spot.x, new_spot.y);
1694:
1695:     // Actually move the items.
1696:     int num_moved = 0;
1697:     while (you.visible_igrd(where) != NON_ITEM)
1698:     {
1699:         if (move_top_item(where, new_spot))
1700:             ++num_moved;
1701:     }
1702:
1703:     mprf(T_("Yoink! You pull the item%s %stowards yourself."),
1704:          num_moved > 1 ? "s" : "",
1705:          new_spot != you.pos() ? T_("partway ") : "");
1706:
1707:     return spret::success;
1708: }
1709:
1710: bool golubria_valid_cell(coord_def p, bool just_check)
```

D-HERE-35 trunk
```cpp
110:                   false, 'n'))
111:     {
112:         canned_msg(MSG_OK);
113:         return false;
114:     }
115:
116:     // The unknown god might not tolerate our current form or some of our gear.
117:     // Warn about whatever they might make us give up.
118:     bool form_at_risk = false;
119:     bool gear_at_risk = false;
120:     for (god_type god : gods)
121:     {
122:         if (!transformed_player_can_join_god(god))
123:             form_at_risk = true;
124:         for (item_def* item : you.equipment.get_slot_items(SLOT_ALL_EQUIPMENT, true))
125:             if (god_forbids_item(*item, god))
126:                 gear_at_risk = true;
127:     }
128:
129:     if (form_at_risk || gear_at_risk)
130:     {
131:         const string prompt = form_at_risk && gear_at_risk
132:             ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
133:             : form_at_risk
134:                 ? T_("Praying here may force you to leave your current form. Pray anyway?")
135:                 : T_("Praying here may force you to remove some of your equipment. Pray anyway?");
136:         if (!yesno(prompt.c_str(), false, 'n'))
137:         {
138:             canned_msg(MSG_OK);
139:             return false;
140:         }
141:     }
142:
143:     const god_type altar_god = *random_iterator(gods);
144:     dungeon_terrain_changed(you.pos(), altar_for_god(altar_god));
145:     take_note(Note(NOTE_MESSAGE, 0, 0,
146:                    "Prayed at the altar of an unknown god."));
147:     you.turn_is_over = true;
148:     {
149:         // Don't check for or charge a Gozag service fee.
150:         unwind_var<int> fakepoor(you.attribute[ATTR_GOLD_GENERATED], 0);
151:
152:         string rejection_message =
153:             cannot_join_god_reason(altar_god, true, false);
154:         if (!rejection_message.empty())
155:         {
156:             mprf(MSGCH_GOD, "%s", rejection_message.c_str());
157:             return true;
```

D-HERE-36 trunk
```cpp
112:         canned_msg(MSG_OK);
113:         return false;
114:     }
115:
116:     // The unknown god might not tolerate our current form or some of our gear.
117:     // Warn about whatever they might make us give up.
118:     bool form_at_risk = false;
119:     bool gear_at_risk = false;
120:     for (god_type god : gods)
121:     {
122:         if (!transformed_player_can_join_god(god))
123:             form_at_risk = true;
124:         for (item_def* item : you.equipment.get_slot_items(SLOT_ALL_EQUIPMENT, true))
125:             if (god_forbids_item(*item, god))
126:                 gear_at_risk = true;
127:     }
128:
129:     if (form_at_risk || gear_at_risk)
130:     {
131:         const string prompt = form_at_risk && gear_at_risk
132:             ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
133:             : form_at_risk
134:                 ? T_("Praying here may force you to leave your current form. Pray anyway?")
135:                 : T_("Praying here may force you to remove some of your equipment. Pray anyway?");
136:         if (!yesno(prompt.c_str(), false, 'n'))
137:         {
138:             canned_msg(MSG_OK);
139:             return false;
140:         }
141:     }
142:
143:     const god_type altar_god = *random_iterator(gods);
144:     dungeon_terrain_changed(you.pos(), altar_for_god(altar_god));
145:     take_note(Note(NOTE_MESSAGE, 0, 0,
146:                    "Prayed at the altar of an unknown god."));
147:     you.turn_is_over = true;
148:     {
149:         // Don't check for or charge a Gozag service fee.
150:         unwind_var<int> fakepoor(you.attribute[ATTR_GOLD_GENERATED], 0);
151:
152:         string rejection_message =
153:             cannot_join_god_reason(altar_god, true, false);
154:         if (!rejection_message.empty())
155:         {
156:             mprf(MSGCH_GOD, "%s", rejection_message.c_str());
157:             return true;
```

D-HERE-37 trunk
```cpp
113:         return false;
114:     }
115:
116:     // The unknown god might not tolerate our current form or some of our gear.
117:     // Warn about whatever they might make us give up.
118:     bool form_at_risk = false;
119:     bool gear_at_risk = false;
120:     for (god_type god : gods)
121:     {
122:         if (!transformed_player_can_join_god(god))
123:             form_at_risk = true;
124:         for (item_def* item : you.equipment.get_slot_items(SLOT_ALL_EQUIPMENT, true))
125:             if (god_forbids_item(*item, god))
126:                 gear_at_risk = true;
127:     }
128:
129:     if (form_at_risk || gear_at_risk)
130:     {
131:         const string prompt = form_at_risk && gear_at_risk
132:             ? T_("Praying here may force you to leave your current form or remove some of your equipment. Pray anyway?")
133:             : form_at_risk
134:                 ? T_("Praying here may force you to leave your current form. Pray anyway?")
135:                 : T_("Praying here may force you to remove some of your equipment. Pray anyway?");
136:         if (!yesno(prompt.c_str(), false, 'n'))
137:         {
138:             canned_msg(MSG_OK);
139:             return false;
140:         }
141:     }
142:
143:     const god_type altar_god = *random_iterator(gods);
144:     dungeon_terrain_changed(you.pos(), altar_for_god(altar_god));
145:     take_note(Note(NOTE_MESSAGE, 0, 0,
146:                    "Prayed at the altar of an unknown god."));
147:     you.turn_is_over = true;
148:     {
149:         // Don't check for or charge a Gozag service fee.
150:         unwind_var<int> fakepoor(you.attribute[ATTR_GOLD_GENERATED], 0);
151:
152:         string rejection_message =
153:             cannot_join_god_reason(altar_god, true, false);
154:         if (!rejection_message.empty())
155:         {
156:             mprf(MSGCH_GOD, "%s", rejection_message.c_str());
157:             return true;
```

D-HERE-38 stable
```cpp
2968:     if (level_target.id.depth > 0)
2969:     {
2970:         you.running = RMODE_INTERLEVEL;
2971:         you.running.pos.reset();
2972:         last_stair.id.depth = -1;
2973:         last_stair.pos.reset();
2974:
2975:         _Route_Warning.new_dest(level_target);
2976:
2977:         _Src_Level = level_id::current();
2978:         _Src_Dest_Level_Delta = level_distance(_Src_Level,
2979:                                                level_target.id);
2980:
2981:         _start_running();
2982:     }
2983: }
2984:
2985: void start_translevel_travel(const level_pos &pos)
2986: {
2987:     if (!can_travel_to(pos.id))
2988:     {
2989:         if (!can_travel_interlevel())
2990:             mpr(T_("Sorry, you can't auto-travel out of here."));
2991:         else
2992:             mpr(T_("Sorry, I don't know how to get there."));
2993:         return;
2994:     }
2995:
2996:     if (pos.is_valid() && !in_bounds(pos.pos))
2997:     {
2998:         mpr(T_("Sorry, I don't know how to get there."));
2999:         return;
3000:     }
3001:
3002:     // Remember where we're going so we can easily go back if interrupted.
3003:     you.travel_x = pos.pos.x;
3004:     you.travel_y = pos.pos.y;
3005:     you.travel_z = pos.id;
3006:
3007: #ifdef DEBUG_TRAVEL
3008:     dprf("going to %d depth %d, pos %d,%d", pos.id.branch, pos.id.depth,
3009:         pos.pos.x, pos.pos.y);
3010: #endif
3011:
3012:     if (!can_travel_interlevel())
```

D-HERE-38 stable
```cpp
5221:     say_any(apply_quantities(stairs), "stair");
5222:     say_any(apply_quantities(transporters), "transporter");
5223:     say_any(apply_quantities(runed_doors), "runed door");
5224:     say_any(apply_quantities(runelights), "runelights");
5225:
5226:     return true;
5227: }
5228:
5229: void do_interlevel_travel()
5230: {
5231:     if (Hints.hints_travel)
5232:         Hints.hints_travel = 0;
5233:
5234:     if (!can_travel_interlevel())
5235:     {
5236:         if (you.running.pos == you.pos())
5237:         {
5238:             mpr(T_("You're already here!"));
5239:             return;
5240:         }
5241:         else if (!you.running.pos.x || !you.running.pos.y)
5242:         {
5243:             mpr(T_("Sorry, you can't auto-travel out of here."));
5244:             return;
5245:         }
5246:
5247:         // Don't ask for a destination if you can only travel
5248:         // within level anyway.
5249:         start_travel(you.running.pos);
5250:     }
5251:     else
5252:         _start_translevel_travel_prompt();
5253:
5254:     if (you.running)
5255:         clear_messages();
5256: }
5257:
5258: #ifdef USE_TILE
5259: // (0,0) = same position is handled elsewhere.
5260: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5261: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5262:
5263: static const command_type cmd_array[8] =
5264: {
5265:     CMD_MOVE_DOWN_LEFT,  CMD_MOVE_DOWN,  CMD_MOVE_DOWN_RIGHT,
```

D-HERE-38 trunk
```cpp
3006:     if (level_target.id.depth > 0)
3007:     {
3008:         you.running = RMODE_INTERLEVEL;
3009:         you.running.pos.reset();
3010:         last_stair.id.depth = -1;
3011:         last_stair.pos.reset();
3012:
3013:         _Route_Warning.new_dest(level_target);
3014:
3015:         _Src_Level = level_id::current();
3016:         _Src_Dest_Level_Delta = level_distance(_Src_Level,
3017:                                                level_target.id);
3018:
3019:         _start_running();
3020:     }
3021: }
3022:
3023: void start_translevel_travel(const level_pos &pos)
3024: {
3025:     if (!can_travel_to(pos.id))
3026:     {
3027:         if (!can_travel_interlevel())
3028:             mpr(T_("Sorry, you can't auto-travel out of here."));
3029:         else
3030:             mpr(T_("Sorry, I don't know how to get there."));
3031:         return;
3032:     }
3033:
3034:     if (pos.is_valid() && !in_bounds(pos.pos))
3035:     {
3036:         mpr(T_("Sorry, I don't know how to get there."));
3037:         return;
3038:     }
3039:
3040:     // Remember where we're going so we can easily go back if interrupted.
3041:     you.travel_x = pos.pos.x;
3042:     you.travel_y = pos.pos.y;
3043:     you.travel_z = pos.id;
3044:
3045: #ifdef DEBUG_TRAVEL
3046:     dprf("going to %d depth %d, pos %d,%d", pos.id.branch, pos.id.depth,
3047:         pos.pos.x, pos.pos.y);
3048: #endif
3049:
3050:     if (!can_travel_interlevel())
```

D-HERE-38 trunk
```cpp
5329:     say_any(apply_quantities(transporters), "transporter");
5330:     say_any(apply_quantities(runed_doors), "runed door");
5331:     say_any(apply_quantities(runelights), "runelights");
5332:     say_any(apply_quantities(mutation_catalysts), "mutation catalysts");
5333:
5334:     return true;
5335: }
5336:
5337: void do_interlevel_travel()
5338: {
5339:     if (Hints.hints_travel)
5340:         Hints.hints_travel = 0;
5341:
5342:     if (!can_travel_interlevel())
5343:     {
5344:         if (you.running.pos == you.pos())
5345:         {
5346:             mpr(T_("You're already here!"));
5347:             return;
5348:         }
5349:         else if (!you.running.pos.x || !you.running.pos.y)
5350:         {
5351:             mpr(T_("Sorry, you can't auto-travel out of here."));
5352:             return;
5353:         }
5354:
5355:         // Don't ask for a destination if you can only travel
5356:         // within level anyway.
5357:         start_travel(you.running.pos);
5358:     }
5359:     else
5360:         _start_translevel_travel_prompt();
5361:
5362:     if (you.running)
5363:         clear_messages();
5364: }
5365:
5366: #ifdef USE_TILE
5367: // (0,0) = same position is handled elsewhere.
5368: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
5369: static const int dir_dy[8] = { 1, 1, 1,  0, 0, -1, -1, -1};
5370:
5371: static const command_type cmd_array[8] =
5372: {
5373:     CMD_MOVE_DOWN_LEFT,  CMD_MOVE_DOWN,  CMD_MOVE_DOWN_RIGHT,
```

D-HERE-39 stable
```cpp
1527: {
1528:
1529:     if (inv_count() < 1)
1530:     {
1531:         canned_msg(MSG_NOTHING_CARRIED);
1532:         return;
1533:     }
1534:
1535:     int flags = MF_SINGLESELECT | MF_ALLOW_FORMATTING | MF_SECONDARY_SCROLL;
1536:     if (Options.show_paged_inventory)
1537:         flags |= MF_PAGED_INVENTORY;
1538:     else
1539:         flags |= MF_SELECT_BY_CATEGORY;
1540:
1541:     InvMenu menu(flags);
1542:     menu.load_inv_items(Options.show_paged_inventory ? OSEL_GEAR : OSEL_ANY, -1);
1543:     menu.set_type(menu_type::describe);
1544:
1545: #ifdef __ANDROID__
1546:     if (crawl_state.updating_scores)
1547:     {
1548:         const string continue_text = string("<bg:brown><white>")
1549:             + T_("Tap here or press Back to view the score summary.")
1550:             + "</white></bg:brown>";
1551:         menu.set_more(formatted_string::parse_string(continue_text));
1552:     }
1553: #endif
1554:
1555:     // Jump to the first non-empty page.
1556:     if ((flags & MF_PAGED_INVENTORY) && menu.item_count(false) == 0)
1557:         menu.cycle_page(1);
1558:
1559:     menu.show(true);
1560:     if (!crawl_state.doing_prev_cmd_again)
1561:     {
1562:         redraw_screen();
1563:         update_screen();
1564:     }
1565: }
1566:
1567: static string _drop_menu_titlefn(const Menu*, const string &)
1568: {
1569: #ifdef __ANDROID__
1570:     if (tiles.is_using_small_layout())
1571:         return string(T_("Drop what?")) + " " + slot_description();
1572: #endif
```

D-HERE-39 trunk
```cpp
1549: {
1550:
1551:     if (inv_count() < 1)
1552:     {
1553:         canned_msg(MSG_NOTHING_CARRIED);
1554:         return;
1555:     }
1556:
1557:     int flags = MF_SINGLESELECT | MF_ALLOW_FORMATTING | MF_SECONDARY_SCROLL;
1558:     if (Options.show_paged_inventory)
1559:         flags |= MF_PAGED_INVENTORY;
1560:     else
1561:         flags |= MF_SELECT_BY_CATEGORY;
1562:
1563:     InvMenu menu(flags);
1564:     menu.load_inv_items(Options.show_paged_inventory ? OSEL_GEAR : OSEL_ANY, -1);
1565:     menu.set_type(menu_type::describe);
1566:
1567: #ifdef __ANDROID__
1568:     if (crawl_state.updating_scores)
1569:     {
1570:         const string continue_text = string("<bg:brown><white>")
1571:             + T_("Tap here or press Back to view the score summary.")
1572:             + "</white></bg:brown>";
1573:         menu.set_more(formatted_string::parse_string(continue_text));
1574:     }
1575: #endif
1576:
1577:     // Jump to the first non-empty page.
1578:     if ((flags & MF_PAGED_INVENTORY) && menu.item_count(false) == 0)
1579:         menu.cycle_page(1);
1580:
1581:     menu.show(true);
1582:     if (!crawl_state.doing_prev_cmd_again)
1583:     {
1584:         redraw_screen();
1585:         update_screen();
1586:     }
1587: }
1588:
1589: static string _drop_menu_titlefn(const Menu*, const string &)
1590: {
1591: #ifdef __ANDROID__
1592:     if (tiles.is_using_small_layout())
1593:         return string(T_("Drop what?")) + " " + slot_description();
1594: #endif
```

D-HERE-40 stable
```cpp
2: # pan.des: Minivaults particular to Pan, and the lairs of the Pan Demon Lords
3: #
4: # Contents:
5: #   Pan inline functions
6: #   Entry portals to Pan
7: #   Panlord vaults: Mnoleg, Lom Lobon, Cerebov, Gloorx Vloq.
8: #   Lesser demon vaults: repeating rune vaults.
9: #   Lesser demon vaults: standalone vault.
10: #
11: ##############################################################################
12:
13: ##############################################################################
14: # Pan lua functions
15: ###############################################################################
16:
17: : crawl_require('dlua/vault.lua')
18:
19: # The generic pan lord warning message.
20:
21: {{
22: function pan_lord_epilogue(name)
23:     local msgs = {
24:         Mnoleg = "The air here is shimmering with an eerie glow.",
25:         ['Lom Lobon'] = "You sense a powerful magical presence. It is not pleased.",
26:         Cerebov = "Searing heat pours from the floors and walls of this place.",
27:         ['Gloorx Vloq'] = "Shadowy figures dance across your vision."
28:     }
29:     local runes = {
30:         Mnoleg = "glowing",
31:         ['Lom Lobon'] = "magical",
32:         Cerebov = "fiery",
33:         ['Gloorx Vloq'] = "dark"
34:     }
35:
36:     crawl.mpr(crawl.t_(msgs[name]), "warning")
37:     crawl.mpr(string.format(
38:         crawl.t_("The mighty Pandemonium lord %s resides here."),
39:         crawl.t_(name)), "warning")
40:     -- Counterpart to branch_rune_desc from lookup-help.cc
41:     crawl.mpr(string.format(crawl.t_("They guard the %s rune of Zot."),
42:                            crawl.t_(runes[name])))
43:     crawl.take_note(util.i18n_format_or_english(
44:         "Entered the realm of %s.", name))
45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', "")
46: end
```

D-HERE-40 trunk
```cpp
2: # pan.des: Minivaults particular to Pan, and the lairs of the Pan Demon Lords
3: #
4: # Contents:
5: #   Pan inline functions
6: #   Entry portals to Pan
7: #   Panlord vaults: Mnoleg, Lom Lobon, Cerebov, Gloorx Vloq.
8: #   Lesser demon vaults: repeating rune vaults.
9: #   Lesser demon vaults: standalone vault.
10: #
11: ##############################################################################
12:
13: ##############################################################################
14: # Pan lua functions
15: ###############################################################################
16:
17: : crawl_require('dlua/vault.lua')
18:
19: # The generic pan lord warning message.
20:
21: {{
22: function pan_lord_epilogue(name)
23:     local msgs = {
24:         Mnoleg = "The air here is shimmering with an eerie glow.",
25:         ['Lom Lobon'] = "You sense a powerful magical presence. It is not pleased.",
26:         Cerebov = "Searing heat pours from the floors and walls of this place.",
27:         ['Gloorx Vloq'] = "Shadowy figures dance across your vision."
28:     }
29:     local runes = {
30:         Mnoleg = "glowing",
31:         ['Lom Lobon'] = "magical",
32:         Cerebov = "fiery",
33:         ['Gloorx Vloq'] = "dark"
34:     }
35:
36:     crawl.mpr(crawl.t_(msgs[name]), "warning")
37:     crawl.mpr(string.format(
38:         crawl.t_("The mighty Pandemonium lord %s resides here."),
39:         crawl.t_(name)), "warning")
40:     -- Counterpart to branch_rune_desc from lookup-help.cc
41:     crawl.mpr(string.format(crawl.t_("They guard the %s rune of Zot."),
42:                            crawl.t_(runes[name])))
43:     crawl.take_note(util.i18n_format_or_english(
44:         "Entered the realm of %s.", name))
45:     crawl.mark_milestone('br.enter', 'entered the realm of ' .. name .. '.', "")
46: end
```

D-HERE-41 stable
```cpp
263:                     "reaper / shadow demon / tormentor"
264:
265:     if e.is_validating() then return end
266:     if crawl.x_chance_in_y(you.depth() + 3, you.depth() + 5) then
267:         e.tags("luniq_hellpanabyss_threat_entry")
268:         e.kmons(glyph .. "1 = " .. tiertwo)
269:         e.kmons("2 = " .. tierthree)
270:         e.nsubst("2 = 2 = 22. / *:.")
271:         e.nsubst("1 = 1:1 / *:.")
272:     else
273:         e.subst("12 = .")
274:         e.kmons(glyph .. " = " .. tiertwo .. " / " ..
275:                 tierthree .. " / " .. tierthree)
276:     end
277:
278:     e.ftile(".+12O$ : floor_demonic_red / floor_demonic_blue / " ..
279:                      "floor_demonic_green / floor_demonic_magenta")
280: end
281:
282: function pan_declare_demonic_rune(holy)
283:   if holy then
284:     crawl.mpr(crawl.t_("The tension of great conflict fills the air!"), "warning")
285:     crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))
286:   else
287:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
288:     crawl.mpr(crawl.t_("It guards the demonic rune of Zot."))
289:   end
290: end
291:
292: function pan_highlights_setup(e)
293:   -- Choose fixed demonic rune vaults.
294:   local set = { "boxes", "hellions", "pain", "frozen", "disco" }
295:   local vaultone = "_" .. util.random_from(set)
296:   local vaulttwo = vaultone
297:   while vaulttwo == vaultone do
298:      vaulttwo = "_" .. util.random_from(set)
299:   end
300:   e.hook('post_place', function ()
301:     dgn.place_maps{tag=("pan_fixed_rune" .. vaultone), count=1, die_on_error=true}
302:     dgn.place_maps{tag=("pan_fixed_lure" .. vaulttwo), count=1, die_on_error=true}
303:     dgn.place_maps{tag=("serial_pan" .. vaultone), count=3}
304:     dgn.place_maps{tag=("serial_pan" .. vaulttwo), count=3}
305:   end)
306: end
307:
```

D-HERE-41 trunk
```cpp
263:                     "reaper / shadow demon / tormentor"
264:
265:     if e.is_validating() then return end
266:     if crawl.x_chance_in_y(you.depth() + 3, you.depth() + 5) then
267:         e.tags("luniq_hellpanabyss_threat_entry")
268:         e.kmons(glyph .. "1 = " .. tiertwo)
269:         e.kmons("2 = " .. tierthree)
270:         e.nsubst("2 = 2 = 22. / *:.")
271:         e.nsubst("1 = 1:1 / *:.")
272:     else
273:         e.subst("12 = .")
274:         e.kmons(glyph .. " = " .. tiertwo .. " / " ..
275:                 tierthree .. " / " .. tierthree)
276:     end
277:
278:     e.ftile(".+12O$ : floor_demonic_red / floor_demonic_blue / " ..
279:                      "floor_demonic_green / floor_demonic_magenta")
280: end
281:
282: function pan_declare_demonic_rune(holy)
283:   if holy then
284:     crawl.mpr(crawl.t_("The tension of great conflict fills the air!"), "warning")
285:     crawl.mpr(crawl.t_("The demonic rune of Zot may be found here."))
286:   else
287:     crawl.mpr(crawl.t_("A powerful Pandemonium lord resides here."), "warning")
288:     crawl.mpr(crawl.t_("It guards the demonic rune of Zot."))
289:   end
290: end
291:
292: function pan_highlights_setup(e)
293:   -- Choose fixed demonic rune vaults.
294:   local set = { "boxes", "hellions", "pain", "frozen", "disco" }
295:   local vaultone = "_" .. util.random_from(set)
296:   local vaulttwo = vaultone
297:   while vaulttwo == vaultone do
298:      vaulttwo = "_" .. util.random_from(set)
299:   end
300:   e.hook('post_place', function ()
301:     dgn.place_maps{tag=("pan_fixed_rune" .. vaultone), count=1, die_on_error=true}
302:     dgn.place_maps{tag=("pan_fixed_lure" .. vaulttwo), count=1, die_on_error=true}
303:     dgn.place_maps{tag=("serial_pan" .. vaultone), count=3}
304:     dgn.place_maps{tag=("serial_pan" .. vaulttwo), count=3}
305:   end)
306: end
307:
```

D-HERE-42 stable
```cpp
2481:     case DNGN_TRAP_TELEPORT_PERMANENT:
2482:     case DNGN_TRAP_TYRANT:
2483:     case DNGN_TRAP_ARCHMAGE:
2484:     case DNGN_TRAP_HARLEQUIN:
2485:     case DNGN_TRAP_DEVOURER:
2486:     case DNGN_TRAP_ALARM:
2487:     case DNGN_TRAP_ZOT:
2488: #if TAG_MAJOR_VERSION == 34
2489:     case DNGN_TRAP_MECHANICAL:
2490:     case DNGN_TRAP_SPEAR:
2491:     case DNGN_TRAP_BOLT:
2492: #endif
2493:     case DNGN_TRAP_NET:
2494:     case DNGN_TRAP_PLATE:
2495:         ostr << T_("These nasty constructions can cause a range of "
2496:                 "unpleasant effects. You won't be able to avoid "
2497:                 "tripping traps by flying over them; their magic "
2498:                 "construction will cause them to be triggered anyway.");
2499:         Hints.hints_events[HINT_SEEN_TRAP] = false;
2500:         break;
2501:
2502:     case DNGN_TRAP_SHAFT:
2503:         ostr << T_("The dungeon contains a number of natural obstacles such "
2504:                 "as shafts, which lead one to three levels down. Once you "
2505:                 "know the shaft is there, you can safely step over it.\n"
2506:                 "If you want to jump down there, use <w>></w> to do so. "
2507:                 "Be warned that getting back here might be difficult.");
2508:         Hints.hints_events[HINT_SEEN_TRAP] = false;
2509:         break;
2510:
2511:     case DNGN_TRAP_WEB:
2512:         ostr << T_("Some areas of the dungeon, such as the Spider Nest, may "
2513:                 "be strewn with giant webs that may ensnare you for a short "
2514:                 "time. Insects, oozes and incorporeal entities can navigate "
2515:                 "the webs safely.");
2516:         Hints.hints_events[HINT_SEEN_WEB] = false;
2517:         break;
2518:
2519:     case DNGN_STONE_STAIRS_DOWN_I:
2520:     case DNGN_STONE_STAIRS_DOWN_II:
2521:     case DNGN_STONE_STAIRS_DOWN_III:
2522:         ostr << T_("You can enter the next (deeper) level by following them "
2523:                 "down (<w>></w>). To get back to this level again, "
2524:                 "press <w><<</w> while standing on the upstairs.");
2525: #ifdef USE_TILE
2526:         ostr << T_(" In Tiles, you can achieve the same, in either direction, "
2527:                 "by clicking the <w>left mouse button</w>.");
2528: #endif
2529:
```

D-HERE-44 stable
```cpp
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
968:             }
969:         }
970:     }
971: }
972:
973: bool item_def::is_identified() const
974: {
```

D-HERE-44 trunk
```cpp
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
968:             }
969:         }
970:     }
971: }
972:
973: bool item_def::is_identified() const
974: {
```

D-HERE-45 stable
```cpp
1504:         return env.item[o].link == NON_ITEM && env.item[o].quantity > 1;
1505: }
1506:
1507: /**
1508:  * Do the pickup command.
1509:  *
1510:  * @param partial_quantity If true, prompt for a quantity to pick up when
1511:  *                         picking up a single stack.
1512: */
1513: void pickup(bool partial_quantity)
1514: {
1515:     int keyin = 'x';
1516:
1517:     int o = you.visible_igrd(you.pos());
1518:     const int num_items = count_movable_items(o);
1519:
1520:     // Store last_pickup in case we need to restore it.
1521:     // Then clear it to fill with items picked up.
1522:     map<int,int> tmp_l_p = you.last_pickup;
1523:     you.last_pickup.clear();
1524:
1525:     if (o == NON_ITEM)
1526:         mpr(T_("There are no items here."));
1527:     else if (num_items == 1) // just one movable item?
1528:     {
1529:         // Get the link to the movable item in the pile.
1530:         while (item_is_stationary(env.item[o]))
1531:             o = env.item[o].link;
1532:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1533:     }
1534:     else if (Options.pickup_menu_limit
1535:              && num_items > (Options.pickup_menu_limit > 0
1536:                              ? Options.pickup_menu_limit
1537:                              : Options.item_stack_summary_minimum - 1))
1538:     {
1539:         pickup_menu(o);
1540:     }
1541:     else
1542:     {
1543:         int next;
1544:         if (num_items == 0)
1545:             mpr(T_("There are no objects that can be picked up here."));
1546:         else
1547:             mpr(T_("There are several objects here."));
1548:         string pickup_warning;
```

D-HERE-45 trunk
```cpp
1470:         return env.item[o].link == NON_ITEM && env.item[o].quantity > 1;
1471: }
1472:
1473: /**
1474:  * Do the pickup command.
1475:  *
1476:  * @param partial_quantity If true, prompt for a quantity to pick up when
1477:  *                         picking up a single stack.
1478: */
1479: void pickup(bool partial_quantity)
1480: {
1481:     int keyin = 'x';
1482:
1483:     int o = you.visible_igrd(you.pos());
1484:     const int num_items = count_movable_items(o);
1485:
1486:     // Store last_pickup in case we need to restore it.
1487:     // Then clear it to fill with items picked up.
1488:     map<int,int> tmp_l_p = you.last_pickup;
1489:     you.last_pickup.clear();
1490:
1491:     if (o == NON_ITEM)
1492:         mpr(T_("There are no items here."));
1493:     else if (num_items == 1) // just one movable item?
1494:     {
1495:         // Get the link to the movable item in the pile.
1496:         while (item_is_stationary(env.item[o]))
1497:             o = env.item[o].link;
1498:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1499:     }
1500:     else if (Options.pickup_menu_limit
1501:              && num_items > (Options.pickup_menu_limit > 0
1502:                              ? Options.pickup_menu_limit
1503:                              : Options.item_stack_summary_minimum - 1))
1504:     {
1505:         pickup_menu(o);
1506:     }
1507:     else
1508:     {
1509:         int next;
1510:         if (num_items == 0)
1511:             mpr(T_("There are no objects that can be picked up here."));
1512:         else
1513:             mpr(T_("There are several objects here."));
1514:         string pickup_warning;
```

D-HERE-46 stable
```cpp
1523:     you.last_pickup.clear();
1524:
1525:     if (o == NON_ITEM)
1526:         mpr(T_("There are no items here."));
1527:     else if (num_items == 1) // just one movable item?
1528:     {
1529:         // Get the link to the movable item in the pile.
1530:         while (item_is_stationary(env.item[o]))
1531:             o = env.item[o].link;
1532:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1533:     }
1534:     else if (Options.pickup_menu_limit
1535:              && num_items > (Options.pickup_menu_limit > 0
1536:                              ? Options.pickup_menu_limit
1537:                              : Options.item_stack_summary_minimum - 1))
1538:     {
1539:         pickup_menu(o);
1540:     }
1541:     else
1542:     {
1543:         int next;
1544:         if (num_items == 0)
1545:             mpr(T_("There are no objects that can be picked up here."));
1546:         else
1547:             mpr(T_("There are several objects here."));
1548:         string pickup_warning;
1549:         bool any_selectable = false;
1550:         while (o != NON_ITEM)
1551:         {
1552:             // Must save this because pickup can destroy the item.
1553:             next = env.item[o].link;
1554:
1555:             if (item_is_stationary(env.item[o]))
1556:             {
1557:                 o = next;
1558:                 continue;
1559:             }
1560:             any_selectable = true;
1561:
1562:             if (keyin != 'a')
1563:             {
1564:                 string prompt = T_("Pick up %s? ((y)es/(n)o/(a)ll/(m)enu/*?g,/q)");
1565:
1566:                 mprf(MSGCH_PROMPT, prompt.c_str(),
1567:                      menu_colour_item_name(env.item[o], DESC_A).c_str());
```

D-HERE-46 trunk
```cpp
1489:     you.last_pickup.clear();
1490:
1491:     if (o == NON_ITEM)
1492:         mpr(T_("There are no items here."));
1493:     else if (num_items == 1) // just one movable item?
1494:     {
1495:         // Get the link to the movable item in the pile.
1496:         while (item_is_stationary(env.item[o]))
1497:             o = env.item[o].link;
1498:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1499:     }
1500:     else if (Options.pickup_menu_limit
1501:              && num_items > (Options.pickup_menu_limit > 0
1502:                              ? Options.pickup_menu_limit
1503:                              : Options.item_stack_summary_minimum - 1))
1504:     {
1505:         pickup_menu(o);
1506:     }
1507:     else
1508:     {
1509:         int next;
1510:         if (num_items == 0)
1511:             mpr(T_("There are no objects that can be picked up here."));
1512:         else
1513:             mpr(T_("There are several objects here."));
1514:         string pickup_warning;
1515:         bool any_selectable = false;
1516:         while (o != NON_ITEM)
1517:         {
1518:             // Must save this because pickup can destroy the item.
1519:             next = env.item[o].link;
1520:
1521:             if (item_is_stationary(env.item[o]))
1522:             {
1523:                 o = next;
1524:                 continue;
1525:             }
1526:             any_selectable = true;
1527:
1528:             if (keyin != 'a')
1529:             {
1530:                 string prompt = T_("Pick up %s? ((y)es/(n)o/(a)ll/(m)enu/*?g,/q)");
1531:
1532:                 mprf(MSGCH_PROMPT, prompt.c_str(),
1533:                      menu_colour_item_name(env.item[o], DESC_A).c_str());
```

D-HERE-47 stable
```cpp
1428:
1429: void trog_do_trogs_hand(int pow)
1430: {
1431:     you.increase_duration(DUR_TROGS_HAND,
1432:                           5 + roll_dice(2, pow / 3 + 1), 100,
1433:                           T_("Your skin crawls."));
1434:     mprf(MSGCH_DURATION, T_("You feel resolute."));
1435: }
1436:
1437: void trog_remove_trogs_hand()
1438: {
1439:     mprf(MSGCH_DURATION, T_("Your skin stops tingling."));
1440:     mprf(MSGCH_DURATION, T_("You feel less resolute."));
1441:     you.duration[DUR_TROGS_HAND] = 0;
1442: }
1443:
1444: // Return whether the player can light the torch on their current floor
1445: // (ie: it is a valid place to do so and it has never been lit here before)
1446: string yred_cannot_light_torch_reason()
1447: {
1448:     // First check invalid locations
1449:     if (player_in_branch(BRANCH_TEMPLE))
1450:         return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");
1451:     else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
1452:         return T_("There are no souls worth scouring here.");
1453:     else if (player_in_branch(BRANCH_ABYSS))
1454:         return T_("Not even a god could conquer a realm without end; waste no time trying.");
1455:
1456:     if (!you.props.exists(YRED_TORCH_USED_KEY))
1457:         return "";
1458:
1459:     CrawlHashTable &levels = you.props[YRED_TORCH_USED_KEY].get_table();
1460:     if (levels.exists(level_id::current().describe()))
1461:         return T_("You have raised the torch once already on this floor. Yredelemnul offers no second chances.");
1462:
1463:     return "";
1464: }
1465:
1466: bool yred_light_the_torch()
1467: {
1468:     mprf(T_("You hold the Black Torch high and begin your conquest of %s in Yredelemnul's name!"),
1469:          level_id::current().describe(true, true).c_str());
1470:
1471:     // Determine number of torch charges based on piety stars.
1472:     // Note: You are given 'hidden' internal torchlight charges even below the
```

D-HERE-47 trunk
```cpp
1519:                                                 MONS_CYCLOPS,
1520:                                                 MONS_DEATH_YAK,
1521:                                                 MONS_TWO_HEADED_OGRE,
1522:                                                 MONS_DEEP_TROLL,
1523:                                                 MONS_IRON_TROLL,
1524:                                                 MONS_STONE_GIANT,
1525:                                                 MONS_ETTIN };
1526:     if (!player_summon_check(types))
1527:         return spret::abort;
1528:
1529:     fail_check();
1530:
1531:     summon_berserker(&you, trog_get_brother_type(you.experience_level));
1532:     return spret::success;
1533: }
1534:
1535: // Return whether the player can light the torch on their current floor
1536: // (ie: it is a valid place to do so and it has never been lit here before)
1537: string yred_cannot_light_torch_reason()
1538: {
1539:     // First check invalid locations
1540:     if (player_in_branch(BRANCH_TEMPLE))
1541:         return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");
1542:     else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
1543:         return T_("There are no souls worth scouring here.");
1544:     else if (player_in_branch(BRANCH_ABYSS))
1545:         return T_("Not even a god could conquer a realm without end; waste no time trying.");
1546:
1547:     if (!you.props.exists(YRED_TORCH_USED_KEY))
1548:         return "";
1549:
1550:     CrawlHashTable &levels = you.props[YRED_TORCH_USED_KEY].get_table();
1551:     if (levels.exists(level_id::current().describe()))
1552:         return T_("You have raised the torch once already on this floor. Yredelemnul offers no second chances.");
1553:
1554:     return "";
1555: }
1556:
1557: bool yred_light_the_torch()
1558: {
1559:     mprf(T_("You hold the Black Torch high and begin your conquest of %s in Yredelemnul's name!"),
1560:          level_id::current().describe(true, true).c_str());
1561:
1562:     // Determine number of torch charges based on piety stars.
1563:     // Note: You are given 'hidden' internal torchlight charges even below the
```

D-HERE-48 stable
```cpp
1430: {
1431:     you.increase_duration(DUR_TROGS_HAND,
1432:                           5 + roll_dice(2, pow / 3 + 1), 100,
1433:                           T_("Your skin crawls."));
1434:     mprf(MSGCH_DURATION, T_("You feel resolute."));
1435: }
1436:
1437: void trog_remove_trogs_hand()
1438: {
1439:     mprf(MSGCH_DURATION, T_("Your skin stops tingling."));
1440:     mprf(MSGCH_DURATION, T_("You feel less resolute."));
1441:     you.duration[DUR_TROGS_HAND] = 0;
1442: }
1443:
1444: // Return whether the player can light the torch on their current floor
1445: // (ie: it is a valid place to do so and it has never been lit here before)
1446: string yred_cannot_light_torch_reason()
1447: {
1448:     // First check invalid locations
1449:     if (player_in_branch(BRANCH_TEMPLE))
1450:         return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");
1451:     else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
1452:         return T_("There are no souls worth scouring here.");
1453:     else if (player_in_branch(BRANCH_ABYSS))
1454:         return T_("Not even a god could conquer a realm without end; waste no time trying.");
1455:
1456:     if (!you.props.exists(YRED_TORCH_USED_KEY))
1457:         return "";
1458:
1459:     CrawlHashTable &levels = you.props[YRED_TORCH_USED_KEY].get_table();
1460:     if (levels.exists(level_id::current().describe()))
1461:         return T_("You have raised the torch once already on this floor. Yredelemnul offers no second chances.");
1462:
1463:     return "";
1464: }
1465:
1466: bool yred_light_the_torch()
1467: {
1468:     mprf(T_("You hold the Black Torch high and begin your conquest of %s in Yredelemnul's name!"),
1469:          level_id::current().describe(true, true).c_str());
1470:
1471:     // Determine number of torch charges based on piety stars.
1472:     // Note: You are given 'hidden' internal torchlight charges even below the
1473:     // piety threshold to hurl torchlight, in case you gain that ability on the
1474:     // current floor.
```

D-HERE-48 trunk
```cpp
1521:                                                 MONS_TWO_HEADED_OGRE,
1522:                                                 MONS_DEEP_TROLL,
1523:                                                 MONS_IRON_TROLL,
1524:                                                 MONS_STONE_GIANT,
1525:                                                 MONS_ETTIN };
1526:     if (!player_summon_check(types))
1527:         return spret::abort;
1528:
1529:     fail_check();
1530:
1531:     summon_berserker(&you, trog_get_brother_type(you.experience_level));
1532:     return spret::success;
1533: }
1534:
1535: // Return whether the player can light the torch on their current floor
1536: // (ie: it is a valid place to do so and it has never been lit here before)
1537: string yred_cannot_light_torch_reason()
1538: {
1539:     // First check invalid locations
1540:     if (player_in_branch(BRANCH_TEMPLE))
1541:         return T_("There are no souls to scour here; only the pathetic idols of powerless gods.");
1542:     else if (player_in_branch(BRANCH_BAZAAR) || player_in_branch(BRANCH_TROVE))
1543:         return T_("There are no souls worth scouring here.");
1544:     else if (player_in_branch(BRANCH_ABYSS))
1545:         return T_("Not even a god could conquer a realm without end; waste no time trying.");
1546:
1547:     if (!you.props.exists(YRED_TORCH_USED_KEY))
1548:         return "";
1549:
1550:     CrawlHashTable &levels = you.props[YRED_TORCH_USED_KEY].get_table();
1551:     if (levels.exists(level_id::current().describe()))
1552:         return T_("You have raised the torch once already on this floor. Yredelemnul offers no second chances.");
1553:
1554:     return "";
1555: }
1556:
1557: bool yred_light_the_torch()
1558: {
1559:     mprf(T_("You hold the Black Torch high and begin your conquest of %s in Yredelemnul's name!"),
1560:          level_id::current().describe(true, true).c_str());
1561:
1562:     // Determine number of torch charges based on piety stars.
1563:     // Note: You are given 'hidden' internal torchlight charges even below the
1564:     // piety threshold to hurl torchlight, in case you gain that ability on the
1565:     // current floor.
```

D-HERE-49 stable
```cpp
1525:     if (o == NON_ITEM)
1526:         mpr(T_("There are no items here."));
1527:     else if (num_items == 1) // just one movable item?
1528:     {
1529:         // Get the link to the movable item in the pile.
1530:         while (item_is_stationary(env.item[o]))
1531:             o = env.item[o].link;
1532:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1533:     }
1534:     else if (Options.pickup_menu_limit
1535:              && num_items > (Options.pickup_menu_limit > 0
1536:                              ? Options.pickup_menu_limit
1537:                              : Options.item_stack_summary_minimum - 1))
1538:     {
1539:         pickup_menu(o);
1540:     }
1541:     else
1542:     {
1543:         int next;
1544:         if (num_items == 0)
1545:             mpr(T_("There are no objects that can be picked up here."));
1546:         else
1547:             mpr(T_("There are several objects here."));
1548:         string pickup_warning;
1549:         bool any_selectable = false;
1550:         while (o != NON_ITEM)
1551:         {
1552:             // Must save this because pickup can destroy the item.
1553:             next = env.item[o].link;
1554:
1555:             if (item_is_stationary(env.item[o]))
1556:             {
1557:                 o = next;
1558:                 continue;
1559:             }
1560:             any_selectable = true;
1561:
1562:             if (keyin != 'a')
1563:             {
1564:                 string prompt = T_("Pick up %s? ((y)es/(n)o/(a)ll/(m)enu/*?g,/q)");
1565:
1566:                 mprf(MSGCH_PROMPT, prompt.c_str(),
1567:                      menu_colour_item_name(env.item[o], DESC_A).c_str());
1568:
1569:                 mouse_control mc(MOUSE_MODE_YESNO);
```

D-HERE-49 trunk
```cpp
1491:     if (o == NON_ITEM)
1492:         mpr(T_("There are no items here."));
1493:     else if (num_items == 1) // just one movable item?
1494:     {
1495:         // Get the link to the movable item in the pile.
1496:         while (item_is_stationary(env.item[o]))
1497:             o = env.item[o].link;
1498:         pickup_single_item(o, partial_quantity ? 0 : env.item[o].quantity);
1499:     }
1500:     else if (Options.pickup_menu_limit
1501:              && num_items > (Options.pickup_menu_limit > 0
1502:                              ? Options.pickup_menu_limit
1503:                              : Options.item_stack_summary_minimum - 1))
1504:     {
1505:         pickup_menu(o);
1506:     }
1507:     else
1508:     {
1509:         int next;
1510:         if (num_items == 0)
1511:             mpr(T_("There are no objects that can be picked up here."));
1512:         else
1513:             mpr(T_("There are several objects here."));
1514:         string pickup_warning;
1515:         bool any_selectable = false;
1516:         while (o != NON_ITEM)
1517:         {
1518:             // Must save this because pickup can destroy the item.
1519:             next = env.item[o].link;
1520:
1521:             if (item_is_stationary(env.item[o]))
1522:             {
1523:                 o = next;
1524:                 continue;
1525:             }
1526:             any_selectable = true;
1527:
1528:             if (keyin != 'a')
1529:             {
1530:                 string prompt = T_("Pick up %s? ((y)es/(n)o/(a)ll/(m)enu/*?g,/q)");
1531:
1532:                 mprf(MSGCH_PROMPT, prompt.c_str(),
1533:                      menu_colour_item_name(env.item[o], DESC_A).c_str());
1534:
1535:                 mouse_control mc(MOUSE_MODE_YESNO);
```

D-HERE-53 stable
```cpp
2250:
2251:     case ABIL_WU_JIAN_WALLJUMP:
2252:     {
2253:         // TODO: Add check for whether there is any valid landing spot
2254:         if (you.is_nervous())
2255:             return fail(T_("You are too terrified to wall jump!"));
2256:         if (you.attribute[ATTR_HELD])
2257:         {
2258:             return fail(make_stringf(T_("You cannot wall jump while caught in a %s."),
2259:                                      you.caught_by() == CAUGHT_WEB
2260:                                          ? T_("web") : T_("net")));
2261:         }
2262:         // Is there a valid place to wall jump?
2263:         bool has_targets = false;
2264:         for (adjacent_iterator ai(you.pos()); ai; ++ai)
2265:             if (feat_can_wall_jump_against(env.grid(*ai)))
2266:             {
2267:                 has_targets = true;
2268:                 break;
2269:             }
2270:
2271:         if (!has_targets)
2272:             return fail(T_("There is nothing to wall jump against here."));
2273:         return true;
2274:     }
2275:
2276:     case ABIL_IGNIS_RISING_FLAME:
2277:         return _can_rising_flame(quiet, reason);
2278:
2279:     case ABIL_DIG:
2280:         if (form_changes_anatomy())
2281:         {
2282:             if (reason)
2283:                 *reason = T_("You can't do that in your present form.");
2284:             return false;
2285:         }
2286:         return true;
2287:
2288:     case ABIL_SIPHON_ESSENCE:
2289:         if (you.duration[DUR_SIPHON_COOLDOWN])
2290:             return fail_canned(MSG_CANNOT_DO_YET, T_("You can't do that yet."));
2291:         return true;
2292:
2293:     case ABIL_YRED_LIGHT_THE_TORCH:
2294:     {
```

D-HERE-53 stable
```cpp
6473: spret wu_jian_wall_jump_ability()
6474: {
6475:     ASSERT(!crawl_state.game_is_arena());
6476:
6477:     if (crawl_state.is_replaying_keys())
6478:     {
6479:         crawl_state.cancel_cmd_all(T_("You can't repeat a wall jump."));
6480:         return spret::abort;
6481:     }
6482:
6483:     string wj_error;
6484:     bool has_targets = false;
6485:
6486:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
6487:         if (wu_jian_can_wall_jump(*ai, wj_error))
6488:         {
6489:             has_targets = true;
6490:             break;
6491:         }
6492:
6493:     if (!has_targets)
6494:     {
6495:         mpr(T_("There is nothing to wall jump against here."));
6496:         return spret::abort;
6497:     }
6498:
6499:     if (you.is_nervous())
6500:     {
6501:         mpr(T_("You are too terrified to wall jump!"));
6502:         return spret::abort;
6503:     }
6504:
6505:     if (you.attribute[ATTR_HELD])
6506:     {
6507:         mprf(T_("You cannot wall jump while caught in a %s."), you.caught_by() == CAUGHT_WEB ? T_("web") : T_("net"));
6508:         return spret::abort;
6509:     }
6510:
6511:     // query for location:
6512:     dist beam;
6513:
6514:     while (1)
6515:     {
6516:         direction_chooser_args args;
6517:         args.restricts = DIR_TARGET;
```

D-HERE-53 trunk
```cpp
2360:
2361:     case ABIL_WU_JIAN_WALLJUMP:
2362:     {
2363:         // TODO: Add check for whether there is any valid landing spot
2364:         if (you.is_nervous())
2365:             return fail(T_("You are too terrified to wall jump!"));
2366:         if (you.attribute[ATTR_HELD])
2367:         {
2368:             return fail(make_stringf(T_("You cannot wall jump while caught in a %s."),
2369:                                      you.caught_by() == CAUGHT_WEB
2370:                                          ? T_("web") : T_("net")));
2371:         }
2372:         // Is there a valid place to wall jump?
2373:         bool has_targets = false;
2374:         for (adjacent_iterator ai(you.pos()); ai; ++ai)
2375:             if (feat_can_wall_jump_against(env.grid(*ai)))
2376:             {
2377:                 has_targets = true;
2378:                 break;
2379:             }
2380:
2381:         if (!has_targets)
2382:             return fail(T_("There is nothing to wall jump against here."));
2383:         return true;
2384:     }
2385:
2386:     case ABIL_IGNIS_RISING_FLAME:
2387:         return _can_rising_flame(quiet, reason);
2388:
2389:     case ABIL_DIG:
2390:         if (form_changes_anatomy())
2391:         {
2392:             if (reason)
2393:                 *reason = T_("You can't do that in your present form.");
2394:             return false;
2395:         }
2396:         return true;
2397:
2398:     case ABIL_SIPHON_ESSENCE:
2399:         if (you.duration[DUR_SIPHON_COOLDOWN])
2400:             return fail_canned(MSG_CANNOT_DO_YET, T_("You can't do that yet."));
2401:         return true;
2402:
2403:     case ABIL_YRED_LIGHT_THE_TORCH:
2404:     {
```

D-HERE-53 trunk
```cpp
6530: spret wu_jian_wall_jump_ability()
6531: {
6532:     ASSERT(!crawl_state.game_is_arena());
6533:
6534:     if (crawl_state.is_replaying_keys())
6535:     {
6536:         crawl_state.cancel_cmd_all(T_("You can't repeat a wall jump."));
6537:         return spret::abort;
6538:     }
6539:
6540:     string wj_error;
6541:     bool has_targets = false;
6542:
6543:     for (adjacent_iterator ai(you.pos()); ai; ++ai)
6544:         if (wu_jian_can_wall_jump(*ai, wj_error))
6545:         {
6546:             has_targets = true;
6547:             break;
6548:         }
6549:
6550:     if (!has_targets)
6551:     {
6552:         mpr(T_("There is nothing to wall jump against here."));
6553:         return spret::abort;
6554:     }
6555:
6556:     if (you.is_nervous())
6557:     {
6558:         mpr(T_("You are too terrified to wall jump!"));
6559:         return spret::abort;
6560:     }
6561:
6562:     if (you.attribute[ATTR_HELD])
6563:     {
6564:         mprf(T_("You cannot wall jump while caught in a %s."), you.caught_by() == CAUGHT_WEB ? T_("web") : T_("net"));
6565:         return spret::abort;
6566:     }
6567:
6568:     // query for location:
6569:     dist beam;
6570:
6571:     while (1)
6572:     {
6573:         direction_chooser_args args;
6574:         args.restricts = DIR_TARGET;
```

D-HERE-54 stable
```cpp
4226:             && !mons_is_projectile(mon->type))
4227:         {
4228:             friendlies = true;
4229:         }
4230:
4231:         const int range = you.pos().distance_from(*ri);
4232:         if (range <= upheaval_radius)
4233:             continue;
4234:
4235:         const int dist = grid_distance(you.pos(), *ri);
4236:
4237:         targets.push_back(*ri);
4238:         // We weight using the square of grid distance, so monsters fewer tiles
4239:         // away are more likely to be hit.
4240:         int weight = LOS_RADIUS * LOS_RADIUS + 1 - dist * dist;
4241:         if (actor_at(*ri))
4242:             weight *= 10;
4243:         weights.push_back(weight);
4244:     }
4245:
4246:     if (targets.empty())
4247:     {
4248:         mpr(T_("There isn't enough space here!"));
4249:         return spret::abort;
4250:     }
4251:
4252:     if (friendlies
4253:         && !yesno(T_("There are friendlies around; are you sure you want to hurt "
4254:                   "them?"), true, 'n'))
4255:     {
4256:         canned_msg(MSG_OK);
4257:         return spret::abort;
4258:     }
4259:
4260:     fail_check();
4261:
4262:     mprf(MSGCH_GOD, T_("Nature churns violently around you!"));
4263:
4264:     // TODO: should count get a cap proportional to targets.size()?
4265:     int count = max(1, min((int)targets.size(),
4266:                             max(you.skill_rdiv(SK_INVOCATIONS, 1, 2),
4267:                                 random2avg(you.skill(SK_INVOCATIONS, 2), 2))));
4268:
4269:     for (int i = 0; i < count; i++)
4270:     {
```

D-HERE-54 trunk
```cpp
4408:
4409:         const monster *mon = monster_at(*ri);
4410:         if (mon && mon->wont_attack() && !mon->is_firewood())
4411:             friendlies = true;
4412:
4413:         const int range = you.pos().distance_from(*ri);
4414:         if (range <= upheaval_radius)
4415:             continue;
4416:
4417:         const int dist = grid_distance(you.pos(), *ri);
4418:
4419:         targets.push_back(*ri);
4420:         // We weight using the square of grid distance, so monsters fewer tiles
4421:         // away are more likely to be hit.
4422:         int weight = LOS_RADIUS * LOS_RADIUS + 1 - dist * dist;
4423:         if (actor_at(*ri))
4424:             weight *= 10;
4425:         weights.push_back(weight);
4426:     }
4427:
4428:     if (targets.empty())
4429:     {
4430:         mpr(T_("There isn't enough space here!"));
4431:         return spret::abort;
4432:     }
4433:
4434:     if (friendlies
4435:         && !yesno(T_("There are friendlies around; are you sure you want to hurt "
4436:                   "them?"), true, 'n'))
4437:     {
4438:         canned_msg(MSG_OK);
4439:         return spret::abort;
4440:     }
4441:
4442:     fail_check();
4443:
4444:     mprf(MSGCH_GOD, T_("Nature churns violently around you!"));
4445:
4446:     // TODO: should count get a cap proportional to targets.size()?
4447:     int count = max(1, min((int)targets.size(),
4448:                             max(you.skill_rdiv(SK_INVOCATIONS, 1, 2),
4449:                                 random2avg(you.skill(SK_INVOCATIONS, 2), 2))));
4450:
4451:     for (int i = 0; i < count; i++)
4452:     {
```

D-HERE-55 stable
```cpp
2031:         return true;
2032:
2033:     case ABIL_LUGONU_CORRUPT:
2034:         return !is_level_incorruptible(quiet, reason);
2035:
2036:     case ABIL_LUGONU_ABYSS_ENTER:
2037:         if (player_in_branch(BRANCH_ABYSS))
2038:             return fail(T_("You're already here!"));
2039:         return true;
2040:
2041:     case ABIL_SIF_MUNA_FORGET_SPELL:
2042:         if (you.spell_no == 0)
2043:             return fail_canned(MSG_NO_SPELLS, T_("You don't know any spells."));
2044:         return true;
2045:
2046:     case ABIL_SIF_MUNA_DIVINE_EXEGESIS:
2047:         return can_cast_spells(quiet, reason);
2048:
2049:     case ABIL_FEDHAS_WALL_OF_BRIARS:
2050:     {
2051:         vector<coord_def> spaces = find_briar_spaces(true);
2052:         if (spaces.empty())
2053:             return fail(T_("There isn't enough space to grow briars here."));
2054:         return true;
2055:     }
2056:
2057:     case ABIL_RU_DRAW_OUT_POWER:
2058:         if (you.duration[DUR_EXHAUSTED])
2059:             return fail(T_("You're too exhausted to draw out your power."));
2060:         if (you.hp == you.hp_max && you.magic_points == you.max_magic_points
2061:             && !you.duration[DUR_CONF]
2062:             && !you.duration[DUR_SLOW]
2063:             && !you.attribute[ATTR_HELD]
2064:             && !you.petrifying()
2065:             && !you.beheld()
2066:             && !you.afraid()
2067:             && !you.is_constricted())
2068:         {
2069:             return fail(T_("You have no need to draw out power."));
2070:         }
2071:         return true;
2072:
2073:     case ABIL_RU_POWER_LEAP:
2074:         if (you.duration[DUR_EXHAUSTED])
2075:             return fail(T_("You're too exhausted to power leap."));
```

D-HERE-55 trunk
```cpp
2124:
2125:     case ABIL_LUGONU_CORRUPT:
2126:         return !is_level_incorruptible(quiet, reason);
2127:
2128:     case ABIL_LUGONU_ABYSS_ENTER:
2129:         if (player_in_branch(BRANCH_ABYSS))
2130:             return fail(T_("You're already here!"));
2131:         return true;
2132:
2133:     case ABIL_SIF_MUNA_FORGET_SPELL:
2134:         if (you.spell_no == 0)
2135:             return fail_canned(MSG_NO_SPELLS, T_("You don't know any spells."));
2136:         return true;
2137:
2138:     case ABIL_SIF_MUNA_DIVINE_EXEGESIS:
2139:     case ABIL_SIF_MUNA_REPEAT_EXEGESIS:
2140:         return can_cast_spells(quiet, false, reason);
2141:
2142:     case ABIL_FEDHAS_WALL_OF_BRIARS:
2143:     {
2144:         vector<coord_def> spaces = find_briar_spaces(true);
2145:         if (spaces.empty())
2146:             return fail(T_("There isn't enough space to grow briars here."));
2147:         return true;
2148:     }
2149:
2150:     case ABIL_RU_DRAW_OUT_POWER:
2151:         if (you.duration[DUR_EXHAUSTED])
2152:             return fail(T_("You're too exhausted to draw out your power."));
2153:         if (you.hp == you.hp_max && you.magic_points == you.max_magic_points
2154:             && !you.duration[DUR_CONF]
2155:             && !you.duration[DUR_SLOW]
2156:             && !you.attribute[ATTR_HELD]
2157:             && !you.petrifying()
2158:             && !you.beheld()
2159:             && !you.afraid()
2160:             && !you.is_constricted())
2161:         {
2162:             return fail(T_("You have no need to draw out power."));
2163:         }
2164:         return true;
2165:
2166:     case ABIL_RU_POWER_LEAP:
2167:         if (you.duration[DUR_EXHAUSTED])
2168:             return fail(T_("You're too exhausted to power leap."));
```

D-HERE-56 stable
```cpp
41:     // Then start a spread of fiant miasma that will become proper miasma a
42:     // turn later.
43:     map_cloud_spreader_marker *marker =
44:     new map_cloud_spreader_marker(target->pos(), CLOUD_FAINT_MIASMA, 7,
45:                                         random_range(18, 28), 5, 2, &you);
46:
47:     // Start the cloud at radius 1, regardless of the speed of the killing blow
48:     marker->speed_increment -= you.time_taken - 7;
49:     env.markers.add(marker);
50:     env.markers.clear_need_activate();
51:
52:     mprf(T_("Rot billows forth from %s wounds!"), target->name(DESC_ITS).c_str());
53:
54:     drain_player(75 - div_rand_round(pow * 4, 10), true, true);
55:
56:     return spret::success;
57: }
58:
59: spret kindle_blastmotes(int pow, bool fail)
60: {
61:     if (cloud_at(you.pos()))
62:     {
63:         mpr(T_("There's already a cloud here!"));
64:         return spret::abort;
65:     }
66:
67:     fail_check();
68:
69:     // Really should be per-cloud, but skeptical people are changing power
70:     // between successive blastmote casts that often.
71:     you.props[BLASTMOTE_POWER_KEY] = pow;
72:     // Longish duration to support setting up silly traps.
73:     you.props[BLASTMOTE_IMMUNE_KEY] = true;
74:     place_cloud(CLOUD_BLASTMOTES, you.pos(), random_range(20, 30), &you);
75:     mpr(T_("A cloud of volatile blastmotes flares up around you! Run!"));
76:
77:     return spret::success;
78: }
79:
80: void explode_blastmotes_at(coord_def p)
81: {
82:     // Assumes all blastmotes are created by the player.
83:     // We could fix this in future by checking the 'killer'
84:     // associated with the cloud being deleted.
85:     delete_cloud(p);
```

D-HERE-56 trunk
```cpp
47:
48:     // Then start a spread of fiant miasma that will become proper miasma a
49:     // turn later.
50:     map_cloud_spreader_marker *marker =
51:     new map_cloud_spreader_marker(target->pos(), CLOUD_FAINT_MIASMA, 7,
52:                                         random_range(18, 28), 5, 2, &you);
53:
54:     // Start the cloud at radius 1, regardless of the speed of the killing blow
55:     marker->speed_increment -= you.time_taken - 7;
56:     env.markers.add(marker);
57:
58:     mprf(T_("Rot billows forth from %s wounds!"), target->name(DESC_ITS).c_str());
59:
60:     drain_player(putrefaction_drain_amount(pow, true), true, true);
61:
62:     return spret::success;
63: }
64:
65: spret kindle_blastmotes(int pow, bool fail)
66: {
67:     if (cloud_at(you.pos()))
68:     {
69:         mpr(T_("There's already a cloud here!"));
70:         return spret::abort;
71:     }
72:
73:     fail_check();
74:
75:     // Really should be per-cloud, but skeptical people are changing power
76:     // between successive blastmote casts that often.
77:     you.props[BLASTMOTE_POWER_KEY] = pow;
78:     // Longish duration to support setting up silly traps.
79:     you.props[BLASTMOTE_IMMUNE_KEY] = true;
80:     place_cloud(CLOUD_BLASTMOTES, you.pos(), random_range(20, 30), &you);
81:     mpr(T_("A cloud of volatile blastmotes flares up around you! Run!"));
82:
83:     return spret::success;
84: }
85:
86: void explode_blastmotes_at(coord_def p)
87: {
88:     // Assumes all blastmotes are created by the player.
89:     // We could fix this in future by checking the 'killer'
90:     // associated with the cloud being deleted.
91:     delete_cloud(p);
```

D-HERE-57 stable
```cpp
3007: spret foxfire_swarm()
3008: {
3009:     bool created = false;
3010:     bool unknown_unseen = false;
3011:     for (radius_iterator ri(you.pos(), 2, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
3012:     {
3013:         if (_create_foxfire(you, *ri, 20))
3014:         {
3015:             created = true;
3016:             continue;
3017:         }
3018:         const actor* agent = actor_at(*ri);
3019:         if (agent && !you.can_see(*agent))
3020:             unknown_unseen = true;
3021:     }
3022:     if (created)
3023:     {
3024:         mpr(T_("Flames leap up around you!"));
3025:         return spret::success;
3026:     }
3027:     if (!unknown_unseen)
3028:     {
3029:         mpr(T_("There's no space to create foxfire here."));
3030:         return spret::abort;
3031:     }
3032:     canned_msg(MSG_NOTHING_HAPPENS);
3033:     return spret::fail; // don't spend piety, do spend a turn
3034: }
3035:
3036: bool summon_hell_out_of_bat(const actor &agent, coord_def pos)
3037: {
3038:     // Since this isn't really used as for a spell: count how many creatures
3039:     // this has already summoned, and abort at our max defined here (four).
3040:     int count = 0;
3041:     for (monster_iterator mi; mi; ++mi)
3042:     {
3043:        if (mi->summoner == agent.mid)
3044:            ++count;
3045:
3046:         if (count > 3)
3047:            return false;
3048:     }
3049:
3050:     monster_type mon = coinflip() ? MONS_HELL_HOUND : MONS_HELL_RAT;
3051:
```

D-HERE-57 trunk
```cpp
3092: spret foxfire_swarm()
3093: {
3094:     bool created = false;
3095:     bool unknown_unseen = false;
3096:     for (radius_iterator ri(you.pos(), 2, C_SQUARE, LOS_NO_TRANS); ri; ++ri)
3097:     {
3098:         if (_create_foxfire(you, *ri, 20))
3099:         {
3100:             created = true;
3101:             continue;
3102:         }
3103:         const actor* agent = actor_at(*ri);
3104:         if (agent && !you.can_see(*agent))
3105:             unknown_unseen = true;
3106:     }
3107:     if (created)
3108:     {
3109:         mpr(T_("Flames leap up around you!"));
3110:         return spret::success;
3111:     }
3112:     if (!unknown_unseen)
3113:     {
3114:         mpr(T_("There's no space to create foxfire here."));
3115:         return spret::abort;
3116:     }
3117:     canned_msg(MSG_NOTHING_HAPPENS);
3118:     return spret::fail; // don't spend piety, do spend a turn
3119: }
3120:
3121: bool summon_hell_out_of_bat(const actor &agent, coord_def pos)
3122: {
3123:     // Since this isn't really used as for a spell: count how many creatures
3124:     // this has already summoned, and abort at our max defined here (four).
3125:     int count = 0;
3126:     for (monster_iterator mi; mi; ++mi)
3127:     {
3128:        if (mi->summoner == agent.mid)
3129:            ++count;
3130:
3131:         if (count > 3)
3132:            return false;
3133:     }
3134:
3135:     monster_type mon = coinflip() ? MONS_HELL_HOUND : MONS_HELL_RAT;
3136:
```

D-HERE-58 stable
```cpp
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
968:             }
969:         }
970:     }
```

D-HERE-58 trunk
```cpp
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
961:             if (it->base_type == OBJ_CORPSES)
962:                 continue;
963:
964:             if (++count > 1)
965:             {
966:                 learned_something_new(HINT_MULTI_PICKUP);
967:                 break;
968:             }
969:         }
970:     }
```

D-HERE-59 stable
```cpp
314:     // If it's not in the game, use the default parent.
315:     return branches[branch].parent_branch;
316: }
317:
318: vector<branch_type> descent_parents(branch_type branch)
319: {
320:     return branches[branch].descent_parents;
321: }
322:
323: /**
324:  * Describe the ambient noise level in this branch.
325:  *
326:  * @param branch The branch in question.
327:  * @returns      A string describing how noisy or quiet the branch is.
328:  */
329: string branch_noise_desc(branch_type br)
330: {
331:     string desc;
332:     const int noise = ambient_noise(br);
333:     if (noise != 0)
334:     {
335:         if (noise > 0)
336:             desc = T_("This branch is noisy: sounds don't travel as far here.");
337:         else
338:             desc = T_("This branch is unnaturally silent: sounds travel farther here.");
339:     }
340:
341:     return desc;
342: }
343:
344: /**
345:  * Write a description of the rune(s), if any, this branch contains.
346:  *
347:  * @param br             the branch in question
348:  * @param remaining_only whether to only mention a rune if the player
349:  *                       hasn't picked it up yet.
350:  * @returns a string mentioning all applicable runes.
351:  */
352: string branch_rune_desc(branch_type br, bool remaining_only)
353: {
354:     string desc;
355:     vector<string> rune_names;
356:
357:     for (rune_type rune : branches[br].runes)
358:         if (!(remaining_only && you.runes[rune]))
```

D-HERE-59 trunk
```cpp
319:     // If it's not in the game, use the default parent.
320:     return branches[branch].parent_branch;
321: }
322:
323: vector<branch_type> descent_parents(branch_type branch)
324: {
325:     return branches[branch].descent_parents;
326: }
327:
328: /**
329:  * Describe the ambient noise level in this branch.
330:  *
331:  * @param branch The branch in question.
332:  * @returns      A string describing how noisy or quiet the branch is.
333:  */
334: string branch_noise_desc(branch_type br)
335: {
336:     string desc;
337:     const int noise = ambient_noise(br);
338:     if (noise != 0)
339:     {
340:         if (noise > 0)
341:             desc = T_("This branch is noisy: sounds don't travel as far here.");
342:         else
343:             desc = T_("This branch is unnaturally silent: sounds travel farther here.");
344:     }
345:
346:     return desc;
347: }
348:
349: /**
350:  * Write a description of the rune(s), if any, this branch contains.
351:  *
352:  * @param br             the branch in question
353:  * @param remaining_only whether to only mention a rune if the player
354:  *                       hasn't picked it up yet.
355:  * @returns a string mentioning all applicable runes.
356:  */
357: string branch_rune_desc(branch_type br, bool remaining_only)
358: {
359:     string desc;
360:     vector<string> rune_names;
361:
362:     for (rune_type rune : branches[br].runes)
363:         if (!(remaining_only && you.runes[rune]))
```

D-HERE-60 stable
```cpp
316: }
317:
318: vector<branch_type> descent_parents(branch_type branch)
319: {
320:     return branches[branch].descent_parents;
321: }
322:
323: /**
324:  * Describe the ambient noise level in this branch.
325:  *
326:  * @param branch The branch in question.
327:  * @returns      A string describing how noisy or quiet the branch is.
328:  */
329: string branch_noise_desc(branch_type br)
330: {
331:     string desc;
332:     const int noise = ambient_noise(br);
333:     if (noise != 0)
334:     {
335:         if (noise > 0)
336:             desc = T_("This branch is noisy: sounds don't travel as far here.");
337:         else
338:             desc = T_("This branch is unnaturally silent: sounds travel farther here.");
339:     }
340:
341:     return desc;
342: }
343:
344: /**
345:  * Write a description of the rune(s), if any, this branch contains.
346:  *
347:  * @param br             the branch in question
348:  * @param remaining_only whether to only mention a rune if the player
349:  *                       hasn't picked it up yet.
350:  * @returns a string mentioning all applicable runes.
351:  */
352: string branch_rune_desc(branch_type br, bool remaining_only)
353: {
354:     string desc;
355:     vector<string> rune_names;
356:
357:     for (rune_type rune : branches[br].runes)
358:         if (!(remaining_only && you.runes[rune]))
359:             rune_names.push_back(rune_type_name(rune));
360:
```

D-HERE-60 trunk
```cpp
321: }
322:
323: vector<branch_type> descent_parents(branch_type branch)
324: {
325:     return branches[branch].descent_parents;
326: }
327:
328: /**
329:  * Describe the ambient noise level in this branch.
330:  *
331:  * @param branch The branch in question.
332:  * @returns      A string describing how noisy or quiet the branch is.
333:  */
334: string branch_noise_desc(branch_type br)
335: {
336:     string desc;
337:     const int noise = ambient_noise(br);
338:     if (noise != 0)
339:     {
340:         if (noise > 0)
341:             desc = T_("This branch is noisy: sounds don't travel as far here.");
342:         else
343:             desc = T_("This branch is unnaturally silent: sounds travel farther here.");
344:     }
345:
346:     return desc;
347: }
348:
349: /**
350:  * Write a description of the rune(s), if any, this branch contains.
351:  *
352:  * @param br             the branch in question
353:  * @param remaining_only whether to only mention a rune if the player
354:  *                       hasn't picked it up yet.
355:  * @returns a string mentioning all applicable runes.
356:  */
357: string branch_rune_desc(branch_type br, bool remaining_only)
358: {
359:     string desc;
360:     vector<string> rune_names;
361:
362:     for (rune_type rune : branches[br].runes)
363:         if (!(remaining_only && you.runes[rune]))
364:             rune_names.push_back(rune_type_name(rune));
365:
```

D-HERE-61 stable
```cpp
2591:                     "(<w>X</w>) with <w>ee</w> while your cursor is on the "
2592:                     "grid in question. Such an exclusion will prevent "
2593:                     "autotravel from ever entering that grid until you "
2594:                     "remove the exclusion with another press of <w>Xe</w>.");
2595:         }
2596:         break;
2597:
2598:     default:
2599:         if (feat_is_altar(feat))
2600:         {
2601:             god_type altar_god = feat_altar_god(feat);
2602:
2603:             // TODO: mention Gozag here?
2604:             if (you_worship(GOD_NO_GOD))
2605:             {
2606:                 ostr << T_("This is your chance to join a religion! In "
2607:                         "general, the gods will help their followers, "
2608:                         "bestowing powers of all sorts upon them, but many "
2609:                         "of them demand a life of dedication, constant "
2610:                         "tributes or entertainment in return.\n");
2611:                 if (altar_god == GOD_ECUMENICAL)
2612:                 {
2613:                     ostr << T_("This particular altar is so ancient that you "
2614:                             "cannot make out which god it is dedicated to! "
2615:                             "Converting here by pressing <w>></w> while "
2616:                             "standing on the altar will enter you into service "
2617:                             "of a random god, who will grant you some "
2618:                             "additional piety in thanks.");
2619:                 }
2620:                 else
2621:                 {
2622:                     ostr << T_("You can get information about <w>")
2623:                          << god_name(altar_god)
2624:                          << T_("</w> by pressing <w>></w> while standing on the "
2625:                             "altar. Before taking up the responding faith "
2626:                             "you'll be asked for confirmation.");
2627:                 }
2628:             }
2629:             else if (you_worship(altar_god))
2630:             {
2631:                 // If we don't have anything to say, return early.
2632:                 return;
2633:             }
2634:             else if (altar_god == GOD_ECUMENICAL)
2635:             {
2636:                 ostr << T_("This particular altar is so ancient that you cannot "
2637:                         "make out which god it is dedicated to, and ")
2638:                      << god_name(you.religion)
2639:                      << T_(" probably won't like it if you switch allegiance. If "
2640:                         "you want to take the risk, you can convert here by "
```

D-HERE-62 stable
```cpp
1915:                           "to shoot at it. If you miss, <w>%s</w> fires at the same "
1916:                           "target again."), key)
1917:         : make_stringf(T_("You'll then be taken to target mode with the nearest "
1918:                           "monster or previous target already targeted. You can "
1919:                           "also cycle through all hostile monsters in sight with "
1920:                           "<w>+</w> or <w>-</w>. Once you're aiming at the correct "
1921:                           "monster, simply hit <w>f</w>, <w>Enter</w> or <w>.</w> "
1922:                           "to shoot at it. To throw this item again, press <w>%s</w> "
1923:                           "to reopen the item menu, select the item, then select a "
1924:                           "target."), key);
1925:     insert_commands(result, { cmd });
1926:
1927:     return result;
1928: }
1929:
1930: string hints_memorise_info()
1931: {
1932:     // TODO: this should probably be in z or I, but adding it to the memorise
1933:     // menu was easier for the moment.
1934:     ostringstream text;
1935:     vector<command_type> cmd;
1936:     text << "<" << colour_to_str(channel_to_colour(MSGCH_TUTORIAL)) << ">";
1937:     string m = T_("This screen shows the spells in your spell library. From here "
1938:                "you can memorise spells by selecting them, as well as view "
1939:                "spell descriptions, search for them, and organize them. As a "
1940:                "conjurer, you start with Magic Dart already memorised and three "
1941:                "other spells in your library, which you can memorise when you "
1942:                "meet their requirements. (To view memorised spells, you can "
1943:                "exit this menu and select <w>I</w>.)");
1944:
1945:     if (player_has_available_spells())
1946:     {
1947:         m += T_("\n\nA spell that isn't <darkgray>grayed out</darkgray> or "
1948:              "<lightred>forbidden</lightred> can be memorised right away by "
1949:              "selecting it at this menu.");
1950:     }
1951:     else if (you.spell_no)
1952:     {
1953:         m += T_("\n\nYou cannot memorise any more spells right now. This will "
1954:              "change as you grow in levels and Spellcasting proficiency.");
1955:     }
1956:     else
1957:     {
1958:         m += T_("\n\nYou cannot memorise any spells right now. This will change "
1959:              "as you grow in levels and Spellcasting proficiency.");
1960:     }
1961:
1962:     if (you.spell_no)
1963:     {
1964: #ifdef USE_TILE
1965:         m += T_("\n\nTo use magic, you can <w>left mouse click</w> on the monster "
```

D-HERE-63 stable
```cpp
196:     { BRANCH_COCYTUS, BRANCH_VESTIBULE, 1, 1, 7, 28,
197:       brflag::no_items | brflag::dangerous_end,
198:       DNGN_ENTER_COCYTUS, DNGN_EXIT_COCYTUS, DNGN_EXIT_COCYTUS,
199:       "Cocytus", "Cocytus", "Coc",
200:       "Your potions freeze solid in the terrible cold.",
201:       LIGHTBLUE, LIGHTCYAN,
202:       'X', { RUNE_COCYTUS }, branch_noise::normal, HELL_MON_DIE_SIZE,
203:       {BRANCH_VESTIBULE}},
204:
205:     { BRANCH_TARTARUS, BRANCH_VESTIBULE, 1, 1, 7, 28,
206:       brflag::no_items | brflag::dangerous_end,
207:       DNGN_ENTER_TARTARUS, DNGN_EXIT_TARTARUS, DNGN_EXIT_TARTARUS,
208:       "Tartarus", "Tartarus", "Tar",
209:       "This decaying realm drains your will.",
210:       MAGENTA, MAGENTA,
211:       'Y', { RUNE_TARTARUS }, branch_noise::normal, HELL_MON_DIE_SIZE,
212:       {BRANCH_VESTIBULE} },
213:
214:     { BRANCH_ZOT, BRANCH_DEPTHS, 4, 4, 5, 27,
215:       brflag::dangerous_end,
216:       DNGN_ENTER_ZOT, DNGN_EXIT_ZOT, NUM_FEATURES,
217:       "Zot", "the Realm of Zot", "Zot",
218:       "Welcome to the Realm of Zot!\n"
219:       "You feel the power of the Orb interfering with translocations here.",
220:       BLACK, BLACK, // set per-map
221:       'Z', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
222:       {BRANCH_DEPTHS} },
223: #if TAG_MAJOR_VERSION == 34
224:
225:     { BRANCH_FOREST, BRANCH_VAULTS, 2, 3, 5, 19,
226:       brflag::spotty,
227:       DNGN_ENTER_FOREST, DNGN_EXIT_FOREST, NUM_FEATURES,
228:       "Forest", "the Enchanted Forest", "Forest",
229:       nullptr,
230:       BROWN, BROWN,
231:       'F', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
232:       {} },
233: #endif
234:
235:     { BRANCH_ABYSS, NUM_BRANCHES, -1, -1, 7, 24,
236:       brflag::no_x_level_travel | brflag::no_map | brflag::no_items,
237:       DNGN_ENTER_ABYSS, DNGN_EXIT_ABYSS, DNGN_FLOOR, // can't get trapped in abyss
238:       "Abyss", "the Abyss", "Abyss",
239:       nullptr,
240:       BLACK, BLACK, // set specially
241:       'J', { RUNE_ABYSSAL }, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
242:       {} },
243:
244:     { BRANCH_PANDEMONIUM, NUM_BRANCHES, -1, -1, 1, 24,
245:       brflag::no_x_level_travel,
246:       DNGN_ENTER_PANDEMONIUM, DNGN_EXIT_PANDEMONIUM, DNGN_TRANSIT_PANDEMONIUM,
247:       "Pandemonium", "Pandemonium", "Pan",
248:       "You enter the halls of Pandemonium!\n"
249:       "To return, you must find a gate leading back.",
250:       BLACK, BLACK, // set specially
251:       'R', { RUNE_DEMONIC, RUNE_MNOLEG, RUNE_LOM_LOBON, RUNE_CEREBOV,
252:              RUNE_GLOORX_VLOQ }, branch_noise::normal, 8,
253:       {} },
254:
255:     { BRANCH_ZIGGURAT, BRANCH_DEPTHS, 1, 4, 27, 27,
256:       brflag::no_x_level_travel | brflag::no_items,
257:       DNGN_ENTER_ZIGGURAT, DNGN_EXIT_ZIGGURAT, DNGN_FLOOR,
258:       "Ziggurat", "a ziggurat", "Zig",
259:       "You land on top of a ziggurat so tall you cannot make out the ground.",
260:       BLACK, BLACK,
261:       'Q', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
262:       {} },
263: #if TAG_MAJOR_VERSION == 34
264:
265:     { BRANCH_LABYRINTH, NUM_BRANCHES, -1, -1, 1, 15,
266:       brflag::no_x_level_travel | brflag::no_items,
267:       DNGN_ENTER_LABYRINTH, DNGN_EXIT_LABYRINTH, DNGN_EXIT_THROUGH_ABYSS,
268:       "Labyrinth", "a Labyrinth", "Lab",
269:       "You enter a labyrinth!",
270:       BLACK, BLACK,
271:       '0', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
272:       {} },
273: #endif
274:
275:     { BRANCH_BAZAAR, NUM_BRANCHES, -1, -1, 1, 18,
276:       brflag::no_x_level_travel | brflag::no_items,
277:       DNGN_ENTER_BAZAAR, DNGN_EXIT_BAZAAR, NUM_FEATURES,
278:       "Bazaar", "a bazaar", "Bazaar",
279:       "You enter an inter-dimensional bazaar!",
280:       BLUE, YELLOW,
281:       '1', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
282:       {} },
283:
284:     { BRANCH_TROVE, NUM_BRANCHES, -1, -1, 1, 18,
285:       brflag::no_x_level_travel | brflag::no_items,
286:       DNGN_ENTER_TROVE, DNGN_EXIT_TROVE, NUM_FEATURES,
287:       "Trove", "a treasure trove", "Trove",
288:       "You enter a treasure trove!",
289:       DARKGREY, BLUE,
290:       '2', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
291:       {} },
292:
293:     { BRANCH_SEWER, NUM_BRANCHES, -1, -1, 1, 4,
294:       brflag::no_x_level_travel | brflag::no_items,
295:       DNGN_ENTER_SEWER, DNGN_EXIT_SEWER, NUM_FEATURES,
296:       "Sewer", "a sewer", "Sewer",
297:       "You enter a sewer!",
298:       LIGHTGREY, BLUE,
299:       '3', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
300:       {} },
301:
302:     { BRANCH_OSSUARY, NUM_BRANCHES, -1, -1, 1, 6,
303:       brflag::no_x_level_travel | brflag::no_items,
304:       DNGN_ENTER_OSSUARY, DNGN_EXIT_OSSUARY, NUM_FEATURES,
305:       "Ossuary", "an ossuary", "Ossuary",
306:       "You enter an ossuary!",
307:       WHITE, YELLOW,
308:       '4', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
309:       {} },
310:
311:     { BRANCH_BAILEY, NUM_BRANCHES, -1, -1, 1, 11,
312:       brflag::no_x_level_travel | brflag::no_items,
313:       DNGN_ENTER_BAILEY, DNGN_EXIT_BAILEY, NUM_FEATURES,
314:       "Bailey", "a bailey", "Bailey",
315:       "You enter a bailey!",
316:       WHITE, LIGHTRED,
317:       '5', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
318:       {} },
319: #if TAG_MAJOR_VERSION > 34
320:
321:     { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
322:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
323:       DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
324:       "Gauntlet", "a Gauntlet", "Gauntlet",
325:       "You enter a gauntlet!",
326:       BLACK, BLACK,
327:       '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
328:       {} },
329: #endif
330:
331:     { BRANCH_ICE_CAVE, NUM_BRANCHES, -1, -1, 1, 15,
332:       brflag::no_x_level_travel | brflag::no_items,
333:       DNGN_ENTER_ICE_CAVE, DNGN_EXIT_ICE_CAVE, NUM_FEATURES,
334:       "Ice Cave", "an ice cave", "IceCv",
335:       "You enter an ice cave!",
336:       BLUE, WHITE,
337: #if TAG_MAJOR_VERSION == 34
338:       '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
339:       {} },
340: #endif
341: #if TAG_MAJOR_VERSION > 34
342:       '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
343:       {} },
344: #endif
345:
346:     { BRANCH_VOLCANO, NUM_BRANCHES, -1, -1, 1, 14,
347:       brflag::no_x_level_travel | brflag::no_items,
348:       DNGN_ENTER_VOLCANO, DNGN_EXIT_VOLCANO, NUM_FEATURES,
349:       "Volcano", "a volcano", "Volcano",
350:       "You enter a volcano!",
351:       RED, RED,
352: #if TAG_MAJOR_VERSION == 34
353:       '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
354:       {} },
355: #endif
356: #if TAG_MAJOR_VERSION > 34
357:       '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
358:       {} },
359: #endif
360:
361:     { BRANCH_WIZLAB, NUM_BRANCHES, -1, -1, 1, 24,
362:       brflag::no_x_level_travel | brflag::no_items,
363:       DNGN_ENTER_WIZLAB, DNGN_EXIT_WIZLAB, NUM_FEATURES,
364:       "Wizlab", "a wizard's laboratory", "WizLab",
365:       "You enter a wizard's laboratory!",
366:       LIGHTGREY, BROWN, // set per-map
367: #if TAG_MAJOR_VERSION == 34
368:       '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
369:       {} },
370: #endif
371: #if TAG_MAJOR_VERSION > 34
372:       '9', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
373:       {} },
374: #endif
375: #if TAG_MAJOR_VERSION == 34
376:
377:     { BRANCH_DEPTHS, BRANCH_DUNGEON, 15, 15, 4, 22,
378:       brflag::none,
379:       DNGN_ENTER_DEPTHS, DNGN_EXIT_DEPTHS, NUM_FEATURES,
380:       "Depths", "the Depths", "Depths",
381:       nullptr,
382:       LIGHTGREY, BROWN,
383:       'U', {}, branch_noise::normal, 10,
384:       {BRANCH_VAULTS, BRANCH_SLIME} },
385: #endif
386:
387:     { BRANCH_DESOLATION, NUM_BRANCHES, -1, -1, 1, 20,
388:       brflag::no_x_level_travel | brflag::no_items,
389:       DNGN_ENTER_DESOLATION, DNGN_EXIT_DESOLATION, NUM_FEATURES, // TODO
390:       "Desolation", "the Desolation of Salt", "Desolation",
391:       "You enter a great desolation of salt!",
392:       LIGHTGREY, BROWN, // TODO
393: #if TAG_MAJOR_VERSION == 34
394:       '9', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
395:       {} },
396: #endif
397: #if TAG_MAJOR_VERSION > 34
398:       '0', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
399:       {} },
400: #endif
401: #if TAG_MAJOR_VERSION == 34
402:
403:     { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
404:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
405:       DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
406:       "Gauntlet", "a Gauntlet", "Gauntlet",
407:       "You enter a gauntlet!",
408:       BLACK, BLACK,
409:       '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
410:       {} },
411: #endif
412:
413:     { BRANCH_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
414:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
415:       DNGN_ENTER_ARENA, DNGN_EXIT_ARENA, NUM_FEATURES,
416:       "Arena", "the Arena", "Arena",
417:       "You enter Okawaru's Arena!",
418:       BLACK, BLACK,
419: #if TAG_MAJOR_VERSION == 34
420:       '"', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
421:       {} },
422: #else
423:       '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
424:       {} },
425: #endif
426:
427:     { BRANCH_CRUCIBLE, NUM_BRANCHES, -1, -1, 1, 0,
428:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
429:       DNGN_ENTER_CRUCIBLE, DNGN_EXIT_CRUCIBLE, NUM_FEATURES,
430:       "Crucible", "the Crucible of Flesh", "Crucible",
431:       "You are dragged down into the Crucible of Flesh!",
432:       BLACK, BLACK,
433:       '@', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
434:       {}
435:     },
436:
437:     { BRANCH_NECROPOLIS, NUM_BRANCHES, -1, -1, 1, 0,
438:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
439:       DNGN_ENTER_NECROPOLIS, DNGN_EXIT_NECROPOLIS, NUM_FEATURES,
440:       "Necropolis", "the Necropolis", "Necropolis",
441:       "You enter an ornate necropolis!",
442:       MAGENTA, LIGHTGREY,
443:       '%', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
444:       {}
445:     },
446: };
447:
448: /*
449:  * There's a few more constant data structures related to branches in
450:  * the early parts of branch.cc (Example: danger_branch_order)
451:  */
```

D-HERE-63 trunk
```cpp
196:     { BRANCH_COCYTUS, BRANCH_VESTIBULE, 1, 1, 7, 28,
197:       brflag::no_items | brflag::dangerous_end,
198:       DNGN_ENTER_COCYTUS, DNGN_EXIT_COCYTUS, DNGN_EXIT_COCYTUS,
199:       "Cocytus", "Cocytus", "Coc",
200:       "Your potions freeze solid in the terrible cold.",
201:       LIGHTBLUE, LIGHTCYAN,
202:       'X', { RUNE_COCYTUS }, branch_noise::normal, HELL_MON_DIE_SIZE,
203:       {BRANCH_VESTIBULE}},
204:
205:     { BRANCH_TARTARUS, BRANCH_VESTIBULE, 1, 1, 7, 28,
206:       brflag::no_items | brflag::dangerous_end,
207:       DNGN_ENTER_TARTARUS, DNGN_EXIT_TARTARUS, DNGN_EXIT_TARTARUS,
208:       "Tartarus", "Tartarus", "Tar",
209:       "This decaying realm drains your will.",
210:       MAGENTA, MAGENTA,
211:       'Y', { RUNE_TARTARUS }, branch_noise::normal, HELL_MON_DIE_SIZE,
212:       {BRANCH_VESTIBULE} },
213:
214:     { BRANCH_ZOT, BRANCH_DEPTHS, 4, 4, 5, 27,
215:       brflag::dangerous_end,
216:       DNGN_ENTER_ZOT, DNGN_EXIT_ZOT, NUM_FEATURES,
217:       "Zot", "the Realm of Zot", "Zot",
218:       "Welcome to the Realm of Zot!\n"
219:       "You feel the power of the Orb interfering with translocations here.",
220:       BLACK, BLACK, // set per-map
221:       'Z', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
222:       {BRANCH_DEPTHS} },
223: #if TAG_MAJOR_VERSION == 34
224:
225:     { BRANCH_FOREST, BRANCH_VAULTS, 2, 3, 5, 19,
226:       brflag::spotty,
227:       DNGN_ENTER_FOREST, DNGN_EXIT_FOREST, NUM_FEATURES,
228:       "Forest", "the Enchanted Forest", "Forest",
229:       nullptr,
230:       BROWN, BROWN,
231:       'F', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
232:       {} },
233: #endif
234:
235:     { BRANCH_ABYSS, NUM_BRANCHES, -1, -1, 7, 24,
236:       brflag::no_x_level_travel | brflag::no_map | brflag::no_items,
237:       DNGN_ENTER_ABYSS, DNGN_EXIT_ABYSS, DNGN_FLOOR, // can't get trapped in abyss
238:       "Abyss", "the Abyss", "Abyss",
239:       nullptr,
240:       BLACK, BLACK, // set specially
241:       'J', { RUNE_ABYSSAL }, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
242:       {} },
243:
244:     { BRANCH_PANDEMONIUM, NUM_BRANCHES, -1, -1, 1, 24,
245:       brflag::no_x_level_travel,
246:       DNGN_ENTER_PANDEMONIUM, DNGN_EXIT_PANDEMONIUM, DNGN_TRANSIT_PANDEMONIUM,
247:       "Pandemonium", "Pandemonium", "Pan",
248:       "You enter the halls of Pandemonium!\n"
249:       "To return, you must find a gate leading back.",
250:       BLACK, BLACK, // set specially
251:       'R', { RUNE_DEMONIC, RUNE_MNOLEG, RUNE_LOM_LOBON, RUNE_CEREBOV,
252:              RUNE_GLOORX_VLOQ }, branch_noise::normal, 8,
253:       {} },
254:
255:     { BRANCH_ZIGGURAT, BRANCH_DEPTHS, 1, 4, 27, 27,
256:       brflag::no_x_level_travel | brflag::no_items,
257:       DNGN_ENTER_ZIGGURAT, DNGN_EXIT_ZIGGURAT, DNGN_FLOOR,
258:       "Ziggurat", "a ziggurat", "Zig",
259:       "You land on top of a ziggurat so tall you cannot make out the ground.",
260:       BLACK, BLACK,
261:       'Q', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
262:       {} },
263: #if TAG_MAJOR_VERSION == 34
264:
265:     { BRANCH_LABYRINTH, NUM_BRANCHES, -1, -1, 1, 15,
266:       brflag::no_x_level_travel | brflag::no_items,
267:       DNGN_ENTER_LABYRINTH, DNGN_EXIT_LABYRINTH, DNGN_EXIT_THROUGH_ABYSS,
268:       "Labyrinth", "a Labyrinth", "Lab",
269:       "You enter a labyrinth!",
270:       BLACK, BLACK,
271:       '0', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
272:       {} },
273: #endif
274:
275:     { BRANCH_BAZAAR, NUM_BRANCHES, -1, -1, 1, 18,
276:       brflag::no_x_level_travel | brflag::no_items,
277:       DNGN_ENTER_BAZAAR, DNGN_EXIT_BAZAAR, NUM_FEATURES,
278:       "Bazaar", "a bazaar", "Bazaar",
279:       "You enter an inter-dimensional bazaar!",
280:       BLUE, YELLOW,
281:       '1', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
282:       {} },
283:
284:     { BRANCH_TROVE, NUM_BRANCHES, -1, -1, 1, 18,
285:       brflag::no_x_level_travel | brflag::no_items,
286:       DNGN_ENTER_TROVE, DNGN_EXIT_TROVE, NUM_FEATURES,
287:       "Trove", "a treasure trove", "Trove",
288:       "You enter a treasure trove!",
289:       DARKGREY, BLUE,
290:       '2', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
291:       {} },
292:
293:     { BRANCH_SEWER, NUM_BRANCHES, -1, -1, 1, 4,
294:       brflag::no_x_level_travel | brflag::no_items,
295:       DNGN_ENTER_SEWER, DNGN_EXIT_SEWER, NUM_FEATURES,
296:       "Sewer", "a sewer", "Sewer",
297:       "You enter a sewer!",
298:       LIGHTGREY, BLUE,
299:       '3', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
300:       {} },
301:
302:     { BRANCH_OSSUARY, NUM_BRANCHES, -1, -1, 1, 6,
303:       brflag::no_x_level_travel | brflag::no_items,
304:       DNGN_ENTER_OSSUARY, DNGN_EXIT_OSSUARY, NUM_FEATURES,
305:       "Ossuary", "an ossuary", "Ossuary",
306:       "You enter an ossuary!",
307:       WHITE, YELLOW,
308:       '4', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
309:       {} },
310:
311:     { BRANCH_BAILEY, NUM_BRANCHES, -1, -1, 1, 11,
312:       brflag::no_x_level_travel | brflag::no_items,
313:       DNGN_ENTER_BAILEY, DNGN_EXIT_BAILEY, NUM_FEATURES,
314:       "Bailey", "a bailey", "Bailey",
315:       "You enter a bailey!",
316:       WHITE, LIGHTRED,
317:       '5', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
318:       {} },
319: #if TAG_MAJOR_VERSION > 34
320:
321:     { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
322:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
323:       DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
324:       "Gauntlet", "a Gauntlet", "Gauntlet",
325:       "You enter a gauntlet!",
326:       BLACK, BLACK,
327:       '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
328:       {} },
329: #endif
330:
331:     { BRANCH_ICE_CAVE, NUM_BRANCHES, -1, -1, 1, 15,
332:       brflag::no_x_level_travel | brflag::no_items,
333:       DNGN_ENTER_ICE_CAVE, DNGN_EXIT_ICE_CAVE, NUM_FEATURES,
334:       "Ice Cave", "an ice cave", "IceCv",
335:       "You enter an ice cave!",
336:       BLUE, WHITE,
337: #if TAG_MAJOR_VERSION == 34
338:       '6', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
339:       {} },
340: #endif
341: #if TAG_MAJOR_VERSION > 34
342:       '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
343:       {} },
344: #endif
345:
346:     { BRANCH_VOLCANO, NUM_BRANCHES, -1, -1, 1, 14,
347:       brflag::no_x_level_travel | brflag::no_items,
348:       DNGN_ENTER_VOLCANO, DNGN_EXIT_VOLCANO, NUM_FEATURES,
349:       "Volcano", "a volcano", "Volcano",
350:       "You enter a volcano!",
351:       RED, RED,
352: #if TAG_MAJOR_VERSION == 34
353:       '7', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
354:       {} },
355: #endif
356: #if TAG_MAJOR_VERSION > 34
357:       '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
358:       {} },
359: #endif
360:
361:     { BRANCH_WIZLAB, NUM_BRANCHES, -1, -1, 1, 24,
362:       brflag::no_x_level_travel | brflag::no_items,
363:       DNGN_ENTER_WIZLAB, DNGN_EXIT_WIZLAB, NUM_FEATURES,
364:       "Wizlab", "a wizard's laboratory", "WizLab",
365:       "You enter a wizard's laboratory!",
366:       LIGHTGREY, BROWN, // set per-map
367: #if TAG_MAJOR_VERSION == 34
368:       '8', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
369:       {} },
370: #endif
371: #if TAG_MAJOR_VERSION > 34
372:       '9', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
373:       {} },
374: #endif
375: #if TAG_MAJOR_VERSION == 34
376:
377:     { BRANCH_DEPTHS, BRANCH_DUNGEON, 15, 15, 4, 22,
378:       brflag::none,
379:       DNGN_ENTER_DEPTHS, DNGN_EXIT_DEPTHS, NUM_FEATURES,
380:       "Depths", "the Depths", "Depths",
381:       nullptr,
382:       LIGHTGREY, BROWN,
383:       'U', {}, branch_noise::normal, 10,
384:       {BRANCH_VAULTS, BRANCH_SLIME} },
385: #endif
386:
387:     { BRANCH_DESOLATION, NUM_BRANCHES, -1, -1, 1, 20,
388:       brflag::no_x_level_travel | brflag::no_items,
389:       DNGN_ENTER_DESOLATION, DNGN_EXIT_DESOLATION, NUM_FEATURES, // TODO
390:       "Desolation", "the Desolation of Salt", "Desolation",
391:       "You enter a great desolation of salt!",
392:       LIGHTGREY, BROWN, // TODO
393: #if TAG_MAJOR_VERSION == 34
394:       '9', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
395:       {} },
396: #endif
397: #if TAG_MAJOR_VERSION > 34
398:       '0', {}, branch_noise::loud, DEFAULT_MON_DIE_SIZE,
399:       {} },
400: #endif
401: #if TAG_MAJOR_VERSION == 34
402:
403:     { BRANCH_GAUNTLET, NUM_BRANCHES, -1, -1, 1, 15,
404:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
405:       DNGN_ENTER_GAUNTLET, DNGN_EXIT_GAUNTLET, DNGN_EXIT_THROUGH_ABYSS,
406:       "Gauntlet", "a Gauntlet", "Gauntlet",
407:       "You enter a gauntlet!",
408:       BLACK, BLACK,
409:       '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
410:       {} },
411: #endif
412:
413:     { BRANCH_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
414:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
415:       DNGN_ENTER_ARENA, DNGN_EXIT_ARENA, NUM_FEATURES,
416:       "Arena", "the Arena", "Arena",
417:       "You enter Okawaru's Arena!",
418:       BLACK, BLACK,
419: #if TAG_MAJOR_VERSION == 34
420:       '"', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
421:       {} },
422: #else
423:       '!', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
424:       {} },
425: #endif
426:
427:     { BRANCH_CRUCIBLE, NUM_BRANCHES, -1, -1, 1, 0,
428:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
429:       DNGN_ENTER_CRUCIBLE, DNGN_EXIT_CRUCIBLE, NUM_FEATURES,
430:       "Crucible", "the Crucible of Flesh", "Crucible",
431:       "You are dragged down into the Crucible of Flesh!",
432:       BLACK, BLACK,
433:       '@', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
434:       {}
435:     },
436:
437:     { BRANCH_NECROPOLIS, NUM_BRANCHES, -1, -1, 1, 0,
438:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
439:       DNGN_ENTER_NECROPOLIS, DNGN_EXIT_NECROPOLIS, NUM_FEATURES,
440:       "Necropolis", "the Necropolis", "Necropolis",
441:       "You enter an ornate necropolis!",
442:       MAGENTA, LIGHTGREY,
443:       '%', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
444:       {}
445:     },
446:
447:     { BRANCH_GULCH, NUM_BRANCHES, -1, -1, 1, 20,
448:       brflag::no_x_level_travel | brflag::no_items,
449:       DNGN_ENTER_GULCH, DNGN_EXIT_GULCH, NUM_FEATURES,
450:       "Gulch", "a gutter gulch", "Gulch",
451:       "You enter the Vaults' gutter gulch!",
452:       GREEN, LIGHTBLUE,
453:       '^', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
454:       {}
455:     },
456:
457:     { BRANCH_XOM_ARENA, NUM_BRANCHES, -1, -1, 1, 0,
458:       brflag::no_x_level_travel | brflag::no_items | brflag::fully_map,
459:       DNGN_ENTER_XOM_ARENA, DNGN_EXIT_XOM_ARENA, NUM_FEATURES,
460:       "Arena?", "Xom's Arena of Wonders", "Arena?",
461:       "You are whisked away to a strange place.",
462:       BLACK, BLACK,
463:       '?', {}, branch_noise::normal, DEFAULT_MON_DIE_SIZE,
464:       {}
465:     },
466:
467: };
468:
469: /*
470:  * There's a few more constant data structures related to branches in
471:  * the early parts of branch.cc (Example: danger_branch_order)
472:  */
```

D-HERE-64 stable
```cpp
1433:     }
1434:
1435:     // If it's not bidirectional, check that the player is headed
1436:     // in the right direction.
1437:     if (!feat_is_bidirectional_portal(ftype))
1438:     {
1439:         if (feat_stair_direction(ftype) != (down ? CMD_GO_DOWNSTAIRS
1440:                                                  : CMD_GO_UPSTAIRS)
1441:             // probably shouldn't be passed known_shaft=true
1442:             // if going up, but just in case...
1443:             && (!down || !known_shaft))
1444:         {
1445:             if (ftype == DNGN_STONE_ARCH)
1446:                 mpr(T_("There is nothing on the other side of the stone arch."));
1447:             else if (ftype == DNGN_ABANDONED_SHOP)
1448:                 mpr(T_("This shop appears to be closed."));
1449:             else if (ftype == DNGN_SEALED_STAIRS_UP
1450:                      || ftype == DNGN_SEALED_STAIRS_DOWN )
1451:             {
1452:                 mpr(T_("A magical barricade bars your way!"));
1453:             }
1454:             else if (down)
1455:                 mpr(T_("You can't go down here!"));
1456:             else
1457:                 mpr(T_("You can't go up here!"));
1458:             return false;
1459:         }
1460:     }
1461:
1462:     // Rune locks
1463:     switch (ftype)
1464:     {
1465:     case DNGN_EXIT_VAULTS:
1466:         if (runes_in_pack() < 1)
1467:         {
1468:             mpr(T_("You need a rune to leave the Vaults."));
1469:             return false;
1470:         }
1471:         break;
1472:     case DNGN_ENTER_ZOT:
1473:         if (runes_in_pack() < ZOT_ENTRY_RUNES && !crawl_state.game_is_descent())
1474:         {
1475:             mprf(T_("You need at least %d runes to enter the Realm of Zot."),
1476:                  ZOT_ENTRY_RUNES);
1477:             return false;
```

D-HERE-64 stable
```cpp
378:             new_level_info.update_stair(you.pos(), lp, true);
379:         }
380:     }
381: }
382:
383: // These checks are probably unnecessary.
384: static bool _check_stairs(const dungeon_feature_type ftype, bool going_up)
385: {
386:     // If it's not bidirectional, check that the player is headed
387:     // in the right direction.
388:     if (!feat_is_bidirectional_portal(ftype))
389:     {
390:         if (feat_stair_direction(ftype) != (going_up ? CMD_GO_UPSTAIRS
391:                                                      : CMD_GO_DOWNSTAIRS))
392:         {
393:             if (ftype == DNGN_STONE_ARCH)
394:                 mpr(T_("There is nothing on the other side of the stone arch."));
395:             else if (ftype == DNGN_ABANDONED_SHOP)
396:                 mpr(T_("This shop has been abandoned, nothing of value remains."));
397:             else if (going_up)
398:                 mpr(T_("You can't go up here!"));
399:             else
400:                 mpr(T_("You can't go down here!"));
401:             return false;
402:         }
403:     }
404:
405:     return true;
406: }
407:
408: static bool _check_fall_down_stairs(const dungeon_feature_type ftype, bool going_up)
409: {
410:     if (!you.airborne()
411:         && you.confused()
412:         && !feat_is_escape_hatch(ftype)
413:         && !crawl_state.game_is_descent()
414:         && coinflip())
415:     {
416:         if (feat_is_staircase(ftype))
417:         {
418:             mpr(going_up
419:                 ? T_("In your confused state, you trip and fall back down the stairs.")
420:                 : T_("In your confused state, you trip and fall down the stairs."));
421:         }
422:         else
```

D-HERE-64 trunk
```cpp
1489:     }
1490:
1491:     // If it's not bidirectional, check that the player is headed
1492:     // in the right direction.
1493:     if (!feat_is_bidirectional_portal(ftype))
1494:     {
1495:         if (feat_stair_direction(ftype) != (down ? CMD_GO_DOWNSTAIRS
1496:                                                  : CMD_GO_UPSTAIRS)
1497:             // probably shouldn't be passed known_shaft=true
1498:             // if going up, but just in case...
1499:             && (!down || !known_shaft))
1500:         {
1501:             if (ftype == DNGN_STONE_ARCH)
1502:                 mpr(T_("There is nothing on the other side of the stone arch."));
1503:             else if (ftype == DNGN_ABANDONED_SHOP)
1504:                 mpr(T_("This shop appears to be closed."));
1505:             else if (ftype == DNGN_SEALED_STAIRS_UP
1506:                      || ftype == DNGN_SEALED_STAIRS_DOWN )
1507:             {
1508:                 mpr(T_("A magical barricade bars your way!"));
1509:             }
1510:             else if (down)
1511:                 mpr(T_("You can't go down here!"));
1512:             else
1513:                 mpr(T_("You can't go up here!"));
1514:             return false;
1515:         }
1516:     }
1517:
1518:     // Rune locks
1519:     switch (ftype)
1520:     {
1521:     case DNGN_EXIT_VAULTS:
1522:         if (runes_in_pack() < 1)
1523:         {
1524:             mpr(T_("You need a rune to leave the Vaults."));
1525:             return false;
1526:         }
1527:         break;
1528:     case DNGN_ENTER_ZOT:
1529:         if (runes_in_pack() < ZOT_ENTRY_RUNES && !crawl_state.game_is_descent())
1530:         {
1531:             mprf(T_("You need at least %d runes to enter the Realm of Zot."),
1532:                  ZOT_ENTRY_RUNES);
1533:             return false;
```

D-HERE-64 trunk
```cpp
390:             new_level_info.update_stair(you.pos(), lp, true);
391:         }
392:     }
393: }
394:
395: // These checks are probably unnecessary.
396: static bool _check_stairs(const dungeon_feature_type ftype, bool going_up)
397: {
398:     // If it's not bidirectional, check that the player is headed
399:     // in the right direction.
400:     if (!feat_is_bidirectional_portal(ftype))
401:     {
402:         if (feat_stair_direction(ftype) != (going_up ? CMD_GO_UPSTAIRS
403:                                                      : CMD_GO_DOWNSTAIRS))
404:         {
405:             if (ftype == DNGN_STONE_ARCH)
406:                 mpr(T_("There is nothing on the other side of the stone arch."));
407:             else if (ftype == DNGN_ABANDONED_SHOP)
408:                 mpr(T_("This shop has been abandoned, nothing of value remains."));
409:             else if (going_up)
410:                 mpr(T_("You can't go up here!"));
411:             else
412:                 mpr(T_("You can't go down here!"));
413:             return false;
414:         }
415:     }
416:
417:     return true;
418: }
419:
420: static bool _check_fall_down_stairs(const dungeon_feature_type ftype, bool going_up)
421: {
422:     if (!you.airborne()
423:         && you.confused()
424:         && !feat_is_escape_hatch(ftype)
425:         && !crawl_state.game_is_descent()
426:         && coinflip())
427:     {
428:         if (feat_is_staircase(ftype))
429:         {
430:             mpr(going_up
431:                 ? T_("In your confused state, you trip and fall back down the stairs.")
432:                 : T_("In your confused state, you trip and fall down the stairs."));
433:         }
434:         else
```

D-HERE-65 stable
```cpp
1435:     // If it's not bidirectional, check that the player is headed
1436:     // in the right direction.
1437:     if (!feat_is_bidirectional_portal(ftype))
1438:     {
1439:         if (feat_stair_direction(ftype) != (down ? CMD_GO_DOWNSTAIRS
1440:                                                  : CMD_GO_UPSTAIRS)
1441:             // probably shouldn't be passed known_shaft=true
1442:             // if going up, but just in case...
1443:             && (!down || !known_shaft))
1444:         {
1445:             if (ftype == DNGN_STONE_ARCH)
1446:                 mpr(T_("There is nothing on the other side of the stone arch."));
1447:             else if (ftype == DNGN_ABANDONED_SHOP)
1448:                 mpr(T_("This shop appears to be closed."));
1449:             else if (ftype == DNGN_SEALED_STAIRS_UP
1450:                      || ftype == DNGN_SEALED_STAIRS_DOWN )
1451:             {
1452:                 mpr(T_("A magical barricade bars your way!"));
1453:             }
1454:             else if (down)
1455:                 mpr(T_("You can't go down here!"));
1456:             else
1457:                 mpr(T_("You can't go up here!"));
1458:             return false;
1459:         }
1460:     }
1461:
1462:     // Rune locks
1463:     switch (ftype)
1464:     {
1465:     case DNGN_EXIT_VAULTS:
1466:         if (runes_in_pack() < 1)
1467:         {
1468:             mpr(T_("You need a rune to leave the Vaults."));
1469:             return false;
1470:         }
1471:         break;
1472:     case DNGN_ENTER_ZOT:
1473:         if (runes_in_pack() < ZOT_ENTRY_RUNES && !crawl_state.game_is_descent())
1474:         {
1475:             mprf(T_("You need at least %d runes to enter the Realm of Zot."),
1476:                  ZOT_ENTRY_RUNES);
1477:             return false;
1478:         }
1479:         break;
```

D-HERE-65 stable
```cpp
376:             lp.id = old_level;
377:             lp.pos = stair_pos;
378:             new_level_info.update_stair(you.pos(), lp, true);
379:         }
380:     }
381: }
382:
383: // These checks are probably unnecessary.
384: static bool _check_stairs(const dungeon_feature_type ftype, bool going_up)
385: {
386:     // If it's not bidirectional, check that the player is headed
387:     // in the right direction.
388:     if (!feat_is_bidirectional_portal(ftype))
389:     {
390:         if (feat_stair_direction(ftype) != (going_up ? CMD_GO_UPSTAIRS
391:                                                      : CMD_GO_DOWNSTAIRS))
392:         {
393:             if (ftype == DNGN_STONE_ARCH)
394:                 mpr(T_("There is nothing on the other side of the stone arch."));
395:             else if (ftype == DNGN_ABANDONED_SHOP)
396:                 mpr(T_("This shop has been abandoned, nothing of value remains."));
397:             else if (going_up)
398:                 mpr(T_("You can't go up here!"));
399:             else
400:                 mpr(T_("You can't go down here!"));
401:             return false;
402:         }
403:     }
404:
405:     return true;
406: }
407:
408: static bool _check_fall_down_stairs(const dungeon_feature_type ftype, bool going_up)
409: {
410:     if (!you.airborne()
411:         && you.confused()
412:         && !feat_is_escape_hatch(ftype)
413:         && !crawl_state.game_is_descent()
414:         && coinflip())
415:     {
416:         if (feat_is_staircase(ftype))
417:         {
418:             mpr(going_up
419:                 ? T_("In your confused state, you trip and fall back down the stairs.")
420:                 : T_("In your confused state, you trip and fall down the stairs."));
```

D-HERE-65 trunk
```cpp
1491:     // If it's not bidirectional, check that the player is headed
1492:     // in the right direction.
1493:     if (!feat_is_bidirectional_portal(ftype))
1494:     {
1495:         if (feat_stair_direction(ftype) != (down ? CMD_GO_DOWNSTAIRS
1496:                                                  : CMD_GO_UPSTAIRS)
1497:             // probably shouldn't be passed known_shaft=true
1498:             // if going up, but just in case...
1499:             && (!down || !known_shaft))
1500:         {
1501:             if (ftype == DNGN_STONE_ARCH)
1502:                 mpr(T_("There is nothing on the other side of the stone arch."));
1503:             else if (ftype == DNGN_ABANDONED_SHOP)
1504:                 mpr(T_("This shop appears to be closed."));
1505:             else if (ftype == DNGN_SEALED_STAIRS_UP
1506:                      || ftype == DNGN_SEALED_STAIRS_DOWN )
1507:             {
1508:                 mpr(T_("A magical barricade bars your way!"));
1509:             }
1510:             else if (down)
1511:                 mpr(T_("You can't go down here!"));
1512:             else
1513:                 mpr(T_("You can't go up here!"));
1514:             return false;
1515:         }
1516:     }
1517:
1518:     // Rune locks
1519:     switch (ftype)
1520:     {
1521:     case DNGN_EXIT_VAULTS:
1522:         if (runes_in_pack() < 1)
1523:         {
1524:             mpr(T_("You need a rune to leave the Vaults."));
1525:             return false;
1526:         }
1527:         break;
1528:     case DNGN_ENTER_ZOT:
1529:         if (runes_in_pack() < ZOT_ENTRY_RUNES && !crawl_state.game_is_descent())
1530:         {
1531:             mprf(T_("You need at least %d runes to enter the Realm of Zot."),
1532:                  ZOT_ENTRY_RUNES);
1533:             return false;
1534:         }
1535:         break;
```

D-HERE-65 trunk
```cpp
388:             lp.id = old_level;
389:             lp.pos = stair_pos;
390:             new_level_info.update_stair(you.pos(), lp, true);
391:         }
392:     }
393: }
394:
395: // These checks are probably unnecessary.
396: static bool _check_stairs(const dungeon_feature_type ftype, bool going_up)
397: {
398:     // If it's not bidirectional, check that the player is headed
399:     // in the right direction.
400:     if (!feat_is_bidirectional_portal(ftype))
401:     {
402:         if (feat_stair_direction(ftype) != (going_up ? CMD_GO_UPSTAIRS
403:                                                      : CMD_GO_DOWNSTAIRS))
404:         {
405:             if (ftype == DNGN_STONE_ARCH)
406:                 mpr(T_("There is nothing on the other side of the stone arch."));
407:             else if (ftype == DNGN_ABANDONED_SHOP)
408:                 mpr(T_("This shop has been abandoned, nothing of value remains."));
409:             else if (going_up)
410:                 mpr(T_("You can't go up here!"));
411:             else
412:                 mpr(T_("You can't go down here!"));
413:             return false;
414:         }
415:     }
416:
417:     return true;
418: }
419:
420: static bool _check_fall_down_stairs(const dungeon_feature_type ftype, bool going_up)
421: {
422:     if (!you.airborne()
423:         && you.confused()
424:         && !feat_is_escape_hatch(ftype)
425:         && !crawl_state.game_is_descent()
426:         && coinflip())
427:     {
428:         if (feat_is_staircase(ftype))
429:         {
430:             mpr(going_up
431:                 ? T_("In your confused state, you trip and fall back down the stairs.")
432:                 : T_("In your confused state, you trip and fall down the stairs."));
```

D-HERE-66 stable
```cpp
401:     if (made_mons)
402:         mpr(T_("...and things crawl out!"));
403:
404:     const bool webbed = _place_webs();
405:     if (!made_mons && !webbed)
406:     {
407:         mpr(T_("...but nothing happens."));
408:         return true;
409:     }
410:
411:     if (!made_mons)
412:         mpr(T_("...but only cobwebs fall out."));
413:     return true;
414: }
415:
416:
417: static bool _make_zig(item_def &zig)
418: {
419:     if (feat_is_critical(env.grid(you.pos()))
420:         || player_in_branch(BRANCH_ARENA)
421:         || is_temp_terrain(you.pos()))
422:     {
423:         mpr(T_("You can't place a gateway to a ziggurat here."));
424:         return false;
425:     }
426:     for (int lev = 1; lev <= brdepth[BRANCH_ZIGGURAT]; lev++)
427:     {
428:         if (is_level_on_stack(level_id(BRANCH_ZIGGURAT, lev))
429:             || you.where_are_you == BRANCH_ZIGGURAT)
430:         {
431:             mpr(T_("Finish your current ziggurat first!"));
432:             return false;
433:         }
434:     }
435:
436:     ASSERT(in_inventory(zig));
437:     dec_inv_item_quantity(zig.link, 1);
438:     dungeon_terrain_changed(you.pos(), DNGN_ENTER_ZIGGURAT);
439:     mpr(T_("You set the figurine down, and a mystic portal to a ziggurat forms."));
440:     return true;
441: }
442:
443: static int _gale_push_dist(const actor* agent, const actor* victim, int pow)
444: {
445:     int dist = 1 + random2(pow / 20);
```

D-HERE-66 trunk
```cpp
389:         mpr(T_("...and things crawl out!"));
390:
391:     const bool webbed = _place_webs();
392:     if (!made_mons && !webbed)
393:     {
394:         mpr(T_("...but nothing happens."));
395:         return true;
396:     }
397:
398:     if (!made_mons)
399:         mpr(T_("...but only cobwebs fall out."));
400:     return true;
401: }
402:
403:
404: static bool _make_zig(item_def &zig)
405: {
406:     if (feat_is_critical(env.grid(you.pos()))
407:         || player_in_branch(BRANCH_ARENA)
408:         || player_in_branch(BRANCH_XOM_ARENA)
409:         || is_temp_terrain(you.pos()))
410:     {
411:         mpr(T_("You can't place a gateway to a ziggurat here."));
412:         return false;
413:     }
414:     if (player_in_branch_recursive(BRANCH_ZIGGURAT))
415:     {
416:         for (int lev = 1; lev <= brdepth[BRANCH_ZIGGURAT]; lev++)
417:         {
418:             if (is_level_on_stack(level_id(BRANCH_ZIGGURAT, lev))
419:                 || you.where_are_you == BRANCH_ZIGGURAT)
420:             {
421:                 mpr(T_("Finish your current ziggurat first!"));
422:                 return false;
423:             }
424:         }
425:     }
426:
427:     ASSERT(in_inventory(zig));
428:     dec_inv_item_quantity(zig.link, 1);
429:     dungeon_terrain_changed(you.pos(), DNGN_ENTER_ZIGGURAT);
430:     mpr(T_("You set the figurine down, and a mystic portal to a ziggurat forms."));
431:     return true;
432: }
433:
```

D-HERE-68 stable
```cpp
1654:         || feat_is_tree(feat)
1655:         || (feat_is_wall(feat) && !feat_is_permarock(feat));
1656: }
1657:
1658: aff_type targeter_overgrow::is_affected(coord_def loc)
1659: {
1660:     if (affected_positions.count(loc))
1661:         return AFF_YES;
1662:
1663:     return AFF_NO;
1664: }
1665:
1666: bool targeter_overgrow::valid_aim(coord_def a)
1667: {
1668:     if (a != origin && !cell_see_cell(origin, a, LOS_NO_TRANS))
1669:     {
1670:         if (agent && agent->see_cell(a))
1671:             return notify_fail(T_("There's something in the way."));
1672:         return notify_fail(T_("You cannot see that place."));
1673:     }
1674:
1675:     if (!overgrow_affects_pos(a))
1676:         return notify_fail(T_("You cannot grow anything here."));
1677:
1678:     return true;
1679: }
1680:
1681: bool targeter_overgrow::set_aim(coord_def a)
1682: {
1683:     affected_positions.clear();
1684:
1685:     if (!targeter::set_aim(a))
1686:         return false;
1687:
1688:     if (overgrow_affects_pos(a))
1689:         affected_positions.insert(a);
1690:     else
1691:         return false;
1692:
1693:     for (adjacent_iterator ai(a, true); ai; ++ai)
1694:     {
1695:         if (overgrow_affects_pos(*ai) && you.see_cell_no_trans(*ai))
1696:             affected_positions.insert(*ai);
1697:     }
1698:
```

D-HERE-68 trunk
```cpp
1635:         || feat_is_tree(feat)
1636:         || (feat_is_wall(feat) && !feat_is_permarock(feat));
1637: }
1638:
1639: aff_type targeter_overgrow::is_affected(coord_def loc)
1640: {
1641:     if (affected_positions.count(loc))
1642:         return AFF_YES;
1643:
1644:     return AFF_NO;
1645: }
1646:
1647: bool targeter_overgrow::valid_aim(coord_def a)
1648: {
1649:     if (a != origin && !cell_see_cell(origin, a, LOS_NO_TRANS))
1650:     {
1651:         if (agent && agent->see_cell(a))
1652:             return notify_fail(T_("There's something in the way."));
1653:         return notify_fail(T_("You cannot see that place."));
1654:     }
1655:
1656:     if (!overgrow_affects_pos(a))
1657:         return notify_fail(T_("You cannot grow anything here."));
1658:
1659:     return true;
1660: }
1661:
1662: bool targeter_overgrow::set_aim(coord_def a)
1663: {
1664:     affected_positions.clear();
1665:
1666:     if (!targeter::set_aim(a))
1667:         return false;
1668:
1669:     if (overgrow_affects_pos(a))
1670:         affected_positions.insert(a);
1671:     else
1672:         return false;
1673:
1674:     for (adjacent_iterator ai(a, true); ai; ++ai)
1675:     {
1676:         if (overgrow_affects_pos(*ai) && you.see_cell_no_trans(*ai))
1677:             affected_positions.insert(*ai);
1678:     }
1679:
```

D-HERE-69 stable
```cpp
915:
916:     return join_strings(colour_names.begin(), colour_names.end(),
917:                     T_("; "));
918: }
919:
920: void item_check()
921: {
922:     describe_floor();
923:     origin_set(you.pos());
924:
925:     ostream& strm = msg::streams(MSGCH_FLOOR_ITEMS);
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
```

D-HERE-69 trunk
```cpp
915:
916:     return join_strings(colour_names.begin(), colour_names.end(),
917:                     T_("; "));
918: }
919:
920: void item_check()
921: {
922:     describe_floor();
923:     origin_set(you.pos());
924:
925:     ostream& strm = msg::streams(MSGCH_FLOOR_ITEMS);
926:
927:     auto items = const_item_list_on_square(you.visible_igrd(you.pos()));
928:
929:     if (items.empty())
930:         return;
931:
932:     // Special case
933:     if (items.size() == 1)
934:     {
935:         const item_def& it = *items[0];
936:         string name = menu_colour_item_name(it, DESC_A);
937:         strm << (T_("You see here "))
938:              << name << (T_(".")) << endl;
939:         return;
940:     }
941:
942:     string desc_string = item_message(items);
943:     // Stack summary case
944:     if (static_cast<int>(items.size()) >= Options.item_stack_summary_minimum)
945:         mprf_nojoin(MSGCH_FLOOR_ITEMS, T_("Items here: %s."), desc_string.c_str());
946:     else if (items.size() <= msgwin_lines() - 1)
947:     {
948:         mpr_nojoin(MSGCH_FLOOR_ITEMS, T_("Things that are here:"));
949:         mprf_nocap("%s", desc_string.c_str());
950:     }
951:     else
952:         strm << (T_("There are many items here.")) << endl;
953:
954:     if (items.size() > 2 && crawl_state.game_is_hints_tutorial())
955:     {
956:         // If there are 2 or more non-corpse items here, we might need
957:         // a hint.
958:         int count = 0;
959:         for (const item_def *it : items)
960:         {
```

D-HERE-71 stable
```cpp
2016:         return true;
2017:
2018:     case ABIL_ELYVILON_DIVINE_VIGOUR:
2019:         if (you.duration[DUR_DIVINE_VIGOUR])
2020:             return fail(T_("You have already been granted divine vigour!"));
2021:         return true;
2022:
2023:     case ABIL_JIYVA_OOZEMANCY:
2024:         if (you.duration[DUR_OOZEMANCY])
2025:             return fail(T_("You are already calling forth ooze!"));
2026:         return true;
2027:
2028:     case ABIL_LUGONU_ABYSS_EXIT:
2029:         if (!player_in_branch(BRANCH_ABYSS))
2030:             return fail(T_("You aren't in the Abyss!"));
2031:         return true;
2032:
2033:     case ABIL_LUGONU_CORRUPT:
2034:         return !is_level_incorruptible(quiet, reason);
2035:
2036:     case ABIL_LUGONU_ABYSS_ENTER:
2037:         if (player_in_branch(BRANCH_ABYSS))
2038:             return fail(T_("You're already here!"));
2039:         return true;
2040:
2041:     case ABIL_SIF_MUNA_FORGET_SPELL:
2042:         if (you.spell_no == 0)
2043:             return fail_canned(MSG_NO_SPELLS, T_("You don't know any spells."));
2044:         return true;
2045:
2046:     case ABIL_SIF_MUNA_DIVINE_EXEGESIS:
2047:         return can_cast_spells(quiet, reason);
2048:
2049:     case ABIL_FEDHAS_WALL_OF_BRIARS:
2050:     {
2051:         vector<coord_def> spaces = find_briar_spaces(true);
2052:         if (spaces.empty())
2053:             return fail(T_("There isn't enough space to grow briars here."));
2054:         return true;
2055:     }
2056:
2057:     case ABIL_RU_DRAW_OUT_POWER:
2058:         if (you.duration[DUR_EXHAUSTED])
2059:             return fail(T_("You're too exhausted to draw out your power."));
2060:         if (you.hp == you.hp_max && you.magic_points == you.max_magic_points
```

D-HERE-71 stable
```cpp
2935:     dprf("level target is %d depth %d, pos %d,%d", target.id.branch,
2936:         target.id.branch, target.pos.x, target.pos.y);
2937: #endif
2938:
2939:     return target;
2940: }
2941:
2942: static void _start_translevel_travel()
2943: {
2944:     // Update information for this level.
2945:     travel_cache.get_level_info(level_id::current()).update();
2946:
2947:     if (level_id::current() == level_target.id)
2948:     {
2949:         if (level_target.pos.x == -1 &&
2950:             level_target.id.depth == branches[level_target.id.branch].numlevels)
2951:         {
2952:             mpr(T_("You're already at the bottom of this branch!"));
2953:             return;
2954:         }
2955:         else if (level_target.pos.x == -1 || level_target.pos == you.pos())
2956:         {
2957:             mpr(T_("You're already here!"));
2958:             return;
2959:         }
2960:     }
2961:
2962: #ifdef DEBUG_TRAVEL
2963:     dprf("starting translevel travel, branch %d depth %d, pos %d,%d",
2964:         level_target.id.branch, level_target.id.depth, level_target.pos.x,
2965:         level_target.pos.y);
2966: #endif
2967:
2968:     if (level_target.id.depth > 0)
2969:     {
2970:         you.running = RMODE_INTERLEVEL;
2971:         you.running.pos.reset();
2972:         last_stair.id.depth = -1;
2973:         last_stair.pos.reset();
2974:
2975:         _Route_Warning.new_dest(level_target);
2976:
2977:         _Src_Level = level_id::current();
2978:         _Src_Dest_Level_Delta = level_distance(_Src_Level,
2979:                                                level_target.id);
```

D-HERE-71 stable
```cpp
5216:
5217:     say_any(items, "item");
5218:     say_any(shops, "shop");
5219:     say_any(apply_quantities(altars), "altar");
5220:     say_any(apply_quantities(portals), "portal");
5221:     say_any(apply_quantities(stairs), "stair");
5222:     say_any(apply_quantities(transporters), "transporter");
5223:     say_any(apply_quantities(runed_doors), "runed door");
5224:     say_any(apply_quantities(runelights), "runelights");
5225:
5226:     return true;
5227: }
5228:
5229: void do_interlevel_travel()
5230: {
5231:     if (Hints.hints_travel)
5232:         Hints.hints_travel = 0;
5233:
5234:     if (!can_travel_interlevel())
5235:     {
5236:         if (you.running.pos == you.pos())
5237:         {
5238:             mpr(T_("You're already here!"));
5239:             return;
5240:         }
5241:         else if (!you.running.pos.x || !you.running.pos.y)
5242:         {
5243:             mpr(T_("Sorry, you can't auto-travel out of here."));
5244:             return;
5245:         }
5246:
5247:         // Don't ask for a destination if you can only travel
5248:         // within level anyway.
5249:         start_travel(you.running.pos);
5250:     }
5251:     else
5252:         _start_translevel_travel_prompt();
5253:
5254:     if (you.running)
5255:         clear_messages();
5256: }
5257:
5258: #ifdef USE_TILE
5259: // (0,0) = same position is handled elsewhere.
5260: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
```

D-HERE-71 trunk
```cpp
2108:         return true;
2109:
2110:     case ABIL_ELYVILON_AURA_OF_VIGOUR:
2111:         if (you.duration[DUR_DIVINE_VIGOUR])
2112:             return fail(T_("You have already been granted divine vigour!"));
2113:         return true;
2114:
2115:     case ABIL_JIYVA_OOZEMANCY:
2116:         if (you.duration[DUR_OOZEMANCY])
2117:             return fail(T_("You are already calling forth ooze!"));
2118:         return true;
2119:
2120:     case ABIL_LUGONU_ABYSS_EXIT:
2121:         if (!player_in_branch(BRANCH_ABYSS))
2122:             return fail(T_("You aren't in the Abyss!"));
2123:         return true;
2124:
2125:     case ABIL_LUGONU_CORRUPT:
2126:         return !is_level_incorruptible(quiet, reason);
2127:
2128:     case ABIL_LUGONU_ABYSS_ENTER:
2129:         if (player_in_branch(BRANCH_ABYSS))
2130:             return fail(T_("You're already here!"));
2131:         return true;
2132:
2133:     case ABIL_SIF_MUNA_FORGET_SPELL:
2134:         if (you.spell_no == 0)
2135:             return fail_canned(MSG_NO_SPELLS, T_("You don't know any spells."));
2136:         return true;
2137:
2138:     case ABIL_SIF_MUNA_DIVINE_EXEGESIS:
2139:     case ABIL_SIF_MUNA_REPEAT_EXEGESIS:
2140:         return can_cast_spells(quiet, false, reason);
2141:
2142:     case ABIL_FEDHAS_WALL_OF_BRIARS:
2143:     {
2144:         vector<coord_def> spaces = find_briar_spaces(true);
2145:         if (spaces.empty())
2146:             return fail(T_("There isn't enough space to grow briars here."));
2147:         return true;
2148:     }
2149:
2150:     case ABIL_RU_DRAW_OUT_POWER:
2151:         if (you.duration[DUR_EXHAUSTED])
2152:             return fail(T_("You're too exhausted to draw out your power."));
```

D-HERE-71 trunk
```cpp
2973:     dprf("level target is %d depth %d, pos %d,%d", target.id.branch,
2974:         target.id.branch, target.pos.x, target.pos.y);
2975: #endif
2976:
2977:     return target;
2978: }
2979:
2980: static void _start_translevel_travel()
2981: {
2982:     // Update information for this level.
2983:     travel_cache.get_level_info(level_id::current()).update();
2984:
2985:     if (level_id::current() == level_target.id)
2986:     {
2987:         if (level_target.pos.x == -1 &&
2988:             level_target.id.depth == branches[level_target.id.branch].numlevels)
2989:         {
2990:             mpr(T_("You're already at the bottom of this branch!"));
2991:             return;
2992:         }
2993:         else if (level_target.pos.x == -1 || level_target.pos == you.pos())
2994:         {
2995:             mpr(T_("You're already here!"));
2996:             return;
2997:         }
2998:     }
2999:
3000: #ifdef DEBUG_TRAVEL
3001:     dprf("starting translevel travel, branch %d depth %d, pos %d,%d",
3002:         level_target.id.branch, level_target.id.depth, level_target.pos.x,
3003:         level_target.pos.y);
3004: #endif
3005:
3006:     if (level_target.id.depth > 0)
3007:     {
3008:         you.running = RMODE_INTERLEVEL;
3009:         you.running.pos.reset();
3010:         last_stair.id.depth = -1;
3011:         last_stair.pos.reset();
3012:
3013:         _Route_Warning.new_dest(level_target);
3014:
3015:         _Src_Level = level_id::current();
3016:         _Src_Dest_Level_Delta = level_distance(_Src_Level,
3017:                                                level_target.id);
```

D-HERE-71 trunk
```cpp
5324:         }
5325:     }
5326:     else
5327:         say_any(apply_quantities(stairs), "stair");
5328:     say_any(apply_quantities(hatches), N_("hatch"));
5329:     say_any(apply_quantities(transporters), "transporter");
5330:     say_any(apply_quantities(runed_doors), "runed door");
5331:     say_any(apply_quantities(runelights), "runelights");
5332:     say_any(apply_quantities(mutation_catalysts), "mutation catalysts");
5333:
5334:     return true;
5335: }
5336:
5337: void do_interlevel_travel()
5338: {
5339:     if (Hints.hints_travel)
5340:         Hints.hints_travel = 0;
5341:
5342:     if (!can_travel_interlevel())
5343:     {
5344:         if (you.running.pos == you.pos())
5345:         {
5346:             mpr(T_("You're already here!"));
5347:             return;
5348:         }
5349:         else if (!you.running.pos.x || !you.running.pos.y)
5350:         {
5351:             mpr(T_("Sorry, you can't auto-travel out of here."));
5352:             return;
5353:         }
5354:
5355:         // Don't ask for a destination if you can only travel
5356:         // within level anyway.
5357:         start_travel(you.running.pos);
5358:     }
5359:     else
5360:         _start_translevel_travel_prompt();
5361:
5362:     if (you.running)
5363:         clear_messages();
5364: }
5365:
5366: #ifdef USE_TILE
5367: // (0,0) = same position is handled elsewhere.
5368: static const int dir_dx[8] = {-1, 0, 1, -1, 1, -1,  0,  1};
```

D-HERE-72 stable
```cpp
1992: static void _get_rune(const item_def& it, bool quiet)
1993: {
1994:     if (!you.runes[it.sub_type])
1995:         you.runes.set(it.sub_type);
1996:
1997:     if (!quiet)
1998:     {
1999:         flash_view_delay(UA_PICKUP, rune_colour(it.sub_type), 300);
2000:         mprf(T_("You pick up the %s rune and feel its power."),
2001:              rune_type_name(it.sub_type));
2002:         int nrunes = runes_in_pack();
2003:         if (nrunes >= you.obtainable_runes)
2004:             mpr(T_("You have collected all the runes! Now go and win!"));
2005:         else if (nrunes == ZOT_ENTRY_RUNES)
2006:         {
2007:             // might be inappropriate in new Sprints, please change it then
2008:             mprf(T_("%d runes! That's enough to enter the realm of Zot."),
2009:                  nrunes);
2010:         }
2011:         else if (nrunes > 1)
2012:         {
2013:             if (player_in_branch(BRANCH_PANDEMONIUM) && _got_all_pan_runes())
2014:                 mpr(T_("You've emptied out Pandemonium! Nothing left here but demons."));
2015:             mprf(T_("You now have %d runes."), nrunes);
2016:         }
2017:
2018:         mpr(T_("Press } to see all the runes you have collected."));
2019:     }
2020:
2021:     if (it.sub_type == RUNE_ABYSSAL)
2022:         mpr(T_("You feel the abyssal rune guiding you out of this place."));
2023: }
2024:
2025: static bool _is_disabled_gem(gem_type gem)
2026: {
2027:     switch (gem)
2028:     {
2029: #if TAG_MAJOR_VERSION == 34
2030:     case GEM_ORC:
2031:         return true;
2032: #endif
2033:     default:
2034:         return false;
2035:     }
2036: }
```

D-HERE-72 trunk
```cpp
1954: static void _get_rune(const item_def& it, bool quiet)
1955: {
1956:     if (!you.runes[it.sub_type])
1957:         you.runes.set(it.sub_type);
1958:
1959:     if (!quiet)
1960:     {
1961:         flash_view_delay(UA_PICKUP, rune_colour(it.sub_type), 300);
1962:         mprf(T_("You pick up the %s rune and feel its power."),
1963:              rune_type_name(it.sub_type));
1964:         int nrunes = runes_in_pack();
1965:         if (nrunes >= you.obtainable_runes)
1966:             mpr(T_("You have collected all the runes! Now go and win!"));
1967:         else if (nrunes == ZOT_ENTRY_RUNES)
1968:         {
1969:             // might be inappropriate in new Sprints, please change it then
1970:             mprf(T_("%d runes! That's enough to enter the realm of Zot."),
1971:                  nrunes);
1972:         }
1973:         else if (nrunes > 1)
1974:         {
1975:             if (player_in_branch(BRANCH_PANDEMONIUM) && _got_all_pan_runes())
1976:                 mpr(T_("You've emptied out Pandemonium! Nothing left here but demons."));
1977:             mprf(T_("You now have %d runes."), nrunes);
1978:         }
1979:
1980:         mpr(T_("Press } to see all the runes you have collected."));
1981:     }
1982:
1983:     if (it.sub_type == RUNE_ABYSSAL)
1984:         mpr(T_("You feel the abyssal rune guiding you out of this place."));
1985: }
1986:
1987: static bool _is_disabled_gem(gem_type gem)
1988: {
1989:     switch (gem)
1990:     {
1991: #if TAG_MAJOR_VERSION == 34
1992:     case GEM_ORC:
1993:         return true;
1994: #endif
1995:     default:
1996:         return false;
1997:     }
1998: }
```

D-HERE-73 stable
```cpp
2790:              healing_done > 25 ? T_(" greatly ") : "");
2791: }
2792:
2793: // Prompts the player for reasons they may not wish to leave a floor.
2794: // Returns whether the player decided to cancel the move.
2795: bool beogh_cancel_leaving_floor()
2796: {
2797:     if (!you_worship(GOD_BEOGH))
2798:         return false;
2799:
2800:     if (you.duration[DUR_BEOGH_DIVINE_CHALLENGE])
2801:     {
2802:         if (!yesno(T_("Are you sure you wish to flee a divine trial? This will "
2803:                    "place you under penance!"), false, 'n'))
2804:         {
2805:             mpr(T_("Beogh appreciates your bravery."));
2806:             return true;
2807:         }
2808:     }
2809:
2810:     if (you.duration[DUR_BLOOD_FOR_BLOOD])
2811:     {
2812:         if (!yesno(T_("Your vengeful prayer will end if you leave here."
2813:                    " Continue?"), false, 'n'))
2814:         {
2815:             canned_msg(MSG_OK);
2816:             return true;
2817:         }
2818:     }
2819:
2820:     return false;
2821: }
2822:
2823: void beogh_increase_orcification()
2824: {
2825:     // Currently gaining a second level doesn't have much messaging. Perhaps in
2826:     // future, it should?
2827:     if (you.props.exists(ORCIFICATION_LEVEL_KEY))
2828:     {
2829:         you.props[ORCIFICATION_LEVEL_KEY] = 2;
2830:         mprf(MSGCH_MUTATION, T_("Your orcish features manifest fully."));
2831:         return;
2832:     }
2833:
2834:     // Adjust the message we give to the player's physiology.
2835:     string msg = species::orcification_msg(you.species);
2836:
2837:     mprf(MSGCH_MUTATION, "%s", T_(msg.c_str()));
```

D-HERE-73 trunk
```cpp
2970:              healing_done > 25 ? T_(" greatly ") : "");
2971: }
2972:
2973: // Prompts the player for reasons they may not wish to leave a floor.
2974: // Returns whether the player decided to cancel the move.
2975: bool beogh_cancel_leaving_floor()
2976: {
2977:     if (!you_worship(GOD_BEOGH))
2978:         return false;
2979:
2980:     if (you.duration[DUR_BEOGH_DIVINE_CHALLENGE])
2981:     {
2982:         if (!yesno(T_("Are you sure you wish to flee a divine trial? This will "
2983:                    "place you under penance!"), false, 'n'))
2984:         {
2985:             mpr(T_("Beogh appreciates your bravery."));
2986:             return true;
2987:         }
2988:     }
2989:
2990:     if (you.duration[DUR_BLOOD_FOR_BLOOD])
2991:     {
2992:         if (!yesno(T_("Your vengeful prayer will end if you leave here."
2993:                    " Continue?"), false, 'n'))
2994:         {
2995:             canned_msg(MSG_OK);
2996:             return true;
2997:         }
2998:     }
2999:
3000:     return false;
3001: }
3002:
3003: void beogh_increase_orcification()
3004: {
3005:     // Currently gaining a second level doesn't have much messaging. Perhaps in
3006:     // future, it should?
3007:     if (you.props.exists(ORCIFICATION_LEVEL_KEY))
3008:     {
3009:         you.props[ORCIFICATION_LEVEL_KEY] = 2;
3010:         mprf(MSGCH_MUTATION, T_("Your orcish features manifest fully."));
3011:         return;
3012:     }
3013:
3014:     // Adjust the message we give to the player's physiology.
3015:     string msg = species::orcification_msg(you.species);
3016:
3017:     mprf(MSGCH_MUTATION, "%s", T_(msg.c_str()));
```

D-HERE-74 stable
```cpp
1774:         }
1775:
1776:         need_here_subtitle = false;
1777:
1778:         if (need_there_subtitle && !(here || res.in_inventory))
1779:         {
1780:             const string cycle_keyhelp =
1781:                 T_(" <lightgrey>([<w>,</w>] to cycle)</lightgrey>");
1782:             stashmenu.add_entry(new StashMenuEntry(
1783:                 string(T_("Results elsewhere")) + cycle_keyhelp,
1784:                 MEL_SUBTITLE, LIGHTCYAN));
1785:             ASSERT(first_hdr);
1786:             first_hdr->text += cycle_keyhelp;
1787:             need_there_subtitle = false;
1788:             initial_snap = static_cast<int>(stashmenu.item_count());
1789:         }
1790:
1791:         if (!res.in_inventory)
1792:         {
1793:             if (const uint8_t waypoint = travel_cache.is_waypoint(res.pos))
1794:                 matchtitle << make_stringf(T_("Waypoint %d"), waypoint) << " ";
1795:             if (here)
1796:                 matchtitle << T_("[right here]") << " ";
1797:             else
1798:             {
1799:                 const string place = res.pos.id.describe();
1800:                 matchtitle << make_stringf(T_("[%s]"), place.c_str()) << " ";
1801:             }
1802:         }
1803:
1804:         matchtitle << res.display_match();
1805:         if (res.duplicates > 0)
1806:         {
1807:             if (res.duplicates != res.duplicate_piles  // piles are only
1808:                                                        // meaningful for items
1809:                 && res.match_type == MATCH_ITEM)
1810:             {
1811:                 matchtitle << make_stringf_p(
1812:                     T_(" (%1$d further duplicate%2$s in %3$d pile%4$s)"),
1813:                     res.duplicates, res.duplicates == 1 ? "" : "s",
1814:                     res.duplicate_piles,
1815:                     res.duplicate_piles == 1 ? "" : "s");
1816:             }
1817:             else
1818:             {
```

D-HERE-74 trunk
```cpp
1916:         }
1917:
1918:         need_here_subtitle = false;
1919:
1920:         if (need_there_subtitle && !(here || res.in_inventory))
1921:         {
1922:             const string cycle_keyhelp =
1923:                 T_(" <lightgrey>([<w>,</w>] to cycle)</lightgrey>");
1924:             stashmenu.add_entry(new StashMenuEntry(
1925:                 string(T_("Results elsewhere")) + cycle_keyhelp,
1926:                 MEL_SUBTITLE, LIGHTCYAN));
1927:             ASSERT(first_hdr);
1928:             first_hdr->text += cycle_keyhelp;
1929:             need_there_subtitle = false;
1930:             initial_snap = static_cast<int>(stashmenu.item_count());
1931:         }
1932:
1933:         if (!res.in_inventory)
1934:         {
1935:             if (const uint8_t waypoint = travel_cache.is_waypoint(res.pos))
1936:                 matchtitle << make_stringf(T_("Waypoint %d"), waypoint) << " ";
1937:             if (here)
1938:                 matchtitle << T_("[right here]") << " ";
1939:             else
1940:             {
1941:                 const string place = res.pos.id.describe();
1942:                 matchtitle << make_stringf(T_("[%s]"), place.c_str()) << " ";
1943:             }
1944:         }
1945:
1946:         matchtitle << res.display_match();
1947:         if (res.duplicates > 0)
1948:         {
1949:             if (res.duplicates != res.duplicate_piles  // piles are only
1950:                                                        // meaningful for items
1951:                 && res.match_type == MATCH_ITEM)
1952:             {
1953:                 matchtitle << make_stringf_p(
1954:                     T_(" (%1$d further duplicate%2$s in %3$d pile%4$s)"),
1955:                     res.duplicates, res.duplicates == 1 ? "" : "s",
1956:                     res.duplicate_piles,
1957:                     res.duplicate_piles == 1 ? "" : "s");
1958:             }
1959:             else
1960:             {
```

D-HERE-75 trunk
```cpp
1818: {
1819:     vector<string> suffixes;
1820:     // Things which describe the cell.
1821:     _push_back_if_nonempty(_cell_cloud_description(pos), &suffixes);
1822:     _push_back_if_nonempty(_cell_sanctuary_description(pos), &suffixes);
1823:     _push_back_if_nonempty(_cell_silence_description(pos), &suffixes);
1824:     _push_back_if_nonempty(_cell_interesting_terrain_description(pos), &suffixes);
1825:
1826:     return suffixes;
1827: }
1828:
1829: static vector<string> _monster_description_suffixes(const monster_info& mi,
1830:                                                     targeting_behaviour* behavior = nullptr)
1831: {
1832:     vector<string> suffixes;
1833:
1834:     _push_back_if_nonempty(mi.wounds_description(true), &suffixes);
1835:     _push_back_if_nonempty(mi.constriction_description(), &suffixes);
1836:     _append_container(suffixes, mi.attributes());
1837:     _append_container(suffixes, _get_monster_desc_vector(mi));
1838:
1839:     if (mi.is(MB_REMEMBERED_INVIS))
1840:         suffixes.push_back(T_("no longer here"));
1841:
1842:     if (behavior)
1843:         _append_container(suffixes, behavior->get_monster_desc(mi));
1844:
1845:     return suffixes;
1846: }
1847:
1848: // Only descriptors with stable monstatus identities belong here. Dynamic
1849: // wounds, constriction, cloud names, and targeting chances are display text,
1850: // not TextDB keys, and have no corresponding monstatus entries.
1851: vector<monster_status_descriptor> get_monster_status_descriptors(const monster_info& mi)
1852: {
1853:     vector<monster_status_descriptor> descriptors;
1854:     if (silenced(mi.pos))
1855:         descriptors.push_back({"silenced monstatus", T_("silenced")});
1856:     _append_container(descriptors, mi.attribute_descriptors());
1857:
1858:     if (mi.attitude != ATT_FRIENDLY && !mi.fellow_slime())
1859:     {
1860:         if (mi.attitude == ATT_GOOD_NEUTRAL)
1861:             descriptors.push_back({"peaceful monstatus", T_("peaceful")});
1862:         else if (mi.attitude != ATT_HOSTILE && !mi.is(MB_FRENZIED))
```

D-HERE-76 stable
```cpp
2046:             break;
2047:
2048:         for (adjacent_iterator ai(you.pos()); ai; ++ai)
2049:             if (feat_is_wall(env.grid(*ai)))
2050:                 return "";
2051:
2052:         return T_("there are no nearby walls to construct a spike launcher in.");
2053:     }
2054:
2055:     case SPELL_DIAMOND_SAWBLADES:
2056:         if (temp && diamond_sawblade_spots(false).empty())
2057:             return T_("there is no room to construct a sawblade.");
2058:         break;
2059:
2060:     case SPELL_SURPRISING_CROCODILE:
2061:         if (temp)
2062:         {
2063:             if (you.is_stationary())
2064:                 return T_("you cannot be moved right now.");
2065:             else if (!monster_habitable_grid(MONS_CROCODILE, you.pos()))
2066:                 return T_("a crocodile could not survive beneath you.");
2067:             else if (count_summons(&you, SPELL_SURPRISING_CROCODILE))
2068:                 return T_("your pet crocodile is still here.");
2069:         }
2070:         break;
2071:
2072:     case SPELL_PLATINUM_PARAGON:
2073:         if (temp)
2074:         {
2075:             if (!you.props.exists(PARAGON_WEAPON_KEY))
2076:             {
2077:                 return T_("you must imprint a weapon on your paragon first! "
2078:                           "(Use the Imprint Weapon ability)");
2079:             }
2080:
2081:             monster* paragon = find_player_paragon();
2082:             if (paragon && paragon_charge_level(*paragon) == 0)
2083:                 return T_("your paragon is already deployed, but not yet charged.");
2084:         }
2085:         break;
2086:
2087:     case SPELL_FORTRESS_BLAST:
2088:         if (temp && you.duration[DUR_FORTRESS_BLAST_TIMER])
2089:             return T_("you are already charging a Fortress Blast.");
2090:         break;
```

D-HERE-76 trunk
```cpp
2064:             break;
2065:
2066:         for (adjacent_iterator ai(you.pos()); ai; ++ai)
2067:             if (feat_is_wall(env.grid(*ai)))
2068:                 return "";
2069:
2070:         return T_("there are no nearby walls to construct a spike launcher in.");
2071:     }
2072:
2073:     case SPELL_DIAMOND_SAWBLADES:
2074:         if (temp && diamond_sawblade_spots(false).empty())
2075:             return T_("there is no room to construct a sawblade.");
2076:         break;
2077:
2078:     case SPELL_SURPRISING_CROCODILE:
2079:         if (temp)
2080:         {
2081:             if (you.is_stationary())
2082:                 return T_("you cannot be moved right now.");
2083:             else if (!monster_habitable_grid(MONS_CROCODILE, you.pos()))
2084:                 return T_("a crocodile could not survive beneath you.");
2085:             else if (count_summons(&you, SPELL_SURPRISING_CROCODILE))
2086:                 return T_("your pet crocodile is still here.");
2087:         }
2088:         break;
2089:
2090:     case SPELL_PLATINUM_PARAGON:
2091:         if (temp)
2092:         {
2093:             if (!you.props.exists(PARAGON_WEAPON_KEY))
2094:             {
2095:                 return T_("you must imprint a weapon on your paragon first! "
2096:                           "(Use the Imprint Weapon ability)");
2097:             }
2098:
2099:             monster* paragon = find_player_paragon();
2100:             if (paragon && paragon_charge_level(*paragon) == 0)
2101:                 return T_("your paragon is already deployed, but not yet charged.");
2102:         }
2103:         break;
2104:
2105:     case SPELL_FORTRESS_BLAST:
2106:         if (temp && you.duration[DUR_FORTRESS_BLAST_TIMER])
2107:             return T_("you are already charging a Fortress Blast.");
2108:         break;
```

补查：stable database.cc:650-698 _parse_text_db 会去除值开头的换行，空条目变为空值；:2740-2785 lookup 对空值回退。因此本报告的空片段回退英文结论有加载器支持。stable player.cc:9438-9476 hands_act 优先使用中文整句，source.txt:42873 的 hands action|Your %s get new energy. 为你的%s焕发出新的活力。
