#!/bin/env python
# Tested with
# Python 3.9.13 (main, Jun  9 2022, 00:00:00)
# [GCC 12.1.1 20220507 (Red Hat 12.1.1-1)] on linux (fedora:36, docker)
# Using c_void_p to keep this file as simple as possible,
# I think we do not need to reimplement Gio in Python here
# We just need to get DMABuf or Memfd fd
import struct
from ctypes import *
from typing import Generic, TypeVar

T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    _value: T = None
    _error: E = None

    def __init__(self, value: T = None, error: E = None):
        self._value = value
        self._error = error

    def unwrap(self):
        if not self.is_ok():
            raise TypeError("Result value is error")
        else:
            return self.unwrap_unchecked()

    def unwrap_unchecked(self):
        return self._value

    def is_ok(self):
        return self._value is not None

    def error(self):
        return self._error


___Gio___ = CDLL("libgio-2.0.so.0")


class GError(Structure):
    def todict(self):
        obj = {"domain": self.domain, "code": self.code, "message": self.message}
        return obj

    _fields_ = [
        ("domain", c_uint32),
        ("code", c_int),
        ("message", c_char_p)]


class GBusType(c_int):
    G_BUS_TYPE_SESSION = c_int(2).value


class GDBusProxyFlags(c_uint):
    G_DBUS_PROXY_FLAGS_NONE = c_uint(0).value
    G_DBUS_PROXY_FLAGS_DO_NOT_LOAD_PROPERTIES = c_uint(1).value
    G_DBUS_PROXY_FLAGS_DO_NOT_CONNECT_SIGNALS = c_uint(2).value
    G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START = c_uint(4).value
    G_DBUS_PROXY_FLAGS_GET_INVALIDATED_PROPERTIES = c_uint(8).value
    G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START_AT_CONSTRUCTION = c_uint(16).value
    G_DBUS_PROXY_FLAGS_NO_MATCH_RULE = c_uint(32).value


___Gio___.g_error_free.restype = None
___Gio___.g_error_free.argtypes = [POINTER(GError)]


def g_error_free(error: POINTER(GError)):
    ___Gio___.g_error_free(error)


GCancellable_p = c_void_p
___Gio___.g_bus_get_sync.restype = c_void_p
___Gio___.g_bus_get_sync.argtypes = [c_int, POINTER(
    GCancellable_p), POINTER(POINTER(GError))]


def g_bus_get_sync(bus_type: GBusType,
                   cancellable=None):
    error = POINTER(GError)()
    # (GBusType bus_type, GCancellable *cancellable,GError **error)
    val: GDBusConnection_p = ___Gio___.g_bus_get_sync(bus_type, cancellable, byref(error))
    if (val is None):
        err = error.contents
        err = err.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(val)


GDBusConnection_p = c_void_p
GDBusInterfaceInfo_p = c_void_p
GDBusProxy_p = c_void_p
___Gio___.g_dbus_proxy_new_sync.restype = GDBusProxy_p
___Gio___.g_dbus_proxy_new_sync.argtypes = [
    GDBusConnection_p,
    GDBusProxyFlags,
    GDBusInterfaceInfo_p,
    c_char_p,
    c_char_p,
    c_char_p,
    GCancellable_p,
    POINTER(POINTER(GError))]


def g_dbus_proxy_new_sync(connection: GDBusConnection_p, flags: GDBusProxyFlags,
                          info: GDBusInterfaceInfo_p, bus_name: str,
                          object_path: str,
                          interface_name: str,
                          cancellable: GCancellable_p = None):
    error = POINTER(GError)()
    proxy: GDBusProxy_p = ___Gio___.g_dbus_proxy_new_sync(
        connection,
        flags,
        info,
        bus_name.encode('utf-8'),
        object_path.encode('utf-8'),
        interface_name.encode('utf-8'),
        cancellable,
        byref(error))
    if proxy is None:
        err = error.contents.toDict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(proxy)


___Gio___.g_dbus_connection_get_unique_name.restype = c_char_p
___Gio___.g_dbus_connection_get_unique_name.argtypes = [c_void_p]


def g_dbus_connection_get_unique_name(connection: GDBusConnection_p):
    # Do not free const gchar * returned by this function
    # c_char_p return is automatically converted to an
    # immutable Python byte's object
    return ___Gio___.g_dbus_connection_get_unique_name(connection)


G_VARIANT_TYPE_VARDICT = b'a{sv}'
PLATFORM_C_MAXINT = 2 ** (struct.Struct('i').size * 8 - 1) - 1
GVariantBuilder_p = c_void_p
GVariantType_p = c_char_p
___Gio___.g_variant_builder_new.restype = GVariantBuilder_p
___Gio___.g_variant_builder_new.argtypes = [c_void_p]


def g_variant_builder_new(v_type: GVariantType_p) -> GVariantBuilder_p:
    return ___Gio___.g_variant_builder_new(v_type)


def __to_va(*args):
    output = []
    argtypes = []
    for arg in args:
        if arg is str:
            # arg_ = cast(arg, c_char_p)
            argtypes.append(c_char_p)
        elif arg is int:
            # arg_ = cast(arg, c_int)
            argtypes.append(c_int)
        else:
            arg_ = cast(arg, c_void_p)
            argtypes.append(c_void_p)
        output.append(arg)
    return output, argtypes


