import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';

const About = () => {
  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      <main className="py-20">
        <div className="container mx-auto px-4">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <h1 className="text-4xl font-bold text-white mb-6">
              About Us
            </h1>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              We are a team of passionate developers and designers dedicated to creating 
              innovative solutions for the automotive industry.
            </p>
          </div>
          
          {/* Mission Section */}
          <div className="bg-gray-800 rounded-lg p-8 mb-16">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold text-white mb-4">
                Our Mission
              </h3>
              <p className="text-lg text-gray-300 max-w-3xl mx-auto">
                To revolutionize automotive design through AI-powered innovation and create the future of mobility.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">Innovation</h4>
                <p className="text-gray-300">
                  Pushing the boundaries of what's possible in automotive design through cutting-edge AI technology.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">Security</h4>
                <p className="text-gray-300">
                  Ensuring the highest standards of data protection and system security for our users.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">Collaboration</h4>
                <p className="text-gray-300">
                  Working together with designers, engineers, and AI experts to create exceptional automotive experiences.
                </p>
              </div>
            </div>
          </div>
          
          {/* Team Section */}
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-white mb-8">
              Our Team
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="w-24 h-24 bg-gray-600 rounded-full mx-auto mb-4"></div>
                <h4 className="text-xl font-semibold text-white mb-2">John Doe</h4>
                <p className="text-gray-400">CEO & Founder</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="w-24 h-24 bg-gray-600 rounded-full mx-auto mb-4"></div>
                <h4 className="text-xl font-semibold text-white mb-2">Jane Smith</h4>
                <p className="text-gray-400">CTO</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="w-24 h-24 bg-gray-600 rounded-full mx-auto mb-4"></div>
                <h4 className="text-xl font-semibold text-white mb-2">Mike Johnson</h4>
                <p className="text-gray-400">Lead Designer</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="w-24 h-24 bg-gray-600 rounded-full mx-auto mb-4"></div>
                <h4 className="text-xl font-semibold text-white mb-2">Sarah Wilson</h4>
                <p className="text-gray-400">AI Engineer</p>
              </div>
            </div>
          </div>
          
          {/* Values Section */}
          <div className="bg-gray-800 rounded-lg p-8">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold text-white mb-4">
                Our Values
              </h3>
              <p className="text-lg text-gray-300 max-w-3xl mx-auto">
                The principles that guide our work and shape our culture.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h4 className="text-xl font-semibold text-white mb-3">Excellence</h4>
                <p className="text-gray-300">
                  We strive for excellence in everything we do, from the quality of our code to the user experience we deliver.
                </p>
              </div>
              
              <div>
                <h4 className="text-xl font-semibold text-white mb-3">Innovation</h4>
                <p className="text-gray-300">
                  We embrace new technologies and approaches to solve complex problems in creative ways.
                </p>
              </div>
              
              <div>
                <h4 className="text-xl font-semibold text-white mb-3">Collaboration</h4>
                <p className="text-gray-300">
                  We believe that the best solutions come from working together and sharing diverse perspectives.
                </p>
              </div>
              
              <div>
                <h4 className="text-xl font-semibold text-white mb-3">Integrity</h4>
                <p className="text-gray-300">
                  We operate with honesty, transparency, and ethical practices in all our business relationships.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default About;
