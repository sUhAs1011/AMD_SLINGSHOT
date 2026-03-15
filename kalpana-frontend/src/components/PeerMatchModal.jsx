import React, { useState, useRef, useEffect } from 'react';

const PeerMatchModal = ({ peerMatch, sessionId, onClose }) => {
  const [connectionStatus, setConnectionStatus] = useState('idle'); // 'idle' | 'connecting' | 'connected' | 'error'
  const [isCustomTime, setIsCustomTime] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(
    peerMatch?.availability?.length > 0 ? peerMatch.availability[0].start_time : ''
  );
  const [customTime, setCustomTime] = useState('');
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!peerMatch) return null;

  // Helper to format ISO to readable string (e.g., "Saturday, 10:00 AM")
  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  const handleSchedule = async () => {
    const finalSlot = isCustomTime ? customTime : selectedSlot;
    
    if (!finalSlot) {
      alert("Please select a time.");
      return;
    }

    setConnectionStatus('connecting');

    try {
      const res = await fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          peer_id: peerMatch.peer_id,
          selected_slot: finalSlot,
        }),
      });

      if (res.ok) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('error');
      }
    } catch (e) {
      console.error(e);
      setConnectionStatus('error');
    }
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="relative w-full max-w-sm overflow-hidden bg-kalpana-800 border border-kalpana-500/50 rounded-3xl shadow-[0_0_50px_rgba(216,27,96,0.2)] animate-in slide-in-from-bottom-4 duration-500">
        <div className="h-2 w-full bg-gradient-to-r from-kalpana-300 via-kalpana-500 to-kalpana-800" />
        
        <div className="p-8 text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-full bg-kalpana-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(216,27,96,0.4)]">
            <span className="text-3xl">
              {connectionStatus === 'connecting' ? '🔄' : 
               connectionStatus === 'connected' ? '✅' : '🤝'}
            </span>
          </div>

          <div className="space-y-2">
            <h3 className="text-2xl font-semibold text-white">
              {connectionStatus === 'connecting' ? 'Locking In Your Slot...' : 
               connectionStatus === 'connected' ? '🎉 You Are Not Alone' : '💙 Someone Understands'}
            </h3>
            
            {connectionStatus === 'idle' || connectionStatus === 'error' ? (
              <div className="space-y-3">
                <p className="text-sm text-kalpana-100/80 leading-relaxed">
                  We found someone who truly gets it. <strong className="font-bold text-white">{peerMatch.peer_id}</strong> has personally lived through{' '}
                  <span className="text-kalpana-300 font-medium">{peerMatch.root_cause || 'a similar experience'}</span> and came out the other side.
                </p>
                <p className="text-xs text-kalpana-100/70 leading-relaxed italic border-l-2 border-kalpana-500/40 pl-3">
                  Pick a time below to connect — you don&rsquo;t have to go through this alone.
                </p>
                {connectionStatus === 'error' && <span className="block text-red-400 mt-2 text-xs">Failed to save appointment. Please try again.</span>}
              </div>
            ) : connectionStatus === 'connecting' ? (
              <p className="text-sm text-kalpana-100/80 leading-relaxed">
                Saving your appointment with <strong className="font-bold text-white">{peerMatch.peer_id}</strong> ...
              </p>
            ) : (
              <p className="text-sm text-kalpana-100/80 leading-relaxed">
                Your connection with <strong className="font-bold text-white">{peerMatch.peer_id}</strong> is confirmed. A real person who has walked your path will meet you at the scheduled time. You took a brave step today. 💙
              </p>
            )}
          </div>

          {/* Scheduling UI */}
          {(connectionStatus === 'idle' || connectionStatus === 'error') && (
            <div className="text-left space-y-4">
              {!isCustomTime ? (
                <div className="flex flex-col gap-2" ref={dropdownRef}>
                  <label className="text-xs text-kalpana-300 uppercase tracking-wider font-semibold">
                    Available Slots
                  </label>
                  {/* Custom dropdown trigger */}
                  <div
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="w-full bg-kalpana-900 border border-kalpana-500/30 rounded-xl p-3 text-sm text-white flex items-center justify-between cursor-pointer hover:border-kalpana-500 transition-colors"
                  >
                    <span>{selectedSlot ? formatTime(selectedSlot) : 'Select a time slot...'}</span>
                    <span className="text-kalpana-300 ml-2">{isDropdownOpen ? '▲' : '▼'}</span>
                  </div>

                  {/* Custom dropdown options panel */}
                  {isDropdownOpen && (
                    <div className="w-full bg-[#1a0a2e] border border-kalpana-500/40 rounded-xl overflow-hidden shadow-lg z-10">
                      {peerMatch.availability?.length > 0 ? (
                        peerMatch.availability.map((slot, i) => (
                          <div
                            key={i}
                            onClick={() => {
                              setSelectedSlot(slot.start_time);
                              setIsDropdownOpen(false);
                            }}
                            className={`px-4 py-3 text-sm cursor-pointer transition-colors hover:bg-kalpana-500/20 ${
                              selectedSlot === slot.start_time
                                ? 'text-white font-semibold bg-kalpana-500/10 border-l-2 border-kalpana-500'
                                : 'text-kalpana-100/80'
                            }`}
                          >
                            📅 {formatTime(slot.start_time)}
                          </div>
                        ))
                      ) : (
                        <div className="px-4 py-3 text-sm text-kalpana-100/50 italic">
                          No availability data received yet.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <label className="text-xs text-kalpana-300 uppercase tracking-wider font-semibold">
                    Propose Custom Time
                  </label>
                  <input 
                    type="datetime-local" 
                    value={customTime}
                    onChange={(e) => setCustomTime(e.target.value)}
                    className="w-full bg-kalpana-900 border border-kalpana-500/30 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-kalpana-500"
                  />
                </div>
              )}
              
              <button 
                onClick={() => setIsCustomTime(!isCustomTime)}
                className="text-xs text-kalpana-300 hover:text-white transition-colors underline decoration-kalpana-500/50 underline-offset-4"
              >
                {isCustomTime ? "Show available slots instead" : "None of these work? Propose a different time."}
              </button>
            </div>
          )}

          <div className="pt-2 flex flex-col gap-3">
            {connectionStatus !== 'connected' ? (
              <>
                <button
                  onClick={handleSchedule}
                  disabled={connectionStatus === 'connecting'}
                  className={`w-full py-3.5 rounded-full text-white font-medium transition-all duration-300 ${
                    connectionStatus === 'connecting' 
                      ? 'bg-kalpana-500/50 cursor-not-allowed' 
                      : 'bg-kalpana-500 hover:bg-[#E6007A] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)]'
                  }`}
                >
                  {connectionStatus === 'connecting' ? 'Saving...' : 'Schedule Connection'}
                </button>
                
                {(connectionStatus === 'idle' || connectionStatus === 'error') && (
                  <button
                    onClick={onClose}
                    className="w-full py-3.5 rounded-full bg-kalpana-900/50 text-kalpana-100 
                               border border-kalpana-300/20 hover:bg-kalpana-800 
                               transition-all duration-300"
                  >
                    Maybe Later
                  </button>
                )}
              </>
            ) : (
              <button
                onClick={onClose}
                className="w-full py-3.5 rounded-full bg-kalpana-500 text-white font-medium 
                           hover:bg-[#E6007A] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)] 
                           transition-all duration-300"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PeerMatchModal;
