import React from 'react';
import styled, { keyframes } from 'styled-components';

const bounce = keyframes`
  0%, 80%, 100% { 
    transform: scale(0);
  }
  40% { 
    transform: scale(1.0);
  }
`;

const DotsContainer = styled.div`
  display: flex;
  align-items: center;
  margin-left: 8px;
`;

const Dot = styled.div`
  width: 4px;
  height: 4px;
  margin: 0 2px;
  background-color: #4CAF50;
  border-radius: 50%;
  animation: ${bounce} 1.4s infinite ease-in-out both;

  &:nth-child(1) {
    animation-delay: -0.32s;
  }

  &:nth-child(2) {
    animation-delay: -0.16s;
  }
`;

const DotsAnimation: React.FC = () => {
  return (
    <DotsContainer>
      <Dot />
      <Dot />
      <Dot />
    </DotsContainer>
  );
};

export default DotsAnimation; 