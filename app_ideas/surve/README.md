# Surve - Universal Sports Score Tracker

**Price:** £5 one-time (App Store)  
**Platforms:** iOS, iPadOS, watchOS  
**Tagline:** "Every sport. Every score. One app."

---

## Overview

Surve is a premium, frictionless score tracking app for ALL sports. While tennis has dedicated score apps, Surve covers every sport imaginable with beautiful, haptic-rich interfaces.

---

## Design System

### Color Palette - "Modern Steel"

| Token | Hex | Usage |
|-------|-----|-------|
| `--steel-50` | `#F8FAFC` | Backgrounds |
| `--steel-100` | `#F1F5F9` | Card backgrounds |
| `--steel-200` | `#E2E8F0` | Borders, dividers |
| `--steel-300` | `#CBD5E1` | Disabled states |
| `--steel-400` | `#94A3B8` | Secondary text |
| `--steel-500` | `#64748B` | Icons |
| `--steel-600` | `#475569` | Body text |
| `--steel-700` | `#334155` | Headings |
| `--steel-800` | `#1E293B` | Strong text |
| `--steel-900` | `#0F172A` | Primary text |
| `--accent-blue` | `#3B82F6` | Primary actions |
| `--accent-cyan` | `#06B6D4` | Highlights, success |
| `--win-green` | `#10B981` | Win indicators |
| `--loss-red` | `#EF4444` | Loss indicators |

### Typography

- **Display:** SF Pro Display (iOS system)
- **Body:** SF Pro Text
- **Monospace:** SF Mono (for scores)
- **Sizes:** Dynamic Type support throughout

### Haptics

| Action | Haptic |
|--------|--------|
| Score increment | Light impact |
| Score decrement | Soft impact |
| Game win | Success notification |
| Match win | Heavy impact + success |
| Button press | Selection |
| Long press | Warning |
| Pull to refresh | Light impact |
| Delete | Rigid |

---

## Features

### Core Features

1. **Multi-Sport Support**
   - Tennis (singles/doubles, all formats)
   - Badminton
   - Squash
   - Table Tennis
   - Basketball
   - Football/Soccer
   - American Football
   - Baseball/Softball
   - Cricket
   - Volleyball (indoor/beach)
   - Handball
   - Hockey (field/ice)
   - Rugby
   - Custom sport builder

2. **Score Tracking Modes**
   - Quick Match (casual)
   - Tournament Mode (brackets)
   - League Mode (season tracking)
   - Practice Mode (solo drills)

3. **Smart Presets**
   - Default rules per sport
   - Custom rule builder
   - Save custom presets
   - Share presets with friends

4. **Statistics & History**
   - Lifetime stats per sport
   - Win/loss ratios
   - Average scores
   - Streak tracking
   - Head-to-head records
   - Performance graphs

5. **Apple Watch App**
   - Quick score entry
   - Glance complications
   - Haptic feedback
   - Standalone mode
   - Siri shortcuts

6. **iPad Experience**
   - Split-screen scoreboard
   - External display support
   - Referee mode (large visible scores)
   - Multi-match tracking

---

## Screens & Navigation

### Main Navigation (Tab Bar)

```
┌─────────────────────────────────────────┐
│  🏠 Home    ➕ New    📊 Stats    ⚙️ Settings  │
└─────────────────────────────────────────┘
```

### Screen Flow

```
Launch
  ↓
Home (Recent Matches)
  ├─→ New Match
  │     ├─→ Select Sport
  │     ├─→ Configure Rules
  │     ├─→ Add Players
  │     └─→ Live Scoreboard
  │
  ├─→ Match History
  │     ├─→ Match Detail
  │     └─→ Share/Export
  │
  ├─→ Statistics
  │     ├─→ Overview
  │     ├─→ By Sport
  │     └─→ Player Comparison
  │
  └─→ Settings
        ├─→ Sport Defaults
        ├─→ Haptics
        ├─→ Appearance
        ├─→ iCloud Sync
        └─→ Export Data
```

---

## Screen Specifications

### 1. Home Screen

**Layout:**
```
┌──────────────────────────────┐
│  Surve              [Search] │
├──────────────────────────────┤
│  Continue Playing            │
│  ┌────────────────────────┐  │
│  │ 🎾 vs Alex            → │  │
│  │ 6-4, 3-2 (Current)     │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Recent Matches              │
│  ┌────────────────────────┐  │
│  │ 🏸 Beat Sarah 21-19   → │  │
│  │ 2 hours ago            │  │
│  ├────────────────────────┤  │
│  │ ⚽ Drew with Team 2-2 → │  │
│  │ Yesterday              │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Quick Start                 │
│  [🎾] [🏸] [🏓] [⚽] [🏀] [+]│
└──────────────────────────────┘
```

**Features:**
- Continue active matches
- Recent match history
- Quick sport access
- Pull to refresh

---

### 2. Live Scoreboard (Tennis Example)

