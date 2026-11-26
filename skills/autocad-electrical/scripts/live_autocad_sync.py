"""100% Zero-Touch Live AutoCAD / AutoCAD Electrical In-Tab Synchronizer.

Preserves BOTH pure 1:1 mm Model Space (zero title blocks in Model Space) AND Paper Space Layouts ('ISO_A3' with
Title Block, Schedules, and calibrated VIEWPORTs) when updating a drawing currently open in AutoCAD.

Architecture (Zero SECURELOAD popups after 1-time trust):
1. Pure inline LISP inside `vla-SendCommand` (NO secondary `_live_swap_worker.lsp` file is ever loaded, so AutoCAD's
   `SECURELOAD` never blocks the 2-step MDI handoff).
2. Exposes `(ag:live-reload main-path cache-path)` so adding `live_update_in_autocad.lsp` once to AutoCAD's
   `APPLOAD -> Startup Suite` (and clicking 'Always Load' once) makes all future updates 100% zero-touch.
"""

from __future__ import annotations

import ctypes
from pathlib import Path


def _build_inline_swap_lisp(dxf_main: str, dxf_cache: str, target_name_upper: str, backup_path: str) -> str:
    """Build a single-line LISP expression for vla-SendCommand (backs up unsaved edits before closing)."""
    return (
        '(progn (vl-load-com) '
        '(setq acad (vlax-get-acad-object) docs (vla-get-Documents acad) me (vla-get-ActiveDocument acad)) '
        f'(vlax-for doc docs (if (= (strcase (vla-get-Name doc)) "{target_name_upper}") '
        '(progn '
        f'(if (= (vla-get-Saved doc) :vlax-false) (vl-catch-all-apply (function vla-SaveAs) (list doc "{backup_path}"))) '
        '(vl-catch-all-apply (function vla-Close) (list doc :vlax-false))))) '
        f'(if (vl-file-systime "{dxf_cache}") '
        f'(progn (vl-file-delete "{dxf_main}") (vl-file-rename "{dxf_cache}" "{dxf_main}"))) '
        f'(if (vl-file-systime "{dxf_main}") '
        f'(progn (setq nd (vla-Open docs "{dxf_main}")) (vla-Activate nd))) '
        '(vl-catch-all-apply (function vla-SendCommand) (list me "_.CLOSE _N ")))\n'
    )


