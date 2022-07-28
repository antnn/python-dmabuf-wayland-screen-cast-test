# Adapted code from 
# https://webrtc.googlesource.com/src/+/93f9db7e8a6f442390bb0ed6a2ffc6fa75b2ae5f/modules/desktop_capture/linux/wayland/
import ctypes
import sys
from random import randrange

import pipewire
from gio import *

kDesktopBusName = "org.freedesktop.portal.Desktop"
kRequestInterfaceName = "org.freedesktop.portal.Request"
kDesktopPath = "/org/freedesktop/portal/desktop"
kDesktopRequestObjectPath = "/org/freedesktop/portal/desktop/request"
kSessionInterfaceName = "org.freedesktop.portal.Session"
req_path = '/org/freedesktop/portal/desktop/request'
req_iface = 'org.freedesktop.portal.Request'
scast_iface = 'org.freedesktop.portal.ScreenCast'
sender_name_ = portal_prefix = "pythonmss"


class CaptureSourceType:
    kScreen = 0b01
    kWindow = 0b10
    kAnyScreenContent = kScreen | kWindow


class CursorMode:
    """Values are set based on cursor mode property in
    xdg-desktop-portal/screencast
    https://github.com/flatpak/xdg-desktop-portal/blob/master/data/org.freedesktop.portal.ScreenCast.xml"""
    kHidden = 0b01, """Mouse cursor will not be included in any form"""
    """Mouse cursor will be part of the screen content"""
    kEmbedded = 0b10
    """Mouse cursor information will be send separately in form of metadata"""
    kMetadata = 0b100


class PersistMode:
    """Values are set based on persist mode property in
    xdg-desktop-portal/screencast
    https://github.com/flatpak/xdg-desktop-portal/blob/master/data/org.freedesktop.portal.ScreenCast.xml"""
    kDoNotPersist = 0b00, """ Do not allow to restore stream """
    """The restore token is valid as long as the application is alive. It's
       stored in memory and revoked when the application closes its DBus
       connection"""
    kTransient = 0b01
    """The restore token is stored in disk and is valid until the user manually
       revokes it"""
    kPersistent = 0b10


class PipeWireStream(Structure):
    pw_fd: c_int
    pw_stream_node_id: c_uint32
    restore_token: c_char_p
    _fields_ = [
        ("pw_fd_", c_int),
        ("pw_stream_node_id", c_uint32)
    ]


libc = CDLL("libc.so.6")
libc.free.argtypes=[c_void_p]
libc.calloc.restype = c_void_p
def take_str_ownership(str_) -> POINTER(c_char):
    """
    Prevent Python string GC. Becasuse Gio multi threading
    """
    size = len(str_)
    if not size:
        return
    _str_ = ""
    if isinstance(str_, str):
        _str_ = str_.encode("utf-8")
    else:
        _str_ = str_
    buf =cast(libc.calloc(1, size + 1), POINTER(c_char))  # NULL terminated
    libc.memcpy(buf, _str_, size)
    return buf


class Portal(Structure):
    multiple: c_bool = False
    capture_source_type: CaptureSourceType = 0
    persist_mode: PersistMode = 0
    cursor_mode: CursorMode = 0
    connection: GDBusConnectionP = None
    # proxy_request_response_handler: GDBusSignalCallback
    # sources_request_response_signal_handler: GDBusSignalCallback
    screencast_proxy: GDBusProxyP = None
    pw_streams: POINTER(PipeWireStream) = None
    cancellable: GCancellableP = None
    portal_handle: POINTER(c_char) = None # Use POINTER(c_char), c_char_p gets coverted to bytes, it is undesired behavour
    session_handle: POINTER(c_char) = None
    sources_handle: POINTER(c_char) = None
    start_handle:  POINTER(c_char) = None
    restore_token:  POINTER(c_char) = None
    session_request_signal_id: c_int =0
    sources_request_signal_id: c_int =0
    start_request_signal_id: c_int = 0
    session_closed_signal_id: c_int =0
    _fields_ = [
        ("multiple", c_bool),
        ("capture_source_type", c_uint32),
        ("connection", GDBusConnectionP),
        ("screencast_proxy", GDBusProxyP),
        ("pw_streams", POINTER(PipeWireStream)),
        ("persist_mode", c_uint32),
        ("cancellable", GCancellableP),
        ("cursor_mode", c_uint32),
        ("portal_handle", POINTER(c_char)),
        ("session_handle", POINTER(c_char)),
        ("sources_handle", POINTER(c_char)),
        ("start_handle", POINTER(c_char)),
        ("restore_token", POINTER(c_char)),
        ("session_request_signal_id", c_int),
        ("sources_request_signal_id", c_int),
        ("start_request_signal_id", c_int),
        ("session_closed_signal_id", c_int),
    ]


