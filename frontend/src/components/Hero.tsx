import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import TypedText from './TypedText';
import { Brain, Target, Calendar, Trophy, ArrowRight } from 'lucide-react';

const Hero: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleStartJourney = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  };

  const goalExamples = [
    "I want to learn Python in 8 weeks",
    "I want to prepare for job interviews in 4 weeks",
    "I want to learn guitar in 5 months",
    "I want to lose 10kg in 3 months",
    "I want to develop a meditation habit in 30 days",
    "I want to write a novel in 6 months"
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-white to-blue-50 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-500 to-blue-700 bg-clip-text text-transparent">
            Your AI Coach That Makes You Act
          </h1>
          
          <div className="text-xl md:text-2xl lg:text-3xl text-gray-700 mb-8">
            <span className="font-medium">ActAI helps you achieve: </span>
            <TypedText texts={goalExamples} typingSpeed={80} deletingSpeed={30} />
          </div>
          
          <p className="text-lg text-gray-600 mb-10 max-w-2xl mx-auto">
            Create personalized plans, get daily tasks, track your progress, and receive motivation 
            when you need it most. Your AI coach, strategist, and therapist in one.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <button
                onClick={handleStartJourney}
                className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
              >
                Go to Dashboard
              </button>
            ) : (
              <>
                <Link
                  to="/register"
                  className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
                >
                  Start Your Journey
                </Link>
                <a href="#learn-more" className="bg-white hover:bg-gray-50 text-blue-500 border border-blue-200 px-8 py-3 rounded-full text-lg font-medium shadow-md hover:shadow-lg transition-all">
                  Learn More
                </a>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Learn More Section */}
      <div id="learn-more" className="py-24 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 text-gray-800">
            Your Personal AI Coach Journey
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mb-6">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Set Your Goals</h3>
              <p className="text-gray-600">
                Tell ActAI what you want to achieve, and it will create a personalized roadmap tailored to your needs and schedule.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mb-6">
                <Calendar className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Daily Guidance</h3>
              <p className="text-gray-600">
                Get actionable daily tasks and reminders that keep you on track. No more guessing what to do next.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all">
              <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mb-6">
                <Trophy className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Track Progress</h3>
              <p className="text-gray-600">
                Monitor your achievements and stay motivated with visual progress tracking and AI-powered insights.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div id="how-it-works" className="py-24 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16 text-gray-800">
            How ActAI Works
          </h2>
          
          <div className="space-y-12">
            {[
              {
                step: "1",
                title: "Share Your Goal",
                description: "Tell ActAI what you want to achieve and when. Be as specific as you can."
              },
              {
                step: "2",
                title: "Get Your Personalized Plan",
                description: "ActAI analyzes your goal and creates a detailed, step-by-step plan tailored to your needs."
              },
              {
                step: "3",
                title: "Take Daily Action",
                description: "Follow your daily tasks and track your progress. ActAI adjusts your plan based on your performance."
              },
              {
                step: "4",
                title: "Achieve Your Goals",
                description: "Stay motivated with AI-powered support and watch as you make consistent progress towards your goals."
              }
            ].map((item, index) => (
              <div key={index} className="flex items-start gap-8">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-16 text-center">
            {isAuthenticated ? (
              <button
                onClick={handleStartJourney}
                className="inline-flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all"
              >
                Go to Dashboard
                <ArrowRight className="h-5 w-5" />
              </button>
            ) : (
              <Link 
                to="/register" 
                className="inline-flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all"
              >
                Start Your Journey
                <ArrowRight className="h-5 w-5" />
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;