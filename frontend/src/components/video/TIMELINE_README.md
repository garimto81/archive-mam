# Hand Timeline Components

Interactive video timeline system for displaying poker hand progression with street markers, action indicators, and real-time playback position tracking.

## Features

- **Street Segments**: Colored timeline segments for each poker street (Preflop, Flop, Turn, River)
- **Action Markers**: Interactive dots showing individual poker actions (bet, raise, fold, call, check, all-in)
- **Community Cards**: Display of community cards revealed at each street
- **Current Position Indicator**: Real-time playback position with smooth animation
- **Hover Tooltips**: Detailed information on hover (time, street, action, cards)
- **Click to Seek**: Click anywhere on timeline to jump to that position
- **Keyboard Accessible**: Full keyboard navigation support (Tab, Enter, Arrow keys)
- **Mobile Responsive**: Optimized for mobile with abbreviated labels
- **ARIA Compliant**: Full screen reader support with semantic HTML

## Components

### HandTimeline

Main timeline component displaying the entire poker hand progression.

```typescript
import { HandTimeline } from "@/components/video";

<HandTimeline
  duration={61.5}
  currentTime={25.3}
  streets={handDetails.streets}
  onSeek={(time) => videoPlayer.seek(time)}
  showActionMarkers={true}
/>
```

**Props**:
- `duration: number` - Total video duration in seconds
- `currentTime: number` - Current playback position in seconds
- `streets: StreetAction[]` - Street-by-street action breakdown
- `onSeek: (time: number) => void` - Callback when user seeks to new position
- `markers?: ActionMarker[]` - Optional additional markers
- `className?: string` - Custom CSS class
- `showActionMarkers?: boolean` - Show action dots (default: true)
- `showStreetLabels?: boolean` - Show street names (default: true)
- `onHover?: (time: number | null) => void` - Callback on hover

### StreetMarker

Individual street segment on the timeline.

```typescript
import { StreetMarker } from "@/components/video";

<StreetMarker
  street="FLOP"
  startPercent={25}
  widthPercent={25}
  isActive={true}
  communityCards={["A♠", "K♥", "Q♦"]}
  color="bg-blue-500"
  onClick={() => seekToFlop()}
/>
```

**Features**:
- Street-specific colors
- Community cards display
- Hover to show cards
- Active/highlight state
- Keyboard accessible

### ActionMarker

Single action indicator on the timeline.

```typescript
import { ActionMarker } from "@/components/video";

<ActionMarker
  action={{
    player: "hero",
    actionType: "RAISE",
    amount: 25,
    timestamp: 15.5
  }}
  position={42.5}
  isActive={false}
  color="bg-orange-500"
  onClick={() => seekTo(15.5)}
/>
```

**Features**:
- Color-coded by action type
- Animated on hover
- Size varies by action importance
- Click to seek to action
- Tooltip on hover

### TimelineTooltip

Floating tooltip for timeline details.

```typescript
import { TimelineTooltip } from "@/components/video";

<TimelineTooltip
  visible={isHovering}
  position={{ x: 150, y: 50 }}
  content={{
    time: "1:23",
    street: "FLOP",
    action: "Hero checks",
    cards: ["A♠", "K♥", "Q♦"]
  }}
/>
```

## Hooks

### useHandTimeline

Hook for timeline calculations and state management.

```typescript
import { useHandTimeline } from "@/hooks/useHandTimeline";

const {
  currentStreet,
  streetSegments,
  actionMarkers,
  seekToStreet,
  seekToAction,
  getStreetAtTime,
  getActionsAtStreet,
} = useHandTimeline({
  streets: handDetails.streets,
  duration: handDetails.duration_seconds,
  currentTime: playerState.currentTime,
  onSeek: (time) => player.seek(time),
});
```

