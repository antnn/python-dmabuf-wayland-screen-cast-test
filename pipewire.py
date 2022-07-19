from pipewirelib import *

class PipewireVersion(Structure):
    _fields_ = [
        ("major", c_int),
        ("minor", c_int),
        ("micro", c_int)]

    def ___le___(self, other):
        if not self.major and not self.minor and not self.micro:
            return False
        return (self.major, self.minor, self.micro) <= (other.major, other.minor, other.micro)

    def ___ge___(self, other):
        if not self.major and not self.minor and not self.micro:
            return False
        return (self.major, self.minor, self.micro) >= (other.major, other.minor, other.micro)

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

global pw_stream_node_id_
global pw_fd_

def process(pw_fd, pw_stream_node_id):
    width = c_uint32(1920)
    height = c_uint32(1080)
    global pw_stream_node_id_
    pw_stream_node_id_ = pw_stream_node_id;
    global pw_fd_
    pw_fd_ = pw_fd
    pw_init()

