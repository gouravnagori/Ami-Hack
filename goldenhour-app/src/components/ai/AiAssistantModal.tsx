import React, { useState } from 'react';
import { api } from '../../lib/api';
import { useSessionStore } from '../../store/session';
import { Button } from '../ui/Button';

interface AiAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AiAssistantModal: React.FC<AiAssistantModalProps> = ({ isOpen, onClose }) => {
  const { user } = useSessionStore();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState<Array<{ sender: 'user' | 'ai'; text: string; model?: string }>>([
    {
      sender: 'ai',
      text: `Hello ${user?.name || 'Partner'}! I am your GoldenHour AI Assistant, powered by Groq (Llama 3.3). Ask me about FSSAI food safety, pickup timing, packaging standards, 80G tax exemptions, or route optimization.`,
    },
  ]);

  const quickPromptsByRole: Record<string, string[]> = {
    donor: [
      'What are the FSSAI temperature rules for hot food packaging?',
      'How does the Section 80G tax exemption certificate work?',
      'How to safely package paneer and dairy gravy for transit?',
    ],
    recipient: [
      'How to organize intake for 100+ meal portions?',
      'What are the dietary segregation guidelines for shelters?',
      'How do I schedule deliveries before lunch distribution?',
    ],
    driver: [
      'How to maintain cold box temperature during Jaipur afternoon?',
      'What to do if kitchen is running 10 minutes late?',
      'How does the autonomous pickup OTP verification work?',
    ],
    admin: [
      'How does GoldenHour algorithmic replanning handle driver dropouts?',
      'What are the primary food spoilage bottlenecks in Jaipur?',
      'Explain the thermal degradation curve for hot surplus food.',
    ],
  };

  const prompts = quickPromptsByRole[user?.role || 'donor'] || quickPromptsByRole.donor;

  const handleAsk = async (questionText?: string) => {
    const q = (questionText || query).trim();
    if (!q) return;

    const newConvo = [...conversation, { sender: 'user' as const, text: q }];
    setConversation(newConvo);
    setQuery('');
    setLoading(true);

    try {
      const res = await api.post<{
        reply: string;
        role: string;
        model: string;
        powered_by: string;
      }>('/ai/assist', {
        query: q,
        context: {
          role: user?.role,
          name: user?.name,
          city: user?.city,
        },
      });

      setConversation([
        ...newConvo,
        {
          sender: 'ai',
          text: res.reply,
          model: res.powered_by || res.model,
        },
      ]);
    } catch {
      setConversation([
        ...newConvo,
        {
          sender: 'ai',
          text: 'Unable to reach Groq AI at this moment. Food safety advice: Always store cooked hot food above 60°C and cold perishables below 5°C. Pickups must complete within 2 hours of preparation.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.45)',
        backdropFilter: 'blur(3px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '85vh',
          background: 'var(--white)',
          borderRadius: 'var(--r-card-lg)',
          boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid var(--line)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            background: 'var(--deep)',
            color: 'var(--white)',
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}>🤖</span>
            <div>
              <strong style={{ fontSize: '1.05rem', display: 'block' }}>GoldenHour AI Assistant</strong>
              <span style={{ fontSize: '0.74rem', color: 'var(--green)', fontWeight: 600 }}>
                Powered by Groq & Llama 3.3 (Ultra-Fast Inference)
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--white)',
              fontSize: '22px',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '4px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Message Thread */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '18px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            background: '#f8faf7',
          }}
        >
          {conversation.map((msg, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '85%',
                  padding: '12px 16px',
                  borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                  background: msg.sender === 'user' ? 'var(--deep)' : 'var(--white)',
                  color: msg.sender === 'user' ? 'var(--white)' : 'var(--ink)',
                  border: msg.sender === 'user' ? 'none' : '1px solid #e1e8df',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                  fontSize: '0.9rem',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {msg.text}
              </div>
              {msg.model && (
                <span style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: '4px', paddingLeft: '4px' }}>
                  ⚡ {msg.model}
                </span>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--muted)', fontSize: '0.84rem' }}>
              <span>🤖</span>
              <span>Thinking with Groq Llama 3.3...</span>
            </div>
          )}
        </div>

        {/* Quick Prompts */}
        <div style={{ padding: '10px 18px', background: 'var(--white)', borderTop: '1px solid var(--line)' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
            Suggested Questions:
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
            {prompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleAsk(p)}
                disabled={loading}
                style={{
                  background: '#f0f5ee',
                  border: '1px solid #d4ebd4',
                  borderRadius: 'var(--r-pill)',
                  padding: '4px 10px',
                  fontSize: '0.76rem',
                  color: 'var(--deep)',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Query Input */}
        <div
          style={{
            padding: '14px 18px',
            background: 'var(--white)',
            borderTop: '1px solid var(--line)',
            display: 'flex',
            gap: '10px',
          }}
        >
          <input
            type="text"
            placeholder="Ask about food safety, dispatch rules, tax receipts..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAsk();
            }}
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: 'var(--r-card-sm)',
              border: '1px solid var(--line)',
              background: 'var(--paper)',
              fontSize: '0.92rem',
              color: 'var(--ink)',
              outline: 'none',
            }}
          />
          <Button variant="primary" disabled={loading || !query.trim()} onClick={() => handleAsk()}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};
