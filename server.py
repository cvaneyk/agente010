import pipecat.transports as t
import pkgutil

print("=== MÓDULOS EN transports ===")
for x in pkgutil.iter_modules(t.__path__):
    print(x.name)

import pipecat.serializers as s
print("\n=== MÓDULOS EN serializers ===")
for x in pkgutil.iter_modules(s.__path__):
    print(x.name)
