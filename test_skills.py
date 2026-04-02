import sys
import os
sys.path.insert(0, os.path.abspath('novaic-gateway'))

from gateway.db.access import init_database, get_database
from gateway.db.repositories.skill import SkillRepository
from gateway.entity.store import get_entity_store
import gateway.entity.defs

db = init_database(":memory:")
store = get_entity_store()
# Register defs
for name in dir(gateway.entity.defs):
    obj = getattr(gateway.entity.defs, name)
    if hasattr(obj, "name") and hasattr(obj, "table"):
        store.register(obj)

store.ensure_all_schemas()

repo = SkillRepository(db)
try:
    print(repo.get_agent_skills("dummy_agent"))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
