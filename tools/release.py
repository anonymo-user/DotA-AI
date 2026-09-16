#!/usr/bin/env python3
"""Version and map-name helpers, derived from the top-level VERSION file."""
import os, struct

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)

BASE_NAME = "DotA v6.83d AI"
PLACEHOLDER = "@@AIVER@@"      # version-number token in the in-game name banners
RELEASE_TOKEN = "@@RELEASE@@"  # full-name token (map header)
NAME_FILES = ("war3map.wts", "war3mapskin.txt")

HM3W_MAGIC = b"HM3W"
HEADER_SIZE = 512


def version():
    """Version string from the VERSION file, e.g. '1.57'."""
    return open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()


def release_name():
    """Plain map name for the .w3x filename and lobby header."""
    return f"{BASE_NAME} {version()}"


def wts_title():
    """In-game title string."""
    return f"DotA v6.83d |c00dd8dffAI {version()}|r"


def upkeep_label():
    """Upkeep label string."""
    return f"v6.83d |c00dd8dffAI|r |c00fff864{version()}|r"


def header_name():
    """Name written into the map header."""
    return release_name()


def inject(name, data):
    """Substitute the version placeholders in a file's bytes, if present."""
    data = data.replace(RELEASE_TOKEN.encode(), release_name().encode())
    data = data.replace(PLACEHOLDER.encode(), version().encode())
    return data


def patch_hm3w(path):
    """Set the map name in the .w3x header, preserving the other header fields and its size."""
    with open(path, "rb") as fh:
        data = bytearray(fh.read())
    if bytes(data[:4]) != HM3W_MAGIC:
        raise ValueError(f"{path}: not an HM3W-prefixed map (magic={bytes(data[:4])!r})")
    unknown = struct.unpack_from("<I", data, 4)[0]
    end = data.index(b"\x00", 8)
    old_name = data[8:end].decode("latin-1")
    flags, players = struct.unpack_from("<II", data, end + 1)
    hdr = bytearray(HM3W_MAGIC)
    hdr += struct.pack("<I", unknown)
    hdr += header_name().encode("latin-1") + b"\x00"
    hdr += struct.pack("<II", flags, players)
    if len(hdr) > HEADER_SIZE:
        raise ValueError(f"HM3W header too long ({len(hdr)} > {HEADER_SIZE})")
    hdr += b"\x00" * (HEADER_SIZE - len(hdr))
    data[:HEADER_SIZE] = hdr
    with open(path, "wb") as fh:
        fh.write(data)
    return old_name, header_name()


def read_hm3w_name(path):
    """Return the current map name from the .w3x header."""
    with open(path, "rb") as fh:
        data = fh.read(HEADER_SIZE)
    if data[:4] != HM3W_MAGIC:
        return None
    return data[8:data.index(b"\x00", 8)].decode("latin-1")


if __name__ == "__main__":
    print(release_name())
