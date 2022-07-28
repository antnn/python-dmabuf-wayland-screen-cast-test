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

___Gio___ = CDLL("libgio-2.0.so.0")

G_DBUS_SIGNAL_FLAGS_NO_MATCH_RULE = 0
G_DBUS_SIGNAL_FLAGS_NONE = 0
G_DBUS_PROXY_FLAGS_NONE = 0
G_DBUS_CALL_FLAGS_NONE = 0
G_BUS_TYPE_SESSION = 2
G_VARIANT_TYPE_VARDICT = b'a{sv}'
PLATFORM_C_MAXINT = 2 ** (struct.Struct('i').size * 8 - 1) - 1

"""Gio type aliases"""


class GBusType(c_int):
    pass


class GCancellableP(c_void_p):
    pass


class GDBusConnectionP(c_void_p):
    pass


class GDBusInterfaceInfoP(c_void_p):
    pass


class GDBusProxyP(c_void_p):
    pass


class GVariantBuilderP(c_void_p):
    pass


class GDBusProxyFlags(c_int):
    pass


class GVariantTypeP(c_char_p):
    pass


class CFunctionType(c_void_p):
    pass


class GDBusSignalFlags(c_int):
    pass


class GDBusSignalCallback(CFunctionType):
    pass


class GDestroyNotify(CFunctionType):
    pass


class GVariantP(c_void_p):
    pass


class GDBusSignalCallbackP(c_void_p):
    pass


class GDBusCallFlags(c_int):
    pass


class GMainContextP(c_void_p):
    pass


class GMainLoopP(c_void_p):
    pass


class GVariantIterP(c_void_p):
    pass


class GUnixFDListP(c_void_p):
    pass


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

class GError(object):
    pass

class _GError(Structure):
    def todict(self) -> GError:
        obj = GError({"domain": self.domain, "code": self.code, "message": self.message})
        return obj

    _fields_ = [
        ("domain", c_uint32),
        ("code", c_int),
        ("message", c_char_p)]


___Gio___.g_error_free.restype = None
___Gio___.g_error_free.argtypes = [POINTER(_GError)]


def g_error_free(error: POINTER(_GError)):
    ___Gio___.g_error_free(error)


___Gio___.g_bus_get_sync.restype = GDBusConnectionP
___Gio___.g_bus_get_sync.argtypes = [GBusType, GCancellableP,
                                     POINTER(POINTER(_GError))]


def g_bus_get_sync(bus_type: GBusType,
                   cancellable=None) -> Result[GDBusConnectionP, GError]:
    error = POINTER(_GError)()
    val: GDBusConnectionP = ___Gio___.g_bus_get_sync(bus_type, cancellable, byref(error))
    if val is None:
        err = error.contents
        err = err.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(val)


___Gio___.g_dbus_proxy_new_sync.restype = GDBusProxyP
___Gio___.g_dbus_proxy_new_sync.argtypes = [GDBusConnectionP,
                                            GDBusProxyFlags,
                                            GDBusInterfaceInfoP,
                                            c_char_p,
                                            c_char_p,
                                            c_char_p,
                                            GCancellableP,
                                            POINTER(POINTER(_GError))]


