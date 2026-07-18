#pragma once

#include "tag-version.h"

#include "bane-type.h"
#include "i18n.h"

struct bane_def
{
    bane_type   type;
    short       duration;    ///< Duration of bane in XP units
    const char* name;        ///< Name of this bane.
    const char* description; ///< What appears on the 'A' screen.
};

static const bane_def bane_data[] =
{
    {
        BANE_LETHARGY,
        BANE_DUR_LONG,
        N_("Lethargy"),
        N_("You cover ground slowly."),
    },

    {
        BANE_HEATSTROKE,
        BANE_DUR_LONG,
        N_("Heatstroke"),
        N_("You often become slowed when damaged by fire."),
    },

    {
        BANE_SNOW_BLINDNESS,
        BANE_DUR_LONG,
        N_("Snow-blindness"),
        N_("You often become weak and blind when damaged by cold."),
    },

    {
        BANE_ELECTROSPASM,
        BANE_DUR_LONG,
        N_("Electrospasm"),
        N_("You often become unable to move when damaged by electricity."),
    },

    {
        BANE_CLAUSTROPHOBIA,
        BANE_DUR_MEDIUM,
        N_("Claustrophobia"),
        N_("Your slaying and spellpower are decreased in confined spaces."),
    },

    {
        BANE_STUMBLING,
        BANE_DUR_SHORT,
        N_("Stumbling"),
        N_("Your evasion is greatly reduced on turns you move or wait in place."),
    },

#if TAG_MAJOR_VERSION == 34
    {
        BANE_RECKLESS_REMOVED,
        0,
        N_("the Removed"),
        N_("You feel a strange sense of nostalgia."),
    },
#endif

    {
        BANE_SUCCOUR,
        BANE_DUR_MEDIUM,
        N_("Succour"),
        N_("You heal other nearby enemies whenever you kill a monster."),
    },

    {
        BANE_MULTIPLICITY,
        BANE_DUR_MEDIUM,
        N_("Multiplicity"),
        N_("Enemies in your sight sometimes split into clones of themselves."),
    },

    {
        BANE_DILETTANTE,
        BANE_DUR_MEDIUM,
        N_("the Dilettante"),
        N_("You are less proficient with several skills."), // Overridden
    },

    {
        BANE_PARADOX,
        BANE_DUR_MEDIUM,
        N_("Paradox"),
        N_("Enemies you spot sometimes become touched by paradox."),
    },

    {
        BANE_WARDING,
        BANE_DUR_MEDIUM,
        N_("Warding"),
        N_("Enemies you encounter may be immune to damage from range."),
    },

    {
        BANE_HUNTED,
        BANE_DUR_LONG,
        N_("the Hunted"),
        N_("When enemies are summoned, they will appear beside you instead."),
    },

    {
        BANE_MORTALITY,
        BANE_DUR_SHORT,
        N_("Mortality"),
        N_("When alone and injured, reapers sometimes come to claim you."),
    },
};
