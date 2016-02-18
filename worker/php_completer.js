/**
 * helper module for codeintel worker
 *
 * @copyright 2016, Ajax.org B.V.
 * @author Lennart Kats <lennart add c9.io>
 */
define(function(require, exports, module) {

var baseHandler = require("plugins/c9.ide.language/base_handler");

var handler = module.exports = Object.create(baseHandler);

handler.handlesLanguage = function(language) {
    return language === "php";
};

// Already defined in c9.ide.language.generic:
//
// handler.getIdentifierRegex
// handler.getCompletionRegex

handler.getCacheCompletionRegex = function() {
     // Match strings that can be an expression or its prefix, i.e.
     // keywords/identifiers followed by whitespace and/or operators
    return new RegExp(
        // 'if/while/for ('
        "(\\b(if|while|for|switch)\\s*\\("
        // other identifiers and keywords without (
        + "|\\b\\w+\\s+"
        // equality operators, operators such as + and -,
        // and opening brackets { and [
        + "|(===?|!==?|[-+]=|[-+*%>?!|&{[])"
        // spaces
        + "|\\s)+"
    );
};

handler.predictNextCompletion = function(doc, fullAst, pos, options, callback) {
    /*
    if (!options.matches.length) {
        // Normally we wouldn't complete here, maybe we can complete for the next char?
        // Let's do so unless it looks like the next char may be a newline or equals sign
        if (options.line[pos.column - 1] && /(?![{;})\]\s"'\+\-\*])./.test(options.line[pos.column - 1]))
            return callback(null, { predicted: "" });
    }
    */
    var predicted = options.matches.filter(function(m) {
        return m.isContextual;
    });
    if (predicted.length !== 1 || predicted[0].icon === "method")
        return callback();
    console.log("[php_completer] Predicted our next completion will be for " + predicted[0].replaceText + ".");
    callback(null, {
        predicted: predicted[0].replaceText + ".",
        showEarly: predicted[0].class === "package"
    });
};

});