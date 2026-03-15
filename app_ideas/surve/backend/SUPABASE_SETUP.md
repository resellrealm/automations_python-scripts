# Surve — Supabase Backend Setup

## Keys You Need (and Where They Go)

| Key | What It Is | Where It Goes | Safe in App? |
|-----|-----------|---------------|--------------|
| **Anon Key** (public) | Public client key, respects Row Level Security | iOS app — `SupabaseClient` init | ✅ YES |
| **Service Role Key** (secret) | Bypasses RLS, full DB access | Supabase Edge Functions ONLY | ❌ NEVER in app |
| **Project URL** | `https://[ref].supabase.co` | iOS app — `SupabaseClient` init | ✅ YES |

**You have the anon key and service role key — you also need the Project URL.**
Get it from: Supabase Dashboard → Project Settings → API → Project URL.

So to wire up the iOS app you need exactly 2 things: **Anon Key + Project URL**.
The service role key stays server-side in Edge Functions only (e.g. for sending push notifications via APNS, or admin tasks).

---

## iOS Client Setup

```swift
// Surve/Core/Services/SupabaseService.swift
import Supabase

let supabase = SupabaseClient(
    supabaseURL: URL(string: "https://YOUR_REF.supabase.co")!,
    supabaseKey: "YOUR_ANON_KEY"
)
```

Store keys in your `Info.plist` or a `Config.xcconfig` (never hardcode in source committed to git):
```
SUPABASE_URL = https://YOUR_REF.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

---

## Swift Package Dependency

```swift
// Package.swift or via Xcode SPM
.package(url: "https://github.com/supabase/supabase-swift", from: "2.0.0")
```

---

## Database Migration (Run in Supabase SQL Editor)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apple_id VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    email VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SPORTS
CREATE TABLE sports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),   -- 'racket' | 'team' | 'individual'
    emoji VARCHAR(10),
    icon_name VARCHAR(50),
    default_rules JSONB,
    is_custom BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- SPORT RULES / PRESETS
CREATE TABLE sport_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport_id UUID REFERENCES sports(id) ON DELETE CASCADE,
    name VARCHAR(100),
    rules JSONB NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PLAYERS
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    is_guest BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MATCHES
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport_id UUID REFERENCES sports(id),
    rule_preset_id UUID REFERENCES sport_rules(id),
    status VARCHAR(20) DEFAULT 'active',  -- 'active' | 'completed' | 'abandoned'
    player_1_id UUID REFERENCES players(id),
    player_2_id UUID REFERENCES players(id),
    winner_id UUID REFERENCES players(id),
    final_score JSONB,
    location VARCHAR(255),
    notes TEXT,
    tags TEXT[],
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MATCH SETS / PERIODS
CREATE TABLE match_sets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    player_1_score INTEGER DEFAULT 0,
    player_2_score INTEGER DEFAULT 0,
    winner_id UUID REFERENCES players(id),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ
);

-- POINTS (detailed tracking)
CREATE TABLE points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE CASCADE,
    set_id UUID REFERENCES match_sets(id),
    point_number INTEGER,
    server_id UUID REFERENCES players(id),
    winner_id UUID REFERENCES players(id),
    is_ace BOOLEAN DEFAULT FALSE,
    is_winner BOOLEAN DEFAULT FALSE,
    is_error BOOLEAN DEFAULT FALSE,
    rally_length INTEGER,
    score_after JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PLAYER STATISTICS
CREATE TABLE player_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    sport_id UUID REFERENCES sports(id),
    matches_played INTEGER DEFAULT 0,
    matches_won INTEGER DEFAULT 0,
    matches_lost INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    detailed_stats JSONB,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(player_id, sport_id)
);

-- CUSTOM SPORTS
CREATE TABLE custom_sports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    emoji VARCHAR(10),
    icon_name VARCHAR(50),
    rules JSONB,
    is_shared BOOLEAN DEFAULT FALSE,
    share_code VARCHAR(20) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_matches_created_by ON matches(created_by);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_date ON matches(started_at DESC);
CREATE INDEX idx_points_match ON points(match_id);
CREATE INDEX idx_sets_match ON match_sets(match_id);
CREATE INDEX idx_player_stats ON player_statistics(player_id);
CREATE INDEX idx_players_user ON players(user_id);
```

---

## Row Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE points ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_sports ENABLE ROW LEVEL SECURITY;

