# -*- coding: utf-8 -*-
"""
bootstrap.py — RF Online Translator (v15)
==========================================
Paths, tessdata, Ollama, HF, cloud providers.
Todos os subprocessos correm SEM janela de consola (sem flashes).
"""

import os
import sys
import re
import json
import time
import shutil
import tempfile
import subprocess
import importlib


# ==================================================================
# CONSTANTES
# ==================================================================
REQUIRED = [
    ("PyQt6",              "PyQt6"),
    ("requests",           "requests"),
    ("PIL",                "Pillow"),
    ("pytesseract",        "pytesseract"),
    ("pandas",             "pandas"),
    ("dateutil",           "python-dateutil"),
    ("pytz",               "pytz"),
    ("tzdata",             "tzdata"),
    ("speech_recognition", "SpeechRecognition"),
    ("pynput",             "pynput"),
    ("edge_tts",           "edge-tts"),
    ("pygame",             "pygame"),
]
# Python 3.13 tirou o 'audioop' (o reconhecimento de voz precisa dele):
# sem este pacote, num PC novo a voz ficava desligada.
if sys.version_info >= (3, 13):
    REQUIRED.append(("audioop", "audioop-lts"))

PYAUDIO_IMPORT = "pyaudio"
PYAUDIO_PKG    = "pyaudio"

TESSERACT_URL  = ("https://digi.bib.uni-mannheim.de/tesseract/"
                  "tesseract-ocr-w64-setup-5.4.0.20240606.exe")
TESSERACT_PAGE = "https://github.com/UB-Mannheim/tesseract/wiki"

TESSDATA_URL = ("https://raw.githubusercontent.com/"
                "tesseract-ocr/tessdata_fast/main/{}.traineddata")

DEFAULT_TESS_LANGS = ["eng", "por", "rus"]

TESS_LANG_PACKS = {
    "eng":     ("English",              "~4 MB"),
    "por":     ("Portuguese",           "~2 MB"),
    "rus":     ("Russian",              "~4 MB"),
    "spa":     ("Spanish",              "~2 MB"),
    "fra":     ("French",               "~2 MB"),
    "deu":     ("German",               "~2 MB"),
    "ita":     ("Italian",              "~2 MB"),
    "kor":     ("Korean",               "~3 MB"),
    "jpn":     ("Japanese",             "~4 MB"),
    "chi_sim": ("Chinese (Simplified)", "~6 MB"),
    "tur":     ("Turkish",              "~2 MB"),
    "pol":     ("Polish",               "~3 MB"),
    "osd":     ("Orientation/Script",   "~10 MB"),
}

OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_EXE_NAME = "ollama.exe"
OLLAMA_PORT = 11434

HF_API = "https://huggingface.co/api/models"
HF_RESOLVE = "https://huggingface.co/{repo}/resolve/main/{filename}"


_BOOT_LANG = None


def _T(text, **fmt):
    """Frase na língua da app. Com a app a correr usa o core.T (segue a
    língua mudada na janela); no arranque (o bootstrap corre antes de o
    core existir) lê a língua do ui_prefs.json, a escolhida no
    install.bat — o terminal do run.bat também fica nessa língua."""
    global _BOOT_LANG
    core = sys.modules.get("core")
    if core is not None and hasattr(core, "T"):
        return core.T(text, **fmt)
    try:
        if _BOOT_LANG is None:
            _BOOT_LANG = "en"
            with open(os.path.join(_app_dir(), "ui_prefs.json"),
                      encoding="utf-8") as f:
                _BOOT_LANG = json.load(f).get("lang") or "en"
        from i18n import PHRASES
        s = PHRASES.get(text, {}).get(_BOOT_LANG) or text \
            if _BOOT_LANG != "en" else text
    except Exception:
        s = text
    try:
        return s.format(**fmt) if fmt else s
    except Exception:
        return s


# ==================================================================
# SUBPROCESS SEM JANELA
# ==================================================================
def _win_flags():
    flags = 0
    if os.name == "nt":
        flags |= subprocess.CREATE_NO_WINDOW
    return flags


def _win_startupinfo():
    if os.name != "nt":
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return si


def _popen_hidden(cmd, **kwargs):
    kwargs.setdefault("creationflags", 0)
    kwargs["creationflags"] |= _win_flags()
    if os.name == "nt":
        kwargs.setdefault("startupinfo", _win_startupinfo())
    return subprocess.Popen(cmd, **kwargs)


def _run_hidden(cmd, **kwargs):
    kwargs.setdefault("creationflags", 0)
    kwargs["creationflags"] |= _win_flags()
    if os.name == "nt":
        kwargs.setdefault("startupinfo", _win_startupinfo())
    return subprocess.run(cmd, **kwargs)


def _check_call_hidden(cmd, **kwargs):
    kwargs.setdefault("creationflags", 0)
    kwargs["creationflags"] |= _win_flags()
    if os.name == "nt":
        kwargs.setdefault("startupinfo", _win_startupinfo())
    return subprocess.check_call(cmd, **kwargs)


