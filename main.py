# -*- coding: utf-8 -*-
"""
main.py — RF Online Translator (GUI)
====================================
Fix v2: hotkey thread-safe via sinais Qt, faulthandler, logs detalhados.
"""

import os
import sys
import re
import time
import ctypes
from ctypes import wintypes
import webbrowser
import threading

# O bootstrap imprime emojis: com a saída redirecionada (atalho, ficheiro)
# o Windows usa cp1252 e o arranque rebentava em UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _no_console_windows():
    """Aberta pelo .exe (pythonw, sem consola), cada programa de consola
    que a app lança — Tesseract (OCR, a cada ciclo), conversor de áudio da
    voz, taskkill, ollama — abria uma janela preta que piscava. O
    'janela escondida' (SW_HIDE) que o pytesseract usa não chega quando o
    Windows Terminal é o terminal predefinido. CREATE_NO_WINDOW resolve
    para todos."""
    if os.name != "nt":
        return
    import subprocess
    orig_init = subprocess.Popen.__init__
    own = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_CONSOLE)

    def init(self, *args, **kwargs):
        flags = kwargs.get("creationflags") or 0
        if not flags & own:     # quem pede consola própria fica como está
            kwargs["creationflags"] = flags | subprocess.CREATE_NO_WINDOW
        orig_init(self, *args, **kwargs)
    subprocess.Popen.__init__ = init


_no_console_windows()


def _ensure_admin():
    """O RF Online corre como administrador (anti-cheat). Sem admin o
    Windows (UIPI) não deixa esta app ler o atalho de voz com o jogo à
    frente, capturar a janela do jogo nem escrever no chat — por isso
    reabre-se com UAC. '--no-admin' desliga."""
    if os.name != "nt" or "--no-admin" in sys.argv:
        return
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return
        import subprocess
        here = os.path.dirname(os.path.abspath(__file__))
        params = subprocess.list2cmdline(
            [os.path.abspath(__file__)] + sys.argv[1:])
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, here, 1)
    except Exception as e:
        print(f"[Admin] Não consegui pedir admin: {e}")
        return
    if rc > 32:
        print("[Admin] A reabrir como administrador (o jogo corre como admin)…")
        sys.exit(0)
    print("[Admin] Sem admin (UAC recusado): o atalho de voz, a captura do "
          "jogo e a escrita no chat podem não funcionar.")


_ensure_admin()

# ---------- FAULTHANDLER (para diagnosticar segfaults) ----------
import faulthandler
try:
    _fault_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(_fault_dir, exist_ok=True)
    _fault_file = open(os.path.join(_fault_dir, "fault.log"), "w", buffering=1)
    faulthandler.enable(file=_fault_file)
except Exception:
    faulthandler.enable()

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QComboBox, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QTextEdit,
    QMessageBox, QMenu, QCheckBox, QGroupBox, QDialog, QScrollArea,
    QListWidget, QListWidgetItem, QProgressBar, QInputDialog,
    QPlainTextEdit, QSystemTrayIcon, QStyle, QFrame, QSizePolicy,
    QSlider, QSpinBox, QColorDialog, QGraphicsOpacityEffect, QTextBrowser,
    QGridLayout
)
from PyQt6.QtCore import (Qt, QTimer, QPoint, QObject, pyqtSignal, QPropertyAnimation,
                          QEasingCurve)
from PyQt6.QtGui import QFont, QTextCursor, QAction, QColor, QCursor, QIcon

# ---------- BOOTSTRAP ----------
from bootstrap import (
    bootstrap, kill_ollama_tray, start_ollama_server,
    find_ollama_exe, is_ollama_running, list_ollama_installed_models,
)
# '--quit' só manda fechar a app aberta: sem instalações nem verificações.
_TESS_OK, _TESS_INFO = (True, "") if "--quit" in sys.argv else bootstrap()

# ---------- CORE ----------
import core
from core import (
    log, setup_logger, log_env_summary,
    tr, set_ui_lang, load_ui_prefs, save_ui_prefs, get_ui_lang,
    UI_LANGS, LANGUAGES, TTS_VOICES_BY_LANG, CLOUD_PROVIDERS,
    HF_SUGGESTIONS, CLOUD_MODELS_FALLBACK, MAX_OVERLAY_LINES,
    PYAUDIO_OK, SR_OK, SR_ERR, PYNPUT_OK,
    AppConfig, AIEngine, TTSManager, OCRWorker, VoiceWorker,
    HotkeyListener, ProfileManager,
    _LangDownloadSignals, _HFSignals,
    list_input_devices, list_output_devices, mic_index_by_name,
    get_app_tessdata_dir, is_tessdata_installed, download_tessdata_lang,
    TESS_LANG_PACKS, resolve_tess_lang,
    hf_list_repo_files_safe, hf_search_models, hf_download_gguf,
    ollama_create_model, list_local_ggufs, get_models_dir,
    get_log_path, get_error_log_path, get_profiles_dir,
    save_overlay_state, load_overlay_state, get_overlay_state_path,
    save_last_config, load_last_config,
    unload_ollama_model, unload_all_ollama_models, unload_other_ollama_models,
    get_speaker_color, SPEAKER_COLORS, GameWindow, MicTester,
    list_cloud_models, cloud_chat, normalize_provider, T, lang_label,
    DEFAULT_OVERLAY_STYLE, merge_overlay_style,
    DEFAULT_VOICE_HOTKEY,
)

core.TESS_OK = _TESS_OK
core.TESS_INFO = _TESS_INFO


# ==================================================================
# TEMA (claro / escuro) — cores suaves, pouco contraste agressivo
# ==================================================================
THEMES = {
    "dark": {
        "bg": "#1f2228", "input": "#2a2e36", "border": "#3a404b",
        "text": "#d5d9e0", "muted": "#8a919d", "title": "#8fb0d8",
        "primary": "#4d6c94", "primary_h": "#58799f", "on_primary": "#eef2f7",
        "success": "#4a7d63", "success_h": "#558a6f",
        "warm": "#8f7146", "warm_h": "#9c7d51",
        "violet": "#665d8f", "violet_h": "#72699c",
        "neutral": "#353a44", "neutral_h": "#404653", "on_neutral": "#d5d9e0",
        "disabled": "#2d3138", "on_disabled": "#6c727d",
        "ok": "#86bf9c", "warn": "#d4b26e", "err": "#d88a8a",
        "info": "#8fb0d8", "sel": "#3d5677", "sel_text": "#eef2f7",
        "deep": "#1a1d22",
    },
    "light": {
        "bg": "#eceef1", "input": "#f8f9fa", "border": "#cdd2d9",
        "text": "#2f3540", "muted": "#6b7280", "title": "#45678f",
        "primary": "#5d7fa8", "primary_h": "#52739b", "on_primary": "#ffffff",
        "success": "#5b9479", "success_h": "#4f866c",
        "warm": "#b08850", "warm_h": "#a17a44",
        "violet": "#8577b0", "violet_h": "#786aa3",
        "neutral": "#dde1e7", "neutral_h": "#d0d6dd", "on_neutral": "#2f3540",
        "disabled": "#e2e5e9", "on_disabled": "#9aa1ab",
        "ok": "#3f8460", "warn": "#94702a", "err": "#b45a5a",
        "info": "#45678f", "sel": "#c8d6e8", "sel_text": "#1f2630",
        "deep": "#f4f5f7",
    },
}
_THEME = {"c": THEMES["dark"], "img": {}}


def _theme_images(name, c):
    """Setas e visto desenhados nas cores do tema (com folha de estilo o
    Qt deixa de desenhar os seus). Ficam em ui_cache/ ao lado da app."""
    from PyQt6.QtGui import QPixmap, QPainter, QPen, QPolygonF
    from PyQt6.QtCore import QPointF
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "ui_cache")
    os.makedirs(folder, exist_ok=True)
    out = {}

    def draw(key, fn):
        pm = QPixmap(24, 24)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fn(p)
        p.end()
        path = os.path.join(folder, f"{key}_{name}.png")
        pm.save(path)
        out[key] = path.replace("\\", "/")

    def tri(points, color):
        def fn(p):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
        return fn

    def check(p):
        pen = QPen(QColor(c["on_primary"]), 3.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPolyline(QPolygonF([QPointF(5, 12.5), QPointF(10, 17.5),
                                  QPointF(19, 7)]))
    draw("down", tri([(5, 8), (19, 8), (12, 16)], c["muted"]))
    draw("up", tri([(5, 16), (19, 16), (12, 8)], c["muted"]))
    draw("check", check)
    return out


def _windows_uses_light():
    try:
        import winreg
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        ) as k:
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 1
    except Exception:
        return False


def theme_colors():
    return _THEME["c"]


def theme_qss():
    """Folha de estilo das janelas da app (config e diálogos). O overlay
    do jogo tem o seu próprio estilo (Aparência)."""
    c, i = _THEME["c"], _THEME["img"]
    return f"""
QMainWindow, QDialog, QWidget {{ background:{c['bg']}; color:{c['text']}; }}
QLabel {{ color:{c['text']}; background:transparent; }}
QGroupBox {{ color:{c['title']}; border:1px solid {c['border']};
    border-radius:8px; margin-top:14px; padding-top:12px; font-weight:bold; }}
QGroupBox::title {{ subcontrol-origin:margin; left:10px; padding:0 6px; }}
QLineEdit, QComboBox, QSpinBox, QListWidget, QTextEdit, QPlainTextEdit {{
    background:{c['input']}; color:{c['text']}; border:1px solid {c['border']};
    border-radius:6px; padding:5px;
    selection-background-color:{c['sel']}; selection-color:{c['sel_text']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border:1px solid {c['primary']}; }}
QComboBox::drop-down {{ subcontrol-origin:padding;
    subcontrol-position:center right; width:22px; border:none; }}
QComboBox::down-arrow {{ image:url({i.get('down', '')}); width:11px; height:11px; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin:border;
    width:20px; border:none; background:transparent; }}
QSpinBox::up-button {{ subcontrol-position:top right; }}
QSpinBox::down-button {{ subcontrol-position:bottom right; }}
QSpinBox::up-arrow {{ image:url({i.get('up', '')}); width:10px; height:10px; }}
QSpinBox::down-arrow {{ image:url({i.get('down', '')}); width:10px; height:10px; }}
QComboBox QAbstractItemView {{ background:{c['input']}; color:{c['text']};
    border:1px solid {c['border']}; outline:0;
    selection-background-color:{c['sel']}; selection-color:{c['sel_text']}; }}
QListWidget::item {{ height:24px; }}
QListWidget::item:selected {{ background:{c['sel']}; color:{c['sel_text']}; }}
QTextEdit#log, QPlainTextEdit#log {{ background:{c['deep']};
    font-family:Consolas,monospace; font-size:11px; }}
QPushButton {{ background:{c['primary']}; color:{c['on_primary']}; border:none;
    padding:8px 12px; border-radius:6px; font-weight:bold; }}
QPushButton:hover {{ background:{c['primary_h']}; }}
QPushButton:disabled {{ background:{c['disabled']}; color:{c['on_disabled']}; }}
QPushButton#small, QPushButton#ghost {{ background:{c['neutral']};
    color:{c['on_neutral']}; padding:6px 10px; font-size:12px; }}
QPushButton#small:hover, QPushButton#ghost:hover {{ background:{c['neutral_h']}; }}
QPushButton#lang, QPushButton#ok {{ background:{c['success']}; padding:8px; }}
QPushButton#lang:hover, QPushButton#ok:hover {{ background:{c['success_h']}; }}
QPushButton#start {{ background:{c['success']}; padding:12px; font-size:14px; }}
QPushButton#start:hover {{ background:{c['success_h']}; }}
QPushButton#hf {{ background:{c['warm']}; padding:8px; }}
QPushButton#hf:hover {{ background:{c['warm_h']}; }}
QPushButton#appearance {{ background:{c['violet']}; padding:8px; }}
QPushButton#appearance:hover {{ background:{c['violet_h']}; }}
QCheckBox {{ color:{c['text']}; padding:4px; background:transparent; }}
QCheckBox::indicator {{ width:15px; height:15px; border-radius:4px;
    border:1px solid {c['border']}; background:{c['input']}; }}
QCheckBox::indicator:checked {{ background:{c['primary']};
    border:1px solid {c['primary']}; image:url({i.get('check', '')}); }}
QProgressBar {{ background:{c['input']}; border:1px solid {c['border']};
    border-radius:4px; color:{c['text']}; text-align:center; }}
QProgressBar::chunk {{ background:{c['primary']}; border-radius:3px; }}
QSlider::groove:horizontal {{ background:{c['input']}; height:6px;
    border-radius:3px; border:1px solid {c['border']}; }}
QSlider::handle:horizontal {{ background:{c['primary']}; width:14px;
    margin:-5px 0; border-radius:7px; }}
QScrollArea {{ border:1px solid {c['border']}; border-radius:6px; }}
QScrollArea#page {{ border:none; background:transparent; }}
QScrollBar:vertical {{ background:transparent; width:10px; margin:2px; }}
QScrollBar:horizontal {{ background:transparent; height:10px; margin:2px; }}
QScrollBar::handle {{ background:{c['neutral_h']}; border-radius:4px;
    min-height:24px; min-width:24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:none; }}
QLabel[role="title"] {{ color:{c['title']}; }}
QLabel[role="muted"] {{ color:{c['muted']}; font-size:11px; }}
QLabel[role="hint"] {{ color:{c['warn']}; font-size:11px; padding:4px; }}
QLabel[role="ok"] {{ color:{c['ok']}; font-size:11px; }}
QLabel[role="warn"] {{ color:{c['warn']}; font-size:11px; }}
QLabel[role="err"] {{ color:{c['err']}; font-size:11px; }}
QLabel[role="info"] {{ color:{c['info']}; font-size:11px; }}
QLabel[role="mono"] {{ color:{c['info']}; font-family:Consolas,monospace; }}
QLabel[role="big"] {{ color:{c['info']}; font-size:16pt; font-weight:bold;
    background:{c['deep']}; border:1px solid {c['border']};
    border-radius:6px; padding:20px; }}
"""


def menu_qss():
    c = _THEME["c"]
    return (f"QMenu{{background:{c['bg']}; color:{c['text']};"
            f" border:1px solid {c['border']}; padding:4px;}}"
            "QMenu::item{padding:6px 20px; border-radius:4px;}"
            f"QMenu::item:selected{{background:{c['sel']};"
            f" color:{c['sel_text']};}}"
            f"QMenu::item:disabled{{color:{c['muted']};}}"
            f"QMenu::separator{{height:1px; background:{c['border']};"
            " margin:4px 6px;}"
            f"QToolTip{{background:{c['bg']}; color:{c['text']};"
            f" border:1px solid {c['border']}; padding:4px;}}")


def set_role(widget, role):
    """Cor de um texto pelo papel ('muted', 'ok', 'err'...) — segue o tema."""
    widget.setProperty("role", role)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def apply_theme(app=None):
    """Aplica o tema guardado (claro/escuro/Windows) à app: paleta Qt
    (caixas de mensagem, seletor de cores...) + menus e dicas."""
    pref = core.get_ui_theme()
    name = ("light" if _windows_uses_light() else "dark") \
        if pref == "system" else pref
    _THEME["c"] = THEMES.get(name, THEMES["dark"])
    app = app or QApplication.instance()
    if app is None:
        return
    try:
        _THEME["img"] = _theme_images(name, _THEME["c"])
    except Exception:
        log().exception("imagens do tema")
        _THEME["img"] = {}
    from PyQt6.QtGui import QPalette
    c = _THEME["c"]
    pal = QPalette()
    R = QPalette.ColorRole
    for role, key in ((R.Window, "bg"), (R.WindowText, "text"),
                      (R.Base, "input"), (R.AlternateBase, "deep"),
                      (R.Text, "text"), (R.Button, "neutral"),
                      (R.ButtonText, "on_neutral"), (R.Highlight, "sel"),
                      (R.HighlightedText, "sel_text"),
                      (R.ToolTipBase, "bg"), (R.ToolTipText, "text"),
                      (R.PlaceholderText, "muted"), (R.Link, "info")):
        pal.setColor(role, QColor(c[key]))
    app.setPalette(pal)
    app.setStyleSheet(menu_qss())


# ==================================================================
# DWM
# ==================================================================
WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011


def set_capture_exclusion(hwnd: int, enable: bool = True) -> bool:
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
        affinity = WDA_EXCLUDEFROMCAPTURE if enable else WDA_NONE
        return bool(user32.SetWindowDisplayAffinity(
            ctypes.c_void_p(hwnd), ctypes.c_uint(affinity)))
    except Exception:
        return False


class _CloudSignals(QObject):
    done = pyqtSignal(str, bool, str, list)   # (para quê, ok, msg, modelos)


class _TextSignal(QObject):
    text = pyqtSignal(str)                    # de uma thread → main thread


def _cloud_check(provider, key, base_url, model, ping=True):
    """(ok, mensagem, modelos). Pede a lista de modelos (não gasta nada).
    ping=True (botão Testar): se a lista for pública (OpenRouter, Ollama
    Cloud) ou não houver lista, faz uma pergunta mínima para provar a
    chave."""
    conf = CLOUD_PROVIDERS.get(provider) or {}
    label = core.provider_label(provider)
    try:
        models = list_cloud_models(provider, key, base_url)
        if core.is_openrouter(provider, base_url) and key:
            # /key prova a chave e diz a quota sem gastar pedidos (o plano
            # grátis só tem 50 por dia aos modelos ':free').
            info = core.openrouter_key_info(key)
            quota = core.openrouter_quota_text(info)
            n_free = sum(1 for m in models if "🆓" in m)
            return True, (T("✅ {p}: key OK — {n} models", p=label,
                            n=len(models))
                          + (T(" ({n} free)", n=n_free) if n_free else "")
                          + (f" · {quota}" if quota else "")), models
        if not ping:
            n_free = sum(1 for m in models if "🆓" in m)
            return True, (T("📋 {p}: {n} models", p=label, n=len(models))
                          + (T(" ({n} free)", n=n_free) if n_free else "")
                          + T(" — type in the field to search")
                          + (T(" (e.g. free)") if n_free else "")), models
        if conf.get("public_models") or (not conf.get("models_url")
                                         and conf.get("base_url")):
            # Lista pública: só uma pergunta mínima prova a chave.
            cloud_chat(provider, model or (models or [""])[0], key,
                       "Reply with OK.", "ping", base_url=base_url,
                       timeout=30)
        return True, T("✅ {p}: key OK — {n} models", p=label,
                       n=len(models)), models
    except Exception as e:
        return False, f"❌ {e}"[:300], []


# ==================================================================
# OPÇÕES DO MODELO (uma por IA: chat e voz)
# ==================================================================
class ModelOptions(QWidget):
    """Temperatura, 'pensar', contexto, resposta máx. e (chat na nuvem)
    linhas por pedido. 'Testado' = valores testados com esta app; 'do
    modelo' = não se envia nada, fica o padrão do modelo."""
    CONTEXTS = (0, 2048, 4096, 8192, 16384, 32768)
    OUTPUTS = (0, 256, 512, 1024, 2048, 4096)
    BATCHES = (1, 2, 3, 4, 6, 8, 10, 12)
    RPMS = (0, 5, 10, 15, 20, 30, 60, 120)

    def __init__(self, chat=True, parent=None):
        super().__init__(parent)
        self.chat = chat
        g = QGridLayout(self)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(5)
        self.temp_cb = QComboBox()
        self.temp_cb.addItem(T("Tested (0.1 local / 0.2 cloud)"), "tested")
        self.temp_cb.addItem(T("Model default"), "model")
        for v in ("0", "0.3", "0.5", "0.7", "1.0"):
            self.temp_cb.addItem(v, v)
        self.temp_cb.setToolTip(T(
            "How free the AI is when translating. Low = faithful and "
            "always the same (best for translating); high = more creative "
            "and it may invent things."))
        self.think_cb = QComboBox()
        self.think_cb.addItem(T("Off — fast (tested)"), "off")
        self.think_cb.addItem(T("Model default"), "model")
        self.think_cb.addItem(T("On — slower"), "on")
        self.think_cb.setToolTip(T(
            "Models that 'think' before answering (all OpenRouter free "
            "models, Gemini, GPT-OSS, Qwen3…). Off: e.g. Nemotron 120B "
            "answers in ~1 s instead of ~9 s. Lines the AI leaves "
            "untranslated are retried one by one. If a model can't turn "
            "it off, the app leaves it as it is."))
        self.ctx_cb = QComboBox()
        for n in self.CONTEXTS:
            self.ctx_cb.addItem(T("Automatic") if n == 0
                                else f"{n // 1024}k", n)
        self.ctx_cb.setToolTip(T(
            "Free / small models: choose 4k or 8k to avoid 'context "
            "length' errors. Batches are made smaller automatically if the "
            "model complains. Local: a smaller context also uses less "
            "VRAM."))
        self.out_cb = QComboBox()
        for n in self.OUTPUTS:
            self.out_cb.addItem(T("Automatic") if n == 0 else str(n), n)
        self.out_cb.setToolTip(T(
            "Longest answer, in tokens. Automatic is enough for chat "
            "(a translation is short)."))
        g.addWidget(QLabel(T("Temperature:")), 0, 0)
        g.addWidget(self.temp_cb, 0, 1)
        g.addWidget(QLabel(T("Thinking:")), 0, 2)
        g.addWidget(self.think_cb, 0, 3)
        g.addWidget(QLabel(T("Context:")), 1, 0)
        g.addWidget(self.ctx_cb, 1, 1)
        g.addWidget(QLabel(T("Answer max.:")), 1, 2)
        g.addWidget(self.out_cb, 1, 3)
        self.batch_cb = QComboBox()
        for n in self.BATCHES:
            self.batch_cb.addItem(T("{n} (default)", n=n) if n == 8
                                  else str(n), n)
        self.batch_cb.setToolTip(T(
            "Cloud: chat lines sent in one request. More lines = fewer "
            "requests (saves free daily limits, e.g. OpenRouter's 50); "
            "with too many, small models skip lines (they are retried "
            "one by one)."))
        self.lbl_batch = QLabel(T("Lines per request:"))
        self.rpm_cb = QComboBox()
        for n in self.RPMS:
            self.rpm_cb.addItem(T("Automatic") if n == 0 else str(n), n)
        self.rpm_cb.setToolTip(T(
            "Cloud: most requests sent to this AI per minute. Every cloud "
            "AI has a limit (e.g. OpenRouter free 20/min, Groq 30/min, "
            "Mistral free ~60/min); over it, it answers 'rate limit' and "
            "the app has to wait. Automatic: 19/min on OpenRouter ':free' "
            "models, no limit on the others."))
        self.lbl_rpm = QLabel(T("Requests/min:"))
        if chat:
            g.addWidget(self.lbl_batch, 2, 0)
            g.addWidget(self.batch_cb, 2, 1)
            g.addWidget(self.lbl_rpm, 2, 2)
            g.addWidget(self.rpm_cb, 2, 3)
        else:
            self.lbl_batch.hide(); self.batch_cb.hide()
            g.addWidget(self.lbl_rpm, 2, 0)
            g.addWidget(self.rpm_cb, 2, 1)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        self.set({})

    def set_cloud(self, cloud):
        """Linhas por pedido e pedidos por minuto só contam na nuvem (o
        local traduz 1 a 1, sem limite)."""
        if self.chat:
            self.lbl_batch.setVisible(cloud)
            self.batch_cb.setVisible(cloud)
        self.lbl_rpm.setVisible(cloud)
        self.rpm_cb.setVisible(cloud)

    @staticmethod
    def _sel(cb, value):
        i = cb.findData(value)
        if i < 0 and isinstance(value, (int, float)) and value:
            # valor fora da lista (perfil feito à mão): acrescenta-o
            cb.addItem(str(value), value)
            i = cb.count() - 1
        cb.setCurrentIndex(max(0, i))

    def set(self, opts):
        d = dict(core.AI_OPT_DEFAULTS)
        d.update({k: v for k, v in (opts or {}).items()
                  if v not in (None, "")})
        t = str(d["temperature"])
        if self.temp_cb.findData(t) < 0:
            try:
                t = f"{float(t):g}"
                if self.temp_cb.findData(t) < 0:
                    self.temp_cb.addItem(t, t)
            except ValueError:
                t = "tested"
        self.temp_cb.setCurrentIndex(max(0, self.temp_cb.findData(t)))
        self.think_cb.setCurrentIndex(
            max(0, self.think_cb.findData(str(d["reasoning"]))))
        self._sel(self.ctx_cb, int(d["context"] or 0))
        self._sel(self.out_cb, int(d["max_output"] or 0))
        self._sel(self.batch_cb, int(d["batch_lines"] or 8))
        self._sel(self.rpm_cb, int(d.get("rpm") or 0))

    def get(self):
        out = {"temperature": self.temp_cb.currentData() or "tested",
               "reasoning": self.think_cb.currentData() or "off",
               "context": int(self.ctx_cb.currentData() or 0),
               "max_output": int(self.out_cb.currentData() or 0),
               "rpm": int(self.rpm_cb.currentData() or 0)}
        if self.chat:
            out["batch_lines"] = int(self.batch_cb.currentData() or 8)
        return out


# ==================================================================
# MANUAL
# ==================================================================
class _BenchSignals(QObject):
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(object)


class BenchmarkTab(QWidget):
    """'📊 Ratings': a tabela das IAs testadas (ai_ratings) e o teste no
    PC de quem usa a app: frases do chat traduzidas pela IA escolhida, com
    as opções que tem agora (camadas na GPU, contexto, temperatura...).
    Diz a velocidade, os problemas e se corre bem neste PC."""
    # ConfigWindow põe aqui como ler a config atual (sem validar).
    config_source = None

    def __init__(self, lang):
        super().__init__()
        from ai_ratings import ratings_html
        v = QVBoxLayout(self)
        v.addWidget(ManualDialog._browser(ratings_html(lang)), 3)
        box = QGroupBox("🧪 " + T("Test on this PC"))
        bv = QVBoxLayout(box)
        hint = QLabel(T(
            "Translates 12 chat-style messages with the AI you choose, with "
            "the options it has now in the settings (GPU layers, context, "
            "temperature…), and says if it runs well on this PC. Change an "
            "option and test again to compare. With the game open the "
            "result is closer to real use."))
        hint.setWordWrap(True)
        set_role(hint, "muted")
        bv.addWidget(hint)
        row = QHBoxLayout()
        self.which_cb = QComboBox()
        self.which_cb.setProperty("data_list", True)
        row.addWidget(self.which_cb, 1)
        self.gpu_cb = QCheckBox(T("Also compare graphics card vs processor"))
        self.gpu_cb.setToolTip(T(
            "Local AI only: runs the test with the graphics card "
            "(Automatic) and with the processor only, and says which is "
            "faster on this PC."))
        row.addWidget(self.gpu_cb)
        self.btn_run = QPushButton("▶ " + T("Test"))
        self.btn_run.clicked.connect(self._run)
        row.addWidget(self.btn_run)
        self.btn_stop = QPushButton("■ " + T("Stop"))
        self.btn_stop.clicked.connect(self._stop_test)
        self.btn_stop.setEnabled(False)
        row.addWidget(self.btn_stop)
        bv.addLayout(row)
        self.bar = QProgressBar()
        self.bar.setTextVisible(True)
        bv.addWidget(self.bar)
        self.out = ManualDialog._browser("")
        bv.addWidget(self.out, 1)
        v.addWidget(box, 2)
        self._stop = threading.Event()
        self._sig = _BenchSignals()
        self._sig.progress.connect(self._on_progress)
        self._sig.done.connect(self._on_done)
        self._fill()

    def _cfg(self):
        try:
            return self.config_source() if self.config_source else None
        except Exception:
            log().exception("teste: config")
            return None

    def _fill(self):
        cb = self.which_cb
        cb.clear()
        cfg = self._cfg() or load_last_config()
        if cfg:
            cb.addItem("🧠 " + T("Chat AI (current settings)"), ("chat", ""))
            if getattr(cfg, "voice_provider", ""):
                cb.addItem("🎤 " + T("Voice AI (current settings)"),
                           ("voice", ""))
        for m in list_ollama_installed_models():
            cb.addItem(f"🖥 {m}", ("local", m))
        for eng in core.MT_ENGINES:
            if eng == "nllb" and not core.nllb_ready():
                continue
            cb.addItem(core.mt_label(eng), ("mt", eng))

    def _make_cfg(self):
        from dataclasses import replace as _r
        cfg = self._cfg() or load_last_config()
        kind, name = self.which_cb.currentData() or ("chat", "")
        if cfg is None:
            return None, ""
        if kind == "voice":
            vc = core.voice_config(cfg)
            return _r(vc, ocr_target=cfg.voice_target), \
                self.which_cb.currentText()
        if kind == "local":
            return _r(cfg, mode="local", model=name), name
        if kind == "mt":
            return _r(cfg, mode="mt", mt_engine=name), core.mt_label(name)
        return cfg, self.which_cb.currentText()

    def _run(self):
        cfg, label = self._make_cfg()
        if cfg is None:
            self.out.setHtml(T("Open the settings and choose an AI first."))
            return
        if cfg.mode == "cloud" and not core.provider_key(
                cfg, cfg.cloud_provider) and not core.is_custom_provider(
                cfg.cloud_provider):
            self.out.setHtml("⚠️ " + T("This AI has no key."))
            return
        gpu = self.gpu_cb.isChecked() and cfg.mode == "local"
        self._stop.clear()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.bar.setRange(0, len(core.BENCH_LINES))
        self.bar.setValue(0)
        self.out.setHtml("⏳ " + T("Testing {n}…", n=label))
        # Os modelos locais em uso (chat e voz) ficam carregados; outro
        # que só foi testado sai da placa gráfica no fim.
        active = self._cfg() or load_last_config()
        in_use = set()
        if active is not None:
            if active.mode == "local":
                in_use.add(active.model)
            vc = core.voice_config(active)
            if vc is not None and vc.mode == "local":
                in_use.add(vc.model)
        keep = cfg.mode == "local" and cfg.model in in_use

        def work():
            try:
                res = core.benchmark_translator(
                    cfg, self._sig.progress.emit, self._stop)
                res["label"] = label
                if gpu and not self._stop.is_set():
                    res["gpu"] = core.benchmark_gpu_layers(
                        cfg, self._sig.progress.emit, self._stop)
            except Exception as e:
                log().exception("teste de desempenho")
                res = {"verdict": "fail", "errors": [str(e)], "label": label,
                       "mode": cfg.mode}
            # Um modelo local que não é o do chat sai da placa gráfica (o
            # jogo precisa dela).
            if cfg.mode == "local" and not keep:
                try:
                    core.unload_ollama_model(cfg.model)
                except Exception:
                    pass
            self._sig.done.emit(res)
        threading.Thread(target=work, daemon=True, name="Benchmark").start()

    def _stop_test(self):
        self._stop.set()

    def _on_progress(self, n, of, text):
        self.bar.setRange(0, max(1, of))
        self.bar.setValue(n)
        self.bar.setFormat(f"{n}/{of}  {text[:60]}")

    def _on_done(self, r):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.bar.setValue(self.bar.maximum())
        self.bar.setFormat(T("Done"))
        esc = Overlay._escape_html
        verdict = {
            "good": "✅ " + T("Runs well on this PC"),
            "ok": "⚠️ " + T("Works, but slow or with some problems"),
            "bad": "❌ " + T("Too slow or too many problems for a busy chat"),
            "fail": "❌ " + T("Did not work"),
        }.get(r.get("verdict"), "")
        html = [f"<h3>{esc(r.get('label', ''))}: {verdict}</h3>"]
        if r.get("errors"):
            html.append("<p style='color:#f87171'>"
                        + "<br>".join(esc(e) for e in r["errors"][:3])
                        + "</p>")
        per = r.get("per_req")
        if per:
            what = (T("{s:.1f} s per message", s=per) if r.get("mode") ==
                    "local" else T("{s:.1f} s per request (6 lines)", s=per))
            html.append(f"<p>⏱ {what}")
            if r.get("warm"):
                html.append(" · " + T("loading the model: {s:.0f} s",
                                      s=r["warm"]))
            fit = r.get("fit")
            if fit is not None:
                html.append(" · " + T("in the graphics card: {p}%",
                                      p=round(fit * 100)))
            html.append("</p>")
            tips = []
            if fit is not None and fit < 0.9:
                tips.append(T("The model doesn't fit in the graphics card "
                              "memory (with the game open) and runs partly "
                              "on the processor: choose a smaller model."))
            if r.get("verdict") in ("ok", "bad") and per and \
                    per > core.BENCH_LIMITS.get(r.get("mode"),
                                                (4, 8))[0]:
                tips.append(T("Slow for a busy chat: try a smaller model, "
                              "'Thinking: off', or a cloud AI."))
            if any("script" in i for i in r.get("issues", [])):
                tips.append(T("This model sometimes answers in another "
                              "alphabet; the app translates those lines "
                              "again, but another model is better."))
            if tips:
                html.append("<ul>" + "".join(f"<li>{t}</li>" for t in tips)
                            + "</ul>")
        for gl, s, fit, _v in r.get("gpu") or []:
            where = T("Graphics card (Automatic)") if gl < 0 \
                else T("Processor only")
            html.append(f"<p>🖥 {where}: "
                        + (T("{s:.1f} s per message", s=s) if s else "—")
                        + "</p>")
        names = {"empty": T("empty"), "untranslated": T("not translated"),
                 "script": T("other alphabet"), "meta": T("talked about "
                 "itself"), "invented": T("invented text"),
                 "item": T("lost an [item]"), "repeat": T("repeated words")}
        rows = []
        for src, out, iss in zip(core.BENCH_LINES, r.get("outs", []),
                                 r.get("issues", [])):
            mark = ("⚠️ " + ", ".join(names.get(i, i) for i in iss)) \
                if iss else "✅"
            rows.append(f"<tr><td>{esc(src)}</td><td>{esc(out)}</td>"
                        f"<td>{mark}</td></tr>")
        if rows:
            html.append("<table border='1' cellspacing='0' cellpadding='4' "
                        "width='100%'>" + "".join(rows) + "</table>")
        self.out.setHtml("".join(html))


