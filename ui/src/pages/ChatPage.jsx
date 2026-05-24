import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import { useApp } from '../context/AppContext';
import { getSettings, streamChat } from '../lib/api';

export default function ChatPage() {
  const { ollamaRunning, models, activeModel, setActiveModel, showToast } = useApp();
  const [temperature, setTemperature] = useState(0.7);
  const [jsonMode, setJsonMode] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [model, setModel] = useState(activeModel);
  const bottomRef = useRef(null);

  useEffect(() => {
    getSettings()
      .then((s) => {
        setTemperature(s.default_temperature);
        setModel(s.default_model);
        setJsonMode(s.json_mode_default);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamText]);

  const handleSend = async () => {
    if (!prompt.trim() || streaming) return;

    if (!ollamaRunning) {
      showToast('Ollama is not running. Start with: ollama serve', 'error');
      return;
    }

    const userPrompt = prompt;
    const userMsg = { role: 'user', content: userPrompt };
    setMessages((m) => [...m, userMsg]);
    setPrompt('');
    setStreaming(true);
    setStreamText('');
    setMetrics(null);

    try {
      let full = '';
      for await (const ev of streamChat(userPrompt, model, temperature, jsonMode)) {
        if (ev.error) throw new Error(ev.error);
        if (!ev.done) {
          full += ev.token || '';
          setStreamText(full);
        } else {
          setMetrics(ev.metrics);
          setMessages((m) => [
            ...m,
            { role: 'assistant', content: full, metrics: ev.metrics },
          ]);
          setStreamText('');
        }
      }
    } catch (err) {
      showToast(err.message || 'Chat failed', 'error');
    } finally {
      setStreaming(false);
    }
  };

  const statusBar = metrics
    ? `${model} · ${metrics.tokens_per_sec} tok/s · ${Math.round(metrics.total_latency)}ms`
    : streaming
      ? `${model} · streaming…`
      : `${model} · ready`;

  const modelOptions =
    models.length > 0 ? models : ['llama3.2', 'mistral', 'phi3'];

  return (
    <Layout title="Chat">
      <div className="flex flex-col h-[calc(100vh-64px)] max-w-[960px] mx-auto">
        <div className="flex-1 overflow-y-auto custom-scrollbar p-gutter space-y-stack_md">
          {messages.length === 0 && !streaming && (
            <div className="text-center py-16 text-on-surface-variant">
              <Icon name="smart_toy" className="text-4xl mb-4 opacity-50" />
              <p className="font-body-md text-body-md">Ask anything — runs entirely on your machine.</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`rounded-xl border border-outline-variant p-4 ${
                msg.role === 'user'
                  ? 'bg-transparent ml-12'
                  : 'bg-surface-container-low mr-12'
              }`}
            >
              <p className="font-label-md text-label-md text-on-surface-variant mb-2">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </p>
              <pre className="font-body-md text-body-md whitespace-pre-wrap font-sans">{msg.content}</pre>
            </div>
          ))}
          {streaming && streamText && (
            <div className="rounded-xl border border-outline-variant p-4 bg-surface-container-low mr-12">
              <p className="font-label-md text-label-md text-primary mb-2">Assistant</p>
              <pre className="font-body-md text-body-md whitespace-pre-wrap font-sans streaming-cursor">
                {streamText}
              </pre>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-outline-variant bg-surface-container px-gutter py-3 flex flex-wrap gap-4 items-center">
          <select
            value={model}
            onChange={(e) => {
              setModel(e.target.value);
              setActiveModel(e.target.value);
            }}
            className="bg-surface-container-low border border-outline-variant rounded px-3 py-2 font-label-md text-label-md text-on-surface focus:border-primary"
          >
            {modelOptions.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2 min-w-[160px]">
            <span className="font-label-md text-label-md text-on-surface-variant">Temp</span>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-24"
            />
            <span className="font-code-sm text-code-sm text-primary w-8">{temperature}</span>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={jsonMode}
              onChange={(e) => setJsonMode(e.target.checked)}
              className="rounded border-outline-variant bg-surface-container text-primary"
            />
            <span className="font-label-md text-label-md text-on-surface-variant">JSON mode</span>
          </label>
        </div>

        <div className="border-t border-outline-variant p-gutter flex gap-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Message LocalMind…"
            rows={2}
            className="flex-1 bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 font-body-md text-body-md text-on-surface focus:border-primary focus:outline-none resize-none"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={streaming}
            className="px-6 bg-primary-container text-on-primary-container font-label-md rounded border border-outline-variant hover:opacity-90 disabled:opacity-50"
          >
            <Icon name="send" />
          </button>
        </div>

        <footer className="h-7 bg-surface-container-lowest border-t border-outline-variant flex items-center px-4 font-code-sm text-code-sm text-on-surface-variant">
          {statusBar}
        </footer>
      </div>
    </Layout>
  );
}
