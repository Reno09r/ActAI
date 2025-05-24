import React, { useState, useEffect } from 'react';

interface TypedTextProps {
  texts: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  delayBetweenTexts?: number;
}

const TypedText: React.FC<TypedTextProps> = ({
  texts,
  typingSpeed = 100,
  deletingSpeed = 50,
  delayBetweenTexts = 2000,
}) => {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;

    if (isPaused) {
      timeout = setTimeout(() => setIsPaused(false), delayBetweenTexts);
      return () => clearTimeout(timeout);
    }

    if (isTyping) {
      if (displayedText.length < texts[currentTextIndex].length) {
        timeout = setTimeout(() => {
          setDisplayedText(texts[currentTextIndex].substring(0, displayedText.length + 1));
        }, typingSpeed);
      } else {
        setIsPaused(true);
        setIsTyping(false);
      }
    } else {
      if (displayedText.length > 0) {
        timeout = setTimeout(() => {
          setDisplayedText(displayedText.substring(0, displayedText.length - 1));
        }, deletingSpeed);
      } else {
        setCurrentTextIndex((currentTextIndex + 1) % texts.length);
        setIsTyping(true);
      }
    }

    return () => clearTimeout(timeout);
  }, [currentTextIndex, delayBetweenTexts, deletingSpeed, displayedText, isPaused, isTyping, texts, typingSpeed]);

  return (
    <div className="inline-block min-h-[32px]">
      <span>{displayedText}</span>
      <span className="animate-blink">|</span>
    </div>
  );
};

export default TypedText;