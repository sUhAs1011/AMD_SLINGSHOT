import React from 'react';
import CustomAudioPlayer from './CustomAudioPlayer';

const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`max-w-[75%] px-5 py-3 text-kalpana-100 shadow-lg ${
          isUser 
            // Solid bright magenta for user
            ? 'bg-kalpana-500 rounded-2xl rounded-tr-sm' 
            // Frosted translucent purple for Kalpana
            : 'bg-kalpana-800/80 backdrop-blur-md border border-kalpana-300/20 rounded-2xl rounded-tl-sm'
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>
        
        {/* Render Custom Audio Player if audioUrl is present */}
        {message.audioUrl && <CustomAudioPlayer audioUrl={message.audioUrl} />}
      </div>
    </div>
  );
};

export default MessageBubble;
