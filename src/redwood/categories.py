import os
import stat
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str
    color: int  # ANSI colour index, same numbering as curses.COLOR_*
    char: str  # fill used when the terminal has no colour


_EXTENSIONS = {
    "video": "mp4 mkv avi mov wmv flv webm m4v mpg mpeg vob 3gp m2ts mts",
    "audio": "mp3 flac wav ogg oga m4a aac wma opus aiff ape mid midi",
    "image": "jpg jpeg png gif bmp tif tiff webp svg heic heif raw cr2 nef arw dng psd xcf ico",
    "archive": (
        "zip tar gz tgz bz2 xz zst 7z rar lz4 lzma iso img dmg deb rpm jar whl apk "
        "snap squashfs qcow2 vmdk vdi vhd vhdx"
    ),
    "document": (
        "pdf doc docx xls xlsx ppt pptx odt ods odp rtf txt md rst epub djvu csv tex "
        "html htm xml json yaml yml toml log"
    ),
    "code": (
        "py pyi c h cc cpp hpp cxx js mjs ts tsx jsx java kt scala go rs rb php pl sh bash "
        "zsh lua cs swift sql css scss vue ipynb el hs ml"
    ),
    "binary": "so dll exe bin o a lib dylib pyc class ko wasm dat db sqlite pack idx",
}

CATEGORIES = [
    Category("video", 1, "#"),
    Category("audio", 5, "~"),
    Category("image", 3, "%"),
    Category("archive", 4, "="),
    Category("document", 6, "+"),
    Category("code", 2, "*"),
    Category("binary", 7, "@"),
    Category("other", 0, "."),
]
OTHER = len(CATEGORIES) - 1
BINARY = next(i for i, c in enumerate(CATEGORIES) if c.name == "binary")

_BY_EXT = {
    ext: next(i for i, c in enumerate(CATEGORIES) if c.name == name)
    for name, exts in _EXTENSIONS.items()
    for ext in exts.split()
}


def categorize(name: str, mode: int = 0) -> int:
    lower = name.lower()
    ext = os.path.splitext(lower)[1][1:]
    if ext in _BY_EXT:
        return _BY_EXT[ext]
    # Versioned shared libraries (libfoo.so.6) and executables like python3.13.
    if ".so." in lower or (stat.S_ISREG(mode) and mode & 0o111):
        return BINARY
    return OTHER
