# -*- coding: utf-8 -*-
"""
manual.py — manual da app (botão 📖 Manual), nas 7 línguas da interface.
HTML simples (o QTextBrowser só percebe um subconjunto de HTML/CSS).
"""

MANUAL = {}

MANUAL["en"] = """
<h2>🎮 RF Online Translator — Manual</h2>
<p>Reads the <b>RF Online chat</b> from the game window, translates every
message with an AI and shows it in a transparent window over the game,
split by channel (All, World, Server, Party, Guild, Raid, Whisper…). It can
read each message aloud (“<i>Name says: message</i>”). You can also
<b>speak in your language</b>: it translates and types it into the game
chat.<br>It only looks at the screen and types like a keyboard. It never
reads game memory or network traffic.</p>

<h3>1. First start</h3>
<p>Quickest way: the <b>🔊 Quick start</b> button (bottom of the main window) reads the essential steps aloud and shows where to click. It opens by itself the first time.</p>
<ol>
<li>Needs Windows 10/11. You don't need to install Python: run
<b>install.bat</b> once. It creates <b>RF Translator.exe</b> and puts the app's
own Python in its <b>python</b> folder (everything stays inside the app
folder).</li>
<li>Open <b>RF Translator.exe</b> and accept the administrator prompt. The game
runs as administrator, so Windows only lets the app read and type in it this
way.</li>
<li>The first start installs what is missing (Python packages, Tesseract
OCR, language packs, Ollama). This can take a few minutes.</li>
<li>Write your <b>character name</b> so your own messages are ignored.</li>
<li>Choose the AI (section 2) and the languages (section 3), then press
<b>▶ Start translator</b>.</li>
</ol>

<h3>2. Choosing the AI</h3>
<ul>
<li><b>Local (Ollama, this PC)</b>: free, private, works offline, uses about
2 GB of graphics memory. <b>gemma2:2b</b> is fast and fits next to the game
on an 8 GB card. Use 🤗 to download other models (☁ AI Clouds says which one fits your PC). Only one model is
loaded at a time. It is unloaded when the app closes, even after a
crash.</li>
<li><b>Without AI</b> (no key, no account): <b>🌐 Google Translate</b>
(online, fast; if Google blocks for a few minutes the app switches to
MyMemory and then to Argos by itself), <b>📦 Argos</b> (offline on this PC;
downloads ~20 MB plus ~150 MB per language pair when you press Start) and
<b>📦 NLLB</b> (offline, one ~630 MB model for 200 languages). No quotas and
no odd AI answers, but they do not fix OCR mistakes or game slang like an AI.
The voice panel can use a different one.</li>
<li><b>Cloud (API)</b>: better quality and no graphics memory. In the AI's panel (chat or voice), choose the AI, paste its key and press
<b>Test</b>. Each AI keeps its own key, saved encrypted with your Windows
account.</li>
<li><b>OpenRouter</b>: one key gives you hundreds of models. Type
<code>free</code> in the model field to see the free ones.
<b>Without credits the free models allow only 50 requests per day.</b>
The overlay and the Test button show how many are left. With 10 credits
the limit goes up to 1000 per day. One request translates up to 6 chat
lines.<br>
Tested free models (October 2026): <code>inclusionai/ling-3.0-flash-sante:free</code>
(fast and correct) and <code>nvidia/nemotron-3-super-120b-a12b:free</code>
(good, about 1 s per request with “thinking” off). Avoid
<code>nemotron-3.5-lightning</code> (very slow, wrong output). Free models
are sometimes busy (“rate-limited upstream”) for a few minutes.</li>
<li><b>Custom server 1 and 2</b>: any OpenAI-compatible server (OpenRouter,
LM Studio, vLLM, another PC, other providers). Write the server URL (for
example <code>https://openrouter.ai/api/v1</code> or
<code>http://localhost:1234/v1</code>), add the key if it needs one, press
Test and choose the model. Having two lets you run two cloud AIs at the same
time.</li>
<li><b>Voice AI</b>: by default it is the same as the chat AI. You can choose
another one, for example a free model for the chat and a better one for
your voice. Two cloud AIs can run at the same time.</li>
<li><b>If this AI fails, try the others that have a key</b>: when the main AI
is down, out of credit or busy, the app uses another AI that is set up and
goes back to the main one after 2 minutes.</li>
<li><b>Profile and options</b> (one set for the chat AI and one for the
voice AI): choose a <b>Profile</b> to fill in the AI, the model and its options
in one click. ⭐ profiles come with the app (✅ = tested with this app,
🆓 = free plan, not tested here). 💾 saves your own and 🗑 deletes it.
Options: <i>Temperature</i> (Tested = 0.1 local / 0.2 cloud; <i>Model
default</i> sends nothing), <i>Thinking</i> (leave it <b>Off</b>, which is
much faster), <i>Context</i> and <i>Answer max.</i> (Automatic is fine;
use 4k–8k for small models) and <i>Lines per request</i> (cloud chat:
more lines means fewer requests, which saves free daily limits).</li>
<li><b>Free AIs for a whole day</b>: all OpenRouter <code>:free</code>
models <b>share</b> the same 50 requests per day (1000 with 10 credits). To
play all day for free, use <b>Local</b> (no limit) or one of these:
<b>Mistral</b> (free “Experiment” plan, about 1 request per second, no
daily limit; profile ⭐ Mistral · Small), <b>Google Gemini</b> (free key from
AI Studio; Flash-Lite allows about 1000 requests per day) or <b>Groq</b>
(free key, about 1000 requests per day per model). Add a second AI as the
fallback and the app switches when one runs out. Limits change, and each
provider shows them on its site.</li>
<li>☁ <b>AI Clouds</b> (tab at the top of this window, or the button under the keys): which cloud AIs are free, their limits and where to create the keys.</li>
<li><b>The two AI panels</b> (chat and voice) are the same: AI, key (Test / Get key), for custom servers a <b>Name</b> you choose and the URL, the model with <b>🔍 search</b>, <b>🆓 Only free</b> (free models are <b>green</b>; ⛔ = refused by your account, e.g. paid models you blocked), profile and options. <b>Requests/min</b> keeps each cloud AI under its rate limit. With a local AI the cloud-only options are hidden.</li>
</ul>

<h3>3. Reading the chat</h3>
<ul>
<li><b>Source language</b>: <i>Auto</i> detects each line, so players can
write in different languages. <b>Translate to</b>: your language.</li>
<li>Keep the game chat open on the channel you want. The app reads the game
window directly, so the overlay can be anywhere and any size. When you
alt-tab, the overlay hides but reading and the voice keep going.</li>
<li>When you open the chat or switch tab, it translates <b>and reads
aloud</b> everything that was not read yet, in order. Messages that were
already read are <b>never repeated</b>, even after you close and reopen the
chat or restart the app (within 6 hours).</li>
<li>Your own messages and the PMs you send (“Sender: …”) are ignored.</li>
<li>🔊 <b>Neural voice</b> reads “Name says: message”. When many messages
are waiting, it reads a little faster so it does not fall behind.</li>
<li><b>Speed</b> and <b>Pitch</b> of the voice (in 🔊 Neural voice): adjust them and press <b>▶ Listen</b> to hear an example before you start. ↺ goes back to the default.</li>
<li>🔔 <b>Sound when someone writes my name</b> (under your character name): when a message contains your name (even with OCR mistakes or written in Cyrillic), an alert plays. Choose the <b>sound</b>, how many times it plays, or a <b>text</b> the voice says instead of the sound, only for you to hear (<code>{name}</code> = who wrote it) and <b>Repeat every X s for Y s</b> (default every 10 s for 30 s). The cancel key (Esc) or starting a dictation stops it. ▶ lets you hear it.</li>
<li><b>Chat reads per minute</b> (Chat reading): how often the app captures the game and reads the chat (20 = default). Fewer uses less CPU.</li>
</ul>

<h3>4. Speaking into the game (microphone)</h3>
<ul>
<li>Choose <b>I speak</b> and <b>Write in</b>, the microphone and the
<b>hotkey</b> (default F11). 🎤 <b>Test</b> shows the level and what was
understood. Devices named “MME:” usually work best.</li>
<li>Modes: <b>Push-to-talk</b> (records while you hold the key and stops
when you let go), <b>Tap</b> (one press listens until you make a long pause)
and <b>Continuous</b> (one press turns it on, another press turns it off; each
sentence is sent when you pause).</li>
<li>In every mode a rising beep means the app is listening and a short beep
means it stopped. While it listens, the overlay shows a blinking red
<b>● Listening</b>, then <b>⏳ Translating</b>.</li>
<li><b>✋ Confirm before sending</b> (in 🎤 Microphone or in the overlay ⚙
menu): off, the app types the message and sends it by itself. On, it types it
in the game chat and waits: a green <b>✔ Send</b> button appears in the
overlay bar (always visible). Press it, or the voice hotkey again, to send;
<b>✖</b> or Esc erases it. After 2 minutes without an answer the text stays
in the chat, not sent.</li>
<li>Voice commands at the start of a sentence:
<b>“reply …”</b> answers the last private message, and
<b>“change to chat guild / server / party / world / whisper”</b> (in any of
the languages) switches the game channel.</li>
<li>Replies use the language of the person you are talking to, when the
app knows it.</li>
<li>⚠️ The app types into the game chat and presses Enter for you.</li>
<li><b>Beeps</b> (through the app's voice output, i.e. your
headphones): rising beep = speak now; short beep = recording finished,
translating; falling beep = cancelled; low beep = still busy with the
previous one.</li>
<li><b>Cancel key</b> (default <b>Esc</b>; you can record another): stops a
dictation at once, whether it is listening, translating or typing, and
erases what was already typed. Enter is never pressed. It only acts while a
dictation is running; otherwise the key goes to the game as usual. In
continuous mode it drops only the current sentence.</li>
</ul>

<h3>5. The overlay</h3>
<ul>
<li>Drag it by the top bar and resize it by the edges. 🔒 locks it: it can't
be moved or resized and clicks go through to the game, but the top bar
stays clickable. <b>Ctrl+Shift+L</b> also locks and unlocks it.</li>
<li>The tabs follow the game channels, and the overlay switches tab when the
game does.</li>
<li>☰ menu: auto-hide after X seconds without messages, background
visibility, settings, voice on/off, language packs, log, ⚠️ errors, clear
overlay, exit.</li>
<li>The icon next to the Windows clock opens the settings and unlocks the
overlay.</li>
<li><b>✕</b> on the overlay goes back to the main window; ✕ on the main
window closes the app. You can change both in <b>⚙ App settings</b>.</li>
<li><b>⚙ App settings</b> (button at the bottom of the main window):
interface language, theme, overlay appearance, what ✕ does, language packs and audio devices
(microphone with 🎤 Test, and the voice output).</li>
<li><b>🔄 Updates</b> (in ⚙ App settings): when the app opens it checks
GitHub; if there is a new version the ⚙ button shows 🆕. <b>⬇️ Update now</b>
replaces only the app's code (~0.3 MB) and restarts it. Your settings, keys,
models and the app's Python stay as they are.</li>
<li><b>💾 Profiles</b> (box on the right of the main window): a profile
saves everything inside that box (character name and alert, chat reading,
microphone and hotkeys, reading voice) plus the overlay appearance and the
audio devices. It never saves the AI: each AI panel has its own profiles, so
applying a 💾 profile keeps the AI you have.</li>
</ul>

<h3>6. Reliable reading, speed and tests</h3>
<ul>
<li><b>Any resolution</b>: the app finds the chat by itself from 720p to 4K. If your chat is bigger or smaller, or the game interface has another scale, use <b>🎯 Calibrate</b> (Chat zone, in Chat reading): open the chat in the game, drag and resize the blue box over the messages and press <b>✔ Confirm</b> (Enter). The box only shows while the game is in front. <b>Use the calibrated zone</b> turns it on or off; the calibration stays saved.</li>
<li>Reading and translating run separately: the app keeps reading the chat while the AI translates, so a slow AI no longer lets messages scroll away unread. Messages that look alike (the same seller changing the price) are all read; the same message posted again is not.</li>
<li>Lines cut in half at the top or bottom of the chat wait until they are fully visible. Stickers are not read. <b>Numbers are always read aloud</b> (“in 5 minutes”, “20k”, “lvl 60”).</li>
<li><b>Game in sleep mode</b> (“Swipe to exit sleep mode”): the chat is still read. To type your voice message the app wakes the game (L key) and puts it back to sleep afterwards.</li>
<li><b>AI speed in the top bar</b>: ⚡ time of each AI request, ⏱ delay from reading the chat to showing the translation, ⏳ messages waiting, 👁 time of each chat read. Green = good, yellow = slow, red = too slow; ⚠ = the AI is failing. It can be turned off in the ⚙ menu (📊).</li>
<li>⚙ menu → <b>🪟 Show</b>: bar and chat, only the top bar (the chat hides and clicks go to the game) or only the chat (no bar; right-click for the menu). In <b>⚙ App settings → overlay appearance</b>: <b>chat font</b>, font size and <b>top bar size</b> (everything in the bar grows together).</li>
<li><b>📊 Ratings</b> (tab at the top of this window, or the ⚙ menu): the AIs tested with this app, with speed and quality, and <b>🧪 Test on this PC</b>: choose an AI (with the options it has now: GPU layers, context…) and press <b>▶ Test</b>. It shows the speed, the problems and whether it runs well on your PC; for a local AI it can also compare graphics card and processor.</li>
<li><b>Continuous mode with headphones</b>: with <b>🎧 Keep reading the chat in continuous mode</b> on, the chat voice keeps reading between your sentences and goes quiet while you speak. With speakers, turn it off so the mic never hears the voice. In every mode, a chat message cut off because you started talking is read again afterwards.</li>
<li><b>Local models</b>: only the model in use stays in the graphics memory; the previous one leaves when you change model or switch to a cloud AI. The voice can use another local model than the chat (then both stay loaded). Everything is unloaded when the app closes, even after a crash.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> sometimes answers in Arabic: the app translates those lines again, but a model from 📊 Ratings is better.</li>
</ul>

<h3>7. Problems</h3>
<ul>
<li><b>“Waiting for the RF Online window”</b>: the game is minimized or
closed.</li>
<li><b>Nothing is translated</b>: check ☰ → ⚠️ Errors. For a cloud AI, press
<b>Test</b> to check the key, credit and daily limit.</li>
<li><b>429 / rate-limited upstream</b>: that free model is busy. Wait a few
minutes or choose another one.</li>
<li><b>Daily limit</b>: the 50 free OpenRouter requests are used up. They
reset at 00:00 UTC. You can also use the local AI or a second AI.</li>
<li><b>Microphone too quiet or not understood</b>: use 🎤 Test, choose the
“MME:” device and turn off Windows audio enhancements (Voice
Clarity).</li>
<li><b>Game stutters with the local AI</b>: choose a smaller model or
<i>GPU layers → CPU only</i>.</li>
<li><b>📄 View log</b> opens the log (the <code>logs</code> folder). Audio is
never saved.</li>
</ul>

<h3>Privacy</h3>
<p>Keys are saved encrypted (Windows DPAPI) and only your Windows account can
read them. With a cloud AI, the chat text is sent to that provider. With the
local AI, nothing leaves the PC. The game captures and the app's voice stay in memory only: nothing is written to disk (no screenshots, no audio).</p>
"""

