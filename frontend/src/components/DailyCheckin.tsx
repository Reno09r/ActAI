import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Calendar, BarChart2, Smile, Target, Check, Edit3, Save, Loader2 } from 'lucide-react';

interface DailyCheckin {
  id: number;
  user_id: number;
  checkin_date: string;
  mood: string;
  reflection_notes: string;
  achievements_today: string;
  ai_motivational_quote: string;
  productivity_score: number;
}

const API_BASE_URL = "/api";

const DailyCheckin = () => {
  const { token } = useAuth();
  const [checkins, setCheckins] = useState<DailyCheckin[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [currentCheckin, setCurrentCheckin] = useState<Partial<DailyCheckin>>({
    mood: '',
    reflection_notes: '',
    achievements_today: '',
    productivity_score: 5
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const moods = [
    { value: 'great', label: '😊 Great', color: 'bg-green-100 text-green-800' },
    { value: 'good', label: '🙂 Good', color: 'bg-blue-100 text-blue-800' },
    { value: 'neutral', label: '😐 Neutral', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'bad', label: '😔 Bad', color: 'bg-orange-100 text-orange-800' },
    { value: 'terrible', label: '😢 Terrible', color: 'bg-red-100 text-red-800' }
  ];

  useEffect(() => {
    fetchCheckinHistory();
  }, []);

  useEffect(() => {
    fetchCheckinForDate(selectedDate);
  }, [selectedDate]);

  const fetchCheckinHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/daily-checkin/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.status === 404) {
        setCheckins([]);
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch checkin history');
      const data = await response.json();
      setCheckins(data);
    } catch (err) {
      setCheckins([]);
    }
  };

  const fetchCheckinForDate = async (date: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/daily-checkin/${date}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.status === 404) {
        setCurrentCheckin({
          mood: '',
          reflection_notes: '',
          achievements_today: '',
          productivity_score: 5
        });
        setIsEditing(true);
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch checkin');
      const data = await response.json();
      setCurrentCheckin(data);
      setIsEditing(false);
    } catch (err) {
      setCurrentCheckin({
        mood: '',
        reflection_notes: '',
        achievements_today: '',
        productivity_score: 5
      });
      setIsEditing(true);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/daily-checkin`;
      const method = currentCheckin.id ? 'PUT' : 'POST';
      const body = {
        ...currentCheckin,
        checkin_date: selectedDate
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) throw new Error('Failed to save checkin');
      
      const data = await response.json();
      setCurrentCheckin(data);
      setIsEditing(false);
      fetchCheckinHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save checkin');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Daily Check-in</h1>

      {error && (
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Check-in Form */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800">Check-in for {new Date(selectedDate).toLocaleDateString()}</h2>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              {isEditing ? <Save className="w-5 h-5" /> : <Edit3 className="w-5 h-5" />}
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Mood</label>
              <div className="grid grid-cols-5 gap-2">
                {moods.map((mood) => (
                  <button
                    key={mood.value}
                    type="button"
                    onClick={() => setCurrentCheckin(prev => ({ ...prev, mood: mood.value }))}
                    className={`p-2 rounded-lg text-center ${
                      currentCheckin.mood === mood.value ? mood.color : 'bg-gray-100'
                    }`}
                  >
                    {mood.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Productivity</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={currentCheckin.productivity_score}
                onChange={(e) => setCurrentCheckin(prev => ({ ...prev, productivity_score: parseFloat(e.target.value) }))}
                className="w-full"
              />
              <div className="text-center mt-1">
                <span className="text-sm text-gray-600">{currentCheckin.productivity_score}/10</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Today's Achievements</label>
              <textarea
                value={currentCheckin.achievements_today || ''}
                onChange={(e) => setCurrentCheckin(prev => ({ ...prev, achievements_today: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="What did you achieve today?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Reflections</label>
              <textarea
                value={currentCheckin.reflection_notes || ''}
                onChange={(e) => setCurrentCheckin(prev => ({ ...prev, reflection_notes: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
                placeholder="Your thoughts and reflections about today..."
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Saving...
                </div>
              ) : (
                'Save Check-in'
              )}
            </button>
          </form>
        </div>

        {/* History and Analytics */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Check-in History</h2>
            <div className="space-y-4">
              {checkins.length === 0 ? (
                <p className="text-gray-500 text-center">No check-ins yet</p>
              ) : (
                checkins.slice(0, 5).map((checkin) => (
                  <div key={checkin.id} className="border-b border-gray-200 pb-4 last:border-b-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">
                        {new Date(checkin.checkin_date).toLocaleDateString()}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        moods.find(m => m.value === checkin.mood)?.color || 'bg-gray-100'
                      }`}>
                        {moods.find(m => m.value === checkin.mood)?.label || checkin.mood}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{checkin.reflection_notes}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Analytics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center mb-2">
                  <Smile className="w-5 h-5 text-blue-500 mr-2" />
                  <h3 className="font-medium">Mood</h3>
                </div>
                <div className="h-32 flex items-center justify-center text-gray-500">
                  Mood Chart
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center mb-2">
                  <Target className="w-5 h-5 text-green-500 mr-2" />
                  <h3 className="font-medium">Productivity</h3>
                </div>
                <div className="h-32 flex items-center justify-center text-gray-500">
                  Productivity Chart
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyCheckin; 