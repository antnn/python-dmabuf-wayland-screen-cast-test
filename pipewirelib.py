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
