# AI Engineering Team

Describe software in plain English and watch a crew of four AI engineers design it, build it, test it, and show it running, live.

A lead designs the system, a backend engineer writes the Python, a frontend engineer builds a Next.js interface, and a test engineer writes unit tests and fixes bugs until they pass. You watch every step: code streams in as it is written, a live preview of the app takes shape, and the finished project downloads as a zip.

Built with [CrewAI](https://crewai.com), FastAPI and Next.js. Bring your own OpenAI API key.

## The team

| Engineer | Role | Output |
|---|---|---|
| **Ada**, Engineering Lead | Turns the brief into a typed design with validation rules, edge cases and a test plan | `design.md` |
| **Linus**, Backend Engineer | Implements the design in Python (standard library only) and proves it runs | modules and `demo.py` |
| **Grace**, Frontend Engineer | Builds a polished Next.js interface on a starter template and checks it type-checks and renders | `src/**` of the Next.js app |
| **Margaret**, Test Engineer | Writes a `unittest` suite, fixes real defects, and reruns until everything passes | `test_*.py` and a summary |

The agents and their prompts live in YAML ([`agents.yaml`](backend/app/config/agents.yaml), [`tasks.yaml`](backend/app/config/tasks.yaml)), so changing how the team works is a prompt edit, not a code change.

## How it works

```
Brief ──► Ada ──► Linus ──► Grace ──► Margaret ──► verify ──► download
          design   Python   Next.js    tests        tests + web check,
                                                    bounded fix loops
```

```
Next.js UI ── POST /api/runs ──► FastAPI ── thread ──► CrewAI crew (sequential)
     ▲                              │                       │ sandbox + web tools,
     └──────── SSE /events ─────────┴─── run event log ◄────┘ streamed LLM chunks
```

- Every thought, tool call, file write, test run and streamed token becomes an event on an append-only log. The UI tails that log over Server-Sent Events.
- **Streaming:** the model's file writes are tool calls. The backend parses the partial JSON arguments as they stream in, so code appears character by character instead of all at once.
- **Live preview:** a real Next.js dev server runs on port 3100 and hot-reloads as Grace writes files. The UI embeds it in an iframe.
- **Self-checking:** Grace has a *Check Web App* tool that runs the TypeScript compiler and renders the page, so she sees her own errors. After the crew finishes, the backend runs the Python tests and the web check itself. Failures are sent back to the responsible engineer for up to two fix rounds.

## Prerequisites

- **Python 3.12 or newer** and [uv](https://docs.astral.sh/uv/)
- **Node.js 20 or newer**
- An **OpenAI API key** with a few dollars of credit

## Quick start

```bash
git clone https://github.com/mirabdullahdev/ai-engineering-team.git
cd ai-engineering-team
```

**1. Backend**

```bash
cd backend
cp .env.example .env
```

On Windows use `copy .env.example .env`. Open `backend/.env` and set your key:

```
OPENAI_API_KEY=sk-...
```

```bash
uv sync
uv run python -m uvicorn app.main:app --port 8000
```

**2. Frontend**, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

**3. Build something.** Open http://localhost:3000, describe the software you want, and press **Enter** (Shift+Enter adds a new line).

The first build installs the preview app's dependencies in `backend/web` automatically, which takes a minute. If that step fails, or you want to do it ahead of time, run `cd backend/web && npm install` once yourself.

### A good first prompt

```
A client invoicing app for a freelance design studio. Users create invoices with a client name, issue date, payment terms (Net 7, Net 14 or Net 30) and line items made of a description, a quantity and a unit price. The app calculates the subtotal, an optional percentage discount, tax at a configurable rate, and the total, rounded to the cent. The due date is the issue date plus the payment terms. An invoice moves from Draft to Sent to Paid, and shows as Overdue automatically when it is Sent and past its due date.

Rules: an invoice needs at least one line item before it can be sent. Quantities must be positive and prices cannot be negative. The discount must be between 0 and 100 percent. Paid invoices cannot be edited. Invoice numbers are sequential (INV-0001, INV-0002).

The interface should feel like a premium boutique studio tool: a dashboard showing outstanding, paid and overdue totals, an invoice list with status labels and filters, and an invoice editor with a live document-style preview that updates as you type. Seed three realistic sample invoices.
```

Smaller briefs, such as a habit tracker or a library lending system, build faster and cost less.

## Configuration

| What | Where |
|---|---|
| Models for each agent | `llm:` in [`backend/app/config/agents.yaml`](backend/app/config/agents.yaml) (default `openai/gpt-5.4-mini`) |
| Agent prompts and task instructions | [`agents.yaml`](backend/app/config/agents.yaml) and [`tasks.yaml`](backend/app/config/tasks.yaml) |
| Starter template for generated frontends | [`backend/template/src`](backend/template/src) |
| Ports | UI `3000`, API `8000`, generated-app preview `3100` |

**Cost:** with the default mini models, three-agent builds used roughly 125k to 240k tokens in testing, and the frontend engineer adds more. Check your usage on the OpenAI dashboard before long sessions.

## Project structure

```
backend/
  app/
    main.py        FastAPI routes, SSE stream, file and download endpoints
    pipeline.py    runs the crew, then verifies and repairs
    crew.py        wires YAML agents and tasks into a CrewAI crew
    streaming.py   turns LLM chunks into live file-write events
    runs.py        run registry and event log
    tools/
      sandbox.py   Python file tools and test runner for the engineers
      web.py       Next.js file tools, preview server and web checks
    config/        agents.yaml, tasks.yaml
  template/src/    pristine Next.js starter copied for every build
  web/             installed Next.js project that the preview runs
frontend/          the Next.js interface you interact with
```

## Safety and privacy

- Your API key lives only in `backend/.env`, which is git-ignored. The repository contains only `.env.example`.
- Generated Python runs on the standard-library-only base interpreter, in a flat directory, with every environment variable containing `KEY`, `TOKEN`, `SECRET` or `PASSWORD` removed.
- The frontend engineer can only write `.ts`, `.tsx` and `.css` files under `src/`, and can only import the packages the starter already has.
- The preview runs on its own origin (`localhost:3100`) inside an iframe.

This is **not** a hardened sandbox. Generated code is untrusted code, so read it before you run it anywhere else.

## Troubleshooting

- **`uvicorn` is blocked on Windows:** run it as `uv run python -m uvicorn app.main:app --port 8000`, as shown above.
- **"Port 3100 is already in use":** a previous preview server is still running. Stop whatever holds that port and start the build again.
- **"`node` was not found":** install Node.js 20 or newer. The live preview needs it.
- **The UI says the backend is not reachable:** start the backend first, on port 8000.
- **A build fails halfway:** the error is shown in the UI. Check your API key and OpenAI credit first.

## Limitations

- Tested with OpenAI models only.
- One build at a time.
- The generated Next.js app is front-end only. It re-implements the business rules in TypeScript and keeps its state in memory. It is not connected to the generated Python backend.
- The generated Python backend uses only the standard library.

## License

MIT, see [LICENSE](LICENSE).
