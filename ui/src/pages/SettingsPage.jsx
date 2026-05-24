import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import { useApp } from '../context/AppContext';
import { getSettings, getStatus, saveSettings } from '../lib/api';

export default function SettingsPage() {
  const { showToast, models, refreshStatus } = useApp();
  const [form, setForm] = useState({
    ollama_base_url: 'http://localhost:11434',
    default_model: 'llama3.2',
    default_temperature: 0.7,
    max_tokens: 2048,
    json_mode_default: false,
  });
  const [jsonToggle, setJsonToggle] = useState(false);
  const [loadedModels, setLoadedModels] = useState([]);

  useEffect(() => {
    getSettings()
      .then((s) => {
        setForm(s);
        setJsonToggle(s.json_mode_default);
      })
      .catch(() => showToast('Failed to load settings', 'error'));
    getStatus()
      .then((s) => setLoadedModels(s.models || []))
      .catch(() => {});
  }, [showToast]);

  const handleSave = async () => {
    try {
      await saveSettings({ ...form, json_mode_default: jsonToggle });
      await refreshStatus();
      showToast('Settings saved successfully');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const modelOptions = loadedModels.length ? loadedModels : models;

  return (
    <Layout title="Settings">
      <div className="flex flex-col items-center w-full max-w-[960px] mx-auto px-gutter py-12 space-y-12">
        <div className="w-full space-y-2">
          <h3 className="font-headline-lg text-headline-lg text-on-surface">Configuration</h3>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Tailor your local inference experience. These settings directly affect the performance
            and response quality of the models running on your machine via Ollama.
          </p>
        </div>

        <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-8">
          <div className="md:col-span-8 space-y-10">
            <div className="space-y-4">
              <label className="flex items-center gap-2 font-label-md text-primary uppercase tracking-wider">
                <Icon name="lan" className="text-[18px]" />
                Connection
              </label>
              <div className="space-y-2">
                <label className="font-label-md text-on-surface-variant" htmlFor="base-url">
                  Ollama base URL
                </label>
                <input
                  id="base-url"
                  type="text"
                  value={form.ollama_base_url}
                  onChange={(e) => setForm({ ...form, ollama_base_url: e.target.value })}
                  className="w-full bg-surface-container-low border border-outline-variant rounded px-4 py-3 font-code-sm text-code-sm focus:border-primary"
                />
              </div>
            </div>

            <div className="space-y-4">
              <label className="flex items-center gap-2 font-label-md text-primary uppercase tracking-wider">
                <Icon name="psychology" className="text-[18px]" />
                Core Model
              </label>
              <select
                id="default-model"
                value={form.default_model}
                onChange={(e) => setForm({ ...form, default_model: e.target.value })}
                className="w-full bg-surface-container-low border border-outline-variant rounded px-4 py-3 font-body-md focus:border-primary"
              >
                {modelOptions.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-6">
              <label className="flex items-center gap-2 font-label-md text-primary uppercase tracking-wider">
                <Icon name="tune" className="text-[18px]" />
                Inference Parameters
              </label>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <label className="font-label-md text-on-surface-variant">Temperature</label>
                  <span className="font-code-sm text-primary">{form.default_temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={form.default_temperature}
                  onChange={(e) =>
                    setForm({ ...form, default_temperature: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <label className="font-label-md text-on-surface-variant" htmlFor="max-tokens">
                  Max Tokens
                </label>
                <input
                  id="max-tokens"
                  type="number"
                  value={form.max_tokens}
                  onChange={(e) => setForm({ ...form, max_tokens: Number(e.target.value) })}
                  className="w-full bg-surface-container-low border border-outline-variant rounded px-4 py-3 font-code-sm focus:border-primary"
                />
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-surface-container-low border border-outline-variant rounded">
              <div>
                <p className="font-label-md text-on-surface">JSON mode</p>
                <p className="text-[12px] text-on-surface-variant opacity-70">
                  Force the model to output valid JSON structures.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setJsonToggle(!jsonToggle)}
                className={`relative inline-flex h-6 w-11 rounded-full border-2 border-transparent transition-colors ${
                  jsonToggle ? 'bg-primary' : 'bg-surface-variant'
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${
                    jsonToggle ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            <div className="pt-6 border-t border-outline-variant flex justify-end">
              <button
                type="button"
                onClick={handleSave}
                className="px-8 py-3 bg-primary-container text-on-primary-container font-label-md rounded border border-outline-variant hover:brightness-110 flex items-center gap-2"
              >
                <Icon name="save" className="text-[20px]" />
                Save Settings
              </button>
            </div>
          </div>

          <div className="md:col-span-4 space-y-6">
            <div className="p-6 border border-outline-variant rounded bg-surface-container-low space-y-4">
              <h4 className="font-label-md text-on-surface flex items-center gap-2">
                <Icon name="data_usage" className="text-primary" />
                System Health
              </h4>
              <p className="text-[12px] text-on-surface-variant">Live stats from your machine</p>
            </div>
            <div className="p-6 border border-outline-variant rounded bg-surface-container-low space-y-4">
              <h4 className="font-label-md text-on-surface">Loaded Models</h4>
              <div className="flex flex-wrap gap-2">
                {modelOptions.slice(0, 6).map((m, i) => {
                  const styles = [
                    'border-primary/40 bg-primary/10 text-primary',
                    'border-secondary/40 bg-secondary/10 text-secondary',
                    'border-tertiary/40 bg-tertiary/10 text-tertiary',
                  ];
                  return (
                    <div
                      key={m}
                      className={`px-3 py-1 rounded-full border text-[11px] font-code-sm ${styles[i % 3]}`}
                    >
                      {m}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
