import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import './chartSetup';
import './index.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const apiUsername = import.meta.env.VITE_API_USERNAME || 'puspal';
  const apiPassword = import.meta.env.VITE_API_PASSWORD || 'admin12345';
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const authHeader = {
    'Authorization': `Basic ${window.btoa(`${apiUsername}:${apiPassword}`)}`
  };

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${apiUrl}/api/upload/`, {
        headers: authHeader 
      });
      setHistory(res.data); 
    } catch (err) { console.error("Sync failed", err); }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleFileUpload = async () => {
    if (!file) return alert("Please select a file.");
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    try {
      const res = await axios.post(`${apiUrl}/api/upload/`, formData, {
        headers: {
          ...authHeader, 
          'Content-Type': 'multipart/form-data'
        }
      });
      setSummary(res.data); 
      fetchHistory();
    } catch (err) { 
      alert("Upload failed: Unauthorized or Server Error"); 
    } finally { setLoading(false); }
  };

  const downloadReport = async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/export-pdf/`, {
        headers: authHeader, 
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Equipment_Report.pdf'); 
      document.body.appendChild(link);
      link.click();
    } catch (err) { alert("Failed to generate report"); }
  };

  const chartData = {
    labels: summary ? Object.keys(summary.distribution) : [],
    datasets: [{
      label: 'Equipment Type Distribution',
      data: summary ? Object.values(summary.distribution) : [],
      backgroundColor: '#0d6efd',
      borderRadius: 4,
    }],
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Chemical Equipment Visualizer</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={downloadReport} className="theme-toggle">Generate PDF Report</button>
          <button onClick={toggleTheme} className="theme-toggle">
            Switch to {isDarkMode ? 'Light' : 'Dark'} Mode
          </button>
        </div>
      </header>

      <section className="card">
        <h3 style={{marginTop: 0}}>Data Import</h3>
        <div style={{display: 'flex', gap: '15px', alignItems: 'center'}}>
          <input 
            type="file" 
            accept=".csv" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={{flexGrow: 1}}
          />
          <button onClick={handleFileUpload} disabled={loading} className="execute-btn">
            {loading ? 'Processing...' : 'Upload and Analyze'}
          </button>
        </div>
      </section>

      {summary && (
        <div className="results-grid">
          <div className="card">
            <h4>Summary Statistics</h4>
            <div className="stat-value">{summary.total_count}</div> 
            <div className="stat-label">Total Equipment Units</div>
            <hr style={{margin: '15px 0', borderColor: 'var(--border-color)'}} />
            <div className="stat-value">{summary.averages.temp.toFixed(1)}°C</div> 
            <div className="stat-label">Average Operating Temp</div>
          </div>
          <div className="card">
            <Bar data={chartData} options={{ maintainAspectRatio: false }} height={200} /> 
          </div>
        </div>
      )}

      <section className="card">
        <h3>Recent Uploads</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Date</th>
              <th>Avg Temp</th>
            </tr>
          </thead>
          <tbody>
            {history.slice(0, 5).map(item => (
              <tr key={item.id}>
                <td>{item.file_name}</td> 
                <td>{item.uploaded_at}</td> 
                <td className="text-accent">{item.results.averages.temp.toFixed(2)}°C</td> 
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;