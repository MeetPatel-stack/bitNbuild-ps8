import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const navItems = [['home', 'Home'], ['trips', 'Trips'], ['activity', 'Concierge Activity'], ['online', 'Concierge Online'], ['profile', 'Profile']]
const sampleTrips = [
  { id: 'paris-demo', city: 'Paris', origin: 'DEL', destination: 'Paris', dates: '12–18 October 2026', status: 'DISRUPTED', caption: 'A change is already being handled.' },
  { id: 'london-demo', city: 'London', origin: 'DEL', destination: 'London', dates: '04–09 November 2026', status: 'CONFIRMED', caption: 'Everything is on schedule.' },
  { id: 'singapore-demo', city: 'Singapore', origin: 'DEL', destination: 'Singapore', dates: '20–26 December 2026', status: 'CONFIRMED', caption: 'Everything is on schedule.' },
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
const feedback = [['“Wayfinder handled my cancelled flight before I even had to call the airline.”', 'Traveler, Mumbai → Paris'], ['“Everything was updated automatically. I just followed the new itinerary.”', 'Traveler, Delhi → London'], ["“I didn't have to worry about my hotel after the flight changed.”", 'Traveler, Bengaluru → Singapore']]

const toStatus = (value) => {
  const v = String(value || '').toUpperCase()
  if (['DISRUPTED', 'CANCELLED', 'FAILED'].includes(v)) return 'disrupted'
  if (['CONFIRMED', 'NORMAL', 'RESOLVED', 'COMPLETED', 'SCHEDULED'].includes(v)) return 'confirmed'
  return 'tracking'
}
const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false }).format(date).replace(',', ' ·')
}
const makeTrip = (trip) => {
  const first = trip.flights?.[0]; const last = trip.flights?.[trip.flights.length - 1]
  const formatter = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  return { id: trip.id, city: trip.destination || trip.title?.split(' to ').pop() || 'Journey', origin: trip.origin || first?.origin || '—', destination: trip.destination || last?.destination || '—', dates: first?.departure_time && last?.arrival_time ? `${formatter.format(new Date(first.departure_time))} – ${formatter.format(new Date(last.arrival_time))}` : 'Travel dates to be confirmed', status: trip.status || 'CONFIRMED', caption: trip.status === 'DISRUPTED' ? 'A change is already being handled.' : 'Everything is on schedule.', raw: trip }
}

function DotPattern() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
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
      else { intensity = 0; frame = 0; draw() }
    }

    const startAnimation = () => {
      if (!frame) { lastFrame = performance.now(); frame = requestAnimationFrame(animate) }
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
    const clearPointer = () => { pointer = null; intensity = Math.max(intensity, 0.55); startAnimation() }

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
  const [menuOpen, setMenuOpen] = useState(false); const [tripFilter, setTripFilter] = useState('All')
  const [apiTrips, setApiTrips] = useState([]); const [liveEvents, setLiveEvents] = useState([]); const [connection, setConnection] = useState('connecting'); const [actionMessage, setActionMessage] = useState('')
  const displayTrips = apiTrips.length ? apiTrips.map(makeTrip) : sampleTrips
  const liveTrip = apiTrips.find((trip) => trip.status === 'DISRUPTED') || apiTrips[0]; const tripId = liveTrip?.id
  const goTo = (next) => { window.location.hash = next; setPage(next); setMenuOpen(false); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  useEffect(() => { const onHash = () => setPage(window.location.hash.slice(1) || 'home'); window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash) }, [])
  useEffect(() => { let mounted = true; fetch(`${API_URL}/api/trips`).then((r) => r.ok ? r.json() : Promise.reject()).then((trips) => { if (mounted) setApiTrips(Array.isArray(trips) ? trips : []) }).catch(() => { if (mounted) setConnection('preview') }); return () => { mounted = false } }, [])
  useEffect(() => {
    if (!tripId) return undefined
    let socket; let mounted = true
    fetch(`${API_URL}/api/trips/${tripId}/timeline`).then((r) => r.ok ? r.json() : []).then((events) => { if (mounted && Array.isArray(events)) setLiveEvents(events) }).catch(() => {})
    try { socket = new WebSocket(API_URL.replace(/^http/, 'ws') + `/ws/trips/${tripId}`); socket.onopen = () => { if (mounted) setConnection('online') }; socket.onmessage = (message) => { try { const event = JSON.parse(message.data); if (event.type !== 'CONNECTION_ESTABLISHED' && mounted) setLiveEvents((events) => [...events, event]) } catch { /* ignore heartbeats */ } }; socket.onclose = () => { if (mounted) setConnection((old) => old === 'online' ? 'offline' : old) } } catch { setConnection('preview') }
    return () => { mounted = false; socket?.close() }
  }, [tripId])
  const timeline = useMemo(() => {
    if (!liveEvents.length) return demoEvents.map(([event_type, title, description, state]) => ({ event_type, title, description, state }))
    const received = new Map(liveEvents.map((event) => [event.event_type || event.type, event])); const active = demoEvents.find(([type]) => !received.has(type))?.[0]
    return demoEvents.map(([event_type, title, description]) => { const event = received.get(event_type); return { event_type, title: event?.title || title, description: event?.description || description, state: event ? 'done' : event_type === active ? 'current' : 'future' } })
  }, [liveEvents])
  const simulateCancellation = async () => {
    const flight = liveTrip?.flights?.find((item) => item.status !== 'CANCELLED')
    if (!liveTrip || !flight) { setActionMessage('Connect the Wayfinder backend to run a live cancellation simulation.'); return }
    setActionMessage('Starting flight-cancellation simulation…')
    try { const r = await fetch(`${API_URL}/api/simulations/flight-cancellation`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ trip_id: liveTrip.id, flight_id: flight.flight_id, reason: 'Demo flight cancellation' }) }); if (!r.ok) throw new Error(); setActionMessage('Simulation started. Live progress will appear in the timeline.') } catch { setActionMessage('The simulation could not be started. Please check that the backend is running.') }
  }
  return <main className="site-shell"><DotPattern /><div className="top-glow" /><Header {...{ page, goTo, menuOpen, setMenuOpen, connection }} />{page === 'home' && <Home goTo={goTo} />}{page === 'trips' && <Trips trips={displayTrips} filter={tripFilter} setFilter={setTripFilter} goTo={goTo} />}{page === 'activity' && <Activity {...{ liveTrip, timeline, connection, actionMessage, onSimulate: simulateCancellation }} />}{page === 'online' && <Online connection={connection} goTo={goTo} />}{page === 'profile' && <Profile />}<footer><span>© Wayfinder</span><span>Autonomous travel care, thoughtfully handled.</span></footer></main>
}

