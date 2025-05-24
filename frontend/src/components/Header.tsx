import React from 'react';
import { Brain } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-10 bg-white/80 backdrop-blur-md p-4 shadow-sm">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-blue-500" />
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-blue-600 bg-clip-text text-transparent">
            ActAI
          </span>
        </div>
        <nav className="hidden md:flex space-x-8">
          <a href="#features" className="text-gray-700 hover:text-blue-500 transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="text-gray-700 hover:text-blue-500 transition-colors">
            How It Works
          </a>
          <a href="/login" className="text-gray-700 hover:text-blue-500 transition-colors">
            Login
          </a>
        </nav>
        <a 
          href="/register" 
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-full shadow-md transition-all hover:shadow-lg"
        >
          Get Started
        </a>
      </div>
    </header>
  );
};

export default Header;