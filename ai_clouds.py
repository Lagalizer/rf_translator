# -*- coding: utf-8 -*-
"""
ai_clouds.py — guia '☁ AI Clouds' (aba da janela do manual): que IAs na
nuvem há, quais têm plano grátis, os limites, onde criar a chave e as
fontes. Nas 7 línguas da interface.

Limites verificados a 2026-10-02 nas páginas oficiais (ver SOURCES). Os
fornecedores mudam-nos sem avisar — o guia diz isso ao utilizador.
"""

CHECKED = "2026-10-04"

# Fontes oficiais dos limites (mostradas no fim do guia).
SOURCES = [
    [
        "OpenRouter",
        "https://openrouter.ai/docs/api-reference/limits"
    ],
    [
        "Mistral AI",
        "https://help.mistral.ai/en/articles/225174-what-are-the-limits-of-the-free-tier"
    ],
    [
        "Google Gemini",
        "https://ai.google.dev/gemini-api/docs/rate-limits"
    ],
    [
        "Google AI Studio",
        "https://aistudio.google.com/rate-limit"
    ],
    [
        "Groq",
        "https://console.groq.com/docs/rate-limits"
    ],
    [
        "Cerebras",
        "https://inference-docs.cerebras.ai/support/rate-limits"
    ],
    [
        "Groq free tier & Llama change",
        "https://klymentiev.com/blog/groq-pricing"
    ],
    [
        "Gemini free tier (Sept 2026)",
        "https://www.memetik.ai/guides/gemini-api-free-tier-limits"
    ],
    [
        "NVIDIA Build free API",
        "https://decodethefuture.org/en/nvidia-nim-api-pricing-limits-guide/"
    ],
    [
        "Cloudflare Workers AI free tier",
        "https://freellm.net/providers/cloudflare-workers-ai"
    ],
    [
        "Together AI free models",
        "https://www.promptfoo.dev/docs/providers/togetherai/"
    ],
    [
        "Cerebras free tier change",
        "https://costbench.com/software/llm-api-providers/cerebras-inference/free-plan/"
    ],
    [
        "SambaNova free tier change",
        "https://costbench.com/software/llm-api-providers/sambanova-cloud/free-plan/"
    ],
    [
        "Ollama model sizes",
        "https://ollama.com/library"
    ]
]

