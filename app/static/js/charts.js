// ==========================================================================
// Face Recognition Management System (FRMS) - Chart.js Visualizations
// ==========================================================================

function renderAttendanceTrendChart(canvasId, trendData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.05)";
  const textColor = isDark ? "#94a3b8" : "#64748b";

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: trendData.labels || [],
      datasets: [
        {
          label: "On-Time Present",
          data: trendData.present || [],
          backgroundColor: "#10b981",
          borderRadius: 6,
        },
        {
          label: "Late Arrivals",
          data: trendData.late || [],
          backgroundColor: "#f59e0b",
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { color: textColor, font: { weight: "600" } },
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor },
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, stepSize: 1 },
          beginAtZero: true,
        },
      },
    },
  });
}

function renderVerificationBreakdownChart(canvasId, breakdownData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const textColor = isDark ? "#94a3b8" : "#64748b";

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: breakdownData.labels || [],
      datasets: [
        {
          data: breakdownData.counts || [],
          backgroundColor: [
            "#10b981", // Success / Match
            "#ef4444", // Mismatch
            "#64748b", // No face
            "#f59e0b", // Multiple faces
            "#06b6d4", // Poor quality
            "#8b5cf6", // Spoof detected
          ],
          borderWidth: 2,
          borderColor: isDark ? "#131b2e" : "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: textColor, boxWidth: 12, padding: 15 },
        },
      },
      cutout: "68%",
    },
  });
}

window.renderAttendanceTrendChart = renderAttendanceTrendChart;
window.renderVerificationBreakdownChart = renderVerificationBreakdownChart;