**Returns**:
- `currentStreet: StreetAction | null` - Currently active street
- `streetSegments: StreetSegment[]` - Calculated street positions
- `actionMarkers: MarkerPosition[]` - Calculated action positions
- `seekToStreet: (street) => void` - Jump to street start
- `seekToAction: (index) => void` - Jump to specific action
- `getStreetAtTime: (time) => StreetAction | null` - Get street at time
- `getActionsAtStreet: (street) => Action[]` - Get all actions at street

## Utilities

### timeline-utils

Utility functions for timeline calculations and formatting.

```typescript
import {
  timeToPercent,      // Convert seconds to percentage (0-100)
  percentToTime,      // Convert percentage to seconds
  getStreetColor,     // Get Tailwind class for street color
  getStreetColorHex,  // Get hex color for street
  getActionColor,     // Get Tailwind class for action color
  getActionColorHex,  // Get hex color for action
  formatAction,       // Format action for display ("Hero raises 25 BB")
  formatTime,         // Format seconds as "MM:SS"
  clamp,              // Clamp value between min/max
  rangesOverlap,      // Check if two ranges overlap
  getRangeDuration,   // Calculate range duration
  getStreetLabel,     // Get full street name ("Preflop")
  getStreetAbbr,      // Get abbreviated street name ("PF")
} from "@/lib/video/timeline-utils";
```

## Street Colors

| Street | Color | Class | Hex |
|--------|-------|-------|-----|
| PREFLOP | Purple | `bg-poker-chip-purple` | `#663399` |
| FLOP | Blue | `bg-blue-500` | `#3B82F6` |
| TURN | Yellow | `bg-yellow-400` | `#FACC15` |
| RIVER | Red | `bg-poker-chip-red` | `#FF6B6B` |

## Action Colors

| Action | Color | Class | Hex |
|--------|-------|-------|-----|
| FOLD | Red | `bg-red-500` | `#EF4444` |
| CHECK | Gray | `bg-gray-400` | `#9CA3AF` |
| CALL | Green | `bg-green-500` | `#22C55E` |
| RAISE | Orange | `bg-orange-500` | `#F97316` |
| BET | Blue | `bg-blue-500` | `#3B82F6` |
| ALL_IN | Purple | `bg-poker-chip-purple` | `#663399` |

## Usage Examples

### Basic Timeline

```typescript
import { HandTimeline } from "@/components/video";
import type { StreetAction } from "@/types/hand";

const streets: StreetAction[] = [
  {
    street: "PREFLOP",
    potBB: 2.5,
    actions: [
      { player: "hero", actionType: "raise", amount: 2.5, timestamp: 0 },
      { player: "villain", actionType: "call", amount: 2.5, timestamp: 3 },
    ],
  },
  {
    street: "FLOP",
    potBB: 5,
    communityCards: ["A♠", "K♥", "Q♦"],
    actions: [
      { player: "villain", actionType: "check", timestamp: 5 },
      { player: "hero", actionType: "bet", amount: 3, timestamp: 8 },
    ],
  },
];

export function HandPlayer() {
  const [currentTime, setCurrentTime] = useState(0);

  return (
    <HandTimeline
      duration={30}
      currentTime={currentTime}
      streets={streets}
      onSeek={setCurrentTime}
    />
  );
}
```

### With Video Player Integration

```typescript
import { HandTimeline } from "@/components/video";

export function VideoWithTimeline() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  return (
    <div>
      <video
        ref={videoRef}
        onTimeUpdate={(e) => setCurrentTime(e.currentTime)}
        src="video.mp4"
      />
      <HandTimeline
        duration={videoRef.current?.duration || 0}
        currentTime={currentTime}
        streets={handDetails.streets}
        onSeek={handleSeek}
      />
    </div>
  );
}
```

### With Hand Details Panel

