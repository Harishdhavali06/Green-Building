
import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const initialRooms = [
  { name: "Lab A", zone: "Laboratory", occupancy: 8, capacity: 12, power: 520 },
  { name: "Classroom B", zone: "Teaching block", occupancy: 0, capacity: 40, power: 180 },
  { name: "Classroom C", zone: "Teaching block", occupancy: 18, capacity: 40, power: 310 },
  { name: "Staff Room", zone: "Faculty block", occupancy: 2, capacity: 15, power: 120 },
];

// Illustrative seat layout for UI demonstration only.
// These seats are NOT detected individually by the current YOLO model.
const seats = [
  { id: 1, x: 0, y: 0, occupied: true },
  { id: 2, x: 1, y: 0, occupied: true },
  { id: 3, x: 2, y: 0, occupied: false },
  { id: 4, x: 3, y: 0, occupied: true },
  { id: 5, x: 0, y: 1, occupied: false },
  { id: 6, x: 1, y: 1, occupied: true },
  { id: 7, x: 2, y: 1, occupied: false },
  { id: 8, x: 3, y: 1, occupied: false },
  { id: 9, x: 0, y: 2, occupied: true },
  { id: 10, x: 1, y: 2, occupied: false },
  { id: 11, x: 2, y: 2, occupied: false },
  { id: 12, x: 3, y: 2, occupied: true },
];

const sampleHistory = [36, 48, 41, 62, 53, 72, 58, 66, 49, 77, 61, 70];

