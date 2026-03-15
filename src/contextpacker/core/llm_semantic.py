from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .config import Config
from ..io.file_read import read_text_safe

SECTION_SEP = "=" * 60
ENTRY_SEP = "-" * 40

CPP_LIKE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".ipp",
    ".inl",
    ".ixx",
    ".m",
    ".mm",
}

JUCE_METHOD_HINTS = (
    "prepareToPlay",
    "releaseResources",
    "processBlock",
    "isBusesLayoutSupported",
    "createEditor",
    "hasEditor",
    "getName",
    "acceptsMidi",
    "producesMidi",
    "isMidiEffect",
    "getTailLengthSeconds",
    "getNumPrograms",
    "getCurrentProgram",
    "setCurrentProgram",
    "getProgramName",
    "changeProgramName",
    "getStateInformation",
    "setStateInformation",
    "paint",
    "resized",
    "timerCallback",
    "buttonClicked",
    "sliderValueChanged",
    "comboBoxChanged",
)

CLASS_RE = re.compile(
    r"\b(class|struct)\s+([A-Za-z_]\w*)\s*(?::\s*([^{]+))?\s*\{",
    re.MULTILINE,
)

FUNC_RE = re.compile(
    r"""(?mx)
    ^
    \s*
    (?:
        template\s*<[^;{}]+>\s*
    )?
    (?:
        [A-Za-z_~][\w:\<\>\,\&\*\s]*?
    )
    \s+
    ([A-Za-z_~]\w*)
    \s*
    \(
        ([^;\)]*(?:\)[^;{()]*)?)
    \)
    \s*
    (?:
        const\b|
        noexcept\b|
        override\b|
        final\b|
        ->\s*[\w:\<\>\,\&\*\s]+
    )*
    \s*
    (?:
        \{
        |
        ;
    )
    """,
)