___Gio___.g_variant_builder_add.restype = c_void_p


# Note from _ctypes/callproc.c
# bool is_variadic = (argtypecount != 0 && argcount > argtypecount)
def g_variant_builder_add(builder: GVariantBuilder_p, format_string: str, *args):
    argtypes_ = [c_void_p, c_char_p]
    args_ = [builder, format_string.encode('utf-8')]
    va_, va_argtypes_ = __to_va(*args)
    args_.extend(va_)
    argtypes_.extend(va_argtypes_)

    ___Gio___.g_variant_builder_add.argtypes = argtypes_
    return ___Gio___.g_variant_builder_add(*args_)


GVariant_p = c_void_p
___Gio___.g_variant_new_string.restype = c_void_p
___Gio___.g_variant_new_string.argtypes = [c_char_p]


def g_variant_new_string(variant_string: str) -> GVariant_p:
    return ___Gio___.g_variant_new_string(variant_string.encode('utf-8'))


# Note
# Make sure you keep references to CFUNCTYPE()
# objects as long as they are used from C code. ctypes doesn’t, and if you don’t,
# they may be garbage collected, crashing your program when a callback is made.
# Also, note that if the callback function is called in a thread created outside of Python’s control
# (e.g. by the foreign code that calls the callback),
# ctypes creates a new dummy Python thread on every invocation.
# This behavior is correct for most purposes,
# but it means that values stored with threading.local will not survive across different callbacks,
# even when those calls are made from the same C thread.

CFunctionType = c_void_p
GDBusSignalFlags = c_int
GDBusSignalCallback = CFunctionType
GDestroyNotify = CFunctionType
G_DBUS_SIGNAL_FLAGS_NO_MATCH_RULE = 1
___Gio___.g_dbus_connection_signal_subscribe.restype = c_int
___Gio___.g_dbus_connection_signal_subscribe.argtypes = [c_void_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p,
                                                         c_int]


def g_dbus_connection_signal_subscribe(connection: GDBusConnection_p,
                                       sender: str,
                                       interface_name: str,
                                       member: str,
                                       object_path: str,
                                       arg0: str,
                                       flags: GDBusSignalFlags,
                                       callback: GDBusSignalCallback,
                                       user_data: c_void_p,
                                       user_data_free_func: GDestroyNotify) -> c_int:
    arg0_ = arg0.encode('utf-8') if arg0 else None
    return ___Gio___.g_dbus_connection_signal_subscribe(connection, sender.encode('utf-8'),
                                                        interface_name.encode('utf-8'),
                                                        member.encode('utf-8'), object_path.encode('utf-8'),
                                                        arg0_,
                                                        flags, callback, user_data, user_data_free_func)


def g_variant_get(value: GVariant_p, format_string: str, *args):
    ___Gio___.g_variant_get.restype = c_void_p
    ___Gio___.g_variant_get.argtypes = [c_void_p, c_char_p]

    return ___Gio___.g_variant_get(value, format_string, *args)


___Gio___.g_dbus_proxy_call_sync.restype = c_void_p
___Gio___.g_dbus_proxy_call_sync.argtypes = [c_void_p, c_char_p, c_void_p, c_int, c_int, c_void_p,
                                             POINTER(POINTER(GError))]
GDBusCallFlags = c_int
G_DBUS_CALL_FLAGS_NONE = 0


def g_dbus_proxy_call_sync(proxy: GDBusProxy_p,
                           method_name: str,
                           parameters: GVariant_p,
                           flags: GDBusCallFlags,
                           timeout_msec: int,
                           cancellable: GCancellable_p):
    error = POINTER(GError)()
    variant = ___Gio___.g_dbus_proxy_call_sync(proxy, method_name.encode('utf-8'),
                                               parameters, flags, timeout_msec, cancellable,
                                               byref(error))
    if variant is None:
        err = error.contents.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(proxy)


___Gio___.g_variant_new.restype = c_void_p


def g_variant_new(format_string: str, *args):
    argtypes_ = [c_char_p]
    args_ = [format_string.encode('utf-8')]
    va_, va_argtypes_ = __to_va(*args)
    args_.extend(va_)
    argtypes_.extend(va_argtypes_)
    ___Gio___.g_variant_new.argtypes = argtypes_
    return ___Gio___.g_variant_new(*args_)


___Gio___.g_cancellable_new.restype = c_void_p


def g_cancellable_new():
    return ___Gio___.g_cancellable_new()


___Gio___.g_main_loop_new.restype = c_void_p
___Gio___.g_main_loop_new.argtypes = [c_void_p, c_bool]
GMainContext_p = c_void_p
GMainLoop_p = c_void_p


def g_main_loop_new(context: GMainContext_p, is_running: bool):
    return ___Gio___.g_main_loop_new(context, is_running)

___Gio___.g_main_loop_run.argtypes = [c_void_p]


def g_main_loop_run(loop: GMainLoop_p):
    return ___Gio___.g_main_loop_run(loop)