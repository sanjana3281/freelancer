// // --- CSRF helper ---
// function getCookie(name) {
//   let cookieValue = null;
//   if (document.cookie && document.cookie !== "") {
//     const cookies = document.cookie.split(";");
//     for (let cookie of cookies) {
//       cookie = cookie.trim();
//       if (cookie.substring(0, name.length + 1) === name + "=") {
//         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//         break;
//       }
//     }
//   }
//   return cookieValue;
// }
// const csrftoken = getCookie("csrftoken");

// // Add option to all selects of a given class
// function addOptionToAllSelects(className, id, text) {
//   document.querySelectorAll("select." + className).forEach(sel => {
//     // skip if already has it
//     const exists = Array.from(sel.options).some(o => String(o.value) === String(id));
//     if (!exists) sel.add(new Option(text, id));
//     // If you're using Select2/TomSelect, uncomment one of these:
//     // $(sel).append(new Option(text, id, false, false)).trigger("change.select2");
//   });
// }

// // Select value in the same row/card as the clicked button
// function selectInSameRow(btn, className, id) {
//   const container = btn.closest(".row, .formset-card") || document;
//   const sel = container.querySelector("select." + className) || document.querySelector("select." + className);
//   if (sel) {
//     sel.value = String(id);
//     sel.dispatchEvent(new Event("change", { bubbles: true }));
//     // If using Select2:
//     // $(sel).val(String(id)).trigger("change");
//   }
// }

// // Generic flow for both Role & Skill buttons
// async function handleAdd(btn) {
//   const endpoint = btn.dataset.endpointUrl;   // e.g., /ajax/skills/create/
//   const targetClass = btn.dataset.targetClass; // e.g., skill-select

//   // Replace prompt with your modal if you like; Enter submits either way.
//   const entered = prompt("Enter the new value:");
//   if (!entered || !entered.trim()) return;
//   const name = entered.trim();

//   const formData = new FormData();
//   formData.append("name", name);

//   try {
//     const resp = await fetch(endpoint, {
//       method: "POST",
//       headers: { "X-CSRFToken": csrftoken },
//       body: formData
//     });

//     // CREATED (201) -> add fresh option everywhere, select it here
//     if (resp.status === 201) {
//       const data = await resp.json();
//       addOptionToAllSelects(targetClass, data.id, data.name);
//       selectInSameRow(btn, targetClass, data.id);
//       return;
//     }

//     // DUPLICATE (409) -> use existing id, just select it (no refresh)
//     if (resp.status === 409) {
//       const data = await resp.json();
//       addOptionToAllSelects(targetClass, data.id, data.name); // ensure present
//       selectInSameRow(btn, targetClass, data.id);
//       alert(`“${data.name}” already exists. Selected it for you.`);
//       return;
//     }

//     // Other errors
//     const err = await resp.json().catch(() => ({}));
//     alert("Could not add. " + (err.error || "Server error."));
//   } catch (e) {
//     console.error(e);
//     alert("Network error.");
//   }
// }

// document.addEventListener("click", (e) => {
//   const btn = e.target.closest(".add-option-btn");
//   if (btn) handleAdd(btn);
// });
// CSRF helper
// ---- CSRF helper ----
// ---- CSRF helper ----
function getCookie(name){let v=null;if(document.cookie&&document.cookie!==""){for(let c of document.cookie.split(";")){c=c.trim();if(c.startsWith(name+"=")){v=decodeURIComponent(c.slice(name.length+1));break;}}}return v;}
const csrftoken = getCookie("csrftoken");

// ---- Add option to ALL selects of a class (native + common plugins) ----
function addOptionEverywhere(className, id, text) {
  const value = String(id);
  const label = String(text);

  document.querySelectorAll("select." + className).forEach(sel => {
    // 1) Native select
    if (!Array.from(sel.options).some(o => String(o.value) === value)) {
      sel.add(new Option(label, value));
    }

    // 2) TomSelect
    if (sel.tomselect) {
      const ts = sel.tomselect;
      ts.addOption({ value, text: label });
      ts.refreshOptions(false);
    }

    // 3) Select2 (jQuery)
    if (window.jQuery && jQuery.fn.select2 && jQuery(sel).data("select2")) {
      // Ensure an <option> exists, then trigger refresh
      if (!jQuery(sel).find("option[value='"+value.replace(/'/g,"\\'")+"']").length) {
        jQuery(sel).append(new Option(label, value, false, false));
      }
      jQuery(sel).trigger("change.select2");
    }

    // 4) Choices.js (if you attached instance on the element as sel.choices)
    if (sel.choices && typeof sel.choices.setChoices === "function") {
      sel.choices.setChoices([{ value, label, selected: false }], 'value', 'label', true);
    }
  });
}

// Select the new/existing option in the same row as the clicked button
function selectInThisRow(btn, className, id) {
  const container = btn.closest(".row, .formset-card, .formset-item") || document;
  const sel = container.querySelector("select." + className) || document.querySelector("select." + className);
  if (!sel) return;

  const value = String(id);

  // Native
  sel.value = value;
  sel.dispatchEvent(new Event("change", { bubbles: true }));

  // TomSelect
  if (sel.tomselect) sel.tomselect.setValue(value, true);

  // Select2
  if (window.jQuery && jQuery.fn.select2 && jQuery(sel).data("select2")) {
    jQuery(sel).val(value).trigger("change");
  }

  // Choices.js
  if (sel.choices && typeof sel.choices.setChoiceByValue === "function") {
    sel.choices.setChoiceByValue(value);
  }
}

async function handleAdd(btn) {
  const endpoint = btn.dataset.endpointUrl;     // /ajax/roles/create/ or /ajax/skills/create/
  const targetClass = btn.dataset.targetClass;  // role-select or skill-select

  const entered = prompt("Enter the new value:");
  if (!entered || !entered.trim()) return;
  const name = entered.trim();

  const fd = new FormData(); fd.append("name", name);

  try {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      body: fd
    });
    const data = await resp.json();

    if (resp.status === 201) {          // created
      addOptionEverywhere(targetClass, data.id, data.name);
      selectInThisRow(btn, targetClass, data.id);
      return;
    }
    if (resp.status === 409) {          // duplicate
      addOptionEverywhere(targetClass, data.id, data.name);
      selectInThisRow(btn, targetClass, data.id);
      alert(`“${data.name}” already exists. Selected it.`);
      return;
    }
    alert(data.error || "Server error.");
  } catch (e) {
    console.error(e);
    alert("Network error.");
  }
}

// Delegate clicks
document.addEventListener("click", e => {
  const btn = e.target.closest(".add-option-btn");
  if (btn) handleAdd(btn);
});