-- Users: only see own profile
CREATE POLICY "users_own" ON users
    FOR ALL USING (auth.uid() = id);

-- Players: see own players
CREATE POLICY "players_own" ON players
    FOR ALL USING (auth.uid() = created_by);

-- Matches: see own matches
CREATE POLICY "matches_own" ON matches
    FOR ALL USING (auth.uid() = created_by);

-- Match sets: see if you own the match
CREATE POLICY "sets_via_match" ON match_sets
    FOR ALL USING (
        match_id IN (SELECT id FROM matches WHERE created_by = auth.uid())
    );

-- Points: see if you own the match
CREATE POLICY "points_via_match" ON points
    FOR ALL USING (
        match_id IN (SELECT id FROM matches WHERE created_by = auth.uid())
    );

-- Stats: see own stats
CREATE POLICY "stats_own" ON player_statistics
    FOR ALL USING (
        player_id IN (SELECT id FROM players WHERE created_by = auth.uid())
    );

-- Custom sports: own + shared
CREATE POLICY "custom_sports_own" ON custom_sports
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "custom_sports_shared_read" ON custom_sports
    FOR SELECT USING (is_shared = TRUE);
```

---

## Apple Sign In → Supabase Auth

```swift
// Surve/Core/Services/AuthService.swift
import Supabase
import AuthenticationServices

class AuthService: NSObject, ObservableObject {
    @Published var isSignedIn = false

    func signInWithApple() {
        let provider = ASAuthorizationAppleIDProvider()
        let request = provider.createRequest()
        request.requestedScopes = [.fullName, .email]

        let controller = ASAuthorizationController(authorizationRequests: [request])
        controller.delegate = self
        controller.performRequests()
    }
}

extension AuthService: ASAuthorizationControllerDelegate {
    func authorizationController(
        controller: ASAuthorizationController,
        didCompleteWithAuthorization authorization: ASAuthorization
    ) {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let identityToken = credential.identityToken,
              let tokenString = String(data: identityToken, encoding: .utf8) else { return }

        Task {
            do {
                try await supabase.auth.signInWithIdToken(
                    credentials: .init(
                        provider: .apple,
                        idToken: tokenString
                    )
                )
                await MainActor.run { self.isSignedIn = true }
            } catch {
                print("Auth error: \(error)")
            }
        }
    }
}
```

---

## Realtime (Live Score Sharing — v2)

```swift
// Subscribe to live match updates (v2 feature)
Task {
    for await change in supabase
        .channel("match:\(matchId)")
        .on(.postgres_changes, table: "match_sets", schema: "public") { change in
            // Update local state
        }
        .subscribe()
    { }
}
```

---

## Seed Data — Default Sports

```sql
INSERT INTO sports (name, category, emoji, icon_name, default_rules, is_system) VALUES
('Tennis',          'racket', '🎾', 'tennis',    '{"sets":3,"games":6,"points":"advantage","tiebreak":true}'::jsonb, true),
('Badminton',       'racket', '🏸', 'badminton', '{"sets":3,"points":21,"clear":2,"rally":true}'::jsonb, true),
('Table Tennis',    'racket', '🏓', 'ping_pong', '{"sets":5,"points":11,"clear":2}'::jsonb, true),
('Squash',          'racket', '🎯', 'squash',    '{"sets":5,"points":11,"rally":true}'::jsonb, true),
('Football',        'team',   '⚽', 'football',  '{"periods":2,"duration":45,"overtime":true}'::jsonb, true),
('Basketball',      'team',   '🏀', 'basketball',  '{"periods":4,"duration":12}'::jsonb, true),
('Volleyball',      'team',   '🏐', 'volleyball',  '{"sets":5,"points":25,"rally":true}'::jsonb, true),
('Cricket',         'team',   '🏏', 'cricket',    '{"innings":1,"overs":20}'::jsonb, true),
('Rugby',           'team',   '🏉', 'rugby',      '{"periods":2,"duration":40}'::jsonb, true),
('American Football','team',  '🏈', 'american_football', '{"periods":4,"duration":15}'::jsonb, true),
('Baseball',        'team',   '⚾', 'baseball',  '{"innings":9}'::jsonb, true),
('Hockey',          'team',   '🏒', 'hockey',    '{"periods":3,"duration":20}'::jsonb, true);
```
