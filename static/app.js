// ═══════════════════════════════════════════════════════════
// CSI Dashboard — Frontend Logic
// ═══════════════════════════════════════════════════════════

let queryCount = 0, totalScore = 0, cacheHits = 0, approvedCount = 0, isProcessing = false;

function sendExample(btn) {
    document.getElementById('chatInput').value = btn.textContent;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || isProcessing) return;

    isProcessing = true;
    document.getElementById('sendBtn').disabled = true;
    input.value = '';

    const welcome = document.querySelector('.welcome');
    if (welcome) welcome.remove();

    addMessage('user', text);
    resetPipeline();
    setStageStatus('guardrails', 'active');
    const typingId = addTyping();

    try {
        const t0 = Date.now();
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text }),
        });

        const raw = await res.text();
        let data;
        try { data = JSON.parse(raw); } catch {
            removeTyping(typingId);
            addMessage('system', 'Server returned invalid JSON.');
            resetPipeline();
            isProcessing = false;
            document.getElementById('sendBtn').disabled = false;
            return;
        }

        const elapsed = Date.now() - t0;
        removeTyping(typingId);
        updatePipeline(data);

        const latencyEl = document.getElementById('latencyDisplay');
        latencyEl.querySelector('span').textContent = `${(elapsed / 1000).toFixed(1)}s`;

        if (data.blocked) {
            addMessage('system', data.blocked_reason);
        } else {
            addMessage('assistant', data.response || 'No response generated.');
        }

        queryCount++;
        updateMetrics(data);

    } catch (err) {
        removeTyping(typingId);
        addMessage('system', `Connection error: ${err.message}`);
        resetPipeline();
    }

    isProcessing = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
}

// ─── Messages ──────────────────────────────────────────────

function addMessage(role, text) {
    const c = document.getElementById('chatMessages');
    const el = document.createElement('div');
    el.className = `message ${role}`;
    const av = role === 'user' ? 'U' : role === 'assistant' ? 'AI' : '!';

    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.split('\n\n').map(p => `<p>${p}</p>`).join('');
    html = html.replace(/\n/g, '<br>');

    el.innerHTML = `<div class="msg-avatar">${av}</div><div class="msg-body">${html}</div>`;
    c.appendChild(el);
    c.scrollTop = c.scrollHeight;
}

function addTyping() {
    const c = document.getElementById('chatMessages');
    const id = 'typing-' + Date.now();
    const el = document.createElement('div');
    el.className = 'message assistant';
    el.id = id;
    el.innerHTML = `<div class="msg-avatar">AI</div><div class="msg-body"><div class="typing"><span></span><span></span><span></span></div></div>`;
    c.appendChild(el);
    c.scrollTop = c.scrollHeight;
    return id;
}

function removeTyping(id) { document.getElementById(id)?.remove(); }

function clearChat() {
    document.getElementById('chatMessages').innerHTML = '';
    resetPipeline();
    queryCount = 0; totalScore = 0; cacheHits = 0; approvedCount = 0;
    document.getElementById('metric-queries').textContent = '0';
    document.getElementById('metric-score').textContent = '--';
    document.getElementById('metric-cache').textContent = '0%';
    document.getElementById('metric-approved').textContent = '--';
    document.getElementById('latencyDisplay').querySelector('span').textContent = '--';
}

// ─── Pipeline ──────────────────────────────────────────────

function resetPipeline() {
    ['guardrails','cache','agent1','agent2','agent3'].forEach(s => {
        document.getElementById(`stage-${s}`).className = 'stage';
        document.getElementById(`status-${s}`).textContent = 'Idle';
    });
    ['gr-pii','gr-injection','gr-topic','cache-result',
     'a1-intent','a1-sentiment','a1-urgency','a2-docs',
     'a3-faith','a3-relevance','a3-decision'].forEach(id => {
        const el = document.getElementById(id);
        el.textContent = '--';
        el.className = 'val';
    });
}

function setStageStatus(stage, status) {
    document.getElementById(`stage-${stage}`).className = `stage ${status}`;
    const tag = document.getElementById(`status-${stage}`);
    tag.textContent = { active: 'Running', complete: 'Done', blocked: 'Blocked' }[status] || status;
}

