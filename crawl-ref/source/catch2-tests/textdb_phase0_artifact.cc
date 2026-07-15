#include "AppHdr.h"

#include "textdb_phase0_artifact.h"

#include "syscalls.h"

#include <fstream>
#include <sstream>
#include <unistd.h>

namespace
{
string json_string(const string &value)
{
    static const char hex[] = "0123456789abcdef";
    string result = "\"";
    for (const unsigned char c : value)
    {
        switch (c)
        {
        case '"': result += "\\\""; break;
        case '\\': result += "\\\\"; break;
        case '\b': result += "\\b"; break;
        case '\f': result += "\\f"; break;
        case '\n': result += "\\n"; break;
        case '\r': result += "\\r"; break;
        case '\t': result += "\\t"; break;
        default:
            if (c < 0x20)
            {
                result += "\\u00";
                result += hex[c >> 4];
                result += hex[c & 0x0f];
            }
            else
                result += static_cast<char>(c);
        }
    }
    result += '"';
    return result;
}

void provenance_json(std::ostringstream &out,
                     const textdb_phase0::source_provenance &provenance)
{
    out << "{\"source_name\":" << json_string(provenance.source_name)
        << ",\"load_index\":" << provenance.load_index
        << ",\"definition_ordinal\":" << provenance.definition_ordinal
        << "}";
}
}

string serialize_textdb_phase0_artifact(
    const textdb_phase0::canonical_speakdb_dump &dump)
{
    std::ostringstream out;
    out << "{\"schema_version\":" << dump.schema_version
        << ",\"database_name\":" << json_string(dump.database_name)
        << ",\"source_directory\":" << json_string(dump.source_directory)
        << ",\"sources\":[";
    for (size_t i = 0; i < dump.sources.size(); ++i)
    {
        if (i)
            out << ',';
        const textdb_phase0::source_snapshot &source = dump.sources[i];
        out << "{\"source_name\":" << json_string(source.source_name)
            << ",\"load_index\":" << source.load_index
            << ",\"normalized_utf8\":"
            << json_string(source.normalized_utf8) << "}";
    }
    out << "],\"entries\":[";
    for (size_t i = 0; i < dump.entries.size(); ++i)
    {
        if (i)
            out << ',';
        const textdb_phase0::canonical_entry &entry = dump.entries[i];
        out << "{\"canonical_key\":" << json_string(entry.canonical_key)
            << ",\"effective_provenance\":";
        provenance_json(out, entry.provenance);
        out << ",\"raw_body\":" << json_string(entry.raw_body)
            << ",\"source_history\":[";
        for (size_t j = 0; j < entry.source_history.size(); ++j)
        {
            if (j)
                out << ',';
            provenance_json(out, entry.source_history[j]);
        }
        out << "],\"variants\":[";
        for (size_t j = 0; j < entry.variants.size(); ++j)
        {
            if (j)
                out << ',';
            const textdb_phase0::canonical_variant &variant = entry.variants[j];
            out << "{\"locator\":{\"canonical_key\":"
                << json_string(variant.locator.canonical_key)
                << ",\"variant_ordinal\":"
                << variant.locator.variant_ordinal << "},\"provenance\":";
            provenance_json(out, variant.provenance);
            out << ",\"weight\":" << variant.weight
                << ",\"raw_pattern\":"
                << json_string(variant.raw_pattern) << "}";
        }
        out << "],\"parse_error\":";
        if (entry.parse_error.empty())
            out << "null";
        else
            out << json_string(entry.parse_error);
        out << ",\"body_empty\":" << (entry.body_empty ? "true" : "false")
            << "}";
    }
    out << "]}\n";
    return out.str();
}

bool write_textdb_phase0_artifact_atomic(
    const textdb_phase0::canonical_speakdb_dump &dump,
    const string &path, string &error)
{
    const string temporary = path + ".tmp." + std::to_string(getpid());
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output)
        {
            error = "cannot open temporary artifact: " + temporary;
            return false;
        }
        const string bytes = serialize_textdb_phase0_artifact(dump);
        output.write(bytes.data(), bytes.size());
        output.close();
        if (!output)
        {
            error = "cannot write temporary artifact: " + temporary;
            unlink_u(temporary.c_str());
            return false;
        }
    }
    if (rename_u(temporary.c_str(), path.c_str()) != 0)
    {
        error = "cannot rename artifact into place: " + path;
        unlink_u(temporary.c_str());
        return false;
    }
    return true;
}