```typescript
export function HandViewer() {
  const [currentTime, setCurrentTime] = useState(0);

  const currentStreet = handDetails.streets.find(
    (street) =>
      street.actions[0].timestamp <= currentTime &&
      street.actions[street.actions.length - 1].timestamp >= currentTime
  );

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2">
        <HandTimeline
          duration={handDetails.duration_seconds}
          currentTime={currentTime}
          streets={handDetails.streets}
          onSeek={setCurrentTime}
        />
      </div>
      <div className="bg-gray-100 p-4 rounded">
        <h3>Street: {currentStreet?.street}</h3>
        <p>Pot: {currentStreet?.potBB} BB</p>
        {currentStreet?.communityCards && (
          <div className="flex gap-1">
            {currentStreet.communityCards.map((card) => (
              <span key={card}>{card}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Focus timeline |
| `Enter` / `Space` | Activate marker or street |
| `Arrow Left` | Previous frame/action (with custom handler) |
| `Arrow Right` | Next frame/action (with custom handler) |
| `Home` | Jump to start (with custom handler) |
| `End` | Jump to end (with custom handler) |

## Accessibility

- **ARIA Labels**: All interactive elements have descriptive labels
- **Role Attributes**: Proper semantic roles (slider, button, tooltip)
- **Keyboard Support**: Full keyboard navigation
- **Screen Reader**: Compatible with screen readers
- **Focus States**: Clear visual focus indicators
- **Color Contrast**: WCAG AA compliant color contrast

## Mobile Responsive

- **Desktop**: Full street names ("Preflop", "Flop", "Turn", "River")
- **Tablet**: Full names with adjusted spacing
- **Mobile**: Abbreviated names ("PF", "F", "T", "R") for space

## Performance Considerations

- **Memoization**: Hook uses `useMemo` for expensive calculations
- **Event Optimization**: Debounced hover events
- **CSS Animations**: Hardware-accelerated transforms
- **Lazy Rendering**: Only renders visible components
- **Virtual Scrolling**: Future support for very long timelines

## Testing

Run tests:

```bash
npm test -- HandTimeline
npm test -- timeline-utils
```

Test coverage includes:
- Timeline calculations and conversions
- Component rendering and interaction
- Accessibility compliance
- Mobile responsiveness
- Tooltip visibility and positioning
- Action marker colors and animations

## Types

All components are fully typed with TypeScript:

```typescript
import type {
  HandTimelineProps,
  StreetMarkerProps,
  ActionMarkerProps,
  TimelineTooltipProps,
  TimelineTooltipContent,
  TooltipPosition,
} from "@/components/video";

import type {
  StreetSegment,
  MarkerPosition,
  UseHandTimelineReturn,
  UseHandTimelineOptions,
} from "@/hooks/useHandTimeline";
```

## Customization

### Theme Colors

Colors are defined in `tailwind.config.ts`:

```typescript
poker: {
  chip: {
    purple: "hsl(270, 50%, 40%)",    // PREFLOP
    // Add more as needed
  },
}
```

### Custom Styling

```typescript
<HandTimeline
  {...props}
  className="custom-timeline my-4"
/>
```

### Event Handlers

```typescript
<HandTimeline
  {...props}
  onHover={(time) => console.log("Hovering at", time)}
  onSeek={(time) => console.log("Seeking to", time)}
/>
```

## Troubleshooting

### Timeline not responding to clicks

Ensure `onSeek` callback is properly connected to video player:

```typescript
const handleSeek = (time: number) => {
  if (videoElement) {
    videoElement.currentTime = time;
  }
};

<HandTimeline {...props} onSeek={handleSeek} />
```

### Action markers not showing

Check `showActionMarkers` prop is `true` and `streets` array has actions:

```typescript
<HandTimeline
  {...props}
  showActionMarkers={true}
  streets={streetsWithActions}
/>
```

### Tooltip positioning issues

Tooltip automatically adjusts for viewport boundaries. Ensure parent container has `position: relative` if custom positioning needed.

## Related Components

- `VideoPlayer` - Main video playback component
- `VideoControls` - Player controls (play, pause, volume)
- `VideoError` - Error display component

## Future Enhancements

- [ ] Playback speed indicator
- [ ] Audio waveform visualization
- [ ] Bookmarks/annotations
- [ ] Multi-hand comparison view
- [ ] Timeline presets (common bet sizing)
- [ ] Export timeline as image/PDF
