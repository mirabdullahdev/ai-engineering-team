import re
import threading
import time
from typing import Any

from crewai.events import LLMStreamChunkEvent, crewai_event_bus

from app.runs import emit
from app.tools.web import display_name

SANDBOX_WRITE_TOOL = "write_sandbox_file"
WEB_WRITE_TOOL = "write_web_file"
DESIGN_FILE = "design.md"
DESIGN_AUTHOR_ROLE = "Engineering Lead"
EMIT_INTERVAL_SECONDS = 0.06

FIELD_START = re.compile(r'"(filename|path|content)"\s*:\s*"')
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", '"': '"', "\\": "\\", "/": "/"}


def read_json_string(raw: str, start: int) -> str:
    out: list[str] = []
    i = start
    while i < len(raw):
        char = raw[i]
        if char == '"':
            break
        if char != "\\":
            out.append(char)
            i += 1
            continue
        if i + 1 >= len(raw):
            break
        escape = raw[i + 1]
        if escape == "u":
            if i + 6 > len(raw):
                break
            out.append(chr(int(raw[i + 2 : i + 6], 16)))
            i += 6
        else:
            out.append(ESCAPES.get(escape, escape))
            i += 2
    text = "".join(out)
    return text.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def read_partial_fields(arguments: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in FIELD_START.finditer(arguments):
        key = match.group(1)
        if key not in fields:
            fields[key] = read_json_string(arguments, match.end())
    return fields


class FileStreamer:
    def __init__(self) -> None:
        self._sent: dict[tuple[str, str], int] = {}
        self._last_emit: dict[tuple[str, str], float] = {}
        self._design: dict[str, str] = {}
        self._lock = threading.Lock()

    def handle(self, event: LLMStreamChunkEvent) -> None:
        if event.tool_call is not None:
            self._handle_tool_call(event)
        elif (getattr(event, "agent_role", None) or "").strip() == DESIGN_AUTHOR_ROLE and event.chunk:
            self._handle_design_text(event)

    def _handle_tool_call(self, event: LLMStreamChunkEvent) -> None:
        call: dict[str, Any] = event.tool_call if isinstance(event.tool_call, dict) else event.tool_call.model_dump()
        function = call.get("function") or {}
        tool_name = function.get("name")
        if tool_name not in (SANDBOX_WRITE_TOOL, WEB_WRITE_TOOL):
            return
        fields = read_partial_fields(function.get("arguments") or "")
        content = fields.get("content")
        target = fields.get("filename") if tool_name == SANDBOX_WRITE_TOOL else fields.get("path")
        if content is None or not target:
            return
        name = target if tool_name == SANDBOX_WRITE_TOOL else display_name(target)
        if name is None:
            return
        self._send((event.response_id or "", str(call.get("index", 0))), name, content)

    def _handle_design_text(self, event: LLMStreamChunkEvent) -> None:
        key = event.response_id or ""
        with self._lock:
            text = self._design.get(key, "") + event.chunk
            self._design = {key: text}
        self._send((key, "design"), DESIGN_FILE, text)

    def _send(self, key: tuple[str, str], name: str, text: str) -> None:
        with self._lock:
            sent = self._sent.get(key, 0)
            now = time.monotonic()
            if len(text) <= sent or (sent and now - self._last_emit.get(key, 0.0) < EMIT_INTERVAL_SECONDS):
                return
            self._sent[key] = len(text)
            self._last_emit[key] = now
            emit("file_delta", name=name, delta=text[sent:], reset=sent == 0)


streamer = FileStreamer()


def install_streaming() -> None:
    @crewai_event_bus.on(LLMStreamChunkEvent)
    def forward_chunk(_source: object, event: LLMStreamChunkEvent) -> None:
        streamer.handle(event)
