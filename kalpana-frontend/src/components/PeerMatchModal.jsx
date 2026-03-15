import React from 'react';

const PeerMatchModal = ({ peerMatch, onClose }) => {
  if (!peerMatch) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300">
      <div 
        className="relative w-full max-w-sm overflow-hidden bg-kalpana-800 border border-kalpana-500/50 rounded-3xl shadow-[0_0_50px_rgba(216,27,96,0.2)] animate-in slide-in-from-bottom-4 duration-500"
      >
        {/* Decorative Top Gradient */}
        <div className="h-2 w-full bg-gradient-to-r from-kalpana-300 via-kalpana-500 to-kalpana-800" />
        
        <div className="p-8 text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-full bg-kalpana-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(216,27,96,0.4)]">
            <span className="text-3xl">🤝</span>
          </div>

          <div className="space-y-2">
            <h3 className="text-2xl font-semibold text-white">Peer Match Found</h3>
            <p className="text-sm text-kalpana-100/80 leading-relaxed">
              We connected you with someone who has survived a very similar experience. 
              Would you like to speak with them?
            </p>
          </div>

          <div className="pt-2 flex flex-col gap-3">
            <button
              onClick={() => {
                alert(`Connecting to Peer ID: ${peerMatch}`);
                onClose();
              }}
              className="w-full py-3.5 rounded-full bg-kalpana-500 text-white font-medium 
                         hover:bg-[#E6007A] hover:shadow-[0_0_20px_rgba(216,27,96,0.6)] 
                         transition-all duration-300"
            >
              Connect Now
            </button>
            <button
              onClick={onClose}
              className="w-full py-3.5 rounded-full bg-kalpana-900/50 text-kalpana-100 
                         border border-kalpana-300/20 hover:bg-kalpana-800 
                         transition-all duration-300"
            >
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PeerMatchModal;
