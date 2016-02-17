import argparse
import json
import sys
import os
import logging
from os import path
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# Hackfix codeintel import path
sys.path.extend([p + "/codeintel" for p in sys.path])

from codeintel2.common import EvalController
from codeintel2.manager import Manager
from codeintel2.environment import DefaultEnvironment

def main(args):
    if args.mode != "daemon":
        print(process(sys.stdin.read(), args.__dict__))
        manager.finalize()
        return
    try:
        server = HTTPServer(("localhost", int(args.port)), Daemon)
    except:
        sys.stderr.write("Daemon unable to listen at :%s\n" % args.port)
        sys.exit(98)
    sys.stderr.write("Daemon listening at :%s\n" % args.port)
    server.serve_forever()

def process(source, args):
    mode = args.get("mode")
    buffer, offset = get_buffer_and_offset(source, args)
    if mode == "completions":
        return json.dumps(get_completions(buffer, offset))
    
    if mode == "goto_definitions":
        raise "Not implemented"

def get_completions(buffer, offset):
    trigger = buffer.preceding_trg_from_pos(offset, offset)
    if trigger is None:
        return []
    results = buffer.cplns_from_trg(trigger, ctlr = LoggingEvalController(), timeout = 5)
    return [{
        "name": result[1],
        "icon": {
                "function": "method",
                "module": "package",
            }.get(result[0], "property")
    } for result in results]

def get_buffer_and_offset(source, args):
    row = int(args.get("row"))
    column = int(args.get("column"))
    path = args.get("path")
    basedir = args.get("basedir")
    language = args.get("language")
    
    env = manager.env = DefaultEnvironment()
    env.get_proj_base_dir = lambda: basedir
    buffer = manager.buf_from_content(source, language, path = path, env = env)
    lines = source.split('\n')
    offset = sum([len(l) + 1 for l in lines[:row - 1]]) + column - 1
    return buffer, offset

class LoggingEvalController(EvalController):
    def debug(self, msg, *args): logger.debug(msg, *args)
    def info(self, msg, *args): logger.info(msg, *args)
    def warn(self, msg, *args): logger.warn(msg, *args)
    def error(self, msg, *args): logger.error(msg, *args)

class Daemon(BaseHTTPRequestHandler):
    def do_POST(self):
        query = urlparse.urlparse(self.path).query
        args = urlparse.parse_qsl(query)

        length = int(self.headers.getheader("content-length", 0))
        source = self.rfile.read(length)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(process(source, dict(args)))
    def log_message(self, format, *args):
        return # log silently

logStream = logging.StreamHandler(sys.stderr)
logStream.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
logging.getLogger("codeintel").addHandler(logStream)
logger = logging.getLogger("codeintel_server")
logger.addHandler(logStream)
logger.setLevel(logging.WARNING)

manager = Manager(
    # db_base_dir = path.join(CI_DIR, 'db'),
    # extra_module_dirs = [path.join(CI_DIR, 'codeintel2'),],
    # db_import_everything_langs = None,
    # db_catalog_dirs = []
)
manager.upgrade()
manager.initialize()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run jedi functions as a daemon or via stdin")
    parser.add_argument("mode", help="Mode of operation", choices=["daemon", "completions", "goto_definitions", "goto_assignments"])
    parser.add_argument("--row", type=int, help="The row to read from")
    parser.add_argument("--column", type=int, help="The column to read from")
    parser.add_argument("--path", help="The path of the file")
    parser.add_argument("--basedir", help="The basedir of the file")
    parser.add_argument("--language", help="The language of the file")
    parser.add_argument("--port", type=int, help="The port for the daemon to listen on")
    parser.add_argument("--nodoc", help="Don't include docstrings in output")
    args = parser.parse_args()
    main(args)