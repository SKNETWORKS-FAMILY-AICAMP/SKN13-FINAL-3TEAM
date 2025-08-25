import React from 'react';

function AboutSection() {
  const features = [
    {
      icon: '👤',
      color: 'green',
      title: 'User-Centered Design Support',
      description: 'Product designers can quickly analyze and understand the Voice of the Customer (VoC)'
    },
    {
      icon: '🛡️',
      color: 'orange',
      title: 'Preserve Hyundai\'s Brand Identity',
      description: 'sLLM trained on the company\'s unique design identity'
    },
    {
      icon: '📊',
      color: 'blue',
      title: 'Market-Driven Design Analysis',
      description: 'Incorporate automotive mechanisms, competitor/subsidiary products, and market trends'
    },
    {
      icon: '⚙️',
      color: 'purple',
      title: 'Personalized Prototype Generation',
      description: 'Generate images and designs based on various prompts'
    }
  ];

  return (
    <section id="about" className="bg-dark-gray py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div>
            <h3 className="text-green-400 text-lg font-semibold mb-4">
              About us
            </h3>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              JACKLETTE with Hyundai Car
            </h2>
            <div className="space-y-4 text-white">
              <p className="text-lg">
                Automotive design is no longer just about aesthetics — it's about understanding people, trends, and technology.
              </p>
              <p className="text-lg">
                JACKLETTE delivers AI-powered support that bridges human emotion with market and mechanical realities.
              </p>
            </div>
          </div>

          {/* Right Content - Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="bg-dark-blue rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
                <div className={`text-3xl mb-4`}>
                  {feature.icon}
                </div>
                <h3 className="text-white font-semibold text-lg mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-sm mb-4">
                  {feature.description}
                </p>
                <button className="text-purple-400 hover:text-purple-300 transition-colors text-sm font-semibold">
                  Learn More
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default AboutSection; 