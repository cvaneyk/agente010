import pipecat.processors.aggregators.llm_context as lc
print("\n=== CLASES EN llm_context ===")
print([x for x in dir(lc) if not x.startswith('_')])

import pipecat.processors.aggregators.llm_response_universal as lru
print("\n=== CLASES EN llm_response_universal ===")
print([x for x in dir(lru) if not x.startswith('_')])

# Ver qué servicios Anthropic hay disponibles
import pipecat.services.anthropic as ant
import pkgutil
print("\n=== MÓDULOS EN services.anthropic ===")
for x in pkgutil.iter_modules(ant.__path__):
    print(x.name)
