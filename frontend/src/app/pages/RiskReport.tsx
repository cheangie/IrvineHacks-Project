import { useParams, useNavigate } from 'react-router';
import { MapPin, ArrowLeft, AlertTriangle, Sparkles, CheckCircle, Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useState, useEffect } from 'react';

const API = 'http://localhost:8000';

interface RiskData {
  address: string;
  county: string;
  neighborhood: string;
  lat: number;
  lng: number;
  flood_zone: string;
  wildfire_hazard: string;
  elevation_m: number;
  landslide_nearby: number;
  fire_distance_km: number;
  active_alerts: string[];
  flood: number;
  fire: number;
  landslide: number;
  overall: number;
  explanation: string;
  recommendations: string[];
  wildfire_probability: { '1_year': number; '5_year': number; '10_year': number; '30_year': number };
  flood_probability: { '1_year': number; '5_year': number; '10_year': number; '30_year': number };
  landslide_probability: { '1_year': number; '5_year': number; '10_year': number; '30_year': number };
}

export default function RiskReport() {
  const { address } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        setLoading(true);
        const decoded = decodeURIComponent(address || '');
        const res = await fetch(`${API}/risk?address=${encodeURIComponent(decoded)}`);
        if (!res.ok) throw new Error('Failed to fetch risk data');
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError('Could not load risk data. Make sure the backend is running.');
      } finally {
        setLoading(false);
      }
    };
    fetchRisk();
  }, [address]);

  const getRiskLevel = (score: number) => {
    if (score < 40) return { level: 'Low', color: 'bg-green-500' };
    if (score < 70) return { level: 'Moderate', color: 'bg-yellow-500' };
    return { level: 'High', color: 'bg-red-500' };
  };

  const getScoreColor = (score: number) => {
    if (score < 40) return 'text-green-500';
    if (score < 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getProgressColor = (score: number) => {
    if (score < 40) return 'bg-green-500';
    if (score < 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Loading state
  if (loading) return (
    <div className="min-h-screen bg-[#d1f4dd] flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-[#0d9488] mx-auto mb-4" />
        <p className="text-gray-700 text-lg font-medium">Analyzing property climate risk...</p>
        <p className="text-gray-500 text-sm mt-2">Querying FEMA, USGS, NOAA and more</p>
      </div>
    </div>
  );

  // Error state
  if (error || !data) return (
    <div className="min-h-screen bg-[#d1f4dd] flex items-center justify-center">
      <div className="text-center bg-white p-8 rounded-xl shadow-sm">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-900 font-semibold text-lg">{error}</p>
        <button onClick={() => navigate('/')} className="mt-4 px-6 py-2 bg-[#0d9488] text-white rounded-lg">
          Go Back
        </button>
      </div>
    </div>
  );

  const overallRisk = getRiskLevel(data.overall);

  // Chart data from real API probabilities
  const chartData = [
    { period: '1 Year',  flood: data.flood_probability['1_year'],  wildfire: data.wildfire_probability['1_year'],  landslide: data.landslide_probability['1_year'] },
    { period: '5 Years', flood: data.flood_probability['5_year'],  wildfire: data.wildfire_probability['5_year'],  landslide: data.landslide_probability['5_year'] },
    { period: '10 Years',flood: data.flood_probability['10_year'], wildfire: data.wildfire_probability['10_year'], landslide: data.landslide_probability['10_year'] },
    { period: '30 Years',flood: data.flood_probability['30_year'], wildfire: data.wildfire_probability['30_year'], landslide: data.landslide_probability['30_year'] },
  ];

  return (
    <div className="min-h-screen bg-[#d1f4dd]">
      {/* Navigation */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-900 hover:text-[#0d9488] transition-colors">
          <ArrowLeft className="w-5 h-5" />
          <span className="font-semibold">🌎 ClimateCheck</span>
        </button>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Property Header */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-gray-400 mt-1" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{data.address}</h1>
              <p className="text-gray-600 mt-1">
                {data.neighborhood} • {data.county} County • {data.lat.toFixed(4)}, {data.lng.toFixed(4)}
              </p>
            </div>
          </div>
        </div>

        {/* Active Alerts Banner */}
        {data.active_alerts.length > 0 && (
          <div className="bg-red-500 text-white rounded-xl p-4 mb-6 shadow-sm">
            {data.active_alerts.map((alert, i) => (
              <div key={i} className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div><strong>⚠️ Active Alert:</strong> {alert}</div>
              </div>
            ))}
          </div>
        )}

        {/* Overall Risk Score Card */}
        <div className="bg-white rounded-xl p-8 shadow-sm mb-6">
          <div className="flex flex-col items-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Overall Climate Risk</h2>
            <div className="relative w-48 h-48 mb-4">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="96" cy="96" r="80" fill="none" stroke="#e5e7eb" strokeWidth="16" />
                <circle
                  cx="96" cy="96" r="80" fill="none"
                  stroke={data.overall < 40 ? '#10b981' : data.overall < 70 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="16"
                  strokeDasharray={`${(data.overall / 100) * 502.65} 502.65`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className={`text-5xl font-bold ${getScoreColor(data.overall)}`}>{data.overall}</div>
                  <div className="text-gray-500 text-sm">out of 100</div>
                </div>
              </div>
            </div>
            <div className={`${overallRisk.color} text-white px-4 py-2 rounded-full font-semibold`}>
              {overallRisk.level} Risk
            </div>
          </div>
        </div>

        {/* Three Risk Score Bar Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Flood */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🌊</span>
              <h3 className="text-lg font-semibold text-gray-900">Flood Risk</h3>
            </div>
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-600">Risk Score</div>
              <div className={`text-2xl font-bold ${getScoreColor(data.flood)}`}>{data.flood}</div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className={`${getProgressColor(data.flood)} h-3 rounded-full`} style={{ width: `${data.flood}%` }} />
            </div>
            <div className="mt-3 text-sm text-gray-500 space-y-1">
              <p>FEMA Zone: <span className="font-medium text-gray-700">{data.flood_zone}</span></p>
              <p>Elevation: <span className="font-medium text-gray-700">{data.elevation_m.toFixed(1)}m</span></p>
            </div>
          </div>

          {/* Wildfire */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🔥</span>
              <h3 className="text-lg font-semibold text-gray-900">Wildfire Risk</h3>
            </div>
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-600">Risk Score</div>
              <div className={`text-2xl font-bold ${getScoreColor(data.fire)}`}>{data.fire}</div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className={`${getProgressColor(data.fire)} h-3 rounded-full`} style={{ width: `${data.fire}%` }} />
            </div>
            <div className="mt-3 text-sm text-gray-500 space-y-1">
              <p>USFS Hazard: <span className="font-medium text-gray-700">{data.wildfire_hazard}</span></p>
              <p>Nearest fire: <span className="font-medium text-gray-700">{data.fire_distance_km}km away</span></p>
            </div>
          </div>

          {/* Landslide */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🏔️</span>
              <h3 className="text-lg font-semibold text-gray-900">Landslide Risk</h3>
            </div>
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-600">Risk Score</div>
              <div className={`text-2xl font-bold ${getScoreColor(data.landslide)}`}>{data.landslide}</div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className={`${getProgressColor(data.landslide)} h-3 rounded-full`} style={{ width: `${data.landslide}%` }} />
            </div>
            <div className="mt-3 text-sm text-gray-500 space-y-1">
              <p>Historical incidents: <span className="font-medium text-gray-700">{data.landslide_nearby} nearby</span></p>
              <p>Elevation: <span className="font-medium text-gray-700">{data.elevation_m.toFixed(1)}m</span></p>
            </div>
          </div>
        </div>

        {/* Probability Over Time Graph */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Risk Probability Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="period" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value: number) => `${value}%`}
              />
              <Legend />
              <Line type="monotone" dataKey="flood" stroke="#3b82f6" strokeWidth={2} name="Flood" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="wildfire" stroke="#ef4444" strokeWidth={2} name="Wildfire" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="landslide" stroke="#f97316" strokeWidth={2} name="Landslide" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* AI Analysis + Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* AI Analysis */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-[#0d9488]" />
              <h2 className="text-xl font-semibold text-gray-900">AI Climate Analysis</h2>
            </div>
            <p className="text-gray-600 leading-relaxed">{data.explanation}</p>
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">What You Should Do</h2>
            <div className="space-y-3">
              {data.recommendations.map((rec, i) => (
                <div key={i} className={`flex gap-3 items-start border-l-4 pl-4 py-2 ${i === 0 ? 'border-red-500' : i === 1 ? 'border-yellow-500' : 'border-green-500'}`}>
                  <CheckCircle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${i === 0 ? 'text-red-500' : i === 1 ? 'text-yellow-500' : 'text-green-500'}`} />
                  <p className="text-gray-700 text-sm">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Property Details */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Property Details</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Flood Zone', value: data.flood_zone },
              { label: 'Wildfire Hazard', value: data.wildfire_hazard },
              { label: 'Elevation', value: `${data.elevation_m.toFixed(1)}m` },
              { label: 'Fire Distance', value: `${data.fire_distance_km}km` },
              { label: 'Landslide Incidents', value: `${data.landslide_nearby} nearby` },
              { label: 'County', value: data.county },
              { label: 'Neighborhood', value: data.neighborhood },
              { label: 'Coordinates', value: `${data.lat.toFixed(3)}, ${data.lng.toFixed(3)}` },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-sm text-gray-500">{label}</div>
                <div className="font-semibold text-gray-900">{value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Sources: FEMA, USFS, USGS, NOAA, NIFC — Powered by Gemini AI</p>
        </div>
      </div>
    </div>
  );
}