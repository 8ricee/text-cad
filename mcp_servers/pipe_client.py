"""Zero-dependency Windows Named Pipe JSON-RPC client using ctypes/kernel32."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import time
import uuid
from typing import Any

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_OPEN_EXISTING = 3
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_ERROR_PIPE_BUSY = 231
_ERROR_FILE_NOT_FOUND = 2

_kernel32.WaitNamedPipeW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
_kernel32.WaitNamedPipeW.restype = wintypes.BOOL

_kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
_kernel32.CreateFileW.restype = wintypes.HANDLE

_kernel32.WriteFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
_kernel32.WriteFile.restype = wintypes.BOOL

_kernel32.ReadFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
_kernel32.ReadFile.restype = wintypes.BOOL

_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL


def pipe_available(pipe_name: str, wait_ms: int = 400) -> bool:
    """Return True if the Named Pipe server is currently listening."""
    pipe_path = rf"\\.\pipe\{pipe_name}"
    deadline = time.monotonic() + (max(50, wait_ms) / 1000.0)
    while True:
        if _kernel32.WaitNamedPipeW(pipe_path, 50):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)


def launch_on_desktop(cmd_str: str, cwd_dir: str) -> int:
    """Spawn a GUI process explicitly on the interactive WinSta0\\Default desktop and return its PID."""
    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("lpReserved", ctypes.c_wchar_p),
            ("lpDesktop", ctypes.c_wchar_p),
            ("lpTitle", ctypes.c_wchar_p),
            ("dwX", ctypes.c_ulong),
            ("dwY", ctypes.c_ulong),
            ("dwXSize", ctypes.c_ulong),
            ("dwYSize", ctypes.c_ulong),
            ("dwXCountChars", ctypes.c_ulong),
            ("dwYCountChars", ctypes.c_ulong),
            ("dwFillAttribute", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("wShowWindow", ctypes.c_ushort),
            ("cbReserved2", ctypes.c_ushort),
            ("lpReserved2", ctypes.c_void_p),
            ("hStdInput", ctypes.c_void_p),
            ("hStdOutput", ctypes.c_void_p),
            ("hStdError", ctypes.c_void_p),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", ctypes.c_void_p),
            ("hThread", ctypes.c_void_p),
            ("dwProcessId", ctypes.c_ulong),
            ("dwThreadId", ctypes.c_ulong),
        ]

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    cmd_buf = ctypes.create_unicode_buffer(cmd_str)
    ok = _kernel32.CreateProcessW(None, cmd_buf, None, None, False, 0x01000010, None, cwd_dir, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        ok = _kernel32.CreateProcessW(None, cmd_buf, None, None, False, 0x00000010, None, cwd_dir, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        raise RuntimeError(f"CreateProcessW failed (Win32 error {ctypes.get_last_error()}): {cmd_str}")
    _kernel32.CloseHandle(pi.hThread)
    _kernel32.CloseHandle(pi.hProcess)
    return int(pi.dwProcessId)


def pipe_call(pipe_name: str, method: str, params: dict[str, Any] | None = None, timeout_s: float = 35.0) -> Any:
    """Send a single JSON-RPC line over a Windows Named Pipe and return the parsed result."""
    pipe_path = rf"\\.\pipe\{pipe_name}"
    deadline = time.monotonic() + timeout_s
    handle = _INVALID_HANDLE_VALUE

    while True:
        rem_ms = max(100, int((deadline - time.monotonic()) * 1000))
        _kernel32.WaitNamedPipeW(pipe_path, min(rem_ms, 1000))
        handle = _kernel32.CreateFileW(
            pipe_path,
            _GENERIC_READ | _GENERIC_WRITE,
            0,
            None,
            _OPEN_EXISTING,
            0,
            None,
        )
        if handle != _INVALID_HANDLE_VALUE:
            break
        err = ctypes.get_last_error()
        if time.monotonic() >= deadline:
            if err == _ERROR_FILE_NOT_FOUND:
                raise RuntimeError(
                    f"Named Pipe '{pipe_path}' not found. Ensure the CAD application is running with the Agy .NET Add-in loaded."
                )
            raise RuntimeError(f"Failed to connect to '{pipe_path}' (Win32 error {err}).")
        if err in (_ERROR_PIPE_BUSY, _ERROR_FILE_NOT_FOUND):
            time.sleep(0.05)
        else:
            raise RuntimeError(f"Failed to open '{pipe_path}' (Win32 error {err}).")

    try:
        req = {"id": uuid.uuid4().hex[:12], "method": method, "params": params or {}}
        payload = (json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8")
        written = wintypes.DWORD(0)
        if not _kernel32.WriteFile(handle, payload, len(payload), ctypes.byref(written), None):
            raise RuntimeError(f"WriteFile failed on '{pipe_path}' (Win32 error {ctypes.get_last_error()}).")

        chunks: list[bytes] = []
        buf = ctypes.create_string_buffer(65536)
        read_n = wintypes.DWORD(0)
        while True:
            ok = _kernel32.ReadFile(handle, buf, 65536, ctypes.byref(read_n), None)
            if read_n.value > 0:
                data = buf.raw[: read_n.value]
                chunks.append(data)
                if b"\n" in data:
                    break
            if not ok:
                break
        raw_resp = b"".join(chunks).decode("utf-8", errors="replace").strip()
        if not raw_resp:
            raise RuntimeError(f"Empty response from '{pipe_path}' for method '{method}'.")
        resp = json.loads(raw_resp.splitlines()[0])
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error") or f"Bridge error on '{method}'.")
        return resp.get("result")
    finally:
        _kernel32.CloseHandle(handle)
