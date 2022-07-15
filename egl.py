#!/bin/env python
# Tested with
# Python 3.9.13 (main, Jun  9 2022, 00:00:00)
# [GCC 12.1.1 20220507 (Red Hat 12.1.1-1)] on linux (fedora:36, docker)
# Using c_void_p to keep this file as simple as possible,
# I think we do not need to reimplement Gio in Python here
# We just need to get DMABuf or Memfd fd

from ctypes import *

EGL_NO_DISPLAY = 0
EGL_EXTENSIONS = 0x3055
EGL_PLATFORM_WAYLAND_KHR = c_uint(0x31D8)
EGLDisplay = c_void_p
EGLint = c_int32
EGLenum = c_uint
EGL_DEFAULT_DISPLAY = c_void_p(0)
EGLAttrib_p = c_void_p

EGL_lib = CDLL("libEGL.so.1")


EGL_lib.eglQueryString.restype = c_char_p
EGL_lib.eglQueryString.argtypes = [EGLDisplay, EGLint]


def eglQueryString(dpy: EGLDisplay, name: EGLint):
    return EGL_lib.eglQueryString(dpy, name).decode()

EGL_lib.EglGetPlatformDisplay.restype = c_void_p
EGL_lib.EglGetPlatformDisplay.argtypes = [EGLenum, c_void_p, EGLAttrib_p]




def EglGetPlatformDisplay(platform: EGLenum, native_display: c_void_p,
                          attrib_list: EGLAttrib_p):
    return EGL_lib.EglGetPlatformDisplay(platform, native_display, attrib_list)


class DMABuf:
    class EGLStruct:
        extensions = None
        display: EGLDisplay = EGL_NO_DISPLAY;
        context: EGLContext = EGL_NO_CONTEXT;
    egl: EGLStruct
    def __init__(self):
        client_extensions = EGL_lib.eglQueryString(EGL_NO_DISPLAY, EGL_EXTENSIONS)
        client_extensions = client_extensions.split(" ");

        has_platform_base_ext = False
        has_platform_gbm_ext = False
        has_khr_platform_gbm_ext = False
        for ext in client_extensions:
            if ext == "EGL_EXT_platform_base":
                has_platform_base_ext = True
                continue
            elif ext == "EGL_MESA_platform_gbm" :
                has_platform_gbm_ext = True
                continue
            elif ext == "EGL_KHR_platform_gbm":
                has_khr_platform_gbm_ext = True
                continue

        if (not has_platform_base_ext or not has_platform_gbm_ext or
        not has_khr_platform_gbm_ext):
            print("One of required EGL extensions is missing")
            return

        self.egl.display = EglGetPlatformDisplay(EGL_PLATFORM_WAYLAND_KHR,
                                                 EGL_DEFAULT_DISPLAY, None);
        if self.egl.display == EGL_NO_DISPLAY:
            RTC_LOG(LS_ERROR) << "Failed to obtain default EGL display: "
            << FormatEGLError(EglGetError()) << "\n"
            << "Defaulting to using first available render node"
        render_node = GetRenderNode();
        if (!render_node):
            return;

drm_fd_ = open(render_node->c_str(), O_RDWR);

if (drm_fd_ < 0) {
RTC_LOG(LS_ERROR) << "Failed to open drm render node: "
<< strerror(errno);
return;
}

gbm_device_ = gbm_create_device(drm_fd_);

if (!gbm_device_)
{
RTC_LOG(LS_ERROR) << "Cannot create GBM device: " << strerror(errno);
close(drm_fd_);
return;
}

// Use
eglGetPlatformDisplayEXT()
to
get
the
display
pointer
// if the
implementation
supports
it. \
    egl_.display = \
    EglGetPlatformDisplayEXT(EGL_PLATFORM_GBM_KHR, gbm_device_, nullptr);
}

if (egl_.display == EGL_NO_DISPLAY) {
RTC_LOG(LS_ERROR) << "Error during obtaining EGL display: "
<< FormatEGLError(EglGetError());
return;
}

EGLint
major, minor;
if (EglInitialize(egl_.display, & major, & minor) == EGL_FALSE) {
RTC_LOG(LS_ERROR) << "Error during eglInitialize: "
<< FormatEGLError(EglGetError());
return;
}

if (EglBindAPI(EGL_OPENGL_API) == EGL_FALSE) {
RTC_LOG(LS_ERROR) << "bind OpenGL API failed";
return;
}

egl_.context = \
    EglCreateContext(egl_.display, nullptr, EGL_NO_CONTEXT, nullptr);

if (egl_.context == EGL_NO_CONTEXT)
{
RTC_LOG(LS_ERROR) << "Couldn't create EGL context: "
<< FormatGLError(EglGetError());
return;
}

if (!GetClientExtensions(egl_.display, EGL_EXTENSIONS)) {
return;
}

bool
has_image_dma_buf_import_modifiers_ext = false;

for (const auto & extension: egl_.extensions)
{
if (extension == "EGL_EXT_image_dma_buf_import") {
has_image_dma_buf_import_ext_ = true;
continue;
} else if (extension == "EGL_EXT_image_dma_buf_import_modifiers") {
has_image_dma_buf_import_modifiers_ext = true;
continue;
}
}

if (has_image_dma_buf_import_ext_ & & has_image_dma_buf_import_modifiers_ext) {
EglQueryDmaBufFormatsEXT = (eglQueryDmaBufFormatsEXT_func)EglGetProcAddress(
"eglQueryDmaBufFormatsEXT");
EglQueryDmaBufModifiersEXT =
(eglQueryDmaBufModifiersEXT_func)
EglGetProcAddress(
"eglQueryDmaBufModifiersEXT");
}

RTC_LOG(LS_INFO) << "Egl initialization succeeded";
egl_initialized_ = true;