class ManualDialog(QDialog):
    """Manual da app na língua da interface. Não bloqueia: dá para o ler
    enquanto se mexe nas configurações."""
    _open = None

    @classmethod
    def show_manual(cls, parent=None, tab=0):
        """tab 0 = manual, 1 = '☁ AI Clouds' (que IAs usar, limites),
        2 = '📊 Ratings' (IAs testadas + teste neste PC)."""
        dlg = cls._open
        try:
            if dlg is not None and dlg.isVisible():
                dlg.tabs.setCurrentIndex(tab)
                dlg.raise_(); dlg.activateWindow()
                return
        except RuntimeError:
            pass
        cls._open = cls(parent)
        cls._open.tabs.setCurrentIndex(tab)
        cls._open.show()

    @staticmethod
    def _browser(html):
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.document().setDefaultStyleSheet(
            "h2 { margin-bottom: 6px; } h3 { margin-top: 14px; } "
            "li { margin-bottom: 4px; } code { font-family: Consolas; } "
            "th { text-align: left; }")
        view.setHtml(html)
        f = view.font(); f.setPointSize(max(f.pointSize(), 10))
        view.setFont(f)
        return view

    def __init__(self, parent=None):
        super().__init__(parent)
        from manual import manual_html
        from ai_clouds import ai_clouds_html
        from PyQt6.QtWidgets import QTabWidget
        self.setWindowTitle(T("📖 Manual") + " — RF Online Translator")
        self.setStyleSheet(theme_qss())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        v = QVBoxLayout(self)
        self.tabs = QTabWidget()
        lang = get_ui_lang()
        self.tabs.addTab(self._browser(manual_html(lang)), T("📖 Manual"))
        self.tabs.addTab(self._browser(ai_clouds_html(lang)), "☁ AI Clouds")
        self.tabs.addTab(BenchmarkTab(lang), "📊 Ratings")
        v.addWidget(self.tabs, 1)
        close = QPushButton(tr("btn_close"))
        close.clicked.connect(self.close)
        v.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)
        scr = QApplication.primaryScreen()
        h = 860 if scr is None else min(860, scr.availableGeometry()
                                          .height() - 80)
        self.resize(900, h)


# ==================================================================
# LOG VIEWER DIALOG
# ==================================================================
class LogViewerDialog(QDialog):
    def __init__(self, parent=None, errors_only=False):
        super().__init__(parent)
        # errors_only: logs/errors.log (só avisos e erros).
        self._path = get_error_log_path() if errors_only else get_log_path()
        self.setWindowTitle(T("⚠️ Errors and warnings") if errors_only
                            else tr("log_title"))
        self.setMinimumSize(1100, 640)
        self.setStyleSheet(theme_qss())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        info = QLabel(tr("log_path", p=self._path))
        set_role(info, "muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel(T("Filter:")))
        self.level_cb = QComboBox()
        for label, val in [(T("All"), "ALL"), ("DEBUG", "DEBUG"),
                            ("INFO", "INFO"), ("WARNING", "WARNING"),
                            ("ERROR+", "ERROR")]:
            self.level_cb.addItem(label, val)
        filter_row.addWidget(self.level_cb)
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText(T("Search text..."))
        filter_row.addWidget(self.search_le, 1)
        layout.addLayout(filter_row)

        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setObjectName("log")
        self.viewer.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.viewer, 1)

        btn_row = QHBoxLayout()
        btn_open = QPushButton("📁")
        btn_open.clicked.connect(self._open_folder)
        btn_row.addWidget(btn_open)
        self.lines_lbl = QLabel("")
        set_role(self.lines_lbl, "muted")
        btn_row.addWidget(self.lines_lbl)
        btn_row.addStretch(1)
        btn_reload = QPushButton(T("🔄 Reload"))
        btn_reload.clicked.connect(self._reload)
        btn_row.addWidget(btn_reload)
        btn_clear = QPushButton(tr("btn_clear_log"))
        btn_clear.clicked.connect(self._clear)
        btn_row.addWidget(btn_clear)
        btn_close = QPushButton(tr("btn_close"))
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._reload()

    def _open_folder(self):
        try:
            folder = os.path.dirname(get_log_path())
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            log().warning(f"Não abri pasta do log: {e}")

    def _reload(self):
        try:
            path = self._path
            if not os.path.isfile(path):
                self.viewer.setPlainText(T("(the log does not exist yet)"))
                return
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            level = self.level_cb.currentData()
            search = self.search_le.text().strip().lower()
            def match(line):
                if level and level != "ALL":
                    if level == "ERROR":
                        if "[ERROR" not in line and "[CRITICAL" not in line:
                            return False
                    elif f"[{level:<7}]" not in line and f"[{level}]" not in line:
                        return False
                if search and search not in line.lower():
                    return False
                return True
            filtered = [ln for ln in lines if match(ln)]
            self.viewer.setPlainText("".join(filtered[-2000:]))
            self.lines_lbl.setText(T("{n} lines / {t} total",
                                     n=len(filtered), t=len(lines)))
        except Exception as e:
            self.viewer.setPlainText(T("Error reading the log: {e}", e=e))

    def _clear(self):
        try:
            path = self._path
            if os.path.isfile(path):
                with open(path, "w", encoding="utf-8"): pass
            self.viewer.setPlainText(T("(log cleared)"))
        except Exception as e:
            QMessageBox.critical(self, tr("err"), str(e))


# ==================================================================
# LANGUAGE MANAGER DIALOG
# ==================================================================
class LanguageManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("ov_lang"))
        self.setMinimumSize(560, 520)
        self.setStyleSheet(theme_qss())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        title = QLabel(tr("ov_lang"))
        tf = QFont("Arial", 13); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        layout.addWidget(title)
        info = QLabel(f"tessdata: {get_app_tessdata_dir() or '(N/A)'}")
        set_role(info, "muted")
        layout.addWidget(info)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(6, 6, 6, 6)
        self.rows_layout.setSpacing(2)
        scroll.setWidget(self.rows_container)
        layout.addWidget(scroll, 1)
        btn_row = QHBoxLayout()
        self.btn_all = QPushButton("📥")
        self.btn_all.clicked.connect(self._install_all)
        btn_row.addWidget(self.btn_all); btn_row.addStretch(1)
        self.btn_close = QPushButton(tr("btn_close"))
        self.btn_close.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)
        self.status_lbl = QLabel("")
        set_role(self.status_lbl, "ok")
        layout.addWidget(self.status_lbl)
        self._rows = {}
        self._refresh()

    def _refresh(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self._rows.clear()
        if not TESS_LANG_PACKS:
            self.rows_layout.addWidget(QLabel("—")); self.rows_layout.addStretch(1)
            return
        for code, (name, size) in TESS_LANG_PACKS.items():
            row = QWidget(); row.setObjectName("row")
            rl = QHBoxLayout(row); rl.setContentsMargins(6, 4, 6, 4)
            installed = is_tessdata_installed(code)
            s = QLabel("✅" if installed else "❌"); s.setFixedWidth(24)
            rl.addWidget(s)
            c = QLabel(code); c.setFixedWidth(70)
            set_role(c, "mono")
            rl.addWidget(c)
            rl.addWidget(QLabel(name), 1)
            sz = QLabel(size); set_role(sz, "muted"); sz.setFixedWidth(60)
            rl.addWidget(sz)
            btn = QPushButton("OK" if installed else "⬇")
            btn.setObjectName("small"); btn.setFixedWidth(60)
            if installed: btn.setEnabled(False)
            else: btn.clicked.connect(lambda _, cc=code: self._install_one(cc))
            rl.addWidget(btn)
            self.rows_layout.addWidget(row); self._rows[code] = btn
        self.rows_layout.addStretch(1)
        missing = [c for c in TESS_LANG_PACKS if not is_tessdata_installed(c)]
        self.btn_all.setEnabled(bool(missing))

    def _install_one(self, code):
        btn = self._rows.get(code)
        if btn: btn.setEnabled(False); btn.setText("...")
        self.status_lbl.setText(f"⬇ {code}")
        sig = _LangDownloadSignals(); sig.done.connect(self._on_done)
        def worker(): sig.done.emit(code, download_tessdata_lang(code))
        threading.Thread(target=worker, daemon=True).start()

    def _install_all(self):
        missing = [c for c in TESS_LANG_PACKS if not is_tessdata_installed(c)]
        if not missing: return
        self.btn_all.setEnabled(False)
        sig = _LangDownloadSignals()
        def on_done(code, ok):
            self.status_lbl.setText(f"{'✅' if ok else '❌'} {code}")
            self._refresh()
        def worker():
            for c in missing:
                sig.done.emit(c, download_tessdata_lang(c))
        sig.done.connect(on_done)
        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, code, ok):
        self.status_lbl.setText(f"{'✅' if ok else '❌'} {code}")
        self._refresh()


# ==================================================================
# HUGGING FACE DIALOG
# ==================================================================
class HuggingFaceDialog(QDialog):
    def __init__(self, parent=None, on_models_changed=None):
        super().__init__(parent)
        self.on_models_changed = on_models_changed
        self.setWindowTitle(tr("hf_title"))
        self.setMinimumSize(900, 720)
        self.setStyleSheet(theme_qss())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        title = QLabel(tr("hf_title"))
        tf = QFont("Arial", 14); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        layout.addWidget(title)
        form = QFormLayout(); form.setSpacing(6)
        repo_row = QHBoxLayout()
        self.repo_le = QLineEdit()
        self.repo_le.setPlaceholderText(tr("hf_search_ph"))
        self.repo_le.returnPressed.connect(self._do_search_or_list)
        repo_row.addWidget(self.repo_le, 1)
        self.sugg_cb = QComboBox()
        self.sugg_cb.addItem("—", "")
        for rid, name in HF_SUGGESTIONS:
            self.sugg_cb.addItem(name, rid)
        self.sugg_cb.currentIndexChanged.connect(self._on_suggestion)
        repo_row.addWidget(self.sugg_cb, 0)
        form.addRow(tr("hf_search"), repo_row)
        self.token_le = QLineEdit()
        self.token_le.setPlaceholderText(tr("hf_token_ph"))
        self.token_le.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(tr("hf_token"), self.token_le)
        layout.addLayout(form)
        hint = QLabel(tr("hf_hint"))
        set_role(hint, "hint")
        hint.setWordWrap(True); layout.addWidget(hint)
        btn_row = QHBoxLayout()
        self.btn_list = QPushButton(tr("btn_search"))
        self.btn_list.setObjectName("hf")
        self.btn_list.clicked.connect(self._do_search_or_list)
        btn_row.addWidget(self.btn_list, 1)
        self.btn_back = QPushButton(tr("btn_back"))
        self.btn_back.setObjectName("ghost")
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self._back_to_search)
        btn_row.addWidget(self.btn_back, 0)
        layout.addLayout(btn_row)
        self.list_lbl = QLabel(tr("hf_results"))
        self.list_lbl.setStyleSheet("font-weight:bold;")
        layout.addWidget(self.list_lbl)
        self.files_lw = QListWidget()
        self.files_lw.itemSelectionChanged.connect(self._on_select_file)
        self.files_lw.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.files_lw, 1)
        ollama_form = QFormLayout()
        self.model_name_le = QLineEdit()
        self.model_name_le.setPlaceholderText("ex: gemma-2-9b-it-Q4_K_M")
        ollama_form.addRow(tr("hf_model_name"), self.model_name_le)
        layout.addLayout(ollama_form)
        self.chk_register = QCheckBox(tr("hf_register"))
        self.chk_register.setChecked(True)
        layout.addWidget(self.chk_register)
        action_row = QHBoxLayout()
        self.btn_download = QPushButton(tr("btn_download"))
        self.btn_download.clicked.connect(self._download_selected)
        self.btn_download.setEnabled(False)
        action_row.addWidget(self.btn_download)
        self.btn_create = QPushButton(tr("btn_create_local"))
        self.btn_create.setObjectName("ok")
        self.btn_create.clicked.connect(self._create_from_local)
        action_row.addWidget(self.btn_create)
        action_row.addStretch(1)
        self.btn_close = QPushButton(tr("btn_close"))
        self.btn_close.clicked.connect(self.accept)
        action_row.addWidget(self.btn_close)
        layout.addLayout(action_row)
        self.progress = QProgressBar(); self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        self.log_te = QTextEdit(); self.log_te.setReadOnly(True)
        self.log_te.setObjectName("log")
        self.log_te.setMaximumHeight(120); layout.addWidget(self.log_te)
        self._signals = _HFSignals()
        self._signals.search_done.connect(self._on_search_done)
        self._signals.files_listed.connect(self._on_files_listed)
        self._signals.progress.connect(self._on_progress)
        self._signals.download_done.connect(self._on_download_done)
        self._signals.create_done.connect(self._on_create_done)
        self._current_repo = ""
        self._last_search_query = ""
        self._current_files = []
        self._log(f"models: {get_models_dir()}")

    def _log(self, msg):
        self.log_te.append(msg)
        self.log_te.moveCursor(QTextCursor.MoveOperation.End)

    def _on_suggestion(self, idx):
        rid = self.sugg_cb.itemData(idx)
        if rid: self.repo_le.setText(rid)

    def _do_search_or_list(self):
        q = self.repo_le.text().strip()
        if not q:
            QMessageBox.warning(self, tr("warn"), T("Type something."))
            return
        if "/" in q and " " not in q:
            left, right = q.split("/", 1)
            if left and right and not left.startswith("http"):
                self._list_repo_files(q); return
        self._search_by_name(q)

    def _search_by_name(self, query):
        token = self.token_le.text().strip() or None
        self.btn_list.setEnabled(False); self.files_lw.clear()
        self._last_search_query = query
        self.btn_back.setVisible(False)
        self.list_lbl.setText(tr("hf_results_for", q=query))
        self._log(f"🔍 {query}")
        def worker():
            try: r, e, c = hf_search_models(query, token=token, limit=80)
            except Exception as ex: r, e, c = [], str(ex), "other"
            self._signals.search_done.emit(r, e, c)
        threading.Thread(target=worker, daemon=True).start()

    def _on_search_done(self, results, err, code):
        self.btn_list.setEnabled(True)
        if err:
            self._log(f"❌ {err.splitlines()[0]}")
            QMessageBox.warning(self, tr("warn"), err); return
        self.files_lw.clear()
        for r in results:
            item = QListWidgetItem(
                f"{r['id']}    ({r['downloads']:,} dl · {r['likes']} ❤)")
            item.setData(Qt.ItemDataRole.UserRole, {"kind": "repo", "id": r["id"]})
            self.files_lw.addItem(item)
        self._log(f"✅ {len(results)} repos")

    def _list_repo_files(self, repo_id):
        token = self.token_le.text().strip() or None
        self.btn_list.setEnabled(False); self.files_lw.clear()
        self._current_repo = repo_id
        self.list_lbl.setText(tr("hf_files_in", r=repo_id))
        self._log(f"→ {repo_id}")
        def worker():
            try: f, e, c = hf_list_repo_files_safe(repo_id, token=token)
            except Exception as ex: f, e, c = [], str(ex), "other"
            self._signals.files_listed.emit(f, e, c)
        threading.Thread(target=worker, daemon=True).start()

    def _on_files_listed(self, files, err, code):
        self.btn_list.setEnabled(True)
        if err:
            self._log(f"❌ {err.splitlines()[0]}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning if code == "auth"
                        else QMessageBox.Icon.Critical)
            msg.setWindowTitle(tr("warn") if code == "auth" else tr("err"))
            msg.setText(err)
            open_btn = msg.addButton(tr("btn_open_hf"), QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()
            if msg.clickedButton() == open_btn:
                try: webbrowser.open(f"https://huggingface.co/{self._current_repo}")
                except Exception: pass
            return
        if not files:
            self._log(T("⚠️ No .gguf")); return
        self._current_files = files; self.files_lw.clear()
        for f in files:
            sz = f["size"] / (1024 * 1024) if f["size"] else 0
            item = QListWidgetItem(f"{f['path']}    ({sz:,.0f} MB)")
            item.setData(Qt.ItemDataRole.UserRole, {"kind": "file", "file": f})
            self.files_lw.addItem(item)
        self._log(T("✅ {n} files", n=len(files)))
        if self._last_search_query: self.btn_back.setVisible(True)

    def _back_to_search(self):
        if self._last_search_query:
            self._search_by_name(self._last_search_query)

    def _on_select_file(self):
        items = self.files_lw.selectedItems()
        if not items:
            self.btn_download.setEnabled(False); return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if data and data.get("kind") == "repo":
            self.btn_download.setEnabled(False); return
        self.btn_download.setEnabled(True)
        if not self.model_name_le.text().strip():
            fname = data["file"]["path"]
            base = os.path.basename(fname).replace(".gguf", "")
            repo_short = self._current_repo.split("/")[-1][:24]
            self.model_name_le.setText(
                re.sub(r"[^a-zA-Z0-9_.-]+", "-",
                       f"{repo_short}-{base}").lower()[:60])

    def _on_double_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data.get("kind") == "repo":
            self.repo_le.setText(data["id"]); self._list_repo_files(data["id"])

    def _download_selected(self):
        items = self.files_lw.selectedItems()
        if not items: return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if not data or data.get("kind") != "file":
            QMessageBox.information(self, tr("info"), T("Select a .gguf."))
            return
        filename = data["file"]["path"]
        repo = self._current_repo
        token = self.token_le.text().strip() or None
        repo_safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", repo.replace("/", "__"))
        dest_dir = os.path.join(get_models_dir(), repo_safe)
        os.makedirs(dest_dir, exist_ok=True)
        self.btn_download.setEnabled(False); self.btn_list.setEnabled(False)
        self.progress.setValue(0)
        self._log(f"⬇️ {filename}")
        def worker():
            def cb(d, t): self._signals.progress.emit(d, t)
            path, err = hf_download_gguf(repo, filename, dest_dir,
                                         token=token, progress_cb=cb)
            if path: self._signals.download_done.emit(path, "")
            else: self._signals.download_done.emit(
                "", f"{T('Download failed')}\n\n{err or ''}".strip())
        threading.Thread(target=worker, daemon=True).start()

    def _on_progress(self, done, total):
        if total > 0:
            pct = int(done * 100 / total)
            self.progress.setValue(pct)
            self.setWindowTitle(
                f"🤗 {pct}% ({done/(1024*1024):,.0f}/{total/(1024*1024):,.0f} MB)")

    def _on_download_done(self, path, err):
        self.btn_download.setEnabled(True); self.btn_list.setEnabled(True)
        self.setWindowTitle(tr("hf_title"))
        if err or not path:
            self._log(f"❌ {err or T('failed')}")
            QMessageBox.critical(self, tr("err"), err or T("Download failed"))
            return
        self._log(f"✅ {path}")
        if self.chk_register.isChecked():
            model_name = self.model_name_le.text().strip()
            if not model_name:
                model_name = os.path.splitext(os.path.basename(path))[0].lower()
                model_name = re.sub(r"[^a-z0-9_.-]+", "-", model_name)
            if not is_ollama_running():
                exe = find_ollama_exe()
                if exe: start_ollama_server(exe)
            self._log(f"➕ {model_name}")
            self.progress.setRange(0, 0)
            def worker():
                ok, msg = ollama_create_model(model_name, path)
                self._signals.create_done.emit(ok, f"{model_name}: {msg}")
            threading.Thread(target=worker, daemon=True).start()

    def _on_create_done(self, ok, msg):
        self.progress.setRange(0, 100); self.progress.setValue(100 if ok else 0)
        if ok:
            self._log(f"✅ {msg}")
            QMessageBox.information(self, tr("info"),
                                    msg + "\n\n" + T("→ list updated."))
            if self.on_models_changed: self.on_models_changed()
        else:
            self._log(f"❌ {msg}")
            QMessageBox.critical(self, tr("err"), msg)

    def _create_from_local(self):
        local = list_local_ggufs()
        if not local:
            QMessageBox.information(self, tr("info"),
                                    T("No GGUFs in {d}.", d=get_models_dir()))
            return
        items = [f"{p}  ({s//(1024*1024)} MB)" for p, s in local]
        choice, ok = QInputDialog.getItem(self, "GGUF", "File:", items, 0, False)
        if not ok: return
        rel_path = local[items.index(choice)][0]
        gguf_full = os.path.join(get_models_dir(), rel_path)
        name, ok = QInputDialog.getText(
            self, "Name", tr("hf_model_name"),
            text=os.path.splitext(os.path.basename(rel_path))[0].lower())
        if not ok or not name.strip(): return
        name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name.strip())[:60]
        self._log(f"➕ {name}")
        self.progress.setRange(0, 0)
        def worker():
            ok2, msg = ollama_create_model(name, gguf_full)
            self._signals.create_done.emit(ok2, f"{name}: {msg}")
        threading.Thread(target=worker, daemon=True).start()


