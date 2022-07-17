#!/bin/env python
# Tested with
# Python 3.9.13 (main, Jun  9 2022, 00:00:00)
# [GCC 12.1.1 20220507 (Red Hat 12.1.1-1)] on linux (fedora:36, docker)

# import mss


# from egl import *


# Framebuffer Format Modifiers https://youtu.be/g5T5wSCXkH4?t=3131
from portal import portal

from ctypes import *

libc = CDLL("libc.so.6")


def main():
    portal()

# client_extensions = egl.eglQueryString(egl.EGL_NO_DISPLAY, egl.EGL_EXTENSIONS)
# client_extensions = client_extensions.split(" ");
# print(client_extensions)


main()
