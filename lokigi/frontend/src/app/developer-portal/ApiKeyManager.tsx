import React, { useState } from "react";

const mockKeys = [
  { id: 1, key: "t2-123456", created: "2025-12-01", usage: 1234 },
  { id: 2, key: "t2-654321", created: "2025-12-15", usage: 42 },
];

export default function ApiKeyManager() {
  const [keys, setKeys] = useState(mockKeys);
  const [newKey, setNewKey] = useState<string | null>(null);

  const generateKey = () => {
    const key = `t2-${Math.floor(Math.random()*1000000)}`;
    setKeys([...keys, { id: Date.now(), key, created: new Date().toISOString().slice(0,10), usage: 0 }]);
    setNewKey(key);
  };
  const revokeKey = (id: number) => setKeys(keys.filter(k => k.id !== id));

  return (
    <div id="api-keys">
      <h2 className="text-xl font-semibold mb-4">API Key Management</h2>
      <button onClick={generateKey} className="btn mb-4">Generar nueva API Key</button>
      {newKey && <div className="mb-4 text-corporate-blue">Nueva llave: <span className="font-mono">{newKey}</span></div>}
      <table className="w-full text-sm mb-4">
        <thead>
          <tr className="text-corporate-blue">
            <th className="text-left">Key</th>
            <th>Creada</th>
            <th>Consumo</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {keys.map(k => (
            <tr key={k.id} className="border-b border-gray-200">
              <td className="font-mono text-xs">{k.key}</td>
              <td>{k.created}</td>
              <td>{k.usage}</td>
              <td><button onClick={() => revokeKey(k.id)} className="text-red-500 hover:underline">Revocar</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-xs text-gray-400">Próximamente: ver consumo en tiempo real y logs de uso.</div>
    </div>
  );
}