# ==================================================================
# CLOUD PROVIDERS
# ==================================================================
# 'kind': formato da API — 'openai' (a maioria), 'anthropic', 'gemini',
# 'ollama'. 'models': sugestões; o 🔄 na config pede a lista atual ao
# fornecedor (as listas fixas ficam desatualizadas) e o campo aceita
# qualquer nome de modelo.
CLOUD_PROVIDERS = {
    "OpenAI (ChatGPT)": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "models_url": "https://api.openai.com/v1/models",
        "models": ["gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o-mini",
                   "gpt-5-mini", "gpt-4.1"],
        "needs_key": True,
        "docs": "https://platform.openai.com/api-keys",
    },
    "DeepSeek": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.deepseek.com/chat/completions",
        "models_url": "https://api.deepseek.com/models",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "needs_key": True,
        "docs": "https://platform.deepseek.com/api_keys",
    },
    "Anthropic (Claude)": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "anthropic",
        "base_url": "https://api.anthropic.com/v1/messages",
        "models_url": "https://api.anthropic.com/v1/models",
        "models": ["claude-haiku-4-5-20251001", "claude-sonnet-5-5",
                   "claude-opus-5-5"],
        "needs_key": True,
        "docs": "https://console.anthropic.com/settings/keys",
    },
    "Google Gemini": {
        "card": "no",   # cartão: no/yes/deposit/paid
        "free_plan": r"flash|gemma",   # grátis no AI Studio
        "kind": "gemini",
        "base_url": ("https://generativelanguage.googleapis.com/v1beta/"
                     "models/{model}:generateContent"),
        "models_url": ("https://generativelanguage.googleapis.com/v1beta/"
                       "models?pageSize=200"),
        # Grátis (set. 2026): Flash-Lite ~500 pedidos/dia, Flash ~20/dia.
        "models": ["gemini-flash-lite-latest", "gemini-3.5-flash-lite",
                   "gemini-flash-latest"],
        "needs_key": True,
        "docs": "https://aistudio.google.com/app/apikey",
    },
    "xAI (Grok)": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.x.ai/v1/chat/completions",
        "models_url": "https://api.x.ai/v1/models",
        "models": ["grok-3-mini", "grok-3"],
        "needs_key": True,
        "docs": "https://console.x.ai/",
    },
    "Mistral AI": {
        "card": "no",   # cartão: no/yes/deposit/paid
        "free_plan": True,   # plano grátis "Experiment"
        "kind": "openai",
        "base_url": "https://api.mistral.ai/v1/chat/completions",
        "models_url": "https://api.mistral.ai/v1/models",
        "models": ["mistral-small-latest", "mistral-medium-latest",
                   "mistral-large-latest"],
        "needs_key": True,
        "docs": "https://console.mistral.ai/api-keys/",
    },
    "Groq (rápido)": {
        "card": "no",   # cartão: no/yes/deposit/paid
        "free_plan": True,   # plano grátis: todos os modelos (com limites)
        "kind": "openai",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "models_url": "https://api.groq.com/openai/v1/models",
        "models": ["allam-2-7b", "openai/gpt-oss-20b",
                   "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
        "needs_key": True,
        "docs": "https://console.groq.com/keys",
    },
    "Qwen (Alibaba)": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": ("https://dashscope-intl.aliyuncs.com/compatible-mode/"
                     "v1/chat/completions"),
        "models_url": ("https://dashscope-intl.aliyuncs.com/compatible-mode/"
                       "v1/models"),
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
        "needs_key": True,
        "docs": "https://modelstudio.console.alibabacloud.com/",
    },
    "OpenRouter (vários)": {
        "card": "no",   # cartão: no/yes/deposit/paid
        "public_models": True,   # lista não prova a chave
        "kind": "openai",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "models_url": "https://openrouter.ai/api/v1/models",
        "models": ["deepseek/deepseek-chat", "google/gemini-2.5-flash",
                   "openai/gpt-4.1-mini", "meta-llama/llama-3.3-70b-instruct",
                   "qwen/qwen-2.5-72b-instruct"],
        "needs_key": True,
        "docs": "https://openrouter.ai/keys",
    },
    "Together AI": {
        "card": "deposit",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.together.xyz/v1/chat/completions",
        "models_url": "https://api.together.xyz/v1/models",
        # Grátis: os que acabam em '-Free' (6 pedidos/min).
        "free_plan": r"-free$",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                   "meta-llama/Llama-3.3-70B-Instruct-Turbo"],
        "needs_key": True,
        "docs": "https://api.together.xyz/settings/api-keys",
    },
    "Cerebras": {
        "card": "yes",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.cerebras.ai/v1/chat/completions",
        "models_url": "https://api.cerebras.ai/v1/models",
        "models": ["llama-3.3-70b", "llama3.1-8b"],
        "needs_key": True,
        "docs": "https://cloud.cerebras.ai/",
    },
    "Fireworks AI": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.fireworks.ai/inference/v1/chat/completions",
        "models_url": "https://api.fireworks.ai/inference/v1/models",
        "models": ["accounts/fireworks/models/llama-v3p3-70b-instruct",
                   "accounts/fireworks/models/qwen2p5-72b-instruct"],
        "needs_key": True,
        "docs": "https://fireworks.ai/account/api-keys",
    },
    "Perplexity": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "base_url": "https://api.perplexity.ai/chat/completions",
        "models": ["sonar"],
        "needs_key": True,
        "docs": "https://www.perplexity.ai/settings/api",
    },
    "Ollama Cloud": {
        "card": "paid",   # cartão: no/yes/deposit/paid
        "public_models": True,   # lista não prova a chave
        "kind": "ollama",
        "base_url": "https://ollama.com/api/chat",
        "models_url": "https://ollama.com/api/tags",
        "models": ["gpt-oss:20b", "gpt-oss:120b", "gemma4:31b",
                   "deepseek-v4.1-flash"],
        "needs_key": True,
        "docs": "https://ollama.com/settings/keys",
    },
    # NVIDIA build.nvidia.com: +80 modelos grátis para testar/uso pessoal
    # (sem cartão, 40 pedidos/min por modelo).
    "NVIDIA (build.nvidia.com)": {
        "card": "no",   # cartão: no/yes/deposit/paid
        "kind": "openai",
        "public_models": True,   # lista não prova a chave
        "free_plan": True,
        "base_url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "models_url": "https://integrate.api.nvidia.com/v1/models",
        "models": ["deepseek-ai/deepseek-v4.1-flash", "google/gemma-4-31b-it",
                   "moonshotai/kimi-k2.6", "mistralai/mistral-large"],
        "needs_key": True,
        "docs": "https://build.nvidia.com/settings/api-keys",
    },
    # Qualquer servidor compatível com a API da OpenAI (LM Studio, vLLM,
    # outro PC, outro fornecedor): URL na config, chave opcional.
    "Personalizado (OpenAI-compatível)": {
        "kind": "openai",
        "base_url": "",
        "models": [],
        "needs_key": False,
        "docs": "",
    },
    # Um 2.º servidor próprio (ex.: chat no OpenRouter, voz noutro
    # servidor), cada um com o seu URL, chave e modelo.
    "Personalizado 2 (OpenAI-compatível)": {
        "kind": "openai",
        "base_url": "",
        "models": [],
        "needs_key": False,
        "docs": "",
    },
}


# ==================================================================
# HELPERS BÁSICOS
# ==================================================================
def _app_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def pip_env():
    """Ambiente para correr o pip sem janelas: o pip corre 'rustc
    --version' (para o user-agent) se o encontrar no PATH, e esse rustc
    abria uma janela de terminal (o pip não a esconde). Sem as pastas do
    rustc no PATH, não corre."""
    env = dict(os.environ)
    dirs = env.get("PATH", "").split(os.pathsep)
    env["PATH"] = os.pathsep.join(
        d for d in dirs
        if d and not os.path.isfile(os.path.join(d, "rustc.exe"))
        and not os.path.isfile(os.path.join(d, "rustc")))
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _pip(*args) -> bool:
    try:
        # --no-cache-dir: nada fica no perfil do Windows (tudo na app).
        _check_call_hidden([sys.executable, "-m", "pip", *args[:1],
                            "--no-cache-dir", *args[1:]], env=pip_env())
        return True
    except Exception:
        return False


