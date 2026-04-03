const DEMO_BASE_PATH = "./data/public-goods-demo/";
const CHART_PADDING = { left: 56, right: 18, top: 16, bottom: 34 };

const COLORS = {
  chartBackground: "#f9f4eb",
  chartGrid: "rgba(43, 58, 43, 0.13)",
  chartAxis: "rgba(29, 40, 29, 0.4)",
  chartMarker: "#1d2f25",
  chartText: "#4f5f4b",
  prey: "#2d5fba",
  predatorLow: [182, 70, 40],
  predatorHigh: [121, 30, 36],
  grassLow: [244, 239, 229],
  grassHigh: [79, 138, 87],
  populationPredator: "#b64628",
  populationPrey: "#2d5fba",
  trait: "#8c6a15",
};

const elements = {
  bundleNote: document.getElementById("bundle-note"),
  statusPill: document.getElementById("status-pill"),
  playPauseButton: document.getElementById("play-pause-button"),
  restartButton: document.getElementById("restart-button"),
  speedSelect: document.getElementById("speed-select"),
  frameSlider: document.getElementById("frame-slider"),
  frameIndexLabel: document.getElementById("frame-index-label"),
  worldCanvas: document.getElementById("world-canvas"),
  populationChart: document.getElementById("population-chart"),
  traitChart: document.getElementById("trait-chart"),
  stepLabel: document.getElementById("step-label"),
  viewerCaption: document.getElementById("viewer-caption"),
  predatorCount: document.getElementById("predator-count"),
  preyCount: document.getElementById("prey-count"),
  meanTrait: document.getElementById("mean-trait"),
  traitVariance: document.getElementById("trait-variance"),
  grassMean: document.getElementById("grass-mean"),
  totalEnergy: document.getElementById("total-energy"),
  samplingDetail: document.getElementById("sampling-detail"),
  seedDetail: document.getElementById("seed-detail"),
  outcomeDetail: document.getElementById("outcome-detail"),
};

const state = {
  manifest: null,
  summary: null,
  currentFrameIndex: 0,
  currentFrame: null,
  renderToken: 0,
  chunkCache: new Map(),
  playing: false,
  framesPerSecond: 8,
  animationFrameId: null,
  lastTimestamp: 0,
  populationChartBase: null,
  traitChartBase: null,
};


function setStatus(text, isError = false) {
  elements.statusPill.textContent = text;
  elements.statusPill.style.background = isError ? "rgba(160, 44, 44, 0.12)" : "rgba(37, 87, 67, 0.12)";
  elements.statusPill.style.color = isError ? "#8a1d1d" : "#255743";
}


function formatValue(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return Number(value).toFixed(digits);
}


function mixColor(start, end, mix) {
  const boundedMix = Math.max(0, Math.min(1, mix));
  const blended = start.map((value, index) => {
    return Math.round(value + (end[index] - value) * boundedMix);
  });
  return `rgb(${blended[0]}, ${blended[1]}, ${blended[2]})`;
}


function predatorColor(trait) {
  return mixColor(COLORS.predatorLow, COLORS.predatorHigh, Number(trait) || 0);
}


async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}


function getFrameCount() {
  return state.manifest ? Number(state.manifest.sampled_frame_count) : 0;
}


function getMaxFrameIndex() {
  return Math.max(0, getFrameCount() - 1);
}


function getChunkIndex(frameIndex) {
  return Math.floor(frameIndex / Number(state.manifest.frame_chunk_size));
}


async function loadChunk(chunkIndex) {
  if (state.chunkCache.has(chunkIndex)) {
    return state.chunkCache.get(chunkIndex);
  }

  const chunkPath = `${DEMO_BASE_PATH}${state.manifest.frame_paths[chunkIndex]}`;
  const chunk = await loadJson(chunkPath);
  state.chunkCache.set(chunkIndex, chunk);
  return chunk;
}


async function getFrame(frameIndex) {
  const chunkIndex = getChunkIndex(frameIndex);
  const chunk = await loadChunk(chunkIndex);
  return chunk.frames[frameIndex - chunk.start_frame_index];
}


function prefetchNextChunk(frameIndex) {
  const nextChunkIndex = getChunkIndex(frameIndex) + 1;
  if (nextChunkIndex >= state.manifest.frame_paths.length || state.chunkCache.has(nextChunkIndex)) {
    return;
  }
  void loadChunk(nextChunkIndex).catch(() => {});
}


function updatePlaybackButton() {
  elements.playPauseButton.textContent = state.playing ? "Pause" : "Play";
}


function updateStaticDetails() {
  elements.bundleNote.textContent =
    `${state.manifest.title}. ${state.manifest.sampled_frame_count} sampled frames from ` +
    `${state.manifest.simulation_steps.toLocaleString()} simulation steps.`;
  elements.samplingDetail.textContent =
    `1 replay frame every ${state.manifest.sample_every_steps} model steps`;
  elements.seedDetail.textContent =
    state.manifest.random_seed === null ? "None" : String(state.manifest.random_seed);
  elements.outcomeDetail.textContent = state.summary.success
    ? "Reached full configured horizon"
    : `Stopped at step ${state.summary.extinction_step}`;
}