# Textos de cada língua. Os {marcadores} ficam iguais.
TXT = {
    "en": {
        "title": "☁ AI Clouds — which AI to use",
        "intro": "The chat and the voice can use a local AI (this PC) or an AI in the cloud. Here are the cloud AIs the app supports, which ones are free and how much they allow. To use one, create a key on the provider's site, paste it in the AI's panel (chat or voice), press <b>Test</b>, then choose it (or a ⭐ profile) for the chat or the voice.",
        "free_h": "Free plans",
        "paid_h": "Pay per use (cheap, no daily limit)",
        "local_h": "Local (no internet, no limit)",
        "col_ai": "AI",
        "col_free": "Free limit",
        "col_key": "Key",
        "col_tip": "Notes",
        "get": "create key",
        "or_lim": "50 requests/day without credits (1000/day after buying 10 credits once) · 20/min",
        "or_tip": "All <code>:free</code> models <b>share</b> the same daily count. ✅ Tested: Ling 3.0 Flash, Nemotron 3 Super 120B (turn “thinking” off).",
        "mi_lim": "about 1 request/second, no daily limit (1 billion tokens/month)",
        "mi_tip": "Free “Experiment” plan (needs phone verification). The best free option for a whole day. Profile ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: about 500 requests/day; Flash: only about 20/day (Sept 2026; your exact numbers are in AI Studio)",
        "ge_tip": "Free key from Google AI Studio. On the free plan Google may use what you send to improve its products.",
        "gr_lim": "allam-2-7b: about 1000 requests/day, 30/min. <b>Without a card</b> on the account, also gpt-oss-120b/20b and Qwen 3.6/3.8 27B (1000/day each)",
        "gr_tip": "Very fast (~0.3 s). With a card on the account the models with a price are billed: block them in console.groq.com → Settings → Limits (the app then shows them ⛔). Llama 3.1/3.3 are no longer available on free accounts (since 16 Aug 2026).",
        "ce_lim": "no permanent free models any more: $5 trial credit for 30 days (since mid-2026)",
        "ce_tip": "Very fast, but after the trial it is paid. SambaNova changed the same way (card + credits since Aug 2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity and Ollama Cloud charge per use. Translating chat costs cents per day with small models (e.g. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). The model list (🔄) shows the price of each one where the provider tells it.",
        "local_txt": "Ollama on this PC: free, private, works offline, no limit. gemma2:2b uses about 1.8 GB of graphics memory. Measured on an 8 GB graphics card with “GPU layers: Automatic”: 100% on the GPU, 45 tokens/s, about 0.6 s per message (CPU only: 8 tokens/s, 2.8 s).",
        "tips_h": "Tips",
        "tips": [
            "To play all day for free: <b>Local</b>, or <b>Mistral</b> for the chat, with a second AI (Groq or Gemini) as the fallback.",
            "Tick <b>If this AI fails, try the others that have a key</b>: when one hits its limit, the app moves to the next one by itself.",
            "<b>Lines per request</b> (chat options): 8–10 lines per request uses fewer of the free requests.",
            "Use a better AI for the <b>voice</b> (what you say goes straight into the game) and a free one for the chat."
        ],
        "src_h": "Sources (checked {d})",
        "src_note": "Providers change their free limits without notice: always check their page.",
        "nv_lim": "free for personal/test use, 40 requests/min per model, 80+ models (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Free NVIDIA Developer account, no card. Already in the app's AI list (NVIDIA). Profile ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10,000 “neurons”/day (about 80 answers), includes Llama 3.3 70B",
        "cf_tip": "Use a Custom server with the URL https://api.cloudflare.com/client/v4/accounts/<your account ID>/ai/v1 and a Workers AI token.",
        "col_card": "💳 Card?",
        "card_no": "No",
        "card_yes": "Yes",
        "card_dep": "Yes (card / small deposit)",
        "card_note": "Card? = whether you must register a card to use the free models.",
        "to_lim": "models ending in <code>-Free</code> (e.g. Llama 3.3 70B Instruct Turbo Free): free, 6 requests/min",
        "to_tip": "Already in the app's AI list (Together AI); the -Free models show green. Set Requests/min to 5.",
        "loc_h": "Local models: which one for your PC",
        "loc_intro": "No local model comes with the app: download one with 🤗 or <code>ollama pull &lt;name&gt;</code>. The game also needs graphics memory (VRAM), so leave room for it. Rule of thumb: free VRAM ≥ download size + about 1 GB. A model that does not fit is split between the GPU and the CPU and gets several times slower. RAM: at least the download size + 4 GB free. The app keeps only one model loaded.",
        "col_model": "Model",
        "col_size": "Download",
        "col_needs": "Graphics card (VRAM) / RAM",
        "col_result": "Result with this app",
        "need_g2": "4 GB or more · or CPU only with 8 GB RAM",
        "res_g2": "✅ Tested, recommended. Best of the small ones in Russian and other languages. 8 GB card with the game open: 0.6 s per message (CPU only: 2.8 s).",
        "need_q15": "2 GB or more · or CPU only",
        "res_q15": "⚠️ Tested: fast (~1.3 s), but in groups of lines it mixes them up and invents text; weak in Russian.",
        "need_q3": "4 GB or more",
        "res_q3": "❌ Tested: slower (~3.8 s) and mixes Chinese words into the translation.",
        "need_6": "6 GB or more",
        "need_8": "8 GB or more (with the game: 10–12 GB)",
        "need_12": "12 GB or more",
        "need_16": "16 GB or more",
        "res_next": "⏳ Not tested here. The next step up from gemma2:2b if you have VRAM to spare.",
        "res_g34": "✅ Tested: the best local translation (understands gaming slang). 8 GB card with the game open: 3.4 s per message.",
        "res_l32": "✅ Tested: good, a little literal. 8 GB card with the game open: 2.0 s per message.",
        "res_g31": "❌ Tested: fast (1.4 s) but invents text and leaves Russian words.",
        "res_untested": "⏳ Not tested here. Better translations, but slower; leave enough VRAM for the game."
    },
    "pt": {
        "title": "☁ AI Clouds — que IA usar",
        "intro": "O chat e a voz podem usar uma IA local (este PC) ou uma IA na nuvem. Aqui estão as IAs na nuvem que a app aceita, quais são grátis e quanto deixam usar. Para usar uma, cria uma chave no site do fornecedor, cola-a no painel da IA (chat ou voz), carrega em <b>Testar</b> e escolhe-a (ou um perfil ⭐) para o chat ou para a voz.",
        "free_h": "Planos grátis",
        "paid_h": "Pagas ao uso (baratas, sem limite diário)",
        "local_h": "Local (sem internet, sem limite)",
        "col_ai": "IA",
        "col_free": "Limite grátis",
        "col_key": "Chave",
        "col_tip": "Notas",
        "get": "criar chave",
        "or_lim": "50 pedidos/dia sem créditos (1000/dia depois de comprar 10 créditos uma vez) · 20/min",
        "or_tip": "Todos os modelos <code>:free</code> <b>partilham</b> a mesma contagem diária. ✅ Testados: Ling 3.0 Flash, Nemotron 3 Super 120B (com o «pensar» desligado).",
        "mi_lim": "cerca de 1 pedido/segundo, sem limite diário (mil milhões de tokens/mês)",
        "mi_tip": "Plano grátis «Experiment» (pede verificação por telemóvel). A melhor opção grátis para o dia todo. Perfil ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: cerca de 500 pedidos/dia; Flash: só cerca de 20/dia (set. 2026; os teus números exatos estão no AI Studio)",
        "ge_tip": "Chave grátis do Google AI Studio. No plano grátis a Google pode usar o que envias para melhorar os seus produtos.",
        "gr_lim": "allam-2-7b: cerca de 1000 pedidos/dia, 30/min. <b>Sem cartão</b> na conta, também gpt-oss-120b/20b e Qwen 3.6/3.8 27B (1000/dia cada)",
        "gr_tip": "Muito rápida (~0,3 s). Com cartão na conta os modelos com preço são cobrados: bloqueia-os em console.groq.com → Settings → Limits (a app mostra-os ⛔). Os Llama 3.1/3.3 já não estão disponíveis em contas grátis (desde 16/08/2026).",
        "ce_lim": "já não tem modelos grátis permanentes: 5 $ de crédito de experiência por 30 dias (desde meados de 2026)",
        "ce_tip": "Muito rápida, mas depois da experiência é paga. O SambaNova mudou da mesma forma (cartão + créditos desde ago/2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity e Ollama Cloud cobram ao uso. Traduzir o chat custa cêntimos por dia com modelos pequenos (ex.: deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). A lista de modelos (🔄) mostra o preço de cada um quando o fornecedor o diz.",
        "local_txt": "Ollama neste PC: grátis, privada, funciona sem internet, sem limite. O gemma2:2b usa cerca de 1,8 GB de memória gráfica. Medido numa placa gráfica de 8 GB com «Camadas na GPU: Automático»: 100% na GPU, 45 tokens/s, cerca de 0,6 s por mensagem (só CPU: 8 tokens/s, 2,8 s).",
        "tips_h": "Dicas",
        "tips": [
            "Para jogar o dia todo sem pagar: <b>Local</b>, ou <b>Mistral</b> no chat, com uma segunda IA (Groq ou Gemini) de reserva.",
            "Marca <b>Se esta IA falhar, usar as outras que têm chave</b>: quando uma chega ao limite, a app passa sozinha para a seguinte.",
            "<b>Linhas por pedido</b> (opções do chat): 8–10 linhas por pedido gasta menos pedidos grátis.",
            "Usa uma IA melhor para a <b>voz</b> (o que dizes vai direto para o jogo) e uma grátis para o chat."
        ],
        "src_h": "Fontes (verificadas a {d})",
        "src_note": "Os fornecedores mudam os limites grátis sem avisar: confirma sempre na página deles.",
        "nv_lim": "grátis para uso pessoal/testes, 40 pedidos/min por modelo, +80 modelos (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Conta NVIDIA Developer grátis, sem cartão. Já está na lista de IAs da app (NVIDIA). Perfil ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10 000 «neurónios»/dia (cerca de 80 respostas), inclui o Llama 3.3 70B",
        "cf_tip": "Usa um Servidor próprio com o URL https://api.cloudflare.com/client/v4/accounts/<o teu account ID>/ai/v1 e um token do Workers AI.",
        "col_card": "💳 Cartão?",
        "card_no": "Não",
        "card_yes": "Sim",
        "card_dep": "Sim (cartão / pequeno depósito)",
        "card_note": "Cartão? = se é preciso registar um cartão para usar os modelos grátis.",
        "to_lim": "modelos que acabam em <code>-Free</code> (ex.: Llama 3.3 70B Instruct Turbo Free): grátis, 6 pedidos/min",
        "to_tip": "Já está na lista de IAs da app (Together AI); os -Free aparecem a verde. Põe Pedidos/min em 5.",
        "loc_h": "Modelos locais: qual para o teu PC",
        "loc_intro": "A app não traz nenhum modelo local: descarrega um com 🤗 ou <code>ollama pull &lt;nome&gt;</code>. O jogo também precisa de memória gráfica (VRAM), por isso deixa-lhe espaço. Regra prática: VRAM livre ≥ tamanho do download + cerca de 1 GB. Um modelo que não cabe é dividido entre a GPU e o CPU e fica várias vezes mais lento. RAM: pelo menos o tamanho do download + 4 GB livres. A app só mantém um modelo carregado.",
        "col_model": "Modelo",
        "col_size": "Download",
        "col_needs": "Placa gráfica (VRAM) / RAM",
        "col_result": "Resultado nesta app",
        "need_g2": "4 GB ou mais · ou só CPU com 8 GB de RAM",
        "res_g2": "✅ Testado, recomendado. O melhor dos pequenos em russo e noutras línguas. Placa de 8 GB com o jogo aberto: 0,6 s por mensagem (só CPU: 2,8 s).",
        "need_q15": "2 GB ou mais · ou só CPU",
        "res_q15": "⚠️ Testado: rápido (~1,3 s), mas em grupos de linhas troca-as e inventa texto; fraco em russo.",
        "need_q3": "4 GB ou mais",
        "res_q3": "❌ Testado: mais lento (~3,8 s) e mete palavras em chinês na tradução.",
        "need_6": "6 GB ou mais",
        "need_8": "8 GB ou mais (com o jogo: 10–12 GB)",
        "need_12": "12 GB ou mais",
        "need_16": "16 GB ou mais",
        "res_next": "⏳ Não testado aqui. O passo seguinte ao gemma2:2b se tiveres VRAM de sobra.",
        "res_g34": "✅ Testado: a melhor tradução local (percebe a gíria dos jogos). Placa de 8 GB com o jogo aberto: 3,4 s por mensagem.",
        "res_l32": "✅ Testado: bom, um pouco literal. Placa de 8 GB com o jogo aberto: 2,0 s por mensagem.",
        "res_g31": "❌ Testado: rápido (1,4 s) mas inventa texto e deixa palavras em russo.",
        "res_untested": "⏳ Não testado aqui. Traduções melhores, mas mais lento; deixa VRAM suficiente para o jogo."
    },
    "es": {
        "title": "☁ AI Clouds — qué IA usar",
        "intro": "El chat y la voz pueden usar una IA local (este PC) o una IA en la nube. Aquí están las IA en la nube que admite la app, cuáles son gratis y cuánto permiten. Para usar una, crea una clave en la web del proveedor, pégala en el panel de la IA (chat o voz), pulsa <b>Probar</b> y elígela (o un perfil ⭐) para el chat o la voz.",
        "free_h": "Planes gratis",
        "paid_h": "De pago por uso (baratas, sin límite diario)",
        "local_h": "Local (sin internet, sin límite)",
        "col_ai": "IA",
        "col_free": "Límite gratis",
        "col_key": "Clave",
        "col_tip": "Notas",
        "get": "crear clave",
        "or_lim": "50 peticiones/día sin créditos (1000/día tras comprar 10 créditos una vez) · 20/min",
        "or_tip": "Todos los modelos <code>:free</code> <b>comparten</b> el mismo contador diario. ✅ Probados: Ling 3.0 Flash, Nemotron 3 Super 120B (con el «pensar» desactivado).",
        "mi_lim": "1 petición/segundo aprox., sin límite diario (mil millones de tokens/mes)",
        "mi_tip": "Plan gratis «Experiment» (pide verificación por teléfono). La mejor opción gratis para todo el día. Perfil ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: unas 500 peticiones/día; Flash: solo unas 20/día (sept. 2026; tus cifras exactas están en AI Studio)",
        "ge_tip": "Clave gratis de Google AI Studio. En el plan gratis Google puede usar lo que envías para mejorar sus productos.",
        "gr_lim": "allam-2-7b: unas 1000 peticiones/día, 30/min. <b>Sin tarjeta</b> en la cuenta, también gpt-oss-120b/20b y Qwen 3.6/3.8 27B (1000/día cada uno)",
        "gr_tip": "Muy rápida (~0,3 s). Con tarjeta en la cuenta se cobran los modelos con precio: bloquéalos en console.groq.com → Settings → Limits (la app los muestra ⛔). Los Llama 3.1/3.3 ya no están en cuentas gratis (desde el 16/08/2026).",
        "ce_lim": "ya no tiene modelos gratis permanentes: 5 $ de crédito de prueba durante 30 días (desde mediados de 2026)",
        "ce_tip": "Muy rápida, pero tras la prueba es de pago. SambaNova cambió igual (tarjeta + créditos desde ago/2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity y Ollama Cloud cobran por uso. Traducir el chat cuesta céntimos al día con modelos pequeños (p. ej. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). La lista de modelos (🔄) muestra el precio de cada uno cuando el proveedor lo indica.",
        "local_txt": "Ollama en este PC: gratis, privada, funciona sin internet, sin límite. gemma2:2b usa unos 1,8 GB de memoria gráfica. Medido en una tarjeta gráfica de 8 GB con «Capas en GPU: Automático»: 100% en la GPU, 45 tokens/s, unos 0,6 s por mensaje (solo CPU: 8 tokens/s, 2,8 s).",
        "tips_h": "Consejos",
        "tips": [
            "Para jugar todo el día gratis: <b>Local</b>, o <b>Mistral</b> en el chat, con una segunda IA (Groq o Gemini) de reserva.",
            "Marca <b>Si esta IA falla, usar las otras que tienen clave</b>: cuando una llega al límite, la app pasa sola a la siguiente.",
            "<b>Líneas por petición</b> (opciones del chat): 8–10 líneas por petición gasta menos peticiones gratis.",
            "Usa una IA mejor para la <b>voz</b> (lo que dices va directo al juego) y una gratis para el chat."
        ],
        "src_h": "Fuentes (comprobadas el {d})",
        "src_note": "Los proveedores cambian los límites gratis sin avisar: compruébalo siempre en su página.",
        "nv_lim": "gratis para uso personal/pruebas, 40 peticiones/min por modelo, +80 modelos (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Cuenta NVIDIA Developer gratis, sin tarjeta. Ya está en la lista de IA de la app (NVIDIA). Perfil ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10 000 «neuronas»/día (unas 80 respuestas), incluye Llama 3.3 70B",
        "cf_tip": "Usa un Servidor propio con la URL https://api.cloudflare.com/client/v4/accounts/<tu account ID>/ai/v1 y un token de Workers AI.",
        "col_card": "💳 ¿Tarjeta?",
        "card_no": "No",
        "card_yes": "Sí",
        "card_dep": "Sí (tarjeta / pequeño depósito)",
        "card_note": "¿Tarjeta? = si hay que registrar una tarjeta para usar los modelos gratis.",
        "to_lim": "modelos que terminan en <code>-Free</code> (p. ej. Llama 3.3 70B Instruct Turbo Free): gratis, 6 peticiones/min",
        "to_tip": "Ya está en la lista de IA de la app (Together AI); los -Free salen en verde. Pon Peticiones/min en 5.",
        "loc_h": "Modelos locales: cuál para tu PC",
        "loc_intro": "La app no trae ningún modelo local: descarga uno con 🤗 o <code>ollama pull &lt;nombre&gt;</code>. El juego también necesita memoria gráfica (VRAM), así que déjale espacio. Regla práctica: VRAM libre ≥ tamaño de la descarga + 1 GB aprox. Un modelo que no cabe se reparte entre la GPU y la CPU y va varias veces más lento. RAM: al menos el tamaño de la descarga + 4 GB libres. La app solo mantiene un modelo cargado.",
        "col_model": "Modelo",
        "col_size": "Descarga",
        "col_needs": "Tarjeta gráfica (VRAM) / RAM",
        "col_result": "Resultado en esta app",
        "need_g2": "4 GB o más · o solo CPU con 8 GB de RAM",
        "res_g2": "✅ Probado, recomendado. El mejor de los pequeños en ruso y otros idiomas. Tarjeta de 8 GB con el juego abierto: 0,6 s por mensaje (solo CPU: 2,8 s).",
        "need_q15": "2 GB o más · o solo CPU",
        "res_q15": "⚠️ Probado: rápido (~1,3 s), pero en grupos de líneas las mezcla e inventa texto; flojo en ruso.",
        "need_q3": "4 GB o más",
        "res_q3": "❌ Probado: más lento (~3,8 s) y mete palabras en chino en la traducción.",
        "need_6": "6 GB o más",
        "need_8": "8 GB o más (con el juego: 10–12 GB)",
        "need_12": "12 GB o más",
        "need_16": "16 GB o más",
        "res_next": "⏳ No probado aquí. El siguiente paso tras gemma2:2b si te sobra VRAM.",
        "res_g34": "✅ Probado: la mejor traducción local (entiende la jerga de juegos). Tarjeta de 8 GB con el juego abierto: 3,4 s por mensaje.",
        "res_l32": "✅ Probado: bueno, un poco literal. Tarjeta de 8 GB con el juego abierto: 2,0 s por mensaje.",
        "res_g31": "❌ Probado: rápido (1,4 s) pero inventa texto y deja palabras en ruso.",
        "res_untested": "⏳ No probado aquí. Mejores traducciones, pero más lento; deja VRAM suficiente para el juego."
    },
    "fr": {
        "title": "☁ AI Clouds — quelle IA utiliser",
        "intro": "Le chat et la voix peuvent utiliser une IA locale (ce PC) ou une IA cloud. Voici les IA cloud acceptées par l'app, celles qui sont gratuites et ce qu'elles permettent. Pour en utiliser une, crée une clé sur le site du fournisseur, colle-la dans le panneau de l'IA (chat ou voix), clique sur <b>Tester</b>, puis choisis-la (ou un profil ⭐) pour le chat ou la voix.",
        "free_h": "Offres gratuites",
        "paid_h": "Payantes à l'usage (bon marché, sans limite quotidienne)",
        "local_h": "Local (sans internet, sans limite)",
        "col_ai": "IA",
        "col_free": "Limite gratuite",
        "col_key": "Clé",
        "col_tip": "Remarques",
        "get": "créer une clé",
        "or_lim": "50 requêtes/jour sans crédits (1000/jour après avoir acheté 10 crédits une fois) · 20/min",
        "or_tip": "Tous les modèles <code>:free</code> <b>partagent</b> le même compteur quotidien. ✅ Testés : Ling 3.0 Flash, Nemotron 3 Super 120B (« réflexion » désactivée).",
        "mi_lim": "environ 1 requête/seconde, sans limite quotidienne (1 milliard de tokens/mois)",
        "mi_tip": "Offre gratuite « Experiment » (vérification par téléphone). La meilleure option gratuite pour toute la journée. Profil ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite : environ 500 requêtes/jour ; Flash : seulement ~20/jour (sept. 2026 ; tes chiffres exacts sont dans AI Studio)",
        "ge_tip": "Clé gratuite de Google AI Studio. Avec l'offre gratuite, Google peut utiliser ce que tu envoies pour améliorer ses produits.",
        "gr_lim": "allam-2-7b : environ 1000 requêtes/jour, 30/min. <b>Sans carte</b> sur le compte, aussi gpt-oss-120b/20b et Qwen 3.6/3.8 27B (1000/jour chacun)",
        "gr_tip": "Très rapide (~0,3 s). Avec une carte sur le compte, les modèles avec prix sont facturés : bloque-les dans console.groq.com → Settings → Limits (l'app les affiche ⛔). Llama 3.1/3.3 ne sont plus disponibles sur les comptes gratuits (depuis le 16/08/2026).",
        "ce_lim": "plus de modèles gratuits permanents : 5 $ de crédit d'essai pendant 30 jours (depuis mi-2026)",
        "ce_tip": "Très rapide, mais payante après l'essai. SambaNova a changé de la même façon (carte + crédits depuis août 2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity et Ollama Cloud sont payants à l'usage. Traduire le chat coûte quelques centimes par jour avec de petits modèles (ex. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). La liste des modèles (🔄) affiche le prix de chacun quand le fournisseur l'indique.",
        "local_txt": "Ollama sur ce PC : gratuit, privé, fonctionne hors ligne, sans limite. gemma2:2b utilise environ 1,8 Go de mémoire graphique. Mesuré sur une carte graphique de 8 Go avec « Couches GPU : Automatique » : 100 % sur le GPU, 45 tokens/s, environ 0,6 s par message (CPU seul : 8 tokens/s, 2,8 s).",
        "tips_h": "Conseils",
        "tips": [
            "Pour jouer toute la journée gratuitement : <b>Local</b>, ou <b>Mistral</b> pour le chat, avec une deuxième IA (Groq ou Gemini) en secours.",
            "Coche <b>Si cette IA échoue, utiliser les autres qui ont une clé</b> : quand une atteint sa limite, l'app passe seule à la suivante.",
            "<b>Lignes par requête</b> (options du chat) : 8–10 lignes par requête consomme moins de requêtes gratuites.",
            "Utilise une meilleure IA pour la <b>voix</b> (ce que tu dis va directement dans le jeu) et une gratuite pour le chat."
        ],
        "src_h": "Sources (vérifiées le {d})",
        "src_note": "Les fournisseurs changent leurs limites gratuites sans prévenir : vérifie toujours leur page.",
        "nv_lim": "gratuit pour usage perso/tests, 40 requêtes/min par modèle, +80 modèles (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Compte NVIDIA Developer gratuit, sans carte. Déjà dans la liste des IA de l'app (NVIDIA). Profil ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10 000 « neurones »/jour (environ 80 réponses), inclut Llama 3.3 70B",
        "cf_tip": "Utilise un Serveur perso avec l'URL https://api.cloudflare.com/client/v4/accounts/<ton account ID>/ai/v1 et un jeton Workers AI.",
        "col_card": "💳 Carte ?",
        "card_no": "Non",
        "card_yes": "Oui",
        "card_dep": "Oui (carte / petit dépôt)",
        "card_note": "Carte ? = s'il faut enregistrer une carte pour utiliser les modèles gratuits.",
        "to_lim": "modèles finissant par <code>-Free</code> (ex. Llama 3.3 70B Instruct Turbo Free) : gratuits, 6 requêtes/min",
        "to_tip": "Déjà dans la liste des IA de l'app (Together AI) ; les -Free sont en vert. Mets Requêtes/min à 5.",
        "loc_h": "Modèles locaux : lequel pour ton PC",
        "loc_intro": "L'app ne fournit aucun modèle local : télécharges-en un avec 🤗 ou <code>ollama pull &lt;nom&gt;</code>. Le jeu a aussi besoin de mémoire graphique (VRAM), laisse-lui de la place. Règle simple : VRAM libre ≥ taille du téléchargement + environ 1 Go. Un modèle qui ne tient pas est partagé entre le GPU et le CPU et devient plusieurs fois plus lent. RAM : au moins la taille du téléchargement + 4 Go libres. L'app ne garde qu'un modèle chargé.",
        "col_model": "Modèle",
        "col_size": "Téléchargement",
        "col_needs": "Carte graphique (VRAM) / RAM",
        "col_result": "Résultat avec cette app",
        "need_g2": "4 Go ou plus · ou CPU seul avec 8 Go de RAM",
        "res_g2": "✅ Testé, recommandé. Le meilleur des petits en russe et dans d'autres langues. Carte de 8 Go avec le jeu ouvert : 0,6 s par message (CPU seul : 2,8 s).",
        "need_q15": "2 Go ou plus · ou CPU seul",
        "res_q15": "⚠️ Testé : rapide (~1,3 s), mais sur plusieurs lignes il les mélange et invente du texte ; faible en russe.",
        "need_q3": "4 Go ou plus",
        "res_q3": "❌ Testé : plus lent (~3,8 s) et glisse des mots chinois dans la traduction.",
        "need_6": "6 Go ou plus",
        "need_8": "8 Go ou plus (avec le jeu : 10–12 Go)",
        "need_12": "12 Go ou plus",
        "need_16": "16 Go ou plus",
        "res_next": "⏳ Pas testé ici. L'étape suivante après gemma2:2b si tu as de la VRAM en trop.",
        "res_g34": "✅ Testé : la meilleure traduction locale (comprend l'argot des jeux). Carte de 8 Go avec le jeu ouvert : 3,4 s par message.",
        "res_l32": "✅ Testé : bon, un peu littéral. Carte de 8 Go avec le jeu ouvert : 2,0 s par message.",
        "res_g31": "❌ Testé : rapide (1,4 s) mais invente du texte et laisse des mots en russe.",
        "res_untested": "⏳ Pas testé ici. Meilleures traductions, mais plus lent ; laisse assez de VRAM au jeu."
    },
    "de": {
        "title": "☁ AI Clouds — welche KI nutzen",
        "intro": "Chat und Stimme können eine lokale KI (dieser PC) oder eine Cloud-KI nutzen. Hier sind die Cloud-KIs, die die App unterstützt, welche kostenlos sind und wie viel sie erlauben. Zum Nutzen: auf der Seite des Anbieters einen Schlüssel erstellen, im Feld der KI (Chat oder Stimme) einfügen, <b>Testen</b> drücken und sie (oder ein ⭐-Profil) für Chat oder Stimme wählen.",
        "free_h": "Kostenlose Pläne",
        "paid_h": "Bezahlung nach Nutzung (günstig, kein Tageslimit)",
        "local_h": "Lokal (ohne Internet, ohne Limit)",
        "col_ai": "KI",
        "col_free": "Kostenloses Limit",
        "col_key": "Schlüssel",
        "col_tip": "Hinweise",
        "get": "Schlüssel erstellen",
        "or_lim": "50 Anfragen/Tag ohne Credits (1000/Tag nach einmaligem Kauf von 10 Credits) · 20/min",
        "or_tip": "Alle <code>:free</code>-Modelle <b>teilen sich</b> denselben Tageszähler. ✅ Getestet: Ling 3.0 Flash, Nemotron 3 Super 120B („Denken“ aus).",
        "mi_lim": "etwa 1 Anfrage/Sekunde, kein Tageslimit (1 Milliarde Tokens/Monat)",
        "mi_tip": "Kostenloser „Experiment“-Plan (Telefon-Verifizierung nötig). Die beste kostenlose Option für den ganzen Tag. Profil ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: etwa 500 Anfragen/Tag; Flash: nur etwa 20/Tag (Sept. 2026; genaue Werte in AI Studio)",
        "ge_tip": "Kostenloser Schlüssel von Google AI Studio. Im kostenlosen Plan darf Google das Gesendete zur Verbesserung seiner Produkte nutzen.",
        "gr_lim": "allam-2-7b: etwa 1000 Anfragen/Tag, 30/min. <b>Ohne Karte</b> im Konto auch gpt-oss-120b/20b und Qwen 3.6/3.8 27B (je 1000/Tag)",
        "gr_tip": "Sehr schnell (~0,3 s). Mit Karte im Konto werden Modelle mit Preis berechnet: sperre sie unter console.groq.com → Settings → Limits (die App zeigt sie ⛔). Llama 3.1/3.3 gibt es seit 16.08.2026 nicht mehr für kostenlose Konten.",
        "ce_lim": "keine dauerhaft kostenlosen Modelle mehr: 5 $ Testguthaben für 30 Tage (seit Mitte 2026)",
        "ce_tip": "Sehr schnell, aber nach dem Test kostenpflichtig. SambaNova hat sich genauso geändert (Karte + Guthaben seit Aug. 2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity und Ollama Cloud rechnen nach Nutzung ab. Chat übersetzen kostet mit kleinen Modellen Cent-Beträge pro Tag (z. B. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). Die Modellliste (🔄) zeigt den Preis, wenn der Anbieter ihn angibt.",
        "local_txt": "Ollama auf diesem PC: kostenlos, privat, offline nutzbar, ohne Limit. gemma2:2b braucht etwa 1,8 GB Grafikspeicher. Gemessen auf einer 8-GB-Grafikkarte mit „GPU-Schichten: Automatisch“: 100 % auf der GPU, 45 Tokens/s, etwa 0,6 s pro Nachricht (nur CPU: 8 Tokens/s, 2,8 s).",
        "tips_h": "Tipps",
        "tips": [
            "Den ganzen Tag kostenlos spielen: <b>Lokal</b>, oder <b>Mistral</b> für den Chat, mit einer zweiten KI (Groq oder Gemini) als Reserve.",
            "Hake <b>Wenn diese KI ausfällt, die anderen mit Schlüssel nutzen</b> an: erreicht eine ihr Limit, wechselt die App selbst zur nächsten.",
            "<b>Zeilen pro Anfrage</b> (Chat-Optionen): 8–10 Zeilen pro Anfrage verbraucht weniger kostenlose Anfragen.",
            "Nimm eine bessere KI für die <b>Stimme</b> (was du sagst, geht direkt ins Spiel) und eine kostenlose für den Chat."
        ],
        "src_h": "Quellen (geprüft am {d})",
        "src_note": "Anbieter ändern ihre kostenlosen Limits ohne Vorwarnung: prüfe immer ihre Seite.",
        "nv_lim": "kostenlos für private Nutzung/Tests, 40 Anfragen/min pro Modell, 80+ Modelle (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Kostenloses NVIDIA-Developer-Konto, ohne Karte. Schon in der KI-Liste der App (NVIDIA). Profil ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10.000 „Neurons“/Tag (etwa 80 Antworten), inkl. Llama 3.3 70B",
        "cf_tip": "Nutze einen eigenen Server mit der URL https://api.cloudflare.com/client/v4/accounts/<deine Account-ID>/ai/v1 und einem Workers-AI-Token.",
        "col_card": "💳 Karte?",
        "card_no": "Nein",
        "card_yes": "Ja",
        "card_dep": "Ja (Karte / kleine Einzahlung)",
        "card_note": "Karte? = ob man eine Karte hinterlegen muss, um die kostenlosen Modelle zu nutzen.",
        "to_lim": "Modelle mit <code>-Free</code> am Ende (z. B. Llama 3.3 70B Instruct Turbo Free): kostenlos, 6 Anfragen/min",
        "to_tip": "Schon in der KI-Liste der App (Together AI); die -Free-Modelle sind grün. Anfragen/min auf 5 stellen.",
        "loc_h": "Lokale Modelle: welches für deinen PC",
        "loc_intro": "Die App bringt kein lokales Modell mit: lade eines mit 🤗 oder <code>ollama pull &lt;Name&gt;</code>. Das Spiel braucht auch Grafikspeicher (VRAM), lass ihm Platz. Faustregel: freier VRAM ≥ Downloadgröße + etwa 1 GB. Ein Modell, das nicht passt, wird zwischen GPU und CPU aufgeteilt und ist um ein Vielfaches langsamer. RAM: mindestens Downloadgröße + 4 GB frei. Die App hält nur ein Modell geladen.",
        "col_model": "Modell",
        "col_size": "Download",
        "col_needs": "Grafikkarte (VRAM) / RAM",
        "col_result": "Ergebnis mit dieser App",
        "need_g2": "ab 4 GB · oder nur CPU mit 8 GB RAM",
        "res_g2": "✅ Getestet, empfohlen. Das beste kleine Modell für Russisch und andere Sprachen. 8-GB-Karte bei offenem Spiel: 0,6 s pro Nachricht (nur CPU: 2,8 s).",
        "need_q15": "ab 2 GB · oder nur CPU",
        "res_q15": "⚠️ Getestet: schnell (~1,3 s), vertauscht aber bei mehreren Zeilen und erfindet Text; schwach in Russisch.",
        "need_q3": "ab 4 GB",
        "res_q3": "❌ Getestet: langsamer (~3,8 s) und mischt chinesische Wörter in die Übersetzung.",
        "need_6": "ab 6 GB",
        "need_8": "ab 8 GB (mit dem Spiel: 10–12 GB)",
        "need_12": "ab 12 GB",
        "need_16": "ab 16 GB",
        "res_next": "⏳ Hier nicht getestet. Der nächste Schritt nach gemma2:2b, wenn VRAM übrig ist.",
        "res_g34": "✅ Getestet: die beste lokale Übersetzung (versteht Gaming-Slang). 8-GB-Karte bei offenem Spiel: 3,4 s pro Nachricht.",
        "res_l32": "✅ Getestet: gut, etwas wörtlich. 8-GB-Karte bei offenem Spiel: 2,0 s pro Nachricht.",
        "res_g31": "❌ Getestet: schnell (1,4 s), erfindet aber Text und lässt russische Wörter stehen.",
        "res_untested": "⏳ Hier nicht getestet. Bessere Übersetzungen, aber langsamer; lass genug VRAM für das Spiel."
    },
    "ru": {
        "title": "☁ AI Clouds — какой ИИ выбрать",
        "intro": "Чат и голос могут использовать локальный ИИ (этот ПК) или облачный. Здесь облачные ИИ, которые поддерживает приложение, какие из них бесплатные и сколько они позволяют. Чтобы подключить: создайте ключ на сайте провайдера, вставьте его в панель ИИ (чат или голос), нажмите <b>Проверить</b> и выберите его (или ⭐-профиль) для чата или голоса.",
        "free_h": "Бесплатные планы",
        "paid_h": "Оплата за использование (дёшево, без дневного лимита)",
        "local_h": "Локально (без интернета, без лимита)",
        "col_ai": "ИИ",
        "col_free": "Бесплатный лимит",
        "col_key": "Ключ",
        "col_tip": "Заметки",
        "get": "создать ключ",
        "or_lim": "50 запросов/день без кредитов (1000/день после разовой покупки 10 кредитов) · 20/мин",
        "or_tip": "Все модели <code>:free</code> <b>делят</b> один дневной счётчик. ✅ Проверены: Ling 3.0 Flash, Nemotron 3 Super 120B («размышление» выкл.).",
        "mi_lim": "около 1 запроса/сек, без дневного лимита (1 млрд токенов/мес.)",
        "mi_tip": "Бесплатный план «Experiment» (нужна проверка по телефону). Лучший бесплатный вариант на весь день. Профиль ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: около 500 запросов/день; Flash: всего около 20/день (сент. 2026; точные цифры — в AI Studio)",
        "ge_tip": "Бесплатный ключ из Google AI Studio. На бесплатном плане Google может использовать отправленное для улучшения своих продуктов.",
        "gr_lim": "allam-2-7b: около 1000 запросов/день, 30/мин. <b>Без карты</b> в аккаунте — также gpt-oss-120b/20b и Qwen 3.6/3.8 27B (по 1000/день)",
        "gr_tip": "Очень быстро (~0,3 с). Если к аккаунту привязана карта, модели с ценой оплачиваются: заблокируйте их в console.groq.com → Settings → Limits (приложение покажет их ⛔). Llama 3.1/3.3 больше недоступны на бесплатных аккаунтах (с 16.08.2026).",
        "ce_lim": "постоянных бесплатных моделей больше нет: $5 пробного кредита на 30 дней (с середины 2026)",
        "ce_tip": "Очень быстро, но после пробного периода платно. SambaNova изменилась так же (карта + кредиты с авг. 2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity и Ollama Cloud берут плату за использование. Перевод чата с маленькими моделями стоит центы в день (напр. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). Список моделей (🔄) показывает цену, если провайдер её сообщает.",
        "local_txt": "Ollama на этом ПК: бесплатно, приватно, без интернета, без лимита. gemma2:2b занимает около 1,8 ГБ видеопамяти. Замер на видеокарте 8 ГБ с «Слои на GPU: Авто»: 100% на GPU, 45 токенов/с, около 0,6 с на сообщение (только CPU: 8 токенов/с, 2,8 с).",
        "tips_h": "Советы",
        "tips": [
            "Чтобы играть весь день бесплатно: <b>локальный</b> ИИ или <b>Mistral</b> для чата, со вторым ИИ (Groq или Gemini) в запасе.",
            "Отметьте <b>Если этот ИИ не отвечает, использовать другие с ключом</b>: когда один упрётся в лимит, приложение само перейдёт к следующему.",
            "<b>Строк на запрос</b> (настройки чата): 8–10 строк на запрос расходует меньше бесплатных запросов.",
            "Возьмите ИИ получше для <b>голоса</b> (сказанное сразу уходит в игру) и бесплатный для чата."
        ],
        "src_h": "Источники (проверено {d})",
        "src_note": "Провайдеры меняют бесплатные лимиты без предупреждения: всегда сверяйтесь с их страницей.",
        "nv_lim": "бесплатно для личного использования/тестов, 40 запросов/мин на модель, 80+ моделей (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Бесплатный аккаунт NVIDIA Developer, без карты. Уже есть в списке ИИ приложения (NVIDIA). Профиль ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10 000 «нейронов»/день (около 80 ответов), включая Llama 3.3 70B",
        "cf_tip": "Используйте «Свой сервер» с URL https://api.cloudflare.com/client/v4/accounts/<ваш account ID>/ai/v1 и токеном Workers AI.",
        "col_card": "💳 Карта?",
        "card_no": "Нет",
        "card_yes": "Да",
        "card_dep": "Да (карта / небольшой депозит)",
        "card_note": "Карта? = нужно ли привязать карту, чтобы пользоваться бесплатными моделями.",
        "to_lim": "модели с окончанием <code>-Free</code> (напр. Llama 3.3 70B Instruct Turbo Free): бесплатно, 6 запросов/мин",
        "to_tip": "Уже есть в списке ИИ приложения (Together AI); модели -Free зелёные. Поставьте «Запросов/мин» = 5.",
        "loc_h": "Локальные модели: какая подойдёт вашему ПК",
        "loc_intro": "В приложении нет встроенной локальной модели: скачайте её через 🤗 или <code>ollama pull &lt;имя&gt;</code>. Игре тоже нужна видеопамять (VRAM), оставьте ей место. Простое правило: свободная VRAM ≥ размер загрузки + ~1 ГБ. Модель, которая не помещается, делится между GPU и CPU и работает в разы медленнее. ОЗУ: не меньше размера загрузки + 4 ГБ свободных. Приложение держит загруженной только одну модель.",
        "col_model": "Модель",
        "col_size": "Загрузка",
        "col_needs": "Видеокарта (VRAM) / ОЗУ",
        "col_result": "Результат в этом приложении",
        "need_g2": "от 4 ГБ · или только CPU с 8 ГБ ОЗУ",
        "res_g2": "✅ Проверена, рекомендуется. Лучшая из маленьких для русского и других языков. Карта 8 ГБ при открытой игре: 0,6 с на сообщение (только CPU: 2,8 с).",
        "need_q15": "от 2 ГБ · или только CPU",
        "res_q15": "⚠️ Проверена: быстрая (~1,3 с), но в пачке строк путает их и выдумывает текст; слабая в русском.",
        "need_q3": "от 4 ГБ",
        "res_q3": "❌ Проверена: медленнее (~3,8 с) и вставляет китайские слова в перевод.",
        "need_6": "от 6 ГБ",
        "need_8": "от 8 ГБ (с игрой: 10–12 ГБ)",
        "need_12": "от 12 ГБ",
        "need_16": "от 16 ГБ",
        "res_next": "⏳ Здесь не проверялась. Следующая ступень после gemma2:2b, если есть лишняя VRAM.",
        "res_g34": "✅ Проверено: лучший локальный перевод (понимает игровой сленг). Видеокарта 8 ГБ с открытой игрой: 3,4 с на сообщение.",
        "res_l32": "✅ Проверено: хорошо, немного буквально. Видеокарта 8 ГБ с открытой игрой: 2,0 с на сообщение.",
        "res_g31": "❌ Проверено: быстро (1,4 с), но выдумывает текст и оставляет русские слова.",
        "res_untested": "⏳ Здесь не проверялась. Перевод лучше, но медленнее; оставьте игре достаточно VRAM."
    },
    "it": {
        "title": "☁ AI Clouds — quale IA usare",
        "intro": "La chat e la voce possono usare un'IA locale (questo PC) o un'IA cloud. Ecco le IA cloud supportate dall'app, quali sono gratuite e quanto permettono. Per usarne una, crea una chiave sul sito del provider, incollala nel pannello dell'IA (chat o voce), premi <b>Prova</b> e sceglila (o un profilo ⭐) per la chat o la voce.",
        "free_h": "Piani gratuiti",
        "paid_h": "A pagamento a consumo (economiche, senza limite giornaliero)",
        "local_h": "Locale (senza internet, senza limite)",
        "col_ai": "IA",
        "col_free": "Limite gratuito",
        "col_key": "Chiave",
        "col_tip": "Note",
        "get": "crea chiave",
        "or_lim": "50 richieste/giorno senza crediti (1000/giorno dopo aver comprato 10 crediti una volta) · 20/min",
        "or_tip": "Tutti i modelli <code>:free</code> <b>condividono</b> lo stesso contatore giornaliero. ✅ Provati: Ling 3.0 Flash, Nemotron 3 Super 120B (con il «ragionamento» spento).",
        "mi_lim": "circa 1 richiesta/secondo, senza limite giornaliero (1 miliardo di token/mese)",
        "mi_tip": "Piano gratuito «Experiment» (serve la verifica col telefono). La migliore opzione gratuita per tutto il giorno. Profilo ⭐ Mistral · Small.",
        "ge_lim": "Flash-Lite: circa 500 richieste/giorno; Flash: solo circa 20/giorno (sett. 2026; i tuoi numeri esatti sono in AI Studio)",
        "ge_tip": "Chiave gratuita da Google AI Studio. Nel piano gratuito Google può usare ciò che invii per migliorare i suoi prodotti.",
        "gr_lim": "allam-2-7b: circa 1000 richieste/giorno, 30/min. <b>Senza carta</b> sull'account, anche gpt-oss-120b/20b e Qwen 3.6/3.8 27B (1000/giorno ciascuno)",
        "gr_tip": "Molto veloce (~0,3 s). Con una carta sull'account i modelli con prezzo si pagano: bloccali in console.groq.com → Settings → Limits (l'app li mostra ⛔). Llama 3.1/3.3 non sono più disponibili sugli account gratuiti (dal 16/08/2026).",
        "ce_lim": "non ha più modelli gratuiti permanenti: 5 $ di credito di prova per 30 giorni (da metà 2026)",
        "ce_tip": "Molto veloce, ma dopo la prova è a pagamento. SambaNova è cambiata allo stesso modo (carta + crediti da ago 2026).",
        "paid_txt": "DeepSeek, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), Qwen, Together, Fireworks, Perplexity e Ollama Cloud si pagano a consumo. Tradurre la chat costa centesimi al giorno con modelli piccoli (es. deepseek-chat, gpt-4.1-nano, claude-haiku, gemini flash-lite). L'elenco dei modelli (🔄) mostra il prezzo di ciascuno quando il provider lo indica.",
        "local_txt": "Ollama su questo PC: gratis, privata, funziona offline, senza limite. gemma2:2b usa circa 1,8 GB di memoria video. Misurato su una scheda video da 8 GB con «Livelli GPU: Automatico»: 100% sulla GPU, 45 token/s, circa 0,6 s per messaggio (solo CPU: 8 token/s, 2,8 s).",
        "tips_h": "Consigli",
        "tips": [
            "Per giocare tutto il giorno gratis: <b>Locale</b>, o <b>Mistral</b> per la chat, con una seconda IA (Groq o Gemini) di riserva.",
            "Spunta <b>Se questa IA fallisce, usa le altre che hanno una chiave</b>: quando una arriva al limite, l'app passa da sola alla successiva.",
            "<b>Righe per richiesta</b> (opzioni della chat): 8–10 righe per richiesta consuma meno richieste gratuite.",
            "Usa un'IA migliore per la <b>voce</b> (ciò che dici va dritto nel gioco) e una gratuita per la chat."
        ],
        "src_h": "Fonti (verificate il {d})",
        "src_note": "I provider cambiano i limiti gratuiti senza preavviso: controlla sempre la loro pagina.",
        "nv_lim": "gratis per uso personale/test, 40 richieste/min per modello, oltre 80 modelli (DeepSeek, Kimi, Gemma 4, Mistral, Nemotron…)",
        "nv_tip": "Account NVIDIA Developer gratuito, senza carta. Già nell'elenco delle IA dell'app (NVIDIA). Profilo ⭐ NVIDIA · DeepSeek V4.1 Flash.",
        "cf_lim": "10.000 «neuroni»/giorno (circa 80 risposte), include Llama 3.3 70B",
        "cf_tip": "Usa un Server personale con l'URL https://api.cloudflare.com/client/v4/accounts/<il tuo account ID>/ai/v1 e un token Workers AI.",
        "col_card": "💳 Carta?",
        "card_no": "No",
        "card_yes": "Sì",
        "card_dep": "Sì (carta / piccolo deposito)",
        "card_note": "Carta? = se bisogna registrare una carta per usare i modelli gratuiti.",
        "to_lim": "modelli che finiscono in <code>-Free</code> (es. Llama 3.3 70B Instruct Turbo Free): gratis, 6 richieste/min",
        "to_tip": "Già nell'elenco delle IA dell'app (Together AI); i -Free sono verdi. Imposta Richieste/min a 5.",
        "loc_h": "Modelli locali: quale per il tuo PC",
        "loc_intro": "L'app non include nessun modello locale: scaricane uno con 🤗 o <code>ollama pull &lt;nome&gt;</code>. Anche il gioco ha bisogno di memoria video (VRAM), lasciagli spazio. Regola pratica: VRAM libera ≥ dimensione del download + circa 1 GB. Un modello che non ci sta viene diviso tra GPU e CPU e diventa molto più lento. RAM: almeno la dimensione del download + 4 GB liberi. L'app tiene caricato un solo modello.",
        "col_model": "Modello",
        "col_size": "Download",
        "col_needs": "Scheda video (VRAM) / RAM",
        "col_result": "Risultato con questa app",
        "need_g2": "4 GB o più · o solo CPU con 8 GB di RAM",
        "res_g2": "✅ Testato, consigliato. Il migliore dei piccoli in russo e altre lingue. Scheda da 8 GB con il gioco aperto: 0,6 s per messaggio (solo CPU: 2,8 s).",
        "need_q15": "2 GB o più · o solo CPU",
        "res_q15": "⚠️ Testato: veloce (~1,3 s), ma con più righe le confonde e inventa testo; debole in russo.",
        "need_q3": "4 GB o più",
        "res_q3": "❌ Testato: più lento (~3,8 s) e mette parole cinesi nella traduzione.",
        "need_6": "6 GB o più",
        "need_8": "8 GB o più (con il gioco: 10–12 GB)",
        "need_12": "12 GB o più",
        "need_16": "16 GB o più",
        "res_next": "⏳ Non testato qui. Il passo successivo a gemma2:2b se hai VRAM in avanzo.",
        "res_g34": "✅ Provato: la migliore traduzione locale (capisce il gergo dei giochi). Scheda da 8 GB con il gioco aperto: 3,4 s per messaggio.",
        "res_l32": "✅ Provato: buono, un po' letterale. Scheda da 8 GB con il gioco aperto: 2,0 s per messaggio.",
        "res_g31": "❌ Provato: veloce (1,4 s) ma inventa testo e lascia parole in russo.",
        "res_untested": "⏳ Non testato qui. Traduzioni migliori, ma più lento; lascia abbastanza VRAM al gioco."
    }
}

