import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const MOVIE_EMOJIS = ['🕷️', '🦇', '⚡'];

const App = () => {
  const [view, setView] = useState('movies');
  const [movies, setMovies] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showtimes, setShowtimes] = useState([]);
  const [selectedShowtime, setSelectedShowtime] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userId, setUserId] = useState('');
  const [phone, setPhone] = useState('');
  const [bookingRef, setBookingRef] = useState(null);
  const [otpCode, setOtpCode] = useState('');
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [paymentTime, setPaymentTime] = useState(0);
  const seatsInterval = useRef(null);
  const paymentInterval = useRef(null);
  const timerInterval = useRef(null);

  useEffect(() => {
    if (view === 'movies') fetchMovies();
    return () => {
      clearInterval(seatsInterval.current);
      clearInterval(paymentInterval.current);
      clearInterval(timerInterval.current);
    };
  }, [view]);

  const fetchMovies = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/movies`);
      setMovies(res.data);
    } catch (err) {
      setError('Could not load movies. Is the API running on port 8000?');
    } finally {
      setLoading(false);
    }
  };

  const handleMovieSelect = async (movie) => {
    setSelectedMovie(movie);
    setView('showtimes');
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/showtimes?movie_id=${movie.id}`);
      setShowtimes(res.data);
    } catch (err) {
      setError('Failed to fetch showtimes.');
    } finally {
      setLoading(false);
    }
  };

  const handleShowtimeSelect = (showtime) => {
    setSelectedShowtime(showtime);
    setView('seats');
    setError(null);
    fetchSeats(showtime.id);
    seatsInterval.current = setInterval(() => fetchSeats(showtime.id), 5000);
  };

  const fetchSeats = async (showtimeId) => {
    try {
      const res = await axios.get(`${API_URL}/showtimes/${showtimeId}/seats`);
      setSeats(res.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch seats', err);
    }
  };

  const handleSeatSelect = (seat) => {
    if (seat.status === 'AVAILABLE') {
      setSelectedSeat(seat);
      setError(null);
    }
  };

  const handleHoldSeat = async () => {
    if (!userId.trim() || !phone.trim()) {
      setError('Please enter your name and phone number.');
      return;
    }
    try {
      const res = await axios.post(`${API_URL}/seats/${selectedSeat.id}/hold`, {
        user_id: userId, phone: phone
      });
      setBookingRef(res.data.booking_ref);
      clearInterval(seatsInterval.current);
      setView('otp');
      setError(null);
      try {
        await axios.post(`${API_URL}/otp/send`, { phone: phone, ref: res.data.booking_ref });
      } catch (e) { /* OTP send failure is non-blocking */ }
    } catch (err) {
      if (err.response && err.response.status === 409) {
        setError('⚡ This seat was just taken by someone else!');
        fetchSeats(selectedShowtime.id);
        setSelectedSeat(null);
      } else {
        setError('Failed to hold seat. Try again.');
      }
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpCode.trim()) { setError('Please enter an OTP code.'); return; }
    setError(null);
    try {
      await axios.post(`${API_URL}/otp/verify`, { ref: bookingRef, code: otpCode });
      setView('payment');
      setPaymentTime(0);
      timerInterval.current = setInterval(() => setPaymentTime(prev => prev + 1), 1000);
      try {
        await axios.post(`${API_URL}/charge`, { booking_ref: bookingRef });
        paymentInterval.current = setInterval(async () => {
          try {
            const res = await axios.get(`${API_URL}/booking/${bookingRef}/status`);
            if (res.data.status === 'SUCCEEDED' || res.data.status === 'FAILED') {
              clearInterval(paymentInterval.current);
              clearInterval(timerInterval.current);
              setPaymentStatus(res.data);
              setView('confirmation');
            }
          } catch (e) { console.error('Poll error', e); }
        }, 2000);
      } catch (e) {
        clearInterval(timerInterval.current);
        setPaymentStatus({ status: 'FAILED' });
        setView('confirmation');
      }
    } catch (err) {
      setError('Invalid OTP code. Try again.');
    }
  };

  const resetBooking = () => {
    setBookingRef(null);
    setPaymentStatus(null);
    setOtpCode('');
    setSelectedSeat(null);
    setSelectedShowtime(null);
    setSelectedMovie(null);
    setError(null);
    setUserId('');
    setPhone('');
    clearInterval(seatsInterval.current);
    clearInterval(paymentInterval.current);
    clearInterval(timerInterval.current);
    setView('movies');
  };

  const goBack = (toView) => {
    setError(null);
    clearInterval(seatsInterval.current);
    if (toView === 'movies') { setSelectedMovie(null); setSelectedShowtime(null); setSelectedSeat(null); }
    if (toView === 'showtimes') { setSelectedShowtime(null); setSelectedSeat(null); }
    setView(toView);
  };

  const fmtDuration = (m) => `${Math.floor(m/60)}h ${m%60}m`;
  const fmtTime = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' })
      + ' · ' + d.toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' });
  };

  // ── VIEWS ──────────────────────────────────────────────
  const renderMovies = () => {
    if (loading) return <div className="loader">🎬 Loading movies...</div>;
    if (movies.length === 0) return <div className="loader">No movies found. Check API connection.</div>;
    return (
      <div className="view-movies">
        <h2 style={{textAlign:'center', marginBottom:'2rem', fontSize:'1.5rem', color:'#94a3b8'}}>Now Showing</h2>
        <div className="movie-grid">
          {movies.map((movie, idx) => (
            <div key={movie.id} className="movie-card" onClick={() => handleMovieSelect(movie)}>
              <div className="movie-poster">
                <span style={{fontSize:'4rem'}}>{MOVIE_EMOJIS[idx % MOVIE_EMOJIS.length]}</span>
              </div>
              <div className="movie-info">
                <h3 className="movie-title">{movie.title}</h3>
                <p className="movie-desc">{movie.description}</p>
                <div className="movie-meta">
                  <span className="movie-duration">🕐 {fmtDuration(movie.duration)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderShowtimes = () => {
    if (loading) return <div className="loader">Loading showtimes...</div>;
    return (
      <div className="showtime-container">
        <button className="btn-back" onClick={() => goBack('movies')}>← Back to Movies</button>
        <h2 style={{textAlign:'center', margin:'1rem 0'}}>{selectedMovie?.title}</h2>
        <p style={{textAlign:'center', color:'#64748b', marginBottom:'2rem'}}>Select a showtime</p>
        <div className="showtime-grid">
          {showtimes.map(st => (
            <div key={st.id} className="showtime-card" onClick={() => handleShowtimeSelect(st)}>
              <div className="showtime-time">{fmtTime(st.starts_at)}</div>
              <div className="showtime-price">৳{Number(st.price).toFixed(0)}</div>
              <div className="showtime-theatre">Theatre {st.theatre_id}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSeats = () => {
    const rows = {};
    seats.forEach(s => { (rows[s.row_label] = rows[s.row_label] || []).push(s); });
    const sortedRows = Object.keys(rows).sort();

    return (
      <div className="seating-view">
        <button className="btn-back" onClick={() => goBack('showtimes')}>← Back to Showtimes</button>
        <div className="nav-breadcrumb">
          <span className="nav-step completed">{selectedMovie?.title}</span>
          <span> › </span>
          <span className="nav-step completed">{fmtTime(selectedShowtime?.starts_at)}</span>
          <span> › </span>
          <span className="nav-step active">Select Seat</span>
        </div>

        <div className="screen-indicator">SCREEN</div>

        <div className="seating-chart">
          {sortedRows.map(rowLabel => (
            <div key={rowLabel} className="seat-row">
              <span className="row-label">{rowLabel}</span>
              {rows[rowLabel].sort((a,b) => a.col_number - b.col_number).map(seat => (
                <div
                  key={seat.id}
                  className={`seat ${seat.status.toLowerCase()}${selectedSeat?.id === seat.id ? ' selected' : ''}`}
                  onClick={() => handleSeatSelect(seat)}
                >
                  {seat.col_number}
                </div>
              ))}
            </div>
          ))}
        </div>

        <div className="seat-legend">
          <div className="legend-item"><span className="legend-dot available"></span> Available</div>
          <div className="legend-item"><span className="legend-dot selected"></span> Selected</div>
          <div className="legend-item"><span className="legend-dot held"></span> Held</div>
          <div className="legend-item"><span className="legend-dot booked"></span> Booked</div>
        </div>

        {selectedSeat && (
          <div className="booking-panel">
            <h3>Seat {selectedSeat.row_label}{selectedSeat.col_number} · ৳{Number(selectedShowtime.price).toFixed(0)}</h3>
            {error && <div className="alert error">{error}</div>}
            <div className="otp-form">
              <input type="text" placeholder="Your Name" value={userId} onChange={e => setUserId(e.target.value)} className="otp-input" />
              <input type="text" placeholder="Phone Number (e.g. 01700000000)" value={phone} onChange={e => setPhone(e.target.value)} className="otp-input" />
              <button className="btn-primary" onClick={handleHoldSeat}>🔒 Hold This Seat</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderOtp = () => (
    <div className="otp-view" style={{maxWidth:'500px', margin:'0 auto'}}>
      <h2 style={{textAlign:'center'}}>📱 Verify Phone Number</h2>
      <div className="booking-panel" style={{marginTop:'1.5rem'}}>
        <div className="ticket-details">
          <div className="ticket-row"><span>Booking Ref</span><span>{bookingRef}</span></div>
          <div className="ticket-row"><span>Seat</span><span>{selectedSeat?.row_label}{selectedSeat?.col_number}</span></div>
          <div className="ticket-row"><span>Movie</span><span>{selectedMovie?.title}</span></div>
        </div>
        {error && <div className="alert error" style={{marginTop:'1rem'}}>{error}</div>}
        <div className="otp-form" style={{marginTop:'1.5rem'}}>
          <p style={{color:'#94a3b8', fontSize:'0.9rem', textAlign:'center'}}>Enter any code — the mock gateway accepts anything</p>
          <input type="text" className="otp-input" placeholder="Enter OTP Code" value={otpCode} onChange={e => setOtpCode(e.target.value)} />
          <button className="btn-primary" onClick={handleVerifyOtp}>✅ Verify & Pay</button>
        </div>
      </div>
    </div>
  );

  const renderPayment = () => (
    <div className="payment-processing">
      <div className="spinner"><div className="pulse-ring"></div></div>
      <h2>Processing your payment...</h2>
      <p style={{color:'#94a3b8'}}>Booking Ref: {bookingRef}</p>
      <p style={{color:'#64748b', fontSize:'0.9rem'}}>Elapsed: {paymentTime}s</p>
      <p style={{color:'#475569', fontSize:'0.8rem', marginTop:'1rem'}}>The mock gateway takes 2-15 seconds to respond</p>
    </div>
  );

  const renderConfirmation = () => {
    const ok = paymentStatus?.status === 'SUCCEEDED';
    return (
      <div className={`confirmation-card ${ok ? 'success' : 'failed'}`}>
        <h2 style={{fontSize:'2rem'}}>{ok ? '🎉 Booking Confirmed!' : '❌ Payment Failed'}</h2>
        <div className="ticket-details" style={{marginTop:'1.5rem'}}>
          <div className="ticket-row"><span>Booking Ref</span><span>{bookingRef}</span></div>
          {ok && <>
            <div className="ticket-row"><span>Movie</span><span>{selectedMovie?.title}</span></div>
            <div className="ticket-row"><span>Seat</span><span>{selectedSeat?.row_label}{selectedSeat?.col_number}</span></div>
            <div className="ticket-row"><span>Amount</span><span>৳{Number(paymentStatus?.amount || 0).toFixed(0)}</span></div>
          </>}
        </div>
        <button className="btn-primary" style={{marginTop:'2rem'}} onClick={resetBooking}>
          {ok ? '🎬 Book Another Seat' : '🔄 Try Again'}
        </button>
      </div>
    );
  };

  return (
    <div className="app-container">
      <header className="header" onClick={resetBooking} style={{cursor:'pointer'}}>
        <h1>🎬 CinemaSeat</h1>
      </header>
      {error && view === 'movies' && <div className="alert error">{error}</div>}
      <main className="main-content">
        {view === 'movies' && renderMovies()}
        {view === 'showtimes' && renderShowtimes()}
        {view === 'seats' && renderSeats()}
        {view === 'otp' && renderOtp()}
        {view === 'payment' && renderPayment()}
        {view === 'confirmation' && renderConfirmation()}
      </main>
    </div>
  );
};

export default App;
