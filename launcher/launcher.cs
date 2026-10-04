// RF Translator.exe — lança a app (main.py) com o Python, sem consola.
// O manifesto (app.manifest) pede administrador ao Windows: o RF Online
// corre como admin e sem isso a app não lê o atalho nem escreve no chat.
//
// Python próprio da app: na 1.ª vez descarrega o Python oficial portátil
// (python.org, 'embeddable') para a pasta 'python\' ao lado do .exe e
// instala lá os pacotes (requirements.txt). Assim ninguém precisa de
// instalar o Python. Sem internet nessa 1.ª vez, usa um Python 3.13 já
// instalado (como antes).
//
//   RF Translator.exe --setup-only   prepara o 'python\' e sai
//
// Recompilar: launcher\build.bat
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows.Forms;

static class Launcher
{
    const string Title = "RF Online Translator";

    static string Quote(string s)
    {
        return "\"" + s.Replace("\"", "\\\"") + "\"";
    }

    // ---------- textos (língua do Windows) ----------
    static readonly Dictionary<string, string[]> Txt =
        new Dictionary<string, string[]> {
        // 0 título, 1 a descarregar Python, 2 pip, 3 pacotes, 4 a verificar,
        // 5 falhou, 6 pronto, 7 sem main.py, 8 não arrancou
        {"en", new[] {"First start — preparing the app",
            "Downloading Python {0} (about 11 MB)…",
            "Installing pip…",
            "Installing the app's packages (about 200 MB). This takes a few minutes, only the first time…",
            "Checking…",
            "Could not prepare the app's own Python:\n{0}\n\nCheck your internet connection and open the app again. Trying a Python already installed on this PC…",
            "Ready!",
            "main.py was not found next to this .exe:\n{0}",
            "Could not start the app with Python 3.13.\n\n{0}\n\nRun run.bat to see the error, or check logs\\fault.log."}},
        {"pt", new[] {"Primeiro arranque — a preparar a app",
            "A descarregar o Python {0} (cerca de 11 MB)…",
            "A instalar o pip…",
            "A instalar os pacotes da app (cerca de 200 MB). Demora uns minutos, só da primeira vez…",
            "A verificar…",
            "Não foi possível preparar o Python da app:\n{0}\n\nVerifica a ligação à internet e abre a app outra vez. A tentar um Python já instalado neste PC…",
            "Pronto!",
            "O main.py não foi encontrado ao lado deste .exe:\n{0}",
            "Não foi possível abrir a app com o Python 3.13.\n\n{0}\n\nCorre o run.bat para ver o erro, ou vê o logs\\fault.log."}},
        {"es", new[] {"Primer inicio — preparando la app",
            "Descargando Python {0} (unos 11 MB)…",
            "Instalando pip…",
            "Instalando los paquetes de la app (unos 200 MB). Tarda unos minutos, solo la primera vez…",
            "Comprobando…",
            "No se pudo preparar el Python de la app:\n{0}\n\nRevisa tu conexión a internet y abre la app otra vez. Probando un Python ya instalado en este PC…",
            "¡Listo!",
            "No se encontró main.py junto a este .exe:\n{0}",
            "No se pudo abrir la app con Python 3.13.\n\n{0}\n\nEjecuta run.bat para ver el error, o mira logs\\fault.log."}},
        {"fr", new[] {"Premier lancement — préparation de l'app",
            "Téléchargement de Python {0} (environ 11 Mo)…",
            "Installation de pip…",
            "Installation des paquets de l'app (environ 200 Mo). Quelques minutes, seulement la première fois…",
            "Vérification…",
            "Impossible de préparer le Python de l'app :\n{0}\n\nVérifie ta connexion internet et rouvre l'app. Essai d'un Python déjà installé sur ce PC…",
            "Prêt !",
            "main.py est introuvable à côté de ce .exe :\n{0}",
            "Impossible de lancer l'app avec Python 3.13.\n\n{0}\n\nLance run.bat pour voir l'erreur, ou regarde logs\\fault.log."}},
        {"de", new[] {"Erster Start — App wird vorbereitet",
            "Python {0} wird heruntergeladen (ca. 11 MB)…",
            "pip wird installiert…",
            "Pakete der App werden installiert (ca. 200 MB). Dauert ein paar Minuten, nur beim ersten Mal…",
            "Wird geprüft…",
            "Das Python der App konnte nicht vorbereitet werden:\n{0}\n\nPrüfe die Internetverbindung und öffne die App erneut. Versuche ein bereits installiertes Python…",
            "Fertig!",
            "main.py wurde neben dieser .exe nicht gefunden:\n{0}",
            "Die App konnte mit Python 3.13 nicht gestartet werden.\n\n{0}\n\nStarte run.bat, um den Fehler zu sehen, oder sieh in logs\\fault.log nach."}},
        {"ru", new[] {"Первый запуск — подготовка приложения",
            "Загрузка Python {0} (около 11 МБ)…",
            "Установка pip…",
            "Установка пакетов приложения (около 200 МБ). Несколько минут, только в первый раз…",
            "Проверка…",
            "Не удалось подготовить Python приложения:\n{0}\n\nПроверьте подключение к интернету и откройте приложение снова. Пробую уже установленный Python…",
            "Готово!",
            "main.py не найден рядом с этим .exe:\n{0}",
            "Не удалось запустить приложение с Python 3.13.\n\n{0}\n\nЗапустите run.bat, чтобы увидеть ошибку, или откройте logs\\fault.log."}},
        {"it", new[] {"Primo avvio — preparazione dell'app",
            "Download di Python {0} (circa 11 MB)…",
            "Installazione di pip…",
            "Installazione dei pacchetti dell'app (circa 200 MB). Qualche minuto, solo la prima volta…",
            "Verifica…",
            "Impossibile preparare il Python dell'app:\n{0}\n\nControlla la connessione a internet e riapri l'app. Provo un Python già installato su questo PC…",
            "Pronto!",
            "main.py non trovato accanto a questo .exe:\n{0}",
            "Impossibile avviare l'app con Python 3.13.\n\n{0}\n\nEsegui run.bat per vedere l'errore, oppure guarda logs\\fault.log."}},
    };

