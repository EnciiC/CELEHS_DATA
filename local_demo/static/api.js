document.querySelector('#api-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = document.querySelector('#run-request');
  const output = document.querySelector('#api-output');
  const endpoint = document.querySelector('#endpoint').value;
  const allowed = ['/api/health','/api/datasets?q=AD','/api/datasets/UPMC_AD/schema','/api/chat'];
  if (!allowed.includes(endpoint)) return;
  button.disabled = true; output.textContent = 'Running request…';
  try {
    const options = endpoint === '/api/chat' ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:document.querySelector('#api-question').value})} : {};
    const response = await fetch(endpoint,options);
    output.textContent = `HTTP ${response.status}\n` + JSON.stringify(await response.json(),null,2);
  } catch(error) { output.textContent = error.message; }
  finally { button.disabled = false; }
});
