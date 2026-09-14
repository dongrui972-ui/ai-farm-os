/**
 * 角色化监控大屏（只看不办）
 * farm  — 田间态势：天气 / 清单状态 / 看田实景
 * expert — 研判态势：待审队列 / Agent / 冲突 / 处方状态
 * gov    — 监管态势：目标核验 / 高优 / 模拟在线率 / 关注
 */
(function (global) {
  const WALL_MAP_IMAGE = "assets/img/farm-real/farm-orthophoto.jpg";
  const SCENES = {
    satellite: {
      id: "satellite",
      name: "正射影像",
      img: WALL_MAP_IMAGE,
    },
    field: {
      id: "field",
      name: "边界底图",
      img: WALL_MAP_IMAGE,
    },
    aerial: {
      id: "aerial",
      name: "机队态势",
      img: WALL_MAP_IMAGE,
    },
    growth: {
      id: "growth",
      name: "长势伪彩",
      img: WALL_MAP_IMAGE,
    },
  };

  // 与 1536×1024 正射资料图同源的场景边界；不用于导航、面积结算或机械自动驾驶。
  const WALL_PLOT_GEOMETRY = {
    "A-01": { points: [[453, 66], [682, 66], [681, 438], [451, 438], [453, 66]], center: [567, 252] },
    "A-02": { points: [[686, 66], [946, 66], [947, 438], [683, 438], [686, 66]], center: [815, 252] },
    "B-01": { points: [[1004, 494], [1461, 493], [1462, 912], [1003, 914], [1004, 494]], center: [1232, 704] },
    "B-02": { points: [[980, 66], [1447, 66], [1451, 438], [979, 438], [980, 66]], center: [1215, 252] },
    "C-01": { points: [[558, 488], [968, 487], [968, 912], [557, 913], [558, 488]], center: [763, 702] },
    "C-02": { points: [[91, 486], [522, 485], [523, 910], [91, 911], [91, 486]], center: [307, 700] },
  };
  const WALL_INFRA_POINTS = {
    "WX-001": [150, 460],
    "RAIN-001": [225, 460],
    "PUMP-001": [305, 460],
    "FLOW-001": [380, 460],
  };

  function syncScenes(fromApi) {
    if (!fromApi) return;
    Object.keys(SCENES).forEach((k) => {
      if (fromApi[k] && fromApi[k].img) {
        SCENES[k] = { ...SCENES[k], ...fromApi[k], id: k, name: SCENES[k].name, img: WALL_MAP_IMAGE };
      }
    });
  }

  const LAYERS_FARM = [
    { id: "moisture", name: "墒情" },
    { id: "crop", name: "长势" },
    { id: "risk", name: "风险" },
    { id: "device", name: "机具" },
  ];
  const LAYERS_PRO = [
    { id: "moisture", name: "墒情" },
    { id: "crop", name: "长势" },
    { id: "plants", name: "单株" },
    { id: "risk", name: "风险" },
    { id: "device", name: "机队" },
    { id: "sensors", name: "传感" },
  ];

  let scene = "satellite";
  let layer = "moisture";
  let selected = "";
  let timer = null;
  let feedTimer = null;
  let pulseTimer = null;
  let refreshTimer = null;
  let open = false;
  let feedCursor = 0;
  let lastPaint = null;
  let lastPaintAt = Date.now();
  let opener = null;
  let cameraViewerOpen = false;
  let cameraViewerOpener = null;
  let pendingFocusMarker = null;
  const inertState = new Map();

  const WALL_FOCUS_ATTRS = ["data-scene", "data-wlayer", "data-code", "data-dev", "data-plant", "data-cam-land"];

  function captureWallFocus(root) {
    const el = document.activeElement;
    if (!el || !root.contains(el)) return null;
    if (el.id) return { id: el.id };
    for (const attr of WALL_FOCUS_ATTRS) {
      if (el.hasAttribute && el.hasAttribute(attr)) return { attr, value: el.getAttribute(attr) };
    }
    return null;
  }

  function restoreWallFocus(root, marker) {
    let target = marker && marker.id ? root.querySelector(`#${marker.id}`) : null;
    if (!target && marker && marker.attr) {
      target = [...root.querySelectorAll(`[${marker.attr}]`)].find((el) => el.getAttribute(marker.attr) === marker.value);
    }
    (target || root.querySelector("#wall-exit"))?.focus();
  }

  function setBackgroundInert(value) {
    [".skip-link", "#topbar", "#layout", "#notif-panel", "#cmd-panel"].forEach((selector) => {
      const el = document.querySelector(selector);
      if (!el) return;
      if (value) {
        inertState.set(el, Boolean(el.inert));
        el.inert = true;
      } else if (inertState.has(el)) {
        el.inert = inertState.get(el);
        inertState.delete(el);
      }
    });
  }

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function currentRole() {
    if (global.currentRole === "farm" || global.currentRole === "expert" || global.currentRole === "gov") {
      return global.currentRole;
    }
    try {
      const s = localStorage.getItem("agrios-role");
      if (s === "farm" || s === "expert" || s === "gov") return s;
    } catch (e) {}
    return document.body?.dataset?.role || "farm";
  }

  function layersFor(role) {
    return role === "farm" ? LAYERS_FARM : LAYERS_PRO;
  }

  function moistureColor(m) {
    if (typeof global.moistureColor === "function") return global.moistureColor(m);
    if (m < 22) return "#c45c26";
    if (m < 28) return "#d6a33a";
    return "#2f9e7a";
  }
  function growthColor(g) {
    if (typeof global.growthColor === "function") return global.growthColor(g);
    if (g < 75) return "#c45c26";
    if (g < 85) return "#d6a33a";
    return "#2f9e7a";
  }
  function riskColor(r) {
    if (typeof global.riskColor === "function") return global.riskColor(r);
    if (r > 50) return "#c45c26";
    if (r > 30) return "#d6a33a";
    return "#2f9e7a";
  }

  function fillOf(l) {
    if (layer === "crop") return growthColor(l.growth);
    if (layer === "risk") return riskColor(l.pest_risk);
    if (layer === "device" || layer === "sensors" || layer === "plants") return "rgba(120,145,110,0.18)";
    return moistureColor(l.moisture);
  }

  function landStatus(l) {
    if (l.moisture < 25) return { tag: "优先核验", cls: "orange", tip: "墒情场景值偏低" };
    if (l.pest_risk > 50) return { tag: "优先核验", cls: "red", tip: "风险场景值偏高" };
    if (l.growth < 75) return { tag: "待复核", cls: "orange", tip: "长势场景值偏弱" };
    return { tag: "规则未触发", cls: "gray", tip: "待现场核验" };
  }

  function layerName(id, role) {
    return (layersFor(role).find((x) => x.id === id) || {}).name || id;
  }

  async function loadData() {
    const api = global.api || (async (p) => global.FarmEngine.handle(p));
    const role = currentRole();
    await api("/api/role", { method: "POST", body: JSON.stringify({ role }) });
    const q = selected ? `&land=${encodeURIComponent(selected)}` : "";
    const [dash, twin, collab, fleet, desk] = await Promise.all([
      api("/api/dashboard"),
      api(`/api/twin?layer=${encodeURIComponent(layer)}${q}`),
      api("/api/collab/center").catch(() => null),
      api("/api/fleet").catch(() => null),
      api("/api/role/desk").catch(() => null),
    ]);
    return { dash, twin, collab, fleet, desk };
  }

  function agentOrbit(agents, joint) {
    const list = (agents || []).slice(0, 7);
    const cx = 138;
    const cy = 108;
    const R = 72;
    const master = list[0] || { name: "Farm Master", status: "运行中" };
    const others = list.slice(1);
    const nodes = others.map((a, i) => {
      const ang = (-90 + (i * 360) / Math.max(others.length, 1)) * (Math.PI / 180);
      return { ...a, x: cx + Math.cos(ang) * R, y: cy + Math.sin(ang) * R };
    });
    const activeNames = new Set(((joint && joint.agents) || []).map((a) => (a.name || "").split(" ")[0]));
    const lines = nodes
      .map((n, i) => {
        const hot = activeNames.size === 0 || [...activeNames].some((x) => (n.name || "").includes(x));
        return `<line class="wall-link ${hot ? "hot" : ""}" x1="${cx}" y1="${cy}" x2="${n.x}" y2="${n.y}" style="animation-delay:${i * 0.25}s"/>`;
      })
      .join("");
    const dots = nodes
      .map((n) => {
        const on = n.status === "运行中" || n.status === "执行中" || n.status === "分析中";
        const hot = [...activeNames].some((x) => (n.name || "").includes(x));
        return `
      <g class="wall-agent-node" data-agent="${esc(n.name || "")}">
        <circle cx="${n.x}" cy="${n.y}" r="17" class="wall-agent-ring ${on ? "on" : ""} ${hot ? "hot" : ""}"/>
        <circle cx="${n.x}" cy="${n.y}" r="11" class="wall-agent-core ${hot ? "hot" : ""}"/>
        <text x="${n.x}" y="${n.y + 30}" text-anchor="middle" class="wall-agent-label">${esc((n.name || "").replace(" Agent", "").slice(0, 9))}</text>
      </g>`;
      })
      .join("");
    return `
      <svg class="wall-agent-svg" viewBox="0 0 276 230">
        ${lines}
        <g class="wall-master" data-agent="master">
          <circle cx="${cx}" cy="${cy}" r="30" class="wall-master-halo"/>
          <circle cx="${cx}" cy="${cy}" r="22" class="wall-master-core"/>
          <text x="${cx}" y="${cy + 4}" text-anchor="middle" class="wall-master-text">总管</text>
          <text x="${cx}" y="${cy + 42}" text-anchor="middle" class="wall-agent-label">${esc((master.name || "Farm Master").replace(" Agent", "").slice(0, 12))}</text>
        </g>
        ${dots}
      </svg>`;
  }

  function mapSvg(lands, devices, sensors, plantList, focus, sceneUrl) {
    const mapPoint = (x, y) => [
      Math.round((Number(x) / 600) * 1536),
      Math.round((Number(y) / 580) * 1024),
    ];
    // 旧场景点位按其地块内相对位置投影到已配准边界；场部设施落在水塘南侧道路带。
    const registeredItemPoint = (item, landCode) => {
      if (WALL_INFRA_POINTS[item && item.code]) return WALL_INFRA_POINTS[item.code];
      const target = WALL_PLOT_GEOMETRY[landCode];
      const sourceLand = (lands || []).find((land) => land.code === landCode);
      const ring = sourceLand?.geojson?.coordinates?.[0] || [];
      if (!target || !ring.length) return mapPoint(item && item.x, item && item.y);
      const sourceX = ring.map((point) => Number(point[0]));
      const sourceY = ring.map((point) => Number(point[1]));
      const targetX = target.points.map((point) => Number(point[0]));
      const targetY = target.points.map((point) => Number(point[1]));
      const sx0 = Math.min(...sourceX);
      const sx1 = Math.max(...sourceX);
      const sy0 = Math.min(...sourceY);
      const sy1 = Math.max(...sourceY);
      const tx0 = Math.min(...targetX);
      const tx1 = Math.max(...targetX);
      const ty0 = Math.min(...targetY);
      const ty1 = Math.max(...targetY);
      const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
      const nx = clamp((Number(item && item.x) - sx0) / Math.max(1, sx1 - sx0), .08, .92);
      const ny = clamp((Number(item && item.y) - sy0) / Math.max(1, sy1 - sy0), .08, .92);
      return [Math.round(tx0 + nx * (tx1 - tx0)), Math.round(ty0 + ny * (ty1 - ty0))];
    };
    const polys = (lands || [])
      .map((l) => {
        const registered = WALL_PLOT_GEOMETRY[l.code];
        const rawRing = (l.geojson && l.geojson.coordinates && l.geojson.coordinates[0]) || [];
        const ring = registered ? registered.points : rawRing.map((p) => mapPoint(p[0], p[1]));
        const pts = ring.map((p) => p.join(",")).join(" ");
        const st = landStatus(l);
        const on = focus === l.code;
        const [cx, cy] = registered ? registered.center : mapPoint(...(l.center || [160, 130]));
        const metric =
          layer === "crop"
            ? `长势 ${l.growth}`
            : layer === "risk"
              ? `风险 ${l.pest_risk}`
              : layer === "sensors"
                ? `${l.sensor_online || 0}/${l.sensor_count || 0}点`
                : layer === "plants"
                  ? `冠${l.canopy_avg || "-"}/根${l.root_avg || "-"}`
                  : layer === "device"
                    ? l.code
                    : `${l.moisture}%`;
        return `
        <g class="wall-plot" data-code="${esc(l.code)}" role="button" tabindex="0" aria-label="选择地块 ${esc(l.code)} ${esc(l.name)}，${esc(st.tip)}">
          <polygon points="${pts}" fill="${fillOf(l)}" fill-opacity="${on ? 0.55 : 0.38}" class="${on ? "on" : ""}" stroke="${on ? "#fff" : "rgba(255,255,255,0.58)"}" stroke-width="${on ? 3 : 1.4}" vector-effect="non-scaling-stroke"/>
          <text x="${cx}" y="${cy - 11}" text-anchor="middle" class="wall-plot-code">${esc(l.code)}</text>
          <text x="${cx}" y="${cy + 31}" text-anchor="middle" class="wall-plot-metric">${esc(metric)}</text>
          <title>${esc(l.code)} ${esc(l.name)} · ${esc(st.tip)}</title>
        </g>`;
      })
      .join("");

    let marks = "";
    if (layer === "device") {
      marks = (devices || [])
        .filter((d) => !d.mesh)
        .map((d) => {
          const [x, y] = registeredItemPoint(d, d.location);
          return `
          <g class="wall-dev-g" transform="translate(${x},${y})" data-dev="${esc(d.code)}" data-dev-land="${esc(d.location)}" role="button" tabindex="0" aria-label="查看设备 ${esc(d.code)}，位置 ${esc(d.location)}">
            <circle r="36" class="wall-dev-halo"/>
            <circle r="24" class="wall-dev ${esc(d.device_type)}"/>
            <text x="34" y="9" class="wall-dev-lab" aria-hidden="true">${esc(d.code)}</text>
          </g>`;
        })
        .join("");
    } else if (layer === "sensors") {
      marks = (sensors || [])
        .map((s) => {
          const dim = focus && s.location !== focus;
          const fill = s.sensor_kind === "ec" ? "#a78bfa" : s.sensor_kind === "temp" ? "#f59e0b" : moistureColor(s.value || 25);
          const [x, y] = registeredItemPoint(s, s.location);
          return `<circle class="wall-sensor ${dim ? "dim" : ""}" cx="${x}" cy="${y}" r="${dim ? 5 : 8}" fill="${fill}" data-dev="${esc(s.code)}" data-dev-land="${esc(s.location)}" role="button" tabindex="0" aria-label="查看传感点 ${esc(s.code)}，位置 ${esc(s.location)}">
            <title>${esc(s.code)} · ${esc(s.last_value)}</title>
          </circle>`;
        })
        .join("");
    } else if (layer === "plants") {
      marks = (plantList || [])
        .map((pl) => {
          const dim = focus && pl.land_code !== focus;
          const fill = growthColor(pl.canopy?.vigor || 70);
          const [x, y] = registeredItemPoint(pl, pl.land_code);
          return `<circle class="wall-plant ${dim ? "dim" : ""} ${pl.status !== "正常" ? "watch" : ""}" cx="${x}" cy="${y}" r="${dim ? 5 : 8}" fill="${fill}" data-plant="${esc(pl.code)}" data-plant-land="${esc(pl.land_code)}" role="button" tabindex="0" aria-label="查看单株 ${esc(pl.code)}，地块 ${esc(pl.land_code)}">
            <title>${esc(pl.code)} · ${esc(pl.morph_name)} · 冠${pl.canopy.vigor}/根${pl.root.vigor}</title>
          </circle>`;
        })
        .join("");
    }
    return `<svg class="wall-field" viewBox="0 0 1536 1024" preserveAspectRatio="xMidYMid meet" role="group" aria-label="地块边界与正射资料同坐标叠加图">
      <image class="wall-map-photo" href="${esc(sceneUrl || WALL_MAP_IMAGE)}" x="0" y="0" width="1536" height="1024" preserveAspectRatio="none"/>
      <rect class="wall-map-photo-veil" x="0" y="0" width="1536" height="1024"/>
      ${polys}${marks}
    </svg>`;
  }

  function headerBar(role, title, now, weather, dataMeta) {
    const roleLabel = role === "expert" ? "专家监控屏" : role === "gov" ? "监管监控屏" : "田间监控屏";
    const isLive = dataMeta && dataMeta.mode === "live";
    const modeLabel = isLive ? "实时监控" : "仿真数据";
    const syncLabel = isLive ? "云边端同步" : "数据刷新";
    return `
      <header class="wall-top">
        <div class="wall-top-l">
          <span class="live-pill"><span class="dot ${isLive ? "green pulse" : "orange"}"></span> ${esc(modeLabel)}</span>
          <span class="wall-role-pill ${esc(role)}">${esc(roleLabel)}</span>
          <span class="wall-brand-mini">一级芯界</span>
          <span class="wall-date">${esc(now.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", weekday: "short" }))}</span>
        </div>
        <h1>${esc(title)}</h1>
        <div class="wall-top-r">
          <span class="wall-sync-pill"><i></i> ${esc(syncLabel)} <b class="num" id="wall-sync-age">0s</b></span>
          <span class="wall-weather mono" id="wall-weather">${esc(weather || "--")}</span>
          <span class="wall-clock num" id="wall-clock">${esc(now.toLocaleTimeString("zh-CN", { hour12: false }))}</span>
          <button type="button" class="btn ghost" id="wall-fs">全屏</button>
          <button type="button" class="btn" id="wall-exit">退出大屏</button>
        </div>
      </header>`;
  }

  function statusStrip(items) {
    return `
      <div class="wall-status-strip">
        ${(items || [])
          .map((it) => {
            const cls = [it.warn ? "warn" : "", it.ok ? "ok" : ""].filter(Boolean).join(" ");
            return `
          <div class="wall-status-item ${cls}">
            <span class="wall-status-label">${esc(it.label)}</span>
            <b class="num">${esc(it.value)}${it.unit ? `<small>${esc(it.unit)}</small>` : ""}</b>
            ${it.note ? `<em class="wall-status-note">${esc(it.note)}</em>` : ""}
          </div>`;
          })
          .join("")}
      </div>`;
  }

  function mapCenter(role, dash, twin, lands, devices, sensors, selectedCode, sc) {
    const lys = layersFor(role);
    const sceneUrl = sc && sc.img ? new URL(sc.img, document.baseURI).href : "";
    return `
      <section class="wall-center">
        <div class="wall-map-tools">
          <div class="wall-seg" data-group="scene">
            ${Object.values(SCENES)
              .map((s) => `<button type="button" class="twin-base-btn ${scene === s.id ? "active" : ""}" data-scene="${s.id}">${esc(s.name)}</button>`)
              .join("")}
          </div>
          <div class="wall-seg" data-group="layer">
            ${lys.map((ly) => `<button type="button" class="twin-base-btn ${layer === ly.id ? "active" : ""}" data-wlayer="${ly.id}">${esc(ly.name)}</button>`).join("")}
          </div>
        </div>
        <div class="wall-map-stage scene-${esc(scene)} layer-${esc(layer)}">
          ${mapSvg(lands, twin.devices || devices, sensors, twin.plants || twin.plants_all || [], selectedCode, sceneUrl)}
          <div class="wall-map-legend">
            <span>${esc(sc.name)}</span><span>·</span>
            <span>${esc(layerName(layer, role))}图层</span><span>·</span>
            <span>单击选中地块${["device", "sensors", "plants"].includes(layer) ? " · 悬停或聚焦点位查看编号" : ""} · ${dash.data_meta && dash.data_meta.mode === "live" ? "30 秒自动刷新" : "30 秒数据刷新"}</span>
          </div>
        </div>
        <div class="wall-cams">
          ${(dash.cams || [])
            .slice(0, 4)
            .map(
              (c) => `
            <div class="wall-cam" data-cam-land="${esc(c.land)}" data-cam-dev="${esc(c.device || "")}" data-cam-img="${esc(c.img || sc.img)}" data-cam-label="${esc(c.label)}" data-cam-zone="${esc(c.zone || "")}" data-cam-updated="${esc(c.updated || "时间待接入")}" data-cam-mode="${dash.data_meta && dash.data_meta.mode === "live" ? "live" : "replay"}" role="button" tabindex="0" aria-label="放大查看 ${esc(c.land)} ${esc(c.label)}监控画面">
              <div class="cam-view" style="background-image:url('${esc(c.img || sc.img)}')">
                <span class="cam-rec"><i></i> ${dash.data_meta && dash.data_meta.mode === "live" ? "实况" : "资料图"}</span>
                <span class="cam-zone">${esc(c.zone || "")}</span>
                <span class="cam-expand" aria-hidden="true">放大</span>
              </div>
              <div class="cam-label"><b>${esc(c.label)}</b><span>${esc(c.land)} · ${esc(c.updated)}</span></div>
            </div>`
            )
            .join("")}
        </div>
      </section>`;
  }

  function renderFarm(ctx) {
    const { dash, twin, lands, devices, sensors, focusLand, sc, k, p, jobs, photos, now } = ctx;
    const focusPhoto = (focusLand && photos[focusLand.code]) || sc.img;
    const weatherLine = (dash.weather && dash.weather.farmer_line) || (dash.weather && dash.weather.summary) || "";
    const urgentN = (jobs || []).filter((j) => j.status === "紧急").length;
    const strip = statusStrip([
      { label: "今日清单", value: (jobs || []).length, unit: "项", note: urgentN ? `${urgentN} 紧急` : "可控", warn: urgentN > 0, ok: urgentN === 0 },
      { label: "全场面积", value: k.area_mu || 2000, unit: "亩", note: "监控覆盖" },
      { label: "亩均增收目标", value: k.income_per_mu || 560, unit: "元", note: "待台账核验", warn: true },
      { label: "节水目标", value: k.water_saving || 20, unit: "%", note: "待计量核验", warn: true },
      { label: "节肥目标", value: k.fertilizer_saving || 15, unit: "%", note: "待投入品台账核验", warn: true },
      { label: "仿真产量估算", value: k.predicted_yield || "--", unit: "kg", note: "未校准", warn: true },
    ]);
    return `
      <div class="wall-screen wall-role-farm">
        ${headerBar("farm", "田间态势监控屏", now, weatherLine, dash.data_meta)}
        ${strip}
        <div class="wall-body wall-body-farm">
          <aside class="wall-col">
            <section class="wall-panel">
              <div class="wall-hd">今日清单状态</div>
              <div class="wall-job-list">
                ${(jobs || [])
                  .slice(0, 5)
                  .map(
                    (j) => `
                  <div class="wall-job-view ${j.status === "紧急" ? "urgent" : ""}">
                    <span>${esc(j.status)}</span>
                    <b>${esc(j.title)}</b>
                    <em>${esc(j.when)}</em>
                  </div>`
                  )
                  .join("") || `<div class="sub">今天没有紧急事项</div>`}
              </div>
            </section>
            <section class="wall-panel">
              <div class="wall-hd">气象与农时</div>
              <div class="wall-mon-note">
                <b>${esc(p.title || "田间态势平稳")}</b>
                <p>${esc(p.desc || weatherLine || "按农时观察墒情与长势")}</p>
                <p class="sub">${esc(p.weather_hint || weatherLine || "天气待更新")}${p.materials ? ` · ${esc(p.materials)}` : ""}</p>
              </div>
            </section>
          </aside>
          ${mapCenter("farm", dash, twin, lands, devices, sensors, selected, sc)}
          <aside class="wall-col">
            <section class="wall-panel wall-focus-panel">
              <div class="wall-hd">当前地块</div>
              ${
                focusLand
                  ? `<div class="wall-focus-card">
                <div class="wall-focus-photo" style="background-image:url('${esc(focusPhoto)}')"></div>
                <div class="wall-focus-body">
                  <div class="row-between"><b>${esc(focusLand.code)} ${esc(focusLand.name)}</b><span class="tag ${landStatus(focusLand).cls}">${esc(landStatus(focusLand).tag)}</span></div>
                  <div class="sub">${esc(focusLand.crop_name)} · ${esc(focusLand.stage)}</div>
                  <div class="wall-plot-metrics">
                    <span>含水 <b>${focusLand.moisture}%</b></span>
                    <span>长势 <b>${focusLand.growth}</b></span>
                  </div>
                </div>
              </div>`
                  : `<div class="sub">点地图选地块</div>`
              }
            </section>
            <section class="wall-panel grow">
              <div class="wall-hd">各田情况</div>
              <div class="wall-lands">
                ${lands
                  .map((l) => {
                    const st = landStatus(l);
                    return `<div class="wall-land ${selected === l.code ? "on" : ""}" data-land="${l.code}">
                      <div class="wall-land-thumb" role="img" aria-label="${esc(l.code)} ${esc(l.crop_name)}田间实景" style="background-image:url('${esc(photos[l.code] || sc.img)}')"></div>
                      <div class="wall-land-body">
                        <div class="row-between"><b>${esc(l.code)}</b><span class="tag ${st.cls}">${esc(st.tag)}</span></div>
                        <div class="sub">${esc(l.crop_name)} · 含水 ${l.moisture}%</div>
                        <div class="bar" aria-hidden="true"><span style="width:${Math.max(0, Math.min(100, Number(l.moisture) || 0))}%;background:${moistureColor(l.moisture)}"></span></div>
                      </div>
                    </div>`;
                  })
                  .join("")}
              </div>
            </section>
          </aside>
        </div>
        <footer class="wall-foot">
          <div class="wall-loop">只看态势不办业务 · 全场 ${k.area_mu || 2000} 亩</div>
          <div class="wall-foot-meta">田间监控 · Esc 退出</div>
        </footer>
      </div>`;
  }

  function renderExpert(ctx) {
    const { dash, twin, collab, fleet, desk, lands, devices, sensors, focusLand, sc, k, p, ai, joint, photos, now } = ctx;
    const focusPhoto = (focusLand && photos[focusLand.code]) || sc.img;
    const pendingHuman = collab && collab.metrics ? collab.metrics.human : 0;
    const m = (desk && desk.metrics) || {};
    const conflict = (ai.conflicts && ai.conflicts[0]) || null;
    const strip = statusStrip([
      { label: "待审", value: m.audit || 0, unit: "单", note: "队列监控", warn: (m.audit || 0) > 0 },
      { label: "人工确认", value: pendingHuman, unit: "项", warn: pendingHuman > 0 },
      { label: "作业窗口", value: (ai.window && ai.window.score) || "--", note: (ai.window && ai.window.slot) || "--" },
      { label: "机队负荷", value: (ai.load && ai.load.util) || 0, unit: "%", warn: ((ai.load && ai.load.util) || 0) > 85 },
      { label: "节水目标", value: k.water_saving || 20, unit: "%", note: "待计量核验", warn: true },
      { label: "节肥目标", value: k.fertilizer_saving || 15, unit: "%", note: "待投入品台账核验", warn: true },
    ]);
    return `
      <div class="wall-screen wall-role-expert">
        ${headerBar("expert", "专家研判监控屏", now, dash.weather && dash.weather.summary, dash.data_meta)}
        ${strip}
        <div class="wall-ai-bar">
          <div class="wall-ai-item"><span class="sub">作业窗口</span><b class="num">${(ai.window && ai.window.score) ?? "--"}</b><span class="mono">${esc((ai.window && ai.window.slot) || "--")}</span></div>
          <div class="wall-ai-item"><span class="sub">冲突仲裁</span><b>${esc((conflict && conflict.level) || "低")}</b><span>${esc((conflict && conflict.text) || "无硬冲突").slice(0, 26)}</span></div>
          <div class="wall-ai-item"><span class="sub">机队负荷</span><b class="num">${(ai.load && ai.load.util) || 0}%</b><div class="wall-mini-bar"><i style="width:${(ai.load && ai.load.util) || 0}%"></i></div></div>
          <div class="wall-ai-timeline">
            ${(ai.timeline || []).map((t) => `<div class="wall-ai-tl"><span class="mono">${esc(t.t)}</span><span>${esc(t.act)}</span><em>${esc(t.agent)}</em></div>`).join("")}
          </div>
        </div>
        <div class="wall-mon-note" style="margin:8px 14px 0">
          <b>${esc(p.title || "研判态势")}</b>
          <p class="sub">${esc((p.why || p.desc || "持续观察待审与冲突状态").slice(0, 120))}</p>
        </div>
        <div class="wall-body">
          <aside class="wall-col">
            <section class="wall-panel">
              <div class="wall-hd">待审核队列</div>
              <div class="wall-audit-list">
                ${((desk && desk.audit_queue) || [])
                  .slice(0, 5)
                  .map(
                    (t) => `
                  <div class="wall-audit-item">
                    <div class="row-between"><b>${esc(t.title)}</b><span class="tag orange">待审</span></div>
                    <div class="sub">${esc(t.land_code)} · ${esc(t.note || "")}</div>
                  </div>`
                  )
                  .join("") || `<div class="sub">暂无待审</div>`}
              </div>
            </section>
            <section class="wall-panel grow">
              <div class="wall-hd">智能体联动</div>
              ${agentOrbit(dash.agents || [], joint)}
            </section>
          </aside>
          ${mapCenter("expert", dash, twin, lands, devices, sensors, selected, sc)}
          <aside class="wall-col">
            <section class="wall-panel">
              <div class="wall-hd">当前地块 / 处方</div>
              ${
                focusLand
                  ? `<div class="wall-focus-card compact">
                <div class="wall-focus-photo" style="background-image:url('${esc(focusPhoto)}')"></div>
                <div class="wall-focus-body">
                  <div class="row-between"><b>${esc(focusLand.code)}</b><span class="tag ${landStatus(focusLand).cls}">${esc(landStatus(focusLand).tag)}</span></div>
                  <div class="wall-plot-metrics">
                    <span>含水 <b>${focusLand.moisture}%</b></span>
                    <span>风险 <b>${focusLand.pest_risk}</b></span>
                    <span>长势 <b>${focusLand.growth}</b></span>
                    <span>NPK <b>${focusLand.n}/${focusLand.p}/${focusLand.k}</b></span>
                  </div>
                </div>
              </div>`
                  : ""
              }
              <div class="wall-rx-list">
                ${((desk && desk.prescriptions) || [])
                  .slice(0, 3)
                  .map(
                    (pl) => `
                  <div class="item wall-rx-item">
                    <div class="row-between"><b>${esc(pl.land_code)} · ${pl.calculation_status === "NOT_CALCULATED" || pl.water_mm == null ? "水量未计算" : `${pl.water_mm} mm`}</b><span class="tag ${statusTone(pl.status)}">${esc(pl.status)}</span></div>
                    <div class="sub">${esc(pl.reason).slice(0, 40)}</div>
                  </div>`
                  )
                  .join("")}
              </div>
            </section>
            <section class="wall-panel grow">
              <div class="wall-hd">作业动态</div>
              <div class="wall-feed" id="wall-feed">
                ${(dash.feed || [])
                  .slice(0, 7)
                  .map(
                    (f) =>
                      `<div class="wall-feed-item"><span class="t">${esc(f.t)}</span><span><b>${esc(f.agent)}</b> ${esc(f.event)}</span></div>`
                  )
                  .join("")}
              </div>
            </section>
          </aside>
        </div>
        <footer class="wall-foot">
          <div class="wall-loop">只看态势不办业务 · 节水/节肥为待核验目标场景</div>
          <div class="wall-foot-meta">专家监控 · Esc 退出</div>
        </footer>
      </div>`;
  }

  function renderGov(ctx) {
    const { dash, twin, desk, lands, devices, sensors, focusLand, sc, k, p, photos, now } = ctx;
    const m = (desk && desk.metrics) || {};
    const onlinePct = m.device_online_pct || 0;
    const focusPhoto = (focusLand && photos[focusLand.code]) || sc.img;
    const strip = statusStrip([
      { label: "管理面积", value: m.area_mu || k.area_mu || 2000, unit: "亩" },
      { label: "节水目标", value: m.water_saving || 20, unit: "%", note: "待计量核验", warn: true },
      { label: "节肥目标", value: m.fertilizer_saving || 15, unit: "%", note: "待投入品台账核验", warn: true },
      { label: "减药目标", value: m.pesticide_saving || 18, unit: "%", note: "待植保台账核验", warn: true },
      { label: "亩均增收目标", value: m.income_per_mu || 560, unit: "元", note: "待台账核验", warn: true },
      { label: "设备状态核验", value: onlinePct, unit: "%", note: "场景档案", warn: true },
      { label: "高优任务", value: m.high_tasks || 0, warn: (m.high_tasks || 0) > 0 },
    ]);
    return `
      <div class="wall-screen wall-role-gov">
        ${headerBar("gov", "监管合规监控屏", now, dash.weather && dash.weather.summary, dash.data_meta)}
        ${strip}
        <div class="wall-mon-note" style="margin:8px 14px 0">
          <b>${esc(p.title || "全场运行可控")}</b>
          <p class="sub">${esc((p.desc || "目标场景核验与高优任务持续监视").slice(0, 120))}</p>
        </div>
        <div class="wall-body wall-body-gov">
          <aside class="wall-col">
            <section class="wall-panel grow">
              <div class="wall-hd">合规目标核验板 · 场景值</div>
              ${((desk && desk.compliance) || [])
                .map(
                  (c) => `
                <div class="wall-comp ${c.verified && c.ok ? "ok" : "bad"}">
                  <div class="row-between"><b>${esc(c.name)}</b><span class="tag ${c.verified && c.ok ? "green" : "orange"}">${c.verified ? (c.ok ? "已核验达标" : "已核验关注") : "待核验"}</span></div>
                  <div class="sub">${esc(c.target)} · ${esc(c.result || "证据待补")}</div>
                  <div class="wall-comp-val num">${esc(c.actual)}</div>
                </div>`
                )
                .join("")}
            </section>
            <section class="wall-panel">
              <div class="wall-hd">关注条</div>
              ${((desk && desk.flags) || [])
                .slice(0, 4)
                .map(
                  (f) => `
                <div class="wall-gov-task">
                  <div class="row-between"><b>${esc(f.title)}</b><span class="tag blue">${esc(f.level)}</span></div>
                  <div class="sub">${esc(f.land_code)} · ${esc(f.at)}</div>
                </div>`
                )
                .join("") || `<div class="sub">暂无关注项</div>`}
            </section>
          </aside>
          ${mapCenter("gov", dash, twin, lands, devices, sensors, selected, sc)}
          <aside class="wall-col">
            <section class="wall-panel">
              <div class="wall-hd">当前地块</div>
              ${
                focusLand
                  ? `<div class="wall-focus-card compact">
                <div class="wall-focus-photo" style="background-image:url('${esc(focusPhoto)}')"></div>
                <div class="wall-focus-body">
                  <div class="row-between"><b>${esc(focusLand.code)}</b><span class="tag ${landStatus(focusLand).cls}">${esc(landStatus(focusLand).tag)}</span></div>
                  <div class="sub">${esc(focusLand.crop_name)} · ${esc(focusLand.stage)}</div>
                </div>
              </div>`
                  : `<div class="sub">点地图选地块</div>`
              }
            </section>
            <section class="wall-panel grow">
              <div class="wall-hd">高优任务监察</div>
              ${((desk && desk.high_tasks) || [])
                .slice(0, 5)
                .map(
                  (t) => `
                <div class="wall-gov-task">
                  <div class="row-between"><b>${esc(t.title)}</b><span class="tag orange">${esc(t.status)}</span></div>
                  <div class="sub">${esc(t.land_code)} · ${esc(t.priority)}优先</div>
                </div>`
                )
                .join("") || `<div class="sub">暂无高优任务</div>`}
            </section>
            <section class="wall-panel">
              <div class="wall-hd">监管动态</div>
              <div class="wall-feed" id="wall-feed">
                ${(dash.feed || [])
                  .slice(0, 3)
                  .map(
                    (f) =>
                      `<div class="wall-feed-item"><span class="t">${esc(f.t)}</span><span><b>${esc(f.agent)}</b> ${esc(f.event)}</span></div>`
                  )
                  .join("")}
              </div>
            </section>
          </aside>
        </div>
        <footer class="wall-foot">
          <div class="wall-loop">只看态势不办业务 · 全场 ${m.area_mu || k.area_mu || 2000} 亩</div>
          <div class="wall-foot-meta">监管监控 · Esc 退出</div>
        </footer>
      </div>`;
  }

  function pushLiveFeed(root, dash) {
    const list = root.querySelector("#wall-feed");
    if (!list || !dash || !(dash.feed || []).length) return;
    const pool = dash.feed;
    feedCursor = (feedCursor + 1) % pool.length;
    const f = pool[feedCursor];
    const row = document.createElement("div");
    row.className = "wall-feed-item flash";
    const t = dash.data_meta && dash.data_meta.mode === "live"
      ? new Date().toLocaleTimeString("zh-CN", { hour12: false })
      : (f.t || "模拟");
    row.innerHTML = `<span class="t">${esc(t)}</span><span><b>${esc(f.agent)}</b> ${esc(f.event)}</span>`;
    list.insertBefore(row, list.firstChild);
    while (list.children.length > 12) list.removeChild(list.lastChild);
  }

  async function paint() {
    const root = document.getElementById("wall-root");
    if (!root || !open) return;
    if (cameraViewerOpen) return;
    const focusMarker = pendingFocusMarker || captureWallFocus(root);
    pendingFocusMarker = null;
    root.setAttribute("aria-busy", "true");
    const role = currentRole();
    if (role === "farm" && !LAYERS_FARM.some((l) => l.id === layer)) layer = "moisture";

    const { dash, twin, collab, fleet, desk } = await loadData();
    if (!open) return;
    syncScenes(dash && dash.scenes);
    lastPaint = { dash, twin, collab, fleet, desk, role };

    const k = dash.kpis || {};
    const p = dash.priority || {};
    const ai = dash.ai_dispatch || {};
    const jobs = dash.today_jobs || [];
    const lands = twin.lands || dash.lands || [];
    const devices = (twin.devices || dash.devices || []).filter((d) => !d.mesh);
    const sensors = twin.sensors || twin.sensors_all || [];
    if (!selected) selected = p.land_code && p.land_code !== "全场" ? p.land_code : (lands[0] && lands[0].code) || "";
    const focusLand = lands.find((l) => l.code === selected) || lands[0];
    const sc = SCENES[scene] || SCENES.satellite;
    const joint = (fleet && fleet.selected) || (fleet && fleet.ops && fleet.ops[0]) || null;
    const photos = dash.land_photos || {};
    if (dash.land_media) {
      Object.keys(dash.land_media).forEach((code) => {
        if (!photos[code]) photos[code] = dash.land_media[code].thumb || dash.land_media[code].field;
      });
    }
    const now = new Date();

    const ctx = { dash, twin, collab, fleet, desk, lands, devices, sensors, focusLand, sc, k, p, ai, jobs, joint, photos, now };

    const wallTitle = role === "expert" ? "专家研判监控屏" : role === "gov" ? "监管合规监控屏" : "田间态势监控屏";
    root.setAttribute("aria-label", wallTitle);
    if (role === "expert") root.innerHTML = renderExpert(ctx);
    else if (role === "gov") root.innerHTML = renderGov(ctx);
    else root.innerHTML = renderFarm(ctx);

    lastPaintAt = Date.now();
    bind(root);
    root.setAttribute("aria-busy", "false");
    restoreWallFocus(root, focusMarker);
  }

  function closeCameraViewer(restoreFocus = true) {
    const root = document.getElementById("wall-root");
    root?.querySelector(".wall-camera-layer")?.remove();
    const screen = root?.querySelector(".wall-screen");
    if (screen) screen.inert = false;
    cameraViewerOpen = false;
    const focusTarget = cameraViewerOpener;
    cameraViewerOpener = null;
    if (restoreFocus && focusTarget && document.contains(focusTarget)) focusTarget.focus();
  }

  function openCameraViewer(trigger) {
    const root = document.getElementById("wall-root");
    const screen = root?.querySelector(".wall-screen");
    if (!root || !screen || cameraViewerOpen) return;
    const land = trigger.dataset.camLand || "未知地块";
    const label = trigger.dataset.camLabel || "监控画面";
    const zone = trigger.dataset.camZone || "田间";
    const updated = trigger.dataset.camUpdated || "时间待接入";
    const isLive = trigger.dataset.camMode === "live";
    const imageUrl = trigger.dataset.camImg ? new URL(trigger.dataset.camImg, document.baseURI).href : new URL(WALL_MAP_IMAGE, document.baseURI).href;
    cameraViewerOpen = true;
    cameraViewerOpener = trigger;
    screen.inert = true;
    root.insertAdjacentHTML(
      "beforeend",
      `<div class="wall-camera-layer">
        <section class="wall-camera-viewer" role="dialog" aria-modal="true" aria-labelledby="wallCameraTitle" aria-describedby="wallCameraDesc">
          <header class="wall-camera-head">
            <div>
              <span class="wall-camera-kicker"><i></i>${isLive ? "实时监控" : "资料画面回放"}</span>
              <h2 id="wallCameraTitle">${esc(land)} · ${esc(label)}</h2>
              <p id="wallCameraDesc">${isLive ? "视频源状态由设备链路提供" : "当前未接入实时视频流，此处播放已登记的资料画面回放"}</p>
            </div>
            <button type="button" class="btn ghost" id="wall-camera-close" aria-label="关闭放大监控画面">关闭</button>
          </header>
          <div class="wall-camera-stage is-playing" id="wallCameraStage">
            <div class="wall-camera-frame" role="img" aria-label="${esc(land)} ${esc(label)}田间监控画面" style="background-image:url('${esc(imageUrl)}')"></div>
            <div class="wall-camera-scan" aria-hidden="true"></div>
            <div class="wall-camera-osd">
              <span class="wall-camera-rec"><i></i>${isLive ? "LIVE" : "REPLAY"}</span>
              <span>${esc(zone)}</span>
              <span class="num" id="wall-camera-time">${esc(new Date().toLocaleTimeString("zh-CN", { hour12: false }))}</span>
            </div>
          </div>
          <footer class="wall-camera-foot">
            <div class="wall-camera-meta"><b>${esc(land)}</b><span>画面记录 ${esc(updated)}</span></div>
            <div class="wall-camera-actions">
              <button type="button" class="btn" id="wall-camera-play" aria-pressed="true">${isLive ? "暂停画面" : "暂停回放"}</button>
              <button type="button" class="btn ghost" id="wall-camera-land">定位 ${esc(land)}</button>
            </div>
          </footer>
        </section>
      </div>`
    );
    const layerEl = root.querySelector(".wall-camera-layer");
    const closeBtn = root.querySelector("#wall-camera-close");
    const playBtn = root.querySelector("#wall-camera-play");
    const stage = root.querySelector("#wallCameraStage");
    layerEl?.addEventListener("click", (event) => {
      if (event.target === layerEl) closeCameraViewer(true);
    });
    closeBtn?.addEventListener("click", () => closeCameraViewer(true));
    playBtn?.addEventListener("click", () => {
      const paused = stage?.classList.toggle("is-paused") || false;
      playBtn.setAttribute("aria-pressed", paused ? "false" : "true");
      playBtn.textContent = paused ? (isLive ? "继续画面" : "继续回放") : (isLive ? "暂停画面" : "暂停回放");
    });
    root.querySelector("#wall-camera-land")?.addEventListener("click", () => {
      selected = land;
      if (global.FarmFocus) global.FarmFocus.land = selected;
      closeCameraViewer(false);
      pendingFocusMarker = { attr: "data-code", value: land };
      paint().catch(() => {});
    });
    closeBtn?.focus();
  }

  function bind(root) {
    root.querySelector("#wall-exit").onclick = () => close();
    root.querySelector("#wall-fs").onclick = () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen?.();
        if (global.toast) global.toast("全屏展示", "按 Esc 可退出浏览器全屏", "green");
      } else {
        document.exitFullscreen?.();
      }
    };

    root.querySelectorAll("[data-scene]").forEach((btn) => {
      btn.onclick = () => {
        scene = btn.dataset.scene;
        paint();
      };
    });
    root.querySelectorAll("[data-wlayer]").forEach((btn) => {
      btn.onclick = () => {
        layer = btn.dataset.wlayer;
        paint();
      };
    });
    root.querySelectorAll("[data-land], .wall-plot").forEach((el) => {
      el.onclick = () => {
        selected = el.dataset.land || el.dataset.code || selected;
        if (global.FarmFocus) global.FarmFocus.land = selected;
        pendingFocusMarker = { attr: el.dataset.code ? "data-code" : "data-land", value: selected };
        paint();
      };
    });
    root.querySelectorAll("[data-dev]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = (ev) => {
        ev.stopPropagation();
        if (el.dataset.devLand && WALL_PLOT_GEOMETRY[el.dataset.devLand]) {
          selected = el.dataset.devLand;
          if (global.FarmFocus) global.FarmFocus.land = selected;
        }
        pendingFocusMarker = { attr: "data-dev", value: el.dataset.dev };
        paint();
      };
    });
    root.querySelectorAll("[data-plant]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = (ev) => {
        ev.stopPropagation();
        if (el.dataset.plantLand) {
          selected = el.dataset.plantLand;
          if (global.FarmFocus) global.FarmFocus.land = selected;
          pendingFocusMarker = { attr: "data-plant", value: el.dataset.plant };
          paint();
        }
      };
    });
    root.querySelectorAll("[data-cam-land]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = () => openCameraViewer(el);
    });
    root.querySelectorAll('[role="button"][tabindex="0"]').forEach((el) => {
      el.onkeydown = (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          if (typeof el.click === "function") el.click();
          else el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: global }));
        }
      };
    });
  }

  async function openWall() {
    if (!open) opener = document.activeElement;
    open = true;
    if (global.FarmFocus && global.FarmFocus.land) selected = global.FarmFocus.land;
    const root = document.getElementById("wall-root");
    if (!root) return;
    root.classList.add("show");
    root.setAttribute("aria-hidden", "false");
    setBackgroundInert(true);
    document.body.classList.add("wall-open");
    document.body.dataset.wallRole = currentRole();
    await paint();
    if (timer) clearInterval(timer);
    if (feedTimer) clearInterval(feedTimer);
    if (pulseTimer) clearInterval(pulseTimer);
    if (refreshTimer) clearInterval(refreshTimer);
    timer = setInterval(() => {
      const el = document.getElementById("wall-clock");
      if (el) el.textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });
      const age = document.getElementById("wall-sync-age");
      if (age) {
        const seconds = Math.max(0, Math.floor((Date.now() - lastPaintAt) / 1000));
        age.textContent = seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m`;
      }
      const cameraTime = document.getElementById("wall-camera-time");
      if (cameraTime) cameraTime.textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });
    }, 1000);
    feedTimer = setInterval(async () => {
      if (!open) return;
      try {
        const dash = await (global.api || ((p) => global.FarmEngine.handle(p)))("/api/dashboard");
        pushLiveFeed(root, dash);
      } catch (e) {
        /* ignore */
      }
    }, 4200);
    pulseTimer = setInterval(() => {
      if (!open) return;
      root.querySelectorAll(".wall-link.hot").forEach((ln) => {
        ln.classList.remove("pulse-once");
        void ln.offsetWidth;
        ln.classList.add("pulse-once");
      });
    }, 3200);
    refreshTimer = setInterval(() => {
      if (open) paint().catch(() => {});
    }, 30000);
  }

  function close(silent) {
    open = false;
    cameraViewerOpen = false;
    cameraViewerOpener = null;
    if (timer) clearInterval(timer);
    if (feedTimer) clearInterval(feedTimer);
    if (pulseTimer) clearInterval(pulseTimer);
    if (refreshTimer) clearInterval(refreshTimer);
    timer = feedTimer = pulseTimer = refreshTimer = null;
    const root = document.getElementById("wall-root");
    if (root) {
      root.classList.remove("show");
      root.setAttribute("aria-hidden", "true");
      root.setAttribute("aria-label", "态势大屏");
      root.innerHTML = "";
    }
    document.body.classList.remove("wall-open");
    delete document.body.dataset.wallRole;
    setBackgroundInert(false);
    if (document.fullscreenElement) document.exitFullscreen?.();
    try {
      localStorage.setItem("agrios-wall", "0");
    } catch (e) {}
    if (typeof global.onFarmWallClose === "function") global.onFarmWallClose();
    if (opener && typeof opener.focus === "function" && document.contains(opener)) opener.focus();
    opener = null;
    if (!silent && global.toast) global.toast("已退出态势大屏", "返回标准工作台", "green");
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && cameraViewerOpen) {
      e.preventDefault();
      closeCameraViewer(true);
      return;
    }
    if (e.key === "Escape" && open && !document.fullscreenElement) close();
    if (e.key === "Tab" && open) {
      const root = document.getElementById("wall-root");
      const focusable = root
        ? [...root.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])')]
            .filter((el) => el.getClientRects().length > 0 && !el.closest("[inert]"))
        : [];
      if (!focusable.length) {
        e.preventDefault();
        root?.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  global.FarmWall = {
    open: openWall,
    close,
    isOpen: () => open,
    paint,
    refreshForRole: () => {
      if (open) {
        document.body.dataset.wallRole = currentRole();
        paint();
      }
    },
  };

  try {
    if (localStorage.getItem("agrios-wall") === "1") {
      setTimeout(() => openWall(), 200);
    }
  } catch (e) {}
})(window);
