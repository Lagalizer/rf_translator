# -*- coding: utf-8 -*-
"""
ai_ratings.py — separador '📊 Ratings' (Manual / AI Clouds): as IAs e
tradutores testados com esta app, com tempos e notas, em 7 línguas.

Como foram medidos: as mesmas 26 mensagens reais do chat do RF (russo,
português, espanhol, inglês, anúncios WTS/WTB com itens [..], gíria) pelos
caminhos da própria app, destino inglês. IA local numa placa gráfica de
8 GB com o jogo aberto; nuvem/tradutores pela internet. Por baixo da tabela
o utilizador testa no próprio PC (main.py, BenchmarkTab).
"""

TESTED = "2026-10-04"

# (nome, tipo, velocidade, estrelas 1-5, chave da nota)
# tipo: 'local' (s por mensagem), 'cloud' / 'mt' (s por pedido de 6 linhas)
RATINGS = [
    ("gemma3:4b", "local", "3.4 s", 5, "n_g3_4b"),
    ("gemma2:2b", "local", "1.6 s", 4, "n_g2_2b"),
    ("llama3.2:3b", "local", "2.0 s", 4, "n_l32_3b"),
    ("gemma3:1b", "local", "1.4 s", 2, "n_g3_1b"),
    ("qwen2.5:1.5b", "local", "1.3 s", 2, "n_q25_15"),
    ("qwen2.5:3b", "local", "3.8 s", 1, "n_q25_3"),
    ("OpenRouter · Ling 3.0 Flash (free)", "cloud", "2.7 s", 5, "n_ling"),
    ("OpenRouter · Nemotron 3 Super 120B (free)", "cloud", "3.1 s", 4,
     "n_nemo"),
    ("OpenRouter · Nemotron 3.5 Lightning (free)", "cloud", "3.3 s", 2,
     "n_light"),
    ("Groq · ALLaM 2 7B", "cloud", "0.3 s", 2, "n_allam"),
    ("Google Translate", "mt", "0.5–1.1 s", 4, "n_google"),
    ("NLLB (offline)", "mt", "2.4 s", 3, "n_nllb"),
    ("Argos (offline)", "mt", "0.9 s", 3, "n_argos"),
]

# Não testados nesta ronda (sem acesso ou limite no momento do teste).
UNTESTED = ["OpenRouter · Gemma 4 31B (free)", "Groq · GPT-OSS 20B",
            "Groq · Qwen 3.6 27B", "Mistral Small", "SambaNova"]

