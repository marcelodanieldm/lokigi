import React from 'react';

interface TableProps {
  columns: string[];
  data: Record<string, any>[];
}

const Table: React.FC<TableProps> = ({ columns, data }) => {
  return (
    <table className="min-w-full bg-white border border-corporate-gray text-corporate-dark rounded shadow">
      <thead className="bg-corporate-gray text-corporate-dark">
        <tr>
          {columns.map((col) => (
            <th key={col} className="px-4 py-2 font-semibold border-b border-corporate-gray">{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i} className="hover:bg-gray-100">
            {columns.map((col) => (
              <td key={col} className="px-4 py-2 border-b border-corporate-gray">{row[col]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Table;