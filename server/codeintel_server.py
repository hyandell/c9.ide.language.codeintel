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
        sys.stderr.write("!!Daemon unable to listen at :%s\n" % args.port)
        sys.exit(98)
    sys.stderr.write("!!Daemon " + "listening at :%s\n" % args.port)
    server.serve_forever()

def process(source, args):
    mode = args.get("mode")
    buffer, line, offset = process_input(source, args)
    scan_workspace(buffer)
    
    if mode == "completions":
        return json.dumps(get_completions(buffer, line, offset))
    
    if mode == "goto_definitions":
        raise "Not implemented"

def get_completions(buffer, line, offset):
    trigger = buffer.preceding_trg_from_pos(offset, offset)
    if trigger is None:
        return []
    results = buffer.cplns_from_trg(trigger, ctlr = LoggingEvalController(), timeout = 5)
    return [
        remove_nulls({
            "name": get_proposal_name(kind, name, buffer.lang, line),
            "replaceText": get_proposal_replace_text(kind, name, buffer.lang, line),
            "icon": {
                "function": "method",
                "module": "package",
                "class": "package",
            }.get(name, "property")
        }) for kind, name in results
    ]

def get_proposal_name(kind, name, lang, line):
    if lang == "PHP" and kind == "variable":
        return "$" + name
    if kind == "function" or kind == "method":
        return name + "()"
    return name

def get_proposal_replace_text(kind, name, lang, line):
    if lang == "PHP" and kind == "variable":
        return "$" + name
    if "import " in line:
        return name
    if kind == "function" or kind == "method":
        return name + "(^^)"

def remove_nulls(d):
    for key, value in d.items():
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            remove_nulls(value)
    return d

def process_input(source, args):
    row = int(args.get("row"))
    column = int(args.get("column"))
    path = args.get("path")
    basedir = args.get("basedir")
    language = args.get("language")
    
    env = manager.env = DefaultEnvironment()
    env.get_proj_base_dir = lambda: basedir
    buffer = manager.buf_from_content(source, language, path = path, env = env)
    lines = source.split('\n')
    line = lines[row]
    offset = sum([len(l) + 1 for l in lines[:row]]) + column
    return buffer, line, offset

def scan_workspace(buffer):
    if not manager.is_citadel_lang(buffer.lang):
        return
    if not buffer.lang in scanned_langs:
        sys.stderr.write("!!Updating " + buffer.lang + " indexes\n")
        scanned_langs.append(buffer.lang)
        buffer.scan()
        sys.stderr.write("!!Done updating indexes\n")
    else:
        buffer.scan()

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
scanned_langs = []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run codeintel commands as a daemon or via stdin")
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