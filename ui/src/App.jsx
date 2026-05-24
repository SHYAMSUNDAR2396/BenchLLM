import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import ChatPage from './pages/ChatPage';
import BenchmarkPage from './pages/BenchmarkPage';
import ComparisonPage from './pages/ComparisonPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/benchmark" element={<BenchmarkPage />} />
          <Route path="/compare" element={<ComparisonPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
