"""AI rewrite feature: sends the transcript + user instructions to Claude,
with a system prompt that explicitly protects the speaker's tone/voice/
structure while applying the requested change.
"""
from __future__ import annotations

import anthropic

from . import config
from .exceptions import RewriteError
from .schemas import RewriteRequest

_SYSTEM_PROMPT = """\
You are an expert editor who rewrites video transcripts while faithfully \
preserving the original speaker's voice.

Before writing anything, analyze the source transcript's:
- Tone (casual vs. formal, earnest vs. sarcastic, energetic vs. laid-back)
- Voice (word choice, slang, catchphrases, characteristic transitions)
- Pacing and sentence structure (short punchy sentences vs. long winding \
ones, how ideas are sequenced)
- Humor, asides, and any phrases or verbal tics the speaker repeats

Then apply ONLY the change the user asks for. Unless the user explicitly \
asks you to change the tone, voice, pacing, or structure, you must preserve \
all of them exactly as they appear in the source - do not make a casual \
speaker sound formal, do not smooth out their quirks, do not homogenize \
their sentence rhythm into generic marketing copy.

Rules:
1. Never fabricate facts, claims, or details that aren't in the source or \
explicitly given in the user's instructions.
2. If asked to change the topic or product, keep the same narrative shape, \
tone, and speech patterns - swap out only the subject matter.
3. If asked to shorten or clean up filler words, cut ruthlessly but keep \
the speaker's characteristic phrasing in what remains.
4. If asked to adapt for a different platform (e.g. YouTube Shorts, TikTok \
caption, blog post), follow that platform's real conventions (pacing, \
length, hooks, formatting) while keeping the voice recognizably the same \
person.
5. Output ONLY the rewritten transcript/copy - no preamble, no meta \
commentary, no markdown headers unless the target format calls for them \
(e.g. a blog post may use headings).
"""

_PRESET_INSTRUCTIONS = {
    "clean_filler": (
        "Clean up filler words (um, uh, you know, like, so, right) and false "
        "starts. Preserve everything else - wording, tone, structure, and "
        "length - as closely as possible."
    ),
    "shorten": (
        "Significantly shorten this while keeping the speaker's voice, tone, "
        "and the most important points. Aim for roughly half the length "
        "unless the user's instructions say otherwise."
    ),
    "youtube_shorts": (
        "Adapt this into a script for a YouTube Shorts video (roughly 30-60 "
        "seconds spoken, ~75-150 words), with a strong hook in the first "
        "line, in the speaker's own voice."
    ),
    "tiktok_caption": (
        "Adapt this into a short, punchy TikTok caption/hook (a few "
        "sentences, casual, scroll-stopping) in the speaker's own voice."
    ),
    "blog_post": (
        "Adapt this into a well-structured blog post (headings, short "
        "paragraphs, natural transitions) while keeping the speaker's voice "
        "recognizable in the prose."
    ),
    "new_topic": (
        "Rewrite this to be about a different subject while keeping the "
        "exact same tone, voice, pacing, and structure."
    ),
    "custom": "",
}


def _build_user_prompt(req: RewriteRequest) -> str:
    parts = []
    preset_instruction = _PRESET_INSTRUCTIONS.get(req.preset, "")
    if preset_instruction:
        parts.append(preset_instruction)
    if req.target_topic:
        parts.append(f"New topic/product to rewrite about: {req.target_topic}")
    if req.instructions.strip():
        parts.append(f"Additional instructions: {req.instructions.strip()}")
    if not parts:
        parts.append(
            "Lightly clean up the transcript for readability while "
            "preserving the voice, tone, and structure exactly."
        )

    instructions_block = "\n".join(f"- {p}" for p in parts)

    return (
        f"Instructions:\n{instructions_block}\n\n"
        f"--- ORIGINAL TRANSCRIPT ---\n{req.transcript_text}\n--- END TRANSCRIPT ---\n\n"
        "Write the rewritten version now, following the rules in your "
        "system prompt."
    )


def rewrite_transcript(req: RewriteRequest) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise RewriteError(
            "Rewrite feature requires ANTHROPIC_API_KEY to be configured."
        )
    if not req.transcript_text.strip():
        raise RewriteError("Nothing to rewrite - transcript text is empty.")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = _build_user_prompt(req)

    try:
        response = client.messages.create(
            model=config.REWRITE_MODEL,
            max_tokens=8000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIStatusError as exc:
        raise RewriteError(f"Claude API error: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise RewriteError(f"Could not reach the Claude API: {exc}") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    rewritten = "\n".join(text_parts).strip()
    if not rewritten:
        raise RewriteError("Claude returned an empty response.")
    return rewritten