MANUAL["pt"] = """
<h2>🎮 RF Online Translator — Manual</h2>
<p>Lê o <b>chat do RF Online</b> a partir da janela do jogo, traduz cada
mensagem com uma IA e mostra-a numa janela transparente por cima do jogo,
separada por canal (Todos, Mundo, Servidor, Grupo, Guilda, Raid, Privado…).
Pode ler cada mensagem em voz alta («<i>Nome diz: mensagem</i>»). Também
podes <b>falar na tua língua</b>: a app traduz e escreve no chat do jogo.<br>
Só olha para o ecrã e escreve como um teclado. Nunca lê a memória do jogo
nem o tráfego de rede.</p>

<h3>1. Primeiro arranque</h3>
<p>O mais rápido: o botão <b>🔊 Guia rápido</b> (no fundo da janela principal) lê em voz alta os passos essenciais e mostra onde clicar. Abre sozinho da primeira vez.</p>
<ol>
<li>Precisa de Windows 10/11. Não precisas de instalar o Python: corre o
<b>install.bat</b> uma vez. Ele cria o <b>RF Translator.exe</b> e põe o Python
da app na pasta <b>python</b> (fica tudo dentro da pasta da app).</li>
<li>Abre o <b>RF Translator.exe</b> e aceita o pedido de administrador. O jogo
corre como administrador e o Windows só deixa a app ler e escrever nele
assim.</li>
<li>O primeiro arranque instala o que faltar (pacotes Python, Tesseract OCR,
pacotes de línguas, Ollama). Pode demorar alguns minutos.</li>
<li>Escreve o <b>nome da tua personagem</b>, para as tuas mensagens serem
ignoradas.</li>
<li>Escolhe a IA (ponto 2) e as línguas (ponto 3) e carrega em <b>▶ Iniciar
tradutor</b>.</li>
</ol>

<h3>2. Escolher a IA</h3>
<ul>
<li><b>Local (Ollama, este PC)</b>: grátis, privada e funciona sem internet.
Usa cerca de 2 GB da memória da placa gráfica. O <b>gemma2:2b</b> é rápido e
cabe ao lado do jogo numa placa de 8 GB. Usa o 🤗 para descarregar outros (o ☁ AI Clouds diz qual cabe no teu PC).
Só fica 1 modelo carregado de cada vez, e é descarregado quando a app fecha,
mesmo que rebente.</li>
<li><b>Sem IA</b> (sem chave nem conta): <b>🌐 Google Tradutor</b>
(online, rápido; se o Google bloquear uns minutos a app passa sozinha para o
MyMemory e depois para o Argos), <b>📦 Argos</b> (offline neste PC;
descarrega ~20 MB e mais ~150 MB por par de línguas ao carregar em Iniciar)
e <b>📦 NLLB</b> (offline, um modelo de ~630 MB para 200 línguas). Sem quotas
nem respostas estranhas da IA, mas não corrigem erros do OCR nem o calão do
jogo como uma IA. O painel da voz pode usar outro.</li>
<li><b>Nuvem (API)</b>: melhor qualidade e não gasta memória gráfica. No painel da IA (chat ou voz), escolhe a IA, cola a chave e carrega em
<b>Testar</b>. Cada IA guarda a sua chave, cifrada com a tua conta do
Windows.</li>
<li><b>OpenRouter</b>: uma chave dá acesso a centenas de modelos. Escreve
<code>free</code> no campo do modelo para veres os grátis.
<b>Sem créditos, os modelos grátis só permitem 50 pedidos por dia.</b>
O overlay e o botão Testar mostram quantos restam. Com 10 créditos passa a
1000 por dia. Cada pedido traduz até 6 linhas do chat.<br>
Modelos grátis testados (outubro de 2026):
<code>inclusionai/ling-3.0-flash-sante:free</code> (rápido e certo) e
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (bom, ~1 s por pedido
com o «pensar» desligado). Evita o <code>nemotron-3.5-lightning</code>
(muito lento e com erros). Às vezes os modelos grátis ficam ocupados uns
minutos («rate-limited upstream»).</li>
<li><b>Servidor próprio 1 e 2</b>: qualquer servidor compatível com a OpenAI
(OpenRouter, LM Studio, vLLM, outro PC, outros fornecedores). Escreve o URL
do servidor (ex.: <code>https://openrouter.ai/api/v1</code> ou
<code>http://localhost:1234/v1</code>) e a chave, se precisar. Depois carrega
em Testar e escolhe o modelo. Com dois podes ter duas IAs na nuvem ao mesmo
tempo.</li>
<li><b>IA da voz</b>: por defeito é a mesma do chat. Podes escolher outra
(ex.: um modelo grátis para o chat e um melhor para a tua voz). Podem
funcionar duas IAs na nuvem ao mesmo tempo.</li>
<li><b>Se esta IA falhar, usar as outras que têm chave</b>: se a principal
estiver em baixo, sem saldo ou ocupada, a app usa outra que esteja
configurada e volta à principal ao fim de 2 minutos.</li>
<li><b>Perfil e opções</b> (um conjunto para a IA do chat e outro para a
IA da voz): escolhe um <b>Perfil</b> para preencher a IA, o modelo e as opções
com um clique. Os perfis ⭐ vêm com a app (✅ = testado com esta app,
🆓 = plano grátis, não testado aqui). O 💾 guarda os teus e o 🗑 apaga-os.
Opções: <i>Temperatura</i> (Testada = 0.1 local / 0.2 nuvem; <i>Do
modelo</i> não envia nada), <i>Pensar</i> (deixa <b>Desligado</b>, que é
muito mais rápido), <i>Contexto</i> e <i>Resposta máx.</i> (Automático
chega; usa 4k–8k em modelos pequenos) e <i>Linhas por pedido</i> (chat na
nuvem: mais linhas = menos pedidos, o que poupa os limites diários
grátis).</li>
<li><b>IAs grátis para o dia todo</b>: todos os modelos <code>:free</code>
do OpenRouter <b>partilham</b> os mesmos 50 pedidos por dia (1000 com 10
créditos). Para jogar o dia todo sem pagar, usa a <b>Local</b> (sem limite)
ou uma destas: <b>Mistral</b> (plano grátis «Experiment», cerca de 1 pedido
por segundo, sem limite diário; perfil ⭐ Mistral · Small), <b>Google
Gemini</b> (chave grátis do AI Studio; o Flash-Lite dá cerca de 1000
pedidos por dia) ou <b>Groq</b> (chave grátis, cerca de 1000 pedidos por dia
por modelo). Põe uma segunda IA como reserva e a app troca quando uma
acabar. Os limites mudam, e cada fornecedor mostra-os no seu site.</li>
<li>☁ <b>AI Clouds</b> (aba no topo desta janela, ou o botão por baixo das chaves): que IAs na nuvem são grátis, os limites e onde criar as chaves.</li>
<li><b>Os dois painéis de IA</b> (chat e voz) são iguais: IA, chave (Testar / Criar chave), nos servidores próprios um <b>Nome</b> à tua escolha e o URL, o modelo com <b>🔍 pesquisa</b>, <b>🆓 Só grátis</b> (os grátis aparecem a <b>verde</b>; ⛔ = recusado pela tua conta, ex.: modelos pagos que bloqueaste), perfil e opções. <b>Pedidos/min</b> mantém cada IA na nuvem abaixo do limite dela. Com IA local as opções só da nuvem ficam escondidas.</li>
</ul>

<h3>3. Ler o chat</h3>
<ul>
<li><b>Língua de origem</b>: <i>Auto</i> deteta cada linha, por isso cada
jogador pode escrever numa língua diferente. <b>Traduzir para</b>: a tua
língua.</li>
<li>Deixa o chat do jogo aberto no canal que queres. A app lê diretamente a
janela do jogo, por isso o overlay pode estar em qualquer sítio e ter
qualquer tamanho. Com alt-tab o overlay esconde-se, mas a leitura e a voz
continuam.</li>
<li>Ao abrires o chat ou mudares de separador, traduz <b>e lê em voz
alta</b> tudo o que ainda não foi lido, por ordem. O que já foi lido
<b>nunca se repete</b>, mesmo depois de fechares e abrires o chat ou de
reabrires a app (até 6 horas).</li>
<li>As tuas mensagens e os PMs que envias («Sender: …») são ignorados.</li>
<li>🔊 A <b>voz neural</b> lê «Nome diz: mensagem». Se houver muitas à
espera, lê um pouco mais depressa para não ficar para trás.</li>
<li><b>Velocidade</b> e <b>Tom</b> da voz (em 🔊 Voz neural): ajusta-os e carrega em <b>▶ Ouvir</b> para ouvires um exemplo antes de começar. O ↺ volta ao padrão.</li>
<li>🔔 <b>Som quando alguém escreve o meu nome</b> (por baixo do nome da personagem): quando uma mensagem tem o teu nome (mesmo com erros do OCR ou escrito em cirílico), toca um alerta. Escolhe o <b>som</b>, quantas vezes toca, ou um <b>texto</b> que a voz diz em vez do som, só para tu ouvires (<code>{name}</code> = quem escreveu) e <b>Repetir a cada X s durante Y s</b> (por defeito a cada 10 s durante 30 s). A tecla de cancelar (Esc) ou começares a ditar param-no. O ▶ deixa-te ouvi-lo.</li>
<li><b>Leituras do chat por minuto</b> (Leitura do chat): quantas vezes a app captura o jogo e lê o chat (20 = predefinido). Menos gasta menos CPU.</li>
</ul>

<h3>4. Falar para o jogo (microfone)</h3>
<ul>
<li>Escolhe <b>Falo em</b> e <b>Escrever em</b>, o microfone e o
<b>atalho</b> (por defeito F11). O 🎤 <b>Testar</b> mostra o nível e o que foi
percebido. Os dispositivos «MME:» costumam funcionar melhor.</li>
<li>Modos: <b>Push-to-talk</b> (grava enquanto seguras a tecla e pára
quando a largas), <b>Toque</b> (um toque ouve até fazeres uma pausa longa) e
<b>Contínuo</b> (um toque liga, outro toque desliga; cada frase é enviada numa
pausa).</li>
<li>Em todos os modos um bip a subir quer dizer que a app está a ouvir e um
bip curto que parou. Enquanto ouve, o overlay mostra <b>● A ouvir</b> a
piscar a vermelho e depois <b>⏳ A traduzir</b>.</li>
<li><b>✋ Confirmar antes de enviar</b> (em 🎤 Microfone ou no menu ⚙ do
overlay): desligado, a app escreve a mensagem e envia-a sozinha. Ligado,
escreve-a no chat do jogo e espera: aparece um botão verde <b>✔ Enviar</b> na
barra do overlay (sempre à vista). Carrega nele, ou outra vez na tecla da
voz, para enviar; <b>✖</b> ou Esc apaga-a. Passados 2 minutos sem resposta o
texto fica no chat, por enviar.</li>
<li>Comandos de voz no início da frase: <b>«reply …»</b> responde ao último
PM, e <b>«muda para o chat guilda / servidor / grupo / mundo / privado»</b>
(em qualquer das línguas) muda o canal no jogo.</li>
<li>As respostas vão na língua da pessoa com quem falas, quando a app a
conhece.</li>
<li>⚠️ A app escreve no chat do jogo e carrega no Enter por ti.</li>
<li><b>Bips</b> (pela saída da voz da app, ou seja, os teus
headphones): bip a subir = fala agora; bip curto = acabou de gravar, a
traduzir; bip a descer = cancelado; bip grave = ainda a tratar do
anterior.</li>
<li><b>Tecla de cancelar</b> (por defeito <b>Esc</b>; podes gravar outra):
pára logo um ditado, esteja a ouvir, a traduzir ou a escrever, e apaga o que
já tinha escrito. Nunca carrega no Enter. Só atua durante um ditado; fora
disso a tecla vai para o jogo como sempre. No modo contínuo descarta só a
frase em curso.</li>
</ul>

<h3>5. O overlay</h3>
<ul>
<li>Arrasta pela barra de cima e muda o tamanho pelas bordas. O 🔒 bloqueia-o:
não se mexe nem muda de tamanho e os cliques passam para o jogo, mas a barra
de cima continua clicável. O <b>Ctrl+Shift+L</b> também bloqueia e
desbloqueia.</li>
<li>Os separadores seguem os canais do jogo, e o overlay muda de separador
quando o jogo muda.</li>
<li>Menu ☰: esconder sozinho após X segundos sem mensagens, visibilidade do
fundo, configurações, voz ligada/desligada, pacotes de línguas, registo,
⚠️ erros, limpar overlay e sair.</li>
<li>O ícone ao lado do relógio do Windows abre as configurações e desbloqueia
o overlay.</li>
<li><b>✕</b> no overlay volta à janela principal; ✕ na janela principal
fecha a app. Podes mudar os dois em <b>⚙ Definições da app</b>.</li>
<li><b>⚙ Definições da app</b> (botão no fundo da janela principal): língua
da app, tema, aparência do overlay, o que faz o ✕, pacotes de idiomas e dispositivos de áudio
(micro com 🎤 Testar e a saída da voz).</li>
<li><b>🔄 Atualizações</b> (em ⚙ Definições da app): ao abrir, a app
verifica o GitHub; se houver uma versão nova o botão ⚙ mostra 🆕. <b>⬇️ Atualizar
agora</b> troca só o código da app (~0,3 MB) e reinicia-a. As tuas definições,
chaves, modelos e o Python da app ficam como estão.</li>
<li><b>💾 Perfis</b> (caixa à direita na janela principal): um perfil
grava tudo o que está dentro dessa caixa (nome da personagem e alerta,
leitura do chat, microfone e teclas, voz que lê) mais a aparência do overlay
e os dispositivos de áudio. Nunca grava a IA: cada painel de IA tem os seus
perfis, por isso aplicar um perfil 💾 mantém a IA que tens.</li>
</ul>

<h3>6. Leitura fiável, velocidade e testes</h3>
<ul>
<li><b>Qualquer resolução</b>: a app encontra o chat sozinha de 720p a 4K. Se o teu chat for maior ou mais pequeno, ou a interface do jogo tiver outra escala, usa <b>🎯 Calibrar</b> (Zona do chat, em Leitura do chat): abre o chat no jogo, arrasta e redimensiona a caixa azul por cima das mensagens e carrega em <b>✔ Confirmar</b> (Enter). A caixa só aparece com o jogo à frente. <b>Usar a zona calibrada</b> liga-a ou desliga-a; a calibração fica guardada.</li>
<li>A leitura e a tradução correm em separado: a app continua a ler o chat enquanto a IA traduz, por isso uma IA lenta já não deixa mensagens subir e perder-se. Mensagens parecidas (o mesmo vendedor a mudar o preço) são todas lidas; a mesma mensagem publicada outra vez não.</li>
<li>Linhas cortadas ao meio em cima ou em baixo do chat esperam até estarem inteiras. Os stickers não são lidos. <b>Os números são sempre lidos em voz alta</b> (“daqui a 5 minutos”, “20k”, “lvl 60”).</li>
<li><b>Jogo no modo de poupança</b> (“Swipe to exit sleep mode”): o chat continua a ser lido. Para escrever a tua mensagem de voz a app acorda o jogo (tecla L) e volta a pô-lo a dormir no fim.</li>
<li><b>Velocidade da IA na barra de cima</b>: ⚡ tempo de cada pedido à IA, ⏱ atraso desde que o chat é lido até a tradução aparecer, ⏳ mensagens à espera, 👁 tempo de cada leitura do chat. Verde = bom, amarelo = lento, vermelho = lento demais; ⚠ = a IA está a falhar. Desliga-se no menu ⚙ (📊).</li>
<li>Menu ⚙ → <b>🪟 Mostrar</b>: barra e chat, só a barra de cima (o chat esconde-se e os cliques vão para o jogo) ou só o chat (sem barra; botão direito para o menu). Em <b>⚙ Configurações da app → aparência do overlay</b>: <b>letra do chat</b>, tamanho da letra e <b>tamanho da barra de cima</b> (tudo na barra cresce junto).</li>
<li><b>📊 Ratings</b> (separador no topo desta janela, ou menu ⚙): as IAs testadas com esta app, com velocidade e qualidade, e <b>🧪 Testar neste PC</b>: escolhe uma IA (com as opções que tem agora: camadas na GPU, contexto…) e carrega em <b>▶ Testar</b>. Mostra a velocidade, os problemas e se corre bem no teu PC; numa IA local também compara placa gráfica e processador.</li>
<li><b>Modo contínuo com auscultadores</b>: com <b>🎧 Continuar a ler o chat no modo contínuo</b> ligado, a voz do chat continua a ler entre as tuas frases e cala-se enquanto falas. Com colunas, desliga-o para o micro nunca ouvir a voz. Em todos os modos, uma mensagem do chat cortada por começares a falar é lida outra vez a seguir.</li>
<li><b>Modelos locais</b>: só o modelo em uso fica na memória da placa gráfica; o anterior sai quando mudas de modelo ou passas para uma IA na nuvem. A voz pode usar outro modelo local diferente do do chat (aí ficam os dois carregados). Tudo é descarregado quando a app fecha, mesmo se rebentar.</li>
<li>⚠️ O <b>Groq · ALLaM 2 7B</b> às vezes responde em árabe: a app volta a traduzir essas linhas, mas um modelo dos 📊 Ratings é melhor.</li>
</ul>

<h3>7. Problemas</h3>
<ul>
<li><b>«À espera da janela do RF Online»</b>: o jogo está minimizado ou
fechado.</li>
<li><b>Não traduz nada</b>: vê em ☰ → ⚠️ Erros. Com uma IA na nuvem, carrega
em <b>Testar</b> para ver a chave, o saldo e o limite diário.</li>
<li><b>429 / rate-limited upstream</b>: esse modelo grátis está ocupado.
Espera uns minutos ou escolhe outro.</li>
<li><b>Limite diário</b>: os 50 pedidos grátis do OpenRouter acabaram.
Renovam às 00:00 UTC. Entretanto podes usar a IA local ou uma segunda
IA.</li>
<li><b>Microfone baixo ou não percebe</b>: usa o 🎤 Testar, escolhe o
dispositivo «MME:» e desliga as melhorias de áudio do Windows (Voice
Clarity).</li>
<li><b>O jogo dá soluços com a IA local</b>: escolhe um modelo mais pequeno
ou <i>Camadas na GPU → só CPU</i>.</li>
<li>O <b>📄 Ver registo</b> abre o registo (pasta <code>logs</code>). O áudio
nunca é gravado.</li>
</ul>

<h3>Privacidade</h3>
<p>As chaves ficam cifradas (DPAPI do Windows) e só a tua conta do Windows as
lê. Com uma IA na nuvem, o texto do chat é enviado a esse fornecedor. Com a
IA local, nada sai do PC. As capturas do jogo e a voz da app ficam só na memória: nada é escrito no disco (nem capturas de ecrã, nem áudio).</p>
"""

