import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import { useApp } from '../context/AppContext';
import { getComparisonReport, getComparisonResults, runComparison } from '../lib/api';

const COLOR_MAP = {
  primary: { text: 'text-primary', bar: 'bg-primary', border: 'hover:border-primary/50' },
  secondary: { text: 'text-secondary', bar: 'bg-secondary', border: 'hover:border-secondary/50' },
  tertiary: { text: 'text-tertiary', bar: 'bg-tertiary', border: 'hover:border-tertiary/50' },
};

export default function ComparisonPage() {
  const { showToast } = useApp();
  const [data, setData] = useState({ models: [], prompt_list: [] });
  const [selectedPromptId, setSelectedPromptId] = useState('');
  const [running, setRunning] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportMd, setReportMd] = useState('');

  const load = async () => {
    try {
      const res = await getComparisonResults();
      setData(res);
      if (res.prompt_list?.length && !selectedPromptId) {
        setSelectedPromptId(res.prompt_list[0].id);
      }
    } catch {
      /* empty state */
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectedPrompt = data.prompt_list?.find((p) => p.id === selectedPromptId);

  const responsesForPrompt = (modelEntry) => {
    const p = modelEntry.prompts?.find((x) => x.prompt_id === selectedPromptId);
    return p || null;
  };

  const maxTps = Math.max(...(data.models?.map((m) => m.avg_tokens_per_sec) || [1]), 1);

  const handleGenerateReport = async () => {
    if (!data.models?.length) {
      setRunning(true);
      try {
        for await (const ev of runComparison()) {
          if (ev.status === 'error') showToast(ev.detail, 'error');
        }
        await load();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        setRunning(false);
      }
    }
    try {
      const md = await getComparisonReport();
      setReportMd(md);
      setReportOpen(true);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const headerRight = (
    <button
      type="button"
      onClick={handleGenerateReport}
      disabled={running}
      className="bg-primary-container text-on-primary-container px-4 py-1.5 rounded font-label-md flex items-center gap-2 hover:opacity-90 disabled:opacity-50"
    >
      {running ? 'Running…' : 'Generate Report'}
      <Icon name="summarize" className="text-[18px]" />
    </button>
  );

  return (
    <Layout title="Model Comparison" headerRight={headerRight}>
      <div className="p-gutter min-h-[calc(100vh-64px)]">
        <div className="max-w-[1200px] mx-auto space-y-gutter">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-stack_md">
            {data.models?.length ? (
              data.models.map((m) => {
                const c = COLOR_MAP[m.color] || COLOR_MAP.primary;
                const barPct = Math.min(100, (m.avg_tokens_per_sec / maxTps) * 100);
                return (
                  <div
                    key={m.model}
                    className={`bg-surface-container-low border border-outline-variant p-stack_md rounded ${c.border}`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <span className={`font-headline-md text-label-md ${c.text}`}>{m.label}</span>
                      <span
                        className={`px-2 py-0.5 border text-[10px] rounded-full uppercase ${c.text} border-current/20`}
                      >
                        {m.quantization}
                      </span>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="font-label-md text-on-surface-variant text-[12px]">
                          Avg tokens/sec
                        </span>
                        <span className="font-code-sm">{m.avg_tokens_per_sec} t/s</span>
                      </div>
                      <div className="w-full bg-surface-variant h-1.5 rounded-full overflow-hidden">
                        <div className={`${c.bar} h-full`} style={{ width: `${barPct}%` }} />
                      </div>
                      <div className="grid grid-cols-2 gap-4 pt-2">
                        <div>
                          <p className="font-label-md text-[11px] text-on-surface-variant uppercase opacity-60">
                            Memory
                          </p>
                          <p className="font-code-sm">{m.avg_memory_mb} MB</p>
                        </div>
                        <div>
                          <p className="font-label-md text-[11px] text-on-surface-variant uppercase opacity-60">
                            Quality
                          </p>
                          <p className="font-code-sm">{m.quality_score} / 10</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="col-span-3 text-on-surface-variant font-body-md">
                No comparison data yet. Click Generate Report to run all models × 40 prompts.
              </p>
            )}
          </div>

          <div className="bg-surface-container-low border border-outline-variant rounded-xl flex flex-col h-[600px] overflow-hidden">
            <div className="p-4 border-b border-outline-variant flex items-center gap-4">
              <span className="font-label-md">Current Prompt:</span>
              <select
                value={selectedPromptId}
                onChange={(e) => setSelectedPromptId(e.target.value)}
                className="bg-surface-variant px-4 py-1.5 rounded border border-outline-variant font-label-md max-w-md truncate"
              >
                {data.prompt_list?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.text.slice(0, 60)}…
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-1 overflow-hidden divide-x divide-outline-variant">
              {data.models?.map((m) => {
                const c = COLOR_MAP[m.color] || COLOR_MAP.primary;
                const resp = responsesForPrompt(m);
                return (
                  <div key={m.model} className="flex-1 flex flex-col overflow-hidden">
                    <div className="p-3 border-b border-outline-variant/30 flex justify-between">
                      <span className={`font-code-sm text-[12px] ${c.text}`}>{m.label} Response</span>
                      <span className="font-code-sm text-[11px] opacity-50">
                        {resp ? `${Math.round(resp.total_latency)}ms` : '—'}
                      </span>
                    </div>
                    <div className="p-6 overflow-y-auto custom-scrollbar flex-1 font-body-md text-on-surface-variant leading-relaxed">
                      {resp?.response || (
                        <span className="opacity-50">No response for this prompt</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {reportOpen && (
        <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-8">
          <div className="bg-surface-container border border-outline-variant rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-outline-variant">
              <h3 className="font-headline-sm text-headline-sm">Comparison Report</h3>
              <button
                type="button"
                onClick={() => setReportOpen(false)}
                className="text-on-surface-variant hover:text-primary"
              >
                <Icon name="close" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar prose prose-invert max-w-none">
              <ReactMarkdown>{reportMd}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
