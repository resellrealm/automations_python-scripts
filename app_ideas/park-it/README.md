# Park-it - Minimalist GPS Parking Tracker

**Price:** £5 one-time (App Store)  
**Platforms:** iOS, iPadOS, watchOS  
**Tagline:** "Never forget where you parked."

**Mascot:** The Panther — sleek black silhouette, single blue eye. Appears throughout the app. See `design/DESIGN_SYSTEM.md`.
**Fonts:** Space Grotesk Bold (brand/headings — sleek, stealthy, panther energy) · Bebas Neue (timer display — race clock)

---

## Overview

Park-it is a premium, minimalist parking location tracker. One tap to save your spot, beautiful black & white maps, zero friction.

---

## Design System

### Color Palette - "Monochrome"

| Token | Hex | Usage |
|-------|-----|-------|
| `--pure-white` | `#FFFFFF` | Backgrounds, map light theme |
| `--off-white` | `#F5F5F5` | Card backgrounds |
| `--light-gray` | `#E5E5E5` | Borders, dividers |
| `--mid-gray` | `#9CA3AF` | Secondary text, icons |
| `--dark-gray` | `#4B5563` | Body text |
| `--charcoal` | `#1F2937` | Headings |
| `--pure-black` | `#000000` | Primary actions, map dark theme |
| `--accent-blue` | `#3B82F6` | Location dot, active states |
| `--success` | `#10B981` | Parked successfully |
| `--warning` | `#F59E0B` | Time warnings |
| `--danger` | `#EF4444` | Delete actions |

### Map Theme - Black & White

