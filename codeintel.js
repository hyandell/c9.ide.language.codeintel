/**
 * Cloud9 codeintel support
 *
 * @copyright 2015, Ajax.org B.V.
 */
define(function(require, exports, module) {
    main.consumes = [
        "Plugin", "language", "jsonalyzer", "settings",
        "preferences", "c9"
    ];
    main.provides = ["language.codeintel"];
    return main;

    function main(options, imports, register) {
        var Plugin = imports.Plugin;
        var language = imports.language;
        var c9 = imports.c9;
        var plugin = new Plugin("Ajax.org", main.consumes);
        var server = require("text!./server/codeintel_server.py")
            .replace(/ {4}/g, " ").replace(/'/g, "'\\''");
        var launchCommand = require("text!./server/launch_command.sh")
            .replace(/ {2,}/g, " ");
        
        plugin.on("load", function() {
            language.registerLanguageHandler("plugins/c9.ide.language.codeintel/worker/codeintel_completer", function(err, handler) {
                if (err) return console.error(err);
                setupHandler(handler);
            }, plugin);
        });
        
        plugin.on("unload", function() {
            
        });
            
        function setupHandler(handler) {
            handler.emit("setup", {
                server: server,
                launchCommand: launchCommand,
                hosted: !options.testing && c9.hosted
            });
        }
        
        /** @ignore */
        register(null, {
            "language.codeintel": plugin
        });
    }
});