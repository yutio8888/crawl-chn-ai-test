#!/usr/bin/env python3
"""Serialize arguments evaluated by Make in each real object's flag context.

The Make exporter runs dependency-free sibling targets into a temporary
directory. Collection replaces the requested database only after every entry
has arrived. No compiler, source discovery, or platform flag list lives here.
"""
import json
import os
from pathlib import Path
import sys
import tempfile


def entry_path(directory, source):
    path = Path(source)
    if path.is_absolute() or '..' in path.parts or path.suffix != '.cc':
        raise ValueError(f'invalid translation-unit path: {source}')
    return Path(directory) / (source + '.json')


def main(argv):
    if not argv:
        raise ValueError('expected entry or collect')
    if argv[0] == 'entry':
        if len(argv) < 6 or not argv[1] or argv[3] != '--':
            raise ValueError('entry needs directory, source, -- and compiler arguments')
        directory, source = argv[1:3]
        output = entry_path(directory, source)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            'directory': str(Path.cwd()), 'file': source,
            'arguments': argv[4:],
        }) + '\n', encoding='utf-8')
    elif argv[0] == 'collect':
        if len(argv) < 4:
            raise ValueError('collect needs output, directory and sources')
        output, directory, *sources = argv[1:]
        if len(set(sources)) != len(sources):
            raise ValueError('duplicate translation unit in export')
        entries = []
        for source in sources:
            entry = json.loads(entry_path(directory, source).read_text(encoding='utf-8'))
            if entry['file'] != source or entry['directory'] != str(Path.cwd()):
                raise ValueError(f'compile entry does not match requested TU: {source}')
            entries.append(entry)
        target = Path(output)
        if not target.is_absolute():
            target = Path(__file__).resolve().parents[2] / target
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=target.parent,
                                             prefix=target.name + '.',
                                             delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(entries, stream, indent=2)
                stream.write('\n')
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    else:
        raise ValueError(f'unknown export operation: {argv[0]}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError, KeyError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(2)
