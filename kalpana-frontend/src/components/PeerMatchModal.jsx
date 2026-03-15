import React, { useState } from 'react';

const PeerMatchModal = ({ peerMatch, onClose }) => {
  const [connectionStatus, setConnectionStatus] = useState('idle'); // 'idle' | 'connecting' | 'connected'

  if (!peerMatch) return null;

  const handleConnect = () => {
    setConnectionStatus('connecting');
    // Simulate connection delay then show success state
    setTimeout(() => {
      setConnectionStatus('connected');
    }, 2500);
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
      <div 
        className="relative w-full max-w-sm overflow-hidden bg-kalpana-800 border border-kalpana-500/50 rounded-3xl shadow-[0_0_50px_rgba(216,27,96,0.2)] animate-in slide-in-from-bottom-4 duration-500"
      >
        {/* Decorative Top Gradient */}
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
              {connectionStatus === 'connecting' ? 'Connecting...' : 
               connectionStatus === 'connected' ? 'Connection Successful!' : 'Peer Match Found'}
            </h3>
            <p className="text-sm text-kalpana-100/80 leading-relaxed">
              {connectionStatus === 'connecting' 
                ? (<span>Establishing secure connection to Peer ID: <strong className="font-bold text-white">{peerMatch.peer_id}</strong> ...</span>)
                : connectionStatus === 'connected'
                ? (<span>You have successfully connected with Peer ID: <strong className="font-bold text-white">{peerMatch.peer_id}</strong>! The live chatroom feature will open here in a future update.</span>)
                : 'We connected you with someone who has survived a very similar experience. Would you like to speak with them?'}
            </p>
          </div>

          <div className="pt-2 flex flex-col gap-3">
            {connectionStatus !== 'connected' ? (
              <>
                <button
                  onClick={handleConnect}
                  disabled={connectionStatus === 'connecting'}
                  className={`w-full py-3.5 rounded-full text-white font-medium transition-all duration-300 ${
                    connectionStatus === 'connecting' 
                      ? 'bg-kalpana-500/50 cursor-not-allowed' 
                      : 'bg-kalpana-500 hover:bg-[#E6007A] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)]'
                  }`}
                >
                  {connectionStatus === 'connecting' ? 'Connecting...' : 'Connect Now'}
                </button>
                
                {connectionStatus === 'idle' && (
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
