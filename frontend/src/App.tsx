import './App.css';
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

function App() {
  const [chat, setChat] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem('chat-history');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/categories')
      .then((res) => res.json())
      .then((data) => setCategories(data.categories || []));
  }, []);

  useEffect(() => {
    if (chat.length === 0) {
      loadLatestReport();
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('chat-history', JSON.stringify(chat));
    const timer = setTimeout(() => {
      chatEndRef.current?.scrollIntoView();
    }, 10);
    return () => clearTimeout(timer);
  }, [chat]);

  const loadLatestReport = async () => {
    try {
      const response = await fetch('/latest-report');
      if (!response.ok) {
        console.error('Failed to load latest report');
        return;
      }
      const data = await response.json();
      const items: any[] = data.items || [];
      
      if (items.length > 0) {
        const formatted = items
          .map(
            (item: any) =>
              `### [${item.title}](${item.source})\n` +
              `**Categories:** ${item.categories.join(', ')}\n\n` +
              `**Summary:** ${item.summary}\n\n` +
              `**Insights:**\n${(item.insights as string[])
                .map((i: string) => `- ${i}`)
                .join('\n')}\n`
          )
          .join('\n---\n');
        
        setChat([{ sender: 'bot', text: `**Latest Tech Trends Report:**\n\n${formatted}` }]);
      }
    } catch (error) {
      console.error('Error loading latest report:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    let question = input;
    if (selectedCategories.length > 0) {
      question += `\nTell me about these categories only: ${selectedCategories.join(
        ', '
      )}`;
    }
    setChat((prev) => [...prev, { sender: 'user', text: input }]);
    setInput('');
    setLoading(true);
    let answer = '';
    setChat((prev) => [...prev, { sender: 'bot', text: '...' }]);
    
    const response = await fetch('/rag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!response.body) {
      setChat((prev) => [
        ...prev.slice(0, -1),
        { sender: 'bot', text: 'No response.' },
      ]);
      setLoading(false);
      return;
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    
    try {
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value);
          answer += chunk;
          
          setChat((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { sender: 'bot', text: answer };
            return updated;
          });
        }
      }
    } catch (error) {
      console.error('Error during streaming:', error);
      setChat((prev) => [
        ...prev.slice(0, -1),
        { sender: 'bot', text: 'Error occurred during streaming.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReport = async () => {
    setChat((prev) => [...prev, { sender: 'user', text: '[Generate Report]' }]);
    setLoading(true);
    setChat((prev) => [
      ...prev,
      { sender: 'bot', text: 'Generating report...' },
    ]);
    const response = await fetch('/report');
    if (!response.ok) {
      setChat((prev) => [
        ...prev.slice(0, -1),
        { sender: 'bot', text: 'Failed to generate report.' },
      ]);
      setLoading(false);
      return;
    }
    const data = await response.json();
    const items: any[] = data.items || [];
    const formatted = items
      .map(
        (item: any) =>
          `### [${item.title}](${item.source})\n` +
          `**Categories:** ${item.categories.join(', ')}\n\n` +
          `**Summary:** ${item.summary}\n\n` +
          `**Insights:**\n${(item.insights as string[])
            .map((i: string) => `- ${i}`)
            .join('\n')}\n`
      )
      .join('\n---\n');
    setChat((prev) => {
      const updated = [...prev];
      updated[updated.length - 1] = { sender: 'bot', text: formatted };
      return updated;
    });
    setLoading(false);
  };

  const handleCategorySelect = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleClearChat = () => {
    setChat([]);
    localStorage.removeItem('chat-history');
    setTimeout(() => {
      loadLatestReport();
    }, 100);
  };

  return (
    <div
      style={{
        height: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        background: '#fafbfc',
      }}
    >
      <div
        style={{
          maxWidth: 600,
          flex: '1 1 0%',
          minHeight: 0,
          margin: '0 auto',
          padding: '4px 20px 4px 20px',
          border: '1px solid #ddd',
          borderRadius: 8,
          background: '#fafbfc',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <h2 style={{ textAlign: 'center', margin: 0, fontSize: 16 }}>Insights GPT</h2>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={handleClearChat}
                disabled={loading || chat.length === 0}
                style={{
                  padding: '6px 18px',
                  borderRadius: 6,
                  border: 'none',
                  background: '#dc3545',
                  color: '#fff',
                  fontWeight: 500,
                  fontSize: 10,
                  cursor: loading || chat.length === 0 ? 'not-allowed' : 'pointer',
                }}
              >
                Clear chat
              </button>
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ marginBottom: 6, fontWeight: 500 }}>Categories:</div>
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 6,
                maxHeight: 80,
                overflowY: 'auto',
              }}
            >
              {categories.map((cat) => (
                <div
                  key={cat}
                  onClick={() => handleCategorySelect(cat)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 12,
                    border: selectedCategories.includes(cat)
                      ? '2px solid #0d6efd'
                      : '1px solid #ccc',
                    background: selectedCategories.includes(cat)
                      ? '#e7f1ff'
                      : '#f8f9fa',
                    color: '#222',
                    cursor: 'pointer',
                    fontSize: 13,
                    userSelect: 'none',
                  }}
                >
                  {cat}
                </div>
              ))}
            </div>
            {selectedCategories.length > 0 && (
              <div style={{ marginTop: 8, marginBottom: 0 }}>
                {selectedCategories.map((cat) => (
                  <span
                    key={cat}
                    style={{
                      display: 'inline-block',
                      background: '#d1e7dd',
                      color: '#222',
                      borderRadius: 10,
                      padding: '2px 10px',
                      marginRight: 6,
                      fontSize: 12,
                    }}
                  >
                    {cat}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            flex: '1 1 0%',
            minHeight: 0,
          }}
        >
          <div
            className="chat-container"
            style={{
              flex: '1 1 0%',
              overflowY: 'auto',
              background: '#fff',
              padding: 16,
              borderRadius: 6,
              border: '1px solid #eee',
              marginBottom: 16,
            }}
          >
            {chat.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  textAlign: msg.sender === 'user' ? 'right' : 'left',
                  margin: '8px 0',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    background: msg.sender === 'user' ? '#d1e7dd' : '#e2e3e5',
                    color: '#222',
                    borderRadius: 12,
                    padding: '8px 14px',
                    maxWidth: '80%',
                    wordBreak: 'break-word',
                  }}
                >
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </span>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 0 }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !loading) handleSend();
              }}
              placeholder="Ask a question..."
              style={{
                flex: 1,
                padding: 10,
                borderRadius: 6,
                border: '1px solid #ccc',
              }}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={{
                padding: '0 18px',
                borderRadius: 6,
                border: 'none',
                background: '#0d6efd',
                color: '#fff',
                opacity: !input.trim() || loading ? 0.5 : 1,
                cursor: !input.trim() || loading ? 'not-allowed' : 'pointer',
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