# ==================================================================
# HOTKEY CAPTURE DIALOG
# ==================================================================
class HotkeyCaptureDialog(QDialog):
    QT_KEY_MAP = {
        Qt.Key.Key_Space: "space", Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Return: "enter", Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Escape: "esc", Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete", Qt.Key.Key_Insert: "insert",
        Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
        Qt.Key.Key_PageUp: "page_up", Qt.Key.Key_PageDown: "page_down",
        Qt.Key.Key_Up: "up", Qt.Key.Key_Down: "down",
        Qt.Key.Key_Left: "left", Qt.Key.Key_Right: "right",
        Qt.Key.Key_CapsLock: "caps_lock",
        Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", Qt.Key.Key_F3: "f3",
        Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", Qt.Key.Key_F6: "f6",
        Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", Qt.Key.Key_F9: "f9",
        Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
        Qt.Key.Key_1: "1", Qt.Key.Key_2: "2", Qt.Key.Key_3: "3",
        Qt.Key.Key_4: "4", Qt.Key.Key_5: "5", Qt.Key.Key_6: "6",
        Qt.Key.Key_7: "7", Qt.Key.Key_8: "8", Qt.Key.Key_9: "9",
        Qt.Key.Key_0: "0",
        Qt.Key.Key_A: "a", Qt.Key.Key_B: "b", Qt.Key.Key_C: "c",
        Qt.Key.Key_D: "d", Qt.Key.Key_E: "e", Qt.Key.Key_F: "f",
        Qt.Key.Key_G: "g", Qt.Key.Key_H: "h", Qt.Key.Key_I: "i",
        Qt.Key.Key_J: "j", Qt.Key.Key_K: "k", Qt.Key.Key_L: "l",
        Qt.Key.Key_M: "m", Qt.Key.Key_N: "n", Qt.Key.Key_O: "o",
        Qt.Key.Key_P: "p", Qt.Key.Key_Q: "q", Qt.Key.Key_R: "r",
        Qt.Key.Key_S: "s", Qt.Key.Key_T: "t", Qt.Key.Key_U: "u",
        Qt.Key.Key_V: "v", Qt.Key.Key_W: "w", Qt.Key.Key_X: "x",
        Qt.Key.Key_Y: "y", Qt.Key.Key_Z: "z",
    }

    def __init__(self, parent=None, initial="f11", allow_esc=False):
        super().__init__(parent)
        self.allow_esc = allow_esc      # Esc grava-se (fecha com Cancelar)
        self.setWindowTitle(tr("capture_title"))
        self.setMinimumSize(420, 220)
        self.setStyleSheet(theme_qss())
        self.captured = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        title = QLabel(tr("capture_title"))
        tf = QFont("Arial", 14); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        layout.addWidget(title)
        hint = QLabel(tr("capture_hint"))
        set_role(hint, "muted")
        hint.setWordWrap(True); layout.addWidget(hint)
        self.current_lbl = QLabel(tr("capture_current", h=initial))
        set_role(self.current_lbl, "big")
        self.current_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_lbl)
        btn_row = QHBoxLayout(); btn_row.addStretch(1)
        btn_cancel = QPushButton(tr("capture_cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_ok = QPushButton(tr("capture_ok"))
        btn_ok.clicked.connect(self._accept_current)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
                    Qt.Key.Key_Meta, Qt.Key.Key_AltGr):
            return
        if key == Qt.Key.Key_Escape and not mods and not self.allow_esc:
            self.reject(); return
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier: parts.append("ctrl")
        if mods & Qt.KeyboardModifier.ShiftModifier: parts.append("shift")
        if mods & Qt.KeyboardModifier.AltModifier: parts.append("alt")
        name = self.QT_KEY_MAP.get(key)
        if name is None:
            txt = event.text()
            if txt and len(txt) == 1: name = txt.lower()
            else: return
        parts.append(name)
        self.captured = "+".join(parts)
        self.current_lbl.setText(tr("capture_current", h=self.captured))

    def _accept_current(self):
        self.accept()


# ==================================================================
# OVERLAY — sinais para thread-safety
# ==================================================================
class Overlay(QWidget):
    HEADER_HEIGHT = 40
    BTN_SIZE = (32, 28)
    RESIZE_MARGIN = 10          # px nas bordas/cantos para redimensionar
    MIN_W, MIN_H = 240, 110
    FADE_AFTER_MS = 2500        # cabeçalho desvanece sem o rato por cima

    # ⭐ Sinais que podem ser emitidos de qualquer thread.
    # Qt encaminha-os para o main thread automaticamente.
    sig_append_system = pyqtSignal(str)
    sig_set_locked = pyqtSignal(bool)

    def __init__(self, on_show_config, on_quit, on_toggle_tts,
                 on_hf=None, on_log=None, on_close=None,
                 on_send=None, on_discard=None, on_toggle_confirm=None):
        super().__init__()
        self.on_send = on_send                  # ✔ Enviar (modo confirmar)
        self.on_discard = on_discard            # ✖ apagar o texto
        self.on_toggle_confirm = on_toggle_confirm
        self.confirm_send = False               # opção atual (menu)
        self.on_show_config = on_show_config
        self.on_quit = on_quit
        self.on_close = on_close or on_quit     # ✕ (o ❌ Sair do menu fecha)
        self.on_toggle_tts = on_toggle_tts
        self.on_hf = on_hf
        self.on_log = on_log

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.opacity_value = 1.0
        self._lines = []
        self._capture_excluded = False

        state = load_overlay_state()
        self.resize(state.get("w", 620), state.get("h", 210))
        self._locked = bool(state.get("locked", False))
        self._pending_pos = QPoint(state.get("x", 100), state.get("y", 100))
        self._state_loaded = False
        self._style = merge_overlay_style(state.get("style", {}))

        self._drag_pos = None
        self._dragging = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = QFrame(self)
        self.header.setFixedHeight(self.HEADER_HEIGHT)
        h_outer = QHBoxLayout(self.header)
        h_outer.setContentsMargins(6, 0, 4, 0)
        h_outer.setSpacing(6)
        # Desempenho (IA, atraso, fila, OCR) com cores, à esquerda. Fica
        # sempre à vista: só o resto do cabeçalho (_hdr_content) desvanece.
        self._perf = None
        self._show_perf = bool(state.get("show_perf", True))
        self._perf_lbl = QLabel(self.header)
        self._perf_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._perf_lbl.setStyleSheet(
            "QLabel{background:rgba(15,17,21,190); border:none;"
            " border-radius:7px; padding:2px 8px; font-size:11pt;"
            " font-weight:bold;}")
        self._perf_lbl.hide()
        # Nunca obriga o overlay a ser largo (encolhe/corta; set_perf mostra
        # menos números quando é estreito).
        self._perf_lbl.setMinimumWidth(1)
        self._perf_lbl.setFixedHeight(30)
        h_outer.addWidget(self._perf_lbl, 0)
        # O mesmo, por baixo do cabeçalho, quando não cabe nele.
        self._perf_float = QLabel(self)
        self._perf_float.setTextFormat(Qt.TextFormat.RichText)
        self._perf_float.setStyleSheet(self._perf_lbl.styleSheet())
        self._perf_float.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._perf_float.hide()
        self._hdr_content = QWidget(self.header)
        self._hdr_content.setStyleSheet("background:transparent;")
        h_outer.addWidget(self._hdr_content, 1)
        h_layout = QHBoxLayout(self._hdr_content)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        self.lbl_title = QLabel(tr("ov_header_title"))
        self.lbl_title.setStyleSheet(
            "color:#9fb7d6; font-weight:bold; font-size:11px;"
            " background:transparent; border:none;")
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Preferred)
        h_layout.addWidget(self.lbl_title, 1)

        # Separadores dos canais (como no jogo). Só aparecem os canais
        # com mensagens; seguem o separador aberto no jogo.
        self.tabs_box = QWidget(self.header)
        self.tabs_box.setStyleSheet("background:transparent; border:none;")
        self._tabs_layout = QHBoxLayout(self.tabs_box)
        self._tabs_layout.setContentsMargins(0, 0, 0, 0)
        self._tabs_layout.setSpacing(2)
        self._tabs_layout.addStretch(1)
        h_layout.addWidget(self.tabs_box, 1)
        self._tab_btns = {}
        self._view = "all"              # canal mostrado
        self._view_partner = None       # conversa no Whisper
        self._unread = {}

        # Modo 'confirmar antes de enviar': aparecem quando há uma
        # mensagem escrita no chat à espera.
        self.btn_send = QPushButton("✔ " + T("Send"), self.header)
        self.btn_send.setFixedHeight(self.BTN_SIZE[1])
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setToolTip(T("Send the message written in the game "
                                   "chat (or press the voice hotkey again)"))
        self.btn_send.setStyleSheet(
            "QPushButton{background:#16a34a; color:#fff; border:none;"
            " border-radius:4px; padding:0 12px; font-weight:bold;"
            " font-size:12px;}"
            "QPushButton:hover{background:#22c55e;}")
        self.btn_send.clicked.connect(
            lambda: self.on_send and self.on_send())
        self.btn_send.hide()
        h_layout.addWidget(self.btn_send, 0)
        self.btn_discard = QPushButton("✖", self.header)
        self.btn_discard.setFixedSize(*self.BTN_SIZE)
        self.btn_discard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_discard.setToolTip(T("Erase it without sending (Esc)"))
        self.btn_discard.setStyleSheet(self._btn_close_style())
        self.btn_discard.clicked.connect(
            lambda: self.on_discard and self.on_discard())
        self.btn_discard.hide()
        h_layout.addWidget(self.btn_discard, 0)

        self.btn_lock = QPushButton("🔓", self.header)
        self.btn_lock.setFixedSize(*self.BTN_SIZE)
        self.btn_lock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lock.clicked.connect(self._toggle_lock)
        self.btn_lock.setStyleSheet(self._btn_style())
        h_layout.addWidget(self.btn_lock, 0)

        self.btn_menu = QPushButton("⚙", self.header)
        self.btn_menu.setFixedSize(*self.BTN_SIZE)
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.clicked.connect(self._show_menu_at_btn)
        self.btn_menu.setStyleSheet(self._btn_style())
        h_layout.addWidget(self.btn_menu, 0)

        self.btn_close = QPushButton("✕", self.header)
        self.btn_close.setFixedSize(*self.BTN_SIZE)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(lambda: self.on_close())
        self.btn_close.setStyleSheet(self._btn_close_style())
        h_layout.addWidget(self.btn_close, 0)

        root.addWidget(self.header)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setFrameStyle(0)
        self.text_edit.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        root.addWidget(self.text_edit, 1)

        self._apply_style()
        self._apply_lock_state()

        # Redimensionar pelas bordas/cantos: precisa de receber o
        # movimento do rato sem botão carregado (para mudar o cursor).
        self.setMinimumSize(self.MIN_W, self.MIN_H)
        self.setMouseTracking(True)
        self.header.setMouseTracking(True)

        # Cabeçalho (botões) desvanece quando o rato não está no overlay
        # e volta ao passar/clicar por cima. Por polling do cursor: o
        # overlay não é ativado (WA_ShowWithoutActivating) e o jogo fica
        # com o foco, por isso enter/leave não são fiáveis.
        self._hdr_fx = QGraphicsOpacityEffect(self._hdr_content)
        self._hdr_fx.setOpacity(1.0)
        self._hdr_content.setGraphicsEffect(self._hdr_fx)
        self._hdr_anim = QPropertyAnimation(self._hdr_fx, b"opacity", self)
        self._hdr_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._hdr_anim.finished.connect(
            lambda: self._hdr_visible or self.header.setStyleSheet(
                "QFrame#ovHeader{background:transparent; border:none;}"))
        self._hdr_visible = True
        self._last_hover = time.time()
        # Esconder sozinho: o corpo (mensagens) desvanece se ninguém falar
        # durante X s; a barra de cima fica sempre à vista e clicável.
        self._body_fx = QGraphicsOpacityEffect(self.text_edit)
        self._body_fx.setOpacity(1.0)
        self.text_edit.setGraphicsEffect(self._body_fx)
        self._body_anim = QPropertyAnimation(self._body_fx, b"opacity", self)
        self._body_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._body_hidden = False
        self._last_activity = time.time()
        # Cliques através do chat (bloqueado ou escondido): o rato vai para
        # o jogo, menos na barra de cima.
        self._click_through = False
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(100)
        self._hover_timer.timeout.connect(self._check_hover)
        self._hover_timer.start()

        # Indicador do micro: pastilha que pisca enquanto a app ouve
        # (fora do cabeçalho e do corpo, que desvanecem).
        self._voice_state = ""
        self._voice_pill = QLabel(self)
        self._voice_pill.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._voice_pill.hide()
        self._pill_on = True
        self._pill_timer = QTimer(self)
        self._pill_timer.setInterval(450)
        self._pill_timer.timeout.connect(self._blink_pill)

        # Connect thread-safe signals
        self.sig_append_system.connect(self.append_system)
        self.sig_set_locked.connect(self._slot_set_locked)
        self._apply_view()

    @staticmethod
    def _btn_style(px=17):
        return ("QPushButton{background:transparent; color:#e5e7eb;"
                f" border:none; font-size:{px}px; padding:0;"
                " font-weight:bold;}"
                "QPushButton:hover{background:rgba(93,127,168,130);"
                " border-radius:3px;}"
                "QPushButton:pressed{background:rgba(82,115,155,200);}")

    @staticmethod
    def _btn_close_style(px=17):
        return ("QPushButton{background:transparent; color:#e5e7eb;"
                f" border:none; font-size:{px}px; padding:0;"
                " font-weight:bold;}"
                "QPushButton:hover{background:rgba(180,90,90,190);"
                " border-radius:3px; color:#fff;}")

    def _hs(self):
        """Escala do cabeçalho (Aparência → tamanho da barra de cima)."""
        try:
            return max(0.8, min(2.0, int(self._style.get(
                "header_scale", 100)) / 100))
        except (TypeError, ValueError):
            return 1.0

    def _scale_header(self):
        """Tudo o que está na barra de cima cresce com a escala: botões,
        separadores, título e o indicador de desempenho."""
        s = self._hs()
        bw, bh = round(self.BTN_SIZE[0] * s), round(self.BTN_SIZE[1] * s)
        px = round(17 * s)
        for b in (self.btn_lock, self.btn_menu):
            b.setFixedSize(bw, bh)
            b.setStyleSheet(self._btn_style(px))
        for b in (self.btn_close, self.btn_discard):
            b.setFixedSize(bw, bh)
            b.setStyleSheet(self._btn_close_style(px))
        self.btn_send.setFixedHeight(bh)
        self.btn_send.setStyleSheet(
            "QPushButton{background:#16a34a; color:#fff; border:none;"
            f" border-radius:4px; padding:0 {round(12 * s)}px;"
            f" font-weight:bold; font-size:{round(12 * s)}px;}}"
            "QPushButton:hover{background:#22c55e;}")
        self.lbl_title.setStyleSheet(
            f"color:#9fb7d6; font-weight:bold; font-size:{round(11 * s)}px;"
            " background:transparent; border:none;")
        for b in self._tab_btns.values():
            b.setFixedHeight(round(24 * s))
        self._refresh_tabs()

    def get_style(self): return dict(self._style)

    def set_style(self, style):
        self._style = merge_overlay_style(style)
        self._apply_style()
        self._apply_view()
        self._rebuild_html()
        self._save_state()

    def _apply_style(self):
        st = self._style
        bc = st.get("border_color", "#60a5fa")
        # Só o próprio cabeçalho (não as etiquetas dentro dele). Desvanecido
        # fica sem fundo: só se vê o indicador de desempenho.
        self._hdr_qss = (
            f"QFrame#ovHeader {{background:rgba(26,29,35,230);"
            f" border-top-left-radius:6px; border-top-right-radius:6px;"
            f" border:1px solid {bc}; border-bottom:none;}}")
        self.header.setObjectName("ovHeader")
        self.header.setStyleSheet(
            self._hdr_qss if getattr(self, "_hdr_visible", True)
            else "QFrame#ovHeader{background:transparent; border:none;}")
        # Indicador de desempenho bem legível e do tamanho da letra do
        # chat (num 4K a 100% a letra escolhida é maior): nunca < 11 pt; o
        # cabeçalho cresce com ele.
        s = self._hs()
        pt = max(round(11 * s), int(st.get("font_size", 11)))
        perf_h = round(pt * 2.7)
        perf_qss = (f"QLabel{{background:rgba(15,17,21,190); border:none;"
                    f" border-radius:7px; padding:2px 8px; font-size:{pt}pt;"
                    f" font-weight:bold;}}")
        self._base_hdr_h = round(40 * s)
        self._perf_hdr_h = max(self._base_hdr_h, perf_h + 10)
        self._set_header_height(self._base_hdr_h)
        self._scale_header()
        for lbl in (self._perf_lbl, self._perf_float):
            lbl.setStyleSheet(perf_qss)
        self._perf_lbl.setFixedHeight(perf_h)
        if getattr(self, "_perf", None):
            self.set_perf(self._perf)
        bg = self._hex_to_rgb(st.get("bg_color", "#000000"))
        alpha = int(st.get("bg_alpha", 180))
        text_color = st.get("text_color", "#f3f4f6")
        font_family = st.get("font_family", "Arial")
        font_size = int(st.get("font_size", 11))
        font_weight = "bold" if st.get("font_bold", True) else "normal"
        self.text_edit.setStyleSheet(
            f"QTextEdit {{background-color: rgba({bg[0]},{bg[1]},{bg[2]},"
            f"{alpha}); color:{text_color}; border:1px solid {bc};"
            f" border-bottom-left-radius:6px;"
            f" border-bottom-right-radius:6px; border-top:none;"
            f" padding:6px; font-family:'{font_family}';"
            f" font-size:{font_size}pt; font-weight:{font_weight};}}")
        self.text_edit.document().setDocumentMargin(4)
        self._rebuild_html()

    @staticmethod
    def _hex_to_rgb(hex_color):
        try:
            h = hex_color.lstrip("#")
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            return (0, 0, 0)

    def _line_to_html(self, line):
        line = line.replace("[emote]", "😊")       # sticker/emote do jogo
        st = self._style
        text_color = st.get("text_color", "#f3f4f6")
        if st.get("show_separator", True):
            sc = self._hex_to_rgb(st.get("separator_color", "#ffffff"))
            sa = int(st.get("separator_alpha", 30))
            sep = (f"border-bottom:1px solid "
                   f"rgba({sc[0]},{sc[1]},{sc[2]},{sa});"
                   f" padding-bottom:2px; margin-bottom:3px;")
        else:
            sep = "margin-bottom:3px;"
        if line.startswith("» "):
            return (f'<div style="{sep}color:#8f97a3; font-style:italic;">'
                    f'{self._escape_html(line)}</div>')
        m = re.match(r"^\[([^\]]+)\]\s*(.*)$", line)
        if m:
            speaker = m.group(1).strip()
            body = m.group(2).strip()
            mode = st.get("speaker_color_mode", "auto")
            if mode == "auto": color = get_speaker_color(speaker)
            elif mode == "single":
                color = st.get("speaker_color_single", "#60a5fa")
            else: color = text_color
            return (f'<div style="{sep}">'
                    f'<span style="color:{color}; font-weight:bold;">'
                    f'{self._escape_html(f"[{speaker}]")}</span>'
                    f'<span style="color:{text_color};"> '
                    f'{self._escape_html(body)}</span></div>')
        return (f'<div style="{sep}color:{text_color};">'
                f'{self._escape_html(line)}</div>')

    @staticmethod
    def _escape_html(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;"))

    def _rebuild_html(self):
        html = "".join(self._line_to_html(l) for l in self._visible_lines())
        body = html or ('<div style="color:#888; font-style:italic;">'
                        + self._escape_html(T("(waiting for translations...)"))
                        + '</div>')
        self.text_edit.setHtml(body)
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def is_dragging(self): return self._dragging
    def is_capture_excluded(self): return self._capture_excluded
    def is_locked(self): return self._locked

    def _slot_set_locked(self, locked):
        """Slot chamado no main thread quando sig_set_locked é emitido."""
        self.set_locked(locked)

    def set_locked(self, locked):
        self._locked = bool(locked)
        self._apply_lock_state()
        self._save_state()
        self.append_system(
            T("🔒 Locked — cannot be moved or resized")
            if self._locked
            else T("🔓 Unlocked — drag by the top, resize by the corners"))

    def _apply_lock_state(self):
        if self._locked:
            self.btn_lock.setText("🔒")
            self.btn_lock.setToolTip(T("Locked"))
        else:
            self.btn_lock.setText("🔓")
            self.btn_lock.setToolTip(T("Unlocked"))

    def _toggle_lock(self):
        self.set_locked(not self._locked)

    def _save_state(self):
        try:
            g = self.frameGeometry()
            save_overlay_state({
                "x": int(g.x()), "y": int(g.y()),
                "w": int(g.width()), "h": int(g.height()),
                "locked": bool(self._locked),
                "show_perf": bool(getattr(self, "_show_perf", True)),
                "style": dict(self._style)})
        except Exception:
            log().exception("Falha a gravar overlay state")

    def moveEvent(self, event):
        super().moveEvent(event)
        if not self._dragging and self._state_loaded:
            self._save_state()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_pill()
        if getattr(self, "_perf", None):
            self.set_perf(self._perf)       # menos números se estreito
        if self._state_loaded: self._save_state()

    # ---------- indicador do micro ----------
    _PILL = {"listen": ("rgba(220,38,38,235)", "rgba(127,29,29,200)"),
             "busy": ("rgba(217,119,6,225)", "rgba(217,119,6,225)"),
             "confirm": ("rgba(22,163,74,235)", "rgba(20,83,45,210)")}

    def set_voice_state(self, state):
        """'listen' = a ouvir (vermelho a piscar), 'busy' = a traduzir
        (âmbar), '' = nada."""
        self._voice_state = state or ""
        pill = self._voice_pill
        waiting = self._voice_state == "confirm"
        self.btn_send.setVisible(waiting)
        self.btn_discard.setVisible(waiting)
        if waiting:
            self._fade_header(True)     # o ✔ tem de estar à vista
        if not self._voice_state:
            self._pill_timer.stop()
            pill.hide()
            return
        pill.setText({"listen": T("● Listening"),
                      "confirm": T("✋ Waiting for ✔ Send")}.get(
                          state, T("⏳ Translating")))
        self._pill_on = True
        self._style_pill()
        pill.adjustSize()
        self._place_pill()
        pill.show(); pill.raise_()
        if state in ("listen", "confirm"):
            self._pill_timer.start()
        else:
            self._pill_timer.stop()

    def _style_pill(self):
        on, off = self._PILL.get(self._voice_state, self._PILL["listen"])
        self._voice_pill.setStyleSheet(
            f"QLabel{{background:{on if self._pill_on else off};"
            f" color:#fff; border-radius:10px; padding:3px 10px;"
            f" font-weight:bold; font-size:10pt;}}")

    def _blink_pill(self):
        self._pill_on = not self._pill_on
        self._style_pill()

    def _place_pill(self):
        pill = getattr(self, "_voice_pill", None)
        if pill is not None:
            pill.move(max(4, self.width() - pill.width() - 14),
                      self.HEADER_HEIGHT + 8)

    # ---------- desempenho ----------
    # (bom até, aceitável até) — acima disso fica vermelho.
    _PERF_LIMITS = {"ai_local": (2.0, 5.0), "ai_cloud": (3.0, 8.0),
                    "lag": (4.0, 10.0), "queue": (2, 8), "ocr": (2.5, 5.0)}
    _PERF_COLORS = ("#4ade80", "#facc15", "#f87171")

    def _perf_color(self, kind, v):
        good, ok = self._PERF_LIMITS[kind]
        return self._PERF_COLORS[0 if v <= good else 1 if v <= ok else 2]

    def set_perf(self, d):
        """Números do OCRWorker (sinal perf); None esconde."""
        self._perf = d
        lbl = self._perf_lbl
        if not d or not self._show_perf:
            lbl.hide()
            self._perf_float.hide()
            self.text_edit.setViewportMargins(0, 0, 0, 0)
            self.lbl_title.setVisible(not self._tab_btns)
            self._set_header_height(self._base_hdr_h)
            return
        parts = []

        def seg(icon, val, kind, fmt="{:.1f}s"):
            if val is None:
                return
            parts.append(f'<span style="color:{self._perf_color(kind, val)}">'
                         f'{icon} {fmt.format(val)}</span>')
        mode = d.get("mode")
        narrow = self.width() < 470
        seg("⚡", d.get("ai"), "ai_local" if mode == "local" else "ai_cloud")
        seg("⏱", d.get("lag"), "lag")
        if not narrow or (d.get("queue") or 0) > 2:
            seg("⏳", d.get("queue"), "queue", "{}")
        if not narrow:
            seg("👁", d.get("ocr"), "ocr")
        if d.get("err"):
            parts.append(f'<span style="color:{self._PERF_COLORS[2]}">⚠</span>')
        if not parts:
            lbl.hide()
            return
        html = "&nbsp; ".join(parts)
        # Não cabe no cabeçalho (overlay estreito, muitos separadores):
        # fica logo por baixo dele, à esquerda (a pastilha do micro está à
        # direita).
        lbl.setText(html)
        need = lbl.sizeHint().width()
        room = self.width() - self._hdr_content.minimumSizeHint().width() - 20
        float_lbl = self._perf_float
        # O título dá o lugar aos números (e aos separadores).
        self.lbl_title.hide()
        no_bar = self._view_mode() == "chat"
        if no_bar:
            need = room + 1             # sem barra: fica no topo do chat
        # O cabeçalho só cresce (letra grande) com os números lá dentro.
        self._set_header_height(self._base_hdr_h if need > room else self._perf_hdr_h)
        if need > room:
            lbl.hide()
            float_lbl.setText(html)
            float_lbl.adjustSize()
            float_lbl.move(8, 4 if no_bar else self.HEADER_HEIGHT + 4)
            float_lbl.show()
            float_lbl.raise_()
            # O texto do chat começa por baixo dele.
            self.text_edit.setViewportMargins(0, float_lbl.height() + 4, 0, 0)
            lbl = float_lbl
        else:
            float_lbl.hide()
            self.text_edit.setViewportMargins(0, 0, 0, 0)
        lbl.setToolTip(T(
            "⚡ time of each AI request · ⏱ delay from the moment the chat "
            "is read until the translation appears · ⏳ messages waiting "
            "for the AI · 👁 time of each chat read (OCR). Green = good, "
            "yellow = slow, red = too slow (try a smaller model, fewer "
            "lines per request or another AI). ⚠ = the AI is failing."))
        lbl.show()

    def _view_mode(self):
        v = self._style.get("view_mode", "all")
        return v if v in ("all", "bar", "chat") else "all"

    def _apply_view(self):
        """'bar' = só a barra de cima (o chat fica escondido e os cliques
        passam para o jogo); 'chat' = só as mensagens, sem a barra (o
        menu abre com o botão direito; arrasta-se pelo topo)."""
        view = self._view_mode()
        self.header.setVisible(view != "chat")
        if view == "bar":
            self._show_body(False)
        elif not self._style.get("auto_hide"):
            self._show_body(True)
        if getattr(self, "_perf", None):
            self.set_perf(self._perf)

    def _set_view_mode(self, view):
        self._set_style_key("view_mode", view)
        self._apply_view()

    def _set_header_height(self, h):
        if h != self.HEADER_HEIGHT:
            self.HEADER_HEIGHT = h
            self.header.setFixedHeight(h)

    def _toggle_perf(self, on):
        self._show_perf = bool(on)
        self.set_perf(self._perf)
        self._save_state()

    # ---------- fade do cabeçalho ----------
    def _fade_header(self, visible):
        if visible == self._hdr_visible:
            return
        self._hdr_visible = visible
        if visible:
            self.header.setStyleSheet(self._hdr_qss)
        self._hdr_anim.stop()
        self._hdr_anim.setDuration(150 if visible else 600)
        self._hdr_anim.setStartValue(self._hdr_fx.opacity())
        self._hdr_anim.setEndValue(1.0 if visible else 0.0)
        self._hdr_anim.start()

    def _check_hover(self):
        if not self.isVisible():
            return
        now = time.time()
        pos = QCursor.pos()
        g = self.frameGeometry()
        inside = g.contains(pos)
        over_header = inside and pos.y() < g.y() + self.HEADER_HEIGHT
        # Bloqueado (ou chat escondido): o corpo deixa passar os cliques
        # para o jogo; a barra de cima continua sempre clicável.
        self._set_click_through((self._locked or self._body_hidden)
                                and not over_header)
        # Esconder sozinho se ninguém falar há X s.
        st = self._style
        if self._view_mode() == "bar":
            if not self._body_hidden:
                self._show_body(False)      # só a barra de cima
        elif st.get("auto_hide"):
            if over_header or self._dragging or (inside and not self._locked):
                self._last_activity = now
                self._show_body(True)
            elif not self._body_hidden and now - self._last_activity > \
                    float(st.get("auto_hide_secs", 20)):
                self._show_body(False)
        elif self._body_hidden:
            self._show_body(True)
        # A barra de cima: sempre à vista com o chat escondido; senão
        # desvanece sem o rato por cima.
        if inside or self._dragging or self._body_hidden \
                or self._voice_state == "confirm":
            self._last_hover = now
            self._fade_header(True)
        elif (now - self._last_hover) * 1000 > self.FADE_AFTER_MS:
            self._fade_header(False)

    def _show_body(self, visible):
        if visible != self._body_hidden:
            return                      # já está assim
        self._body_hidden = not visible
        self._body_anim.stop()
        self._body_anim.setDuration(200 if visible else 800)
        self._body_anim.setStartValue(self._body_fx.opacity())
        self._body_anim.setEndValue(1.0 if visible else 0.0)
        self._body_anim.start()

    def _set_click_through(self, on):
        """WS_EX_TRANSPARENT na janela (já é 'layered'): o Windows manda o
        rato para a janela de baixo (o jogo). Ligado/desligado conforme o
        rato está no corpo ou na barra de cima."""
        if on == self._click_through or os.name != "nt":
            return
        try:
            u32 = ctypes.windll.user32
            u32.GetWindowLongW.restype = ctypes.c_long
            hwnd = int(self.winId())
            ex = u32.GetWindowLongW(hwnd, -20)          # GWL_EXSTYLE
            ex = (ex | 0x20) if on else (ex & ~0x20)    # WS_EX_TRANSPARENT
            u32.SetWindowLongW(hwnd, -20, ex)
            self._click_through = on
        except Exception:
            log().exception("click-through")

    def _set_style_key(self, key, value):
        st = dict(self._style)
        st[key] = value
        self.set_style(st)

    # ---------- redimensionar ----------
    def _edges_at(self, pos):
        """Bordas sob o cursor (para redimensionar), ou vazio."""
        m, w, h = self.RESIZE_MARGIN, self.width(), self.height()
        edges = Qt.Edge(0)
        if pos.x() <= m: edges |= Qt.Edge.LeftEdge
        if pos.x() >= w - m: edges |= Qt.Edge.RightEdge
        if pos.y() <= 4: edges |= Qt.Edge.TopEdge   # topo fino: é o header
        if pos.y() >= h - m: edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _cursor_for(edges):
        E = Qt.Edge
        diag1 = (E.LeftEdge | E.TopEdge, E.RightEdge | E.BottomEdge)
        diag2 = (E.RightEdge | E.TopEdge, E.LeftEdge | E.BottomEdge)
        if edges in diag1: return Qt.CursorShape.SizeFDiagCursor
        if edges in diag2: return Qt.CursorShape.SizeBDiagCursor
        if edges & (E.LeftEdge | E.RightEdge): return Qt.CursorShape.SizeHorCursor
        if edges & (E.TopEdge | E.BottomEdge): return Qt.CursorShape.SizeVerCursor
        return None

    def mousePressEvent(self, event):
        self._last_hover = time.time()
        self._fade_header(True)
        if self._locked:            # bloqueado: nem move nem redimensiona
            event.ignore(); return
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._edges_at(event.position().toPoint())
            if edges and self.windowHandle() is not None:
                self.windowHandle().startSystemResize(edges)
                event.accept(); return
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.y() <= self.HEADER_HEIGHT + 4:
                self._drag_pos = (event.globalPosition().toPoint()
                                  - self.frameGeometry().topLeft())
                self._dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept(); return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not event.buttons() and not self._locked:
            shape = self._cursor_for(self._edges_at(event.position().toPoint()))
            if shape is not None:
                self.setCursor(shape)
            elif not self._dragging:
                self.unsetCursor()
        if self._locked:
            event.ignore(); return
        if (self._drag_pos is not None
                and event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._locked:
            event.ignore(); return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            self._dragging = False
            self.unsetCursor()
            self._save_state()
            event.accept()

    def _build_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(menu_qss())
        state_txt = ("🔒  " + T("Locked") if self._locked
                     else "🔓  " + T("Unlocked"))
        a_state = menu.addAction(state_txt); a_state.setEnabled(False)
        menu.addSeparator()
        a_toggle = menu.addAction(
            tr("ov_lock_off") if self._locked else tr("ov_lock_on"))
        st = self._style
        a_auto = menu.addAction("👁  " + T("Auto-hide the chat"))
        a_auto.setCheckable(True)
        a_auto.setChecked(bool(st.get("auto_hide")))
        m_secs = menu.addMenu("⏱  " + T("Hide after"))
        secs = {}
        for n in (10, 20, 30, 60, 120, 300):
            a = m_secs.addAction(T("{n} s", n=n) if n < 60
                                 else T("{n} min", n=n // 60))
            a.setCheckable(True)
            a.setChecked(int(st.get("auto_hide_secs", 20)) == n)
            secs[a] = n
        m_bg = menu.addMenu("🌫  " + T("Background visibility"))
        bgs = {}
        cur = round(int(st.get("bg_alpha", 180)) * 100 / 255)
        for p in (0, 10, 25, 40, 55, 70, 85, 100):
            a = m_bg.addAction(f"{p}%")
            a.setCheckable(True)
            a.setChecked(abs(cur - p) <= 2)
            bgs[a] = p
        m_view = menu.addMenu("🪟  " + T("Show"))
        self._a_views = {}
        for key, text in (("all", T("Bar and chat")),
                          ("bar", T("Only the top bar (hide the chat)")),
                          ("chat", T("Only the chat (hide the bar)"))):
            a = m_view.addAction(text)
            a.setCheckable(True)
            a.setChecked(self._view_mode() == key)
            self._a_views[a] = key
        a_perf = menu.addAction("📊  " + T("Show AI speed in the bar"))
        a_perf.setCheckable(True)
        a_perf.setChecked(bool(self._show_perf))
        self._a_perf = a_perf
        menu.addSeparator()
        a_back = None       # era 'Voltar às configurações' (repetido)
        a_cfg = menu.addAction(tr("ov_config"))
        a_tts = menu.addAction(tr("ov_tts"))
        a_confirm = menu.addAction(T("✋ Confirm before sending (voice)"))
        a_confirm.setCheckable(True)
        a_confirm.setChecked(bool(self.confirm_send))
        a_confirm.setEnabled(self.on_toggle_confirm is not None)
        a_lang = menu.addAction(tr("ov_lang"))
        a_hf = menu.addAction(tr("ov_hf")) if self.on_hf else None
        a_log = menu.addAction(tr("ov_log")) if self.on_log else None
        a_err = menu.addAction(T("⚠️ Errors"))
        a_manual = menu.addAction(T("📖  Manual"))
        a_clouds = menu.addAction("☁  AI Clouds")
        self._a_ratings = menu.addAction("📊  " + T("AI ratings and speed "
                                                   "test"))
        a_clear = menu.addAction(tr("ov_clear"))
        menu.addSeparator()
        a_quit = menu.addAction(tr("ov_quit"))
        return (menu, a_toggle, a_back, a_cfg, a_tts, a_lang,
                a_hf, a_log, a_err, a_clear, a_quit, a_auto, secs, bgs,
                a_manual, a_clouds, a_confirm)

    def _handle_menu_choice(self, chosen, refs):
        (_, a_toggle, a_back, a_cfg, a_tts, a_lang,
         a_hf, a_log, a_err, a_clear, a_quit, a_auto, secs, bgs,
         a_manual, a_clouds, a_confirm) = refs
        if chosen is None: return
        if chosen is getattr(self, "_a_perf", None):
            self._toggle_perf(chosen.isChecked())
            return
        if chosen in getattr(self, "_a_views", {}):
            self._set_view_mode(self._a_views[chosen])
            return
        if chosen is getattr(self, "_a_ratings", None):
            ManualDialog.show_manual(None, tab=2)
            return
        if chosen == a_toggle: self._toggle_lock()
        elif chosen == a_auto or chosen in secs:
            if chosen in secs:
                self._set_style_key("auto_hide_secs", secs[chosen])
            on = True if chosen in secs else chosen.isChecked()
            self._set_style_key("auto_hide", on)
            self._last_activity = time.time()
            n = int(self._style.get("auto_hide_secs", 20))
            self.append_system(
                T("👁 Auto-hide on — hides after {n} s without messages", n=n)
                if on else T("👁 Auto-hide off"))
        elif chosen in bgs:
            self._set_style_key("bg_alpha", round(bgs[chosen] * 2.55))
        elif chosen == a_back or chosen == a_cfg: self.on_show_config()
        elif chosen == a_tts: self.on_toggle_tts()
        elif chosen == a_confirm:
            self.on_toggle_confirm(a_confirm.isChecked())
        elif chosen == a_lang: LanguageManagerDialog(self).exec()
        elif a_hf and chosen == a_hf: self.on_hf()
        elif a_log and chosen == a_log: self.on_log()
        elif chosen == a_err: LogViewerDialog(None, errors_only=True).exec()
        elif chosen == a_manual: ManualDialog.show_manual(None)
        elif chosen == a_clouds: ManualDialog.show_manual(None, tab=1)
        elif chosen == a_clear:
            self._lines.clear(); self._rebuild_html()
        elif chosen == a_quit: self.on_quit()

    def _show_menu_at_btn(self):
        refs = self._build_menu()
        pos = self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft())
        chosen = refs[0].exec(pos)
        self._handle_menu_choice(chosen, refs)

    def contextMenuEvent(self, event):
        refs = self._build_menu()
        chosen = refs[0].exec(event.globalPos())
        self._handle_menu_choice(chosen, refs)

    # Sem 'system': esse chat é ignorado (ao abri-lo no jogo o overlay
    # fica onde estava).
    TAB_LABELS = {"all": "All", "world": "World", "server": "Server",
                  "party": "Party", "guild": "Guild", "raid": "Raid",
                  "whisper": "PM", "channel": "Chan"}
    MAX_STORED = 400

    def append_text(self, channel, text=None):
        """(canal, texto) vindo do OCRWorker; (texto) = mensagem da app.
        Em modo cloud chega um lote de várias linhas; cada uma tem de ser
        uma entrada para o '[Nome]' ganhar a cor do jogador."""
        if text is None:
            channel, text = None, channel
        self._last_activity = time.time()
        if self._view_mode() != "bar":
            self._show_body(True)       # alguém falou: volta a aparecer
        new = [(channel, l) for l in text.splitlines() if l.strip()]
        self._lines.extend(new)
        if len(self._lines) > self.MAX_STORED:
            self._lines = self._lines[-self.MAX_STORED:]
        if channel and channel != "all":
            self._ensure_tab(channel)
            if channel != self._view and self._view != "all":
                self._unread[channel] = self._unread.get(channel, 0) + len(new)
                self._refresh_tabs()
        self._rebuild_html()

    def append_system(self, text):
        self.append_text(None, f"» {text}")

    # ---------- separadores ----------
    def _ensure_tab(self, channel):
        if channel in self._tab_btns or channel not in self.TAB_LABELS:
            return
        if not self._tab_btns:
            self._make_tab("all")
        self._make_tab(channel)
        self.lbl_title.hide()
        self._refresh_tabs()

    def _make_tab(self, channel):
        b = QPushButton(self.TAB_LABELS[channel], self.tabs_box)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFixedHeight(round(24 * self._hs()))
        b.clicked.connect(lambda _=False, c=channel: self.set_view(c))
        # Mantém a ordem dos separadores do jogo.
        order = list(self.TAB_LABELS)
        pos = sum(1 for c in self._tab_btns if order.index(c) < order.index(channel))
        self._tabs_layout.insertWidget(pos, b)
        self._tab_btns[channel] = b

    def _refresh_tabs(self):
        s = self._hs()
        for ch, b in self._tab_btns.items():
            active = ch == self._view
            n = self._unread.get(ch, 0)
            label = self.TAB_LABELS[ch]
            if ch == "whisper" and active and self._view_partner:
                label = f"PM·{self._view_partner[:10]}"
            b.setText(f"{label} {n}" if n and not active else label)
            b.setStyleSheet(
                "QPushButton{border:none; border-radius:4px;"
                f" padding:0 {round(7 * s)}px; font-size:{round(12 * s)}px;"
                " font-weight:bold;"
                + (" background:rgba(93,127,168,210); color:#f1f4f8;}"
                   if active else
                   (" background:rgba(176,136,80,110); color:#ecd9b4;}" if n
                    else " background:rgba(255,255,255,22); color:#c5cbd4;}"))
                + "QPushButton:hover{background:rgba(93,127,168,150);}")

    def set_view(self, spec):
        """'guild' / 'whisper:PlayerAlpha' / 'all'. Chamado pelo clique no
        separador ou quando mudas de separador no jogo."""
        channel, _, partner = (spec or "all").partition(":")
        if channel not in self.TAB_LABELS:
            return
        self._view = channel
        self._view_partner = partner or None
        self._unread.pop(channel, None)
        if channel != "all":
            self._ensure_tab(channel)
        self._refresh_tabs()
        self._rebuild_html()

    def _visible_lines(self):
        """Linhas do canal/conversa mostrados (mensagens da app em todos)."""
        out = []
        want = core._speaker_key(self._view_partner) \
            if self._view_partner else None
        for ch, line in self._lines:
            if ch is None or self._view == "all":
                out.append(line)
            elif ch == self._view:
                if want and ch == "whisper":
                    m = re.match(r"^\[([^\]]+)\]", line)
                    # Parecido chega: o OCR lê o nome com uma letra
                    # trocada de vez em quando ('PlayerAlphe').
                    if m and core._similar(core._speaker_key(m.group(1)),
                                           want) < 0.8:
                        continue
                out.append(line)
        return out[-MAX_OVERLAY_LINES:]

    def capture_region(self):
        g = self.frameGeometry()
        x1 = g.x() + 3
        y1 = g.y() + self.HEADER_HEIGHT + 3
        x2 = g.x() + g.width() - 3
        y2 = g.y() + g.height() - 3
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            return None
        return (x1, y1, x2, y2)

    def showEvent(self, event):
        super().showEvent(event)
        if os.name == "nt":
            try:
                hwnd = int(self.winId())
                ok = set_capture_exclusion(hwnd, True)
                self._capture_excluded = ok
                log().info(f"DWM exclusion: {'ativa' if ok else 'falhou'}")
            except Exception as e:
                log().warning(f"DWM erro: {e}")
                self._capture_excluded = False
        if not self._state_loaded and self._pending_pos is not None:
            self.move(self._pending_pos)
            self._state_loaded = True
            log().info(f"Overlay em ({self._pending_pos.x()},"
                       f"{self._pending_pos.y()}) "
                       f"{self.width()}x{self.height()} "
                       f"locked={self._locked}")


# ==================================================================
# APPEARANCE DIALOG
# ==================================================================
class AppearanceDialog(QDialog):
    def __init__(self, parent=None, style: dict = None):
        super().__init__(parent)
        self.setWindowTitle(tr("grp_appearance"))
        self.setMinimumSize(520, 620)
        self.setStyleSheet(theme_qss())
        self._style = merge_overlay_style(style or {})
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        title = QLabel("🎨  " + tr("grp_appearance"))
        tf = QFont("Arial", 13); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        layout.addWidget(title)
        form = QFormLayout(); form.setSpacing(10)
        from PyQt6.QtWidgets import QFontComboBox
        self.font_cb = QFontComboBox()
        self.font_cb.setProperty("data_list", True)
        self.font_cb.setCurrentFont(QFont(self._style.get("font_family")
                                          or "Arial"))
        form.addRow(T("Chat font:"), self.font_cb)
        self.font_size_sb = QSpinBox()
        self.font_size_sb.setRange(8, 32)
        self.font_size_sb.setValue(int(self._style["font_size"]))
        form.addRow(tr("lbl_font_size"), self.font_size_sb)
        self.hdr_scale_sb = QSpinBox()
        self.hdr_scale_sb.setRange(80, 200)
        self.hdr_scale_sb.setSingleStep(10)
        self.hdr_scale_sb.setSuffix(" %")
        self.hdr_scale_sb.setValue(int(self._style.get("header_scale", 100)))
        self.hdr_scale_sb.setToolTip(T(
            "Size of the overlay's top bar: buttons, channel tabs and the "
            "AI speed numbers grow together."))
        form.addRow(T("Top bar size:"), self.hdr_scale_sb)
        self.bold_cb = QCheckBox(T("Bold"))
        self.bold_cb.setChecked(bool(self._style["font_bold"]))
        form.addRow("", self.bold_cb)
        self.speaker_mode_cb = QComboBox()
        self.speaker_mode_cb.addItem(T("Auto (varied colors)"), "auto")
        self.speaker_mode_cb.addItem(T("Single color"), "single")
        self.speaker_mode_cb.addItem(T("No color"), "none")
        for i in range(self.speaker_mode_cb.count()):
            if self.speaker_mode_cb.itemData(i) == self._style["speaker_color_mode"]:
                self.speaker_mode_cb.setCurrentIndex(i); break
        form.addRow(tr("lbl_speaker_mode"), self.speaker_mode_cb)
        self.speaker_color_btn = QPushButton()
        self._set_color_btn(self.speaker_color_btn,
                             self._style["speaker_color_single"])
        self.speaker_color_btn.clicked.connect(
            lambda: self._pick_color("speaker_color_single",
                                      self.speaker_color_btn))
        form.addRow(T("Name color:"), self.speaker_color_btn)
        self.text_color_btn = QPushButton()
        self._set_color_btn(self.text_color_btn, self._style["text_color"])
        self.text_color_btn.clicked.connect(
            lambda: self._pick_color("text_color", self.text_color_btn))
        form.addRow(tr("lbl_text_color"), self.text_color_btn)
        self.bg_color_btn = QPushButton()
        self._set_color_btn(self.bg_color_btn, self._style["bg_color"])
        self.bg_color_btn.clicked.connect(
            lambda: self._pick_color("bg_color", self.bg_color_btn))
        form.addRow(T("Background color:"), self.bg_color_btn)
        # Visibilidade do fundo em % (guardado como alfa 0-255).
        self.bg_alpha_sl = QSlider(Qt.Orientation.Horizontal)
        self.bg_alpha_sl.setRange(0, 100)
        pct = round(int(self._style["bg_alpha"]) * 100 / 255)
        self.bg_alpha_sl.setValue(pct)
        self.bg_alpha_lbl = QLabel(f"{pct}%")
        self.bg_alpha_lbl.setFixedWidth(44)
        h = QHBoxLayout(); h.addWidget(self.bg_alpha_sl, 1)
        h.addWidget(self.bg_alpha_lbl, 0)
        self.bg_alpha_sl.valueChanged.connect(
            lambda v: self.bg_alpha_lbl.setText(f"{v}%"))
        form.addRow(T("Background visibility:"), h)
        self.auto_hide_cb = QCheckBox(T("Auto-hide the chat when no one "
                                        "talks (the top bar stays)"))
        self.auto_hide_cb.setChecked(bool(self._style.get("auto_hide")))
        form.addRow("", self.auto_hide_cb)
        self.auto_hide_sb = QSpinBox()
        self.auto_hide_sb.setRange(5, 600)
        self.auto_hide_sb.setSuffix(" s")
        self.auto_hide_sb.setValue(int(self._style.get("auto_hide_secs", 20)))
        form.addRow(T("Hide after:"), self.auto_hide_sb)
        self.sep_cb = QCheckBox(T("Show a separator between messages"))
        self.sep_cb.setChecked(bool(self._style["show_separator"]))
        form.addRow("", self.sep_cb)
        self.sep_alpha_sl = QSlider(Qt.Orientation.Horizontal)
        self.sep_alpha_sl.setRange(0, 255)
        self.sep_alpha_sl.setValue(int(self._style["separator_alpha"]))
        self.sep_alpha_lbl = QLabel(str(self._style["separator_alpha"]))
        self.sep_alpha_lbl.setFixedWidth(40)
        h2 = QHBoxLayout(); h2.addWidget(self.sep_alpha_sl, 1)
        h2.addWidget(self.sep_alpha_lbl, 0)
        self.sep_alpha_sl.valueChanged.connect(
            lambda v: self.sep_alpha_lbl.setText(str(v)))
        form.addRow(T("Separator opacity:"), h2)
        self.spacing_sb = QSpinBox()
        self.spacing_sb.setRange(0, 20)
        self.spacing_sb.setValue(int(self._style["line_spacing"]))
        form.addRow(T("Line spacing:"), self.spacing_sb)
        layout.addLayout(form); layout.addStretch(1)
        btn_row = QHBoxLayout()
        btn_reset = QPushButton(tr("btn_reset_style"))
        btn_reset.clicked.connect(self._reset)
        btn_row.addWidget(btn_reset); btn_row.addStretch(1)
        btn_cancel = QPushButton(tr("capture_cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_apply = QPushButton(T("Apply"))
        btn_apply.clicked.connect(self._apply)
        btn_row.addWidget(btn_apply)
        layout.addLayout(btn_row)

    @staticmethod
    def _set_color_btn(btn, hex_color):
        btn.setText(hex_color)
        r, g, b = Overlay._hex_to_rgb(hex_color)
        # Letra legível em cores claras e escuras.
        ink = ("#1f2630" if 0.299 * r + 0.587 * g + 0.114 * b > 150
               else "#ffffff")
        btn.setStyleSheet(
            f"QPushButton{{background:{hex_color}; color:{ink};"
            f"border:1px solid #555; border-radius:4px; padding:4px;"
            f"min-width:60px;}}"
            f"QPushButton:hover{{border-color:{theme_colors()['primary']};}}")

    def _pick_color(self, key, btn):
        cur = QColor(self._style.get(key, "#000000"))
        c = QColorDialog.getColor(cur, self, T("Choose color"))
        if c.isValid():
            hx = c.name(); self._style[key] = hx
            self._set_color_btn(btn, hx)

    def _reset(self):
        self._style = dict(DEFAULT_OVERLAY_STYLE)
        self.font_cb.setCurrentFont(QFont(self._style["font_family"]))
        self.hdr_scale_sb.setValue(self._style["header_scale"])
        self.font_size_sb.setValue(self._style["font_size"])
        self.bold_cb.setChecked(self._style["font_bold"])
        for i in range(self.speaker_mode_cb.count()):
            if self.speaker_mode_cb.itemData(i) == self._style["speaker_color_mode"]:
                self.speaker_mode_cb.setCurrentIndex(i)
        self._set_color_btn(self.speaker_color_btn,
                             self._style["speaker_color_single"])
        self._set_color_btn(self.text_color_btn, self._style["text_color"])
        self._set_color_btn(self.bg_color_btn, self._style["bg_color"])
        self.bg_alpha_sl.setValue(round(self._style["bg_alpha"] * 100 / 255))
        self.auto_hide_cb.setChecked(self._style["auto_hide"])
        self.auto_hide_sb.setValue(self._style["auto_hide_secs"])
        self.sep_cb.setChecked(self._style["show_separator"])
        self.sep_alpha_sl.setValue(self._style["separator_alpha"])
        self.spacing_sb.setValue(self._style["line_spacing"])

    def _apply(self):
        self._style["font_family"] = self.font_cb.currentFont().family()
        self._style["header_scale"] = int(self.hdr_scale_sb.value())
        self._style["font_size"] = int(self.font_size_sb.value())
        self._style["font_bold"] = bool(self.bold_cb.isChecked())
        self._style["speaker_color_mode"] = self.speaker_mode_cb.currentData()
        self._style["bg_alpha"] = round(self.bg_alpha_sl.value() * 2.55)
        self._style["auto_hide"] = bool(self.auto_hide_cb.isChecked())
        self._style["auto_hide_secs"] = int(self.auto_hide_sb.value())
        self._style["show_separator"] = bool(self.sep_cb.isChecked())
        self._style["separator_alpha"] = int(self.sep_alpha_sl.value())
        self._style["line_spacing"] = int(self.spacing_sb.value())
        self.accept()

    def get_style(self): return dict(self._style)


# ==================================================================
# CONFIG WINDOW
# ==================================================================
# ==================================================================
# PAINEL DE IA (o do chat e o da voz são iguais)
# ==================================================================
class AIPanel(QGroupBox):
    """Uma IA (chat ou voz), tudo no mesmo sítio: IA, nome/URL do
    servidor próprio, chave, modelo (pesquisa, só grátis, grátis a verde,
    ⛔ recusados pela conta), perfil e opções. As chaves, URLs e nomes são
    da janela (partilhados): a mesma IA nos dois painéis mostra a mesma
    chave. Com IA local escondem-se as opções que só contam na nuvem."""
    FREE_COLOR = QColor("#22c55e")
    BLOCKED_COLOR = QColor("#ef4444")

    def __init__(self, owner, which):
        title = ("🧠 " + T("Chat translation AI (what you read)")
                 if which == "chat"
                 else "🎤 " + T("Voice AI (what you say)"))
        super().__init__(title)
        self.owner, self.which = owner, which
        self._prov = None           # IA na nuvem mostrada agora
        self._last_cloud = ""       # última IA na nuvem escolhida
        self._all_models = []       # lista completa (etiquetas) da IA
        O = owner
        f = self.form = QFormLayout(self)
        f.setSpacing(7)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignLeft
                            | Qt.AlignmentFlag.AlignVCenter)

        self.prov_cb = QComboBox()
        self.prov_cb.setProperty("data_list", True)
        if which == "voice":
            self.prov_cb.addItem(tr("voice_ai_same"), "")
        self.prov_cb.addItem("🖥 " + T("Local (Ollama, this PC)"), "local")
        for name in core.MT_ENGINES:        # tradutores sem IA
            self.prov_cb.addItem(core.mt_label(name), name)
        for name in CLOUD_PROVIDERS:
            self.prov_cb.addItem("☁ " + core.provider_label(name), name)
        self.prov_cb.currentIndexChanged.connect(self._on_prov_changed)
        f.addRow(T("AI:"), self.prov_cb)

        # Servidor próprio: nome (muda-se) e URL
        self.name_le = QLineEdit()
        self.name_le.setPlaceholderText(T("Name (e.g. SambaNova)"))
        self.name_le.setToolTip(T("The name this server shows in the "
                                  "lists and messages."))
        self.name_le.textEdited.connect(self._on_name_edited)
        f.addRow(T("Name:"), self.name_le)
        self.url_le = QLineEdit()
        self.url_le.setPlaceholderText("https://api.example.com/v1")
        self.url_le.textEdited.connect(self._on_url_edited)
        f.addRow(tr("lbl_custom_url"), self.url_le)

        # Chave
        self.key_le = QLineEdit()
        self.key_le.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_le.textEdited.connect(self._on_key_edited)
        self.btn_get = O._small_btn(tr("lbl_get_key"), self._open_docs)
        self.key_row = O._hbox(
            self.key_le,
            O._small_btn("👁", self._toggle_key, 36,
                         T("Show / hide the key")),
            O._small_btn(tr("btn_test_key"), self._test),
            self.btn_get)
        f.addRow(tr("lbl_api_key"), self.key_row)

        # Modelo + pesquisa + só grátis
        self.model_cb = QComboBox()
        self.model_cb.setProperty("data_list", True)
        self.model_cb.setMaxVisibleItems(20)
        self.model_row = O._hbox(
            self.model_cb,
            O._small_btn("🔄", self._refresh_list, 36,
                         T("Current list of this AI's models")))
        f.addRow(tr("lbl_model"), self.model_row)
        self.search_le = QLineEdit()
        self.search_le.setClearButtonEnabled(True)
        self.search_le.setPlaceholderText(
            "🔍 " + T("Search models (e.g. llama, 70b, free)"))
        self.search_le.textChanged.connect(lambda *_: self._apply_filter())
        self.free_cb = QCheckBox("🆓 " + T("Only free"))
        self.free_cb.setToolTip(T(
            "Shows and allows only free models (green in the list). With "
            "it on, the app never uses a paid model, also not as a "
            "fallback. ⛔ = refused by your account (blocked or paid)."))
        self.free_cb.toggled.connect(lambda *_: self._apply_filter())
        self.search_row = O._hbox(self.search_le, self.free_cb)
        f.addRow(self.search_row)

        # Perfil
        self.prof_cb = QComboBox()
        self.prof_cb.setProperty("data_list", True)
        self.prof_cb.activated.connect(lambda i: self._apply_profile())
        self.prof_row = O._hbox(
            self.prof_cb,
            O._small_btn("💾", self._save_profile, 36,
                         T("Save this AI + model + options as a "
                           "profile")),
            O._small_btn("🗑", self._delete_profile, 36,
                         T("Delete the chosen profile (⭐ ones can't be "
                           "deleted)")))
        f.addRow(T("Profile:"), self.prof_row)

        self.opts = ModelOptions(chat=(which == "chat"))
        f.addRow(self.opts)
        self.status = O._hint("")
        f.addRow(self.status)
        self.fallback_cb = self.btn_hf = None
        if which == "chat":
            self.fallback_cb = QCheckBox(tr("chk_fallback"))
            self.fallback_cb.setChecked(True)
            f.addRow(self.fallback_cb)
            self.btn_hf = QPushButton(tr("btn_hf"))
            self.btn_hf.setObjectName("hf")
            self.btn_hf.clicked.connect(O._open_hf)
            f.addRow(self.btn_hf)
        else:
            self.status.setText(T(
                "Your speech goes straight into the game: a better AI here "
                "is worth it. Two different cloud AIs at the same time are "
                "fine."))

    # ---------- o que está escolhido ----------
    def provider(self):
        return self.prov_cb.currentData() or ""

    def is_same(self):
        return self.which == "voice" and not self.provider()

    def is_local(self):
        return self.provider() == "local"

    def is_mt(self):
        """Tradutor sem IA (Google / Argos): sem chave, modelo nem perfis."""
        return core.is_mt_provider(self.provider())

    def is_cloud(self):
        return not (self.is_same() or self.is_local() or self.is_mt())

    def model(self):
        # Local sem modelos / Ollama desligado: a lista só tem o aviso
        # ('⚠️ No model installed') e fica desativada. O texto do aviso ia
        # para o Ollama como nome do modelo → '400 invalid model name'.
        if self.is_local() and not self.model_cb.isEnabled():
            return ""
        return core.model_id(self.model_cb.currentText()).strip()

    def _url(self):
        return self.owner._custom_urls.get(self._prov or "", "")

    def model_is_free(self):
        if not self.is_cloud():
            return True
        # Nome escrito à mão: usa a etiqueta (preço) que veio na lista.
        mid = self.model()
        label = next((l for l in self._all_models
                      if core.model_id(l) == mid), self.model_cb.currentText())
        return core.is_free_model(self._prov, label, self._url())

    # ---------- IA ----------
    def _on_prov_changed(self, *_):
        if not self.model_cb.isEnabled():
            # A lista só tinha o aviso do Local ('⚠️ No model installed'):
            # não pode passar para a nuvem como nome de modelo.
            self.model_cb.clear()
        prov = self.provider()
        self._prov = prov if self.is_cloud() else None
        if self._prov:
            self._last_cloud = self._prov
        self._load_fields()
        self._update_visibility()
        if self.is_local():
            self._refresh_local()
        elif self.is_cloud():
            self._show_cloud_models()
        self.fill_profiles()
        self.owner._update_gpu_visibility()

    def _load_fields(self):
        O, p = self.owner, self._prov or ""
        self.key_le.setText(O._api_keys.get(p, ""))
        self.url_le.setText(O._custom_urls.get(p, ""))
        self.name_le.setText(O._custom_names.get(p, ""))

    def _update_visibility(self):
        cloud, local, same = self.is_cloud(), self.is_local(), self.is_same()
        mt = self.is_mt()
        custom = cloud and core.is_custom_provider(self._prov)
        conf = CLOUD_PROVIDERS.get(self._prov or "") or {}
        ai = cloud or local
        rows = ((self.name_le, custom), (self.url_le, custom),
                (self.key_row, cloud), (self.model_row, ai),
                (self.search_row, cloud), (self.opts, ai),
                (self.prof_row, not mt))
        for w, vis in rows:
            self.form.setRowVisible(w, vis)
        self.key_le.setPlaceholderText(T("(optional)") if custom
                                       else "sk-...")
        self.btn_get.setEnabled(bool(conf.get("docs")))
        self.opts.set_cloud(cloud)
        self.model_cb.setEditable(cloud)
        if self.fallback_cb is not None:
            self.form.setRowVisible(self.fallback_cb, cloud)
            self.form.setRowVisible(self.btn_hf, local)
        if same:
            self.status.setText(T("Uses the chat AI (above)."))
            set_role(self.status, "muted")
        elif mt:
            self.status.setText({
                "google": T("No key and no account. Fast and free, but it "
                            "does not fix OCR mistakes or game slang like "
                            "an AI does. If Google blocks, it switches to "
                            "MyMemory and then to Argos."),
                "argos": T("Runs on this PC, without internet once ready. "
                           "The first time it downloads ~20 MB plus ~150 MB "
                           "per language pair (e.g. Russian→English)."),
                "nllb": T("Runs on this PC, without internet once ready: "
                          "one model for 200 languages. It downloads "
                          "~650 MB when you press Start the first time."),
            }.get(self.provider(), ""))
            set_role(self.status, "muted")

    def _on_key_edited(self, text):
        if self._prov:
            self.owner._api_keys[self._prov] = text.strip()
            self.owner._sync_fields(self, self._prov)

    def _on_url_edited(self, text):
        if self._prov:
            self.owner._custom_urls[self._prov] = text.strip()
            self.owner._sync_fields(self, self._prov)

    def _on_name_edited(self, text):
        if self._prov:
            self.owner._custom_names[self._prov] = text.strip()
            core.set_custom_names(self.owner._custom_names)
            self.owner._relabel(self._prov)
            self.owner._sync_fields(self, self._prov)

    def relabel(self, prov):
        i = self.prov_cb.findData(prov)
        if i >= 0:
            self.prov_cb.setItemText(i, "☁ " + core.provider_label(prov))

    def _toggle_key(self):
        M = QLineEdit.EchoMode
        self.key_le.setEchoMode(M.Normal if self.key_le.echoMode()
                                == M.Password else M.Password)

    def _open_docs(self):
        conf = CLOUD_PROVIDERS.get(self._prov or "") or {}
        if conf.get("docs"):
            try: webbrowser.open(conf["docs"])
            except Exception: pass

    def missing(self):
        """'' se a IA tem o que precisa; senão o que falta (para avisar)."""
        if not self.is_cloud():
            return ""
        conf = CLOUD_PROVIDERS.get(self._prov) or {}
        if core.is_custom_provider(self._prov) and not self._url():
            return "url"
        if conf.get("needs_key", True) and \
                not self.owner._api_keys.get(self._prov):
            return "key"
        return ""

    def _point_missing(self):
        what = self.missing()
        if not what:
            return False
        p = core.provider_label(self._prov)
        self.status.setText(
            T("🌐 Write the server URL for {p} here (and the key, if it "
              "needs one) and press Test.", p=p) if what == "url" else
            T("🔑 Paste the key for {p} here and press Test.", p=p))
        set_role(self.status, "warn")
        return True

    # ---------- lista de modelos ----------
    def _refresh_local(self):
        cur = self.model()
        self.model_cb.setEditable(False)
        running = is_ollama_running()
        installed = list_ollama_installed_models() if running else []
        self._all_models = list(installed)
        self.model_cb.clear()
        if installed:
            self.model_cb.addItems(installed)
            self.model_cb.setEnabled(True)
            i = self.model_cb.findText(cur) if cur else -1
            self.model_cb.setCurrentIndex(max(0, i))
            self.status.setText(tr("ollama_online", n=len(installed)))
            set_role(self.status, "ok")
            return
        self.model_cb.setEnabled(False)
        if running:
            self.model_cb.addItem(tr("no_model_item"), None)
            self.status.setText(tr("ollama_nomodel"))
            set_role(self.status, "warn")
        else:
            self.model_cb.addItem(tr("offline_item"), None)
            self.status.setText(tr("ollama_offline"))
            set_role(self.status, "err")

    def _show_cloud_models(self, keep=""):
        """Lista guardada desta IA já; a completa vem do fornecedor em
        fundo (não gasta pedidos)."""
        self.model_cb.setEnabled(True)
        self.set_models(self.owner._cloud_models_for(
            self._prov, keep or self.model()), keep=keep or self.model())
        if not self._point_missing():
            note = core.card_note(self._prov)
            self.status.setText(T(
                "🔄 = full list of this AI's models · 🔍 search · green = "
                "free") + (f"\n{note}" if note else ""))
            set_role(self.status, "muted")
        conf = CLOUD_PROVIDERS.get(self._prov) or {}
        if self._prov not in self.owner._model_lists and (
                self.owner._api_keys.get(self._prov)
                or conf.get("public_models") or self._url()):
            self.owner._start_cloud_check(self, self._prov, ping=False)

    def set_models(self, labels, keep=None):
        self._all_models = list(labels or [])
        self._apply_filter(keep)

    def _apply_filter(self, keep=None):
        if not self.is_cloud():
            return
        cur = keep if keep is not None else self.model()
        words = self.search_le.text().lower().split()
        free_only = self.free_cb.isChecked()
        prov, url = self._prov, self._url()
        cb = self.model_cb
        cb.blockSignals(True)
        cb.clear()
        for label in self._all_models:
            low = label.lower()
            if words and not all(w in low for w in words):
                continue
            free = core.is_free_model(prov, label, url)
            if free_only and not free:
                continue
            blocked = core.is_blocked(prov, label)
            text = label
            if blocked:
                text += (" ⛔" if core._LABEL_SEP in label
                         else core._LABEL_SEP + "⛔ " + T("refused by your "
                                                          "account"))
            cb.addItem(text)
            color = self.BLOCKED_COLOR if blocked else (
                self.FREE_COLOR if free else None)
            if color is not None:
                cb.setItemData(cb.count() - 1, color,
                               Qt.ItemDataRole.ForegroundRole)
        idx = next((i for i in range(cb.count())
                    if core.model_id(cb.itemText(i)) == cur), -1)
        if idx >= 0:
            cb.setCurrentIndex(idx)
        elif cur and not (free_only and not core.is_free_model(
                prov, cur, url)):
            cb.setCurrentText(cur)
        elif cb.count():
            cb.setCurrentIndex(0)
        cb.blockSignals(False)

    def _refresh_list(self):
        if self.is_local():
            self._refresh_local()
        elif self.is_cloud():
            self.owner._start_cloud_check(self, self._prov, ping=False)

    def _test(self):
        if self.is_cloud():
            self.owner._start_cloud_check(self, self._prov, ping=True)

    def on_check_done(self, ok, msg, models):
        self.status.setText(msg)
        set_role(self.status, "ok" if ok else "err")
        if ok and models:
            self.set_models(models, keep=self.model())

    # ---------- estado (config) ----------
    def set_state(self, prov, model, opts):
        self.prov_cb.blockSignals(True)
        if not self.owner._select_data(self.prov_cb, prov or ""):
            self.prov_cb.setCurrentIndex(0)
        self.prov_cb.blockSignals(False)
        self.free_cb.blockSignals(True)
        self.free_cb.setChecked(bool((opts or {}).get("free_only")))
        self.free_cb.blockSignals(False)
        self.opts.set(opts)
        self._prov = self.provider() if self.is_cloud() else None
        if self._prov:
            self._last_cloud = self._prov
        self._load_fields()
        self._update_visibility()
        if self.is_local():
            self._refresh_local()
            i = self.model_cb.findText(model or "")
            if i >= 0:
                self.model_cb.setCurrentIndex(i)
        elif self.is_cloud():
            self._show_cloud_models(keep=model or "")
        self.fill_profiles()
        self.owner._update_gpu_visibility()

    def get_state(self):
        opts = dict(self.opts.get())
        opts["free_only"] = self.free_cb.isChecked()
        return {"provider": self.provider(),
                "model": "" if self.is_same() or self.is_mt()
                else self.model(),
                "opts": opts}

    # ---------- perfis ----------
    def fill_profiles(self, profs=None, select=None):
        """Só os perfis do tipo escolhido no painel: com 'Local' os locais,
        com uma IA da nuvem os da nuvem (antes apareciam todos e com o
        Local escolhido via-se a lista das nuvens). 'Igual ao chat': todos."""
        if profs is None:
            profs = core.load_model_profiles()
        cb = self.prof_cb
        if select is None:
            select = cb.currentData()
        if self.is_local():
            profs = {n: d for n, d in profs.items()
                     if d.get("mode") == "local"}
            head = (T("— choose a local profile —") if profs else
                    T("— no local profiles yet (💾 saves one) —"))
        elif self.is_cloud():
            profs = {n: d for n, d in profs.items()
                     if d.get("mode") != "local"}
            head = T("— choose a cloud profile —")
        else:
            head = T("— choose a profile —")
        cb.blockSignals(True)
        cb.clear()
        cb.addItem(head, None)
        for name, d in profs.items():
            tag = {"tested": "  ✅", "free": "  🆓"}.get(d.get("note"), "")
            cb.addItem(name + tag, name)
        cb.setToolTip(T("⭐ = comes with the app · ✅ = tested with this "
                        "app · 🆓 = free plan (not tested here). Choosing "
                        "one fills in the AI, model and options."))
        if not (select and self.owner._select_data(cb, select)):
            cb.setCurrentIndex(0)
        cb.blockSignals(False)

    def _apply_profile(self):
        name = self.prof_cb.currentData()
        d = core.load_model_profiles().get(name) if name else None
        if not d:
            return
        model = d.get("model") or ""
        local = d.get("mode") == "local"
        prov = "local" if local else self.owner._resolve_provider(
            d.get("provider"))
        self.set_state(prov, model, d.get("opts"))
        if local and self.model_cb.findText(model) < 0:
            self.status.setText(T("⚠️ {m} is not installed — download it "
                                  "with 🤗 or 'ollama pull {m}'", m=model))
            set_role(self.status, "warn")
        elif not self._point_missing():
            self.status.setText(T("✅ Profile '{n}' applied — press Start "
                                  "to use it", n=name))
            set_role(self.status, "ok")
        log().info(f"Perfil de modelo ({self.which}): {name}")

    def _save_profile(self):
        if self.is_same():
            self.owner._warn(T("Choose the voice AI first (not 'Same as "
                               "chat')."))
            return
        st = self.get_state()
        if not st["model"]:
            self.owner._warn(T("Choose a model."))
            return
        data = {"mode": "local" if self.is_local() else "cloud",
                "provider": "" if self.is_local() else self._prov,
                "model": st["model"], "opts": st["opts"]}
        name, ok = QInputDialog.getText(
            self, T("Save model profile"), T("Profile name:"),
            text=st["model"].split("/")[-1])
        name = (name or "").strip()
        if not ok or not name:
            return
        if name in core.MODEL_PRESETS:
            self.owner._warn(T("That name belongs to a ⭐ profile — "
                               "choose another."))
            return
        if core.save_model_profile(name, data):
            self.owner._refresh_model_profiles(select=(self, name))

    def _delete_profile(self):
        name = self.prof_cb.currentData()
        if not name:
            return
        if name in core.MODEL_PRESETS:
            self.owner._warn(T("⭐ profiles come with the app and can't be "
                               "deleted."))
            return
        if QMessageBox.question(self, tr("warn"), T(
                "Delete the profile '{n}'?", n=name)) \
                != QMessageBox.StandardButton.Yes:
            return
        core.delete_model_profile(name)
        self.owner._refresh_model_profiles()


class QuickGuideDialog(QDialog):
    """🔊 Guia rápido: só o essencial para pôr o overlay a traduzir e a
    ler em voz alta. Cada passo é lido pela voz neural (na língua da
    interface) e o campo a mexer pisca na janela principal. Não é modal:
    vais fazendo enquanto ele explica."""

    HL = "border:2px solid {c}; border-radius:6px;"
    voice_failed = pyqtSignal()     # da thread da voz → aviso no guia
    VOICE_WORKERS = 4               # frases geradas ao mesmo tempo

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle(T("🔊 Quick start"))
        self.setStyleSheet(theme_qss())
        self.setMinimumWidth(540)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # (título, texto, campo da janela principal a destacar)
        self.steps = [
            (T("Welcome"),
             T("This guide shows only the essentials: your name, the "
               "translator, your language, the voice and Start. Do each "
               "step in the main window and press Next."), None),
            (T("1. Your character name"),
             T("Write your character name exactly as it appears in the "
               "game. Your own messages are then ignored and not read "
               "aloud."), "my_name_le"),
            (T("2. Translator or AI?"),
             T("In the chat AI panel choose what translates. Translators, "
               "without AI: Google Translate is online and fast, with "
               "nothing to install and no key; Argos and NLLB work without "
               "internet and download by themselves when you press Start. "
               "They are quick and have no limits, but translate word for "
               "word and don't understand game slang or fix reading "
               "mistakes. AIs translate better: they understand slang and "
               "fix those mistakes. A local AI, Ollama, for example "
               "gemma2:2b from Download models, is free and private, but "
               "uses graphics memory and processor while you play. A cloud "
               "AI uses nothing on your PC, but needs a key, and free plans "
               "have daily limits. To start, Google Translate is enough."),
             "chat_panel.prov_cb"),
            (T("3. Chat reads per minute"),
             T("Chat reads per minute is how often the app reads the game "
               "chat. With a cloud AI it matters: each read that finds new "
               "messages is one request, and the messages that arrived in "
               "between go together. Fewer reads mean fewer requests, so "
               "the free daily limit lasts longer, but translations appear "
               "a little later; more reads show them sooner and spend more "
               "requests. With the chat idle nothing is sent. With "
               "translators or a local AI there is no limit: fewer reads "
               "only save processor."), "ocr_rate_cb"),
            (T("4. Your language"),
             T("In Chat reading, set Translate to to your language. Leave "
               "the source language on Auto: it detects each message."),
             "ocr_tgt_cb"),
            (T("5. Hear the translations"),
             T("Tick Read translations aloud and choose a voice in your "
               "language. Listen plays an example. If you hear nothing, "
               "choose the output device in App settings."), "tts_cb"),
            (T("6. Talk into the game (optional)"),
             T("If you also want to speak and have it written in the game "
               "chat: in Microphone check the voice hotkey, F11 by default, "
               "or press Record to choose another, and set I speak and "
               "Write in. Choose the microphone in App settings and press "
               "Test to check it hears you. Then, in the game, hold the "
               "key, speak and let go: the app translates it and types it "
               "in the chat. A rising beep means it is listening; Esc "
               "cancels. Mode also offers tap or continuous. You can turn "
               "on Confirm before sending to check each message first, say "
               "reply and your message to answer the last private message, "
               "or say change to chat guild to switch channel."),
             "voice_hotkey_le"),
            (T("7. Start"),
             T("Open RF Online and press Start translator. The overlay "
               "appears over the game: open the game chat and the "
               "messages show up translated and are read aloud. Done!"),
             "start_btn"),
        ]
        self.i = 0
        # Voz: cada passo partido em frases, geradas de antemão por várias
        # threads (o passo aberto primeiro) e guardadas só em memória. A
        # voz neural demora ~1 s por frase curta e ~8 s por um passo
        # inteiro: assim a 1.ª frase entra logo e o resto segue.
        self._chunks = [self._split(self._spoken(k))
                        for k in range(len(self.steps))]
        self._audio = {}            # (passo, frase) → mp3
        self._taken = set()         # frases a ser geradas
        self._audio_lock = threading.Lock()
        self._workers = 0
        self._failed = False
        self._closed = False
        self._play_step = None      # passo a ser lido agora
        self._play_k = 0            # próxima frase a tocar
        self._player = QTimer(self)
        self._player.setInterval(60)
        self._player.timeout.connect(self._tick)
        self._hl = None             # (widget, folha de estilo original)
        self._blink = False
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._pulse)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)
        self.lbl_count = QLabel()
        set_role(self.lbl_count, "muted")
        v.addWidget(self.lbl_count)
        self.lbl_title = QLabel()
        tf = QFont("Arial", 13); tf.setBold(True)
        self.lbl_title.setFont(tf); set_role(self.lbl_title, "title")
        v.addWidget(self.lbl_title)
        self.lbl_text = QLabel()
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setMinimumHeight(110)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        v.addWidget(self.lbl_text, 1)
        self.voice_chk = QCheckBox(T("🔊 Read the steps aloud"))
        self.voice_chk.setChecked(True)
        self.voice_chk.toggled.connect(
            lambda on: self._say() if on else self._quiet())
        v.addWidget(self.voice_chk)
        self.lbl_voice_err = QLabel(T(
            "⚠️ The voice needs internet — the steps are written above."))
        set_role(self.lbl_voice_err, "err")
        self.lbl_voice_err.setWordWrap(True)
        self.lbl_voice_err.hide()
        self.voice_failed.connect(self._on_voice_failed)
        v.addWidget(self.lbl_voice_err)
        row = QHBoxLayout()
        self.btn_back = QPushButton(T("◀ Back"))
        self.btn_back.clicked.connect(lambda: self._go(-1))
        self.btn_again = QPushButton(T("🔁 Repeat"))
        self.btn_again.clicked.connect(self._say)
        self.btn_next = QPushButton()
        self.btn_next.setObjectName("start")
        self.btn_next.clicked.connect(lambda: self._go(1))
        row.addWidget(self.btn_back); row.addWidget(self.btn_again)
        row.addStretch(1); row.addWidget(self.btn_next)
        v.addLayout(row)
        self._show()

    # ---- voz
    def _voice(self):
        """Uma das vozes neurais da app, na língua da interface: a que
        escolheste em 🔊 Voz Neural se for desta língua, senão a 1.ª."""
        lang = get_ui_lang()
        voices = TTS_VOICES_BY_LANG.get(lang) or TTS_VOICES_BY_LANG["en"]
        mine = self.owner.voice_cb.currentData() or ""
        if any(code == mine for _, code in voices):
            return mine
        return voices[0][1]

    def _tts(self):
        if self.owner.tts is None:
            self.owner.tts = TTSManager()
        return self.owner.tts

    def _spoken(self, idx):
        """Texto falado do passo: sem o número ('2. ')."""
        title, text, _ = self.steps[idx]
        title = re.sub(r"^\d+\.\s*", "", title)
        return title + (" " if title[-1:] in "?!." else ". ") + text

    @staticmethod
    def _split(text):
        """Frases (corta em . ! ? ; : seguidos de espaço)."""
        parts = re.split(r"(?<=[.!?;:])\s+", text.strip())
        return [p for p in parts if p.strip()]

    def _next_job(self):
        """Próxima frase a gerar: as do passo aberto, depois as dos passos
        seguintes, depois as de trás. Chamar com o lock."""
        n = len(self.steps)
        order = list(range(self.i, n)) + list(range(0, self.i))
        for st in order:
            for k in range(len(self._chunks[st])):
                key = (st, k)
                if key not in self._audio and key not in self._taken:
                    return key
        return None

    def _fetch(self):
        """Arranca as threads que geram a voz (a voz neural da app; nunca
        passa pela IA nem pelo tradutor: os textos já vêm traduzidos)."""
        self._failed = False
        voice = self._voice()
        tts = self._tts()

        def run():
            try:
                while not self._closed and not self._failed:
                    with self._audio_lock:
                        key = self._next_job()
                        if key is None:
                            return
                        self._taken.add(key)
                    try:
                        audio = tts.synth(self._chunks[key[0]][key[1]], voice)
                    finally:
                        with self._audio_lock:
                            self._taken.discard(key)
                    with self._audio_lock:
                        self._audio[key] = audio
            except Exception as e:
                log().warning(f"guia: voz falhou: {e}")
                self._failed = True
                if not self._closed:
                    self.voice_failed.emit()
            finally:
                with self._audio_lock:
                    self._workers -= 1

        with self._audio_lock:
            start = self.VOICE_WORKERS - self._workers
            self._workers += max(0, start)
        for _ in range(max(0, start)):
            threading.Thread(target=run, daemon=True,
                             name="GuideVoice").start()

    def _say(self):
        """Lê o passo aberto desde o início: cala logo o anterior e toca
        as frases deste à medida que ficam prontas."""
        self._quiet()
        self._play_step = None
        if not self.voice_chk.isChecked():
            return
        self.lbl_voice_err.hide()
        self._play_step, self._play_k = self.i, 0
        if self._failed or self._workers == 0:
            self._fetch()
        self._player.start()

    def _tick(self):
        """Toca a frase seguinte quando a anterior acabou."""
        st = self._play_step
        if st is None or self._closed or st != self.i:
            self._player.stop()
            return
        tts = self._tts()
        if tts.is_playing():
            return
        if self._play_k >= len(self._chunks[st]):
            self._play_step = None          # passo lido até ao fim
            self._player.stop()
            return
        with self._audio_lock:
            audio = self._audio.get((st, self._play_k))
        if audio is None:
            return                          # ainda a gerar
        self._play_k += 1
        self._play(audio)

    def _play(self, audio):
        try:
            tts = self._tts()
            tts.configure(tts.enabled, tts.voice,
                          self.owner.out_cb.currentData())
            tts.play_bytes(audio)
        except Exception:
            log().exception("guia: tocar voz")

    def _on_voice_failed(self):
        if self._play_step is not None:
            self.lbl_voice_err.show()
        self._play_step = None
        self._player.stop()

    def _quiet(self):
        try:
            self._tts().stop_preview()
        except Exception:
            pass

    # ---- destaque do campo
    def _target(self, path):
        obj = self.owner
        for part in (path or "").split("."):
            obj = getattr(obj, part, None) if part else None
        return obj if isinstance(obj, QWidget) else None

    def _unhighlight(self):
        self._timer.stop()
        if self._hl:
            w, css = self._hl
            self._hl = None
            try:
                w.setStyleSheet(css)
            except RuntimeError:        # a janela foi reconstruída
                pass

    def _pulse(self):
        if not self._hl:
            return
        self._blink = not self._blink
        w, css = self._hl
        c = "#f59e0b" if self._blink else "transparent"
        try:
            w.setStyleSheet(css + self.HL.format(c=c)
                            if w.objectName() != "start" else
                            css + f"QPushButton#start{{{self.HL.format(c=c)}}}")
        except RuntimeError:
            self._hl = None

    def _highlight(self, path):
        self._unhighlight()
        w = self._target(path)
        if w is None:
            return
        self._hl = (w, w.styleSheet())
        page = self.owner.findChild(QScrollArea, "page")
        if page is not None:
            try:
                page.ensureWidgetVisible(w, 40, 80)
            except Exception:
                pass
        self._blink = False
        self._pulse()
        self._timer.start()

    # ---- passos
    def _show(self):
        title, text, target = self.steps[self.i]
        n = len(self.steps)
        self.lbl_count.setText(T("Step {a} of {b}", a=self.i + 1, b=n))
        self.lbl_title.setText(title)
        self.lbl_text.setText(text)
        self.btn_back.setEnabled(self.i > 0)
        self.btn_next.setText(T("Next ▶") if self.i < n - 1
                              else T("✔ Finish"))
        self._highlight(target)
        # Textos de tamanhos diferentes: a janela cresce/encolhe com eles,
        # mas não sai do sítio (o canto de cima fica onde a puseste).
        pos = self.pos()
        self.adjustSize()
        if self.isVisible():
            self.move(pos)
        self._say()

    def _go(self, d):
        if self.i + d >= len(self.steps):
            self.close()
            return
        self.i = max(0, self.i + d)
        self._show()

    def closeEvent(self, event):
        self._closed = True
        self._play_step = None
        self._player.stop()
        self._unhighlight()
        self._quiet()
        super().closeEvent(event)

    def place(self):
        """Só ao abrir: à direita, em cima, na janela principal (cresce
        para baixo com os passos maiores). Depois fica onde a puseres."""
        self.adjustSize()
        g = self.owner.frameGeometry()
        self.move(g.right() - self.width() - 30, g.top() + 90)


class SettingsDialog(QDialog):
    """Definições da app (botão ⚙ da janela principal): língua da
    interface, tema, aparência do overlay, o que faz o ✕ de cada janela,
    pacotes de idiomas e dispositivos de áudio. Os widgets ficam também na ConfigWindow
    (owner.mic_cb, owner.out_cb...), que os grava na config como antes.
    Mudar a língua reconstrói a janela principal e esta."""

    def __init__(self, owner):
        super().__init__(owner)
        self.setWindowTitle(T("App settings"))
        self.setStyleSheet(theme_qss())
        self.setMinimumWidth(600)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)
        title = QLabel(T("⚙ App settings"))
        tf = QFont("Arial", 13); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        v.addWidget(title)

        g, f = owner._group("🌐 " + T("Interface"))
        owner.ui_lang_cb = QComboBox()
        for code, name in UI_LANGS.items():
            owner.ui_lang_cb.addItem(name, code)
        owner._select_data(owner.ui_lang_cb, get_ui_lang())
        owner.ui_lang_cb.currentIndexChanged.connect(
            owner._on_ui_lang_changed)
        f.addRow(tr("grp_language") + ":", owner.ui_lang_cb)
        owner.theme_cb = QComboBox()
        for key in core.UI_THEMES:
            owner.theme_cb.addItem(tr(f"theme_{key}"), key)
        owner._select_data(owner.theme_cb, core.get_ui_theme())
        owner.theme_cb.currentIndexChanged.connect(owner._on_theme_changed)
        f.addRow(tr("lbl_theme"), owner.theme_cb)
        v.addWidget(g)

        g, f = owner._group("🎨 " + tr("grp_appearance"))
        owner.btn_appearance = QPushButton("🎨  " + tr("grp_appearance"))
        owner.btn_appearance.setObjectName("appearance")
        owner.btn_appearance.clicked.connect(owner._open_appearance)
        f.addRow(owner.btn_appearance)
        owner.app_status = owner._hint("")
        f.addRow(owner.app_status)
        v.addWidget(g)

        g, f = owner._group("✕ " + T("When closing"))
        self.close_cbs = {}
        for which, label, items in (
                ("close_overlay", T("✕ in chat mode (overlay):"),
                 (("config", T("Go back to the main window")),
                  ("quit", T("Close the app")))),
                ("close_main", T("✕ in the main window:"),
                 (("quit", T("Close the app")),
                  ("tray", T("Keep running in the tray (icon next to "
                             "the clock)"))))):
            cb = QComboBox()
            for key, text in items:
                cb.addItem(text, key)
            owner._select_data(cb, core.get_close_action(which))
            cb.currentIndexChanged.connect(
                lambda _i, w=which, c=cb:
                core.set_close_action(w, c.currentData()))
            f.addRow(label, cb)
            self.close_cbs[which] = cb
        f.addRow(owner._hint(T("❌ Quit in the overlay menu and in the "
                               "tray icon always closes the app.")))
        v.addWidget(g)

        g, f = owner._group(tr("ov_lang"))
        f.addRow(owner._hint(T("Languages the app can read in the game "
                               "chat (text recognition, OCR).")))
        owner.btn_lang_mgr = QPushButton(tr("btn_lang_mgr"))
        owner.btn_lang_mgr.setObjectName("lang")
        owner.btn_lang_mgr.clicked.connect(owner._open_lang_manager)
        f.addRow(owner.btn_lang_mgr)
        v.addWidget(g)

        g, f = owner._group("🎧 " + tr("grp_audio"))
        owner.mic_cb = QComboBox()
        owner.btn_mic_test = owner._small_btn(
            tr("btn_mic_test"), owner._test_mic,
            tip=T("Talk for 5 s: shows this input's level and what the "
                  "recognition understood"))
        f.addRow(tr("lbl_mic"), owner._hbox(
            owner.mic_cb,
            owner._small_btn("🔄", owner._refresh_audio_devices, 36),
            owner.btn_mic_test))
        owner.mic_level = QProgressBar()
        owner.mic_level.setRange(0, 100)
        owner.mic_level.setTextVisible(False)
        owner.mic_level.setFixedHeight(8)
        owner.mic_level.hide()
        f.addRow(owner.mic_level)
        owner.mic_test_lbl = owner._hint("")
        owner.mic_test_lbl.hide()
        f.addRow(owner.mic_test_lbl)
        owner.out_cb = QComboBox()
        f.addRow(tr("lbl_out"), owner.out_cb)
        f.addRow(owner._hint(T("The devices are saved when you press "
                               "Start.")))
        v.addWidget(g)

        # Atualizações: compara com o GitHub e troca só o código (~0,3 MB);
        # Python, Ollama, modelos e definições ficam como estão.
        g, f = owner._group("🔄 " + T("Updates"))
        self._upd_changed = None        # ficheiros diferentes do GitHub
        self._upd_silent = False
        self._upd_sig = _UpdateSignals()
        self._upd_sig.checked.connect(self._upd_checked)
        self._upd_sig.applied.connect(self._upd_applied)
        self._upd_sig.status.connect(lambda t: self.upd_lbl.setText(t))
        self.upd_btn = QPushButton(T("🔄 Check for updates"))
        self.upd_btn.clicked.connect(self._upd_click)
        self.upd_lbl = owner._hint(T("Only the app's code is replaced (~0.3 "
                                     "MB). Your settings, keys, models and "
                                     "the app's Python stay as they are."))
        f.addRow(self.upd_btn)
        f.addRow(self.upd_lbl)
        if core.update_is_dev_copy():
            self.upd_btn.setEnabled(False)
            self.upd_lbl.setText(T("This folder is a development copy "
                                   "(git): update it with git."))
        v.addWidget(g)

        v.addStretch(1)
        close = QPushButton(tr("btn_close"))
        close.clicked.connect(self.accept)
        v.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)

    # ---------- atualizações ----------
    def check_updates(self, silent=False):
        """Em fundo. silent=True (ao abrir a app): só avisa se houver."""
        if core.update_is_dev_copy():
            return
        self._upd_silent = silent
        if not silent:
            self.upd_btn.setEnabled(False)
            self.upd_lbl.setText(T("🔄 Checking…"))

        def run():
            try:
                res = core.update_check()
            except Exception as e:
                res = e
            self._upd_sig.checked.emit(res)
        threading.Thread(target=run, daemon=True, name="UpdateCheck").start()

    def _upd_click(self):
        if self._upd_changed:
            self._upd_apply()
        else:
            self.check_updates()

    def _upd_checked(self, res):
        if getattr(self, "_upd_busy", False):
            return      # já a atualizar (ex.: a verificação do arranque)
        self.upd_btn.setEnabled(True)
        owner = self.parent()
        if isinstance(res, Exception):
            log().warning(f"Atualizações: falhou: {res}")
            if not self._upd_silent:
                self.upd_lbl.setText(T("⚠️ Could not check: {e}",
                                       e=str(res)[:150]))
            return
        self._upd_changed = res
        if res:
            self.upd_lbl.setText(T("🆕 There is a new version ({n} files "
                                   "changed).", n=len(res)))
            self.upd_btn.setText(T("⬇️ Update now"))
            if owner is not None and hasattr(owner, "btn_settings"):
                owner.btn_settings.setText(T("⚙ App settings") + "  🆕")
                owner.btn_settings.setToolTip(T(
                    "There is a new version: open the settings and press "
                    "Update now."))
        elif not self._upd_silent:
            self.upd_lbl.setText(T("✅ You have the latest version."))

    def _upd_apply(self):
        self._upd_busy = True
        self.upd_btn.setEnabled(False)
        changed = list(self._upd_changed or [])

        def run():
            try:
                msg = core.update_apply(changed,
                                        status=self._upd_sig.status.emit)
                self._upd_sig.applied.emit(msg, True)
            except Exception as e:
                log().exception("Atualização falhou")
                self._upd_sig.applied.emit(
                    T("⚠️ The update failed: {e}", e=str(e)[:150]), False)
        threading.Thread(target=run, daemon=True, name="Update").start()

    def _upd_applied(self, msg, ok):
        self.upd_lbl.setText(msg)
        owner = self.parent()
        if not ok:
            self._upd_busy = False
            self.upd_btn.setEnabled(True)
            return
        # Reinicia já com o código novo (o que está aberto é o antigo).
        restart = getattr(owner, "on_restart", None)
        if restart:
            QTimer.singleShot(1500, restart)


