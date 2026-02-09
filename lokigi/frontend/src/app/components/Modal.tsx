```tsx
import React from 'react';

interface ModalProps {
  title: string;
  children: React.ReactNode;
  actions: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ title, children, actions }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
      <div className="bg-white border border-corporate-gray rounded-lg shadow-lg p-8 max-w-lg w-full">
        <h2 className="text-2xl font-bold text-corporate-blue mb-4">{title}</h2>
        <div className="text-corporate-dark mb-6">{children}</div>
        <div className="flex justify-end gap-2">
          {actions}
        </div>
      </div>
    </div>
  );
};

export default Modal;
```