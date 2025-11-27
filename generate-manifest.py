#!/usr/bin/env python3

import argparse
import gi
import hashlib
import json
import os
import re
import sys
from urllib import request

gi.require_version('Flatpak', '1.0')
from gi.repository import Flatpak

# Architecture conversion between debian and flatpak
DEBIAN_TO_FLATPAK_ARCH_OVERRIDES = {
    'armhf': 'arm',
    'amd64': 'x86_64',
    'arm64': 'aarch64',
}

FLATPAK_TO_DEBIAN_ARCH_OVERRIDES = \
    dict([(v, k) for k, v in DEBIAN_TO_FLATPAK_ARCH_OVERRIDES.items()])

def canonicalize_arch(arch, debian=False):
    """Transform arch names to the canonical names used by flatpak

    If debian is True, they are instead converted to canonical debian names.
    """
    if debian:
        return FLATPAK_TO_DEBIAN_ARCH_OVERRIDES.get(arch, arch)
    else:
        return DEBIAN_TO_FLATPAK_ARCH_OVERRIDES.get(arch, arch)

def sha256(filename):
    checksum = hashlib.sha256()
    with open(filename, 'rb') as f:
        for data in iter(lambda: f.read(65536), b''):
            checksum.update(data)
    return checksum.hexdigest()

def add_fonts_module(data):
    """Add fonts module to manifest json"""

    sources = []

    for font in os.listdir('fonts'):
        if font.endswith('.zip'):
            path = 'fonts/' + font
            sources.append({ 'type': 'file',
                              'path': path,
                              'dest-filename': font.replace("+", "-"),
                              'sha256': sha256(path)})

    # Append the fonts to the end of the manifest, but before the
    # os-release scripts
    data['modules'].insert(-1, {
        'name': 'default-theme-fonts',
        'buildsystem': 'simple',
        'build-commands': [
            "mkdir -p /usr/share/fonts",
            "for font in *.zip; do unzip $font -d /usr/share/fonts/${font%.*}; done",
        ],
        'sources': sources,
    })

aparser = argparse.ArgumentParser(description='Add necessary build-args to manifest')
aparser.add_argument('--arch', metavar='ARCH',
                     help='build architecture')
aparser.add_argument('--sdk-branch',
                     help='Branch of the SDK to be built (default=master)',
                     dest='branch',
                     default='master')
aparser.add_argument('--base-runtime-version',
                     help='Version of the base runtime to be built',
                     dest='runtime_version')
aparser.add_argument('infile', metavar='FILE', nargs='?',
                     help='file to edit, stdin by default',
                     type=argparse.FileType('r'),
                     default=sys.stdin)
args = aparser.parse_args()

data = json.load(args.infile)
add_fonts_module(data)
print(json.dumps(data, indent=4))
