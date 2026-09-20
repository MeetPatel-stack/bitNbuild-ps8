import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import api, { getWebSocketUrl } from './api'

const navItems = [
  ['home', 'Home'],
  ['trips', 'Trips'],
  ['activity', 'Concierge Activity'],
  ['online', 'Concierge Online'],
  ['profile', 'Profile'],
]

const sampleTrips = [
  {
    id: 'paris-demo',
    city: 'Paris',
    origin: 'DEL',
    destination: 'Paris',
    dates: '12–18 October 2026',
    status: 'DISRUPTED',
    caption: 'A change is already being handled.',
  },
  {
    id: 'london-demo',
    city: 'London',
    origin: 'DEL',
    destination: 'London',
    dates: '04–09 November 2026',
    status: 'CONFIRMED',
    caption: 'Everything is on schedule.',
  },
  {
    id: 'singapore-demo',
    city: 'Singapore',
    origin: 'DEL',
    destination: 'Singapore',
    dates: '20–26 December 2026',
    status: 'CONFIRMED',
    caption: 'Everything is on schedule.',
  },
]

const demoEvents = [
  ['DISRUPTION_DETECTED', 'Disruption detected', 'Your flight cancellation was identified.', 'done'],
  ['IMPACT_ANALYZED', 'Connection affected', 'The rest of your itinerary is being protected.', 'done'],
  ['FLIGHTS_SEARCHED', 'Searching alternative flights', 'In progress', 'current'],
  ['POLICY_CHECKED', 'Policy constraints checked', 'Waiting for the best option.', 'future'],
  ['REBOOKING_STARTED', 'Replacement flight selected', 'Waiting for confirmation.', 'future'],
  ['REBOOKING_CONFIRMED', 'Flight rebooked', 'Waiting for confirmation.', 'future'],
  ['HOTEL_UPDATE_CONFIRMED', 'Hotel reservation updated', 'Waiting for confirmation.', 'future'],
  ['NOTIFICATION_SENT', 'Traveler notified', 'Waiting for confirmation.', 'future'],
]

const feedback = [
  ['“Wayfinder handled my cancelled flight before I even had to call the airline.”', 'Traveler, Mumbai → Paris'],
  ['“Everything was updated automatically. I just followed the new itinerary.”', 'Traveler, Delhi → London'],
  ["“I didn't have to worry about my hotel after the flight changed.”", 'Traveler, Bengaluru → Singapore'],
]

const toStatus = (value) => {
  const v = String(value || '').toUpperCase()
  if (['DISRUPTED', 'CANCELLED', 'FAILED'].includes(v)) return 'disrupted'
  if (['CONFIRMED', 'NORMAL', 'RESOLVED', 'COMPLETED', 'SCHEDULED'].includes(v)) return 'confirmed'
  return 'tracking'
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })
        .format(date)
        .replace(',', ' ·')
}

const makeTrip = (trip) => {
  const tripId = trip.id || trip._id || 'unknown-trip'
  const first = trip.flights?.[0]
  const last = trip.flights?.[trip.flights.length - 1]
  const formatter = new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })

  return {
    id: tripId,
    city: trip.destination || trip.title?.split(' to ').pop() || 'Journey',
    origin: trip.origin || first?.origin || '—',
    destination: trip.destination || last?.destination || '—',
    dates:
      first?.departure_time && last?.arrival_time
        ? `${formatter.format(new Date(first.departure_time))} – ${formatter.format(new Date(last.arrival_time))}`
        : 'Travel dates confirmed',
    status: trip.status || 'CONFIRMED',
    caption:
      trip.status === 'DISRUPTED'
        ? 'A change is already being handled.'
        : trip.status === 'RESOLVED'
          ? 'Autonomous rebooking complete.'
          : 'Everything is on schedule.',
    raw: trip,
  }
}

