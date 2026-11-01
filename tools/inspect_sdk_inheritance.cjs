// Resolve named declaration inheritance without treating unresolved bases as absence.
const fs = require('fs'), path = require('path');
const ts = require(path.join(__dirname,'../data/runtime/typescript/lib/typescript.js'));

function inspect(request) {
  const declarations = new Map(), diagnostics = [];
  for (const file of request.files) {
    const sf = ts.createSourceFile(file.path,file.text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TS);
    diagnostics.push(...sf.parseDiagnostics.map(d=>({path:file.path,line:sf.getLineAndCharacterOfPosition(d.start||0).line+1,message:ts.flattenDiagnosticMessageText(d.messageText,' ')})));
    function visit(node,namespace) {
      if(ts.isModuleDeclaration(node)) {
        const name = node.name.getText(sf).replace(/^['"]|['"]$/g,'');
        ts.forEachChild(node,n=>visit(n,[...namespace,name]));return;
      }
      if(ts.isClassDeclaration(node)||ts.isInterfaceDeclaration(node)) {
        const name=node.name?.getText(sf), full=[...namespace,name].join('.');
        const bases=(node.heritageClauses||[]).filter(h=>h.token===ts.SyntaxKind.ExtendsKeyword).flatMap(h=>h.types.map(t=>t.expression.getText(sf)));
        const members=(node.members||[]).filter(m=>m.name).map(m=>({name:m.name.getText(sf).replace(/^['"]|['"]$/g,''),signature:m.getText(sf),line:sf.getLineAndCharacterOfPosition(m.getStart(sf)).line+1}));
        const declarationsForName=declarations.get(full)||[];
        declarationsForName.push({name:full,namespace,bases,members,path:file.path,
          line:sf.getLineAndCharacterOfPosition(node.getStart(sf)).line+1,end_line:sf.getLineAndCharacterOfPosition(node.end-1).line+1});
        declarations.set(full,declarationsForName);
      }
      ts.forEachChild(node,n=>visit(n,namespace));
    }
    visit(sf,[]);
  }
  const chain=[],missing=[],visiting=new Set(),finished=new Set();
  function walk(name) {
    if(visiting.has(name))throw new Error('Cyclic inheritance: '+name);
    if(finished.has(name))return;
    const matchesForName=declarations.get(name);
    if(!matchesForName){missing.push(name);return;}
    if(matchesForName.length!==1)throw new Error('Ambiguous selected base declaration: '+name);
    const decl=matchesForName[0];
    visiting.add(name);
    const matches=decl.members.filter(m=>m.name===request.member);
    chain.push({name:decl.name,path:decl.path,line:decl.line,end_line:decl.end_line,bases:decl.bases,
      declared_member_count:decl.members.length,target_members:matches});
    for(const base of decl.bases) {
      const local=[...decl.namespace,base].join('.');
      walk(declarations.has(local)?local:base);
    }
    visiting.delete(name);finished.add(name);
  }
  walk(request.root);
  const found=chain.flatMap(c=>c.target_members.map(m=>({owner:c.name,path:c.path,...m})));
  const relevantDiagnostics=diagnostics.filter(d=>chain.some(c=>c.path===d.path&&d.line<=c.end_line));
  return {typescript:ts.version,chain,unresolved_bases:missing,diagnostics,selected_chain_diagnostics:relevantDiagnostics,
    whole_file_syntax_verified:diagnostics.length===0,matches:found,
    status:relevantDiagnostics.length||missing.length?'incomplete_inheritance_evidence':found.length?'member_found':'member_absent_in_complete_selected_chain'};
}
if(require.main===module) {
  const request=JSON.parse(fs.readFileSync(0,'utf8'));
  process.stdout.write(JSON.stringify(inspect(request)));
}
module.exports={inspect};