def g_dbus_proxy_new_sync(connection: GDBusConnectionP,
                          flags: GDBusProxyFlags,
                          info: GDBusInterfaceInfoP,
                          bus_name: str,
                          object_path: str,
                          interface_name: str,
                          cancellable: GCancellableP = None) -> Result[GDBusProxyP, GError]:
    error = POINTER(_GError)()
    proxy: GDBusProxyP = ___Gio___.g_dbus_proxy_new_sync(
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
___Gio___.g_dbus_connection_get_unique_name.argtypes = [GDBusConnectionP]


def g_dbus_connection_get_unique_name(connection: GDBusConnectionP) -> bytes:
    # Do not free const gchar * returned by this function
    return ___Gio___.g_dbus_connection_get_unique_name(connection)


___Gio___.g_variant_builder_unref.argtypes=[GVariantBuilderP]
def g_variant_builder_unref(builder: GVariantBuilderP): 
    ___Gio___.g_variant_builder_unref(builder)


___Gio___.g_variant_builder_new.restype = GVariantBuilderP
___Gio___.g_variant_builder_new.argtypes = [GVariantTypeP]


def g_variant_builder_new(v_type: GVariantTypeP) -> GVariantBuilderP:
    return ___Gio___.g_variant_builder_new(v_type)


""" 
g_variant_builder_add is VA function
From Pyton _ctypes/callproc.c 
        bool is_variadic = (argtypecount != 0 && argcount > argtypecount)
"""


def g_variant_builder_add(builder: GVariantBuilderP, format_string: str, *args):
    argtypes_ = [GVariantBuilderP, c_char_p]
    args_ = [builder, format_string.encode('utf-8')]
    args_, argtypes_ = ___va___(args_, argtypes_, *args)
    ___Gio___.g_variant_builder_add.argtypes = argtypes_
    ___Gio___.g_variant_builder_add(*args_)


___Gio___.g_variant_new_string.restype = GVariantP
___Gio___.g_variant_new_string.argtypes = [c_char_p]


def g_variant_new_string(variant_string: str) -> GVariantP:
    return ___Gio___.g_variant_new_string(variant_string.encode('utf-8'))


___Gio___.g_dbus_connection_signal_subscribe.restype = c_int
___Gio___.g_dbus_connection_signal_subscribe.argtypes = [GDBusConnectionP,
                                                         c_char_p,
                                                         c_char_p,
                                                         c_char_p,
                                                         c_char_p,
                                                         c_char_p,
                                                         GDBusSignalFlags,
                                                         c_void_p,  # GDBusSignalCallbackP,
                                                         c_void_p,
                                                         GDestroyNotify]


def g_dbus_connection_signal_subscribe(connection: GDBusConnectionP,
                                       sender: str,
                                       interface_name: str,
                                       member: str,
                                       object_path: str,
                                       arg0: str,
                                       flags: GDBusSignalFlags,
                                       callback: GDBusSignalCallback,
                                       user_data: c_void_p,
                                       user_data_free_func: GDestroyNotify) -> c_int:
    connection = GDBusConnectionP(connection.value)
    arg0_ = arg0.encode('utf-8') if arg0 else None
    return ___Gio___.g_dbus_connection_signal_subscribe(connection,
                                                        sender.encode('utf-8'),
                                                        interface_name.encode('utf-8'),
                                                        member.encode('utf-8'),
                                                        object_path,
                                                        arg0_, flags, callback, user_data,
                                                        user_data_free_func)


# void
def g_variant_get(value: GVariantP, format_string: str, *args):
    argtypes_ = [GVariantP, c_char_p]
    args_ = [value, format_string.encode('utf-8')]
    args_, argtypes_ = ___va___(args_, argtypes_, *args)
    ___Gio___.g_variant_get.argtypes = argtypes_
    ___Gio___.g_variant_get(*args_)


___Gio___.g_dbus_proxy_call_sync.restype = GVariantP
___Gio___.g_dbus_proxy_call_sync.argtypes = [GDBusProxyP,
                                             c_char_p,
                                             GVariantP,
                                             GDBusCallFlags,
                                             c_int,
                                             GCancellableP,
                                             POINTER(POINTER(_GError))]


def g_dbus_proxy_call_sync(proxy: GDBusProxyP,
                           method_name: str,
                           parameters: GVariantP,
                           flags: GDBusCallFlags,
                           timeout_msec: int,
                           cancellable: GCancellableP) -> Result[GVariantP, GError]:
    error = POINTER(_GError)()
    variant = ___Gio___.g_dbus_proxy_call_sync(proxy, method_name.encode('utf-8'),
                                               parameters, flags, timeout_msec, cancellable,
                                               byref(error))
    if variant is None:
        err = error.contents.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(variant)


___Gio___.g_variant_unref.argtypes=[GVariantP]
def g_variant_unref(value: GVariantP):
    ___Gio___.g_variant_unref(value)


___Gio___.g_variant_new.restype = GVariantP


def g_variant_new(format_string: str, *args) -> GVariantP:
    argtypes_ = [c_char_p]
    args_ = [format_string.encode('utf-8')]
    args_, argtypes_ = ___va___(args_, argtypes_, *args)
    ___Gio___.g_variant_new.argtypes = argtypes_
    return ___Gio___.g_variant_new(*args_)


___Gio___.g_cancellable_new.restype = GCancellableP


def g_cancellable_new() -> GCancellableP:
    return ___Gio___.g_cancellable_new()


___Gio___.g_main_loop_new.restype = GMainLoopP
___Gio___.g_main_loop_new.argtypes = [GMainContextP, c_bool]


def g_main_loop_new(context: GMainContextP, is_running: bool) -> GMainLoopP:
    return ___Gio___.g_main_loop_new(context, is_running)


___Gio___.g_main_loop_run.argtypes = [GMainLoopP]


def g_main_loop_run(loop: GMainLoopP):
    ___Gio___.g_main_loop_run(loop)


___Gio___.g_variant_lookup_value.restype = GVariantP
___Gio___.g_variant_lookup_value.argtypes = [GVariantP, c_char_p, GVariantTypeP]


def g_variant_lookup_value(dictionary: GVariantP, key: str, expected_type: GVariantTypeP) -> GVariantP:
    return ___Gio___.g_variant_lookup_value(dictionary, key.encode('utf-8'), expected_type)


___Gio___.g_variant_dup_string.restype = POINTER(c_char)
___Gio___.g_variant_dup_string.argtypes = [GVariantP, POINTER(c_ulong)]


def g_variant_dup_string(value: GVariantP, length: POINTER(c_ulong)) -> c_char_p:
    # Do not edit Python implicitly converts it to copy bytes array and frees the copy
    return cast(___Gio___.g_variant_dup_string(value, length),  POINTER(c_char))


___Gio___.g_variant_new_uint32.restype = GVariantP
___Gio___.g_variant_new_uint32.argtypes = [c_uint32]


def g_variant_new_uint32(value) -> GVariantP:
    return ___Gio___.g_variant_new_uint32(c_uint32(value))


___Gio___.g_variant_new_boolean.restype = GVariantP
___Gio___.g_variant_new_boolean.argtypes = [c_bool]


def g_variant_new_boolean(value: bool) -> GVariantP:
    return ___Gio___.g_variant_new_boolean(value)


___Gio___.g_dbus_proxy_get_cached_property.restype = GVariantP
___Gio___.g_dbus_proxy_get_cached_property.argtypes = [GDBusProxyP, c_char_p]


def g_dbus_proxy_get_cached_property(proxy: GDBusProxyP, property_name: str) -> GVariantP:
    return ___Gio___.g_dbus_proxy_get_cached_property(proxy, property_name.encode('utf-8'))


___Gio___.g_variant_lookup.restype = c_bool


def g_variant_lookup(dictionary: GVariantP, key: str, format_string: str, *args) -> bool:
    argtypes_ = [GVariantP, c_char_p, c_char_p]
    args_ = [dictionary, key.encode('utf-8'), format_string.encode('utf-8')]
    args_, argtypes_ = ___va___(args_, argtypes_, *args)
    ___Gio___.g_variant_lookup.argtypes = argtypes_
    return ___Gio___.g_variant_lookup(*args_)


___Gio___.g_variant_iter_next.restype = c_bool


def g_variant_iter_next(iter_: GVariantIterP, format_string: str, *args) -> bool:
    argtypes_ = [GVariantIterP, c_char_p]
    args_ = [iter_, format_string.encode('utf-8')]
    args_, argtypes_ = ___va___(args_, argtypes_, *args)
    ___Gio___.g_variant_iter_next.argtypes = argtypes_
    return ___Gio___.g_variant_iter_next(*args_)


___Gio___.g_dbus_proxy_call_with_unix_fd_list_sync.restype = GVariantP
___Gio___.g_dbus_proxy_call_with_unix_fd_list_sync.argtypes = [GDBusProxyP,
                                                               c_char_p,
                                                               GVariantP,
                                                               GDBusCallFlags,
                                                               c_int,
                                                               GUnixFDListP,
                                                               POINTER(GUnixFDListP),  # TODO check if it works
                                                               GCancellableP,
                                                               POINTER(POINTER(_GError))]


def g_dbus_proxy_call_with_unix_fd_list_sync(proxy: GDBusProxyP,
                                             method_name: str,
                                             parameters: GVariantP,
                                             flags: GDBusCallFlags,
                                             timeout_msec: int,
                                             fd_list: GUnixFDListP,
                                             out_fd_list: POINTER(GUnixFDListP),
                                             cancellable: GCancellableP) -> Result[GVariantP, GError]:
    error = POINTER(_GError)()
    variant = ___Gio___.g_dbus_proxy_call_with_unix_fd_list_sync(proxy, method_name.encode('utf-8'),
                                                                 parameters, flags,
                                                                 timeout_msec, fd_list, out_fd_list,
                                                                 cancellable, byref(error))
    if variant is None:
        err = error.contents.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(variant)


___Gio___.g_unix_fd_list_get.restype = c_int
___Gio___.g_unix_fd_list_get.argtypes = [GUnixFDListP, c_int, POINTER(POINTER(_GError))]


def g_unix_fd_list_get(fdlist: GUnixFDListP, index: int) -> Result[int, GError]:
    error = POINTER(_GError)()
    val = ___Gio___.g_unix_fd_list_get(fdlist, index, byref(error))
    if val is None:
        err = error.contents.todict()
        g_error_free(error)
        return Result(error=err)
    else:
        return Result(val)

___Gio___.g_dbus_connection_signal_unsubscribe.argtypes = [GDBusConnectionP, c_uint]
def g_dbus_connection_signal_unsubscribe(connection:GDBusConnectionP, subscription_id:c_uint):
    ___Gio___.g_dbus_connection_signal_unsubscribe(connection,subscription_id)


___Gio___.g_object_unref.argtypes = [c_void_p]
def g_object_unref (object: c_void_p):
    ___Gio___.g_object_unref(object)


def ___va___(args, argtypes, *vargs):
    """Helper function for variable arguments functions"""
    for arg in vargs:
        if isinstance(arg, str):
            arg_ = cast(arg.encode('utf-8'), c_char_p)
            argtypes.append(c_char_p)
        elif isinstance(arg, c_char_p):
            arg_ = arg
            argtypes.append(c_char_p)
        elif isinstance(arg, int) or isinstance(arg, c_int):
            arg_ = arg
            argtypes.append(c_int)
        elif isinstance(arg, c_uint32):
            arg_ = arg
            argtypes.append(c_uint32)
        elif isinstance(arg, c_void_p):
            arg_ = arg
            argtypes.append(c_void_p)
        else:
            arg_ = cast(arg, c_void_p)
            argtypes.append(c_void_p)
        args.append(arg_)
    return args, argtypes
