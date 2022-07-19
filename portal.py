import sys
from random import randrange

import pipewire
from gio import *

kDesktopBusName = "org.freedesktop.portal.Desktop"
kRequestInterfaceName = "org.freedesktop.portal.Request"
kDesktopPath = '/org/freedesktop/portal/desktop'
req_path = '/org/freedesktop/portal/desktop/request'
req_iface = 'org.freedesktop.portal.Request'
scast_iface = 'org.freedesktop.portal.ScreenCast'
sender_name_ = portal_prefix = "pythonmss"


def new_request_path(connection: GDBusConnection_p):
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


global screencast_proxy_
global connection_

kDesktopRequestObjectPath = "/org/freedesktop/portal/desktop/request"


def prepare_signal_handle(token, connection):
    sender = str(g_dbus_connection_get_unique_name(connection), "utf-8")
    sender = sender.replace(":", "").replace(".", "_")
    handle = '%s/%s/%s' % (kDesktopRequestObjectPath, sender, token)
    return handle


def setup_request_response_signal(object_path: str,
                                  callback,
                                  user_data: c_void_p,
                                  connection: GDBusConnection_p):
    return g_dbus_connection_signal_subscribe(connection,
                                              kDesktopBusName, kRequestInterfaceName, "Response",
                                              object_path, None, G_DBUS_SIGNAL_FLAGS_NO_MATCH_RULE,
                                              callback, user_data, None)


@CFUNCTYPE(None, GDBusConnection_p, c_char_p, c_char_p, c_char_p, c_char_p, GVariant_p, c_void_p)
def on_session_closed_signal(connection: GDBusConnection_p,
                             sender_name: c_char_p,
                             object_path: c_char_p,
                             interface_name: c_char_p,
                             signal_name: c_char_p,
                             parameters: GVariant_p,
                             user_data: c_void_p):
    print("session is closed")
    exit(0)


kSessionInterfaceName = "org.freedesktop.portal.Session"


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


cursor_mode_ = CursorMode.kMetadata
restore_token_ = ""


def cleanup():
    print("CLEANUP")

global pw_fd_
global pw_stream_node_id_
def open_pipewire_remote():
    print("PIPEWIRE\n")
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    outlist = c_void_p(0)
    variant = g_dbus_proxy_call_with_unix_fd_list_sync(screencast_proxy_, "OpenPipeWireRemote",
                                                       g_variant_new("(oa{sv})", session_handle_, builder),
                                                       G_DBUS_CALL_FLAGS_NONE, -1, None, byref(outlist), cancellable_)
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
    on_portal_done()
    

@CFUNCTYPE(None, GDBusConnection_p, c_char_p, c_char_p, c_char_p, c_char_p, GVariant_p, c_void_p)
def start_request_response_signal_handler(
        connection: GDBusConnection_p,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariant_p,
        user_data: c_void_p):
    print("Start signal received.\n");
    portal_response = c_uint32(0)
    response_data = c_void_p(0)
    iter_ = c_void_p(0)
    global restore_token_
    restore_token_ = c_char_p(0);
    g_variant_get(parameters, "(u@a{sv})", byref(portal_response), byref(response_data))
    if portal_response or not response_data:
        print("Failed to start the screen cast session.", file=sys.stderr)
        on_portal_done()
        return
    if g_variant_lookup(response_data, "streams", "a(ua{sv})", byref(iter_)):
        variant = c_void_p(0)
        while g_variant_iter_next(iter_, "@(ua{sv})", byref(variant)):
            stream_id = c_uint32(0)
            type_ = c_uint32(0)
            options = c_void_p(0)
            g_variant_get(variant, "(u@a{sv})", byref(stream_id), byref(options))
            if g_variant_lookup(options, "source_type", "u", byref(type_)):
                capture_source_type = type_
            global pw_stream_node_id_
            pw_stream_node_id_ = stream_id
            break
    if g_variant_lookup(response_data, "restore_token", "s", byref(restore_token_)):
        restore_token = restore_token_
    open_pipewire_remote()


