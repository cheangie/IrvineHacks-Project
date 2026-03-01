import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Search, GitCompare } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [address, setAddress] = useState('');
  const [showCompare, setShowCompare] = useState(false);
  const [secondAddress, setSecondAddress] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) return;
    if (showCompare && secondAddress.trim()) {
      navigate(`/compare/${encodeURIComponent(address)}/${encodeURIComponent(secondAddress)}`);
    } else {
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
          <h1 className="text-gray-900 text-5xl font-bold text-center mb-4">
            Know your property's climate risk before you buy.
          </h1>

          <form onSubmit={handleSearch} className="mt-12">
            {/* Address inputs */}
            <div className="flex flex-col gap-3">
              {/* First address */}
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. 123 Main St, Irvine, CA, 92617"
                className="w-full px-6 py-4 text-lg rounded-xl bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0d9488]"
              />

              {/* Divider + compare toggle */}
              {!showCompare ? (
                <button
                  type="button"
                  onClick={() => setShowCompare(true)}
                  className="text-[#0d9488] hover:text-[#0f766e] text-sm font-medium text-left transition-colors"
                >
                  + Compare a second property
                </button>
              ) : (
                <>
                  {/* Divider line */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1 border-t border-dashed border-gray-400" />
                    <span className="text-gray-500 text-sm font-medium">vs</span>
                    <div className="flex-1 border-t border-dashed border-gray-400" />
                  </div>

                  {/* Second address */}
                  <input
                    type="text"
                    value={secondAddress}
                    onChange={(e) => setSecondAddress(e.target.value)}
                    placeholder="e.g. 456 Oak Ave, Austin, TX, 78701"
                    className="w-full px-6 py-4 text-lg rounded-xl bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0d9488]"
                  />

                  <button
                    type="button"
                    onClick={() => { setShowCompare(false); setSecondAddress(''); }}
                    className="text-gray-400 hover:text-gray-600 text-sm text-left transition-colors"
                  >
                    − Remove comparison
                  </button>
                </>
              )}
            </div>

            {/* Format hint */}
            <p className="text-sm text-gray-500 mt-3">
              Format: <span className="font-medium text-gray-700">Street Address, City, State, Zip</span>
            </p>

            {/* Submit button */}
            <button
              type="submit"
              className="w-100 mx-auto mt-4 px-8 py-4 bg-[#0d9488] hover:bg-[#0f766e] text-white font-semibold rounded-xl flex items-center justify-center gap-2 transition-colors text-lg"
            >
              {showCompare && secondAddress.trim() ? (
                <>
                  <GitCompare className="w-5 h-5" />
                  Compare Properties
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Analyze Property
                </>
              )}
            </button>
          </form>

          {/* Risk Type Preview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16">
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🌊</div>
              <h3 className="text-gray-900 font-semibold text-lg">Flood</h3>
              <p className="text-gray-600 text-sm mt-2">FEMA flood zones and historical flood data</p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🔥</div>
              <h3 className="text-gray-900 font-semibold text-lg">Wildfire</h3>
              <p className="text-gray-600 text-sm mt-2">Fire hazard severity and proximity analysis</p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[#0d9488] transition-colors shadow-sm">
              <div className="text-4xl mb-3">🏔️</div>
              <h3 className="text-gray-900 font-semibold text-lg">Landslide</h3>
              <p className="text-gray-600 text-sm mt-2">Terrain stability and geological risk factors</p>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full px-6 py-8 text-center text-gray-600 text-sm">
        Climate risk data powered by FEMA, USGS, and NOAA
      </div>
    </div>
  );
}