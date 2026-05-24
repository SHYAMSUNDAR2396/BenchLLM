import { useState } from 'react';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import { useApp } from '../context/AppContext';
import { runBenchmark } from '../lib/api';

const DEFAULT_MODELS = [
  { id: 'mistral', label: 'Mistral 7B', arch: 'Mistral' },
  { id: 'llama3.2', label: 'Llama 3 8B', arch: 'Llama' },
  { id: 'phi3', label: 'Phi-3 Mini', arch: 'Phi' },
];

export default function BenchmarkPage() {
  const { ollamaRunning, models, showToast } = useApp();
  const [numPrompts, setNumPrompts] = useState(10);
  const [selected, setSelected] = useState(['mistral', 'llama3.2']);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(null);
  const [results, setResults] = useState([]);

  const available = models.length
    ? DEFAULT_MODELS.filter((m) => models.some((om) => om.includes(m.id.split(':')[0]) || om === m.id))
    : DEFAULT_MODELS;

  const toggleModel = (id) => {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  };

  const handleRun = async () => {
    if (!ollamaRunning) {
      showToast('Ollama is not running. Start with: ollama serve', 'error');
      return;
    }
    if (!selected.length) {
      showToast('Select at least one model', 'error');
      return;
    }

    setRunning(true);
    setResults([]);
    setProgress({ model: selected[0], prompt_num: 0, total: numPrompts, current_tps: 0 });

    try {
      for await (const ev of runBenchmark(selected, numPrompts)) {
        if (ev.status === 'complete') {
          setResults(ev.results || []);
          setProgress(null);
        } else if (ev.status === 'error') {
          showToast(ev.detail, 'error');
        } else {
          setProgress(ev);
        }
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setRunning(false);
    }
  };

  const winnerTps = results.length
    ? Math.max(...results.map((r) => r.avg_tokens_per_sec))
    : 0;

  const pct = progress
    ? Math.round((progress.prompt_num / progress.total) * 100)
    : results.length
      ? 100
      : 0;

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify({ models: results }, null, 2)], {
      type: 'application/json',
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'benchmark_results.json';
    a.click();
  };

  return (
    <Layout title="Benchmark">
      <div className="p-gutter h-[calc(100vh-64px)] overflow-y-auto custom-scrollbar">
        <div className="max-w-[960px] mx-auto space-y-stack_md">
          <section>
            <h1 className="font-headline-lg text-headline-lg text-on-surface">Benchmark Models</h1>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Measure inference performance on your hardware using standardized prompts.
            </p>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
            <div className="md:col-span-1 bg-surface-container-low border border-outline-variant rounded-lg p-stack_md">
              <h3 className="font-headline-sm text-headline-sm mb-4">Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface-variant mb-2">
                    Number of Prompts
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={numPrompts}
                    onChange={(e) => setNumPrompts(Number(e.target.value))}
                    className="w-full bg-surface-container border border-outline-variant rounded px-3 py-2 text-on-surface focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block font-label-md text-label-md text-on-surface-variant mb-2">
                    Select Models
                  </label>
                  <div className="space-y-2">
                    {available.map((m) => (
                      <label key={m.id} className="flex items-center gap-3 cursor-pointer group">
                        <input
                          type="checkbox"
                          checked={selected.includes(m.id)}
                          onChange={() => toggleModel(m.id)}
                          className="rounded border-outline-variant bg-surface-container text-primary"
                        />
                        <span className="font-body-md text-body-md text-on-surface group-hover:text-primary">
                          {m.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleRun}
                  disabled={running}
                  className="w-full mt-4 bg-primary-container text-on-primary-container font-label-md py-3 rounded border border-outline-variant flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-50"
                >
                  <Icon name="play_arrow" className="text-[18px]" />
                  Run Benchmark
                </button>
              </div>
            </div>

            <div className="md:col-span-2 bg-surface-container border border-outline-variant rounded-lg p-stack_md">
              <div>
                <h3 className="font-headline-sm text-headline-sm text-primary">
                  {running ? 'In Progress' : results.length ? 'Complete' : 'Ready'}
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  {progress
                    ? `Currently testing ${progress.model} — prompt ${progress.prompt_num}/${progress.total}`
                    : 'Configure models and run benchmark'}
                </p>
              </div>
              <div className="mt-6 space-y-6">
                <div>
                  <div className="flex justify-between font-label-md text-label-md mb-2">
                    <span className="text-on-surface">
                      {progress
                        ? `${progress.model} — prompt ${progress.prompt_num}/${progress.total}`
                        : 'Progress'}
                    </span>
                    <span className="text-primary">{pct}%</span>
                  </div>
                  <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-surface-container-low border border-outline-variant rounded">
                    <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">
                      Current Speed
                    </p>
                    <p className="font-headline-md text-headline-md text-on-surface">
                      {progress?.current_tps?.toFixed?.(1) ?? '—'}{' '}
                      <span className="text-body-md text-on-surface-variant">t/s</span>
                    </p>
                  </div>
                  <div className="p-4 bg-surface-container-low border border-outline-variant rounded">
                    <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">
                      Status
                    </p>
                    <p className="font-headline-md text-headline-md text-on-surface">
                      {running ? 'Running' : 'Idle'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <section className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
            <div className="px-gutter py-4 border-b border-outline-variant flex justify-between items-center">
              <h3 className="font-headline-sm text-headline-sm">Benchmark Results</h3>
              <button
                type="button"
                onClick={downloadJson}
                disabled={!results.length}
                className="text-primary flex items-center gap-2 font-label-md hover:bg-surface-variant px-3 py-1.5 rounded disabled:opacity-40"
              >
                <Icon name="download" className="text-[18px]" />
                Save as JSON
              </button>
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-highest/30">
                  <th className="px-gutter py-3 font-label-md text-on-surface-variant uppercase">Model</th>
                  <th className="px-gutter py-3 font-label-md text-on-surface-variant uppercase">Architecture</th>
                  <th className="px-gutter py-3 font-label-md text-on-surface-variant uppercase">Tokens/sec</th>
                  <th className="px-gutter py-3 font-label-md text-on-surface-variant uppercase text-right">
                    Latency
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/50">
                {results.map((r) => {
                  const isWinner = r.avg_tokens_per_sec === winnerTps && winnerTps > 0;
                  return (
                    <tr
                      key={r.model}
                      className={isWinner ? 'bg-primary/5' : 'hover:bg-surface-variant/20'}
                    >
                      <td className="px-gutter py-4 flex items-center gap-3">
                        {isWinner && (
                          <Icon name="workspace_premium" className="text-primary" filled />
                        )}
                        <span
                          className={`font-body-md ${isWinner ? 'text-primary font-semibold' : 'text-on-surface pl-9'}`}
                        >
                          {r.model}
                        </span>
                      </td>
                      <td className="px-gutter py-4 text-on-surface-variant">{r.architecture}</td>
                      <td className="px-gutter py-4">
                        <span
                          className={`font-code-sm px-2 py-0.5 border rounded ${
                            isWinner
                              ? 'text-primary bg-primary/10 border-primary/20'
                              : 'text-on-surface border-outline-variant'
                          }`}
                        >
                          {r.avg_tokens_per_sec} t/s
                        </span>
                      </td>
                      <td className="px-gutter py-4 font-code-sm text-right">
                        {r.avg_latency_ms} ms
                      </td>
                    </tr>
                  );
                })}
                {!results.length && (
                  <tr>
                    <td colSpan={4} className="px-gutter py-8 text-center text-on-surface-variant">
                      Run a benchmark to see results
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        </div>
      </div>
    </Layout>
  );
}