class _UpdateSignals(QObject):
    """Da thread das atualizações para a janela (Qt só na thread
    principal)."""
    checked = pyqtSignal(object)        # [ficheiros] ou Exception
    applied = pyqtSignal(str, bool)     # (mensagem, correu bem)
    status = pyqtSignal(str)


def _native_to_logical(x, y):
    """Píxel físico do ecrã (Win32) → coordenada do Qt. O Qt escala cada
    monitor à volta da sua origem (ecrãs a 125%/150%)."""
    for s in QApplication.screens():
        g, dpr = s.geometry(), s.devicePixelRatio()
        if g.x() <= x < g.x() + g.width() * dpr \
                and g.y() <= y < g.y() + g.height() * dpr:
            return QPoint(round(g.x() + (x - g.x()) / dpr),
                          round(g.y() + (y - g.y()) / dpr))
    return QPoint(int(x), int(y))


def _logical_to_native(p):
    s = QApplication.screenAt(p) or QApplication.primaryScreen()
    g, dpr = s.geometry(), s.devicePixelRatio()
    return (g.x() + (p.x() - g.x()) * dpr, g.y() + (p.y() - g.y()) * dpr)


class ChatCalibrator(QWidget):
    """Retângulo transparente por cima do jogo: arrastas e redimensionas
    até cobrir as mensagens do chat e carregas em ✔ Confirmar (ou Enter).
    Bordas largas para pegar facilmente; setas movem 1 px (Shift = muda o
    tamanho). Depois desaparece; a zona fica em fracções da altura do jogo
    (como core.CHAT_REGION_REL)."""
    GRIP = 18                   # px das bordas/cantos que redimensionam
    MIN_W, MIN_H = 240, 180

    def __init__(self, game_rect, rect_rel, on_done):
        super().__init__()
        self.game_rect = game_rect          # (x, y, w, h) físicos
        self.on_done = on_done              # on_done(rect_rel | None | 'auto')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setMinimumSize(self.MIN_W, self.MIN_H)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        gx, gy, gw, gh = game_rect
        x1, y1, x2, y2 = rect_rel
        tl = _native_to_logical(gx + x1 * gh, gy + y1 * gh)
        br = _native_to_logical(gx + x2 * gh, gy + y2 * gh)
        self.setGeometry(tl.x(), tl.y(), max(self.MIN_W, br.x() - tl.x()),
                         max(self.MIN_H, br.y() - tl.y()))
        self._press = None          # (posição global, geometria, zona)
        self._done = False

        box = QFrame(self)
        box.setObjectName("calibBox")
        box.setStyleSheet(
            "#calibBox{background:rgba(17,24,39,225); border-radius:8px;"
            " border:1px solid #60a5fa;}"
            "QLabel{color:#f3f4f6; font-size:12px; background:transparent;"
            " border:none;}"
            "QPushButton{color:#fff; border:none; border-radius:5px;"
            " padding:6px 10px; font-weight:bold; font-size:12px;}")
        v = QVBoxLayout(box)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(6)
        lbl = QLabel(T("Drag and resize this box so it covers the chat "
                       "messages (from the channel tags on the left to the "
                       "end of the text). Enter = confirm, Esc = cancel."))
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        row = QHBoxLayout()
        for text, color, slot in (
                ("✔ " + T("Confirm"), "#16a34a", self._confirm),
                ("↺ " + T("Automatic"), "#4d6c94", self._auto),
                ("✖ " + T("Cancel"), "#9b3b3b", self._cancel)):
            b = QPushButton(text)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{background:{color};}}")
            b.clicked.connect(slot)
            row.addWidget(b)
        v.addLayout(row)
        self._box = box
        self._place_box()
        # Só à vista com o jogo (ou esta caixa) à frente: com alt-tab
        # esconde-se, como o overlay.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._game = GameWindow()
        self._vis_timer = QTimer(self)
        self._vis_timer.setInterval(200)
        self._vis_timer.timeout.connect(self._follow_game)
        self._vis_timer.start()

    def _follow_game(self):
        if self._done:
            return
        front = (self._game.is_foreground()
                 or self._game.foreground_is_own_process())
        if front != self.isVisible() and not self._press:
            self.setVisible(front)

    # ---------- desenho ----------
    def _place_box(self):
        w = min(self.width() - 2 * self.GRIP, 420)
        self._box.setFixedWidth(max(160, w))
        self._box.adjustSize()
        self._box.move((self.width() - self._box.width()) // 2,
                       (self.height() - self._box.height()) // 2)

    def resizeEvent(self, e):
        self._place_box()
        super().resizeEvent(e)

    def paintEvent(self, _):
        from PyQt6.QtGui import QPainter, QPen, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        # Fundo quase transparente (vê-se o chat) mas clicável.
        p.fillRect(r, QColor(59, 130, 246, 38))
        p.setPen(QPen(QColor("#3b82f6"), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(r)
        # Pegas nos cantos e a meio das bordas.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#93c5fd")))
        g = self.GRIP
        w, h = self.width(), self.height()
        for x, y in ((0, 0), (w - g, 0), (0, h - g), (w - g, h - g),
                     ((w - g) // 2, 0), ((w - g) // 2, h - g),
                     (0, (h - g) // 2), (w - g, (h - g) // 2)):
            p.drawRoundedRect(x + 2, y + 2, g - 4, g - 4, 3, 3)

    # ---------- rato ----------
    def _zone(self, pos):
        g, w, h = self.GRIP, self.width(), self.height()
        left, right = pos.x() < g, pos.x() > w - g
        top, bottom = pos.y() < g, pos.y() > h - g
        return (left, top, right, bottom)

    def _cursor_for(self, z):
        left, top, right, bottom = z
        C = Qt.CursorShape
        if (left and top) or (right and bottom):
            return C.SizeFDiagCursor
        if (right and top) or (left and bottom):
            return C.SizeBDiagCursor
        if left or right:
            return C.SizeHorCursor
        if top or bottom:
            return C.SizeVerCursor
        return C.SizeAllCursor

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = (e.globalPosition().toPoint(), self.geometry(),
                           self._zone(e.position().toPoint()))

    def mouseMoveEvent(self, e):
        if not self._press:
            self.setCursor(self._cursor_for(self._zone(e.position().toPoint())))
            return
        start, geo, (left, top, right, bottom) = self._press
        d = e.globalPosition().toPoint() - start
        x1, y1, x2, y2 = geo.left(), geo.top(), geo.right(), geo.bottom()
        if not any((left, top, right, bottom)):
            self.move(geo.topLeft() + d)
            return
        if left:
            x1 = min(x1 + d.x(), x2 - self.MIN_W)
        if right:
            x2 = max(x2 + d.x(), x1 + self.MIN_W)
        if top:
            y1 = min(y1 + d.y(), y2 - self.MIN_H)
        if bottom:
            y2 = max(y2 + d.y(), y1 + self.MIN_H)
        self.setGeometry(x1, y1, x2 - x1 + 1, y2 - y1 + 1)

    def mouseReleaseEvent(self, _):
        self._press = None

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
            return
        if k == Qt.Key.Key_Escape:
            self._cancel()
            return
        step = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}.get(k)
        if step:
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.resize(max(self.MIN_W, self.width() + step[0]),
                            max(self.MIN_H, self.height() + step[1]))
            else:
                self.move(self.x() + step[0], self.y() + step[1])
            return
        super().keyPressEvent(e)

    # ---------- fim ----------
    def rect_rel(self):
        """Zona em fracções da altura da área cliente do jogo."""
        gx, gy, gw, gh = self.game_rect
        g = self.geometry()
        x1, y1 = _logical_to_native(g.topLeft())
        x2, y2 = _logical_to_native(QPoint(g.right() + 1, g.bottom() + 1))
        x1, x2 = max(0, x1 - gx), min(gw, x2 - gx)
        y1, y2 = max(0, y1 - gy), min(gh, y2 - gy)
        return [round(v / gh, 5) for v in (x1, y1, x2, y2)]

    def _finish(self, result):
        if self._done:
            return
        self._done = True
        self._vis_timer.stop()
        self.hide()
        self.deleteLater()
        self.on_done(result)

    def _confirm(self):
        self._finish(self.rect_rel())

    def _auto(self):
        self._finish("auto")

    def _cancel(self):
        self._finish(None)

    def closeEvent(self, e):
        self._finish(None)
        super().closeEvent(e)


class ConfigWindow(QMainWindow):
    """Janela de configuração em 3 colunas: Geral · IA · Jogo e voz.
    Tudo visível (a área rola se o ecrã for pequeno); mudar a língua
    reconstrói a janela inteira na língua nova."""

    def __init__(self, on_start, last_cfg=None, on_hf=None, on_log=None):
        super().__init__()
        self.on_start = on_start
        self.on_hf = on_hf
        self.on_log = on_log
        self._api_keys, self._cloud_models = {}, {}
        self._custom_urls = {}          # servidor personalizado → URL
        self._custom_names = {}         # servidor personalizado → nome
        self._model_lists = {}          # IA → lista completa de modelos
        self.panels = ()
        self._acct_provider = None
        self._mic_tester = None
        self.tts = None                 # da app (para o '▶ Ouvir')
        self._mic_names = {}
        self._check_prov = {}           # pedido à nuvem → fornecedor
        self._cloud_sig = _CloudSignals()
        self._cloud_sig.done.connect(self._on_cloud_done)
        self.settings_dlg = None
        self.on_close = None            # da app: ✕ desta janela
        self._build_ui()
        try:
            if last_cfg is None:
                last_cfg = load_last_config()
            if last_cfg:
                self._apply_config(last_cfg)
                log().info("Last config restaurada")
        except Exception:
            log().exception("Falha a restaurar last config")
        scr = QApplication.primaryScreen()
        avail = scr.availableGeometry() if scr else None
        w, h = 1500, 1010
        if avail is not None:
            w, h = min(w, avail.width() - 40), min(h, avail.height() - 60)
        self.resize(w, h)
        self.setMinimumSize(900, 560)

    # ------------------------------------------------------------ UI
    @staticmethod
    def _group(title):
        g = QGroupBox(title)
        f = QFormLayout(g)
        f.setSpacing(7)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignLeft
                            | Qt.AlignmentFlag.AlignVCenter)
        return g, f

    @staticmethod
    def _small_btn(text, slot, width=None, tip=""):
        b = QPushButton(text)
        b.setObjectName("small")
        if width:
            b.setFixedWidth(width)
        if tip:
            b.setToolTip(tip)
        b.clicked.connect(slot)
        return b

    @staticmethod
    def _hint(text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        set_role(lbl, "muted")
        return lbl

    @staticmethod
    def _hbox(*widgets, stretch_first=True):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        for i, x in enumerate(widgets):
            h.addWidget(x, 1 if (i == 0 and stretch_first) else 0)
        return w

    @staticmethod
    def _slider(lo, hi, step, value, unit):
        """(QSlider, linha com o valor à direita e ↺ para o padrão)."""
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(lo, hi)
        sl.setSingleStep(step)
        sl.setPageStep(step * 2)
        lbl = QLabel()
        lbl.setMinimumWidth(56)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight
                         | Qt.AlignmentFlag.AlignVCenter)

        def show(v):
            # Encaixa no passo (setas/rato podem dar valores intermédios).
            snapped = int(round(v / step) * step)
            if snapped != v:
                sl.setValue(snapped)
                return
            lbl.setText(f"{v:+d}{unit}" if v else f"0{unit}")
        sl.valueChanged.connect(show)
        reset = QPushButton("↺")
        reset.setObjectName("small")
        reset.setFixedWidth(32)
        reset.setToolTip(T("Default"))
        reset.clicked.connect(lambda: sl.setValue(0))
        sl.setValue(value)
        show(value)
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.addWidget(sl, 1)
        h.addWidget(lbl)
        h.addWidget(reset)
        return sl, w

    def _on_mention_text(self, text):
        # Com texto, a voz di-lo em vez do som: o som fica desligado.
        has = bool(text.strip())
        self.mention_tone_cb.setEnabled(not has)
        self.mention_rep_sp.setEnabled(not has)

    def _preview_mention(self):
        if self.tts is None:
            self.tts = TTSManager()
        self.tts.configure(self.tts.enabled, self.voice_cb.currentData()
                           or self.tts.voice, self.out_cb.currentData(),
                           rate=self.tts_rate_sl.value(),
                           pitch=self.tts_pitch_sl.value())
        text = self.mention_text_le.text().strip()
        if text:
            self.tts.speak_now(text.replace("{name}", "Player"))
        else:
            self.tts.cue("mention:" + (self.mention_tone_cb.currentData()
                                       or "ding"), self.mention_rep_sp.value())

    def _preview_voice(self):
        if self.tts is None:
            self.tts = TTSManager()
        voice = self.voice_cb.currentData() or "en-US-AriaNeural"
        prefix = voice.split("-")[0].lower()
        text = core.VOICE_SAMPLES.get(prefix, core.VOICE_SAMPLES["en"])
        if prefix not in ("ru", "uk", "bg", "sr", "kk"):
            text = core.transliterate_cyrillic(text)
        self.tts.configure(self.tts.enabled, self.tts.voice,
                           self.out_cb.currentData())
        self.tts.preview(text, voice, self.tts_rate_sl.value(),
                         self.tts_pitch_sl.value())

    def _fill_lang_cb(self, cb, with_auto):
        cb.clear()
        for key in LANGUAGES:
            if key.startswith("Auto") and not with_auto:
                continue
            cb.addItem(lang_label(key), key)

    @staticmethod
    def _select_data(cb, value):
        i = cb.findData(value)
        if i >= 0:
            cb.setCurrentIndex(i)
        return i >= 0

    def _build_ui(self):
        old = self.centralWidget()
        try:
            if self.guide_dlg is not None:
                self.guide_dlg.close()
        except RuntimeError:
            pass
        self.guide_dlg = None
        self.setStyleSheet(theme_qss())
        self.setWindowTitle(tr("window_title"))
        outer = QWidget()
        ov = QVBoxLayout(outer)
        ov.setContentsMargins(16, 12, 16, 12)
        ov.setSpacing(8)

        title = QLabel("🎮  " + tr("app_title"))
        tf = QFont("Arial", 15); tf.setBold(True)
        title.setFont(tf); set_role(title, "title")
        ov.addWidget(title)

        scroll = QScrollArea()
        scroll.setObjectName("page")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget()
        cols = QHBoxLayout(page)
        cols.setContentsMargins(0, 0, 6, 0)
        cols.setSpacing(14)
        # Esquerda: a IA (cada painel tem os seus perfis de modelo).
        # Direita: a caixa do perfil 💾 com tudo o que ele grava dentro.
        c2, right = QVBoxLayout(), QVBoxLayout()
        c2.setSpacing(8)
        cols.addLayout(c2, 13); cols.addLayout(right, 22)
        prof = QGroupBox("💾 " + tr("grp_profiles"))
        pv = QVBoxLayout(prof)
        pv.setContentsMargins(8, 6, 8, 8)
        pv.setSpacing(8)
        self._build_profiles(pv)
        inner = QHBoxLayout()
        inner.setSpacing(10)
        c1, c3 = QVBoxLayout(), QVBoxLayout()
        for c in (c1, c3):
            c.setSpacing(8)
        inner.addLayout(c1, 1); inner.addLayout(c3, 1)
        pv.addLayout(inner)
        right.addWidget(prof)
        scroll.setWidget(page)
        ov.addWidget(scroll, 1)

        old_dlg = self.settings_dlg
        self.settings_dlg = SettingsDialog(self)
        self._build_general(c1)
        self._build_ai(c2)
        self._build_game(c1, c3)
        for c in (c1, c2, c3, right):
            c.addStretch(1)

        # Rodapé (sempre à vista)
        status_row = QHBoxLayout()
        for ok, txt_ok, txt_no in (
                (_TESS_OK, tr("status_tess_ok"), tr("status_tess_miss")),
                (SR_OK, tr("status_audio_ok"), tr("status_audio_no")),
                (PYNPUT_OK, tr("status_kb_ok"), tr("status_kb_no"))):
            lbl = QLabel(txt_ok if ok else txt_no)
            set_role(lbl, "ok" if ok else "err")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_row.addWidget(lbl)
        ov.addLayout(status_row)
        info = QLabel(tr("info_help"))
        set_role(info, "muted")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ov.addWidget(info)
        bottom = QHBoxLayout()
        self.btn_manual = QPushButton(T("📖 Manual"))
        self.btn_manual.clicked.connect(
            lambda: ManualDialog.show_manual(self))
        bottom.addWidget(self.btn_manual, 0)
        self.btn_guide = QPushButton(T("🔊 Quick start"))
        self.btn_guide.setToolTip(T(
            "A short spoken guide: what to fill in to start the overlay "
            "and hear the translations"))
        self.btn_guide.clicked.connect(self.open_guide)
        bottom.addWidget(self.btn_guide, 0)
        self.btn_log = QPushButton(tr("btn_log"))
        self.btn_log.clicked.connect(self._open_log)
        bottom.addWidget(self.btn_log, 0)
        self.btn_settings = QPushButton(T("⚙ App settings"))
        self.btn_settings.setToolTip(T(
            "Interface language, theme, overlay appearance, what ✕ does, "
            "language packs and audio devices"))
        self.btn_settings.clicked.connect(self._open_settings)
        bottom.addWidget(self.btn_settings, 0)
        if not ConfigWindow._update_checked:
            # 1x por arranque, em fundo: se houver versão nova o botão ⚙
            # ganha um 🆕 (atualiza-se nas Definições).
            ConfigWindow._update_checked = True
            QTimer.singleShot(4000, lambda: self.settings_dlg.check_updates(
                silent=True))
        self.start_btn = QPushButton(tr("btn_start"))
        self.start_btn.setObjectName("start")
        self.start_btn.clicked.connect(self._start)
        bottom.addWidget(self.start_btn, 1)
        ov.addLayout(bottom)

        self.setCentralWidget(outer)
        if old is not None:
            old.deleteLater()
        if old_dlg is not None:
            old_dlg.hide()
            old_dlg.deleteLater()

        self._refresh_audio_devices()
        self._refresh_profiles()
        self._update_app_status()
        self._refresh_model_profiles()
        for pn in self.panels:
            pn._on_prov_changed()
        self._on_ocr_tgt_changed()
        self._refresh_ocr_status()

    # ---------- coluna 1: geral ----------
    def _build_general(self, col):
        # Língua, tema, aparência, ✕, pacotes e áudio: nas Definições.
        g, f = self._group("🧑 " + tr("grp_myname"))
        self.my_name_le = QLineEdit()
        self.my_name_le.setPlaceholderText(T("e.g. PlayerOne"))
        f.addRow(tr("lbl_my_name"), self.my_name_le)
        f.addRow(self._hint(tr("lbl_my_name_hint")))
        self.mention_cb = QCheckBox(T("🔔 Sound when someone writes my name"))
        self.mention_cb.setToolTip(T(
            "When a message in the chat contains your character name (they "
            "are talking to you or about you), a short 'ding' plays — also "
            "with the reading voice off. Your own messages don't count."))
        f.addRow(self.mention_cb)
        self.mention_tone_cb = QComboBox()
        for key, label in (("ding", T("Ding")), ("bell", T("Bell")),
                           ("ping", T("Ping")),
                           ("triple", T("Triple beep")),
                           ("rising", T("Rising")), ("soft", T("Soft")),
                           ("radar", T("Radar")), ("alarm", T("Alarm"))):
            self.mention_tone_cb.addItem("🎵 " + label, key)
        self.mention_rep_sp = QSpinBox()
        self.mention_rep_sp.setRange(1, 10)
        self.mention_rep_sp.setValue(1)
        self.mention_rep_sp.setSuffix("×")
        self.mention_rep_sp.setToolTip(T("How many times the sound plays"))
        f.addRow(T("Sound:"), self._hbox(
            self.mention_tone_cb, self.mention_rep_sp,
            self._small_btn("▶", self._preview_mention, 36,
                            T("Hear the sound (and the text)"))))
        self.mention_text_le = QLineEdit()
        self.mention_text_le.setPlaceholderText(
            T("e.g. {name} is talking to you"))
        self.mention_text_le.setToolTip(T(
            "Optional: instead of the sound, the voice says this text for "
            "you to hear (it is never written in the chat). {name} = who "
            "wrote your name. Empty = the sound above."))
        self.mention_text_le.textChanged.connect(self._on_mention_text)
        f.addRow(T("Or say:"), self.mention_text_le)
        self.mention_every_sp = QSpinBox()
        self.mention_every_sp.setRange(1, 300)
        self.mention_every_sp.setSuffix(" s")
        self.mention_during_sp = QSpinBox()
        self.mention_during_sp.setRange(0, 600)
        self.mention_during_sp.setSuffix(" s")
        self.mention_every_sp.setValue(10)
        self.mention_during_sp.setValue(30)
        tip = T("The sound plays again every X seconds for Y seconds "
                "(e.g. every 10 s for 30 s = at 0, 10 and 20 s; 0 = only "
                "once). The cancel key (Esc) or starting a dictation stops "
                "it. The text is said only once.")
        for w in (self.mention_every_sp, self.mention_during_sp):
            w.setToolTip(tip)
        lbl_for = QLabel(T("for"))
        f.addRow(T("Repeat every:"), self._hbox(
            self.mention_every_sp, lbl_for, self.mention_during_sp,
            stretch_first=False))
        col.addWidget(g)


    def _build_profiles(self, box):
        """Barra do perfil 💾: grava o que está nesta caixa, a aparência
        do overlay e os dispositivos de áudio — nunca a IA."""
        row = QHBoxLayout()
        self.profile_cb = QComboBox()
        row.addWidget(self.profile_cb, 1)
        for txt, fn in ((tr("btn_apply_profile"), self._apply_profile),
                        (tr("btn_save_profile"), self._save_profile),
                        (tr("btn_delete_profile"), self._delete_profile)):
            b = QPushButton(txt); b.setObjectName("small")
            b.clicked.connect(fn); row.addWidget(b)
        box.addLayout(row)
        box.addWidget(self._hint(T(
            "A profile saves everything in this box, plus the overlay "
            "appearance and the audio devices (⚙ App settings). The AI is "
            "not included: each AI panel has its own profiles.")))

    # ---------- coluna 2: IA ----------
    def _build_ai(self, col):
        # Dois painéis iguais: a IA do chat (o que lês) e a da voz (o que
        # dizes), cada um com a IA, chave, modelo, perfil e opções.
        self.chat_panel = AIPanel(self, "chat")
        self.voice_panel = AIPanel(self, "voice")
        self.panels = (self.chat_panel, self.voice_panel)
        col.addWidget(self.chat_panel)
        col.addWidget(self.voice_panel)
        self.btn_clouds = QPushButton("☁ AI Clouds — " + T(
            "which AI to use, free limits, where to get keys"))
        self.btn_clouds.setObjectName("small")
        self.btn_clouds.clicked.connect(
            lambda: ManualDialog.show_manual(self, tab=1))
        self.btn_ratings = QPushButton("📊 " + T(
            "AI ratings and speed test on this PC"))
        self.btn_ratings.setObjectName("small")
        self.btn_ratings.clicked.connect(
            lambda: ManualDialog.show_manual(self, tab=2))
        col.addWidget(self.btn_clouds)
        col.addWidget(self.btn_ratings)
        # O teste de desempenho usa as opções que estão nesta janela agora.
        BenchmarkTab.config_source = staticmethod(
            lambda: self._gather_config(show_errors=False, validate=False))

        # Desempenho do Ollama (só local)
        self.g_gpu, f = self._group("⚙ " + tr("grp_gpu"))
        self.gpu_layers_cb = QComboBox()
        self.gpu_layers_cb.addItem(T("Automatic"), -1)
        self.gpu_layers_cb.addItem(T("CPU only (0) — best while gaming"), 0)
        for n in (2, 4, 6, 8, 12, 16, 20, 24, 32, 48):
            self.gpu_layers_cb.addItem(T("{n} layers", n=n), n)
        self.gpu_layers_cb.addItem(T("Max (999)"), 999)
        f.addRow(tr("lbl_gpu_layers"), self.gpu_layers_cb)
        self.num_par_cb = QComboBox()
        for n in (1, 2, 4, 8):
            self.num_par_cb.addItem(str(n), n)
        f.addRow(tr("lbl_num_parallel"), self.num_par_cb)
        self.keep_alive_cb = QComboBox()
        # Predefinição: nunca descarregar por tempo — o modelo sai da VRAM
        # quando a app fecha ou rebenta (vigia em _start_unload_watchdog).
        for k, l in (("-1", T("∞ Never (unloaded when the app closes)")),
                     ("0", T("0 (unload right away)")),
                     ("5m", T("5 min")), ("15m", T("15 min")),
                     ("1h", T("1 hour"))):
            self.keep_alive_cb.addItem(l, k)
        f.addRow(tr("lbl_keep_alive"), self.keep_alive_cb)
        col.addWidget(self.g_gpu)

    # ---------- coluna 3: jogo e voz ----------
    def _build_game(self, col, col_voice):
        g, f = self._group("📖 " + tr("grp_ocr"))
        self.ocr_src_cb = QComboBox()
        self._fill_lang_cb(self.ocr_src_cb, True)
        self.ocr_src_cb.currentIndexChanged.connect(self._refresh_ocr_status)
        f.addRow(tr("lbl_ocr_src"), self.ocr_src_cb)
        self.ocr_tgt_cb = QComboBox()
        self._fill_lang_cb(self.ocr_tgt_cb, False)
        self._select_data(self.ocr_tgt_cb, "English")
        self.ocr_tgt_cb.currentIndexChanged.connect(self._on_ocr_tgt_changed)
        f.addRow(tr("lbl_ocr_tgt"), self.ocr_tgt_cb)
        self.ocr_rate_cb = QComboBox()
        for n in (10, 20, 30, 40, 60):
            self.ocr_rate_cb.addItem(T("{n} (default)", n=n) if n == 20
                                     else str(n), n)
        self._select_data(self.ocr_rate_cb, 20)
        self.ocr_rate_cb.setToolTip(T(
            "How many times per minute the app captures the game window "
            "and reads the chat (OCR, in memory). Fewer = less CPU; more = "
            "new messages appear sooner. Without new messages nothing is "
            "sent to the AI."))
        f.addRow(T("Chat reads per minute:"), self.ocr_rate_cb)
        # Zona do chat: automática (qualquer resolução) ou marcada à mão.
        self._chat_region = []
        self.calib_on_cb = QCheckBox(T("Use the calibrated zone"))
        self.calib_on_cb.setChecked(True)
        self.calib_on_cb.setToolTip(T(
            "Off: the app finds the chat by itself (automatic, works at any "
            "resolution). The calibration stays saved for later."))
        self.calib_on_cb.toggled.connect(lambda _: self._refresh_calib())
        f.addRow(T("Chat zone:"), self._hbox(
            self._small_btn("🎯 " + T("Calibrate"), self._calibrate_chat,
                            tip=T("Open the chat in the game first. A box "
                                  "appears over the game: drag and resize "
                                  "it over the chat messages and confirm. "
                                  "Only needed if the app doesn't read your "
                                  "chat well (different chat size or UI "
                                  "scale).")),
            self.calib_on_cb, stretch_first=False))
        self.calib_lbl = self._hint("")
        f.addRow(self.calib_lbl)
        self._calib_sig = _TextSignal()
        self._calib_sig.text.connect(self._calib_checked)
        self._refresh_calib()
        self.ocr_status_lbl = self._hint("")
        f.addRow(self.ocr_status_lbl)
        col.addWidget(g)
        col = col_voice

        g, f = self._group("🎤 " + tr("grp_voice"))
        self.voice_src_cb = QComboBox()
        self._fill_lang_cb(self.voice_src_cb, False)
        self._select_data(self.voice_src_cb, "Portuguese (PT)")
        f.addRow(tr("lbl_voice_src"), self.voice_src_cb)
        self.voice_tgt_cb = QComboBox()
        self._fill_lang_cb(self.voice_tgt_cb, False)
        self._select_data(self.voice_tgt_cb, "Russian")
        f.addRow(tr("lbl_voice_tgt"), self.voice_tgt_cb)
        self.voice_hotkey_le = QLineEdit()
        self.voice_hotkey_le.setReadOnly(True)
        self.voice_hotkey_le.setText(DEFAULT_VOICE_HOTKEY)
        f.addRow(tr("lbl_voice_hotkey"), self._hbox(
            self.voice_hotkey_le,
            self._small_btn(tr("btn_record_key"), self._record_hotkey)))
        self.cancel_hotkey_le = QLineEdit()
        self.cancel_hotkey_le.setReadOnly(True)
        self.cancel_hotkey_le.setText("esc")
        self.cancel_hotkey_le.setToolTip(T(
            "Stops a dictation at once: stops listening, translating and "
            "typing, and erases what was already typed (Enter is never "
            "pressed). It only works while a dictation is running; "
            "otherwise the key goes to the game as usual."))
        f.addRow(T("Cancel key:"), self._hbox(
            self.cancel_hotkey_le,
            self._small_btn(tr("btn_record_key"), self._record_cancel_key)))
        self.voice_mode_cb = QComboBox()
        for k in ("hold", "auto", "continuous"):
            self.voice_mode_cb.addItem(tr(f"vm_{k}"), k)
        self.voice_mode_cb.setToolTip(T(
            "Push-to-talk: records while you hold the hotkey and stops "
            "when you let go (best with TV/game noise).\nTap: one press "
            "listens until you make a long pause.\nContinuous: one press "
            "turns it on, another press turns it off; each sentence is "
            "sent when you pause (with headphones the chat voice keeps "
            "reading between your sentences).\nIn every mode a rising beep means it is listening and a "
            "short beep means it stopped; the overlay shows ● Listening."))
        f.addRow(tr("lbl_voice_mode"), self.voice_mode_cb)
        self.voice_confirm_cb = QCheckBox(
            T("✋ Confirm before sending (voice)"))
        self.voice_confirm_cb.setToolTip(T(
            "Off: the app types the message in the game chat and sends it "
            "(Enter) by itself.\nOn: it types it and waits — press ✔ Send "
            "in the overlay bar (or the voice hotkey again) to send it; "
            "Esc or ✖ erases it. Also in the overlay ⚙ menu."))
        f.addRow(self.voice_confirm_cb)
        self.cont_tts_cb = QCheckBox(
            T("🎧 Keep reading the chat in continuous mode"))
        self.cont_tts_cb.setChecked(True)
        self.cont_tts_cb.setToolTip(T(
            "On (with headphones): in continuous mode the chat voice keeps "
            "reading between your sentences and goes quiet while you "
            "speak; the sentence it was reading is read again afterwards.\n"
            "Off (with speakers): the chat voice stays quiet while "
            "continuous mode is on, so the mic never hears it."))
        f.addRow(self.cont_tts_cb)
        col.addWidget(g)

        g, f = self._group("🔊 " + tr("grp_tts"))
        self.tts_cb = QCheckBox(tr("chk_tts"))
        self.tts_cb.setChecked(True)
        f.addRow(self.tts_cb)
        self.voice_cb = QComboBox()
        self.btn_tts_preview = self._small_btn(
            T("▶ Listen"), self._preview_voice,
            tip=T("Plays an example with this voice, speed and pitch"))
        f.addRow(tr("lbl_tts_voice"), self._hbox(self.voice_cb,
                                                 self.btn_tts_preview))
        self.tts_rate_sl, rate_row = self._slider(-50, 100, 5, 0, "%")
        self.tts_rate_sl.setToolTip(T(
            "How fast the voice reads. When many messages are waiting it "
            "reads another 20% faster to catch up."))
        f.addRow(T("Speed:"), rate_row)
        self.tts_pitch_sl, pitch_row = self._slider(-40, 40, 2, 0, " Hz")
        self.tts_pitch_sl.setToolTip(T("Lower or higher voice."))
        f.addRow(T("Pitch:"), pitch_row)
        col.addWidget(g)

    # ------------------------------------------------------------ geral
    def _record_cancel_key(self):
        cur = self.cancel_hotkey_le.text() or "esc"
        dlg = HotkeyCaptureDialog(self, initial=cur, allow_esc=True)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.captured:
            if dlg.captured == (self.voice_hotkey_le.text() or "").lower():
                self._warn(T("The cancel key must be different from the "
                             "voice hotkey."))
                return
            self.cancel_hotkey_le.setText(dlg.captured)
            log().info(f"Tecla de cancelar: {dlg.captured}")

    def _record_hotkey(self):
        cur = self.voice_hotkey_le.text() or DEFAULT_VOICE_HOTKEY
        dlg = HotkeyCaptureDialog(self, initial=cur)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.captured:
            self.voice_hotkey_le.setText(dlg.captured)
            log().info(f"Hotkey voz alterado para: {dlg.captured}")

    def _update_app_status(self):
        st = load_overlay_state().get("style", {})
        a = st.get("bg_alpha")
        self.app_status.setText(T(
            "Font {f}pt · background opacity {a} · name colors: {c}",
            f=st.get("font_size", "?"),
            a=f"{round(int(a) * 100 / 255)}%" if a is not None else "?",
            c=st.get("speaker_color_mode", "?"))
            + (" · " + T("auto-hide {n} s", n=st.get("auto_hide_secs", 20))
               if st.get("auto_hide") else ""))

    _on_style_changed_cb = None
    def set_on_style_changed(self, cb): self._on_style_changed_cb = cb

    def _open_appearance(self):
        cur = load_overlay_state().get("style", {})
        dlg = AppearanceDialog(self, cur)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_style = dlg.get_style()
            state = load_overlay_state()
            state["style"] = new_style
            save_overlay_state(state)
            self._update_app_status()
            if self._on_style_changed_cb:
                self._on_style_changed_cb(new_style)

    def _on_theme_changed(self, idx):
        key = self.theme_cb.itemData(idx)
        if not key: return
        core.set_ui_theme(key)
        apply_theme()
        self.setStyleSheet(theme_qss())
        if self.settings_dlg is not None:
            self.settings_dlg.setStyleSheet(theme_qss())

    def _on_ui_lang_changed(self, idx):
        code = self.ui_lang_cb.itemData(idx)
        if not code or code == get_ui_lang(): return
        # Guarda o que está escrito, reconstrói tudo na língua nova e repõe.
        snap = self._gather_config(show_errors=False, validate=False)
        reopen = self.settings_dlg is not None \
            and self.settings_dlg.isVisible()
        set_ui_lang(code)
        self._build_ui()
        if snap:
            self._apply_config(snap)
        if reopen:      # a mudança veio das Definições: reabre-as
            QTimer.singleShot(0, self._open_settings)

    guide_dlg = None

    def open_guide(self):
        dlg = self.guide_dlg
        try:
            if dlg is not None and dlg.isVisible():
                dlg.raise_(); dlg.activateWindow()
                return
        except RuntimeError:            # já foi apagado (WA_DeleteOnClose)
            pass
        self.guide_dlg = dlg = QuickGuideDialog(self)
        dlg.show()
        dlg.place()

    def _open_settings(self):
        dlg = self.settings_dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    _quitting = False
    _update_checked = False     # verificação de atualizações já feita
    on_restart = None           # a app: fecha e abre outra vez (update)

    def closeEvent(self, event):
        # ✕ da janela principal: a app decide (fechar ou ficar na bandeja).
        if self.settings_dlg is not None:
            self.settings_dlg.hide()
        super().closeEvent(event)
        if self.on_close and not self._quitting:
            QTimer.singleShot(0, self.on_close)

    def _open_log(self): LogViewerDialog(self).exec()

    def _open_lang_manager(self):
        LanguageManagerDialog(self).exec()
        self._refresh_ocr_status()

    def _refresh_profiles(self):
        self.profile_cb.clear()
        self.profile_cb.addItem("—", "")
        for name in ProfileManager.list_profiles():
            self.profile_cb.addItem(name, name)

    def _apply_profile(self):
        name = self.profile_cb.currentData()
        if not name: return
        # A IA (fornecedor, modelo, chaves, opções) fica como está.
        cur = self._gather_config(show_errors=False, validate=False)
        cfg = ProfileManager.load_profile(name, cur) if cur else None
        if not cfg:
            QMessageBox.critical(self, tr("err"),
                                 T("Could not load '{n}'.", n=name)); return
        self._apply_config(cfg)
        if cfg.appearance_style:
            state = load_overlay_state()
            state["style"] = merge_overlay_style(cfg.appearance_style)
            save_overlay_state(state)
            self._update_app_status()
            if self._on_style_changed_cb:
                self._on_style_changed_cb(state["style"])
        QMessageBox.information(self, tr("info"),
                                tr("profile_applied", n=name))

    def _save_profile(self):
        name, ok = QInputDialog.getText(self, tr("profile_save"),
                                        tr("profile_name"))
        if not ok or not name.strip(): return
        # Sem validar a IA: o perfil não a grava.
        cfg = self._gather_config(show_errors=False, validate=False)
        if not cfg:
            return
        ok, msg = ProfileManager.save_profile(name, cfg)
        if ok:
            self._refresh_profiles()
            QMessageBox.information(self, tr("info"),
                                    tr("profile_saved", n=msg))
        else:
            QMessageBox.critical(self, tr("err"), msg)

    def _delete_profile(self):
        name = self.profile_cb.currentData()
        if not name: return
        if QMessageBox.question(self, tr("warn"),
                                tr("profile_confirm_delete", n=name)) \
                != QMessageBox.StandardButton.Yes: return
        if ProfileManager.delete_profile(name):
            self._refresh_profiles()
            QMessageBox.information(self, tr("info"), tr("profile_deleted"))

    # ------------------------------------------------------------ IA
    # ---------- perfis de modelos ----------
    def _refresh_model_profiles(self, select=None):
        """select = (painel, nome) a escolher depois de guardar."""
        profs = core.load_model_profiles()
        for pn in self.panels:
            pn.fill_profiles(profs, select[1] if select
                             and select[0] is pn else None)

    def _key_for(self, prov):
        return self._api_keys.get(prov, "")

    def _url_for(self, prov):
        return self._custom_urls.get(prov, "")

    def _resolve_provider(self, prov):
        """Perfil do OpenRouter, mas a tua chave está num servidor próprio
        com o URL do OpenRouter: usa esse."""
        prov = normalize_provider(prov)
        if prov.startswith("OpenRouter") and not self._key_for(prov):
            for p in CLOUD_PROVIDERS:
                if core.is_custom_provider(p) and \
                        "openrouter.ai" in self._url_for(p).lower():
                    return p
        return prov

    def refresh_local_models(self):
        """Modelos do Ollama mudaram (🤗, arranque): atualiza os painéis
        que estão em 'Local'."""
        for pn in self.panels:
            if pn.is_local():
                pn._refresh_local()

    def _sync_fields(self, src, prov):
        """Chave/URL/nome mudados num painel: o outro, se mostra a mesma
        IA, atualiza-se."""
        for pn in self.panels:
            if pn is not src and pn._prov == prov:
                pn._load_fields()

    def _relabel(self, prov):
        for pn in self.panels:
            pn.relabel(prov)

    def _update_gpu_visibility(self):
        if hasattr(self, "g_gpu"):
            self.g_gpu.setVisible(any(pn.is_local() for pn in self.panels))

    def _open_hf(self):
        def changed():
            for pn in self.panels:
                if pn.is_local():
                    pn._refresh_local()
        HuggingFaceDialog(self, on_models_changed=changed).exec()

    def _cloud_models_for(self, prov, current=""):
        if self._model_lists.get(prov):
            out = list(self._model_lists[prov])
            if current and not any(core.model_id(m) == current
                                   for m in out):
                out.insert(0, current)
            return out
        conf = CLOUD_PROVIDERS.get(prov) or {}
        out = []
        for m in ([current, self._cloud_models.get(prov, "")]
                  + list(conf.get("models") or [])):
            if m and m not in out:
                out.append(m)
        return out

    def _start_cloud_check(self, panel, prov, ping=True):
        key, url = self._key_for(prov), self._url_for(prov)
        model = panel.model() or self._cloud_models.get(prov, "")
        panel.status.setText(f"⏳ {core.provider_label(prov)}…")
        set_role(panel.status, "muted")
        self._check_prov[panel.which] = prov
        sig = self._cloud_sig

        def worker():
            ok, msg, models = _cloud_check(prov, key, url, model, ping)
            try:
                sig.done.emit(panel.which, ok, msg, models)
            except RuntimeError:
                pass            # a janela fechou entretanto
        threading.Thread(target=worker, daemon=True).start()

    def _on_cloud_done(self, purpose, ok, msg, models):
        prov = self._check_prov.get(purpose)
        if ok and models and prov:
            self._model_lists[prov] = list(models)
        try:
            for pn in self.panels:
                if pn.which == purpose and pn._prov == prov:
                    pn.on_check_done(ok, msg, models)
                elif ok and models and pn._prov == prov:
                    pn.set_models(models, keep=pn.model())
        except RuntimeError:
            return              # janela reconstruída entretanto

    # ------------------------------------------------------------ jogo
    def _on_ocr_tgt_changed(self, *_):
        self._refresh_tts_voices(self.ocr_tgt_cb.currentData() or "English")

    # ------------------------------------------------- zona do chat
    def _refresh_calib(self):
        """Aplica já (também com a tradução a correr) e mostra o estado."""
        has = bool(self._chat_region)
        self.calib_on_cb.setEnabled(has)
        on = has and self.calib_on_cb.isChecked()
        core.set_chat_calibration(self._chat_region if on else None)
        self.calib_lbl.setText(
            "🎯 " + T("Calibrated zone in use.") if on else
            T("Automatic (works at any resolution).")
            + (" " + T("Calibration saved.") if has else ""))

    def _calibrate_chat(self):
        game = GameWindow()
        rect = game.client_rect()
        if not rect:
            self._warn(T("Open the game (not minimized) and its chat "
                         "first."))
            return
        start = self._chat_region or list(core.CHAT_REGION_REL)
        self.showMinimized()
        game.activate()
        self._calibrator = ChatCalibrator(rect, start, self._calib_done)
        self._calibrator.show()
        self._calibrator.raise_()
        self._calibrator.activateWindow()

    def _calib_done(self, result):
        self._calibrator = None
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if result is None:
            return
        if result == "auto":
            self.calib_on_cb.setChecked(False)
        else:
            self._chat_region = list(result)
            self.calib_on_cb.setChecked(True)
            log().info(f"Zona do chat calibrada: {self._chat_region}")
        self._refresh_calib()
        try:
            cfg = self._gather_config(show_errors=False, validate=False)
            if cfg:
                save_last_config(cfg)
        except Exception:
            log().exception("calibração: falha a guardar")
        if result == "auto":
            return
        self.calib_lbl.setText("⏳ " + T("Reading the chat in this zone…"))
        src = self.ocr_src_cb.currentData() or "Auto (detectar)"

        def run():
            try:
                lines = core.read_chat_once(src=src)
            except Exception as e:
                log().exception("calibração: leitura de teste")
                lines = None
                msg = f"⚠️ {e}"
            else:
                msg = ""
            if not msg:
                msg = ("✅ " + T("Calibrated: {n} chat messages read in this "
                                 "zone.", n=len(lines))) if lines else (
                    "⚠️ " + T("No chat messages found in this zone. Is the "
                              "chat open? Calibrate again or use "
                              "Automatic."))
            self._calib_sig.text.emit(msg)
        threading.Thread(target=run, daemon=True, name="CalibCheck").start()

    def _calib_checked(self, msg):
        self.calib_lbl.setText(msg)

    def _refresh_ocr_status(self, *_):
        key = self.ocr_src_cb.currentData() or ""
        if key.startswith("Auto"):
            self.ocr_status_lbl.setText(
                f"ℹ️ auto ({resolve_tess_lang(key) or 'eng'})")
            set_role(self.ocr_status_lbl, "info"); return
        code = LANGUAGES.get(key, {}).get("tess")
        if not code:
            self.ocr_status_lbl.setText(""); return
        if is_tessdata_installed(code):
            self.ocr_status_lbl.setText(f"✅ {code}")
            set_role(self.ocr_status_lbl, "ok")
        else:
            self.ocr_status_lbl.setText(T("⚠️ {c} missing", c=code))
            set_role(self.ocr_status_lbl, "err")

    def _test_mic(self):
        if self._mic_tester is not None:
            return
        lang = LANGUAGES.get(self.voice_src_cb.currentData(), {}).get("stt")
        self._mic_tester = MicTester(
            self.mic_cb.currentData(), lang,
            device_name=self._mic_names.get(self.mic_cb.currentData(), ""))
        self._mic_tester.level.connect(self.mic_level.setValue)
        self._mic_tester.done.connect(self._mic_test_done)
        self.btn_mic_test.setEnabled(False)
        self.mic_level.setValue(0); self.mic_level.show()
        self.mic_test_lbl.setText(T("🎤 Speak now (5 s)…"))
        self.mic_test_lbl.show()
        self._mic_tester.start()

    def _mic_test_done(self, text):
        try:
            self.mic_test_lbl.setText(text)
            self.mic_level.hide()
            self.btn_mic_test.setEnabled(True)
        except RuntimeError:
            pass
        self._mic_tester = None

    def _refresh_audio_devices(self):
        prev_mic = self.mic_cb.currentData(); self.mic_cb.clear()
        self._mic_names = {}
        self.mic_cb.addItem(tr("sys_default"), None)
        if not PYAUDIO_OK:
            self.mic_cb.addItem("(N/A)", None); self.mic_cb.setEnabled(False)
        else:
            try:
                for idx, name in list_input_devices():
                    self._mic_names[idx] = name
                    label = name if len(name) <= 55 else name[:52] + "..."
                    self.mic_cb.addItem(f"[{idx}] {label}", idx)
            except Exception as e:
                self.mic_cb.addItem(f"(Err: {e})", None)
        if prev_mic is not None:
            self._select_data(self.mic_cb, prev_mic)
        prev_out = self.out_cb.currentData(); self.out_cb.clear()
        self.out_cb.addItem(tr("sys_default"), None)
        try:
            for name in list_output_devices():
                label = name if len(name) <= 55 else name[:52] + "..."
                self.out_cb.addItem(label, name)
        except Exception as e:
            self.out_cb.addItem(f"(Err: {e})", None)
        if prev_out is not None:
            self._select_data(self.out_cb, prev_out)

    def _refresh_tts_voices(self, target_lang):
        prefix = LANGUAGES.get(target_lang, {}).get("tts", "en")
        voices = TTS_VOICES_BY_LANG.get(prefix, TTS_VOICES_BY_LANG["en"])
        current = self.voice_cb.currentData()
        self.voice_cb.clear()
        for label, code in voices:
            self.voice_cb.addItem(label, code)
        if current:
            self._select_data(self.voice_cb, current)

    # ------------------------------------------------------------ config
    def _apply_config(self, cfg):
        self._api_keys = dict(getattr(cfg, "api_keys", None) or {})
        self._cloud_models = dict(getattr(cfg, "cloud_models", None) or {})
        prov = normalize_provider(cfg.cloud_provider)
        if cfg.api_key and prov and not self._api_keys.get(prov):
            self._api_keys[prov] = cfg.api_key
        if cfg.mode == "cloud" and cfg.model and prov:
            self._cloud_models.setdefault(prov, cfg.model)
        self._custom_urls = {k: v for k, v in (
            getattr(cfg, "custom_urls", None) or {}).items() if v}
        slot1 = "Personalizado (OpenAI-compatível)"
        if getattr(cfg, "custom_base_url", "") \
                and not self._custom_urls.get(slot1):
            self._custom_urls[slot1] = cfg.custom_base_url
        self._custom_names = {k: v for k, v in (
            getattr(cfg, "custom_names", None) or {}).items() if v}
        core.set_custom_names(self._custom_names)
        for name in CLOUD_PROVIDERS:
            self._relabel(name)
        from dataclasses import replace as _dc_replace
        chat_opts = {k: core.ai_opt(cfg, k) for k in core.AI_OPT_DEFAULTS}
        vtmp = _dc_replace(cfg, ai_opts=dict(
            getattr(cfg, "voice_opts", None) or {}))
        voice_opts = {k: core.ai_opt(vtmp, k) for k in core.AI_OPT_DEFAULTS}
        self.chat_panel._last_cloud = prov
        self.chat_panel.set_state(
            "local" if cfg.mode == "local" else
            (getattr(cfg, "mt_engine", "") or "google") if cfg.mode == "mt"
            else prov, cfg.model, chat_opts)
        if cfg.mode in ("local", "mt"):
            self.chat_panel._last_cloud = prov
        self.chat_panel.fallback_cb.setChecked(
            getattr(cfg, "cloud_fallback", True))
        self.voice_panel.set_state(
            normalize_provider(getattr(cfg, "voice_provider", "")),
            getattr(cfg, "voice_model", ""), voice_opts)
        self._select_data(self.ocr_rate_cb,
                          int(getattr(cfg, "ocr_per_min", 20) or 20))
        self._chat_region = list(getattr(cfg, "chat_region", None) or [])
        self.calib_on_cb.setChecked(bool(getattr(cfg, "chat_region_on",
                                                 True)))
        self._refresh_calib()
        self._select_data(self.gpu_layers_cb, cfg.gpu_layers)
        self._select_data(self.num_par_cb, cfg.num_parallel)
        self._select_data(self.keep_alive_cb, cfg.keep_alive)
        # Pelo nome primeiro: o índice muda ao religar o micro USB.
        mic_idx = mic_index_by_name(getattr(cfg, "mic_device_name", "")) \
            if getattr(cfg, "mic_device_name", "") else None
        if mic_idx is None:
            mic_idx = cfg.mic_device_index
        if mic_idx is not None:
            self._select_data(self.mic_cb, mic_idx)
        if cfg.tts_output_device:
            self._select_data(self.out_cb, cfg.tts_output_device)
        self._select_data(self.ocr_src_cb, cfg.ocr_source)
        self._select_data(self.ocr_tgt_cb, cfg.ocr_target)
        self._select_data(self.voice_src_cb, cfg.voice_source)
        self._select_data(self.voice_tgt_cb, cfg.voice_target)
        self.voice_hotkey_le.setText(cfg.voice_hotkey or DEFAULT_VOICE_HOTKEY)
        self.cancel_hotkey_le.setText(getattr(cfg, "cancel_hotkey", "esc")
                                      or "esc")
        self._select_data(self.voice_mode_cb,
                          getattr(cfg, "voice_mode", "hold"))
        self.voice_confirm_cb.setChecked(
            bool(getattr(cfg, "voice_confirm", False)))
        self.cont_tts_cb.setChecked(
            bool(getattr(cfg, "continuous_tts", True)))
        self.my_name_le.setText(cfg.my_name or "")
        self.mention_cb.setChecked(bool(getattr(cfg, "mention_sound", False)))
        self._select_data(self.mention_tone_cb,
                          getattr(cfg, "mention_tone", "ding") or "ding")
        self.mention_rep_sp.setValue(int(getattr(cfg, "mention_repeat", 1)
                                         or 1))
        self.mention_text_le.setText(getattr(cfg, "mention_text", "") or "")
        self._on_mention_text(self.mention_text_le.text())
        self.mention_every_sp.setValue(int(getattr(cfg, "mention_every", 10)
                                           or 10))
        self.mention_during_sp.setValue(int(getattr(cfg, "mention_during", 30)
                                            if getattr(cfg, "mention_during",
                                                       None) is not None
                                            else 30))
        self.tts_cb.setChecked(cfg.tts_enabled)
        self._refresh_tts_voices(cfg.ocr_target)
        if cfg.tts_voice:
            self._select_data(self.voice_cb, cfg.tts_voice)
        self.tts_rate_sl.setValue(int(getattr(cfg, "tts_rate", 0) or 0))
        self.tts_pitch_sl.setValue(int(getattr(cfg, "tts_pitch", 0) or 0))
        self._refresh_ocr_status()

    def _warn(self, text):
        QMessageBox.warning(self, tr("warn"), text)

    def _gather_config(self, show_errors=True, validate=True):
        chat, voice = self.chat_panel.get_state(), self.voice_panel.get_state()
        mode = ("local" if chat["provider"] == "local" else
                "mt" if core.is_mt_provider(chat["provider"]) else "cloud")
        prov = (chat["provider"] if mode == "cloud"
                else self.chat_panel._last_cloud) or "DeepSeek"
        model = chat["model"]
        api_keys = {k: v for k, v in self._api_keys.items() if v}
        custom_urls = {k: v for k, v in self._custom_urls.items() if v}
        custom_names = {k: v for k, v in self._custom_names.items() if v}
        custom_url = custom_urls.get("Personalizado (OpenAI-compatível)", "")
        cloud_models = dict(self._cloud_models)
        if mode == "cloud" and model:
            cloud_models[prov] = model
        voice_prov = voice["provider"]
        voice_model = voice["model"] if voice_prov else ""
        if voice_prov and voice_prov != "local" and voice_model:
            cloud_models[voice_prov] = voice_model

        def fail(text):
            if show_errors:
                self._warn(text)
            return None

        if validate:
            for pn, st in ((self.chat_panel, chat), (self.voice_panel, voice)):
                what = T("The chat AI ({p})", p="{p}") if pn.which == "chat" \
                    else T("The voice AI ({p})", p="{p}")
                if pn.is_same():
                    continue
                if pn.is_local() and not st["model"]:
                    return fail(T("No Ollama models.\nUse 🤗 or: "
                                  "ollama pull gemma2:2b") if pn.which ==
                                "chat" else
                                T("Choose the voice's local (Ollama) model."))
                if pn.is_cloud():
                    name = core.provider_label(pn._prov)
                    if pn.missing():
                        pn._point_missing()
                        return fail(T("{who} has no key (or URL).\nPaste it "
                                      "in its panel and press Test.",
                                      who=what.format(p=name)))
                    if not st["model"]:
                        return fail(T("Choose a model."))
                    known = self._model_lists.get(pn._prov)
                    if known and not core.is_custom_provider(pn._prov) and \
                            not any(core.model_id(m) == st["model"]
                                    for m in known):
                        return fail(T("'{m}' is not in the list of models "
                                      "your {p} account can use (the "
                                      "provider says it doesn't exist or "
                                      "you have no access).\nChoose one from "
                                      "the list.", m=st["model"], p=name))
                    if st["opts"].get("free_only") and not pn.model_is_free():
                        return fail(T("'{m}' is not a free model and "
                                      "'Only free' is on.\nChoose a green "
                                      "model or turn 'Only free' off.",
                                      m=st["model"]))
        hotkey = self.voice_hotkey_le.text().strip() or DEFAULT_VOICE_HOTKEY
        current_style = load_overlay_state().get("style", {})
        return AppConfig(
            mode=mode,
            mt_engine=chat["provider"] if mode == "mt" else "",
            cloud_provider=prov,
            model=model, api_key=api_keys.get(prov, ""),
            gpu_layers=int(self.gpu_layers_cb.currentData()
                           if self.gpu_layers_cb.currentData() is not None
                           else -1),
            num_parallel=int(self.num_par_cb.currentData() or 1),
            keep_alive=self.keep_alive_cb.currentData() or "-1",
            ocr_source=self.ocr_src_cb.currentData() or "Auto (detectar)",
            ocr_target=self.ocr_tgt_cb.currentData() or "English",
            voice_source=self.voice_src_cb.currentData() or "English",
            voice_target=self.voice_tgt_cb.currentData() or "English",
            voice_hotkey=hotkey,
            tts_enabled=self.tts_cb.isChecked(),
            tts_voice=self.voice_cb.currentData() or "en-US-AriaNeural",
            tts_rate=self.tts_rate_sl.value(),
            tts_pitch=self.tts_pitch_sl.value(),
            tts_output_device=self.out_cb.currentData(),
            mic_device_index=self.mic_cb.currentData(),
            mic_device_name=self._mic_names.get(self.mic_cb.currentData(), ""),
            my_name=self.my_name_le.text().strip(),
            mention_sound=self.mention_cb.isChecked(),
            mention_tone=self.mention_tone_cb.currentData() or "ding",
            mention_repeat=self.mention_rep_sp.value(),
            mention_text=self.mention_text_le.text().strip(),
            mention_every=self.mention_every_sp.value(),
            mention_during=self.mention_during_sp.value(),
            appearance_style=dict(current_style),
            voice_mode=self.voice_mode_cb.currentData() or "hold",
            voice_confirm=self.voice_confirm_cb.isChecked(),
            continuous_tts=self.cont_tts_cb.isChecked(),
            cancel_hotkey=self.cancel_hotkey_le.text().strip() or "esc",
            api_keys=api_keys, cloud_models=cloud_models,
            voice_provider=voice_prov, voice_model=voice_model,
            cloud_fallback=self.chat_panel.fallback_cb.isChecked(),
            custom_base_url=custom_url, custom_urls=custom_urls,
            custom_names=custom_names,
            ocr_per_min=int(self.ocr_rate_cb.currentData() or 20),
            chat_region=list(self._chat_region),
            chat_region_on=self.calib_on_cb.isChecked(),
            ai_opts=chat["opts"], voice_opts=voice["opts"],
            # Compatibilidade (versões antigas da app leem estes):
            ai_reasoning=chat["opts"].get("reasoning") == "on",
            max_context=int(chat["opts"].get("context") or 0))

    def _start(self):
        log().info("[_start] begin")
        cfg = self._gather_config()
        if not cfg:
            log().info("[_start] no config — abort")
            return
        if not _TESS_OK:
            self._warn(T("Tesseract OCR is missing."))
        ocr_lang_code = LANGUAGES.get(cfg.ocr_source, {}).get("tess")
        if ocr_lang_code and not is_tessdata_installed(ocr_lang_code):
            if QMessageBox.question(
                    self, tr("warn"),
                    T("Language pack '{c}' is missing. Open the manager?",
                      c=ocr_lang_code)) == QMessageBox.StandardButton.Yes:
                self._open_lang_manager()
        try:
            save_last_config(cfg)
        except Exception:
            log().exception("[_start] falha a guardar last config")
        log().info(f"[_start] on_start | mode={cfg.mode} model={cfg.model} "
                   f"voz={cfg.voice_provider}/{cfg.voice_model} "
                   f"ctx={cfg.max_context}")
        self.on_start(cfg)
        log().info("[_start] on_start returned OK")


# ==================================================================
# APP
# ==================================================================
class RFTranslatorApp:
    def __init__(self):
        self.cfg_window = None
        self.overlay = None
        self.ocr_worker = None
        self.hotkey_listener = None
        self.engine = None
        self.voice_engine = None
        self.tts = TTSManager()
        self.last_cfg = None
        self._voice_busy = False
        self._voice_started = 0.0
        self._voice_job = 0             # nº do ditado atual
        self._voice_cancel = None       # Event da tecla de cancelar
        self._continuous_stop = None    # Event do modo contínuo ligado
        self._voice_worker_ref = None
        self._tray_icon = None
        self.game = GameWindow()
        # O overlay só aparece com o jogo (ou esta app) em primeiro plano.
        self._vis_timer = QTimer()
        self._vis_timer.setInterval(250)
        self._vis_timer.timeout.connect(self._update_overlay_visibility)

    def _update_overlay_visibility(self):
        ov = self.overlay
        if ov is None or self.ocr_worker is None:
            return      # parado / na janela de config
        try:
            in_game = (self.game.is_foreground()
                       and not self.game.is_minimized())
            show = in_game or self.game.foreground_is_own_process()
        except Exception:
            log().exception("visibilidade do overlay")
            show = True
        if show and not ov.isVisible():
            ov.show()
        elif not show and ov.isVisible():
            ov.hide()

    def start(self):
        self.cfg_window = ConfigWindow(
            on_start=self.on_start_translator,
            on_hf=self._open_hf_from_app,
            on_log=self._open_log_from_app)
        self.cfg_window.set_on_style_changed(self._on_style_changed)
        self.cfg_window.on_close = self._on_main_closed
        self.cfg_window.on_restart = self._restart_after_update
        self.cfg_window.tts = self.tts
        # Antes de mostrar: o botão da barra de tarefas nasce já com o ícone.
        _set_class_icon(int(self.cfg_window.winId()))
        self.cfg_window.show()
        self._setup_tray()
        if not os.path.isfile(core.get_last_config_path()):
            # 1.ª vez (ex.: amigo que acabou de instalar): abre o guia
            # rápido falado (o manual completo está no botão 📖).
            QTimer.singleShot(800, self.cfg_window.open_guide)

    def _on_style_changed(self, new_style):
        if self.overlay:
            self.overlay.set_style(new_style)

    def _setup_tray(self):
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable(): return
            self._tray_icon = QSystemTrayIcon(
                QIcon(APP_ICON) if os.path.isfile(APP_ICON)
                else self.cfg_window.style().standardIcon(
                    QStyle.StandardPixmap.SP_ComputerIcon))
            self._tray_icon.setToolTip("RF Online Translator")
            menu = QMenu()
            a_show = QAction("⚙  " + tr("ov_config"), menu)
            a_show.triggered.connect(self._tray_show)
            a_unlock = QAction("🔓  " + T("Unlock overlay"), menu)
            a_unlock.triggered.connect(self._tray_unlock)
            a_manual = QAction(T("📖  Manual"), menu)
            a_manual.triggered.connect(lambda: ManualDialog.show_manual(None))
            a_quit = QAction("❌  " + tr("ov_quit"), menu)
            a_quit.triggered.connect(self.quit)
            menu.addAction(a_show); menu.addAction(a_unlock)
            menu.addAction(a_manual)
            menu.addSeparator(); menu.addAction(a_quit)
            self._tray_icon.setContextMenu(menu)
            self._tray_icon.activated.connect(
                lambda r: self._tray_show()
                if r == QSystemTrayIcon.ActivationReason.DoubleClick
                else None)
            self._tray_icon.show()
        except Exception:
            log().exception("Falha a criar tray icon")

    def _tray_show(self): self.show_config()
    def _tray_unlock(self):
        if self.overlay:
            # Emitir sinal thread-safe
            self.overlay.sig_set_locked.emit(False)

    def _open_hf_from_app(self):
        HuggingFaceDialog(None,
                          on_models_changed=self._on_hf_models_changed).exec()
    def _open_log_from_app(self): LogViewerDialog(None).exec()
    def _on_hf_models_changed(self):
        if self.cfg_window: self.cfg_window.refresh_local_models()
        if self.overlay:
            self.overlay.sig_append_system.emit(
                T("🤗 New Ollama model available."))

    def on_start_translator(self, cfg):
        log().info("[on_start] begin")
        try:
            self.last_cfg = cfg
            core.set_custom_names(getattr(cfg, "custom_names", None) or {})
            self.engine = AIEngine(cfg)
            # IA só para a voz (se escolhida); senão a mesma do chat.
            vcfg = core.voice_config(cfg)
            self.voice_engine = AIEngine(vcfg) if vcfg else self.engine
            log().info("[on_start] engine OK"
                       + (f" | voz: {vcfg.mode}/{vcfg.cloud_provider}/"
                          f"{vcfg.model}" if vcfg else ""))
            # Modelos locais em uso: o do chat e o da voz (se forem
            # diferentes ficam os dois na VRAM; senão só um). Tudo o resto
            # sai da memória — também ao passar de local para a nuvem.
            keep_models = {m for m in (
                cfg.model if cfg.mode == "local" else None,
                vcfg.model if vcfg and vcfg.mode == "local" else None) if m}
            local_model = cfg.model if cfg.mode == "local" else (
                next(iter(keep_models)) if keep_models else None)

            self.tts.configure(enabled=cfg.tts_enabled,
                               voice=cfg.tts_voice,
                               output_device=cfg.tts_output_device,
                               rate=getattr(cfg, "tts_rate", 0),
                               pitch=getattr(cfg, "tts_pitch", 0))
            log().info("[on_start] tts OK")

            if local_model:
                exe = find_ollama_exe()
                log().info(f"[on_start] ollama exe: {exe}")
                if exe:
                    extra = {
                        "OLLAMA_NUM_PARALLEL": cfg.num_parallel or 1,
                        "OLLAMA_KEEP_ALIVE": cfg.keep_alive or "-1",
                        # 2 = chat e voz com modelos locais diferentes; a
                        # app descarrega tudo o que não está em uso (só um
                        # modelo na VRAM quando é o mesmo ou só um é local).
                        "OLLAMA_MAX_LOADED_MODELS": max(1, len(keep_models))}
                    if cfg.gpu_layers >= 0:
                        extra["OLLAMA_GPU_LAYERS"] = cfg.gpu_layers
                    try:
                        start_ollama_server(exe, extra_env=extra)
                        log().info("[on_start] ollama env aplicado")
                    except Exception:
                        log().exception("[on_start] falha a arrancar Ollama")
                    # Se o Ollama morrer a meio, o motor relança-o.
                    for eng in (self.engine, self.voice_engine):
                        eng.restart_backend = (
                            lambda: start_ollama_server(exe, extra_env=extra))
                    if len(keep_models) > 1:
                        threading.Thread(
                            target=self._ensure_two_models,
                            args=(exe, extra, sorted(keep_models)),
                            daemon=True).start()
            if is_ollama_running():
                # O Ollama pode estar com outros modelos (o anterior, ou
                # o local de antes de passares para a nuvem).
                threading.Thread(target=unload_other_ollama_models,
                                 args=(keep_models,), daemon=True).start()

            log().info("[on_start] a esconder config window")
            self.cfg_window.hide()
            log().info("[on_start] config escondida")

            log().info("[on_start] a criar Overlay...")
            self.overlay = Overlay(
                on_show_config=self.show_config,
                on_quit=self.quit,
                on_close=self._on_overlay_close,
                on_toggle_tts=self.toggle_tts,
                on_hf=self._open_hf_from_app,
                on_log=self._open_log_from_app,
                on_send=self._confirm_send,
                on_discard=self.on_voice_cancel,
                on_toggle_confirm=self._set_voice_confirm)
            log().info("[on_start] Overlay criada")
            self.overlay.confirm_send = bool(
                getattr(cfg, "voice_confirm", False))

            self.overlay.show()
            log().info("[on_start] Overlay mostrada")

            def ai_label(c):
                return (T("Local") if c.mode == "local" else
                        core.mt_label(c.mt_engine) if c.mode == "mt"
                        else core.provider_label(c.cloud_provider))
            self.overlay.append_system(
                T("Chat AI: {a} • {m}", a=ai_label(cfg),
                  m=cfg.model if cfg.mode != "mt" else "—"))
            self.overlay.append_system(
                f"OCR: {lang_label(cfg.ocr_source)} → "
                f"{lang_label(cfg.ocr_target)}")
            self.overlay.append_system(
                T("Voice: {a} → {b}", a=lang_label(cfg.voice_source),
                  b=lang_label(cfg.voice_target)))
            if self.voice_engine is not self.engine:
                ve = self.voice_engine.cfg
                self.overlay.append_system(T(
                    "🎤 Voice AI: {a} • {m}", a=ai_label(ve),
                    m=ve.model if ve.mode != "mt" else "—"))
            self.overlay.append_system(
                T("🎹 Voice hotkey: {k}", k=cfg.voice_hotkey)
                + "  •  " + T("cancel: {k}",
                              k=getattr(cfg, "cancel_hotkey", "esc") or "esc"))
            self.overlay.append_system(
                f"🔊 TTS: {'ON' if cfg.tts_enabled else 'OFF'}")
            if cfg.my_name:
                self.overlay.append_system(
                    T("🧑 Ignoring: {n}", n=cfg.my_name)
                    + (" • 🔔" if getattr(cfg, "mention_sound", False)
                       else ""))
            log().info("[on_start] overlay msgs OK")

            self.ocr_worker = OCRWorker(self.engine, self.overlay, self.tts,
                                        cfg, game=self.game)
            self.ocr_worker.translated.connect(self.overlay.append_text)
            self.ocr_worker.tab_changed.connect(self.overlay.set_view)
            self.ocr_worker.error.connect(self.overlay.append_system)
            self.ocr_worker.perf.connect(self.overlay.set_perf)
            self.ocr_worker.start()
            self._vis_timer.start()
            log().info("[on_start] OCR worker startado")
            self._prepare_argos(cfg)
            self._confirm_engines(cfg)
            self._show_openrouter_quota(cfg)

            self.hotkey_listener = HotkeyListener(
                on_voice=self.on_voice_hotkey,
                voice_hotkey=cfg.voice_hotkey,
                on_toggle_lock=self._toggle_overlay_lock,
                lock_hotkey="ctrl+shift+l",
                should_capture=lambda: (self.game.is_foreground()
                                        or self.game.foreground_is_own_process()),
                on_cancel=self.on_voice_cancel,
                cancel_hotkey=getattr(cfg, "cancel_hotkey", "esc") or "esc",
                cancel_active=lambda: (self._voice_busy
                                       or self.tts.alert_active()))
            self.hotkey_listener.start()
            # Mede o ruído de fundo do micro agora (ainda não estás a
            # falar): o limiar de 'estás a falar' fica acima dele.
            threading.Thread(target=VoiceWorker.calibrate, args=(cfg,),
                             daemon=True, name="MicCalib").start()
            log().info("[on_start] Hotkey listener startado")
        except Exception:
            log().exception("[on_start] CRASH")
            raise

    def _confirm_engines(self, cfg):
        """Tradução de teste com o tradutor/modelo escolhido (chat e voz) e
        o resultado no overlay: confirma que carregou e funciona, ou mostra
        o erro logo (antes só se sabia quando chegava a 1.ª mensagem). No
        Local também deixa o modelo já carregado na memória."""
        ov = self.overlay
        jobs = [(T("Chat translator"), self.engine, cfg.ocr_target)]
        if self.voice_engine is not None and \
                self.voice_engine is not self.engine:
            jobs.append((T("Voice translator"), self.voice_engine,
                         cfg.voice_target))

        def name_of(c):
            return (T("Local") + f" · {c.model}" if c.mode == "local" else
                    core.mt_label(c.mt_engine) if c.mode == "mt" else
                    f"{core.provider_label(c.cloud_provider)} · {c.model}")

        def run():
            for what, eng, target in jobs:
                if eng is None or not self.overlay:
                    continue
                src_lang, sample = (("English", "Hello, where is the boss?")
                                    if target.startswith("Russian") else
                                    ("Russian", "Привет, где босс?"))
                t0 = time.time()
                try:
                    out = eng.translate(
                        sample, core.build_ocr_line_prompt(src_lang, target),
                        target=target)
                    out = next((l for l in (out or "").splitlines()
                                if l.strip()), "").strip()
                    if not out:
                        raise ValueError(T("empty answer"))
                    msg = T("✅ {w} ready ({n}, {s:.1f} s): '{a}' → '{b}'",
                            w=what, n=name_of(eng.cfg),
                            s=time.time() - t0, a=sample, b=out[:80])
                except Exception as e:
                    log().warning(f"Teste do tradutor ({what}) falhou: {e}")
                    msg = T("❌ {w} failed ({n}): {e}", w=what,
                            n=name_of(eng.cfg), e=str(e)[:160])
                log().info(msg)
                if ov:
                    ov.sig_append_system.emit(msg)
        threading.Thread(target=run, daemon=True, name="EngineCheck").start()

    def _prepare_argos(self, cfg):
        """Argos escolhido (chat ou voz): instala o motor e descarrega já os
        modelos mais prováveis, em fundo, com o progresso no overlay —
        senão a 1.ª mensagem ficava minutos à espera."""
        mts = [e.cfg for e in (self.engine, self.voice_engine)
               if e is not None and e.cfg.mode == "mt"]
        ov = self.overlay
        # Mensagens dos tradutores sem IA (downloads, Google bloqueado →
        # plano B) vão para o overlay.
        core.argos_status = (lambda t: ov.sig_append_system.emit(t)) \
            if ov and mts else None
        if any(c.mt_engine == "nllb" for c in mts):
            # Descarrega já (~650 MB) em vez de na 1.ª mensagem.
            def nllb_prep():
                try:
                    core._nllb_model()
                except Exception as e:
                    log().exception("NLLB: preparação falhou")
                    if ov:
                        ov.sig_append_system.emit(f"⚠️ NLLB: {e}")
            threading.Thread(target=nllb_prep, daemon=True,
                             name="NLLBPrep").start()
        uses = [c for c in mts if c.mt_engine == "argos"]
        if not uses:
            return
        sources, targets = {"Russian", "English"}, set()
        if cfg.ocr_source in core.LANGUAGES and core._mt_code(cfg.ocr_source):
            sources.add(cfg.ocr_source)
        targets.add(cfg.ocr_target)
        if any(c is self.voice_engine.cfg for c in uses) or \
                self.voice_engine is self.engine:
            sources.add(cfg.voice_source)
            targets.update({cfg.voice_target, "Russian", "English"})
        threading.Thread(target=core.argos_prepare,
                         args=(sorted(sources), sorted(targets)),
                         daemon=True, name="ArgosPrep").start()

    def _show_openrouter_quota(self, cfg):
        """OpenRouter sem créditos = 50 pedidos grátis por dia: mostra no
        overlay quantos restam (sem gastar nenhum)."""
        engines = [e for e in (self.engine, self.voice_engine)
                   if e is not None and e.cfg.mode == "cloud"]
        keys = []
        for e in engines:
            p = e.cfg.cloud_provider
            if core.is_openrouter(p, core.provider_base_url(e.cfg, p)):
                k = core.provider_key(e.cfg, p)
                if k and k not in keys:
                    keys.append(k)
        worker = self.ocr_worker
        if not keys or worker is None:
            return

        def run():
            for k in keys:
                try:
                    info = core.openrouter_key_info(k)
                except Exception as e:
                    log().warning(f"OpenRouter: quota indisponível ({e})")
                    continue
                txt = core.openrouter_quota_text(info)
                if not txt:
                    continue
                log().info(f"OpenRouter: {txt}")
                if info.get("free_left") is not None \
                        and info["free_left"] <= 5:
                    txt += " — " + T("free models will stop soon; resets "
                                     "at 00:00 UTC")
                worker._emit("error", "OpenRouter: " + txt)
        threading.Thread(target=run, daemon=True,
                         name="ORQuota").start()

    def _toggle_overlay_lock(self):
        """Chamado do thread do pynput — só emite sinal, NUNCA toca na GUI."""
        if self.overlay:
            try:
                self.overlay.sig_set_locked.emit(not self.overlay.is_locked())
            except Exception:
                log().exception("Falha a emitir sig_set_locked")

    def toggle_tts(self):
        self.tts.enabled = not self.tts.enabled
        if self.overlay:
            self.overlay.sig_append_system.emit(
                f"🔊 {'ON' if self.tts.enabled else 'OFF'}")

    def on_voice_hotkey(self):
        """Chamado do thread do pynput — NUNCA toca na GUI diretamente."""
        if self.engine is None or self.overlay is None:
            return
        self.tts.stop_alert()       # vais responder: o alerta já cumpriu
        # Mensagem escrita à espera de confirmação: o atalho envia-a.
        if self._confirm_send():
            return
        # Modo contínuo ligado: o atalho outra vez desliga-o.
        if self._continuous_stop is not None:
            self._continuous_stop.set()
            self._continuous_stop = None
            return
        if self._voice_busy:
            # Rede de segurança: uma gravação nunca demora mais de ~40s.
            if time.time() - self._voice_started < 45:
                log().info("Hotkey voz ignorada: ainda a processar a anterior")
                # Bip grave: 'ainda não, estou a tratar da anterior'
                # (a tecla de cancelar acaba com ela).
                self.tts.cue("busy")
                return
            log().warning("Voz presa há >45s — a libertar")
        # Ctrl+S noutras apps é 'guardar': só grava com o jogo à frente
        # (senão escrevia a tradução no browser/editor).
        try:
            # Jogo à frente, ou o foco ficou no overlay (clicaste-lhe):
            # aí o VoiceWorker devolve o foco ao jogo antes de escrever.
            if not (self.game.is_foreground()
                    or self.game.foreground_is_own_process()):
                log().info("Hotkey voz ignorada: jogo não está à frente")
                return
        except Exception:
            log().exception("is_foreground")
        self._voice_busy = True
        self._voice_started = time.time()
        self._voice_job += 1
        job = self._voice_job
        self._voice_cancel = threading.Event()
        cont = None
        if getattr(self.last_cfg, "voice_mode", "hold") == "continuous":
            cont = self._continuous_stop = threading.Event()
            # Pode ficar ligado muito tempo: sem a rede de segurança dos 45s.
            self._voice_started = float("inf")
        # Emitir sinal thread-safe
        self.overlay.sig_append_system.emit(T("🎤 Recording..."))
        ocr = self.ocr_worker
        # on_done é chamado directamente pela thread da voz: o sinal
        # 'finished' ligado aqui (thread do pynput, sem event loop Qt)
        # nunca era entregue e o Ctrl+S ficava ignorado depois da 1.ª vez.
        worker = VoiceWorker(self.voice_engine or self.engine,
                             self.last_cfg, game=self.game,
                             chat_open=ocr.chat_open if ocr else None,
                             tts=self.tts,
                             on_done=lambda: self._voice_done(job),
                             cancel_event=self._voice_cancel,
                             reply_target=(lambda: ocr.last_pm_from)
                             if ocr else None,
                             lang_hint=ocr.guess_target_lang if ocr else None,
                             current_channel=(lambda: ocr.game_tab)
                             if ocr else None,
                             release_event=getattr(self.hotkey_listener,
                                                   "release_event", None),
                             continuous_stop=cont)
        worker.status.connect(self.overlay.append_system)
        worker.voice_state.connect(self.overlay.set_voice_state)
        self._voice_worker_ref = worker
        worker.trigger()

    def _confirm_send(self):
        """✔ Enviar (ou o atalho outra vez): envia a mensagem que está
        escrita no chat à espera. True se havia uma."""
        w = self._voice_worker_ref
        if w is not None and w.awaiting:
            w.confirm_event.set()
            return True
        return False

    def _set_voice_confirm(self, on):
        """Opção do menu do overlay: confirmar antes de enviar."""
        on = bool(on)
        if self.overlay:
            self.overlay.confirm_send = on
        if self.last_cfg is not None:
            # O ditado em curso lê este mesmo objeto: vale já.
            self.last_cfg.voice_confirm = on
            save_last_config(self.last_cfg)
        if self.cfg_window:
            self.cfg_window.voice_confirm_cb.setChecked(on)
        if self.overlay:
            self.overlay.append_system(
                T("✋ Confirm before sending: ON") if on
                else T("⚡ Sends by itself: confirmation OFF"))
        if not on:
            self._confirm_send()    # a que estava à espera vai já

    def _voice_done(self, job=None):
        # Um ditado cancelado acaba mais tarde (ex.: à espera da IA): não
        # pode libertar o ditado novo que entretanto começaste.
        if job is None or job == self._voice_job:
            self._voice_busy = False

    def on_voice_cancel(self):
        """Tecla de cancelar (thread do pynput — só sinais, nada de Qt)."""
        if self.tts.stop_alert():
            log().info("Alerta de menção parado (tecla de cancelar)")
            if not self._voice_busy:
                return
        if not self._voice_busy or self._voice_cancel is None:
            return
        self._voice_cancel.set()
        self.tts.cue("cancel")
        if self._continuous_stop is None:
            # Liberta já: dá para ditar outra vez sem esperar que a IA
            # responda ao pedido cancelado (que já não vai escrever nada).
            self._voice_busy = False
        if self.overlay:
            self.overlay.sig_append_system.emit(
                T("✖ Dictation cancelled — nothing sent"))

    def show_config(self):
        self._stop_workers()
        if self.overlay:
            try: self.overlay._save_state()
            except Exception: pass
            self.overlay.hide()
        if self.cfg_window:
            if self.last_cfg:
                self.cfg_window._refresh_audio_devices()
                self.cfg_window.refresh_local_models()
                self.cfg_window._refresh_profiles()
                self.cfg_window._apply_config(self.last_cfg)
            self.cfg_window._update_app_status()
            self.cfg_window.show()
            self.cfg_window.raise_()
            self.cfg_window.activateWindow()

    def _on_overlay_close(self):
        """✕ do overlay (modo chat): o que está nas Definições."""
        if core.get_close_action("close_overlay") == "quit":
            self.quit()
        else:
            self.show_config()

    def _on_main_closed(self):
        """✕ da janela principal: fecha a app ou fica na bandeja."""
        if self.ocr_worker is not None:
            return      # tradutor a correr: a janela só foi escondida
        if core.get_close_action("close_main") == "tray" and self._tray_icon:
            self._tray_icon.showMessage(
                "RF Online Translator",
                T("The app is still running here. Double-click to open it; "
                  "right-click → Quit to close it."),
                QSystemTrayIcon.MessageIcon.Information, 4000)
            return
        self.quit()

    def _stop_workers(self):
        self._vis_timer.stop()
        if self._continuous_stop is not None:
            self._continuous_stop.set()
            self._continuous_stop = None
        if self.ocr_worker:
            self.ocr_worker.stop(); self.ocr_worker = None
            if self.overlay:
                self.overlay.set_perf(None)
        if self.hotkey_listener:
            self.hotkey_listener.stop(); self.hotkey_listener = None

    def _ensure_two_models(self, exe, extra, models):
        """Chat e voz com modelos locais DIFERENTES: os dois têm de ficar na
        memória ao mesmo tempo. Um Ollama que já estava a correr com 'só 1
        modelo' trocava um pelo outro a cada ditado (5-15 s a recarregar o
        do chat de cada vez): carrega os dois e, se não couberem juntos,
        relança o Ollama a aceitar 2."""
        import requests
        import subprocess
        ka = str(extra.get("OLLAMA_KEEP_ALIVE", "-1"))
        ka = int(ka) if re.fullmatch(r"-?\d+", ka) else ka
        for attempt in range(2):
            for m in models:
                try:
                    requests.post(f"{core.OLLAMA_URL}/api/generate",
                                  json={"model": m, "keep_alive": ka},
                                  timeout=180)
                except Exception:
                    log().debug(f"Ollama: carregar {m}", exc_info=True)
            loaded = set(core.loaded_ollama_models())
            if all(m in loaded for m in models):
                log().info(f"Ollama: chat e voz carregados ({models})")
                return
            if attempt:
                log().warning(f"Ollama: não cabem os dois modelos {models} "
                              f"(só {sorted(loaded)})")
                return
            log().warning("Ollama a correr com 1 modelo só — a relançar "
                          "para chat e voz ficarem os dois")
            try:
                subprocess.run(["taskkill", "/IM", "ollama.exe", "/F"],
                               capture_output=True, timeout=10)
                time.sleep(1.0)
                start_ollama_server(exe, extra_env=extra)
            except Exception:
                log().exception("Ollama: relançar falhou")
                return

    def _unload_ollama(self):
        try:
            if is_ollama_running():
                unload_all_ollama_models()      # o que estiver na VRAM
        except Exception:
            log().exception("Falha a descarregar modelo Ollama")

    def _restart_after_update(self):
        """Depois de atualizar: fecha (limpo, como o ✕) e uma vigia abre a
        app outra vez quando esta acabar — já com o código novo."""
        log().info("Atualização: a reiniciar a app")
        try:
            core.restart_app_after_exit()
        except Exception:
            log().exception("Não consegui agendar o reinício")
        self.quit()

    def quit(self):
        log().info("A fechar app.")
        if self.cfg_window:
            self.cfg_window._quitting = True
        try:
            if self.overlay: self.overlay._save_state()
        except Exception: pass
        self._stop_workers()
        self.tts.stop()
        self._unload_ollama()
        if self._tray_icon:
            try: self._tray_icon.hide()
            except Exception: pass
        if self.overlay: self.overlay.close()
        if self.cfg_window: self.cfg_window.close()
        QApplication.quit()


# ==================================================================
# ENTRY
# ==================================================================
def _install_excepthooks():
    def _excepthook(etype, value, tb):
        try:
            log().error("Excepção não tratada:", exc_info=(etype, value, tb))
        except Exception:
            import traceback
            traceback.print_exception(etype, value, tb)
    sys.excepthook = _excepthook

    def _thread_excepthook(args):
        try:
            log().error(f"Excepção na thread {args.thread}:",
                        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        except Exception:
            import traceback
            traceback.print_exception(args.exc_type, args.exc_value,
                                       args.exc_traceback)
    try:
        threading.excepthook = _thread_excepthook
    except Exception:
        pass


_WATCHDOG_SRC = r'''
import ctypes, json, sys, time, urllib.request
pid, url, log_path = int(sys.argv[1]), sys.argv[2], sys.argv[3]
k = ctypes.windll.kernel32
h = k.OpenProcess(0x00100000, False, pid)          # SYNCHRONIZE
if not h:
    sys.exit(0)
k.WaitForSingleObject(h, 0xFFFFFFFF)               # espera a app terminar
def post(path, body=None):
    req = urllib.request.Request(url + path, data=json.dumps(body).encode()
                                 if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read() or b"{}")
gone = []
try:
    for m in post("/api/ps").get("models", []):
        name = m.get("name") or m.get("model")
        post("/api/generate", {"model": name, "keep_alive": 0})
        gone.append(name)
except Exception as e:
    gone.append(f"erro: {e}")
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + ".000 [INFO   ] "
                "[Vigia       ] [watchdog] App terminou (pid %d) — modelos "
                "descarregados da VRAM: %s\n" % (pid, gone or "nenhum"))
except Exception:
    pass
'''


APP_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "app.ico")
_INSTANCE_MUTEX = None


def _single_instance():
    """False se a app já estiver aberta. Duas cópias = dois atalhos de voz
    a disputar o Ctrl+S e dois OCR a gastar CPU (fácil com o .exe:
    duplo clique duas vezes)."""
    global _INSTANCE_MUTEX
    if os.name != "nt" or "--allow-multiple" in sys.argv:
        return True
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.restype = wintypes.HANDLE
        k32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL,
                                     wintypes.LPCWSTR]
        _INSTANCE_MUTEX = k32.CreateMutexW(None, False,
                                           "RFOnlineTranslator.SingleInstance")
        err = ctypes.get_last_error()
        # 183 = já existe; 5 = existe mas de outro nível (admin/não admin).
        return not (err in (183, 5) or not _INSTANCE_MUTEX)
    except Exception:
        return True


_QUIT_EVENT_NAME = "RFOnlineTranslator.Quit"


def _quit_event(create):
    """Evento do Windows para pedir à app aberta que feche (--quit)."""
    if os.name != "nt":
        return None
    k32 = ctypes.windll.kernel32
    k32.CreateEventW.restype = wintypes.HANDLE
    k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL,
                                 wintypes.BOOL, wintypes.LPCWSTR]
    k32.OpenEventW.restype = wintypes.HANDLE
    k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL,
                               wintypes.LPCWSTR]
    if create:      # manual-reset, começa desligado
        return k32.CreateEventW(None, True, False, _QUIT_EVENT_NAME)
    return k32.OpenEventW(0x0002, False, _QUIT_EVENT_NAME)  # EVENT_MODIFY_STATE


def _signal_quit():
    h = _quit_event(create=False)
    if not h:
        return False
    ctypes.windll.kernel32.SetEvent(ctypes.c_void_p(h))
    return True


def _start_unload_watchdog():
    """Processo à parte que espera a app terminar — fechada, crash ou
    morta à força — e descarrega os modelos do Ollama da VRAM. Com
    keep_alive '∞' o modelo fica carregado enquanto a app corre."""
    if os.name != "nt":
        return
    try:
        import subprocess
        exe = sys.executable
        pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        subprocess.Popen(
            [pyw if os.path.isfile(pyw) else exe, "-c", _WATCHDOG_SRC,
             str(os.getpid()), core.OLLAMA_URL, get_log_path()],
            creationflags=(subprocess.CREATE_NO_WINDOW
                           | subprocess.DETACHED_PROCESS),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True)
        log().info("Vigia ativo: descarrega o modelo quando a app terminar")
    except Exception:
        log().exception("Não consegui arrancar o vigia de descarga")


def _set_class_icon(hwnd):
    """A app corre como admin e o Windows (UIPI) não deixa a barra de
    tarefas (sem admin) pedir o ícone à janela (WM_GETICON): usa o da
    classe da janela, que no Qt é o ícone genérico das aplicações. Põe o
    app.ico na classe (vale para todas as janelas da app)."""
    if os.name != "nt" or not hwnd or not os.path.isfile(APP_ICON):
        return
    try:
        u32 = ctypes.windll.user32
        u32.LoadImageW.restype = ctypes.c_void_p
        u32.LoadImageW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p,
                                   ctypes.c_uint, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_uint)
        u32.SetClassLongPtrW.restype = ctypes.c_void_p
        u32.SetClassLongPtrW.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                         ctypes.c_void_p)
        IMAGE_ICON, LR_LOADFROMFILE = 1, 0x10
        GCLP_HICON, GCLP_HICONSM = -14, -34
        for idx, metric in ((GCLP_HICON, 11), (GCLP_HICONSM, 49)):
            size = u32.GetSystemMetrics(metric)    # SM_CXICON / SM_CXSMICON
            ico = u32.LoadImageW(None, APP_ICON, IMAGE_ICON, size, size,
                                 LR_LOADFROMFILE)
            if ico:
                u32.SetClassLongPtrW(ctypes.c_void_p(hwnd), idx, ico)
    except Exception:
        log().exception("Ícone da barra de tarefas")
    _set_taskbar_props(hwnd)


