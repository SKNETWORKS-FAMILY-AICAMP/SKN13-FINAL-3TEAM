import React from 'react';

function Footer() {
  const footerLinks = [
    {
      title: 'Quick Link',
      links: ['About Us', 'Feature', 'Career', 'Contact Us']
    },
    {
      title: 'Help',
      links: ['Customer Support', 'Terms', 'Privacy', 'FAQs']
    },
    {
      title: 'Others',
      links: ['Start Trading', 'Earn Free Crypto', 'Crypto Wallete', 'Payment Option']
    }
  ];

  return (
    <footer className="bg-dark-blue border-t border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Logo and Description */}
          <div className="lg:col-span-2">
            <h3 className="text-white font-bold text-xl mb-4">
              JACKLETTE with Hyundai Car
            </h3>
            <p className="text-gray-400 mb-6">
              AI-powered automotive design support platform
            </p>
          </div>

          {/* Footer Links */}
          {footerLinks.map((section, index) => (
            <div key={index}>
              <h4 className="text-white font-semibold mb-4">{section.title}</h4>
              <ul className="space-y-2">
                {section.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <a href="#" className="text-gray-400 hover:text-white transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Download App */}
          <div>
            <h4 className="text-white font-semibold mb-4">Download App</h4>
            <div className="space-y-3">
              <button className="w-full bg-black text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 hover:bg-gray-800 transition-colors">
                <span>📱</span>
                <span className="text-sm">Get It On Google Play</span>
              </button>
              <button className="w-full bg-black text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 hover:bg-gray-800 transition-colors">
                <span>🍎</span>
                <span className="text-sm">Download On The App Store</span>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">
            © Copyright 2024, all right reserved by cryptodive
          </p>
          <div className="flex space-x-4 mt-4 md:mt-0">
            <button className="text-gray-400 hover:text-white transition-colors">
              <span className="text-lg">a</span>
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <span className="text-lg">⊞</span>
            </button>
            <button className="text-gray-400 hover:text-white transition-colors">
              <span className="text-lg">×</span>
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer; 