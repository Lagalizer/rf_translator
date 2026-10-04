# -*- coding: utf-8 -*-
"""
core.py — RF Online Translator
==============================
Motor central: logger, i18n, idiomas, IA, TTS, workers, profiles.
Suporta my_name, last_config, aparência persistida, hotkey configurável.
"""

import os
import sys
import re
import json
import time
import queue
import asyncio
import ctypes
import random
import logging
import tempfile
import threading
import webbrowser
from collections import deque
from dataclasses import dataclass, asdict, field, replace as dc_replace
from difflib import SequenceMatcher
from logging.handlers import RotatingFileHandler


# ==================================================================
# BOOTSTRAP
# ==================================================================
try:
    from bootstrap import (
        get_log_path, get_profiles_dir, get_models_dir,
        get_app_tessdata_dir, get_tessdata_path, is_tessdata_installed,
        download_tessdata_lang, TESS_LANG_PACKS,
        hf_list_repo_files, hf_list_repo_files_safe, hf_search_models,
        hf_download_gguf, ollama_create_model, ollama_delete_model,
        list_local_ggufs, find_ollama_exe, is_ollama_running,
        start_ollama_server, list_ollama_installed_models, kill_ollama_tray,
        CLOUD_PROVIDERS,
    )
except Exception as _e:
    print(f"[core] Bootstrap indisponível: {_e}")

    def get_log_path(): return "./logs/rf_translator.log"
    def get_profiles_dir(): return "./profiles"
    def get_models_dir(): return "./models"
    def get_app_tessdata_dir(): return ""
    def get_tessdata_path(l): return ""
    def is_tessdata_installed(l): return True
    def download_tessdata_lang(l, timeout=120): return False
    TESS_LANG_PACKS = {}
    def hf_list_repo_files(*a, **k): return []
    def hf_list_repo_files_safe(*a, **k): return [], "off", "other"
    def hf_search_models(*a, **k): return [], "off", "other"
    def hf_download_gguf(*a, **k): return None, "off"
    def ollama_create_model(*a, **k): return False, "off"
    def ollama_delete_model(*a, **k): return False, "off"
    def list_local_ggufs(): return []
    def find_ollama_exe(): return None
    def is_ollama_running(**k): return False
    def start_ollama_server(exe, extra_env=None): return False
    def list_ollama_installed_models(**k): return []
    def kill_ollama_tray(): pass
    CLOUD_PROVIDERS = {"DeepSeek": {
        "base_url": "https://api.deepseek.com/chat/completions",
        "models": ["deepseek-chat"], "needs_key": True,
        "docs": "https://platform.deepseek.com/api_keys"}}


# ==================================================================
# FLAGS
# ==================================================================
TESS_OK = True
TESS_INFO = "unknown"

import requests
import edge_tts
import pygame
import pytesseract
from PIL import ImageGrab, Image, ImageChops, ImageFilter, ImageOps, ImageStat

def _tess_run_mem(image, extension="", lang=None, config="", nice=0,
                  timeout=0, return_bytes=False):
    """Substitui pytesseract.run_and_get_output: a captura do jogo vai
    para o Tesseract por 'pipe' (stdin) e o texto volta por stdout. O
    pytesseract original gravava cada captura do chat num PNG no Temp
    (e o resultado num .txt/.tsv) — agora nada toca no disco."""
    import io
    import shlex
    import subprocess
    pt = pytesseract.pytesseract
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    buf = io.BytesIO()
    image.save(buf, "PNG", compress_level=1)
    cmd = [pt.tesseract_cmd, "stdin", "stdout"]
    if lang:
        cmd += ["-l", lang]
    if config:
        cmd += shlex.split(config, posix=(sys.platform != "win32"))
    exts = extension.split()
    cmd += [e for e in exts if e not in {"box", "osd", "tsv", "xml"}]
    if "tsv" in exts:
        cmd.append("tsv")
    try:
        p = subprocess.run(cmd, input=buf.getvalue(), capture_output=True,
                           timeout=timeout or None,
                           creationflags=getattr(subprocess,
                                                 "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        raise pt.TesseractNotFoundError()
    except subprocess.TimeoutExpired:
        raise RuntimeError("Tesseract process timeout")
    if p.returncode:
        raise pt.TesseractError(p.returncode, pt.get_errors(
            p.stderr.decode(pt.DEFAULT_ENCODING, "replace")))
    # stdout no Windows usa \r\n; o ficheiro do original usava \n.
    out = p.stdout.replace(b"\r\n", b"\n")
    return out if return_bytes else out.decode(pt.DEFAULT_ENCODING)


pytesseract.pytesseract.run_and_get_output = _tess_run_mem


def _ascii_tessdata(path):
    """Pasta tessdata que o Tesseract consegue abrir. Ele lê o caminho na
    codificação antiga do Windows: com a app em 'C:\\Users\\Игрок\\...'
    (num Windows que não é russo) dava 'Error opening data file' e o OCR
    não arrancava. 1) o nome curto 8.3 do Windows (só ASCII); 2) uma cópia
    em C:\\ProgramData\\RFTranslator\\tessdata."""
    if path.isascii() or os.name != "nt":
        return path
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024) \
                and buf.value.isascii():
            return buf.value
    except Exception:
        pass
    try:
        import shutil
        dst = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                           "RFTranslator", "tessdata")
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(path):
            src, out = os.path.join(path, f), os.path.join(dst, f)
            if f.endswith(".traineddata") and (
                    not os.path.isfile(out)
                    or os.path.getsize(out) != os.path.getsize(src)):
                shutil.copyfile(src, out)
        if dst.isascii():
            log().info(f"Tessdata copiado para caminho ASCII: {dst}")
            return dst
    except Exception:
        log().exception("Tessdata: cópia para caminho ASCII falhou")
    return path

try:
    import pyaudio
    PYAUDIO_OK = True
    PYAUDIO_ERR = ""
except Exception as e:
    pyaudio = None
    PYAUDIO_OK = False
    PYAUDIO_ERR = str(e)

try:
    import speech_recognition as sr
    SR_OK = PYAUDIO_OK
    SR_ERR = "" if SR_OK else "PyAudio missing"
except Exception as e:
    sr = None
    SR_OK = False
    SR_ERR = str(e)

try:
    from pynput.keyboard import (
        Controller, Key, Listener as KeyboardListener
    )
    PYNPUT_OK = True
except Exception as e:
    Controller = Key = KeyboardListener = None
    PYNPUT_OK = False

from PyQt6.QtCore import QObject, pyqtSignal


# ==================================================================
# CONSTANTES
# ==================================================================
OLLAMA_URL = "http://localhost:11434"
MAX_OVERLAY_LINES = 40
DEFAULT_VOICE_HOTKEY = "f11"
DEFAULT_LOCK_HOTKEY = "ctrl+shift+l"


# ==================================================================
# HOTKEY HELPERS
# ==================================================================
def key_to_string(key) -> str:
    """Converte Key do pynput em string (corrige Ctrl+letra → 0x01..0x1A)."""
    if key is None:
        return ""
    try:
        ch = getattr(key, "char", None)
        if ch and len(ch) == 1:
            code = ord(ch)
            if 0x01 <= code <= 0x1A:
                return chr(ord('a') + code - 1)
            return ch.lower()
    except Exception:
        pass
    try:
        vk = getattr(key, "vk", None)
        if vk is not None:
            if 0x30 <= vk <= 0x39:
                return chr(vk)
            if 0x41 <= vk <= 0x5A:
                return chr(vk).lower()
    except Exception:
        pass
    try:
        name = str(key).replace("Key.", "")
        if name.startswith("0x"):
            vk = getattr(getattr(key, "value", None), "vk", None)
            if vk is not None:
                return f"vk_{vk}"
        return name.lower()
    except Exception:
        return ""


def parse_hotkey(spec: str):
    if not spec or not isinstance(spec, str):
        return None
    parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
    if not parts:
        return None
    modifiers = {"ctrl", "shift", "alt", "win", "meta", "super", "control"}
    mods = {
        "ctrl": "ctrl" in parts or "control" in parts,
        "shift": "shift" in parts,
        "alt": "alt" in parts,
        "win": any(m in parts for m in ("win", "meta", "super")),
    }
    key_name = None
    for p in reversed(parts):
        if p not in modifiers:
            key_name = p
            break
    if not key_name:
        return None
    return {"key": key_name, "ctrl": mods["ctrl"], "shift": mods["shift"],
            "alt": mods["alt"], "win": mods["win"]}


def hotkey_matches(spec: dict, key, ctrl: bool, shift: bool,
                    alt: bool, win: bool = False) -> bool:
    if not spec:
        return False
    if bool(spec.get("ctrl")) != bool(ctrl):
        return False
    if bool(spec.get("shift")) != bool(shift):
        return False
    if bool(spec.get("alt")) != bool(alt):
        return False
    want = (spec.get("key") or "").lower()
    got = key_to_string(key)
    if not got:
        return False
    return got == want


# ==================================================================
# PALETA DE CORES
# ==================================================================
SPEAKER_COLORS = [
    "#60a5fa", "#34d399", "#f59e0b", "#f87171", "#a78bfa",
    "#f472b6", "#22d3ee", "#facc15", "#fb923c", "#4ade80",
]


def get_speaker_color(speaker: str) -> str:
    if not speaker:
        return SPEAKER_COLORS[0]
    s = speaker.strip().lower()
    h = sum(ord(c) * (i + 1) for i, c in enumerate(s)) % len(SPEAKER_COLORS)
    return SPEAKER_COLORS[h]


# ==================================================================
# ESTILO POR DEFEITO
# ==================================================================
DEFAULT_OVERLAY_STYLE = {
    "bg_color": "#000000",
    "bg_alpha": 180,
    "border_color": "#5d7fa8",
    "border_alpha": 180,
    "text_color": "#f3f4f6",
    "speaker_color_mode": "auto",
    "speaker_color_single": "#60a5fa",
    "font_family": "Arial",
    "font_size": 11,
    "font_bold": True,
    "show_separator": True,
    "separator_color": "#ffffff",
    "separator_alpha": 30,
    "line_spacing": 4,
    "show_timestamps": False,
    # Esconde o chat do overlay se ninguém falar durante X s (a barra de
    # cima fica sempre visível).
    "auto_hide": False,
    "auto_hide_secs": 20,
    # Tamanho da barra de cima em % (botões, separadores, indicador).
    "header_scale": 100,
    # O que o overlay mostra: 'all', 'bar' (só a barra de cima) ou 'chat'
    # (só as mensagens, sem a barra).
    "view_mode": "all",
    # O que disseste pela voz fica X s no chat aberto e depois só no
    # separador '🎤 Eu' (0 = só lá).
    "my_speech_secs": 20,
    # Com o cadeado, os cliques no chat vão para o jogo. Desligado: o chat
    # recebe o rato e dá para selecionar/copiar texto.
    "locked_click_through": True,
}


def merge_overlay_style(data):
    out = dict(DEFAULT_OVERLAY_STYLE)
    if isinstance(data, dict):
        for k, v in data.items():
            if k in out:
                out[k] = v
    return out


# ==================================================================
# PATH HELPERS
# ==================================================================
def _app_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_overlay_state_path() -> str:
    return os.path.join(_app_dir(), "overlay_state.json")


def get_last_config_path() -> str:
    return os.path.join(_app_dir(), "last_config.json")


def save_overlay_state(state: dict) -> bool:
    try:
        with open(get_overlay_state_path(), "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        log().debug("Overlay state guardado")
        return True
    except Exception:
        log().exception("Falha a guardar overlay state")
        return False


def load_overlay_state() -> dict:
    default = {
        "x": 100, "y": 100, "w": 620, "h": 210, "locked": False,
        "style": dict(DEFAULT_OVERLAY_STYLE),
    }
    try:
        path = get_overlay_state_path()
        if not os.path.isfile(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in default.items():
            if k == "style":
                continue
            data.setdefault(k, v)
        data["style"] = merge_overlay_style(data.get("style"))
        return data
    except Exception:
        log().exception("Falha a ler overlay state")
        return default


# ------------------------------------------------------------------
# Chaves das IAs cifradas no disco (DPAPI do Windows): só a tua conta do
# Windows, neste PC, as consegue ler — copiar o ficheiro não as revela.
# ------------------------------------------------------------------
_SECRET_PREFIX = "dpapi:"


class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(data: bytes, protect: bool) -> bytes:
    import ctypes.wintypes  # noqa: F401 (carrega windll.crypt32)
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(data, len(data))
    src = _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = _BLOB()
    fn = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    # CRYPTPROTECT_UI_FORBIDDEN = 0x1
    if not fn(ctypes.byref(src), None, None, None, None, 0x1,
              ctypes.byref(out)):
        raise OSError(ctypes.GetLastError(), "DPAPI falhou")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(out.pbData)


def encrypt_secret(text):
    if not text or os.name != "nt" or str(text).startswith(_SECRET_PREFIX):
        return text
    import base64
    try:
        return _SECRET_PREFIX + base64.b64encode(
            _dpapi(text.encode("utf-8"), True)).decode("ascii")
    except Exception:
        log().exception("Não consegui cifrar a chave — fica em texto")
        return text


def decrypt_secret(text):
    if not text or not str(text).startswith(_SECRET_PREFIX):
        return text or ""
    import base64
    try:
        return _dpapi(base64.b64decode(text[len(_SECRET_PREFIX):]),
                      False).decode("utf-8")
    except Exception:
        # Outro utilizador/PC: a chave não se consegue ler — tens de a
        # voltar a escrever (melhor isso que mandar lixo à IA).
        log().warning("Chave guardada ilegível (outro utilizador/PC?) — "
                      "escreve-a de novo")
        return ""


def config_to_disk(cfg):
    """asdict(cfg) com as chaves cifradas (last_config)."""
    data = asdict(cfg)
    data["api_key"] = encrypt_secret(data.get("api_key") or "")
    data["api_keys"] = {k: encrypt_secret(v)
                        for k, v in (data.get("api_keys") or {}).items() if v}
    return data


def save_last_config(cfg) -> bool:
    try:
        with open(get_last_config_path(), "w", encoding="utf-8") as f:
            json.dump(config_to_disk(cfg), f, indent=2, ensure_ascii=False)
        log().info(f"Last config guardada em {get_last_config_path()}")
        return True
    except Exception:
        log().exception("Falha a guardar last config")
        return False


def load_last_config():
    try:
        path = get_last_config_path()
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid = {k: v for k, v in data.items()
                 if k in AppConfig.__dataclass_fields__}
        valid.setdefault("my_name", "")
        valid.setdefault("appearance_style", {})
        return AppConfig(**migrate_config_dict(valid))
    except Exception:
        log().exception("Falha a ler last config")
        return None


# ==================================================================
# OLLAMA UNLOAD
# ==================================================================
def unload_ollama_model(model_name: str, timeout: float = 10.0) -> bool:
    if not model_name:
        return False
    try:
        log().info(f"A descarregar modelo Ollama: {model_name}")
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model_name, "prompt": "", "keep_alive": 0},
            timeout=timeout)
        if r.status_code == 200:
            log().info(f"Modelo {model_name} descarregado com sucesso")
            return True
        log().warning(f"Unload devolveu {r.status_code}")
        return False
    except Exception as e:
        log().warning(f"Falha a descarregar modelo: {e}")
        return False


