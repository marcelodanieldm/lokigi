```tsx
import React from 'react';

interface CTAButtonProps {
  label: string;
  onClick: () => void;
}

const CTAButton: React.FC<CTAButtonProps> = ({ label, onClick }) => {
  return (
    <button
      className="btn btn-primary bg-corporate-blue text-white font-semibold px-6 py-2 rounded shadow hover:bg-blue-700 transition"
      onClick={onClick}
    >
      {label}
    </button>
  );
};

export default CTAButton;
```