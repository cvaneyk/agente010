import pipecat.transports.websocket as ws
import pkgutil

print("=== MÓDULOS EN transports.websocket ===")
for x in pkgutil.iter_modules(ws.__path__):
    print(x.name)

import pipecat.serializers.twilio as tw
print("\n=== CLASES EN serializers.twilio ===")
print([x for x in dir(tw) if not x.startswith('_')])