def loaded_ollama_models():
    """Modelos que estão agora na memória do Ollama (/api/ps)."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/ps", timeout=5)
        r.raise_for_status()
        return [m.get("name") or m.get("model")
                for m in r.json().get("models", [])
                if m.get("name") or m.get("model")]
    except Exception:
        return []


def unload_other_ollama_models(keep) -> list:
    """Descarrega da VRAM todos os modelos menos os de `keep` (um nome ou
    vários: o do chat e o da voz, se forem diferentes). O jogo (e o resto
    do PC) também precisam de VRAM: o que não está em uso sai sempre —
    também quando mudas de modelo local, ou de local para a nuvem."""
    if isinstance(keep, str):
        keep = {keep}
    keep = {k for k in (keep or ()) if k}
    gone = []
    try:
        r = requests.get(f"{OLLAMA_URL}/api/ps", timeout=5)
        r.raise_for_status()
        for m in r.json().get("models", []):
            name = m.get("name") or m.get("model")
            if name and name not in keep and unload_ollama_model(name):
                gone.append(name)
    except Exception:
        log().debug("Falha a listar modelos carregados", exc_info=True)
    if gone:
        log().info(f"Modelos descarregados (ficam: "
                   f"{', '.join(sorted(keep)) or 'nenhum'}): {gone}")
    return gone


def unload_all_ollama_models() -> int:
    """Descarrega os modelos que estão na VRAM (/api/ps). Antes percorria
    todos os instalados, e o pedido para um modelo que não estava
    carregado carregava-o só para o descarregar a seguir."""
    return len(unload_other_ollama_models(keep=None))


# ==================================================================
# LOGGER
# ==================================================================
_LOG = None


class DetailedFormatter(logging.Formatter):
    def format(self, record):
        ct = self.converter(record.created)
        ts = time.strftime("%Y-%m-%d %H:%M:%S", ct) + \
             f".{int(record.msecs):03d}"
        th = record.threadName or "MainThread"
        loc = f"{record.filename}:{record.lineno}"
        fn = record.funcName
        lvl = record.levelname.ljust(7)
        msg = record.getMessage()
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return f"{ts} [{lvl}] [{th:<12}] [{loc} {fn}()] {msg}"


def get_error_log_path():
    return os.path.join(os.path.dirname(get_log_path()), "errors.log")


def setup_logger():
    global _LOG
    _LOG = logging.getLogger("RFTranslator")
    _LOG.setLevel(logging.DEBUG)
    if _LOG.handlers:
        return _LOG
    fmt = DetailedFormatter()
    try:
        fh = RotatingFileHandler(get_log_path(), maxBytes=10 * 1024 * 1024,
                                 backupCount=5, encoding="utf-8")
        fh.setLevel(logging.DEBUG); fh.setFormatter(fmt)
        _LOG.addHandler(fh)
        # Só avisos e erros, num ficheiro à parte (menu ⚠️ Erros).
        eh = RotatingFileHandler(get_error_log_path(), maxBytes=2 * 1024 * 1024,
                                 backupCount=3, encoding="utf-8")
        eh.setLevel(logging.WARNING); eh.setFormatter(fmt)
        _LOG.addHandler(eh)
    except Exception as e:
        print(f"[Logger] Não consegui criar ficheiro de log: {e}")
    try:
        if sys.stderr is None:
            raise RuntimeError("sem consola")  # pythonw / .exe: só ficheiros
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO); ch.setFormatter(fmt)
        _LOG.addHandler(ch)
    except Exception:
        pass
    return _LOG


def log():
    global _LOG
    if _LOG is None:
        _LOG = setup_logger()
    return _LOG


def log_env_summary():
    lg = log()
    lg.info("=" * 70)
    lg.info("RF Online Translator — resumo do ambiente")
    lg.info(f"Python       : {sys.version.split()[0]}")
    lg.info(f"Executable   : {sys.executable}")
    lg.info(f"CWD          : {os.getcwd()}")
    lg.info(f"App dir      : {_app_dir()}")
    lg.info(f"Log file     : {get_log_path()}")
    lg.info(f"Models dir   : {get_models_dir()}")
    lg.info(f"Profiles dir : {get_profiles_dir()}")
    lg.info(f"Tessdata dir : {get_app_tessdata_dir()}")
    lg.info(f"Overlay st.  : {get_overlay_state_path()}")
    lg.info(f"Last config  : {get_last_config_path()}")
    lg.info(f"OS           : {os.name} / {sys.platform}")
    lg.info(f"PyAudio      : {'OK' if PYAUDIO_OK else 'FALTA'}")
    lg.info(f"SpeechRecog  : {'OK' if SR_OK else 'FALTA'}")
    lg.info(f"pynput       : {'OK' if PYNPUT_OK else 'FALTA'}")
    lg.info("=" * 70)


# ==================================================================
# I18N
# ==================================================================
UI_LANGS = {
    "en": "English", "pt": "Português", "es": "Español",
    "fr": "Français", "de": "Deutsch", "ru": "Русский", "it": "Italiano",
}

STRINGS = {
    "app_title":       {"en": "RF Online Translator", "pt": "RF Online Tradutor"},
    "window_title":    {"en": "RF Online — Bidirectional Translator",
                        "pt": "RF Online — Tradutor Bidirecional"},
    "grp_language":    {"en": "Language", "pt": "Idioma"},
    "grp_ai":          {"en": "AI Engine", "pt": "Motor de IA"},
    "grp_gpu":         {"en": "GPU / Performance (Ollama)",
                        "pt": "GPU / Desempenho (Ollama)"},
    "grp_profiles":    {"en": "Profiles", "pt": "Perfis"},
    "grp_audio":       {"en": "Audio Devices", "pt": "Dispositivos de Áudio"},
    "grp_ocr":         {"en": "Chat Reading (OCR → Overlay)",
                        "pt": "Leitura do chat (OCR → Overlay)"},
    "grp_voice":       {"en": "Microphone (voice → type in game)",
                        "pt": "Microfone (voz → digitar no jogo)"},
    "grp_tts":         {"en": "Neural Voice (speak translations)",
                        "pt": "Voz Neural (ditar traduções)"},
    "grp_appearance":  {"en": "Overlay Appearance", "pt": "Aparência do Overlay"},
    "grp_myname":      {"en": "My character name", "pt": "Nome do meu personagem"},
    "lbl_provider":    {"en": "Cloud provider:", "pt": "Fornecedor nuvem:"},
    "lbl_mode":        {"en": "Mode:", "pt": "Modo:"},
    "lbl_model":       {"en": "Model:", "pt": "Modelo:"},
    "lbl_api_key":     {"en": "API Key:", "pt": "Chave da API:"},
    "lbl_get_key":     {"en": "Get key", "pt": "Obter chave"},
    "lbl_gpu_layers":  {"en": "GPU layers:", "pt": "Camadas GPU:"},
    "lbl_num_parallel":{"en": "Parallel requests:", "pt": "Pedidos paralelos:"},
    "lbl_keep_alive":  {"en": "Keep alive:", "pt": "Manter em memória:"},
    "lbl_mic":         {"en": "🎤 Microphone:", "pt": "🎤 Microfone:"},
    "lbl_out":         {"en": "🔊 Output (TTS):", "pt": "🔊 Saída (TTS):"},
    "lbl_ocr_src":     {"en": "Source language:", "pt": "Idioma de origem:"},
    "lbl_ocr_tgt":     {"en": "Translate to:", "pt": "Traduzir para:"},
    "lbl_voice_src":   {"en": "I speak:", "pt": "Eu falo em:"},
    "lbl_voice_tgt":   {"en": "Write in:", "pt": "Escrever em:"},
    "lbl_tts_voice":   {"en": "Voice:", "pt": "Voz:"},
    "lbl_font_size":   {"en": "Font size:", "pt": "Tamanho letra:"},
    "lbl_bg_alpha":    {"en": "Background opacity:", "pt": "Opacidade do fundo:"},
    "lbl_speaker_mode":{"en": "Speaker colors:", "pt": "Cores dos nomes:"},
    "lbl_text_color":  {"en": "Text color:", "pt": "Cor do texto:"},
    "lbl_voice_hotkey":{"en": "Voice hotkey:", "pt": "Tecla da voz:"},
    "lbl_my_name":     {"en": "My in-game name:", "pt": "Nome no jogo:"},
    "lbl_my_name_hint":{"en": "Messages from this name are ignored (yours).",
                        "pt": "Mensagens deste nome são ignoradas (as tuas)."},
    "btn_record_key":  {"en": "🎹 Record", "pt": "🎹 Gravar"},
    "sys_default":     {"en": "(System default)", "pt": "(Padrão do sistema)"},
    "mode_local":      {"en": "Local (Ollama)", "pt": "Local (Ollama)"},
    "mode_cloud":      {"en": "Cloud (API)", "pt": "Nuvem (API)"},
    "btn_start":       {"en": "▶  Start Translator", "pt": "▶  Iniciar Tradutor"},
    "btn_hf":          {"en": "🤗  Download models from Hugging Face",
                        "pt": "🤗  Descarregar modelos do Hugging Face"},
    "btn_lang_mgr":    {"en": "🌍  Manage language packs",
                        "pt": "🌍  Gerir pacotes de idiomas"},
    "btn_log":         {"en": "📄  View log", "pt": "📄  Ver log"},
    "btn_save_profile":{"en": "💾 Save", "pt": "💾 Guardar"},
    "btn_delete_profile":{"en": "🗑 Delete", "pt": "🗑 Apagar"},
    "btn_apply_profile":{"en": "✓ Apply", "pt": "✓ Aplicar"},
    "btn_search":      {"en": "🔍 Search / List", "pt": "🔍 Pesquisar / Listar"},
    "btn_download":    {"en": "⬇️ Download selected",
                        "pt": "⬇️ Descarregar selecionado"},
    "btn_create_local":{"en": "➕ Create from local GGUF",
                        "pt": "➕ Criar do GGUF local"},
    "btn_close":       {"en": "Close", "pt": "Fechar"},
    "btn_back":        {"en": "↩ Back", "pt": "↩ Voltar"},
    "btn_open_hf":     {"en": "Open HF", "pt": "Abrir HF"},
    "btn_clear_log":   {"en": "🗑 Clear", "pt": "🗑 Limpar"},
    "btn_reset_style": {"en": "↺ Reset style", "pt": "↺ Restaurar estilo"},
    "hf_title":        {"en": "🤗 Hugging Face", "pt": "🤗 Hugging Face"},
    "hf_search":       {"en": "🔍 Search:", "pt": "🔍 Pesquisa:"},
    "hf_search_ph":    {"en": "Type 'gemma' or 'gemma 3b' → all authors • 'user/repo' → that repo",
                        "pt": "Escreve 'gemma' ou 'gemma 3b' → todos os autores • 'user/repo' → esse repo"},
    "hf_token":        {"en": "Token:", "pt": "Token:"},
    "hf_token_ph":     {"en": "(optional) hf_xxx — https://huggingface.co/settings/tokens",
                        "pt": "(opcional) hf_xxx — https://huggingface.co/settings/tokens"},
    "hf_results":      {"en": "Results:", "pt": "Resultados:"},
    "hf_results_for":  {"en": "Results for '{q}':", "pt": "Resultados para '{q}':"},
    "hf_files_in":     {"en": "Files in '{r}':", "pt": "Ficheiros em '{r}':"},
    "hf_model_name":   {"en": "Model name:", "pt": "Nome do modelo:"},
    "hf_register":     {"en": "Register in Ollama automatically",
                        "pt": "Registar no Ollama automaticamente"},
    "hf_hint":         {"en": "💡 Type 'gemma' → all authors. 'user/repo' → that repo.",
                        "pt": "💡 Escreve 'gemma' → todos os autores. 'user/repo' → esse repo."},
    "log_title":       {"en": "📄 Log Viewer", "pt": "📄 Visualizador de Log"},
    "log_path":        {"en": "Log file: {p}", "pt": "Ficheiro: {p}"},
    "log_autoscroll":  {"en": "Auto-scroll", "pt": "Auto-scroll"},
    "profile_save":    {"en": "Save profile", "pt": "Guardar perfil"},
    "profile_name":    {"en": "Profile name:", "pt": "Nome do perfil:"},
    "profile_saved":   {"en": "Profile saved: {n}", "pt": "Perfil guardado: {n}"},
    "profile_deleted": {"en": "Profile deleted.", "pt": "Perfil apagado."},
    "profile_applied": {"en": "Profile applied: {n}", "pt": "Perfil aplicado: {n}"},
    "profile_confirm_delete": {"en": "Delete profile '{n}'?",
                        "pt": "Apagar perfil '{n}'?"},
    "info_help":       {"en": "Overlay: drag by the top, resize by the edges  •  🔒 locks it",
                        "pt": "Overlay: arrasta pelo topo, redimensiona pelas bordas  •  🔒 bloqueia"},
    "chk_tts":         {"en": "Read translations aloud", "pt": "Ler as traduções em voz alta"},
    "lbl_theme":       {"en": "Theme:", "pt": "Tema:"},
    "lbl_voice_mode":  {"en": "Mode:", "pt": "Modo:"},
    "lbl_voice_ai":    {"en": "Voice AI:", "pt": "IA da voz:"},
    "voice_ai_same":   {"en": "Same as chat", "pt": "A mesma do chat"},
    "btn_test_key":    {"en": "Test", "pt": "Testar"},
    "lbl_custom_url":  {"en": "Server URL:", "pt": "URL do servidor:"},
    "chk_fallback":    {"en": "If this AI fails, try the others that have a key",
                        "pt": "Se esta IA falhar, usar as outras que têm chave"},
    "key_hint":        {"en": "Each AI keeps its own key.",
                        "pt": "Cada IA guarda a sua própria chave."},
    "btn_mic_test":    {"en": "🎤 Test", "pt": "🎤 Testar"},
    "vm_hold":         {"en": "Push-to-talk: records while you hold the key",
                        "pt": "Push-to-talk: grava enquanto manténs a tecla"},
    "vm_auto":         {"en": "Tap: listens until a long pause",
                        "pt": "Toque: ouve até uma pausa longa"},
    "vm_continuous":   {"en": "Continuous: tap = on, tap again = off",
                        "pt": "Contínuo: toque liga, outro toque desliga"},
    "theme_dark":      {"en": "🌙 Dark", "pt": "🌙 Escuro"},
    "theme_light":     {"en": "☀️ Light", "pt": "☀️ Claro"},
    "theme_system":    {"en": "🖥 Same as Windows", "pt": "🖥 Igual ao Windows"},
    "status_tess_ok":  {"en": "✅ Tesseract OK", "pt": "✅ Tesseract OK"},
    "status_tess_miss":{"en": "⚠️ Tesseract missing", "pt": "⚠️ Tesseract ausente"},
    "status_audio_ok": {"en": "✅ Audio (voice hotkey)", "pt": "✅ Áudio (tecla voz)"},
    "status_audio_no": {"en": "⚠️ Audio disabled", "pt": "⚠️ Áudio desativado"},
    "status_kb_ok":    {"en": "✅ Keyboard (pynput)", "pt": "✅ Teclado (pynput)"},
    "status_kb_no":    {"en": "⚠️ Keyboard disabled", "pt": "⚠️ Teclado desativado"},
    "ollama_online":   {"en": "🟢 Ollama online — {n} model(s)",
                        "pt": "🟢 Ollama online — {n} modelo(s)"},
    "ollama_nomodel":  {"en": "🟡 Ollama online, no models. Use 🤗 or: ollama pull gemma2:2b",
                        "pt": "🟡 Ollama online, sem modelos. Usa 🤗 ou: ollama pull gemma2:2b"},
    "ollama_offline":  {"en": "🔴 Ollama offline — run run.bat",
                        "pt": "🔴 Ollama offline — corre run.bat"},
    "no_model_item":   {"en": "⚠️ No model installed", "pt": "⚠️ Nenhum modelo instalado"},
    "offline_item":    {"en": "❌ Ollama offline — start run.bat",
                        "pt": "❌ Ollama offline — arranca run.bat"},
    "warn":            {"en": "Warning", "pt": "Aviso"},
    "err":             {"en": "Error", "pt": "Erro"},
    "info":            {"en": "Info", "pt": "Informação"},
    "ov_config":       {"en": "⚙  Settings", "pt": "⚙  Configurações"},
    "ov_tts":          {"en": "🔊  Toggle voice", "pt": "🔊  Ativar/Desativar voz"},
    "ov_lang":         {"en": "🌍  Language packs", "pt": "🌍  Gestor de idiomas"},
    "ov_hf":           {"en": "🤗  Download models (HF)", "pt": "🤗  Descarregar modelos (HF)"},
    "ov_clear":        {"en": "🧹  Clear overlay", "pt": "🧹  Limpar overlay"},
    "ov_quit":         {"en": "❌  Quit", "pt": "❌  Sair"},
    "ov_log":          {"en": "📄  View log", "pt": "📄  Ver log"},
    "ov_config_short": {"en": "⚙  Back to Settings", "pt": "⚙  Voltar às Configurações"},
    "ov_lock_on":      {"en": "🔒  Lock (drag disabled)",
                        "pt": "🔒  Bloquear (sem arrasto)"},
    "ov_lock_off":     {"en": "🔓  Unlock (draggable)",
                        "pt": "🔓  Desbloquear (arrastável)"},
    "ov_header_title": {"en": "🎮  RF Translator", "pt": "🎮  RF Tradutor"},
    "capture_title":   {"en": "Record hotkey", "pt": "Gravar tecla"},
    "capture_hint":    {"en": "Press the key or combination you want...",
                        "pt": "Pressiona a tecla ou combinação desejada..."},
    "capture_current": {"en": "Current: {h}", "pt": "Atual: {h}"},
    "capture_ok":      {"en": "OK", "pt": "OK"},
    "capture_cancel":  {"en": "Cancel", "pt": "Cancelar"},
}

_UI_STATE = {"lang": "en", "theme": "dark",
             "close_overlay": "config", "close_main": "quit"}

# O que faz o ✕ de cada janela (escolhe-se nas Definições).
# Overlay (modo chat): voltar à janela principal ou fechar a app.
# Janela principal: fechar a app ou ficar no ícone junto ao relógio.
CLOSE_CHOICES = {"close_overlay": ("config", "quit"),
                 "close_main": ("quit", "tray")}


# Traduções das 7 línguas da interface (i18n.py): textos completos de
# tr(chave) e frases T("texto em inglês").
try:
    from i18n import PHRASES, STRINGS_I18N, LANG_NAMES
except Exception as _e:     # sem o ficheiro: fica tudo em inglês
    print(f"[core] i18n indisponível: {_e}")
    PHRASES, STRINGS_I18N, LANG_NAMES = {}, {}, {}
for _k, _v in STRINGS_I18N.items():
    STRINGS.setdefault(_k, {}).update(_v)


def T(text, **fmt):
    """Frase da interface na língua escolhida. O texto-fonte é o inglês;
    as outras línguas vêm de i18n.PHRASES."""
    lang = _UI_STATE.get("lang", "en")
    s = text if lang == "en" else (PHRASES.get(text, {}).get(lang) or text)
    if fmt:
        try:
            s = s.format(**fmt)
        except Exception:
            pass
    return s


def lang_label(key):
    """Nome de uma língua (chave de LANGUAGES) na língua da interface."""
    lang = _UI_STATE.get("lang", "en")
    return (LANG_NAMES.get(key) or {}).get(lang) or key


def tr(key, **fmt):
    entry = STRINGS.get(key, {})
    lang = _UI_STATE.get("lang", "en")
    s = entry.get(lang) or entry.get("en") or key
    if fmt:
        try:
            s = s.format(**fmt)
        except Exception:
            pass
    return s


def _prefs_path():
    return os.path.join(_app_dir(), "ui_prefs.json")


def load_ui_prefs():
    try:
        with open(_prefs_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        lang = data.get("lang", "en")
        if lang in UI_LANGS:
            _UI_STATE["lang"] = lang
        if data.get("theme") in UI_THEMES:
            _UI_STATE["theme"] = data["theme"]
        for key, choices in CLOSE_CHOICES.items():
            if data.get(key) in choices:
                _UI_STATE[key] = data[key]
    except Exception:
        pass


def save_ui_prefs():
    try:
        with open(_prefs_path(), "w", encoding="utf-8") as f:
            json.dump({k: _UI_STATE[k] for k in
                       ("lang", "theme", *CLOSE_CHOICES)}, f, indent=2)
    except Exception:
        pass


# Tema das janelas da app: 'dark', 'light' ou 'system' (o do Windows).
UI_THEMES = ("dark", "light", "system")


def get_ui_theme():
    return _UI_STATE.get("theme", "dark")


def set_ui_theme(theme):
    if theme in UI_THEMES:
        _UI_STATE["theme"] = theme
        save_ui_prefs()


def set_ui_lang(lang):
    if lang in UI_LANGS:
        _UI_STATE["lang"] = lang
        save_ui_prefs()


def get_ui_lang():
    return _UI_STATE["lang"]


def get_close_action(which):
    """'close_overlay' ou 'close_main' → a escolha guardada."""
    return _UI_STATE.get(which, CLOSE_CHOICES[which][0])


def set_close_action(which, action):
    if action in CLOSE_CHOICES.get(which, ()):
        _UI_STATE[which] = action
        save_ui_prefs()


# ==================================================================
# IDIOMAS / VOZES
# ==================================================================
LANGUAGES = {
    "Auto (detectar)":       {"stt": None,    "tess": None,      "tts": "en"},
    "English":               {"stt": "en-US", "tess": "eng",     "tts": "en"},
    "Portuguese (PT)":       {"stt": "pt-PT", "tess": "por",     "tts": "pt"},
    "Portuguese (BR)":       {"stt": "pt-BR", "tess": "por",     "tts": "pt"},
    "Russian":               {"stt": "ru-RU", "tess": "rus",     "tts": "ru"},
    "Spanish":               {"stt": "es-ES", "tess": "spa",     "tts": "es"},
    "French":                {"stt": "fr-FR", "tess": "fra",     "tts": "fr"},
    "German":                {"stt": "de-DE", "tess": "deu",     "tts": "de"},
    "Italian":               {"stt": "it-IT", "tess": "ita",     "tts": "it"},
    "Korean":                {"stt": "ko-KR", "tess": "kor",     "tts": "ko"},
    "Japanese":              {"stt": "ja-JP", "tess": "jpn",     "tts": "ja"},
    "Chinese (Simplified)":  {"stt": "zh-CN", "tess": "chi_sim", "tts": "zh"},
    "Turkish":               {"stt": "tr-TR", "tess": "tur",     "tts": "tr"},
    "Polish":                {"stt": "pl-PL", "tess": "pol",     "tts": "pl"},
}

TTS_VOICES_BY_LANG = {
    "en": [("Aria (US, F)", "en-US-AriaNeural"),
           ("Jenny (US, F)", "en-US-JennyNeural"),
           ("Guy (US, M)", "en-US-GuyNeural"),
           ("Sonia (UK, F)", "en-GB-SoniaNeural"),
           ("Ryan (UK, M)", "en-GB-RyanNeural"),
           ("Natasha (AU, F)", "en-AU-NatashaNeural")],
    "pt": [("Raquel (PT, F)", "pt-PT-RaquelNeural"),
           ("Duarte (PT, M)", "pt-PT-DuarteNeural"),
           ("Francisca (BR, F)", "pt-BR-FranciscaNeural"),
           ("António (BR, M)", "pt-BR-AntonioNeural")],
    "ru": [("Svetlana (F)", "ru-RU-SvetlanaNeural"),
           ("Dmitry (M)", "ru-RU-DmitryNeural")],
    "es": [("Elvira (ES, F)", "es-ES-ElviraNeural"),
           ("Álvaro (ES, M)", "es-ES-AlvaroNeural"),
           ("Dalia (MX, F)", "es-MX-DaliaNeural"),
           ("Jorge (MX, M)", "es-MX-JorgeNeural")],
    "fr": [("Denise (FR, F)", "fr-FR-DeniseNeural"),
           ("Henri (FR, M)", "fr-FR-HenriNeural"),
           ("Sylvie (CA, F)", "fr-CA-SylvieNeural")],
    "de": [("Katja (F)", "de-DE-KatjaNeural"),
           ("Conrad (M)", "de-DE-ConradNeural")],
    "it": [("Elsa (F)", "it-IT-ElsaNeural"),
           ("Diego (M)", "it-IT-DiegoNeural")],
    "ko": [("Sun-Hi (F)", "ko-KR-SunHiNeural"),
           ("InJoon (M)", "ko-KR-InJoonNeural")],
    "ja": [("Nanami (F)", "ja-JP-NanamiNeural"),
           ("Keita (M)", "ja-JP-KeitaNeural")],
    "zh": [("Xiaoxiao (F)", "zh-CN-XiaoxiaoNeural"),
           ("Yunxi (M)", "zh-CN-YunxiNeural")],
    "tr": [("Emel (F)", "tr-TR-EmelNeural"),
           ("Ahmet (M)", "tr-TR-AhmetNeural")],
    "pl": [("Zofia (F)", "pl-PL-ZofiaNeural"),
           ("Marek (M)", "pl-PL-MarekNeural")],
}

CLOUD_MODELS_FALLBACK = ["deepseek-chat", "gpt-4.1-mini"]
HF_SUGGESTIONS = [
    ("bartowski/Qwen2.5-7B-Instruct-GGUF", "Qwen 2.5 7B Instruct"),
    ("bartowski/Qwen2.5-14B-Instruct-GGUF", "Qwen 2.5 14B Instruct"),
    ("bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", "Llama 3.1 8B Instruct"),
    ("bartowski/gemma-2-9b-it-GGUF", "Gemma 2 9B"),
    ("bartowski/Phi-3.5-mini-instruct-GGUF", "Phi 3.5 mini"),
    ("QuantFactory/DeepSeek-R1-Distill-Qwen-7B-GGUF", "DeepSeek R1 Distill 7B"),
    ("TheBloke/Mistral-7B-Instruct-v0.2-GGUF", "Mistral 7B Instruct"),
]


# ==================================================================
# ÁUDIO
# ==================================================================
# Ordem de preferência ao recuperar um micro. WDM-KS fica de fora: é
# exclusivo e falha ('Unanticipated host error') se outra app usa o micro.
# DirectSound por último: com o USB Mic devolvia um sinal congelado (o
# mesmo valor sempre) em vez de áudio.
_MIC_API_PREF = ("MME", "Windows WASAPI", "Windows DirectSound")


def _mic_base_name(name):
    # O Windows renomeia ao religar: 'Microfone (2- USB Mic)' == 'USB Mic'.
    return re.sub(r"\b\d+-\s*", "", (name or "").lower()).strip()


def _mic_opens(pa, index):
    """Abre e fecha o micro com os parâmetros do speech_recognition."""
    try:
        info = pa.get_device_info_by_index(index)
        st = pa.open(format=pyaudio.paInt16, channels=1,
                     rate=int(info["defaultSampleRate"]), input=True,
                     input_device_index=index, frames_per_buffer=1024)
        st.read(256, exception_on_overflow=False)
        st.close()
        return True
    except Exception:
        return False


def mic_index_by_name(name):
    """Índice atual do micro com este nome da lista ('MME: Microfone
    (2- USB Mic)'), ou None. Tolera o '2-'/'3-' que o Windows acrescenta
    ao religar."""
    if not name:
        return None
    devs = list_input_devices()
    for i, n in devs:
        if n == name:
            return i
    api, _, base = name.partition(": ")
    want = _mic_base_name(base)
    for i, n in devs:
        a, _, b = n.partition(": ")
        if a == api and _mic_base_name(b) == want:
            return i
    return None


def resolve_mic(index, name=""):
    """(índice que abre, descrição). Primeiro pelo nome guardado (os
    índices mudam ao religar USB); depois o índice; se falhar, o mesmo
    micro por outro driver; por fim o micro padrão do Windows."""
    if not PYAUDIO_OK:
        return index, "?"
    by_name = mic_index_by_name(name)
    if by_name is not None:
        if by_name != index:
            log().info(f"Micro '{name}' agora é o índice {by_name} "
                       f"(era {index})")
        index = by_name
    pa = pyaudio.PyAudio()
    try:
        def desc(i):
            d = pa.get_device_info_by_index(i)
            api = pa.get_host_api_info_by_index(d["hostApi"])["name"]
            return f"{d['name']} ({api})"
        n = pa.get_device_count()
        if index is not None and 0 <= index < n and _mic_opens(pa, index):
            return index, desc(index)
        want = None
        if index is not None and 0 <= index < n:
            want = _mic_base_name(pa.get_device_info_by_index(index)["name"])
        cands = []
        for i in range(n):
            d = pa.get_device_info_by_index(i)
            if d.get("maxInputChannels", 0) <= 0:
                continue
            api = pa.get_host_api_info_by_index(d["hostApi"])["name"]
            if api not in _MIC_API_PREF:
                continue
            if want and _mic_base_name(d["name"]) == want:
                cands.append((_MIC_API_PREF.index(api), i))
        for _, i in sorted(cands):
            if _mic_opens(pa, i):
                log().info(f"Micro {index} não abre — a usar {i}: {desc(i)}")
                return i, desc(i)
        try:
            i = pa.get_default_input_device_info()["index"]
            log().info(f"Micro {index} não abre — a usar o padrão {i}")
            return i, desc(i)
        except Exception:
            return None, "padrão"
    finally:
        pa.terminate()


def list_input_devices():
    if not PYAUDIO_OK:
        return []
    devices = []
    try:
        p = pyaudio.PyAudio()
        try:
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info.get("maxInputChannels", 0) <= 0:
                        continue
                    api = p.get_host_api_info_by_index(
                        info["hostApi"])["name"]
                    # WDM-KS é exclusivo e falha; DirectSound devolvia
                    # sinal em loop/congelado com o USB Mic. MME e WASAPI
                    # mostram os mesmos dispositivos.
                    if api in ("Windows WDM-KS", "Windows DirectSound"):
                        continue
                    short = {"Windows DirectSound": "DirectSound",
                             "Windows WASAPI": "WASAPI"}.get(api, api)
                    devices.append(
                        (i, f"{short}: {info.get('name', f'Device {i}')}"))
                except Exception:
                    continue
        finally:
            p.terminate()
    except Exception:
        log().exception("list_input_devices falhou")
        return []
    devices.sort(key=lambda d: (0 if "default" in d[1].lower() else 1,
                                d[1].lower()))
    return devices


def list_output_devices():
    try:
        from pygame._sdl2 import audio as sdl_audio
        names = sdl_audio.get_audio_device_names(False)
        names = [n for n in names if n]
        names.sort(key=lambda n: (0 if "default" in n.lower() else 1,
                                  n.lower()))
        return names
    except Exception:
        log().warning("Não consegui listar saídas (pygame._sdl2)")
        return []


# ==================================================================
# PROMPTS
# ==================================================================
def build_ocr_prompt(src, tgt):
    # Num chat internacional cada linha pode vir numa língua diferente.
    src_note = ("Players write in different languages: detect the "
                "language of EACH line separately"
                if src.startswith("Auto")
                else f"Most lines are in {src}, but players may also write "
                     "in other languages: detect each line separately")
    return (
        f"This is MMORPG guild chat. {src_note}.\n"
        "Each chat line starts with a speaker name in brackets, "
        "e.g. '[Player] hello there'.\n"
        f"Translate each line into {tgt}, KEEPING the speaker name in brackets.\n"
        "Format your output EXACTLY as one message per line:\n"
        "  [Speaker] translated message\n"
        "Rules:\n"
        "- Keep game slang as-is (CC, MA, Chip War, WTB, WTS, afk, gank, wtb).\n"
        "- Do NOT translate the speaker names.\n"
        "- Keep numbers and amounts exactly as written (30kk, 1300, +5, "
        "21:00).\n"
        "- Text inside brackets in the message body is an item or place "
        "name (e.g. [Kallon Catalyst], [Central Tower]): keep it unchanged.\n"
        f"- If a line is already in {tgt}, copy it unchanged.\n"
        "- Skip any line that is just numbers, timestamps or random letters.\n"
        "- Never invent content that is not in the input.\n"
        "- No explanations, no quotes, no extra text.\n"
        "Output only the translated lines."
    )


# ==================================================================
# OCR: LÍNGUA + PRÉ-PROCESSAMENTO
# ==================================================================
_LATIN_TESS = {"eng", "por", "spa", "fra", "deu", "ita", "tur", "pol"}


def resolve_tess_lang(src):
    """Línguas Tesseract para a origem escolhida.

    Nomes de jogadores são quase sempre latinos, por isso 'eng' entra
    sempre. Em Auto usa eng+rus (o chat do RF mistura EN e RU) — sem
    isto o texto cirílico sai como lixo ('Bce npuBeT').
    """
    code = LANGUAGES.get(src, {}).get("tess")
    if code:
        langs = [code] + ([] if code == "eng" else ["eng"])
    else:
        # Auto: eng+rus + pacotes instalados de OUTROS alfabetos (instalar
        # 'kor' no gestor de tessdata = Auto passa a ler coreano). Línguas
        # latinas (por, spa, deu...) ficam de fora: o 'eng' já as lê (só
        # perde acentos, a IA entende na mesma) e cada pacote extra deixa o
        # OCR ~50% mais lento e piora o russo ('не' → 'He').
        langs = ["eng", "rus"]
        for info in LANGUAGES.values():
            t = info.get("tess")
            if t and t not in langs and t not in _LATIN_TESS:
                langs.append(t)
    ok = [l for l in langs if is_tessdata_installed(l)]
    return "+".join(ok) if ok else None


# Altura do painel do chat a 2560x1440 (onde os filtros foram afinados).
_CHAT_H_REF = 1190


def preprocess_chat_image(img, scale=None):
    """Isola o texto do chat antes do OCR.

    O texto do chat é claro ou colorido (guild = verde-amarelo, nomes
    brancos, whisper = roxo); o 'N min ago' e o ícone 🌐 são cinzento
    neutro. Mantém píxeis brilhantes OU saturados, descarta o cinzento,
    e uma abertura morfológica apaga os contornos finos que sobram.
    Devolve texto preto em fundo branco, ampliado `scale`x.

    Sem `scale`, amplia para a letra ficar sempre do tamanho que tem a
    2560x1440 ×2 (onde os filtros foram afinados): a 1920x1080 a letra é
    3/4 e o OCR lia 2 de 24 mensagens; a 4K é maior. Escala pela altura,
    como a UI do jogo.
    """
    im = img.convert("RGB")
    if scale is None:
        scale = 2.0 * _CHAT_H_REF / max(1, im.height)
    im = im.resize((max(1, round(im.width * scale)),
                    max(1, round(im.height * scale))), Image.LANCZOS)
    if scale >= 3.9:
        # Ecrãs ~720p: a letra ampliada ~4x fica desfocada e perde o
        # brilho que o filtro procura. Nitidez: 720p 58% → 78% das
        # mensagens; a 768p-1080p não ajudava ou piorava, por isso só aqui.
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120,
                                               threshold=2))
    r, g, b = im.split()
    mx = ImageChops.lighter(r, ImageChops.lighter(g, b))
    mn = ImageChops.darker(r, ImageChops.darker(g, b))
    m_bright = mx.point(lambda v: 255 if v >= 185 else 0)
    m_sat = ImageChops.multiply(
        ImageChops.subtract(mx, mn).point(lambda v: 255 if v >= 50 else 0),
        mx.point(lambda v: 255 if v >= 140 else 0))
    mask = ImageChops.lighter(m_bright, m_sat)
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    ink = mask.histogram()[255] / float(mask.width * mask.height or 1)
    if ink < 0.002:
        # Cores inesperadas (outro tema/canal): fallback para cinzento.
        gray = ImageOps.autocontrast(im.convert("L"), cutoff=1)
        return ImageOps.invert(gray)
    return ImageChops.invert(mask)


# ==================================================================
# JANELA DO JOGO
# ==================================================================
GAME_EXE_HINTS = ("projectrf",)          # ProjectRF-Win64-Shipping.exe
GAME_TITLE_EXACT = ("rf online next",)
# Painel de mensagens do chat (aberto), em fracções da ALTURA da área
# cliente: x1, y1, x2, y2. Medido a 2560x1440: x 140→762, y 90→1280 —
# exclui a coluna de tabs (All/World/Guild...), o cabeçalho 'CHAT' e a
# barra de ícones + caixa de texto em baixo.
CHAT_REGION_REL = (140 / 1440, 90 / 1440, 762 / 1440, 1280 / 1440)
# Zona do chat marcada à mão (⚙ Configurações → 🎯 Calibrar a zona do
# chat), na mesma escala (fracções da ALTURA da área cliente; o x também,
# porque a UI escala pela altura e fica encostada à esquerda). None = a
# automática. Para chats maiores/menores ou UI noutra escala.
_CHAT_CALIB = {"rect": None}


def set_chat_calibration(rect):
    """rect = (x1, y1, x2, y2) em fracções da altura, ou None."""
    try:
        r = tuple(float(v) for v in rect) if rect else None
    except (TypeError, ValueError):
        r = None
    if r and (len(r) != 4 or r[2] - r[0] < 0.05 or r[3] - r[1] < 0.05
              or min(r) < 0 or r[3] > 1.0):
        r = None
    _CHAT_CALIB["rect"] = r
    return r


def apply_chat_calibration(cfg):
    """Usa a zona calibrada da config (se existir e estiver ligada)."""
    return set_chat_calibration(
        getattr(cfg, "chat_region", None)
        if getattr(cfg, "chat_region_on", True) else None)


def chat_calibration():
    return _CHAT_CALIB["rect"]


def chat_region_rel():
    return _CHAT_CALIB["rect"] or CHAT_REGION_REL
# Caixa da mensagem, mesma escala. x=600: dentro da caixa no Guild (que
# começa em x≈150) e no Whisper (aí há antes o campo do destinatário,
# x≈160-300, e a mensagem só começa em x≈415); antes do botão ▲ (x≈720).
CHAT_INPUT_REL = (600 / 1440, 1395 / 1440)
# Separadores da coluna da esquerda: centro y (a 1440 de altura).
CHAT_TABS_Y = {"all": 124, "world": 198, "server": 276, "party": 351,
               "guild": 427, "raid": 503, "whisper": 580, "channel": 655,
               "system": 731}
CHAT_TAB_X = 65
# Para o 'reply': separador Whisper e o campo do destinatário da barra de
# baixo no Whisper (x≈160-300).
CHAT_TAB_WHISPER_REL = (CHAT_TAB_X / 1440, CHAT_TABS_Y["whisper"] / 1440)
CHAT_RECIPIENT_REL = (230 / 1440, 1395 / 1440)


class GameWindow:
    """Encontra a janela do RF e captura-a directamente.

    Captura só a janela do jogo (PrintWindow + PW_RENDERFULLCONTENT): com
    alt-tab para o browser o OCR continua a ver o chat do jogo e nunca o
    Google. Não toca na memória do jogo — é a mesma API que as
    ferramentas de screenshot usam. Procura pelo executável, não pelo
    título: 'RF Online' também aparece no título desta app e em
    separadores do browser.
    """
    PW_CLIENTONLY = 0x1
    PW_RENDERFULLCONTENT = 0x2

    def __init__(self):
        self.hwnd = None
        self._last_lookup = 0.0
        self._ok = os.name == "nt"
        if not self._ok:
            return
        from ctypes import wintypes
        u32 = ctypes.windll.user32
        g32 = ctypes.windll.gdi32
        k32 = ctypes.windll.kernel32
        H = wintypes.HANDLE
        u32.GetForegroundWindow.restype = wintypes.HWND
        u32.IsWindow.argtypes = [wintypes.HWND]
        u32.IsIconic.argtypes = [wintypes.HWND]
        u32.IsWindowVisible.argtypes = [wintypes.HWND]
        u32.GetClientRect.argtypes = [wintypes.HWND,
                                      ctypes.POINTER(wintypes.RECT)]
        u32.ClientToScreen.argtypes = [wintypes.HWND,
                                       ctypes.POINTER(wintypes.POINT)]
        u32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        u32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        u32.GetAsyncKeyState.restype = ctypes.c_short
        u32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR,
                                       ctypes.c_int]
        u32.GetDC.argtypes = [wintypes.HWND]
        u32.GetDC.restype = wintypes.HDC
        u32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        u32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC,
                                    wintypes.UINT]
        g32.CreateCompatibleDC.argtypes = [wintypes.HDC]
        g32.CreateCompatibleDC.restype = wintypes.HDC
        g32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int,
                                               ctypes.c_int]
        g32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        g32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        g32.SelectObject.restype = wintypes.HGDIOBJ
        g32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        g32.DeleteDC.argtypes = [wintypes.HDC]
        g32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP,
                                  wintypes.UINT, wintypes.UINT,
                                  ctypes.c_void_p, ctypes.c_void_p,
                                  wintypes.UINT]
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                    wintypes.DWORD]
        k32.OpenProcess.restype = H
        k32.QueryFullProcessImageNameW.argtypes = [
            H, wintypes.DWORD, wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD)]
        k32.CloseHandle.argtypes = [H]
        self._u32, self._g32, self._k32, self._wt = u32, g32, k32, wintypes
        self._enum_proto = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    # ---------- procurar ----------
    def _pid_of(self, hwnd):
        pid = self._wt.DWORD()
        self._u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    def _exe_of(self, pid):
        h = self._k32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFO
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(520)
            n = self._wt.DWORD(520)
            if self._k32.QueryFullProcessImageNameW(h, 0, buf,
                                                    ctypes.byref(n)):
                return os.path.basename(buf.value).lower()
            return ""
        finally:
            self._k32.CloseHandle(h)

    def _title_of(self, hwnd):
        buf = ctypes.create_unicode_buffer(256)
        self._u32.GetWindowTextW(hwnd, buf, 256)
        return buf.value

    def find(self):
        """hwnd da janela do jogo (cache; procura no máx. a cada 2s)."""
        if not self._ok:
            return None
        if self.hwnd and self._u32.IsWindow(self.hwnd):
            return self.hwnd
        self.hwnd = None
        now = time.time()
        if now - self._last_lookup < 2.0:
            return None
        self._last_lookup = now
        own_pid = os.getpid()
        found = []

        def cb(hwnd, _):
            if not self._u32.IsWindowVisible(hwnd):
                return True
            pid = self._pid_of(hwnd)
            if pid == own_pid:
                return True
            exe = self._exe_of(pid)
            title = self._title_of(hwnd).strip().lower()
            if any(h in exe for h in GAME_EXE_HINTS) \
                    or title in GAME_TITLE_EXACT:
                found.append(hwnd)
                return False
            return True

        self._u32.EnumWindows(self._enum_proto(cb), 0)
        if found:
            self.hwnd = found[0]
            log().info(f"Janela do jogo encontrada: hwnd={self.hwnd} "
                       f"'{self._title_of(self.hwnd)}'")
        return self.hwnd

    # ---------- estado ----------
    def modifiers_down(self):
        """Ctrl/Shift/Alt ainda carregados (do atalho da voz)."""
        if not self._ok:
            return False
        return any(self._u32.GetAsyncKeyState(vk) & 0x8000
                   for vk in (0x11, 0x10, 0x12))   # CTRL, SHIFT, ALT

    def is_minimized(self):
        h = self.find()
        return bool(h) and bool(self._u32.IsIconic(h))

    def is_foreground(self):
        h = self.find()
        return bool(h) and self._u32.GetForegroundWindow() == h

    def client_rect(self):
        """(x, y, largura, altura) da área cliente do jogo no ecrã, em
        píxeis físicos, ou None (fechado/minimizado)."""
        h = self.find()
        if not h or self._u32.IsIconic(h):
            return None
        r = self._wt.RECT()
        if not self._u32.GetClientRect(h, ctypes.byref(r)):
            return None
        pt = self._wt.POINT(0, 0)
        self._u32.ClientToScreen(h, ctypes.byref(pt))
        if r.right <= 0 or r.bottom <= 0:
            return None
        return pt.x, pt.y, r.right, r.bottom

    def click_chat_input(self):
        """Clica na caixa de texto do chat e devolve o rato ao sítio.
        False se o jogo não estiver em primeiro plano."""
        return self.click_rel(*CHAT_INPUT_REL)

    def click_rel(self, rel_x, rel_y):
        """Clica num ponto da UI do jogo (fracções da altura da área
        cliente, como CHAT_REGION_REL) e devolve o rato ao sítio."""
        h = self.find()
        if not h or not self.is_foreground():
            return False
        r = self._wt.RECT()
        if not self._u32.GetClientRect(h, ctypes.byref(r)):
            return False
        pt = self._wt.POINT(0, 0)
        self._u32.ClientToScreen(h, ctypes.byref(pt))
        ch = r.bottom - r.top
        x = pt.x + int(rel_x * ch)
        y = pt.y + int(rel_y * ch)
        old = self._wt.POINT()
        self._u32.GetCursorPos(ctypes.byref(old))
        # A UI do jogo (Unreal) só aceita o clique se o rato já estiver
        # 'pousado' no botão: sem isto os cliques nos separadores do chat
        # perdiam-se ou eram processados fora de ordem.
        self._u32.SetCursorPos(x, y)
        self._u32.mouse_event(0x0001, 1, 0, 0, 0)    # MOVE (hover)
        self._u32.mouse_event(0x0001, -1, 0, 0, 0)
        time.sleep(0.15)
        self._u32.mouse_event(0x0002, 0, 0, 0, 0)    # LEFTDOWN
        time.sleep(random.uniform(0.07, 0.11))
        self._u32.mouse_event(0x0004, 0, 0, 0, 0)    # LEFTUP
        time.sleep(0.12)
        self._u32.SetCursorPos(old.x, old.y)
        return True

    @staticmethod
    def active_tab(img):
        """Separador do chat ativo no jogo ('guild', 'whisper'...), ou
        None (chat fechado). O ativo tem fundo mais claro e texto branco:
        nas capturas ganhou sempre por 20-36 pontos de brilho."""
        if img is None:
            return None
        g = img.convert("L")
        s = g.size[1] / 1440
        scores = {}
        for name, y in CHAT_TABS_Y.items():
            box = (int(4 * s), int((y - 28) * s), int(132 * s),
                   int((y + 28) * s))
            scores[name] = ImageStat.Stat(g.crop(box)).mean[0]
        ranked = sorted(scores, key=scores.get, reverse=True)
        if scores[ranked[0]] - scores[ranked[1]] < 10:
            return None
        return ranked[0]

    @staticmethod
    def chat_panel_open(img, partner=None):
        """O painel do chat do jogo está aberto? Vê-se pela barra de
        escrever em baixo: aberto tem o nome do canal e 'Please enter a
        message'; fechado, nesse sítio estão o nível e a barra de vida.

        Porque é preciso: com o chat FECHADO a coluna da esquerda tem os
        ícones do jogo e o ícone branco do grupo ('P') cai onde fica o
        separador 'Server' — o brilho dizia 'Server ativo' e o overlay
        saltava para um canal vazio (as conversas pareciam perdidas)."""
        channel, rest = GameWindow.input_row_of(img)
        names = ("whisper", "guild", "system", "server", "world", "party",
                 "channel", "group", "raid", "all")
        raw_ok = channel in names and channel != "whisper"
        # A escrever um PM: 'whisper | playeralpha texto' (sem o 'please').
        # Aceita se a 1.ª palavra é a pessoa da conversa — senão o chat
        # parecia fechado e a app deixava de ler enquanto escrevias.
        if channel == "whisper" and partner and rest:
            if _similar(_speaker_key(rest.split()[0]),
                        _speaker_key(partner)) >= 0.75:
                return True
        return bool(re.search(r"please|enter a|messag", rest)) or (
            raw_ok and bool(rest))

    @staticmethod
    def sleep_mode(img):
        """O jogo está no modo de poupança ('Swipe to exit sleep mode' no
        topo, ecrã escuro com o relógio)? O chat continua à vista e lê-se,
        mas teclas e cliques não chegam ao chat até o acordar (arrastar)."""
        if img is None:
            return False
        w, h = img.size
        s = h / 1440
        cx = w // 2
        crop = img.crop((cx - int(420 * s), int(150 * s), cx + int(420 * s),
                         int(215 * s))).convert("L")
        f = 2 / s
        crop = crop.resize((round(crop.width * f), round(crop.height * f)),
                           Image.LANCZOS)
        crop = ImageOps.invert(ImageOps.autocontrast(crop, cutoff=2))
        try:
            txt = pytesseract.image_to_string(
                crop, config="--psm 7 -l eng").lower()
        except Exception:
            return False
        return bool(re.search(r"sleep|swipe to ex|exit sl", txt))

    SLEEP_KEY = "l"     # tecla do jogo que liga/desliga o modo de poupança

    def toggle_sleep(self):
        """Carrega na tecla do modo de poupança (só com o jogo à frente)."""
        if not PYNPUT_OK or not self.is_foreground():
            return False
        kb = Controller()
        kb.press(self.SLEEP_KEY)
        time.sleep(random.uniform(0.07, 0.11))
        kb.release(self.SLEEP_KEY)
        return True

    def wake(self):
        """Acorda o jogo do modo de poupança. True = estava a dormir e
        acordou (quem chamou volta a pô-lo a dormir no fim); False = não
        estava a dormir; None = não consegui acordá-lo.
        Testado: a tecla L alterna o modo; o 'swipe' só pega devagar."""
        if not self.sleep_mode(self.capture_client()):
            return False
        if not self.is_foreground():
            return None
        for attempt in ("key", "swipe"):
            if attempt == "key":
                self.toggle_sleep()
            else:
                self._swipe()
            t0 = time.time()
            while time.time() - t0 < 2.0:
                time.sleep(0.3)
                if not self.sleep_mode(self.capture_client()):
                    log().info(f"Jogo acordado do modo de poupança "
                               f"({attempt})")
                    time.sleep(0.3)     # a UI do chat volta a responder
                    return True
        log().warning("Jogo em modo de poupança — não acordou")
        return None

    def _swipe(self):
        """Arrasto lento da esquerda para a direita no meio do ecrã (o
        'Swipe to exit sleep mode'). Rápido o jogo ignorava-o."""
        rect = self.client_rect()
        if not rect:
            return False
        gx, gy, gw, gh = rect
        old = self._wt.POINT()
        self._u32.GetCursorPos(ctypes.byref(old))
        self._u32.SetCursorPos(gx + gw // 2 - gw // 5, gy + gh // 2)
        time.sleep(0.08)
        self._u32.mouse_event(0x0002, 0, 0, 0, 0)        # LEFTDOWN
        time.sleep(0.08)
        steps = 60
        for _ in range(steps):
            self._u32.mouse_event(0x0001, (2 * gw // 5) // steps, 0, 0, 0)
            time.sleep(0.02)
        time.sleep(0.08)
        self._u32.mouse_event(0x0004, 0, 0, 0, 0)        # LEFTUP
        self._u32.SetCursorPos(old.x, old.y)
        return True

    @staticmethod
    def whisper_partner(img):
        """Nome da conversa aberta no Whisper (barra 'PlayerAlpha ⌃' no
        topo do painel), ou None."""
        if img is None:
            return None
        s = img.size[1] / 1440
        crop = img.crop((int(150 * s), int(95 * s), int(690 * s),
                         int(142 * s))).convert("L")
        # Letra do tamanho de 1440p x2, seja qual for a resolução.
        f = 2 / s
        crop = crop.resize((round(crop.width * f), round(crop.height * f)),
                           Image.LANCZOS)
        crop = ImageOps.invert(ImageOps.autocontrast(crop, cutoff=2))
        try:
            txt = pytesseract.image_to_string(
                crop, config="--psm 7 -l eng+rus").strip()
        except Exception:
            return None
        name = re.sub(r"[^\wЀ-ӿ]", "", txt.split(" ")[0] if txt
                      else "")
        return name or None

    def click_tab(self, channel, tries=3):
        """Clica num separador do chat do jogo e confirma que ficou ativo
        (logo a seguir a outra troca o painel ainda anima e o 1.º clique
        às vezes perde-se — no teste o 'World' falhou assim)."""
        y = CHAT_TABS_Y.get(channel)
        if y is None:
            return False
        for _ in range(tries):
            if not self.click_rel(CHAT_TAB_X / 1440, y / 1440):
                return False
            t0 = time.time()
            while time.time() - t0 < 1.5:
                time.sleep(0.3)
                if self.active_tab(self.capture_client()) == channel:
                    return True
        return False

    def read_input_row(self):
        """OCR da barra de baixo do chat: (canal, resto) em minúsculas,
        ex. ('whisper', 'playeralpha please enter a messa'). ('', '') se
        não der para ler. Usado para confirmar antes de escrever."""
        return self.input_row_of(self.capture_client())

    @staticmethod
    def input_row_of(img):
        """read_input_row() sobre uma captura já feita."""
        if img is None:
            return "", ""
        s = img.size[1] / 1440

        def ocr(x1, x2):
            # O nome do canal é escrito em cor apagada: o filtro de cor do
            # chat apagava-o. Aqui: cinzento + contraste, ampliado 3x.
            crop = img.crop((int(x1 * s), int(1362 * s),
                             int(x2 * s), int(1428 * s))).convert("L")
            f = 3 / s       # letra do tamanho de 1440p x3
            crop = crop.resize((round(crop.width * f),
                                round(crop.height * f)), Image.LANCZOS)
            crop = ImageOps.invert(ImageOps.autocontrast(crop, cutoff=2))
            try:
                return pytesseract.image_to_string(
                    crop, config="--psm 7 -l eng").strip().lower()
            except Exception:
                log().exception("read_input_row")
                return ""
        channel = re.sub(r"[^a-z]", "", ocr(8, 142))
        rest = " ".join(re.findall(r"[a-z0-9_]+", ocr(150, 700)))
        # OCR troca letras do canal ('build' = guild, 'miisear' = whisper):
        # fica o nome de canal mais parecido.
        names = ("whisper", "guild", "system", "server", "world", "party",
                 "channel", "group", "raid", "all")
        best = max(names, key=lambda n: _similar(channel, n)) if channel \
            else ""
        if best and _similar(channel, best) >= 0.4:
            channel = best
        # Só o Whisper tem um nome (destinatário) antes da caixa.
        if channel not in names and rest and not rest.startswith("please"):
            channel = "whisper"
        return channel, rest

    def activate(self):
        """Traz o jogo para a frente (ex.: o foco ficou no overlay depois
        de lhe clicares). Funciona porque esta app está à frente."""
        h = self.find()
        if not h:
            return False
        if self.is_foreground():
            return True
        try:
            self._u32.SetForegroundWindow.argtypes = [self._wt.HWND]
            self._u32.SetForegroundWindow(h)
        except Exception:
            return False
        for _ in range(20):
            if self.is_foreground():
                return True
            time.sleep(0.05)
        return False

    def foreground_is_own_process(self):
        if not self._ok:
            return False
        fg = self._u32.GetForegroundWindow()
        return bool(fg) and self._pid_of(fg) == os.getpid()

    # ---------- capturar ----------
    def capture_chat(self):
        """O painel de mensagens do chat, tirado da própria janela do jogo
        — independente de onde/que tamanho tem o overlay. None se o jogo
        estiver fechado ou minimizado."""
        return self.crop_chat(self.capture_client())

    @staticmethod
    def crop_chat(img):
        """Recorta o painel de mensagens de uma captura da área cliente."""
        if img is None:
            return None
        w, h = img.size
        # A UI do jogo escala pela altura e fica encostada à esquerda.
        x1, y1, x2, y2 = chat_region_rel()
        box = (max(0, int(x1 * h)), max(0, int(y1 * h)),
               min(int(x2 * h), w), min(int(y2 * h), h))
        if box[2] - box[0] < 50 or box[3] - box[1] < 50:
            return None
        return img.crop(box)

    def capture_client(self):
        """Área cliente da janela do jogo (sem moldura), ou None.

        PrintWindow funciona com o jogo atrás de outras janelas; com o
        jogo à frente em ecrã inteiro o Windows pode deixá-lo desenhar
        directo no ecrã (sem passar pelo DWM) e a imagem vem preta — aí
        captura-se o ecrã na área do jogo (o overlay está excluído das
        capturas, não aparece)."""
        img = self._print_window()
        if img is None and self.is_foreground():
            img = self._grab_screen_client()
        return img

    def _grab_screen_client(self):
        h = self.find()
        if not h or self._u32.IsIconic(h):
            return None
        r = self._wt.RECT()
        if not self._u32.GetClientRect(h, ctypes.byref(r)):
            return None
        pt = self._wt.POINT(0, 0)
        self._u32.ClientToScreen(h, ctypes.byref(pt))
        try:
            img = ImageGrab.grab(bbox=(pt.x, pt.y, pt.x + r.right,
                                       pt.y + r.bottom), all_screens=True)
        except Exception:
            log().exception("captura do ecrã falhou")
            return None
        return img.convert("RGB")

    def _print_window(self):
        h = self.find()
        if not h or self._u32.IsIconic(h):
            return None
        r = self._wt.RECT()
        if not self._u32.GetClientRect(h, ctypes.byref(r)):
            return None
        w, hh = r.right - r.left, r.bottom - r.top
        if w <= 0 or hh <= 0:
            return None
        u32, g32 = self._u32, self._g32
        hdc = u32.GetDC(h)
        mdc = g32.CreateCompatibleDC(hdc)
        bmp = g32.CreateCompatibleBitmap(hdc, w, hh)
        old = g32.SelectObject(mdc, bmp)
        try:
            if not u32.PrintWindow(h, mdc, self.PW_RENDERFULLCONTENT
                                   | self.PW_CLIENTONLY):
                return None

            class BIH(ctypes.Structure):
                _fields_ = [("biSize", ctypes.c_uint32),
                            ("biWidth", ctypes.c_int32),
                            ("biHeight", ctypes.c_int32),
                            ("biPlanes", ctypes.c_uint16),
                            ("biBitCount", ctypes.c_uint16),
                            ("biCompression", ctypes.c_uint32),
                            ("rest", ctypes.c_uint32 * 5)]
            bih = BIH(40, w, -hh, 1, 32, 0)
            buf = ctypes.create_string_buffer(w * hh * 4)
            g32.SelectObject(mdc, old)
            if not g32.GetDIBits(mdc, bmp, 0, hh, buf, ctypes.byref(bih), 0):
                return None
            img = Image.frombuffer("RGB", (w, hh), buf, "raw", "BGRX", 0, 1)
        finally:
            g32.DeleteObject(bmp)
            g32.DeleteDC(mdc)
            u32.ReleaseDC(h, hdc)
        if img.getextrema() == ((0, 0), (0, 0), (0, 0)):
            return None     # janela ainda não desenhada / minimizada
        return img


def read_chat_once(game=None, src="Auto (detectar)"):
    """Lê o chat agora (como o OCRWorker, uma vez): [linhas] ou None se o
    jogo não está à vista. Para confirmar a calibração da zona do chat."""
    game = game or GameWindow()
    full = game.capture_client()
    img = GameWindow.crop_chat(full)
    if img is None:
        return None
    td = get_app_tessdata_dir()
    if td and os.path.isdir(td) and not os.environ.get("TESSDATA_PREFIX"):
        os.environ["TESSDATA_PREFIX"] = \
            _ascii_tessdata(os.path.abspath(td)) + os.sep
    lang = resolve_tess_lang(src)
    raw = ocr_chat_text(preprocess_chat_image(img, 2.0 * 1440 / full.height),
                        "--psm 6" + (f" -l {lang}" if lang else ""))
    return [l for ch, l in parse_ocr_messages(raw) if ch != "system"]


def build_ocr_line_prompt(src, tgt):
    """Prompt de uma só mensagem (sem nome) — para modelos locais
    pequenos, que em lote saltam/trocam linhas."""
    src_note = (" It can be in any language: detect it."
                if src.startswith("Auto")
                else f" It is usually {src}, but can be another language.")
    return (
        f"Translate this MMORPG chat message into {tgt}.{src_note}\n"
        f"If it is already in {tgt}, return it unchanged.\n"
        "Keep game slang (CC, MA, WTB, WTS, afk, gank), numbers and "
        "amounts (30kk, 1300) and anything in [brackets] unchanged.\n"
        "Never add content. Output ONLY the translated message, on one "
        "line, no quotes, no notes."
    )


def build_ocr_retry_prompt(src, tgt):
    """Para repetir uma linha que a IA devolveu sem traduzir: com 'mantém
    WTS…' alguns modelos (Nemotron sem raciocínio) guardavam a frase
    toda ('WTS 2 чипа, пишите в лс')."""
    return (
        f"Translate this MMORPG chat message into {tgt}. Translate EVERY "
        f"word that is not in {tgt}. Only these stay as they are: the "
        "abbreviations WTB, WTS, WTT, LFG, PM, CC, MA, afk, and text in "
        "[brackets].\n"
        "Output ONLY the translated message, on one line, no quotes, no "
        "notes."
    )


# Frase do botão '▶ Ouvir' da voz, pela língua da voz (prefixo).
VOICE_SAMPLES = {
    "en": "Player says: who is coming to the boss in five minutes?",
    "pt": "Jogador diz: quem vem ao boss daqui a cinco minutos?",
    "es": "Jugador dice: ¿quién viene al jefe en cinco minutos?",
    "fr": "Joueur dit : qui vient au boss dans cinq minutes ?",
    "de": "Spieler sagt: wer kommt in fünf Minuten zum Boss?",
    "ru": "Игрок говорит: кто идёт на босса через пять минут?",
    "it": "Giocatore dice: chi viene al boss tra cinque minuti?",
}


# Como a voz anuncia quem fala, na língua de destino.
SPEECH_TEMPLATES = {
    "English": "{name} says: {msg}",
    "Portuguese (PT)": "{name} diz: {msg}",
    "Portuguese (BR)": "{name} diz: {msg}",
    "Russian": "{name} говорит: {msg}",
    "Spanish": "{name} dice: {msg}",
    "French": "{name} dit : {msg}",
    "German": "{name} sagt: {msg}",
    "Italian": "{name} dice: {msg}",
    "Korean": "{name} 님: {msg}",
    "Japanese": "{name}さん: {msg}",
    "Chinese (Simplified)": "{name}说：{msg}",
    "Turkish": "{name} diyor ki: {msg}",
    "Polish": "{name} mówi: {msg}",
}


_CYR_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g",
}


def transliterate_cyrillic(text):
    """'Шум says: hi' → 'Shum says: hi'. A voz inglesa não lê cirílico
    (calava-se nos nomes russos). Palavras todas em maiúsculas viram
    'Veter' para não serem soletradas letra a letra."""
    def word(m):
        w = m.group(0)
        out = []
        for c in w:
            t = _CYR_TRANSLIT.get(c.lower(), c)
            out.append(t.capitalize() if c.isupper() else t)
        res = "".join(out)
        if len(w) > 3 and w.isupper():
            res = res.capitalize()
        return res
    return re.sub(r"[Ѐ-ӿ]+", word, text)


def format_speech(line, target):
    """'[Nome] mensagem' → 'Nome says: mensagem' (None se nada a dizer)."""
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line.strip())
    name, msg = (m.group(1).strip(), m.group(2)) if m else (None, line)
    msg = msg.replace(EMOTE_TOKEN, " ")         # stickers não se lêem
    # Itens/locais entre [] lêem-se sem os parênteses.
    msg = re.sub(r"[\[\]]", "", msg).strip()
    # Números lêem-se sempre ('5', '90', '20k', 'daqui a 5 minutos'): no
    # jogo dizem quando, quanto, que nível. Só ':D', '??', '+' ficam calados.
    if not re.search(r"[^\W\d_]{2,}|\d", msg):
        return None
    if not name:
        return msg
    tpl = SPEECH_TEMPLATES.get(target, SPEECH_TEMPLATES["English"])
    return tpl.format(name=name, msg=msg)


# ==================================================================
# LÍNGUA DE UMA MENSAGEM (para responder na mesma língua)
# ==================================================================
_LANG_STOPWORDS = {
    "English": "the and you is are to of it what how this that for with "
               "have not do can my your so but was im dont lol yes need "
               "anyone who where when want",
    "Portuguese (PT)": "de que não nao os as é um uma para com eu tu você "
                       "voce isso está esta mas muito obrigado sim já ja vou "
                       "quem onde quer alguém alguem também tambem fazer",
    "Spanish": "que de el la los las es y en un una por con para yo tú "
               "eres está pero muy gracias sí qué quien donde quiero "
               "alguien también hacer tienes",
    "French": "le la les et est je tu vous de un une pas que qui pour avec "
              "ce merci oui suis",
    "German": "der die das und ist ich du nicht ein eine zu mit wer was wie "
              "danke ja bin hast",
    "Italian": "il lo la che è di un una non per con sono sei grazie ciao",
    "Polish": "i w nie to jest się na że z co jak ale dzięki tak",
    "Turkish": "ve bir bu ne değil mı mi ben sen için çok var yok evet "
               "tamam",
}
_LANG_STOPWORDS = {k: set(v.split()) for k, v in _LANG_STOPWORDS.items()}
_LANG_DIACRITICS = (("Portuguese (PT)", "ãõç"), ("Spanish", "ñ¿¡"),
                    ("German", "ßäöü"), ("Polish", "łąęśżźćń"),
                    ("Turkish", "ğşıç"), ("French", "èêàùœç"))


def detect_lang(text):
    """Língua (chave de LANGUAGES) de uma mensagem, ou None se não der
    para saber (curta demais, só números/emojis)."""
    t = (text or "").lower()
    if re.search(r"[Ѐ-ӿ]", t):
        return "Russian"
    if re.search(r"[가-힯]", t):
        return "Korean"
    if re.search(r"[぀-ヿ]", t):
        return "Japanese"
    if re.search(r"[一-鿿]", t):
        return "Chinese (Simplified)"
    words = re.findall(r"[a-zà-ÿğşıłąęśżźćń']+", t)
    if not words:
        return None
    scores = {lang: sum(1 for w in words if w in sw)
              for lang, sw in _LANG_STOPWORDS.items()}
    for lang, chars in _LANG_DIACRITICS:
        scores[lang] += 2 * sum(1 for c in chars if c in t)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None
    # Empate (palavras comuns a várias línguas): sem decisão.
    if list(scores.values()).count(scores[best]) > 1:
        return None
    return best


# Comando de voz 'muda para o chat server' / 'change to chat guild' /
# 'переключи на сервер'... → nome do canal. Nomes em várias línguas.
_CHANNEL_ALIASES = {
    "all": "all todos tudo geral все общий tous alle tutti",
    "world": "world mundo mundial мир monde welt mondo",
    "server": "server servidor servido сервер serveur",
    "party": "party festa grupo pt пати группа groupe gruppe gruppo",
    "guild": "guild guilda guilde clã cla clan гильдия ги gremio gilde "
             "gilda",
    "raid": "raid reide рейд",
    "whisper": "whisper privado privada pm sussurro личка лс шепот privé "
               "prive privato flüstern",
    "channel": "channel canal канал kanal canale",
    "system": "system sistema система système",
}
_CHANNEL_ALIASES = {ch: set(v.split()) for ch, v in _CHANNEL_ALIASES.items()}
_CMD_WORDS = set("change switch go open muda mudar troca trocar abre abrir "
                 "vai ir passa cambia cambiar переключи открой смени "
                 "passe changer ouvre wechsle wechseln öffne apri "
                 "chat канал".split())


def parse_chat_command(text):
    """Canal pedido numa frase curta tipo 'muda para o chat server', ou
    None se não for um comando (então é uma mensagem para enviar)."""
    words = re.findall(r"[\wЀ-ӿ]+", (text or "").lower())
    if not words or len(words) > 7:
        return None
    if not any(w in _CMD_WORDS for w in words):
        return None
    for w in reversed(words):
        for ch, aliases in _CHANNEL_ALIASES.items():
            if w in aliases:
                return ch
    return None


def _needs_translation(body):
    """False para ':D', '90', '[Central Tower]' — nada para traduzir."""
    rest = re.sub(r"\[[^\]]*\]", " ", body)
    return bool(re.search(r"[^\W\d_]{2,}", rest))


_ITEM_RE = re.compile(r"\[[^\[\]]+\]")
# Alfabetos (para ver se a tradução veio na escrita da língua de destino).
_SCRIPTS = {
    "latin": re.compile(r"[A-Za-zÀ-ɏ]"),
    "cyrillic": re.compile(r"[Ѐ-ӿ]"),
    "arabic": re.compile(r"[؀-ۿݐ-ݿ]"),
    "hebrew": re.compile(r"[֐-׿]"),
    "greek": re.compile(r"[Ͱ-Ͽ]"),
    "hangul": re.compile(r"[가-힯ᄀ-ᇿ]"),
    "kana": re.compile(r"[぀-ヿ]"),
    "han": re.compile(r"[一-鿿]"),
    "thai": re.compile(r"[฀-๿]"),
    "devanagari": re.compile(r"[ऀ-ॿ]"),
}
_TARGET_SCRIPTS = {"Russian": {"cyrillic"}, "Korean": {"hangul", "han"},
                   "Japanese": {"kana", "han"},
                   "Chinese (Simplified)": {"han"}}


def wrong_script(text, target):
    """A tradução veio noutro alfabeto? O Groq ALLaM respondia às vezes em
    árabe ('من سيذهب إلى حرب الرقائق') e outros deixavam metade em russo.
    Não contam os itens '[...]' nem siglas/nomes latinos curtos."""
    t = _ITEM_RE.sub(" ", text or "")
    want = _TARGET_SCRIPTS.get(target or "", {"latin"})
    good = bad = 0
    for name, rx in _SCRIPTS.items():
        n = len(rx.findall(t))
        if name in want:
            good += n
        elif not (name == "latin" and want != {"latin"}):
            bad += n
    return bad > 0.3 * max(1, good + bad)


def fix_translation(src, res):
    """Correções à tradução do corpo de uma mensagem (sem '[Nome]'),
    para qualquer IA/tradutor:
    - WTB (compro) ↔ WTS (vendo) trocado = o pior erro numa troca: repõe;
      e a sigla que desapareceu ('I want to buy a ...') volta à frente.
    - Itens/locais '[...]' são o que importa num WTB/WTS. O modelo às
      vezes estraga-os ('[+10 Prime Drive]' → '[Prime Drive]', '[7
      Blade]') ou tira os parênteses ('a Kallon Catalyst'): o original
      volta ao MESMO sítio. Antes juntava-se o original à frente e o item
      aparecia duas vezes. Só se não houver rasto dele vai para a frente."""
    res = (res or "").strip()
    if len(res) > 2 * len(src) + 30:
        # Saída em ciclo ('mainstremainstre…', 'go go go go …', a mesma
        # frase 5x): fica uma vez; e nunca muito maior que o original.
        res = re.sub(r"(.{2,60}?)(?:\s*\1){3,}", r"\1", res)
        if len(res) > 4 * len(src) + 80:
            res = res[:2 * len(src) + 40].rsplit(" ", 1)[0] + "…"
    for a, b in (("wtb", "wts"), ("wts", "wtb")):
        if re.search(rf"\b{a}\b", src, re.I) \
                and not re.search(rf"\b{a}\b", res, re.I):
            if re.search(rf"\b{b}\b", res, re.I):
                res = re.sub(rf"\b{b}\b", a.upper(), res, flags=re.I)
            else:
                res = f"{a.upper()} {res}"
    if EMOTE_TOKEN in src and EMOTE_TOKEN not in res:
        res = f"{res} {EMOTE_TOKEN}"
    items = [i for i in _ITEM_RE.findall(src) if i != EMOTE_TOKEN]
    if not items:
        return res
    for item in items:
        if item in res:
            continue
        inner = item[1:-1].strip()
        if not inner:
            continue
        cands = [c for c in _ITEM_RE.findall(res) if c not in items]
        best = max(cands, key=lambda c: _similar(c.lower(), item.lower()),
                   default=None)
        if best and _similar(best.lower(), item.lower()) >= 0.6:
            res = res.replace(best, item, 1)
            continue
        m = re.search(re.escape(inner), res, re.I)
        if m:
            res = res[:m.start()] + item + res[m.end():]
            continue
        res = f"{item} {res}"
    # Cópias estragadas que sobraram ao lado do original.
    for c in _ITEM_RE.findall(res):
        if c not in items and any(_similar(c.lower(), i.lower()) >= 0.6
                                  for i in items if i in res):
            res = re.sub(r"\s*" + re.escape(c), "", res, count=1)
    return re.sub(r"\s{2,}", " ", res).strip()


EMOTE_TOKEN = "[emote]"


# Leitura cirílica estragada de um nome → leitura inglesa (ou None se
# não deu): os mesmos nomes aparecem em todos os ciclos.
_NAME_FIX_CACHE = {}


def _fix_speaker_words(img, d, words):
    """{índice: texto} para palavras do NOME do jogador (entre os 1.ºs
    '[ ]' da linha) lidas em cirílico com confiança baixa: relê só esse
    bocado com OCR inglês. Um ícone colado ao nome ('[◇ ExampleName]')
    fazia o OCR ler 'ЕхатрІеNаmе' (conf 56); 'Ма!' (16) era 'Marlow'.
    Nomes russos a sério ('Тестер', conf 82) ficam como estão; e o texto
    da mensagem nunca é mexido ('Привет' viraria 'NpuBet')."""
    fixed = {}
    by_line = {}
    for i in words:
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        by_line.setdefault(key, []).append(i)
    for idxs in by_line.values():
        start = next((n for n, i in enumerate(idxs[:4])
                      if "[" in d["text"][i]), None)
        if start is None:
            continue
        for i in idxs[start:start + 4]:
            t = d["text"][i]
            try:
                conf = float(d["conf"][i])
            except (TypeError, ValueError):
                conf = 0
            if _CYR_RE.search(t) and conf < 65 and t in _NAME_FIX_CACHE:
                if _NAME_FIX_CACHE[t]:
                    fixed[i] = _NAME_FIX_CACHE[t]
            elif _CYR_RE.search(t) and conf < 65:
                if len(_NAME_FIX_CACHE) > 300:
                    _NAME_FIX_CACHE.clear()
                _NAME_FIX_CACHE[t] = None   # mesmo se falhar: não repete
                x, y = d["left"][i], d["top"][i]
                w, h = d["width"][i], d["height"][i]
                crop = img.crop((max(0, x - 6), max(0, y - 6),
                                 x + w + 6, y + h + 6))
                try:
                    e = pytesseract.image_to_data(
                        crop, config="--psm 8 -l eng",
                        output_type=pytesseract.Output.DICT)
                except Exception:
                    continue
                cand = [(e["text"][j], float(e["conf"][j]))
                        for j in range(len(e["text"])) if e["text"][j].strip()]
                txt = "".join(c for c, _ in cand)
                core = re.sub(r"[^\w]", "", txt)
                if len(re.findall(r"[A-Za-z]", core)) >= 3 \
                        and max((c for _, c in cand), default=0) >= 30:
                    lead = "[" if t.lstrip("|").startswith("[") else ""
                    tail = "]" if t.endswith("]") else ""
                    fixed[i] = lead + core + tail
                    _NAME_FIX_CACHE[t] = fixed[i]
                    log().debug(f"OCR: nome relido em inglês {t!r} → "
                                f"{fixed[i]!r} (conf {conf:.0f})")
            if "]" in t:
                break
    return fixed


# Marcas no início de cada linha do OCR quando a POSIÇÃO na imagem diz o
# que ela é (parse_ocr_messages tira-as):
#   MSG_START + etiqueta + MSG_SEP + resto  → mensagem nova (tem a etiqueta
#                                             do canal na coluna da esquerda)
#   MSG_CONT + texto                        → continuação da anterior
# Com a letra pequena (720p/768p) a etiqueta saía ilegível ('4 Sucvec',
# 'П бегу') e a mensagem colava-se à anterior; a posição não engana.
# (Uso privado do Unicode: '\x1d'..'\x1f' contam como espaço/quebra de
# linha para strip() e splitlines().)
MSG_START, MSG_SEP, MSG_CONT = "", "", ""
# Coluna das etiquetas ('Guild', '4 Server', 'Whisper'), em fracção da
# largura do painel: começam em ~2%, o '[Nome]' e as continuações em ~15%.
_PILL_COL = 0.12


def _ink_rows(gray, box):
    """[True/False] por linha de píxeis de `box`: tem tinta (texto preto)?"""
    x0, y0, x1, y1 = box
    if x1 - x0 < 1 or y1 - y0 < 1:
        return []
    col = gray.crop(box).resize((1, y1 - y0), Image.BOX)
    return [v < 248 for v in col.getdata()]


def _is_sticker(gray, d, i, median):
    """A palavra i é um bocado de um sticker? O sticker é uma imagem com
    3-4 linhas de altura e o OCR lia-o como letras soltas da altura do
    texto ('ma', 'fi', 'Ws'), que iam para a IA e eram lidas em voz alta.
    Mede a mancha de tinta contínua na vertical por cima/baixo da palavra:
    texto ~1,3 linhas (há espaço branco entre linhas), sticker > 3."""
    x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
    reach = int(3 * median)
    y0 = max(0, y - reach)
    rows = _ink_rows(gray, (x, y0, x + w, min(gray.height, y + h + reach)))
    if not rows:
        return False
    gap_max = max(2, int(0.2 * median))
    c = min(len(rows) - 1, y - y0 + h // 2)

    def extend(step):
        j, gap, last = c, 0, c
        while 0 <= j + step < len(rows):
            j += step
            if rows[j]:
                gap, last = 0, j
            else:
                gap += 1
                if gap > gap_max:
                    break
        return last
    return extend(1) - extend(-1) > 3.2 * median


def _line_starts(gray, d, boxes, keys):
    """{linha: True (mensagem nova) / False (continuação)} pela posição, ou
    None se este ecrã não tem etiquetas de canal (outro layout)."""
    W = gray.width
    starts = {}
    for k in keys:
        ids = boxes[k]
        if d["left"][ids[0]] < _PILL_COL * W:
            starts[k] = True
            continue
        # O OCR às vezes não lê a etiqueta: vê-se a tinta dela na coluna.
        top = min(d["top"][i] for i in ids)
        bot = max(d["top"][i] + d["height"][i] for i in ids)
        rows = _ink_rows(gray, (int(0.01 * W), top, int(_PILL_COL * W), bot))
        starts[k] = sum(rows) >= 0.4 * max(1, len(rows))
    return starts if any(starts.values()) else None


def ocr_chat_text(img, config):
    """Como pytesseract.image_to_string, mas os stickers/emotes viram
    '[emote]': o OCR lia-os como palavras de lixo ('sey', 'see%s') muito
    mais altas que o texto (107 px vs 43 px de mediana no teste). Cada
    linha leva MSG_START/MSG_CONT conforme a posição (ver acima)."""
    d = pytesseract.image_to_data(img, config=config,
                                  output_type=pytesseract.Output.DICT)
    words = [i for i, t in enumerate(d["text"]) if t.strip()]
    if not words:
        return ""
    heights = sorted(d["height"][i] for i in words)
    median = heights[len(heights) // 2]
    fixed = _fix_speaker_words(img, d, words)
    gray = img.convert("L")
    W = gray.width
    lines, order, boxes = {}, [], {}
    for i in words:
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        if key not in lines:
            lines[key] = []
            boxes[key] = []
            order.append(key)
        boxes[key].append(i)
        tok = fixed.get(i, d["text"][i])
        if median and (d["height"][i] > 1.8 * median or (
                d["left"][i] > _PILL_COL * W
                and len(tok.strip("[]")) <= 4
                and _is_sticker(gray, d, i, median))):
            tok = EMOTE_TOKEN
            if lines[key] and lines[key][-1] == EMOTE_TOKEN:
                continue
        lines[key].append(tok)
    keep = _drop_cut_top(d, words, order, lines, median)
    starts = _line_starts(gray, d, boxes, keep) if keep else None
    keep = _drop_cut_bottom(gray, d, boxes, keep, starts, median)
    out = []
    for k in keep:
        if starts is None:
            out.append(" ".join(lines[k]))
        elif starts[k]:
            pill = [n for n, i in enumerate(boxes[k])
                    if d["left"][i] < _PILL_COL * W]
            cut = (pill[-1] + 1) if pill else 0
            out.append(MSG_START + " ".join(lines[k][:cut]) + MSG_SEP
                       + " ".join(lines[k][cut:]))
        elif out:
            out.append(MSG_CONT + " ".join(lines[k]))
        # Continuação antes da 1.ª mensagem: o início está acima do painel.
    return "\n".join(out)


def _drop_cut_top(d, words, order, lines, median):
    """Tira do topo do painel o que é só um bocado de mensagem:
    1) a linha cortada ao meio pela borda de cima (o chat subiu; letras
       com metade da altura e confiança ~30%: 'UEIVG! LeaiNWIIAAT J >
       24' em vez de '[PlayerOne] из за турелек');
    2) as linhas seguintes sem '[' (o resto dessa mensagem, que perdeu
       o '[Nome]': 'O6mkaTbca?') — antes iam como aviso do sistema, a
       voz lia lixo e a IA chegou a inventar 'I'm going to bed.'.
    Essa mensagem já foi lida quando estava inteira, mais abaixo. Sem
    nenhuma linha com '[' (separador System) não se tira nada."""
    if not order or not median:
        return order
    by_line = {}
    for i in words:
        k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        by_line.setdefault(k, []).append(i)

    def cut_at_top(k):
        ids = by_line.get(k) or []
        if not ids:
            return False
        top = min(d["top"][i] for i in ids)
        hs = sorted(d["height"][i] for i in ids)
        return top < 0.6 * median and hs[len(hs) // 2] < 0.75 * median

    out = list(order)
    if cut_at_top(out[0]):
        log().debug(f"OCR: linha cortada no topo ignorada: "
                    f"{' '.join(lines[out[0]])[:60]!r}")
        out = out[1:]
    def header(k):
        # '[Nome]' (o OCR às vezes perde um dos parênteses: 'Пат] wts')
        head = " ".join(lines[k])[:40]
        return "[" in head or "]" in head

    if any(header(k) for k in out):
        while out and not header(out[0]):
            log().debug(f"OCR: resto de mensagem sem nome ignorado: "
                        f"{' '.join(lines[out[0]])[:60]!r}")
            out = out[1:]
    return out


def _drop_cut_bottom(gray, d, boxes, keep, starts, median):
    """Tira do fundo a mensagem cuja última linha a borda de baixo corta
    ao meio (zona calibrada à mão a meio de uma linha): as letras
    cortadas saíam como lixo ('Пизеаг Enrre [21153]') e, com o chat
    parado, a mesma leitura repetia-se e ia para a IA. Sai a mensagem
    toda (o início sozinho parecia uma mensagem completa); é lida quando
    subir no chat."""
    if not keep or not median:
        return keep
    # Há letras a tocar na borda de baixo? (A zona automática acaba no
    # espaço vazio por cima da barra de ícones: nunca toca.)
    edge = max(3, int(0.25 * median))
    rows = _ink_rows(gray, (int(_PILL_COL * gray.width), gray.height - edge,
                            gray.width, gray.height))
    if not any(rows):
        return keep
    ids = boxes[keep[-1]]
    bot = max(d["top"][i] + d["height"][i] for i in ids)
    out = list(keep)
    log().debug("OCR: mensagem cortada no fundo da zona ignorada")
    if bot >= gray.height - 1.2 * median:
        cut = out.pop()             # a própria última linha está cortada
        if starts is None or starts.get(cut):
            return out
    else:
        # A linha cortada nem foi lida (só se vê um bocado). Se tem a
        # etiqueta do canal é uma mensagem nova: a de cima está completa.
        pill = _ink_rows(gray, (int(0.01 * gray.width), int(bot),
                                int(_PILL_COL * gray.width), gray.height))
        if starts is None or any(pill):
            return keep
    # O que ficou no fim é o início da mensagem cortada: sai até à etiqueta.
    while out and not starts.get(out[-1]):
        out.pop()
    if out:
        out.pop()
    return out


def build_voice_prompt(src, tgt):
    # O reconhecimento de voz (Google) troca palavras de jogo em inglês por
    # palavras parecidas ('boss' → 'vosso', 'dungeon' → 'dension') — e as
    # hipóteses alternativas trazem o mesmo erro. Quem pode corrigir é o
    # modelo, pelo contexto.
    return (f"This {src} message from an MMORPG player came from speech "
            "recognition, so gaming words may be misheard as similar-"
            "sounding words (e.g. 'vosso'/'bós' = boss, 'dension'/'danjon' "
            "= dungeon, 'ellar'/'iler' = healer, 'fumar' = farm, 'drope' = "
            "drop). Silently fix such words, then translate the WHOLE "
            f"message into {tgt}: every word must be in {tgt}, leave no "
            f"{src} words. Keep MMORPG terms accurate. Respond ONLY with "
            "the translation, no quotes, no explanations.")


# ==================================================================
# DEDUP / NAME HELPERS
# ==================================================================
def _normalize_for_dedup(text):
    # \W é unicode-aware: mantém cirílico (antes '[^a-z0-9]' apagava-o e
    # todas as mensagens russas do mesmo jogador pareciam iguais).
    return re.sub(r"[\W_]+", "", (text or "").lower())


def _normalize_name(n):
    return re.sub(r"[\W_]+", "", (n or "").lower())


_SPEAKER_KEY_MAP = str.maketrans("oqdilsz", "0001152")


def _speaker_key(n):
    """Chave de nome tolerante a trocas do OCR (N0va = NOVA, testO07 =
    test007 = te5t007)."""
    # Mapear cirílico ANTES de minúsculas: 'ВЕТЕР' == 'BETEP'.
    n = re.sub(r"[\W_]+", "", n or "").translate(_CYR_TO_LAT).lower()
    return n.translate(_SPEAKER_KEY_MAP)


def _similar(a, b):
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


# ==================================================================
# LIMPEZA DE TEXTO OCR
# ==================================================================
# Letras que o Tesseract troca entre latim e cirílico (eng+rus).
_CYR_TO_LAT = str.maketrans(
    "аеорсхукмтгзпидАЕОРСХУКМТВНЗ",
    "aeopcxykmtrsnugAEOPCXYKMTBHS")
_LAT_TO_CYR = str.maketrans(
    "aeopcxykmrnuABEHKMOPCTXy",
    "аеорсхукмгпиАВЕНКМОРСТХу")
_CYR_RE = re.compile(r"[Ѐ-ӿ]")
_LAT_RE = re.compile(r"[A-Za-z]")
_CYR_LOOKALIKE = set("аеорсхукмтгзпидАЕОРСХУКМТВНЗ")
_LAT_LOOKALIKE = set("aeopcxykmrnuABEHKMOPCTXy")
# Restos do ícone 🌐 / timestamp no fim da mensagem.
_TRAILING_JUNK_RE = re.compile(
    r"(?:\s*[@®©¢§&%“”‘’{}=~_|\\«»*]+|\s*\d?:{2,}['’.]?|(?<=[^\s:]):)+\s*$")
# Em fundo claro o 🌐 sai como ' 2:', ' 15:', ' =:' no fim da linha.
_TRAILING_GLOBE_RE = re.compile(r"\s+[^\s\w]?\d{0,2}[^\s\w]?:[:*]*\s*$")


def _fix_confusables(text):
    """Corrige palavras lidas no alfabeto errado.

    Linha maioritariamente latina: 'зеа007' → 'sea007', 'и' → 'u'.
    Linha maioritariamente cirílica: 'He знаю' → 'Не знаю'. Siglas em
    maiúsculas (CC, MA, WTB) ficam como estão.
    """
    n_cyr = len(_CYR_RE.findall(text))
    n_lat = len(_LAT_RE.findall(text))
    if n_cyr == 0 or n_lat == 0:
        return text
    out = []
    for tok in re.split(r"(\s+)", text):
        letters = [c for c in tok if c.isalpha()]
        if not letters:
            out.append(tok); continue
        if n_lat > 2 * n_cyr and all(
                (c in _CYR_LOOKALIKE) or not _CYR_RE.match(c)
                for c in letters) and any(_CYR_RE.match(c) for c in letters):
            tok = tok.translate(_CYR_TO_LAT)
        elif n_cyr > 2 * n_lat and not tok.isupper() and all(
                c in _LAT_LOOKALIKE for c in letters):
            tok = tok.translate(_LAT_TO_CYR)
        out.append(tok)
    return "".join(out)


# Numa linha em russo o OCR lê os números do chat (letra quadrada) como
# letras cirílicas: '60+' → 'БО+', '80' → 'ВП'/'ВО'. Só tokens curtos, todo
# em maiúsculas dessas letras (ou misturados com dígitos): palavras russas
# a sério ('Босс', 'ВОТ') não mudam.
_CYR_DIGIT = str.maketrans("БВЗОПбзо", "68300630")
_CYR_DIGIT_RE = re.compile(
    r"(?<![\wЀ-ӿ])([0-9БВЗОПбзо]{2,4})(?=[кkКK]?(?:[+%]|[^\wЀ-ӿ]|$))")


def _fix_digits(text):
    if not _CYR_RE.search(text):
        return text

    def fix(m):
        tok = m.group(1)
        after = text[m.end():m.end() + 2]
        if re.search(r"[0-9]", tok):
            return tok.translate(_CYR_DIGIT)    # '6О' / '2О0к': mistura
        # Só letras: tem de parecer mesmo um número (siglas como 'ВВП'
        # ficam): 2 maiúsculas a começar por Б/В (6/8), ou com '+'/'%'/'к'
        # logo a seguir ('ОО+').
        if not re.fullmatch(r"[БВЗОП]{2,3}", tok):
            return tok
        if (len(tok) == 2 and tok[0] in "БВ") or after[:1] in ("+", "%") \
                or after[:1] in ("к", "k", "К", "K"):
            return tok.translate(_CYR_DIGIT)
        return tok
    return _CYR_DIGIT_RE.sub(fix, text)


def _fix_speaker(speaker):
    speaker = re.sub(r"^[^\wЀ-ӿ]+|[^\wЀ-ӿ]+$", "",
                     speaker).strip()
    tokens = speaker.split()
    # Ícone antes do nome (coroa de guild) lido como 'ii', 'idi', 'М'.
    # Nomes do RF não têm espaços.
    while len(tokens) >= 2 and len(tokens[0]) <= 3 and len(tokens[1]) >= 3:
        tokens = tokens[1:]
    # Token com escrita mista ('зеа007') é um nome latino lido mal; e
    # nome em 'CamelCase' só com letras cirílicas parecidas com latinas
    # ('СарТор' = CapTop) também — nomes russos a sério ('ВЕТЕР',
    # 'Сокол') não têm minúscula seguida de maiúscula.
    def latin_misread(t):
        if not _CYR_RE.search(t):
            return False
        if _LAT_RE.search(t) or re.search(r"\d", t):
            return True
        return (bool(re.search(r"[а-яё][А-ЯЁ]", t))
                and all(c in _CYR_LOOKALIKE for c in t if c.isalpha()))
    tokens = [t.translate(_CYR_TO_LAT) if latin_misread(t) else t
              for t in tokens]
    return " ".join(tokens)


# Canais do chat do jogo (separadores da coluna da esquerda).
CHANNELS = ("all", "world", "server", "party", "guild", "raid", "whisper",
            "channel", "system")
_TAG_TO_CHANNEL = {"all": "all", "world": "world", "server": "server",
                   "party": "party", "guild": "guild", "gremio": "guild",
                   "whisper": "whisper", "channel": "channel",
                   "system": "system", "group": "raid", "raid": "raid",
                   "grupo": "raid"}


def clean_ocr_text(raw: str) -> str:
    return "\n".join(line for _, line in parse_ocr_messages(raw))


def parse_ocr_messages(raw: str):
    """[(canal, '[Nome] mensagem')] pela ordem do chat. O canal vem da
    etiqueta de cada linha ('Guild', 'Whisper'...); None se não tiver."""
    # 'emote': com o chat fechado o OCR lê o mundo do jogo e os ícones
    # grandes viram '[emote]' no início da linha — parecia um '[Nome]'.
    GENERIC_NAMES = {"player", "unknown", "system", "null", "npc",
                     "you", "none", "?", "emote"}
    TAB_PREFIXES = (r"All|World|Server|Party|Guild|Whisper|Channel|"
                    r"System|Group|Raid|Grupo|Gremio")

    # O tab do canal ('Guild', 'Whisper') vem sempre antes de '[Nome]'.
    # Case-sensitive e exige '[' a seguir: senão 'all night' numa linha
    # de continuação perdia o 'all'.
    # Também 'Guild A guild auction has ended.' (aviso sem [Nome]).
    # 'Guild N.' = aviso da guild (o OCR lê o 'N.' como 'М.').
    # 'System' + qualquer palavra: os avisos de drops começam pelo nome de
    # quem apanhou, às vezes em minúsculas ('System playerone obteve [...]').
    TAB_TAG_RE = re.compile(
        rf"^(?:(?:{TAB_PREFIXES})(?:\s*[NМM]\.\s*"
        r"|[\s\)\]\"'`•·:.\-]*(?=[\[\(]|[A-ZА-ЯЁ]))|System\s+(?=\S))")

    def strip_tab_prefix(s):
        return TAB_TAG_RE.sub("", s).strip()

    def split_merged_lines(s):
        # Mantém a etiqueta (e o nº do servidor) na nova linha: é dela
        # que vem o canal.
        # Não parte entre o nº do servidor e a etiqueta ('4 Server [x]'
        # no início da linha).
        s = re.sub(
            rf"(?<!^\d)(?<!^\d\d)\s+((?:\d{{1,2}}\s*)?(?:{TAB_PREFIXES})"
            rf"[\s\)\]\"'`•·:.\-]*\[)",
            r"\n\1", s)
        # Etiqueta perdida mas com o ícone da coroa antes do nome ('...
        # não percebi ``. [м PlayerOne ] Entramos'): os nomes não têm
        # espaços, por isso '[ícone Nome]' a meio começa mensagem nova.
        # Ícone só com letras/№: '[+7 Blade]' (item) não parte. Antes tem
        # de vir pontuação (a etiqueta mal lida), não 'Guild' nem texto.
        s = re.sub(r"(?<=[^\w\s])\s+(\[\s*(?:[^\W\d_]{1,3}|№)\s+[^\s\]]{3,20}"
                   r"\s*\])", r"\n\1", s)
        # Aviso do System colado ao fim do anterior ('(Bound). System x').
        # Só depois do fim típico de um aviso ('] .' / '(Bound).'): senão
        # '[Hiro] System is down' partia a mensagem do jogador.
        s = re.sub(r"(\]\s?\.|\)\.)\s+(System\s)", r"\1\n\2", s)
        # World com a etiqueta mal lida ('двор 4 Вегуег [х]'): nº +
        # palavra + '[' a meio da linha também começa mensagem nova.
        return re.sub(r"(?<=\S)\s+(\d{1,2}\s+[^\s\[\]]{4,8}\s*\[)",
                      r"\n\1", s)

    TAB_NAMES = ("All", "World", "Server", "Party", "Guild", "Whisper",
                 "Channel", "System", "Group", "Raid")

    def normalize_tag(s):
        """'4 Server [Name] WTB' → ('Server [Name] WTB', True): no World
        cada linha traz o nº do servidor de quem escreve. Também corrige
        a etiqueta lida em cirílico ('Зегуег [x]' → 'Server [x]').
        Só mexe quando vem logo antes de '[Nome]'."""
        m = re.match(r"^(\d{1,2})?\s*([^\s\[\(]{3,9})(?=\s*[\[\(])", s)
        if not m:
            return s, False
        word = m.group(2).translate(_CYR_TO_LAT).lower()
        best = max(TAB_NAMES, key=lambda n: _similar(word, n.lower()))
        if _similar(word, best.lower()) < 0.6:
            return s, False         # é um nome/palavra, não uma etiqueta
        return best + s[m.end(2):], bool(m.group(1))

    def fix_bracket(s):
        if s.startswith(("(", "{")):
            s = "[" + s[1:]
        # ']' lido como ')' / '}' (com ou sem espaço): '[PlayerOne ) wts',
        # '{Hiro) [+8 ...', '[PlayerTwo} да'. Nomes não têm espaços.
        s = re.sub(r"^\[\s*([^\]\)\}\s]{2,30})\s*[\)\}](?=\s|$)", r"[\1]", s,
                   count=1)
        # Whisper sem ']' ('[ Oenger: P1ayerA!pha I see you...'): o nome é
        # a 1.ª palavra depois de ':'; um 'I'/'l'/'|' solto a seguir era o
        # ']' mal lido.
        if s.startswith("[") and "]" not in s[:48]:
            s = re.sub(r"^\[\s*([^\s:;\]]{3,12})\s*[:;]\s*([^\s\]]{2,30})"
                       r"(?:\s+[Il|1](?=\s))?\s+",
                       r"[\1: \2] ", s, count=1)
        s = re.sub(r"^\[([^\]\)]+)\)\]", r"[\1]", s)
        # ']' lido como 'l'/'1'/'|' colado ao nome: '[ExampleNamel ok'.
        if s.startswith("[") and "]" not in s.split(" ", 1)[0] \
                and ")" not in s.split(" ", 1)[0]:
            s = re.sub(r"^\[(\S{2,30}?)[l1|IJ]\s", r"[\1] ", s)
        # (Nome sem espaços: '[Hiro)) ))) спс' não pode virar o nome
        # 'Hiro)) ))) спс не надо (+12'.)
        m = re.match(r"^\[([^\]\)\s]{1,30})\)", s)
        if m and "]" not in s[:len(m.group(0))]:
            s = "[" + m.group(1) + "]" + s[len(m.group(0)):]
        return s

    def clean_body(body):
        body = re.sub(
            rf"^\s*(?:{TAB_PREFIXES})[\s\)\]\"'`•·:.\-]+",
            "", body)
        body = re.sub(r"^[\s\]\)]+", "", body)
        body = re.sub(r"\s+", " ", body).strip()
        body = _TRAILING_GLOBE_RE.sub("", body)
        # Barra de ícones por baixo do chat (🎲📍➕) lida como ' +.'.
        body = re.sub(r"\s+[+*]\s*\.?\s*$", "", body)
        return _TRAILING_JUNK_RE.sub("", body).strip()

    def remove_time_noise(s):
        s = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", "", s)
        # Unidade como palavra inteira: antes '1 Server' (nº do servidor
        # no World) era apagado como '1 s(egundo)'.
        s = re.sub(
            r"\b\d+\s*(?:min[a-z]*|h|hrs?|hours?|sec[a-z]*|seconds?|s|seg)"
            r"\b(?:\s+ago)?",
            "", s, flags=re.I)
        s = re.sub(r"\bago\b", "", s, flags=re.I)
        s = re.sub(r"[©®™|¦]\s*\d+\b", "", s)
        return s

    def whisper_speaker(speaker):
        """No RF Next o whisper é do ponto de vista de quem envia:
        '[Sender: X] msg'    = EU enviei a X  → None (ignora, como my_name)
        '[Recipient: X] msg' = X enviou-me    → X
        (Confirmado no log: a voz escreveu '2 минуты' e o OCR leu
        '[Sender: PlayerAlpha] минуты'.) O OCR lê 'Sender' como 'Gender'."""
        m = re.match(r"^(\S{2,12})\s*[:;]\s*(.+)$", speaker)
        loose = False
        if not m:
            # Os ':' perdidos ('Sender PlayerOne'): só com a 1.ª palavra
            # muito parecida com Sender/Recipient (nomes não têm espaços).
            m = re.match(r"^(\S{4,12})\s+(\S.{1,30})$", speaker)
            loose = True
        if not m:
            return speaker
        role = re.sub(r"[^a-z]", "",
                      m.group(1).translate(_CYR_TO_LAT).lower())
        if loose and max(_similar(role, "sender"),
                         _similar(role, "recipient")) < 0.75:
            return speaker
        # Por parecença: o OCR lê 'Sender' como 'Gender', 'Oenger',
        # 'Sencer'... e 'Recipient' como 'Recipiert', 'Rec1pient'.
        if (re.match(r"^.?en[dgc]|^de$|^send", role)
                or _similar(role, "sender") >= 0.6):
            return None
        if (role.startswith(("rec", "rek", "para"))
                or _similar(role, "recipient") >= 0.6):
            return m.group(2).strip()
        return speaker

    def pill_tag(pill):
        """Texto da etiqueta à esquerda ('4 Server', 'Guild', '4 Sucvec')
        → ('4 Server ' / 'Guild ' / '', é do World?). Ilegível = ''."""
        # Nº do servidor (só no World); '1' sai muitas vezes como 'i'/'l'.
        numbered = bool(re.match(r"^\W*(?:\d|[iIl|](?=\s|[A-ZА-Я]))", pill))
        words = re.findall(r"[^\d\W]{3,9}", pill)
        if not words:
            return "", numbered
        word = max(words, key=len).translate(_CYR_TO_LAT).lower()
        best = max(TAB_NAMES, key=lambda n: _similar(word, n.lower()))
        if _similar(word, best.lower()) < 0.6:
            return "", numbered
        return best + " ", numbered

    def bracket_speaker(sub):
        """Mensagem nova (pela posição) cujo '[' saiu como '|', 'I', '(':
        '| Gender PlayerOnel yes' → '[Gender: PlayerOnel] yes'."""
        if re.match(r"^\[[^\]]{1,40}\]", sub):
            return sub
        bare = re.sub(r"^[^\w\[]*(?:[\[|({]|[Il1](?=\s))?\s*", "", sub,
                      count=1)
        m = re.match(r"^(\S{3,12}?)[:;.,]?\s+(\S{2,30}?)\s*"
                     r"[\]|lI1)]?\s+(.*)$", bare)
        if m:
            role = re.sub(r"[^a-z]", "", m.group(1).translate(
                _CYR_TO_LAT).lower())
            for name in ("sender", "recipient"):
                if _similar(role, name) >= 0.6:
                    return f"[{name.title()}: {m.group(2)}] {m.group(3)}"
        return sub

    # 1) Linhas → mensagens. O chat parte mensagens longas em várias
    #    linhas; uma linha sem tab/[Nome] continua a mensagem anterior.
    messages = []   # [speaker or None, body, canal]
    for raw_line in raw.splitlines():
        s = raw_line.strip()
        if not s:
            continue
        # A posição na imagem já disse o que a linha é (ocr_chat_text).
        if s.startswith(MSG_CONT):
            if messages:
                messages[-1][1] += " " + s[1:].strip()
            continue
        if s.startswith(MSG_START):
            pill, _, rest = s[1:].partition(MSG_SEP)
            tag, numbered = pill_tag(pill)
            rest = remove_time_noise(rest)
            rest = re.sub(r"[©®™¦→←↑↓•◆★♥]+", " ", rest)
            rest = re.sub(r"\s+", " ", rest).strip()
            sub = fix_bracket(bracket_speaker(rest))
            sub = re.sub(r"(?<=\s)\|(?=\s)", "I", sub)
            sub = re.sub(r"\s*\|\s*", " ", sub).strip()
            # ']' perdido de todo ('[ExampleName Босс кто...'): numa mensagem
            # nova o nome é a 1.ª palavra (nomes não têm espaços).
            if not re.match(r"^\[[^\[\]]{1,40}\]", sub):
                sub = re.sub(r"^\[([^\]\s]{2,30})\s+", r"[\1] ", sub,
                             count=1)
            channel = None
            if tag:
                channel = "world" if numbered else \
                    _TAG_TO_CHANNEL.get(tag.strip().lower())
            elif numbered:
                channel = "world"
            m = re.match(r"^\[([^\]]{1,40})\]\s*(.*)$", sub)
            # 4.º campo: mensagem confirmada pela posição (filtro de lixo
            # mais brando: '))) спс не надо (+12)' é mesmo uma mensagem).
            if m:
                messages.append([m.group(1).strip(), m.group(2), channel,
                                 True])
            elif sub:
                messages.append([None, sub, channel, True])
            continue
        s = split_merged_lines(s)
        for sub in s.splitlines():
            sub = sub.strip()
            if not sub:
                continue
            # A etiqueta primeiro: '1 Server [x]' tem um nº que o filtro de
            # tempos ('1 s') podia comer.
            sub, numbered = normalize_tag(sub)
            sub = remove_time_noise(sub)
            sub = re.sub(r"(?<=\s)\|(?=\s)", "I", sub)   # 'yes | did'
            sub = re.sub(r"[©®™|¦→←↑↓•◆★♥]+", " ", sub)
            sub = re.sub(r"\s+", " ", sub).strip()
            had_tab = bool(TAB_TAG_RE.match(sub))
            channel = None
            if had_tab:
                tag = re.match(rf"^({TAB_PREFIXES})", sub).group(1).lower()
                # Com nº de servidor à frente é o chat World (multi-servidor).
                channel = "world" if numbered else _TAG_TO_CHANNEL.get(tag)
            sub = strip_tab_prefix(sub)
            if not sub:
                continue
            # A anterior deixou um item por fechar ('[Kallon Catalyst' /
            # '(Bound)] 30 dias'): é continuação, não um '[Nome]' novo.
            if (not had_tab and messages
                    and messages[-1][1].count("[") > messages[-1][1].count("]")):
                messages[-1][1] += " " + sub
                continue
            sub = fix_bracket(sub)
            m = re.match(r"^\[([^\]]{1,40})\]\s*(.*)$", sub)
            # '(Bound).' sozinho na linha é o fim do nome de um item da
            # anterior, não um '[Nome]' sem mensagem.
            if (m and not had_tab and messages
                    and not re.search(r"\w", m.group(2))):
                messages[-1][1] += " " + sub
                continue
            if m:
                messages.append([m.group(1).strip(), m.group(2), channel])
            elif (not had_tab and messages
                  and not _TRAILING_GLOBE_RE.search(messages[-1][1])):
                # Se a anterior já acabou no 🌐 ('ok 2:') está
                # completa: isto é outra coisa (barra de ícones → 'mot.').
                messages[-1][1] += " " + sub
            else:
                messages.append([None, sub, channel])

    # 2) Limpa e filtra cada mensagem.
    out_lines = []
    prev_line = None
    for msg in messages:
        speaker, body, channel = msg[:3]
        sure = len(msg) > 3
        body = clean_body(body)
        if speaker is not None:
            if re.match(r"^\S{2,12}\s*:", speaker):
                channel = "whisper"     # '[Sender: X]' / '[Recipient: X]'
            speaker = whisper_speaker(speaker)
            if speaker is None:
                log().debug(f"OCR: whisper enviado por mim ignorado: "
                            f"{body[:60]!r}")
                continue
            speaker = _fix_speaker(speaker)
            if speaker.lower() in GENERIC_NAMES:
                continue
            sp_letters = re.sub(
                r"[\W\d_]", "", speaker)
            if len(sp_letters) < 2:
                continue
            body = _fix_digits(_fix_confusables(body))
            if not body:
                continue
            real_words = re.findall(
                r"[^\W\d_]{2,}", body)
            non_space = re.sub(r"\s", "", body)
            if not non_space:
                continue
            # Mensagens curtas tipo ':D', '90', 'ok' passam se forem
            # curtas; o lixo longo sem palavras não.
            if real_words:
                letters_count = sum(len(w) for w in real_words)
                if letters_count / len(non_space) < (0.3 if sure else 0.5):
                    continue
            elif len(non_space) > 4:
                continue
            weird = re.sub(
                r"[\w\s.,!?¿¡()\-'\"@:;/\[\]=+%*]",
                "", body)
            if len(weird) > len(body) * 0.25:
                continue
            line = f"[{speaker}] {body}"
            if line == prev_line:
                continue
            prev_line = line
            out_lines.append((channel, line))
            continue
        sub = _fix_confusables(body)
        # '[emote]' não é uma palavra: 'Фо of [emote]' (mundo do jogo)
        # passava por aviso do sistema.
        real_words = re.findall(
            r"[^\W\d_]{2,}", sub.replace(EMOTE_TOKEN, ""))
        if len(real_words) < 3:
            continue
        non_space = re.sub(r"\s", "", sub)
        letters_count = sum(len(w) for w in real_words)
        if not non_space or letters_count / len(non_space) < 0.6:
            continue
        if max((len(w) for w in real_words), default=0) < 3:
            continue
        if sub == prev_line:
            continue
        prev_line = sub
        out_lines.append((channel, sub))
    return out_lines


def filter_my_messages(text: str, my_name: str) -> str:
    """Remove linhas cujo speaker == my_name."""
    if not text or not my_name:
        return text
    target = _speaker_key(my_name)
    if not target:
        return text
    kept = []
    for line in text.splitlines():
        m = re.match(r"^\[([^\]]+)\]\s*", line)
        if m:
            sp = _speaker_key(m.group(1))
            if sp and sp == target:
                log().debug(f"OCR: mensagem própria ignorada: {line[:60]!r}")
                continue
        kept.append(line)
    return "\n".join(kept)


def _phonetic_name(n):
    """Forma 'como se diz' de um nome, para o comparar escrito noutro
    alfabeto: 'H1ro' / 'Hiro' / 'Хиро' (→ 'Khiro') → 'hiro'."""
    n = transliterate_cyrillic(n or "").lower()
    n = n.translate(str.maketrans("013457", "oieast"))
    n = re.sub(r"[^a-z]", "", n)
    n = n.replace("kh", "h").replace("y", "i").replace("ph", "f")
    return re.sub(r"(.)\1+", r"\1", n)          # 'Hirro' = 'Hiro'


def mentions_name(line, my_name):
    """A mensagem fala de mim / para mim? O meu nome no TEXTO da
    mensagem (não no nome de quem fala), tolerante ao OCR ('H1ro' =
    'Hiro' = 'HIRO') e escrito em cirílico ('Хиро' → 'Khiro' ~ 'Hiro')."""
    if not line or not my_name:
        return False
    target = _speaker_key(my_name)
    if len(target) < 3:
        return False
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line)
    if m and _speaker_key(m.group(1)) == target:
        return False                    # sou eu a falar
    body = m.group(2) if m else line
    phon = _phonetic_name(my_name)
    for word in re.findall(r"[\wЀ-ӿ]+", body):
        if len(phon) >= 3 and _phonetic_name(word) == phon:
            return True
        for w in {word, transliterate_cyrillic(word)}:
            k = _speaker_key(w)
            if not k:
                continue
            if k == target or (len(target) >= 4 and len(k) >= 4
                               and abs(len(k) - len(target)) <= 1
                               and _similar(k, target) >= 0.85):
                return True
            # 'Hiro' colado a outra coisa ('@Hiro', 'Hiroo', 'hiro!')
            if len(target) >= 4 and k.startswith(target) \
                    and len(k) - len(target) <= 2:
                return True
    return False


# ==================================================================
# CONFIG
# ==================================================================
@dataclass
class AppConfig:
    mode: str
    cloud_provider: str
    model: str
    api_key: str
    gpu_layers: int
    num_parallel: int
    keep_alive: str
    ocr_source: str
    ocr_target: str
    voice_source: str
    voice_target: str
    voice_hotkey: str
    tts_enabled: bool
    tts_voice: str
    tts_output_device: str
    mic_device_index: int
    my_name: str = ""
    appearance_style: dict = field(default_factory=dict)
    # Som quando alguém escreve o meu nome no chat (falam comigo/de mim).
    mention_sound: bool = False
    mention_tone: str = "ding"      # chave de MENTION_SOUNDS
    mention_repeat: int = 1         # quantas vezes toca o som
    # O alerta volta a tocar de X em X s durante Y s (Y=0: só 1 vez).
    mention_every: int = 10
    mention_during: int = 30
    # Frase que a voz diz depois do som ('' = nenhuma); {name} = quem
    # escreveu o teu nome.
    mention_text: str = ""
    # 'hold' = push-to-talk: grava enquanto o atalho está carregado
    # 'auto' = um toque: ouve até uma pausa longa (bip no fim)
    # 'continuous' = um toque liga, outro toque desliga; envia cada frase
    #                numa pausa longa
    voice_mode: str = "hold"
    # Voz → chat: False = escreve e carrega no Enter; True = escreve e
    # espera que confirmes (✔ Enviar no overlay ou o atalho outra vez).
    voice_confirm: bool = False
    # Voz que lê o chat: velocidade (%) e tom (Hz) do edge-tts.
    tts_rate: int = 0
    tts_pitch: int = 0
    # Tecla que cancela o ditado a meio (ouvir/traduzir/escrever). Só é
    # 'engolida' enquanto há um ditado; fora disso chega ao jogo.
    cancel_hotkey: str = "esc"
    # Nome do micro ('MME: Microfone (2- USB Mic)'): os índices do PyAudio
    # mudam sempre que se religa um USB; o nome não.
    mic_device_name: str = ""
    # Uma chave por IA na nuvem ({'OpenAI (ChatGPT)': 'sk-...'}): mudar
    # de fornecedor já não apaga a chave do outro.
    api_keys: dict = field(default_factory=dict)
    # Último modelo escolhido em cada fornecedor (voz e plano B usam-no).
    cloud_models: dict = field(default_factory=dict)
    # IA só para a voz: '' = a mesma do chat; senão um fornecedor na
    # nuvem (ex.: chat no Ollama local, voz no DeepSeek).
    voice_provider: str = ""
    voice_model: str = ""
    # mode 'mt' (tradutor sem IA): 'google' ou 'argos' (ver MT_ENGINES).
    mt_engine: str = ""
    # IA na nuvem falhou (sem saldo, limite, em baixo): tenta as outras
    # que têm chave.
    cloud_fallback: bool = True
    # 'Personalizado (OpenAI-compatível)': ex. http://localhost:1234/v1
    custom_base_url: str = ""
    # Limite de contexto em tokens (0 = automático). Modelos grátis têm
    # contextos pequenos: pedir demais dá erro ('maximum context length').
    max_context: int = 0
    # URL de cada servidor personalizado ({'Personalizado 2 (...)':
    # 'https://...'}); o 1.º também fica em custom_base_url (configs antigas).
    custom_urls: dict = field(default_factory=dict)
    # Nome que deste a cada servidor próprio (ex.: 'SambaNova').
    custom_names: dict = field(default_factory=dict)
    # Leituras do chat por minuto (capturas do jogo + OCR). Menos = menos
    # CPU; mais = mensagens aparecem mais depressa.
    ocr_per_min: int = 20
    # Modelos que 'pensam' antes de responder (todos os grátis do
    # OpenRouter): False = pede a resposta direta — o Nemotron 120B passa
    # de ~9 s para ~1 s por lote. Para traduzir chat não faz falta.
    ai_reasoning: bool = False
    # Opções do modelo de cada IA (ver AI_OPT_DEFAULTS): a do chat e a da
    # voz (esta só conta se a voz usar outra IA).
    ai_opts: dict = field(default_factory=dict)
    voice_opts: dict = field(default_factory=dict)
    # Zona do chat calibrada à mão ([x1, y1, x2, y2] em fracções da altura
    # do jogo; [] = nunca calibrada) e se se usa (False = automática, mas
    # a calibração fica guardada).
    chat_region: list = field(default_factory=list)
    chat_region_on: bool = True
    # Modo contínuo: a voz continua a ler o chat entre as tuas frases (com
    # auscultadores). Desligado = calada enquanto o contínuo está ligado.
    continuous_tts: bool = True


# Opções de um modelo. 'tested' = valores testados com esta app.
AI_OPT_DEFAULTS = {
    "temperature": "tested",    # 'tested' | 'model' (a do modelo) | '0.3'
    "reasoning": "off",         # 'off' (rápido) | 'model' | 'on'
    "context": 0,               # tokens de contexto (0 = automático)
    "max_output": 0,            # tokens da resposta (0 = automático)
    "batch_lines": 8,           # linhas do chat por pedido (nuvem)
    "rpm": 0,                   # pedidos por minuto (0 = automático)
    "free_only": False,         # só modelos grátis (lista e uso)
}
TESTED_TEMPERATURE = {"local": 0.1, "cloud": 0.2}


def ai_opt(cfg, key):
    """Opção do modelo desta config (com compatibilidade: as configs
    antigas tinham max_context e ai_reasoning globais)."""
    opts = getattr(cfg, "ai_opts", None) or {}
    v = opts.get(key)
    if v not in (None, ""):
        return v
    if key == "context":
        return int(getattr(cfg, "max_context", 0) or 0)
    if key == "reasoning":
        return "on" if getattr(cfg, "ai_reasoning", False) else "off"
    return AI_OPT_DEFAULTS[key]


def ai_temperature(cfg):
    """Temperatura a pedir, ou None = a do modelo (não se envia)."""
    t = str(ai_opt(cfg, "temperature"))
    if t == "model":
        return None
    if t == "tested":
        return TESTED_TEMPERATURE["local" if cfg.mode == "local"
                                  else "cloud"]
    try:
        return max(0.0, min(2.0, float(t)))
    except ValueError:
        return TESTED_TEMPERATURE["cloud"]


# Nomes antigos dos fornecedores (configs guardadas antes).
_PROVIDER_ALIASES = {"OpenAI": "OpenAI (ChatGPT)",
                     "OpenRouter": "OpenRouter (vários)"}


def normalize_provider(name):
    return _PROVIDER_ALIASES.get(name or "", name or "")


def migrate_config_dict(valid):
    """Configs antigas: 1 só api_key → api_keys[fornecedor]. Decifra as
    chaves guardadas (DPAPI); as antigas em texto passam a cifradas na
    próxima gravação."""
    valid["api_key"] = decrypt_secret(valid.get("api_key") or "")
    valid["api_keys"] = {k: decrypt_secret(v) for k, v in
                         (valid.get("api_keys") or {}).items()}
    prov = normalize_provider(valid.get("cloud_provider", ""))
    if prov:
        valid["cloud_provider"] = prov
    keys = dict(valid.get("api_keys") or {})
    for old, new in _PROVIDER_ALIASES.items():
        if old in keys and new not in keys:
            keys[new] = keys.pop(old)
    if valid.get("api_key") and prov and not keys.get(prov):
        keys[prov] = valid["api_key"]
    valid["api_keys"] = keys
    urls = dict(valid.get("custom_urls") or {})
    if valid.get("custom_base_url"):
        urls.setdefault("Personalizado (OpenAI-compatível)",
                        valid["custom_base_url"])
    valid["custom_urls"] = urls
    # Opções globais antigas → opções de cada IA.
    for k in ("ai_opts", "voice_opts"):
        opts = dict(valid.get(k) or {})
        if valid.get("max_context") and "context" not in opts:
            opts["context"] = int(valid["max_context"])
        if valid.get("ai_reasoning") and "reasoning" not in opts:
            opts["reasoning"] = "on"
        valid[k] = opts
    return valid


def provider_key(cfg, provider):
    provider = normalize_provider(provider)
    k = (getattr(cfg, "api_keys", None) or {}).get(provider) or ""
    if not k and provider == normalize_provider(cfg.cloud_provider):
        k = cfg.api_key or ""
    return k.strip()


def is_custom_provider(provider):
    """Servidor próprio (URL escrito por ti, não um fornecedor fixo)."""
    conf = CLOUD_PROVIDERS.get(normalize_provider(provider))
    return bool(conf) and not conf.get("base_url")


def provider_base_url(cfg, provider):
    """URL do servidor de um fornecedor personalizado ('' nos outros)."""
    provider = normalize_provider(provider)
    url = (getattr(cfg, "custom_urls", None) or {}).get(provider) or ""
    if not url and provider == "Personalizado (OpenAI-compatível)":
        url = getattr(cfg, "custom_base_url", "") or ""
    return url.strip()


# Nome que deste a cada servidor próprio ({'Personalizado (...)':
# 'SambaNova'}); vem da config (custom_names).
_CUSTOM_NAMES = {}


def set_custom_names(names):
    _CUSTOM_NAMES.clear()
    _CUSTOM_NAMES.update({k: v.strip() for k, v in (names or {}).items()
                          if v and v.strip()})


def provider_label(provider):
    """Nome a mostrar (os personalizados na língua da interface, ou o
    nome que lhes deste)."""
    provider = normalize_provider(provider)
    if _CUSTOM_NAMES.get(provider):
        return _CUSTOM_NAMES[provider]
    if provider == "Personalizado (OpenAI-compatível)":
        return T("Custom server 1 (OpenAI-compatible)")
    if provider == "Personalizado 2 (OpenAI-compatível)":
        return T("Custom server 2 (OpenAI-compatible)")
    if provider == "Groq (rápido)":
        return f"Groq ({T('fast')})"
    if provider == "OpenRouter (vários)":
        return f"OpenRouter ({T('many models')})"
    return provider


# Modelos que a TUA conta recusou (bloqueados nas definições, sem saldo):
# não se voltam a usar (nem como plano B) e aparecem com ⛔ na lista.
_BLOCKED = {}           # (fornecedor, modelo) → motivo


def _blocked_path():
    return os.path.join(os.path.dirname(os.path.abspath(
        get_last_config_path())), "ui_cache", "blocked_models.json")


def _load_blocked():
    try:
        with open(_blocked_path(), encoding="utf-8") as f:
            for k, v in json.load(f).items():
                prov, _, model = k.partition("|")
                _BLOCKED[(prov, model)] = v
    except Exception:
        pass


def mark_blocked(provider, model, reason):
    key = (normalize_provider(provider), model_id(model))
    if _BLOCKED.get(key) == reason:
        return
    _BLOCKED[key] = reason
    log().warning(f"Modelo recusado pela conta: {key[0]}/{key[1]} — "
                  f"{reason}")
    try:
        os.makedirs(os.path.dirname(_blocked_path()), exist_ok=True)
        with open(_blocked_path(), "w", encoding="utf-8") as f:
            json.dump({f"{p}|{m}": r for (p, m), r in _BLOCKED.items()}, f,
                      ensure_ascii=False)
    except Exception:
        pass


def unmark_blocked(provider, model):
    """Voltou a funcionar (desbloqueaste-o): tira a marca."""
    key = (normalize_provider(provider), model_id(model))
    if _BLOCKED.pop(key, None) is not None:
        try:
            with open(_blocked_path(), "w", encoding="utf-8") as f:
                json.dump({f"{p}|{m}": r for (p, m), r in _BLOCKED.items()},
                          f, ensure_ascii=False)
        except Exception:
            pass


def is_blocked(provider, model):
    return (normalize_provider(provider), model_id(model)) in _BLOCKED


# Etiqueta de cada modelo que o fornecedor listou (com preço ou 🆓):
# assim um nome escrito à mão ('qwen/qwen3.8-27b') sabe o preço.
_MODEL_LABELS = {}


def _plan_free(provider, mid):
    """Pelo plano do fornecedor, um modelo SEM preço indicado é grátis?
    (Groq/Mistral: True; Gemini: só flash/gemma.)"""
    fp = (CLOUD_PROVIDERS.get(normalize_provider(provider)) or {}) \
        .get("free_plan")
    if isinstance(fp, str):
        return bool(re.search(fp, mid, re.I))
    return fp is True


def is_free_model(provider, label, base_url=""):
    """O modelo é grátis? Manda o preço que o fornecedor indicou (lista
    de modelos): 🆓/preço 0/':free' = grátis, '$' = pago. Sem preço
    conhecido: só os do Gemini Flash (plano grátis) — na dúvida NÃO é
    grátis, para 'Só grátis' nunca deixar passar um pago. Local: grátis."""
    if not provider or provider == "local":
        return True
    label = label or ""
    if _LABEL_SEP not in label:
        label = _MODEL_LABELS.get((normalize_provider(provider),
                                   model_id(label)), label)
    mid = model_id(label).lower()
    if mid.endswith(":free") or mid == "openrouter/free":
        return True
    if is_openrouter(provider, base_url):
        # No OpenRouter só os ':free' entram na quota grátis: os de preço
        # 0 sem ':free' (ex.: 'ling-3.1-flash') pedem saldo na chave.
        return False
    if "🆓" in label:
        return True
    if _LABEL_SEP in label:
        return "$" not in label.split(_LABEL_SEP, 1)[1] and \
            not is_openrouter(provider, base_url)
    fp = (CLOUD_PROVIDERS.get(normalize_provider(provider)) or {}) \
        .get("free_plan")
    return isinstance(fp, str) and _plan_free(provider, model_id(label))


_load_blocked()


def card_note(provider):
    """Aviso sobre o cartão para chegar aos modelos grátis desta IA."""
    provider = normalize_provider(provider)
    card = (CLOUD_PROVIDERS.get(provider) or {}).get("card")
    if provider.startswith("Groq"):
        return T("🆓 Free without a card. With a card on the account, the "
                 "models with a price are billed.")
    return {"no": T("🆓 Has free models without a card."),
            "deposit": T("💳 Has free models, but asks for a card / a small "
                         "deposit when you sign up."),
            "yes": T("💳 Needs a card: only trial credits, no permanent "
                     "free models."),
            "paid": T("💳 Paid AI: needs a card and credit (no free "
                      "models)."),
            }.get(card, "")


def is_openrouter(provider, base_url=""):
    return (normalize_provider(provider).startswith("OpenRouter")
            or "openrouter.ai" in (base_url or "").lower())


def provider_ready(cfg, provider):
    """Há o que é preciso para usar esta IA (chave, ou URL no
    personalizado)?"""
    conf = CLOUD_PROVIDERS.get(normalize_provider(provider))
    if not conf:
        return False
    if not conf.get("needs_key", True):
        return bool(provider_base_url(cfg, provider))
    return bool(provider_key(cfg, provider))


def provider_model(cfg, provider):
    provider = normalize_provider(provider)
    m = (getattr(cfg, "cloud_models", None) or {}).get(provider)
    if m:
        return m
    if cfg.mode != "local" and provider == normalize_provider(
            cfg.cloud_provider) and cfg.model:
        return cfg.model
    models = (CLOUD_PROVIDERS.get(provider) or {}).get("models") or []
    return models[0] if models else ""


def voice_config(cfg):
    """Config para a IA da voz, ou None se a voz usa a mesma do chat.
    voice_provider 'local' = Ollama neste PC (ex.: chat na nuvem, voz
    local). Com o chat também local: o mesmo modelo (só 1 na VRAM, o jogo
    precisa dela), a não ser que escolhas outro para a voz — aí ficam os
    dois carregados (a app relança o Ollama para aceitar 2)."""
    vp = normalize_provider(getattr(cfg, "voice_provider", "") or "")
    from dataclasses import replace
    if is_mt_provider(vp):
        if cfg.mode == "mt" and getattr(cfg, "mt_engine", "") == vp:
            return None                 # = o mesmo tradutor do chat
        return replace(cfg, mode="mt", mt_engine=vp)
    if vp == "local":
        model = getattr(cfg, "voice_model", "")
        if cfg.mode == "local" and (not model or model == cfg.model):
            return None                 # = a mesma IA do chat
        return replace(cfg, mode="local", model=model,
                       ai_opts=dict(getattr(cfg, "voice_opts", None) or {})
                       ) if model else None
    if not vp or vp not in CLOUD_PROVIDERS:
        return None
    return replace(cfg, mode="cloud", cloud_provider=vp,
                   model=getattr(cfg, "voice_model", "")
                   or provider_model(cfg, vp),
                   ai_opts=dict(getattr(cfg, "voice_opts", None) or {}))


# ------------------------------------------------------------------
# Perfis de modelos: IA + modelo + opções, para pôr no chat ou na voz
# com um clique. Os '⭐' vêm com a app; os teus ficam em
# model_profiles.json (sem chaves — essas ficam nas 'Chaves das IAs').
# ------------------------------------------------------------------
MODEL_PRESETS = {
    "⭐ OpenRouter · Ling 3.0 Flash (free)": {
        "mode": "cloud", "provider": "OpenRouter (vários)",
        "model": "inclusionai/ling-3.0-flash-sante:free",
        "opts": {"temperature": "tested", "reasoning": "off",
                 "batch_lines": 8},
        "note": "tested"},
    "⭐ OpenRouter · Nemotron 3 Super 120B (free)": {
        "mode": "cloud", "provider": "OpenRouter (vários)",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "opts": {"temperature": "tested", "reasoning": "off",
                 "batch_lines": 8},
        "note": "tested"},
    "⭐ Mistral · Small (free plan)": {
        "mode": "cloud", "provider": "Mistral AI",
        "model": "mistral-small-latest",
        "opts": {"temperature": "tested", "reasoning": "model",
                 "batch_lines": 6},
        "note": "free"},
    "⭐ Google Gemini · Flash-Lite (free plan)": {
        "mode": "cloud", "provider": "Google Gemini",
        "model": "gemini-flash-lite-latest",
        "opts": {"temperature": "tested", "reasoning": "off",
                 "batch_lines": 8},
        "note": "free"},
    "⭐ Groq · ALLaM 2 7B (free)": {
        "mode": "cloud", "provider": "Groq (rápido)",
        "model": "allam-2-7b",
        "opts": {"temperature": "tested", "reasoning": "off",
                 "batch_lines": 6},
        "note": "tested"},
    "⭐ NVIDIA · DeepSeek V4.1 Flash (free)": {
        "mode": "cloud", "provider": "NVIDIA (build.nvidia.com)",
        "model": "deepseek-ai/deepseek-v4.1-flash",
        "opts": {"temperature": "tested", "reasoning": "off",
                 "batch_lines": 8, "rpm": 30},
        "note": "free"},
}


def model_profiles_path():
    return os.path.join(os.path.dirname(os.path.abspath(
        get_last_config_path())), "model_profiles.json")


def load_model_profiles(with_presets=True):
    """{nome: {'mode', 'provider', 'model', 'opts'}} — os ⭐ primeiro."""
    out = dict(MODEL_PRESETS) if with_presets else {}
    try:
        with open(model_profiles_path(), encoding="utf-8") as f:
            mine = json.load(f)
        for name, d in (mine or {}).items():
            if isinstance(d, dict) and name not in MODEL_PRESETS:
                out[name] = d
    except FileNotFoundError:
        pass
    except Exception:
        log().exception("Falha a ler model_profiles.json")
    return out


def save_model_profile(name, data):
    name = (name or "").strip()[:60]
    if not name or name in MODEL_PRESETS:
        return False
    mine = load_model_profiles(with_presets=False)
    mine[name] = {k: data.get(k) for k in ("mode", "provider", "model",
                                            "opts")}
    try:
        with open(model_profiles_path(), "w", encoding="utf-8") as f:
            json.dump(mine, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        log().exception("Falha a guardar perfil de modelo")
        return False


def delete_model_profile(name):
    if name in MODEL_PRESETS:
        return False
    mine = load_model_profiles(with_presets=False)
    if mine.pop(name, None) is None:
        return False
    try:
        with open(model_profiles_path(), "w", encoding="utf-8") as f:
            json.dump(mine, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        log().exception("Falha a apagar perfil de modelo")
        return False


class CloudError(requests.exceptions.HTTPError):
    """Erro de uma IA na nuvem, já em texto legível ('chave inválida')."""
    status = None
    daily_limit = False     # quota diária gasta (não vale a pena insistir)


def _cloud_error(provider, r):
    msg = ""
    try:
        j = r.json()
        e = j.get("error", j) if isinstance(j, dict) else j
        if isinstance(e, list) and e:
            e = e[0]
        msg = e.get("message", "") if isinstance(e, dict) else str(e)
        # OpenRouter: 'Provider returned error' + o motivo real em
        # metadata.raw ('... is temporarily rate-limited upstream').
        raw = ((e.get("metadata") or {}).get("raw")
               if isinstance(e, dict) else None)
        if isinstance(raw, str) and raw.strip():
            msg = raw.strip()
    except Exception:
        msg = (r.text or "")[:200]
    hint = {401: T("invalid key"), 402: T("no credit"),
            403: T("no access"), 404: T("model does not exist"),
            429: T("rate limit or credit used up")
            }.get(r.status_code, T("server down")
                  if r.status_code >= 500 else "")
    if not hint and r.status_code in (400, 403) \
            and re.search(r"api.?key|auth", msg, re.I):
        hint = T("invalid key")         # Gemini e xAI respondem 400
    if not hint and r.status_code in (400, 413, 422) and re.search(
            r"context|too long|too large|max_tokens|maximum.*tokens",
            msg, re.I):
        hint = T("too much text for this model")
    if r.status_code == 429 and re.search(r"per.?day|daily", msg, re.I):
        # OpenRouter sem créditos: 50 pedidos/dia aos modelos ':free'.
        hint = T("daily limit of free requests used up — it resets at "
                 "00:00 UTC; with 10 credits on OpenRouter it becomes "
                 "1000/day")
    text = (T("{p}: error {code}", p=provider_label(provider),
              code=r.status_code)
            + (f" ({hint})" if hint else "")
            + (f" — {msg.strip()[:160]}" if msg.strip() else ""))
    err = CloudError(text, response=r)
    err.status = r.status_code
    err.daily_limit = (r.status_code == 429
                       and bool(re.search(r"per.?day|daily", msg, re.I)))
    return err


def _custom_url(base, path):
    base = (base or "").strip().rstrip("/")
    if not base:
        raise ValueError(T("Custom: the server URL is missing"))
    if base.endswith("/chat/completions"):
        base = base[:-len("/chat/completions")]
    return f"{base}/{path}"


def _auth_headers(kind, key):
    if kind == "anthropic":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    if kind == "gemini":
        # No cabeçalho, não no URL: o URL aparece nos erros e no log.
        return {"x-goog-api-key": key}
    return {"Authorization": f"Bearer {key}"} if key else {}


# Contexto de cada modelo (o OpenRouter diz-o na lista de modelos).
_MODEL_CTX = {}
DEFAULT_CLOUD_CTX = 8192


def context_for(cfg, model=""):
    """Tokens de contexto a respeitar para este modelo."""
    lim = int(ai_opt(cfg, "context") or 0)
    if lim > 0:
        return lim
    known = _MODEL_CTX.get(model_id(model))
    return known or (4096 if cfg.mode == "local" else DEFAULT_CLOUD_CTX)


def output_tokens(ctx, cfg=None):
    """Resposta máxima: uma tradução é curta; o resto fica para o pedido.
    Com cfg, respeita a opção 'Resposta máx.' do modelo."""
    if cfg is not None:
        n = int(ai_opt(cfg, "max_output") or 0)
        if n > 0:
            return min(n, max(64, ctx // 2))
    return int(min(1024, max(128, ctx // 4)))


def fit_to_context(text, sysp, ctx):
    """Corta o texto se não couber (≈2,5 caracteres por token — o russo
    gasta mais tokens que o inglês). Rede de segurança: os lotes do chat
    já são feitos para caber."""
    budget = ctx - output_tokens(ctx) - int(len(sysp) / 2.5) - 32
    max_chars = max(200, int(budget * 2.5))
    if len(text) <= max_chars:
        return text
    log().warning(f"Texto ({len(text)} chars) maior que o contexto "
                  f"({ctx} tokens) — cortado a {max_chars}")
    cut = text[:max_chars]
    return cut[:cut.rfind("\n")] if "\n" in cut else cut


def is_context_error(e):
    """Erro de 'pedido grande demais para este modelo'?"""
    msg = str(e).lower()
    return (getattr(e, "status", None) in (400, 413, 422)
            and any(w in msg for w in ("context", "token", "too long",
                                       "too large", "length", "max_tokens")))


# Modelos que recusaram o pedido de 'pensar'/'não pensar': não se envia
# outra vez (cada recusa custava um pedido a mais).
_NO_REASONING_PARAM = set()


def _reasoning_fields(kind, provider, url, model, mode):
    """Campos do pedido para ligar/desligar o 'pensar' (raciocínio) de
    cada fornecedor. mode: 'off' | 'on' | 'model' (não mexe)."""
    if mode not in ("off", "on") or (provider, model) in _NO_REASONING_PARAM:
        return {}
    off, m = mode == "off", model.lower()
    if kind == "gemini":
        if "gemini-3" in m:
            return {"thinkingLevel": "low" if off else "high"}
        if "2.5" in m or "flash" in m or "pro" in m:
            return {"thinkingBudget": 0 if off else -1}
        return {}
    if kind == "ollama":
        return {"think": not off}
    if kind != "openai":
        return {}           # Anthropic: só pensa se lho pedirem
    if is_openrouter(provider, url):
        return {"reasoning": {"enabled": not off}}
    if provider.startswith("OpenAI") and re.match(r"(gpt-5|o\d)", m):
        return {"reasoning_effort": "minimal" if off else "medium"}
    if provider.startswith("Groq"):
        if "gpt-oss" in m:
            return {"reasoning_effort": "low" if off else "medium"}
        if "qwen3" in m:
            return {"reasoning_effort": "none" if off else "default"}
    if provider.startswith("xAI") and "mini" in m:
        return {"reasoning_effort": "low" if off else "high"}
    return {}


def cloud_chat(provider, model, key, sysp, text, base_url="", timeout=60,
               max_out=None, reasoning="off", temperature=0.2):
    """Uma pergunta a uma IA na nuvem; devolve só o texto da resposta.
    max_out: limite de tokens da resposta (evita o erro de contexto nos
    modelos com pouco contexto, ex. muitos ':free').
    reasoning='off': pede aos modelos que 'pensam' a resposta direta (no
    OpenRouter o raciocínio gastava ~600 tokens e ~8 s por lote, e com um
    max_out pequeno a resposta podia vir vazia); 'model' = não mexe.
    temperature=None = a do modelo."""
    if reasoning is True or reasoning is False:     # chamadas antigas
        reasoning = "on" if reasoning else "off"
    provider = normalize_provider(provider)
    model = model_id(model)
    conf = CLOUD_PROVIDERS.get(provider)
    if not conf:
        raise ValueError(T("Unknown provider: {p}", p=provider))
    if not model:
        raise ValueError(T("{p}: choose a model", p=provider))
    kind = conf.get("kind", "openai")
    headers = {"Content-Type": "application/json", **_auth_headers(kind, key)}
    url = conf.get("base_url") or ""
    if kind == "openai" and not url:
        url = _custom_url(base_url, "chat/completions")
    think = _reasoning_fields(kind, provider, url, model, reasoning)
    if kind == "anthropic":
        payload = {"model": model, "max_tokens": max_out or 1024,
                   "system": sysp,
                   "messages": [{"role": "user", "content": text}]}
        if temperature is not None:
            payload["temperature"] = temperature
    elif kind == "gemini":
        url = url.format(model=model)
        gen = {}
        if temperature is not None:
            gen["temperature"] = temperature
        if max_out:
            gen["maxOutputTokens"] = max_out if not think or \
                think.get("thinkingBudget") == 0 else max(max_out, 4096)
        if think:
            gen["thinkingConfig"] = think
        payload = {"systemInstruction": {"parts": [{"text": sysp}]},
                   "contents": [{"role": "user", "parts": [{"text": text}]}],
                   "generationConfig": gen}
    elif kind == "ollama":
        payload = {"model": model, "stream": False, "options": {},
                   "messages": [{"role": "system", "content": sysp},
                                {"role": "user", "content": text}]}
        if temperature is not None:
            payload["options"]["temperature"] = temperature
        payload.update(think)
    else:
        openrouter = is_openrouter(provider, url)
        if openrouter:
            headers["HTTP-Referer"] = "https://github.com/rf-translator"
            headers["X-Title"] = "RF Online Translator"
        payload = {"model": model,
                   "messages": [{"role": "system", "content": sysp},
                                {"role": "user", "content": text}]}
        if temperature is not None:
            payload["temperature"] = temperature
        # A OpenAI oficial tem contextos enormes e os modelos novos recusam
        # 'max_tokens'; nos outros o limite evita o erro de contexto.
        if max_out and not provider.startswith("OpenAI"):
            payload["max_tokens"] = max_out if reasoning != "on" \
                else max(max_out, 4096)
        payload.update(think)
    t0 = time.time()
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code == 400 and "temperature" in (r.text or "").lower():
        # Modelos que só aceitam a temperatura padrão (ex.: gpt-5).
        payload.pop("temperature", None)
        (payload.get("generationConfig") or {}).pop("temperature", None)
        (payload.get("options") or {}).pop("temperature", None)
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code == 400 and think and re.search(
            r"reason|think|budget|effort", r.text or "", re.I):
        # Modelo que não aceita mudar o 'pensar' (ex.: 'reasoning is
        # mandatory'): deixa-o como é, com espaço para pensar + responder.
        log().info(f"{provider}/{model}: não aceita mudar o 'pensar' — "
                   f"fica o do modelo")
        _NO_REASONING_PARAM.add((provider, model))
        for k in think:
            payload.pop(k, None)
        gen = payload.get("generationConfig") or {}
        gen.pop("thinkingConfig", None)
        if gen.get("maxOutputTokens"):
            gen["maxOutputTokens"] = max(4096, gen["maxOutputTokens"])
        if payload.get("max_tokens"):
            payload["max_tokens"] = max(4096, payload["max_tokens"])
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if not r.ok:
        raise _cloud_error(provider, r)
    data = r.json()
    log().debug(f"CLOUD[{provider}/{model}] ← {time.time()-t0:.2f}s")
    if kind == "anthropic":
        out = "".join(b.get("text", "") for b in data.get("content", [])
                      if b.get("type") == "text")
    elif kind == "gemini":
        parts = ((data.get("candidates") or [{}])[0].get("content") or {}) \
            .get("parts") or []
        out = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    elif kind == "ollama":
        out = (data.get("message") or {}).get("content") or ""
    else:
        out = ((data.get("choices") or [{}])[0].get("message") or {}) \
            .get("content") or ""
        if isinstance(out, list):
            out = "".join(p.get("text", "") for p in out
                          if isinstance(p, dict))
    # Modelos que 'pensam' em voz alta (<think>...</think>).
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.S | re.I)
    out = out.strip()
    if not out and (text or "").strip() and max_out and max_out < 4096:
        # Vazia porque o modelo gastou os tokens a pensar (os 'reasoning'
        # que não deixam desligar): mais uma vez, com espaço para pensar.
        log().info(f"{provider}/{model}: resposta vazia — repito com mais "
                   f"tokens")
        return cloud_chat(provider, model, key, sysp, text,
                          base_url=base_url, timeout=timeout, max_out=4096,
                          reasoning=reasoning, temperature=temperature)
    if not out and (text or "").strip():
        # Resposta vazia (ex.: o modelo gastou os tokens todos a pensar):
        # é um erro — senão a mensagem contava como traduzida e perdia-se.
        raise ValueError(T("{p}: the model gave an empty answer — try "
                           "another model", p=provider_label(provider)))
    return out


_NOT_CHAT_MODEL = re.compile(
    r"embed|whisper|tts|dall-e|image|audio|realtime|transcri|moderation|"
    r"rerank|guard|search|computer-use|codex|veo|imagen|aqa|learnlm|"
    r"lyria|music|safety|orpheus|playai", re.I)


def openrouter_key_info(key, timeout=15):
    """Estado da chave do OpenRouter, sem gastar pedidos: dict com
    'free_left', 'free_limit' (pedidos grátis que restam hoje), 'credit'
    (créditos que restam, None = sem limite) e 'free_tier'. Chave
    inválida → CloudError."""
    r = requests.get("https://openrouter.ai/api/v1/key",
                     headers=_auth_headers("openai", key), timeout=timeout)
    if not r.ok:
        raise _cloud_error("OpenRouter", r)
    d = r.json().get("data") or {}
    daily = d.get("free_model_daily_requests") or {}
    return {"free_left": daily.get("remaining"),
            "free_limit": daily.get("limit"),
            "credit": d.get("limit_remaining"),
            "free_tier": bool(d.get("is_free_tier"))}


def openrouter_quota_text(info):
    """'🆓 9/50 free requests left today' (ou '' se não se souber)."""
    left, lim = info.get("free_left"), info.get("free_limit")
    if left is None or not lim:
        return ""
    return T("🆓 {n}/{m} free requests left today", n=left, m=lim)


def list_cloud_models(provider, key, base_url="", timeout=15):
    """Modelos de chat que esta conta pode usar, pedidos ao fornecedor
    (sem gastar nada). Também serve para testar a chave."""
    provider = normalize_provider(provider)
    conf = CLOUD_PROVIDERS.get(provider) or {}
    kind = conf.get("kind", "openai")
    url = conf.get("models_url") or (
        _custom_url(base_url, "models") if not conf.get("base_url") else "")
    if not url:
        return list(conf.get("models") or [])
    r = requests.get(url, headers=_auth_headers(kind, key), timeout=timeout)
    if not r.ok:
        raise _cloud_error(provider, r)
    data = r.json()
    if kind == "gemini":
        names = [m.get("name", "").replace("models/", "")
                 for m in data.get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
    elif kind == "ollama":
        names = [m.get("name") or m.get("model") for m in data.get("models", [])]
    else:
        names = []
        for m in data.get("data", []):
            if m.get("id") and m.get("context_length"):
                try:
                    _MODEL_CTX[m["id"]] = int(m["context_length"])
                except (TypeError, ValueError):
                    pass
            names.append(_model_label(m))
    out = []
    for n in sorted({n for n in names
                     if n and not _NOT_CHAT_MODEL.search(model_id(n))},
                    key=str.lower):
        # Plano grátis do fornecedor (Groq, Mistral...) e o modelo sem
        # preço: marca-se como no OpenRouter (pesquisa 'free', cor verde).
        if _LABEL_SEP not in n and not is_openrouter(provider, base_url) \
                and _plan_free(provider, n):
            n = f"{n}{_LABEL_SEP}🆓 free plan"
        if is_openrouter(provider, base_url):
            mid = model_id(n)
            if mid == "openrouter/free":            # escolhe um ':free'
                n = f"{mid}{_LABEL_SEP}🆓 free"
            elif "🆓" in n and not mid.endswith(":free"):
                # Preço 0 mas sem ':free': o OpenRouter pede saldo na chave
                # ('Key limit exceeded') — não conta como grátis.
                n = f"{mid}{_LABEL_SEP}$0 · " + T("needs credit on the key")
        _MODEL_LABELS[(provider, model_id(n))] = n
        out.append(n)
    return out


# Etiqueta na lista: 'id  ·  🆓 free (grátis)' / 'id  ·  $0.15 / $0.60 por 1M'
# — escrever 'free' na pesquisa mostra os grátis. model_id() tira-a.
_LABEL_SEP = "  ·  "


def model_id(label):
    return (label or "").split(_LABEL_SEP)[0].strip()


def _model_label(m):
    mid = m.get("id")
    price = m.get("pricing") or {}     # OpenRouter: preço por token
    try:
        if "input" in price and "prompt" not in price:
            # Together: preço por 1M tokens ('input'/'output').
            p_in = float(price.get("input", "x")) / 1e6
            p_out = float(price.get("output", "x")) / 1e6
        else:
            p_in = float(price.get("prompt", "x"))
            p_out = float(price.get("completion", "x"))
    except (TypeError, ValueError):
        return mid
    if p_in < 0 or p_out < 0:           # -1 = preço variável (auto/router)
        return mid
    if p_in == 0 and p_out == 0:
        # 'free' fica sempre (procurar 'free' funciona em qualquer língua).
        word = T("free")
        return (f"{mid}{_LABEL_SEP}🆓 free"
                + (f" ({word})" if word != "free" else ""))
    return (f"{mid}{_LABEL_SEP}${p_in * 1e6:.2f} / ${p_out * 1e6:.2f} "
            + T("per 1M tokens"))


# ==================================================================
# AI ENGINE
# ==================================================================
# ==================================================================
# TRADUTORES SEM IA (mode 'mt')
# ==================================================================
# Google Tradutor (o endpoint do site, sem chave nem conta) e Argos
# (offline: modelos CTranslate2 de ~150 MB por par de línguas, corre no
# CPU). Sem IA: sem quotas, sem respostas tontas do modelo; em troca não
# corrige erros do OCR nem percebe tão bem o calão do jogo.
MT_ENGINES = {"google": "Google Translate", "argos": "Argos",
              "nllb": "NLLB"}


def is_mt_provider(p):
    return (p or "") in MT_ENGINES


def mt_label(p):
    return {"google": "🌐 " + T("Google Translate (no AI)"),
            "argos": "📦 " + T("Argos (offline, no AI)"),
            "nllb": "📦 " + T("NLLB (offline, ~630 MB)")}.get(p, p)


def _mt_code(lang):
    """'Russian' → 'ru'; None para 'Auto'/desconhecida."""
    code = (LANGUAGES.get(lang or "") or {}).get("stt")
    return code.split("-")[0] if code else None


def _mt_split(text):
    """[(prefixo '[Nome] ', corpo)] por linha: só o corpo se traduz."""
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"^(\[[^\]]+\]\s*)(.*)$", line)
        out.append((m.group(1), m.group(2)) if m else ("", line))
    return out


_google_blocked = {}         # endereço → até quando evitar (429)


def _google_translate(bodies, target, source=None):
    """Dois endereços grátis do Google: com pedidos a mais um responde 429
    durante uns minutos — passa para o outro e evita esse 5 min."""
    tl = _mt_code(target) or "en"
    if tl == "zh":
        tl = "zh-CN"
    sl = _mt_code(source) or "auto"
    todo = [b for b in bodies if b.strip()]

    def chrome():
        # Uma tradução por linha ('q' repetido): não junta nem parte linhas.
        r = requests.get("https://clients5.google.com/translate_a/t",
                         params={"client": "dict-chrome-ex", "sl": sl,
                                 "tl": tl, "q": todo}, timeout=15)
        r.raise_for_status()
        res = [x[0] if isinstance(x, list) else x for x in r.json()]
        if len(res) != len(todo):
            raise ValueError(T("Google: the answer has a different number "
                               "of lines"))
        return res

    def gtx():
        def one(q):
            r = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": sl, "tl": tl, "dt": "t",
                        "q": q}, timeout=15)
            r.raise_for_status()
            return "".join(s[0] for s in (r.json()[0] or []) if s and s[0])
        parts = one("\n".join(todo)).split("\n")
        return parts if len(parts) == len(todo) else [one(b) for b in todo]

    if not todo:
        return list(bodies)
    now, err = time.time(), None
    ways = [("chrome", chrome), ("gtx", gtx)]
    ways.sort(key=lambda w: _google_blocked.get(w[0], 0) > now)
    for name, fn in ways:
        try:
            res = iter(t.strip() for t in fn())
            return [next(res) if b.strip() else b for b in bodies]
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                _google_blocked[name] = now + 300
                log().warning(f"Google ({name}): 429 — a usar o outro")
            err = e
        except (requests.exceptions.RequestException, ValueError) as e:
            err = e
    if isinstance(err, requests.exceptions.RequestException):
        raise err
    raise requests.exceptions.RequestException(str(err))


def _mymemory_translate(bodies, target, source=None):
    """MyMemory (grátis, sem chave, ~5000 caracteres/dia por IP): plano B
    do Google. Precisa da língua de origem: a de cada linha."""
    tl = _mt_code(target) or "en"
    out = []
    for b in bodies:
        sl = _mt_code(source) or _mt_code(detect_lang(b)) or "en"
        if not b.strip() or sl == tl:
            out.append(b)
            continue
        r = requests.get("https://api.mymemory.translated.net/get",
                         params={"q": b, "langpair": f"{sl}|{tl}"},
                         timeout=15)
        r.raise_for_status()
        j = r.json()
        if j.get("quotaFinished") or int(j.get("responseStatus") or 200) \
                != 200:
            raise requests.exceptions.RequestException(
                "MyMemory: " + (j.get("responseDetails")
                                or T("daily limit reached")))
        out.append((j.get("responseData") or {}).get("translatedText") or b)
    return out


_mt_fallback_said = {}      # tradutor de reserva → quando se avisou


def _mt_fallback(name, err):
    """Avisa (no máx. de 10 em 10 min) que se passou para outro tradutor."""
    log().warning(f"Tradutor: a usar {name} ({err})")
    if time.time() - _mt_fallback_said.get(name, 0) > 600:
        _mt_fallback_said[name] = time.time()
        _argos_say(T("⚠️ Google is not answering — using {n} for now",
                     n=name))


_ARGOS_INDEX = ("https://raw.githubusercontent.com/argosopentech/"
                "argospm-index/main/index.json")
_argos_models = {}          # (de, para) → (Translator, SentencePiece)
_argos_lock = threading.Lock()
argos_status = None         # callable(str) → mensagens para o overlay


def argos_dir():
    return os.path.join(_app_dir(), "argos")


def argos_runtime_ok():
    try:
        import ctranslate2  # noqa: F401
        import sentencepiece  # noqa: F401
        return True
    except ImportError:
        return False


def _argos_say(text):
    log().info(f"Argos: {text}")
    if argos_status:
        try:
            argos_status(text)
        except Exception:
            pass


def _pip_env():
    try:
        from bootstrap import pip_env
        return pip_env()
    except Exception:
        return None


def argos_install_runtime():
    """ctranslate2 + sentencepiece (~20 MB) no Python da app (1.ª vez)."""
    if argos_runtime_ok():
        return True
    _argos_say(T("📦 Installing the offline translator (~20 MB)…"))
    import importlib
    import subprocess
    p = subprocess.run([sys.executable, "-m", "pip", "install",
                        "--no-cache-dir", "--disable-pip-version-check",
                        "ctranslate2", "sentencepiece"],
                       capture_output=True, text=True,
                       env=_pip_env(),
                       creationflags=getattr(subprocess,
                                             "CREATE_NO_WINDOW", 0))
    importlib.invalidate_caches()
    if p.returncode or not argos_runtime_ok():
        log().error(f"Argos: pip falhou: {p.stderr[-400:]}")
        raise RuntimeError(T("Could not install the offline translator"))
    return True


def _argos_model_path(src, tgt):
    base = os.path.join(argos_dir(), f"{src}_{tgt}")
    for root, dirs, files in os.walk(base):
        # Os pacotes OPUS-MT (ex.: es→en) trazem 'bpe.model' em vez de
        # 'sentencepiece.model': antes não eram reconhecidos e o modelo
        # (~150 MB) voltava a ser descarregado sempre que a app abria.
        if "model" in dirs and ("sentencepiece.model" in files
                                or "bpe.model" in files):
            return root
    return None


class _BPETokenizer:
    """Tokenizador dos pacotes Argos com 'bpe.model' (códigos BPE do
    subword-nmt, como o OPUS-MT): mesmo encode/decode que o
    SentencePiece usado no resto, sem dependências novas."""

    def __init__(self, path):
        self.ranks, self.cache = {}, {}
        with open(path, encoding="utf-8") as f:
            n = 0
            for line in f:
                if line.startswith("#version"):
                    continue
                a = line.rstrip("\r\n").split(" ")
                if len(a) == 2:
                    self.ranks.setdefault((a[0], a[1]), n)
                    n += 1

    def _word(self, word):
        if word in self.cache:
            return self.cache[word]
        w = list(word[:-1]) + [word[-1] + "</w>"]
        while len(w) > 1:
            r, i = min((self.ranks.get((w[i], w[i + 1]), 1 << 62), i)
                       for i in range(len(w) - 1))
            if r == 1 << 62:
                break
            a, b, nw, j = w[i], w[i + 1], [], 0
            while j < len(w):
                if j < len(w) - 1 and w[j] == a and w[j + 1] == b:
                    nw.append(a + b)
                    j += 2
                else:
                    nw.append(w[j])
                    j += 1
            w = nw
        if w[-1] == "</w>":
            w = w[:-1]
        elif w[-1].endswith("</w>"):
            w[-1] = w[-1][:-4]
        out = [s + "@@" for s in w[:-1]] + w[-1:]
        if len(self.cache) < 20000:
            self.cache[word] = out
        return out

    def encode(self, text, out_type=str):
        toks = re.findall(r"\w+|[^\w\s]", text)
        return [p for t in toks for p in self._word(t)]

    _MOSES = {"&apos;": "'", "&quot;": '"', "&amp;": "&", "&lt;": "<",
              "&gt;": ">", "&#91;": "[", "&#93;": "]", "&#124;": "|",
              "@-@": "-"}

    @classmethod
    def decode(cls, tokens):
        s = " ".join(tokens).replace("@@ ", "").replace("@@", "")
        for a, b in cls._MOSES.items():
            s = s.replace(f" {a} ", b) if a == "@-@" else s.replace(a, b)
        s = re.sub(r"\s+([.,!?;:%)\]}»])", r"\1", s)
        s = re.sub(r"([(\[{«¿¡])\s+", r"\1", s)
        return re.sub(r"\s*'\s*", "'", s).strip()


def argos_download(src, tgt):
    """Descarrega e extrai o modelo src→tgt (~150 MB). False se o Argos
    não tem esse par."""
    if _argos_model_path(src, tgt):
        return True
    idx = requests.get(_ARGOS_INDEX, timeout=30).json()
    pkg = next((p for p in idx if p.get("from_code") == src
                and p.get("to_code") == tgt and p.get("links")), None)
    if not pkg:
        return False
    _argos_say(T("📦 Downloading the offline model {a}→{b} (~150 MB)…",
                 a=src, b=tgt))
    os.makedirs(argos_dir(), exist_ok=True)
    tmp = os.path.join(argos_dir(), f"{src}_{tgt}.zip.part")
    with requests.get(pkg["links"][0], stream=True,
                      timeout=(30, 120)) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    import zipfile
    with zipfile.ZipFile(tmp) as z:
        z.extractall(os.path.join(argos_dir(), f"{src}_{tgt}"))
    os.remove(tmp)
    _argos_say(T("✅ Offline model {a}→{b} ready", a=src, b=tgt))
    return bool(_argos_model_path(src, tgt))


def _argos_pair(src, tgt):
    key = (src, tgt)
    if key in _argos_models:
        return _argos_models[key]
    with _argos_lock:
        if key in _argos_models:
            return _argos_models[key]
        argos_install_runtime()
        if not argos_download(src, tgt):
            _argos_models[key] = None
            return None
        import ctranslate2
        import sentencepiece as spm
        path = _argos_model_path(src, tgt)
        sp_file = os.path.join(path, "sentencepiece.model")
        bpe = not os.path.isfile(sp_file)
        tok = (_BPETokenizer(os.path.join(path, "bpe.model")) if bpe
               else spm.SentencePieceProcessor(model_file=sp_file))
        # Os OPUS-MT (bpe) em int8 só davam lixo repetido ('mainstremain…'):
        # ficam no tipo com que vêm.
        _argos_models[key] = (
            ctranslate2.Translator(os.path.join(path, "model"), device="cpu",
                                   compute_type="default" if bpe else "int8"),
            tok)
        return _argos_models[key]


def _ct2_sentences(texts, run):
    """Os modelos offline (Argos, NLLB) são de uma frase: com duas ('где
    босс? го в рейд') traduziam só a 1.ª. Parte em frases, traduz todas de
    uma vez (run: [frases] → [traduções]) e volta a juntar por linha."""
    pieces, owner = [], []
    for i, t in enumerate(texts):
        for s in re.split(r"(?<=[.!?…])\s+", t.strip()):
            if s:
                pieces.append(s)
                owner.append(i)
    out = [[] for _ in texts]
    for i, r in zip(owner, run(pieces) if pieces else []):
        # Alguns modelos devolvem peças que o decode não junta ('▁Onde▁
        # está') ou pontuação solta ('can 't', 'job .').
        r = re.sub(r"\s+", " ", r.replace("▁", " ")).strip()
        r = re.sub(r"\s+([.,!?;:)])", r"\1", r)
        r = re.sub(r"(\w) '(\w)", r"\1'\2", r)
        out[i].append(r)
    return [" ".join(o) for o in out]


def _argos_run(pair, texts):
    tr, sp = pair

    def run(pieces):
        res = tr.translate_batch([sp.encode(p, out_type=str)
                                  for p in pieces],
                                 beam_size=2, max_decoding_length=256)
        return [sp.decode(r.hypotheses[0]) for r in res]
    return _ct2_sentences(texts, run)


def _argos_translate(bodies, target, source=None):
    """Cada linha da sua língua (detect_lang); sem par direto passa pelo
    inglês (ru→pt = ru→en→pt)."""
    tgt = _mt_code(target) or "en"
    fixed = _mt_code(source)
    out = list(bodies)
    groups = {}
    for i, b in enumerate(bodies):
        src = fixed or _mt_code(detect_lang(b)) or "en"
        if b.strip() and src != tgt:
            groups.setdefault(src, []).append(i)
    for src, idxs in groups.items():
        texts = [bodies[i] for i in idxs]
        try:
            direct = _argos_pair(src, tgt)
            if direct:
                texts = _argos_run(direct, texts)
            else:
                for a, b in ((src, "en"), ("en", tgt)):
                    if a == b:
                        continue
                    pair = _argos_pair(a, b)
                    if not pair:
                        raise RuntimeError(T("Argos has no model {a}→{b}",
                                             a=a, b=b))
                    texts = _argos_run(pair, texts)
        except RuntimeError as e:
            # Só estas linhas ficam como estão: antes uma língua sem
            # modelo deixava o lote todo (6 mensagens) por traduzir.
            if _argos_missing.get(src) is None:
                _argos_missing[src] = time.time()
                _argos_say(f"⚠️ {e}")
            log().warning(f"Argos: {e} — {len(idxs)} linha(s) no original")
            continue
        for i, t in zip(idxs, texts):
            out[i] = t
    return out


_argos_missing = {}         # língua sem modelo → quando se avisou


# NLLB-200 (Meta), versão destilada 600M em CTranslate2 int8 (~630 MB):
# um só modelo para 200 línguas, sem pares nem passagem pelo inglês.
# Só se descarrega quando o escolhes.
NLLB_REPO = "JustFrederik/nllb-200-distilled-600M-ct2-int8"
NLLB_FILES = ("config.json", "shared_vocabulary.txt",
              "sentencepiece.bpe.model", "model.bin")
_NLLB_CODES = {"en": "eng_Latn", "pt": "por_Latn", "ru": "rus_Cyrl",
               "es": "spa_Latn", "fr": "fra_Latn", "de": "deu_Latn",
               "it": "ita_Latn", "ko": "kor_Hang", "ja": "jpn_Jpan",
               "zh": "zho_Hans", "tr": "tur_Latn", "pl": "pol_Latn"}
_nllb = None


def nllb_dir():
    return os.path.join(_app_dir(), "nllb")


def nllb_ready():
    return all(os.path.isfile(os.path.join(nllb_dir(), f))
               for f in NLLB_FILES)


def nllb_download():
    """~630 MB do Hugging Face (retoma se cortar a meio)."""
    if nllb_ready():
        return True
    argos_install_runtime()
    _argos_say(T("📦 Downloading the NLLB offline model (~630 MB)…"))
    from bootstrap import hf_download_gguf
    for f in NLLB_FILES:
        path, err = hf_download_gguf(NLLB_REPO, f, nllb_dir())
        if not path:
            raise RuntimeError(f"NLLB: {err}")
    _argos_say(T("✅ NLLB offline model ready"))
    return True


def _nllb_model():
    global _nllb
    with _argos_lock:
        if _nllb is None:
            nllb_download()
            import ctranslate2
            import sentencepiece as spm
            _nllb = (ctranslate2.Translator(nllb_dir(), device="cpu",
                                            compute_type="int8"),
                     spm.SentencePieceProcessor(model_file=os.path.join(
                         nllb_dir(), "sentencepiece.bpe.model")))
    return _nllb


def _nllb_translate(bodies, target, source=None):
    tr, sp = _nllb_model()
    tgt = _mt_code(target) or "en"
    fixed = _mt_code(source)
    out = list(bodies)
    groups = {}
    for i, b in enumerate(bodies):
        src = fixed or _mt_code(detect_lang(b)) or "en"
        if b.strip() and src != tgt:
            groups.setdefault(src, []).append(i)
    for src, idxs in groups.items():
        s_code = _NLLB_CODES.get(src, "eng_Latn")
        t_code = _NLLB_CODES.get(tgt, "eng_Latn")

        def run(pieces):
            res = tr.translate_batch(
                [[s_code] + sp.encode(p, out_type=str) + ["</s>"]
                 for p in pieces],
                target_prefix=[[t_code]] * len(pieces),
                beam_size=2, max_decoding_length=256)
            return [sp.decode(r.hypotheses[0][1:]) for r in res]
        for i, t in zip(idxs, _ct2_sentences([bodies[i] for i in idxs],
                                             run)):
            out[i] = t
    return out


def argos_prepare(sources, targets):
    """Prepara já (ao carregar em Iniciar) os modelos mais prováveis, para
    a 1.ª mensagem não ficar minutos à espera do download."""
    try:
        for s in sources:
            for t in targets:
                s_c, t_c = _mt_code(s), _mt_code(t)
                if s_c and t_c and s_c != t_c:
                    if not _argos_pair(s_c, t_c):
                        for a, b in ((s_c, "en"), ("en", t_c)):
                            if a != b:
                                _argos_pair(a, b)
    except Exception as e:
        log().exception("Argos: preparação falhou")
        _argos_say(f"⚠️ Argos: {e}")


def mt_translate(engine, text, target, source=None):
    """Traduz texto (uma ou várias linhas '[Nome] msg') sem IA; o '[Nome]'
    fica como está. Erros de rede saem como RequestException (a app
    trata-os como os da IA)."""
    lines = _mt_split(text)
    # '[emote]' sai antes de traduzir (o Argos apagava-o) e volta no fim.
    emotes = [b.count(EMOTE_TOKEN) for _, b in lines]
    bodies = [re.sub(r"\s+", " ", b.replace(EMOTE_TOKEN, " ")).strip()
              for _, b in lines]
    if not any(bodies):
        return text
    # Itens/locais '[...]' não se traduzem: o Google/NLLB trocavam-nos por
    # frases ('[+12 Prime ... Gun]' → 'What's going on?'). Só os bocados de
    # texto entre eles vão ao tradutor; os itens voltam ao mesmo sítio.
    # Cada bocado vai com a língua da LINHA inteira: sozinho ('vendo') o
    # detetor não acertava.
    groups = {}         # língua → ([bocados], [(linha, posição)])
    for i, b in enumerate(bodies):
        lang = source or detect_lang(_ITEM_RE.sub(" ", b))
        for k, part in enumerate(re.split(r"(\[[^\[\]]+\])", b)):
            if part.strip() and not part.startswith("[") \
                    and re.search(r"[^\W\d_]", part):
                g = groups.setdefault(lang, ([], []))
                g[0].append(part.strip())
                g[1].append((i, k))
    parts = [re.split(r"(\[[^\[\]]+\])", b) for b in bodies]
    for lang, (pieces, where) in groups.items():
        if engine == "argos":
            done = _argos_translate(pieces, target, lang)
        elif engine == "nllb":
            done = _nllb_translate(pieces, target, lang)
        else:
            # Google bloqueado (429) ou em baixo: MyMemory, depois o Argos
            # (offline; da 1.ª vez descarrega o que precisa).
            try:
                done = _google_translate(pieces, target, lang)
            except requests.exceptions.RequestException as e:
                try:
                    done = _mymemory_translate(pieces, target, lang)
                    _mt_fallback("MyMemory", e)
                except requests.exceptions.RequestException as e2:
                    _mt_fallback("Argos", e2)
                    done = _argos_translate(pieces, target, lang)
        for (i, k), t in zip(where, done):
            parts[i][k] = f" {t} "
    res = [fix_translation(b, re.sub(r"\s+", " ", "".join(p)).strip())
           for b, p in zip(bodies, parts)]
    return "\n".join(p + (r + f" {EMOTE_TOKEN}" * n).strip()
                     for (p, _), r, n in zip(lines, res, emotes))


class _VoiceFirst:
    """A tua voz passa à frente do chat na IA. O Ollama traduz um pedido
    de cada vez: numa rajada do chat (20 mensagens x 0,6-3 s) o ditado
    ficava à espera de todas. Enquanto há um ditado a traduzir, o chat
    não manda pedidos novos (no máx. o que já ia a meio)."""
    _cond = threading.Condition()
    _waiting = 0

    def __enter__(self):
        with self._cond:
            type(self)._waiting += 1
        return self

    def __exit__(self, *exc):
        with self._cond:
            type(self)._waiting -= 1
            self._cond.notify_all()

    @classmethod
    def wait(cls, timeout=30.0):
        """O chat espera aqui antes de cada pedido (no máx. `timeout`)."""
        end = time.time() + timeout
        with cls._cond:
            while cls._waiting > 0 and time.time() < end:
                cls._cond.wait(max(0.05, end - time.time()))


voice_first = _VoiceFirst


class AIEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        # Relança o Ollama se ele morrer a meio (main.py preenche). Sem
        # isto a app ficava muda até a reabrires.
        self.restart_backend = None
        self._restart_lock = threading.Lock()
        self._last_restart = 0.0

    def _try_restart(self):
        """True se o Ollama foi relançado (no máx. 1x por minuto)."""
        if self.restart_backend is None:
            return False
        with self._restart_lock:
            if time.time() - self._last_restart < 60:
                return False
            self._last_restart = time.time()
            log().warning("Ollama não responde — a relançar")
            try:
                return bool(self.restart_backend())
            except Exception:
                log().exception("Falha a relançar o Ollama")
                return False

    def input_budget_chars(self, sysp):
        """Caracteres que cabem num pedido (para fazer lotes do chat)."""
        ctx = context_for(self.cfg, self.cfg.model)
        return max(200, int((ctx - output_tokens(ctx, self.cfg)
                             - len(sysp) / 2.5 - 32) * 2.5))

    def translate(self, text, system_prompt, target=None):
        if self.cfg.mode == "mt":
            # Sem IA: o prompt não serve; a língua de destino é a do chat
            # (ou a que a voz pede).
            return mt_translate(getattr(self.cfg, "mt_engine", "google"),
                                text, target or self.cfg.ocr_target)
        try:
            text = fit_to_context(text, system_prompt,
                                  context_for(self.cfg, self.cfg.model))
            if self.cfg.mode == "local":
                return self._ollama(text, system_prompt)
            return self._cloud(text, system_prompt)
        except Exception:
            log().exception("AIEngine.translate falhou")
            raise

    def _ollama(self, text, sysp):
        # /api/chat aplica o template do modelo com papel 'system'; com
        # temperatura baixa os modelos pequenos inventam muito menos
        # (antes: lixo OCR → '"Hello there!"').
        payload = {"model": self.cfg.model,
                   "messages": [{"role": "system", "content": sysp},
                                {"role": "user", "content": text}],
                   "options": {},
                   "stream": False}
        temp = ai_temperature(self.cfg)
        if temp is not None:
            payload["options"]["temperature"] = temp
        # Modelos locais que 'pensam' (qwen3, deepseek-r1...): desligado
        # responde muito mais depressa. Os outros ignoram/recusam (fica
        # registado e não se volta a enviar).
        mode = str(ai_opt(self.cfg, "reasoning"))
        if mode in ("off", "on") and \
                ("local", self.cfg.model) not in _NO_REASONING_PARAM:
            payload["think"] = mode == "on"
        # Camadas na GPU (0 = só CPU). Antes ia numa variável de ambiente
        # que o Ollama ignora. Com o jogo a usar a placa a ~92%, o modelo
        # na GPU disputava-a com o jogo (quebras de FPS a cada tradução) e
        # nem era mais rápido: medido 4,7 s na GPU vs 4,6 s em 6 núcleos.
        gl = int(getattr(self.cfg, "gpu_layers", -1) if
                 getattr(self.cfg, "gpu_layers", -1) is not None else -1)
        if gl >= 0:
            payload["options"]["num_gpu"] = gl
        if gl == 0:
            # Metade dos núcleos: o resto fica para o jogo.
            payload["options"]["num_thread"] = max(2, (os.cpu_count() or 4) // 2)
        # Contexto menor = menos VRAM (cache do modelo). Só se o
        # escolheres; em 'Auto' fica o padrão do Ollama.
        ctx = int(ai_opt(self.cfg, "context") or 0)
        if ctx > 0:
            payload["options"]["num_ctx"] = ctx
            payload["options"]["num_predict"] = output_tokens(ctx, self.cfg)
        elif int(ai_opt(self.cfg, "max_output") or 0) > 0:
            payload["options"]["num_predict"] = int(
                ai_opt(self.cfg, "max_output"))
        if self.cfg.keep_alive not in (None, ""):
            ka = str(self.cfg.keep_alive).strip()
            # A API quer número para '-1' (nunca) e '0'; texto p/ '5m'.
            payload["keep_alive"] = int(ka) if re.fullmatch(r"-?\d+", ka) \
                else ka
        if not (self.cfg.model or "").strip():
            # O Ollama respondia só '400 Bad Request' ('model is required').
            raise ValueError(T("No local (Ollama) model chosen — pick one "
                               "in the AI panel (🤗 downloads one)."))
        log().debug(f"OLLAMA → model={self.cfg.model} "
                    f"text_len={len(text)}")
        t0 = time.time()
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              timeout=180)
        except requests.exceptions.ConnectionError:
            if not self._try_restart():
                raise
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              timeout=180)
        if r.status_code == 400 and "think" in payload \
                and "think" in (r.text or "").lower():
            # 'does not support thinking': não se volta a pedir.
            _NO_REASONING_PARAM.add(("local", self.cfg.model))
            payload.pop("think", None)
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              timeout=180)
        if r.status_code >= 400:
            # O motivo vem no corpo ({'error': ...}); o raise_for_status só
            # dizia '400 Client Error: Bad Request'.
            try:
                why = r.json().get("error") or r.text
            except ValueError:
                why = r.text
            log().warning(f"OLLAMA {r.status_code} ({self.cfg.model}): "
                          f"{why[:300]}")
            raise requests.exceptions.HTTPError(
                f"Ollama {r.status_code} ({self.cfg.model}): {why[:200]}",
                response=r)
        dt = time.time() - t0
        out = ((r.json().get("message") or {}).get("content") or "").strip()
        log().debug(f"OLLAMA ← {dt:.2f}s, {len(out)} chars")
        return out

    _rate_lock = threading.Lock()
    _rate_last = {}         # fornecedor → hora do último pedido

    def _throttle(self, provider, model):
        """Respeita 'Pedidos por minuto' (opção do modelo). Automático:
        modelos ':free' do OpenRouter a 20/min (o limite deles); os
        outros sem espera (um 429 faz a app esperar sozinha)."""
        rpm = int(ai_opt(self.cfg, "rpm") or 0)
        if rpm <= 0 and "free" in model_id(model).lower().rsplit(":", 1)[-1]:
            rpm = 19
        if rpm <= 0:
            return
        gap = 60.0 / rpm
        key = normalize_provider(provider)
        with AIEngine._rate_lock:
            wait = gap - (time.time() - AIEngine._rate_last.get(key, 0))
            if wait > 0:
                time.sleep(wait)
            AIEngine._rate_last[key] = time.time()

    def _cloud_one(self, provider, model, text, sysp):
        self._throttle(provider, model)
        try:
            out = self._cloud_call(provider, model, text, sysp)
        except CloudError as e:
            # A conta recusa este modelo (bloqueado nas definições, sem
            # saldo, sem acesso): marca-o e não insiste.
            msg = str(e).lower()
            # 'key limit exceeded' = modelo com custo numa chave sem
            # saldo; 'agentic harnesses' = o OpenRouter só o dá a agentes.
            if e.status in (402, 403) and re.search(
                    r"block|permission|not have access|payment|credit|"
                    r"billing|upgrade|paid|limit exceeded|agentic|"
                    r"only available", msg):
                mark_blocked(provider, model,
                             "blocked" if "block" in msg else "paid")
            raise
        if is_blocked(provider, model):
            unmark_blocked(provider, model)
        return out

    def _cloud_call(self, provider, model, text, sysp):
        return cloud_chat(provider, model, provider_key(self.cfg, provider),
                          sysp, text,
                          base_url=provider_base_url(self.cfg, provider),
                          max_out=output_tokens(context_for(self.cfg, model),
                                                self.cfg),
                          reasoning=str(ai_opt(self.cfg, "reasoning")),
                          temperature=ai_temperature(self.cfg))

    _fallback = None    # (fornecedor, modelo, até quando) do plano B
    _bad_key = {}       # fornecedor → até quando não entra no plano B (401)

    def _cloud(self, text, sysp):
        main = (normalize_provider(self.cfg.cloud_provider or "DeepSeek"),
                self.cfg.model)
        # Depois de a principal falhar usa o plano B durante 2 min antes
        # de voltar a tentar a principal (não espera por ela a cada msg).
        fb = self._fallback
        order = [main]
        if fb and time.time() < fb[2]:
            order = [fb[:2], main]
        if getattr(self.cfg, "cloud_fallback", True):
            free_only = bool(ai_opt(self.cfg, "free_only"))
            now = time.time()
            for p in CLOUD_PROVIDERS:
                m = provider_model(self.cfg, p)
                if p != main[0] and (p, m) not in order and m \
                        and AIEngine._bad_key.get(p, 0) < now \
                        and provider_ready(self.cfg, p) \
                        and not is_blocked(p, m) \
                        and (not free_only or is_free_model(
                            p, m, provider_base_url(self.cfg, p))):
                    order.append((p, m))
        first_err = None
        for p, m in order:
            try:
                out = self._cloud_one(p, m, text, sysp)
            except (requests.exceptions.RequestException, ValueError) as e:
                first_err = first_err or e
                log().warning(f"IA {p}/{m} falhou: {e}")
                if isinstance(e, CloudError) and e.status == 401 \
                        and (p, m) != main:
                    # Chave inválida: o plano B não a volta a tentar em
                    # cada mensagem (só daqui a 10 min).
                    AIEngine._bad_key[p] = time.time() + 600
                continue
            if (p, m) != main:
                if not (fb and fb[:2] == (p, m)):
                    log().warning(f"A usar o plano B: {p}/{m}")
                self._fallback = (p, m, time.time() + 120)
            else:
                self._fallback = None
            return out
        raise first_err


# ==================================================================
# TTS
# ==================================================================
class TTSManager:
    def __init__(self):
        self.enabled = False
        self.voice = "en-US-AriaNeural"
        self.rate_pct = 0           # velocidade: -50 … +100 (%)
        self.pitch_hz = 0           # tom: -40 … +40 (Hz)
        self.output_device = None
        # O chat todo é lido (também o histórico ao abrir o chat): com 10
        # deitava fora as mais antigas. Muitas em espera = lê mais rápido.
        self._queue = queue.Queue(maxsize=80)
        self._playing_job = None    # frase da fila a tocar agora
        self._stop = False
        self._paused = False
        self._alert_stop = None     # Event do alerta de menção a tocar
        self._mixer_ready = False
        # Restos de sessões fechadas à força (cada frase é apagada depois
        # de tocar; um crash deixava-a no Temp).
        cleanup_temp_files()
        self._init_mixer()
        threading.Thread(target=self._loop, daemon=True,
                         name="TTS").start()

    def _init_mixer(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            kwargs = {"frequency": 24000, "size": -16, "channels": 2,
                      "buffer": 512}
            if self.output_device:
                kwargs["devicename"] = self.output_device
            pygame.mixer.init(**kwargs)
            self._mixer_ready = True
        except Exception as e:
            log().warning(f"Mixer device falhou ({e}), uso default")
            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=24000, size=-16, channels=2,
                                  buffer=512)
                self._mixer_ready = True
            except Exception as e2:
                log().error(f"Erro mixer: {e2}")
                self._mixer_ready = False

    @property
    def rate(self):
        return f"{self.rate_pct:+d}%"

    @property
    def pitch(self):
        return f"{self.pitch_hz:+d}Hz"

    def configure(self, enabled, voice, output_device, rate=None,
                  pitch=None):
        self.enabled = bool(enabled)
        if voice:
            self.voice = voice
        if rate is not None:
            self.rate_pct = max(-50, min(100, int(rate)))
        if pitch is not None:
            self.pitch_hz = max(-40, min(40, int(pitch)))
        if output_device != self.output_device:
            self.output_device = output_device
            self._init_mixer()

    def speak(self, text):
        if not text:
            return
        if not self.enabled:
            log().debug(f"TTS desligado — não lido: {text[:60]!r}")
            return
        text = self._clean(text)
        if not text:
            return
        # Voz não-cirílica (ex.: en-US-AriaNeural) salta nomes russos:
        # passa-os para letras latinas ('Шум' → 'Shum').
        if not (self.voice or "").lower().startswith(("ru-", "uk-", "bg-",
                                                      "sr-", "kk-")):
            text = transliterate_cyrillic(text)
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            try:
                dropped = self._queue.get_nowait()
                log().info(f"TTS: fila cheia — saltada a mais antiga: "
                           f"{dropped[:50]!r}")
            except queue.Empty: pass
            try: self._queue.put_nowait(text)
            except queue.Full: pass

    def stop(self):
        self._stop = True
        try: pygame.mixer.music.stop()
        except Exception: pass
        try: pygame.mixer.music.unload()
        except Exception: pass
        cleanup_temp_files()

    def pause(self):
        """Cala já e segura a fila (ex.: enquanto o micro grava, senão
        o reconhecimento apanhava a voz das colunas)."""
        self._paused = True
        # A frase da fila cala-a o _play (em ~30 ms) e guarda-a para a ler
        # outra vez; aqui só se cala o que não é da fila (pré-escuta).
        if getattr(self, "_playing_job", None) is None:
            try: pygame.mixer.music.stop()
            except Exception: pass

    def resume(self):
        self._paused = False

    # Sons de aviso da voz: (frequência Hz, duração ms) de cada nota.
    CUES = {
        "start": ((660, 70), (990, 110)),     # sobe: 'fala agora'
        "stop": ((880, 70),),                 # acabou de gravar
        "cancel": ((520, 80), (330, 130)),    # desce: cancelado
        "busy": ((300, 160),),                # ainda a tratar da anterior
    }
    # Sons à escolha para 'escreveram o meu nome' (0 Hz = pausa).
    MENTION_SOUNDS = {
        "ding": ((784, 90), (1047, 90), (1319, 170)),
        "bell": ((1319, 180), (988, 280)),
        "ping": ((1568, 130),),
        "triple": ((880, 80), (0, 60), (880, 80), (0, 60), (880, 80)),
        "rising": ((523, 80), (659, 80), (784, 80), (1047, 160)),
        "soft": ((440, 170), (554, 240)),
        "radar": ((1200, 50), (0, 70), (1200, 50), (0, 220), (1200, 50),
                  (0, 70), (1200, 50)),
        "alarm": ((988, 120), (740, 120), (988, 120), (740, 120)),
    }

    def cue(self, kind="start", repeat=1):
        """Bip pela mesma saída da voz (o que ouves nos headphones). O
        winsound.Beep de antes tinha 70 ms e às vezes nem se ouvia (a
        placa de som 'acorda' e come o início). Nunca vai para o disco.
        kind: um dos CUES, ou 'mention:<som>' (MENTION_SOUNDS)."""
        if kind.startswith("mention"):
            name = kind.split(":", 1)[1] if ":" in kind else "ding"
            notes = self.MENTION_SOUNDS.get(name) \
                or self.MENTION_SOUNDS["ding"]
        else:
            notes = self.CUES.get(kind) or self.CUES["start"]
        repeat = max(1, min(10, int(repeat or 1)))
        if repeat > 1:
            notes = tuple(notes) + ((0, 180),)
            notes = notes * repeat
        # Duração (s): quem fala a seguir espera que o som acabe.
        self.last_cue_secs = sum(ms + 20 for _, ms in notes) / 1000
        try:
            if self._mixer_ready and pygame.mixer.get_init():
                import array
                import math
                freq, _size, chans = pygame.mixer.get_init()
                samples = array.array("h")
                for hz, ms in notes:
                    n = int(freq * ms / 1000)
                    fade = max(1, int(freq * 0.008))   # sem estalos
                    for i in range(n):
                        env = min(1.0, i / fade, (n - i) / fade)
                        v = int(11000 * env * math.sin(
                            2 * math.pi * hz * i / freq))
                        samples.extend([v] * chans)
                    samples.extend([0] * (int(freq * 0.02) * chans))
                snd = pygame.mixer.Sound(buffer=samples.tobytes())
                snd.set_volume(1.0)
                snd.play()
                self._last_cue = snd      # não deixar o som ser libertado
                return
        except Exception:
            log().debug("cue pygame falhou", exc_info=True)
        try:
            import winsound
            for hz, ms in notes:
                if hz:
                    winsound.Beep(hz, max(ms, 90))
                else:
                    time.sleep(ms / 1000)
        except Exception:
            pass

    def start_alert(self, kind, repeat=1, every=10, during=30, text=""):
        """Toca o som já e depois de `every` em `every` s enquanto não
        passarem `during` s (ex.: 10/30 → aos 0, 10 e 20 s). Com `text`,
        a voz diz o texto EM VEZ do som. Um alerta novo substitui o
        anterior; stop_alert() (tecla de cancelar ou começares a ditar)
        acaba-o."""
        self.stop_alert()
        stop = threading.Event()
        self._alert_stop = stop
        every = max(1, int(every or 10))
        during = max(0, int(during or 0))

        def run():
            t0 = time.time()
            while not stop.is_set() and not self._stop:
                if text:
                    self.speak_now(text)
                else:
                    self.cue(kind, repeat)
                if time.time() - t0 + every >= during or \
                        stop.wait(every):
                    break
            if self._alert_stop is stop:
                self._alert_stop = None
        threading.Thread(target=run, daemon=True, name="Alert").start()

    def alert_active(self):
        return getattr(self, "_alert_stop", None) is not None

    def stop_alert(self):
        ev = getattr(self, "_alert_stop", None)
        self._alert_stop = None
        if ev is not None:
            ev.set()
            return True
        return False

    def speak_after_cue(self, text):
        """speak_now depois de o último som (cue) acabar de tocar."""
        threading.Timer(getattr(self, "last_cue_secs", 0) + 0.1,
                        self.speak_now, args=(text,)).start()

    def speak_now(self, text):
        """Fala `text` a seguir à frase que está a tocar (passa à frente da
        fila) — mesmo com a leitura do chat desligada (é um aviso que
        escreveste tu)."""
        text = self._clean(text or "")
        if not text:
            return
        if not (self.voice or "").lower().startswith(("ru-", "uk-", "bg-",
                                                      "sr-", "kk-")):
            text = transliterate_cyrillic(text)
        with self._queue.mutex:
            self._queue.queue.appendleft(text)
            self._queue.unfinished_tasks += 1
            self._queue.not_empty.notify()

    @staticmethod
    def _clean(text):
        text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
        text = re.sub(r"[*_~`|<>\[\]{}]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()[:500]

    # Fila com tantas frases em espera → lê 20% mais depressa.
    FAST_QUEUE = 4

    def _loop(self):
        nxt = None      # frase seguinte, já a ser sintetizada
        cur = None      # frase interrompida por pause(): volta a tocar
        while not self._stop:
            if self._paused:
                time.sleep(0.1)
                continue
            if cur is None:
                if nxt is None:
                    try:
                        text = self._queue.get(timeout=0.4)
                    except queue.Empty:
                        continue
                    nxt = self._prepare(text)
                cur, nxt = nxt, None
            # Enquanto esta toca, a seguinte já se sintetiza (o edge-tts
            # demora ~0,5-1 s por frase): sem silêncios entre mensagens.
            if nxt is None:
                try:
                    nxt = self._prepare(self._queue.get_nowait())
                except queue.Empty:
                    pass
            try:
                done = self._play(cur)
            except Exception:
                log().exception("TTS speak falhou")
                done = True
            # Calada a meio (começaste a falar ao micro): a mesma frase
            # volta a ser lida desde o início — antes perdia-se.
            if done:
                cur = None
        if nxt:
            nxt["thread"].join(timeout=5)
            nxt["audio"] = None

    def _prepare(self, text):
        """Começa a sintetizar `text` noutra thread. O áudio fica só na
        memória — nunca é escrito no disco."""
        rate = self.rate
        if self._queue.qsize() >= self.FAST_QUEUE:
            # Atrasado: +20% sobre a velocidade que escolheste.
            rate = f"{min(100, self.rate_pct + 20):+d}%"
        job = {"text": text, "audio": None}

        def gen():
            # O servidor de voz da Microsoft às vezes responde 503 a uma
            # frase: tenta outra vez em vez de a perder.
            for attempt in range(3):
                try:
                    job["audio"] = asyncio.run(self._generate(text, rate))
                    return
                except Exception as e:
                    if attempt == 2 or self._stop:
                        log().warning(f"TTS: falha a sintetizar "
                                      f"{text[:50]!r}: {e}")
                        return
                    time.sleep(0.5 * (attempt + 1))
        job["thread"] = threading.Thread(target=gen, daemon=True,
                                         name="TTSgen")
        job["thread"].start()
        return job

    def _play(self, job):
        """Toca a frase. False = calada por pause() (antes de começar ou a
        meio): o _loop volta a tocá-la quando retomar."""
        import io
        text = job["text"]
        job["thread"].join(timeout=30)
        done = True
        try:
            if not self._mixer_ready:
                self._init_mixer()
                if not self._mixer_ready:
                    log().warning(f"TTS: áudio indisponível — não lido: "
                                  f"{text[:60]!r}")
                    return True
            if not job["audio"] or self._stop:
                return True
            if self._paused:
                done = False
                return False
            log().info(f"TTS: a ler ({self._queue.qsize()} em espera): "
                       f"{text[:80]!r}")
            self._playing_job = job
            pygame.mixer.music.load(io.BytesIO(job["audio"]), "mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop:
                if self._paused:
                    pygame.mixer.music.stop()
                    log().info(f"TTS: interrompida (micro) — volta a ler: "
                               f"{text[:50]!r}")
                    done = False
                    return False
                time.sleep(0.03)
            return True
        finally:
            self._playing_job = None
            try: pygame.mixer.music.unload()
            except Exception: pass
            if done:
                job["audio"] = None     # larga a memória

    def stop_preview(self):
        """Cala o '▶ Ouvir' / o guia falado a meio."""
        try:
            if self._mixer_ready and pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def synth(self, text, voice=None):
        """mp3 da frase em memória (bytes), para tocar mais tarde sem
        esperar (o guia rápido gera os passos todos de antemão)."""
        return asyncio.run(self._generate(text, "+0%", "+0Hz", voice))

    def is_playing(self):
        try:
            return bool(self._mixer_ready and pygame.mixer.get_init()
                        and pygame.mixer.music.get_busy())
        except Exception:
            return False

    def play_bytes(self, audio):
        """Toca um mp3 em memória; o que estava a tocar cala-se."""
        import io
        if not self._mixer_ready:
            self._init_mixer()
        pygame.mixer.music.stop()
        pygame.mixer.music.load(io.BytesIO(audio), "mp3")
        pygame.mixer.music.play()

    def preview(self, text, voice=None, rate=None, pitch=None,
                on_error=None):
        """Botão '▶ Ouvir' da config: lê `text` já com esta voz,
        velocidade e tom (mesmo com a leitura do chat desligada). Só em
        memória, como o resto."""
        import io
        voice = voice or self.voice
        r = f"{max(-50, min(100, int(rate or 0))):+d}%" if rate is not None \
            else self.rate
        pt = f"{max(-40, min(40, int(pitch or 0))):+d}Hz" \
            if pitch is not None else self.pitch

        def run():
            try:
                audio = asyncio.run(self._generate(text, r, pt, voice))
                if not self._mixer_ready:
                    self._init_mixer()
                pygame.mixer.music.stop()
                pygame.mixer.music.load(io.BytesIO(audio), "mp3")
                pygame.mixer.music.play()
            except Exception as e:
                log().warning(f"TTS: pré-escuta falhou: {e}")
                if on_error:            # ex.: sem internet (voz neural)
                    try: on_error(str(e))
                    except Exception: pass
        threading.Thread(target=run, daemon=True, name="TTSpreview").start()

    async def _generate(self, text, rate=None, pitch=None, voice=None):
        """mp3 da frase, em memória (bytes)."""
        buf = bytearray()
        async for chunk in edge_tts.Communicate(
                text, voice or self.voice, rate=rate or self.rate,
                pitch=pitch or self.pitch).stream():
            if chunk.get("type") == "audio":
                buf += chunk["data"]
        if not buf:
            raise RuntimeError("edge-tts: sem áudio")
        return bytes(buf)


def cleanup_temp_files(max_age=120):
    """Apaga de vez (os.remove: não vai para a Reciclagem) o que a app
    deixa no Temp quando é fechada à força: a voz sintetizada
    (rf_tts_*.mp3) e as imagens/texto do chat que o pytesseract escreve
    a cada leitura (tess_*; normalmente apaga-as logo). Os tess_ com
    menos de `max_age` s ficam: podem ser de uma leitura a decorrer."""
    import glob
    tmp = tempfile.gettempdir()
    now, n = time.time(), 0
    for pat, age in (("rf_tts_*.mp3", 0), ("tess_*", max_age)):
        for f in glob.glob(os.path.join(tmp, pat)):
            try:
                if os.path.isfile(f) and now - os.path.getmtime(f) >= age:
                    os.remove(f)
                    n += 1
            except OSError:
                pass
    if n:
        log().info(f"Temp: {n} ficheiro(s) temporário(s) apagado(s)")
    return n


# ==================================================================
# OCR WORKER
# ==================================================================
class OCRWorker(QObject):
    translated = pyqtSignal(str, str)   # (canal, '[Nome] tradução')
    tab_changed = pyqtSignal(str)       # 'guild', 'whisper:PlayerAlpha'...
    error = pyqtSignal(str)
    # Desempenho para o cabeçalho do overlay: {'ai': s por pedido,
    # 'lag': s do OCR ver a mensagem até aparecer, 'queue': à espera,
    # 'ocr': s por leitura, 'err': a IA está a falhar, 'mode': ...}
    perf = pyqtSignal(dict)

    def __init__(self, engine, overlay, tts, cfg, game=None):
        super().__init__()
        self.engine = engine
        self.overlay = overlay
        self.tts = tts
        self.cfg = cfg
        self.game = game or GameWindow()
        self._running = False
        # Mensagens já traduzidas, pela ordem do chat: (speaker_key,
        # body_key). Lê-se o chat como um log: só o que está ABAIXO da
        # última mensagem traduzida é novo.
        self._history = deque(maxlen=600)
        # speaker_key → {grafia: contagem}; unifica 'testO07'/'test007'.
        self._speakers = {}
        self._prev_frame = []   # chaves do frame anterior (estabilidade)
        self._unstable = (None, 0)  # (linha instável, leituras seguidas)
        self._settling = False      # há linhas novas por confirmar
        self.last_chat_seen = 0.0
        self.last_pm_from = None    # quem me mandou o último PM ('reply')
        self.last_was_backlog = False
        self.game_tab = None        # separador ativo no jogo
        self.whisper_with = None    # conversa aberta no Whisper
        self._partner_checked = 0.0
        self._tab_seen = None       # leitura anterior do separador
        self._panel_state = (False, 0.0)    # (chat aberto?, quando se viu)
        self._partner_read = None   # leitura anterior do nome no Whisper
        self._last_err = ("", 0.0)
        # Língua das mensagens recentes, por canal e por pessoa: a voz
        # responde na língua de quem fala ali.
        self._lang_by_ch = {}
        self._lang_by_speaker = {}
        self._seen_saved = 0.0
        self._ai_errors = 0     # erros seguidos da IA (espera mais)
        # Fila de tradução (ver _enqueue): [(key, linha, canal)] por ordem.
        self._todo = deque()
        self._todo_cond = threading.Condition()
        self._inflight = []     # o lote que a IA está a traduzir agora
        self._seen_at = {}      # key → quando o OCR a viu (para o atraso)
        self._perf_ai = deque(maxlen=5)
        self._perf_lag = deque(maxlen=5)
        self._perf_ocr = 0.0
        self._perf_sent = 0.0
        apply_chat_calibration(cfg)
        self._load_seen()

    # ---------- o que já foi lido (sobrevive a reabrir a app) ----------
    # Sem isto, reabrir a app voltava a ditar o chat todo que já ouviste.
    SEEN_MAX_AGE = 6 * 3600

    @staticmethod
    def _seen_path():
        return os.path.join(os.path.dirname(os.path.abspath(
            get_last_config_path())), "ui_cache", "chat_seen.json")

    def _load_seen(self):
        try:
            with open(self._seen_path(), encoding="utf-8") as f:
                d = json.load(f)
            if time.time() - float(d.get("t", 0)) > self.SEEN_MAX_AGE:
                return
            self._history.extend(tuple(k) for k in d.get("history", [])
                                 if isinstance(k, list) and len(k) == 2)
            for k, v in (d.get("speakers") or {}).items():
                if isinstance(v, dict):
                    self._speakers[k] = {n: int(c) for n, c in v.items()}
            log().info(f"Chat: {len(self._history)} mensagens já lidas "
                       f"(sessão anterior) — não se repetem")
        except FileNotFoundError:
            pass
        except Exception:
            log().warning("Chat: histórico guardado ilegível — ignorado")

    def _save_seen(self, force=False):
        if not force and time.time() - self._seen_saved < 5:
            return
        self._seen_saved = time.time()
        try:
            path = self._seen_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"t": time.time(),
                           "history": [list(k) for k in self._history],
                           "speakers": self._speakers}, f,
                          ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            log().debug("Chat: falha a guardar o histórico", exc_info=True)

    # ---------- língua para responder ----------
    def _note_lang(self, channel, line):
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line)
        if not m:
            return
        lang = detect_lang(m.group(2))
        if not lang:
            return
        for store, k in ((self._lang_by_ch, channel or "all"),
                         (self._lang_by_speaker, _speaker_key(m.group(1)))):
            store.setdefault(k, deque(maxlen=20)).append(lang)

    @staticmethod
    def _majority(langs, min_count):
        if not langs or len(langs) < min_count:
            return None
        counts = {}
        for l in langs:
            counts[l] = counts.get(l, 0) + 1
        best = max(counts, key=counts.get)
        return best if counts[best] / len(langs) >= 0.5 else None

    def guess_target_lang(self, channel=None, speaker=None):
        """Língua em que se deve responder: a de quem me escreveu (reply)
        ou a mais usada no canal. None = sem dados (usa a da config)."""
        if speaker:
            lang = self._majority(
                list(self._lang_by_speaker.get(_speaker_key(speaker), [])), 1)
            if lang:
                return lang
        if channel:
            return self._majority(list(self._lang_by_ch.get(channel, [])), 2)
        return None

    # ---------- separador do jogo ----------
    def _known_name(self, name):
        """Grafia conhecida (de quem já falou no chat) mais parecida com
        `name`, ou None. 'PlayerAlphe' lido no topo do Whisper = 'PlayerAlpha'."""
        key = _speaker_key(name)
        best, best_sim = None, 0.0
        for k in self._speakers:
            sim = _similar(k, key)
            if sim > best_sim:
                best, best_sim = k, sim
        if best is None or best_sim < 0.75:
            return None
        counts = self._speakers[best]
        return max(counts, key=counts.get)

    def _panel_open(self, full):
        """GameWindow.chat_panel_open com memória (o OCR da barra custa
        ~750 ms): 'aberto' vale 10 s, 'fechado' 2 s; o _loop esquece-a
        quando o separador aceso muda. Lida sempre, mesmo com um separador
        aceso: com o chat fechado os ícones do jogo acendem separadores
        falsos e o OCR lia o mundo do jogo como mensagens."""
        is_open, when = self._panel_state
        if time.time() - when < (10 if is_open else 2):
            return is_open
        is_open = GameWindow.chat_panel_open(full, self.whisper_with)
        self._panel_state = (is_open, time.time())
        return is_open

    def _update_game_tab(self, full, tab=None):
        tab = tab or GameWindow.active_tab(full)
        self._tab_seen = tab
        if tab is None:
            return
        # Com o chat fechado os ícones do jogo 'acendem' um separador
        # falso (o 'P' do grupo cai no 'Server') e o overlay saltava para
        # um canal vazio. Só muda se a barra de escrever confirmar que o
        # chat está mesmo aberto e uma 2.ª captura logo a seguir ler o
        # mesmo separador (a barra às vezes lia lixo como 'system' e as
        # mensagens da guild iam parar ao separador System). Esperar pelo
        # ciclo seguinte atrasava a troca 2-4 s (o OCR do chat é lento).
        if tab != self.game_tab:
            if not self._panel_open(full):
                return
            time.sleep(0.25)
            again = self.game.capture_client()
            if GameWindow.active_tab(again) != tab:
                return
        now = time.time()
        partner = self.whisper_with
        if tab == "whisper" and (tab != self.game_tab
                                 or now - self._partner_checked > 5):
            self._partner_checked = now
            read = GameWindow.whisper_partner(full)
            prev_read, self._partner_read = self._partner_read, read
            known = self._known_name(read) if read else None
            if known:
                partner = known
            elif read and read == prev_read and len(read) >= 3:
                partner = read      # nome novo, lido igual 2x seguidas
            elif tab != self.game_tab:
                partner = None
            # Senão (não leu / leitura duvidosa): fica o anterior — antes
            # o nome saltava 'PlayerAlpha' → 'SRR' → 'PlayerAlphe' e o
            # separador PM do overlay escondia as mensagens.
        if tab != self.game_tab or (tab == "whisper"
                                    and partner != self.whisper_with):
            self.game_tab, self.whisper_with = tab, partner
            log().info(f"Chat do jogo: {tab}"
                       + (f" com {partner}" if tab == "whisper" and partner
                          else ""))
            self._emit("tab_changed", f"{tab}:{partner}"
                       if tab == "whisper" and partner else tab)

    def _track_pm_sender(self, raw):
        """'[Recipient: X]' = X mandou-me PM. Guarda o mais recente
        visível (o de mais abaixo no chat)."""
        found = re.findall(r"\[\s*R[eе]c\w*\s*[:;]\s*([^\]\)\n]{2,30})", raw)
        if not found:
            return
        name = _fix_speaker(found[-1].strip())
        if len(re.sub(r"[\W_]", "", name)) >= 2:
            self.last_pm_from = self._canon_speaker(name)[0]

    def chat_open(self):
        """O painel do chat está aberto? (o OCR viu mensagens há pouco)"""
        return time.time() - self.last_chat_seen < 6.0

    BATCH_LINES = 8
    _batch_cap = 64         # baixa sozinho se o modelo der erro de contexto
    # Ao abrir o chat/outro separador lê TUDO o que ainda não foi lido
    # (antes só as últimas 3). O que já foi lido nunca se repete: o
    # histórico (_history) filtra-o, também depois de reabrir a app.
    # Overlay pequeno (faixa no fundo do chat) só vê 1 mensagem de cada
    # vez — com 2 nunca arrancava. O mundo do jogo com o chat fechado
    # não produz linhas '[Nome] texto', e as repetidas são filtradas
    # pelo histórico.
    MIN_SPEAKERS_NEW_SCREEN = 1

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True,
                         name="OCRWorker").start()
        threading.Thread(target=self._translate_loop, daemon=True,
                         name="Translator").start()

    def _emit(self, signal_name, value):
        # Ao fechar a app o QObject pode já ter sido destruído enquanto
        # esta thread ainda esperava pela IA; até ler self.translated
        # rebenta nesse caso, por isso tudo dentro do try.
        if not self._running:
            return
        try:
            getattr(self, signal_name).emit(value)
        except (RuntimeError, AttributeError):
            self._running = False

    def _emit2(self, signal_name, a, b):
        if not self._running:
            return
        try:
            getattr(self, signal_name).emit(a, b)
        except (RuntimeError, AttributeError):
            self._running = False

    def stop(self):
        self._running = False
        with self._todo_cond:
            # Ainda por traduzir: saem do histórico para serem lidas da
            # próxima vez que abrires a app (não ficam 'lidas' sem o serem).
            undone = [k for k, _, _ in list(self._inflight) + list(self._todo)]
            self._todo.clear()
            self._todo_cond.notify_all()
        if undone:
            hist = list(self._history)
            for k in reversed(undone):
                for i in range(len(hist) - 1, -1, -1):
                    if hist[i] == k:
                        del hist[i]
                        break
            self._history.clear()
            self._history.extend(hist)
        self._save_seen(force=True)

    def _error_once(self, msg, every=30.0):
        """Mostra um erro no overlay sem o repetir a cada ciclo (com o
        Ollama em baixo enchia o overlay de '[Rede] ...')."""
        last_msg, last_t = self._last_err
        if msg != last_msg or time.time() - last_t > every:
            self._last_err = (msg, time.time())
            self._emit("error", msg)

    # Píxeis diferentes entre duas máscaras do chat abaixo dos quais o
    # texto é o mesmo: parado mudam 150-320 (fundo a mexer), uma mensagem
    # nova mexe milhares (e o scroll quase tudo).
    SAME_FRAME_PX = 800
    # Releitura rápida para confirmar uma linha nova (o scroll do jogo
    # acaba em ~0,2 s).
    SETTLE_GAP = 0.35

    def _setup_tessdata_env(self):
        tessdata_dir = get_app_tessdata_dir()
        if not tessdata_dir or not os.path.isdir(tessdata_dir):
            log().warning(f"Tessdata dir não existe: {tessdata_dir}")
            return False
        prefix = _ascii_tessdata(os.path.abspath(tessdata_dir)) + os.sep
        os.environ["TESSDATA_PREFIX"] = prefix
        log().info(f"TESSDATA_PREFIX = {prefix}")
        ok = True
        for f in ("eng.traineddata", "por.traineddata", "rus.traineddata"):
            p = os.path.join(tessdata_dir, f)
            if os.path.isfile(p):
                log().info(f"  ✓ {f} ({os.path.getsize(p)//1024} KB)")
            else:
                log().warning(f"  ✗ {f} EM FALTA")
                if f == "eng.traineddata":
                    ok = False
        try:
            ver = pytesseract.get_tesseract_version()
            log().info(f"Tesseract version: {ver}")
            langs = pytesseract.get_languages(config="")
            log().info(f"Línguas disponíveis: {langs}")
        except Exception as e:
            log().warning(f"Falha a inspecionar Tesseract: {e}")
            ok = False
        return ok

    def _canon_speaker(self, name):
        """(grafia mais frequente, chave) para um nome lido pelo OCR."""
        key = _speaker_key(name)
        if not key:
            return name, key
        if key not in self._speakers:
            # Nomes longos toleram 2 letras trocadas pelo OCR
            # ('EGxampleNamel' = 'ExampleName'); curtos só 1.
            long_name = len(key) >= 8
            max_diff, thr = (2, 0.8) if long_name else (1, 0.85)
            best, best_sim = None, 0.0
            for k in self._speakers:
                if abs(len(k) - len(key)) <= max_diff:
                    sim = _similar(k, key)
                    if sim >= thr and sim > best_sim:
                        best, best_sim = k, sim
            if best:
                key = best
            if len(self._speakers) > 500:
                self._speakers.clear()
        counts = self._speakers.setdefault(key, {})
        counts[name] = counts.get(name, 0) + 1
        return max(counts, key=counts.get), key

    @staticmethod
    def _body_key(body):
        # Cirílico/latino parecidos colapsam ('ага' == 'ara').
        return _normalize_for_dedup(body).translate(_CYR_TO_LAT) \
            .translate(_SPEAKER_KEY_MAP)

    @staticmethod
    def _matches(key, keys, thr=0.85):
        sp, body = key
        for s_sp, s_body in keys:
            if s_sp != sp:
                continue
            if s_body == body:
                return True
            # Mensagem meio cortada no topo/fundo da região: é o início ou
            # o fim da outra (não um pedaço do meio: 'Заходим' novo estava
            # dentro de 'также заходим в дискорд' antigo). As duas com
            # >= 6 letras: um 'в' / 'да' antigo cabia em quase tudo.
            if min(len(body), len(s_body)) >= 6:
                short, full = sorted((body, s_body), key=len)
                if full.startswith(short) or full.endswith(short):
                    return True
            if (SequenceMatcher(None, s_body, body).quick_ratio() >= thr
                    and _similar(s_body, body) >= thr):
                return True
        return False

    def _parse_frame(self, frame):
        """[(key, linha, canal)] do ecrã, de cima para baixo. `frame` é
        [(canal, linha)] (parse_ocr_messages) ou texto simples."""
        if isinstance(frame, str):
            frame = [(None, l) for l in frame.splitlines()]
        items = []
        for channel, line in frame:
            m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line)
            if m:
                sp, sp_key = self._canon_speaker(m.group(1))
                line = f"[{sp}] {m.group(2)}"
                key = (sp_key, self._body_key(m.group(2)))
            else:
                # Linha sem [Nome] que começa por um nome conhecido: é o
                # cabeçalho da conversa do Whisper ('PlayerAlpha ▽') colado
                # a uma linha cortada — não é um aviso do sistema.
                first = line.split(" ", 1)[0]
                if len(first) >= 3 and _speaker_key(first) in self._speakers:
                    continue
                key = ("", self._body_key(line))
            fallback = self.game_tab or "all"
            # O System só tem avisos do jogo: uma linha '[Nome] ...' sem
            # etiqueta não é dali (era o separador mal lido).
            if key[0] and fallback == "system":
                fallback = "all"
            # No World cada linha é '4 Server [Nome]': se o OCR perde o nº
            # do servidor a linha parecia do chat Server (que estava vazio).
            if channel == "server" and self.game_tab == "world":
                channel = "world"
            if key[1]:
                items.append((key, line, channel or fallback))
        return items

    ALIGN_HIST = 150        # mensagens do histórico comparadas com o ecrã

    def _locate_last(self, keys):
        """Índice no ecrã da última mensagem já lida, ou None.

        Alinha o ecrã com o histórico pela ORDEM, como um diff: a cadeia
        mais comprida de pares (linha do ecrã, mensagem já lida) que
        avançam juntos nos dois. Antes cada linha nova era comparada com
        as 80 últimas por semelhança, e uma mensagem nova parecida com uma
        antiga do mesmo jogador ('WTS [item] 20k' → 'WTS [item] 18k', 'go
        raid' → 'go raid now') passava por lida e perdia-se. Com a ordem,
        a nova vem DEPOIS da última da cadeia e não pode ser a antiga.
        Mensagens curtas ('+', 'да') valem pouco: sozinhas não chegam para
        dizer que o ecrã já foi lido (seria um '+' antigo igual)."""
        hist = list(self._history)[-self.ALIGN_HIST:]
        if not hist or not keys:
            return None
        n, m = len(keys), len(hist)
        weight = [1.0 if len(k[1]) >= 6 else 0.3 for k in keys]
        best = [[0.0] * (m + 1) for _ in range(n + 1)]
        same = {}
        for i in range(1, n + 1):
            ki, row, prev = keys[i - 1], best[i], best[i - 1]
            for j in range(1, m + 1):
                v = prev[j] if prev[j] > row[j - 1] else row[j - 1]
                hj = hist[j - 1]
                if ki[0] == hj[0]:
                    ok = same.get((i, j))
                    if ok is None:
                        ok = same[(i, j)] = self._matches(ki, (hj,), 0.75)
                    if ok and prev[j - 1] + weight[i - 1] > v:
                        v = prev[j - 1] + weight[i - 1]
                row[j] = v
        if best[n][m] < 1.0:
            return None
        # A última linha do ecrã na cadeia (num empate fica a mais acima:
        # um '+' repetido em baixo é o novo).
        i, j = n, m
        while i > 0 and j > 0:
            if best[i][j] == best[i - 1][j]:
                i -= 1
            elif best[i][j] == best[i][j - 1]:
                j -= 1
            else:
                return i - 1
        return None

    def _is_repeat(self, key, recent):
        """A mesma pessoa voltou a escrever a mesma coisa (anúncio WTS
        repetido): não se lê outra vez. Só iguais (ou quase, o OCR varia);
        curtas ('+', 'да') só contra as 3 últimas."""
        sp, body = key
        pool = recent if len(body) >= 6 else recent[-3:]
        for s_sp, s_body in pool:
            if s_sp == sp and (s_body == body or (
                    len(body) >= 12 and _similar(s_body, body) >= 0.92)):
                return True
        return False

    def _new_messages(self, cleaned):
        """[(key, linha)] novas, por ordem, prontas a traduzir.

        - Só o que está abaixo da última mensagem traduzida é novo: linhas
          antigas lidas de outra forma (fundo diferente ao reabrir o chat)
          ficam acima da âncora e não se repetem.
        - Sem âncora (1.ª leitura, rajada de mensagens) traduz o ecrã todo,
          mas só se parecer mesmo o chat (>= 2 linhas '[Nome]'): com o chat
          fechado o OCR só vê o mundo do jogo.
        - Cada mensagem tem de aparecer em 2 frames seguidos (no scroll a
          última linha sai cortada e o modelo inventava o resto); pára na
          primeira instável para não trocar a ordem.
        """
        items = self._parse_frame(cleaned) if cleaned else []
        keys = [k for k, _, _ in items]
        prev_frame, self._prev_frame = self._prev_frame, keys
        if any(sp for sp, _ in keys):
            self.last_chat_seen = time.time()
        self.last_was_backlog = False
        if not items:
            return []
        anchor = self._locate_last(keys)
        if anchor is None:
            if sum(1 for sp, _ in keys if sp) < self.MIN_SPEAKERS_NEW_SCREEN:
                return []
            new = items
            # Ecrã sem nada já traduzido (arranque, outro separador):
            # é histórico — vai para o overlay mas não se lê em voz alta.
            self.last_was_backlog = True
        else:
            new = items[anchor + 1:]
        # Só as linhas instáveis NO FIM esperam pela leitura seguinte: é a
        # última a entrar no fundo durante o scroll (cortada, o modelo
        # inventava o resto). Uma linha com outra estável por baixo já está
        # completa — antes parava-se na 1.ª instável, e com o chat a correr
        # a de cima (a sair, cortada) bloqueava tudo e o resto perdia-se.
        stable = [self._matches(k, prev_frame) for k, _, _ in new]
        upto = max((i for i, s in enumerate(stable) if s), default=-1) + 1
        # Há linhas novas à espera de confirmação: o _loop volta a capturar
        # já (não espera o intervalo todo) — se a imagem não mudou, ficam
        # confirmadas sem outro OCR (~4 s mais depressa por mensagem).
        self._settling = upto < len(new)
        if upto < len(new):
            # A última nunca estabiliza (sticker a mexer, OCR que varia
            # sempre): passa à 3.ª leitura seguida.
            sig = (new[upto - 1][0] if upto else None, new[upto][0][0])
            stuck, count = self._unstable
            count = count + 1 if stuck == sig else 1
            self._unstable = (sig, count)
            if count >= 3:
                upto += 1
        recent = list(self._history)[-80:]
        pending = [(key, line, channel) for key, line, channel in new[:upto]
                   if not self._is_repeat(key, recent)]
        if upto:
            self._unstable = (None, 0) if upto >= len(new) else \
                self._unstable
        return pending

    # Quando o OCR manda lixo o modelo responde a falar de si próprio
    # ('I will not translate or alter the content of the message.').
    _META_RE = re.compile(
        r"\b(?:I (?:will|can|cannot|can't|won't) ?(?:not )?(?:translate|"
        r"alter|help)|I'?m sorry|as an ai|unable to translate|no text to "
        r"translate|the content of the message|there is nothing to "
        r"translate|does not (?:make sense|contain)|(?:it|this|the "
        r"message|text)(?:'s| is) already in \w+)\b", re.I)

    _SLANG_RE = re.compile(
        r"\b(?:WTB|WTS|WTT|LFG|LFM|LF\d?M?|PM|DM|BM|AFK|GG|GL|HF|TY|THX|"
        r"PLZ|PLS|LOL|XD|OMG|BRB|IMO|DPS|AOE|CC|MA|PvP|PvE)\b", re.I)

    def _already_target(self, body):
        """Não vale a pena ir ao modelo: sem itens/números/siglas a
        mensagem já está na língua de destino, ou é conversa curta latina
        ('gg wp', 'ty', 'lol ok'). Poupa tempo e evita o modelo inventar
        ('WTB [item] 30 dias' → 'WTS 2 and 1')."""
        core_txt = re.sub(r"\[[^\]]*\]", " ", body)
        core_txt = self._SLANG_RE.sub(" ", core_txt)
        core_txt = re.sub(r"[\d\W_]+", " ", core_txt).strip()
        words = core_txt.split()
        if not words:
            return True
        if not re.search(r"[^\x00-ɏ]", core_txt) and len(words) <= 2:
            return True     # latino e curtíssimo
        lang = detect_lang(core_txt)
        return bool(lang) and lang.split(" ")[0] == \
            (self.cfg.ocr_target or "").split(" ")[0]

    def _translate_one(self, line, line_prompt):
        """Traduz só o corpo de uma mensagem e repõe o '[Nome]'.
        '' = descartar (o modelo recusou/explicou em vez de traduzir)."""
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line)
        sp, body = (m.group(1), m.group(2)) if m else (None, line)
        if _needs_translation(body) and not self._already_target(body):
            # (Marcas tipo '[1]' no lugar dos itens não servem: o gemma tira
            # os parênteses e escreve '2 and 1'.)
            def ask(prompt):
                r = self.engine.translate(body, prompt) or ""
                r = next((l for l in r.splitlines() if l.strip()), "")
                return r.strip().strip('"“”«»').strip()
            res = ask(line_prompt)
            target = self.cfg.ocr_target
            if wrong_script(res, target) and self.cfg.mode != "mt":
                # Noutro alfabeto (árabe, metade em russo...): mais uma vez
                # com o prompt estrito; senão fica o original (não lixo).
                log().info(f"OCR: tradução noutro alfabeto ({res[:40]!r}) "
                           f"— a repetir")
                res = ask(build_ocr_retry_prompt(self.cfg.ocr_source, target))
                if wrong_script(res, target):
                    res = body
            if self._META_RE.search(res) and not self._META_RE.search(body):
                if not sp:
                    log().info(f"OCR: resposta do modelo descartada (lixo?): "
                               f"{body[:50]!r} → {res[:60]!r}")
                    return ""
                # Mensagem de um jogador: mais vale o original que perdê-la.
                log().info(f"OCR: modelo não traduziu ({res[:50]!r}) — "
                           f"mostra o original")
                res = body
            # Alguns modelos repetem o '[Nome]' mesmo sem o receberem.
            if not re.match(r"^\[[^\]]{1,40}\]", body):
                res = re.sub(r"^\[[^\]]{1,40}\]\s*(?=\S)", "", res)
            body = fix_translation(body, res or body)
        return f"[{sp}] {body}" if sp else body

    _LINE_RE = re.compile(r"^\[([^\]]+)\]\s*(.*)$")

    def _worth_translating(self, line):
        m = self._LINE_RE.match(line)
        body = m.group(2) if m else line
        return _needs_translation(body) and not self._already_target(body)

    def _repair_batch(self, batch, result, line_prompt):
        """Resposta de um lote → linhas pela ordem do lote. Linhas que o
        modelo deixou por traduzir (iguais ao original) ou comeu são
        traduzidas uma a uma — os modelos grátis às vezes saltam uma
        ('[PlayerTwo] WTS 2 чипа' ficava em russo)."""
        def split(line):
            m = self._LINE_RE.match(line)
            return ((_speaker_key(m.group(1)), m.group(2)) if m
                    else ("", line))
        outs = [l.strip() for l in (result or "").splitlines() if l.strip()]
        parsed = [split(l) + (l,) for l in outs]
        same_count = len(parsed) == len(batch)
        final, j, fixed = [], 0, 0
        for n, (_, line, _) in enumerate(batch):
            sp, body = split(line)
            hit = None
            if same_count:
                hit = n         # uma linha por mensagem, pela mesma ordem
            else:
                for k in range(j, len(parsed)):
                    if parsed[k][0] == sp or (
                            sp and parsed[k][0]
                            and _similar(parsed[k][0], sp) >= 0.6):
                        hit = k
                        break
            out = None
            if hit is not None and not _needs_translation(body):
                # Nada para traduzir ('[emote]', '+5', só itens): fica como
                # está, diga o modelo o que disser.
                j = hit + 1
                final.append(line)
                continue
            if hit is not None:
                j = hit + 1
                # O nome fica o original (alguns modelos traduzem-no ou
                # mudam-lhe as letras) e o corpo leva as correções.
                name = self._LINE_RE.match(line)
                fixed_body = fix_translation(body, parsed[hit][1])
                out = f"[{name.group(1)}] {fixed_body}" if name \
                    else fixed_body
                if ((self._body_key(parsed[hit][1]) == self._body_key(body)
                     or (self.cfg.mode != "mt"
                         and wrong_script(fixed_body, self.cfg.ocr_target)))
                        and _needs_translation(body)
                        and not self._already_target(body)):
                    out = None          # sem traduzir / noutro alfabeto
            if out is None and _needs_translation(body) \
                    and not self._already_target(body):
                fixed += 1
                try:
                    out = self._translate_one(line, line_prompt)
                except Exception as e:
                    log().warning(f"OCR: linha {line[:40]!r} — {e}")
                    out = line
            final.append(out if out is not None else line)
        if fixed:
            log().info(f"OCR: {fixed} linha(s) do lote traduzida(s) à "
                       f"parte (o modelo saltou-as)")
        return "\n".join(l for l in final if l)

    def _mention_check(self, lines):
        """Toca o som de menção (1x) se alguma destas mensagens escreve o
        meu nome. Antes da tradução: o nome fica igual em qualquer
        língua."""
        if not getattr(self.cfg, "mention_sound", False) or not self.tts:
            return
        hit = next((l for l in lines
                    if mentions_name(l, self.cfg.my_name)), None)
        if not hit:
            return
        log().info(f"OCR: o teu nome foi escrito no chat: {hit[:80]!r}")
        try:
            # Texto escrito = a voz di-lo (só para ti ouvires, nunca vai
            # para o chat) em vez do som.
            text = (getattr(self.cfg, "mention_text", "") or "").strip()
            if text:
                m = re.match(r"^\[([^\]]+)\]", hit)
                who = m.group(1).strip() if m else ""
                text = text.replace("{name}", who)
            self.tts.start_alert(
                "mention:" + (getattr(self.cfg, "mention_tone", "")
                              or "ding"),
                getattr(self.cfg, "mention_repeat", 1) or 1,
                getattr(self.cfg, "mention_every", 10) or 10,
                getattr(self.cfg, "mention_during", 30), text=text)
        except Exception:
            log().debug("cue mention", exc_info=True)

    def _show(self, result, speak=True, channel="all"):
        if not result:
            return
        log().info(f"OCR tradução [{channel}]: {result[:250]!r}")
        self._emit2("translated", channel or "all", result)
        if not speak:
            log().debug("TTS: histórico (arranque/separador novo) — não lido")
            return
        # Fala sempre, também com alt-tab (o overlay é que só aparece no
        # jogo): antes calava-se fora do jogo e perdiam-se mensagens.
        # Uma frase por mensagem: 'ExampleName says: hello'.
        for line in result.splitlines():
            speech = format_speech(line, self.cfg.ocr_target)
            if speech:
                self.tts.speak(speech)

    def _loop(self):
        time.sleep(1.5)
        tess_lang = resolve_tess_lang(self.cfg.ocr_source)

        tess_working = True
        try:
            ver = pytesseract.get_tesseract_version()
            log().info(f"Tesseract disponível: v{ver}")
        except Exception as e:
            tess_working = False
            log().error(f"Tesseract NÃO disponível: {e}")
            self.error.emit(T("[OCR] Tesseract is not working: {e}", e=e))

        if tess_working:
            self._setup_tessdata_env()

        cfg_parts = ["--psm 6"]
        if tess_lang:
            cfg_parts.append(f"-l {tess_lang}")
        tess_config = " ".join(cfg_parts)
        log().info(f"OCR config: '{tess_config}' | my_name='{self.cfg.my_name}'")

        first_run = True
        game_state = None
        prev_mask, raw, last_ocr = None, "", 0.0
        while self._running:
            try:
                if not tess_working:
                    time.sleep(5)
                    continue
                # Lê o painel do chat directamente da janela do jogo: o
                # overlay pode estar em qualquer sítio/tamanho, e com
                # alt-tab nunca se lê o browser.
                full = self.game.capture_client()
                img = self.game.crop_chat(full)
                if img is None:
                    if game_state != "missing":
                        game_state = "missing"
                        log().info("OCR: jogo não encontrado/minimizado")
                        self._emit("error",
                                   T("🎮 Waiting for the RF Online window…"))
                    time.sleep(2.0)
                    continue
                if game_state != "ok":
                    if game_state == "missing":
                        self._emit("error",
                                   T("🎮 Game found — reading the chat"))
                    game_state = "ok"

                # O OCR custa 2-3 s de CPU por ciclo: só se faz quando o
                # chat mudou. Chat fechado (nenhum separador aceso, ou a
                # barra de escrever diz que está fechado) = só o mundo do
                # jogo, que o OCR lia como lixo ('[emote] ...'): não se lê.
                tab = GameWindow.active_tab(full)
                if tab != self._tab_seen:
                    # Separador aceso mudou (abriste o chat / trocaste):
                    # a barra lê-se já, não a memória de há 2 s.
                    self._panel_state = (False, 0.0)
                # O System (avisos do jogo: drops, leilões...) é ignorado.
                # Com a zona do chat calibrada à mão o layout pode não ser o
                # padrão (separadores/barra noutro sítio): lê na mesma e o
                # chat conta como aberto se o OCR vir as etiquetas dos
                # canais à esquerda das mensagens (MSG_START).
                calibrated = chat_calibration() is not None
                closed = tab is None or not self._panel_open(full)
                if tab == "system" or (closed and not calibrated):
                    self._update_game_tab(full, tab)
                    time.sleep(self._read_gap())
                    continue
                t0 = time.time()
                # Letra sempre do tamanho de 1440p x2 (a zona calibrada pode
                # ter outra altura; a letra depende da altura do jogo).
                mask = preprocess_chat_image(img, 2.0 * 1440 / full.height)
                same = (prev_mask is not None
                        and prev_mask.size == mask.size
                        and time.time() - last_ocr < 15
                        and sum(ImageChops.difference(prev_mask, mask)
                                .histogram()[1:]) < self.SAME_FRAME_PX)
                prev_mask = mask
                if not same:
                    raw = ocr_chat_text(mask, tess_config).strip()
                    last_ocr = time.time()
                    self._perf_ocr = last_ocr - t0
                dt = time.time() - t0
                self._emit_perf()
                if closed and MSG_START not in raw:
                    self._update_game_tab(full, tab)
                    time.sleep(self._read_gap())
                    continue

                self._update_game_tab(full, tab)
                self._track_pm_sender(raw)
                # Linhas 'System ...' no All também não se traduzem.
                frame = [(ch, l) for ch, l in parse_ocr_messages(raw)
                         if ch != "system"]
                if first_run:
                    log().debug(f"OCR bruto ({dt*1000:.0f} ms) "
                                f"{len(raw)} chars → {len(frame)} msgs")
                first_run = False

                if self.cfg.my_name:
                    frame = [(ch, l) for ch, l in frame
                             if filter_my_messages(l, self.cfg.my_name)]
                for ch, l in frame:
                    self._note_lang(ch, l)

                pending = self._new_messages(frame)
                if pending:
                    log().info(f"OCR {len(pending)} msg nova(s): "
                               f"{chr(10).join(l for _, l, _ in pending)[:200]!r}")
                    # O som de 'escreveram o meu nome' toca já, antes da
                    # tradução (o nome fica igual em qualquer língua).
                    self._mention_check([l for _, l, _ in pending])
                    self._enqueue(pending)
                    self._save_seen()
                # Sem mensagens novas não há pedido nenhum à IA. O ritmo é
                # sempre o escolhido, também com o chat parado.
            except Exception as e:
                self._error_once(f"[OCR] {str(e)[:200]}")
                log().exception("OCR erro")
                time.sleep(2.0)
            if self._settling:
                self._settling = False
                time.sleep(self.SETTLE_GAP)
            else:
                time.sleep(self._read_gap())

    # ---------- fila de tradução ----------
    # A leitura do chat (OCR) e a tradução correm em threads separadas: o
    # OCR lê sempre ao seu ritmo e põe as mensagens novas nesta fila; outra
    # thread traduz pela ordem. Antes o ciclo parava de ler enquanto a IA
    # traduzia: com uma IA lenta (local só CPU ~3 s por mensagem, nuvem a
    # pensar, ou a esperar depois de um erro) o chat subia e as mensagens
    # saíam do ecrã antes de serem lidas — perdiam-se.
    MAX_TODO = 120          # acima disto as mais antigas vão sem tradução

    def _enqueue(self, pending):
        """Mensagens novas → fila. Entram já no histórico (lidas: não voltam
        a entrar); se a app fechar antes de as traduzir saem dele (stop)."""
        overflow = []
        now = time.time()
        if len(self._seen_at) > 500:
            self._seen_at.clear()
        with self._todo_cond:
            for item in pending:
                self._history.append(item[0])
                self._todo.append(item)
                self._seen_at.setdefault(item[0], now)
            while len(self._todo) > self.MAX_TODO:
                overflow.append(self._todo.popleft())
            self._todo_cond.notify_all()
        if overflow:
            # A IA não acompanha (em baixo / sem quota): o overlay mostra o
            # original em vez de as perder (sem voz).
            log().warning(f"Fila de tradução cheia — {len(overflow)} "
                          f"mostrada(s) sem tradução")
            for _, line, ch in overflow:
                self._show(line, False, ch)

    def _emit_perf(self, force=False):
        """Números do cabeçalho do overlay (no máx. 1x por segundo)."""
        now = time.time()
        if not force and now - self._perf_sent < 1.0:
            return
        self._perf_sent = now

        def avg(d):
            return round(sum(d) / len(d), 2) if d else None
        self._emit("perf", {
            "ai": avg(self._perf_ai), "lag": avg(self._perf_lag),
            "queue": len(self._todo) + len(self._inflight),
            "ocr": round(self._perf_ocr, 2) if self._perf_ocr else None,
            "err": self._ai_errors > 0, "mode": self.cfg.mode})

    def _take_batch(self, prompt):
        """Tira da fila o próximo pedido: 1 mensagem (IA local, uma a uma:
        os modelos pequenos trocam linhas em lote) ou um lote seguido do
        mesmo canal (nuvem/tradutores; mais linhas = menos pedidos)."""
        first = self._todo.popleft()
        batch = [first]
        if self.cfg.mode == "local":
            return batch
        limit = min(max(1, int(ai_opt(self.cfg, "batch_lines")
                               or self.BATCH_LINES)), self._batch_cap)
        budget = self.engine.input_budget_chars(prompt)
        size = len(first[1])
        while (self._todo and len(batch) < limit
               and self._todo[0][2] == first[2]
               and size + len(self._todo[0][1]) + 1 <= budget):
            size += len(self._todo[0][1]) + 1
            batch.append(self._todo.popleft())
        return batch

    def _translate_loop(self):
        prompt = build_ocr_prompt(self.cfg.ocr_source, self.cfg.ocr_target)
        line_prompt = build_ocr_line_prompt(self.cfg.ocr_source,
                                            self.cfg.ocr_target)
        retry_prompt = build_ocr_retry_prompt(self.cfg.ocr_source,
                                              self.cfg.ocr_target)
        bad_tries = 0
        while self._running:
            with self._todo_cond:
                while self._running and not self._todo:
                    self._todo_cond.wait(0.5)
                if not self._running:
                    break
                batch = self._take_batch(prompt)
                self._inflight = batch
            # O teu ditado (voz → chat) passa à frente na IA.
            voice_first.wait()
            try:
                ch = batch[0][2]
                t0 = time.time()
                if not any(self._worth_translating(line)
                           for _, line, _ in batch):
                    # Só stickers, números, itens ou já na tua língua: nem
                    # vai à IA (um '[emote]' sozinho voltava 'emote
                    # message').
                    result = "\n".join(line for _, line, _ in batch)
                elif self.cfg.mode == "local":
                    result = self._translate_one(batch[0][1], line_prompt)
                else:
                    result = self.engine.translate(
                        "\n".join(line for _, line, _ in batch), prompt)
                    result = self._repair_batch(batch, result, retry_prompt)
                self._inflight = []
                self._show(result, True, ch)
                now = time.time()
                self._perf_ai.append(now - t0)
                for key, _, _ in batch:
                    seen = self._seen_at.pop(key, None)
                    if seen:
                        self._perf_lag.append(now - seen)
                self._ai_errors = 0
                bad_tries = 0
                self._emit_perf(force=True)
                continue
            except requests.exceptions.RequestException as e:
                self._ai_errors += 1
                if isinstance(e, CloudError):
                    if is_context_error(e) and self._batch_cap > 1:
                        # Lote grande demais para este modelo: metade.
                        self._batch_cap = max(1, min(
                            self._batch_cap,
                            int(ai_opt(self.cfg, "batch_lines") or 8)) // 2)
                        log().warning(f"Lote reduzido a {self._batch_cap}")
                    self._error_once(f"⚠️ {e}", every=120.0
                                     if e.daily_limit else 30.0)
                elif isinstance(e, requests.exceptions.ConnectionError):
                    self._error_once(T("🔴 The AI engine is not "
                                       "responding — messages are on hold"))
                else:
                    self._error_once(T("[Network] {err}",
                                       err=str(e)[:160]))
                log().warning(f"IA: {e} — {len(self._todo) + len(batch)} "
                              f"mensagem(ns) à espera")
                long_wait = getattr(e, "daily_limit", False)
            except Exception as e:
                self._ai_errors += 1
                bad_tries += 1
                self._error_once(f"[OCR] {str(e)[:200]}")
                log().exception("Tradução: erro")
                long_wait = False
                if bad_tries >= 3:
                    # Erro que não é da rede e se repete com estas
                    # mensagens: mostra-as como estão e segue.
                    self._inflight = []
                    bad_tries = 0
                    for _, line, ch in batch:
                        self._show(line, False, ch)
                    continue
            # Falhou: voltam para a frente da fila, pela mesma ordem, e
            # tenta outra vez depois da espera (o OCR continua a ler).
            with self._todo_cond:
                self._todo.extendleft(reversed(batch))
                self._inflight = []
            self._emit_perf(force=True)
            self._backoff(long_wait)

    def _read_gap(self):
        """Segundos entre leituras do chat ('Leituras do chat por minuto';
        20/min = 3 s, a predefinição: menos pedidos às IAs na nuvem, que
        só recebem pedidos quando há mensagens novas). Sempre este ritmo,
        também com o chat parado."""
        n = int(getattr(self.cfg, "ocr_per_min", 20) or 20)
        return 60.0 / max(5, min(120, n))

    def _backoff(self, long_wait=False):
        """Depois de erros da IA espera cada vez mais (3, 6, 12… até 60 s;
        quota diária gasta: 5 min) em vez de repetir o mesmo pedido a
        cada 1,5 s — cada repetição gastava pedidos da quota grátis."""
        wait = 300 if long_wait else min(60.0, 1.5 * 2 ** self._ai_errors)
        end = time.time() + wait
        while self._running and time.time() < end:
            time.sleep(0.5)


# ==================================================================
# TESTE DE DESEMPENHO (📊 no Manual): a IA/tradutor corre bem neste PC?
# ==================================================================
# Frases no estilo do chat do RF (escritas para o teste, nomes genéricos):
# russo, português, espanhol, alemão, inglês, itens [..], WTB/WTS, gíria e
# um erro típico do OCR ('гдe' com 'e' latino).
BENCH_LINES = [
    "[PlayerOne] кто идёт на босса через 10 минут?",
    "[Hiro] продам [+10 Prime Anti-Gravity Drive] за 20к",
    "[PlayerTwo] парни, дайте пати 60+ пожалуйста",
    "[ExampleName] я ливаю с пати, всем спасибо",
    "[PlayerOne] у нас в ги уже такой дроп крутой",
    "[Hiro] синий навык нельзя обменять между серверами",
    "[PlayerTwo] WTB [Kallon Catalyst] 30 дней, пишите в лс",
    "[PlayerOne] alguém vai na dungeon agora? preciso de healer",
    "[Hiro] ¿quién va a la guerra de chips hoy?",
    "[PlayerTwo] wer kommt mit zum Boss?",
    "[ExampleName] Yes, we will keep growing.",
    "[PlayerOne] гдe босс? го в рейд",
]
# s por mensagem (local) / por pedido de 6 linhas (nuvem, tradutores):
# até ao 1.º = bom; até ao 2.º = aceitável; mais = lento num chat cheio.
BENCH_LIMITS = {"local": (2.0, 4.0), "cloud": (4.0, 8.0), "mt": (3.0, 6.0)}


def _bench_issues(src, out, target):
    """Problemas de uma linha traduzida no teste."""
    m = re.match(r"^\[([^\]]+)\]\s*(.*)$", src)
    body = m.group(2) if m else src
    om = re.match(r"^\[([^\]]+)\]\s*(.*)$", out or "")
    obody = om.group(2) if om else (out or "")
    if not obody.strip():
        return ["empty"]
    issues = []
    lang = detect_lang(_ITEM_RE.sub(" ", body))
    if lang and lang.split(" ")[0] != (target or "").split(" ")[0]:
        if OCRWorker._body_key(obody) == OCRWorker._body_key(body):
            issues.append("untranslated")
        elif wrong_script(obody, target):
            issues.append("script")
    if OCRWorker._META_RE.search(obody):
        issues.append("meta")
    if len(obody) > 3 * len(body) + 25:
        issues.append("invented")
    if any(i not in obody for i in _ITEM_RE.findall(body)):
        issues.append("item")
    words = re.findall(r"\w+", obody.lower())
    grams = [" ".join(words[i:i + 3]) for i in range(len(words) - 2)]
    if len(grams) != len(set(grams)):
        issues.append("repeat")
    return issues


def _ollama_fit(model):
    """Fração do modelo na placa gráfica (1.0 = cabe todo), ou None."""
    try:
        for m in requests.get(f"{OLLAMA_URL}/api/ps",
                              timeout=5).json().get("models", []):
            if (m.get("name") or m.get("model")) == model and m.get("size"):
                return m.get("size_vram", 0) / m["size"]
    except Exception:
        pass
    return None


def benchmark_translator(cfg, progress=None, stop=None, lines=None):
    """Traduz BENCH_LINES pelos mesmos caminhos da app (local: uma a uma;
    nuvem/tradutores: lotes de 6 com a reparação) e mede. progress(n, de,
    texto) a cada passo; stop (Event) interrompe. Devolve um dict."""
    lines = list(lines or BENCH_LINES)
    target = cfg.ocr_target or "English"
    eng = AIEngine(cfg)
    w = OCRWorker.__new__(OCRWorker)
    w.cfg, w.engine = cfg, eng
    line_prompt = build_ocr_line_prompt(cfg.ocr_source, target)
    prompt = build_ocr_prompt(cfg.ocr_source, target)
    retry = build_ocr_retry_prompt(cfg.ocr_source, target)
    res = {"mode": cfg.mode, "model": cfg.model, "target": target,
           "outs": [], "errors": [], "times": [], "warm": None}

    def say(n, text):
        if progress:
            progress(n, len(lines), text)
    if cfg.mode == "local":
        # 1.º pedido à parte: carrega o modelo na memória (só a 1.ª vez).
        say(0, T("Loading the model…"))
        t0 = time.time()
        try:
            w._translate_one("[X] привет", line_prompt)
        except Exception as e:
            res["errors"].append(str(e)[:200])
            return _bench_finish(res, lines)
        res["warm"] = time.time() - t0
        res["fit"] = _ollama_fit(cfg.model)
        for n, line in enumerate(lines):
            if stop is not None and stop.is_set():
                break
            say(n, line)
            t0 = time.time()
            try:
                out = w._translate_one(line, line_prompt)
            except Exception as e:
                res["errors"].append(str(e)[:200])
                out = ""
            res["times"].append(time.time() - t0)
            res["outs"].append(out)
    else:
        for i in range(0, len(lines), 6):
            if stop is not None and stop.is_set():
                break
            batch = [(("", ""), l, "all") for l in lines[i:i + 6]]
            say(i, lines[i])
            t0 = time.time()
            try:
                out = eng.translate("\n".join(l for _, l, _ in batch), prompt)
                out = w._repair_batch(batch, out, retry).splitlines()
            except Exception as e:
                res["errors"].append(str(e)[:200])
                out = []
            res["times"].append(time.time() - t0)
            res["outs"] += (out + [""] * len(batch))[:len(batch)]
    return _bench_finish(res, lines)


def _bench_finish(res, lines):
    outs = res["outs"]
    res["issues"] = [_bench_issues(s, o, res["target"])
                     for s, o in zip(lines, outs)]
    t = res["times"]
    res["per_req"] = sum(t) / len(t) if t else None
    bad = sum(1 for i in res["issues"] if i)
    good, ok = BENCH_LIMITS.get(res["mode"], BENCH_LIMITS["cloud"])
    if not outs or len(res["errors"]) >= max(1, len(t)):
        res["verdict"] = "fail"
    elif res["per_req"] > ok or bad > 0.25 * len(outs):
        res["verdict"] = "bad"
    elif res["per_req"] > good or bad > 0.1 * len(outs) or res["errors"]:
        res["verdict"] = "ok"
    else:
        res["verdict"] = "good"
    res["bad_lines"] = bad
    return res


def benchmark_gpu_layers(cfg, progress=None, stop=None):
    """IA local: a mesma frase com a placa gráfica (Automático) e só com o
    processador (0 camadas). Diz o que é mais rápido neste PC com o jogo
    aberto. [(camadas, s por mensagem, fração na placa)]."""
    out = []
    sample = BENCH_LINES[:4]
    for gl in (-1, 0):
        if stop is not None and stop.is_set():
            break
        c = dc_replace(cfg, gpu_layers=gl)
        r = benchmark_translator(c, progress, stop, sample)
        out.append((gl, r.get("per_req"), r.get("fit"), r.get("verdict")))
    return out


# ==================================================================
# VOICE WORKER
# ==================================================================
class VoiceCancelled(Exception):
    """Carregaste na tecla de cancelar a meio de um ditado."""


class VoiceWorker(QObject):
    status = pyqtSignal(str)
    finished = pyqtSignal()
    # Indicador no overlay: 'listen' (a ouvir), 'busy' (a traduzir), ''.
    voice_state = pyqtSignal(str)
    # Frase enviada: (o que disseste, o que foi escrito no jogo).
    spoken = pyqtSignal(str, str)

    # Início da frase que pede resposta por PM. O Google em pt-PT escreve
    # 'reply' muitas vezes como 'replay' / 'répli'.
    REPLY_RE = re.compile(
        r"^\s*(?:reply|replay|repl[ae]i|r[eé]pli|responde(?:r)?|resposta)"
        r"\b[\s,.:;!\-]*", re.I)

    def __init__(self, engine, cfg, game=None, chat_open=None, tts=None,
                 on_done=None, reply_target=None, lang_hint=None,
                 current_channel=None, release_event=None,
                 continuous_stop=None, cancel_event=None):
        super().__init__()
        self.engine = engine
        self.cfg = cfg
        self.game = game
        self.chat_open = chat_open      # callable → bool (do OCRWorker)
        self.tts = tts
        self.on_done = on_done          # chamado nesta thread no fim
        self.reply_target = reply_target  # callable → nome do último PM
        self.lang_hint = lang_hint      # OCRWorker.guess_target_lang
        self.current_channel = current_channel  # callable → separador
        self.release_event = release_event  # largar o atalho (push-to-talk)
        self.continuous_stop = continuous_stop  # Event: modo contínuo
        # Tecla de cancelar: pára de ouvir/traduzir/escrever e apaga o que
        # já tinha escrito no chat (nunca carrega no Enter).
        self.cancel_event = cancel_event or threading.Event()
        # Modo 'confirmar antes de enviar': o texto fica escrito no chat
        # até confirm_event (✔ Enviar / atalho outra vez).
        self.confirm_event = threading.Event()
        self.awaiting = False

    def _cancelled(self):
        return self.cancel_event.is_set()

    def _check_cancel(self):
        if self.cancel_event.is_set():
            raise VoiceCancelled()

    def _cancellable(self, source):
        """A leitura do micro rebenta logo que cancelas (o listen() do
        speech_recognition não tem outra forma de parar a meio)."""
        stream = source.stream
        orig = stream.read

        def read(*a, **k):
            if self.cancel_event.is_set():
                raise VoiceCancelled()
            return orig(*a, **k)
        stream.read = read

    def _switch_channel(self, channel):
        """Comando de voz: muda o separador do chat no jogo (só clica,
        não escreve nada)."""
        if self.game is None:
            return
        if not self.game.is_foreground() \
                and self.game.foreground_is_own_process():
            self.game.activate()
            time.sleep(0.2)
        if not self.game.is_foreground():
            self.status.emit(T("[⚠️ The game is not in front]"))
            return
        t0 = time.time()
        while self.game.modifiers_down() and time.time() - t0 < 2.0:
            time.sleep(0.05)
        if self.game.wake() is None:
            self.status.emit(T("[⚠️ The game is in sleep mode — press L "
                               "in the game; nothing written]"))
            return
        if self.chat_open is not None and not self.chat_open():
            kb = Controller()
            kb.press(Key.enter); kb.release(Key.enter)   # abre o chat
            time.sleep(0.6)
        if self.game.click_tab(channel):
            self.status.emit(f"[💬 Chat: {channel}]")
            log().info(f"Voice: separador → {channel}")
        else:
            self.status.emit(T("[⚠️ Could not switch to {ch}]", ch=channel))

    _mic_cache = None       # (índice da config, índice que abre)
    _threshold = 300        # limiar de energia (adapta-se e fica guardado)
    _dynamic = True         # sem calibração (ou ruído 0): limiar adaptativo

    HOLD_MIN = 0.35         # s: menos que isto = toque sem falar
    HOLD_MAX = 30           # s: push-to-talk nunca grava mais do que isto
    TAP_PAUSE = 1.5         # s de silêncio que acabam o modo 'toque'

    def _record(self, rec, source):
        """Push-to-talk ('hold'): grava enquanto o atalho está carregado e
        pára quando o largas — com TV/jogo a entrar no micro nunca há
        silêncio. Um toque rápido não grava nada (devolve None).
        Toque ('auto'): ouve até uma pausa longa na fala."""
        ev = self.release_event
        if ev is None or getattr(self.cfg, "voice_mode", "hold") == "auto":
            rec.pause_threshold = self.TAP_PAUSE
            return rec.listen(source, timeout=6, phrase_time_limit=25)
        frames, t0 = [], time.time()
        while not ev.is_set() and time.time() - t0 < self.HOLD_MAX:
            frames.append(source.stream.read(source.CHUNK))
        self._check_cancel()
        held = time.time() - t0
        if held < self.HOLD_MIN:
            log().info("Voice: push-to-talk largado logo — nada gravado")
            return None
        log().info(f"Voice: push-to-talk {held:.1f}s")
        return sr.AudioData(b"".join(frames), source.SAMPLE_RATE,
                            source.SAMPLE_WIDTH)

    @classmethod
    def calibrate(cls, cfg, seconds=1.0):
        """Mede o ruído de fundo do micro (ao arrancar a app, quando ainda
        não estás a falar) e põe o limiar de 'estás a falar' acima dele.
        Com o USB Mic o ruído tem energia ~350 e o limiar fixo era 300:
        a app achava que estavas sempre a falar e cortava as frases nos
        sítios errados (modos 'toque' e 'contínuo')."""
        if not (SR_OK and PYAUDIO_OK):
            return None
        try:
            try:
                import audioop
            except ImportError:
                import audioop_lts as audioop
            want = (cfg.mic_device_index, getattr(cfg, "mic_device_name", ""))
            idx, _ = resolve_mic(*want)
            cls._mic_cache = (want, idx)
            with sr.Microphone(device_index=idx) as src:
                per_s = src.SAMPLE_RATE / src.CHUNK
                # O micro acabado de abrir dá ~0,3 s de silêncio digital
                # (a medição dava 'ruído 0' e o limiar ficava baixo demais).
                for _ in range(int(per_s * 0.3)):
                    src.stream.read(src.CHUNK)
                n = max(1, int(per_s * seconds))
                e = sorted(audioop.rms(src.stream.read(src.CHUNK),
                                       src.SAMPLE_WIDTH) for _ in range(n))
            noise = e[int(len(e) * 0.9)]
            # Ainda 0 = micro calado/desligado: sem medição fiável, o
            # limiar adapta-se sozinho durante a gravação (como antes).
            cls._dynamic = noise < 30
            cls._threshold = max(300, min(noise * 2.0, 6000))
            log().info(f"Voice: ruído de fundo {noise} → limiar "
                       f"{cls._threshold:.0f}"
                       + (" (adaptativo)" if cls._dynamic else ""))
            return cls._threshold
        except Exception:
            log().exception("Voice: calibração do micro falhou")
            return None

    def _beep(self, kind="start"):
        """Bip: 'start' = já estou a gravar, fala; 'stop' = acabou de
        gravar. Sai pelos headphones (mesma saída da voz da app)."""
        if self.tts is not None:
            self.tts.cue(kind)
            return
        try:
            import winsound
            winsound.Beep(880, 120)
        except Exception:
            pass

    @staticmethod
    def _boost_audio(audio):
        """Normaliza o volume antes do reconhecimento. Micro baixo ou a
        sair de um voice changer chegava com pico ~1% da escala e o
        Google não percebia nada."""
        try:
            import audioop
        except ImportError:
            try:
                import audioop_lts as audioop
            except ImportError:
                return audio
        raw, w = audio.frame_data, audio.sample_width
        peak = audioop.max(raw, w)
        full = (1 << (8 * w - 1)) - 1
        # Suave: com o USB Mic (pico ~8%) o ganho x10 amplificava também o
        # ruído e o Google inventava palavras ('a a a a ... 212'); sem
        # ganho percebia bem. Só mexe se estiver quase inaudível, máx. x3.
        if 0 < peak < full * 0.03:
            factor = min(full * 0.1 / peak, 3.0)
            raw = audioop.mul(raw, w, factor)
            log().info(f"Voice: volume baixo (pico {peak}) — ganho x{factor:.1f}")
            return sr.AudioData(raw, audio.sample_rate, w)
        return audio

    @staticmethod
    def _clean_translation(text):
        """Só a frase traduzida: os modelos pequenos às vezes juntam
        'Перевод:', aspas ou uma 2.ª linha de explicação — e isso ia
        parar ao chat do jogo."""
        text = next((l for l in (text or "").splitlines() if l.strip()), "")
        text = re.sub(r"^\s*(?:translation|tradução|traducción|перевод|"
                      r"übersetzung|traduction)\s*:\s*", "", text, flags=re.I)
        return text.strip().strip('"“”«»\'').strip()

    def trigger(self):
        threading.Thread(target=self._run, daemon=True,
                         name="VoiceWorker").start()

    def _open_mic(self):
        """(Recognizer, Microphone) prontos a gravar. O micro resolve-se
        1x por sessão e o limiar vem da gravação anterior: antes perdia-se
        ~1 s do início da frase a testar o micro e a medir o ruído (e se
        já estavas a falar a medição subia o limiar e cortava palavras)."""
        rec = sr.Recognizer()
        cls = type(self)
        want = (self.cfg.mic_device_index,
                getattr(self.cfg, "mic_device_name", ""))
        if cls._mic_cache is None or cls._mic_cache[0] != want:
            mic_index, mic_desc = resolve_mic(*want)
            cls._mic_cache = (want, mic_index)
            if mic_index != self.cfg.mic_device_index:
                self.status.emit(T("[🎤 Mic: {d}]", d=mic_desc))
        mic_index = cls._mic_cache[1]
        mic = (sr.Microphone(device_index=mic_index)
               if mic_index is not None else sr.Microphone())
        rec.energy_threshold = cls._threshold
        # Fixo no valor calibrado: o ajuste automático descia o limiar até
        # ao ruído do micro e o modo toque/automático gravava 13 s de
        # ruído sem ninguém falar (o Ctrl+S seguinte era ignorado). Sem
        # calibração fiável (ruído 0) fica o ajuste automático.
        rec.dynamic_energy_threshold = cls._dynamic
        rec.pause_threshold = 1.0        # pausas a meio da frase
        return rec, mic

    # Palavras de jogo que o reconhecimento em português troca por outras
    # parecidas ('boss' → 'vosso'). O Google dá várias hipóteses: fica a
    # que tem estas palavras quando a 1.ª não tem.
    GAME_TERMS = re.compile(
        r"\b(?:boss(?:es)?|dungeon|dg|party|guild|raid|farm\w*|drop|loot|"
        r"buff|debuff|tank|healer|heal|dps|pvp|pve|skins?|set|upgrade|"
        r"craft|quest|mobs?|spawn|respawn|arena|item|gold|wtb|wts|afk|"
        r"lag|lvl|level|exp|xp|nerf|combo|skills?|mana|hp|mp|pots?|"
        r"potion|login|logar|server)\b", re.I)

    def _recognize(self, rec, audio):
        stt_code = LANGUAGES.get(self.cfg.voice_source,
                                  {}).get("stt") or "en-US"
        audio = self._boost_audio(audio)    # o áudio nunca vai para disco
        res = rec.recognize_google(audio, language=stt_code, show_all=True)
        alts = [a.get("transcript", "") for a in
                (res.get("alternative", []) if isinstance(res, dict) else [])
                if a.get("transcript")]
        if not alts:
            raise sr.UnknownValueError()
        text = alts[0]
        if not self.GAME_TERMS.search(text):
            game = next((a for a in alts[1:] if self.GAME_TERMS.search(a)),
                        None)
            if game:
                log().info(f"STT: hipótese com palavra de jogo escolhida "
                           f"({text!r} → {game!r})")
                text = game
        log().info(f"STT ({stt_code}): {text!r}  [{len(alts)} hipóteses]")
        return text

    def _run(self):
        try:
            if not SR_OK:
                self.status.emit(T("[⚠️ Voice unavailable: {e}]", e=SR_ERR))
                return
            if not PYNPUT_OK:
                self.status.emit(T("[⚠️ pynput unavailable]"))
                return
            if self.continuous_stop is not None:
                self._run_continuous()
                return
            self.status.emit("[🎤 ...]")
            log().info("Voice: começar a gravar")
            if self.tts:
                self.tts.pause()
            cls = type(self)
            rec, mic = self._open_mic()
            try:
                try:
                    source = mic.__enter__()
                except Exception:
                    cls._mic_cache = None    # micro mudou: re-resolve
                    raise
                try:
                    self._cancellable(source)
                    self._beep("start")
                    self.voice_state.emit("listen")
                    self.status.emit(T("[🎤 Speak now]"))
                    audio = self._record(rec, source)
                    self._beep("stop" if audio is not None else "cancel")
                    self.voice_state.emit("busy" if audio is not None
                                          else "")
                finally:
                    mic.__exit__(None, None, None)
                # Guarda o limiar já adaptado ao teu micro/ambiente.
                cls._threshold = max(150, min(rec.energy_threshold, 4000))
            finally:
                if self.tts:
                    self.tts.resume()
            self._check_cancel()
            if audio is None:
                self.status.emit(T("[⚠️ Hold the key down while you talk]"))
                return
            self.status.emit("[🧠 ...]")
            text_src = self._recognize(rec, audio)
            self._check_cancel()
            if not text_src.strip():
                self.status.emit(T("[⚠️ Nothing detected]"))
                return
            self._handle_text(text_src)
        except VoiceCancelled:
            log().info("Voice: cancelado pela tecla de cancelar")
        except sr.WaitTimeoutError:
            self.status.emit(T("[⌛ No audio]"))
        except sr.UnknownValueError:
            self.status.emit(T("[❓ Audio not recognized]"))
        except Exception as e:
            self.status.emit(T("[Error] {e}", e=e))
            log().exception("Voice worker erro")
        finally:
            self.voice_state.emit("")
            if self.on_done:
                try:
                    self.on_done()
                except Exception:
                    log().exception("Voice on_done")
            self.finished.emit()

    # Com a voz do chat a tocar, falar tem de ser x2,5 mais alto que o
    # limiar para começar uma frase: com colunas o micro apanha a voz da
    # app (eco) e mandava-a para o chat.
    BARGE_IN = 2.5
    PHRASE_MAX = 15         # s no máximo por frase

    def _listen_phrase(self, rec, source, stop):
        """Uma frase do modo contínuo, enquanto a voz do chat continua a
        ler. Quando começas a falar a voz cala-se (a frase dela volta a ser
        lida depois) e grava até uma pausa longa. None = desligado;
        'noise' = um estalo curto, não uma frase."""
        try:
            import audioop
        except ImportError:
            import audioop_lts as audioop
        chunk, width = source.CHUNK, source.SAMPLE_WIDTH
        per = chunk / source.SAMPLE_RATE
        pre = deque(maxlen=max(1, int(0.5 / per)))   # início da 1.ª sílaba
        frames, silent, t0, voiced = None, 0.0, 0.0, 0.0
        while not stop.is_set():
            buf = source.stream.read(chunk)
            e = audioop.rms(buf, width)
            thr = rec.energy_threshold
            if frames is None:
                playing = self.tts is not None and self.tts.is_playing()
                if e > thr * (self.BARGE_IN if playing else 1.0):
                    frames, silent, t0 = list(pre) + [buf], 0.0, time.time()
                    voiced = per
                    if self.tts:
                        self.tts.pause()
                    continue
                pre.append(buf)
                if rec.dynamic_energy_threshold and not playing:
                    damp = rec.dynamic_energy_adjustment_damping ** per
                    rec.energy_threshold = max(150, thr * damp + e
                                               * rec.dynamic_energy_ratio
                                               * (1 - damp))
                continue
            frames.append(buf)
            if e > thr:
                silent, voiced = 0.0, voiced + per
            else:
                silent += per
            if silent >= rec.pause_threshold \
                    or len(frames) * per > self.PHRASE_MAX:
                break
        if frames is None:
            return None
        if voiced < 0.3:
            return "noise"          # estalo/tosse: não é uma frase
        return sr.AudioData(b"".join(frames), source.SAMPLE_RATE, width)

    def _run_continuous(self):
        """Modo contínuo: ouve sempre; cada frase (acaba numa pausa longa)
        é traduzida e enviada. O atalho outra vez desliga.
        A voz que lê o chat continua a ler entre as tuas frases (cala-se
        quando falas). Com 'ouvir o chat no modo contínuo' desligado fica
        calada o tempo todo, como antes (para quem usa colunas)."""
        stop = self.continuous_stop
        cls = type(self)
        hear = bool(getattr(self.cfg, "continuous_tts", True))
        if self.tts and not hear:
            self.tts.pause()
        rec, mic = self._open_mic()
        rec.pause_threshold = 1.3            # pausa longa = fim da frase
        try:
            source = mic.__enter__()
        except Exception:
            cls._mic_cache = None
            if self.tts:
                self.tts.resume()
            raise
        self._cancellable(source)
        self._beep("start")
        self.voice_state.emit("listen")
        self.status.emit(T("[🎙️ Continuous ON — talk; a long pause sends. "
                           "Hotkey again turns it off]"))
        log().info("Voice: modo contínuo ligado")
        try:
            while not stop.is_set():
                try:
                    audio = self._listen_phrase(rec, source, stop)
                    if audio is None or stop.is_set():
                        break
                    if hear and self.tts:
                        # A frase acabou: o chat volta a ser lido enquanto
                        # a tua é reconhecida, traduzida e escrita.
                        self.tts.resume()
                    if audio == "noise":
                        continue
                    try:
                        text = self._recognize(rec, audio)
                    except sr.UnknownValueError:
                        continue
                    self._check_cancel()
                    if text.strip():
                        self.voice_state.emit("busy")
                        self._handle_text(text)
                except sr.WaitTimeoutError:
                    continue
                except VoiceCancelled:
                    # Só descarta esta frase; o atalho é que desliga.
                    log().info("Voice contínuo: frase cancelada")
                except Exception as e:   # uma frase falhada não desliga
                    self.status.emit(T("[Error] {e}", e=e))
                    log().exception("Voice contínuo: frase falhou")
                finally:
                    self.cancel_event.clear()
                    if hear and self.tts:
                        self.tts.resume()
                    if not stop.is_set():
                        self.voice_state.emit("listen")
                cls._threshold = max(150, min(rec.energy_threshold, 4000))
        finally:
            mic.__exit__(None, None, None)
            if self.tts:
                self.tts.resume()
            self._beep("stop")
            self.status.emit(T("[🎙️ Continuous OFF]"))
            log().info("Voice: modo contínuo desligado")

    def _handle_text(self, text_src):
        """Frase reconhecida → comando de canal, reply ou mensagem: traduz
        para a língua certa e escreve no chat."""
        self.status.emit(f"[{lang_label(self.cfg.voice_source)}] {text_src}")
        # 'reply ...' / 'responde ...' → PM a quem me mandou o último.
        reply_to = None
        m = self.REPLY_RE.match(text_src)
        if m:
            reply_to = self.reply_target() if self.reply_target else None
            if not reply_to:
                self.status.emit(T("[⚠️ Reply: I haven't seen any received PM "
                                   "(open the chat so I can read it)]"))
                return
            text_src = text_src[m.end():].strip()
            if not text_src:
                self.status.emit(T("[⚠️ Reply without a message]"))
                return
            self.status.emit(T("[↩️ PM to {n}]", n=reply_to))
            log().info(f"Voice: reply para {reply_to}: {text_src!r}")
        else:
            # 'muda para o chat server' → só troca o separador.
            cmd = parse_chat_command(text_src)
            if cmd:
                self._switch_channel(cmd)
                return
        # Língua de destino automática: a de quem me escreveu (reply)
        # ou a mais usada no canal aberto; senão a da config.
        target, why = self.cfg.voice_target, T("settings")
        if self.lang_hint:
            try:
                if reply_to:
                    auto = self.lang_hint(speaker=reply_to)
                    why = T("{n}'s language", n=reply_to)
                else:
                    ch = self.current_channel() \
                        if self.current_channel else None
                    if ch in (None, "all") and self.game:
                        # No 'All' escreve-se no canal da barra de baixo.
                        ch = self.game.read_input_row()[0] or ch
                    auto = self.lang_hint(channel=ch)
                    why = T("language of channel {ch}", ch=ch)
                if auto:
                    target = auto
                else:
                    why = T("settings")
            except Exception:
                log().exception("lang_hint")
        same = target.split(" ")[0] == self.cfg.voice_source.split(" ")[0]
        if same:
            # Ali já se fala a minha língua: vai como eu disse.
            text_out = text_src
            self.status.emit(T("[🌐 {lang} ({why}) — no translation]", lang=lang_label(target), why=why))
        else:
            self.status.emit(f"[🌐 → {lang_label(target)} ({why})]")
            text_out = self._translate_voice(text_src, target)
        log().info(f"Voice → {target} ({why}): {text_out!r}")
        self._check_cancel()
        if not text_out:
            self.status.emit(T("[⚠️ Empty translation]"))
            return
        self.status.emit(f"[{lang_label(target)}] {text_out}")
        if self._type_in_game(text_out, reply_to=reply_to):
            self.status.emit(T("[✅ Sent]"))
            # O overlay mostra a fala no chat uns segundos e guarda-a no
            # separador '🎤 Eu'.
            self.spoken.emit(text_src, text_out)

    def _translate_voice(self, text_src, target):
        """Corrige as palavras de jogo mal ouvidas e traduz. Para destinos
        que não o inglês vai em 2 passos (corrigir→inglês, inglês→destino):
        num só passo o modelo pequeno misturava línguas ('Olá как
        дела… amigo'); em inglês acertava sempre."""
        with voice_first():
            return self._translate_voice_now(text_src, target)

    def _translate_voice_now(self, text_src, target):
        src = self.cfg.voice_source
        if self.engine.cfg.mode == "mt":
            # Sem IA: tradução direta (o Google/Argos não corrige palavras
            # mal ouvidas).
            return self._clean_translation(mt_translate(
                getattr(self.engine.cfg, "mt_engine", "google"),
                text_src, target, source=src))
        if target == "English" or self.engine.cfg.mode != "local":
            return self._clean_translation(self.engine.translate(
                text_src, build_voice_prompt(src, target)))
        english = self._clean_translation(self.engine.translate(
            text_src, build_voice_prompt(src, "English")))
        if not english:
            return ""
        log().info(f"Voice: via inglês: {english!r}")
        return self._clean_translation(self.engine.translate(
            english, f"Translate this English MMORPG chat message into "
                     f"{target}. Every word must be in {target}. Keep "
                     "gaming terms accurate. Respond ONLY with the "
                     "translation, no quotes, no explanations."))

    def _in_game(self):
        return self.game is None or self.game.is_foreground()

    def _erase(self, kb, n):
        """Apaga n letras acabadas de escrever (cancelado a meio)."""
        for _ in range(n):
            if not self._in_game():
                return
            kb.press(Key.backspace); kb.release(Key.backspace)
            time.sleep(0.03)

    def _type_slow(self, kb, text):
        """Escreve letra a letra; False se saíres do jogo a meio. Se
        cancelares, apaga o que já escreveu e levanta VoiceCancelled."""
        for n, ch in enumerate(text):
            if self._cancelled():
                self._erase(kb, n)
                raise VoiceCancelled()
            if not self._in_game():
                log().info("Voice: alt-tab durante a escrita — parado")
                self.status.emit(T("[⚠️ Stopped: you left the game]"))
                return False
            try: kb.type(ch)
            except Exception: pass
            # O jogo perde letras abaixo de ~50 ms entre teclas (a 15-45
            # ms só entrava a 1.ª); testado OK a 50/80/120 ms, também em
            # cirílico. Não aceita Ctrl+V.
            time.sleep(random.uniform(0.07, 0.11))
        return True

    @staticmethod
    def _name_matches(seen, name):
        want = _speaker_key(name)
        got = _speaker_key(seen.split(" ")[0]) if seen else ""
        return bool(want) and (want == got or _similar(want, got) >= 0.8)

    def _set_whisper_target(self, kb, name):
        """Separador Whisper → (se preciso) destinatário = name.
        Confirma cada passo com OCR da barra de baixo antes de escrever:
        sem caixa de texto ativa as letras iam para o jogo como atalhos."""
        channel, rest = "", ""
        for attempt in range(2):
            if not self.game.click_rel(*CHAT_TAB_WHISPER_REL):
                self.status.emit(T("[⚠️ Not sent: you left the game]"))
                return False
            # O painel anima ao trocar de separador e durante isso a barra
            # lê-se vazia: repete a leitura até ~3 s.
            t0 = time.time()
            while time.time() - t0 < 3.0:
                time.sleep(0.4)
                channel, rest = self.game.read_input_row()
                if channel.startswith("whis"):
                    break
            log().info(f"Reply: barra do chat = {channel!r} {rest!r}")
            if channel.startswith("whis"):
                break
        else:
            self.status.emit(T("[⚠️ Reply: could not open Whisper — "
                               "nothing written]"))
            return False
        if self._name_matches(rest, name):
            return True                     # já é a conversa certa
        if not self.game.click_rel(*CHAT_RECIPIENT_REL):
            self.status.emit(T("[⚠️ Not sent: you left the game]"))
            return False
        time.sleep(0.3)
        kb.press(Key.end); kb.release(Key.end)
        for _ in range(30):                 # apaga o nome anterior
            if not self._in_game():
                return False
            kb.press(Key.backspace); kb.release(Key.backspace)
            time.sleep(0.03)
        if not self._type_slow(kb, name):
            return False
        t0 = time.time()
        while time.time() - t0 < 2.0:
            time.sleep(0.4)
            channel, rest = self.game.read_input_row()
            if channel.startswith("whis") and self._name_matches(rest, name):
                break
        if not (channel.startswith("whis") and self._name_matches(rest, name)):
            log().info(f"Reply: destinatário não confirmado ({rest!r})")
            self.status.emit(T("[⚠️ Reply: could not set '{n}' as the "
                               "recipient — message not written]", n=name))
            return False
        return True

    CONFIRM_WAIT = 120      # s à espera do ✔; depois fica escrito sem enviar

    def _wait_confirm(self, kb, text):
        """Texto escrito no chat, Enter por carregar: espera pelo ✔ Enviar
        (ou o atalho outra vez). Cancelar apaga-o. True = envia."""
        self.confirm_event.clear()
        self.awaiting = True
        self.voice_state.emit("confirm")
        self.status.emit(T("[✋ Written, not sent — press ✔ Send (or the "
                           "voice hotkey again); Esc erases it]"))
        log().info("Voice: à espera de confirmação")
        try:
            t0 = time.time()
            while not self.confirm_event.is_set():
                if self._cancelled():
                    if self.game and not self._in_game() \
                            and self.game.foreground_is_own_process():
                        self.game.activate()
                        time.sleep(0.2)
                    self._erase(kb, len(text))
                    raise VoiceCancelled()
                if time.time() - t0 > self.CONFIRM_WAIT:
                    self.status.emit(T("[⌛ Not confirmed — the text stays "
                                       "in the chat, not sent]"))
                    return False
                time.sleep(0.05)
        finally:
            self.awaiting = False
            self.voice_state.emit("busy")
        # Clicaste no ✔ do overlay: o foco volta ao jogo antes do Enter.
        if self.game and not self._in_game() \
                and self.game.foreground_is_own_process():
            self.game.activate()
            time.sleep(0.25)
        log().info("Voice: confirmado")
        return True

    def _type_in_game(self, text, reply_to=None):
        """Abre o chat se preciso, clica na caixa de texto, escreve e
        envia — sem teres de clicar no chat. Nunca escreve fora do jogo:
        se fizeres alt-tab pára (e não carrega no Enter). Com reply_to
        manda como PM a essa pessoa (separador Whisper)."""
        # Foco no overlay/config desta app (clicaste-lhe): devolve-o ao
        # jogo antes de clicar e escrever.
        if self.game and not self._in_game() \
                and self.game.foreground_is_own_process():
            self.game.activate()
            time.sleep(0.2)
        if not self._in_game():
            self.status.emit(T("[⚠️ Not sent: the game is not in "
                               "the foreground]"))
            log().info("Voice: jogo não está em primeiro plano — cancelado")
            return False
        # Espera que largues o Ctrl/Shift/Alt do atalho (senão o clique
        # vira Ctrl+clique e as letras viram atalhos).
        t0 = time.time()
        while self.game and self.game.modifiers_down() \
                and time.time() - t0 < 2.0:
            time.sleep(0.05)
        # Modo de poupança do jogo: o chat vê-se mas não recebe teclas.
        # Acorda-o (tecla L) e no fim volta a pô-lo a dormir.
        woke = self.game.wake() if self.game else False
        if woke is None:
            self.status.emit(T("[⚠️ The game is in sleep mode — press L "
                               "in the game; nothing written]"))
            return False
        try:
            return self._type_in_game_now(text, reply_to)
        finally:
            if woke:
                time.sleep(0.5)
                if self.game.is_foreground() \
                        and not GameWindow.sleep_mode(
                            self.game.capture_client()):
                    self.game.toggle_sleep()
                    log().info("Jogo de volta ao modo de poupança")

    def _type_in_game_now(self, text, reply_to=None):
        log().info(f"A digitar no jogo ({len(text)} chars)")
        kb = Controller()
        time.sleep(0.15)
        if self.game:
            if self.chat_open is not None and not self.chat_open():
                # Chat fechado: Enter abre-o (o ícone diz 'ENTER').
                kb.press(Key.enter); kb.release(Key.enter)
                time.sleep(0.6)
            if reply_to and not self._set_whisper_target(kb, reply_to):
                return False        # _set_whisper_target já disse porquê
            if not reply_to:
                channel, _ = self.game.read_input_row()
                if channel.startswith("system"):
                    # Separador System é só de leitura: as letras iam
                    # para o jogo como atalhos.
                    self.status.emit(T("[⚠️ Chat is on 'System' (read only) — "
                                       "switch tab; nothing written]"))
                    return False
            if not self.game.click_chat_input():
                self.status.emit(T("[⚠️ Not sent: you left the game]"))
                return False
            time.sleep(0.3)     # a caixa demora a ganhar o foco
        else:
            kb.press(Key.enter); kb.release(Key.enter)
            time.sleep(0.1)
        if not self._type_slow(kb, text):
            return False
        time.sleep(0.15)
        if self._cancelled():           # cancelado mesmo antes do Enter
            self._erase(kb, len(text))
            raise VoiceCancelled()
        if getattr(self.cfg, "voice_confirm", False) \
                and not self._wait_confirm(kb, text):
            return False
        if not self._in_game():
            self.status.emit(T("[⚠️ Not sent: the game is not in "
                               "the foreground]"))
            return False
        kb.press(Key.enter); kb.release(Key.enter)
        log().info("Digitação concluída")
        return True


# ==================================================================
# HOTKEY LISTENER — thread-safe (só chama os callbacks, NUNCA Qt direto)
# ==================================================================
class HotkeyListener:
    def __init__(self, on_voice, voice_hotkey="f11",
                 on_toggle_lock=None, lock_hotkey="ctrl+shift+l",
                 should_capture=None, on_cancel=None, cancel_hotkey="",
                 cancel_active=None):
        self.on_voice = on_voice
        # Tecla de cancelar o ditado: só é 'engolida' enquanto há um
        # ditado a decorrer (cancel_active); fora disso chega ao jogo
        # normalmente (ex.: Esc).
        self.on_cancel = on_cancel
        self.cancel_active = cancel_active
        self.cancel_spec = parse_hotkey(cancel_hotkey) if cancel_hotkey \
            else None
        self._cancel_vk = self._spec_vk(self.cancel_spec) \
            if (os.name == "nt" and self.cancel_spec) else None
        self._cancel_suppressing = False
        self.voice_spec = parse_hotkey(voice_hotkey) or {"key": "f11"}
        # Com o jogo à frente o atalho é 'engolido' (não chega ao jogo):
        # o S do Ctrl+S é andar para trás e o boneco parava de atacar.
        self.should_capture = should_capture
        self._voice_vk = self._spec_vk(self.voice_spec) if os.name == "nt" \
            else None
        self._suppressing = False
        self.release_event = None   # set() quando largas o atalho
        self.lock_spec = parse_hotkey(lock_hotkey) or {
            "key": "l", "ctrl": True, "shift": True}
        self.on_toggle_lock = on_toggle_lock
        self._listener = None
        self._mods = {"ctrl": False, "shift": False, "alt": False,
                      "win": False}
        self._last_voice_fire = 0.0
        self._last_lock_fire = 0.0
        self._repeat_delay = 0.5

    def start(self):
        if not PYNPUT_OK:
            log().warning("pynput indisponível — hotkeys desativadas")
            return
        try:
            kwargs = {}
            if self._voice_vk is not None or self._cancel_vk is not None:
                kwargs["win32_event_filter"] = self._win32_filter
            self._listener = KeyboardListener(
                on_press=self._on_press, on_release=self._on_release,
                **kwargs)
            self._listener.start()
            log().info(f"Hotkey listener ativo — voz='{self._spec_str(self.voice_spec)}' "
                       f"lock='{self._spec_str(self.lock_spec)}' "
                       f"cancelar='{self._spec_str(self.cancel_spec)}'")
        except Exception:
            log().exception("Falha a iniciar hotkey listener")

    @staticmethod
    def _spec_vk(spec):
        """Virtual-key do atalho ('s' → 0x53, 'f11' → 0x7A), ou None."""
        k = (spec or {}).get("key") or ""
        k = k.lower()
        if len(k) == 1 and k.isalnum():
            return ord(k.upper())
        m = re.fullmatch(r"f(\d{1,2})", k)
        if m and 1 <= int(m.group(1)) <= 24:
            return 0x6F + int(m.group(1))
        return {"space": 0x20, "tab": 0x09, "insert": 0x2D, "home": 0x24,
                "end": 0x23, "pause": 0x13, "page_up": 0x21,
                "page_down": 0x22, "esc": 0x1B, "escape": 0x1B,
                "backspace": 0x08, "delete": 0x2E, "enter": 0x0D,
                "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
                "caps_lock": 0x14}.get(k)

    def _mods_match(self, spec=None):
        """Ctrl/Shift/Alt carregados = exatamente os do atalho."""
        st = lambda vk: bool(ctypes.windll.user32.GetAsyncKeyState(vk)
                             & 0x8000)
        spec = spec or self.voice_spec
        return (st(0x11) == bool(spec.get("ctrl"))
                and st(0x10) == bool(spec.get("shift"))
                and st(0x12) == bool(spec.get("alt")))

    def _cancel_filter(self, msg, data):
        """Tecla de cancelar. True = tratada aqui (não é o atalho de
        voz)."""
        if msg in (0x0100, 0x0104):
            if self._cancel_suppressing:
                self._listener.suppress_event()     # repetição automática
                return True
            if not self._mods_match(self.cancel_spec):
                return False
            try:
                active = bool(self.cancel_active and self.cancel_active())
                capture = self.should_capture() if self.should_capture \
                    else True
            except Exception:
                active, capture = False, False
            if not (active and capture):
                return False        # nada a cancelar: a tecla vai ao jogo
            self._cancel_suppressing = True
            log().info(f"Hotkey cancelar: {self._spec_str(self.cancel_spec)}")
            threading.Thread(target=self._fire_cancel, daemon=True,
                             name="HotkeyCancel").start()
            self._listener.suppress_event()
            return True
        if msg in (0x0101, 0x0105) and self._cancel_suppressing:
            self._cancel_suppressing = False
            self._listener.suppress_event()
            return True
        return False

    def _fire_cancel(self):
        try:
            if self.on_cancel:
                self.on_cancel()
        except Exception:
            log().exception("Erro em on_cancel")

    def _win32_filter(self, msg, data):
        """Hook de teclado do Windows (antes do jogo receber a tecla)."""
        if self._cancel_vk is not None and data.vkCode == self._cancel_vk \
                and self._cancel_filter(msg, data):
            return True
        if self._voice_vk is None or data.vkCode != self._voice_vk:
            return True
        if msg in (0x0100, 0x0104):                 # KEYDOWN / SYSKEYDOWN
            if self._suppressing:
                # Repetição automática do teclado com o atalho mantido
                # (a cada ~0,5 s): não é um novo carregar. Antes criava um
                # release_event novo e a gravação em curso nunca sabia que
                # o tinhas largado — gravava sempre os 20 s.
                self._listener.suppress_event()
            if not self._mods_match():
                return True
            try:
                capture = self.should_capture() if self.should_capture \
                    else True
            except Exception:
                capture = True
            if not capture:
                return True     # outra app à frente: Ctrl+S normal
            self._suppressing = True
            now = time.time()
            if now - self._last_voice_fire > self._repeat_delay:
                self._last_voice_fire = now
                # Push-to-talk: largar a tecla acaba a gravação.
                self.release_event = threading.Event()
                log().info(f"Hotkey voz: {self._spec_str(self.voice_spec)}"
                           " (engolido, não chega ao jogo)")
                threading.Thread(target=self._fire_voice, daemon=True,
                                 name="HotkeyVoice").start()
            self._listener.suppress_event()
        elif msg in (0x0101, 0x0105) and self._suppressing:   # KEYUP
            self._suppressing = False
            if self.release_event is not None:
                self.release_event.set()
            self._listener.suppress_event()
        return True

    def _fire_voice(self):
        try:
            self.on_voice()
        except Exception:
            log().exception("Erro em on_voice")

    @staticmethod
    def _spec_str(spec):
        if not spec:
            return "?"
        parts = []
        if spec.get("ctrl"): parts.append("ctrl")
        if spec.get("shift"): parts.append("shift")
        if spec.get("alt"): parts.append("alt")
        parts.append(spec.get("key") or "?")
        return "+".join(parts)

    def _update_mods(self, key, pressed):
        try:
            if key in (Key.ctrl_l, Key.ctrl_r, Key.ctrl):
                self._mods["ctrl"] = pressed
            elif key in (Key.shift_l, Key.shift_r, Key.shift):
                self._mods["shift"] = pressed
            elif key in (Key.alt_l, Key.alt_r, Key.alt):
                self._mods["alt"] = pressed
            elif key in (Key.cmd_l, Key.cmd_r, Key.cmd):
                self._mods["win"] = pressed
        except Exception:
            pass

    def _on_press(self, key):
        try:
            self._update_mods(key, True)
            if key in (Key.ctrl_l, Key.ctrl_r, Key.ctrl,
                        Key.shift_l, Key.shift_r, Key.shift,
                        Key.alt_l, Key.alt_r, Key.alt,
                        Key.cmd_l, Key.cmd_r, Key.cmd):
                return

            now = time.time()

            if self.on_toggle_lock and hotkey_matches(
                    self.lock_spec, key,
                    self._mods["ctrl"], self._mods["shift"],
                    self._mods["alt"], self._mods["win"]):
                if now - self._last_lock_fire > self._repeat_delay:
                    self._last_lock_fire = now
                    log().info("Hotkey lock toggle")
                    try:
                        self.on_toggle_lock()
                    except Exception:
                        log().exception("Erro em on_toggle_lock")
                return

            # Com o filtro Win32 ativo é ele que trata o atalho de voz (e
            # só com o jogo à frente); aqui só sem filtro (ex. tecla rara).
            if self._voice_vk is None and hotkey_matches(
                    self.voice_spec, key,
                    self._mods["ctrl"], self._mods["shift"],
                    self._mods["alt"], self._mods["win"]):
                if now - self._last_voice_fire > self._repeat_delay:
                    self._last_voice_fire = now
                    log().info(f"Hotkey voz: {self._spec_str(self.voice_spec)}")
                    try:
                        self.on_voice()
                    except Exception:
                        log().exception("Erro em on_voice")
        except Exception:
            log().exception("Erro no hotkey listener")

    def _on_release(self, key):
        self._update_mods(key, False)

    def stop(self):
        if self._listener:
            try: self._listener.stop()
            except Exception: pass


# ==================================================================
# SINAIS
# ==================================================================
class _LangDownloadSignals(QObject):
    done = pyqtSignal(str, bool)


class MicTester(QObject):
    """Botão '🎤 Testar' da config: mostra o nível do micro escolhido
    durante uns segundos e o que o Google percebeu. Com Voicemeeter /
    voice changer há muitas entradas e só uma leva a voz — assim vê-se
    logo qual."""
    level = pyqtSignal(int)      # 0-100 (% da escala)
    done = pyqtSignal(str)

    def __init__(self, device_index, stt_lang, seconds=5.0, device_name=""):
        super().__init__()
        self.device_index = device_index
        self.device_name = device_name
        self.stt_lang = stt_lang or "en-US"
        self.seconds = seconds

    def start(self):
        threading.Thread(target=self._run, daemon=True,
                         name="MicTester").start()

    def _run(self):
        try:
            try:
                import audioop
            except ImportError:
                import audioop_lts as audioop
            if not SR_OK:
                self.done.emit(f"⚠️ {SR_ERR}")
                return
            idx, desc = resolve_mic(self.device_index, self.device_name)
            frames, rms_list, peak_max = [], [], 0
            with sr.Microphone(device_index=idx) as src:
                n = int(src.SAMPLE_RATE / src.CHUNK * self.seconds)
                for _ in range(n):
                    buf = src.stream.read(src.CHUNK)
                    frames.append(buf)
                    p = audioop.max(buf, src.SAMPLE_WIDTH)
                    rms_list.append(audioop.rms(buf, src.SAMPLE_WIDTH))
                    peak_max = max(peak_max, p)
                    self.level.emit(min(100, int(100 * p / 32767)))
                rate, width = src.SAMPLE_RATE, src.SAMPLE_WIDTH
            self.level.emit(0)
            pct = 100 * peak_max / 32767
            # Áudio real varia de bloco para bloco; um driver avariado
            # repete sempre o mesmo valor.
            # (DirectSound do USB Mic repetia '261, 1316, 261, 1316...'
            # em loop; voz real dá quase todos os valores diferentes.)
            tail = rms_list[len(rms_list) // 4:]

            def loops(k):
                same = sum(1 for i in range(len(tail) - k)
                           if tail[i] == tail[i + k])
                return same >= 0.9 * max(1, len(tail) - k)
            frozen = (len(tail) > 20 and max(tail) > 300
                      and any(loops(k) for k in range(1, 17)))
            audio = VoiceWorker._boost_audio(
                sr.AudioData(b"".join(frames), rate, width))
            try:
                heard = sr.Recognizer().recognize_google(
                    audio, language=self.stt_lang)
            except sr.UnknownValueError:
                heard = None
            if frozen:
                verdict = T("❌ frozen signal (driver) — choose the same "
                            "input in MME or WASAPI")
            elif pct < 0.5:
                verdict = T("❌ no sound — mic muted or this input does "
                            "not carry your voice")
            elif pct < 10:
                verdict = T("⚠️ very low — raise this input's volume in "
                            "Windows")
            else:
                verdict = T("✅ good volume")
            heard_s = f"“{heard}”" if heard else T("(nothing)")
            self.done.emit(desc + "\n" + T("peak {p}% — {v}", p=f"{pct:.0f}",
                                           v=verdict) + "\n"
                           + T("Understood: {h}", h=heard_s))
        except Exception as e:
            log().exception("MicTester")
            self.done.emit(T("⚠️ Error: {e}", e=e))


class _HFSignals(QObject):
    search_done = pyqtSignal(list, str, str)
    files_listed = pyqtSignal(list, str, str)
    progress = pyqtSignal(int, int)
    download_done = pyqtSignal(str, str)
    create_done = pyqtSignal(bool, str)


# ==================================================================
# PROFILE MANAGER
# ==================================================================
# Os perfis 💾 gravam tudo menos a IA: cada painel de IA tem os seus
# perfis de modelo (model_profiles.json) e as chaves ficam só na
# last_config. Aplicar um perfil (mesmo um antigo, que tinha a IA) não
# mexe nestes campos.
AI_CONFIG_FIELDS = frozenset({
    "mode", "cloud_provider", "model", "api_key", "api_keys",
    "cloud_models", "voice_provider", "voice_model", "mt_engine",
    "cloud_fallback", "custom_base_url", "custom_urls", "custom_names",
    "max_context", "ai_reasoning", "ai_opts", "voice_opts",
    "gpu_layers", "num_parallel", "keep_alive"})


class ProfileManager:
    @staticmethod
    def list_profiles():
        d = get_profiles_dir()
        out = []
        try:
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".json"):
                    out.append(fn[:-5])
        except Exception:
            log().exception("list_profiles falhou")
        return out

    @staticmethod
    def save_profile(name, cfg):
        try:
            d = get_profiles_dir()
            safe = re.sub(r"[^a-zA-Z0-9_\- ]+", "_", name.strip())[:60]
            if not safe:
                return False, "Nome inválido."
            path = os.path.join(d, f"{safe}.json")
            data = {k: v for k, v in asdict(cfg).items()
                    if k not in AI_CONFIG_FIELDS}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log().info(f"Profile guardado: {safe}")
            return True, safe
        except Exception as e:
            log().exception("Erro a guardar profile")
            return False, str(e)

    @staticmethod
    def load_profile(name, base):
        """base (a config atual) com o que o perfil grava por cima; a IA
        fica a de base."""
        try:
            path = os.path.join(get_profiles_dir(), f"{name}.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid = {k: v for k, v in data.items()
                     if k in AppConfig.__dataclass_fields__
                     and k not in AI_CONFIG_FIELDS}
            log().info(f"Profile carregado: {name}")
            return dc_replace(base, **valid)
        except Exception:
            log().exception(f"Erro a carregar profile '{name}'")
            return None

    @staticmethod
    def delete_profile(name):
        try:
            path = os.path.join(get_profiles_dir(), f"{name}.json")
            if os.path.isfile(path):
                os.remove(path)
                log().info(f"Profile apagado: {name}")
                return True
        except Exception:
            log().exception("Erro a apagar profile")
        return False


# ==================================================================
# ATUALIZAÇÕES (GitHub)
# ==================================================================
# A app vem do zip do GitHub: só código (~0,3 MB). O Python da app, o
# Ollama, modelos e pacotes de línguas ficam como estão. Compara-se o SHA
# git de cada ficheiro com a árvore do GitHub (1 pedido, sem descarregar)
# e, para atualizar, descarrega-se o zip e trocam-se só os que mudaram.
UPDATE_REPO = "Lagalizer/rf_translator"
UPDATE_BRANCH = "master"


def update_is_dev_copy():
    """Pasta com .git (a de quem desenvolve): não se atualiza por aqui —
    apagava alterações ainda não enviadas para o GitHub."""
    return os.path.isdir(os.path.join(_app_dir(), ".git"))


def _git_blob_sha(path):
    import hashlib
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def update_check(timeout=15):
    """Ficheiros da app diferentes do GitHub → [caminhos]. Erros de rede
    sobem (RequestException)."""
    r = requests.get(f"https://api.github.com/repos/{UPDATE_REPO}/git/"
                     f"trees/{UPDATE_BRANCH}", params={"recursive": "1"},
                     timeout=timeout,
                     headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    changed = []
    for e in r.json().get("tree", []):
        if e.get("type") != "blob":
            continue
        local = os.path.join(_app_dir(), *e["path"].split("/"))
        try:
            same = os.path.isfile(local) and _git_blob_sha(local) == e["sha"]
        except OSError:
            same = False
        if not same:
            changed.append(e["path"])
    log().info(f"Atualizações: {len(changed)} ficheiro(s) diferentes do "
               f"GitHub: {changed[:20]}")
    return changed


def update_apply(changed, status=None):
    """Descarrega o zip do GitHub e troca só os ficheiros 'changed'.
    Depois recompila o .exe (se o launcher mudou) e instala pacotes novos
    (se o requirements.txt mudou), sem janelas. → texto do resultado."""
    import io
    import subprocess
    import zipfile
    say = status or (lambda t: None)
    if update_is_dev_copy():
        raise RuntimeError(T("This folder is a development copy (git): "
                             "update it with git."))
    say(T("⬇️ Downloading the new version…"))
    r = requests.get(f"https://codeload.github.com/{UPDATE_REPO}/zip/refs/"
                     f"heads/{UPDATE_BRANCH}", timeout=60)
    r.raise_for_status()
    want, done = set(changed), []
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for info in z.infolist():
            if info.is_dir() or "/" not in info.filename:
                continue
            rel = info.filename.split("/", 1)[1]    # sem 'repo-master/'
            if rel not in want:
                continue
            dest = os.path.join(_app_dir(), *rel.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            tmp = dest + ".update"
            with open(tmp, "wb") as f:
                f.write(z.read(info))
            os.replace(tmp, dest)
            done.append(rel)
    log().info(f"Atualização: {len(done)} ficheiro(s) trocados: {done}")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if any(p.startswith("launcher/") for p in done) and os.name == "nt":
        say(T("🔧 Rebuilding RF Translator.exe…"))
        p = subprocess.run(["cmd", "/c", os.path.join(_app_dir(), "launcher",
                                                      "build.bat")],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           creationflags=flags)
        log().info(f"Atualização: build.bat → {p.returncode}")
    if "requirements.txt" in done:
        say(T("📦 Installing new packages…"))
        env = None
        try:
            from bootstrap import pip_env
            env = pip_env()
        except Exception:
            pass
        p = subprocess.run([sys.executable, "-m", "pip", "install",
                            "--no-cache-dir", "-r",
                            os.path.join(_app_dir(), "requirements.txt")],
                           capture_output=True, text=True, env=env,
                           encoding="utf-8", errors="replace",
                           creationflags=flags)
        log().info(f"Atualização: pip → {p.returncode}")
    return T("✅ Updated ({n} files). The app restarts now.", n=len(done))


def restart_app_after_exit():
    """Abre a app outra vez quando esta acabar de fechar (uma 2.ª cópia ao
    mesmo tempo era recusada: 'a app já está aberta')."""
    import subprocess
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    main = os.path.join(_app_dir(), "main.py")
    src = ("import ctypes, subprocess, sys\n"
           "k = ctypes.windll.kernel32\n"
           "h = k.OpenProcess(0x00100000, False, int(sys.argv[1]))\n"
           "if h:\n"
           "    k.WaitForSingleObject(h, 60000)\n"
           "subprocess.Popen([sys.argv[2], sys.argv[3]], cwd=sys.argv[4])\n")
    subprocess.Popen([pyw if os.path.isfile(pyw) else exe, "-c", src,
                      str(os.getpid()), pyw if os.path.isfile(pyw) else exe,
                      main, _app_dir()],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                     | getattr(subprocess, "DETACHED_PROCESS", 0),
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)
