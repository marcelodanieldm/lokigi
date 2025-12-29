import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";

const codePython = `import requests
resp = requests.get('https://api.lokigi.com/api/v1/audit', headers={'x-api-key': 'YOUR_KEY'})
print(resp.json())`;
const codeJS = `fetch('https://api.lokigi.com/api/v1/audit', { headers: { 'x-api-key': 'YOUR_KEY' } })
  .then(r => r.json())
  .then(console.log);`;
const codePHP = `<?php
$resp = file_get_contents('https://api.lokigi.com/api/v1/audit', false, stream_context_create([
  'http' => [
    'header' => 'x-api-key: YOUR_KEY'
  ]
]));
echo $resp;
?>`;

export default function ApiDocs() {
  return (
    <div id="api-docs">
      <h2 className="text-xl font-semibold mb-4">Documentación de la API</h2>
      <p className="mb-4 text-gray-300">Ejemplo de uso en Python, JavaScript y PHP:</p>
      <div className="space-y-4">
        <div>
          <div className="font-mono text-green-400 mb-1">Python</div>
          <SyntaxHighlighter language="python" style={vscDarkPlus} customStyle={{borderRadius:8, fontSize:14}}>{codePython}</SyntaxHighlighter>
        </div>
        <div>
          <div className="font-mono text-green-400 mb-1">JavaScript</div>
          <SyntaxHighlighter language="javascript" style={vscDarkPlus} customStyle={{borderRadius:8, fontSize:14}}>{codeJS}</SyntaxHighlighter>
        </div>
        <div>
          <div className="font-mono text-green-400 mb-1">PHP</div>
          <SyntaxHighlighter language="php" style={vscDarkPlus} customStyle={{borderRadius:8, fontSize:14}}>{codePHP}</SyntaxHighlighter>
        </div>
      </div>
      <div className="mt-6 text-sm text-gray-400">Consulta la <a href="/api/openapi.json" className="underline text-green-400">OpenAPI Spec</a> para más detalles.</div>
    </div>
  );
}
