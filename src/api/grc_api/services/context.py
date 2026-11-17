"""Organisation data loaded once per request: names, holders and owners are derived from it."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from grc_api.domain.org import PersonRef, position_owners, role_holders
from grc_api.models import Control, Kpi, Mandate, Opportunity, Position, Process, Risk, Role, User
from grc_api.repositories import elements, org


@dataclass
class OrgData:
    users: dict[str, User]
    roles: dict[str, Role]
    positions: dict[str, Position]
    position_roles: dict[str, list[tuple[str, str]]]  # position id → [(role id, comment)]

    @property
    def refs(self) -> list[PersonRef]:
        return [PersonRef(u.id, u.position_id) for u in self.users.values() if u.status == "active"]

    def name(self, user_id: str | None) -> str:
        u = self.users.get(user_id or "")
        return u.display_name if u else (user_id or "")

    def role_holders(self, role_id: str) -> list[str]:
        roles_by_pos = {p: [r for r, _ in rs] for p, rs in self.position_roles.items()}
        return role_holders(role_id, roles_by_pos, self.refs)

    def owners(self, kind: str, obj: object) -> list[str]:
        if isinstance(obj, Role):
            return [obj.role_owner_user_id] if obj.role_owner_user_id else []
        if isinstance(obj, Position):
            return position_owners(obj.reports_to_disciplinary_id, self.refs)
        if isinstance(obj, Process | Opportunity | Control | Kpi):
            return self.role_holders(obj.owner_role_id) if obj.owner_role_id else []
        if isinstance(obj, Mandate):
            return [obj.granted_by_user_id] if obj.granted_by_user_id else []
        if isinstance(obj, Risk):
            return [obj.owner_user_id] if obj.owner_user_id else []
        return []

    def label(self, id_: str | None) -> str:
        if not id_:
            return ""
        for coll in (self.roles, self.positions):
            if id_ in coll:
                e = coll[id_]
                return f"{e.code} {e.title}"
        return self.name(id_)


async def load_org(db: AsyncSession) -> OrgData:
    users = {u.id: u for u in await elements.list_all(db, User)}
    roles = {r.id: r for r in await elements.list_all(db, Role)}
    positions = {p.id: p for p in await elements.list_all(db, Position)}
    pr: dict[str, list[tuple[str, str]]] = {}
    for x in await org.all_position_roles(db):
        pr.setdefault(x.position_id, []).append((x.role_id, x.comment))
    return OrgData(users, roles, positions, pr)