MANUAL["es"] = """
<h2>🎮 RF Online Translator — Manual</h2>
<p>Lee el <b>chat de RF Online</b> desde la ventana del juego, traduce cada
mensaje con una IA y lo muestra en una ventana transparente sobre el juego,
separado por canal (Todos, Mundo, Servidor, Grupo, Gremio, Raid, Privado…).
Puede leer cada mensaje en voz alta («<i>Nombre dice: mensaje</i>»). También
puedes <b>hablar en tu idioma</b>: lo traduce y lo escribe en el chat del
juego.<br>Solo mira la pantalla y escribe como un teclado. Nunca lee la
memoria del juego ni el tráfico de red.</p>

<h3>1. Primer inicio</h3>
<p>Lo más rápido: el botón <b>🔊 Guía rápida</b> (abajo en la ventana principal) lee en voz alta los pasos esenciales y muestra dónde pulsar. Se abre solo la primera vez.</p>
<ol>
<li>Necesita Windows 10/11. No hace falta instalar Python: ejecuta
<b>install.bat</b> una vez. Crea <b>RF Translator.exe</b> y pone el Python de
la app en su carpeta <b>python</b> (todo queda dentro de la carpeta de la
app).</li>
<li>Abre <b>RF Translator.exe</b> y acepta el aviso de administrador. El juego
se ejecuta como administrador y Windows solo deja a la app leer y escribir
en él así.</li>
<li>El primer inicio instala lo que falte (paquetes de Python, Tesseract
OCR, paquetes de idiomas, Ollama). Puede tardar unos minutos.</li>
<li>Escribe el <b>nombre de tu personaje</b> para que se ignoren tus
mensajes.</li>
<li>Elige la IA (punto 2) y los idiomas (punto 3) y pulsa <b>▶ Iniciar
traductor</b>.</li>
</ol>

<h3>2. Elegir la IA</h3>
<ul>
<li><b>Local (Ollama, este PC)</b>: gratis, privada y funciona sin internet.
Usa unos 2 GB de la memoria de la tarjeta gráfica. <b>gemma2:2b</b> es rápido
y cabe junto al juego en una tarjeta de 8 GB. Usa 🤗 para descargar otros
modelos (☁ AI Clouds dice cuál cabe en tu PC). Solo hay 1 modelo cargado a la vez, y se descarga al cerrar la app,
incluso si falla.</li>
<li><b>Sin IA</b> (sin clave ni cuenta): <b>🌐 Google Traductor</b>
(en línea, rápido; si Google bloquea unos minutos la app pasa sola a
MyMemory y luego a Argos), <b>📦 Argos</b> (sin conexión en este PC;
descarga ~20 MB y ~150 MB por par de idiomas al pulsar Iniciar) y
<b>📦 NLLB</b> (sin conexión, un modelo de ~630 MB para 200 idiomas). Sin
cuotas ni respuestas raras de la IA, pero no corrigen errores del OCR ni la
jerga del juego como una IA. El panel de voz puede usar otro.</li>
<li><b>Nube (API)</b>: mejor calidad y no gasta memoria gráfica. En el panel de la IA (chat o voz), elige la IA, pega la clave y pulsa
<b>Probar</b>. Cada IA guarda su clave, cifrada con tu cuenta de
Windows.</li>
<li><b>OpenRouter</b>: una clave da acceso a cientos de modelos. Escribe
<code>free</code> en el campo del modelo para ver los gratuitos.
<b>Sin créditos, los modelos gratis solo permiten 50 peticiones al día.</b>
El overlay y el botón Probar muestran cuántas quedan. Con 10 créditos sube
a 1000 al día. Cada petición traduce hasta 6 líneas del chat.<br>
Modelos gratis probados (octubre de 2026):
<code>inclusionai/ling-3.0-flash-sante:free</code> (rápido y correcto) y
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (bueno, ~1 s por petición
con el «pensar» desactivado). Evita <code>nemotron-3.5-lightning</code> (muy
lento y con errores). A veces los modelos gratis están ocupados unos minutos
(«rate-limited upstream»).</li>
<li><b>Servidor propio 1 y 2</b>: cualquier servidor compatible con OpenAI
(OpenRouter, LM Studio, vLLM, otro PC, otros proveedores). Escribe la URL
(p. ej. <code>https://openrouter.ai/api/v1</code> o
<code>http://localhost:1234/v1</code>) y la clave si hace falta. Luego pulsa
Probar y elige el modelo. Con dos puedes tener dos IA en la nube a la
vez.</li>
<li><b>IA de la voz</b>: por defecto es la misma del chat. Puedes elegir otra
(p. ej. un modelo gratis para el chat y uno mejor para tu voz). Pueden
funcionar dos IA en la nube a la vez.</li>
<li><b>Si esta IA falla, usar las otras que tienen clave</b>: si la principal
está caída, sin saldo u ocupada, la app usa otra que esté configurada y
vuelve a la principal a los 2 minutos.</li>
<li><b>Perfil y opciones</b> (un conjunto para la IA del chat y otro
para la IA de la voz): elige un <b>Perfil</b> para rellenar la IA, el modelo
y sus opciones con un clic. Los perfiles ⭐ vienen con la app (✅ = probado
con esta app, 🆓 = plan gratis, no probado aquí). 💾 guarda los tuyos y 🗑
los borra. Opciones: <i>Temperatura</i> (Probada = 0.1 local / 0.2 nube;
<i>La del modelo</i> no envía nada), <i>Pensar</i> (déjalo
<b>Desactivado</b>, que es mucho más rápido), <i>Contexto</i> y
<i>Respuesta máx.</i> (Automático basta; usa 4k–8k en modelos pequeños) y
<i>Líneas por petición</i> (chat en la nube: más líneas = menos
peticiones, lo que ahorra los límites diarios gratis).</li>
<li><b>IA gratis para todo el día</b>: todos los modelos
<code>:free</code> de OpenRouter <b>comparten</b> las mismas 50 peticiones
al día (1000 con 10 créditos). Para jugar todo el día gratis, usa la
<b>Local</b> (sin límite) o una de estas: <b>Mistral</b> (plan gratis
«Experiment», 1 petición por segundo aprox., sin límite diario; perfil
⭐ Mistral · Small), <b>Google Gemini</b> (clave gratis de AI Studio;
Flash-Lite da unas 1000 peticiones al día) o <b>Groq</b> (clave gratis, unas
1000 peticiones al día por modelo). Pon una segunda IA de reserva y la app
cambia cuando una se agote. Los límites cambian, y cada proveedor los
muestra en su web.</li>
<li>☁ <b>AI Clouds</b> (pestaña arriba en esta ventana, o el botón bajo las claves): qué IA en la nube son gratis, sus límites y dónde crear las claves.</li>
<li><b>Los dos paneles de IA</b> (chat y voz) son iguales: IA, clave (Probar / Obtener clave), en los servidores propios un <b>Nombre</b> a tu elección y la URL, el modelo con <b>🔍 búsqueda</b>, <b>🆓 Solo gratis</b> (los gratis salen en <b>verde</b>; ⛔ = rechazado por tu cuenta, p. ej. modelos de pago que bloqueaste), perfil y opciones. <b>Peticiones/min</b> mantiene cada IA en la nube por debajo de su límite. Con IA local se ocultan las opciones solo de la nube.</li>
</ul>

<h3>3. Leer el chat</h3>
<ul>
<li><b>Idioma de origen</b>: <i>Auto</i> detecta cada línea, así cada
jugador puede escribir en un idioma distinto. <b>Traducir a</b>: tu
idioma.</li>
<li>Deja el chat del juego abierto en el canal que quieras. La app lee
directamente la ventana del juego, así que el overlay puede estar en
cualquier sitio y tener cualquier tamaño. Con alt-tab el overlay se oculta,
pero la lectura y la voz siguen.</li>
<li>Al abrir el chat o cambiar de pestaña, traduce <b>y lee en voz alta</b>
todo lo que aún no se leyó, en orden. Lo ya leído <b>nunca se repite</b>,
incluso después de cerrar y abrir el chat o de reiniciar la app (hasta 6
horas).</li>
<li>Tus mensajes y los privados que envías («Sender: …») se ignoran.</li>
<li>🔊 La <b>voz neuronal</b> lee «Nombre dice: mensaje». Si hay muchos en
espera, lee un poco más rápido para no quedarse atrás.</li>
<li><b>Velocidad</b> y <b>Tono</b> de la voz (en 🔊 Voz neuronal): ajústalos y pulsa <b>▶ Escuchar</b> para oír un ejemplo antes de empezar. ↺ vuelve al valor por defecto.</li>
<li>🔔 <b>Sonido cuando alguien escribe mi nombre</b> (bajo el nombre del personaje): cuando un mensaje contiene tu nombre (incluso con errores del OCR o escrito en cirílico), suena un aviso. Elige el <b>sonido</b>, cuántas veces suena, o un <b>texto</b> que la voz dice en lugar del sonido, solo para que lo oigas (<code>{name}</code> = quién lo escribió) y <b>Repetir cada X s durante Y s</b> (por defecto cada 10 s durante 30 s). La tecla de cancelar (Esc) o empezar a dictar lo detienen. ▶ te deja oírlo.</li>
<li><b>Lecturas del chat por minuto</b> (Lectura del chat): cuántas veces la app captura el juego y lee el chat (20 = predeterminado). Menos gasta menos CPU.</li>
</ul>

<h3>4. Hablar al juego (micrófono)</h3>
<ul>
<li>Elige <b>Hablo en</b> y <b>Escribir en</b>, el micrófono y la
<b>tecla</b> (por defecto F11). 🎤 <b>Probar</b> muestra el nivel y lo que se
entendió. Los dispositivos «MME:» suelen funcionar mejor.</li>
<li>Modos: <b>Pulsar para hablar</b> (graba mientras mantienes la tecla y
para al soltarla), <b>Toque</b> (una pulsación escucha hasta que haces una
pausa larga) y <b>Continuo</b> (una pulsación lo activa, otra lo desactiva;
cada frase se envía en una pausa).</li>
<li>En todos los modos un pitido ascendente indica que la app escucha y un
pitido corto que ha parado. Mientras escucha, el overlay muestra
<b>● Escuchando</b> parpadeando en rojo y luego <b>⏳ Traduciendo</b>.</li>
<li><b>✋ Confirmar antes de enviar</b> (en 🎤 Micrófono o en el menú ⚙
del overlay): desactivado, la app escribe el mensaje y lo envía sola.
Activado, lo escribe en el chat del juego y espera: aparece un botón verde
<b>✔ Enviar</b> en la barra del overlay (siempre visible). Púlsalo, o otra vez
la tecla de voz, para enviar; <b>✖</b> o Esc lo borra. Tras 2 minutos sin
respuesta el texto queda en el chat, sin enviar.</li>
<li>Comandos de voz al inicio de la frase: <b>«reply …»</b> responde al
último privado, y <b>«cambia al chat gremio / servidor / grupo / mundo /
privado»</b> (en cualquiera de los idiomas) cambia el canal del juego.</li>
<li>Las respuestas van en el idioma de la persona con la que hablas, cuando la
app lo conoce.</li>
<li>⚠️ La app escribe en el chat del juego y pulsa Enter por ti.</li>
<li><b>Pitidos</b> (por la salida de voz de la app, es decir, tus
auriculares): pitido que sube = habla ahora; pitido corto = terminó de
grabar, traduciendo; pitido que baja = cancelado; pitido grave = aún con el
anterior.</li>
<li><b>Tecla de cancelar</b> (por defecto <b>Esc</b>; puedes grabar otra):
detiene un dictado al momento, esté escuchando, traduciendo o escribiendo, y
borra lo ya escrito. Nunca pulsa Enter. Solo actúa durante un dictado; si no,
la tecla llega al juego como siempre. En modo continuo descarta solo la frase
en curso.</li>
</ul>

<h3>5. El overlay</h3>
<ul>
<li>Arrástralo por la barra superior y cambia su tamaño por los bordes.
🔒 lo bloquea: no se mueve ni cambia de tamaño y los clics pasan al juego,
pero la barra superior sigue siendo clicable. <b>Ctrl+Shift+L</b> también lo
bloquea y desbloquea.</li>
<li>Las pestañas siguen los canales del juego, y el overlay cambia de pestaña
cuando cambia el juego.</li>
<li>Menú ☰: ocultar solo tras X segundos sin mensajes, visibilidad del
fondo, configuración, voz sí/no, paquetes de idiomas, registro, ⚠️ errores,
limpiar overlay y salir.</li>
<li>El icono junto al reloj de Windows abre la configuración y desbloquea el
overlay.</li>
<li><b>✕</b> en el overlay vuelve a la ventana principal; ✕ en la ventana
principal cierra la app. Puedes cambiar ambos en <b>⚙ Ajustes de la
app</b>.</li>
<li><b>⚙ Ajustes de la app</b> (botón abajo en la ventana principal): idioma
de la app, tema, apariencia del overlay, qué hace ✕, paquetes de idiomas y dispositivos de audio
(micrófono con 🎤 Probar y la salida de voz).</li>
<li><b>🔄 Actualizaciones</b> (en ⚙ Ajustes de la app): al abrirse, la
app comprueba GitHub; si hay una versión nueva el botón ⚙ muestra 🆕.
<b>⬇️ Actualizar ahora</b> cambia solo el código de la app (~0,3 MB) y la
reinicia. Tus ajustes, claves, modelos y el Python de la app se quedan igual.</li>
<li><b>💾 Perfiles</b> (recuadro a la derecha de la ventana principal):
un perfil guarda todo lo que hay en ese recuadro (nombre del personaje y
aviso, lectura del chat, micrófono y teclas, voz lectora) más la apariencia
del overlay y los dispositivos de audio. Nunca guarda la IA: cada panel de IA
tiene sus propios perfiles, así que aplicar un perfil 💾 mantiene tu IA.</li>
</ul>

<h3>6. Lectura fiable, velocidad y pruebas</h3>
<ul>
<li><b>Cualquier resolución</b>: la app encuentra el chat sola de 720p a 4K. Si tu chat es más grande o más pequeño, o la interfaz del juego tiene otra escala, usa <b>🎯 Calibrar</b> (Zona del chat, en Lectura del chat): abre el chat en el juego, arrastra y cambia el tamaño del cuadro azul sobre los mensajes y pulsa <b>✔ Confirmar</b> (Enter). El cuadro solo aparece con el juego delante. <b>Usar la zona calibrada</b> la activa o desactiva; la calibración queda guardada.</li>
<li>La lectura y la traducción van por separado: la app sigue leyendo el chat mientras la IA traduce, así que una IA lenta ya no deja que los mensajes suban y se pierdan. Los mensajes parecidos (el mismo vendedor cambiando el precio) se leen todos; el mismo mensaje publicado otra vez no.</li>
<li>Las líneas cortadas por la mitad arriba o abajo del chat esperan hasta verse enteras. Los stickers no se leen. <b>Los números siempre se leen en voz alta</b> («en 5 minutos», «20k», «lvl 60»).</li>
<li><b>Juego en modo ahorro</b> («Swipe to exit sleep mode»): el chat se sigue leyendo. Para escribir tu mensaje de voz la app despierta el juego (tecla L) y lo vuelve a dormir al final.</li>
<li><b>Velocidad de la IA en la barra superior</b>: ⚡ tiempo de cada petición a la IA, ⏱ retraso desde que se lee el chat hasta que aparece la traducción, ⏳ mensajes esperando, 👁 tiempo de cada lectura del chat. Verde = bien, amarillo = lento, rojo = demasiado lento; ⚠ = la IA está fallando. Se desactiva en el menú ⚙ (📊).</li>
<li>Menú ⚙ → <b>🪟 Mostrar</b>: barra y chat, solo la barra superior (el chat se oculta y los clics van al juego) o solo el chat (sin barra; clic derecho para el menú). En <b>⚙ Ajustes de la app → apariencia del overlay</b>: <b>fuente del chat</b>, tamaño de letra y <b>tamaño de la barra superior</b> (todo en la barra crece junto).</li>
<li><b>📊 Ratings</b> (pestaña arriba en esta ventana, o menú ⚙): las IA probadas con esta app, con velocidad y calidad, y <b>🧪 Probar en este PC</b>: elige una IA (con las opciones que tiene ahora: capas en la GPU, contexto…) y pulsa <b>▶ Probar</b>. Muestra la velocidad, los problemas y si funciona bien en tu PC; con una IA local también compara tarjeta gráfica y procesador.</li>
<li><b>Modo continuo con auriculares</b>: con <b>🎧 Seguir leyendo el chat en modo continuo</b> activado, la voz del chat sigue leyendo entre tus frases y se calla mientras hablas. Con altavoces, desactívalo para que el micro nunca oiga la voz. En todos los modos, un mensaje del chat cortado porque empezaste a hablar se vuelve a leer después.</li>
<li><b>Modelos locales</b>: solo el modelo en uso se queda en la memoria de la tarjeta gráfica; el anterior sale cuando cambias de modelo o pasas a una IA en la nube. La voz puede usar otro modelo local distinto del del chat (entonces se quedan los dos cargados). Todo se descarga al cerrar la app, incluso si falla.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> a veces responde en árabe: la app vuelve a traducir esas líneas, pero un modelo de 📊 Ratings es mejor.</li>
</ul>

<h3>7. Problemas</h3>
<ul>
<li><b>«Esperando la ventana de RF Online»</b>: el juego está minimizado o
cerrado.</li>
<li><b>No traduce nada</b>: mira en ☰ → ⚠️ Errores. Con una IA en la nube,
pulsa <b>Probar</b> para revisar la clave, el saldo y el límite
diario.</li>
<li><b>429 / rate-limited upstream</b>: ese modelo gratis está ocupado.
Espera unos minutos o elige otro.</li>
<li><b>Límite diario</b>: se acabaron las 50 peticiones gratis de OpenRouter.
Se renuevan a las 00:00 UTC. Mientras tanto puedes usar la IA local o una
segunda IA.</li>
<li><b>Micrófono bajo o no entiende</b>: usa 🎤 Probar, elige el dispositivo
«MME:» y desactiva las mejoras de audio de Windows (Voice Clarity).</li>
<li><b>El juego da tirones con la IA local</b>: elige un modelo más pequeño o
<i>Capas en GPU → solo CPU</i>.</li>
<li><b>📄 Ver registro</b> abre el registro (carpeta <code>logs</code>). El
audio nunca se guarda.</li>
</ul>

<h3>Privacidad</h3>
<p>Las claves se guardan cifradas (DPAPI de Windows) y solo tu cuenta de
Windows puede leerlas. Con una IA en la nube, el texto del chat se envía a ese
proveedor. Con la IA local, nada sale del PC. Las capturas del juego y la voz de la app solo están en memoria: no se escribe nada en el disco (ni capturas, ni audio).</p>
"""