function Header({ page, goTo, menuOpen, setMenuOpen, connection }) {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const updateScrollState = () => setIsScrolled(window.scrollY > 18)
    updateScrollState()
    window.addEventListener('scroll', updateScrollState, { passive: true })
    return () => window.removeEventListener('scroll', updateScrollState)
  }, [])

  return <header className={`nav-wrap ${isScrolled ? 'is-scrolled' : ''}`}><nav className="navbar" aria-label="Primary navigation"><button className="brand" onClick={() => goTo('home')}><span className="brand-mark">W</span><span>Wayfinder</span></button><div className="nav-links">{navItems.map(([key, label]) => <button className={page === key ? 'active' : ''} onClick={() => goTo(key)} key={key}>{label}</button>)}</div><div className="nav-status"><i className={connection === 'online' ? 'pulse' : ''} /> Concierge</div><button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation"><span /><span /><span /></button></nav>{menuOpen && <div className="mobile-menu">{navItems.map(([key, label]) => <button className={page === key ? 'active' : ''} onClick={() => goTo(key)} key={key}>{label}</button>)}</div>}</header>
}
const Eyebrow = ({ children }) => <p className="eyebrow">{children}</p>
const Status = ({ value }) => <span className={`status ${toStatus(value)}`}><b>●</b> {value}</span>
const ArrowLink = ({ children, onClick }) => <button className="arrow-link" onClick={onClick}>{children} <span>→</span></button>

function Home({ goTo }) { return <><section className="hero-section container"><div className="hero-copy"><Eyebrow><span className="soft-dot" /> Autonomous travel care</Eyebrow><h1>Your journey,<br /><em>already handled.</em></h1><p className="lead">Every reservation, every connection, and every unexpected turn — kept in one calm, clear view.</p><button className="primary-button" onClick={() => goTo('trips')}>Get Started <span>→</span></button></div><div className="hero-card"><div className="hero-card-top"><span className="chip tracking"><b>●</b> Concierge tracking</span><span className="muted">12 Oct 2026</span></div><div className="route"><div><small>DEL</small><strong>Delhi</strong></div><div className="route-line"><i /><span>AI 141</span><i /></div><div><small>CDG</small><strong>Paris</strong></div></div><div className="hero-card-note"><span className="mini-check">✓</span><div><b>We’re already protecting your trip</b><p>Alternative routes and your hotel are being checked.</p></div></div></div></section><section className="feedback-section"><div className="container"><div className="section-heading"><div><Eyebrow>Traveler feedback</Eyebrow><h2>Travel plans feel lighter<br />when someone’s on it.</h2></div><p>Demo feedback from Wayfinder’s sample journey flow.</p></div><div className="feedback-rail">{[...feedback, ...feedback].map(([quote, person], index) => <article className="feedback-card" key={index}><span className="quote-mark">“</span><blockquote>{quote}</blockquote><p>— {person}</p></article>)}</div></div></section><section className="home-cta container"><div><Eyebrow>Calm, even when plans change</Eyebrow><h2>One clear place for<br />every next step.</h2></div><ArrowLink onClick={() => goTo('activity')}>See concierge activity</ArrowLink></section></> }