function setVal(id, text, cls) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.className = `val${cls ? ' ' + cls : ''}`;
}

function updatePipeline(data) {
    // Guardrails — show specific check results
    if (data.guardrails) {
        const gr = data.guardrails;
        setStageStatus('guardrails', gr.is_safe ? 'complete' : 'blocked');

        // PII: show what was found
        setVal('gr-pii', gr.pii_detected?.length ? `Redacted: ${gr.pii_detected.join(', ')}` : 'Clean', gr.pii_detected?.length ? 'warn' : 'good');

        // Injection: show if this specific check blocked
        if (gr.injection_blocked) {
            setVal('gr-injection', 'BLOCKED', 'bad');
        } else {
            setVal('gr-injection', 'Safe', 'good');
        }

        // Topic: show if this specific check blocked
        if (gr.topic_blocked) {
            setVal('gr-topic', 'OFF-TOPIC', 'bad');
        } else {
            setVal('gr-topic', 'On-topic', 'good');
        }
    }

    if (data.blocked) {
        setVal('cache-result', 'Skipped', '');
        setVal('a1-intent', 'Skipped', '');
        setVal('a2-docs', 'Skipped', '');
        setVal('a3-decision', 'Skipped', '');
        return;
    }

    // Cache
    setStageStatus('cache', 'complete');
    if (data.cache_hit) {
        setVal('cache-result', `HIT (${Math.round((data.cache_similarity || 1) * 100)}%)`, 'good');
        setStageStatus('agent1', 'complete');
        setStageStatus('agent2', 'complete');
        setStageStatus('agent3', 'complete');
        setVal('a1-intent', 'Cached', 'good');
        setVal('a2-docs', 'Cached', 'good');
        setVal('a3-decision', 'CACHED', 'good');
        return;
    }
    setVal('cache-result', 'MISS', 'warn');

    // Agent 1
    setStageStatus('agent1', 'complete');
    if (data.classification) {
        const c = data.classification;
        setVal('a1-intent', c.intent || 'general', '');
        setVal('a1-sentiment', c.sentiment || 'neutral',
            { positive: 'good', neutral: '', negative: 'warn', frustrated: 'bad' }[c.sentiment] || '');
        setVal('a1-urgency', c.urgency || 'low',
            { low: 'good', medium: '', high: 'warn', critical: 'bad' }[c.urgency] || '');
    }

    // Agent 2
    setStageStatus('agent2', 'complete');
    setVal('a2-docs', data.retrieved_docs?.length ? `${data.retrieved_docs.length} chunks` : 'Retrieved', '');

    // Agent 3
    setStageStatus('agent3', 'complete');
    if (data.evaluation) {
        const e = data.evaluation;
        const f = parseFloat(e.faithfulness) || 0;
        const r = parseFloat(e.answer_relevance) || 0;
        const d = (e.decision || '').toLowerCase();
        setVal('a3-faith', f.toFixed(2), f >= .8 ? 'good' : f >= .6 ? 'warn' : 'bad');
        setVal('a3-relevance', r.toFixed(2), r >= .8 ? 'good' : r >= .6 ? 'warn' : 'bad');
        setVal('a3-decision', d.toUpperCase(), { approve: 'good', revise: 'warn', escalate: 'bad' }[d] || '');
    }
}

function updateMetrics(data) {
    document.getElementById('metric-queries').textContent = queryCount;
    if (data.evaluation?.overall_score) {
        totalScore += data.evaluation.overall_score;
        document.getElementById('metric-score').textContent = (totalScore / queryCount).toFixed(2);
    }
    if (data.cache_hit) cacheHits++;
    document.getElementById('metric-cache').textContent = queryCount > 0 ? Math.round(cacheHits / queryCount * 100) + '%' : '0%';
    if (data.evaluation?.decision?.toLowerCase() === 'approve') approvedCount++;
    document.getElementById('metric-approved').textContent = queryCount > 0 ? Math.round(approvedCount / queryCount * 100) + '%' : '--';
}
