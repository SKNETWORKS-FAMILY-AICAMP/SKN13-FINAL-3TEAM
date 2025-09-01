import React from 'react';
import ioniq5 from '../assets/ioniq5.png';

function HeroSection() {
  return (
    <section className="bg-dark-blue min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Main Content */}
        <div className="relative z-10">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            AI-powered Car Prototype Image in minutes
          </h1>
          <p className="text-gray-400 text-lg md:text-xl mb-8 max-w-3xl mx-auto">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
          </p>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <button className="bg-purple-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-purple-700 transition-colors">
              Get Started
            </button>
            <button className="bg-transparent text-white border-2 border-gray-400 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-dark-blue transition-colors">
              How it works
            </button>
          </div>
        </div>

        {/* Car Image */}
        <div className="relative">
          <div className="w-full max-w-5xl mx-auto">
            <div className="relative">
              <img 
                src={ioniq5} 
                alt="Hyundai IONIQ 5" 
                className="w-full h-auto max-h-96 object-contain mx-auto"
                style={{
                  filter: 'brightness(1.1) contrast(1.1)',
                  transform: 'perspective(1000px) rotateY(-5deg)'
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection; 