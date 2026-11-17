"""The authenticated principal of a request."""

from dataclasses import dataclass, field

from grc_api.domain.permissions import permissions_of


@dataclass(frozen=True)
class Principal:
    user_id: str
    name: str
    system_roles: tuple[str, ...]
    csrf_token: str = ""
    permissions: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def of(
        cls, user_id: str, name: str, system_roles: list[str], csrf_token: str = ""
    ) -> "Principal":
        return cls(user_id, name, tuple(system_roles), csrf_token, permissions_of(system_roles))

    def can(self, permission: str) -> bool:
        return permission in self.permissions


SYSTEM = Principal.of("system", "System", ["admin", "ia"])
