import { useParams, useNavigate } from 'react-router';
import { MapPin, ArrowLeft, AlertTriangle, Sparkles, CheckCircle, Loader2 } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';
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

const getRiskLevel = (score: number) => {
  if (score < 40) return { level: 'Low', color: 'text-green-500', bg: 'bg-green-500' };
  if (score < 70) return { level: 'Moderate', color: 'text-yellow-500', bg: 'bg-yellow-500' };
  return { level: 'High', color: 'text-red-500', bg: 'bg-red-500' };
};

const getProgressColor = (score: number) => {
  if (score < 40) return 'bg-green-500';
  if (score < 70) return 'bg-yellow-500';
  return 'bg-red-500';
};

function PropertyCard({ data, label }: { data: RiskData; label: string }) {
  const overall = getRiskLevel(data.overall);
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className={`p-4 ${label === 'Property A' ? 'bg-blue-50 border-b-2 border-blue-400' : 'bg-orange-50 border-b-2 border-orange-400'}`}>
        <div className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">{label}</div>
        <div className="flex items-start gap-2">
          <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-bold text-gray-900 text-sm">{data.address}</div>
            <div className="text-gray-500 text-xs">{data.neighborhood} • {data.county}</div>
          </div>
        </div>
      </div>

      {/* Overall Score */}
      <div className="p-6 text-center border-b border-gray-100">
        <div className={`text-5xl font-bold ${overall.color}`}>{data.overall}</div>
        <div className="text-gray-500 text-sm mt-1">out of 100</div>
        <div className={`${overall.bg} text-white px-3 py-1 rounded-full text-sm font-semibold inline-block mt-2`}>
          {overall.level} Risk
        </div>
      </div>

      {/* Active Alerts */}
      {data.active_alerts.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 px-4 py-3 mx-4 mt-4 rounded">
          <div className="flex gap-2 items-start">
            <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
            <p className="text-red-700 text-xs">{data.active_alerts[0]}</p>
          </div>
        </div>
      )}

      {/* Risk Scores */}
      <div className="p-4 space-y-3">
        {[
          { emoji: '🌊', label: 'Flood', score: data.flood, detail: `FEMA Zone: ${data.flood_zone}` },
          { emoji: '🔥', label: 'Wildfire', score: data.fire, detail: `USFS: ${data.wildfire_hazard}` },
          { emoji: '🏔️', label: 'Landslide', score: data.landslide, detail: `${data.landslide_nearby} incidents nearby` },
        ].map(({ emoji, label, score, detail }) => (
          <div key={label}>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">{emoji} {label}</span>
              <span className={`text-sm font-bold ${getRiskLevel(score).color}`}>{score}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className={`${getProgressColor(score)} h-2 rounded-full`} style={{ width: `${score}%` }} />
            </div>
            <div className="text-xs text-gray-400 mt-0.5">{detail}</div>
          </div>
        ))}
      </div>

      {/* AI Explanation */}
      <div className="px-4 pb-4 border-t border-gray-100 pt-4">
        <div className="flex items-center gap-1 mb-2">
          <Sparkles className="w-4 h-4 text-[#0d9488]" />
          <span className="text-sm font-semibold text-gray-900">AI Analysis</span>
        </div>
        <p className="text-xs text-gray-600 leading-relaxed">{data.explanation}</p>
      </div>

      {/* Recommendations */}
      <div className="px-4 pb-4 border-t border-gray-100 pt-4">
        <div className="text-sm font-semibold text-gray-900 mb-2">What You Should Do</div>
        <div className="space-y-2">
          {data.recommendations.slice(0, 2).map((rec, i) => (
            <div key={i} className={`flex gap-2 items-start border-l-2 pl-3 py-1 ${i === 0 ? 'border-red-400' : 'border-yellow-400'}`}>
              <CheckCircle className={`w-3 h-3 mt-0.5 flex-shrink-0 ${i === 0 ? 'text-red-400' : 'text-yellow-400'}`} />
              <p className="text-xs text-gray-600">{rec}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Compare() {
  const { address1, address2 } = useParams();
  const navigate = useNavigate();
  const [data1, setData1] = useState<RiskData | null>(null);
  const [data2, setData2] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchBoth = async () => {
      try {
        setLoading(true);
        const [r1, r2] = await Promise.all([
          fetch(`${API}/risk?address=${encodeURIComponent(decodeURIComponent(address1 || ''))}`),
          fetch(`${API}/risk?address=${encodeURIComponent(decodeURIComponent(address2 || ''))}`),
        ]);
        if (!r1.ok || !r2.ok) throw new Error('Failed to fetch');
        const [j1, j2] = await Promise.all([r1.json(), r2.json()]);
        setData1(j1);
        setData2(j2);
      } catch (e) {
        setError('Could not load comparison data. Make sure the backend is running.');
      } finally {
        setLoading(false);
      }
    };
    fetchBoth();
  }, [address1, address2]);

  if (loading) return (
    <div className="min-h-screen bg-[#d1f4dd] flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-[#0d9488] mx-auto mb-4" />
        <p className="text-gray-700 text-lg font-medium">Analyzing both properties...</p>
        <p className="text-gray-500 text-sm mt-2">This may take a few seconds</p>
      </div>
    </div>
  );

  if (error || !data1 || !data2) return (
    <div className="min-h-screen bg-[#d1f4dd] flex items-center justify-center">
      <div className="text-center bg-white p-8 rounded-xl shadow-sm">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-900 font-semibold">{error}</p>
        <button onClick={() => navigate('/')} className="mt-4 px-6 py-2 bg-[#0d9488] text-white rounded-lg">Go Back</button>
      </div>
    </div>
  );

  // Radar chart data
  const radarData = [
    { risk: 'Flood',     A: data1.flood,     B: data2.flood },
    { risk: 'Wildfire',  A: data1.fire,      B: data2.fire },
    { risk: 'Landslide', A: data1.landslide, B: data2.landslide },
  ];

  const winner = data1.overall <= data2.overall ? 'A' : 'B';
  const winnerData = winner === 'A' ? data1 : data2;

  return (
    <div className="min-h-screen bg-[#d1f4dd]">
      {/* Nav */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-900 hover:text-[#0d9488] transition-colors">
          <ArrowLeft className="w-5 h-5" />
          <span className="font-semibold">🌎 ClimateCheck</span>
        </button>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">Property Comparison</h1>
        <p className="text-gray-500 text-center mb-8">Side-by-side climate risk analysis</p>

        {/* Winner Banner */}
        <div className="bg-[#0d9488] text-white rounded-xl p-4 mb-6 text-center shadow-sm">
          <div className="text-sm font-medium opacity-80 mb-1">🏆 Lower Climate Risk</div>
          <div className="font-bold text-lg">{winnerData.address}</div>
          <div className="text-sm opacity-80 mt-1">Overall score: {winnerData.overall}/100 vs {(winner === 'A' ? data2 : data1).overall}/100</div>
        </div>

        {/* Side by Side Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <PropertyCard data={data1} label="Property A" />
          <PropertyCard data={data2} label="Property B" />
        </div>

        {/* Radar Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2 text-center">Risk Profile Comparison</h2>
          <p className="text-sm text-gray-500 text-center mb-6">Closer to center = lower risk</p>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="risk" />
              <Radar name="Property A" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
              <Radar name="Property B" dataKey="B" stroke="#f97316" fill="#f97316" fillOpacity={0.2} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-6 mt-2">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500" /><span className="text-sm text-gray-600">Property A</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-orange-500" /><span className="text-sm text-gray-600">Property B</span></div>
          </div>
        </div>

        {/* Score Comparison Table */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Score Breakdown</h2>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left text-sm text-gray-500 pb-3">Category</th>
                <th className="text-center text-sm text-blue-500 pb-3">Property A</th>
                <th className="text-center text-sm text-orange-500 pb-3">Property B</th>
                <th className="text-center text-sm text-gray-500 pb-3">Better</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {[
                { label: '🌊 Flood', a: data1.flood, b: data2.flood },
                { label: '🔥 Wildfire', a: data1.fire, b: data2.fire },
                { label: '🏔️ Landslide', a: data1.landslide, b: data2.landslide },
                { label: '⭐ Overall', a: data1.overall, b: data2.overall },
              ].map(({ label, a, b }) => (
                <tr key={label} className="py-2">
                  <td className="py-3 text-sm font-medium text-gray-700">{label}</td>
                  <td className={`py-3 text-center font-bold ${getRiskLevel(a).color}`}>{a}</td>
                  <td className={`py-3 text-center font-bold ${getRiskLevel(b).color}`}>{b}</td>
                  <td className="py-3 text-center text-sm">
                    {a < b ? <span className="text-blue-500 font-medium">A ✓</span> : a > b ? <span className="text-orange-500 font-medium">B ✓</span> : <span className="text-gray-400">Tie</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}