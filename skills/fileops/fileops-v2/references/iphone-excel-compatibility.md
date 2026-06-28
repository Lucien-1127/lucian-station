# iPhone Excel (iOS) Compatibility

## Summary

iPhone/iPad Excel (Microsoft Excel for iOS) and Apple Numbers have stricter
.xlsx parsing than desktop Excel. Two common failure modes:

1. **Emoji in sheet tab names** → file silently fails to open (hang or crash)
2. **Explicit font name in `Font(name='Arial')`** → file opens but looks wrong
   or fails to render entirely

## Root Cause

- **Sheet names with emoji**: iOS Excel cannot decode UTF-8 emoji characters
  in the `<sheet name="...">` XML attribute. The file opens as a blank
  workbook or displays "File cannot be opened."
  
- **Font name references**: iOS Excel falls back to system fonts when it
  cannot find the named font. Using `Font(name='Arial')` should work (iOS has
  Arial), but certain highly-styled xlsx files from openpyxl can trigger
  rendering issues. Safer: omit `name=` entirely and let the app default.

## Non-negotiable Rules for Mobile .xlsx

| Rule | Why | Fix |
|------|-----|-----|
| No emoji in sheet names | iOS Excel crashes on decode | `'📝 歷史紀錄'` → `'歷史紀錄'` |
| No font name in openpyxl | Rendering failures | `Font(size=10)` NOT `Font(name='Arial', size=10)` |
| Max ~8 columns wide | iPhone screen width (~375pt) | Merge/trim columns to fit without horizontal scroll |
| Row height ≥20pt | Touch target size for taps | `ws.row_dimensions[r].height = 22` minimum |
| Avoid excessive merged cells | iOS parsing is slower than desktop | Only merge headers and summary rows |

## Safe openpyxl Pattern for Mobile

```python
from openpyxl.styles import Font

# DO NOT use name= parameter
header_font = Font(bold=True, size=11, color='ffffff')
body_font = Font(size=10, color='333333')
money_font = Font(bold=True, size=11, color='333333')

# Page setup for phone screen
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.page_setup.orientation = 'portrait'
```

## Testing on Device

1. Generate the .xlsx file on server
2. Transfer to iPhone via Taildrop: `tailscale file cp <file> iphone:`
3. Open from Files app → Tailscale folder → tap file
4. If blank/crash → strip emoji + font names, regenerate, re-transfer