APP_USER_MODEL_ID = "RFOnlineTranslator.App"


def _set_taskbar_props(hwnd):
    """Com um AppUserModelID próprio a barra de tarefas procura o ícone
    pelo ID (não pela janela) e, sem atalho registado, mostrava o ícone
    genérico. As propriedades RelaunchIconResource/Command da janela
    (IPropertyStore) dizem-lhe qual é."""
    if os.name != "nt" or not hwnd:
        return
    try:
        import uuid
        exe = os.path.join(os.path.dirname(APP_ICON), "RF Translator.exe")
        icon = f"{exe},0" if os.path.isfile(exe) else f"{APP_ICON},0"
        relaunch = f'"{exe}"' if os.path.isfile(exe) else \
            f'"{sys.executable}" "{os.path.abspath(__file__)}"'

        class GUID(ctypes.Structure):
            _fields_ = [("b", ctypes.c_byte * 16)]

        class PROPERTYKEY(ctypes.Structure):
            _fields_ = [("fmtid", GUID), ("pid", wintypes.DWORD)]

        class PROPVARIANT(ctypes.Structure):
            _fields_ = [("vt", ctypes.c_ushort), ("r", ctypes.c_ushort * 3),
                        ("val", ctypes.c_wchar_p), ("pad", ctypes.c_void_p)]

        def guid(s):
            g = GUID()
            ctypes.memmove(g.b, uuid.UUID(s).bytes_le, 16)
            return g

        fmt = guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3")
        ps = ctypes.c_void_p()
        hr = ctypes.windll.shell32.SHGetPropertyStoreForWindow(
            ctypes.c_void_p(hwnd),
            ctypes.byref(guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")),
            ctypes.byref(ps))
        if hr != 0 or not ps:
            return
        vtbl = ctypes.cast(ctypes.cast(ps, ctypes.POINTER(ctypes.c_void_p))[0],
                           ctypes.POINTER(ctypes.c_void_p))
        set_value = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PROPERTYKEY),
            ctypes.POINTER(PROPVARIANT))(vtbl[6])
        release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])
        # 2 = RelaunchCommand, 3 = RelaunchIconResource,
        # 4 = RelaunchDisplayNameResource, 5 = ID (por último).
        for pid, text in ((2, relaunch), (3, icon),
                          (4, "RF Online Translator"),
                          (5, APP_USER_MODEL_ID)):
            pv = PROPVARIANT(vt=31, val=text)       # VT_LPWSTR
            set_value(ps, ctypes.byref(PROPERTYKEY(fmt, pid)),
                      ctypes.byref(pv))
        release(ps)
    except Exception:
        log().exception("Propriedades da barra de tarefas")


