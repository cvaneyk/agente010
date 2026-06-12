import pipecat.processors.aggregators as m
import pkgutil

print("=== MÓDULOS DISPONIBLES ===")
for x in pkgutil.iter_modules(m.__path__):
    print(x.name)

import pipecat.processors.aggregators.llm_response as lr
print("\n=== CLASES EN llm_response ===")
print([x for x in dir(lr) if not x.startswith('_')])
