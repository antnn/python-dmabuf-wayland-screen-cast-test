import sys

from pipewirelib import *



class PipewireVersion(Structure):
    _fields_ = [
        ("major", c_int),
        ("minor", c_int),
        ("micro", c_int)]

    @staticmethod
    def parse(version_string: str):
        ver = list(map(int, version_string.split('.')))
        if len(ver) != 3:
            return
        return PipewireVersion(*ver)

    def ___le___(self, other):
        if not self.major and not self.minor and not self.micro:
            return False
        return (self.major, self.minor, self.micro) <= (other.major, other.minor, other.micro)

    def ___ge___(self, other):
        if not self.major and not self.minor and not self.micro:
            return False
        return (self.major, self.minor, self.micro) >= (other.major, other.minor, other.micro)


@CFUNCTYPE(None)
def on_core_info():
    pass
@CFUNCTYPE(None)
def on_core_done():
    pass
@CFUNCTYPE(None)
def on_core_error():
    pass
@CFUNCTYPE(None)
def on_stream_state_changed():
    pass
@CFUNCTYPE(None)
def on_streamParam_changed():
    pass
@CFUNCTYPE(None)
def on_stream_process():
    pass
@CFUNCTYPE(None)
def on_renegotiate_format():
    pass

global pw_stream_node_id_
global pw_fd_


class DATA(Structure):
    pass


userdata = DATA()


def process(pw_fd, pw_stream_node_id):
    width = c_uint32(1920)
    height = c_uint32(1080)
    global pw_stream_node_id_
    pw_stream_node_id_ = pw_stream_node_id
    global pw_fd_
    pw_fd_ = pw_fd
    pw_init()
    pw_main_loop_ = pw_thread_loop_new("pipewire-main-loop", None)
    pw_context_ = pw_context_new(pw_thread_loop_get_loop(pw_main_loop_), None, 0);
    if not pw_context_:
        print("Failed to create PipeWire context", file=sys.stderr)
        return False
    if pw_thread_loop_start(pw_main_loop_) < 0:
        print("Failed to start main PipeWire loop", file=sys.stderr)
        return False
    pw_client_version_ = pw_get_library_version()
    pw_core_events_ = PWCoreEvents()
    pw_core_events_.version = PW_VERSION_CORE_EVENTS
    pw_core_events_.info = cast(on_core_info, c_void_p)
    pw_core_events_.done = cast(on_core_done, c_void_p)
    pw_core_events_.error = cast(on_core_error, c_void_p)

    pw_stream_events_ = PWStreamEvents()
    pw_stream_events_.version = PW_VERSION_STREAM_EVENTS
    pw_stream_events_.state_changed = cast(on_stream_state_changed, c_void_p)
    pw_stream_events_.param_changed = cast(on_streamParam_changed, c_void_p)
    pw_stream_events_.process = cast(on_stream_process, c_void_p)

    pw_thread_loop_lock(pw_main_loop_)
    if not pw_fd_:
        pw_core_ = pw_context_connect(pw_context_, None, 0)
    else:
        pw_core_ = pw_context_connect_fd(pw_context_, pw_fd_, None, 0)

    if not pw_core_:
        print("Failed to connect PipeWire context", file=sys.stderr)
        return False
    spa_core_listener_ = SPAHook()
    pw_proxy_add_listener(pw_core_, spa_core_listener_, pw_core_events_, userdata)
    loop__ = pw_thread_loop_get_loop(pw_main_loop_)
    renegotiate_ = pw_loop_add_event(loop__, on_renegotiate_format, userdata)




