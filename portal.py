import sys
from random import randrange

import pipewire
from gio import *

kDesktopBusName = "org.freedesktop.portal.Desktop"
kRequestInterfaceName = "org.freedesktop.portal.Request"
kDesktopRequestObjectPath = "/org/freedesktop/portal/desktop/request"
kSessionInterfaceName = "org.freedesktop.portal.Session"
kDesktopPath = '/org/freedesktop/portal/desktop'
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
        ("pw_stream_node_id", c_uint32),
        ("restore_token", c_char_p)
    ]


class Portal(Structure):
    multiple: c_bool
    capture_mode: CaptureSourceType
    persist_mode: PersistMode
    cursor_mode: CursorMode
    connection: GDBusConnectionP
    #proxy_request_response_handler: GDBusSignalCallback
    #sources_request_response_signal_handler: GDBusSignalCallback
    screencast_proxy: GDBusProxyP
    pw_streams: POINTER(PipeWireStream)
    cancellable: GCancellableP
    portal_handle: c_char_p
    session_handle: c_char_p
    sources_handle: c_char_p
    start_handle: c_char_p
    session_request_signal_id: c_int
    sources_request_signal_id: c_int
    start_request_signal_id: c_int
    session_closed_signal_id: c_int

    _fields_ = [
        ("multiple", c_bool),
        ("capture_mode", c_uint32),
        ("connection", GDBusConnectionP),
        ("screencast_proxy", GDBusProxyP),
        ("pw_streams", POINTER(PipeWireStream)),
        ("persist_mode", c_uint32),
        ("cancellable", GCancellableP),
        ("cursor_mode", c_uint32),
        ("portal_handle", c_char_p),
        ("session_handle", c_char_p),
        ("sources_handle", c_char_p),
        ("start_handle", c_char_p),
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


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, c_void_p)
def on_session_closed_signal(connection: GDBusConnectionP,
                             sender_name: c_char_p,
                             object_path: c_char_p,
                             interface_name: c_char_p,
                             signal_name: c_char_p,
                             parameters: GVariantP,
                             user_data: c_void_p):
    portal = (cast(user_data, POINTER(Portal))).contents
    print("session is closed")
    exit(0)



def cleanup():
    print("CLEANUP")


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
        print("Error getting fd")
    variant = variant.unwrap_unchecked()
    index = c_int32(0)
    g_variant_get(variant, "(h)", byref(index))
    global pw_fd_
    pw_fd_ = g_unix_fd_list_get(outlist, index)
    if pw_fd_ == -1 or pw_fd_.error():
        print("Error: %s", pw_fd_.error(), file=sys.stderr)
        cleanup()
        return
    pw_fd_ = pw_fd_.unwrap_unchecked()
    on_portal_done(portal)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, c_void_p)
def start_request_response_signal_handler(
        connection: GDBusConnectionP,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    print("Start signal received.\n")
    portal = (cast(user_data, POINTER(Portal))).contents
    portal_response = c_uint32(0)
    response_data = GVariantP(0)
    iter_ = GVariantIterP(0)
    restore_token = c_char_p(0)
    g_variant_get(parameters, "(u@a{sv})",
                  byref(portal_response), byref(response_data))
    if portal_response or not response_data:
        print("Failed to start the screen cast session.", file=sys.stderr)
        on_portal_done()
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
                capture_source_type = type_
            global pw_stream_node_id_
            pw_stream_node_id_ = stream_id
            break
    # TODO possible memory leak (char*)
    if g_variant_lookup(response_data, "restore_token", "s", byref(restore_token)):
        portal.pw_streams
    open_pipewire_remote()


def start_request(portal:Portal):
    session_handle_ = portal.session_handle # gets freed by Python 
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    # token for handle
    variant_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token", g_variant_new_string(variant_string))
    start_handle = prepare_signal_handle(variant_string, portal.connection).encode("utf-8")
    start_request_signal_id = setup_request_response_signal(
        start_handle, start_request_response_signal_handler, None, portal.connection)
    parent_window = ""
    print("Starting the portal session.\n")
    res = g_dbus_proxy_call_sync(
        portal.screencast_proxy, "Start",
        g_variant_new("(osa{sv})", session_handle_, parent_window, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, portal.cancellable)
    if not res:
        print("Error", file=sys.stderr)
        exit(-1)


def on_portal_done(portal: Portal, error=None):
    print("TODO handle streams and erros")
    # pipewire.process(portal.pw_fd, portal.pw_stream_node_id_)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, c_void_p)
def sources_request_response_signal_handler(
        connection: GDBusConnectionP,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    portal = (cast(user_data, POINTER(Portal))).contents
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
        builder, "{sv}", "types", g_variant_new_uint32(portal.capture_mode))
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
            # if len(portal.restore_token):
            #    g_variant_builder_add(builder, "{sv}", "restore_token",
            #                          g_variant_new_string(portal.restore_token))

    token_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token",
                          g_variant_new_string(token_string))
    portal.sources_handle = prepare_signal_handle(
        token_string, portal.connection).encode("utf-8")
    portal.sources_request_signal_id = setup_request_response_signal(
        portal.sources_handle, sources_request_response_signal_handler,
        byref(portal), portal.connection)
    print("Requesting sources from the screen cast session.\n")
    result = g_dbus_proxy_call_sync(
        portal.screencast_proxy, "SelectSources",
        g_variant_new("(oa{sv})", portal.session_handle, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, portal.cancellable)
    if not result:
        exit(-1)


@CFUNCTYPE(None, GDBusConnectionP, c_char_p, c_char_p, c_char_p, c_char_p, GVariantP, c_void_p)
def request_session_response_signal_handler(
        connection: GDBusConnectionP,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariantP,
        user_data: c_void_p):
    portal = (cast(user_data, POINTER(Portal))).contents
    portal_response = c_uint32(0)
    response_data = GVariantP(0)
    g_variant_get(parameters, "(u@a{sv})",
                  byref(portal_response), byref(response_data))
    g_session_handle = g_variant_lookup_value(
        response_data, "session_handle", None)
    portal.session_handle = g_variant_dup_string(
        g_session_handle, None).encode('utf-8')
    if len(portal.session_handle) == 0 or portal_response:
        print("Failed to request the session subscription.\n", file=sys.stderr)
        # OnPortalDone(RequestResponse::kError);
        return
    portal.session_closed_signal_id = g_dbus_connection_signal_subscribe(
        connection, kDesktopBusName, kSessionInterfaceName, "Closed",
        portal.session_handle, None, G_DBUS_SIGNAL_FLAGS_NONE,
        on_session_closed_signal, user_data, None)
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
    portal.portal_handle = prepare_signal_handle(
        handle_token, portal.connection).encode('utf-8')
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


portal = Portal()
portal.multiple = c_bool(False)
portal.capture_mode = CaptureSourceType.kScreen
portal.cancellable = g_cancellable_new()
portal.cursor_mode = CursorMode.kMetadata



def portal_init():
    portal.persist_mode = PersistMode.kTransient
    connection = g_bus_get_sync(G_BUS_TYPE_SESSION)
    screencast_proxy = None
    if connection.is_ok():
        portal.connection = connection.unwrap_unchecked()
        screencast_proxy = g_dbus_proxy_new_sync(portal.connection,
                                                 G_DBUS_PROXY_FLAGS_NONE,
                                                 None, kDesktopBusName, kDesktopPath, scast_iface, None)
        portal.screencast_proxy = screencast_proxy.unwrap()
        setup_session_request_handlers(portal)
        mainloop = g_main_loop_new(None, True)

        g_main_loop_run(mainloop)
    else:
        print(connection.error())
        exit(-1)