MANUAL["fr"] = """
<h2>🎮 RF Online Translator — Manuel</h2>
<p>Lit le <b>chat de RF Online</b> depuis la fenêtre du jeu, traduit chaque
message avec une IA et l'affiche dans une fenêtre transparente au-dessus du
jeu, séparé par canal (Tous, Monde, Serveur, Groupe, Guilde, Raid, Privé…).
Il peut lire chaque message à voix haute (« <i>Nom dit : message</i> »).
Tu peux aussi <b>parler dans ta langue</b> : l'app traduit et l'écrit dans
le chat du jeu.<br>Elle regarde seulement l'écran et tape comme un clavier.
Elle ne lit jamais la mémoire du jeu ni le trafic réseau.</p>

<h3>1. Premier lancement</h3>
<p>Le plus rapide : le bouton <b>🔊 Guide rapide</b> (en bas de la fenêtre principale) lit à voix haute les étapes essentielles et montre où cliquer. Il s'ouvre tout seul la première fois.</p>
<ol>
<li>Il faut Windows 10/11. Pas besoin d'installer Python : lance
<b>install.bat</b> une fois. Il crée <b>RF Translator.exe</b> et met le Python
de l'app dans son dossier <b>python</b> (tout reste dans le dossier de
l'app).</li>
<li>Ouvre <b>RF Translator.exe</b> et accepte la demande administrateur. Le
jeu tourne en administrateur et Windows ne laisse l'app lire et écrire dedans
que comme ça.</li>
<li>Le premier lancement installe ce qui manque (paquets Python, Tesseract
OCR, packs de langues, Ollama). Cela peut prendre quelques minutes.</li>
<li>Écris le <b>nom de ton personnage</b> pour que tes propres messages
soient ignorés.</li>
<li>Choisis l'IA (point 2) et les langues (point 3), puis clique sur
<b>▶ Démarrer le traducteur</b>.</li>
</ol>

<h3>2. Choisir l'IA</h3>
<ul>
<li><b>Local (Ollama, ce PC)</b> : gratuit, privé et fonctionne sans
internet. Utilise environ 2 Go de mémoire de la carte graphique.
<b>gemma2:2b</b> est rapide et tient à côté du jeu sur une carte de 8 Go.
Utilise 🤗 pour télécharger d'autres modèles (☁ AI Clouds dit lequel convient à ton PC). Un seul modèle est chargé à la
fois, et il est déchargé à la fermeture de l'app, même après un plantage.</li>
<li><b>Sans IA</b> (sans clé ni compte) : <b>🌐 Google Traduction</b>
(en ligne, rapide ; si Google bloque quelques minutes, l'app passe seule à
MyMemory puis à Argos), <b>📦 Argos</b> (hors ligne sur ce PC ; télécharge
~20 Mo plus ~150 Mo par paire de langues quand tu cliques sur Démarrer) et
<b>📦 NLLB</b> (hors ligne, un modèle de ~630 Mo pour 200 langues). Pas de
quotas ni de réponses bizarres d'IA, mais ils ne corrigent pas les erreurs
d'OCR ni l'argot du jeu comme une IA. Le panneau de la voix peut en utiliser
un autre.</li>
<li><b>Cloud (API)</b> : meilleure qualité, sans mémoire graphique. Dans le panneau de l'IA (chat ou voix), choisis l'IA, colle sa clé et clique sur
<b>Tester</b>. Chaque IA garde sa clé, chiffrée avec ton compte
Windows.</li>
<li><b>OpenRouter</b> : une clé donne accès à des centaines de modèles. Tape
<code>free</code> dans le champ du modèle pour voir les gratuits.
<b>Sans crédits, les modèles gratuits ne permettent que 50 requêtes par
jour.</b> L'overlay et le bouton Tester affichent combien il en reste. Avec
10 crédits, on passe à 1000 par jour. Une requête traduit jusqu'à 6 lignes
du chat.<br>
Modèles gratuits testés (octobre 2026) :
<code>inclusionai/ling-3.0-flash-sante:free</code> (rapide et correct) et
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (bon, ~1 s par requête
avec la « réflexion » désactivée). Évite <code>nemotron-3.5-lightning</code>
(très lent, résultats faux). Les modèles gratuits sont parfois occupés
quelques minutes (« rate-limited upstream »).</li>
<li><b>Serveur perso 1 et 2</b> : tout serveur compatible OpenAI
(OpenRouter, LM Studio, vLLM, un autre PC, d'autres fournisseurs). Écris
l'URL (ex. <code>https://openrouter.ai/api/v1</code> ou
<code>http://localhost:1234/v1</code>) et la clé si besoin. Clique ensuite
sur Tester et choisis le modèle. Avec deux serveurs, tu peux faire tourner
deux IA cloud en même temps.</li>
<li><b>IA de la voix</b> : par défaut c'est celle du chat. Tu peux en choisir
une autre (ex. un modèle gratuit pour le chat et un meilleur pour ta voix).
Deux IA cloud peuvent tourner en même temps.</li>
<li><b>Si cette IA échoue, utiliser les autres qui ont une clé</b> : si l'IA
principale est en panne, sans crédit ou occupée, l'app passe à une autre IA
configurée et revient à la principale après 2 minutes.</li>
<li><b>Profil et options</b> (un jeu pour l'IA du chat et un pour l'IA
de la voix) : choisis un <b>Profil</b> pour remplir l'IA, le modèle et ses
options en un clic. Les profils ⭐ sont fournis avec l'app (✅ = testé avec
cette app, 🆓 = offre gratuite, non testée ici). 💾 enregistre les tiens et
🗑 les supprime. Options : <i>Température</i> (Testée = 0.1 local / 0.2
cloud ; <i>Celle du modèle</i> n'envoie rien), <i>Réflexion</i> (laisse
<b>Désactivé</b>, c'est beaucoup plus rapide), <i>Contexte</i> et
<i>Réponse max.</i> (Automatique suffit ; 4k–8k pour les petits modèles)
et <i>Lignes par requête</i> (chat cloud : plus de lignes = moins de
requêtes, ce qui économise les limites quotidiennes gratuites).</li>
<li><b>IA gratuites toute la journée</b> : tous les modèles
<code>:free</code> d'OpenRouter <b>partagent</b> les mêmes 50 requêtes par
jour (1000 avec 10 crédits). Pour jouer toute la journée gratuitement,
utilise l'IA <b>Locale</b> (sans limite) ou l'une de celles-ci :
<b>Mistral</b> (offre gratuite « Experiment », environ 1 requête par
seconde, sans limite quotidienne ; profil ⭐ Mistral · Small), <b>Google
Gemini</b> (clé gratuite d'AI Studio ; Flash-Lite permet environ 1000
requêtes par jour) ou <b>Groq</b> (clé gratuite, environ 1000 requêtes par
jour et par modèle). Ajoute une deuxième IA en secours : l'app bascule quand
l'une est épuisée. Les limites changent, et chaque fournisseur les affiche
sur son site.</li>
<li>☁ <b>AI Clouds</b> (onglet en haut de cette fenêtre, ou le bouton sous les clés) : quelles IA cloud sont gratuites, leurs limites et où créer les clés.</li>
<li><b>Les deux panneaux d'IA</b> (chat et voix) sont identiques : IA, clé (Tester / Obtenir une clé), pour les serveurs perso un <b>Nom</b> au choix et l'URL, le modèle avec <b>🔍 recherche</b>, <b>🆓 Gratuits seulement</b> (les gratuits sont en <b>vert</b> ; ⛔ = refusé par ton compte, ex. modèles payants que tu as bloqués), profil et options. <b>Requêtes/min</b> garde chaque IA cloud sous sa limite. Avec une IA locale, les options cloud sont masquées.</li>
</ul>

<h3>3. Lire le chat</h3>
<ul>
<li><b>Langue source</b> : <i>Auto</i> détecte chaque ligne, donc chaque
joueur peut écrire dans une langue différente. <b>Traduire en</b> : ta
langue.</li>
<li>Garde le chat du jeu ouvert sur le canal voulu. L'app lit directement la
fenêtre du jeu, donc l'overlay peut être n'importe où et de n'importe quelle
taille. Avec alt-tab, l'overlay se cache mais la lecture et la voix
continuent.</li>
<li>Quand tu ouvres le chat ou changes d'onglet, l'app traduit <b>et lit à
voix haute</b> tout ce qui n'a pas encore été lu, dans l'ordre. Ce qui a déjà
été lu <b>n'est jamais répété</b>, même après avoir fermé et rouvert le chat
ou relancé l'app (jusqu'à 6 heures).</li>
<li>Tes messages et les MP que tu envoies (« Sender: … ») sont
ignorés.</li>
<li>🔊 La <b>voix neuronale</b> lit « Nom dit : message ». S'il y en a beaucoup
en attente, elle lit un peu plus vite pour ne pas prendre de retard.</li>
<li><b>Vitesse</b> et <b>Ton</b> de la voix (dans 🔊 Voix neuronale) : règle-les et clique sur <b>▶ Écouter</b> pour entendre un exemple avant de commencer. ↺ remet la valeur par défaut.</li>
<li>🔔 <b>Son quand quelqu'un écrit mon nom</b> (sous le nom du personnage) : quand un message contient ton nom (même avec des erreurs d'OCR ou écrit en cyrillique), une alerte retentit. Choisis le <b>son</b>, combien de fois il joue, ou un <b>texte</b> que la voix dit à la place du son, rien que pour toi (<code>{name}</code> = qui l'a écrit) et <b>Répéter toutes les X s pendant Y s</b> (par défaut toutes les 10 s pendant 30 s). La touche d'annulation (Échap) ou une dictée l'arrêtent. ▶ permet de l'écouter.</li>
<li><b>Lectures du chat par minute</b> (Lecture du chat) : combien de fois l'app capture le jeu et lit le chat (20 = par défaut). Moins = moins de CPU.</li>
</ul>

<h3>4. Parler au jeu (micro)</h3>
<ul>
<li>Choisis <b>Je parle</b> et <b>Écrire en</b>, le micro et le
<b>raccourci</b> (F11 par défaut). 🎤 <b>Tester</b> montre le niveau et ce qui
a été compris. Les périphériques « MME: » marchent souvent mieux.</li>
<li>Modes : <b>Appuyer pour parler</b> (enregistre tant que tu maintiens la
touche et s'arrête quand tu la relâches), <b>Appui</b> (un appui écoute
jusqu'à une longue pause) et <b>Continu</b> (un appui l'active, un autre le
désactive ; chaque phrase est envoyée à chaque pause).</li>
<li>Dans tous les modes, un bip montant indique que l'app écoute et un bip
court qu'elle s'est arrêtée. Pendant l'écoute, l'overlay affiche
<b>● Écoute</b> qui clignote en rouge, puis <b>⏳ Traduction</b>.</li>
<li><b>✋ Confirmer avant d'envoyer</b> (dans 🎤 Micro ou dans le menu ⚙
de l'overlay) : désactivé, l'app écrit le message et l'envoie toute seule.
Activé, elle l'écrit dans le chat du jeu et attend : un bouton vert
<b>✔ Envoyer</b> apparaît dans la barre de l'overlay (toujours visible).
Appuie dessus, ou à nouveau sur la touche de voix, pour envoyer ; <b>✖</b> ou
Échap l'efface. Après 2 minutes sans réponse le texte reste dans le chat, non
envoyé.</li>
<li>Commandes vocales en début de phrase : <b>« reply … »</b> répond au
dernier MP, et <b>« passe au chat guilde / serveur / groupe / monde /
privé »</b> (dans n'importe quelle langue de l'app) change le canal du
jeu.</li>
<li>Les réponses partent dans la langue de ton interlocuteur, quand l'app la
connaît.</li>
<li>⚠️ L'app écrit dans le chat du jeu et appuie sur Entrée pour toi.</li>
<li><b>Bips</b> (par la sortie voix de l'app, c'est-à-dire ton
casque) : bip montant = parle ; bip court = enregistrement fini, traduction
en cours ; bip descendant = annulé ; bip grave = encore occupé avec la
précédente.</li>
<li><b>Touche d'annulation</b> (<b>Échap</b> par défaut ; tu peux en
enregistrer une autre) : arrête aussitôt une dictée, qu'elle écoute,
traduise ou écrive, et efface ce qui était déjà écrit. N'appuie jamais sur
Entrée. N'agit que pendant une dictée ; sinon la touche va au jeu comme
d'habitude. En mode continu, elle n'annule que la phrase en cours.</li>
</ul>

<h3>5. L'overlay</h3>
<ul>
<li>Fais-le glisser par la barre du haut et redimensionne-le par les bords.
🔒 le verrouille : il ne bouge plus, ne change plus de taille et les clics
passent au jeu, mais la barre du haut reste cliquable. <b>Ctrl+Shift+L</b>
le verrouille et le déverrouille aussi.</li>
<li>Les onglets suivent les canaux du jeu, et l'overlay change d'onglet quand
le jeu change.</li>
<li>Menu ☰ : masquage auto après X secondes sans message, visibilité du
fond, paramètres, voix oui/non, packs de langues, journal, ⚠️ erreurs, vider
l'overlay et quitter.</li>
<li>L'icône près de l'horloge de Windows ouvre les paramètres et déverrouille
l'overlay.</li>
<li><b>✕</b> sur l'overlay revient à la fenêtre principale ; ✕ sur la
fenêtre principale ferme l'app. Les deux se changent dans <b>⚙ Paramètres de
l'app</b>.</li>
<li><b>⚙ Paramètres de l'app</b> (bouton en bas de la fenêtre principale) :
langue de l'app, thème, apparence de l'overlay, action de ✕, packs de langues et périphériques audio
(micro avec 🎤 Tester et la sortie de la voix).</li>
<li><b>🔄 Mises à jour</b> (dans ⚙ Paramètres de l'app) : à l'ouverture,
l'app vérifie GitHub ; s'il y a une nouvelle version, le bouton ⚙ affiche 🆕.
<b>⬇️ Mettre à jour</b> remplace seulement le code de l'app (~0,3 Mo) et la
redémarre. Tes réglages, clés, modèles et le Python de l'app ne changent pas.</li>
<li><b>💾 Profils</b> (cadre à droite de la fenêtre principale) : un
profil enregistre tout ce qui est dans ce cadre (nom du personnage et alerte,
lecture du chat, micro et touches, voix de lecture) plus l'apparence de
l'overlay et les périphériques audio. Il n'enregistre jamais l'IA : chaque
panneau d'IA a ses propres profils, donc appliquer un profil 💾 garde ton
IA.</li>
</ul>

<h3>6. Lecture fiable, vitesse et tests</h3>
<ul>
<li><b>Toutes les résolutions</b> : l'app trouve le chat toute seule de 720p à 4K. Si ton chat est plus grand ou plus petit, ou si l'interface du jeu a une autre échelle, utilise <b>🎯 Calibrer</b> (Zone du chat, dans Lecture du chat) : ouvre le chat dans le jeu, déplace et redimensionne le cadre bleu sur les messages et appuie sur <b>✔ Confirmer</b> (Entrée). Le cadre n'apparaît que quand le jeu est devant. <b>Utiliser la zone calibrée</b> l'active ou la désactive ; la calibration reste enregistrée.</li>
<li>La lecture et la traduction tournent séparément : l'app continue de lire le chat pendant que l'IA traduit, donc une IA lente ne laisse plus les messages défiler sans être lus. Les messages qui se ressemblent (le même vendeur qui change le prix) sont tous lus ; le même message republié ne l'est pas.</li>
<li>Les lignes coupées en haut ou en bas du chat attendent d'être entièrement visibles. Les stickers ne sont pas lus. <b>Les nombres sont toujours lus à voix haute</b> (« dans 5 minutes », « 20k », « lvl 60 »).</li>
<li><b>Jeu en mode veille</b> (« Swipe to exit sleep mode ») : le chat est toujours lu. Pour écrire ton message vocal, l'app réveille le jeu (touche L) et le remet en veille ensuite.</li>
<li><b>Vitesse de l'IA dans la barre du haut</b> : ⚡ temps de chaque requête à l'IA, ⏱ délai entre la lecture du chat et l'affichage de la traduction, ⏳ messages en attente, 👁 temps de chaque lecture du chat. Vert = bien, jaune = lent, rouge = trop lent ; ⚠ = l'IA échoue. Se désactive dans le menu ⚙ (📊).</li>
<li>Menu ⚙ → <b>🪟 Afficher</b> : barre et chat, seulement la barre du haut (le chat se cache et les clics vont au jeu) ou seulement le chat (sans barre ; clic droit pour le menu). Dans <b>⚙ Réglages de l'app → apparence de l'overlay</b> : <b>police du chat</b>, taille du texte et <b>taille de la barre du haut</b> (tout dans la barre grandit ensemble).</li>
<li><b>📊 Ratings</b> (onglet en haut de cette fenêtre, ou menu ⚙) : les IA testées avec cette app, avec vitesse et qualité, et <b>🧪 Tester sur ce PC</b> : choisis une IA (avec ses options actuelles : couches GPU, contexte…) et appuie sur <b>▶ Tester</b>. Elle montre la vitesse, les problèmes et si elle fonctionne bien sur ton PC ; pour une IA locale elle compare aussi carte graphique et processeur.</li>
<li><b>Mode continu avec un casque</b> : avec <b>🎧 Continuer à lire le chat en mode continu</b> activé, la voix du chat continue de lire entre tes phrases et se tait quand tu parles. Avec des haut-parleurs, désactive-le pour que le micro n'entende jamais la voix. Dans tous les modes, un message du chat coupé parce que tu as commencé à parler est relu ensuite.</li>
<li><b>Modèles locaux</b> : seul le modèle utilisé reste dans la mémoire de la carte graphique ; le précédent sort quand tu changes de modèle ou passes à une IA cloud. La voix peut utiliser un autre modèle local que le chat (les deux restent alors chargés). Tout est déchargé à la fermeture de l'app, même après un plantage.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> répond parfois en arabe : l'app retraduit ces lignes, mais un modèle des 📊 Ratings est préférable.</li>
</ul>

<h3>7. Problèmes</h3>
<ul>
<li><b>« En attente de la fenêtre de RF Online »</b> : le jeu est réduit ou
fermé.</li>
<li><b>Rien n'est traduit</b> : regarde ☰ → ⚠️ Erreurs. Avec une IA cloud,
clique sur <b>Tester</b> pour vérifier la clé, le crédit et la limite
quotidienne.</li>
<li><b>429 / rate-limited upstream</b> : ce modèle gratuit est occupé.
Attends quelques minutes ou choisis-en un autre.</li>
<li><b>Limite quotidienne</b> : les 50 requêtes gratuites OpenRouter sont
épuisées. Elles reviennent à 00:00 UTC. En attendant, tu peux utiliser l'IA
locale ou une deuxième IA.</li>
<li><b>Micro trop faible ou mal compris</b> : utilise 🎤 Tester, choisis le
périphérique « MME: » et désactive les améliorations audio de Windows (Voice
Clarity).</li>
<li><b>Le jeu saccade avec l'IA locale</b> : choisis un modèle plus petit ou
<i>Couches GPU → CPU seulement</i>.</li>
<li><b>📄 Voir le journal</b> ouvre le journal (dossier <code>logs</code>).
L'audio n'est jamais enregistré.</li>
</ul>

<h3>Confidentialité</h3>
<p>Les clés sont chiffrées (DPAPI de Windows) et seul ton compte Windows peut
les lire. Avec une IA cloud, le texte du chat est envoyé à ce fournisseur.
Avec l'IA locale, rien ne quitte le PC. Les captures du jeu et la voix de l'app restent en mémoire : rien n'est écrit sur le disque (ni captures d'écran, ni audio).</p>
"""

