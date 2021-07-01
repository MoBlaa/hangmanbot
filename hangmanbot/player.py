"""Data classes for players."""
from __future__ import annotations
import json
from typing import Any

import discord


class Player:
    """Player instance."""
    id: int
    name: str
    mention: str

    def __init__(self, id: int, name: str, mention: str):
        super(Player, self).__init__()
        self.id = id
        self.name = name
        self.mention = mention

    @classmethod
    def from_user(cls, user: discord.User) -> Player:
        return cls(user.id, user.display_name, user.mention)

    @classmethod
    def from_json(cls, data: dict):
        return cls(id=data['id'], name=data['name'], mention=data['mention'])

    def __str__(self):
        return f"{self.name} [{self.id}]"


class PlayerEncoder(json.JSONEncoder):
    """Implements json encoding for Player instances."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Player):
            return {
                'id': o.id,
                'name': o.name,
                'mention': o.mention,
            }
        return super().default(o)
