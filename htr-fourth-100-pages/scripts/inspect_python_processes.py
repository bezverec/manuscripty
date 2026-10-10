import ctypes,json
from ctypes import wintypes as w
k=ctypes.WinDLL('kernel32',use_last_error=True); n=ctypes.WinDLL('ntdll')
class PE(ctypes.Structure):
 _fields_=[('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',w.DWORD),('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
k.CreateToolhelp32Snapshot.restype=w.HANDLE
k.OpenProcess.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE]
k.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(PE)];k.Process32NextW.argtypes=k.Process32FirstW.argtypes
n.NtQueryInformationProcess.argtypes=[w.HANDLE,w.ULONG,ctypes.c_void_p,w.ULONG,ctypes.POINTER(w.ULONG)]
s=k.CreateToolhelp32Snapshot(2,0);p=PE();p.dwSize=ctypes.sizeof(p);out=[];ok=k.Process32FirstW(s,ctypes.byref(p))
while ok:
 if p.szExeFile.lower()=='python.exe':
  h=k.OpenProcess(0x1000,False,p.th32ProcessID);length=w.ULONG();cmd=''
  if h:
   n.NtQueryInformationProcess(h,60,None,0,ctypes.byref(length));buf=ctypes.create_string_buffer(length.value)
   if n.NtQueryInformationProcess(h,60,buf,length.value,ctypes.byref(length))==0:
    size=ctypes.c_ushort.from_buffer(buf).value;ptr=ctypes.c_void_p.from_buffer(buf,8).value;cmd=ctypes.wstring_at(ptr,size//2)
   k.CloseHandle(h)
  out.append({'pid':p.th32ProcessID,'command':cmd})
 ok=k.Process32NextW(s,ctypes.byref(p))
k.CloseHandle(s);print(json.dumps(out))
