import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

const CustomAudioPlayer = ({ audioUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const audioRef = useRef(null);

  useEffect(() => {
    const audio = audioRef.current;
    
    // Set duration once metadata is loaded
    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    // Update current time as audio plays
    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    // Reset when audio finishes
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    if (audio) {
      audio.addEventListener('loadedmetadata', handleLoadedMetadata);
      audio.addEventListener('timeupdate', handleTimeUpdate);
      audio.addEventListener('ended', handleEnded);
    }

    return () => {
      if (audio) {
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('timeupdate', handleTimeUpdate);
        audio.removeEventListener('ended', handleEnded);
      }
    };
  }, [audioUrl]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    const seekTime = (e.target.value / 100) * duration;
    audio.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (timeInSeconds) => {
    if (isNaN(timeInSeconds)) return "0:00";
    const mins = Math.floor(timeInSeconds / 60);
    const secs = Math.floor(timeInSeconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex items-center gap-3 w-full max-w-[280px] bg-kalpana-900/40 border border-kalpana-300/20 rounded-full px-3 py-2 mt-3 shadow-inner">
      {/* Hidden Native Audio Element */}
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Play/Pause Button */}
      <button 
        onClick={togglePlayPause}
        className="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-full bg-kalpana-500 text-white hover:bg-[#E6007A] transition-colors focus:outline-none"
      >
        {isPlaying ? <Pause fill="currentColor" size={14} /> : <Play fill="currentColor" size={14} className="ml-0.5" />}
      </button>

      {/* Progress Bar & Timer */}
      <div className="flex-1 flex flex-col justify-center gap-1">
        <input 
          type="range" 
          min="0" 
          max="100" 
          value={duration ? (currentTime / duration) * 100 : 0} 
          onChange={handleSeek}
          className="w-full h-1.5 bg-kalpana-800 rounded-full appearance-none cursor-pointer 
                     [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 
                     [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-kalpana-300 
                     [&::-webkit-slider-thumb]:rounded-full hover:[&::-webkit-slider-thumb]:bg-kalpana-100"
        />
        <div className="flex justify-between text-[10px] text-kalpana-300/80 font-mono">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  );
};

export default CustomAudioPlayer;