MEMBER_RE = re.compile(
    r"""(?mx)
    ^
    \s*
    (?:
        static\s+|
        constexpr\s+|
        inline\s+|
        mutable\s+|
        const\s+
    )*
    [A-Za-z_]\w*[\w:\<\>\,\&\*\s]*
    \s+
    ([A-Za-z_]\w*)
    \s*
    (?:
        =[^;]+
    )?
    ;
    $
    """
)

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+([<"][^>"]+[>"])', re.MULTILINE)
MACRO_RE = re.compile(
    r"^\s*#\s*(?:if|ifdef|ifndef|define|undef|elif|else|endif)\b.*$", re.MULTILINE
)
COMMENT_LINE_RE = re.compile(r"//.*?$", re.MULTILINE)
COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
CHAR_RE = re.compile(r"'(?:\\.|[^'\\])*'")

JUCE_SIGNAL_TOKENS = (
    "AudioProcessor",
    "AudioProcessorEditor",
    "AudioBuffer",
    "MidiBuffer",
    "AudioProcessorValueTreeState",
    "Component",
    "Slider",
    "Button",
    "Label",
    "ComboBox",
    "JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR",
    "JUCE_CALLTYPE",
    "BusesProperties",
    "ScopedNoDenormals",
)


@dataclass(frozen=True)
class SemanticFileSummary:
    rel_path: str
    includes: list[str]
    macros: list[str]
    classes: list[str]
    functions: list[str]
    members: list[str]
    juce_hints: list[str]
    symbols: list[str]


def _strip_comments_and_literals(text: str) -> str:
    text = COMMENT_BLOCK_RE.sub(" ", text)
    text = COMMENT_LINE_RE.sub(" ", text)
    text = STRING_RE.sub('""', text)
    text = CHAR_RE.sub("''", text)
    return text


def _compact_ws(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = []
    blank_run = 0
    for ln in lines:
        if ln.strip():
            cleaned.append(ln)
            blank_run = 0
        else:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()


def _unique_stable(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        s = item.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _extract_classes(text: str) -> list[str]:
    out: list[str] = []
    for kind, name, bases in CLASS_RE.findall(text):
        bases = " ".join(bases.split()) if bases else ""
        if bases:
            out.append(f"{kind} {name} : {bases}")
        else:
            out.append(f"{kind} {name}")
    return _unique_stable(out)


def _extract_functions(text: str) -> list[str]:
    out: list[str] = []
    for name, params in FUNC_RE.findall(text):
        params = " ".join(params.split())
        out.append(f"{name}({params})")
    return _unique_stable(out)


def _extract_members(text: str) -> list[str]:
    out = MEMBER_RE.findall(text)
    return _unique_stable(out)


def _extract_includes(raw_text: str) -> list[str]:
    return _unique_stable(INCLUDE_RE.findall(raw_text))


def _extract_macros(raw_text: str) -> list[str]:
    return _unique_stable([m.group(0).strip() for m in MACRO_RE.finditer(raw_text)])


def _extract_juce_hints(text: str) -> list[str]:
    hits = []
    for token in JUCE_METHOD_HINTS:
        if re.search(rf"\b{re.escape(token)}\b", text):
            hits.append(token)
    for token in JUCE_SIGNAL_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", text):
            hits.append(token)
    return _unique_stable(hits)


def _extract_symbols(
    classes: list[str], functions: list[str], members: list[str]
) -> list[str]:
    syms: list[str] = []
    syms.extend(classes)
    syms.extend(functions[:80])
    syms.extend(members[:80])
    return _unique_stable(syms)


def summarize_cpp_for_llm(rel_path: str, raw_text: str) -> SemanticFileSummary:
    stripped = _strip_comments_and_literals(raw_text)
    stripped = _compact_ws(stripped)

    includes = _extract_includes(raw_text)
    macros = _extract_macros(raw_text)
    classes = _extract_classes(stripped)
    functions = _extract_functions(stripped)
    members = _extract_members(stripped)
    juce_hints = _extract_juce_hints(stripped)
    symbols = _extract_symbols(classes, functions, members)

    return SemanticFileSummary(
        rel_path=rel_path,
        includes=includes[:80],
        macros=macros[:80],
        classes=classes[:80],
        functions=functions[:160],
        members=members[:120],
        juce_hints=juce_hints[:80],
        symbols=symbols[:200],
    )


def summarize_generic_text_for_llm(rel_path: str, raw_text: str) -> str:
    lines = raw_text.splitlines()
    trimmed: list[str] = []
    for ln in lines[:200]:
        s = ln.strip()
        if not s:
            continue
        trimmed.append(s)
    body = "\n".join(trimmed[:80])
    return f"FILE: {rel_path}\nMODE: generic_text\nCONTENT_HEAD:\n[\n{body}\n]\n"


def render_llm_transcript(project_name: str, files: list[Path], config: Config) -> str:
    header = (
        f"LLM PROJECT TRANSCRIPT: {project_name}\n"
        f"Generated by ContextPacker\n"
        f"Mode: lite semantic compressor tuned for C++ / JUCE\n"
        f"{SECTION_SEP}\n\n"
    )

    root = config.project_root
    entries: list[str] = []

    for p in files:
        rel = str(p.relative_to(root))
        raw = read_text_safe(p)

        if p.suffix.lower() in CPP_LIKE_SUFFIXES:
            summary = summarize_cpp_for_llm(rel, raw)
            entry = [
                f"FILE: {summary.rel_path}",
                "MODE: cpp_juce_semantic_lite",
            ]

            if summary.includes:
                entry.append("INCLUDES:")
                entry.extend(f"- {x}" for x in summary.includes)

            if summary.macros:
                entry.append("MACROS:")
                entry.extend(f"- {x}" for x in summary.macros)

            if summary.classes:
                entry.append("CLASSES:")
                entry.extend(f"- {x}" for x in summary.classes)

            if summary.juce_hints:
                entry.append("JUCE_HINTS:")
                entry.extend(f"- {x}" for x in summary.juce_hints)

            if summary.functions:
                entry.append("FUNCTIONS:")
                entry.extend(f"- {x}" for x in summary.functions)

            if summary.members:
                entry.append("MEMBERS:")
                entry.extend(f"- {x}" for x in summary.members)

            if summary.symbols:
                entry.append("SYMBOL_INDEX:")
                entry.extend(f"- {x}" for x in summary.symbols)

            entries.append("\n".join(entry) + f"\n{ENTRY_SEP}\n")
        else:
            entries.append(summarize_generic_text_for_llm(rel, raw) + f"{ENTRY_SEP}\n")

    return header + "".join(entries)

