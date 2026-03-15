#!/usr/bin/env python3
"""
Generate a realistic Event Storming board for Cargo Shipping domain.
Uses Event Storming color conventions and layouts.
"""

import random
import math

# Set seed for reproducible randomness
random.seed(42)

def random_rotation():
    """Return a slight rotation angle for realism."""
    return random.uniform(-3, 3)

def wrap_text(text, max_width=14):
    """Wrap text to fit within sticky note width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line + [word])) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines

class StickyNote:
    """Represents a sticky note on the board."""

    def __init__(self, x, y, text, note_type, width=140, height=90):
        self.x = x
        self.y = y
        self.text = text
        self.note_type = note_type
        self.width = width
        self.height = height
        self.rotation = random_rotation()
        self.colors = {
            'event': ('#FF8C00', '#000000'),      # Orange bg, black text
            'command': ('#4169E1', '#FFFFFF'),    # Blue bg, white text
            'aggregate': ('#FFD700', '#000000'),  # Yellow bg, black text
            'policy': ('#9370DB', '#FFFFFF'),     # Purple bg, white text
            'hotspot': ('#FF6B6B', '#000000'),    # Red bg, black text
            'read_model': ('#3CB371', '#FFFFFF'), # Green bg, white text
            'actor': ('#FFF8DC', '#000000'),      # Cream bg, black text
            'external': ('#F0F0F0', '#000000'),   # Light gray bg, black text
        }

    def to_svg(self):
        """Generate SVG for this sticky note."""
        bg_color, text_color = self.colors.get(self.note_type, ('#FFFFFF', '#000000'))

        # Create group with rotation
        svg = f'  <g transform="translate({self.x}, {self.y}) rotate({self.rotation})">\n'

        # Background rectangle with shadow
        svg += f'    <rect x="0" y="2" width="{self.width}" height="{self.height}" '
        svg += f'fill="#00000020" rx="3"/>\n'

        # Main rectangle
        svg += f'    <rect x="0" y="0" width="{self.width}" height="{self.height}" '
        svg += f'fill="{bg_color}" stroke="#333333" stroke-width="1" rx="3"/>\n'

        # Text
        lines = wrap_text(self.text, max_width=16)
        y_offset = 12

        for i, line in enumerate(lines):
            svg += f'    <text x="7" y="{y_offset + i * 16}" font-size="12" '
            svg += f'font-family="Arial, sans-serif" fill="{text_color}" '
            svg += f'font-weight="500">{line}</text>\n'

        svg += '  </g>\n'
        return svg


def create_arrow(x1, y1, x2, y2, label=""):
    """Create an arrow line with optional label."""
    svg = f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    svg += f'stroke="#666666" stroke-width="2" marker-end="url(#arrowhead)"/>\n'

    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2 - 10
        svg += f'  <text x="{mid_x}" y="{mid_y}" font-size="11" '
        svg += f'font-family="Arial, sans-serif" fill="#666666" '
        svg += f'text-anchor="middle">{label}</text>\n'

    return svg


def create_boundary_box(x, y, width, height, label, color):
    """Create a dashed boundary box for a bounded context."""
    svg = f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" '
    svg += f'fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="8,4" rx="5"/>\n'

    svg += f'  <text x="{x + 10}" y="{y + 20}" font-size="14" '
    svg += f'font-family="Arial, sans-serif" font-weight="bold" fill="{color}">{label}</text>\n'

    return svg


def create_legend():
    """Create a legend in the top-right corner."""
    svg = '  <!-- Legend -->\n'
    svg += '  <g id="legend" transform="translate(3600, 30)">\n'

    items = [
        ('#FF8C00', 'Event'),
        ('#4169E1', 'Command'),
        ('#FFD700', 'Aggregate'),
        ('#9370DB', 'Policy'),
        ('#FF6B6B', 'Hotspot'),
        ('#3CB371', 'Read Model'),
        ('#FFF8DC', 'Actor'),
        ('#F0F0F0', 'External'),
    ]

    svg += '    <text x="0" y="0" font-size="14" font-weight="bold" '
    svg += 'font-family="Arial, sans-serif" fill="#333333">Legend</text>\n'

    for i, (color, label) in enumerate(items):
        y_pos = 25 + i * 20
        svg += f'    <rect x="0" y="{y_pos}" width="12" height="12" fill="{color}" stroke="#333333" stroke-width="0.5"/>\n'
        svg += f'    <text x="18" y="{y_pos + 10}" font-size="11" '
        svg += f'font-family="Arial, sans-serif" fill="#333333">{label}</text>\n'

    svg += '  </g>\n'
    return svg


def create_crossed_out_note():
    """Create a crossed-out sticky note showing a modeling decision."""
    svg = '  <!-- Crossed-out note (modeling correction) -->\n'
    svg += '  <g id="crossed-note" transform="translate(580, 200) rotate(-1)">\n'

    svg += '    <rect x="0" y="2" width="140" height="90" fill="#00000020" rx="3"/>\n'
    svg += '    <rect x="0" y="0" width="140" height="90" fill="#FFD700" stroke="#333333" stroke-width="1" rx="3"/>\n'

    svg += '    <text x="7" y="25" font-size="12" font-family="Arial, sans-serif" '
    svg += 'fill="#000000" font-weight="500" text-decoration="line-through">Shipment</text>\n'

    # Strikethrough line
    svg += '    <line x1="7" y1="20" x2="120" y2="20" stroke="#000000" stroke-width="2"/>\n'

    svg += '    <text x="7" y="50" font-size="12" font-family="Arial, sans-serif" '
    svg += 'fill="#FF6B6B" font-weight="bold">=&gt; Cargo</text>\n'

    svg += '  </g>\n'
    return svg


# SVG dimensions
viewbox_width = 3840
viewbox_height = 1200

# Start SVG
svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 {viewbox_width} {viewbox_height}" width="{viewbox_width}" height="{viewbox_height}"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <!-- Arrow marker -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#666666"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{viewbox_width}" height="{viewbox_height}" fill="#FAFAFA"/>

  <!-- Grid for reference (faint) -->
  <defs>
    <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
      <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#E0E0E0" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="{viewbox_width}" height="{viewbox_height}" fill="url(#grid)"/>

'''

# Create bounded context zones
svg_content += '  <!-- BOUNDED CONTEXT ZONES -->\n'
svg_content += create_boundary_box(50, 150, 1250, 1000, 'Booking Context', '#2E8B57')
svg_content += create_boundary_box(1350, 150, 1050, 1000, 'Tracking Context', '#4169E1')
svg_content += create_boundary_box(2500, 150, 700, 500, 'Voyage Context', '#9370DB')
svg_content += create_boundary_box(2500, 700, 700, 450, 'Location\n(Reference Data)', '#808080')

# ZONE 1: BOOKING CONTEXT
svg_content += '\n  <!-- ZONE 1: BOOKING CONTEXT -->\n'

notes_booking = [
    # Actors
    StickyNote(100, 200, 'Shipping\nClerk', 'actor', width=100, height=70),

    # Command flow
    StickyNote(250, 200, 'Book Cargo', 'command'),

    # Cargo Aggregate (larger)
    StickyNote(250, 330, 'Cargo', 'aggregate', width=140, height=110),

    # Events
    StickyNote(400, 200, 'Cargo\nBooked', 'event'),

    # Next command
    StickyNote(550, 200, 'Assign\nItinerary', 'command'),
    StickyNote(550, 330, 'Cargo Routed', 'event'),

    # Change Destination command
    StickyNote(700, 200, 'Change\nDestination', 'command'),
    StickyNote(700, 330, 'Destination\nChanged', 'event'),

    # Policy
    StickyNote(850, 500, 'When Cargo\nHandled →\nDerive Delivery', 'policy'),

    # More events
    StickyNote(400, 500, 'Cargo\nMisdirected', 'event'),
    StickyNote(550, 500, 'Cargo\nDelivered', 'event'),

    # Read Model
    StickyNote(1000, 200, 'Cargo\nTracking\nView', 'read_model'),

    # External System
    StickyNote(1000, 330, 'Routing\nEngine', 'external'),

    # Hotspot
    StickyNote(1000, 500, 'What if routing\nengine is\nunavailable?', 'hotspot'),
]

for note in notes_booking:
    svg_content += note.to_svg()

# ZONE 2: TRACKING CONTEXT
svg_content += '\n  <!-- ZONE 2: TRACKING CONTEXT -->\n'

notes_tracking = [
    # Actor
    StickyNote(1400, 200, 'Port\nOperations', 'actor', width=100, height=70),

    # Command
    StickyNote(1550, 200, 'Register\nHandling\nEvent', 'command'),

    # Events - vertical timeline
    StickyNote(1700, 200, 'Cargo\nReceived', 'event'),
    StickyNote(1700, 330, 'Cargo\nLoaded', 'event'),
    StickyNote(1700, 500, 'Cargo\nUnloaded', 'event'),
    StickyNote(1700, 670, 'Customs\nCleared', 'event'),

    # More events
    StickyNote(1850, 200, 'Cargo\nClaimed', 'event'),

    # Handling Event Aggregate (larger)
    StickyNote(1850, 330, 'Handling\nEvent', 'aggregate', width=140, height=110),

    # Hotspot
    StickyNote(2050, 500, 'How do we\nhandle partial\nunloads?', 'hotspot'),
]

for note in notes_tracking:
    svg_content += note.to_svg()

# ZONE 3: VOYAGE CONTEXT
svg_content += '\n  <!-- ZONE 3: VOYAGE CONTEXT -->\n'

notes_voyage = [
    # Actor
    StickyNote(2550, 200, 'Scheduling\nDept', 'actor', width=100, height=70),

    # Command
    StickyNote(2700, 200, 'Schedule\nVoyage', 'command'),

    # Events
    StickyNote(2700, 330, 'Voyage\nScheduled', 'event'),
    StickyNote(2700, 500, 'Voyage\nDelayed', 'event'),

    # Voyage Aggregate
    StickyNote(2850, 330, 'Voyage', 'aggregate', width=140, height=110),
]

for note in notes_voyage:
    svg_content += note.to_svg()

# ZONE 4: LOCATION (Reference Data)
svg_content += '\n  <!-- ZONE 4: LOCATION (Reference Data) -->\n'

notes_location = [
    StickyNote(2550, 750, 'UN/LOCODE\nPort\nRegistry', 'external'),
    StickyNote(2700, 850, 'Should\nLocation be\nexternal\nservice?', 'hotspot'),
]

for note in notes_location:
    svg_content += note.to_svg()

# Add arrows showing flow
svg_content += '\n  <!-- FLOW ARROWS -->\n'

# Booking flow
svg_content += create_arrow(350, 235, 390, 235)  # Book Cargo -> Cargo Booked
svg_content += create_arrow(440, 280, 510, 235)  # Cargo Booked -> Assign Itinerary
svg_content += create_arrow(600, 280, 640, 235)  # Itinerary -> Change Destination
svg_content += create_arrow(750, 280, 740, 310)  # Change Destination -> Destination Changed

# Tracking flow
svg_content += create_arrow(1620, 235, 1670, 235)  # Register -> Cargo Received
svg_content += create_arrow(1750, 260, 1750, 300)  # Cargo Received -> Cargo Loaded
svg_content += create_arrow(1750, 380, 1750, 460)  # Cargo Loaded -> Cargo Unloaded

# Integration arrow (Tracking to Booking)
svg_content += create_arrow(1950, 520, 1100, 520, 'Cargo\nHandled')

# Voyage flow
svg_content += create_arrow(2770, 260, 2760, 310)  # Schedule Voyage -> Voyage Scheduled

# Add crossed-out note
svg_content += create_crossed_out_note()

# Add legend
svg_content += create_legend()

# Close SVG
svg_content += '</svg>'

# Write to file
output_path = '/sessions/keen-kind-albattani/mnt/xp-2026/ddd-meets-genai/skills/domain-modeler/evals/files/cargo-shipping-es-board.svg'
with open(output_path, 'w') as f:
    f.write(svg_content)

print(f"SVG file created successfully: {output_path}")
print(f"Dimensions: {viewbox_width}x{viewbox_height} pixels")
