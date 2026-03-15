import React, { useState, useRef, useEffect } from 'react';
import FluidBackground from './components/FluidBackground';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';
import PeerMatchModal from './components/PeerMatchModal';

// Generate a simple unique session ID
function generateSessionId() {
  return 'sess_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'kalpana',
      content: 'Hello. I am Kalpana, a safe space to share whatever is on your mind today. How are you feeling?'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [peerMatch, setPeerMatch] = useState(null);
  const scrollRef = useRef(null);
  const sessionIdRef = useRef(generateSessionId());

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSendMessage = async (text, audioUrl = null) => {
    if (!text.trim() && !audioUrl) return;

    // Add user message to UI immediately
    const userMsg = { role: 'user', content: text, ...(audioUrl && { audioUrl }) };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      // Build chat history for the API (all messages including the new one)
      const chatHistory = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content
      }));

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionIdRef.current,
          chat_history: chatHistory
        })
      });

      if (!response.ok) {
        throw new Error('API Response Error');
      }

      // Add an empty Kalpana message that we will stream into
      setMessages(prev => [...prev, { role: 'kalpana', content: '' }]);
      setIsTyping(false);

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse complete SSE lines from the buffer
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          try {
            const payload = JSON.parse(line.slice(6)); // Remove "data: " prefix

            if (payload.type === 'chunk') {
              // Append text chunk to the last (Kalpana) message
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = { ...last, content: last.content + payload.content };
                return updated;
              });
            } else if (payload.type === 'metadata') {
              // Handle peer match notification
              if (payload.peer_group_match) {
                setPeerMatch(payload.peer_group_match);
              }
            }
          } catch {
            // Ignore malformed JSON lines
          }
        }
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setIsTyping(false);
      setMessages(prev => [...prev, {
        role: 'kalpana',
        content: "I'm sorry, I'm having trouble connecting to my systems right now. Please try again."
      }]);
    }
  };

  return (
    <div className="relative w-full h-screen overflow-hidden text-kalpana-100 font-sans selection:bg-kalpana-500/30">
      {/* Dynamic Thematic Background */}
      <FluidBackground />

      {/* Main Layout Container */}
      <div className="relative z-10 w-full h-full max-w-4xl mx-auto flex flex-col bg-black/20 backdrop-blur-sm border-x border-kalpana-800/50 shadow-2xl">
        
        {/* Header */}
        <header className="p-5 border-b border-kalpana-800/80 bg-kalpana-900/60 backdrop-blur-md flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kalpana-500 to-kalpana-800 flex items-center justify-center shadow-[0_0_15px_rgba(216,27,96,0.3)]">
            <span className="text-white text-xl font-bold italic">K</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Kalpana AI</h1>
            <p className="text-xs text-kalpana-300/80">Privacy-First Empathy. {isTyping && "Typing..."}</p>
          </div>
        </header>

        {/* Scrollable Chat Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2 scroll-smooth"
        >
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
          ))}

          {isTyping && (
            <div className="flex w-full mb-4 justify-start">
              <div className="px-5 py-4 bg-kalpana-800/50 backdrop-blur-md border border-kalpana-300/20 rounded-2xl rounded-tl-sm flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-kalpana-300/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-kalpana-300/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-kalpana-300/60 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <ChatInput onSendMessage={handleSendMessage} isTyping={isTyping} />
      </div>

      {/* Modal View */}
      <PeerMatchModal peerMatch={peerMatch} onClose={() => setPeerMatch(null)} />
    </div>
  );
}

export default App;
