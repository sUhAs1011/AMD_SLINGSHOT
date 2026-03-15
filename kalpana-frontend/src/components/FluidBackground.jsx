import React from 'react';

const FluidBackground = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10 bg-gradient-to-br from-kalpana-900 to-[#12041A]">
      {/* Top Right Blob */}
      <div 
        className="absolute -top-[10%] -right-[10%] w-[50vw] h-[50vw] rounded-full 
                   bg-kalpana-500 opacity-20 blur-[100px] mix-blend-screen 
                   animate-[pulse_8s_ease-in-out_infinite]" 
      />
      
      {/* Bottom Left Blob */}
      <div 
        className="absolute -bottom-[20%] -left-[10%] w-[60vw] h-[60vw] rounded-full 
                   bg-kalpana-800 opacity-40 blur-[120px] mix-blend-screen 
                   animate-[pulse_10s_ease-in-out_infinite_reverse]" 
      />
      
      {/* Center Subtle Highlight */}
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 
                   w-[30vw] h-[30vw] rounded-full bg-kalpana-300 opacity-10 blur-[80px]" 
      />
    </div>
  );
};

export default FluidBackground;
