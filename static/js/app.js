
async function loadLeaderboard(){
  const chartEl = document.getElementById('scoreChart');
  if(!chartEl) return;
  const res = await fetch('/api/leaderboard');
  const data = await res.json();
  const labels = data.map(d=>d.name);
  const scores = data.map(d=>d.score);
  const colors = scores.map((_,i)=> i<5 ? 'rgba(128,0,64,0.8)' : 'rgba(128,0,64,0.3)');
  new Chart(chartEl, {
    type:'bar',
    data:{labels, datasets:[{label:'Top Scores', data:scores, backgroundColor:colors}]},
    options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true,max:100}}}
  });
  const list = document.getElementById('lb-list');
  list.innerHTML = data.map((d,i)=>`<div>${i+1}. <strong>${d.name}</strong> — ${d.score}%</div>`).join('');
}
document.addEventListener('DOMContentLoaded', loadLeaderboard);

const metaForm = document.getElementById('quizMetaForm');
if(metaForm){
  metaForm.addEventListener('submit', e=>{
    e.preventDefault();
    const title = document.getElementById('quizTitle').value.trim();
    const count = parseInt(document.getElementById('qCount').value,10);
    const qForm = document.getElementById('questionsForm');
    qForm.style.display='block'; qForm.innerHTML='';
    for(let i=1;i<=count;i++){
      qForm.insertAdjacentHTML('beforeend', `
        <fieldset class="card" style="padding:16px;margin:12px 0">
          <legend>Question ${i}</legend>
          <label>Text</label><input required name="text${i}">
          <div class="grid-2">
            <div><label>Option A</label><input required name="A${i}"></div>
            <div><label>Option B</label><input required name="B${i}"></div>
            <div><label>Option C</label><input required name="C${i}"></div>
            <div><label>Option D</label><input required name="D${i}"></div>
          </div>
          <label>Correct (A/B/C/D)</label><input required name="correct${i}" maxlength="1">
        </fieldset>
      `);
    }
    qForm.insertAdjacentHTML('beforeend', `<button class="btn" id="saveQuizBtn">Save Quiz</button>`);
    document.getElementById('saveQuizBtn').onclick = async (ev)=>{
      ev.preventDefault();
      const qs = [];
      for(let i=1;i<=count;i++){
        const get = name => qForm.querySelector(`[name="${name}${i}"]`).value.trim();
        qs.push({text:get('text'), A:get('A'), B:get('B'), C:get('C'), D:get('D'), correct:get('correct').toUpperCase()});
      }
      const body = {title, questions:qs};
      const res = await fetch('/api/quizzes',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
      const out = await res.json();
      if(out.ok){ alert('Quiz saved! ID: '+out.quiz_id); window.location='/dashboard'; }
      else { alert('Failed: '+(out.error||'unknown')); }
    };
  });
}