def _is_installed(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


# ==================================================================
# PATHS
# ==================================================================
def get_models_dir() -> str:
    d = os.path.join(_app_dir(), "models")
    os.makedirs(d, exist_ok=True)
    return d


def get_log_dir() -> str:
    d = os.path.join(_app_dir(), "logs")
    os.makedirs(d, exist_ok=True)
    return d


def get_log_path() -> str:
    return os.path.join(get_log_dir(), "rf_translator.log")


def get_profiles_dir() -> str:
    d = os.path.join(_app_dir(), "profiles")
    os.makedirs(d, exist_ok=True)
    return d


def get_app_tessdata_dir() -> str:
    return os.path.join(_app_dir(), "tessdata")


def get_tessdata_path(lang: str) -> str:
    return os.path.join(get_app_tessdata_dir(), f"{lang}.traineddata")


# ==================================================================
# DOWNLOAD
# ==================================================================
def _safe_download_dir() -> str:
    custom = os.environ.get("RF_DOWNLOAD_DIR")
    if custom:
        try:
            os.makedirs(custom, exist_ok=True)
            return custom
        except Exception:
            pass
    local = os.environ.get("LOCALAPPDATA")
    if local:
        d = os.path.join(local, "RFTranslator", "downloads")
        try:
            os.makedirs(d, exist_ok=True)
            return d
        except Exception:
            pass
    d = os.path.join(_app_dir(), "_downloads")
    try:
        os.makedirs(d, exist_ok=True)
        return d
    except Exception:
        pass
    return tempfile.gettempdir()


def _is_ramdisk_like(path: str) -> bool:
    if os.name != "nt":
        return False
    try:
        drive = os.path.splitdrive(os.path.abspath(path))[0].upper()
        sysdrive = os.environ.get("SystemDrive", "C:").upper()
        return drive != sysdrive and drive != ""
    except Exception:
        return False


def _download_file(url, dest, timeout=300, headers=None) -> bool:
    try:
        import requests
        with requests.get(url, stream=True, timeout=timeout,
                          allow_redirects=True, headers=headers or {}) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = done * 100 // total
                            print(f"\r[Setup] Download: {pct}%",
                                  end="", flush=True)
        print()
        return True
    except Exception as e:
        print(_T("\n[Setup] Download failed: {e}", e=e))
        return False


def _strip_zone_identifier(path):
    try:
        with open(path + ":Zone.Identifier", "w"):
            pass
    except Exception:
        pass


# ==================================================================
# ELEVAÇÃO
# ==================================================================
def _run_elevated_and_wait(exe, args, timeout=420) -> int:
    if os.name != "nt":
        return -1
    import ctypes
    from ctypes import wintypes
    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    SEE_MASK_NOASYNC        = 0x00000100
    WAIT_OBJECT_0           = 0x00000000
    WAIT_TIMEOUT            = 0x00000102
    ERROR_CANCELLED         = 1223

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD), ("fMask", ctypes.c_ulong),
            ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HKEY),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NOASYNC
    sei.lpVerb = "runas"
    sei.lpFile = exe
    sei.lpParameters = args
    sei.nShow = 0  # SW_HIDE - também esconder o instalador
    ctypes.windll.kernel32.SetLastError(0)
    ok = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
    if not ok:
        err = ctypes.windll.kernel32.GetLastError()
        if err == ERROR_CANCELLED:
            print(_T("[Setup] UAC cancelled."))
        else:
            print(_T("[Setup] ShellExecuteEx failed ({e}).", e=err))
        return -1
    if not sei.hProcess:
        return 0
    start = time.time()
    while time.time() - start < timeout:
        r = ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 1000)
        if r == WAIT_OBJECT_0:
            code = wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(
                sei.hProcess, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(sei.hProcess)
            return code.value
        if r == WAIT_TIMEOUT:
            continue
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)
        return -2
    ctypes.windll.kernel32.CloseHandle(sei.hProcess)
    return -2


# ==================================================================
# OLLAMA — bloqueio de tray app / popups
# ==================================================================
def _running_exes():
    """Nomes (minúsculas) dos processos a correr, lidos ao Windows sem
    lançar nenhum programa (antes: 9 'taskkill' a cada arranque, ~3 s,
    mesmo sem o ícone do Ollama aberto). None se não der para ler."""
    try:
        import ctypes
        from ctypes import wintypes

        class PE32(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD),
                        ("cntUsage", wintypes.DWORD),
                        ("th32ProcessID", wintypes.DWORD),
                        ("th32DefaultHeapID", ctypes.c_void_p),
                        ("th32ModuleID", wintypes.DWORD),
                        ("cntThreads", wintypes.DWORD),
                        ("th32ParentProcessID", wintypes.DWORD),
                        ("pcPriClassBase", ctypes.c_long),
                        ("dwFlags", wintypes.DWORD),
                        ("szExeFile", ctypes.c_wchar * 260)]
        k32 = ctypes.windll.kernel32
        k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        snap = k32.CreateToolhelp32Snapshot(0x2, 0)    # TH32CS_SNAPPROCESS
        if not snap or snap == ctypes.c_void_p(-1).value:
            return None
        names, e = set(), PE32()
        e.dwSize = ctypes.sizeof(PE32)
        ok = k32.Process32FirstW(ctypes.c_void_p(snap), ctypes.byref(e))
        while ok:
            names.add(e.szExeFile.lower())
            ok = k32.Process32NextW(ctypes.c_void_p(snap), ctypes.byref(e))
        k32.CloseHandle(ctypes.c_void_p(snap))
        return names
    except Exception:
        return None