function chartRect(canvas) {
  return {
    left: CHART_PADDING.left,
    top: CHART_PADDING.top,
    right: canvas.width - CHART_PADDING.right,
    bottom: canvas.height - CHART_PADDING.bottom,
  };
}


function drawChartScaffold(ctx, canvas, maxValue) {
  const rect = chartRect(canvas);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = COLORS.chartBackground;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const plotWidth = rect.right - rect.left;
  const plotHeight = rect.bottom - rect.top;
  const yTicks = 4;

  ctx.strokeStyle = COLORS.chartGrid;
  ctx.lineWidth = 1;
  for (let tick = 0; tick <= yTicks; tick += 1) {
    const ratio = tick / yTicks;
    const y = rect.bottom - ratio * plotHeight;
    ctx.beginPath();
    ctx.moveTo(rect.left, y);
    ctx.lineTo(rect.right, y);
    ctx.stroke();
  }

  ctx.strokeStyle = COLORS.chartAxis;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(rect.left, rect.top);
  ctx.lineTo(rect.left, rect.bottom);
  ctx.lineTo(rect.right, rect.bottom);
  ctx.stroke();

  ctx.fillStyle = COLORS.chartText;
  ctx.font = "12px IBM Plex Mono, monospace";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let tick = 0; tick <= yTicks; tick += 1) {
    const ratio = tick / yTicks;
    const y = rect.bottom - ratio * plotHeight;
    const value = maxValue * ratio;
    ctx.fillText(value.toFixed(maxValue <= 1 ? 2 : 0), rect.left - 8, y);
  }

  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText("0", rect.left, rect.bottom + 10);
  ctx.fillText(
    state.summary.steps_done.toLocaleString(),
    rect.right,
    rect.bottom + 10,
  );

  return rect;
}


function drawSeries(ctx, rect, values, color, maxValue) {
  if (!values.length) {
    return;
  }
  const plotWidth = rect.right - rect.left;
  const plotHeight = rect.bottom - rect.top;
  const denominator = Math.max(1, values.length - 1);

  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;

  let penDown = false;
  values.forEach((value, index) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      penDown = false;
      return;
    }
    const x = rect.left + (index / denominator) * plotWidth;
    const y = rect.bottom - (Number(value) / Math.max(maxValue, 1e-9)) * plotHeight;
    if (!penDown) {
      ctx.moveTo(x, y);
      penDown = true;
      return;
    }
    ctx.lineTo(x, y);
  });

  ctx.stroke();
}


function buildPopulationChartBase() {
  const canvas = document.createElement("canvas");
  canvas.width = elements.populationChart.width;
  canvas.height = elements.populationChart.height;
  const ctx = canvas.getContext("2d");
  const maxValue = Math.max(
    1,
    ...state.summary.pred_hist,
    ...state.summary.prey_hist,
  );
  const rect = drawChartScaffold(ctx, canvas, maxValue);
  drawSeries(ctx, rect, state.summary.pred_hist, COLORS.populationPredator, maxValue);
  drawSeries(ctx, rect, state.summary.prey_hist, COLORS.populationPrey, maxValue);
  return canvas;
}


function buildTraitChartBase() {
  const canvas = document.createElement("canvas");
  canvas.width = elements.traitChart.width;
  canvas.height = elements.traitChart.height;
  const ctx = canvas.getContext("2d");
  const rect = drawChartScaffold(ctx, canvas, 1.0);
  drawSeries(ctx, rect, state.summary.mean_trait_hist, COLORS.trait, 1.0);
  return canvas;
}


function drawChartMarker(targetCanvas, baseCanvas, step) {
  const ctx = targetCanvas.getContext("2d");
  ctx.clearRect(0, 0, targetCanvas.width, targetCanvas.height);
  ctx.drawImage(baseCanvas, 0, 0);

  const rect = chartRect(targetCanvas);
  const plotWidth = rect.right - rect.left;
  const markerX = rect.left + (Number(step) / Math.max(1, state.summary.steps_done)) * plotWidth;

  ctx.strokeStyle = COLORS.chartMarker;
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(markerX, rect.top);
  ctx.lineTo(markerX, rect.bottom);
  ctx.stroke();
  ctx.setLineDash([]);
}


function drawWorld(frame) {
  const canvas = elements.worldCanvas;
  const ctx = canvas.getContext("2d");
  const gridWidth = Number(state.manifest.grid_width);
  const gridHeight = Number(state.manifest.grid_height);
  const cellWidth = canvas.width / gridWidth;
  const cellHeight = canvas.height / gridHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < gridHeight; y += 1) {
    for (let x = 0; x < gridWidth; x += 1) {
      const grassValue = frame.grass[y * gridWidth + x] / Number(state.manifest.grass_quantization_levels);
      ctx.fillStyle = mixColor(COLORS.grassLow, COLORS.grassHigh, grassValue);
      ctx.fillRect(
        x * cellWidth,
        y * cellHeight,
        Math.ceil(cellWidth) + 0.5,
        Math.ceil(cellHeight) + 0.5,
      );
    }
  }

  ctx.fillStyle = COLORS.prey;
  frame.preys.forEach(([x, y]) => {
    ctx.fillRect(
      x * cellWidth + cellWidth * 0.18,
      y * cellHeight + cellHeight * 0.18,
      Math.max(2, cellWidth * 0.64),
      Math.max(2, cellHeight * 0.64),
    );
  });

  frame.predators.forEach(([x, y, trait]) => {
    const centerX = (x + 0.5) * cellWidth;
    const centerY = (y + 0.5) * cellHeight;
    const radius = Math.max(2.5, Math.min(cellWidth, cellHeight) * 0.34);
    ctx.beginPath();
    ctx.fillStyle = predatorColor(trait);
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "rgba(18, 18, 18, 0.35)";
    ctx.lineWidth = 1;
    ctx.stroke();
  });
}


