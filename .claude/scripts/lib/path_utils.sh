#!/usr/bin/env bash

# Resolve a user-facing repository path before the caller changes directory.
# Relative values are always anchored at the supplied repository root. Absolute
# values are accepted for explicit external destinations.
dcss_resolve_repo_path()
{
    if [ "$#" -ne 2 ] || [ -z "$1" ] || [ -z "$2" ]; then
        echo "dcss_resolve_repo_path requires <repo-root> <path>" >&2
        return 2
    fi

    local repo_root="$1"
    local value="$2"
    case "$value" in
        /*) printf '%s\n' "$value" ;;
        ./*) printf '%s/%s\n' "$repo_root" "${value#./}" ;;
        *) printf '%s/%s\n' "$repo_root" "$value" ;;
    esac
}

# Load a plain key=value configuration without evaluating shell syntax.
# Existing environment variables win over values in the file.
dcss_load_path_config()
{
    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
        echo "dcss_load_path_config requires an existing config file" >&2
        return 2
    fi

    local config_file="$1"
    local line key value line_number=0
    while IFS= read -r line || [ -n "$line" ]; do
        line_number=$((line_number + 1))
        line="${line%$'\r'}"
        case "$line" in
            ""|\#*) continue ;;
            *=*) ;;
            *)
                echo "invalid path config line $config_file:$line_number" >&2
                return 2
                ;;
        esac

        key="${line%%=*}"
        value="${line#*=}"
        case "$key" in
            DCSS_DEPLOY_ROOT|DCSS_WINDOWS_DEPLOY_DIR|DCSS_ANDROID_DEPLOY_DIR) ;;
            *)
                echo "unsupported path config key $key at $config_file:$line_number" >&2
                return 2
                ;;
        esac

        if ! declare -p "$key" >/dev/null 2>&1; then
            printf -v "$key" '%s' "$value"
            export "$key"
        fi
    done < "$config_file"
}

# The default local config is optional. An explicitly requested config must
# exist so a typo cannot silently fall back to another deployment location.
dcss_load_repo_path_config()
{
    if [ "$#" -ne 2 ] || [ -z "$1" ]; then
        echo "dcss_load_repo_path_config requires <repo-root> <explicit-config>" >&2
        return 2
    fi

    local repo_root="$1"
    local explicit_config="$2"
    local config_input="${explicit_config:-.dcss-paths.conf}"
    local config_file
    config_file="$(dcss_resolve_repo_path "$repo_root" "$config_input")" || return

    if [ ! -f "$config_file" ]; then
        if [ -n "$explicit_config" ]; then
            echo "explicit path config not found: $config_file" >&2
            return 2
        fi
        return 0
    fi
    dcss_load_path_config "$config_file"
}
