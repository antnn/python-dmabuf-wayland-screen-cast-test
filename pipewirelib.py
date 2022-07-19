import struct
from ctypes import *
from typing import Generic, TypeVar

___PW___ = CDLL("libpipewire-0.3.so.0")

ENOTSUP = EOPNOTSUPP = 95

___PW___.pw_init.argtypes = [POINTER(c_int), POINTER(POINTER(c_char_p))]


def pw_init(*args):
    ___PW___.pw_init(None, None)


class SPADictP(c_void_p):
    pass


___PW___.pw_thread_loop_new.restype = c_void_p
___PW___.pw_thread_loop_new.argtypes = [c_char_p, c_void_p]
def pw_thread_loop_new(name: str, props: SPADictP):
    return SPADictP(___PW___.pw_thread_loop_new(name.encode('utf-8'), props))


class PWThreadLoopP(c_void_p):
    pass

class PWLoopP(c_void_p):
    pass


___PW___.pw_thread_loop_get_loop.restype = PWLoopP
___PW___.pw_thread_loop_get_loop.argtypes = [PWThreadLoopP]
def pw_thread_loop_get_loop(loop: PWThreadLoopP):
    return PWThreadLoopP(___PW___.pw_thread_loop_get_loop(loop))


class PWContextP(c_void_p):
    pass

class PWPropertiesP(c_void_p):
    pass


___PW___.pw_context_new.restype = PWContextP
___PW___.pw_context_new.argtypes = [PWLoopP, PWPropertiesP, c_size_t]
def pw_context_new(main_loop: PWLoopP, props: PWPropertiesP, user_data_size: int):
    return PWContextP(___PW___.pw_context_new(main_loop, props, user_data_size))


___PW___.pw_thread_loop_start.restype = c_int
___PW___.pw_thread_loop_start.argtypes = [PWThreadLoopP]
def pw_thread_loop_start(loop: PWThreadLoopP):
    return ___PW___.pw_thread_loop_start(loop)


___PW___.pw_get_library_version.restype = c_char_p
def pw_get_library_version():
    return ___PW___.pw_get_library_version()


___PW___.pw_thread_loop_lock.argtypes = [PWThreadLoopP]
def pw_thread_loop_lock(loop: PWThreadLoopP):
    return ___PW___. pw_thread_loop_lock(loop)

class PWCoreP(c_void_p):
    pass


#struct pw_core *pw_context_connect(struct pw_context *context, struct pw_properties *properties, size_t user_data_size)
___PW___.pw_context_connect.restype = PWCoreP
___PW___.pw_context_connect.argtypes = [PWContextP, PWPropertiesP, c_size_t]
def pw_context_connect(context: PWContextP, properties: PWPropertiesP, userdata_size: int):
    return ___PW___.pw_context_connect(context, properties, userdata_size)


___PW___.pw_context_connect_fd.restype = PWCoreP
___PW___.pw_context_connect_fd.argtypes = [PWContextP, c_int, PWPropertiesP, c_size_t]
def pw_context_connect_fd(context: PWContextP, fd: int, properties: PWPropertiesP, userdata_size: int):
    return ___PW___.pw_context_connect_fd(context, fd, properties, userdata_size)

class SPASource(c_void_p):
    pass


class SPACallbacks(Structure):
    _fields_ = [
        ("funcs", c_void_p),
        ("data", c_void_p)
    ]

class SPAInterface(Structure):
    _fields_ = [
        ("type", c_char_p),
        ("version", c_uint32),
        ("cb", SPACallbacks)
    ]

class SPALoopUtils(Structure):
    _fields_ = [
        ("iface", SPAInterface)
    ]


class PWLoop(Structure):
    _fields_ = [
        ("system", c_void_p),
        ("loop", c_void_p),
        ("control", c_void_p),
        ("utils", c_void_p)
    ]

def __pw_loop_add_event(pw_loop: PWLoop, user_method: c_void_p, userdata: c_void_p):
    utils = cast(pw_loop.utils, SPALoopUtils)
    print("___pw_loop_add")






class SPALoopUtilsMethods(Structure):
    _fields_ = [
        ("add_io", c_void_p),
        ("update_io", c_void_p),
        ("add_idle", c_void_p),
        ("enable_idle", c_void_p),
        ("signal_event", c_void_p),
        ("add_timer", c_void_p),
        ("update_timer", c_void_p),
        ("add_signal", c_void_p),
        ("destroy_source", c_void_p)
    ]


class PWCoreEvents(Structure):
    info_types = [c_void_p, c_void_p]
    done_types = [c_void_p, c_uint32, c_int]
    ping_types = [c_void_p, c_uint32, c_int]
    error_types = [c_void_p, c_uint32, c_int, c_int, c_char_p]
    removeid_types = [c_void_p, c_uint32]
    boundid_types = [c_void_p, c_uint32, c_uint32]
    addmem_types = [c_void_p, c_uint32, c_uint32, c_int, c_uint32]
    removemem_types = [c_void_p, c_uint32]
    _fields_ = [
        ("version", c_int32),
        ("info", c_void_p),
        ("done", c_void_p),
        ("ping", c_void_p),
        ("error", c_void_p),
        ("remove_id", c_void_p),
        ("bound_id", c_void_p),
        ("add_mem", c_void_p),
        ("remove_mem", c_void_p),
    ]

class PWStreamEvents(Structure):
    destroy_types = [c_void_p]
    statechanged_types = [c_void_p, c_int, c_int, c_char_p]
    controlinfo_types = [c_void_p, c_uint32, c_void_p]
    iochanged_types = [c_void_p, c_uint32, c_void_p, c_uint32]
    paramchanged_types = [c_void_p, c_uint32, c_void_p]
    addbuffer_types = [c_void_p, c_void_p]
    removebuffer_types = [c_void_p, c_void_p]
    process_types = [c_void_p]
    drained_types = [c_void_p]
    command_types = [c_void_p, c_void_p]
    triggerdone_types = [c_void_p]
    _fields_ = [
        ("version", c_int32),
        ("destroy", c_void_p),
        ("state_changed", c_void_p),
        ("control_info", c_void_p),
        ("io_changed", c_void_p),
        ("param_changed", c_void_p),
        ("add_buffer", c_void_p),
        ("remove_buffer", c_void_p),
        ("process", c_void_p),
        ("drained", c_void_p),
        ("command", c_void_p),
        ("trigger_done", c_void_p),
    ]


PW_VERSION_CORE_EVENTS = 0
PW_VERSION_STREAM_EVENTS = 2