Using **CartoDB Dark Matter** or custom styled **Mapbox**:
- Black background (#000000)
- White roads (#FFFFFF at varying opacity)
- Gray buildings (#333333)
- Blue current location dot
- No POI clutter
- Minimal labels only

### Typography

- **Brand / Headings:** Space Grotesk Bold — sleek, slightly futuristic, precision tech. Panther energy.
- **Timer / Display:** Bebas Neue — "2h 34m" at 72pt looks like a race clock. Impossible to miss.
- **Monospace:** SF Mono — coordinates, rates
- See `design/DESIGN_SYSTEM.md` for full Swift type scale and mood-match reasoning

### Haptics

| Action | Haptic |
|--------|--------|
| Save location | Success notification |
| Find car | Heavy impact + success |
| Time warning | Warning notification |
| Long press on map | Light impact |
| Navigation arrow tap | Selection |
| Delete | Rigid |
| Pull to refresh | Light impact |

---

## Features

### Core Features

1. **One-Tap Parking**
   - Auto-detect when you stop driving (motion coprocessor)
   - One tap to save exact GPS location
   - Automatic parking detection (optional)

2. **Black & White Map**
   - Clean, minimalist CartoDB Dark Matter tiles
   - No visual clutter
   - High contrast for outdoor visibility
   - Works offline (caches area)

3. **Find My Car**
   - Large "Find Car" button
   - Distance and walking time
   - Compass direction
   - AR arrow (point to car)
   - Turn-by-turn walking navigation

4. **Time Tracking**
   - Auto-start timer when parked
   - Set parking duration limit
   - Notifications before expiry
   - Rate calculator (optional input)

5. **Photo Notes**
   - Quick photo of surroundings
   - Text notes (level, zone, color)
   - Voice memo (watch)

6. **Parking History**
   - All previous parking spots
   - Search/filter by location/date
   - Export history
   - Delete old spots

7. **Apple Watch**
   - Complication: time parked
   - One-tap "Find Car"
   - Haptic direction guidance
   - Siri: "Where did I park?"

8. **Widgets**
   - Home screen: time parked, quick find
   - Lock screen: live activity with timer
   - Always-on Display support

---

## Screens & Navigation

### Screen Flow

```
Launch
  ↓
Map View (Main)
  ├─→ Tap to Park → Confirm → Saved
  ├─→ Long Press → Drop Pin → Save
  ├─→ Search Location
  ├─→ Current Location
  │
  ├─→ [Active Parking Card Tap]
  │     ├─→ View Details
  │     ├─→ Navigate to Car
  │     ├─→ Edit Notes
  │     ├─→ Share Location
  │     └─→ End Parking
  │
  ├─→ History Tab
  │     ├─→ Past Parkings
  │     ├─→ Favorites
  │     └─→ Statistics
  │
  └─→ Settings
        ├─→ Map Preferences
        ├─→ Notifications
        ├─→ Auto-Detection
        ├─→ Appearance
        └─→ Export Data
```

---

## Screen Specifications

### 1. Main Map View

**Layout:**
```
┌──────────────────────────────┐
│                              │
│                              │
│                              │
│         [MAP VIEW]           │
│    (Black & White Tiles)     │
│                              │
│         📍 You               │
│                              │
│                              │
│                              │
├──────────────────────────────┤
│  [🔍]  [Current Location]    │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │ 🅿️ PARKED              │  │
│  │                        │  │
│  │ 2h 34m parked          │  │
│  │ 450m away              │  │
│  │                        │  │
│  │ [  📍 Find Car  ]      │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  [🗺️] [🅿️] [📜] [⚙️]        │
└──────────────────────────────┘
```

**Map Controls:**
- Pinch to zoom
- Double-tap to zoom in
- Two-finger tap to zoom out
- Long press to drop pin
- Compass button (top-right)

**Bottom Card States:**

**Not Parked:**
```
┌────────────────────────┐
│  [     Park Here     ] │
│  Tap to save location  │
└────────────────────────┘
```

**Parked:**
```
┌────────────────────────┐
│  🅿️ 2h 34m • £8.50    │
│  [   Find My Car   ]   │
└────────────────────────┘
```

---

### 2. Parking Confirmation

**Layout:**
```
┌──────────────────────────────┐
│  Save Location        [✕]    │
├──────────────────────────────┤
│                              │
│     ┌────────────────┐       │
│     │                │       │
│     │    🅿️          │       │
│     │                │       │
│     │  Location Saved│       │
│     │                │       │
│     └────────────────┘       │
│                              │
│  📍 51.5074° N, 0.1278° W   │
│  📅 Today, 2:34 PM          │
│                              │
├──────────────────────────────┤
│  Add Details (Optional)      │
│  ┌────────────────────────┐  │
│  │ 📷 Add Photo          → │  │
│  ├────────────────────────┤  │
│  │ 📝 Note: [Level 3...  → │  │
│  ├────────────────────────┤  │
│  │ ⏱️ Set Reminder: [2hr ▼]│  │
│  ├────────────────────────┤  │
│  │ 💷 Parking Rate: [£2/hr]│  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  [       Done       ]        │
└──────────────────────────────┘
```

**Haptic:** Success notification on save

---

### 3. Find Car / Navigation

**Layout:**
```
┌──────────────────────────────┐
│  ← Back               [🗺️]    │
├──────────────────────────────┤
│                              │
│     ┌────────────────┐       │
│     │                │       │
│     │      ↑         │       │
│     │     230m       │       │
│     │    3 min       │       │
│     │                │       │
│     └────────────────┘       │
│                              │
│  ┌────────────────────────┐  │
│  │     [ARROW]            │  │
│  │     Points to car      │  │
│  │     ( Compass )        │  │
│  └────────────────────────┘  │
│                              │
│  📍 Your Car                 │
│  2:34 PM today               │
│  📝 Level 3, Row B           │
│                              │
├──────────────────────────────┤
│  [ 📍  Maps  ] [ 🚶 Walk ]   │
│  [  📷 View Photo  ]         │
└──────────────────────────────┘
```

**AR View (Toggle):**
- Camera view with AR arrow overlay
- Distance floating above arrow
- Updates in real-time

---

### 4. Parking Details

**Layout:**
```
┌──────────────────────────────┐
│  Parking Details      [✕]    │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │        [MAP]           │  │
│  │     Small Preview      │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  🅿️ Parking Spot            │
│  📅 Today, 2:34 PM          │
│  ⏱️ 2h 34m duration         │
│  💷 £5.08 estimated          │
├──────────────────────────────┤
│  Details                     │
│  ┌────────────────────────┐  │
│  │ 📷 [Photo thumbnail]  → │  │
│  ├────────────────────────┤  │
│  │ 📝 Note                │  │
│  │ "Level 3, near lift"   │  │
│  ├────────────────────────┤  │
│  │ 📍 Address             │  │
│  │ 123 Oxford Street...   │  │
│  ├────────────────────────┤  │
│  │ 🌐 Coordinates         │  │
│  │ 51.5074° N, 0.1278° W  │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Actions                     │
│  ┌────────────────────────┐  │
│  │ 📍 Navigate to Car    → │  │
│  │ 📤 Share Location     → │  │
│  │ ⭐ Save to Favorites  → │  │
│  │ 🗑️ Delete Record      → │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

---

### 5. History View

**Layout:**
```
┌──────────────────────────────┐
│  History              [🔍]    │
├──────────────────────────────┤
│  [All ▼] [This Month ▼]      │
├──────────────────────────────┤
│  Today                       │
│  ┌────────────────────────┐  │
│  │ 🅿️ Oxford Street     → │  │
│  │ 2:34 PM • 2h 34m      │  │
│  │ £5.08                 │  │
│  ├────────────────────────┤  │
│  │ 🅿️ Tesco Car Park    → │  │
│  │ 9:15 AM • 45m         │  │
│  │ Free                  │  │
│  └────────────────────────┘  │
│                              │
│  Yesterday                   │
│  ┌────────────────────────┐  │
│  │ 🅿️ Train Station     → │  │
│  │ 5:30 PM • 12h         │  │
│  │ £24.00                │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ 📊 Stats Overview     → │  │
│  │ 142 parkings this year │  │
│  │ £342 spent            │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

---

### 6. Settings

**Layout:**
```
┌──────────────────────────────┐
│  Settings                    │
├──────────────────────────────┤
│  Map                         │
│  ┌────────────────────────┐  │
│  │ Theme [Dark (B&W)   ▼] │  │
│  │ Labels [Minimal     ▼] │  │
│  │ Offline Cache    [✓]   │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Notifications               │
│  ┌────────────────────────┐  │
│  │ Time Warnings      [✓] │  │
│  │ 30 min before      [✓] │  │
│  │ 5 min before       [✓] │  │
│  │ Auto-Detected      [✓] │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Auto-Detection              │
│  ┌────────────────────────┐  │
│  │ Detect Parking     [✓] │  │
│  │ Walking Speed      [5km/h]│ │
│  │ Minimum Duration   [5min]│ │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Data                        │
│  ┌────────────────────────┐  │
│  │ Export History      →  │  │
│  │ iCloud Sync        [✓] │  │
│  │ Clear All Data     →   │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  About                       │
│  ┌────────────────────────┐  │
│  │ Version 1.0.0          │  │
│  │ Rate App            →  │  │
│  │ Share App           →  │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

---

## Backend Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Swift + Vapor or Node.js |
| Database | PostgreSQL + PostGIS |
| Maps | Mapbox / CartoDB tiles |
| Geocoding | Mapbox Geocoding API |
| Sync | CloudKit |
| Auth | Apple Sign In |
| Push | APNS |

### Database Schema

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    apple_id VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Parking Sessions
CREATE TABLE parking_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    
    -- Location (PostGIS)
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    
    -- Address info
    address TEXT,
    street VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    
    -- Timing
    parked_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_minutes INTEGER,
    
    -- User input
    note TEXT,
    photo_url TEXT,
    
    -- Rate tracking
    hourly_rate DECIMAL(10, 2),
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2),
    
    -- Reminders
    reminder_set BOOLEAN DEFAULT FALSE,
    reminder_minutes INTEGER,
    reminder_sent BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_favorite BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    detected_automatically BOOLEAN DEFAULT FALSE,
    weather_at_parking JSONB,
    
    cloudkit_record_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Favorite Locations
CREATE TABLE favorite_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address TEXT,
    note TEXT,
    icon VARCHAR(50) DEFAULT 'car',
    color VARCHAR(20) DEFAULT 'blue',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Statistics (materialized view or computed)
CREATE TABLE parking_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    
    total_parkings INTEGER DEFAULT 0,
    total_duration_minutes INTEGER DEFAULT 0,
    total_estimated_cost DECIMAL(10, 2) DEFAULT 0,
    
    this_month_parkings INTEGER DEFAULT 0,
    this_month_cost DECIMAL(10, 2) DEFAULT 0,
    
    favorite_location_id UUID REFERENCES favorite_locations(id),
    favorite_location_count INTEGER DEFAULT 0,
    
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Spatial index for fast location queries
CREATE INDEX idx_parking_location ON parking_sessions USING GIST(location);
CREATE INDEX idx_parking_user_active ON parking_sessions(user_id, is_active);
CREATE INDEX idx_parking_date ON parking_sessions(parked_at DESC);
CREATE INDEX idx_favorites_user ON favorite_locations(user_id);
```

### API Endpoints

```
# Authentication
POST /auth/apple
POST /auth/refresh

# Parking Sessions
GET  /parkings              # List all (with filters)
GET  /parkings/active       # Get current active parking
POST /parkings              # Create new parking
GET  /parkings/:id          # Get details
PATCH /parkings/:id         # Update (add note, photo)
POST /parkings/:id/end      # End parking session
DELETE /parkings/:id        # Delete

# Navigation
GET  /parkings/:id/navigate # Get walking directions
GET  /parkings/:id/distance # Get distance/time to car

# Favorites
GET  /favorites             # List favorite spots
POST /favorites             # Save favorite
DELETE /favorites/:id       # Remove favorite

# Statistics
GET  /stats                 # Get statistics
GET  /stats/history         # Parking history
GET  /stats/spending        # Cost analysis

# Geocoding
GET  /geocode/reverse       # Get address from lat/lng
GET  /geocode/search        # Search for location

# Sync
POST /sync                  # Trigger sync
GET  /sync/status           # Check sync status

# Export
GET  /export                # Export all data
```

---

## Map Configuration

### CartoDB Dark Matter (Recommended)

```javascript
// Mapbox style URL for black & white
tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'

// Or custom Mapbox style
style: 'mapbox://styles/username/dark-monochrome'
```

### Custom Map Style (Mapbox)

```json
{
  "version": 8,
  "name": "Park-it Dark",
  "sources": {
    "mapbox": {
      "type": "vector",
      "url": "mapbox://mapbox.mapbox-streets-v8"
    }
  },
  "layers": [
    {
      "id": "background",
      "type": "background",
      "paint": {
        "background-color": "#000000"
      }
    },
    {
      "id": "water",
      "type": "fill",
      "source": "mapbox",
      "source-layer": "water",
      "paint": {
        "fill-color": "#111111"
      }
    },
    {
      "id": "road",
      "type": "line",
      "source": "mapbox",
      "source-layer": "road",
      "paint": {
        "line-color": "#333333",
        "line-width": 1
      }
    },
    {
      "id": "road-major",
      "type": "line",
      "source": "mapbox",
      "source-layer": "road",
      "filter": ["in", "class", "primary", "trunk", "motorway"],
      "paint": {
        "line-color": "#555555",
        "line-width": 2
      }
    }
  ]
}
```

---

## Apple Watch App

### Complications

- **Graphic Circular:** Time parked / Distance to car
- **Graphic Rectangular:** Quick "Find Car" button
- **Modular Small:** Parking status icon
- **Modular Large:** Time + distance

### Screens

1. **Current Status**
   - Time parked
   - Quick "Find Car" button
   - Distance

2. **Navigation**
   - Arrow pointing to car
   - Distance
   - Haptic feedback as you get closer

3. **Quick Park**
   - One-tap save (uses watch GPS)

---

## iPad Specific Features

- Larger map view
- Split view with history
- Picture-in-picture navigation
- External display support (show map on car screen via CarPlay?)

---

## Live Activities (iOS 16+)

**Dynamic Island / Lock Screen:**
```
┌──────────────────────────────┐
│  🅿️ 2h 14m    [Find Car]    │
│  ⏱️ 16m remaining            │
└──────────────────────────────┘
```

---

## Auto-Detection Logic

```swift
// Pseudocode for automatic parking detection
func detectParking() {
    // 1. Check if user was driving (speed > 20 km/h)
    // 2. Check if user stopped (speed = 0)
    // 3. Check if user started walking (speed 3-6 km/h)
    // 4. Check if user walked away from car location (> 50m)
    // 5. If all conditions met within 5 minutes → Auto-save parking
    
    // Use CoreMotion for activity detection
    // Use CLLocationManager for GPS
}
```

---

## Monetization

- **Price:** £4.99 one-time purchase
- **No subscriptions**
- **No ads**
- **No data selling**
- **Family Sharing:** Supported
- **iCloud Sync:** Included

---

## Development Phases

### Phase 1: Core (MVP)
- Manual parking save
- Black & white map
- Find car with compass
- Basic history

### Phase 2: Polish
- Photo notes
- Time reminders
- Apple Watch app
- Widgets

### Phase 3: Smart Features
- Auto-detection
- Cost tracking
- Statistics
- iCloud sync

### Phase 4: Power Features
- AR navigation
- Live activities
- Siri shortcuts
- Parking rate database