def kill_ollama_tray():
    if os.name != "nt":
        return
    running = _running_exes()
    for name in ("ollama app.exe", "ollama-app.exe", "ollama app"):
        if running is not None and name not in running:
            continue        # não está aberto: nada a fechar
        try:
            _run_hidden(
                ["taskkill", "/IM", name, "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5)
        except Exception:
            pass


def disable_ollama_tray_autostart():
    if os.name != "nt":
        return
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, "Ollama")
                except FileNotFoundError:
                    pass
        except Exception:
            pass
        approved_path = (r"Software\Microsoft\Windows\CurrentVersion"
                         r"\Explorer\StartupApproved\Run")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, approved_path,
                                0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                try:
                    winreg.SetValueEx(
                        key, "Ollama", 0, winreg.REG_BINARY,
                        b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass


def block_ollama_popups():
    if os.name != "nt":
        return
    kill_ollama_tray()
    disable_ollama_tray_autostart()
    os.environ["OLLAMA_NOSIGNUP"] = "1"
    os.environ["OLLAMA_NO_UPDATE_CHECK"] = "1"
    os.environ["OLLAMA_HIDE_TRAY"] = "1"


# ==================================================================
# CLEANUP
# ==================================================================
def _kill_blockers():
    if os.name != "nt":
        return
    for name in ("python", "pythonw", "ollama", "OllamaSetup"):
        try:
            _run_hidden(
                ["taskkill", "/IM", f"{name}.exe", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5)
        except Exception:
            pass


def cleanup_incomplete_downloads(verbose=True, aggressive=False) -> dict:
    if aggressive:
        if verbose:
            print("[Cleanup] A terminar processos...")
        _kill_blockers()
        time.sleep(1.5)
    targets = [
        os.path.join(_app_dir(), "models"),
        os.path.join(_app_dir(), "_downloads"),
        os.path.join(_app_dir(), "ollama", "models", "blobs"),
        _safe_download_dir(),
    ]
    bad_exts = (".part", ".tmp", ".partial", ".crdownload", ".download")
    removed, failed = [], []
    freed_bytes = 0

    def try_delete(full):
        nonlocal freed_bytes
        try:
            size = os.path.getsize(full)
            os.remove(full)
            removed.append(full)
            freed_bytes += size
            if verbose:
                print(f"[Cleanup] Apagado: {full}")
        except PermissionError:
            try:
                _run_hidden(
                    ["powershell", "-NoProfile", "-Command",
                     f"Remove-Item -LiteralPath '{full}' -Force"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=10)
                if not os.path.exists(full):
                    removed.append(full)
                    if verbose:
                        print(f"[Cleanup] Apagado (PS): {full}")
                    return
            except Exception:
                pass
            failed.append((full, "em uso"))
        except Exception as e:
            failed.append((full, str(e)))

    for root in targets:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                lower = fn.lower()
                # Modelo a meio ('x.gguf.part'): o download continua daqui
                # da próxima vez — só a limpeza 'aggressive' o apaga.
                if lower.endswith(".gguf.part") and not aggressive:
                    continue
                if lower.endswith(bad_exts):
                    try_delete(full)
                    continue
                try:
                    if os.path.getsize(full) == 0:
                        try_delete(full)
                        continue
                except Exception:
                    pass
                if "partial" in lower and os.path.basename(dirpath) == "blobs":
                    try_delete(full)
                    continue
    return {"removed": removed, "failed": failed,
            "freed_mb": round(freed_bytes / (1024 * 1024), 1)}


def cleanup_empty_model_dirs(verbose=True) -> int:
    removed = 0
    for root in [get_models_dir(), os.path.join(_app_dir(), "_downloads")]:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            if dirpath == root:
                continue
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    removed += 1
                    if verbose:
                        print(f"[Cleanup] Pasta vazia: {dirpath}")
            except Exception:
                pass
    return removed


def full_cleanup(verbose=True) -> dict:
    print("=" * 60)
    print("  Cleanup — Downloads incompletos")
    print("=" * 60)
    r1 = cleanup_incomplete_downloads(verbose=verbose, aggressive=True)
    dirs = cleanup_empty_model_dirs(verbose=verbose)
    print("-" * 60)
    print(f"  Ficheiros apagados  : {len(r1['removed'])}")
    print(f"  Espaço libertado    : {r1['freed_mb']} MB")
    print(f"  Pastas vazias       : {dirs}")
    if r1["failed"]:
        print(f"  ⚠️  Presos           : {len(r1['failed'])}")
    print("=" * 60)
    return r1


# ==================================================================
# DEPENDÊNCIAS PYTHON
# ==================================================================
def ensure_dependencies():
    missing = [pkg for mod, pkg in REQUIRED if not _is_installed(mod)]
    if missing:
        # O pip só corre quando falta alguma coisa: a cada arranque abria
        # uma janela de terminal (o pip corre 'rustc --version' sem a
        # esconder) e gastava uns segundos.
        print(_T("[Setup] Checking pip..."))
        try:
            _check_call_hidden(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir",
                 "--upgrade", "pip", "--quiet"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=pip_env())
        except Exception:
            pass
        print(_T("[Setup] Installing {n}: {l}", n=len(missing), l=", ".join(missing)))
        if not _pip("install", "--upgrade", *missing):
            for pkg in missing:
                print(f"[Setup]   -> {pkg}")
                _pip("install", "--upgrade", pkg)
        importlib.invalidate_caches()
        still = [pkg for mod, pkg in REQUIRED if not _is_installed(mod)]
        if still:
            print(_T("[Setup] WARNING: still missing: {l}", l=", ".join(still)))
    else:
        print(_T("[Setup] Python packages OK."))
    if not _is_installed(PYAUDIO_IMPORT):
        print(_T("[Setup] PyAudio missing — trying to install..."))
        ok = _pip("install", PYAUDIO_PKG) and _is_installed(PYAUDIO_IMPORT)
        if not ok and os.name == "nt":
            if _pip("install", "pipwin"):
                try:
                    _check_call_hidden(
                        [sys.executable, "-m", "pipwin", "install",
                         PYAUDIO_PKG])
                    ok = _is_installed(PYAUDIO_IMPORT)
                except Exception:
                    pass
        if not ok:
            print(_T("[Setup] WARNING: PyAudio not available. Voice turned off."))
    else:
        print("[Setup] PyAudio OK.")


# ==================================================================
# TESSERACT
# ==================================================================
def _tesseract_candidates():
    app = _app_dir()
    return [
        os.path.join(app, "tesseract", "tesseract.exe"),
        os.path.join(app, "Tesseract-OCR", "tesseract.exe"),
        os.path.join(app, "tesseract-ocr", "tesseract.exe"),
        os.path.join(app, "bin", "tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(
            r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract", "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
        "/usr/local/Cellar/tesseract/bin/tesseract",
    ]


def find_tesseract():
    for cand in _tesseract_candidates():
        if os.path.isfile(cand):
            return cand
    return shutil.which("tesseract")


def try_install_tesseract_winget():
    if os.name != "nt":
        return None
    if not shutil.which("winget"):
        print(_T("[Setup] winget not available."))
        return None
    print(_T("[Setup] Attempt 1: winget..."))
    try:
        _check_call_hidden(
            ["winget", "install", "--id",
             "UB-Mannheim.TesseractOCR", "--silent",
             "--accept-package-agreements",
             "--accept-source-agreements",
             "--disable-interactivity"], timeout=600)
    except Exception as e:
        print(_T("[Setup] winget failed: {e}", e=e))
        return None
    p = find_tesseract()
    if p:
        print(f"[Setup] Tesseract via winget: {p}")
    return p


def try_install_tesseract_download():
    if os.name != "nt":
        return None
    target_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    for c in target_candidates:
        if os.path.isfile(c):
            print(_T("[Setup] Already there: {p}", p=c))
            return c
    dl_dir = _safe_download_dir()
    if _is_ramdisk_like(dl_dir):
        print(_T("[Setup] WARNING: suspicious folder ({p}).", p=dl_dir))
        fallback = os.path.join(
            os.environ.get("LOCALAPPDATA", r"C:\\"),
            "RFTranslator", "downloads")
        try:
            os.makedirs(fallback, exist_ok=True)
            dl_dir = fallback
        except Exception:
            pass
    installer = os.path.join(dl_dir, "tesseract-setup.exe")
    print(_T("[Setup] Attempt 2: downloading Tesseract..."))
    if not _download_file(TESSERACT_URL, installer, timeout=180):
        return None
    _strip_zone_identifier(installer)
    if not os.path.isfile(installer):
        return None
    size = os.path.getsize(installer)
    if size < 30 * 1024 * 1024:
        print(_T("[Setup] File too small ({n}).", n=size))
        try:
            os.remove(installer)
        except Exception:
            pass
        return None
    print(f"[Setup] OK ({size // (1024 * 1024)} MB)")
    print(_T("[Setup] Starting the installer with UAC (click Yes)..."))
    exit_code = _run_elevated_and_wait(installer, "/S", timeout=420)
    if exit_code == -1:
        try:
            os.remove(installer)
        except Exception:
            pass
        return None
    for _ in range(20):
        for c in target_candidates:
            if os.path.isfile(c):
                print(f"[Setup] ✅ Tesseract: {c}")
                try:
                    os.remove(installer)
                except Exception:
                    pass
                return c
        time.sleep(1)
    print(_T("[Setup] tesseract.exe did not appear."))
    return None


def ensure_tesseract(auto_install=True):
    try:
        import pytesseract
    except Exception as e:
        return False, f"pytesseract não importável: {e}"
    path = find_tesseract()
    if not path and auto_install:
        path = try_install_tesseract_winget()
        if not path:
            path = try_install_tesseract_download()
    if not path:
        print(_T("[Setup] Install it by hand: {u}", u=TESSERACT_PAGE))
        return False, "Tesseract não encontrado."
    try:
        pytesseract.pytesseract.tesseract_cmd = path
        version = pytesseract.get_tesseract_version()
        return True, f"{path} (v{version})"
    except Exception as e:
        return False, f"Tesseract em {path}, mas falhou: {e}"


# ==================================================================
# TESSDATA
# ==================================================================
def is_tessdata_installed(lang) -> bool:
    if os.path.isfile(get_tessdata_path(lang)):
        return True
    tess = find_tesseract()
    if tess:
        sys_td = os.path.join(os.path.dirname(tess), "tessdata")
        if os.path.isfile(os.path.join(sys_td, f"{lang}.traineddata")):
            return True
    return False


def download_tessdata_lang(lang, timeout=120) -> bool:
    td = get_app_tessdata_dir()
    os.makedirs(td, exist_ok=True)
    dest = get_tessdata_path(lang)
    if os.path.isfile(dest):
        return True
    url = TESSDATA_URL.format(lang)
    print(_T("[Setup] Downloading tessdata: {l}", l=lang))
    try:
        import requests
        with requests.get(url, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = done * 100 // total
                            print(f"\r[Setup] {lang}: {pct}%",
                                  end="", flush=True)
        print()
        return True
    except Exception as e:
        print(_T("\n[Setup] Failed {l}: {e}", l=lang, e=e))
        try:
            if os.path.isfile(dest):
                os.remove(dest)
        except Exception:
            pass
        return False


def ensure_tessdata_defaults(tesseract_exe, auto_download=True) -> bool:
    td = get_app_tessdata_dir()
    os.makedirs(td, exist_ok=True)
    sys_td = os.path.join(os.path.dirname(tesseract_exe), "tessdata")
    missing = [l for l in DEFAULT_TESS_LANGS
               if not os.path.isfile(get_tessdata_path(l))]
    if missing and os.path.isdir(sys_td):
        copied = []
        for l in list(missing):
            src = os.path.join(sys_td, f"{l}.traineddata")
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, get_tessdata_path(l))
                    copied.append(l)
                    missing.remove(l)
                except Exception:
                    pass
        if copied:
            print(_T("[Setup] Copied: {l}", l=", ".join(copied)))
    if missing and auto_download:
        print(_T("[Setup] Downloading {n} tessdata...", n=len(missing)))
        for l in missing:
            download_tessdata_lang(l)
    have = [l for l in DEFAULT_TESS_LANGS
            if os.path.isfile(get_tessdata_path(l))
            or os.path.isfile(os.path.join(sys_td, f"{l}.traineddata"))]
    print(f"[Setup] Tessdata: {len(have)}/{len(DEFAULT_TESS_LANGS)}")
    return len(have) == len(DEFAULT_TESS_LANGS)


# ==================================================================
# OLLAMA
# ==================================================================
def _ollama_app_dir() -> str:
    return os.path.join(_app_dir(), "ollama")


def _ollama_exe_path() -> str:
    return os.path.join(_ollama_app_dir(), OLLAMA_EXE_NAME)


def _ollama_models_dir() -> str:
    return os.path.join(_ollama_app_dir(), "models")


def is_ollama_running(timeout=1.5) -> bool:
    try:
        import requests
        r = requests.get(f"http://localhost:{OLLAMA_PORT}/api/tags",
                         timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def list_ollama_installed_models(timeout=3.0):
    try:
        import requests
        r = requests.get(f"http://localhost:{OLLAMA_PORT}/api/tags",
                         timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
        names = [m.get("name", "")
                 for m in data.get("models", []) if m.get("name")]
        names.sort(key=lambda s: s.lower())
        return names
    except Exception:
        return []


def find_ollama_exe():
    p = _ollama_exe_path()
    if os.path.isfile(p):
        return p
    p = shutil.which("ollama")
    if p:
        return p
    for c in [
        os.path.expanduser(
            r"~\AppData\Local\Programs\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
    ]:
        if os.path.isfile(c):
            return c
    return None


# ------------------------------------------------------------------
# OLLAMA: fechar tudo o que a app abriu
# ------------------------------------------------------------------
# O servidor que ESTA app arranca é dela: tem de fechar com ela, também num
# crash. Um Ollama que já estava aberto (o do utilizador) nunca é tocado.
# Três redes: (1) Job Object do Windows com KILL_ON_JOB_CLOSE - o sistema
# mata o servidor e os 'runners' quando a app acaba, seja como for;
# (2) stop_app_ollama() no fecho normal; (3) o vigia (main.py) e o
# kill_orphan_app_ollama() no arranque limpam o que ficou de versões antigas
# (processos cujo .exe está na pasta ollama\ da app).
_JOB = None
_OWNED_PROCS = []          # os Popen do 'ollama serve' que a app arrancou
_JOB_KILL_ON_CLOSE = 0x2000
_SINGLE_INSTANCE_MUTEX = "RFOnlineTranslator.SingleInstance"


def _kernel32():
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                          ctypes.c_void_p, wintypes.DWORD]
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD)]
    k.OpenMutexW.restype = wintypes.HANDLE
    k.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    return k


def _kill_on_exit_job():
    """Um Job Object só da app: tudo o que lá estiver morre quando a app
    termina (o handle fecha com o processo, mesmo num crash)."""
    global _JOB
    if _JOB or os.name != "nt":
        return _JOB
    import ctypes
    from ctypes import wintypes

    class _Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _Io(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in (
            "ReadOperationCount", "WriteOperationCount",
            "OtherOperationCount", "ReadTransferCount",
            "WriteTransferCount", "OtherTransferCount")]

    class _Ext(ctypes.Structure):
        _fields_ = [("Basic", _Basic), ("Io", _Io),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    try:
        k = _kernel32()
        job = k.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _Ext()
        info.Basic.LimitFlags = _JOB_KILL_ON_CLOSE
        if not k.SetInformationJobObject(job, 9, ctypes.byref(info),
                                         ctypes.sizeof(info)):
            return None
        _JOB = job
    except Exception:
        return None
    return _JOB


def _own_ollama(proc):
    """Regista o 'ollama serve' que a app arrancou e põe-no no Job Object."""
    _OWNED_PROCS.append(proc)
    if os.name != "nt":
        return
    try:
        job = _kill_on_exit_job()
        if job:
            _kernel32().AssignProcessToJobObject(job, int(proc._handle))
    except Exception:
        pass


def _app_ollama_pids():
    """PIDs dos processos cujo .exe está na pasta ollama\\ da app (servidor
    e 'runners' dos modelos). Só o Ollama da app, nunca o do sistema."""
    if os.name != "nt":
        return []
    import ctypes
    from ctypes import wintypes
    root = os.path.normcase(os.path.abspath(_ollama_app_dir())) + os.sep
    k = _kernel32()

    class _Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260)]

    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Entry)]
    k.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Entry)]
    snap = k.CreateToolhelp32Snapshot(0x2, 0)          # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return []
    pids = []
    try:
        e = _Entry()
        e.dwSize = ctypes.sizeof(_Entry)
        ok = k.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            h = k.OpenProcess(0x1000, False, e.th32ProcessID)  # QUERY_LIMITED
            if h:
                try:
                    buf = ctypes.create_unicode_buffer(1024)
                    n = wintypes.DWORD(1024)
                    if k.QueryFullProcessImageNameW(h, 0, buf,
                                                    ctypes.byref(n)):
                        if os.path.normcase(buf.value).startswith(root):
                            pids.append(int(e.th32ProcessID))
                finally:
                    k.CloseHandle(h)
            ok = k.Process32NextW(snap, ctypes.byref(e))
    finally:
        k.CloseHandle(snap)
    return pids