def new_request_path(connection: GDBusConnectionP):
    token = str(g_dbus_connection_get_unique_name(connection), "utf-8")
    path = req_path
    handle = ('%s/%s/' % (path, token)).replace(":", "").replace(".", "_")
    return handle.encode('utf-8')


def new_session_path():
    import struct
    platform_c_maxint = 2 ** (struct.Struct('i').size * 8 - 1) - 1
    token = randrange(0, platform_c_maxint)
    path = '/org/freedesktop/portal/desktop/session/%s/%s' % (
        sender_name_, token)
    return path.encode('utf-8'), token




def prepare_signal_handle(token, connection):
    sender = str(g_dbus_connection_get_unique_name(connection), "utf-8")
    sender = sender.replace(":", "").replace(".", "_")
    handle = '%s/%s/%s' % (kDesktopRequestObjectPath, sender, token)
    return handle


def setup_request_response_signal(object_path: str,
                                  callback,
                                  user_data: c_void_p,
                                  connection: GDBusConnectionP):
    return g_dbus_connection_signal_subscribe(connection,
                                              kDesktopBusName, kRequestInterfaceName, "Response",
                                              object_path, None, G_DBUS_SIGNAL_FLAGS_NO_MATCH_RULE,
                                              callback, user_data, None)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, POINTER(Portal))
def on_session_closed_signal(connection: GDBusConnectionP,
                             sender_name: c_char_p,
                             object_path: c_char_p,
                             interface_name: c_char_p,
                             signal_name: c_char_p,
                             parameters: GVariantP,
                             user_data: c_void_p):
    portal = user_data.contents
    g_dbus_connection_signal_unsubscribe(portal.connection,
                                       portal.session_closed_signal_id);
    print("session is closed")



def unsubscribe_handlers(portal: Portal):
    if portal.start_request_signal_id:
        g_dbus_connection_signal_unsubscribe(portal.connection, portal.start_request_signal_id);
        portal.start_request_signal_id = 0;

    if portal.sources_request_signal_id:
        g_dbus_connection_signal_unsubscribe(portal.connection, portal.sources_request_signal_id)
        portal.sources_request_signal_id = 0;
  
    if portal.session_request_signal_id:
        g_dbus_connection_signal_unsubscribe(portal.connection, portal.session_request_signal_id);
        portal.session_request_signal_id = 0
  

def cleanup(portal:Portal):
    unsubscribe_handlers(portal)
    libc.free(portal.session_handle)
    portal.session_handle = None
    g_object_unref(portal.cancellable)
    portal.cancellable = None
    #if (pw_fd_ != -1):
    #    close(pw_fd_)
  


def open_pipewire_remote(portal: Portal):
    print("PIPEWIRE\n")
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    outlist = GUnixFDListP(0)
    variant = g_dbus_proxy_call_with_unix_fd_list_sync(portal.screencast_proxy, "OpenPipeWireRemote",
                                                       g_variant_new("(oa{sv})",
                                                                     portal.session_handle, builder),
                                                       G_DBUS_CALL_FLAGS_NONE, -1,
                                                       None, byref(outlist),
                                                       portal.cancellable)
    if not variant:
        print("Error getting fd: %s" % (variant.error().message))
    variant = variant.unwrap_unchecked()
    index = c_int32(0)
    g_variant_get(variant, "(h)", byref(index))
    global pw_fd_
    pw_fd_ = g_unix_fd_list_get(outlist, index)
    if pw_fd_ == -1 or pw_fd_.error():
        print("Error: %s", pw_fd_.error().message, file=sys.stderr)
        cleanup()
        #g_variant_unref(variant)
        #g_variant_builder_unref(builder)
        return
    pw_fd_ = pw_fd_.unwrap_unchecked()
    #g_variant_unref(variant)
    #g_variant_builder_unref(builder)
    on_portal_done(portal)