TXT = {
    "en": {
        "title": "📊 AI ratings — tested with this app",
        "intro": "The same 26 real RF chat messages (Russian, Portuguese, "
                 "Spanish, English, WTS/WTB ads with [items], slang) "
                 "translated into English through the app itself. Local AI "
                 "on an 8 GB graphics card with the game open. Speed: local "
                 "= per message; cloud and translators = per request of 6 "
                 "lines. Tested on {d}. Below you can test on your own PC.",
        "c_ai": "AI / model", "c_kind": "Type", "c_speed": "Speed",
        "c_q": "Quality", "c_note": "Notes",
        "k_local": "🖥 Local", "k_cloud": "☁ Cloud", "k_mt": "🌐 Translator",
        "untested": "⏳ Not tested this time (no access or limit reached "
                    "during the test): {l}.",
        "n_g3_4b": "Best local translation (understands gaming slang). Needs "
                   "~3 GB of free graphics memory with the game open.",
        "n_g2_2b": "Recommended local choice: good and light (1.6 GB).",
        "n_l32_3b": "Good, a little literal.",
        "n_g3_1b": "Fast but invents text and leaves Russian words. Not "
                   "recommended.",
        "n_q25_15": "Mixes up lines and invents text; weak in Russian.",
        "n_q25_3": "Slower and puts Chinese words in the translation.",
        "n_ling": "Very natural ('leaving the party'). Free, 20 "
                  "requests/min.",
        "n_nemo": "Good; sometimes literal ('rains with party').",
        "n_light": "Sometimes only spells Russian in Latin letters instead "
                   "of translating.",
        "n_allam": "Extremely fast, but sometimes answers in Arabic (the "
                   "app now translates those lines again). Prefer another "
                   "model.",
        "n_google": "Fast and free, no key. Literal with gaming slang.",
        "n_nllb": "Offline (processor), decent.",
        "n_argos": "Offline and light; sometimes a wrong word ('heater' for "
                   "healer).",
    },
    "pt": {
        "title": "📊 Ratings das IAs — testadas com esta app",
        "intro": "As mesmas 26 mensagens reais do chat do RF (russo, "
                 "português, espanhol, inglês, anúncios WTS/WTB com "
                 "[itens], gíria) traduzidas para inglês pela própria app. "
                 "IA local numa placa gráfica de 8 GB com o jogo aberto. "
                 "Velocidade: local = por mensagem; nuvem e tradutores = "
                 "por pedido de 6 linhas. Testado em {d}. Mais abaixo podes "
                 "testar no teu PC.",
        "c_ai": "IA / modelo", "c_kind": "Tipo", "c_speed": "Velocidade",
        "c_q": "Qualidade", "c_note": "Notas",
        "k_local": "🖥 Local", "k_cloud": "☁ Nuvem", "k_mt": "🌐 Tradutor",
        "untested": "⏳ Não testados desta vez (sem acesso ou limite "
                    "atingido durante o teste): {l}.",
        "n_g3_4b": "A melhor tradução local (percebe a gíria dos jogos). "
                   "Precisa de ~3 GB livres na placa gráfica com o jogo "
                   "aberto.",
        "n_g2_2b": "Escolha local recomendada: boa e leve (1,6 GB).",
        "n_l32_3b": "Boa, um pouco literal.",
        "n_g3_1b": "Rápido mas inventa texto e deixa palavras em russo. "
                   "Não recomendado.",
        "n_q25_15": "Troca linhas e inventa texto; fraco em russo.",
        "n_q25_3": "Mais lento e mete palavras em chinês na tradução.",
        "n_ling": "Muito natural ('leaving the party'). Grátis, 20 "
                  "pedidos/min.",
        "n_nemo": "Bom; às vezes literal ('rains with party').",
        "n_light": "Às vezes só escreve o russo em letras latinas em vez de "
                   "traduzir.",
        "n_allam": "Rapidíssimo, mas às vezes responde em árabe (a app "
                   "agora volta a traduzir essas linhas). Prefere outro "
                   "modelo.",
        "n_google": "Rápido e grátis, sem chave. Literal com a gíria dos "
                    "jogos.",
        "n_nllb": "Offline (processador), razoável.",
        "n_argos": "Offline e leve; às vezes uma palavra errada ('heater' "
                   "em vez de healer).",
    },
    "es": {
        "title": "📊 Valoración de las IA — probadas con esta app",
        "intro": "Los mismos 26 mensajes reales del chat de RF (ruso, "
                 "portugués, español, inglés, anuncios WTS/WTB con "
                 "[objetos], jerga) traducidos al inglés por la propia app. "
                 "IA local en una tarjeta gráfica de 8 GB con el juego "
                 "abierto. Velocidad: local = por mensaje; nube y "
                 "traductores = por petición de 6 líneas. Probado el {d}. "
                 "Más abajo puedes probar en tu PC.",
        "c_ai": "IA / modelo", "c_kind": "Tipo", "c_speed": "Velocidad",
        "c_q": "Calidad", "c_note": "Notas",
        "k_local": "🖥 Local", "k_cloud": "☁ Nube", "k_mt": "🌐 Traductor",
        "untested": "⏳ No probados esta vez (sin acceso o límite alcanzado "
                    "durante la prueba): {l}.",
        "n_g3_4b": "La mejor traducción local (entiende la jerga de "
                   "juegos). Necesita ~3 GB libres en la tarjeta gráfica "
                   "con el juego abierto.",
        "n_g2_2b": "Opción local recomendada: buena y ligera (1,6 GB).",
        "n_l32_3b": "Buena, un poco literal.",
        "n_g3_1b": "Rápido pero inventa texto y deja palabras en ruso. No "
                   "recomendado.",
        "n_q25_15": "Mezcla líneas e inventa texto; flojo en ruso.",
        "n_q25_3": "Más lento y mete palabras en chino en la traducción.",
        "n_ling": "Muy natural ('leaving the party'). Gratis, 20 "
                  "peticiones/min.",
        "n_nemo": "Bueno; a veces literal ('rains with party').",
        "n_light": "A veces solo escribe el ruso con letras latinas en vez "
                   "de traducir.",
        "n_allam": "Rapidísimo, pero a veces responde en árabe (la app "
                   "ahora vuelve a traducir esas líneas). Mejor otro "
                   "modelo.",
        "n_google": "Rápido y gratis, sin clave. Literal con la jerga de "
                    "juegos.",
        "n_nllb": "Sin conexión (procesador), aceptable.",
        "n_argos": "Sin conexión y ligero; a veces una palabra equivocada "
                   "('heater' en vez de healer).",
    },
    "fr": {
        "title": "📊 Notes des IA — testées avec cette app",
        "intro": "Les mêmes 26 vrais messages du chat de RF (russe, "
                 "portugais, espagnol, anglais, annonces WTS/WTB avec "
                 "[objets], argot) traduits en anglais par l'app elle-même. "
                 "IA locale sur une carte graphique de 8 Go avec le jeu "
                 "ouvert. Vitesse : locale = par message ; cloud et "
                 "traducteurs = par requête de 6 lignes. Testé le {d}. Plus "
                 "bas, tu peux tester sur ton PC.",
        "c_ai": "IA / modèle", "c_kind": "Type", "c_speed": "Vitesse",
        "c_q": "Qualité", "c_note": "Notes",
        "k_local": "🖥 Locale", "k_cloud": "☁ Cloud",
        "k_mt": "🌐 Traducteur",
        "untested": "⏳ Pas testés cette fois (pas d'accès ou limite "
                    "atteinte pendant le test) : {l}.",
        "n_g3_4b": "La meilleure traduction locale (comprend l'argot des "
                   "jeux). Il faut ~3 Go libres sur la carte graphique avec "
                   "le jeu ouvert.",
        "n_g2_2b": "Choix local conseillé : bon et léger (1,6 Go).",
        "n_l32_3b": "Bon, un peu littéral.",
        "n_g3_1b": "Rapide mais invente du texte et laisse des mots en "
                   "russe. Déconseillé.",
        "n_q25_15": "Mélange les lignes et invente du texte ; faible en "
                    "russe.",
        "n_q25_3": "Plus lent et met des mots chinois dans la traduction.",
        "n_ling": "Très naturel ('leaving the party'). Gratuit, 20 "
                  "requêtes/min.",
        "n_nemo": "Bon ; parfois littéral ('rains with party').",
        "n_light": "Parfois il écrit seulement le russe en lettres latines "
                   "au lieu de traduire.",
        "n_allam": "Extrêmement rapide, mais répond parfois en arabe (l'app "
                   "retraduit maintenant ces lignes). Préfère un autre "
                   "modèle.",
        "n_google": "Rapide et gratuit, sans clé. Littéral avec l'argot des "
                    "jeux.",
        "n_nllb": "Hors ligne (processeur), correct.",
        "n_argos": "Hors ligne et léger ; parfois un mauvais mot ('heater' "
                   "au lieu de healer).",
    },
    "de": {
        "title": "📊 KI-Bewertungen — mit dieser App getestet",
        "intro": "Dieselben 26 echten RF-Chatnachrichten (Russisch, "
                 "Portugiesisch, Spanisch, Englisch, WTS/WTB-Anzeigen mit "
                 "[Gegenständen], Slang), von der App selbst ins Englische "
                 "übersetzt. Lokale KI auf einer 8-GB-Grafikkarte bei "
                 "offenem Spiel. Tempo: lokal = pro Nachricht; Cloud und "
                 "Übersetzer = pro Anfrage mit 6 Zeilen. Getestet am {d}. "
                 "Weiter unten kannst du auf deinem PC testen.",
        "c_ai": "KI / Modell", "c_kind": "Art", "c_speed": "Tempo",
        "c_q": "Qualität", "c_note": "Hinweise",
        "k_local": "🖥 Lokal", "k_cloud": "☁ Cloud",
        "k_mt": "🌐 Übersetzer",
        "untested": "⏳ Diesmal nicht getestet (kein Zugang oder Limit "
                    "während des Tests erreicht): {l}.",
        "n_g3_4b": "Beste lokale Übersetzung (versteht Gaming-Slang). "
                   "Braucht ~3 GB freien Grafikspeicher bei offenem Spiel.",
        "n_g2_2b": "Empfohlene lokale Wahl: gut und leicht (1,6 GB).",
        "n_l32_3b": "Gut, etwas wörtlich.",
        "n_g3_1b": "Schnell, erfindet aber Text und lässt russische Wörter "
                   "stehen. Nicht empfohlen.",
        "n_q25_15": "Vertauscht Zeilen und erfindet Text; schwach in "
                    "Russisch.",
        "n_q25_3": "Langsamer und setzt chinesische Wörter in die "
                   "Übersetzung.",
        "n_ling": "Sehr natürlich ('leaving the party'). Kostenlos, 20 "
                  "Anfragen/min.",
        "n_nemo": "Gut; manchmal wörtlich ('rains with party').",
        "n_light": "Schreibt Russisch manchmal nur in lateinischen "
                   "Buchstaben statt zu übersetzen.",
        "n_allam": "Extrem schnell, antwortet aber manchmal auf Arabisch "
                   "(die App übersetzt diese Zeilen jetzt erneut). Lieber "
                   "ein anderes Modell.",
        "n_google": "Schnell und kostenlos, ohne Schlüssel. Wörtlich bei "
                    "Gaming-Slang.",
        "n_nllb": "Offline (Prozessor), ordentlich.",
        "n_argos": "Offline und leicht; manchmal ein falsches Wort "
                   "('heater' statt healer).",
    },
    "ru": {
        "title": "📊 Оценки ИИ — проверены с этим приложением",
        "intro": "Одни и те же 26 настоящих сообщений из чата RF (русский, "
                 "португальский, испанский, английский, объявления WTS/WTB "
                 "с [предметами], сленг) переведены на английский самим "
                 "приложением. Локальный ИИ — на видеокарте 8 ГБ с "
                 "открытой игрой. Скорость: локальный = на сообщение; "
                 "облако и переводчики = на запрос из 6 строк. Проверено "
                 "{d}. Ниже можно проверить на своём ПК.",
        "c_ai": "ИИ / модель", "c_kind": "Тип", "c_speed": "Скорость",
        "c_q": "Качество", "c_note": "Заметки",
        "k_local": "🖥 Локальный", "k_cloud": "☁ Облако",
        "k_mt": "🌐 Переводчик",
        "untested": "⏳ В этот раз не проверены (нет доступа или лимит во "
                    "время проверки): {l}.",
        "n_g3_4b": "Лучший локальный перевод (понимает игровой сленг). "
                   "Нужно ~3 ГБ свободной видеопамяти с открытой игрой.",
        "n_g2_2b": "Рекомендуемый локальный вариант: хороший и лёгкий "
                   "(1,6 ГБ).",
        "n_l32_3b": "Хороший, немного буквальный.",
        "n_g3_1b": "Быстрый, но выдумывает текст и оставляет русские "
                   "слова. Не рекомендуется.",
        "n_q25_15": "Путает строки и выдумывает текст; слабый в русском.",
        "n_q25_3": "Медленнее и вставляет китайские слова в перевод.",
        "n_ling": "Очень естественно ('leaving the party'). Бесплатно, 20 "
                  "запросов/мин.",
        "n_nemo": "Хорошо; иногда буквально ('rains with party').",
        "n_light": "Иногда просто пишет русский латиницей вместо перевода.",
        "n_allam": "Очень быстрый, но иногда отвечает по-арабски "
                   "(приложение теперь переводит такие строки заново). "
                   "Лучше другую модель.",
        "n_google": "Быстрый и бесплатный, без ключа. Буквален с игровым "
                    "сленгом.",
        "n_nllb": "Офлайн (процессор), неплохо.",
        "n_argos": "Офлайн и лёгкий; иногда неверное слово ('heater' "
                   "вместо healer).",
    },
    "it": {
        "title": "📊 Valutazioni delle IA — provate con questa app",
        "intro": "Gli stessi 26 messaggi reali della chat di RF (russo, "
                 "portoghese, spagnolo, inglese, annunci WTS/WTB con "
                 "[oggetti], gergo) tradotti in inglese dall'app stessa. IA "
                 "locale su una scheda grafica da 8 GB con il gioco aperto. "
                 "Velocità: locale = per messaggio; cloud e traduttori = "
                 "per richiesta di 6 righe. Provato il {d}. Più sotto puoi "
                 "provare sul tuo PC.",
        "c_ai": "IA / modello", "c_kind": "Tipo", "c_speed": "Velocità",
        "c_q": "Qualità", "c_note": "Note",
        "k_local": "🖥 Locale", "k_cloud": "☁ Cloud",
        "k_mt": "🌐 Traduttore",
        "untested": "⏳ Non provati questa volta (nessun accesso o limite "
                    "raggiunto durante la prova): {l}.",
        "n_g3_4b": "La migliore traduzione locale (capisce il gergo dei "
                   "giochi). Servono ~3 GB liberi sulla scheda grafica con "
                   "il gioco aperto.",
        "n_g2_2b": "Scelta locale consigliata: buona e leggera (1,6 GB).",
        "n_l32_3b": "Buona, un po' letterale.",
        "n_g3_1b": "Veloce ma inventa testo e lascia parole in russo. "
                   "Sconsigliato.",
        "n_q25_15": "Scambia le righe e inventa testo; debole in russo.",
        "n_q25_3": "Più lento e mette parole cinesi nella traduzione.",
        "n_ling": "Molto naturale ('leaving the party'). Gratis, 20 "
                  "richieste/min.",
        "n_nemo": "Buono; a volte letterale ('rains with party').",
        "n_light": "A volte scrive solo il russo in lettere latine invece "
                   "di tradurre.",
        "n_allam": "Velocissimo, ma a volte risponde in arabo (ora l'app "
                   "ritraduce quelle righe). Meglio un altro modello.",
        "n_google": "Veloce e gratis, senza chiave. Letterale con il gergo "
                    "dei giochi.",
        "n_nllb": "Offline (processore), discreto.",
        "n_argos": "Offline e leggero; a volte una parola sbagliata "
                   "('heater' invece di healer).",
    },
}


def ratings_html(lang):
    t = TXT.get(lang) or TXT["en"]
    rows = "".join(
        f"<tr><td><b>{name}</b></td><td>{t['k_' + kind]}</td>"
        f"<td>{speed}</td><td>{'★' * stars}{'☆' * (5 - stars)}</td>"
        f"<td>{t[note]}</td></tr>"
        for name, kind, speed, stars, note in RATINGS)
    return f"""
<h2>{t['title']}</h2>
<p>{t['intro'].format(d=TESTED)}</p>
<table border="1" cellspacing="0" cellpadding="5" width="100%">
<tr><th>{t['c_ai']}</th><th>{t['c_kind']}</th><th>{t['c_speed']}</th>
<th>{t['c_q']}</th><th>{t['c_note']}</th></tr>
{rows}
</table>
<p><i>{t['untested'].format(l=', '.join(UNTESTED))}</i></p>
"""
