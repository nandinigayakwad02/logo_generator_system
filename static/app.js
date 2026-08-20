document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const logoForm = document.getElementById('logoForm');
  const brandNameInput = document.getElementById('brandName');
  const descriptionInput = document.getElementById('description');
  const colorPaletteInput = document.getElementById('colorPalette');
  const qualitySelect = document.getElementById('qualitySelect');
  const bgSelect = document.getElementById('bgSelect');
  
  const sparkIdeasBtn = document.getElementById('sparkIdeasBtn');
  const generateLogoBtn = document.getElementById('generateLogoBtn');
  
  const stylePresets = document.getElementById('stylePresets');
  const colorQuickTags = document.getElementById('colorQuickTags');
  
  const ideasContainer = document.getElementById('ideasContainer');
  const ideasGrid = document.getElementById('ideasGrid');
  const closeIdeasBtn = document.getElementById('closeIdeasBtn');
  
  const stageViewport = document.getElementById('stageViewport');
  const emptyState = document.getElementById('emptyState');
  const loaderState = document.getElementById('loaderState');
  const resultState = document.getElementById('resultState');
  const resultActions = document.getElementById('resultActions');
  const mockupContainer = document.getElementById('mockupContainer');
  const logoImage = document.getElementById('logoImage');
  
  const stageTabs = document.querySelectorAll('.stage-tab');
  
  const downloadBtn = document.getElementById('downloadBtn');
  const copyPromptBtn = document.getElementById('copyPromptBtn');
  const toggleBgBtn = document.getElementById('toggleBgBtn');
  const regenerateBtn = document.getElementById('regenerateBtn');
  
  const promptInspector = document.getElementById('promptInspector');
  const promptText = document.getElementById('promptText');
  
  const viewHistoryBtn = document.getElementById('viewHistoryBtn');
  const historyDrawer = document.getElementById('historyDrawer');
  const closeHistoryBtn = document.getElementById('closeHistoryBtn');
  const historyGrid = document.getElementById('historyGrid');
  const historyBadge = document.getElementById('historyBadge');
  
  const tipText = document.getElementById('tipText');

  // State Variables
  let selectedStyle = 'minimalist';
  let activeLogoData = null;
  let customPromptOverride = null;
  let currentBgMode = 0; // 0: light, 1: dark, 2: grey
  const bgModes = ['#ffffff', '#0f172a', '#e2e8f0'];

  const tips = [
    "GPT Image (gpt-image-1) creates stunningly detailed vector logos with transparent backgrounds.",
    "GPT-4 structures creative concepts, icon symbols, and typography directions for perfect prompts.",
    "Try switching to Business Card or T-Shirt tabs to see how your logo looks on merchandise!",
    "Monogram styles work amazingly well for tech and fashion brands with 2-3 word names.",
    "You can edit the prompt in the Inspector panel below to fine-tune icon symbols or colors!",
    "Transparent PNG output means your logo is ready to use instantly on any background."
  ];
  let tipInterval = null;

  // Initialize History Count
  fetchHistory();

  // Style Chip Click
  stylePresets.addEventListener('click', (e) => {
    const chip = e.target.closest('.preset-chip');
    if (!chip) return;
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    selectedStyle = chip.dataset.style;
  });

  // Color Tag Click
  colorQuickTags.addEventListener('click', (e) => {
    const tag = e.target.closest('.tag-chip');
    if (!tag) return;
    colorPaletteInput.value = tag.dataset.color;
  });

  // Spark Ideas Button (GPT-4)
  sparkIdeasBtn.addEventListener('click', async () => {
    const brand_name = brandNameInput.value.trim();
    const description = descriptionInput.value.trim();

    if (!brand_name || !description) {
      alert('Please fill in both Brand Name and Description to generate ideas.');
      return;
    }

    sparkIdeasBtn.disabled = true;
    sparkIdeasBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Brainstorming Concepts...';

    try {
      const res = await fetch('/api/generate-ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name,
          description,
          style: selectedStyle,
          colors: colorPaletteInput.value
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to generate ideas');
      }

      const data = await res.json();
      renderIdeas(data.concepts || []);
      ideasContainer.classList.remove('hidden');

    } catch (err) {
      alert(`Idea Generation Error: ${err.message}`);
    } finally {
      sparkIdeasBtn.disabled = false;
      sparkIdeasBtn.innerHTML = '<i class="fa-solid fa-lightbulb"></i> GPT Design Spark Ideas';
    }
  });

  closeIdeasBtn.addEventListener('click', () => {
    ideasContainer.classList.add('hidden');
  });

  function renderIdeas(concepts) {
    ideasGrid.innerHTML = '';
    concepts.forEach((concept, index) => {
      const card = document.createElement('div');
      card.className = 'idea-card';

      const colorStr = Array.isArray(concept.color_palette) ? concept.color_palette.join(', ') : String(concept.color_palette || '');
      const iconStr = Array.isArray(concept.icon_idea) ? concept.icon_idea.join(', ') : String(concept.icon_idea || '');
      const promptStr = String(concept.dalle_prompt || '');

      card.innerHTML = `
        <h4>Option ${index + 1}: ${escapeHtml(concept.title)}</h4>
        <p><strong>Icon:</strong> ${escapeHtml(iconStr)}</p>
        <p><strong>Colors:</strong> ${escapeHtml(colorStr)}</p>
        <div style="margin-top:6px;"><span class="idea-badge"><i class="fa-solid fa-check"></i> Select & Generate</span></div>
      `;

      card.addEventListener('click', () => {
        customPromptOverride = promptStr;
        colorPaletteInput.value = colorStr;
        promptText.value = promptStr;
        promptInspector.classList.remove('hidden');
        triggerLogoGeneration();
      });

      ideasGrid.appendChild(card);
    });
  }

  // Generate Logo Button
  generateLogoBtn.addEventListener('click', () => {
    customPromptOverride = null;
    triggerLogoGeneration();
  });

  async function triggerLogoGeneration() {
    const brand_name = brandNameInput.value.trim();
    const description = descriptionInput.value.trim();

    if (!brand_name || !description) {
      alert('Please fill in both Brand Name and Description.');
      return;
    }

    // Show Loader State
    showLoader();
    startTipRotation();

    try {
      const payload = {
        brand_name,
        description,
        style: selectedStyle,
        colors: colorPaletteInput.value,
        custom_prompt: customPromptOverride || (promptText.value ? promptText.value.trim() : null),
        quality: qualitySelect.value,
        background: bgSelect.value
      };

      const res = await fetch('/api/generate-logo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Logo generation failed');
      }

      const logoData = await res.json();
      activeLogoData = logoData;
      renderGeneratedResult(logoData);
      fetchHistory(); // refresh history count

    } catch (err) {
      alert(`Logo Generation Error: ${err.message}`);
      showEmptyState();
    } finally {
      stopTipRotation();
    }
  }

  function showLoader() {
    emptyState.classList.add('hidden');
    resultState.classList.add('hidden');
    resultActions.classList.add('hidden');
    loaderState.classList.remove('hidden');
  }

  function showEmptyState() {
    loaderState.classList.add('hidden');
    resultState.classList.add('hidden');
    resultActions.classList.add('hidden');
    emptyState.classList.remove('hidden');
  }

  function renderGeneratedResult(data) {
    loaderState.classList.add('hidden');
    emptyState.classList.add('hidden');

    logoImage.src = data.image_url;
    promptText.value = data.prompt;

    resultState.classList.remove('hidden');
    resultActions.classList.remove('hidden');
    promptInspector.classList.remove('hidden');
  }

  // Stage View Tabs
  stageTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      stageTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const view = tab.dataset.view;
      mockupContainer.className = `mockup-frame ${view}-mode`;
    });
  });

  // Action Bar Listeners
  downloadBtn.addEventListener('click', () => {
    if (!activeLogoData) return;
    const a = document.createElement('a');
    a.href = activeLogoData.image_url;
    a.download = `${activeLogoData.brand_name.replace(/\s+/g, '_')}_logo.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });

  copyPromptBtn.addEventListener('click', () => {
    const text = promptText.value;
    if (text) {
      navigator.clipboard.writeText(text);
      copyPromptBtn.innerHTML = '<i class="fa-solid fa-check"></i> Prompt Copied!';
      setTimeout(() => {
        copyPromptBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy DALL-E Prompt';
      }, 2000);
    }
  });

  toggleBgBtn.addEventListener('click', () => {
    currentBgMode = (currentBgMode + 1) % bgModes.length;
    mockupContainer.style.backgroundColor = bgModes[currentBgMode];
  });

  regenerateBtn.addEventListener('click', () => {
    triggerLogoGeneration();
  });

  // History Modal Logic
  viewHistoryBtn.addEventListener('click', () => {
    fetchHistory(true);
    historyDrawer.classList.remove('hidden');
  });

  closeHistoryBtn.addEventListener('click', () => {
    historyDrawer.classList.add('hidden');
  });

  async function fetchHistory(openModal = false) {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const history = await res.json();
        historyBadge.textContent = history.length;

        if (openModal) {
          renderHistoryGrid(history);
        }
      }
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  }

  function renderHistoryGrid(historyItems) {
    historyGrid.innerHTML = '';
    if (historyItems.length === 0) {
      historyGrid.innerHTML = '<p style="color:#94a3b8;">No logos generated yet.</p>';
      return;
    }

    historyItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'history-card';
      const dateStr = item.timestamp ? new Date(item.timestamp).toLocaleDateString() : '';
      card.innerHTML = `
        <img src="${item.image_url}" alt="${escapeHtml(item.brand_name)}" />
        <div class="title">${escapeHtml(item.brand_name)}</div>
        <div class="date">${dateStr} • ${escapeHtml(item.style || 'minimalist')}</div>
      `;

      card.addEventListener('click', () => {
        activeLogoData = item;
        brandNameInput.value = item.brand_name || '';
        descriptionInput.value = item.description || '';
        colorPaletteInput.value = item.colors || '';
        renderGeneratedResult(item);
        historyDrawer.classList.add('hidden');
      });

      historyGrid.appendChild(card);
    });
  }

  // Tip Rotation
  function startTipRotation() {
    let index = 0;
    tipText.textContent = tips[0];
    tipInterval = setInterval(() => {
      index = (index + 1) % tips.length;
      tipText.textContent = tips[index];
    }, 3500);
  }

  function stopTipRotation() {
    if (tipInterval) clearInterval(tipInterval);
  }

  function escapeHtml(val) {
    if (val === null || val === undefined) return '';
    const str = typeof val === 'string' ? val : JSON.stringify(val);
    return str.replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[m]);
  }
});
