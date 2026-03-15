import React from 'react';

const CrisisModal = ({ isOpen, onAcknowledgeSafe }) => {
  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 z-[60] flex items-center justify-center p-4 bg-[#12041A]/95 backdrop-blur-sm">
      <div className="w-full max-w-md border border-red-300/50 bg-kalpana-900 rounded-2xl shadow-[0_0_40px_rgba(244,143,177,0.2)] overflow-hidden">
        <div className="h-2 w-full bg-gradient-to-r from-red-300 via-red-400 to-red-500" />

        <div className="p-7 space-y-5">
          <h2 className="text-2xl font-semibold text-white">You matter. Let&apos;s get immediate support.</h2>

          <p className="text-sm text-kalpana-100/90 leading-relaxed">
            If you might be feeling unsafe right now, speaking with a trained crisis counselor can help.
            You do not have to handle this alone.
          </p>

          <div className="space-y-3">
            <button
              type="button"
              className="w-full rounded-xl py-3 bg-red-500/80 text-white font-medium border border-red-300/40 cursor-not-allowed opacity-80"
              title="Demo button for now"
            >
              Call Crisis Support (Demo)
            </button>
            <button
              type="button"
              className="w-full rounded-xl py-3 bg-red-500/60 text-white font-medium border border-red-300/40 cursor-not-allowed opacity-80"
              title="Demo button for now"
            >
              Open Crisis Chat (Demo)
            </button>
            <button
              type="button"
              className="w-full rounded-xl py-3 bg-red-500/40 text-white font-medium border border-red-300/40 cursor-not-allowed opacity-80"
              title="Demo button for now"
            >
              Emergency Services (Demo)
            </button>
          </div>

          <p className="text-xs text-kalpana-300/90">
            Privacy note: your conversation remains private. This safety step is shown to support you.
          </p>

          <button
            type="button"
            onClick={onAcknowledgeSafe}
            className="w-full rounded-xl py-3 bg-kalpana-500 text-white font-medium hover:bg-[#E6007A] transition-colors"
          >
            I&apos;m safe for now - continue with Kalpana
          </button>
        </div>
      </div>
    </div>
  );
};

export default CrisisModal;
