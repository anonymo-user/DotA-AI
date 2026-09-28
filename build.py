#!/usr/bin/env python3
"""Pack the source tree in src/ into a playable Warcraft III (.w3x) map.

Usage:
  python3 build.py                     # build src/ -> ../<map name>.w3x
  python3 build.py <src_dir> <out.w3x> # build a source tree to a specific path
  python3 build.py --verify            # build twice and check output integrity
"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))
from w3x import Archive
import release


def build(src_dir, out_w3x):
    """Pack src_dir into the .w3x archive at out_w3x."""
    files = [l for l in open(os.path.join(src_dir, "_filelist.txt")).read().splitlines() if l.strip()]
    hdr = open(os.path.join(src_dir, "_hm3w.bin"), "rb").read()
    if len(hdr) != 512 or hdr[:4] != b"HM3W":
        raise ValueError(f"{src_dir}/_hm3w.bin: expected a 512-byte HM3W map header")
    tmp_mpq = out_w3x + ".mpqtmp"
    a = Archive.create(tmp_mpq, max_files=len(files) + 16)
    written = 0
    for f in files:
        disk = os.path.join(src_dir, f.replace("\\", "/"))
        if not os.path.exists(disk):
            raise FileNotFoundError(f"src missing {f}")
        a.write(f, release.inject(f, open(disk, "rb").read()))
        written += 1
    a.close()
    with open(out_w3x, "wb") as o:            # [512-byte header][MPQ]
        o.write(hdr)
        with open(tmp_mpq, "rb") as m:
            o.write(m.read())
    os.remove(tmp_mpq)
    release.patch_hm3w(out_w3x)
    return written


def check_name(src_dir):
    """Sanity-check the source name-files before building."""
    wts = open(os.path.join(src_dir, "war3map.wts"), "rb").read()
    skin = open(os.path.join(src_dir, "war3mapSkin.txt"), "rb").read()
    tok = release.PLACEHOLDER.encode()
    problems = []
    if (b"DotA v6.81b |c00dd8dffAI " + tok + b"|r") not in wts:
        problems.append("war3map.wts is missing the coloured title token")
    if (b"v6.81b |c00dd8dffAI|r |c00fff864" + tok) not in skin:
        problems.append("war3mapSkin.txt is missing the upkeep label token")
    return problems


def verify():
    """Build src/ twice and check: every archived file matches its source, the file set is
    complete, the two builds match, and the map name resolves correctly."""
    here = os.path.dirname(__file__)
    src = os.path.join(here, "src")
    name_problems = check_name(src)
    if name_problems:
        print("NAME:", "; ".join(name_problems)); return False
    want_list = [l.strip() for l in open(os.path.join(src, "_filelist.txt")) if l.strip()]
    want = {w.lower() for w in want_list}
    out1, out2 = "/tmp/_build_verify1.w3x", "/tmp/_build_verify2.w3x"
    n = build(src, out1); build(src, out2)
    a1, a2 = Archive(out1), Archive(out2)
    s1 = {f.lower(): f for f in a1.list() if f.lower() != "(listfile)"}
    s2 = {f.lower(): f for f in a2.list() if f.lower() != "(listfile)"}
    set_ok = set(s1.keys()) == want
    deterministic = s1.keys() == s2.keys() and all(a1.read(s1[k]) == a2.read(s2[k]) for k in s1)
    faithful = True
    for w in want_list:
        disk = os.path.join(src, w.replace("\\", "/"))
        if a1.read(s1[w.lower()]) != release.inject(w, open(disk, "rb").read()):
            faithful = False; break
    wts_built = a1.read(s1["war3map.wts"])
    name_ok = release.wts_title().encode() in wts_built and release.PLACEHOLDER.encode() not in wts_built
    a1.close(); a2.close()
    hdr = release.read_hm3w_name(out1)
    hdr_ok = hdr == release.header_name()
    ok = faithful and set_ok and deterministic and name_ok and hdr_ok
    extra = sorted(set(s1.keys()) - want); missing = sorted(want - set(s1.keys()))
    print(f"built {n} files; faithful={faithful} complete={set_ok} deterministic={deterministic} "
          f"named={name_ok and hdr_ok} ({release.release_name()})"
          + (f" extra={extra} missing={missing}" if not set_ok else ""))
    return ok


if __name__ == "__main__":
    args = sys.argv[1:]
    here = os.path.dirname(__file__)
    src = os.path.join(here, "src")
    if args == ["--verify"]:
        sys.exit(0 if verify() else 1)
    elif len(args) == 2:
        n = build(args[0], args[1])
        print(f"built {args[1]}: {n} files")
    elif not args:
        problems = check_name(src)
        if problems:
            print("NAME:", "; ".join(problems)); sys.exit(1)
        out = os.path.join(here, "..", f"{release.release_name()}.w3x")
        n = build(src, out)
        print(f"built {out}: {n} files (in-game name: {release.release_name()})")
    else:
        print(__doc__); sys.exit(1)
