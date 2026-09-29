import sys

if sys.platform == "win32":
    raise SystemExit("Run development on the Mac. The Windows PC only hosts Ollama.")

from .runner import main

raise SystemExit(main())
