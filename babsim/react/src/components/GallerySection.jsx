import React, { useState, useEffect } from 'react';

// 이미지들을 import로 가져오기
import concept1 from '../assets/concept1.jpg';
import concept2 from '../assets/concept2.jpg';
import concept3 from '../assets/concept3.jpg';
import concept4 from '../assets/concept4.jpg';
import concept5 from '../assets/concept5.jpg';
import concept6 from '../assets/concept6.jpg';
import concept7 from '../assets/concept7.jpg';
import concept8 from '../assets/concept8.jpg';
import concept9 from '../assets/concept9.jpg';
import concept10 from '../assets/concept10.jpg';
import concept11 from '../assets/concept11.jpg';

function GallerySection() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const images = [
    concept1, concept2, concept3, concept4, concept5,
    concept6, concept7, concept8, concept9, concept10, concept11
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
    }, 3000); // 3초마다 이미지 변경

    return () => clearInterval(interval);
  }, [images.length]);

  return (
    <section id="gallery" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h3 className="text-gray-500 text-sm font-semibold mb-4 tracking-wide uppercase">
            AI-Generated Concepts
          </h3>
          <h2 className="text-4xl md:text-6xl font-bold text-black mb-8 leading-tight">
            Our Design Gallery
          </h2>
          <p className="text-gray-600 text-xl max-w-4xl mx-auto leading-relaxed">
        AI와 함께하는 새로운 자동차 디자인의 세계.<br/>
        단순한 발상에서 시작해, 현실감 넘치는 콘셉트로 완성되는 과정을 경험하세요.<br/>
        상상력이 곧 디자인이 되는 순간을 지금 만나보세요.
          </p>
        </div>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          <button className="px-6 py-3 bg-black text-white rounded-full text-sm font-medium hover:bg-gray-800 transition-all duration-300">
            All Concepts
          </button>
          <button className="px-6 py-3 bg-white text-black border border-gray-300 rounded-full text-sm font-medium hover:bg-gray-50 transition-all duration-300">
            Sedans
          </button>
          <button className="px-6 py-3 bg-white text-black border border-gray-300 rounded-full text-sm font-medium hover:bg-gray-50 transition-all duration-300">
            SUVs
          </button>
          <button className="px-6 py-3 bg-white text-black border border-gray-300 rounded-full text-sm font-medium hover:bg-gray-50 transition-all duration-300">
            Sports Cars
          </button>
          <button className="px-6 py-3 bg-white text-black border border-gray-300 rounded-full text-sm font-medium hover:bg-gray-50 transition-all duration-300">
            Electric
          </button>
        </div>

        {/* Image Gallery */}
        <div className="relative overflow-hidden">
          <div className="flex space-x-6 animate-scroll">
            {/* First set of images */}
            {images.map((image, index) => (
              <div key={`first-${index}`} className="flex-shrink-0">
                <div className="w-80 h-64 bg-gray-100 rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 relative">
                  <img 
                    src={image} 
                    alt={`Concept ${index + 1}`}
                    className="w-full h-full object-cover"
                    style={{
                      width: '320px',
                      height: '256px',
                      objectFit: 'cover'
                    }}
                    onLoad={() => console.log(`✅ Image ${index + 1} loaded successfully:`, image)}
                    onError={(e) => {
                      console.error(`❌ Image ${index + 1} failed to load:`, image);
                      console.error('Error details:', e);
                    }}
                  />
                </div>
              </div>
            ))}
            
            {/* Second set of images for continuous scroll */}
            {images.map((image, index) => (
              <div key={`second-${index}`} className="flex-shrink-0">
                <div className="w-80 h-64 bg-gray-100 rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 relative">
                  <img 
                    src={image} 
                    alt={`Concept ${index + 1}`}
                    className="w-full h-full object-cover"
                    style={{
                      width: '320px',
                      height: '256px',
                      objectFit: 'cover'
                    }}
                    onLoad={() => console.log(`✅ Second set Image ${index + 1} loaded successfully:`, image)}
                    onError={(e) => {
                      console.error(`❌ Second set Image ${index + 1} failed to load:`, image);
                      console.error('Error details:', e);
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

    

      <style jsx>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        
        .animate-scroll {
          animation: scroll 20s linear infinite;
          width: max-content;
        }
        
        .animate-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </section>
  );
}

export default GallerySection;
