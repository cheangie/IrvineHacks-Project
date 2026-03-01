import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Search } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [address, setAddress] = useState('');
  const [showSecondProperty, setShowSecondProperty] = useState(false);
  const [secondAddress, setSecondAddress] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      navigate(`/report/${encodeURIComponent(address)}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#d1f4dd] flex flex-col">
      {/* Header */}
      <div className="w-full px-6 py-8">
        <div className="text-gray-900 text-3xl font-bold flex items-center gap-2">
          🌎 ClimateCheck
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 -mt-20">
        <div className="w-full max-w-3xl">
          {/* Subtitle */}
          <h1 className="text-gray-900 text-5xl font-bold text-center mb-4">
            Know your property's climate risk before you buy.
          </h1>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="mt-12">
            <div className="flex gap-3">
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. 123 Main St, Irvine, CA, 92617"
                className="flex-1 px-6 py-4 text-lg rounded-xl bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0d9488]"
              />
              <button
                type="submit"
                className="px-8 py-4 bg-[#0d9488] hover:bg-[#0f766e] text-white font-semibold rounded-xl flex items-center gap-2 transition-colors"
              >
                <Search className="w-5 h-5" />
                Analyze Property
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Format: <span className="font-medium text-gray-700">Street Address, City, State, Zip</span>
            </p>
          </form>

          {/* Compare Second Property */}
          {!showSecondProperty ? (
            <button
              onClick={() => setShowSecondProperty(true)}
              className="mt-4 text-[#0d9488] hover:text-[#0f766e] text-sm font-medium transition-colors"
            >
              + Compare a second property
            </button>
          ) : (
            <div className="mt-4">
              <input
                type="text"
                value={secondAddress}
                onChange={(e) => setSecondAddress(e.target.value)}
                placeholder="Enter second property address"
                className="w-full px-6 py-3 rounded-xl bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0d9488]"
              />
            </div>
          )}

          {/* Risk Type Preview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16">
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🌊</div>
              <h3 className="text-gray-900 font-semibold text-lg">Flood</h3>
              <p className="text-gray-600 text-sm mt-2">
                FEMA flood zones and historical flood data
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🔥</div>
              <h3 className="text-gray-900 font-semibold text-lg">Wildfire</h3>
              <p className="text-gray-600 text-sm mt-2">
                Fire hazard severity and proximity analysis
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🏔️</div>
              <h3 className="text-gray-900 font-semibold text-lg">Landslide</h3>
              <p className="text-gray-600 text-sm mt-2">
                Terrain stability and geological risk factors
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="w-full px-6 py-8 text-center text-gray-600 text-sm">
        Climate risk data powered by FEMA, USGS, and NOAA
      </div>
    </div>
  );
}