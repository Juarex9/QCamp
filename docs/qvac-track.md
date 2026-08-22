> Brief **oficial** del sponsor (texto del track). Cómo lo cubre Qcamp:
> [cobertura.md](cobertura.md). Cómo se envía: [submit.md](submit.md).

🔷 QVAC Track
Tether · you can enter 1 track from this sponsor

🎯 Overview
QVAC by Tether is a local AI SDK. It runs models entirely on the user's device (no cloud, no API keys, no data leaving the machine) through a single unified interface in JavaScript/TypeScript (@qvac/sdk) or Python (tetherto-qvac-sdk). The same code runs on Linux, macOS, Windows, Android and iOS.

One SDK covers text generation, embeddings, RAG, fine-tuning, multimodal, OCR, transcription, text-to-speech, translation and more. It's open source (Apache 2.0), and if you'd rather not learn a new API at all, QVAC ships an HTTP server with an OpenAI-compatible endpoint; point any existing AI tool at localhost and it works out of the box.

Why this matters for what you build: local means private (financial documents, health data, and personal records never leave the device), cheap (no inference bill), and offline-capable. The interesting constraint is that you're working with small models; the craft is getting a 1–4B model to do real work reliably.

🏆 Prize breakdown
Total Prize Pool: Up to $2,000 USDt in prizes, $1,500 across the two project prizes, plus a $500 Vault Guardian pool. Distributed at the judges' discretion based on the merit, quality, originality, and impact of the submitted projects.

🥇 1st place — $1,000 USDt — Local agents that replace operations work: The most interesting thing happening with local AI right now is back-office automation: work that today needs a team of people reading documents and making judgment calls. Build an agent that does that work on-device.
🥈 2nd place — $500 USDt — Small models, hard tasks: tool use & reliability: Getting a small local model to chain tools correctly (without forgetting a step, ignoring a result, or inventing an answer) is genuinely difficult. This prize goes to the project that pulls it off most convincingly.
Additional perks: 🛡️ The Vault Guardian — $500 USDt, split between everyone who beats it. Not a judged prize and not tied to your project: an open challenge running alongside the hackathon. The Guardian is a local AI holding a WDK wallet with real funds; talk it into releasing them. Anyone who gets through the dungeon shares the $500 pool, so the earlier and the more of you who crack it, the smaller each slice. Full details below.

🧑‍💻 Track focus
🥇 Track 1 — Local agents for operations work
The pitch: an entire category of back-office work is people reading documents, spotting discrepancies, and escalating what matters. It's high-volume, judgment-heavy, and touches data companies genuinely cannot send to a third-party API. That makes it the natural home for local AI.

Invoice reconciliation. Ingest invoices (PDFs, photos, scans) with OCR, extract line items, match them against purchase orders or bank statements, and flag mismatches with an explanation a human can check in five seconds. This is the flagship use case; nail it, and you're competitive.
Post-trigger credit risk workflow. Not scoring credit risk itself, the operations around it. A threshold trips: now pull the relevant documents, summarise the exposure, draft the internal note, propose next actions, route it to the right person.
Payment and transaction analysis. Anomaly triage over transaction logs, merchant categorization, duplicate-charge detection, plain-English summaries of "what changed this month and why."
NLP-to-finance, generally. Anything that turns unstructured text or documents into structured financial output: contract terms into a payment schedule, expense receipts into a ledger, an email thread into a reconciliation task.
Multimodal document understanding. Photograph of a receipt in bad lighting → structured data. Handwritten delivery note → line items. Combine OCR with a multimodal model in one pipeline.
What makes a submission strong here: it works on messy real inputs, not one hand-picked clean PDF. It shows its reasoning so a human can audit it. And it's honest about what it can't do, an agent that flags uncertainty beats one that confidently hallucinates a number.

🥈 Track 2 — Tool use and small-model reliability
Small models are bad at tools in specific, recognizable ways: they forget a step midway through a chain, ignore what a tool actually returned and answer from memory instead, or invent a result when the call fails. Making a 1–4B model chain tools cleanly is a real engineering problem, and that's the whole of this track.

