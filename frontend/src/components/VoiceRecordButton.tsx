import React, { useState, useRef, useEffect } from 'react';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import { Loader2 } from 'lucide-react';
import styled from 'styled-components';

const Button = styled.button<{ isRecording: boolean; isProcessing: boolean }>`
  background: ${props => {
    if (props.isProcessing) return '#4a5568';
    return props.isRecording ? '#ff4444' : '#4CAF50';
  }};
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 20px;

  &:hover {
    transform: ${props => props.isProcessing ? 'none' : 'scale(1.1)'};
    background: ${props => {
      if (props.isProcessing) return '#4a5568';
      return props.isRecording ? '#ff0000' : '#45a049';
    }};
  }

  &:active {
    transform: ${props => props.isProcessing ? 'none' : 'scale(0.95)'};
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
`;

interface VoiceRecordButtonProps {
  onRecordingComplete: (audioBlob: Blob) => void;
}

const VoiceRecordButton: React.FC<VoiceRecordButtonProps> = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleRecordingComplete = () => {
      setIsProcessing(false);
    };

    const button = buttonRef.current;
    if (button) {
      button.addEventListener('recording-complete', handleRecordingComplete);
    }

    return () => {
      if (button) {
        button.removeEventListener('recording-complete', handleRecordingComplete);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/mp3' });
        setIsProcessing(true);
        onRecordingComplete(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <Button 
      ref={buttonRef}
      className="voice-record-button"
      isRecording={isRecording} 
      isProcessing={isProcessing}
      onClick={handleClick}
      disabled={isProcessing}
      title={isProcessing ? "Обработка..." : isRecording ? "Остановить запись" : "Начать запись"}
    >
      {isProcessing ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : isRecording ? (
        <FaStop />
      ) : (
        <FaMicrophone />
      )}
    </Button>
  );
};

export default VoiceRecordButton; 