# (nome, chave do limite, chave da nota, link da chave, chave do cartão)
FREE = [
    [
        "OpenRouter",
        "or_lim",
        "or_tip",
        "https://openrouter.ai/keys",
        "card_no"
    ],
    [
        "Mistral AI",
        "mi_lim",
        "mi_tip",
        "https://console.mistral.ai/api-keys/",
        "card_no"
    ],
    [
        "Google Gemini",
        "ge_lim",
        "ge_tip",
        "https://aistudio.google.com/app/apikey",
        "card_no"
    ],
    [
        "Groq",
        "gr_lim",
        "gr_tip",
        "https://console.groq.com/keys",
        "card_no"
    ],
    [
        "NVIDIA",
        "nv_lim",
        "nv_tip",
        "https://build.nvidia.com/settings/api-keys",
        "card_no"
    ],
    [
        "Cloudflare Workers AI",
        "cf_lim",
        "cf_tip",
        "https://dash.cloudflare.com/profile/api-tokens",
        "card_no"
    ],
    [
        "Together AI",
        "to_lim",
        "to_tip",
        "https://api.together.xyz/settings/api-keys",
        "card_dep"
    ],
    [
        "Cerebras",
        "ce_lim",
        "ce_tip",
        "https://cloud.cerebras.ai/",
        "card_yes"
    ]
]