Multi-step tool chaining. An agent that calls third-party search, a calculator, a local database, and a file reader in sequence, and genuinely uses what comes back, without dropping context halfway through.
Grounded answers from live sources. Wire a local model to external search or an API so its output is anchored in what it retrieved, and show it refusing to answer rather than confabulating when the tool returns nothing useful.
Reliability engineering. Validation layers, retries, structured-output enforcement, self-checking passes. Show us the failure modes you hit and how you designed around them.
What makes a submission strong here: evidence, not vibes. Run the same task N times and show the success rate. Show us the failures you couldn't fix as well as the ones you could, a project that honestly maps where a small model breaks is worth more than one that demos a single clean run.

🛡️ Extra challenge — The Vault Guardian
Open to everyone, independent of your project. $500 USDt split between everyone who beats it.

The Vault Guardian is a local-first prompt-injection game: a defender AI holds a secret, you chat with it and try to get it to leak. All inference runs locally through @qvac/sdk on the Bare runtime (no cloud, no API calls). For the hackathon, the Guardian holds a WDK wallet with real funds. Convince it to release them.

Reference implementation will be shared at the hackathon.

🛠️ Tech requirements
Must use
QVAC as the inference layer: @qvac/sdk (JS/TS) or tetherto-qvac-sdk (Python). All model inference must run locally.
Using QVAC's OpenAI-compatible HTTP server as your local model provider counts. Calling a cloud model API does not.
The Vault Guardian challenge is separate from your project submission; you can enter it whether or not you're competing for a prize.
Hardware and models
Check the system requirements first:https://docs.qvac.tether.io/system-requirements/, supported platforms, runtimes, and the compatibility matrix.
Budget your RAM. A 4B model at Q4 needs roughly 4 GB and is the practical ceiling on a normal laptop; 8B wants ~8 GB. Models download once on first run (~2.5 GB for a 4B).
Models are on Hugging Face:https://huggingface.co/qvac,but you can use any open-spurce model of your preference.
Two things to know before you plan your build:
VisionPsy is not supported by the SDK yet. Vision in QVAC is good, but not via VisionPsy for now. Use the SDK's multimodal and OCR capabilities instead.
Skip image and video generation. They exist in the SDK and they're fun, but output quality isn't where we'd want it for a judged submission. Projects leaning on them won't score well.
Reusing code
You may reuse existing code. We will only judge what you built during the hackathon.
The QVAC integration itself must be new, written this weekend.
Don't bolt QVAC on in parallel. A project that already has its own cloud AI layer and simply adds QVAC alongside it for the prize will be discarded. Local inference has to be doing real work in your product.
AI-assisted coding
Allowed and encouraged, QVAC ships an OpenAI-compatible server precisely so you can plug it into your existing tooling.

But review what your model writes. Small-model orchestration is easy to fake and hard to do well. Hallucinated SDK methods, dead code paths, a README describing capabilities that don't exist, or a demo that only works on one cherry-picked input, all of that gets discarded without further review. Run the thing on inputs you didn't choose in advance before you submit it.

Submission must include
Public repo with a README explaining what you built and which QVAC capabilities and models you used.
Permalinks to the QVAC integration, direct GitHub links to the files/lines where inference happens. This is what we look at first, so make it easy.
Recorded demo video (async — see Judges section) showing it running locally, end to end.
Model and hardware details: which model, which quantization, what machine you ran it on, rough latency.
Setup instructions that work from a clean clone.
📚 Developer resources
Start here

Documentation home:https://docs.qvac.tether.io/
Introduction & core concepts:https://docs.qvac.tether.io/introduction/
System requirements & compatibility matrix:https://docs.qvac.tether.io/system-requirements/
JS/TS SDK quickstart:https://docs.qvac.tether.io/js-ts-sdk/
Python SDK quickstart:https://docs.qvac.tether.io/python-sdk/
API reference:https://docs.qvac.tether.io/reference/api/
Troubleshooting:https://docs.qvac.tether.io/troubleshooting/
Capabilities most relevant to these tracks

