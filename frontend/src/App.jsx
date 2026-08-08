import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const fallbackApiUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
const rawApiUrl = import.meta.env.VITE_API_URL || fallbackApiUrl;
const API_URL = rawApiUrl.startsWith('http') ? rawApiUrl.replace(/\/$/, '') : fallbackApiUrl.replace(/\/$/, '');

const POSTER_GRADIENTS = [
  'linear-gradient(135deg, #1e293b, #0f172a)',
  'linear-gradient(135deg, #0f172a, #1e1b4b)',
  'linear-gradient(135deg, #0f172a, #312e81)',
  'linear-gradient(135deg, #171717, #0a0a0a)',
  'linear-gradient(135deg, #1e293b, #020617)',
  'linear-gradient(135deg, #172554, #0f172a)',
];

const App = () => {
  const [filter, setFilter] = useState('');
  const [holdTimeLeft, setHoldTimeLeft] = useState(null);
  const [view, setView] = useState('movies');
  const [movies, setMovies] = useState([]);

  // Filtered movies based on search input
  const filteredMovies = movies.filter(m =>
    m.title.toLowerCase().includes(filter.toLowerCase()) ||
    (m.description && m.description.toLowerCase().includes(filter.toLowerCase()))
  );
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showtimes, setShowtimes] = useState([]);
  const [selectedShowtime, setSelectedShowtime] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [heldSeatsList, setHeldSeatsList] = useState([]);
  const [bookingRefs, setBookingRefs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userId, setUserId] = useState('');
  const [phone, setPhone] = useState('');
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

  // Robust 60s timer countdown effect
  useEffect(() => {
    if (holdTimeLeft === null) return;
    if (holdTimeLeft <= 0) {
      // Auto release held seats on timeout
      if (heldSeatsList && heldSeatsList.length > 0) {
        heldSeatsList.forEach(seat => {
          axios.post(`${API_URL}/seats/${seat.id}/release`, { user_id: userId }).catch(() => {});
        });
      }
      alert('Hold expired (60-second limit reached). Returning to seat selection.');
      setHoldTimeLeft(null);
      setBookingRefs([]);
      setHeldSeatsList([]);
      setSelectedSeats([]);
      setView('seats');
      return;
    }
    const timer = setTimeout(() => {
      setHoldTimeLeft(prev => (prev !== null ? prev - 1 : null));
    }, 1000);
    return () => clearTimeout(timer);
  }, [holdTimeLeft, heldSeatsList, userId]);

  const fetchMovies = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/movies`);
      setMovies(res.data);
    } catch (err) {
      setError('Could not load movies. Please check API connection.');
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
    if (seat.status !== 'AVAILABLE') return;
    setError(null);
    setSelectedSeats(prev => {
      const isAlreadySelected = prev.some(s => s.id === seat.id);
      if (isAlreadySelected) {
        return prev.filter(s => s.id !== seat.id);
      } else {
        if (prev.length >= 3) {
          setError('You can select a maximum of 3 seats at a time.');
          return prev;
        }
        return [...prev, seat];
      }
    });
  };

  const handleHoldSeat = async () => {
    if (selectedSeats.length === 0) {
      setError('Please select at least 1 seat.');
      return;
    }
    if (!userId.trim() || !phone.trim()) {
      setError('Please provide your name and phone number to continue.');
      return;
    }
    setError(null);
    try {
      const holdResults = await Promise.all(
        selectedSeats.map(seat =>
          axios.post(`${API_URL}/seats/${seat.id}/hold`, {
            user_id: userId,
            phone: phone,
          })
        )
      );
      const refs = holdResults.map(res => res.data.booking_ref);
      setBookingRefs(refs);
      setHeldSeatsList(selectedSeats);

      // Start 60s hold countdown
      setHoldTimeLeft(parseInt(import.meta.env.VITE_HOLD_TTL_SECONDS || '60'));

      clearInterval(seatsInterval.current);
      setView('otp');
      setError(null);

      try {
        await axios.post(`${API_URL}/otp/send`, { phone: phone, ref: refs[0] });
      } catch (e) { /* non-blocking */ }
    } catch (err) {
      if (err.response && err.response.status === 409) {
        setError('One or more selected seats were just reserved by another user. Please re-select.');
        fetchSeats(selectedShowtime.id);
        setSelectedSeats([]);
      } else if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to reserve seats. Please try again.');
      }
    }
  };

  const handleResendOtp = async () => {
    setError(null);
    try {
      await axios.post(`${API_URL}/otp/send`, { phone: phone, ref: bookingRefs[0] });
      setError('OTP resent! Please wait a few seconds.');
    } catch (e) {
      setError('Failed to resend OTP.');
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpCode.trim()) { setError('Please enter the verification code.'); return; }
    setError(null);
    try {
      await axios.post(`${API_URL}/otp/verify`, { ref: bookingRefs[0], code: otpCode });
      setHoldTimeLeft(null); // Stop timer on success
      setView('payment');
      setPaymentTime(0);
      timerInterval.current = setInterval(() => setPaymentTime(prev => prev + 1), 1000);

      try {
        await Promise.all(bookingRefs.map(ref => axios.post(`${API_URL}/charge`, { booking_ref: ref })));
        paymentInterval.current = setInterval(async () => {
          try {
            const statuses = await Promise.all(bookingRefs.map(ref => axios.get(`${API_URL}/booking/${ref}/status`)));
            const allDone = statuses.every(r => r.data.status === 'SUCCEEDED' || r.data.status === 'FAILED');
            if (allDone) {
              clearInterval(paymentInterval.current);
              clearInterval(timerInterval.current);
              const totalAmount = statuses.reduce((sum, r) => sum + Number(r.data.amount || 0), 0);
              const anyFailed = statuses.some(r => r.data.status === 'FAILED');
              setPaymentStatus({
                status: anyFailed ? 'FAILED' : 'SUCCEEDED',
                amount: totalAmount,
              });
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
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Invalid verification code. Please try again.');
      }
    }
  };

  const handleCancelHold = async () => {
    try {
      await Promise.all(heldSeatsList.map(seat => axios.post(`${API_URL}/seats/${seat.id}/release`, { user_id: userId })));
    } catch (e) {
      // ignore
    }
    setHoldTimeLeft(null);
    setBookingRefs([]);
    setHeldSeatsList([]);
    setSelectedSeats([]);
    setView('seats');
  };

  const resetBooking = () => {
    setBookingRefs([]);
    setHeldSeatsList([]);
    setPaymentStatus(null);
    setOtpCode('');
    setSelectedSeats([]);
    setSelectedShowtime(null);
    setSelectedMovie(null);
    setError(null);
    setUserId('');
    setPhone('');
    setHoldTimeLeft(null);
    clearInterval(seatsInterval.current);
    clearInterval(paymentInterval.current);
    clearInterval(timerInterval.current);
    setView('movies');
  };

  const goBack = (toView) => {
    setError(null);
    clearInterval(seatsInterval.current);
    if (toView === 'movies') { setSelectedMovie(null); setSelectedShowtime(null); setSelectedSeats([]); }
    if (toView === 'showtimes') { setSelectedShowtime(null); setSelectedSeats([]); }
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
    if (loading) return <div className="loader">Loading movies...</div>;
    if (movies.length === 0) return <div className="loader">No movies found. Check API connection.</div>;
    return (
      <div className="view-movies">
          <input
            type="text"
            placeholder="Search movies..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="form-input"
            style={{ marginBottom: '1rem', width: '100%' }}
          />
          {filteredMovies.length === 0 ? (
            <div className="loader">No movies match your search.</div>
          ) : (
            <div className="movie-grid">
              {filteredMovies.map((movie, idx) => (
                <div key={movie.id} className="movie-card" onClick={() => handleMovieSelect(movie)}>
                  <div className="movie-poster" style={{ background: POSTER_GRADIENTS[idx % POSTER_GRADIENTS.length] }}>
                    <span className="poster-title-initial">{movie.title.charAt(0)}</span>
                  </div>
                  <div className="movie-info">
                    <h3 className="movie-title">{movie.title}</h3>
                    <p className="movie-desc">{movie.description}</p>
                    <div className="movie-meta">
                      <span className="movie-duration">{fmtDuration(movie.duration)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}</div>
    );
  };

  const renderShowtimes = () => {
    if (loading) return <div className="loader">Loading showtimes...</div>;
    return (
      <div className="showtime-container">
        <button className="btn-back" onClick={() => goBack('movies')}>&#8592; Back to Movies</button>
        <h2 className="selected-title">{selectedMovie?.title}</h2>
        <p className="subtitle">Select a showtime</p>
        <div className="showtime-grid">
          {showtimes.length === 0 && <p style={{color:'#64748b'}}>No showtimes available.</p>}
          {showtimes.map(st => (
            <div key={st.id} className="showtime-card" onClick={() => handleShowtimeSelect(st)}>
              <div className="showtime-time">{fmtTime(st.starts_at)}</div>
              <div className="showtime-price">BDT {Number(st.price).toFixed(0)}</div>
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
    const totalPrice = selectedSeats.length * Number(selectedShowtime?.price || 0);

    return (
      <div className="seating-view">
        <button className="btn-back" onClick={() => goBack('showtimes')}>&#8592; Back to Showtimes</button>
        <div className="nav-breadcrumb">
          <span className="nav-step completed">{selectedMovie?.title}</span>
          <span className="separator">/</span>
          <span className="nav-step completed">{fmtTime(selectedShowtime?.starts_at)}</span>
          <span className="separator">/</span>
          <span className="nav-step active">Select Seats (Max 3)</span>
        </div>

        <div className="screen-indicator">SCREEN</div>

        <div className="seating-chart">
          {sortedRows.map(rowLabel => (
            <div key={rowLabel} className="seat-row">
              <span className="row-label">{rowLabel}</span>
              {rows[rowLabel].sort((a,b) => a.col_number - b.col_number).map(seat => {
                const isSelected = selectedSeats.some(s => s.id === seat.id);
                return (
                  <div
                    key={seat.id}
                    className={`seat ${seat.status.toLowerCase()}${isSelected ? ' selected' : ''}`}
                    onClick={() => handleSeatSelect(seat)}
                  >
                    {seat.col_number}
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        <div className="seat-legend">
          <div className="legend-item"><span className="legend-dot available"></span> Available</div>
          <div className="legend-item"><span className="legend-dot selected"></span> Selected</div>
          <div className="legend-item"><span className="legend-dot held"></span> Held</div>
          <div className="legend-item"><span className="legend-dot booked"></span> Booked</div>
        </div>

        {error && <div className="alert error" style={{ maxWidth: '500px', margin: '0 auto 1.5rem' }}>{error}</div>}

        {selectedSeats.length > 0 && (
          <div className="booking-panel centered-panel fade-in">
            <h3>
              {selectedSeats.length} {selectedSeats.length === 1 ? 'Seat' : 'Seats'} Selected: {' '}
              {selectedSeats.map(s => `${s.row_label}${s.col_number}`).join(', ')}
              &mdash; BDT {totalPrice.toFixed(0)}
            </h3>
            <div className="otp-form" style={{ marginTop: '1rem' }}>
              <input type="text" placeholder="Full Name" value={userId} onChange={e => setUserId(e.target.value)} className="form-input" />
              <input type="text" placeholder="Phone Number (e.g. 01700000000)" value={phone} onChange={e => setPhone(e.target.value)} className="form-input" />
              <button className="btn-primary" onClick={handleHoldSeat}>Hold Selected Seats</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderOtp = () => (
    <div className="otp-view">
      <h2 className="section-title">Verify Phone Number</h2>
      <div className="booking-panel centered-panel fade-in">
        <div className="ticket-details">
          <div className="ticket-row"><span>Booking Ref</span><span>{bookingRefs.join(', ')}</span></div>
          <div className="ticket-row"><span>Seats</span><span>{heldSeatsList.map(s => `${s.row_label}${s.col_number}`).join(', ')}</span></div>
          <div className="ticket-row"><span>Movie</span><span>{selectedMovie?.title}</span></div>
        </div>
        {error && <div className="alert error" style={{marginTop:'1rem'}}>{error}</div>}
        <div className="otp-form" style={{marginTop:'1.5rem'}}>
          <p className="help-text" style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f59e0b' }}>
            Hold expires in: {holdTimeLeft !== null ? `${holdTimeLeft}s` : '—'}
          </p>
          <p className="help-text">Please enter the verification code. (Hint: Type anything, read the error message for the code, then type it in!)</p>
          <input type="text" className="form-input text-center" placeholder="Enter Code" value={otpCode} onChange={e => setOtpCode(e.target.value)} />
          <button className="btn-primary" onClick={handleVerifyOtp}>Verify & Continue</button>
          <button className="btn-back" style={{width: '100%', marginTop: '1rem'}} onClick={handleResendOtp}>Didn't receive it? Resend OTP</button>
          <button className="btn-danger" style={{width: '100%', marginTop: '0.5rem'}} onClick={handleCancelHold}>Cancel Hold</button>
        </div>
      </div>
    </div>
  );

  const renderPayment = () => (
    <div className="payment-processing fade-in">
      <div className="spinner"><div className="pulse-ring"></div></div>
      <h2 className="section-title">Processing Payment</h2>
      <p className="help-text">Booking Ref: {bookingRefs.join(', ')}</p>
      <p className="timer-text">Elapsed: {paymentTime}s</p>
      <p className="note-text">Please do not refresh this page.</p>
    </div>
  );

  const renderConfirmation = () => {
    const ok = paymentStatus?.status === 'SUCCEEDED';
    return (
      <div className={`confirmation-card ${ok ? 'success' : 'failed'} fade-in`}>
        <h2 className="confirmation-title">{ok ? 'Booking Confirmed' : 'Payment Failed'}</h2>
        <div className="ticket-details-box">
          <div className="ticket-row"><span>Booking Ref</span><span>{bookingRefs.join(', ')}</span></div>
          {ok && <>
            <div className="ticket-row"><span>Movie</span><span>{selectedMovie?.title}</span></div>
            <div className="ticket-row"><span>Seats</span><span>{heldSeatsList.map(s => `${s.row_label}${s.col_number}`).join(', ')}</span></div>
            <div className="ticket-row"><span>Total Amount</span><span>BDT {Number(paymentStatus?.amount || 0).toFixed(0)}</span></div>
          </>}
        </div>
        <button className="btn-primary" style={{marginTop:'2rem'}} onClick={resetBooking}>
          {ok ? 'Book Another Ticket' : 'Return Home'}
        </button>
      </div>
    );
  };

  return (
    <div className="app-container">
      <header className="header" onClick={resetBooking}>
        <h1 className="logo">CinemaSeat</h1>
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
