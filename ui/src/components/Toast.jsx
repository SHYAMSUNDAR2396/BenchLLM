import { useApp } from '../context/AppContext';

export default function Toast() {
  const { toast } = useApp();
  if (!toast) return null;

  const isError = toast.type === 'error';

  return (
    <div
      className={`fixed bottom-6 right-6 z-[100] px-4 py-3 rounded border font-label-md text-label-md shadow-lg ${
        isError
          ? 'bg-error-container text-on-error-container border-error'
          : 'bg-surface-container-highest text-on-surface border-outline-variant'
      }`}
    >
      {toast.message}
    </div>
  );
}