def start_request():
    global session_handle_
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    # token for handle
    variant_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token", g_variant_new_string(variant_string))
    start_handle = prepare_signal_handle(variant_string, connection_)
    start_request_signal_id = setup_request_response_signal(
        start_handle, start_request_response_signal_handler, None, connection_)
    parent_window = ""
    print("Starting the portal session.\n")
    res = g_dbus_proxy_call_sync(
        screencast_proxy_, "Start",
        g_variant_new("(osa{sv})", session_handle_, parent_window, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, cancellable_)
    if not res:
        print("Error", file=sys.stderr)
        exit(-1)


def on_portal_done():
    global pw_fd_
    global pw_stream_node_id_
    pipewire.process(pw_fd_, pw_stream_node_id_)


@CFUNCTYPE(None, GDBusConnection_p, c_char_p, c_char_p, c_char_p, c_char_p, GVariant_p, c_void_p)
def sources_request_response_signal_handler(
        connection: GDBusConnection_p,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariant_p,
        user_data: c_void_p):
    portal_response = c_uint32(0)
    g_variant_get(parameters, "(u@a{sv})", byref(portal_response), None);
    if portal_response:
        print("Failed to select sources for the screen cast session.", file=sys.stderr)
        on_portal_done()
    start_request()


def sources_request(session_handle_):
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    token_string = ""
    g_variant_builder_add(builder, "{sv}", "types", g_variant_new_uint32(CaptureSourceType.kScreen))
    g_variant_builder_add(builder, "{sv}", "multiple", g_variant_new_boolean(False))
    cursor_modes_variant = g_dbus_proxy_get_cached_property(screencast_proxy_, "AvailableCursorModes")
    if cursor_modes_variant:
        modes = c_uint32(0)
        g_variant_get(cursor_modes_variant, "u", byref(modes))
        modes = modes.value
        if modes & cursor_mode_:
            g_variant_builder_add(builder, "{sv}", "cursor_mode",
                                  g_variant_new_uint32(cursor_mode_))
    versionVariant = g_dbus_proxy_get_cached_property(screencast_proxy_, "version")
    if versionVariant:
        version = c_uint32(0)
        g_variant_get(versionVariant, "u", byref(version))
        version = version.value
        if version >= 4:
            persist_mode_ = PersistMode.kTransient
            g_variant_builder_add(builder, "{sv}", "persist_mode", g_variant_new_uint32(persist_mode_))
            if len(restore_token_):
                g_variant_builder_add(builder, "{sv}", "restore_token",
                                      g_variant_new_string(restore_token_))

    token_string = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "handle_token",
                          g_variant_new_string(token_string))
    sources_handle = prepare_signal_handle(token_string, connection_)
    sources_request_signal_id_ = setup_request_response_signal(
        sources_handle, sources_request_response_signal_handler,
        None, connection_)
    print("Requesting sources from the screen cast session.\n")
    result = g_dbus_proxy_call_sync(
        screencast_proxy_, "SelectSources",
        g_variant_new("(oa{sv})", session_handle_, builder),
        G_DBUS_CALL_FLAGS_NONE, -1, cancellable_)
    if not result:
        exit(-1)


global session_handle_


@CFUNCTYPE(None, GDBusConnection_p, c_char_p, c_char_p, c_char_p, c_char_p, GVariant_p, c_void_p)
def request_session_response_signal_handler(
        connection: GDBusConnection_p,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariant_p,
        user_data: c_void_p):
    portal_response = c_uint32(1)
    response_data = c_void_p(0)
    g_variant_get(c_void_p(parameters), "(u@a{sv})", byref(portal_response), byref(response_data))
    g_session_handle = g_variant_lookup_value(response_data, "session_handle", None)
    global session_handle_
    session_handle_ = g_variant_dup_string(g_session_handle, None)
    if session_handle_ == "" or not session_handle_ or portal_response:
        print("Failed to request the session subscription.\n", file=sys.stderr)
        # OnPortalDone(RequestResponse::kError);
        return
    global session_request_signal_id_
    session_closed_signal_id_ = g_dbus_connection_signal_subscribe(
        connection, kDesktopBusName, kSessionInterfaceName, "Closed",
        session_handle_, None, G_DBUS_SIGNAL_FLAGS_NONE,
        on_session_closed_signal, None, None)
    sources_request(session_handle_)


session_request_signal_id_ = 0
cancellable_ = g_cancellable_new()


def setup_session_request_handlers(connection_):
    # global connection_
    global session_request_signal_id_
    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)
    session_handle_token = "%s_session%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    handle_token = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    g_variant_builder_add(builder, "{sv}", "session_handle_token", g_variant_new_string(session_handle_token))
    g_variant_builder_add(builder, "{sv}", "handle_token", g_variant_new_string(handle_token))
    portal_handle = prepare_signal_handle(handle_token, connection_)
    session_request_signal_id_ = setup_request_response_signal(
        portal_handle, request_session_response_signal_handler, None,
        connection_)
    print("Desktop session requested: ", session_request_signal_id_)

    variant = g_variant_new("(a{sv})", builder)
    res = g_dbus_proxy_call_sync(screencast_proxy_, "CreateSession", variant,
                                 G_DBUS_CALL_FLAGS_NONE, -1, cancellable_)
    if res.error():
        print("Error during call to *CreateSession*\n", file=sys.stderr)


def portal():
    global screencast_proxy_
    connection = g_bus_get_sync(GBusType.G_BUS_TYPE_SESSION)
    screencast_proxy = None
    if connection.is_ok():
        global connection_
        connection_ = connection.unwrap_unchecked()
        screencast_proxy = g_dbus_proxy_new_sync(GDBusConnectionP(connection_.value),
                                                 GDBusProxyFlags.G_DBUS_PROXY_FLAGS_NONE,
                                                 None, kDesktopBusName, kDesktopPath, scast_iface, None)
        screencast_proxy_ = screencast_proxy.unwrap()
        setup_session_request_handlers(connection_)
        mainloop = g_main_loop_new(None, True)

        g_main_loop_run(mainloop)
    else:
        print(connection.error())
        exit(-1)
