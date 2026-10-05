# Netra AI - Hackathon Pitch & Judge Demonstration Guide

---

## 1. The 2-Minute Hackathon Pitch Script

> **Time: 120 seconds | Delivery: Confident, empathetic, and clear**

### [0:00 - 0:25] The Problem
*"Over 40 million visually impaired people worldwide—and more than 8 million in India alone—navigate city streets every day. But our streets aren't built for accessibility. Open drains, sudden descending stairs, low construction poles, speeding auto-rickshaws, and potholes turn an ordinary walk into a hazardous challenge.*

*Traditional white canes only detect obstacles once you've already touched them—at foot level. Commercial AI smart glasses cost upwards of **\$3,000 to \$5,000 (over ₹2.5 Lakhs)**, putting independence far out of reach for 99% of people."*

### [0:25 - 0:55] The Solution
*"Meet **Netra**—your phone just got eyes.*

*Netra turns any smartphone into an intelligent spatial guide dog. Using real-time computer vision, Netra scans the user's path, estimates direction and distance, and speaks out loud from the exact side obstacles appear—in Hindi or English.*

*A car coming on your left? You hear an urgent beep in your left ear. A person 3 metres ahead? Netra announces 'Person, ahead, 3 metres'. Clean, spatial, and intuitive."*

### [0:55 - 1:25] The Innovation & Engineering
*"What makes Netra unique? Three breakthroughs:*
1. **Zero Hardware Cost & Zero Install Barrier**: Runs entirely as a progressive web app directly in the mobile browser. No app store download needed, no expensive gadgets required.
2. **Directional Spatial Audio**: We built a custom Web Audio synthesizer that pans stereo sound in real time—closer obstacles produce a higher pitch and faster beep cadence.
3. **Privacy by Design**: Live camera video never touches a hard drive. It is evaluated in volatile memory and destroyed immediately—guaranteeing 100% privacy."*

### [1:25 - 1:50] The Impact
*"Netra bridges safety and dignity. From automated traffic-light reading that tells you when it's safe to cross, to fall detection that automatically generates pre-filled WhatsApp distress links for family members with GPS coordinates.*

*Best of all: it costs **₹0**."*

### [1:50 - 2:00] The Closing Call
*"Independence shouldn't cost a fortune. With Netra, every smartphone becomes a pair of eyes.*  
*Thank you! Let me show you Netra in action."*

---

## 2. Step-by-Step Live Demo Script for Judges

### Step 1: The Sound & Spatial Audio Demo (No Camera Needed)
1. Open `http://127.0.0.1:8000/demo/` on your laptop or phone.
2. Put the earphones or speaker volume up.
3. Click **"Left Ear"** and **"Right Ear"** under *Test Directional Stereo Beeps*. Show judges how the audio physically pans to the correct side.
4. Click **"Pedestrian Ahead (3m)"** -> Netra announces: *"Person, ahead, 3.0 metres"*.
5. Click **"Speeding Car (5m)"** -> Immediate urgent left-panned warning beep and speech.
6. Click **"Toggle Traffic Light"** -> Netra announces: *"Red light. Stop and wait"* followed by *"Green light. You can cross safely"*.

### Step 2: The Live Camera Navigation
1. Open `http://127.0.0.1:8000/navigate/`.
2. Tap **"Start Walking"**. Show the live video feed streaming to the server at 15 FPS.
3. Show how detected people or obstacles get bounding boxes, distance badges, and plot onto the top-down spatial radar in real time.
4. Tap **"Describe Scene"** -> Netra generates a natural sentence summary: *"A person is right ahead, 2.5 meters away."*

### Step 3: Safety Distress & Emergency SOS
1. Show the Settings page (`/settings/`) with Aunt Sarah saved as an emergency contact.
2. Demonstrate how a fall or SOS trigger instantly produces a ready-to-open WhatsApp link:  
   `https://wa.me/919876543210?text=EMERGENCY:+Netra+detected+a+fall...+Location:+https://maps.google.com/?q=28.61,77.20`

---

## 3. Competitive Advantage Matrix

| Feature | Netra AI | OrCam MyEye | Envision AI | Seeing AI (Microsoft) |
| :--- | :---: | :---: | :---: | :---: |
| **Cost** | **Free ($0)** | \$4,250 | \$249/yr | Free |
| **Installation** | **Zero Install (PWA)** | Proprietary Hardware | App Store Install | iOS App Store Only |
| **Bilingual Hindi + English** | **Yes** | Limited | Partial | No |
| **3D Directional Spatial Beeps** | **Yes** | No | No | No |
| **Top-Down Radar View** | **Yes** | No | No | No |
| **Emergency Fall SOS Links** | **Yes** | No | No | No |
| **Zero Video Disk Persistence** | **Yes (RAM only)** | Unknown | Cloud Stored | Cloud Stored |

---

## 4. Honest Safety Disclaimers & Limitations

* **Complementary Aid**: Netra is designed as an assistive aid to complement a traditional white cane or guide dog, **not** to replace them. White canes provide essential tactile ground feedback that cameras cannot replace.
* **Monocular Distance Approximation**: Distance is estimated using known real-world obstacle heights and pinhole optics formulas. It is approximate (±0.3m).
* **Lighting Conditions**: Like human eyes, cameras perform suboptimally in pitch darkness or intense blinding glare.