    static string[] L()
    {
        // A língua escolhida no install.bat (ui_prefs.json, a mesma da
        // app); sem ela, a do Windows.
        string lang = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
        try
        {
            string prefs = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,
                                        "ui_prefs.json");
            if (File.Exists(prefs))
            {
                var m = System.Text.RegularExpressions.Regex.Match(
                    File.ReadAllText(prefs), "\"lang\"\\s*:\\s*\"([a-z]{2})\"");
                if (m.Success) lang = m.Groups[1].Value;
            }
        }
        catch { }
        return Txt.ContainsKey(lang) ? Txt[lang] : Txt["en"];
    }

    // ---------- Python portátil da app ----------
    // Versões 3.13 a tentar, da mais nova para a mais antiga (a 1.ª que
    // existir em python.org). 3.13: a versão com que a app foi testada.
    static IEnumerable<string> Versions()
    {
        for (int p = 30; p >= 16; p--) yield return "3.13." + p;
        yield return "3.13.12";
        yield return "3.13.4";
    }

    static bool UrlExists(string url)
    {
        try
        {
            var rq = (HttpWebRequest)WebRequest.Create(url);
            rq.Method = "HEAD";
            rq.Timeout = 8000;
            using (var rs = (HttpWebResponse)rq.GetResponse())
                return rs.StatusCode == HttpStatusCode.OK;
        }
        catch { return false; }
    }

    // Temporários da instalação (pip, get-pip): dentro da pasta da app,
    // apagados no fim — nada fica no Temp do Windows.
    static string setupTmp;

    static int Run(string exe, string args, string cwd, StringBuilder log)
    {
        var psi = new ProcessStartInfo(exe, args);
        psi.WorkingDirectory = cwd;
        // Nada fora da pasta da app: sem cache do pip no perfil do Windows
        // nem pacotes do utilizador.
        psi.EnvironmentVariables["PIP_NO_CACHE_DIR"] = "1";
        psi.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
        // O pip corre 'rustc --version' se o encontrar no PATH, e esse
        // rustc abria uma janela de terminal: tira essas pastas do PATH.
        var keep = new List<string>();
        foreach (string d in (psi.EnvironmentVariables["PATH"] ?? "").Split(';'))
        {
            if (d.Length == 0) continue;
            bool rust = false;
            try { rust = File.Exists(Path.Combine(d, "rustc.exe")); }
            catch { }
            if (!rust) keep.Add(d);
        }
        psi.EnvironmentVariables["PATH"] = string.Join(";", keep.ToArray());
        if (setupTmp != null)
        {
            psi.EnvironmentVariables["TEMP"] = setupTmp;
            psi.EnvironmentVariables["TMP"] = setupTmp;
        }
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;
        using (var p = new Process())
        {
            p.StartInfo = psi;
            p.OutputDataReceived += (s, e) => { if (e.Data != null) lock (log) log.AppendLine(e.Data); };
            p.ErrorDataReceived += (s, e) => { if (e.Data != null) lock (log) log.AppendLine(e.Data); };
            p.Start();
            p.BeginOutputReadLine();
            p.BeginErrorReadLine();
            p.WaitForExit();
            return p.ExitCode;
        }
    }

    static string Tail(StringBuilder sb, int n)
    {
        string s;
        lock (sb) s = sb.ToString().Trim();
        return s.Length <= n ? s : "…" + s.Substring(s.Length - n);
    }

    /// Prepara dir\python (Python portátil + pacotes). Erro → mensagem.
    static string SetupPython(string dir, Action<string> status)
    {
        string[] t = L();
        string final = Path.Combine(dir, "python");
        string work = Path.Combine(dir, "python.setup");
        string tmpZip = Path.Combine(dir, "python.setup.zip");   // tudo dentro da app
        var log = new StringBuilder();
        setupTmp = Path.Combine(dir, "python.setup.tmp");
        try
        {
            if (Directory.Exists(setupTmp)) Directory.Delete(setupTmp, true);
            Directory.CreateDirectory(setupTmp);
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;  // TLS 1.2
            string ver = null, url = null;
            foreach (string v in Versions())
            {
                string u = "https://www.python.org/ftp/python/" + v +
                           "/python-" + v + "-embed-amd64.zip";
                if (UrlExists(u)) { ver = v; url = u; break; }
            }
            if (url == null)
                return "python.org: no Python 3.13 download found";
            status(string.Format(t[1], ver));
            if (Directory.Exists(work)) Directory.Delete(work, true);
            using (var wc = new WebClient())
                wc.DownloadFile(url, tmpZip);
            ZipFile.ExtractToDirectory(tmpZip, work);
            File.Delete(tmpZip);

            // python313._pth: site-packages (pip), a pasta da app (para
            // 'import core') e 'import site'.
            foreach (string pth in Directory.GetFiles(work, "python*._pth"))
            {
                string zipName = Path.GetFileNameWithoutExtension(pth) + ".zip";
                File.WriteAllText(pth, zipName + "\r\n.\r\nLib\\site-packages\r\n..\r\nimport site\r\n");
            }
            Directory.CreateDirectory(Path.Combine(work, @"Lib\site-packages"));

            status(t[2]);
            string getpip = Path.Combine(work, "get-pip.py");
            using (var wc = new WebClient())
                wc.DownloadFile("https://bootstrap.pypa.io/get-pip.py", getpip);
            string py = Path.Combine(work, "python.exe");
            if (Run(py, Quote(getpip) + " --no-cache-dir --no-warn-script-location --disable-pip-version-check",
                    work, log) != 0)
                return "pip: " + Tail(log, 400);
            File.Delete(getpip);

            status(t[3]);
            string req = Path.Combine(dir, "requirements.txt");
            if (Run(py, "-m pip install --no-cache-dir --no-warn-script-location --disable-pip-version-check -r " + Quote(req),
                    dir, log) != 0)
                return "pip install: " + Tail(log, 600);

            status(t[4]);
            if (Run(py, "-c \"import PyQt6.QtWidgets, requests, PIL, pytesseract, speech_recognition, pynput, pyaudio, edge_tts, pygame\"",
                    dir, log) != 0)
                return "import: " + Tail(log, 600);

            if (Directory.Exists(final)) Directory.Delete(final, true);
            Directory.Move(work, final);
            status(t[6]);
            return null;
        }
        catch (Exception e)
        {
            return e.Message + (log.Length > 0 ? "\n" + Tail(log, 300) : "");
        }
        finally
        {
            try { if (File.Exists(tmpZip)) File.Delete(tmpZip); } catch { }
            try { if (Directory.Exists(work)) Directory.Delete(work, true); } catch { }
            try { if (Directory.Exists(setupTmp)) Directory.Delete(setupTmp, true); } catch { }
            setupTmp = null;
        }
    }

    /// Janela de progresso enquanto prepara o Python. null = OK.
    static string SetupWithWindow(string dir)
    {
        string[] t = L();
        var form = new Form();
        form.Text = Title;
        form.FormBorderStyle = FormBorderStyle.FixedDialog;
        form.MaximizeBox = false;
        form.MinimizeBox = true;
        form.StartPosition = FormStartPosition.CenterScreen;
        form.ClientSize = new Size(520, 150);
        try { form.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
        var head = new Label();
        head.Text = t[0];
        head.Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 12, FontStyle.Bold);
        head.SetBounds(16, 14, 488, 26);
        var msg = new Label();
        msg.Text = "…";
        msg.SetBounds(16, 46, 488, 50);
        var bar = new ProgressBar();
        bar.Style = ProgressBarStyle.Marquee;
        bar.MarqueeAnimationSpeed = 30;
        bar.SetBounds(16, 108, 488, 22);
        form.Controls.Add(head);
        form.Controls.Add(msg);
        form.Controls.Add(bar);

        string error = "cancelled";
        form.Shown += (s, e) =>
        {
            var th = new Thread(() =>
            {
                error = SetupPython(dir, text =>
                {
                    try { form.BeginInvoke((Action)(() => msg.Text = text)); } catch { }
                });
                try { form.BeginInvoke((Action)(() => form.Close())); } catch { }
            });
            th.IsBackground = true;
            th.Start();
        };
        Application.EnableVisualStyles();
        Application.Run(form);
        return error;
    }

    [STAThread]
    static int Main(string[] args)
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string main = Path.Combine(dir, "main.py");
        if (!File.Exists(main))
        {
            MessageBox.Show(string.Format(L()[7], dir),
                            Title, MessageBoxButtons.OK,
                            MessageBoxIcon.Error);
            return 1;
        }
        bool setupOnly = false;
        string extra = "";
        foreach (string a in args)
        {
            if (a == "--setup-only") { setupOnly = true; continue; }
            extra += " " + Quote(a);
        }

        // 1) O Python da app (pasta 'python\'); na 1.ª vez prepara-o.
        string ownPy = Path.Combine(dir, @"python\pythonw.exe");
        if (!File.Exists(ownPy))
        {
            string err = SetupWithWindow(dir);
            if (err != null)
            {
                MessageBox.Show(string.Format(L()[5], err), Title,
                                MessageBoxButtons.OK, MessageBoxIcon.Warning);
                if (setupOnly) return 1;
            }
        }
        if (setupOnly)
            return File.Exists(ownPy) ? 0 : 1;

        var cands = new List<KeyValuePair<string, string>>();
        if (File.Exists(ownPy))
            cands.Add(new KeyValuePair<string, string>(ownPy, ""));

        // 2) Sem o Python da app: um Python 3.13 instalado, o 'pyw' do
        //    Windows, o da .venv e por fim o que estiver no PATH.
        string local = Environment.GetFolderPath(
            Environment.SpecialFolder.LocalApplicationData);
        string[] direct = {
            Path.Combine(local, @"Programs\Python\Python313\pythonw.exe"),
            @"C:\Program Files\Python313\pythonw.exe",
        };
        foreach (string p in direct)
            if (File.Exists(p))
                cands.Add(new KeyValuePair<string, string>(p, ""));
        string pyw = Path.Combine(Environment.GetFolderPath(
            Environment.SpecialFolder.Windows), "pyw.exe");
        if (File.Exists(pyw))
            cands.Add(new KeyValuePair<string, string>(pyw, "-3.13 "));
        string venv = Path.Combine(dir, @".venv\Scripts\pythonw.exe");
        if (File.Exists(venv))
            cands.Add(new KeyValuePair<string, string>(venv, ""));
        cands.Add(new KeyValuePair<string, string>("pythonw.exe", ""));

        string lastError = "";
        foreach (var c in cands)
        {
            try
            {
                var psi = new ProcessStartInfo(c.Key,
                    c.Value + Quote(main) + extra);
                psi.WorkingDirectory = dir;
                psi.UseShellExecute = false;
                // Nunca uma janela de consola (nem com python.exe).
                psi.CreateNoWindow = true;
                Process proc = Process.Start(psi);
                // Morreu logo com erro = este Python não serve (ex.: falta
                // um pacote): tenta o seguinte e, no fim, avisa.
                if (proc.WaitForExit(5000) && proc.ExitCode != 0)
                {
                    lastError = c.Key + " → exit code " + proc.ExitCode;
                    continue;
                }
                return 0;
            }
            catch (Exception e)
            {
                lastError = c.Key + " → " + e.Message;
            }
        }
        MessageBox.Show(string.Format(L()[8], lastError),
            Title, MessageBoxButtons.OK, MessageBoxIcon.Error);
        return 1;
    }
}
