import ctypes
ll = ctypes.cdll.LoadLibrary
lib = ll("./lib.so")
k = lib.Foo_bar(1)
print(k)