PAID = [
    [
        "DeepSeek",
        "https://platform.deepseek.com/api_keys"
    ],
    [
        "OpenAI",
        "https://platform.openai.com/api-keys"
    ],
    [
        "Anthropic",
        "https://console.anthropic.com/settings/keys"
    ],
    [
        "xAI",
        "https://console.x.ai/"
    ],
    [
        "Qwen",
        "https://modelstudio.console.alibabacloud.com/"
    ],
    [
        "Fireworks",
        "https://fireworks.ai/account/api-keys"
    ],
    [
        "Perplexity",
        "https://www.perplexity.ai/settings/api"
    ],
    [
        "Ollama Cloud",
        "https://ollama.com/settings/keys"
    ]
]

# Modelos locais (Ollama): (modelo, download, chave da VRAM/RAM,
# chave do resultado). ✅/⚠️/❌ = testados com a app; ⏳ = não.
LOCAL = [
    [
        "gemma2:2b",
        "1.6 GB",
        "need_g2",
        "res_g2"
    ],
    [
        "qwen2.5:1.5b",
        "1.0 GB",
        "need_q15",
        "res_q15"
    ],
    [
        "qwen2.5:3b",
        "1.9 GB",
        "need_q3",
        "res_q3"
    ],
    [
        "gemma3:4b",
        "3.3 GB",
        "need_6",
        "res_g34"
    ],
    [
        "llama3.2:3b",
        "2.0 GB",
        "need_q3",
        "res_l32"
    ],
    [
        "gemma3:1b",
        "0.8 GB",
        "need_q15",
        "res_g31"
    ],
    [
        "qwen2.5:7b · llama3.1:8b",
        "4.7–4.9 GB",
        "need_8",
        "res_untested"
    ],
    [
        "gemma2:9b",
        "5.4 GB",
        "need_12",
        "res_untested"
    ],
    [
        "gemma3:12b · qwen2.5:14b",
        "8.1–9.0 GB",
        "need_16",
        "res_untested"
    ]
]