@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, POINTER(Portal))
def start_request_response_signal_handler(
        connection: GDBusConnectionP,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    print("Start signal received.\n")
    portal = user_data.contents
    portal_response = c_uint32(0)
    response_data = GVariantP(0)
    iter_ = GVariantIterP(0)
    restore_token = c_char_p(0)
    g_variant_get(parameters, "(u@a{sv})",
                  byref(portal_response), byref(response_data))
    if portal_response or not response_data:
        #print("Failed to start the screen cast session: ", file=sys.stderr)
        on_portal_done(portal, "Failed to start the screen cast session:")
        return
    if g_variant_lookup(response_data, "streams", "a(ua{sv})", byref(iter_)):
        variant = GVariantP(0)
        while g_variant_iter_next(iter_, "@(ua{sv})", byref(variant)):
            stream_id = c_uint32(0)
            type_ = c_uint32(0)
            options = GVariantP(0)
            g_variant_get(variant, "(u@a{sv})",
                          byref(stream_id), byref(options))
            if g_variant_lookup(options, "source_type", "u", byref(type_)):
                portal.capture_source_type = type_
            global pw_stream_node_id_
            pw_stream_node_id_ = stream_id
            break
    # TODO possible memory leak (char*)
    if g_variant_lookup(response_data, "restore_token", "s", byref(restore_token)):
        portal.pw_streams
    #g_variant_unref(response_data)
    open_pipewire_remote(portal)


def start_request(portal: Portal):
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    variant_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token", g_variant_new_string(variant_string))
    portal.start_handle = take_str_ownership(prepare_signal_handle(variant_string, portal.connection))
    start_request_signal_id = setup_request_response_signal(
        portal.start_handle, start_request_response_signal_handler, byref(portal), portal.connection)
    parent_window = ""
    print("Starting the portal session.\n")
    res = g_dbus_proxy_call_sync(
        portal.screencast_proxy, "Start",
        g_variant_new("(osa{sv})", portal.session_handle, parent_window, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, portal.cancellable)
    if not res:
        print("Error", file=sys.stderr)
        g_variant_builder_unref(builder)
        exit(-1)
    #g_variant_unref(res.unwrap_unchecked())
    g_variant_builder_unref(builder)


def on_portal_done(portal: Portal, error=None):
    if error:
        cleanup(portal)
        return
    print("TODO handle streams")
    #pipewire.process(portal.pw_fd, portal.pw_stream_node_id)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, POINTER(Portal))
def sources_request_response_signal_handler(
        connection: GDBusConnectionP,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    portal = user_data.contents  # (cast(user_data, POINTER(Portal))).contents
    portal_response = c_uint32(0)
    g_variant_get(parameters, "(u@a{sv})", byref(portal_response), None)
    if portal_response:
        # TODO Error handling
        print("TODO Error handling")
        print("Failed to select sources for the screen cast session.", file=sys.stderr)
        on_portal_done(portal, )
    start_request(portal)


def sources_request(portal: Portal):
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    g_variant_builder_add(
        builder, "{sv}", "types", g_variant_new_uint32(portal.capture_source_type))
    g_variant_builder_add(
        builder, "{sv}", "multiple", g_variant_new_boolean(portal.multiple))
    cursor_modes_variant = g_dbus_proxy_get_cached_property(
        portal.screencast_proxy, "AvailableCursorModes")
    if cursor_modes_variant:
        modes = c_uint32(0)
        g_variant_get(cursor_modes_variant, "u", byref(modes))
        modes = modes.value
        if modes & portal.cursor_mode:
            g_variant_builder_add(builder, "{sv}", "cursor_mode",
                                  g_variant_new_uint32(portal.cursor_mode))
    version_variant = g_dbus_proxy_get_cached_property(
        portal.screencast_proxy, "version")
    if version_variant:
        version = c_uint32(0)
        g_variant_get(version_variant, "u", byref(version))
        version = version.value
        if version >= 4:
            g_variant_builder_add(builder, "{sv}", "persist_mode",
                                  g_variant_new_uint32(portal.persist_mode))
            if portal.restore_token:
                g_variant_builder_add(builder, "{sv}", "restore_token",
                                      g_variant_new_string(portal.restore_token))

    token_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token",
                          g_variant_new_string(token_string))
    portal.sources_handle = take_str_ownership(prepare_signal_handle(
        token_string, portal.connection))
    portal.sources_request_signal_id = setup_request_response_signal(
        portal.sources_handle, sources_request_response_signal_handler,
        byref(portal), portal.connection)
    print("Requesting sources from the screen cast session.\n")
    result = g_dbus_proxy_call_sync(
        portal.screencast_proxy, "SelectSources",
        g_variant_new("(oa{sv})", portal.session_handle, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, portal.cancellable)
    if not result:
        g_variant_builder_unref(builder)
        exit(-1)
    g_variant_builder_unref(builder)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, POINTER(Portal))
def request_session_response_signal_handler(
        connection: GDBusConnectionP,  # passed as int
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    portal = user_data.contents
    portal_response = c_uint32(0)
    response_data = GVariantP(0)
    g_variant_get(parameters, "(u@a{sv})",
                  byref(portal_response), byref(response_data))
    g_session_handle = g_variant_lookup_value(
        response_data, "session_handle", None)
    # res = g_variant_dup_string(g_session_handle, None)
    portal.session_handle = g_variant_dup_string(g_session_handle, None)
    res_str = cast(portal.session_handle, c_char_p).value
    if len(res_str) == 0 or portal_response:
        print("Failed to request the session subscription.\n", file=sys.stderr)
        # OnPortalDone(RequestResponse::kError);
        
        return
    portal.session_closed_signal_id = g_dbus_connection_signal_subscribe(
        connection, kDesktopBusName, kSessionInterfaceName, "Closed",
        portal.session_handle, None, G_DBUS_SIGNAL_FLAGS_NONE,
        on_session_closed_signal, user_data, None)
    #g_variant_unref(response_data)
    sources_request(portal)


def setup_session_request_handlers(portal: Portal):
    # global connection_
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    session_handle_token = "%s_session%d" % (
        portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    handle_token = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(
        builder, "{sv}", "session_handle_token", g_variant_new_string(session_handle_token))
    g_variant_builder_add(
        builder, "{sv}", "handle_token", g_variant_new_string(handle_token))
    portal.portal_handle = take_str_ownership(prepare_signal_handle(
        handle_token, portal.connection))
    portal.session_request_signal_id = setup_request_response_signal(
        portal.portal_handle, request_session_response_signal_handler, byref(
            portal),
        portal.connection)
    print("Desktop session requested: ", portal.session_request_signal_id)

    variant = g_variant_new("(a{sv})", builder)
    res = g_dbus_proxy_call_sync(portal.screencast_proxy, "CreateSession", variant,
                                 G_DBUS_CALL_FLAGS_NONE, -1, portal.cancellable)
    if res.error():
        print("Error during call to *CreateSession*\n", file=sys.stderr)
        #g_variant_unref(variant)
        #g_variant_builder_unref(builder)
    g_variant_builder_unref(builder)


portal_ = Portal()
#portal_.restore_token = b""
portal_.multiple = c_bool(False)
portal_.capture_source_type = CaptureSourceType.kScreen
portal_.cancellable = g_cancellable_new()
portal_.cursor_mode = CursorMode.kMetadata
portal_.persist_mode = PersistMode.kTransient


def portal_init():
    connection = g_bus_get_sync(G_BUS_TYPE_SESSION)
    screencast_proxy = None
    if connection.is_ok():
        portal_.connection = connection.unwrap_unchecked()
        screencast_proxy = g_dbus_proxy_new_sync(portal_.connection,
                                                 G_DBUS_PROXY_FLAGS_NONE,
                                                 None, kDesktopBusName, kDesktopPath, scast_iface, None)
        portal_.screencast_proxy = screencast_proxy.unwrap()
        setup_session_request_handlers(portal_)
        mainloop = g_main_loop_new(None, True)

        g_main_loop_run(mainloop)
    else:
        print(connection.error())
        exit(-1)
