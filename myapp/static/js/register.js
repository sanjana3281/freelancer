
  const params = new URLSearchParams(location.search);
  let role = (params.get('role') || 'freelancer').toLowerCase();
  const nice = role === 'recruiter' ? 'Recruiter' : 'Freelancer';
  document.getElementById('who').textContent = nice;

  
  function showRole(r){
    const isR = r === 'recruiter';
    document.querySelectorAll('.only-f').forEach(el => el.style.display = isR ? 'none' : 'block');
    document.querySelectorAll('.only-r').forEach(el => el.style.display = isR ? 'block' : 'none');
  }
  showRole(role);

 
  document.getElementById('pill-login').onclick = () => location.href = `/login?role=${role}`;
  document.getElementById('pill-register').classList.add('is-active');


  function getCookie(name){ const v = `; ${document.cookie}`.split(`; ${name}=`); if(v.length===2) return v.pop().split(';').shift(); }
  const csrftoken = getCookie('csrftoken');


  document.getElementById('reg-form').addEventListener('submit', async (e)=>{
    e.preventDefault();

    if(role === 'freelancer'){
      const name = document.getElementById('f_name').value.trim();
      const email = document.getElementById('f_email').value.trim();
      const pw = document.getElementById('f_password').value;
      const pw2 = document.getElementById('f_password2').value;
      if(pw !== pw2){ alert('Passwords do not match.'); return; }

      const res = await fetch('/api/freelancers/register', {
        method:'POST',
        headers:{ 'Content-Type':'application/json', 'X-CSRFToken': csrftoken },
        credentials:'same-origin',
        body: JSON.stringify({ name, email, password: pw })
      });
      const data = await res.json().catch(()=>({}));
      if(res.ok){ alert('Freelancer registered!'); location.href = `/login?role=freelancer`; }
      else{ alert(data.detail || 'Registration failed'); }

    }else{
      const company_name = document.getElementById('r_company').value.trim();
      const contact_person = document.getElementById('r_contact').value.trim();
      const email = document.getElementById('r_email').value.trim();
      const pw = document.getElementById('r_password').value;
      const pw2 = document.getElementById('r_password2').value;
      if(pw !== pw2){ alert('Passwords do not match.'); return; }

      const res = await fetch('/api/recruiters/register', {
        method:'POST',
        headers:{ 'Content-Type':'application/json', 'X-CSRFToken': csrftoken },
        credentials:'same-origin',
        body: JSON.stringify({ company_name, contact_person, email, password: pw })
      });
      const data = await res.json().catch(()=>({}));
      if(res.ok){ alert('Recruiter registered!'); location.href = `/login?role=recruiter`; }
      else{ alert(data.detail || 'Registration failed'); }
    }
  });


  document.getElementById('to-login').href = `/login?role=${role}`;