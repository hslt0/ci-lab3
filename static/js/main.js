const defaultVariant = window.defaultVariant;
document.getElementById("variant").value = JSON.stringify(defaultVariant, null, 2);

document.getElementById("loadDefault").addEventListener("click", () => {
  document.getElementById("variant").value = JSON.stringify(defaultVariant, null, 2);
});

function gridHtml(result, size, reefs) {
  if (!result) return "<p>Алгоритм не запускався.</p>";
  const reefSet = new Set(reefs.map(p => `${p[0]},${p[1]}`));
  const shipMap = new Map();
  result.placements.forEach((ship, index) => {
    for (let offset = 0; offset < ship.length; offset++) {
      const r = ship.direction === "H" ? ship.row : ship.row + offset;
      const c = ship.direction === "H" ? ship.col + offset : ship.col;
      shipMap.set(`${r},${c}`, String(index + 1));
    }
  });
  let html = `<div class="grid" style="grid-template-columns:repeat(${size}, 1fr)">`;
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const key = `${r},${c}`;
      let cls = "cell";
      let text = "";
      if (reefSet.has(key)) { cls += " reef"; text = "Р"; }
      if (shipMap.has(key)) { cls = "cell ship"; text = shipMap.get(key); }
      html += `<div class="${cls}">${text}</div>`;
    }
  }
  html += "</div>";
  if (result.unplaced.length) {
    html += `<p class="error">Не розміщено: ${result.unplaced.join(", ")}</p>`;
  }
  return html;
}

function drawChart(ga, sa) {
  const canvas = document.getElementById("chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const gaHistory = ga ? ga.history.map(p => p.best) : [];
  const saHistory = sa ? sa.history.map(p => p.best) : [];
  const all = gaHistory.concat(saHistory);
  if (!all.length) return;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const pad = 35;
  ctx.strokeStyle = "#b0bec5";
  ctx.beginPath();
  ctx.moveTo(pad, pad); ctx.lineTo(pad, canvas.height-pad);
  ctx.lineTo(canvas.width-pad, canvas.height-pad); ctx.stroke();
  ctx.fillStyle = "#263238";
  ctx.font = "12px Segoe UI";
  ctx.fillText(max.toFixed(2), 5, pad);
  ctx.fillText(min.toFixed(2), 5, canvas.height-pad);

  function series(values, color) {
    if (!values.length) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    values.forEach((value, index) => {
      const x = pad + index / Math.max(1, values.length - 1) * (canvas.width - 2 * pad);
      const y = canvas.height-pad - (value-min)/(max-min || 1)*(canvas.height-2*pad);
      if (index === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.stroke();
  }
  series(gaHistory, "#1565c0");
  series(saHistory, "#ef6c00");
  ctx.fillStyle = "#1565c0"; ctx.fillRect(pad, 12, 12, 12);
  ctx.fillStyle = "#263238"; ctx.fillText("ГА", pad+18, 22);
  ctx.fillStyle = "#ef6c00"; ctx.fillRect(pad+70, 12, 12, 12);
  ctx.fillStyle = "#263238"; ctx.fillText("SA", pad+88, 22);
}

document.getElementById("run").addEventListener("click", async () => {
  const error = document.getElementById("error");
  error.textContent = "";
  let variant;
  try { variant = JSON.parse(document.getElementById("variant").value); }
  catch (exc) { error.textContent = "Некоректний JSON: " + exc.message; return; }

  const payload = {
    variant,
    algorithm: document.getElementById("algorithm").value,
    seed: document.getElementById("seed").value,
    ga: {
      population: Number(document.getElementById("population").value),
      generations: Number(document.getElementById("generations").value),
      crossover: Number(document.getElementById("crossover").value),
      mutation: Number(document.getElementById("mutation").value),
      elitism: Number(document.getElementById("elitism").value)
    },
    sa: {
      iterations: Number(document.getElementById("iterations").value),
      initialTemperature: Number(document.getElementById("initialTemperature").value),
      finalTemperature: Number(document.getElementById("finalTemperature").value)
    }
  };

  const button = document.getElementById("run");
  button.disabled = true;
  try {
    const response = await fetch("/api/run", {
      method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Помилка запуску.");

    const ga = data.ga;
    const sa = data.sa;
    document.getElementById("gaGrid").innerHTML = gridHtml(ga, data.variant.field_size, data.variant.reefs);
    document.getElementById("saGrid").innerHTML = gridHtml(sa, data.variant.field_size, data.variant.reefs);

    const rows = [];
    if (ga) rows.push(`<tr><td>Генетичний алгоритм</td><td>${ga.fitness}</td><td>${ga.placements.length}</td><td>${ga.unplaced.length}</td></tr>`);
    if (sa) rows.push(`<tr><td>Імітаційний відпал</td><td>${sa.fitness}</td><td>${sa.placements.length}</td><td>${sa.unplaced.length}</td></tr>`);
    document.getElementById("summary").innerHTML = rows.join("");

    document.getElementById("metrics").innerHTML =
      `<div><b>Поле</b><br>${data.variant.field_size} × ${data.variant.field_size}</div>` +
      `<div><b>Кораблі</b><br>${data.variant.ships.length}</div>` +
      `<div><b>Рифів</b><br>${data.variant.reefs.length}</div>`;
    drawChart(ga, sa);
  } catch (exc) {
    error.textContent = exc.message;
  } finally {
    button.disabled = false;
  }
});
