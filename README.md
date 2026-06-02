# S/V Oroboro — sailingoroboro.com

The sailing journal of Francesco and Yuka — two former Silicon Valley tech workers who quit their jobs in 2018 to sail around the world on a Leopard 40 catamaran named Oroboro. Seven years and 25,000 nautical miles later, they're still out there.

**Route:** Cape Town → Namibia → South Atlantic → St Helena → Brazil → Caribbean → Bahamas → Azores → Portugal → Mediterranean → Greece (ongoing)

---

## Site Structure

| File | Description |
|------|-------------|
| `index.html` | Homepage — editorial design with hero, timeline, stories, about |
| `styles.css` | Homepage CSS (Playfair Display + Inter, sand/navy palette) |
| `blog.html` | All 75 blog posts with region filters |
| `posts/` | Individual post pages generated from WordPress export |
| `map.html` | Interactive Leaflet.js journey map |
| `about.html` | About page |
| `css/style.css` | CSS for blog/post/map pages |
| `build.py` | Static site generator — reads WordPress XML, regenerates blog pages |
| `img/` | Logo assets (white, mark, stacked, horizontal variants) |
| `OroboroHeroPhoto.jpeg` | Hero photo — Oroboro under spinnaker |
| `OroboroHomePage169.MOV` | Hero video source (31s, 16:9) |
| `Final artwork Oroboro/` | Full logo artwork (AI, EPS, PNG, JPG, PSD) |
| `CNAME` | `sailingoroboro.com` |

## Rebuild Blog Pages

Blog posts are generated from a WordPress XML export:

```bash
/usr/bin/python3 build.py
```

Source XML: `~/Documents/Blog Documentation/Oroboro Blog Back Up Text.xml`

## Deploy

```bash
git add -A && git commit -m "..." && git push
```

GitHub Pages serves from the `main` branch root.

## Links

- Instagram: [@sailingoroboro](https://instagram.com/sailingoroboro)
- Boat manager: [boat.sailingoroboro.com](https://boat.sailingoroboro.com)
