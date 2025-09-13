import React, { useState } from 'react';

function FAQSection() {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: 'What is cryptocurrency?',
      answer: 'Cryptocurrency is a digital or virtual form of currency that uses cryptography for security.'
    },
    {
      question: 'What is a blockchain?',
      answer: 'A blockchain is a distributed ledger technology that maintains a continuously growing list of records.'
    },
    {
      question: 'What is a cryptocurrency wallet?',
      answer: 'A cryptocurrency wallet is a digital wallet that allows you to store, send, and receive cryptocurrencies.'
    },
    {
      question: 'How do I start investing in cryptocurrency?',
      answer: 'To start investing in cryptocurrency, you need to choose a reliable exchange and create an account.'
    },
    {
      question: 'How do I keep my cryptocurrency secure?',
      answer: 'Keep your cryptocurrency secure by using hardware wallets and enabling two-factor authentication.'
    },
    {
      question: 'What are the most popular cryptocurrencies?',
      answer: 'Bitcoin, Ethereum, and Binance Coin are among the most popular cryptocurrencies.'
    }
  ];

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="py-24 bg-gradient-to-b from-gray-900 to-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <h3 className="text-green-400 text-lg font-semibold mb-4 tracking-wide uppercase">
            FAQs
          </h3>
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-8 leading-tight">
            Frequently Asked Questions
          </h2>
          <p className="text-gray-300 text-xl max-w-4xl mx-auto leading-relaxed">
            Follow design trends and continually update your skills by learning new tools and techniques.
          </p>
        </div>

        {/* FAQ Accordion */}
        <div className="max-w-4xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="group">
              <div 
                className="bg-gradient-to-r from-gray-800 to-gray-900 rounded-2xl border border-gray-700 hover:border-gray-500 transition-all duration-300 cursor-pointer"
                onClick={() => toggleFAQ(index)}
              >
                <div className="p-8">
                  <div className="flex items-center justify-between">
                    <h3 className="text-white font-bold text-xl group-hover:text-green-400 transition-colors duration-300">
                      {faq.question}
                    </h3>
                    <div className={`transform transition-transform duration-300 ${openIndex === index ? 'rotate-180' : ''}`}>
                      <svg className="w-6 h-6 text-gray-400 group-hover:text-green-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                  {openIndex === index && (
                    <div className="mt-6 pt-6 border-t border-gray-700">
                      <p className="text-gray-300 text-lg leading-relaxed">
                        {faq.answer}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FAQSection; 