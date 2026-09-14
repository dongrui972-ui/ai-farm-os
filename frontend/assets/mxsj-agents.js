/**
 * 作物 AI 智能体规格落地
 * - 专家名录、协同中心、联合诊断、协作工作台
 * - 规则编排仿真，不宣称真实模型或设备执行
 */
(function (global) {
  const EXPERT_CATALOG = [
    { key: "master", name: "Farm Master Agent", role: "总管拆解与汇总", duty: "任务规划、动态组队、交叉复核汇总", tools: ["任务编排", "专家选择", "结论汇总"] },
    { key: "crop-vigor", name: "作物长势 Agent", role: "作物长势评估", duty: "胁迫表现与生育期影响", tools: ["长势评估", "NDVI解读"] },
    { key: "soil-health", name: "土壤健康 Agent", role: "土壤健康评估", duty: "盐分、根区与返盐风险", tools: ["EC评估", "返盐风险"] },
    { key: "vri-optimize", name: "水肥优化 Agent", role: "变量水肥优化", duty: "补水条件、方案约束与安全边界", tools: ["墒情计算", "处方约束"] },
    { key: "weather", name: "气象分析 Agent", role: "气象窗口评估", duty: "蒸散、降雨与作业时间窗", tools: ["蒸散估算", "窗口判断"] },
    { key: "pest-alert", name: "病虫害预警 Agent", role: "病虫害监测预警", duty: "病斑/虫害风险识别", tools: ["病斑检测", "预警分级"] },
    { key: "yield-predict", name: "产量预测 Agent", role: "产量预测", duty: "单产与偏差分析", tools: ["产量模型"] },
    { key: "root-growth", name: "根系生长 Agent", role: "根系生长分析", duty: "根区水分与生长限制", tools: ["根区诊断"] },
    { key: "breeding", name: "生物育种 Agent", role: "生物育种咨询", duty: "品种适应性与育种建议", tools: ["品种匹配"] },
    { key: "phenotype", name: "表型分析 Agent", role: "作物表型分析", duty: "表型指标与影像特征", tools: ["表型分割"] },
    { key: "robot", name: "Robot Agent", role: "无人设备调度", duty: "巡田与农机路径", tools: ["路径规划"] },
    { key: "finance", name: "Finance Agent", role: "收益分析", duty: "成本与亩均增收", tools: ["ROI"] },
  ];

  const collabTasks = [
    {
      id: "CASE-DEMO-001",
      title: "B-01 棉花吐絮偏慢 · 脱叶窗口联合研判",
      land: "B-01",
      scene: "秋收脱叶",
      stage: "NO_GO · 证据待补",
      risk: "高",
      agents: ["master", "crop-vigor", "phenotype", "weather", "pest-alert"],
      conflict: "模拟开絮率不足 vs 过早脱叶风险：当前证据不足，不能形成喷施结论",
      gaps: ["带时间位置的开絮样方", "未来 7 日逐小时天气", "登记药剂标签与剂量校准", "清场与人工批准"],
      master: "NO_GO：先补齐现场样方、天气、标签、剂量与责任人批准；本案例不生成设备命令。",
      todos: ["补齐脱叶证据包", "指派农艺师与场长复核"],
      trace: [
        { t: "模拟", agent: "Farm Master", event: "接收仿真事件并拆解证据问题" },
        { t: "模拟", agent: "作物长势/表型/气象", event: "生成分析草稿，标记证据缺口" },
        { t: "NO_GO", agent: "安全门禁", event: "未形成可执行处方，等待人工复核" },
      ],
      selected: true,
    },
    {
      id: "CASE-DEMO-002",
      title: "B-02 春玉米机收含水与进仓节奏",
      land: "B-02",
      scene: "机收转运",
      stage: "NO_GO · 条件待核验",
      risk: "中",
      agents: ["master", "yield-predict", "robot", "weather"],
      conflict: "模拟含水与烘干吞吐均未由现场系统核验",
      gaps: ["成熟/黑层证据", "校准含水率", "试收损失与破碎率", "道路隔离", "运输、烘干与仓容"],
      master: "NO_GO：完成试收与收储能力核验后，由机务和仓储负责人共同排程。",
      todos: ["完成试收证据包", "核验道路与仓储能力"],
      trace: [{ t: "NO_GO", agent: "Robot Agent", event: "仅生成路线回放，未启动机收编队" }],
      selected: false,
    },
    {
      id: "CASE-DEMO-003",
      title: "C-01 冬麦适播准备证据核查",
      land: "C-01",
      scene: "秋种备播",
      stage: "证据待补充",
      risk: "中",
      agents: ["master", "weather", "vri-optimize", "crop-vigor"],
      conflict: "库尔勒本地种植制度未绑定，不得套用北疆适播日期",
      gaps: ["农业生态区编码与批准模板", "种子批次/发芽率/千粒重", "目标基本苗", "播层底墒", "机具校准"],
      master: "NO_GO：先由本地农艺师批准区域模板，再核验种子、底墒与机具。",
      todos: ["绑定属地模板", "补齐种子与底墒证据"],
      trace: [{ t: "NO_GO", agent: "气象/水肥", event: "区域规则缺失，未生成播种或灌水处方" }],
      selected: false,
    },
  ];

  let diagnosis = {
    stage: 1,
    executionState: "awaiting_approval",
    feedbackOutcome: "normal",
    caseId: "CASE-DEMO-001",
    label: "案例仿真",
  };

  let workbench = {
    conversations: [
      { id: "wb-1", title: "新协作任务", status: "仿真草稿", updatedAt: "模拟 2026-09-12 18:20", callCount: 5, agents: 3 },
    ],
    active: null,
    messages: [],
    mode: "规则编排仿真（非真实模型计费）",
  };

  function selectedTask() {
    return collabTasks.find((t) => t.selected) || collabTasks[0];
  }

  function catalogAgents() {
    return EXPERT_CATALOG.map((a, i) => ({
      id: 100 + i,
      key: a.key,
      name: a.name,
      role: a.role,
      status: a.key === "master" ? "仿真编排" : "仿真待机",
      last_action: a.duty,
      memory: [a.duty],
      tools: a.tools,
      score: null,
      score_label: "未验证",
      recent: [],
      source: "mxsj",
    }));
  }

  function diagnosisExperts() {
    const task = selectedTask();
    if (task.scene === "秋收脱叶") {
      return [
        { key: "crop-vigor", name: "作物长势 Agent", duty: "开絮进度与叶色", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 760, evidence: 0, gap: "原始样方与条带复核" },
        { key: "phenotype", name: "表型分析 Agent", duty: "开絮热力候选图", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 840, evidence: 0, gap: "原始影像与地面真值" },
        { key: "weather", name: "气象分析 Agent", duty: "脱叶喷施窗口", status: diagnosis.stage >= 2 ? "不可判定" : "等待", ms: 620, evidence: 0, gap: "逐小时预报与叶湿" },
        { key: "pest-alert", name: "病虫害预警 Agent", duty: "吐絮期残留风险", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 700, evidence: 0, gap: "物种/病级与局部取样" },
      ];
    }
    if (task.scene === "机收转运") {
      return [
        { key: "yield-predict", name: "产量预测 Agent", duty: "实收与测产偏差", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 780, evidence: 0, gap: "实收校准与地磅记录" },
        { key: "robot", name: "Robot Agent", duty: "机收路径与卸粮", status: diagnosis.stage >= 2 ? "NO_GO" : "等待", ms: 710, evidence: 0, gap: "边界、道路、试收与 ACK" },
        { key: "weather", name: "气象分析 Agent", duty: "收晒窗口", status: diagnosis.stage >= 2 ? "不可判定" : "等待", ms: 600, evidence: 0, gap: "逐小时天气" },
      ];
    }
    return [
      { key: "weather", name: "气象分析 Agent", duty: "适播窗与初霜风险", status: diagnosis.stage >= 2 ? "不可判定" : "等待", ms: 640, evidence: 0, gap: "属地模板与逐小时天气" },
      { key: "vri-optimize", name: "水肥优化 Agent", duty: "播前底墒", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 760, evidence: 0, gap: "底墒剖面与传感器 QC" },
      { key: "crop-vigor", name: "作物长势 Agent", duty: "播前地力与茬口", status: diagnosis.stage >= 2 ? "草稿完成" : "等待", ms: 720, evidence: 0, gap: "区域种植制度与整地记录" },
    ];
  }

  function runWorkbench(question) {
    const experts = ["crop-vigor", "soil-health", "vri-optimize"].map((k) => EXPERT_CATALOG.find((a) => a.key === k));
    const run = {
      id: "RUN-" + Date.now().toString().slice(-6),
      status: "draft_pending_human_review",
      stage: "草稿待人工复核",
      question,
      callCount: 5,
      providerName: "本地规则编排",
      model: "mxsj-demo-orchestrator",
      selectedAgents: experts.map((e) => ({ key: e.key, name: e.name, role: e.role, status: "草稿完成", ms: 700 + Math.round(Math.random() * 200) })),
      timeline: [
        { name: "总管拆解", status: "完成", note: "选择 3 位专家：长势 / 土壤 / 水肥" },
        { name: "专家并行", status: "草稿完成", note: "3/3 完成规则仿真" },
        { name: "交叉复核", status: "草稿完成", note: "发现 1 项分歧、2 项证据缺口" },
        { name: "总管汇总", status: "草稿完成", note: "生成安全纯文本答复" },
        { name: "人工复核边界", status: "待人工", note: "不调用工具/不控制设备" },
      ],
      conflicts: 1,
      gaps: 2,
      answer:
        "综合长势下降、墒情偏低与 EC 偏高信息：不能排除缺水与盐分叠加。" +
        "建议先核验排盐条件与最近灌溉实绩；若试验补水，仅采用小水分次并设置停止条件。" +
        "本答复不生成可直接下发设备的处方，高风险操作须场长结合现场数据复核。",
    };
    workbench.active = run;
    workbench.messages.push({ role: "user", text: question, at: new Date().toLocaleTimeString("zh-CN", { hour12: false }) });
    workbench.messages.push({ role: "stage", text: "总管已选择 3 位专家并开始并行分析", at: new Date().toLocaleTimeString("zh-CN", { hour12: false }) });
    workbench.messages.push({ role: "assistant", text: run.answer, at: new Date().toLocaleTimeString("zh-CN", { hour12: false }), run });
    const conv = workbench.conversations[0] || { id: "wb-1", title: "", status: "", updatedAt: "", callCount: 0, agents: 0 };
    conv.title = question.slice(0, 18) || "协作任务";
    conv.status = "草稿待复核";
    conv.updatedAt = new Date().toLocaleString("zh-CN");
    conv.callCount = run.callCount;
    conv.agents = experts.length;
    workbench.conversations[0] = conv;
    return run;
  }

  function handle(path, options, fallback) {
    const method = (options && options.method) || "GET";
    const body = options && options.body ? JSON.parse(options.body) : {};
    const url = new URL(path, "http://local.farm");
    const p = url.pathname;

    if (p === "/api/agents/catalog") {
      return { catalog: EXPERT_CATALOG, source: "crop-ai", note: "作物 AI 管家专家能力名录" };
    }

    if (p === "/api/collab/center") {
      const task = selectedTask();
      return {
        label: "案例仿真",
        metrics: {
          running: collabTasks.filter((t) => t.stage.includes("分析") || t.stage.includes("确认")).length,
          human: collabTasks.filter((t) => t.stage.includes("确认")).length,
          conflict: collabTasks.filter((t) => !!t.conflict).length,
          traceable: collabTasks.length,
        },
        tasks: collabTasks,
        selected: task,
        safety: "协同中心不直接生成真实工单，不控制设备；人工确认进入分步诊断页。",
      };
    }

    if (p === "/api/collab/select" && method === "POST") {
      collabTasks.forEach((t) => { t.selected = t.id === body.id; });
      return selectedTask();
    }

    if (p === "/api/diagnosis") {
      const task = selectedTask();
      diagnosis.caseId = task.id;
      const pack = task.scene === "秋收脱叶"
        ? {
            problem: `${task.land} 的开絮率仅为仿真快照；需判断证据是否足以进入脱叶评估，当前默认 NO_GO。`,
            evidence: [
              { name: "开絮率", value: "模拟约 58%", tag: "缺原始样方", ok: false },
              { name: "风速", value: "模拟 1.4 m/s", tag: "缺来源/时间戳", ok: false },
              { name: "未来 7 日", value: "未接入", tag: "逐小时预报缺失", ok: false },
              { name: "药剂与剂量", value: "未绑定", tag: "标签/校准/批准缺失", ok: false },
            ],
            conflict: {
              a: "表型草稿：模拟开絮率可触发现场复核",
              b: "农艺安全：过早或错误条件施药可能影响衣分、品级并产生漂移/药害",
              resolve: "NO_GO：补齐样方、天气、标签、剂量、清场和人工批准后重新研判；仅可模拟回放。",
            },
          }
        : task.scene === "机收转运"
          ? {
              problem: `${task.land} 的成熟期与含水均为仿真快照；需核验是否具备安全机收与收储条件。`,
              evidence: [
                { name: "籽粒含水", value: "模拟 24.5%", tag: "缺校准记录", ok: false },
                { name: "成熟/试收", value: "未导入", tag: "损失与破碎率缺失", ok: false },
                { name: "运输/烘干/仓容", value: "未接入", tag: "能力待核验", ok: false },
                { name: "天气与道路", value: "未接入", tag: "窗口不可判定", ok: false },
              ],
              conflict: {
                a: "机务草稿：成熟期模拟提示可准备试收",
                b: "安全与仓储：缺试收、道路、运输和收储证据，不得开机",
                resolve: "NO_GO：由机务与仓储负责人完成试收和容量核验，再人工排程；仅可模拟回放。",
              },
            }
          : {
              problem: `${task.land} 位于库尔勒试验场；区域模板、种子与底墒证据不足，当前 NO_GO。`,
              evidence: [
                { name: "区域模板", value: "未绑定", tag: "不得套用北疆日期", ok: false },
                { name: "底墒剖面", value: "待补采", tag: "证据缺口", ok: false },
                { name: "种子与播量", value: "未核验", tag: "批次/发芽率/千粒重缺失", ok: false },
                { name: "机具校准", value: "未确认", tag: "播种参数缺失", ok: false },
              ],
              conflict: {
                a: "总管草稿：可先登记区域规则与证据补全任务",
                b: "农艺与水肥：属地模板、种子和底墒不全，不得确定播期、播量或水量",
                resolve: "NO_GO：由本地农艺师批准模板，补齐种子、底墒与机具校准后再研判。",
              },
            };
      return {
        label: diagnosis.label,
        caseId: diagnosis.caseId,
        land: task.land,
        scene: task.scene,
        stage: diagnosis.stage,
        executionState: diagnosis.executionState,
        feedbackOutcome: diagnosis.feedbackOutcome,
        problem: pack.problem,
        evidence: pack.evidence,
        experts: diagnosisExperts(),
        conflict: pack.conflict,
        track: ["仿真事件进入总管", "总管拆解证据问题", "专家规则草稿", "交叉复核", "人工门禁与模拟回放", "反馈复盘"],
        stages: ["证据检查", "联合分析草稿", "协同决策", "模拟回放与复盘"],
      };
    }

    if (p === "/api/diagnosis/advance" && method === "POST") {
      if (diagnosis.stage < 4) diagnosis.stage += 1;
      if (diagnosis.stage === 4) diagnosis.executionState = "awaiting_approval";
      return handle("/api/diagnosis", { method: "GET" });
    }
    if (p === "/api/diagnosis/reset" && method === "POST") {
      diagnosis = { stage: 1, executionState: "awaiting_approval", feedbackOutcome: "normal", caseId: "CASE-DEMO-001", label: "案例仿真" };
      return handle("/api/diagnosis", { method: "GET" });
    }
    if (p === "/api/diagnosis/approve" && method === "POST") {
      diagnosis.executionState = "queued";
      return handle("/api/diagnosis", { method: "GET" });
    }
    if (p === "/api/diagnosis/exec" && method === "POST") {
      const order = ["queued", "running", "feedback", "reviewed"];
      const i = order.indexOf(diagnosis.executionState);
      diagnosis.executionState = order[Math.min(i + 1, order.length - 1)];
      if (diagnosis.executionState === "feedback") diagnosis.feedbackOutcome = body.outcome === "abnormal" ? "abnormal" : "normal";
      return handle("/api/diagnosis", { method: "GET" });
    }
    if (p === "/api/diagnosis/reopen" && method === "POST") {
      diagnosis.stage = 2;
      diagnosis.executionState = "awaiting_approval";
      diagnosis.feedbackOutcome = "abnormal";
      return handle("/api/diagnosis", { method: "GET" });
    }

    if (p === "/api/workbench") {
      return {
        ...workbench,
        catalog: EXPERT_CATALOG.filter((a) => a.key !== "master"),
        safety: "只回答、不调用工具、不直接执行设备。高风险建议须人工复核。",
      };
    }
    if (p === "/api/workbench/ask" && method === "POST") {
      const q = (body.question || "").trim();
      if (!q) throw new Error("请输入问题");
      if (q.length > 4000) throw new Error("问题超过 4000 字符上限");
      return runWorkbench(q);
    }
    if (p === "/api/workbench/new" && method === "POST") {
      workbench.messages = [];
      workbench.active = null;
      workbench.conversations.unshift({
        id: "wb-" + Date.now(),
        title: "新协作任务",
        status: "准备中",
        updatedAt: new Date().toLocaleString("zh-CN"),
        callCount: 0,
        agents: 0,
      });
      return workbench;
    }

    if (typeof fallback === "function") return fallback(path, options);
    throw new Error("未知 mxsj 接口 " + p);
  }

  // 包装原 FarmEngine，优先处理 mxsj 路由
  const prev = global.FarmEngine && global.FarmEngine.handle;
  global.FarmEngine = {
    handle(path, options) {
      try {
        return handle(path, options, prev);
      } catch (e) {
        if (String(e.message || "").startsWith("未知 mxsj") && prev) return prev(path, options);
        throw e;
      }
    },
    catalog: EXPERT_CATALOG,
    collabTasks,
  };

  // 将 mxsj 名录合并进既有 agents 列表（若原引擎暴露内部则跳过；页面通过 /api/agents/catalog 读取）
  global.FarmMxsj = { EXPERT_CATALOG, catalogAgents };
})(window);