function App() {
  const [active, setActive] = useState("Overview");
  const [liveCount, setLiveCount] = useState(null);
  const [cameraStatus, setCameraStatus] = useState("Connecting");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiResult, setAiResult] = useState(null);
  const [rooms] = useState(initialRooms);

  useEffect(() => {
    let mounted = true;

    async function updateOccupancy() {
      try {
        const response = await fetch(
          `${API}/api/occupancy?t=${Date.now()}`,
          { cache: "no-store" }
        );
        if (!response.ok) throw new Error("API unavailable");

        const data = await response.json();
        if (!mounted) return;

        if (
          data.status === "live" &&
          Number.isInteger(data.occupancy) &&
          data.occupancy >= 0
        ) {
          setLiveCount(data.occupancy);
          setCameraStatus("Connected");
          setLastUpdated(new Date());
        } else {
          setCameraStatus("Waiting for camera data");
        }
      } catch {
        if (mounted) setCameraStatus("API disconnected");
      }
    }

    updateOccupancy();
    const timer = setInterval(updateOccupancy, 1500);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  const totalPower = rooms.reduce((sum, room) => sum + room.power, 0);
  const emptyRooms = rooms.filter((room) => room.occupancy === 0);
  const occupancyPercent =
    liveCount === null ? null : Math.min(100, Math.round((liveCount / 40) * 100));

  const insights = useMemo(() => {
    const items = [];
    if (emptyRooms.length) {
      items.push({
        type: "Review",
        title: `${emptyRooms.length} sample room needs review`,
        text: "Check whether lighting and equipment can be reduced when the room is unused.",
      });
    }
    if (liveCount === 0) {
      items.push({
        type: "Occupancy",
        title: "No people detected in the camera view",
        text: "Verify the camera view before making building-wide energy decisions.",
      });
    }
    if (liveCount > 0) {
      items.push({
        type: "Live camera",
        title: `${liveCount} ${liveCount === 1 ? "person" : "people"} detected`,
        text: "This is a camera-frame count, not a verified count for every room.",
      });
    }
    return items;
  }, [emptyRooms.length, liveCount]);

  async function generateRecommendations() {
    setAiLoading(true);
    setAiError("");
    setAiResult(null);

    try {
      const response = await fetch(`${API}/api/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          live_occupancy: liveCount,
          camera_status: cameraStatus,
          rooms: rooms.map((room) => ({
            name: room.name,
            occupancy: room.occupancy,
            capacity: room.capacity,
            estimated_power_w: room.power,
          })),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "AI service unavailable");
      }

      setAiResult(data.recommendations);
    } catch (error) {
      setAiError(
        error.message.includes("Failed to fetch")
          ? "AI endpoint unavailable. Start the updated backend and configure your Gemini API key."
          : error.message
      );
    } finally {
      setAiLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" onClick={() => setActive("Overview")}>
          <span className="brand-mark">e</span>
          <span>
            <strong>ecotwin</strong>
            <small>SMART CAMPUS PROJECT</small>
          </span>
        </a>

        <p className="nav-label">WORKSPACE</p>
        <nav>
          {[
            ["Overview", "◫"],
            ["Rooms", "▦"],
            ["Energy", "ϟ"],
            ["Sustainability", "♧"],
          ].map(([label, symbol]) => (
            <button
              key={label}
              className={`nav-item ${active === label ? "selected" : ""}`}
              onClick={() => {
                setActive(label);
                if (label !== "Overview") {
                  document.getElementById(label.toLowerCase())?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                } else {
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }
              }}
            >
              <span className="nav-symbol">{symbol}</span>
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <span className={`connection-dot ${cameraStatus === "Connected" ? "is-live" : ""}`} />
          <div>
            <strong>{cameraStatus === "Connected" ? "Camera connected" : cameraStatus}</strong>
            <small>YOLO · Phone camera</small>
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div>
            <p className="eyebrow">CAMPUS OPERATIONS / OVERVIEW</p>
            <h1>Building overview</h1>
            <p className="subtitle">A clearer view of how your spaces are being used.</p>
          </div>
          <div className={`live-badge ${cameraStatus === "Connected" ? "live" : ""}`}>
            <span />
            {cameraStatus === "Connected" ? "LIVE CAMERA" : cameraStatus.toUpperCase()}
          </div>
        </header>

        <section className="welcome-banner">
          <div className="welcome-copy">
            <p className="eyebrow">GREEN CAMPUS · DIGITAL TWIN</p>
            <h2>Small changes.<br />Smarter buildings.</h2>
            <p>Use occupancy insights to spot opportunities for more efficient campus operations.</p>
            <button
              className="banner-button"
              onClick={() => document.getElementById("sustainability")?.scrollIntoView({ behavior: "smooth" })}
            >
              Explore insights <span>↗</span>
            </button>
          </div>
          <div className="banner-illustration" aria-hidden="true">
            <div className="illustration-sun" />
            <div className="illustration-building">
              <div className="building-roof" />
              <div className="building-windows">
                {Array.from({ length: 12 }, (_, i) => <i key={i} />)}
              </div>
              <div className="building-door" />
            </div>
            <div className="illustration-plant plant-left">♧</div>
            <div className="illustration-plant plant-right">♧</div>
          </div>
        </section>

        <section className="metrics-grid">
          <article className="metric-card">
            <div className="metric-top"><span>People detected</span><span className="metric-icon blue">♙</span></div>
            <h2>{liveCount === null ? "—" : liveCount}</h2>
            <p className="metric-foot">
              <span className={`mini-dot ${cameraStatus === "Connected" ? "green-dot" : ""}`} />
              {liveCount === null ? cameraStatus : "Live overall camera count"}
            </p>
          </article>
          <article className="metric-card">
            <div className="metric-top"><span>Estimated power</span><span className="metric-icon amber">ϟ</span></div>
            <h2>{totalPower.toLocaleString()} <small>W</small></h2>
            <p className="metric-foot">Illustrative room estimates</p>
          </article>
          <article className="metric-card">
            <div className="metric-top"><span>Rooms monitored</span><span className="metric-icon mint">▦</span></div>
            <h2>{rooms.length}</h2>
            <p className="metric-foot">Sample building layout</p>
          </article>
          <article className="metric-card">
            <div className="metric-top"><span>Rooms to review</span><span className="metric-icon rose">!</span></div>
            <h2>{emptyRooms.length}</h2>
            <p className="metric-foot">Based on sample room data</p>
          </article>
        </section>

        <section className="main-grid" id="rooms">
          <article className="panel floor-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">SPACE VIEW</p>
                <h3>Lab A · Seat map</h3>
                <p className="section-description">A simple view of the lab's seating layout.</p>
              </div>
              <span className="small-tag">FLOOR 01</span>
            </div>

            <div className="seat-legend">
              <span><i className="legend-dot occupied-key" /> Occupied</span>
              <span><i className="legend-dot empty-key" /> Empty</span>
              <span className="demo-label">ILLUSTRATIVE SEATS</span>
            </div>

            <div className="lab-room">
              <div className="room-wall-label">FRONT · DISPLAY / BOARD</div>
              <div className="board-line"><span>LAB A</span></div>
              <div className="seat-grid">
                {seats.map((seat) => (
                  <div className="desk-unit" key={seat.id}>
                    <div className={`seat-bot ${seat.occupied ? "bot-occupied" : "bot-empty"}`}>
                      <span className="bot-antenna" />
                      <span className="bot-face">
                        <i /><i />
                      </span>
                      <span className="bot-mouth" />
                    </div>
                    <div className="desk-top">
                      <span className="desk-number">{String(seat.id).padStart(2, "0")}</span>
                    </div>
                    <span className={`seat-status ${seat.occupied ? "seat-status-occupied" : "seat-status-empty"}`}>
                      {seat.occupied ? "In use" : "Empty"}
                    </span>
                  </div>
                ))}
              </div>
              <div className="room-bottom-label">ENTRANCE</div>
            </div>

            <div className="seat-map-note">
              <span>ⓘ</span>
              <p>Seat states are sample visuals for the prototype. The current camera model counts people in the frame; it does not yet identify individual chairs.</p>
            </div>
          </article>

          <article className="panel insights-panel" id="sustainability">
            <div className="section-heading">
              <div>
                <p className="section-kicker">OPERATIONS</p>
                <h3>What needs a look?</h3>
                <p className="section-description">Initial observations from available data.</p>
              </div>
              <span className="insight-icon">✳</span>
            </div>

            <div className="insight-list">
              {insights.map((item, index) => (
                <div className="insight-item" key={`${item.title}-${index}`}>
                  <span className="insight-mark">{index === 0 ? "ϟ" : "↗"}</span>
                  <div>
                    <span className="insight-type">{item.type}</span>
                    <strong>{item.title}</strong>
                    <p>{item.text}</p>
                  </div>
                </div>
              ))}
              {insights.length === 0 && (
                <div className="empty-insights">
                  <strong>Waiting for camera data</strong>
                  <p>Connect the camera feed to see occupancy observations here.</p>
                </div>
              )}
            </div>

            <div className="sustainability-note">
              <span className="note-leaf">♧</span>
              <div>
                <strong>Measure before you save</strong>
                <p>Real energy savings need meter readings and reliable room-level occupancy data.</p>
              </div>
            </div>
          </article>
        </section>

        <section className="analytics-grid" id="energy">
          <article className="panel chart-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">ENERGY</p>
                <h3>Power use snapshot</h3>
                <p className="section-description">Illustrative values, not live meter readings.</p>
              </div>
              <span className="chart-unit">W</span>
            </div>
            <div className="power-bars">
              {rooms.map((room) => (
                <div className="power-bar-row" key={room.name}>
                  <span className="power-room-name">{room.name}</span>
                  <div className="power-track">
                    <div style={{ width: `${(room.power / 600) * 100}%` }} />
                  </div>
                  <strong>{room.power}</strong>
                </div>
              ))}
            </div>
            <div className="chart-footnote">Sample room estimates · Update with real power-meter data for accurate analysis.</div>
          </article>

          <article className="panel trend-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">ACTIVITY</p>
                <h3>Daily usage pattern</h3>
                <p className="section-description">Example trend for interface demonstration.</p>
              </div>
              <span className="small-tag">SAMPLE</span>
            </div>
            <div className="trend-chart" aria-label="Illustrative activity bar chart">
              {sampleHistory.map((value, index) => (
                <div className="trend-column" key={`${value}-${index}`}>
                  <div className="trend-bar" style={{ height: `${value}%` }} title={`Sample value ${value}`} />
                  <span>{["8a", "", "10a", "", "12p", "", "2p", "", "4p", "", "6p", ""][index]}</span>
                </div>
              ))}
            </div>
            <div className="chart-footnote">Illustrative activity values · Not historical camera data.</div>
          </article>
        </section>

        <section className="panel ai-panel">
          <div className="ai-heading">
            <div className="ai-mark">✳</div>
            <div>
              <p className="section-kicker">GENAI · ENERGY ASSISTANT</p>
              <h3>Ask EcoTwin for practical next steps</h3>
              <p className="section-description">Generate recommendations from the current prototype data.</p>
            </div>
          </div>
          <button className="ai-button" onClick={generateRecommendations} disabled={aiLoading}>
            {aiLoading ? "Generating..." : "Generate recommendations"} <span>↗</span>
          </button>

          {aiError && <div className="ai-error">{aiError}</div>}
          {aiResult && (
            <div className="ai-result">
              {typeof aiResult === "string" ? (
                <p>{aiResult}</p>
              ) : Array.isArray(aiResult) ? (
                aiResult.map((item, index) => (
                  <div className="ai-recommendation" key={index}>
                    <span className="recommendation-number">{String(index + 1).padStart(2, "0")}</span>
                    <div>
                      <strong>{item.title || item.recommendation || `Recommendation ${index + 1}`}</strong>
                      <p>{item.reason || item.action || item.description || ""}</p>
                    </div>
                  </div>
                ))
              ) : (
                <pre>{JSON.stringify(aiResult, null, 2)}</pre>
              )}
            </div>
          )}
          <p className="ai-disclaimer">AI suggestions are advisory. Validate occupancy and energy measurements before acting.</p>
        </section>

        <section className="panel room-table-panel">
          <div className="section-heading table-heading">
            <div>
              <p className="section-kicker">ROOM DIRECTORY</p>
              <h3>Room monitoring</h3>
              <p className="section-description">Sample room values — not live room-level readings.</p>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>ROOM</th><th>ZONE</th><th>OCCUPANCY</th><th>UTILIZATION</th><th>EST. POWER</th><th>STATUS</th></tr>
              </thead>
              <tbody>
                {rooms.map((room) => {
                  const percent = Math.round((room.occupancy / room.capacity) * 100);
                  return (
                    <tr key={room.name}>
                      <td><strong>{room.name}</strong></td>
                      <td>{room.zone}</td>
                      <td>{room.occupancy} / {room.capacity}</td>
                      <td>
                        <div className="progress-track">
                          <div style={{ width: `${percent}%` }} />
                        </div>
                        <small className="utilization-label">{percent}%</small>
                      </td>
                      <td>{room.power} W</td>
                      <td><span className={`status-pill ${room.occupancy > 0 ? "status-on" : "status-off"}`}>{room.occupancy > 0 ? "Occupied" : "Empty"}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <footer className="page-footer">
          <span>ECOTWIN · HACKATHON PROTOTYPE</span>
          <span>{cameraStatus === "Connected" ? `Camera updated ${lastUpdated?.toLocaleTimeString() || "recently"}` : cameraStatus} · Sample room and energy data</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