def main():
    setup_logger()
    log_env_summary()
    _install_excepthooks()
    load_ui_prefs()

    # ID próprio na barra de tarefas: sem ele o Windows junta as janelas
    # ao pythonw.exe e mostra o ícone do Python em vez do app.ico.
    if os.name == "nt":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                APP_USER_MODEL_ID)
        except Exception:
            pass

    log().info("[main] a criar QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("RF Online Translator")
    app.setQuitOnLastWindowClosed(False)
    # Fusion + paleta do tema: o mesmo aspeto em claro e escuro, também
    # nas caixas de mensagem e no seletor de cores.
    app.setStyle("Fusion")
    apply_theme(app)
    if os.path.isfile(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))
    log().info("[main] QApplication OK")

    if "--quit" in sys.argv:
        # 'RF Translator.exe --quit': fecha a app aberta de forma limpa
        # (descarrega o modelo como no ✕).
        ok = _signal_quit()
        log().info(f"[main] --quit: {'pedido enviado' if ok else 'app não está aberta'}")
        sys.exit(0)

    if not _single_instance():
        log().info("[main] já há uma cópia da app aberta — a sair")
        QMessageBox.information(None, "RF Online Translator",
                                T("The app is already running (see the "
                                  "tray icon next to the clock)."))
        sys.exit(0)

    try: kill_ollama_tray()
    except Exception: log().exception("kill_ollama_tray")
    _start_unload_watchdog()

    try:
        import atexit
        atexit.register(lambda: unload_all_ollama_models()
                        if is_ollama_running() else None)
    except Exception: pass

    problems = []
    if not _TESS_OK: problems.append("• Tesseract")
    if not SR_OK: problems.append(f"• Audio ({SR_ERR or 'N/A'})")
    if not PYNPUT_OK: problems.append("• Keyboard (pynput)")
    if problems:
        log().warning("Módulos em falta: " + ", ".join(problems))
        QMessageBox.warning(None, "Warning",
                            "\n".join(problems) +
                            "\n\n" + T("The app keeps running with limits."))

    try:
        rf = RFTranslatorApp()
        rf.start()
        log().info("GUI iniciada.")
        # --autostart: arranca logo com a última config (o mesmo que
        # carregar em Iniciar), para atalhos e testes.
        if "--autostart" in sys.argv:
            log().info("[main] --autostart")
            QTimer.singleShot(1500, rf.cfg_window._start)
        # Pedido de fecho vindo de 'RF Translator.exe --quit'.
        quit_ev = _quit_event(create=True)
        if quit_ev:
            quit_timer = QTimer()
            quit_timer.setInterval(500)
            quit_timer.timeout.connect(
                lambda: rf.quit() if ctypes.windll.kernel32.WaitForSingleObject(
                    ctypes.c_void_p(quit_ev), 0) == 0 else None)
            quit_timer.start()
    except Exception as e:
        log().exception("Falha a arrancar GUI")
        QMessageBox.critical(None, "Fatal", f"{e}\n\n" + T("See the log."))
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()