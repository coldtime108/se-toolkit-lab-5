import { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

interface ScoreBucket {
  bucket: string;
  count: number;
}

interface TimelinePoint {
  date: string;
  submissions: number;
}

interface PassRate {
  task: string;
  avg_score: number;
  attempts: number;
}

function Dashboard() {
  const [lab, setLab] = useState('lab-04');
  const [scores, setScores] = useState<ScoreBucket[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [passRates, setPassRates] = useState<PassRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const labs = ['lab-01', 'lab-02', 'lab-03', 'lab-04', 'lab-05'];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('api_key');
      if (!token) {
        setError('No API key found. Please log in.');
        setLoading(false);
        return;
      }

      try {
        const baseUrl = import.meta.env.VITE_API_TARGET;
        const headers = { Authorization: `Bearer ${token}` };

        const [scoresRes, timelineRes, passRatesRes] = await Promise.all([
          fetch(`${baseUrl}/analytics/scores?lab=${lab}`, { headers }),
          fetch(`${baseUrl}/analytics/timeline?lab=${lab}`, { headers }),
          fetch(`${baseUrl}/analytics/pass-rates?lab=${lab}`, { headers }),
        ]);

        if (!scoresRes.ok || !timelineRes.ok || !passRatesRes.ok) {
          throw new Error('Failed to fetch analytics data');
        }

        const scoresData = await scoresRes.json();
        const timelineData = await timelineRes.json();
        const passRatesData = await passRatesRes.json();

        setScores(scoresData);
        setTimeline(timelineData);
        setPassRates(passRatesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [lab]);

  const barChartData = {
    labels: scores.map((item) => item.bucket),
    datasets: [
      {
        label: 'Number of submissions',
        data: scores.map((item) => item.count),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
    ],
  };

  const lineChartData = {
    labels: timeline.map((item) => item.date),
    datasets: [
      {
        label: 'Submissions per day',
        data: timeline.map((item) => item.submissions),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' as const },
      title: { display: true, text: 'Score Distribution' },
    },
  };

  const lineOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' as const },
      title: { display: true, text: 'Submissions Timeline' },
    },
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Analytics Dashboard</h1>

      <div>
        <label htmlFor="lab-select">Select Lab: </label>
        <select
          id="lab-select"
          value={lab}
          onChange={(e) => setLab(e.target.value)}
        >
          {labs.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '30px' }}>
        <div>
          {scores.length > 0 ? (
            <Bar data={barChartData} options={barOptions} />
          ) : (
            <p>No score data available</p>
          )}
        </div>

        <div>
          {timeline.length > 0 ? (
            <Line data={lineChartData} options={lineOptions} />
          ) : (
            <p>No timeline data available</p>
          )}
        </div>
      </div>

      <div style={{ marginTop: '40px' }}>
        <h2>Pass Rates per Task</h2>
        {passRates.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Task</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Average Score</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Attempts</th>
              </tr>
            </thead>
            <tbody>
              {passRates.map((item) => (
                <tr key={item.task}>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{item.task}</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{item.avg_score.toFixed(1)}</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>{item.attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No pass rates data available</p>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
