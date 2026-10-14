// Syntax inspection of a bounded set of declarations; this is not SDK compilation.
const fs = require('fs');
const path = require('path');
const ts = require(path.join(__dirname, '../data/runtime/typescript/lib/typescript.js'));

function inspect(text, filename) {
  const sf = ts.createSourceFile(filename, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const selected = new Map([
    ['ButtonAttribute', new Set(['fontSize', 'minFontScale'])],
    ['TextAttribute', new Set(['minFontScale'])],
    ['AudioStreamInfo', new Set(['channelLayout'])],
    ['AudioRendererInfo', new Set(['volumeMode'])]
  ]);
  const facts = [], owners = [];
  const docs = n => (n.jsDoc || []).map(d => d.getText(sf));
  function visit(node, chain, parentDocs) {
    const named = node.name && node.name.getText(sf).replace(/^['"]|['"]$/g, '');
    let next = chain, inheritedDocs = parentDocs;
    if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node) || ts.isModuleDeclaration(node) || ts.isEnumDeclaration(node)) {
      next = [...chain, named];
      inheritedDocs = [...parentDocs, ...docs(node)];
      if (selected.has(named) || named === 'AudioVolumeMode') {
        const start = node.getStart(sf);
        owners.push({name: named, chain: next, line: sf.getLineAndCharacterOfPosition(start).line + 1,
                     jsdoc: docs(node), heritage: (node.heritageClauses || []).map(h => h.getText(sf))});
      }
    }
    const owner = chain.at(-1);
    const member = selected.has(owner) && selected.get(owner).has(named)
      && (ts.isMethodDeclaration(node) || ts.isMethodSignature(node) || ts.isPropertySignature(node));
    const enumeration = ts.isEnumDeclaration(node) && named === 'AudioVolumeMode';
    if (member || enumeration) {
      const start = node.getStart(sf), end = node.end;
      facts.push({owner: enumeration ? 'audio' : owner, name: named, kind: enumeration ? 'enum' : node.parameters ? 'method' : 'property',
        line: sf.getLineAndCharacterOfPosition(start).line + 1,
        end_line: sf.getLineAndCharacterOfPosition(end - 1).line + 1,
        signature: enumeration ? null : text.slice(start, end),
        declared_type: node.type ? node.type.getText(sf) : null,
        optional: !!node.questionToken,
        parameters: (node.parameters || []).map(p => ({name: p.name.getText(sf), type: p.type ? p.type.getText(sf) : null, optional: !!p.questionToken})),
        jsdoc: docs(node), ancestor_jsdoc: parentDocs,
        raw_declaration: text.slice(start, end)});
    }
    ts.forEachChild(node, n => visit(n, next, inheritedDocs));
  }
  visit(sf, [], []);
  return {typescript: ts.version, diagnostics: sf.parseDiagnostics.map(d => ({start: d.start, message: ts.flattenDiagnosticMessageText(d.messageText, ' ')})), owners, facts};
}

if (require.main === module) {
  const request = JSON.parse(fs.readFileSync(0, 'utf8'));
  process.stdout.write(JSON.stringify(request.map(x => ({id: x.id, ...inspect(x.text, x.path)}))));
}
module.exports = {inspect};