function DotPattern() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return undefined
    const context = canvas.getContext('2d')
    const pointerCapable = window.matchMedia('(hover: hover) and (pointer: fine)').matches
    let frame = 0
    let width = 0
    let height = 0
    let pixelRatio = 1
    let pointer = null
    let intensity = 0
    let lastFrame = 0

    const draw = () => {
      context.clearRect(0, 0, width, height)
      const centerX = width / 2
      const centerY = height / 2
      const centerRadius = Math.hypot(centerX, centerY)
      const spacing = 24

      for (let y = 12; y < height; y += spacing) {
        for (let x = 12; x < width; x += spacing) {
          const centerFade = Math.max(0, 1 - Math.hypot(x - centerX, y - centerY) / centerRadius)
          let offsetX = 0
          let offsetY = 0
          if (pointer && intensity > 0) {
            const deltaX = x - pointer.x
            const deltaY = y - pointer.y
            const distance = Math.hypot(deltaX, deltaY)
            const radius = 121
            if (distance < radius && distance > 0.1) {
              const force = ((radius - distance) / radius) ** 2 * 4.31 * intensity
              offsetX = (deltaX / distance) * force
              offsetY = (deltaY / distance) * force
            }
          }
          context.fillStyle = `rgba(122, 155, 179, ${0.22 + centerFade * 0.33})`
          context.beginPath()
          context.arc(x + offsetX, y + offsetY, 1.2, 0, Math.PI * 2)
          context.fill()
        }
      }
    }

    const animate = (time) => {
      const delta = Math.min((time - lastFrame) / 16.67 || 1, 3)
      lastFrame = time
      intensity *= 0.9 ** delta
      draw()
      if (intensity > 0.012) frame = requestAnimationFrame(animate)
      else {
        intensity = 0
        frame = 0
        draw()
      }
    }

    const startAnimation = () => {
      if (!frame) {
        lastFrame = performance.now()
        frame = requestAnimationFrame(animate)
      }
    }

    const resize = () => {
      width = window.innerWidth
      height = window.innerHeight
      pixelRatio = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.round(width * pixelRatio)
      canvas.height = Math.round(height * pixelRatio)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
      draw()
    }

    const movePointer = (event) => {
      pointer = { x: event.clientX, y: event.clientY }
      intensity = 1
      startAnimation()
    }
    const clearPointer = () => {
      pointer = null
      intensity = Math.max(intensity, 0.55)
      startAnimation()
    }

    resize()
    window.addEventListener('resize', resize)
    if (pointerCapable) {
      window.addEventListener('pointermove', movePointer, { passive: true })
      window.addEventListener('pointerleave', clearPointer)
    }
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', movePointer)
      window.removeEventListener('pointerleave', clearPointer)
    }
  }, [])

  return <canvas ref={canvasRef} className="dot-pattern" aria-hidden="true" />
}

