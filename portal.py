from random import randrange
from gio import *

kDesktopBusName = "org.freedesktop.portal.Desktop"
kRequestInterfaceName = "org.freedesktop.portal.Request"
kDesktopPath = '/org/freedesktop/portal/desktop'
req_path = '/org/freedesktop/portal/desktop/request'
req_iface = 'org.freedesktop.portal.Request'
scast_iface = 'org.freedesktop.portal.ScreenCast'
sender_name_ = "pythonmss"
portal_prefix = "pythonmss"


def new_request_path(connection: GDBusConnection_p):
    token = str(g_dbus_connection_get_unique_name(connection), "utf-8")
    path = str(req_path, "utf-8")
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


def portal():
    global screencast_proxy_
    connection = g_bus_get_sync(GBusType.G_BUS_TYPE_SESSION)
    screencast_proxy = None
    if connection.is_ok():
        global connection_
        connection_ = connection.unwrap_unchecked()
        screencast_proxy = g_dbus_proxy_new_sync(connection_,
                                                 GDBusProxyFlags.G_DBUS_PROXY_FLAGS_NONE,
                                                 None, kDesktopBusName, kDesktopPath, scast_iface, None)
        screencast_proxy_ = screencast_proxy.unwrap()
        setup_session_request_handlers()
        mainloop = g_main_loop_new(None, True)
        g_main_loop_run(mainloop)
    else:
        print(connection.error())
        exit(-1)


kDesktopRequestObjectPath = "/org/freedesktop/portal/desktop/request"


def prepare_signal_handle(token, connection):
    sender = str(g_dbus_connection_get_unique_name(connection), "utf-8")
    sender = sender.replace(":", "").replace(".", "_")
    handle = '%s/%s/%s' % (kDesktopRequestObjectPath, sender, token)
    return handle


def setup_request_response_signal(object_path: str,
                                  callback: c_void_p,
                                  user_data: c_void_p,
                                  connection: GDBusConnection_p):
    return g_dbus_connection_signal_subscribe(connection,
                                              kDesktopBusName, kRequestInterfaceName, "Response",
                                              object_path, None, G_DBUS_SIGNAL_FLAGS_NO_MATCH_RULE,
                                              callback, user_data, None)


@CFUNCTYPE(c_int,GDBusConnection_p, c_char_p, c_char_p, c_char_p,
           c_char_p, GVariant_p, c_void_p)
def request_session_response_signal_handler(
        connection: GDBusConnection_p,
        sender_name: c_char_p,
        object_path: c_char_p,
        interface_name: c_char_p,
        signal_name: c_char_p,
        parameters: GVariant_p,
        user_data: c_void_p):
    print("CALLBACK")
    portal_response = 0
    response_data: POINTER(GVariant_p)()
    g_variant_get(parameters, "(u@a{sv})", POINTER(portal_response), response_data)



session_request_signal_id_ = 0

cancellable_ = g_cancellable_new()


def setup_session_request_handlers():
    global connection_

    builder = g_variant_builder_new(G_VARIANT_TYPE_VARDICT)

    session_handle_token = "%s_session%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))
    handle_token = "%s_%d" % (portal_prefix, randrange(0, PLATFORM_C_MAXINT))

    g_variant_builder_add(builder, "{sv}", "session_handle_token", g_variant_new_string(session_handle_token))

    g_variant_builder_add(builder, "{sv}", "handle_token", g_variant_new_string(handle_token))

    portal_handle = prepare_signal_handle(handle_token, connection_)
    session_request_signal_id_ = setup_request_response_signal(
        portal_handle, request_session_response_signal_handler, None,
        connection_)
    print("Desktop session requested")
    var = g_variant_new("(a{sv})", builder)
    res = g_dbus_proxy_call_sync(
        screencast_proxy_, "CreateSession", var,
        G_DBUS_CALL_FLAGS_NONE, -1, cancellable_)
    print("Result %s", res)
