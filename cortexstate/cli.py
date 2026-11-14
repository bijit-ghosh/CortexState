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
    demo = sub.add_parser('demo', help='Start a disposable dashboard with sample memories')
    demo.add_argument('--port', type=int, default=8787)
    for command in ("add", "search", "list", "context", "purge-expired"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--tenant", required=True)
        cmd.add_argument("--user", required=True)
        cmd.add_argument("--agent", default="default")
        cmd.add_argument("--session", default="persistent")
        if command in ("add", "search", "context"):
            cmd.add_argument("text")
    args = parser.parse_args()
    if args.command == 'demo':
        import secrets
        import tempfile
        from pathlib import Path
        from .server import make_server
        with tempfile.TemporaryDirectory() as directory:
            memory = Memory(Path(directory) / 'demo.db')
            scope = Scope('demo', 'alice')
            for fact in ('Alice prefers email for project updates', 'Run regression tests before merging changes',
                         'The support team uses UTC for incident timelines'):
                memory.add(fact, scope=scope, metadata={'source': 'synthetic-demo'})
            key = secrets.token_urlsafe(32)
            with make_server(memory, {key: 'demo'}, port=args.port) as server:
                print(f'Dashboard: http://127.0.0.1:{server.server_port}/dashboard\nDisposable service key: {key}\nUser: alice | Agent: default | Session: persistent\nCtrl+C stops the demo and removes its temporary database.', flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    pass
        return
    model = None
    embedding_model = os.environ.get('CORTEXSTATE_EMBEDDING_MODEL')
    generation_model = os.environ.get('CORTEXSTATE_GENERATION_MODEL')
    if embedding_model or generation_model:
        from .providers import OpenAIModels
        model = OpenAIModels(embedding_model=embedding_model, generation_model=generation_model)
    memory = Memory(args.db, embedder=model.embed if embedding_model else None,
                    embedding_id='openai/' + embedding_model if embedding_model else None)
    if args.command == "serve":
        from .server import make_server
        credentials = json.loads(os.environ.get("CORTEXSTATE_KEYS", "{}"))
        with make_server(memory, credentials, args.host, args.port, model=model) as server:
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
