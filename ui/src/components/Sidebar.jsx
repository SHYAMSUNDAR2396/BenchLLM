import { NavLink } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import Icon from './Icon';

const nav = [
  { to: '/', label: 'Chat', icon: 'chat' },
  { to: '/benchmark', label: 'Benchmark', icon: 'speed' },
  { to: '/compare', label: 'Compare', icon: 'compare_arrows' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
];

export default function Sidebar() {
  const { ollamaRunning } = useApp();

  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] bg-surface-container border-r border-outline-variant flex flex-col py-base_unit z-50">
      <div className="px-gutter mb-stack_md flex items-center gap-3">
        <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-on-primary">
          <Icon name="memory" className="text-headline-sm" />
        </div>
        <div>
          <h1 className="font-headline-md text-headline-md text-primary leading-none">LocalMind AI</h1>
          <p className="font-label-md text-label-md text-on-surface-variant">Local Inference</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1">
        {nav.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2 transition-colors ${
                isActive
                  ? 'text-primary border-l-2 border-primary bg-surface-container-highest'
                  : 'text-on-surface-variant hover:bg-surface-variant'
              }`
            }
          >
            <Icon name={icon} />
            <span className="font-label-md text-label-md">{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-stack_sm">
        <button
          type="button"
          className="w-full bg-primary-container text-on-primary-container font-label-md text-label-md py-2 rounded border border-outline-variant hover:opacity-90 transition-opacity"
        >
          New Thread
        </button>
      </div>
      <div className="mt-auto border-t border-outline-variant pt-stack_sm">
        <div className="flex items-center gap-3 px-4 py-2 text-on-surface-variant">
          <div
            className={`w-2 h-2 rounded-full ${ollamaRunning ? 'bg-primary pulse-indicator' : 'bg-error'}`}
          />
          <Icon name="sensors" className="text-[18px]" />
          <span className="font-label-md text-label-md">Ollama Status</span>
        </div>
      </div>
    </aside>
  );
}
