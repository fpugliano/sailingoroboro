# Voice Cloning Guide — ElevenLabs

## What you need
- ElevenLabs account (Creator plan, ~$22/month — needed for voice cloning)
- A quiet room, no echo
- Any microphone (AirPods work, a USB mic is better)
- ~10–15 minutes of your voice recorded

## Step 1 — Record your voice sample

Read the text below aloud, naturally, at a normal pace. Don't try to perform — just talk as you would in conversation.
Save as a single MP3 or WAV file.

---

### Reading script for voice cloning:

We left the dock on a Tuesday morning. The bay was flat and the wind was light — perfect conditions for a first departure, not that we knew what we were doing. We'd spent months preparing for this moment, reading books, watching videos, asking advice from anyone who'd done it before. But nothing really prepares you for the moment the lines come off the cleats and the shore starts moving away.

Yuka stood at the bow and I was at the helm. Neither of us said much. There was nothing to say. The marina slipped behind us, and ahead was the open water, and beyond that, eventually, the ocean. I remember thinking: we've actually done it. And then immediately thinking: now what?

The first few days were hard. We were clumsy on deck, forgetting where things were stowed, getting the sheets tangled. We sailed too conservatively, reefing when we didn't need to, then not reefing when we should have. We made mistakes, corrected them, and made different ones. That's how you learn.

By the end of the first week, something had shifted. The boat started to feel like home — not in a comfortable, familiar way, but in the way that a living thing becomes part of you. You stop thinking about where the winch handle is. Your hands find the right lines without looking. You start to read the water differently.

I think about that first week a lot. Everyone who sails long distances goes through it — the adjustment, the humility, the slow accumulation of competence. It's not dramatic. It happens quietly, one small thing at a time.

The Leopard 38 is a catamaran, which means two hulls, two engines, and a lot of space below deck. It also means you can anchor in shallow water, which opens up places a monohull can't reach. We chose it because we were going to live on it, and space matters when you're on passage for three weeks at a stretch. But the real reason, if I'm honest, is that we fell in love with it the first time we stepped aboard. That's not a rational thing. It just happened.

Cape Town was our first stop. South Africa surprised us — the mountains, the wine, the wild coast down towards the Cape of Good Hope. We spent four months there while the boat was being finished and outfitted. By the time we left, it felt like leaving a second home.

The Atlantic crossing was the biggest thing I'd ever done. Fourteen days offshore, no land, no other boats for days at a time. Just the two of us, the boat, and the sea. I'd been nervous about it for months. But when we were actually out there, it was the most peaceful I'd ever felt. There's something clarifying about being completely removed from the world. No news, no notifications, no decisions to make except the next watch change. Just the boat, and the wind, and the stars at night.

We saw dolphins nearly every day. One morning, a pod of them swam with us for almost two hours, riding the bow wave, crossing back and forth under the hulls. Yuka and I sat on the trampoline at the front of the boat and watched them and didn't say a word for a long time.

That's the thing about sailing that no one tells you before you do it. It's not about adventure. It's about presence. You are completely, unavoidably present. The sea doesn't let you be anywhere else.

---

## Step 2 — Clone your voice in ElevenLabs

1. Go to elevenlabs.io → VoiceLab → Add a New Voice → Instant Voice Clone
2. Upload your recording
3. Name it "Francesco" 
4. Done — your cloned voice is now available for generation

## Step 3 — Pick a Host voice

In ElevenLabs Voice Library, search for:
- A neutral male or female voice with slight British or American accent
- Suggestions to try: "Jessica", "Brian", "Callum"
- Pick whoever sounds like a credible podcast host alongside your voice

## Step 4 — Generate the audio

For each line in the script:
- Set voice to "Francesco" for FRANCESCO lines
- Set voice to your chosen Host for HOST lines
- Use model: "Eleven Multilingual v2" (handles both English and Japanese)
- Stability: 0.5 / Similarity: 0.75 (good starting point)

Export each line as an MP3, then stitch together in GarageBand or Audacity.

## Step 5 — Add music (optional but recommended)

Search "free podcast intro music sailing" on freemusicarchive.org or pixabay.com/music.
Fade in at the start, fade out under the first HOST line.

## Note on Japanese
ElevenLabs Multilingual v2 handles Japanese well with a cloned English voice —
the pronunciation will have a slight accent, which is authentic to who you are.
If you want native-quality Japanese, clone a separate Japanese-speaking voice for the Host.
