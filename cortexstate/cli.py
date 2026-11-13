import argparse
import json
import os
from .memory import Memory, Scope


def main():
    parser = argparse.ArgumentParser(description="CortexState local memory and HTTP service")
    parser.add_argument("--db", default="cortexstate.db")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    for command in ("add", "search", "list", "context", "purge-expired"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--tenant", required=True)
        cmd.add_argument("--user", required=True)
        cmd.add_argument("--agent", default="default")
        cmd.add_argument("--session", default="persistent")
        if command in ("add", "search", "context"):
            cmd.add_argument("text")
    args = parser.parse_args()
    memory = Memory(args.db)
    if args.command == "serve":
        from .server import make_server
        credentials = json.loads(os.environ.get("CORTEXSTATE_KEYS", "{}"))
        with make_server(memory, credentials, args.host, args.port) as server:
            print(f"CortexState listening on {args.host}:{server.server_port}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        return
    scope = Scope(args.tenant, args.user, args.agent, args.session)
    operation = getattr(memory, args.command.replace("-", "_"))
    result = operation(args.text, scope=scope) if hasattr(args, "text") else operation(scope=scope)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