function Trips({ trips, filter, setFilter, goTo }) { const filtered = trips.filter((trip) => filter === 'All' || (filter === 'Active' ? trip.status === 'DISRUPTED' : filter === 'Upcoming' ? trip.status === 'CONFIRMED' : trip.status === 'COMPLETED')); return <section className="page container trips-page"><div className="page-heading"><div><Eyebrow>Wayfinder journeys</Eyebrow><h1>Your trips</h1></div><p>A quiet overview of where you’re headed and what is being cared for.</p></div><div className="filters">{['All', 'Upcoming', 'Active', 'Completed'].map((item) => <button className={filter === item ? 'selected' : ''} onClick={() => setFilter(item)} key={item}>{item}</button>)}</div><div className="trip-grid">{filtered.map((trip) => <article className={`trip-card ${toStatus(trip.status)}`} key={trip.id}><div className="trip-card-head"><Eyebrow>Current journey</Eyebrow><Status value={trip.status} /></div><h2>{trip.city}</h2><p className="trip-caption">{trip.caption}</p><div className="trip-route"><div><small>{trip.origin}</small><span>Origin</span></div><div className="travel-stroke"><i /> <b>✦</b> <i /></div><div><small>{trip.destination}</small><span>Destination</span></div></div><div className="trip-card-foot"><span>{trip.dates}</span><ArrowLink onClick={() => goTo('activity')}>View trip</ArrowLink></div></article>)}</div></section> }
const InfoCard = ({ label, children, className = '' }) => <section className={`info-card ${className}`}><Eyebrow>{label}</Eyebrow>{children}</section>

