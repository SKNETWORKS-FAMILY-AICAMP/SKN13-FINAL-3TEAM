import React from 'react';

function AboutSection() {
  const features = [
    {
      title: 'User-Centered Design Support',
      description: '고객의 목소리(VoC)를 빠르게 분석하고 이해할 수 있습니다.'
    },
    {
      title: 'Preserve Hyundai\'s Brand Identity',
      description: '현대자동차만의 고유한 디자인 아이덴티티를 반영합니다.'
    },
    {
      title: 'Market-Driven Design Analysis',
      description: '자동차 기술, 경쟁사 및 시장 트렌드를 분석합니다.'
    },
    {
      title: 'Personalized Prototype Generation',
      description: '다양한 프롬프트를 기반으로 맞춤형 이미지를 생성합니다.'
    }
  ];

  return (
    <section id="about" className="py-24 bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-20 w-4 h-4 bg-white rounded-full opacity-60 animate-pulse"></div>
        <div className="absolute top-40 right-32 w-6 h-6 bg-white rounded-full opacity-40 animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute bottom-32 left-40 w-3 h-3 bg-white rounded-full opacity-50 animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-32 right-20 w-8 h-8 border border-white rounded-full opacity-30"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Title and Motto */}
          <div className="space-y-8 mb-16">
            <div className="space-y-6">
              <h2 className="text-4xl md:text-5xl font-bold text-white leading-tight">
                About Us
              </h2>
              <p className="text-xl md:text-2xl text-gray-300 leading-relaxed">
                Automotive design is no longer just about aesthetics 
                <br/>— it's about understanding people, trends, and technology.
              </p>
              <p className="text-lg md:text-xl text-gray-400 leading-relaxed">
                JACKLETTE delivers AI-powered support that bridges 
                <br/>human emotion with market and mechanical realities.
              </p>
            </div>
          </div>

          {/* Feature Square Boxes */}
          <div className="flex flex-wrap justify-center gap-4">
            {features.map((feature, index) => (
              <div key={index} className="group">
                <div className="w-32 h-32 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 hover:border-white/20 transition-all duration-300 hover:bg-white/10 flex items-center justify-center p-4">
                  <h3 className="text-white font-bold text-xs group-hover:text-blue-400 transition-colors duration-300 text-center leading-tight">
                    {feature.title}
                  </h3>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default AboutSection; 