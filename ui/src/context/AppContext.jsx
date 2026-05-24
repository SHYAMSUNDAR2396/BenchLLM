import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { getStatus } from '../lib/api';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [ollamaRunning, setOllamaRunning] = useState(true);
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState('llama3.2');
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const status = await getStatus();
      setOllamaRunning(status.ollama_running);
      setModels(status.models || []);
      if (status.active_model) setActiveModel(status.active_model);
    } catch {
      setOllamaRunning(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    const id = setInterval(refreshStatus, 15000);
    return () => clearInterval(id);
  }, [refreshStatus]);

  return (
    <AppContext.Provider
      value={{
        ollamaRunning,
        models,
        activeModel,
        setActiveModel,
        refreshStatus,
        showToast,
        toast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