function Activity({ liveTrip, timeline, connection, actionMessage, onSimulate }) {
  const flight = liveTrip?.flights?.[0]; const hotel = liveTrip?.hotels?.[0]; const status = liveTrip?.status || 'DISRUPTED'
  return <section className="page container activity-page"><div className="page-heading activity-heading"><div><Eyebrow>Autonomous travel care</Eyebrow><h1>Concierge activity</h1></div><span className={`connection ${connection}`}><i /> {connection === 'online' ? 'Live activity connected' : connection === 'preview' ? 'Demo preview' : 'Connecting'}</span></div><div className="activity-layout"><aside className="activity-aside"><InfoCard label="Traveler"><div className="person"><span className="avatar">A</span><div><h3>Aarav Mehta</h3><p>Wayfinder Priority member</p></div></div></InfoCard><InfoCard label="Current journey"><Status value={status} /><div className="compact-route"><strong>{liveTrip?.origin || 'DEL'}</strong><span>⟶</span><strong>{liveTrip?.destination || 'Paris'}</strong></div><p>12–18 October 2026</p><ArrowLink>View complete journey</ArrowLink></InfoCard><InfoCard label="Stay"><span className="small-status">NORMAL</span><h3>{hotel?.hotel_name || 'Hôtel des Grands Boulevards'}</h3><p>{hotel?.city || 'Paris'}, France</p><div className="stay-times"><span>Check in <b>{formatDate(hotel?.check_in) || '12 Oct · 15:00'}</b></span><span>Check out <b>{formatDate(hotel?.check_out) || '18 Oct · 11:00'}</b></span></div></InfoCard><InfoCard label="Final resolution" className="resolution-card"><div className="resolution-empty"><span>✦</span><div><h3>We’ll place your confirmed itinerary here.</h3><p>When the resolution is complete, you’ll see the new flight, arrival time, fare difference, hotel change, and confirmation details.</p></div></div></InfoCard></aside><div className="activity-main"><InfoCard label="Flight" className="flight-card"><div className="flight-title"><Status value={flight?.status === 'CANCELLED' ? 'DISRUPTED' : status} /><span>{flight?.airline || 'Air India'} · Original flight</span></div><div className="flight-route"><div><small>{flight?.origin || 'DEL'}</small><b>{formatDate(flight?.departure_time) || '12 Oct · 01:45'}</b></div><div><em>{flight?.flight_number || 'AI 141'}</em><i /></div><div><small>{flight?.destination || 'CDG'}</small><b>{formatDate(flight?.arrival_time) || '12 Oct · 08:05'}</b></div></div></InfoCard><div className="status-impact"><InfoCard label="Disruption status" className="disruption-card"><Status value="DISRUPTED" /><h2>Your concierge is on it.</h2><p>Your scheduled flight has been cancelled. Wayfinder is protecting the rest of your trip.</p><span className="monitoring"><i className="pulse" /> Concierge monitoring</span></InfoCard><InfoCard label="Trip impact" className="impact-card"><dl><div><dt>Flight</dt><dd>Cancelled</dd></div><div><dt>Connection</dt><dd>At risk</dd></div><div><dt>Hotel</dt><dd>Potentially affected</dd></div><div><dt>Additional cost</dt><dd>₹0</dd></div><div><dt>Arrival delay</dt><dd>+1h 20m</dd></div></dl></InfoCard></div><InfoCard label="Concierge activity" className="timeline-card"><div className="timeline-heading"><div><h2>Resolution in motion</h2><p>Each decision is coordinated against your itinerary and travel preferences.</p></div>{connection === 'online' && <button className="outline-button" onClick={onSimulate}>Simulate cancellation</button>}</div><ol className="timeline">{timeline.map((event) => <li className={event.state} key={event.event_type}><span className="timeline-marker">{event.state === 'done' ? '✓' : event.state === 'current' ? '●' : '○'}</span><div><b>{event.title}</b><p>{event.description}</p><code>{event.event_type}</code></div></li>)}</ol>{actionMessage && <p className="action-message">{actionMessage}</p>}</InfoCard></div></div></section>
}
function Online({ goTo }) {
  return <section className="page container online-page">
      <div className="page-heading">
        <div><Eyebrow>Monitoring now</Eyebrow><h2>3 trips being monitored</h2></div>
      </div>
      <div className="trip-grid">
        <article className="trip-card disrupted"><div className="trip-card-head"><Eyebrow>Monitored journey</Eyebrow><span className="status disrupted"><b>●</b> ALERT</span></div><h2>Delhi → Paris</h2><p className="trip-caption">12–18 Oct</p><div className="trip-card-foot"><span>Concierge attention needed</span><span className="status disrupted"><b>●</b> ALERT</span></div></article>
        <article className="trip-card"><div className="trip-card-head"><Eyebrow>Monitored journey</Eyebrow><span className="status confirmed"><b>●</b> WATCHING</span></div><h2>Delhi → London</h2><p className="trip-caption">04–09 Nov</p><div className="trip-card-foot"><span>Journey is being monitored</span><span className="status confirmed"><b>●</b> WATCHING</span></div></article>
        <article className="trip-card"><div className="trip-card-head"><Eyebrow>Monitored journey</Eyebrow><span className="status confirmed"><b>●</b> WATCHING</span></div><h2>Delhi → Singapore</h2><p className="trip-caption">20–26 Dec</p><div className="trip-card-foot"><span>Journey is being monitored</span><span className="status confirmed"><b>●</b> WATCHING</span></div></article>
      </div>
      <div className="page-heading"><div><Eyebrow>What Wayfinder watches</Eyebrow><h2>Every detail around the journey.</h2></div></div>
      <div className="trip-grid">
        {['✈ Flight status', '⇄ Connections', '✓ Policy checks', '🏨 Hotel reservations'].map((item) => <section className="info-card" key={item}><h3>{item}</h3></section>)}
      </div>
      <InfoCard label="Ready to act"><h2>Detect → Analyze → Search → Rebook<br />→ Update → Notify</h2></InfoCard>
      <InfoCard label="Recent activity" className="timeline-card">
        <ol className="timeline">
          <li className="done"><span className="timeline-marker">✓</span><div><b>Paris trip monitored</b></div></li>
          <li className="done"><span className="timeline-marker">✓</span><div><b>Trip impact analyzed</b></div></li>
          <li className="current"><span className="timeline-marker">●</span><div><b>Alternative flights being searched</b></div></li>
        </ol>
        <ArrowLink onClick={() => goTo('activity')}>View activity</ArrowLink>
      </InfoCard>
  </section>
}
function Profile() { return <section className="page container profile-page"><div className="profile-card"><span className="profile-avatar">A</span><Eyebrow>Profile</Eyebrow><h1>Aarav Mehta</h1><p className="member">Wayfinder Priority member</p><div className="profile-divider" /><div className="profile-detail"><span>Travel care</span><b>Autonomous concierge enabled</b></div><div className="profile-detail"><span>Communication</span><b>Trip updates &amp; confirmations</b></div></div></section> }
export default App