function updateStats(frame) {
  elements.frameSlider.value = String(state.currentFrameIndex);
  elements.frameIndexLabel.textContent =
    `${state.currentFrameIndex + 1} / ${getFrameCount()}`;
  elements.stepLabel.textContent = `Step ${Number(frame.step).toLocaleString()}`;
  elements.viewerCaption.textContent =
    `Replay frames are sampled every ${state.manifest.sample_every_steps} simulation steps.`;

  elements.predatorCount.textContent = String(frame.stats.predator_count);
  elements.preyCount.textContent = String(frame.stats.prey_count);
  elements.meanTrait.textContent = formatValue(frame.stats.mean_trait, 3);
  elements.traitVariance.textContent = formatValue(frame.stats.trait_variance, 4);
  elements.grassMean.textContent = formatValue(frame.stats.grass_mean, 3);
  elements.totalEnergy.textContent = formatValue(frame.stats.total_energy, 1);
}


function render() {
  if (!state.currentFrame) {
    return;
  }
  drawWorld(state.currentFrame);
  updateStats(state.currentFrame);
  drawChartMarker(elements.populationChart, state.populationChartBase, state.currentFrame.step);
  drawChartMarker(elements.traitChart, state.traitChartBase, state.currentFrame.step);
}


async function setFrameIndex(frameIndex) {
  if (!state.manifest) {
    return;
  }
  const clamped = Math.max(0, Math.min(getMaxFrameIndex(), frameIndex));
  const token = ++state.renderToken;
  const frame = await getFrame(clamped);
  if (token !== state.renderToken) {
    return;
  }
  state.currentFrameIndex = clamped;
  state.currentFrame = frame;
  render();
  prefetchNextChunk(clamped);
}


function stopPlayback() {
  state.playing = false;
  state.lastTimestamp = 0;
  updatePlaybackButton();
  if (state.animationFrameId !== null) {
    cancelAnimationFrame(state.animationFrameId);
    state.animationFrameId = null;
  }
}


function animationLoop(timestamp) {
  if (!state.playing) {
    state.animationFrameId = null;
    return;
  }

  if (!state.lastTimestamp) {
    state.lastTimestamp = timestamp;
  }

  const msPerFrame = 1000 / state.framesPerSecond;
  if (timestamp - state.lastTimestamp >= msPerFrame) {
    state.lastTimestamp = timestamp;
    if (state.currentFrameIndex >= getMaxFrameIndex()) {
      stopPlayback();
      return;
    }
    void setFrameIndex(state.currentFrameIndex + 1);
  }

  state.animationFrameId = requestAnimationFrame(animationLoop);
}


function startPlayback() {
  if (!state.manifest || state.playing) {
    return;
  }
  state.playing = true;
  state.lastTimestamp = 0;
  updatePlaybackButton();
  state.animationFrameId = requestAnimationFrame(animationLoop);
}


function togglePlayback() {
  if (state.playing) {
    stopPlayback();
    return;
  }
  startPlayback();
}


async function boot() {
  setStatus("Loading");
  try {
    state.manifest = await loadJson(`${DEMO_BASE_PATH}manifest.json`);
    state.summary = await loadJson(`${DEMO_BASE_PATH}${state.manifest.summary_path}`);

    elements.frameSlider.max = String(getMaxFrameIndex());
    elements.speedSelect.value = String(state.framesPerSecond);
    updateStaticDetails();

    state.populationChartBase = buildPopulationChartBase();
    state.traitChartBase = buildTraitChartBase();

    await setFrameIndex(0);
    setStatus("Ready");
    updatePlaybackButton();
  } catch (error) {
    console.error(error);
    setStatus("Load error", true);
    elements.bundleNote.textContent =
      "Failed to load the replay bundle. If you are previewing locally, serve the repository over HTTP.";
    elements.viewerCaption.textContent = String(error);
  }
}


elements.playPauseButton.addEventListener("click", () => {
  togglePlayback();
});

elements.restartButton.addEventListener("click", () => {
  stopPlayback();
  void setFrameIndex(0);
});

elements.speedSelect.addEventListener("change", (event) => {
  state.framesPerSecond = Number(event.target.value);
});

elements.frameSlider.addEventListener("input", (event) => {
  stopPlayback();
  void setFrameIndex(Number(event.target.value));
});

void boot();
