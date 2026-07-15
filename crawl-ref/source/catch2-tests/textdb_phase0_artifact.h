#pragma once

#include "database.h"

string serialize_textdb_phase0_artifact(
    const textdb_phase0::canonical_speakdb_dump &dump);
bool write_textdb_phase0_artifact_atomic(
    const textdb_phase0::canonical_speakdb_dump &dump,
    const string &path, string &error);