def _escape_lisp_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def push_live_dxf_to_running_autocad(target_dxf_path: Path, cache_dxf_path: Path) -> bool:
    """Reload an open DXF in AutoCAD MDI preserving both 1:1 Model Space and Paper Space ('ISO_A3') Layouts."""
    lsp_path = target_dxf_path.parent / "live_update_in_autocad.lsp"
    dxf_cache = cache_dxf_path.resolve().as_posix()
    dxf_main = target_dxf_path.resolve().as_posix()
    backup_dxf = target_dxf_path.with_name(f"{target_dxf_path.stem}_unsaved_backup{target_dxf_path.suffix}").resolve().as_posix()
    target_name_upper = target_dxf_path.name.upper()

    inline_swap = _build_inline_swap_lisp(dxf_main, dxf_cache, target_name_upper, backup_dxf)
    inline_swap_escaped = _escape_lisp_str(inline_swap)

    lsp_content = f""";; ============================================================================
;; 100% ZERO-TOUCH MDI RELOAD (INLINE LISP HANDOFF - ZERO SECURELOAD BLOCKS)
;; Add this file ONCE to AutoCAD APPLOAD -> Startup Suite for permanent zero-touch sync.
;; ============================================================================
(vl-load-com)

(defun ag:live-reload ( main-path cache-path / acad docs tmpdoc fname cmd curdoc bkp )
  (setq acad (vlax-get-acad-object))
  (setq docs (vla-get-Documents acad))
  (setq fname (strcase (strcat (vl-filename-base main-path) (vl-filename-extension main-path))))
  (setq bkp (strcat (vl-filename-directory main-path) "/" (vl-filename-base main-path) "_unsaved_backup" (vl-filename-extension main-path)))
  (vlax-for curdoc docs
    (if (and (= (strcase (vla-get-Name curdoc)) fname) (= (vla-get-Saved curdoc) :vlax-false))
      (progn
        (princ "\\n[Antigravity AI] CANH BAO: Ban ve dang co chinh sua tay chua luu! Dang backup...")
        (vl-catch-all-apply (function vla-SaveAs) (list curdoc bkp))
      )
    )
  )
  (setq cmd (strcat
    "(progn (vl-load-com) "
    "(setq acad (vlax-get-acad-object) docs (vla-get-Documents acad) me (vla-get-ActiveDocument acad)) "
    "(vlax-for doc docs (if (= (strcase (vla-get-Name doc)) \\"" fname "\\") "
    "(vl-catch-all-apply (function vla-Close) (list doc :vlax-false)))) "
    "(if (vl-file-systime \\"" cache-path "\\") "
    "(progn (vl-file-delete \\"" main-path "\\") (vl-file-rename \\"" cache-path "\\" \\"" main-path "\\"))) "
    "(if (vl-file-systime \\"" main-path "\\") "
    "(progn (setq nd (vla-Open docs \\"" main-path "\\")) (vla-Activate nd))) "
    "(vl-catch-all-apply (function vla-SendCommand) (list me \\"_.CLOSE _N \\")))\\n"
  ))
  (setq tmpdoc (vla-Add docs))
  (vla-Activate tmpdoc)
  (vla-SendCommand tmpdoc cmd)
  (princ)
)

(defun c:LIVEUPDATE ( / acad docs tmpdoc )
  (setq acad (vlax-get-acad-object))
  (setq docs (vla-get-Documents acad))
  (setq tmpdoc (vla-Add docs))
  (vla-Activate tmpdoc)
  (vla-SendCommand tmpdoc "{inline_swap_escaped}")
  (princ "\\n[Antigravity AI] Đã đồng bộ bản vẽ 1:1 + Layout ISO_A3!")
  (princ)
)
"""
    lsp_path.write_text(lsp_content, encoding="utf-8")

    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)

        class COPYDATASTRUCT(ctypes.Structure):
            _fields_ = [
                ("dwData", ctypes.c_void_p),
                ("cbData", ctypes.c_ulong),
                ("lpData", ctypes.c_void_p),
            ]

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        acad_hwnds: list[int] = []

        def cb(hwnd, lparam):
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            if cls.value == "AfxMDIFrame140u":
                buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, buf, 512)
                if "AutoCAD" in buf.value:
                    acad_hwnds.append(hwnd)
            return True

        if hdesk:
            user32.EnumDesktopWindows(hdesk, WNDENUMPROC(cb), 0)
        else:
            user32.EnumWindows(WNDENUMPROC(cb), 0)

        if not acad_hwnds:
            return False

        # Send pure inline LISP (vla-Add + vla-SendCommand) so SECURELOAD never blocks it!
        lsp_posix = lsp_path.resolve().as_posix()
        cmd = (
            '\x1b\x1b(progn (vl-load-com) '
            '(if (boundp (quote ag:live-reload)) '
            f'(ag:live-reload "{dxf_main}" "{dxf_cache}") '
            f'(progn (setq td (vla-Add (vla-get-Documents (vlax-get-acad-object)))) '
            f'(vla-Activate td) (vla-SendCommand td "{inline_swap_escaped}"))))\n'
        )
        buf = ctypes.create_unicode_buffer(cmd)
        cds = COPYDATASTRUCT()
        cds.dwData = 1
        cds.cbData = ctypes.sizeof(buf)
        cds.lpData = ctypes.addressof(buf)

        res_out = ctypes.c_void_p()
        for hwnd in acad_hwnds:
            user32.SendMessageTimeoutW(hwnd, 0x004A, 0, ctypes.byref(cds), 0x0002, 2000, ctypes.byref(res_out))
        return True
    except Exception:
        return False


def save_dxf_zero_touch_in_place(doc, out_path: Path) -> Path:
    """Save DXF directly to out_path; if locked by an open AutoCAD tab, live-reload via inline LISP MDI handoff."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc.saveas(out_path)
        return out_path
    except PermissionError:
        cache_path = out_path.parent / "_live_sync_cache.dxf"
        doc.saveas(cache_path)
        pushed = push_live_dxf_to_running_autocad(out_path, cache_path)
        print(f" [ZERO-TOUCH LIVE SYNC] '{out_path.name}' reloaded in AutoCAD with Model (1:1) + Layout (ISO_A3) (status={pushed})")
        return cache_path if cache_path.exists() else out_path
