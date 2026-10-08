# Clickable URLs Feature

## Overview

The Client UI now automatically converts URLs in response messages into clickable hyperlinks, improving user experience and making it easier to access SD Elements projects, documentation, and other resources directly from chat responses.

## Implementation

### Location
- **JavaScript**: `client-ui/static/app.js`
- **CSS**: `client-ui/static/styles.css`

### How It Works

1. **URL Detection**: The `linkifyUrls()` function uses a regex pattern to identify URLs:
   ```javascript
   const urlRegex = /(https?:\/\/[^\s<>"']+)/g;
   ```

2. **Safe HTML Conversion**: 
   - Text is split by URLs
   - Non-URL parts are HTML-escaped to prevent XSS attacks
   - URLs are converted to anchor tags with security attributes

3. **Security Features**:
   - `target="_blank"` - Opens links in new tab
   - `rel="noopener noreferrer"` - Prevents security vulnerabilities
   - HTML escaping prevents injection attacks

4. **Smart Punctuation Handling**:
   - Trailing punctuation (`.`, `,`, `;`, `!`, `?`) is separated from URLs
   - Prevents broken links from punctuation at end of sentences

### Example Transformation

**Input Text:**
```
Project created successfully! 
URL: https://sde-ent-onyxdrift.sdelab.net/bunits/ocean-freight/project/
You can also visit https://docs.sdelements.com/ for more info.
```

**Output HTML:**
```html
Project created successfully! 
URL: <a href="https://sde-ent-onyxdrift.sdelab.net/bunits/ocean-freight/project/" 
      target="_blank" 
      rel="noopener noreferrer">
  https://sde-ent-onyxdrift.sdelab.net/bunits/ocean-freight/project/
</a>
You can also visit <a href="https://docs.sdelements.com/" 
                       target="_blank" 
                       rel="noopener noreferrer">
  https://docs.sdelements.com/
</a> for more info.
```

## Styling

### Assistant Message Links
- **Color**: Brand purple (`#667eea`)
- **Decoration**: Bottom border (subtle underline)
- **Hover**: Changes to darker purple (`#764ba2`)
- **Font Weight**: Medium (500) for emphasis

### User Message Links
- **Color**: White (maintains contrast)
- **Decoration**: Underline
- **Hover**: Slight opacity change

### Error Message Links
- **Color**: Error red (`#c33`)
- **Decoration**: Underline

## Supported URL Formats

✅ `https://example.com`
✅ `http://example.com`
✅ `https://example.com/path/to/resource`
✅ `https://example.com/path?query=value`
✅ `https://example.com:8080/path`

❌ `www.example.com` (no protocol)
❌ `ftp://example.com` (only http/https supported)

## Security Considerations

1. **XSS Prevention**: All non-URL text is HTML-escaped
2. **Target Safety**: `rel="noopener noreferrer"` prevents window.opener attacks
3. **URL Validation**: Only http/https protocols are linkified
4. **Character Filtering**: Regex excludes dangerous characters (`<>'"`)

## Testing

### Manual Testing

1. Send a query that returns a project URL:
   ```
   Create a project named "Test Project" in application 516
   ```

2. Verify the response contains a clickable URL

3. Click the URL and verify:
   - Opens in new tab
   - Navigates to correct SD Elements page

### Test Cases

1. **Single URL**: Simple URL in message
2. **Multiple URLs**: Message with several URLs
3. **URL with punctuation**: "Visit https://example.com. Thanks!"
4. **Mixed content**: Text before, between, and after URLs
5. **Long URLs**: URLs with long paths and query parameters

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Modern mobile browsers

Uses standard DOM APIs and CSS, no special compatibility concerns.

## Future Enhancements

Potential improvements:
- [ ] Support for other protocols (ftp, mailto)
- [ ] Detect URLs without http/https (www.example.com)
- [ ] Show URL preview on hover
- [ ] Click tracking/analytics
- [ ] Custom link icons for different domains

## Rollback

If issues arise, revert with:

```bash
git revert <commit-hash>
docker-compose up --build -d
```

The system will fall back to plain text URLs.

## Related Files

- `client-ui/static/app.js` - JavaScript implementation
- `client-ui/static/styles.css` - Link styling
- `client-ui/static/index.html` - HTML structure (unchanged)

## Version History

- **v1.0.0** (Dec 2025) - Initial implementation
  - Automatic URL detection and linking
  - Security features (XSS prevention, safe target)
  - Styled links for all message types

