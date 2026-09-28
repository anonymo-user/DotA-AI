"""Minimal ctypes wrapper over StormLib for reading and writing WC3 .w3x (MPQ) archives."""
import ctypes, os, sys, glob


def _preload_libstdcpp():
    """libstorm.so needs a recent libstdc++. Discover one instead of hardcoding a path:
    $W3X_LIBSTDCPP_DIR, then $CONDA_PREFIX/lib, then common conda envs, else the system copy."""
    candidates = []
    if os.environ.get("W3X_LIBSTDCPP_DIR"):
        candidates.append(os.environ["W3X_LIBSTDCPP_DIR"])
    if os.environ.get("CONDA_PREFIX"):
        candidates.append(os.path.join(os.environ["CONDA_PREFIX"], "lib"))
    home = os.path.expanduser("~")
    candidates += glob.glob(os.path.join(home, "miniconda3", "envs", "*", "lib"))
    candidates += glob.glob(os.path.join(home, "miniconda3", "lib"))
    candidates += glob.glob(os.path.join(home, "anaconda3", "envs", "*", "lib"))
    for d in candidates:
        so = os.path.join(d, "libstdc++.so.6")
        if os.path.exists(so):
            os.environ["LD_LIBRARY_PATH"] = d + ":" + os.environ.get("LD_LIBRARY_PATH", "")
            try:
                ctypes.CDLL(so, mode=ctypes.RTLD_GLOBAL); return
            except OSError:
                continue


_preload_libstdcpp()
_DIR = os.path.dirname(os.path.abspath(__file__))
S = ctypes.CDLL(os.path.join(_DIR, "libstorm.so"), use_errno=True)

S.SFileOpenArchive.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
S.SFileOpenArchive.restype = ctypes.c_int
S.SFileCreateArchive.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
S.SFileCreateArchive.restype = ctypes.c_int
S.SFileCloseArchive.argtypes = [ctypes.c_void_p]
S.SFileOpenFileEx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
S.SFileOpenFileEx.restype = ctypes.c_int
S.SFileGetFileSize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
S.SFileGetFileSize.restype = ctypes.c_uint
S.SFileReadFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p]
S.SFileReadFile.restype = ctypes.c_int
S.SFileCloseFile.argtypes = [ctypes.c_void_p]
S.SFileCreateFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_ulonglong, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
S.SFileCreateFile.restype = ctypes.c_int
S.SFileWriteFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
S.SFileWriteFile.restype = ctypes.c_int
S.SFileFinishFile.argtypes = [ctypes.c_void_p]
S.SFileFinishFile.restype = ctypes.c_int
S.SErrGetLastError.argtypes = []
S.SErrGetLastError.restype = ctypes.c_uint


class SFILE_FIND_DATA(ctypes.Structure):
    _fields_ = [("cFileName", ctypes.c_char * 1024), ("szPlainName", ctypes.c_char_p),
                ("dwHashIndex", ctypes.c_uint), ("dwBlockIndex", ctypes.c_uint),
                ("dwFileSize", ctypes.c_uint), ("dwFileFlags", ctypes.c_uint),
                ("dwCompSize", ctypes.c_uint), ("dwFileTimeLo", ctypes.c_uint),
                ("dwFileTimeHi", ctypes.c_uint), ("lcLocale", ctypes.c_uint)]


S.SFileFindFirstFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(SFILE_FIND_DATA), ctypes.c_char_p]
S.SFileFindFirstFile.restype = ctypes.c_void_p
S.SFileFindNextFile.argtypes = [ctypes.c_void_p, ctypes.POINTER(SFILE_FIND_DATA)]
S.SFileFindNextFile.restype = ctypes.c_int
S.SFileFindClose.argtypes = [ctypes.c_void_p]

MPQ_OPEN_READ_ONLY = 0x00000100
MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_REPLACEEXISTING = 0x80000000
MPQ_COMPRESSION_ZLIB = 0x02
MPQ_CREATE_ARCHIVE_V1 = 0x00000000
MPQ_CREATE_LISTFILE = 0x00100000
SFILE_INVALID_SIZE = 0xFFFFFFFF


def _err():
    return S.SErrGetLastError()


class Archive:
    def __init__(self, path):
        self.h = ctypes.c_void_p()
        if not S.SFileOpenArchive(path.encode(), 0, MPQ_OPEN_READ_ONLY, ctypes.byref(self.h)):
            raise OSError(f"open failed err={_err()} path={path}")
        self.path = path

    @classmethod
    def create(cls, path, max_files, flags=MPQ_CREATE_ARCHIVE_V1 | MPQ_CREATE_LISTFILE):
        """Create a new empty MPQ (written at file offset 0). max_files sizes the hash
        table (rounded up to a power of two)."""
        if os.path.exists(path):
            os.remove(path)
        h = ctypes.c_void_p()
        if not S.SFileCreateArchive(path.encode(), flags, max_files, ctypes.byref(h)):
            raise OSError(f"create archive failed err={_err()} path={path}")
        self = cls.__new__(cls)
        self.h = h
        self.path = path
        return self

    def close(self):
        if self.h:
            S.SFileCloseArchive(self.h); self.h = None

    def __enter__(self): return self
    def __exit__(self, *a): self.close()

    def list(self):
        names, fd = [], SFILE_FIND_DATA()
        hf = S.SFileFindFirstFile(self.h, b"*", ctypes.byref(fd), None)
        if not hf:
            return names
        try:
            while True:
                names.append(fd.cFileName.decode("utf-8", "replace"))
                if not S.SFileFindNextFile(hf, ctypes.byref(fd)):
                    break
        finally:
            S.SFileFindClose(hf)
        return names

    def read(self, name):
        fh = ctypes.c_void_p()
        if not S.SFileOpenFileEx(self.h, name.encode(), 0, ctypes.byref(fh)):
            raise KeyError(f"no file {name} err={_err()}")
        try:
            size = S.SFileGetFileSize(fh, None)
            if size == SFILE_INVALID_SIZE:
                raise OSError(f"size fail {name}")
            buf = ctypes.create_string_buffer(size)
            read = ctypes.c_uint(0)
            if not S.SFileReadFile(fh, buf, size, ctypes.byref(read), None) and read.value != size:
                raise OSError(f"read fail {name} err={_err()}")
            return buf.raw[:read.value]
        finally:
            S.SFileCloseFile(fh)

    def has(self, name):
        fh = ctypes.c_void_p()
        if S.SFileOpenFileEx(self.h, name.encode(), 0, ctypes.byref(fh)):
            S.SFileCloseFile(fh); return True
        return False

    def write(self, name, data):
        """Add a file (archive must be created writable)."""
        fh = ctypes.c_void_p()
        flags = MPQ_FILE_COMPRESS | MPQ_FILE_REPLACEEXISTING
        if not S.SFileCreateFile(self.h, name.encode(), 0, len(data), 0, flags, ctypes.byref(fh)):
            raise OSError(f"create fail {name} err={_err()}")
        try:
            if not S.SFileWriteFile(fh, data, len(data), MPQ_COMPRESSION_ZLIB):
                raise OSError(f"write fail {name} err={_err()}")
        finally:
            if not S.SFileFinishFile(fh):
                raise OSError(f"finish fail {name} err={_err()}")


if __name__ == "__main__":
    with Archive(sys.argv[1]) as a:
        for n in sorted(a.list()):
            print(n)
