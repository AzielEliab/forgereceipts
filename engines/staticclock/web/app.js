(function () {
  var geo = document.getElementById("geo");
  var anchor = document.getElementById("anchor");
  var go = document.getElementById("go");
  var fields = {
    geo: document.getElementById("out-geo"),
    time: document.getElementById("out-time"),
    date: document.getElementById("out-date"),
    lang: document.getElementById("out-lang"),
    dialect: document.getElementById("out-dialect")
  };

  function fill(el, value) {
    el.textContent = value || "—";
    if (value) el.classList.remove("empty");
    else el.classList.add("empty");
  }

  function clearAdvisory() {
    fill(fields.geo, "");
    fill(fields.time, "");
    fill(fields.date, "");
    fill(fields.lang, "");
    fill(fields.dialect, "");
  }

  fetch("/api/anchors").then(function (r) { return r.json(); }).then(function (names) {
    names.forEach(function (name) {
      var opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      anchor.appendChild(opt);
    });
  });

  fetch("/api/zones").then(function (r) { return r.json(); }).then(function (rows) {
    var body = document.getElementById("zones-body");
    body.textContent = "";
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      ["region", "iana", "local_date", "local_time", "utc_offset"].forEach(function (k) {
        var td = document.createElement("td");
        td.textContent = row[k] || "";
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  });

  document.getElementById("advise-form").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = (geo.value || "").trim();
    var picked = (anchor.value || "").trim();
    var query = text || picked;
    go.disabled = true;
    fetch("/api/advise", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ geo: query })
    }).then(function (r) { return r.json(); }).then(function (adv) {
      fill(fields.geo, adv.geo_location_chosen);
      fill(fields.time, adv.optimal_time);
      fill(fields.date, adv.optimal_date);
      fill(fields.lang, adv.primary_language);
      fill(fields.dialect, adv.dialect_section);
    }).catch(function () {
      clearAdvisory();
    }).finally(function () {
      go.disabled = false;
    });
  });
})();
