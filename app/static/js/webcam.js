// ==========================================================================
// Face Recognition Management System (FRMS) - Webcam Controller
// Handles MediaDevices getUserMedia, live validation, canvas capture
// ==========================================================================

class WebcamController {
  constructor(options = {}) {
    this.videoEl = null;
    this.stream = null;
    this.deviceId = options.deviceId || null;
    this.facingMode = options.facingMode || "user";
    this.liveCheckInterval = null;
    this.onStatusChange = options.onStatusChange || null;
    this.onQualityUpdate = options.onQualityUpdate || null;
  }

  // Start webcam stream
  async start(videoElement) {
    this.videoEl = typeof videoElement === "string" ? document.getElementById(videoElement) : videoElement;
    if (!this.videoEl) {
      throw new Error("Webcam video element not found.");
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Camera API is not supported in this browser or environment (requires HTTPS or localhost).");
    }

    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        deviceId: this.deviceId ? { exact: this.deviceId } : undefined,
        facingMode: this.deviceId ? undefined : this.facingMode,
      },
      audio: false,
    };

    try {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (constraintErr) {
        console.warn("Retrying with default unconstrained video stream...", constraintErr);
        this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }
      this.videoEl.muted = true;
      this.videoEl.playsInline = true;
      this.videoEl.setAttribute("playsinline", "");
      this.videoEl.setAttribute("muted", "");
      this.videoEl.srcObject = this.stream;
      try {
        await this.videoEl.play();
      } catch (playErr) {
        console.warn("video.play() autoplay exception handled:", playErr);
      }

      if (this.onStatusChange) {
        this.onStatusChange({ status: "streaming", message: "Camera connected successfully." });
      }

      await this.populateCameraSelect();
      return true;
    } catch (err) {
      console.error("Camera access error:", err);
      let userMsg = "Camera access failed: " + err.message;
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        userMsg = "Camera permission denied. Please allow camera in browser address bar.";
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        userMsg = "No webcam detected on this device.";
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        userMsg = "Webcam is in use by another app or browser window.";
      }
      if (this.onStatusChange) {
        this.onStatusChange({ status: "error", message: userMsg, error: err });
      }
      throw new Error(userMsg);
    }
  }

  // Stop camera and release tracks
  stop() {
    if (this.liveCheckInterval) {
      clearInterval(this.liveCheckInterval);
      this.liveCheckInterval = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    if (this.videoEl) {
      this.videoEl.srcObject = null;
    }

    if (this.onStatusChange) {
      this.onStatusChange({ status: "stopped", message: "Camera turned off." });
    }
  }

  // Enumerate and populate camera selector dropdown
  async populateCameraSelect(selectElementId = "cameraSelect") {
    const select = document.getElementById(selectElementId);
    if (!select) return;

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter((d) => d.kind === "videoinput");

      select.innerHTML = "";
      videoDevices.forEach((device, idx) => {
        const option = document.createElement("option");
        option.value = device.deviceId;
        option.text = device.label || `Camera ${idx + 1}`;
        if (this.deviceId === device.deviceId) option.selected = true;
        select.appendChild(option);
      });

      if (videoDevices.length > 1) {
        select.parentElement?.classList.remove("d-none");
      }
    } catch (e) {
      console.warn("Could not list video devices:", e);
    }
  }

  // Switch camera device
  async switchCamera(newDeviceId) {
    this.deviceId = newDeviceId;
    this.stop();
    if (this.videoEl) {
      await this.start(this.videoEl);
    }
  }

  // Capture current video frame to JPEG base64 string
  captureBase64(quality = 0.92) {
    if (!this.videoEl || !this.stream) {
      throw new Error("Cannot capture frame: Camera is not active.");
    }

    const canvas = document.createElement("canvas");
    canvas.width = this.videoEl.videoWidth || 640;
    canvas.height = this.videoEl.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    // Un-mirror image on capture so saved embedding matches real face orientation
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(this.videoEl, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL("image/jpeg", quality);
  }

  // Starts lightweight background quality & face detection check
  startLiveAnalysis(intervalMs = 1500) {
    if (this.liveCheckInterval) clearInterval(this.liveCheckInterval);

    this.liveCheckInterval = setInterval(async () => {
      if (!this.stream || !this.videoEl || this.videoEl.paused) return;

      try {
        const frameData = this.captureBase64(0.7);
        const res = await fetch("/api/face/detect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: frameData }),
        });

        if (res.ok) {
          const data = await res.json();
          if (this.onQualityUpdate) {
            this.onQualityUpdate(data);
          }
        }
      } catch (err) {
        // Silent catch for live polling frame checks
      }
    }, intervalMs);
  }
}

window.WebcamController = WebcamController;
