
  const params = new URLSearchParams(location.search);
  const role = (params.get('role') || 'freelancer').toLowerCase();
  const nice = role === 'recruiter' ? 'Recruiter' : 'Freelancer';
  document.getElementById('who').textContent = nice;

 
  document.getElementById('pill-register').onclick = () => location.href = `/register?role=${role}`;
  document.getElementById('pill-login').classList.add('is-active');


  function getCookie(name){ const v = `; ${document.cookie}`.split(`; ${name}=`); if(v.length===2) return v.pop().split(';').shift(); }
  const csrftoken = getCookie('csrftoken');

 
  document.getElementById('login-form').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const endpoint = role === 'recruiter' ? '/api/recruiters/login' : '/api/freelancers/login';

    const res = await fetch(endpoint, {
      method:'POST',
      headers:{ 'Content-Type':'application/json', 'X-CSRFToken': csrftoken },
      credentials:'same-origin',
      body: JSON.stringify({ email, password })
    });
    const data = await res.json().catch(()=>({}));
    if(res.ok){
      alert(`Logged in as ${nice}!`);
    }else{
      alert(data.detail || 'Invalid email or password');
    }
  });


  document.getElementById('to-register').href = `/register?role=${role}`;