MANUAL["de"] = """
<h2>🎮 RF Online Translator — Anleitung</h2>
<p>Liest den <b>RF-Online-Chat</b> aus dem Spielfenster, übersetzt jede
Nachricht mit einer KI und zeigt sie in einem transparenten Fenster über dem
Spiel an, nach Kanal getrennt (Alle, Welt, Server, Gruppe, Gilde, Raid,
Flüstern…). Jede Nachricht kann vorgelesen werden („<i>Name sagt:
Nachricht</i>“). Du kannst auch <b>in deiner Sprache sprechen</b>: die App
übersetzt und tippt es in den Spielchat.<br>Sie schaut nur auf den Bildschirm
und tippt wie eine Tastatur. Sie liest nie den Spielspeicher oder den
Netzwerkverkehr.</p>

<h3>1. Erster Start</h3>
<p>Am schnellsten: Der Knopf <b>🔊 Schnellstart</b> (unten im Hauptfenster) liest die wichtigsten Schritte vor und zeigt, wo du klicken musst. Er öffnet sich beim ersten Start von selbst.</p>
<ol>
<li>Benötigt Windows 10/11. Python musst du nicht installieren: starte
einmal <b>install.bat</b>. Es erstellt <b>RF Translator.exe</b> und legt das
eigene Python der App in den Ordner <b>python</b> (alles bleibt im
App-Ordner).</li>
<li>Öffne <b>RF Translator.exe</b> und bestätige die Administrator-Abfrage.
Das Spiel läuft als Administrator, und nur so lässt Windows die App darin
lesen und tippen.</li>
<li>Beim ersten Start wird installiert, was fehlt (Python-Pakete, Tesseract
OCR, Sprachpakete, Ollama). Das kann ein paar Minuten dauern.</li>
<li>Trage deinen <b>Charakternamen</b> ein, damit deine eigenen Nachrichten
ignoriert werden.</li>
<li>Wähle die KI (Punkt 2) und die Sprachen (Punkt 3) und drücke
<b>▶ Übersetzer starten</b>.</li>
</ol>

<h3>2. KI wählen</h3>
<ul>
<li><b>Lokal (Ollama, dieser PC)</b>: kostenlos, privat und ohne Internet
nutzbar. Braucht etwa 2 GB Grafikspeicher. <b>gemma2:2b</b> ist schnell und
passt neben dem Spiel auf eine 8-GB-Karte. Mit 🤗 lädst du andere Modelle (☁ AI Clouds sagt, welches zu deinem PC passt).
Es ist immer nur 1 Modell geladen, und es wird beim Schließen der App
entladen, auch nach einem Absturz.</li>
<li><b>Ohne KI</b> (ohne Schlüssel und Konto): <b>🌐 Google
Übersetzer</b> (online, schnell; blockiert Google ein paar Minuten, wechselt
die App selbst zu MyMemory und dann zu Argos), <b>📦 Argos</b> (offline auf
diesem PC; lädt beim Start ~20 MB plus ~150 MB pro Sprachpaar) und
<b>📦 NLLB</b> (offline, ein ~630-MB-Modell für 200 Sprachen). Keine Limits
und keine seltsamen KI-Antworten, aber sie korrigieren weder OCR-Fehler noch
Spieler-Slang wie eine KI. Das Sprach-Panel kann einen anderen nutzen.</li>
<li><b>Cloud (API)</b>: bessere Qualität und kein Grafikspeicher. Im Feld der KI (Chat oder Stimme) die KI wählen, den Schlüssel einfügen und
<b>Testen</b> drücken. Jede KI behält ihren eigenen Schlüssel,
verschlüsselt mit deinem Windows-Konto.</li>
<li><b>OpenRouter</b>: ein Schlüssel gibt Zugriff auf Hunderte Modelle.
<code>free</code> ins Modellfeld tippen, um die kostenlosen zu sehen.
<b>Ohne Credits erlauben die kostenlosen Modelle nur 50 Anfragen pro
Tag.</b> Overlay und Testen-Knopf zeigen, wie viele übrig sind. Mit 10
Credits sind es 1000 pro Tag. Eine Anfrage übersetzt bis zu 6
Chatzeilen.<br>
Getestete kostenlose Modelle (Oktober 2026):
<code>inclusionai/ling-3.0-flash-sante:free</code> (schnell und korrekt) und
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (gut, ~1 s pro Anfrage
mit ausgeschaltetem „Denken“). Meide <code>nemotron-3.5-lightning</code>
(sehr langsam, falsche Ausgabe). Kostenlose Modelle sind manchmal für ein
paar Minuten ausgelastet („rate-limited upstream“).</li>
<li><b>Eigener Server 1 und 2</b>: jeder OpenAI-kompatible Server
(OpenRouter, LM Studio, vLLM, ein anderer PC, andere Anbieter). Trage die
URL ein (z. B. <code>https://openrouter.ai/api/v1</code> oder
<code>http://localhost:1234/v1</code>) und bei Bedarf den Schlüssel. Dann
Testen drücken und das Modell wählen. Mit zwei Servern laufen zwei
Cloud-KIs gleichzeitig.</li>
<li><b>Sprach-KI</b>: standardmäßig dieselbe wie im Chat. Du kannst eine
andere wählen (z. B. ein kostenloses Modell für den Chat und ein besseres für
deine Stimme). Zwei Cloud-KIs können gleichzeitig laufen.</li>
<li><b>Wenn diese KI ausfällt, die anderen mit Schlüssel nutzen</b>: ist die
Haupt-KI down, ohne Guthaben oder ausgelastet, nimmt die App eine andere
eingerichtete KI und kehrt nach 2 Minuten zur Haupt-KI zurück.</li>
<li><b>Profil und Optionen</b> (ein Satz für die Chat-KI und einer
für die Sprach-KI): wähle ein <b>Profil</b>, um KI, Modell und Optionen mit
einem Klick auszufüllen. ⭐-Profile kommen mit der App (✅ = mit dieser App
getestet, 🆓 = kostenloser Plan, hier nicht getestet). 💾 speichert eigene
Profile, 🗑 löscht sie. Optionen: <i>Temperatur</i> (Getestet = 0.1 lokal /
0.2 Cloud; <i>Modell-Standard</i> sendet nichts), <i>Denken</i> (lass es
<b>Aus</b>, das ist viel schneller), <i>Kontext</i> und <i>Antwort
max.</i> (Automatisch reicht; 4k–8k für kleine Modelle) und <i>Zeilen pro
Anfrage</i> (Cloud-Chat: mehr Zeilen = weniger Anfragen, das spart
kostenlose Tageslimits).</li>
<li><b>Kostenlose KIs für den ganzen Tag</b>: alle
<code>:free</code>-Modelle von OpenRouter <b>teilen sich</b> dieselben 50
Anfragen pro Tag (1000 mit 10 Credits). Um den ganzen Tag kostenlos zu
spielen, nutze die <b>lokale</b> KI (ohne Limit) oder eine davon:
<b>Mistral</b> (kostenloser „Experiment“-Plan, etwa 1 Anfrage pro Sekunde,
kein Tageslimit; Profil ⭐ Mistral · Small), <b>Google Gemini</b>
(kostenloser Schlüssel von AI Studio; Flash-Lite erlaubt etwa 1000 Anfragen
pro Tag) oder <b>Groq</b> (kostenloser Schlüssel, etwa 1000 Anfragen pro Tag
und Modell). Richte eine zweite KI als Reserve ein, dann wechselt die App,
wenn eine aufgebraucht ist. Die Limits ändern sich; jeder Anbieter zeigt sie
auf seiner Website.</li>
<li>☁ <b>AI Clouds</b> (Tab oben in diesem Fenster oder der Knopf unter den Schlüsseln): welche Cloud-KIs kostenlos sind, ihre Limits und wo man Schlüssel erstellt.</li>
<li><b>Die zwei KI-Felder</b> (Chat und Stimme) sind gleich: KI, Schlüssel (Testen / Schlüssel holen), bei eigenen Servern ein frei wählbarer <b>Name</b> und die URL, das Modell mit <b>🔍 Suche</b>, <b>🆓 Nur kostenlose</b> (kostenlose sind <b>grün</b>; ⛔ = von deinem Konto abgelehnt, z. B. gesperrte kostenpflichtige Modelle), Profil und Optionen. <b>Anfragen/min</b> hält jede Cloud-KI unter ihrem Limit. Bei lokaler KI sind die Cloud-Optionen ausgeblendet.</li>
</ul>

<h3>3. Chat lesen</h3>
<ul>
<li><b>Ausgangssprache</b>: <i>Auto</i> erkennt jede Zeile, also kann jeder
Spieler in einer anderen Sprache schreiben. <b>Übersetzen nach</b>: deine
Sprache.</li>
<li>Lass den Spielchat im gewünschten Kanal offen. Die App liest das
Spielfenster direkt, darum kann das Overlay überall sein und jede Größe
haben. Bei Alt-Tab verschwindet das Overlay, aber Lesen und Stimme laufen
weiter.</li>
<li>Wenn du den Chat öffnest oder den Tab wechselst, übersetzt die App
<b>und liest vor</b>, was noch nicht gelesen wurde, der Reihe nach. Bereits
Gelesenes wird <b>nie wiederholt</b>, auch nicht nach Schließen und Öffnen
des Chats oder einem Neustart der App (bis zu 6 Stunden).</li>
<li>Deine Nachrichten und von dir gesendete PMs („Sender: …“) werden
ignoriert.</li>
<li>🔊 Die <b>neuronale Stimme</b> liest „Name sagt: Nachricht“. Warten viele
Nachrichten, liest sie etwas schneller, damit sie nicht zurückfällt.</li>
<li><b>Tempo</b> und <b>Tonhöhe</b> der Stimme (unter 🔊 Neuronale Stimme): einstellen und <b>▶ Anhören</b> drücken, um vorher ein Beispiel zu hören. ↺ setzt auf Standard zurück.</li>
<li>🔔 <b>Ton, wenn jemand meinen Namen schreibt</b> (unter dem Charakternamen): enthält eine Nachricht deinen Namen (auch mit OCR-Fehlern oder in Kyrillisch), ertönt ein Alarm. Wähle den <b>Ton</b>, wie oft er spielt, oder einen <b>Text</b>, den die Stimme statt des Tons nur für dich sagt (<code>{name}</code> = wer ihn geschrieben hat), und <b>Wiederholen alle X s für Y s</b> (Standard alle 10 s für 30 s). Die Abbrechen-Taste (Esc) oder ein Diktat stoppt ihn. Mit ▶ kannst du ihn anhören.</li>
<li><b>Chat-Lesungen pro Minute</b> (Chat lesen): wie oft die App das Spiel erfasst und den Chat liest (20 = Standard). Weniger = weniger CPU.</li>
</ul>

<h3>4. Ins Spiel sprechen (Mikrofon)</h3>
<ul>
<li>Wähle <b>Ich spreche</b> und <b>Schreiben auf</b>, das Mikrofon und die
<b>Taste</b> (Standard F11). 🎤 <b>Testen</b> zeigt den Pegel und was
verstanden wurde. Geräte mit „MME:“ funktionieren meist am besten.</li>
<li>Modi: <b>Push-to-Talk</b> (nimmt auf, solange du die Taste hältst, und
stoppt beim Loslassen), <b>Tippen</b> (ein Druck hört zu, bis du eine lange
Pause machst) und <b>Dauerhaft</b> (ein Druck schaltet ein, ein weiterer aus;
jeder Satz wird bei einer Pause gesendet).</li>
<li>In allen Modi bedeutet ein steigender Piepton, dass die App zuhört, und
ein kurzer, dass sie gestoppt hat. Während sie zuhört, zeigt das Overlay ein
rot blinkendes <b>● Hört zu</b>, danach <b>⏳ Übersetze</b>.</li>
<li><b>✋ Vor dem Senden bestätigen</b> (unter 🎤 Mikrofon oder im ⚙-Menü
des Overlays): aus, die App schreibt die Nachricht und sendet sie selbst. An,
sie schreibt sie in den Spiel-Chat und wartet: In der Overlay-Leiste
erscheint ein grüner Knopf <b>✔ Senden</b> (immer sichtbar). Drück ihn oder
nochmal die Sprach-Taste zum Senden; <b>✖</b> oder Esc löscht sie. Nach 2
Minuten ohne Antwort bleibt der Text ungesendet im Chat.</li>
<li>Sprachbefehle am Satzanfang: <b>„reply …“</b> antwortet auf die letzte
PM, und <b>„wechsle zu Chat Gilde / Server / Gruppe / Welt / Flüstern“</b>
(in jeder der Sprachen) wechselt den Kanal im Spiel.</li>
<li>Antworten gehen in der Sprache deines Gegenübers raus, wenn die App sie
kennt.</li>
<li>⚠️ Die App tippt in den Spielchat und drückt Enter für dich.</li>
<li><b>Pieptöne</b> (über die Sprachausgabe der App, also deine
Kopfhörer): steigender Ton = jetzt sprechen; kurzer Ton = Aufnahme fertig,
wird übersetzt; fallender Ton = abgebrochen; tiefer Ton = noch mit dem
vorherigen beschäftigt.</li>
<li><b>Abbrechen-Taste</b> (Standard <b>Esc</b>; du kannst eine andere
aufnehmen): stoppt ein Diktat sofort, egal ob es zuhört, übersetzt oder
tippt, und löscht bereits Getipptes. Enter wird nie gedrückt. Wirkt nur
während eines Diktats; sonst geht die Taste wie gewohnt ans Spiel. Im
Dauermodus verwirft sie nur den aktuellen Satz.</li>
</ul>

<h3>5. Das Overlay</h3>
<ul>
<li>An der oberen Leiste ziehen und an den Rändern die Größe ändern. 🔒 sperrt
es: es bewegt sich nicht, ändert die Größe nicht und Klicks gehen ans Spiel
durch, aber die obere Leiste bleibt klickbar. <b>Strg+Umschalt+L</b> sperrt
und entsperrt es ebenfalls.</li>
<li>Die Tabs folgen den Spielkanälen, und das Overlay wechselt den Tab, wenn
das Spiel wechselt.</li>
<li>Menü ☰: automatisch ausblenden nach X Sekunden ohne Nachricht,
Hintergrund-Sichtbarkeit, Einstellungen, Stimme an/aus, Sprachpakete, Log,
⚠️ Fehler, Overlay leeren und Beenden.</li>
<li>Das Symbol neben der Windows-Uhr öffnet die Einstellungen und entsperrt
das Overlay.</li>
<li><b>✕</b> im Overlay führt zurück zum Hauptfenster; ✕ im Hauptfenster
beendet die App. Beides lässt sich in <b>⚙ App-Einstellungen</b> ändern.</li>
<li><b>⚙ App-Einstellungen</b> (Knopf unten im Hauptfenster): App-Sprache,
Design, Overlay-Aussehen, was ✕ tut, Sprachpakete und Audiogeräte (Mikrofon mit 🎤 Testen und
die Sprachausgabe).</li>
<li><b>🔄 Updates</b> (in ⚙ App-Einstellungen): Beim Öffnen prüft die
App GitHub; gibt es eine neue Version, zeigt der ⚙-Knopf 🆕. <b>⬇️ Jetzt
aktualisieren</b> ersetzt nur den Code der App (~0,3 MB) und startet sie neu.
Deine Einstellungen, Schlüssel, Modelle und das Python der App bleiben.</li>
<li><b>💾 Profile</b> (Rahmen rechts im Hauptfenster): ein Profil
speichert alles in diesem Rahmen (Charaktername und Hinweis, Chat lesen,
Mikrofon und Tasten, Vorlesestimme) sowie das Overlay-Aussehen und die
Audiogeräte. Die KI speichert es nie: Jedes KI-Feld hat eigene Profile, ein
💾-Profil anzuwenden behält also deine KI.</li>
</ul>

<h3>6. Zuverlässiges Lesen, Tempo und Tests</h3>
<ul>
<li><b>Jede Auflösung</b>: Die App findet den Chat selbst, von 720p bis 4K. Ist dein Chat größer oder kleiner oder hat die Spieloberfläche eine andere Skalierung, nutze <b>🎯 Kalibrieren</b> (Chat-Bereich, unter Chat lesen): Öffne den Chat im Spiel, ziehe den blauen Rahmen über die Nachrichten, passe die Größe an und drücke <b>✔ Bestätigen</b> (Enter). Der Rahmen ist nur sichtbar, wenn das Spiel vorne ist. <b>Kalibrierten Bereich verwenden</b> schaltet ihn ein oder aus; die Kalibrierung bleibt gespeichert.</li>
<li>Lesen und Übersetzen laufen getrennt: Die App liest den Chat weiter, während die KI übersetzt, so lässt eine langsame KI keine Nachrichten mehr ungelesen wegscrollen. Ähnliche Nachrichten (derselbe Verkäufer ändert den Preis) werden alle gelesen; dieselbe Nachricht noch einmal gepostet nicht.</li>
<li>Oben oder unten halb abgeschnittene Zeilen warten, bis sie ganz sichtbar sind. Sticker werden nicht gelesen. <b>Zahlen werden immer vorgelesen</b> („in 5 Minuten“, „20k“, „lvl 60“).</li>
<li><b>Spiel im Energiesparmodus</b> („Swipe to exit sleep mode“): Der Chat wird weiter gelesen. Um deine Sprachnachricht zu schreiben, weckt die App das Spiel (Taste L) und schickt es danach wieder schlafen.</li>
<li><b>KI-Tempo in der oberen Leiste</b>: ⚡ Dauer jeder KI-Anfrage, ⏱ Verzögerung vom Lesen des Chats bis zur Übersetzung, ⏳ wartende Nachrichten, 👁 Dauer jedes Chat-Lesens. Grün = gut, gelb = langsam, rot = zu langsam; ⚠ = die KI schlägt fehl. Lässt sich im ⚙-Menü (📊) ausschalten.</li>
<li>⚙-Menü → <b>🪟 Anzeigen</b>: Leiste und Chat, nur die obere Leiste (der Chat wird ausgeblendet, Klicks gehen ans Spiel) oder nur den Chat (ohne Leiste; Rechtsklick für das Menü). In <b>⚙ App-Einstellungen → Overlay-Aussehen</b>: <b>Chat-Schrift</b>, Schriftgröße und <b>Größe der oberen Leiste</b> (alles in der Leiste wächst zusammen).</li>
<li><b>📊 Ratings</b> (Tab oben in diesem Fenster oder ⚙-Menü): die mit dieser App getesteten KIs mit Tempo und Qualität, und <b>🧪 Auf diesem PC testen</b>: Wähle eine KI (mit ihren aktuellen Optionen: GPU-Schichten, Kontext…) und drücke <b>▶ Testen</b>. Es zeigt das Tempo, die Probleme und ob sie auf deinem PC gut läuft; bei lokaler KI vergleicht es auch Grafikkarte und Prozessor.</li>
<li><b>Dauermodus mit Kopfhörern</b>: Mit <b>🎧 Chat im Dauermodus weiter vorlesen</b> liest die Chat-Stimme zwischen deinen Sätzen weiter und schweigt, während du sprichst. Mit Lautsprechern schalte es aus, damit das Mikro die Stimme nie hört. In allen Modi wird eine Chat-Nachricht, die unterbrochen wurde, weil du zu sprechen begannst, danach erneut gelesen.</li>
<li><b>Lokale Modelle</b>: Nur das benutzte Modell bleibt im Grafikspeicher; das vorherige wird entladen, wenn du das Modell wechselst oder zu einer Cloud-KI gehst. Die Stimme kann ein anderes lokales Modell als der Chat nutzen (dann bleiben beide geladen). Alles wird entladen, wenn die App schließt, auch nach einem Absturz.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> antwortet manchmal auf Arabisch: Die App übersetzt diese Zeilen erneut, aber ein Modell aus 📊 Ratings ist besser.</li>
</ul>

<h3>7. Probleme</h3>
<ul>
<li><b>„Warte auf das RF-Online-Fenster“</b>: das Spiel ist minimiert oder
geschlossen.</li>
<li><b>Nichts wird übersetzt</b>: unter ☰ → ⚠️ Fehler nachsehen. Bei einer
Cloud-KI <b>Testen</b> drücken, um Schlüssel, Guthaben und Tageslimit zu
prüfen.</li>
<li><b>429 / rate-limited upstream</b>: dieses kostenlose Modell ist
ausgelastet. Ein paar Minuten warten oder ein anderes wählen.</li>
<li><b>Tageslimit</b>: die 50 kostenlosen OpenRouter-Anfragen sind
verbraucht. Sie werden um 00:00 UTC zurückgesetzt. Bis dahin kannst du die
lokale KI oder eine zweite KI nutzen.</li>
<li><b>Mikrofon zu leise oder wird nicht verstanden</b>: 🎤 Testen nutzen, das
„MME:“-Gerät wählen und die Windows-Audioverbesserungen (Voice Clarity)
ausschalten.</li>
<li><b>Das Spiel ruckelt mit der lokalen KI</b>: ein kleineres Modell oder
<i>GPU-Schichten → nur CPU</i> wählen.</li>
<li><b>📄 Log anzeigen</b> öffnet das Log (Ordner <code>logs</code>). Audio
wird nie gespeichert.</li>
</ul>

<h3>Datenschutz</h3>
<p>Schlüssel werden verschlüsselt gespeichert (Windows DPAPI), und nur dein
Windows-Konto kann sie lesen. Mit einer Cloud-KI geht der Chattext an diesen
Anbieter. Mit der lokalen KI verlässt nichts den PC. Spielaufnahmen und die Stimme der App bleiben nur im Arbeitsspeicher: nichts wird auf die Festplatte geschrieben (keine Screenshots, kein Audio).</p>
"""

