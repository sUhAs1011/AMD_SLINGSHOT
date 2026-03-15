import React, { useState, useRef } from 'react';
import { Send, Mic, Trash2 } from 'lucide-react';

const ChatInput = ({ onSendMessage, isTyping }) => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef(null);
  const recordingTimeRef = useRef(0);
  const isInitializingRef = useRef(false);
  
  // MediaRecorder refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    onSendMessage(input.trim());
    setInput('');
  };

  const startRecording = async () => {
    if (isTyping || isRecording || isInitializingRef.current) return;
    isInitializingRef.current = true;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Setup recorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
        
        // Send the voice note using the ref to get the correct time
        onSendMessage(`[🎤 Voice Note - ${formatTime(recordingTimeRef.current)}]`, audioUrl);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      recordingTimeRef.current = 0;
      isInitializingRef.current = false;
      
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;
          recordingTimeRef.current = newTime;
          return newTime;
        });
      }, 1000);

    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access is required to send voice notes.");
      isInitializingRef.current = false;
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop(); // This triggers the onstop event which handles the cleanup
      clearInterval(timerRef.current);
      timerRef.current = null;
      setIsRecording(false);
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = null; // Disable the save handler
      mediaRecorderRef.current.stop();
      
      // Stop all tracks to release the microphone
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      audioChunksRef.current = []; // Discard chunks
      clearInterval(timerRef.current);
      timerRef.current = null;
      setRecordingTime(0);
      recordingTimeRef.current = 0;
      setIsRecording(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full bg-kalpana-900/50 backdrop-blur-lg border-t border-kalpana-800 p-4">
      <div className="max-w-4xl mx-auto relative h-14 flex items-center">
        
        {isRecording ? (
          /* Voice Recording UI */
          <div className="w-full h-full bg-kalpana-800/80 text-kalpana-100 border border-kalpana-500/50 rounded-full flex items-center justify-between px-6 shadow-[0_0_15px_rgba(216,27,96,0.2)] animate-in fade-in zoom-in duration-300">
            <div className="flex items-center gap-3 text-kalpana-300">
              {/* Pulsing Red Recording Dot */}
              <span className="w-3 h-3 rounded-full bg-red-500 animate-[pulse_1.5s_ease-in-out_infinite]" />
              <span className="font-mono text-lg transition-all">{formatTime(recordingTime)}</span>
              <span className="ml-2 text-sm text-kalpana-300/60 animate-pulse">Recording...</span>
            </div>
            
            <div className="flex items-center gap-3">
              <button 
                onClick={cancelRecording}
                className="p-2 text-kalpana-300 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-all duration-300"
                title="Cancel Recording"
              >
                <Trash2 size={20} />
              </button>
              <button 
                onClick={stopRecording}
                className="w-10 h-10 rounded-full bg-kalpana-500 text-white flex items-center justify-center hover:bg-[#E6007A] shadow-[0_0_15px_rgba(216,27,96,0.3)] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)] transition-all duration-300 hover:scale-105"
                title="Send Voice Note"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        ) : (
          /* Standard Text Input UI */
          <form onSubmit={handleSubmit} className="relative flex items-center w-full h-full">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isTyping}
              placeholder={isTyping ? "Kalpana is typing..." : "Type your message here..."}
              className="w-full h-full bg-kalpana-800/40 text-kalpana-100 placeholder-kalpana-300/50 
                         border border-kalpana-300/20 rounded-full py-0 pl-6 pr-14 
                         focus:outline-none focus:ring-2 focus:ring-kalpana-500/50 transition-all duration-300"
            />
            
            {/* Toggle between Mic icon (when empty) and Send icon (when typed) */}
            {input.trim() ? (
              <button
                type="submit"
                disabled={isTyping}
                className="absolute right-2 p-2.5 rounded-full bg-kalpana-500 text-white
                           hover:bg-[#E6007A] disabled:opacity-50 disabled:cursor-not-allowed
                           shadow-[0_0_15px_rgba(216,27,96,0.3)] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)]
                           transition-all duration-300 hover:scale-105 animate-in zoom-in"
              >
                <Send size={18} />
              </button>
            ) : (
              <button
                type="button"
                onClick={startRecording}
                disabled={isTyping}
                className="absolute right-2 p-2.5 rounded-full bg-kalpana-800 text-kalpana-300 border border-kalpana-300/20
                           hover:text-kalpana-500 hover:border-kalpana-500/50 hover:bg-kalpana-800 disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all duration-300 animate-in zoom-in"
                title="Record Voice Note"
              >
                <Mic size={18} />
              </button>
            )}
          </form>
        )}

      </div>
    </div>
  );
};

export default ChatInput;
