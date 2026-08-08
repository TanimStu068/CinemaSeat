import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USER_ID = "test-user-123";
const PHONE = "01700000000";

function App() {
  const [seats, setSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [bookingRef, setBookingRef] = useState(null);
  const [bookingStatus, setBookingStatus] = useState(null);
  const [otpCode, setOtpCode] = useState("");
  const [message, setMessage] = useState("");

  const fetchSeats = async () => {
    try {
      // Hardcoded showtime ID 1 for demonstration
      const res = await axios.get(`${API_URL}/showtimes/1/seats`);
      setSeats(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setMessage("Failed to load seats");
    }
  };

  useEffect(() => {
    fetchSeats();
    // Poll seats every 5 seconds to update availability
    const interval = setInterval(fetchSeats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Poll booking status
  useEffect(() => {
    let interval;
    if (bookingRef && !['SUCCEEDED', 'FAILED', 'REFUNDED'].includes(bookingStatus)) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}/booking/${bookingRef}/status`);
          setBookingStatus(res.data.status);
          if (res.data.status === 'SUCCEEDED') {
            setMessage("Booking Successful!");
            fetchSeats();
          } else if (res.data.status === 'FAILED') {
            setMessage("Booking Failed.");
            fetchSeats();
          }
        } catch (err) {
          console.error(err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [bookingRef, bookingStatus]);

  const handleSeatClick = async (seat) => {
    if (seat.status !== 'AVAILABLE') return;
    setMessage("");
    setSelectedSeat(seat);
    try {
      const res = await axios.post(`${API_URL}/seats/${seat.id}/hold`, {
        user_id: USER_ID,
        phone: PHONE
      });
      setBookingRef(res.data.booking_ref);
      setBookingStatus("PENDING");
      setMessage("Seat held! Sending OTP...");
      
      // Request OTP
      await axios.post(`${API_URL}/otp/send`, {
        phone: PHONE,
        ref: res.data.booking_ref
      });
    } catch (err) {
      if (err.response && err.response.status === 409) {
         setMessage("Sorry, this seat was just taken!");
         fetchSeats();
      } else {
         setMessage("Error holding seat");
      }
    }
  };

  const handleVerifyOtp = async () => {
    try {
      await axios.post(`${API_URL}/otp/verify`, {
        ref: bookingRef,
        code: otpCode
      });
      setMessage("OTP Verified. Initiating payment...");
      
      // Initiate charge
      await axios.post(`${API_URL}/charge`, {
        booking_ref: bookingRef
      });
      
    } catch (err) {
      setMessage("Invalid OTP or error verifying.");
    }
  };

  if (loading) return <div className="loader">Loading CinemaSeat...</div>;

  return (
    <div className="app-container">
      <header className="header">
        <h1>CinemaSeat</h1>
        <p>Spider-Man: Brand New Day - Midnight Premiere</p>
      </header>

      {message && <div className="alert">{message}</div>}

      <div className="main-content">
        <div className="screen-indicator">SCREEN</div>
        
        <div className="seating-chart">
          {seats.reduce((rows, seat) => {
            if (!rows[seat.row_label]) rows[seat.row_label] = [];
            rows[seat.row_label].push(seat);
            return rows;
          }, Object.create(null)) && Object.entries(
            seats.reduce((acc, seat) => {
              (acc[seat.row_label] = acc[seat.row_label] || []).push(seat);
              return acc;
            }, {})
          ).map(([rowLabel, rowSeats]) => (
            <div key={rowLabel} className="seat-row">
              <div className="row-label">{rowLabel}</div>
              {rowSeats.map(seat => (
                <button
                  key={seat.id}
                  className={`seat ${seat.status.toLowerCase()} ${selectedSeat?.id === seat.id ? 'selected' : ''}`}
                  onClick={() => handleSeatClick(seat)}
                  disabled={seat.status !== 'AVAILABLE'}
                >
                  {seat.col_number}
                </button>
              ))}
            </div>
          ))}
        </div>

        {bookingRef && bookingStatus && !['SUCCEEDED', 'FAILED'].includes(bookingStatus) && (
          <div className="booking-panel">
            <h2>Complete Your Booking</h2>
            <p>Booking Ref: {bookingRef}</p>
            <p>Status: <span className="status-badge">{bookingStatus}</span></p>

            {(bookingStatus === 'PENDING' || bookingStatus === 'OTP_SENT') && (
              <div className="otp-form">
                <input 
                  type="text" 
                  placeholder="Enter OTP (anything for mock)" 
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                />
                <button onClick={handleVerifyOtp}>Verify & Pay</button>
              </div>
            )}
            
            {bookingStatus === 'CHARGING' && (
              <div className="loading-spinner">Waiting for payment confirmation...</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