**Layout:**
```
┌──────────────────────────────┐
│  🎾 Tennis - Best of 3 Sets  │
│  Standard Scoring            │
├──────────────────────────────┤
│                              │
│     ┌──────────────────┐     │
│     │                  │     │
│     │    PLAYER 1      │     │
│     │                  │     │
│     │       6          │     │
│     │     ─────        │     │
│     │       3          │     │
│     │      40          │     │
│     │                  │     │
│     │   [+]    [-]     │     │
│     │                  │     │
│     └──────────────────┘     │
│                              │
│           VS                 │
│                              │
│     ┌──────────────────┐     │
│     │                  │     │
│     │    PLAYER 2      │     │
│     │                  │     │
│     │       4          │     │
│     │     ─────        │     │
│     │       2          │     │
│     │      30          │     │
│     │                  │     │
│     │   [+]    [-]     │     │
│     │                  │     │
│     └──────────────────┘     │
│                              │
├──────────────────────────────┤
│  [History] [Stats] [Settings]│
│  [🏠 End Match]  [⚙️ Options]│
└──────────────────────────────┘
```

**Interactions:**
- Tap score to increment (haptic: light impact)
- Swipe down to undo (haptic: soft impact)
- Long press score to edit manually
- Shake to undo last point
- Double tap for quick stats

---

### 3. Sport Selection

**Layout:**
```
┌──────────────────────────────┐
│  Select Sport         [✕]    │
├──────────────────────────────┤
│  Favorites                   │
│  [🎾] [🏸] [🏓]              │
├──────────────────────────────┤
│  Racket Sports               │
│  ┌────────────────────────┐  │
│  │ 🎾 Tennis             → │  │
│  │ Singles, Doubles       │  │
│  ├────────────────────────┤  │
│  │ 🏸 Badminton          → │  │
│  │ Singles, Doubles       │  │
│  ├────────────────────────┤  │
│  │ 🏓 Table Tennis       → │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Team Sports                 │
│  ┌────────────────────────┐  │
│  │ ⚽ Football/Soccer    → │  │
│  │ 🏀 Basketball         → │  │
│  │ 🏈 American Football  → │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  [+] Create Custom Sport     │
└──────────────────────────────┘
```

---

### 4. Match Configuration

**Layout:**
```
┌──────────────────────────────┐
│  Configure Match      [✕]    │
├──────────────────────────────┤
│  Players                     │
│  ┌────────────────────────┐  │
│  │ Player 1               │  │
│  │ [You               ▼]  │  │
│  ├────────────────────────┤  │
│  │ Player 2               │  │
│  │ [Select Opponent   ▼]  │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Format                      │
│  [Best of 3    ▼]            │
├──────────────────────────────┤
│  Rules                       │
│  ┌────────────────────────┐  │
│  │ Tiebreak at 6-6    [✓] │  │
│  │ Advantage scoring  [✓] │  │
│  │ Final set tiebreak [ ] │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Advanced                    │
│  ┌────────────────────────┐  │
│  │ Shot tracking      [✓] │  │
│  │ Serve stats        [✓] │  │
│  │ Rally length       [ ] │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  [     Start Match     ]     │
└──────────────────────────────┘
```

---

### 5. Statistics Dashboard

**Layout:**
```
┌──────────────────────────────┐
│  Statistics           [⚙️]    │
├──────────────────────────────┤
│  Overall Performance         │
│  ┌────────────────────────┐  │
│  │     ┌────┐             │  │
│  │     │ 72%│ Win Rate    │  │
│  │     └────┘             │  │
│  │  142 Matches Played    │  │
│  │  102 Wins | 40 Losses  │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  By Sport                    │
│  ┌────────────────────────┐  │
│  │ 🎾 Tennis    45-12 79% │  │
│  │ 🏸 Badminton 28-15 65% │  │
│  │ 🏓 Ping Pong 15-3  83% │  │
│  │ ⚽ Football   14-10 58% │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  Recent Form (Last 10)       │
│  ✅✅❌✅✅✅✅❌✅✅           │
├──────────────────────────────┤
│  [📈 View Detailed Analytics]│
└──────────────────────────────┘
```

---

## Backend Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Swift + Vapor (or Node.js + Express) |
| Database | PostgreSQL |
| Real-time | WebSockets |
| Sync | CloudKit (primary), iCloud backup |
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
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sports
CREATE TABLE sports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- racket, team, individual
    icon_name VARCHAR(50),
    default_rules JSONB,
    is_custom BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id)
);

-- Sport Rules/Presets
CREATE TABLE sport_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport_id UUID REFERENCES sports(id),
    name VARCHAR(100),
    rules JSONB NOT NULL, -- scoring, format, special conditions
    is_default BOOLEAN DEFAULT FALSE
);

