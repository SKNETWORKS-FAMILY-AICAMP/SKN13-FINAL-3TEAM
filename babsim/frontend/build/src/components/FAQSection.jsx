import React from 'react';

function FAQSection() {
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

  return (
    <section className="bg-dark-blue py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h3 className="text-green-400 text-lg font-semibold mb-4">
            FAQs
          </h3>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Frequently Asked Questions
          </h2>
          <p className="text-gray-400 text-lg max-w-3xl mx-auto">
            Follow design trends and continually update your skills by learning new tools and techniques.
          </p>
        </div>

        {/* FAQ Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {faqs.map((faq, index) => (
            <div key={index} className="border-b border-gray-700 pb-6">
              <h3 className="text-white font-semibold text-lg mb-3">
                {faq.question}
              </h3>
              <p className="text-gray-400">
                {faq.answer}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FAQSection; 