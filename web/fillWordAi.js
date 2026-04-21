async function fillWordAiDraft() {
  const word = document.getElementById('wf-id').value.trim();
  if (!word) { alert('단어(id)를 먼저 입력해주세요.'); return; }
  
  const btn = event.currentTarget || event.target;
  const originalText = btn.textContent;
  btn.textContent = '가져오는 중...';
  btn.disabled = true;
  
  try {
    const payload = { word: word };
    const res = await fetch('/api/batch/ai_draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'AI 초안 실패');
    
    // 기본 도메인
    if (data.domain) {
      document.getElementById('wf-domain').innerHTML = ''; // 초기화
      initMultiInput('wf-domain', [data.domain], 'domain-list');
    }
    
    // 번역 및 설명
    if (data.ko) document.getElementById('wf-ko').value = data.ko;
    if (data.en) document.getElementById('wf-en').value = data.en;
    if (data.ja) document.getElementById('wf-ja').value = data.ja;
    if (data.zh) document.getElementById('wf-zh').value = data.zh;
    if (data.description_ko) document.getElementById('wf-desc').value = data.description_ko;
    if (data.description_en) document.getElementById('wf-desc-en').value = data.description_en;
    
    // 형태소/관계어 (있으면 채우기)
    if (data.abbr) document.getElementById('wf-abbr').value = data.abbr;
    if (data.from) document.getElementById('wf-from').value = data.from;
    
    if (data.variants && data.variants.length > 0) {
      document.getElementById('wf-variants').value = data.variants.map(v => `${v.type}:${v.value}`).join('\n');
    }
    if (data.synonyms && data.synonyms.length > 0) {
      document.getElementById('wf-synonyms').value = data.synonyms.join(', ');
    }
    if (data.antonyms && data.antonyms.length > 0) {
      document.getElementById('wf-antonyms').value = data.antonyms.join(', ');
    }
    if (data.source_urls && data.source_urls.length > 0) {
      document.getElementById('wf-urls').value = data.source_urls.join('\n');
    }
    if (data.not_terms && data.not_terms.length > 0) {
      document.getElementById('wf-not').value = data.not_terms.join(', ');
    } else if (data.not && data.not.length > 0) {
      document.getElementById('wf-not').value = data.not.join(', ');
    }
    
  } catch(err) {
    alert(err.message);
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}
