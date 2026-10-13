"""Local fork of Cognee's Hermes integration; inert registration only."""
from pathlib import Path
from .provider import RemoteMemoryProvider

def register(ctx):
    ctx.register_memory_provider(RemoteMemoryProvider())
    ctx.register_skill('setup',Path(__file__).parent/'skills/setup/SKILL.md',description='Use when installing or connecting Cognee Memory on a recipient Hermes profile.')
    ctx.register_skill('using',Path(__file__).parent/'skills/using/SKILL.md',description='Use when operating Cognee remote memory with selected Brain UUIDs.')