function App() {
  const [page, setPage] = useState(() => window.location.hash.slice(1) || 'home')
  const [menuOpen, setMenuOpen] = useState(false)
  const [tripFilter, setTripFilter] = useState('All')

  // Data & API states
  const [apiTrips, setApiTrips] = useState([])
  const [selectedTripId, setSelectedTripId] = useState(null)
  const [selectedTripDetails, setSelectedTripDetails] = useState(null)
  const [liveEvents, setLiveEvents] = useState([])
  const [connection, setConnection] = useState('connecting')
  const [actionMessage, setActionMessage] = useState({ text: '', type: 'info' })
  const [actionLoading, setActionLoading] = useState(false)
  const [loadingTrips, setLoadingTrips] = useState(true)

  const goTo = (next) => {
    window.location.hash = next
    setPage(next)
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    const onHash = () => setPage(window.location.hash.slice(1) || 'home')
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  // 1. Initial load of trips from backend via Axios
  const loadTrips = async () => {
    setLoadingTrips(true)
    try {
      const trips = await api.trips.fetchTrips()
      if (Array.isArray(trips) && trips.length > 0) {
        setApiTrips(trips)
      } else {
        // Auto-seed demo trip if backend DB is empty
        const seeded = await api.demo.seedDemoData()
        if (seeded?.trip) {
          setApiTrips([seeded.trip])
        }
      }
    } catch (err) {
      console.warn('Trips fetch error, using preview mode:', err)
      setConnection((prev) => (prev === 'online' ? prev : 'preview'))
    } finally {
      setLoadingTrips(false)
    }
  }

  useEffect(() => {
    loadTrips()
  }, [])

  // Active trip calculation
  const displayTrips = apiTrips.length ? apiTrips.map(makeTrip) : sampleTrips
  const activeTripSummary =
    (selectedTripId ? apiTrips.find((trip) => (trip.id || trip._id) === selectedTripId) : null) ||
    apiTrips.find((trip) => trip.status === 'DISRUPTED') ||
    apiTrips[0]

  const tripId = activeTripSummary?.id || activeTripSummary?._id

  // Full trip data for detailed views (combining summary and detailed backend response)
  const liveTrip = selectedTripDetails || activeTripSummary

  // 2. Fetch trip details, timeline, and connect WebSocket when tripId changes
  useEffect(() => {
    if (!tripId) return undefined
    let socket = null
    let mounted = true

    // Fetch detailed trip document (with hotels, traveler profile, and rebookings)
    api.trips
      .fetchTrip(tripId)
      .then((data) => {
        if (mounted && data) setSelectedTripDetails(data)
      })
      .catch((err) => {
        console.warn(`Could not load full trip ${tripId}:`, err)
      })

    // Fetch existing timeline events
    api.trips
      .fetchTripTimeline(tripId)
      .then((events) => {
        if (mounted && Array.isArray(events)) setLiveEvents(events)
      })
      .catch((err) => {
        console.warn(`Could not load timeline for ${tripId}:`, err)
      })

    // Connect WebSocket
    try {
      const wsUrl = getWebSocketUrl(`/ws/trips/${tripId}`)
      socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        if (mounted) setConnection('online')
      }

      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data)
          if (event.type !== 'CONNECTION_ESTABLISHED' && mounted) {
            setLiveEvents((prev) => {
              const alreadyExists = prev.some(
                (e) =>
                  (e.id && e.id === event.id) ||
                  (e.event_type === event.event_type && e.timestamp === event.timestamp),
              )
              return alreadyExists ? prev : [...prev, event]
            })

            // Refresh trip details if resolution or disruption updates occurred
            const eventType = event.event_type || event.type
            if (
              [
                'DISRUPTION_DETECTED',
                'REBOOKING_CONFIRMED',
                'HOTEL_UPDATE_CONFIRMED',
                'PROCESS_COMPLETED',
                'REBOOKING_STARTED',
              ].includes(eventType)
            ) {
              api.trips.fetchTrip(tripId).then((data) => {
                if (mounted && data) setSelectedTripDetails(data)
              }).catch(() => {})

              api.trips.fetchTrips().then((trips) => {
                if (mounted && Array.isArray(trips)) setApiTrips(trips)
              }).catch(() => {})
            }
          }
        } catch {
          /* ignore heartbeats */
        }
      }

      socket.onclose = () => {
        if (mounted) setConnection((old) => (old === 'online' ? 'offline' : old))
      }

      socket.onerror = () => {
        if (mounted && connection !== 'online') setConnection('preview')
      }
    } catch {
      if (mounted) setConnection('preview')
    }

    return () => {
      mounted = false
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [tripId])

  // Timeline representation
  const timeline = useMemo(() => {
    if (!liveEvents.length) {
      return demoEvents.map(([event_type, title, description, state]) => ({
        event_type,
        title,
        description,
        state,
      }))
    }
    const received = new Map(liveEvents.map((event) => [event.event_type || event.type, event]))
    const active = demoEvents.find(([type]) => !received.has(type))?.[0]

    return demoEvents.map(([event_type, title, description]) => {
      const event = received.get(event_type)
      return {
        event_type,
        title: event?.title || title,
        description: event?.description || description,
        state: event ? 'done' : event_type === active ? 'current' : 'future',
      }
    })
  }, [liveEvents])

  // 3. Trigger flight cancellation simulation via Axios
  const simulateCancellation = async () => {
    const flight = liveTrip?.flights?.find((item) => item.status !== 'CANCELLED')
    if (!liveTrip || !flight) {
      setActionMessage({
        text: 'No active flight available to cancel for this journey. Reset the journey to test again.',
        type: 'error',
      })
      return
    }

    setActionLoading(true)
    setActionMessage({
      text: `Simulating cancellation for flight ${flight.flight_number || flight.flight_id}…`,
      type: 'info',
    })

    try {
      const response = await api.disruptions.simulateFlightCancellation({
        tripId: liveTrip.id || liveTrip._id,
        flightId: flight.flight_id,
        reason: 'Air traffic control ground stop at departure airport',
      })

      setActionMessage({
        text:
          response?.message ||
          'Cancellation registered. Autonomous concierge worker dispatched.',
        type: 'info',
      })

      // Immediately refresh trip state
      const targetId = liveTrip.id || liveTrip._id
      const updated = await api.trips.fetchTrip(targetId)
      if (updated) setSelectedTripDetails(updated)

      const trips = await api.trips.fetchTrips()
      if (Array.isArray(trips)) setApiTrips(trips)
    } catch (err) {
      console.error('Simulation failed:', err)
      setActionMessage({
        text: `Simulation failed: ${err.message}. Ensure backend is running on ${api.API_BASE_URL}.`,
        type: 'error',
      })
    } finally {
      setActionLoading(false)
    }
  }

  // 4. Reset Demo Trip via Axios
  const handleResetDemo = async () => {
    setActionLoading(true)
    setActionMessage({
      text: 'Resetting demo journey (AMD → DEL → LHR) to scheduled state…',
      type: 'info',
    })

    try {
      await api.demo.seedDemoData()
      const trips = await api.trips.fetchTrips()
      if (Array.isArray(trips)) setApiTrips(trips)

      const demoId = 'demo-trip-amd-lhr'
      setSelectedTripId(demoId)

      const refreshed = await api.trips.fetchTrip(demoId)
      if (refreshed) setSelectedTripDetails(refreshed)

      const freshTimeline = await api.trips.fetchTripTimeline(demoId)
      setLiveEvents(Array.isArray(freshTimeline) ? freshTimeline : [])

      setActionMessage({
        text: 'Journey reset successfully: Flights restored to scheduled, timeline cleared.',
        type: 'info',
      })
    } catch (err) {
      console.error('Reset error:', err)
      setActionMessage({
        text: `Failed to reset journey: ${err.message}`,
        type: 'error',
      })
    } finally {
      setActionLoading(false)
    }
  }

  const handleSelectTrip = (id) => {
    setSelectedTripId(id)
    goTo('activity')
  }

  return (
    <main className="site-shell">
      <DotPattern />
      <div className="top-glow" />
      <Header {...{ page, goTo, menuOpen, setMenuOpen, connection }} />

      {page === 'home' && <Home goTo={goTo} activeTrip={liveTrip} />}
      {page === 'trips' && (
        <Trips
          trips={displayTrips}
          filter={tripFilter}
          setFilter={setTripFilter}
          onSelectTrip={handleSelectTrip}
          loading={loadingTrips}
        />
      )}
      {page === 'activity' && (
        <Activity
          {...{
            liveTrip,
            timeline,
            connection,
            actionMessage,
            actionLoading,
            onSimulate: simulateCancellation,
            onResetDemo: handleResetDemo,
          }}
        />
      )}
      {page === 'online' && (
        <Online
          connection={connection}
          goTo={goTo}
          trips={displayTrips}
        />
      )}
      {page === 'profile' && <Profile user={liveTrip?.traveler} />}

      <footer>
        <span>© Wayfinder</span>
        <span>Autonomous travel care, thoughtfully handled.</span>
      </footer>
    </main>
  )
}