def _kill_pid_tree(pid):
    try:
        _run_hidden(["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=10)
    except Exception:
        pass


def stop_app_ollama() -> int:
    """Fecha o Ollama da app: o servidor que ela arrancou (também se for o
    do sistema) e qualquer processo da pasta ollama\\ da app. Devolve
    quantos fechou. Não toca num Ollama que já estava aberto antes."""
    pids = set(_app_ollama_pids())
    for proc in _OWNED_PROCS:
        try:
            if proc.poll() is None:            # poll: o PID pode ter sido reutilizado
                pids.add(proc.pid)
        except Exception:
            pass
    _OWNED_PROCS.clear()
    for pid in pids:
        _kill_pid_tree(pid)
    return len(pids)


def kill_orphan_app_ollama() -> int:
    """No arranque: se NÃO há outra cópia da app aberta, qualquer Ollama da
    pasta da app que esteja a correr ficou de uma sessão que acabou mal
    (ou de uma versão antiga sem esta limpeza). Fecha-o."""
    if os.name != "nt":
        return 0
    try:
        k = _kernel32()
        h = k.OpenMutexW(0x00100000, False, _SINGLE_INSTANCE_MUTEX)  # SYNCHRONIZE
        if h:                                   # outra cópia está viva: não tocar
            k.CloseHandle(h)
            return 0
    except Exception:
        return 0
    try:
        pids = _app_ollama_pids()
    except Exception:
        return 0
    for pid in pids:
        _kill_pid_tree(pid)
    return len(pids)


def start_ollama_server(ollama_exe, extra_env=None):
    if is_ollama_running():
        kill_ollama_tray()
        return True
    models_dir = _ollama_models_dir()
    os.makedirs(models_dir, exist_ok=True)
    env = {**os.environ,
           "OLLAMA_MODELS": models_dir,
           "OLLAMA_NOSIGNUP": "1",
           "OLLAMA_NO_UPDATE_CHECK": "1",
           "OLLAMA_HIDE_TRAY": "1"}
    # Só 1 modelo na VRAM (o jogo também precisa dela), também quando o
    # Ollama arranca aqui no início, antes de a config ser lida.
    env.setdefault("OLLAMA_MAX_LOADED_MODELS", "1")
    if extra_env:
        env.update({k: str(v) for k, v in extra_env.items()
                    if v is not None})
    creationflags = 0
    if os.name == "nt":
        # CREATE_NO_WINDOW (consola escondida), NÃO DETACHED_PROCESS: sem
        # consola nenhuma, cada processo que o Ollama lança para carregar
        # um modelo abria uma consola nova que piscava no ecrã. Com a
        # consola escondida, esses processos herdam-na e não aparecem.
        creationflags = (subprocess.CREATE_NO_WINDOW |
                         subprocess.CREATE_NEW_PROCESS_GROUP)
    try:
        si = _win_startupinfo()
        proc = _popen_hidden([ollama_exe, "serve"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL,
                             creationflags=creationflags,
                             startupinfo=si,
                             env=env, close_fds=True)
        _own_ollama(proc)       # morre com a app: fechada, crash ou morta
    except Exception as e:
        print(_T("[Setup] Error starting ollama serve: {e}", e=e))
        return False
    for _ in range(30):
        if is_ollama_running():
            kill_ollama_tray()
            return True
        time.sleep(0.5)
    kill_ollama_tray()
    return False


def try_install_ollama_download():
    if os.name != "nt":
        return None
    p = find_ollama_exe()
    if p:
        print(_T("[Setup] Ollama already installed: {p}", p=p))
        return p
    print(_T("[Setup] Ollama not found — downloading (~700 MB)..."))
    dl_dir = _safe_download_dir()
    if _is_ramdisk_like(dl_dir):
        fallback = os.path.join(
            os.environ.get("LOCALAPPDATA", r"C:\\"),
            "RFTranslator", "downloads")
        try:
            os.makedirs(fallback, exist_ok=True)
            dl_dir = fallback
        except Exception:
            pass
    installer = os.path.join(dl_dir, "OllamaSetup.exe")
    if not _download_file(OLLAMA_DOWNLOAD_URL, installer, timeout=600):
        return None
    _strip_zone_identifier(installer)
    if not os.path.isfile(installer):
        return None
    size = os.path.getsize(installer)
    if size < 100 * 1024 * 1024:
        print(_T("[Setup] File too small ({n}).",
                 n=f"{size // (1024 * 1024)} MB"))
        try:
            os.remove(installer)
        except Exception:
            pass
        return None
    install_dir = _ollama_app_dir()
    os.makedirs(install_dir, exist_ok=True)
    print(_T("[Setup] Installing Ollama in: {p}", p=install_dir))
    args = [installer, "/VERYSILENT", "/NORESTART",
            "/SUPPRESSMSGBOXES", "/SP-", f"/DIR={install_dir}"]
    try:
        _run_hidden(args, timeout=600,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(_T("[Setup] Installer error: {e}", e=e))
        return None
    for _ in range(15):
        if os.path.isfile(_ollama_exe_path()):
            print(f"[Setup] ✅ Ollama: {_ollama_exe_path()}")
            kill_ollama_tray()
            disable_ollama_tray_autostart()
            try:
                os.remove(installer)
            except Exception:
                pass
            return _ollama_exe_path()
        time.sleep(1)
    p = find_ollama_exe()
    if p:
        kill_ollama_tray()
        disable_ollama_tray_autostart()
        try:
            os.remove(installer)
        except Exception:
            pass
        return p
    print(_T("[Setup] ollama.exe did not appear."))
    return None


def ensure_ollama(auto_install=True):
    kill_ollama_tray()
    block_ollama_popups()
    if is_ollama_running():
        print(_T("[Setup] Ollama already online at localhost:{p}", p=OLLAMA_PORT))
        kill_ollama_tray()
        return True
    ollama_exe = find_ollama_exe()
    if not ollama_exe:
        if not auto_install:
            print(_T("[Setup] Ollama not found."))
            return False
        ollama_exe = try_install_ollama_download()
    if not ollama_exe:
        print(_T("[Setup] WARNING: Ollama not available."))
        return False
    print(_T("[Setup] Starting the Ollama service..."))
    if start_ollama_server(ollama_exe):
        print(_T("[Setup] ✅ Ollama online at localhost:{p}", p=OLLAMA_PORT))
        return True
    print(_T("[Setup] WARNING: the Ollama service did not start."))
    return False


# ==================================================================
# HUGGING FACE
# ==================================================================
def hf_list_repo_files(repo_id, token=None, timeout=30):
    import requests
    url = f"{HF_API}/{repo_id}/tree/main"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    entries = r.json()
    files = []
    for e in entries:
        if e.get("type") != "file":
            continue
        path = e.get("path", "")
        if not path.lower().endswith(".gguf"):
            continue
        files.append({"path": path, "size": e.get("size", 0)})
    files.sort(key=lambda x: x["path"])
    return files


def hf_list_repo_files_safe(repo_id, token=None, timeout=30):
    if not repo_id or "/" not in repo_id:
        return [], _T("Invalid format. Use user/repo."), "notfound"
    try:
        import requests
        url = f"{HF_API}/{repo_id}/tree/main"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 401:
            return [], _T("🔒 Gated repo: {r}\nAccept the terms at "
                          "https://huggingface.co/{r} and paste a token.",
                          r=repo_id), "auth"
        if r.status_code == 404:
            return [], _T("❌ Repo not found: {r}", r=repo_id), "notfound"
        if r.status_code == 403:
            return [], _T("🚫 Access denied (403). A token is needed."), "auth"
        r.raise_for_status()
        entries = r.json()
    except Exception as e:
        return [], _T("Network error: {e}", e=e), "network"
    files = []
    for e in entries:
        if e.get("type") != "file":
            continue
        path = e.get("path", "")
        if not path.lower().endswith(".gguf"):
            continue
        files.append({"path": path, "size": e.get("size", 0)})
    files.sort(key=lambda x: x["path"])
    return files, "", ""


def hf_search_models(query, token=None, limit=60, only_gguf=True,
                     timeout=30):
    if not query or len(query) < 2:
        return [], _T("Type at least 2 letters."), "other"
    try:
        import requests
        params = {"search": query,
                  "limit": max(1, min(limit, 200)),
                  "sort": "downloads", "direction": "-1"}
        if only_gguf:
            params["filter"] = "gguf"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(HF_API, params=params, headers=headers,
                         timeout=timeout)
        if r.status_code == 401:
            return [], _T("🔒 Hugging Face asked for a token."), "auth"
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return [], _T("Unexpected answer."), "other"
        results = []
        for m in data:
            mid = m.get("id") or m.get("modelId") or m.get("_id", "")
            if not mid or "/" not in mid:
                continue
            results.append({
                "id": mid,
                "downloads": int(m.get("downloads") or 0),
                "likes": int(m.get("likes") or 0),
            })
        if not results:
            return [], _T("Nothing found for '{q}'.", q=query), "notfound"
        return results, "", ""
    except Exception as e:
        return [], _T("Network error: {e}", e=e), "network"


def hf_download_gguf(repo_id, filename, dest_dir, token=None,
                     progress_cb=None, timeout=7200, tries=30):
    """(caminho, None) ou (None, erro). Os modelos têm 2-9 GB: um corte
    de rede ou 60 s parado apagava tudo e recomeçava do zero (com uma
    ligação instável nunca acabava). Agora continua de onde ficou (HTTP
    Range) e tenta outra vez até 'tries' vezes."""
    import requests
    os.makedirs(dest_dir, exist_ok=True)
    basename = os.path.basename(filename)
    dest = os.path.join(dest_dir, basename)
    if os.path.isfile(dest):
        if os.path.getsize(dest) > 100 * 1024 * 1024:
            return dest, None
    url = HF_RESOLVE.format(repo=repo_id, filename=filename)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    tmp = dest + ".part"
    total, err, start = 0, None, time.time()
    for attempt in range(tries):
        if time.time() - start > timeout:
            break
        done = os.path.getsize(tmp) if os.path.isfile(tmp) else 0
        if total and done >= total:
            break
        h = dict(headers)
        if done:
            h["Range"] = f"bytes={done}-"
        try:
            with requests.get(url, headers=h, stream=True,
                              timeout=(30, 60), allow_redirects=True) as r:
                if r.status_code == 416:        # já tem tudo
                    break
                if r.status_code in (401, 403):
                    return None, _T(
                        "🔒 {s}: {r} — accept the terms on the Hugging "
                        "Face site and paste a token.",
                        s=r.status_code, r=repo_id)
                if r.status_code == 404:
                    return None, f"❌ 404: {repo_id}/{filename}"
                r.raise_for_status()
                if done and r.status_code != 206:
                    done = 0            # o servidor não retoma: do início
                length = int(r.headers.get("content-length", 0))
                total = done + length if length else total
                with open(tmp, "ab" if done else "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                            if progress_cb:
                                progress_cb(done, total)
            if not total or done >= total:
                break
            err = _T("connection cut at {n} MB", n=done // (1024 * 1024))
        except Exception as e:
            err = str(e)
        print(_T("[HF] Attempt {a}/{b} failed: {e}", a=attempt + 1, b=tries, e=err))
        time.sleep(min(30, 2 + attempt * 2))
    size = os.path.getsize(tmp) if os.path.isfile(tmp) else 0
    if size and (not total or size >= total):
        if os.path.isfile(dest):
            os.remove(dest)
        os.rename(tmp, dest)
        return dest, None
    # O .part fica: ao descarregar outra vez continua daqui.
    return None, _T("Download failed ({a}/{b} MB): {e}",
                    a=size // (1024 * 1024), b=total // (1024 * 1024),
                    e=err or _T("no answer"))


def ollama_create_model(model_name, gguf_path, system_prompt=None,
                        ollama_exe=None, timeout=3600):
    if not ollama_exe:
        ollama_exe = find_ollama_exe()
    if not ollama_exe:
        return False, _T("ollama.exe not found")
    if not os.path.isfile(gguf_path):
        return False, _T("GGUF does not exist: {p}", p=gguf_path)
    if not is_ollama_running():
        if not start_ollama_server(ollama_exe):
            return False, _T("The Ollama service is not running")
    modelfile_path = os.path.join(
        os.path.dirname(gguf_path),
        f"{os.path.basename(gguf_path)}.Modelfile")
    try:
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write(f'FROM "{os.path.abspath(gguf_path)}"\n')
            if system_prompt:
                f.write(f'SYSTEM """{system_prompt}"""\n')
            f.write('PARAMETER temperature 0.2\n')
    except Exception as e:
        return False, _T("Modelfile failed: {e}", e=e)
    try:
        result = _run_hidden(
            [ollama_exe, "create", model_name, "-f", modelfile_path],
            timeout=timeout, capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            return False, _T("ollama create failed: {e}", e=err[:500])
        return True, _T("Model created.")
    except subprocess.TimeoutExpired:
        return False, _T("Creating the model took too long.")
    except Exception as e:
        return False, str(e)


def ollama_delete_model(model_name, ollama_exe=None):
    if not ollama_exe:
        ollama_exe = find_ollama_exe()
    if not ollama_exe:
        return False, _T("ollama.exe not found")
    try:
        result = _run_hidden(
            [ollama_exe, "rm", model_name],
            timeout=60, capture_output=True, text=True)
        if result.returncode != 0:
            return False, (result.stderr or result.stdout or "").strip()
        return True, _T("Model deleted.")
    except Exception as e:
        return False, str(e)


def list_local_ggufs():
    root = get_models_dir()
    found = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".gguf"):
                full = os.path.join(dirpath, fn)
                try:
                    size = os.path.getsize(full)
                except Exception:
                    size = 0
                rel = os.path.relpath(full, root)
                found.append((rel, size))
    found.sort(key=lambda x: x[0])
    return found


# ==================================================================
# ENTRY
# ==================================================================
def bootstrap():
    print("=" * 60)
    print("  RF Online Translator — Bootstrap")
    print("=" * 60)
    auto = os.environ.get("RF_NO_AUTO_INSTALL", "0") != "1"
    block_ollama_popups()
    try:
        _r = cleanup_incomplete_downloads(verbose=False)
        if _r["removed"]:
            print(_T("[Setup] Cleanup: {n} file(s) — {m} MB",
                     n=len(_r["removed"]), m=_r["freed_mb"]))
        cleanup_empty_model_dirs(verbose=False)
    except Exception as e:
        print(_T("[Setup] Cleanup failed: {e}", e=e))
    ensure_dependencies()
    tesseract_ok, tesseract_msg = ensure_tesseract(auto_install=auto)
    tessdata_ok = False
    if tesseract_ok:
        tess = find_tesseract()
        if tess:
            tessdata_ok = ensure_tessdata_defaults(tess,
                                                    auto_download=auto)
    ollama_ok = ensure_ollama(auto_install=auto)
    get_models_dir()
    get_log_dir()
    get_profiles_dir()
    n_models = len(list_ollama_installed_models()) if ollama_ok else 0
    print("=" * 60)
    print(_T("  Summary"))
    print("=" * 60)
    print(f"  Tesseract : {'✅ OK' if tesseract_ok else '⚠️'}")
    print(f"  Tessdata  : {'✅ OK' if tessdata_ok else '⚠️'}")
    print(f"  Ollama    : {'✅ online' if ollama_ok else '⚠️ offline'}")
    if ollama_ok:
        print(_T("  Models    : {n}", n=n_models))
    print("=" * 60)
    return tesseract_ok, tesseract_msg


if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        full_cleanup(verbose=True)
    elif "--cleanup-quiet" in sys.argv:
        full_cleanup(verbose=False)
    elif "--list-models" in sys.argv:
        for m in list_ollama_installed_models() or ["(nenhum)"]:
            print(m)
    elif "--kill-tray" in sys.argv:
        kill_ollama_tray()
        disable_ollama_tray_autostart()
        print("Tray bloqueada.")
    elif "--search" in sys.argv:
        try:
            q = sys.argv[sys.argv.index("--search") + 1]
        except Exception:
            q = ""
        if not q:
            print("Uso: py bootstrap.py --search <termo>")
        else:
            results, err, _ = hf_search_models(q)
            if err:
                print(f"Erro: {err}")
            else:
                for r in results:
                    print(f"  • {r['id']}  ({r['downloads']:,} dl)")
    else:
        ok, info = bootstrap()
        print(f"\nTesseract: {'OK' if ok else 'FALHOU'}\nInfo: {info}")