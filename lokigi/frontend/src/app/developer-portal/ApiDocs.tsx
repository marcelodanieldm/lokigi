import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { prism } from "react-syntax-highlighter/dist/cjs/styles/prism";

const codePython = `import requests\\nresp = requests.get('https://api.lokigi.com/api/v1/audit', headers={'x-api-key': 'YOUR_KEY'})\\nprint(resp.json())`;
const codeJS = `fetch('https://api.lokigi.com/api/v1/audit', { headers: { 'x-api-key': 'YOUR_KEY' } })\\n  .then(r => r.json())\\n  .then(console.log);`;
const codePHP = `<?php\\n$resp = file_get_contents('https://api.lokigi.com/api/v1/audit', false, stream_context_create([\\n  'http' => [\\n    'header' => 'x-api-key: YOUR_KEY'\\n  ]\\n]));\\necho $resp;\\n?>`;

export default function ApiDocs() {
  return (
    <div id="api-docs">
      <h2 className="text-xl font-semibold mb-4">Documentación de la API</h2>
      <p className="mb-4 text-gray-600">Ejemplo de uso en Python, JavaScript y PHP:</p>
      <div className="space-y-4">
        <div>
          <div className="font-mono text-corporate-blue mb-1">Python</div>
          <SyntaxHighlighter language="python" style={prism} customStyle={{borderRadius:8, fontSize:14, background:'#f4f6fa', border:'1px solid #e5e7eb'}}>{codePython}</SyntaxHighlighter>
        </div>
        <div>
          <div className="font-mono text-corporate-blue mb-1">JavaScript</div>
          <SyntaxHighlighter language="javascript" style={prism} customStyle={{borderRadius:8, fontSize:14, background:'#f4f6fa', border:'1px solid #e5e7eb'}}>{codeJS}</SyntaxHighlighter>
        </div>
        <div>
          <div className="font-mono text-corporate-blue mb-1">PHP</div>
          <SyntaxHighlighter language="php" style={prism} customStyle={{borderRadius:8, fontSize:14, background:'#f4f6fa', border:'1px solid #e5e7eb'}}>{codePHP}</SyntaxHighlighter>
        </div>
      </div>
      <div className="mt-6 text-sm text-gray-500">Consulta la <a href="/api/openapi.json" className="underline text-corporate-blue">OpenAPI Spec</a> para más detalles.</div>
    </div>
  );
}
