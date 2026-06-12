import subprocess
result = subprocess.run(
    ["python", "-c", "import pipecat; import pkgutil; import pipecat.processors.aggregators as m; [print(x.name) for x in pkgutil.iter_modules(m.__path__)]"],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)