Text generation:https://docs.qvac.tether.io/ai-capabilities/text-generation/
OCR:https://docs.qvac.tether.io/ai-capabilities/ocr/
Multimodal:https://docs.qvac.tether.io/ai-capabilities/multimodal/
RAG:https://docs.qvac.tether.io/ai-capabilities/rag/
Text embeddings:https://docs.qvac.tether.io/ai-capabilities/text-embeddings/
Fine-tuning (LoRA):https://docs.qvac.tether.io/ai-capabilities/fine-tuning/
Batch processing:https://docs.qvac.tether.io/ai-capabilities/batch-processing/
Transcription:https://docs.qvac.tether.io/ai-capabilities/transcription/
Voice assistant:https://docs.qvac.tether.io/ai-capabilities/voice-assistant/
Delegated inference (P2P):https://docs.qvac.tether.io/p2p-capabilities/delegated-inference/
Tooling

CLI:https://docs.qvac.tether.io/cli/
OpenAI-compatible HTTP server:https://docs.qvac.tether.io/cli/http-server/
Configuration & plugins:https://docs.qvac.tether.io/configuration/
Model download lifecycle:https://docs.qvac.tether.io/models/download-lifecycle/
Electron tutorial:https://docs.qvac.tether.io/tutorials/electron/
Expo tutorial:https://docs.qvac.tether.io/tutorials/expo/
Models & research

Models overview:https://qvac.tether.io/models/
Hugging Face:https://huggingface.co/qvac
Fabric LLM (fine-tuning engine):https://qvac.tether.io/dev/fabric
Genesis (synthetic pre-training dataset):https://qvac.tether.io/dev/genesis
Vault Guardian challenge

Vault Guardian reference implementation
Bare runtime:https://bare.pears.com
Community & support

GitHub:https://github.com/tetherto/qvac
Discord:https://discord.com/invite/tetherdev
Blog:https://qvac.tether.io/blog
X / Twitter: https://x.com/QVAC
QV.AC (see QVAC in action):https://qv.ac
💬 Mentors
Raquel, DevRel | Telegram: @rraigal | Twitter: @rraigal_
Mentorship is IRL & online: you will have your dedicated topic on the hackathon Telegram group chat and hackers will ping the mentors whenever they need them.
For deeper technical questions, mentors will point you to the channels where the QVAC team lives:
Discord: https://discord.com/invite/tetherdev
Keet: keet://chat/gfo61f4e6zc5t1ifncyh9yp7s5eynbruz5bs95oc5ufn3e79entmhicijfysdat4uqz3s71sdqenc5iaufamq96afr1u8k15jntooq3wae8zzfqxeqapfspke3u5uthzquc7kwmyyzz9xcx61jjojxwpage3nyedtmrawhnjaktxzenpnhd4f67yjsa5aya
The hackathon kicks off on Saturday at 12PM (ARG time) and wraps up on Sunday at 12PM (ARG time). Mentors will be especially available on Saturday (the peak day for support and guidance).
🎓 Judges
Raquel, DevRel | Telegram: @rraigal | Twitter: @rraigal_
Judging will start at 1PM (Arg time) on Sunday 23rd, for about 4hs.
Everything happens online.
Demo is async: hackers will record a demo they will attach to their project submission.
💻 Workshop
Local AI That Actually Ships — QVAC Essentials and AI Coding Good Practices

Saturday 9.30 AM (ARG time) Live at the hackathon venue and streamed online.
Everything you need to build on QVAC this weekend, plus the working habits that separate a winning submission from a discarded one. We'll cover the QVAC essentials — installing the SDK, loading and running a model locally, picking the right model for the RAM you actually have, and wiring up the capabilities these tracks reward most: OCR, multimodal document understanding, RAG and tool calling. We'll also look at where small models break, and the validation and structured-output patterns that keep them honest. The second half is about coding with AI assistants without shipping slop: how to ground your assistant in the real SDK, why hallucinated methods are the most common failure we see in hackathon submissions, and how to test on inputs you didn't cherry-pick. Bring a laptop — you'll leave with a model running locally and a project skeleton to build on.