def ai_clouds_html(lang):
    t = TXT.get(lang) or TXT["en"]
    rows = "".join(
        f"<tr><td><b>{name}</b></td><td>{t[lim]}</td><td>{t[card]}</td>"
        f"<td>{t[tip]}</td><td><a href='{url}'>{t['get']}</a></td></tr>"
        for name, lim, tip, url, card in FREE)
    paid_links = " · ".join(f"<a href='{u}'>{n}</a>" for n, u in PAID)
    local = "".join(
        f"<tr><td><b>{name}</b></td><td>{size}</td><td>{t[need]}</td>"
        f"<td>{t[res]}</td></tr>" for name, size, need, res in LOCAL)
    tips = "".join(f"<li>{x}</li>" for x in t["tips"])
    srcs = "".join(f"<li>{n}: <a href='{u}'>{u}</a></li>"
                   for n, u in SOURCES)
    return f"""
<h2>{t['title']}</h2>
<p>{t['intro']}</p>
<h3>🆓 {t['free_h']}</h3>
<p><i>{t['card_note']}</i></p>
<table border="1" cellspacing="0" cellpadding="5" width="100%">
<tr><th>{t['col_ai']}</th><th>{t['col_free']}</th><th>{t['col_card']}</th>
<th>{t['col_tip']}</th><th>{t['col_key']}</th></tr>
{rows}
</table>
<h3>💳 {t['paid_h']}</h3>
<p>{t['paid_txt']}<br>{paid_links}</p>
<h3>🖥 {t['local_h']}</h3>
<p>{t['local_txt']}</p>
<h4>{t['loc_h']}</h4>
<p>{t['loc_intro']}</p>
<table border="1" cellspacing="0" cellpadding="5" width="100%">
<tr><th>{t['col_model']}</th><th>{t['col_size']}</th><th>{t['col_needs']}</th>
<th>{t['col_result']}</th></tr>
{local}
</table>
<h3>💡 {t['tips_h']}</h3>
<ul>{tips}</ul>
<h3>📚 {t['src_h'].format(d=CHECKED)}</h3>
<p><i>{t['src_note']}</i></p>
<ul>{srcs}</ul>
"""
