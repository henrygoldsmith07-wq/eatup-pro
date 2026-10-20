# EatUp Clone - Customization Guide

This guide shows you how to customize your EatUp storage analyzer website.

## Quick Customizations

### Change Brand Color

Find in `index.html` (lines ~25-28):
```javascript
colors: { 
    brand: { 
        500: '#0071e3',  // CHANGE THIS
        600: '#0077ed',  // DARKER SHADE
        700: '#005bb5'   // HOVER SHADE
    }
}
```

**Color Suggestions:**
- **Purple**: `#8b5cf6`, `#7c3aed`, `#6d28d9`
- **Green**: `#10b981`, `#059669`, `#047857`
- **Orange**: `#f97316`, `#ea580c`, `#c2410c`
- **Red**: `#ef4444`, `#dc2626`, `#b91c1c`

### Update Company/Brand Name

1. **Page Title**: Find `<title>` tag and change "EatUp" to your name
2. **Logo**: Replace the SVG icon or change to an image
3. **Brand text**: All instances of "EatUp" can be changed

### Modify Hero Text

Search for in `index.html`:
```html
<h1 class="text-5xl md:text-7xl font-bold mb-6 animate-text-shimmer...">
    See What's Eating Your PC
</h1>
<p class="text-xl md:text-2xl text-neutral-600 dark:text-neutral-400 mb-8...">
    The modern disk space analyzer...
</p>
```

Update these to match your product description.

### Change Pricing

**Free Tier** (find in index.html, search for "Free"):
```html
<h3 class="text-2xl font-bold mb-2">Free</h3>
<div class="text-4xl font-bold mb-6">$0</div>
```

**Pro Tier** (search for "$5.99"):
```html
<h3 class="text-2xl font-bold mb-2">Pro Lifetime</h3>
<div class="text-4xl font-bold mb-6">$5.99</div>
```

### Update Features List

Modify feature card descriptions in the Features section:
- Look for section `id="features"`
- Edit individual feature cards (storage-map, file-discovery, cleanup)
- Add/remove features by copying/duplicating `<div>` blocks

## Adding New Sections

### Insert After Hero Section

```html
<!-- Your new section after </section id="hero"> -->
<section id="new-section" class="py-20 px-6">
    <div class="max-w-7xl mx-auto reveal">
        <h2 class="text-3xl md:text-4xl font-bold mb-8 text-center">Your Heading</h2>
        <p class="text-lg text-neutral-600 dark:text-neutral-400 text-center mb-12">
            Description goes here
        </p>
    </div>
</section>
```

### Add Dark Mode Support

For any colored background, add both light and dark variants:
```html
class="bg-white dark:bg-gray-900"
```

For text:
```html
class="text-neutral-900 dark:text-white"
```

## Font Changes

Current: Plus Jakarta Sans

To change, update the Google Fonts link:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

And update the CSS:
```css
font-family: 'Inter', sans-serif;
```

## Adding Animations

Available animations (already included):
- `.animate-text-shimmer` - Gradient shimmer effect
- `.animate-float` - Gentle up/down floating
- `.animate-pulse-slow` - Slowed pulse animation

Add to any element to use them.

## Responsive Breakpoints

Tailwind breakpoints used:
- Mobile: Default (< 640px)
- Tablet: `md:` prefix (≥ 768px)
- Desktop: `lg:` prefix (≥ 1024px)
- Large: `xl:` prefix (≥ 1280px)

## Interactive Elements

### FAQ Accordion
Click on FAQ items to expand/collapse. JavaScript auto-handles this.

### Theme Toggle
Sun/moon icon toggles dark/light mode. Saves preference to localStorage.

### Smooth Scroll
All anchor links scroll smoothly to destination.

## Troubleshooting

**Dark mode not working?**
- Ensure `<html>` tag has class="" initially
- Check themeToggle JavaScript is present

**Mobile menu not opening?**
- Verify mobileMenuBtn click handler exists
- Check z-index values (should be 50+)

**Animations too fast/slow?**
- Adjust transition times in CSS (.reveal transition timing)

**Colors don't match?**
- Use browser dev tools to inspect computed styles
- Try adding `!important` to custom overrides

## Performance Tips

1. Keep images optimized (use WebP format)
2. Minimize inline styles (use Tailwind classes)
3. Lazy load heavy assets
4. Consider preloading critical fonts

## Next Steps

After customization:
1. Test on multiple browsers
2. Test on mobile devices
3. Validate HTML (HTML Tidy)
4. Optimize images if adding any
5. Set up analytics if needed

---

Need help? Review the source code comments - all sections are clearly marked!
