import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';
import { Phone, Calendar, MessageSquare, Brain, ArrowRight } from 'lucide-react';
import { Button } from './common/ui';

const LandingPage = () => {
  const navigate = useNavigate();
  const { user, login } = useAuth();

  const googleLogin = useGoogleLogin({
    onSuccess: login,
    flow: 'auth-code',
    scope: [
      'https://www.googleapis.com/auth/userinfo.profile',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/calendar.events',
      'https://www.googleapis.com/auth/calendar.readonly'
    ].join(' '),
    access_type: 'offline',
    prompt: 'consent'
  });

  const features = [
    {
      icon: <Phone className="w-12 h-12 text-blue-500" />,
      title: "Real-time Call Screening",
      description: "Advanced call screening powered by OpenAI's Realtime API for intelligent conversation handling"
    },
    {
      icon: <Calendar className="w-12 h-12 text-green-500" />,
      title: "Calendar Integration",
      description: "Seamless Google Calendar integration for smart schedule management and availability tracking"
    },
    {
      icon: <MessageSquare className="w-12 h-12 text-purple-500" />,
      title: "SMS Integration",
      description: "Automated SMS capabilities for scheduling and follow-up communications"
    },
    {
      icon: <Brain className="w-12 h-12 text-red-500" />,
      title: "AI-Powered Decisions",
      description: "Intelligent decision-making for call handling based on context and importance"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 via-white to-blue-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 sm:pb-16 md:pb-20 lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8">
              <div className="text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                  <span className="block">Your AI Secretary</span>
                </h1>
                <p className="mt-3 text-lg text-gray-500 sm:mt-5 sm:max-w-xl sm:mx-auto lg:mx-0">
                  An intelligent call screening system that manages your calls, schedules, and communications.
                </p>
                <div className="mt-5 sm:mt-8 flex justify-center lg:justify-start">
                  {user ? (
                    <Button
                      size="lg"
                      onClick={() => navigate('/profile')}
                      className="w-full sm:w-auto"
                    >
                      Go to Dashboard
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  ) : (
                    <Button
                      size="lg"
                      onClick={() => googleLogin()}
                      className="w-full sm:w-auto"
                    >
                      Sign in with Google
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  )}
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
              Everything you need to manage your calls and schedule efficiently
            </p>
          </div>

          <div className="mt-20">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => (
                <div 
                  key={index} 
                  className="relative group"
                >
                  <div className="flex flex-col items-center p-6 bg-white rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2">
                    <div className="flex items-center justify-center w-16 h-16 mb-4">
                      {feature.icon}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-500 text-center">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">Ready to get started?</span>
            <span className="block text-blue-200">Get your AI secretary today.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:ml-8">
            {user ? (
              <Button
                variant="secondary"
                size="lg"
                onClick={() => navigate('/profile')}
                className="w-full sm:w-auto"
              >
                Go to Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            ) : (
              <Button
                variant="secondary"
                size="lg"
                onClick={() => googleLogin()}
                className="w-full sm:w-auto text-white border-white hover:bg-blue-700"
              >
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Testimonials Section */}
      <div className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
              Loved by Professionals
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
              See what others are saying about their AI secretary
            </p>
          </div>
          
          <div className="mt-20 grid grid-cols-1 gap-8 md:grid-cols-3">
            {[
              {
                quote: "Finally, an AI assistant that truly understands context and handles calls intelligently.",
                author: "Sarah Johnson",
                role: "Senior Executive"
              },
              {
                quote: "The calendar integration is seamless. It's like having a real secretary managing my schedule.",
                author: "Michael Chen",
                role: "Business Owner"
              },
              {
                quote: "The personality makes it fun to interact with. It's professional yet has character.",
                author: "Amanda Peters",
                role: "Legal Professional"
              }
            ].map((testimonial, index) => (
              <div key={index} className="bg-white p-8 rounded-xl shadow-lg">
                <p className="text-gray-600 italic mb-4">{testimonial.quote}</p>
                <div>
                  <p className="font-semibold text-gray-900">{testimonial.author}</p>
                  <p className="text-gray-500 text-sm">{testimonial.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;