function Header({ page, goTo, menuOpen, setMenuOpen, connection }) {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const updateScrollState = () => setIsScrolled(window.scrollY > 18)
    updateScrollState()
    window.addEventListener('scroll', updateScrollState, { passive: true })
    return () => window.removeEventListener('scroll', updateScrollState)
  }, [])

  return (
    <header className={`nav-wrap ${isScrolled ? 'is-scrolled' : ''}`}>
      <nav className="navbar" aria-label="Primary navigation">
        <button className="brand" onClick={() => goTo('home')}>
          <span className="brand-mark">W</span>
          <span>Wayfinder</span>
        </button>
        <div className="nav-links">
          {navItems.map(([key, label]) => (
            <button
              className={page === key ? 'active' : ''}
              onClick={() => goTo(key)}
              key={key}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="nav-status">
          <i className={connection === 'online' ? 'pulse' : ''} />{' '}
          {connection === 'online' ? 'Concierge Live' : 'Concierge'}
        </div>
        <button
          className="menu-button"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          <span />
          <span />
          <span />
        </button>
      </nav>
      {menuOpen && (
        <div className="mobile-menu">
          {navItems.map(([key, label]) => (
            <button
              className={page === key ? 'active' : ''}
              onClick={() => goTo(key)}
              key={key}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </header>
  )
}

const Eyebrow = ({ children }) => <p className="eyebrow">{children}</p>
const Status = ({ value }) => <span className={`status ${toStatus(value)}`}><b>●</b> {value}</span>
const ArrowLink = ({ children, onClick }) => (
  <button className="arrow-link" onClick={onClick}>
    {children} <span>→</span>
  </button>
)

function Home({ goTo, activeTrip }) {
  const firstFlight = activeTrip?.flights?.[0]
  const origin = activeTrip?.origin || firstFlight?.origin || 'DEL'
  const destination = activeTrip?.destination || firstFlight?.destination || 'CDG'
  const flightNo = firstFlight?.flight_number || 'AI 141'

  return (
    <>
      <section className="hero-section container">
        <div className="hero-copy">
          <Eyebrow>
            <span className="soft-dot" /> Autonomous travel care
          </Eyebrow>
          <h1>
            Your journey,<br />
            <em>already handled.</em>
          </h1>
          <p className="lead">
            Every reservation, every connection, and every unexpected turn — kept in one calm, clear view.
          </p>
          <button className="primary-button" onClick={() => goTo('trips')}>
            Get Started <span>→</span>
          </button>
        </div>

        <div className="hero-card">
          <div className="hero-card-top">
            <span className="chip tracking"><b>●</b> Concierge tracking</span>
            <span className="muted">Live Protection</span>
          </div>
          <div className="route">
            <div>
              <small>{origin}</small>
              <strong>{activeTrip?.city || origin}</strong>
            </div>
            <div className="route-line">
              <i />
              <span>{flightNo}</span>
              <i />
            </div>
            <div>
              <small>{destination}</small>
              <strong>{activeTrip?.destination || destination}</strong>
            </div>
          </div>
          <div className="hero-card-note">
            <span className="mini-check">✓</span>
            <div>
              <b>We’re already protecting your trip</b>
              <p>Alternative routes and your hotel are being checked in real time.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="feedback-section">
        <div className="container">
          <div className="section-heading">
            <div>
              <Eyebrow>Traveler feedback</Eyebrow>
              <h2>Travel plans feel lighter<br />when someone’s on it.</h2>
            </div>
            <p>Demo feedback from Wayfinder’s sample journey flow.</p>
          </div>
          <div className="feedback-rail">
            {[...feedback, ...feedback].map(([quote, person], index) => (
              <article className="feedback-card" key={index}>
                <span className="quote-mark">“</span>
                <blockquote>{quote}</blockquote>
                <p>— {person}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="home-cta container">
        <div>
          <Eyebrow>Calm, even when plans change</Eyebrow>
          <h2>One clear place for<br />every next step.</h2>
        </div>
        <ArrowLink onClick={() => goTo('activity')}>See concierge activity</ArrowLink>
      </section>
    </>
  )
}

function Trips({ trips, filter, setFilter, onSelectTrip, loading }) {
  const filtered = trips.filter(
    (trip) =>
      filter === 'All' ||
      (filter === 'Active'
        ? trip.status === 'DISRUPTED'
        : filter === 'Upcoming'
          ? trip.status === 'CONFIRMED' || trip.status === 'SCHEDULED'
          : trip.status === 'COMPLETED' || trip.status === 'RESOLVED'),
  )

  return (
    <section className="page container trips-page">
      <div className="page-heading">
        <div>
          <Eyebrow>Wayfinder journeys</Eyebrow>
          <h1>Your trips</h1>
        </div>
        <p>A quiet overview of where you’re headed and what is being cared for.</p>
      </div>

      <div className="filters">
        {['All', 'Upcoming', 'Active', 'Completed'].map((item) => (
          <button
            className={filter === item ? 'selected' : ''}
            onClick={() => setFilter(item)}
            key={item}
          >
            {item}
          </button>
        ))}
      </div>

      {loading && trips.length === 0 ? (
        <div className="empty-state">Loading your journeys from the concierge…</div>
      ) : (
        <div className="trip-grid">
          {filtered.map((trip) => (
            <article className={`trip-card ${toStatus(trip.status)}`} key={trip.id}>
              <div className="trip-card-head">
                <Eyebrow>Current journey</Eyebrow>
                <Status value={trip.status} />
              </div>
              <h2>{trip.city}</h2>
              <p className="trip-caption">{trip.caption}</p>
              <div className="trip-route">
                <div>
                  <small>{trip.origin}</small>
                  <span>Origin</span>
                </div>
                <div className="travel-stroke">
                  <i /> <b>✦</b> <i />
                </div>
                <div>
                  <small>{trip.destination}</small>
                  <span>Destination</span>
                </div>
              </div>
              <div className="trip-card-foot">
                <span>{trip.dates}</span>
                <ArrowLink onClick={() => onSelectTrip(trip.id)}>View trip</ArrowLink>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

const InfoCard = ({ label, children, className = '' }) => (
  <section className={`info-card ${className}`}>
    <Eyebrow>{label}</Eyebrow>
    {children}
  </section>
)

function Activity({
  liveTrip,
  timeline,
  connection,
  actionMessage,
  actionLoading,
  onSimulate,
  onResetDemo,
}) {
  const flights = liveTrip?.flights || []
  const primaryFlight = flights[0]
  const hotel = liveTrip?.hotels?.[0]
  const status = liveTrip?.status || 'CONFIRMED'
  const rebooking = liveTrip?.rebookings?.[0]

  // Traveler dynamic information
  const travelerName = liveTrip?.traveler?.name || 'Priya Sharma'
  const loyaltyTier = liveTrip?.traveler?.loyalty_tier || 'Priority'
  const travelerAvatar = travelerName.charAt(0)

  return (
    <section className="page container activity-page">
      <div className="page-heading activity-heading">
        <div>
          <Eyebrow>Autonomous travel care</Eyebrow>
          <h1>Concierge activity</h1>
        </div>
        <span className={`connection ${connection}`}>
          <i />{' '}
          {connection === 'online'
            ? 'Live activity connected'
            : connection === 'preview'
              ? 'Demo preview'
              : 'Connecting'}
        </span>
      </div>

      <div className="activity-layout">
        <aside className="activity-aside">
          <InfoCard label="Traveler">
            <div className="person">
              <span className="avatar">{travelerAvatar}</span>
              <div>
                <h3>{travelerName}</h3>
                <p>Wayfinder {loyaltyTier} member</p>
              </div>
            </div>
          </InfoCard>

          <InfoCard label="Current journey">
            <Status value={status} />
            <div className="compact-route">
              <strong>{liveTrip?.origin || 'AMD'}</strong>
              <span>⟶</span>
              <strong>{liveTrip?.destination || 'LHR'}</strong>
            </div>
            <p>{liveTrip?.title || 'Ahmedabad to London Journey'}</p>
          </InfoCard>

          <InfoCard label="Stay">
            <span className="small-status">{hotel?.status || 'CONFIRMED'}</span>
            <h3>{hotel?.hotel_name || 'The Langham, London'}</h3>
            <p>{hotel?.city || 'London'}, {hotel?.address?.split(',').pop() || 'United Kingdom'}</p>
            <div className="stay-times">
              <span>
                Check in <b>{formatDate(hotel?.check_in) || 'Scheduled'}</b>
              </span>
              <span>
                Check out <b>{formatDate(hotel?.check_out) || 'Scheduled'}</b>
              </span>
            </div>
          </InfoCard>

          <InfoCard label="Final resolution" className="resolution-card">
            {rebooking ? (
              <div className="resolution-filled">
                <div className="resolution-badge">✓ Rebooked Autonomously</div>
                <div className="resolution-details">
                  <div className="resolution-row">
                    <span>Replacement Flight</span>
                    <strong>
                      {rebooking.new_flights?.[0]?.airline || rebooking.airline || 'Air India'}{' '}
                      {rebooking.new_flights?.[0]?.flight_number || ''}
                    </strong>
                  </div>
                  <div className="resolution-row">
                    <span>Booking Ref</span>
                    <strong>{rebooking.booking_reference || 'AUT-CONFIRMED'}</strong>
                  </div>
                  <div className="resolution-row">
                    <span>Fare Difference</span>
                    <strong style={{ color: '#2c7047' }}>₹{rebooking.cost_difference || 0} (Waiver)</strong>
                  </div>
                  <div className="resolution-row">
                    <span>Status</span>
                    <strong style={{ color: '#2c7047' }}>{rebooking.status || 'CONFIRMED'}</strong>
                  </div>
                </div>
                <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: '10px' }}>
                  {rebooking.policy_compliance_notes || 'All alternative flights secured under airline disruption policy.'}
                </p>
              </div>
            ) : (
              <div className="resolution-empty">
                <span>✦</span>
                <div>
                  <h3>We’ll place your confirmed itinerary here.</h3>
                  <p>
                    When the resolution is complete, you’ll see the new flight, arrival time,
                    fare difference, hotel change, and confirmation details.
                  </p>
                </div>
              </div>
            )}
          </InfoCard>
        </aside>

        <div className="activity-main">
          <InfoCard label="Flight itinerary" className="flight-card">
            {flights.length > 0 ? (
              flights.map((fl, idx) => (
                <div
                  key={fl.flight_id || idx}
                  style={{
                    marginBottom: idx < flights.length - 1 ? '24px' : 0,
                    paddingBottom: idx < flights.length - 1 ? '20px' : 0,
                    borderBottom: idx < flights.length - 1 ? '1px dashed #e2edf5' : 'none',
                  }}
                >
                  <div className="flight-title">
                    <Status
                      value={
                        fl.status === 'CANCELLED'
                          ? 'DISRUPTED'
                          : fl.status === 'REBOOKED'
                            ? 'RESOLVED'
                            : fl.status || status
                      }
                    />
                    <span>
                      {fl.airline || 'Air India'} · {fl.flight_number || 'AI 401'} (Segment {idx + 1})
                    </span>
                  </div>
                  <div className="flight-route">
                    <div>
                      <small>{fl.origin || 'AMD'}</small>
                      <b>{formatDate(fl.departure_time) || 'Departure'}</b>
                    </div>
                    <div>
                      <em>{fl.flight_number || 'AI 401'}</em>
                      <i />
                    </div>
                    <div>
                      <small>{fl.destination || 'DEL'}</small>
                      <b>{formatDate(fl.arrival_time) || 'Arrival'}</b>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div>
                <div className="flight-title">
                  <Status value={primaryFlight?.status === 'CANCELLED' ? 'DISRUPTED' : status} />
                  <span>{primaryFlight?.airline || 'Air India'} · Original flight</span>
                </div>
                <div className="flight-route">
                  <div>
                    <small>{primaryFlight?.origin || 'AMD'}</small>
                    <b>{formatDate(primaryFlight?.departure_time) || '12 Oct · 01:45'}</b>
                  </div>
                  <div>
                    <em>{primaryFlight?.flight_number || 'AI 401'}</em>
                    <i />
                  </div>
                  <div>
                    <small>{primaryFlight?.destination || 'DEL'}</small>
                    <b>{formatDate(primaryFlight?.arrival_time) || '12 Oct · 08:05'}</b>
                  </div>
                </div>
              </div>
            )}
          </InfoCard>

          <div className="status-impact">
            <InfoCard label="Disruption status" className="disruption-card">
              <Status value={status === 'RESOLVED' ? 'CONFIRMED' : status === 'DISRUPTED' ? 'DISRUPTED' : 'NORMAL'} />
              <h2>
                {status === 'RESOLVED'
                  ? 'Your journey is resolved.'
                  : status === 'DISRUPTED'
                    ? 'Your concierge is on it.'
                    : 'Your journey is on schedule.'}
              </h2>
              <p>
                {status === 'RESOLVED'
                  ? 'New flights and hotel accommodations have been successfully secured.'
                  : status === 'DISRUPTED'
                    ? 'Scheduled flight cancellation detected. Wayfinder is coordinating replacement connections and hotel stays.'
                    : 'Wayfinder is actively monitoring weather, flight radar, and connecting gates.'}
              </p>
              <span className="monitoring">
                <i className="pulse" /> Concierge monitoring
              </span>
            </InfoCard>

            <InfoCard label="Trip impact" className="impact-card">
              <dl>
                <div>
                  <dt>Flight status</dt>
                  <dd>{status === 'DISRUPTED' ? 'Disrupted' : status === 'RESOLVED' ? 'Rebooked' : 'On Time'}</dd>
                </div>
                <div>
                  <dt>Connection</dt>
                  <dd>{status === 'DISRUPTED' ? 'Protected' : status === 'RESOLVED' ? 'Restored' : 'Guaranteed'}</dd>
                </div>
                <div>
                  <dt>Hotel Stay</dt>
                  <dd>{hotel?.status === 'MODIFIED' ? 'Check-in adjusted' : 'Synced'}</dd>
                </div>
                <div>
                  <dt>Additional cost</dt>
                  <dd>₹0 (Waived)</dd>
                </div>
                <div>
                  <dt>Concierge Action</dt>
                  <dd>{status === 'RESOLVED' ? 'Completed' : status === 'DISRUPTED' ? 'Active' : 'Standby'}</dd>
                </div>
              </dl>
            </InfoCard>
          </div>

          <InfoCard label="Concierge activity" className="timeline-card">
            <div className="timeline-heading">
              <div>
                <h2>Resolution in motion</h2>
                <p>Each decision is coordinated against your itinerary and travel preferences.</p>
              </div>
              <div className="timeline-controls">
                <button
                  className="outline-button primary-action"
                  onClick={onSimulate}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Executing…' : 'Simulate cancellation'}
                </button>
                <button
                  className="outline-button"
                  onClick={onResetDemo}
                  disabled={actionLoading}
                  title="Reset trip and timeline in backend"
                >
                  Reset Journey
                </button>
              </div>
            </div>

            <ol className="timeline">
              {timeline.map((event) => (
                <li className={event.state} key={event.event_type}>
                  <span className="timeline-marker">
                    {event.state === 'done' ? '✓' : event.state === 'current' ? '●' : '○'}
                  </span>
                  <div>
                    <b>{event.title}</b>
                    <p>{event.description}</p>
                    <code>{event.event_type}</code>
                  </div>
                </li>
              ))}
            </ol>

            {actionMessage?.text && (
              <p className={`action-message ${actionMessage.type === 'error' ? 'error' : ''}`}>
                {actionMessage.text}
              </p>
            )}
          </InfoCard>
        </div>
      </div>
    </section>
  )
}

function Online({ goTo, trips }) {
  const monitoredTrips = trips.length > 0 ? trips : sampleTrips

  return (
    <section className="page container online-page">
      <div className="page-heading">
        <div>
          <Eyebrow>Monitoring now</Eyebrow>
          <h2>{monitoredTrips.length} trips being monitored</h2>
        </div>
      </div>

      <div className="trip-grid">
        {monitoredTrips.map((trip) => (
          <article className={`trip-card ${toStatus(trip.status)}`} key={trip.id}>
            <div className="trip-card-head">
              <Eyebrow>Monitored journey</Eyebrow>
              <span className={`status ${toStatus(trip.status)}`}>
                <b>●</b> {trip.status}
              </span>
            </div>
            <h2>{trip.origin} → {trip.destination}</h2>
            <p className="trip-caption">{trip.dates}</p>
            <div className="trip-card-foot">
              <span>{trip.caption}</span>
              <span className={`status ${toStatus(trip.status)}`}>
                <b>●</b> {trip.status === 'DISRUPTED' ? 'ALERT' : 'ACTIVE'}
              </span>
            </div>
          </article>
        ))}
      </div>

      <div className="page-heading">
        <div>
          <Eyebrow>What Wayfinder watches</Eyebrow>
          <h2>Every detail around the journey.</h2>
        </div>
      </div>

      <div className="trip-grid">
        {['✈ Flight status', '⇄ Connections', '✓ Policy checks', '🏨 Hotel reservations'].map((item) => (
          <section className="info-card" key={item}>
            <h3>{item}</h3>
          </section>
        ))}
      </div>

      <InfoCard label="Ready to act">
        <h2>
          Detect → Analyze → Search → Rebook<br />
          → Update → Notify
        </h2>
      </InfoCard>

      <InfoCard label="Recent activity" className="timeline-card">
        <ol className="timeline">
          <li className="done">
            <span className="timeline-marker">✓</span>
            <div><b>Journey monitored via airline telematics</b></div>
          </li>
          <li className="done">
            <span className="timeline-marker">✓</span>
            <div><b>Connection risk matrix calculated</b></div>
          </li>
          <li className="current">
            <span className="timeline-marker">●</span>
            <div><b>Automated concierge standby enabled</b></div>
          </li>
        </ol>
        <ArrowLink onClick={() => goTo('activity')}>View activity</ArrowLink>
      </InfoCard>
    </section>
  )
}

function Profile({ user }) {
  const name = user?.name || 'Priya Sharma'
  const email = user?.email || 'priya.sharma@example.com'
  const phone = user?.phone || '+91-98765-43210'
  const tier = user?.loyalty_tier || 'Gold'
  const initial = name.charAt(0)

  return (
    <section className="page container profile-page">
      <div className="profile-card">
        <span className="profile-avatar">{initial}</span>
        <Eyebrow>Traveler Profile</Eyebrow>
        <h1>{name}</h1>
        <p className="member">Wayfinder {tier} member</p>
        <div className="profile-divider" />
        <div className="profile-detail">
          <span>Travel care status</span>
          <b>Autonomous concierge enabled</b>
        </div>
        <div className="profile-detail">
          <span>Email</span>
          <b>{email}</b>
        </div>
        <div className="profile-detail">
          <span>Contact phone</span>
          <b>{phone}</b>
        </div>
        {user?.preferences?.meal && (
          <div className="profile-detail">
            <span>Meal preference</span>
            <b>{user.preferences.meal}</b>
          </div>
        )}
        {user?.preferences?.seat && (
          <div className="profile-detail">
            <span>Seat preference</span>
            <b>{user.preferences.seat.toUpperCase()}</b>
          </div>
        )}
      </div>
    </section>
  )
}

export default App