-- Players (can be users or guest players)
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    display_name VARCHAR(100) NOT NULL,
    is_guest BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport_id UUID REFERENCES sports(id),
    rule_preset_id UUID REFERENCES sport_rules(id),
    
    -- Match info
    status VARCHAR(20) DEFAULT 'active', -- active, completed, abandoned
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    
    -- Players
    player_1_id UUID REFERENCES players(id),
    player_2_id UUID REFERENCES players(id),
    
    -- Result
    winner_id UUID REFERENCES players(id),
    final_score JSONB,
    
    -- Metadata
    location VARCHAR(255),
    notes TEXT,
    tags TEXT[],
    
    created_by UUID REFERENCES users(id),
    cloudkit_record_id VARCHAR(255)
);

-- Sets/Periods
CREATE TABLE match_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id),
    set_number INTEGER NOT NULL,
    player_1_score INTEGER DEFAULT 0,
    player_2_score INTEGER DEFAULT 0,
    winner_id UUID REFERENCES players(id),
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

-- Points (for detailed tracking)
CREATE TABLE points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID REFERENCES matches(id),
    set_id UUID REFERENCES match_sets(id),
    
    point_number INTEGER,
    server_id UUID REFERENCES players(id),
    winner_id UUID REFERENCES players(id),
    
    -- Optional detailed tracking
    is_ace BOOLEAN DEFAULT FALSE,
    is_winner BOOLEAN DEFAULT FALSE,
    is_error BOOLEAN DEFAULT FALSE,
    rally_length INTEGER,
    
    score_after JSONB, -- {p1: 40, p2: 30}
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Statistics Aggregates
CREATE TABLE player_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id),
    sport_id UUID REFERENCES sports(id),
    
    matches_played INTEGER DEFAULT 0,
    matches_won INTEGER DEFAULT 0,
    matches_lost INTEGER DEFAULT 0,
    
    -- Sport-specific stats (JSONB for flexibility)
    detailed_stats JSONB,
    
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(player_id, sport_id)
);

-- Custom Sports
CREATE TABLE custom_sports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(100),
    icon_name VARCHAR(50),
    rules JSONB,
    is_shared BOOLEAN DEFAULT FALSE,
    share_code VARCHAR(20)
);

-- Indexes for performance
CREATE INDEX idx_matches_user ON matches(created_by);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_date ON matches(started_at DESC);
CREATE INDEX idx_points_match ON points(match_id);
CREATE INDEX idx_player_stats_player ON player_statistics(player_id);
```

### API Endpoints

```
# Authentication
POST /auth/apple          # Apple Sign In
POST /auth/refresh        # Refresh token

# Sports
GET  /sports              # List all sports
GET  /sports/:id          # Get sport details
GET  /sports/:id/rules    # Get rule presets
POST /sports/custom       # Create custom sport

# Players
GET  /players             # List my players
POST /players             # Create player
GET  /players/:id         # Get player details
GET  /players/:id/stats   # Get player statistics

# Matches
GET  /matches             # List matches (with filters)
POST /matches             # Create new match
GET  /matches/:id         # Get match details
PATCH /matches/:id        # Update match (scores)
POST /matches/:id/points  # Record a point
POST /matches/:id/end     # End match
DELETE /matches/:id       # Delete match

# Statistics
GET  /stats/overview      # Overall stats
GET  /stats/by-sport      # Stats grouped by sport
GET  /stats/head-to-head  # Compare two players
GET  /stats/trends        # Win/loss trends

# Sync
POST /sync/icloud         # Trigger iCloud sync
GET  /sync/status         # Check sync status

# Export
GET  /export/matches      # Export match data (CSV/JSON)
GET  /export/stats        # Export statistics
```

---

## Apple Watch App

### Complications

- **Graphic Circular:** Current match score
- **Graphic Rectangular:** Last match result
- **Modular Small:** Sport icon + win streak
- **Modular Large:** Recent match summary

### Screens

1. **Active Matches List**
2. **Quick Score Entry** (crown to increment)
3. **Match Summary**
4. **Siri Shortcuts:** "Start a tennis match with Alex"

---

## iPad Specific Features

- **Referee Mode:** Large scores visible from distance
- **External Display:** AirPlay scoreboard to TV
- **Multi-match:** Track multiple matches simultaneously
- **Split View:** Stats on left, live match on right

---

## Monetization

- **Price:** £4.99 one-time purchase
- **No subscriptions**
- **No ads**
- **Family Sharing:** Supported
- **iCloud Sync:** Included

---

## Future Features (v2+)

- [ ] Live sharing (spectators see scores in real-time)
- [ ] Team/Club management
- [ ] Tournament brackets
- [ ] ELO rankings per sport
- [ ] Video highlights integration
- [ ] Social sharing cards
- [ ] Apple TV app (scoreboard display)
- [ ] Advanced analytics (AI insights)

---

## Development Phases

### Phase 1: Core (MVP)
- Tennis, Badminton, Table Tennis
- Basic score tracking
- iPhone app only
- Local storage

### Phase 2: Expansion
- Add 10+ more sports
- iPad app
- Apple Watch app
- iCloud sync

### Phase 3: Polish
- Statistics & analytics
- Custom sports
- Haptics throughout
- Refinement

### Phase 4: Power Features
- Live sharing
- Tournament mode
- Advanced tracking