MANUAL["ru"] = """
<h2>🎮 RF Online Translator — руководство</h2>
<p>Читает <b>чат RF Online</b> из окна игры, переводит каждое сообщение с
помощью ИИ и показывает его в прозрачном окне поверх игры, по каналам (Все,
Мир, Сервер, Группа, Гильдия, Рейд, Личка…). Может зачитывать каждое
сообщение вслух («<i>Имя говорит: сообщение</i>»). Ещё можно <b>говорить на
своём языке</b>: приложение переведёт сказанное и напечатает его в чат
игры.<br>Оно только смотрит на экран и печатает как клавиатура. Память игры и
сетевой трафик оно никогда не читает.</p>

<h3>1. Первый запуск</h3>
<p>Быстрее всего: кнопка <b>🔊 Быстрый старт</b> (внизу главного окна) зачитывает главные шаги и показывает, куда нажимать. При первом запуске открывается сама.</p>
<ol>
<li>Нужна Windows 10/11. Устанавливать Python не нужно: один раз
запустите <b>install.bat</b>. Он создаст <b>RF Translator.exe</b> и положит
собственный Python приложения в папку <b>python</b> (всё остаётся в папке
приложения).</li>
<li>Откройте <b>RF Translator.exe</b> и подтвердите запрос администратора.
Игра работает от администратора, и только так Windows разрешает приложению
читать её окно и печатать в него.</li>
<li>При первом запуске устанавливается всё недостающее (пакеты Python,
Tesseract OCR, языковые пакеты, Ollama). Это может занять несколько
минут.</li>
<li>Впишите <b>имя своего персонажа</b>, чтобы ваши сообщения
игнорировались.</li>
<li>Выберите ИИ (пункт 2) и языки (пункт 3) и нажмите <b>▶ Запустить
переводчик</b>.</li>
</ol>

<h3>2. Выбор ИИ</h3>
<ul>
<li><b>Локально (Ollama, этот ПК)</b>: бесплатно, приватно и без интернета.
Занимает около 2 ГБ видеопамяти. <b>gemma2:2b</b> работает быстро и
помещается рядом с игрой на карте с 8 ГБ. Через 🤗 можно скачать другие
модели (в ☁ AI Clouds — какая подойдёт вашему ПК). Загружена всегда только 1 модель, и она выгружается при закрытии
приложения, даже после сбоя.</li>
<li><b>Без ИИ</b> (без ключа и аккаунта): <b>🌐 Google Переводчик</b>
(онлайн, быстро; если Google блокирует на несколько минут, приложение само
переключается на MyMemory, затем на Argos), <b>📦 Argos</b> (офлайн на этом
ПК; при нажатии «Запустить» скачивает ~20 МБ и ~150 МБ на каждую пару
языков) и <b>📦 NLLB</b> (офлайн, одна модель ~630 МБ для 200 языков). Без
лимитов и странных ответов ИИ, но они не исправляют ошибки OCR и игровой
сленг, как ИИ. Панель голоса может использовать другой.</li>
<li><b>Облако (API)</b>: качество выше, видеопамять не нужна. В панели ИИ (чат или голос) выберите ИИ, вставьте ключ и нажмите
<b>Проверить</b>. У каждого ИИ свой ключ, он хранится зашифрованным под вашей
учётной записью Windows.</li>
<li><b>OpenRouter</b>: один ключ открывает сотни моделей. Введите
<code>free</code> в поле модели, чтобы увидеть бесплатные.
<b>Без кредитов бесплатные модели дают только 50 запросов в день.</b>
Оверлей и кнопка «Проверить» показывают, сколько осталось. С 10 кредитами
лимит вырастает до 1000 в день. Один запрос переводит до 6 строк чата.<br>
Проверенные бесплатные модели (октябрь 2026):
<code>inclusionai/ling-3.0-flash-sante:free</code> (быстро и правильно) и
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (хорошо, ~1 с на запрос с
выключенным «размышлением»). Не берите <code>nemotron-3.5-lightning</code>
(очень медленно, неверный результат). Бесплатные модели иногда заняты
несколько минут («rate-limited upstream»).</li>
<li><b>Свой сервер 1 и 2</b>: любой сервер, совместимый с OpenAI (OpenRouter,
LM Studio, vLLM, другой ПК, другие провайдеры). Впишите URL (например
<code>https://openrouter.ai/api/v1</code> или
<code>http://localhost:1234/v1</code>) и ключ, если он нужен. Затем нажмите
«Проверить» и выберите модель. С двумя серверами можно одновременно
использовать два облачных ИИ.</li>
<li><b>ИИ для голоса</b>: по умолчанию тот же, что для чата. Можно выбрать
другой (например, бесплатную модель для чата и получше для голоса). Два
облачных ИИ могут работать одновременно.</li>
<li><b>Если этот ИИ не отвечает, использовать другие с ключом</b>: если
основной ИИ недоступен, без кредитов или занят, приложение берёт другой
настроенный ИИ и через 2 минуты возвращается к основному.</li>
<li><b>Профиль и настройки</b> (отдельно для ИИ чата и для ИИ
голоса): выберите <b>Профиль</b>, чтобы одним кликом заполнить ИИ, модель и
её настройки. ⭐-профили идут с приложением (✅ = проверено с этим
приложением, 🆓 = бесплатный план, здесь не проверен). 💾 сохраняет свои
профили, 🗑 удаляет их. Настройки: <i>Температура</i> (Проверено = 0.1
локально / 0.2 облако; <i>Как у модели</i> ничего не отправляет),
<i>Размышление</i> (оставьте <b>Выкл.</b>, так намного быстрее),
<i>Контекст</i> и <i>Макс. ответ</i> («Авто» хватает; 4k–8k для маленьких
моделей) и <i>Строк на запрос</i> (облачный чат: больше строк = меньше
запросов, это экономит бесплатные дневные лимиты).</li>
<li><b>Бесплатные ИИ на весь день</b>: все модели <code>:free</code> на
OpenRouter <b>делят</b> одни и те же 50 запросов в день (1000 с 10
кредитами). Чтобы играть весь день бесплатно, используйте <b>локальный</b>
ИИ (без лимита) или один из этих: <b>Mistral</b> (бесплатный план
«Experiment», около 1 запроса в секунду, без дневного лимита; профиль
⭐ Mistral · Small), <b>Google Gemini</b> (бесплатный ключ из AI Studio;
Flash-Lite даёт около 1000 запросов в день) или <b>Groq</b> (бесплатный
ключ, около 1000 запросов в день на модель). Добавьте второй ИИ как
запасной, и приложение переключится, когда один закончится. Лимиты меняются,
каждый провайдер показывает их на своём сайте.</li>
<li>☁ <b>AI Clouds</b> (вкладка вверху этого окна или кнопка под ключами): какие облачные ИИ бесплатны, их лимиты и где создать ключи.</li>
<li><b>Две панели ИИ</b> (чат и голос) одинаковые: ИИ, ключ («Проверить» / «Получить ключ»), для своих серверов — <b>Имя</b> на ваш выбор и URL, модель с <b>🔍 поиском</b>, <b>🆓 Только бесплатные</b> (бесплатные — <b>зелёные</b>; ⛔ = отклонено вашим аккаунтом, напр. заблокированные платные модели), профиль и настройки. <b>Запросов/мин</b> держит каждый облачный ИИ ниже его лимита. С локальным ИИ облачные настройки скрыты.</li>
</ul>

<h3>3. Чтение чата</h3>
<ul>
<li><b>Исходный язык</b>: <i>Авто</i> определяет язык каждой строки, так что
игроки могут писать на разных языках. <b>Переводить на</b>: ваш язык.</li>
<li>Держите чат игры открытым на нужном канале. Приложение читает окно игры
напрямую, поэтому оверлей может быть где угодно и любого размера. При
Alt+Tab оверлей прячется, но чтение и озвучка продолжаются.</li>
<li>Когда вы открываете чат или переключаете вкладку, приложение переводит
<b>и озвучивает</b> всё, что ещё не было прочитано, по порядку. Уже
прочитанное <b>никогда не повторяется</b>, даже после закрытия и открытия
чата или перезапуска приложения (в течение 6 часов).</li>
<li>Ваши сообщения и отправленные вами личные сообщения («Sender: …»)
игнорируются.</li>
<li>🔊 <b>Нейронный голос</b> читает «Имя говорит: сообщение». Если ждёт
много сообщений, он читает чуть быстрее, чтобы не отставать.</li>
<li><b>Скорость</b> и <b>Тон</b> голоса (в 🔊 Нейронный голос): настройте и нажмите <b>▶ Прослушать</b>, чтобы услышать пример до запуска. ↺ возвращает значение по умолчанию.</li>
<li>🔔 <b>Звук, когда кто-то пишет моё имя</b> (под именем персонажа): если в сообщении есть ваше имя (даже с ошибками OCR или кириллицей), звучит сигнал. Выберите <b>звук</b>, сколько раз он звучит, или <b>текст</b>, который голос скажет вместо звука, только для вас (<code>{name}</code> = кто написал), и <b>Повторять каждые X с в течение Y с</b> (по умолчанию каждые 10 с в течение 30 с). Клавиша отмены (Esc) или начало диктовки останавливают его. ▶ — прослушать.</li>
<li><b>Чтений чата в минуту</b> (Чтение чата): как часто приложение снимает игру и читает чат (20 = по умолчанию). Меньше — меньше нагрузка на ЦП.</li>
</ul>

<h3>4. Голос в игру (микрофон)</h3>
<ul>
<li>Выберите <b>Я говорю на</b> и <b>Писать на</b>, микрофон и
<b>клавишу</b> (по умолчанию F11). 🎤 <b>Проверить</b> показывает уровень и
то, что было распознано. Устройства «MME:» обычно работают лучше.</li>
<li>Режимы: <b>Push-to-talk</b> (запись, пока клавиша нажата, остановка —
когда отпускаете), <b>Нажатие</b> (одно нажатие слушает до длинной паузы) и
<b>Непрерывно</b> (одно нажатие включает, другое выключает; каждая фраза
отправляется на паузе).</li>
<li>Во всех режимах восходящий сигнал значит, что приложение слушает, а
короткий — что запись остановлена. Пока идёт запись, на оверлее мигает
красное <b>● Слушаю</b>, затем <b>⏳ Перевожу</b>.</li>
<li><b>✋ Подтверждать перед отправкой</b> (в 🎤 Микрофон или в меню ⚙
оверлея): выкл. — приложение набирает сообщение и само отправляет. Вкл. —
набирает его в чате игры и ждёт: на панели оверлея появляется зелёная
кнопка <b>✔ Отправить</b> (всегда видна). Нажмите её или клавишу голоса ещё
раз, чтобы отправить; <b>✖</b> или Esc стирает. Через 2 минуты без ответа
текст остаётся в чате неотправленным.</li>
<li>Голосовые команды в начале фразы: <b>«reply …»</b> отвечает на последнее
личное сообщение, а <b>«переключи на чат гильдия / сервер / группа / мир /
личка»</b> (на любом из языков) меняет канал в игре.</li>
<li>Ответы уходят на языке собеседника, если приложение его знает.</li>
<li>⚠️ Приложение печатает в чат игры и нажимает Enter за вас.</li>
<li><b>Сигналы</b> (через звуковой выход приложения, т. е. ваши
наушники): восходящий = говорите; короткий = запись окончена, идёт перевод;
нисходящий = отменено; низкий = ещё обрабатывается предыдущая.</li>
<li><b>Клавиша отмены</b> (по умолчанию <b>Esc</b>; можно записать
другую): сразу останавливает диктовку, на каком бы этапе она ни была
(запись, перевод или печать), и стирает уже напечатанное. Enter не
нажимается. Работает только во время диктовки; иначе клавиша уходит в игру
как обычно. В непрерывном режиме отменяет только текущую фразу.</li>
</ul>

<h3>5. Оверлей</h3>
<ul>
<li>Перетаскивайте за верхнюю панель и меняйте размер за края. 🔒 блокирует
оверлей: он не двигается, не меняет размер, и клики проходят в игру, но
верхняя панель остаётся кликабельной. <b>Ctrl+Shift+L</b> тоже блокирует и
разблокирует его.</li>
<li>Вкладки повторяют каналы игры, и оверлей переключает вкладку вместе с
игрой.</li>
<li>Меню ☰: автоскрытие через X секунд без сообщений, видимость фона,
настройки, голос вкл/выкл, языковые пакеты, журнал, ⚠️ ошибки, очистить
оверлей и выход.</li>
<li>Значок рядом с часами Windows открывает настройки и разблокирует
оверлей.</li>
<li><b>✕</b> на оверлее возвращает в главное окно; ✕ в главном окне
закрывает приложение. Оба действия меняются в <b>⚙ Настройки
приложения</b>.</li>
<li><b>⚙ Настройки приложения</b> (кнопка внизу главного окна): язык
приложения, тема, вид оверлея, действие ✕, языковые пакеты и аудиоустройства (микрофон
с 🎤 Тест и вывод голоса).</li>
<li><b>🔄 Обновления</b> (в ⚙ Настройки приложения): при запуске
приложение проверяет GitHub; если есть новая версия, на кнопке ⚙ появляется 🆕.
<b>⬇️ Обновить сейчас</b> заменяет только код приложения (~0,3 МБ) и
перезапускает его. Ваши настройки, ключи, модели и Python приложения не
меняются.</li>
<li><b>💾 Профили</b> (рамка справа в главном окне): профиль сохраняет
всё, что внутри этой рамки (имя персонажа и оповещение, чтение чата,
микрофон и клавиши, голос чтения), а также вид оверлея и аудиоустройства.
ИИ он не сохраняет никогда: у каждой панели ИИ свои профили, поэтому
применение профиля 💾 оставляет ваш ИИ.</li>
</ul>

<h3>6. Надёжное чтение, скорость и проверки</h3>
<ul>
<li><b>Любое разрешение</b>: приложение само находит чат от 720p до 4K. Если ваш чат больше или меньше, или интерфейс игры в другом масштабе, используйте <b>🎯 Калибровать</b> (Зона чата, в Чтении чата): откройте чат в игре, перетащите синюю рамку на сообщения, подгоните размер и нажмите <b>✔ Подтвердить</b> (Enter). Рамка видна, только когда игра на переднем плане. <b>Использовать откалиброванную зону</b> включает или выключает её; калибровка сохраняется.</li>
<li>Чтение и перевод идут раздельно: приложение продолжает читать чат, пока ИИ переводит, поэтому медленный ИИ больше не даёт сообщениям уйти вверх непрочитанными. Похожие сообщения (тот же продавец меняет цену) читаются все; то же сообщение, отправленное снова, — нет.</li>
<li>Строки, обрезанные сверху или снизу чата, ждут, пока не станут видны целиком. Стикеры не читаются. <b>Числа всегда читаются вслух</b> («через 5 минут», «20k», «lvl 60»).</li>
<li><b>Игра в режиме сна</b> («Swipe to exit sleep mode»): чат всё равно читается. Чтобы напечатать голосовое сообщение, приложение будит игру (клавиша L) и потом снова усыпляет её.</li>
<li><b>Скорость ИИ на верхней панели</b>: ⚡ время каждого запроса к ИИ, ⏱ задержка от чтения чата до появления перевода, ⏳ сообщения в очереди, 👁 время каждого чтения чата. Зелёный = хорошо, жёлтый = медленно, красный = слишком медленно; ⚠ = ИИ даёт сбои. Отключается в меню ⚙ (📊).</li>
<li>Меню ⚙ → <b>🪟 Показывать</b>: панель и чат, только верхняя панель (чат скрыт, клики идут в игру) или только чат (без панели; меню по правой кнопке). В <b>⚙ Настройки приложения → вид оверлея</b>: <b>шрифт чата</b>, размер шрифта и <b>размер верхней панели</b> (всё на панели растёт вместе).</li>
<li><b>📊 Ratings</b> (вкладка вверху этого окна или меню ⚙): ИИ, проверенные с этим приложением, со скоростью и качеством, и <b>🧪 Проверить на этом ПК</b>: выберите ИИ (с его текущими опциями: слои на GPU, контекст…) и нажмите <b>▶ Проверить</b>. Показывает скорость, проблемы и хорошо ли он работает на вашем ПК; для локального ИИ также сравнивает видеокарту и процессор.</li>
<li><b>Непрерывный режим в наушниках</b>: с включённым <b>🎧 Продолжать читать чат в непрерывном режиме</b> голос чата читает между вашими фразами и замолкает, пока вы говорите. С колонками выключите, чтобы микрофон не слышал голос. Во всех режимах сообщение чата, прерванное тем, что вы начали говорить, потом читается заново.</li>
<li><b>Локальные модели</b>: в видеопамяти остаётся только используемая модель; предыдущая выгружается, когда вы меняете модель или переходите на облачный ИИ. Голос может использовать другую локальную модель, чем чат (тогда загружены обе). Всё выгружается при закрытии приложения, даже после сбоя.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> иногда отвечает по-арабски: приложение переводит такие строки заново, но лучше модель из 📊 Ratings.</li>
</ul>

<h3>7. Проблемы</h3>
<ul>
<li><b>«Ожидание окна RF Online»</b>: игра свёрнута или закрыта.</li>
<li><b>Ничего не переводится</b>: посмотрите ☰ → ⚠️ Ошибки. Для облачного ИИ
нажмите <b>Проверить</b>, чтобы проверить ключ, баланс и дневной
лимит.</li>
<li><b>429 / rate-limited upstream</b>: эта бесплатная модель занята.
Подождите несколько минут или выберите другую.</li>
<li><b>Дневной лимит</b>: 50 бесплатных запросов OpenRouter закончились. Они
обновляются в 00:00 UTC. Пока можно использовать локальный ИИ или второй
ИИ.</li>
<li><b>Микрофон тихий или не распознаёт</b>: используйте 🎤 Проверить,
выберите устройство «MME:» и выключите улучшения звука Windows (Voice
Clarity).</li>
<li><b>Игра подтормаживает с локальным ИИ</b>: выберите модель поменьше или
<i>Слои на GPU → только CPU</i>.</li>
<li><b>📄 Журнал</b> открывает журнал (папка <code>logs</code>). Звук никогда
не сохраняется.</li>
</ul>

<h3>Конфиденциальность</h3>
<p>Ключи хранятся в зашифрованном виде (Windows DPAPI), и прочитать их может
только ваша учётная запись Windows. С облачным ИИ текст чата отправляется
этому провайдеру. С локальным ИИ ничего не покидает ПК. Снимки игры и голос приложения хранятся только в памяти: на диск ничего не записывается (ни снимки экрана, ни звук).</p>
"""

