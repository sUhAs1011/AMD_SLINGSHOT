import React, { useState, useRef, useEffect } from 'react';
import FluidBackground from './components/FluidBackground';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';
import PeerMatchModal from './components/PeerMatchModal';
import CrisisModal from './components/CrisisModal';

const INITIAL_GREETING = 'Hello. I am Kalpana, a safe space to share whatever is on your mind today. How are you feeling?';

// Generate a simple unique session ID
function generateSessionId() {
  return `sess_${Math.random().toString(36).substring(2)}${Date.now().toString(36)}`;
}

function shouldAttemptTts(replyMode, isVoiceInput) {
  if (replyMode === 'text_only') return false;
  if (replyMode === 'voice_preferred') return true;
  return isVoiceInput;
}

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'kalpana',
      content: INITIAL_GREETING,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const [isKalpanaRecordingVoice, setIsKalpanaRecordingVoice] = useState(false);
  const [replyMode, setReplyMode] = useState('auto'); // auto | text_only | voice_preferred
  const [lastDetectedLanguageCode, setLastDetectedLanguageCode] = useState('en-IN');
  const [peerMatch, setPeerMatch] = useState(null);
  const [isCrisisMode, setIsCrisisMode] = useState(false);

  const scrollRef = useRef(null);
  const sessionIdRef = useRef(generateSessionId());
  const apiHistoryRef = useRef([{ role: 'assistant', content: INITIAL_GREETING }]);

  const isUiBusy = isTyping || isVoiceProcessing || isKalpanaRecordingVoice;

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping, isKalpanaRecordingVoice]);

  const modeLabel = (() => {
    if (isVoiceProcessing) return 'Processing voice...';
    if (isKalpanaRecordingVoice) return 'Recording voice note...';
    if (isTyping) return 'Typing...';
    return 'Online';
  })();

  const handleSendMessage = async (text, audioUrl = null, audioBlob = null) => {
    if (isCrisisMode || isUiBusy) return;
    if (!text.trim() && !audioUrl) return;

    const isVoiceInput = Boolean(audioBlob);
    const userVisibleText = text.trim();
    let userTextForApi = userVisibleText;
    let turnLanguageCode = lastDetectedLanguageCode;

    // Add user message to UI immediately.
    const userMsg = { role: 'user', content: userVisibleText, ...(audioUrl && { audioUrl }) };
    setMessages((prev) => [...prev, userMsg]);

    if (isVoiceInput) {
      setIsVoiceProcessing(true);
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice_note.webm');
        formData.append('session_id', sessionIdRef.current);

        const transcribeResponse = await fetch('/api/transcribe', {
          method: 'POST',
          body: formData,
        });
        if (!transcribeResponse.ok) {
          throw new Error(`Transcribe endpoint failed with status ${transcribeResponse.status}`);
        }

        const transcribePayload = await transcribeResponse.json();
        if (transcribePayload.status !== 'success' || !transcribePayload.transcript_en?.trim()) {
          throw new Error(transcribePayload.message || 'Voice transcription failed.');
        }

        userTextForApi = transcribePayload.transcript_en.trim();
        turnLanguageCode =
          transcribePayload.effective_voice_language ||
          transcribePayload.detected_language_code ||
          turnLanguageCode;
        if (turnLanguageCode) {
          setLastDetectedLanguageCode(turnLanguageCode);
        }
      } catch (error) {
        // Fallback: send the visible placeholder text so chat continues.
        console.error('Voice Transcription Error:', error);
        userTextForApi = userVisibleText;
      } finally {
        setIsVoiceProcessing(false);
      }
    }

    setIsTyping(true);
    try {
      // Build chat history for backend from canonical API history, not UI-only messages.
      const chatHistory = [...apiHistoryRef.current, { role: 'user', content: userTextForApi }];

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionIdRef.current,
          chat_history: chatHistory,
        }),
      });
      if (!response.ok) {
        throw new Error('API Response Error');
      }

      // Add an empty Kalpana message that we will stream into.
      setMessages((prev) => [...prev, { role: 'kalpana', content: '' }]);
      setIsTyping(false);

      // Read the SSE stream.
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedAssistantText = '';
      let crisisIntercepted = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse complete SSE lines from the buffer.
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          try {
            const payload = JSON.parse(line.slice(6));

            if (payload.type === 'chunk') {
              streamedAssistantText += payload.content;
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                updated[updated.length - 1] = { ...last, content: last.content + payload.content };
                return updated;
              });
            } else if (payload.type === 'metadata') {
              if (payload.crisis_intercept === true) {
                crisisIntercepted = true;
                setIsCrisisMode(true);
                setPeerMatch(null);
              } else if (payload.peer_group_match) {
                setPeerMatch(payload.peer_group_match);
              }
            }
          } catch {
            // Ignore malformed JSON lines.
          }
        }
      }

      // Persist canonical text history used for future backend turns.
      apiHistoryRef.current = [
        ...apiHistoryRef.current,
        { role: 'user', content: userTextForApi },
        { role: 'assistant', content: streamedAssistantText },
      ];

      const shouldRunTts =
        !crisisIntercepted &&
        streamedAssistantText.trim().length > 0 &&
        shouldAttemptTts(replyMode, isVoiceInput);

      if (shouldRunTts) {
        setIsKalpanaRecordingVoice(true);
        try {
          const ttsResponse = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: streamedAssistantText,
              session_id: sessionIdRef.current,
              target_language_code: turnLanguageCode || null,
            }),
          });

          if (!ttsResponse.ok) {
            throw new Error(`TTS endpoint failed with status ${ttsResponse.status}`);
          }

          const ttsPayload = await ttsResponse.json();
          if (ttsPayload.status === 'success' && ttsPayload.audio_base64) {
            const mimeType = ttsPayload.mime_type || 'audio/mpeg';
            const generatedAudioUrl = `data:${mimeType};base64,${ttsPayload.audio_base64}`;
            if (ttsPayload.spoken_language_code) {
              setLastDetectedLanguageCode(ttsPayload.spoken_language_code);
            }

            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, audioUrl: generatedAudioUrl };
              return updated;
            });
          } else {
            console.warn('TTS fallback to text:', ttsPayload.message || 'No audio payload returned.');
          }
        } catch (error) {
          console.error('TTS Error:', error);
        } finally {
          setIsKalpanaRecordingVoice(false);
        }
      }
    } catch (error) {
      console.error('Chat Error:', error);
      setIsTyping(false);
      setIsKalpanaRecordingVoice(false);

      const fallbackMessage = "I'm sorry, I'm having trouble connecting to my systems right now. Please try again.";
      setMessages((prev) => [
        ...prev,
        {
          role: 'kalpana',
          content: fallbackMessage,
        },
      ]);
      apiHistoryRef.current = [
        ...apiHistoryRef.current,
        { role: 'user', content: userTextForApi },
        { role: 'assistant', content: fallbackMessage },
      ];
    }
  };

  return (
    <div className="relative w-full h-screen overflow-hidden text-kalpana-100 font-sans selection:bg-kalpana-500/30">
      {/* Dynamic Thematic Background */}
      <FluidBackground />

      {/* Main Layout Container */}
      <div className="relative z-10 w-full h-full max-w-4xl mx-auto flex flex-col bg-black/20 backdrop-blur-sm border-x border-kalpana-800/50 shadow-2xl">
        {/* Header */}
        <header className="p-5 border-b border-kalpana-800/80 bg-kalpana-900/60 backdrop-blur-md flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kalpana-500 to-kalpana-800 flex items-center justify-center shadow-[0_0_15px_rgba(216,27,96,0.3)]">
              <span className="text-white text-xl font-bold italic">K</span>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">Kalpana AI</h1>
              <p className="text-xs text-kalpana-300/80">Privacy-First Empathy. {modeLabel}</p>
            </div>
          </div>

          <div className="flex items-center gap-1 rounded-full border border-kalpana-300/20 bg-kalpana-900/60 p-1">
            <button
              type="button"
              onClick={() => setReplyMode('auto')}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                replyMode === 'auto' ? 'bg-kalpana-500 text-white' : 'text-kalpana-300 hover:text-white'
              }`}
            >
              Auto
            </button>
            <button
              type="button"
              onClick={() => setReplyMode('text_only')}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                replyMode === 'text_only' ? 'bg-kalpana-500 text-white' : 'text-kalpana-300 hover:text-white'
              }`}
            >
              Text Only
            </button>
            <button
              type="button"
              onClick={() => setReplyMode('voice_preferred')}
              className={`px-3 py-1.5 text-xs rounded-full transition-colors ${
                replyMode === 'voice_preferred' ? 'bg-kalpana-500 text-white' : 'text-kalpana-300 hover:text-white'
              }`}
            >
              Voice Preferred
            </button>
          </div>
        </header>

        {/* Scrollable Chat Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2 scroll-smooth">
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

          {isKalpanaRecordingVoice && (
            <div className="flex w-full mb-4 justify-start">
              <div className="px-5 py-3 bg-kalpana-800/60 backdrop-blur-md border border-kalpana-300/20 rounded-2xl rounded-tl-sm flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-red-400 animate-pulse" />
                <span className="text-sm text-kalpana-100/90">Kalpana is recording a voice note...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <ChatInput onSendMessage={handleSendMessage} isTyping={isUiBusy} isInputLocked={isCrisisMode} />
      </div>

      {/* Modal View */}
      {!isCrisisMode && (
        <PeerMatchModal
          peerMatch={peerMatch}
          sessionId={sessionIdRef.current}
          onClose={() => setPeerMatch(null)}
        />
      )}
      <CrisisModal isOpen={isCrisisMode} onAcknowledgeSafe={() => setIsCrisisMode(false)} />
    </div>
  );
}

export default App;
