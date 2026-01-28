import { useEffect, useState } from 'react';

interface StreamingTextProps {
  text: string;
  speed?: number;  // ms per character
}

export function StreamingText({ text, speed = 10 }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    // 如果新文本比当前显示的长，继续打字效果
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, speed);
      return () => clearTimeout(timer);
    }
  }, [text, currentIndex, speed]);

  // 如果文本变短了（比如重新渲染），直接显示
  useEffect(() => {
    if (text.length < displayedText.length) {
      setDisplayedText(text);
      setCurrentIndex(text.length);
    }
  }, [text, displayedText.length]);

  return (
    <div className="text-[14px] text-white/90 leading-relaxed whitespace-pre-wrap">
      {displayedText}
      {currentIndex < text.length && (
        <span className="inline-block w-0.5 h-4 bg-violet-400 animate-pulse ml-0.5" />
      )}
    </div>
  );
}

