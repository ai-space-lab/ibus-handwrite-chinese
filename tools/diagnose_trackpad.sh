#!/bin/bash
# tools/diagnose_trackpad.sh — Diagnose why ibus-handwrite-chinese doesn't detect the trackpad
set -e

echo "=== IBus Handwrite Chinese — Trackpad Diagnostics ==="
echo ""

echo "--- Step 1: Evdev Device Scan ---"
python3 -c "
import evdev, os

devices = evdev.list_devices()
print(f'Found {len(devices)} event device(s):')
print()

# Trackpad candidates found
candidates_current = []
candidates_fixed = []

for p in devices:
    try:
        d = evdev.InputDevice(p)
        caps = d.capabilities(absinfo=False)
        btns = caps.get(evdev.ecodes.EV_KEY, [])
        abs_codes = caps.get(evdev.ecodes.EV_ABS, [])
        name = d.name
        path = d.path
        d.close()

        has_btn_touch = evdev.ecodes.BTN_TOUCH in btns
        has_mt_tracking = evdev.ecodes.ABS_MT_TRACKING_ID in abs_codes
        has_abs_x = evdev.ecodes.ABS_X in abs_codes
        has_mt_pos_x = evdev.ecodes.ABS_MT_POSITION_X in abs_codes
        has_pos = has_abs_x or has_mt_pos_x

        print(f'  {path}  {name}')
        print(f'    BTN_TOUCH={has_btn_touch}  ABS_MT_TRACKING_ID={has_mt_tracking}  ABS_X={has_abs_x}  ABS_MT_POSITION_X={has_mt_pos_x}')

        if (has_btn_touch or has_mt_tracking) and has_pos:
            if has_btn_touch:
                print(f'    ✓ Would be selected by CURRENT filter (has BTN_TOUCH)')
                candidates_current.append(name)
            else:
                print(f'    ✗ MISSED by current filter (no BTN_TOUCH, but has ABS_MT_TRACKING_ID)')
                print(f'    → Would be selected by FIXED filter')
                candidates_fixed.append(name)
        else:
            print(f'    → Not a suitable trackpad device')

    except PermissionError:
        print(f'  {p}: PERMISSION DENIED — user cannot read this device')
    except Exception as e:
        print(f'  {p}: ERROR: {e}')

print()
if candidates_current:
    print(f'Trackpad(s) matching CURRENT filter ({len(candidates_current)}):')
    for c in candidates_current:
        print(f'  - {c}')
else:
    print('No trackpad matches the CURRENT filter (BTN_TOUCH + position).')

if candidates_fixed:
    print()
    print(f'Trackpad(s) that would match FIXED filter ({len(candidates_fixed)}):')
    for c in candidates_fixed:
        print(f'  - {c} (adds ABS_MT_TRACKING_ID support)')

print()
if candidates_current:
    print('STATUS: Device should work with current code.')
elif candidates_fixed:
    print('STATUS: Device detected but needs ABS_MT_TRACKING_ID filter fix.')
else:
    print('STATUS: No suitable device found. Check permissions below.')
"

echo ""
echo "--- Step 2: Udev Rule ---"
RULE_FILE="/etc/udev/rules.d/99-trackpad-handwrite.rules"
if [ -f "$RULE_FILE" ]; then
    echo "  ✓ Udev rule installed at $RULE_FILE"
    cat "$RULE_FILE"
else
    echo "  ✗ Udev rule NOT installed at $RULE_FILE"
fi

echo ""
echo "--- Step 3: Device Permissions ---"
echo "  Checking ACLs on input devices..."
getfacl /dev/input/event* 2>/dev/null | head -20 || echo "  (getfacl not available or no event devices)"

echo ""
echo "--- Step 4: Python evdev Module ---"
if python3 -c "import evdev; print(evdev.__version__)" 2>/dev/null; then
    echo "  ✓ python3-evdev is installed"
else
    echo "  ✗ python3-evdev is NOT installed"
    echo "  Install: sudo apt install python3-evdev"
fi

echo ""
echo "=== Diagnostics Complete ==="
echo ""
echo "Next steps based on findings above:"
echo "  1. If 'STATUS: Device detected but needs ABS_MT_TRACKING_ID filter fix':"
echo "     → The filter fix is needed. Run: python3 src/ibus-engine-handwrite-chinese --test"
echo "  2. If 'PERMISSION DENIED' or 'No suitable device found':"
echo "     → Run: sudo udevadm control --reload-rules && sudo udevadm trigger"
echo "     → Or add user to 'input' group: sudo usermod -a -G input $USER && reboot"
echo "  3. If BTN_TOUCH=True but no strokes in --test mode:"
echo "     → May be a grab/state-machine issue. Run with IBUS_HANDWRITE_EVDEV_DEBUG=1"
echo ""