MANUAL["it"] = """
<h2>🎮 RF Online Translator — Manuale</h2>
<p>Legge la <b>chat di RF Online</b> dalla finestra del gioco, traduce ogni
messaggio con un'IA e lo mostra in una finestra trasparente sopra il gioco,
divisa per canale (Tutti, Mondo, Server, Gruppo, Gilda, Raid, Privato…).
Può leggere ogni messaggio ad alta voce («<i>Nome dice: messaggio</i>»).
Puoi anche <b>parlare nella tua lingua</b>: l'app traduce e lo scrive nella
chat del gioco.<br>Guarda solo lo schermo e scrive come una tastiera. Non
legge mai la memoria del gioco né il traffico di rete.</p>

<h3>1. Primo avvio</h3>
<p>Il modo più rapido: il pulsante <b>🔊 Guida rapida</b> (in basso nella finestra principale) legge ad alta voce i passi essenziali e mostra dove cliccare. Si apre da solo la prima volta.</p>
<ol>
<li>Serve Windows 10/11. Non serve installare Python: avvia una volta
<b>install.bat</b>. Crea <b>RF Translator.exe</b> e mette il Python dell'app
nella sua cartella <b>python</b> (tutto resta nella cartella dell'app).</li>
<li>Apri <b>RF Translator.exe</b> e accetta la richiesta di amministratore.
Il gioco gira come amministratore e Windows lascia leggere e scrivere nel
gioco solo così.</li>
<li>Il primo avvio installa ciò che manca (pacchetti Python, Tesseract OCR,
pacchetti lingua, Ollama). Può richiedere qualche minuto.</li>
<li>Scrivi il <b>nome del tuo personaggio</b> così i tuoi messaggi vengono
ignorati.</li>
<li>Scegli l'IA (punto 2) e le lingue (punto 3) e premi <b>▶ Avvia
traduttore</b>.</li>
</ol>

<h3>2. Scegliere l'IA</h3>
<ul>
<li><b>Locale (Ollama, questo PC)</b>: gratis, privata e funziona senza
internet. Usa circa 2 GB di memoria della scheda video. <b>gemma2:2b</b> è
veloce e sta accanto al gioco su una scheda da 8 GB. Usa 🤗 per scaricare
altri modelli (☁ AI Clouds dice quale va bene per il tuo PC). È caricato 1 solo modello alla volta, e viene scaricato quando
l'app si chiude, anche dopo un crash.</li>
<li><b>Senza IA</b> (senza chiave né account): <b>🌐 Google
Traduttore</b> (online, veloce; se Google blocca per qualche minuto l'app
passa da sola a MyMemory e poi ad Argos), <b>📦 Argos</b> (offline su questo
PC; scarica ~20 MB più ~150 MB per coppia di lingue quando premi Avvia) e
<b>📦 NLLB</b> (offline, un modello da ~630 MB per 200 lingue). Niente quote
né risposte strane dell'IA, ma non correggono gli errori dell'OCR né lo slang
di gioco come un'IA. Il pannello della voce può usarne un altro.</li>
<li><b>Cloud (API)</b>: qualità migliore e niente memoria video. Nel pannello dell'IA (chat o voce), scegli l'IA, incolla la chiave e premi
<b>Prova</b>. Ogni IA conserva la propria chiave, cifrata con il tuo account
Windows.</li>
<li><b>OpenRouter</b>: una chiave dà accesso a centinaia di modelli. Scrivi
<code>free</code> nel campo del modello per vedere quelli gratuiti.
<b>Senza crediti i modelli gratuiti permettono solo 50 richieste al
giorno.</b> L'overlay e il pulsante Prova mostrano quante ne restano. Con 10
crediti diventano 1000 al giorno. Una richiesta traduce fino a 6 righe della
chat.<br>
Modelli gratuiti provati (ottobre 2026):
<code>inclusionai/ling-3.0-flash-sante:free</code> (veloce e corretto) e
<code>nvidia/nemotron-3-super-120b-a12b:free</code> (buono, ~1 s a richiesta
con il «ragionamento» spento). Evita <code>nemotron-3.5-lightning</code>
(molto lento, risultati sbagliati). A volte i modelli gratuiti sono occupati
per qualche minuto («rate-limited upstream»).</li>
<li><b>Server personale 1 e 2</b>: qualsiasi server compatibile con OpenAI
(OpenRouter, LM Studio, vLLM, un altro PC, altri provider). Scrivi l'URL
(es. <code>https://openrouter.ai/api/v1</code> o
<code>http://localhost:1234/v1</code>) e la chiave se serve. Poi premi Prova
e scegli il modello. Con due server puoi usare due IA cloud insieme.</li>
<li><b>IA della voce</b>: di base è la stessa della chat. Puoi sceglierne
un'altra (es. un modello gratuito per la chat e uno migliore per la tua
voce). Due IA cloud possono funzionare insieme.</li>
<li><b>Se questa IA fallisce, usa le altre che hanno una chiave</b>: se l'IA
principale è giù, senza credito o occupata, l'app passa a un'altra IA
configurata e torna alla principale dopo 2 minuti.</li>
<li><b>Profilo e opzioni</b> (uno per l'IA della chat e uno per l'IA
della voce): scegli un <b>Profilo</b> per compilare IA, modello e opzioni
con un clic. I profili ⭐ sono inclusi nell'app (✅ = provato con questa app,
🆓 = piano gratuito, non provato qui). 💾 salva i tuoi e 🗑 li elimina.
Opzioni: <i>Temperatura</i> (Provata = 0.1 locale / 0.2 cloud; <i>Quella
del modello</i> non invia nulla), <i>Ragionamento</i> (lascialo
<b>Spento</b>, è molto più veloce), <i>Contesto</i> e <i>Risposta
max.</i> (Automatico basta; 4k–8k per i modelli piccoli) e <i>Righe per
richiesta</i> (chat cloud: più righe = meno richieste, così risparmi i
limiti giornalieri gratuiti).</li>
<li><b>IA gratuite per tutto il giorno</b>: tutti i modelli
<code>:free</code> di OpenRouter <b>condividono</b> le stesse 50 richieste al
giorno (1000 con 10 crediti). Per giocare tutto il giorno gratis usa l'IA
<b>Locale</b> (senza limite) o una di queste: <b>Mistral</b> (piano gratuito
«Experiment», circa 1 richiesta al secondo, senza limite giornaliero;
profilo ⭐ Mistral · Small), <b>Google Gemini</b> (chiave gratuita da AI
Studio; Flash-Lite consente circa 1000 richieste al giorno) o <b>Groq</b>
(chiave gratuita, circa 1000 richieste al giorno per modello). Aggiungi una
seconda IA di riserva e l'app cambia quando una si esaurisce. I limiti
cambiano, e ogni provider li mostra sul suo sito.</li>
<li>☁ <b>AI Clouds</b> (scheda in alto in questa finestra, o il pulsante sotto le chiavi): quali IA cloud sono gratuite, i loro limiti e dove creare le chiavi.</li>
<li><b>I due pannelli IA</b> (chat e voce) sono uguali: IA, chiave (Prova / Ottieni chiave), per i server personali un <b>Nome</b> a scelta e l'URL, il modello con <b>🔍 ricerca</b>, <b>🆓 Solo gratuiti</b> (i gratuiti sono <b>verdi</b>; ⛔ = rifiutato dal tuo account, es. modelli a pagamento che hai bloccato), profilo e opzioni. <b>Richieste/min</b> tiene ogni IA cloud sotto il suo limite. Con un'IA locale le opzioni solo cloud sono nascoste.</li>
</ul>

<h3>3. Leggere la chat</h3>
<ul>
<li><b>Lingua di origine</b>: <i>Auto</i> riconosce ogni riga, quindi ogni
giocatore può scrivere in una lingua diversa. <b>Traduci in</b>: la tua
lingua.</li>
<li>Tieni la chat del gioco aperta sul canale che vuoi. L'app legge
direttamente la finestra del gioco, quindi l'overlay può stare ovunque e
avere qualsiasi dimensione. Con alt-tab l'overlay si nasconde, ma lettura e
voce continuano.</li>
<li>Quando apri la chat o cambi scheda, l'app traduce <b>e legge ad alta
voce</b> tutto ciò che non è ancora stato letto, in ordine. Ciò che è già
stato letto <b>non si ripete mai</b>, anche dopo aver chiuso e riaperto la
chat o riavviato l'app (fino a 6 ore).</li>
<li>I tuoi messaggi e i PM che invii («Sender: …») vengono ignorati.</li>
<li>🔊 La <b>voce neurale</b> legge «Nome dice: messaggio». Se ci sono molti
messaggi in attesa, legge un po' più veloce per non restare indietro.</li>
<li><b>Velocità</b> e <b>Tono</b> della voce (in 🔊 Voce neurale): regolali e premi <b>▶ Ascolta</b> per sentire un esempio prima di iniziare. ↺ torna al predefinito.</li>
<li>🔔 <b>Suono quando qualcuno scrive il mio nome</b> (sotto il nome del personaggio): quando un messaggio contiene il tuo nome (anche con errori dell'OCR o scritto in cirillico), suona un avviso. Scegli il <b>suono</b>, quante volte suona, oppure un <b>testo</b> che la voce dice al posto del suono, solo per te (<code>{name}</code> = chi l'ha scritto) e <b>Ripeti ogni X s per Y s</b> (predefinito ogni 10 s per 30 s). Il tasto annulla (Esc) o iniziare a dettare lo fermano. ▶ te lo fa sentire.</li>
<li><b>Letture della chat al minuto</b> (Lettura della chat): quante volte l'app cattura il gioco e legge la chat (20 = predefinito). Meno = meno CPU.</li>
</ul>

<h3>4. Parlare nel gioco (microfono)</h3>
<ul>
<li>Scegli <b>Parlo in</b> e <b>Scrivi in</b>, il microfono e il
<b>tasto</b> (predefinito F11). 🎤 <b>Prova</b> mostra il livello e cosa è
stato capito. I dispositivi «MME:» di solito funzionano meglio.</li>
<li>Modalità: <b>Push-to-talk</b> (registra finché tieni premuto il tasto e
si ferma quando lo lasci), <b>Tocco</b> (un tocco ascolta finché fai una
pausa lunga) e <b>Continuo</b> (un tocco lo attiva, un altro lo disattiva;
ogni frase viene inviata a ogni pausa).</li>
<li>In ogni modalità un bip crescente indica che l'app sta ascoltando e un
bip breve che si è fermata. Mentre ascolta, l'overlay mostra
<b>● In ascolto</b> che lampeggia in rosso, poi <b>⏳ Traduco</b>.</li>
<li><b>✋ Conferma prima di inviare</b> (in 🎤 Microfono o nel menu ⚙
dell'overlay): disattivato, l'app scrive il messaggio e lo invia da sola.
Attivato, lo scrive nella chat del gioco e aspetta: nella barra dell'overlay
appare un pulsante verde <b>✔ Invia</b> (sempre visibile). Premilo, o di nuovo
il tasto voce, per inviare; <b>✖</b> o Esc lo cancella. Dopo 2 minuti senza
risposta il testo resta nella chat, non inviato.</li>
<li>Comandi vocali a inizio frase: <b>«reply …»</b> risponde all'ultimo PM, e
<b>«cambia alla chat gilda / server / gruppo / mondo / privato»</b> (in
qualsiasi lingua) cambia il canale nel gioco.</li>
<li>Le risposte vanno nella lingua della persona con cui parli, quando l'app
la conosce.</li>
<li>⚠️ L'app scrive nella chat del gioco e preme Invio per te.</li>
<li><b>Bip</b> (dall'uscita voce dell'app, cioè le tue cuffie):
bip che sale = parla ora; bip corto = registrazione finita, sto traducendo;
bip che scende = annullato; bip grave = ancora occupato con la
precedente.</li>
<li><b>Tasto annulla</b> (predefinito <b>Esc</b>; puoi registrarne un
altro): ferma subito una dettatura, che stia ascoltando, traducendo o
scrivendo, e cancella ciò che era già scritto. Non preme mai Invio. Agisce
solo durante una dettatura; altrimenti il tasto va al gioco come sempre. In
modalità continua scarta solo la frase in corso.</li>
</ul>

<h3>5. L'overlay</h3>
<ul>
<li>Trascinalo dalla barra in alto e ridimensionalo dai bordi. 🔒 lo blocca:
non si sposta, non cambia dimensione e i clic passano al gioco, ma la barra
in alto resta cliccabile. Anche <b>Ctrl+Shift+L</b> lo blocca e lo
sblocca.</li>
<li>Le schede seguono i canali del gioco, e l'overlay cambia scheda quando
cambia il gioco.</li>
<li>Menu ☰: nascondi da solo dopo X secondi senza messaggi, visibilità dello
sfondo, impostazioni, voce sì/no, pacchetti lingua, log, ⚠️ errori, svuota
overlay ed esci.</li>
<li>L'icona vicino all'orologio di Windows apre le impostazioni e sblocca
l'overlay.</li>
<li><b>✕</b> sull'overlay torna alla finestra principale; ✕ nella finestra
principale chiude l'app. Puoi cambiarli entrambi in <b>⚙ Impostazioni
dell'app</b>.</li>
<li><b>⚙ Impostazioni dell'app</b> (pulsante in basso nella finestra
principale): lingua dell'app, tema, aspetto dell'overlay, cosa fa ✕, pacchetti lingua e
dispositivi audio (microfono con 🎤 Prova e l'uscita della voce).</li>
<li><b>🔄 Aggiornamenti</b> (in ⚙ Impostazioni dell'app): all'apertura
l'app controlla GitHub; se c'è una nuova versione il pulsante ⚙ mostra 🆕.
<b>⬇️ Aggiorna ora</b> sostituisce solo il codice dell'app (~0,3 MB) e la
riavvia. Le tue impostazioni, chiavi, modelli e il Python dell'app restano
come sono.</li>
<li><b>💾 Profili</b> (riquadro a destra nella finestra principale): un
profilo salva tutto ciò che c'è in quel riquadro (nome del personaggio e
avviso, lettura della chat, microfono e tasti, voce di lettura) più l'aspetto
dell'overlay e i dispositivi audio. Non salva mai l'IA: ogni pannello IA ha i
suoi profili, quindi applicare un profilo 💾 mantiene la tua IA.</li>
</ul>

<h3>6. Lettura affidabile, velocità e test</h3>
<ul>
<li><b>Qualsiasi risoluzione</b>: l'app trova la chat da sola da 720p a 4K. Se la tua chat è più grande o più piccola, o l'interfaccia del gioco ha un'altra scala, usa <b>🎯 Calibra</b> (Zona della chat, in Lettura della chat): apri la chat nel gioco, trascina e ridimensiona il riquadro blu sopra i messaggi e premi <b>✔ Conferma</b> (Invio). Il riquadro appare solo con il gioco in primo piano. <b>Usa la zona calibrata</b> la attiva o disattiva; la calibrazione resta salvata.</li>
<li>Lettura e traduzione vanno separate: l'app continua a leggere la chat mentre l'IA traduce, quindi un'IA lenta non lascia più scorrere via messaggi non letti. I messaggi simili (lo stesso venditore che cambia prezzo) vengono letti tutti; lo stesso messaggio ripubblicato no.</li>
<li>Le righe tagliate a metà in alto o in basso nella chat aspettano di essere visibili per intero. Gli sticker non vengono letti. <b>I numeri vengono sempre letti ad alta voce</b> («tra 5 minuti», «20k», «lvl 60»).</li>
<li><b>Gioco in modalità risparmio</b> («Swipe to exit sleep mode»): la chat viene comunque letta. Per scrivere il tuo messaggio vocale l'app sveglia il gioco (tasto L) e poi lo rimette in risparmio.</li>
<li><b>Velocità dell'IA nella barra in alto</b>: ⚡ tempo di ogni richiesta all'IA, ⏱ ritardo dalla lettura della chat alla comparsa della traduzione, ⏳ messaggi in attesa, 👁 tempo di ogni lettura della chat. Verde = bene, giallo = lento, rosso = troppo lento; ⚠ = l'IA sta fallendo. Si disattiva nel menu ⚙ (📊).</li>
<li>Menu ⚙ → <b>🪟 Mostra</b>: barra e chat, solo la barra in alto (la chat si nasconde e i clic vanno al gioco) o solo la chat (senza barra; clic destro per il menu). In <b>⚙ Impostazioni dell'app → aspetto dell'overlay</b>: <b>carattere della chat</b>, dimensione del testo e <b>dimensione della barra in alto</b> (tutto nella barra cresce insieme).</li>
<li><b>📊 Ratings</b> (scheda in alto in questa finestra, o menu ⚙): le IA provate con questa app, con velocità e qualità, e <b>🧪 Prova su questo PC</b>: scegli un'IA (con le opzioni che ha ora: livelli GPU, contesto…) e premi <b>▶ Prova</b>. Mostra la velocità, i problemi e se funziona bene sul tuo PC; con un'IA locale confronta anche scheda grafica e processore.</li>
<li><b>Modalità continua con le cuffie</b>: con <b>🎧 Continua a leggere la chat in modalità continua</b> attivo, la voce della chat continua a leggere tra le tue frasi e tace mentre parli. Con gli altoparlanti disattivalo, così il microfono non sente mai la voce. In ogni modalità, un messaggio della chat interrotto perché hai iniziato a parlare viene riletto dopo.</li>
<li><b>Modelli locali</b>: nella memoria della scheda grafica resta solo il modello in uso; il precedente esce quando cambi modello o passi a un'IA cloud. La voce può usare un altro modello locale rispetto alla chat (allora restano caricati entrambi). Tutto viene scaricato quando l'app si chiude, anche dopo un crash.</li>
<li>⚠️ <b>Groq · ALLaM 2 7B</b> a volte risponde in arabo: l'app ritraduce quelle righe, ma un modello dei 📊 Ratings è meglio.</li>
</ul>

<h3>7. Problemi</h3>
<ul>
<li><b>«In attesa della finestra di RF Online»</b>: il gioco è ridotto a icona
o chiuso.</li>
<li><b>Non traduce niente</b>: guarda in ☰ → ⚠️ Errori. Con un'IA cloud premi
<b>Prova</b> per controllare chiave, credito e limite giornaliero.</li>
<li><b>429 / rate-limited upstream</b>: quel modello gratuito è occupato.
Aspetta qualche minuto o scegline un altro.</li>
<li><b>Limite giornaliero</b>: le 50 richieste gratuite di OpenRouter sono
finite. Si azzerano alle 00:00 UTC. Nel frattempo puoi usare l'IA locale o
una seconda IA.</li>
<li><b>Microfono basso o non capisce</b>: usa 🎤 Prova, scegli il dispositivo
«MME:» e disattiva i miglioramenti audio di Windows (Voice Clarity).</li>
<li><b>Il gioco scatta con l'IA locale</b>: scegli un modello più piccolo o
<i>Livelli GPU → solo CPU</i>.</li>
<li><b>📄 Vedi log</b> apre il log (cartella <code>logs</code>). L'audio non
viene mai salvato.</li>
</ul>

<h3>Privacy</h3>
<p>Le chiavi sono salvate cifrate (DPAPI di Windows) e solo il tuo account
Windows può leggerle. Con un'IA cloud il testo della chat viene inviato a
quel provider. Con l'IA locale nulla esce dal PC. Le catture del gioco e la voce dell'app restano solo in memoria: nulla viene scritto sul disco (né screenshot, né audio).</p>
"""


def manual_html(lang):
    return MANUAL.get(lang) or MANUAL["en"]
